#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_CeleritasInjector.py  —  URN VIA-SYS-ENG-009  v0100

把 VeritasCeleritas 加速引擎導入母系統所有 .py
=============================================

由 Invoke-VeritasNexusCore.ps1 調用。

為什麼不直接寫死 `from VeritasCeleritas import _LazyModule`
--------------------------------------------------------
因為名字猜錯時，hook 會安靜掉進 except 分支：檔案改了、標記在、閘門綠，
但一次加速都沒發生。所以本工具先用 AST 讀 VeritasCeleritas.py 的**真實**
頂層匯出名單（唯讀，不執行對方程式碼），照實際有的名字生 hook；
一個可用的都找不到就拒絕注入，不留半套。

三道必須守的界線
----------------
1. 自我匯入        VeritasCeleritas.py 自己不能掛 hook。
2. 啟動期循環      Celeritas 的本地依賴閉包全部排除。它 import 的模組若反過來
                   import 它，載入時就成環，整個平台起不來。
3. 執行期綁定驗證  parse+compile 過關只代表語法對。另外開子行程真的 import 一次，
                   確認選定的符號存在。這關沒過就不准 --commit。

預設 dry-run 落在 staging。--commit 才寫回原地，且每檔先備份（只增不減）。
"""

from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====


import argparse
import ast
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

URN_SELF = "VIA-SYS-ENG-009"
VERSION = "v0100"
HOOK_MARK = "VIA-CELERITAS-HOOK"
HOOK_VERSION = "v2"

SKIP_DIRS = {
    "_superseded", "_legacy", "_to_delete", "_backup", "_recover", "_duplicates",
    "_versionguard", "_governance", "_hardening", "_deepprobe", "_audit",
    "_mother_audit", "_nexus", "_nexus_stage", "_celeritas", "_celeritas_stage",
    "_archive", ".git", "__pycache__", ".venv", "venv", "node_modules",
    "site-packages", ".idea", ".vs", ".pytest_cache", "build", "dist",
}

# 依偏好排序。找到哪個就用哪個，不假設。
PREFERRED_API = [
    "_LazyModule", "_LazyAttr", "LazyModule", "LazyAttr",
    "lazy_module", "lazy_import", "accelerate", "install", "enable", "boost",
]

LEADING_WS = re.compile(r"^[ \t]*")
SHEBANG = re.compile(r"^#!")
CODING = re.compile(r"^#.*coding[:=]")


def now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def read_text(path: Path) -> Optional[str]:
    for enc in ("utf-8-sig", "utf-8", "cp950"):
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, OSError):
            continue
    return None


def write_utf8_nobom(path: Path, text: str) -> None:
    """UTF-8 no-BOM 原子寫入。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
        os.replace(tmp, str(path))
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


# ---------------------------------------------------------------------------
# 1. 探測 Celeritas 的真實 API
# ---------------------------------------------------------------------------

def probe_celeritas(path: Path) -> Dict[str, Any]:
    """AST 讀出 VeritasCeleritas.py 的頂層匯出名單。不執行對方任何程式碼。

    回傳 exports / dunder_all / chosen / imports / error。
    chosen 為空代表沒有可用 API —— 呼叫端必須據此中止。
    """
    result: Dict[str, Any] = {
        "path": str(path), "exports": [], "dunder_all": [], "chosen": [],
        "imports": [], "error": "",
    }
    text = read_text(path)
    if text is None:
        result["error"] = "無法讀取（編碼問題或檔案不存在）"
        return result
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        result["error"] = "VeritasCeleritas.py 本身語法有誤 L%s: %s" % (exc.lineno, exc.msg)
        return result

    exports: List[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            exports.append(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    exports.append(target.id)
                    if target.id == "__all__" and isinstance(node.value, (ast.List, ast.Tuple)):
                        result["dunder_all"] = [
                            e.value for e in node.value.elts
                            if isinstance(e, ast.Constant) and isinstance(e.value, str)]
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            exports.append(node.target.id)
    result["exports"] = sorted(set(exports))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                result["imports"].append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            result["imports"].append(node.module.split(".")[0])
    result["imports"] = sorted(set(result["imports"]))

    available = set(result["dunder_all"]) or set(result["exports"])
    result["chosen"] = [name for name in PREFERRED_API if name in available]
    if not result["chosen"]:
        # 退而求其次：任何看起來像 lazy / accel 的公開名稱
        guess = [n for n in sorted(available)
                 if re.search(r"(?i)lazy|accel|celerit|fast|boost", n)]
        result["chosen"] = guess[:4]
    return result


def dependency_closure(celeritas: Path, root: Path) -> Set[str]:
    """算出 Celeritas 的本地依賴閉包（相對路徑集合）。

    這些模組一律不掛 hook。理由：Celeritas 匯入 A，A 又被掛上「匯入
    Celeritas」的 hook，就成了啟動期循環匯入，整個平台起不來。
    """
    index: Dict[str, Path] = {}
    for dirpath, dirnames, filenames in os.walk(str(root)):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            if name.endswith(".py"):
                index.setdefault(name[:-3], Path(dirpath) / name)

    closure: Set[str] = set()
    queue: List[Path] = [celeritas]
    seen: Set[str] = set()
    while queue:
        current = queue.pop()
        key = str(current.resolve())
        if key in seen:
            continue
        seen.add(key)
        try:
            closure.add(str(current.relative_to(root)))
        except ValueError:
            pass
        text = read_text(current)
        if text is None:
            continue
        try:
            tree = ast.parse(text, filename=str(current))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            names: List[str] = []
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module.split(".")[0]]
            for name in names:
                target = index.get(name)
                if target is not None and str(target.resolve()) not in seen:
                    queue.append(target)
    return closure


# ---------------------------------------------------------------------------
# 2. 生 hook
# ---------------------------------------------------------------------------

def build_hook(chosen: List[str], supportive: Path) -> str:
    """生惰性代理 hook。

    為什麼不是 `from VeritasCeleritas import accelerate`：
    實測 import 一次 0.411 秒（且該機器 polars/numba/duckdb 還是 stub，
    真裝了只會更慢）。把 eager import 塞進上千支 .py，等於每支腳本啟動
    都先付這個成本 —— 那是反加速。VeritasCeleritas 自己有
    ENABLE_LAZY_IMPORTS 與 _LazyModule，正因為 import 成本就是它要解的題。

    所以這裡放一個代理：不碰就零成本，第一次真的取用屬性時才載入。
    代理轉發整個模組，不只挑幾個名字，__all__ 裡的 411 個匯出全都拿得到。
    """
    literal = str(supportive.resolve()).replace("\\", "\\\\")
    sample = ", ".join(chosen[:4]) if chosen else "accelerate"
    return (
        '# --- {mark} {ver} ({urn} 自動插入；移除本區塊即完全還原) ---\n'
        '# 惰性綁定：import 期零成本，首次取用 _VIA.<name> 才載入 VeritasCeleritas。\n'
        '# 用法： _VIA.{sample} ...   （__all__ 全部匯出皆可直接取用）\n'
        'class _ViaCeleritas:  # noqa: E402\n'
        '    _mod = None\n'
        '    _failed = False\n'
        '    @classmethod\n'
        '    def _load(cls):\n'
        '        if cls._mod is None and not cls._failed:\n'
        '            import os as _o, sys as _s\n'
        '            _p = _o.environ.get("VIA_SUPPORTIVE") or r"{literal}"\n'
        '            if _p and _p not in _s.path:\n'
        '                _s.path.insert(0, _p)\n'
        '            try:\n'
        '                import VeritasCeleritas as _c\n'
        '                cls._mod = _c\n'
        '            except Exception:\n'
        '                cls._failed = True\n'
        '        return cls._mod\n'
        '    def __getattr__(self, name):\n'
        '        _m = _ViaCeleritas._load()\n'
        '        if _m is None:\n'
        '            raise AttributeError(\n'
        '                "VeritasCeleritas 不可用，無法取用 %s" % name)\n'
        '        return getattr(_m, name)\n'
        '_VIA = _ViaCeleritas()\n'
        '# --- end {mark} ---\n'
    ).format(mark=HOOK_MARK, ver=HOOK_VERSION, urn=URN_SELF,
             literal=literal, sample=sample)


def insertion_line(text: str, tree: ast.Module) -> int:
    """hook 要插在 module docstring 與 from __future__ 之後。"""
    line = 1
    for raw in text.splitlines()[:2]:
        if SHEBANG.match(raw) or CODING.match(raw):
            line += 1
        else:
            break
    if tree.body:
        first = tree.body[0]
        line = max(line, first.lineno)
        if ast.get_docstring(tree) is not None:
            line = (getattr(first, "end_lineno", first.lineno) or first.lineno) + 1
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            line = max(line, (getattr(node, "end_lineno", node.lineno) or node.lineno) + 1)
    return line


def verify_source(text: str, name: str) -> Tuple[bool, str]:
    try:
        ast.parse(text, filename=name)
    except SyntaxError as exc:
        return False, "parse L%s: %s" % (exc.lineno, exc.msg)
    try:
        compile(text, name, "exec")
    except (SyntaxError, ValueError) as exc:
        return False, "compile: %s" % exc
    return True, ""


# ---------------------------------------------------------------------------
# 3. 執行期綁定驗證
# ---------------------------------------------------------------------------

def verify_binding(python_exe: str, supportive: Path,
                   chosen: List[str]) -> Dict[str, Any]:
    """真的 import 一次，並問 Celeritas 自己的健康 API。

    hasattr 過關不代表會加速：Celeritas 有 stub 系統，函式庫沒裝時
    is_stub() 為 True，此時 API 還在但底層空轉。所以一併取回
    count_real_libs / get_missing_libs，讓實際加速範圍是可見的。
    """
    script = (
        "import json, sys, time\n"
        "sys.path.insert(0, sys.argv[1])\n"
        "out = {'ok': False, 'found': [], 'missing': [], 'error': '',\n"
        "       'import_seconds': 0.0, 'exports': 0, 'real_libs': None,\n"
        "       'missing_libs': [], 'version': ''}\n"
        "try:\n"
        "    t0 = time.perf_counter()\n"
        "    import VeritasCeleritas as C\n"
        "    out['import_seconds'] = round(time.perf_counter() - t0, 3)\n"
        "    out['version'] = str(getattr(C, '__version__', ''))\n"
        "    out['exports'] = len(getattr(C, '__all__', []) or [])\n"
        "    for name in sys.argv[2:]:\n"
        "        (out['found'] if hasattr(C, name) else out['missing']).append(name)\n"
        "    try:\n"
        "        if hasattr(C, 'count_real_libs'):\n"
        "            out['real_libs'] = C.count_real_libs()\n"
        "        if hasattr(C, 'get_missing_libs'):\n"
        "            out['missing_libs'] = sorted(C.get_missing_libs())[:25]\n"
        "    except Exception as exc:\n"
        "        out['missing_libs'] = ['health probe failed: %s' % exc]\n"
        "    out['ok'] = bool(out['found']) and not out['missing']\n"
        "except Exception as exc:\n"
        "    out['error'] = '%s: %s' % (type(exc).__name__, exc)\n"
        "print(json.dumps(out))\n"
    )
    try:
        proc = subprocess.run(
            [python_exe, "-c", script, str(supportive.resolve())] + chosen,
            capture_output=True, text=True, timeout=180)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "found": [], "missing": chosen,
                "error": "子行程失敗: %s" % exc}
    lines = (proc.stdout or "").strip().splitlines()
    if not lines:
        return {"ok": False, "found": [], "missing": chosen,
                "error": (proc.stderr or "無輸出")[:300]}
    try:
        return json.loads(lines[-1])
    except ValueError:
        return {"ok": False, "found": [], "missing": chosen,
                "error": "無法解析子行程輸出"}


def verify_laziness(python_exe: str, hook: str, chosen: List[str]) -> Dict[str, Any]:
    """證明 hook 真的是惰性，而且真的綁得到。

    這一關才是重點。compile 過只代表語法對；上一版就是這樣：閘門全綠、
    hook 裝好、_VIA_CELERITAS 卻是 False，一次加速都沒發生。
    這裡實際載入一支注入過的模組，量兩件事：
      1. 只 import 不取用時，VeritasCeleritas 不得出現在 sys.modules（零成本）
      2. 取用 _VIA.<name> 時要真的拿到東西（綁定成立）
    """
    result: Dict[str, Any] = {"lazy": False, "binds": False, "cold_seconds": 0.0,
                              "warm_seconds": 0.0, "error": ""}
    probe = chosen[0] if chosen else "accelerate"
    workdir = Path(tempfile.mkdtemp(prefix="via_lazy_"))
    try:
        target = workdir / "via_lazy_probe.py"
        target.write_text(
            '"""Laziness probe."""\n' + hook + "\nVALUE = 1\n",
            encoding="utf-8", newline="\n")
        script = (
            "import json, sys, time\n"
            "sys.path.insert(0, sys.argv[1])\n"
            "out = {'lazy': False, 'binds': False, 'cold_seconds': 0.0,\n"
            "       'warm_seconds': 0.0, 'error': ''}\n"
            "try:\n"
            "    t0 = time.perf_counter()\n"
            "    import via_lazy_probe as M\n"
            "    out['cold_seconds'] = round(time.perf_counter() - t0, 3)\n"
            "    out['lazy'] = 'VeritasCeleritas' not in sys.modules\n"
            "    t1 = time.perf_counter()\n"
            "    obj = getattr(M._VIA, sys.argv[2])\n"
            "    out['warm_seconds'] = round(time.perf_counter() - t1, 3)\n"
            "    out['binds'] = obj is not None\n"
            "except Exception as exc:\n"
            "    out['error'] = '%s: %s' % (type(exc).__name__, exc)\n"
            "print(json.dumps(out))\n"
        )
        try:
            proc = subprocess.run([python_exe, "-c", script, str(workdir), probe],
                                  capture_output=True, text=True, timeout=180)
        except (OSError, subprocess.TimeoutExpired) as exc:
            result["error"] = "子行程失敗: %s" % exc
            return result
        lines = (proc.stdout or "").strip().splitlines()
        if not lines:
            result["error"] = (proc.stderr or "無輸出")[:300]
            return result
        try:
            return json.loads(lines[-1])
        except ValueError:
            result["error"] = "無法解析子行程輸出"
            return result
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


# ---------------------------------------------------------------------------
# 4. 主流程
# ---------------------------------------------------------------------------

class Target:
    __slots__ = ("path", "rel", "status", "reason", "line", "patched")

    def __init__(self, path: Path, rel: str):
        self.path = path
        self.rel = rel
        self.status = "PENDING"
        self.reason = ""
        self.line = 0
        self.patched = ""


def collect(root: Path) -> List[Path]:
    found: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(str(root)):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            if name.endswith(".py"):
                found.append(Path(dirpath) / name)
    return sorted(found)


def fingerprint(root: Path) -> Tuple[int, int]:
    count = total = 0
    for dirpath, dirnames, filenames in os.walk(str(root)):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            try:
                total += (Path(dirpath) / name).stat().st_size
                count += 1
            except OSError:
                pass
    return count, total


CSS = """
:root{--bg:#f5f4f0;--paper:#fff;--ink:#1e1d1a;--line:#dbd9d3;--mute:#8a8780;
--blue:#4c78a8;--teal:#439a9a;--red:#c96b5a;--green:#5a9e6f}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);margin:0;padding:28px 30px 60px;
font:13px/1.5 "DM Sans",-apple-system,"Noto Sans TC",sans-serif}
h1{font:400 21px/1.2 "Syne","DM Sans",sans-serif;margin:0 0 4px}
h2{font:400 15px/1.2 "Syne",sans-serif;margin:30px 0 8px;
border-left:3px solid var(--ink);padding-left:9px}
.head{display:flex;align-items:center;gap:16px;border-bottom:1px solid var(--ink);
padding-bottom:16px}
.seal{font:400 34px/1 "Noto Serif TC",serif;border:1.5px solid var(--red);
color:var(--red);padding:6px 11px;border-radius:2px}
.sub{color:var(--mute);font:11px "DM Mono",Consolas,monospace}
.lede{color:var(--mute);font-size:12px;margin:6px 0 10px;max-width:98ch}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(126px,1fr));gap:9px;margin:14px 0}
.card{background:var(--paper);border:1px solid var(--line);border-radius:2px;padding:9px 11px}
.card .k{font:10px "DM Mono",Consolas,monospace;color:var(--mute);text-transform:uppercase}
.card .v{font:400 21px/1.2 "Syne",sans-serif;margin-top:3px}
table{width:100%;border-collapse:collapse;background:var(--paper);
border:1px solid var(--line);font-size:12px;table-layout:fixed}
th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;
vertical-align:top;word-break:break-all}
th{background:#faf9f6;font:10px "DM Mono",Consolas,monospace;color:var(--mute);
text-transform:uppercase;position:sticky;top:0;z-index:2}
.mono{font:11px "DM Mono",Consolas,monospace}
.num{text-align:right;font:11px "DM Mono",Consolas,monospace}
.pass{color:var(--green)}.fail{color:var(--red);font-weight:600}.warn{color:#b8893f}
.wrap{max-height:460px;overflow:auto;border:1px solid var(--line);border-radius:2px}
.wrap table{border:none}
pre{background:var(--paper);border:1px solid var(--line);border-radius:2px;
padding:11px;font:11px "DM Mono",Consolas,monospace;overflow:auto;white-space:pre-wrap}
"""


def table_html(rows: List[List[str]], headers: List[str],
               widths: Optional[List[str]] = None) -> str:
    if not rows:
        return '<p class="lede">（無）</p>'
    cols = ("<colgroup>%s</colgroup>" %
            "".join('<col style="width:%s">' % w for w in widths)) if widths else ""
    head = "".join("<th>%s</th>" % esc(h) for h in headers)
    body = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r) for r in rows)
    return "<table>%s<thead><tr>%s</tr></thead><tbody>%s</tbody></table>" % (cols, head, body)


def build_html(ctx: Dict[str, Any]) -> str:
    gates = ctx["gates"]
    verdict = "FAIL" if any(g["status"] == "FAIL" for g in gates) else (
        "WARN" if any(g["status"] == "WARN" for g in gates) else "PASS")
    gate_rows = [['<span class="mono">%s</span>' % esc(g["code"]), esc(g["title"]),
                  '<span class="%s">%s</span>' % (g["status"].lower(), g["status"]),
                  esc(g["detail"])] for g in gates]
    by_status: Dict[str, List[Target]] = {}
    for target in ctx["targets"]:
        by_status.setdefault(target.status, []).append(target)
    status_rows = [[esc(k), '<span class="num">%d</span>' % len(v),
                    esc(v[0].reason if v else "")]
                   for k, v in sorted(by_status.items(), key=lambda kv: -len(kv[1]))]
    skip_rows = [['<span class="mono">%s</span>' % esc(t.rel), esc(t.status), esc(t.reason)]
                 for t in ctx["targets"] if t.status != "INJECTED"][:400]
    done_rows = [['<span class="mono">%s</span>' % esc(t.rel),
                  '<span class="num">%d</span>' % t.line]
                 for t in ctx["targets"] if t.status == "INJECTED"][:400]
    probe = ctx["probe"]
    cards = "".join('<div class="card"><div class="k">%s</div><div class="v">%s</div></div>'
                    % (k, v) for k, v in ctx["cards"])
    return (
        "<!DOCTYPE html><html lang='zh-Hant'><head><meta charset='utf-8'>"
        "<title>VeritasCeleritas 導入 %s</title>"
        "<link href='https://fonts.googleapis.com/css2?family=Syne:wght@400;600&"
        "family=DM+Sans:wght@400;500&family=DM+Mono:wght@400;500&"
        "family=Noto+Serif+TC:wght@400&display=swap' rel='stylesheet'>"
        "<style>%s</style></head><body>"
        "<div class='head'><div class='seal'>理</div><div>"
        "<h1>VeritasCeleritas 加速引擎導入</h1>"
        "<div class='sub'>%s %s · %s · 模式 %s · 判定 <span class='%s'>%s</span>"
        "</div></div></div>"
        "<div class='sub'>root %s</div><div class='sub'>目的地 %s</div>"
        "<div class='cards'>%s</div>"
        "<h2>閘門</h2>%s"
        "<h2>Celeritas API 探測（AST，未執行對方程式碼）</h2>"
        "<p class='lede'>hook 用的是這裡探測到的**真實**名稱。猜名字的話，"
        "每個檔案都會安靜掉進 except，改了等於沒改。</p>"
        "<pre>路徑     %s\n"
        "__all__  %s\n"
        "頂層匯出 %s\n"
        "選用     %s\n"
        "執行期綁定 %s\n"
        "惰性驗證   %s</pre>"
        "<h2>產生的 hook</h2><pre>%s</pre>"
        "<h2>處置統計</h2>%s"
        "<h2>已注入</h2><div class='wrap'>%s</div>"
        "<h2>未注入（含原因）</h2>"
        "<p class='lede'>Celeritas 自己與它的本地依賴閉包一律排除 —— "
        "它們若反過來匯入 Celeritas，載入時就成環。</p><div class='wrap'>%s</div>"
        "</body></html>"
        % (esc(ctx["stamp"]), CSS, URN_SELF, VERSION, esc(ctx["generated"]),
           esc(ctx["mode"]), verdict.lower(), verdict,
           esc(ctx["root"]), esc(ctx["dest"]), cards,
           table_html(gate_rows, ["code", "gate", "status", "detail"],
                      ["7%", "24%", "8%", "61%"]),
           esc(probe["path"]),
           esc(", ".join(probe["dunder_all"]) or "（未定義 __all__）"),
           esc(", ".join(probe["exports"][:40]) or "（無）"),
           esc(", ".join(probe["chosen"]) or "（無 —— 已中止）"),
           esc(json.dumps(ctx["binding"], ensure_ascii=False)),
           esc(json.dumps(ctx["lazy"], ensure_ascii=False)),
           esc(ctx["hook"]),
           table_html(status_rows, ["處置", "檔數", "說明"], ["22%", "10%", "68%"]),
           table_html(done_rows, ["檔案", "插入行"], ["84%", "16%"]),
           table_html(skip_rows, ["檔案", "處置", "原因"], ["46%", "16%", "38%"])))


def run(root: Path, celeritas: Path, out_dir: Path, stage: Path,
        python_exe: str, commit: bool) -> int:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)

    root_full = str(root.resolve()).rstrip(os.sep) + os.sep
    if (str(out_dir.resolve()).rstrip(os.sep) + os.sep).startswith(root_full):
        print("輸出目錄在母系統之內，已中止。")
        return 1

    if not celeritas.is_file():
        print("找不到 VeritasCeleritas.py：%s" % celeritas)
        return 1

    probe = probe_celeritas(celeritas)
    if probe["error"]:
        print("探測失敗：%s" % probe["error"])
        return 1
    if not probe["chosen"]:
        print("VeritasCeleritas.py 沒有任何可用的匯出 API。")
        print("頂層匯出：%s" % (", ".join(probe["exports"][:30]) or "（無）"))
        print("拒絕注入 —— 掛上去也只會每次掉進 except，改了等於沒改。")
        return 1

    supportive = celeritas.parent
    binding = verify_binding(python_exe, supportive, probe["chosen"])
    hook = build_hook(probe["chosen"], supportive)
    lazy = verify_laziness(python_exe, hook, probe["chosen"])

    closure = dependency_closure(celeritas, root)
    before = fingerprint(root)

    targets: List[Target] = []
    for path in collect(root):
        rel = str(path.relative_to(root))
        target = Target(path, rel)
        targets.append(target)

        if rel in closure:
            target.status = "SKIP_BOOTSTRAP"
            target.reason = "Celeritas 本身或其依賴閉包，注入會造成啟動期循環匯入"
            continue
        text = read_text(path)
        if text is None:
            target.status = "SKIP_UNREADABLE"
            target.reason = "無法以 utf-8 / cp950 解碼"
            continue
        if HOOK_MARK in text:
            target.status = "ALREADY"
            target.reason = "已有 hook，維持原狀（冪等）"
            continue
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError as exc:
            target.status = "SKIP_BROKEN"
            target.reason = "語法壞檔 L%s: %s —— 先修語法再談加速" % (exc.lineno, exc.msg)
            continue

        line = insertion_line(text, tree)
        lines = text.splitlines(keepends=True)
        candidate = "".join(lines[:line - 1]) + hook + "".join(lines[line - 1:])
        ok, why = verify_source(candidate, rel)
        if not ok:
            target.status = "REVERTED"
            target.reason = "注入後複驗失敗，已放棄本檔：%s" % why
            continue
        target.status = "INJECTED"
        target.line = line
        target.patched = candidate

    injected = [t for t in targets if t.status == "INJECTED"]

    # 落地
    backups: List[str] = []
    if commit:
        if not (binding.get("ok") and lazy.get("binds") and lazy.get("lazy")):
            print("執行期驗證未過，拒絕 --commit。")
            print("  lazy=%s" % json.dumps(lazy, ensure_ascii=False))
            print("  %s" % json.dumps(binding, ensure_ascii=False))
            return 1
        backup_root = out_dir / ("backup_%s" % stamp)
        for target in injected:
            relative = backup_root / target.rel
            relative.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(target.path), str(relative))
            backups.append(target.rel)
            write_utf8_nobom(target.path, target.patched)
        dest = str(root)
        mode = "COMMIT（已寫回原地，備份在 %s）" % backup_root
    else:
        if stage.exists():
            shutil.rmtree(stage)
        for target in injected:
            write_utf8_nobom(stage / target.rel, target.patched)
        dest = str(stage)
        mode = "DRY-RUN（只寫 staging）"

    after = fingerprint(root)
    counts: Dict[str, int] = {}
    for target in targets:
        counts[target.status] = counts.get(target.status, 0) + 1

    gates: List[Dict[str, str]] = [{
        "code": "C01", "title": "Celeritas API 探測到真實名稱",
        "status": "PASS" if probe["chosen"] else "FAIL",
        "detail": "選用 %s；頂層匯出共 %d 個"
                  % (", ".join(probe["chosen"]), len(probe["exports"]))}, {
        "code": "C02", "title": "執行期綁定驗證",
        "status": "PASS" if binding.get("ok") else "FAIL",
        "detail": "found=%s missing=%s %s"
                  % (binding.get("found"), binding.get("missing"),
                     binding.get("error", ""))}, {
        "code": "C03", "title": "啟動期循環匯入已排除",
        "status": "PASS",
        "detail": "Celeritas 依賴閉包 %d 個模組全部排除：%s"
                  % (len(closure), ", ".join(sorted(closure)[:6]))}, {
        "code": "C04", "title": "注入後全部通過 parse+compile",
        "status": "PASS" if counts.get("REVERTED", 0) == 0 else "FAIL",
        "detail": "注入 %d，複驗失敗放棄 %d" % (len(injected), counts.get("REVERTED", 0))}, {
        "code": "C05", "title": "語法壞檔未被注入",
        "status": "PASS" if counts.get("SKIP_BROKEN", 0) == 0 else "WARN",
        "detail": "%d 個語法壞檔跳過（需你本人先修語法）" % counts.get("SKIP_BROKEN", 0)}, {
        "code": "C07", "title": "hook 為惰性（import 期零成本）",
        "status": "PASS" if lazy.get("lazy") else "FAIL",
        "detail": "冷載入 %.3fs，VeritasCeleritas %s在 sys.modules 中；"
                  "非惰性代表每支腳本啟動都先付 Celeritas 的 import 成本"
                  % (lazy.get("cold_seconds", 0),
                     "不" if lazy.get("lazy") else "已")}, {
        "code": "C08", "title": "hook 真的綁得到（非靜默空轉）",
        "status": "PASS" if lazy.get("binds") else "FAIL",
        "detail": "首次取用耗時 %.3fs；%s"
                  % (lazy.get("warm_seconds", 0),
                     lazy.get("error") or "取用 _VIA.<name> 成功")}, {
        "code": "C09", "title": "實際加速範圍（stub 揭露）",
        "status": "PASS" if binding.get("real_libs") else "WARN",
        "detail": "Celeritas %s，__all__ %d 個匯出，真實函式庫 %s；缺: %s"
                  % (binding.get("version", "?"), binding.get("exports", 0),
                     binding.get("real_libs"),
                     ", ".join(binding.get("missing_libs", [])[:10]) or "無")}, {
        "code": "C06", "title": "dry-run 未寫入母系統",
        "status": "PASS" if (commit or before == after) else "FAIL",
        "detail": ("COMMIT 模式：已寫回 %d 檔，備份 %d 檔" % (len(injected), len(backups))
                   if commit else
                   "前 %d 檔 %d bytes / 後 %d 檔 %d bytes"
                   % (before[0], before[1], after[0], after[1]))}]

    ctx = {
        "stamp": stamp, "generated": now(), "root": str(root), "dest": dest,
        "mode": mode, "gates": gates, "targets": targets, "probe": probe,
        "binding": binding, "lazy": lazy, "hook": hook,
        "cards": [("py 總數", "%d" % len(targets)),
                  ("已注入", "%d" % len(injected)),
                  ("已有 hook", "%d" % counts.get("ALREADY", 0)),
                  ("依賴閉包排除", "%d" % counts.get("SKIP_BOOTSTRAP", 0)),
                  ("語法壞檔", "%d" % counts.get("SKIP_BROKEN", 0)),
                  ("放棄", "%d" % counts.get("REVERTED", 0))],
    }

    html_path = out_dir / ("VIA_CeleritasInject_%s.html" % stamp)
    write_utf8_nobom(html_path, build_html(ctx))
    write_utf8_nobom(out_dir / ("via_celeritas_inject_%s.json" % stamp), json.dumps({
        "urn": URN_SELF, "version": VERSION, "generated_at": now(),
        "root": str(root), "celeritas": str(celeritas), "mode": mode,
        "probe": probe, "binding": binding, "lazy": lazy, "gates": gates,
        "closure": sorted(closure), "backups": backups,
        "targets": [{"rel": t.rel, "status": t.status, "line": t.line,
                     "reason": t.reason} for t in targets],
    }, ensure_ascii=False, indent=2))

    print("=" * 68)
    print(" VeritasCeleritas 導入 %s %s · %s" % (URN_SELF, VERSION, mode))
    print("=" * 68)
    for gate in gates:
        print("%-5s %-28s %-5s %s" % (gate["code"], gate["title"], gate["status"],
                                      gate["detail"][:84]))
    print("-" * 68)
    print(" 報告 %s" % html_path)
    return 0 if all(g["status"] != "FAIL" for g in gates) else 2


def _selftest() -> int:
    """建假樹驗證：API 探測、循環閉包排除、冪等、壞檔跳過、無 API 時拒絕。"""
    tmp = Path(tempfile.mkdtemp(prefix="celer_"))
    failures: List[str] = []
    try:
        root = tmp / "mother"
        sup = root / "supportive modules"
        sup.mkdir(parents=True)

        # Celeritas 匯入本地 VIA_Bootstrap -> 兩者都必須排除
        (sup / "VeritasCeleritas.py").write_text(
            "import VIA_Bootstrap\n\n__all__ = ['_LazyModule', '_LazyAttr']\n\n"
            "class _LazyModule:\n    pass\n\nclass _LazyAttr:\n    pass\n",
            encoding="utf-8")
        (sup / "VIA_Bootstrap.py").write_text("VALUE = 1\n", encoding="utf-8")

        def w(rel: str, text: str) -> None:
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

        w("plain.py", "def a():\n    return 1\n")
        w("withdoc.py", '"""doc."""\nfrom __future__ import annotations\nimport os\n')
        w("broken.py", "def z(:\n    pass\n")
        w("sub/deep.py", "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\nX = 1\n")

        celeritas = sup / "VeritasCeleritas.py"
        code = run(root, celeritas, tmp / "out", tmp / "stage",
                   sys.executable, commit=False)
        plan = json.loads(sorted((tmp / "out").glob("via_celeritas_inject_*.json"))[-1]
                          .read_text(encoding="utf-8"))
        status = {t["rel"]: t["status"] for t in plan["targets"]}

        if plan["probe"]["chosen"] != ["_LazyModule", "_LazyAttr"]:
            failures.append("API 探測錯誤：%s" % plan["probe"]["chosen"])
        if not plan["binding"]["ok"]:
            failures.append("執行期綁定未過：%s" % plan["binding"])
        cel = str(Path("supportive modules") / "VeritasCeleritas.py")
        boot = str(Path("supportive modules") / "VIA_Bootstrap.py")
        if status.get(cel) != "SKIP_BOOTSTRAP":
            failures.append("Celeritas 自己沒被排除：%s" % status.get(cel))
        if status.get(boot) != "SKIP_BOOTSTRAP":
            failures.append("依賴閉包沒被排除（會循環匯入）：%s" % status.get(boot))
        if status.get("broken.py") != "SKIP_BROKEN":
            failures.append("語法壞檔未跳過")
        for rel in ("plain.py", "withdoc.py", str(Path("sub") / "deep.py")):
            if status.get(rel) != "INJECTED":
                failures.append("%s 未注入：%s" % (rel, status.get(rel)))

        # from __future__ 前面不得多出語句；shebang 必須留在第一行
        body = (tmp / "stage" / "withdoc.py").read_text(encoding="utf-8")
        tree = ast.parse(body)
        idx = [i for i, n in enumerate(tree.body)
               if isinstance(n, ast.ImportFrom) and n.module == "__future__"]
        if not idx:
            failures.append("__future__ 不見了")
        else:
            for node in tree.body[:idx[0]]:
                is_doc = (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
                          and isinstance(node.value.value, str))
                if not is_doc:
                    failures.append("__future__ 前多了 %s" % type(node).__name__)
        deep = (tmp / "stage" / "sub" / "deep.py").read_text(encoding="utf-8")
        if not deep.startswith("#!/usr/bin/env python3"):
            failures.append("shebang 不在第一行了")
        for name in ("plain.py", "withdoc.py"):
            ok, why = verify_source((tmp / "stage" / name).read_text(encoding="utf-8"), name)
            if not ok:
                failures.append("%s 注入後編譯失敗 %s" % (name, why))

        # 冪等：把 staging 當來源再跑一次，應全部 ALREADY
        shutil.copy2(str(celeritas), str(tmp / "stage" / "VeritasCeleritas.py"))
        run(tmp / "stage", tmp / "stage" / "VeritasCeleritas.py",
            tmp / "out2", tmp / "stage2", sys.executable, commit=False)
        plan2 = json.loads(sorted((tmp / "out2").glob("via_celeritas_inject_*.json"))[-1]
                           .read_text(encoding="utf-8"))
        again = [t["rel"] for t in plan2["targets"] if t["status"] == "INJECTED"]
        if again:
            failures.append("重跑又注入了 %s（不冪等）" % again)

        # 沒有可用 API 時必須拒絕，而不是掛半套
        empty_root = tmp / "empty"
        empty_sup = empty_root / "supportive modules"
        empty_sup.mkdir(parents=True)
        (empty_sup / "VeritasCeleritas.py").write_text("PI = 3\n", encoding="utf-8")
        (empty_root / "x.py").write_text("Y = 1\n", encoding="utf-8")
        refused = run(empty_root, empty_sup / "VeritasCeleritas.py",
                      tmp / "out3", tmp / "stage3", sys.executable, commit=False)
        if refused == 0:
            failures.append("無可用 API 時竟然沒拒絕")
        if (tmp / "stage3" / "x.py").exists():
            failures.append("無可用 API 時仍然改了檔案")
        if code not in (0, 2):
            failures.append("非預期離開碼 %d" % code)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print()
    if failures:
        for item in failures:
            print("FAIL  " + item)
        return 1
    print("PASS  VIA_CeleritasInjector %s 自我測試全過" % VERSION)
    print("      API 探測 / 執行期綁定 / 依賴閉包排除 / __future__ 保序 /")
    print("      shebang 保序 / 壞檔跳過 / 冪等 / 無 API 時拒絕注入")
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="VIA_CeleritasInjector.py",
        description="%s %s 將 VeritasCeleritas 導入母系統所有 .py" % (URN_SELF, VERSION))
    parser.add_argument("--root", default="")
    parser.add_argument("--celeritas", default="")
    parser.add_argument("--out", default="")
    parser.add_argument("--stage", default="")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--commit", action="store_true",
                        help="寫回原地（每檔先備份）。綁定驗證未過則拒絕。")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)

    if args.selftest or not args.root:
        return _selftest()
    root = Path(args.root)
    if not root.is_dir():
        print("找不到母系統：%s" % root)
        return 1
    celeritas = Path(args.celeritas) if args.celeritas else (
        root / "supportive modules" / "VeritasCeleritas.py")
    out_dir = Path(args.out) if args.out else Path(
        r"C:\VeritasIntelligenceAnalytics\CGE\_celeritas")
    stage = Path(args.stage) if args.stage else Path(
        r"C:\VeritasIntelligenceAnalytics\CGE\_celeritas_stage")
    return run(root, celeritas, out_dir, stage, args.python, args.commit)


if __name__ == "__main__":
    sys.exit(main())
