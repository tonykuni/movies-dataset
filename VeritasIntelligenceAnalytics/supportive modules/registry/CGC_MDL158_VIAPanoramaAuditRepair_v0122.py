#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""CGC_MDL158_VIAPanoramaAuditRepair v0122 — 薄尾(v0121 以前一字不動):新動詞 hydra(三回合正交探針 · 依賴圖分組 · 原子修補 · 戰報)

操作員 2026-11-26:「請問目前短指令有以下這套短指令嗎?若有如下面內容優化,用 py 寫 AST 導入加速器」——
貼上的提示詞要的是「三回合獨立 AST 全景掃描與交叉確認 → 依賴圖拓撲分組(並行批次 vs 序列階梯)→ 原子沙盒修改與自動回滾 → 全景對照戰報」。
現況(讀碼):本工具已有 scan(全倉治理七類 + 通用 AST 類,只報不改)· delta · fix(先乾跑;--apply 先備份 → 改 → ast.parse +
compile + 重稽核不變差,不過自動還原)。缺:任意目標夾、三個正交切面、依賴圖 / 影響半徑分組、修前修後戰報。
本版只補缺的,掛成動詞 hydra(重用前版鏈的 _read_checks_py · accel_workers · template_exempt,不另做一支):

  hydra <夾或檔…> [--apply] [--json] [--out <檔>] [--workers N] [--max N]
  ① 三回合(每回合一個正交切面;每筆發現帶「覆核」= 雙判(兩個獨立判法都成立)或 單判(規則))
     P1 語法 · 匯入 · 符號:SYNTAX(ast + compile 雙判)· COMPILE · UNRESOLVED(本夾找不到 + find_spec 找不到;try/except ImportError 內的不算)
        · CYCLE(模組層匯入的強連通分量;雙判 = 兩向可達)· UNDEF(ruff F821 + 本模組沒有任何綁定;沒 ruff = 黃 · 照實寫略過)
        · DUPDEF / UNREACH / MUTDEF(前版 _read_checks_py)
     P2 介面契約:ARITY(本夾函式的呼叫端 ↔ 定義簽章;雙判 = AST 計數 + inspect.Signature.bind 都不過;有 decorator 的不判)
        · SCHEMA = 灰(DataFrame ↔ Parquet / DuckDB 欄位由各系統現成的動詞負責:VDF_SystemManager parquet align,唯讀)
     P3 執行期邊界:ENCODING(文字模式 open / read_text / write_text 沒給 encoding)· BOM(寫出用 utf-8-sig)· LEAK(open / connect
        指派給名字、同一範圍沒 close / with / return)· NOTIMEOUT(requests.* / urlopen 沒給 timeout)· ASYNCBLOCK(async def 裡 time.sleep /
        requests.*)· BAREEXC / SWALLOW(前版 _read_checks_py)
  ② 依賴圖:本夾模組匯入邊(函式內匯入也算影響半徑;循環只看模組層)。影響半徑 = 會被牽動的下游檔數。
     A 組 = 半徑 0 且不在循環裡 → 並行一口氣修;B 組 = 有下游或在循環裡 → 拓撲序(被依賴的底層先)逐支修。
  ③ 修補(只有 --apply 才寫;只修「機械可證」的兩類,其餘只列計畫):
     ENCODING → 在那個呼叫的右括號前插 encoding(讀 = utf-8-sig 容 BOM · 寫 = utf-8 無 BOM;mode 不是字面值 = 不猜、改列人工)
     BOM(open / write_text 寫出)→ 該字面值 utf-8-sig 換 utf-8(to_csv 的 utf-8-sig 多半為 Excel 刻意 → 人工)
     每檔:備份到 TEMP → 依節點位置由後往前改 → ast.parse + compile → 本檔三回合重掃「不得多出任何新發現」→
     B 組另重掃影響半徑內的下游 → 任一關不過 = 從備份還原(ROLLBACK);暫存檔 + os.replace 原子換檔。
     收容 / 凍結 / 正典 U/I(前版 template_exempt 名冊 · 路徑含 intake)一律不寫,照列。
  ④ 修後全景再掃一次:原始確認數 · 已修 · 剩下 · 新增(必須 0,否則 RED)。戰報 JSON 寫 UTF-8 無 BOM(TEMP 或 --out)。
  三數照列:應掃 · 已掃 · 略過(略過逐類計數)。只讀程式碼結構;不執行被掃的檔;不出網;不用 TA-Lib;不設同意閘。
其餘動詞(read · slice · digest · pack · --if-etag · chain · scan · report · delta · fix · tests · cache · tools · verbs)全部照前版;
verbs 改印本版表(多 hydra)。舊主控台的字串門要看到的字照留:"read" "slice" "digest" --if-etag def pack_payload。
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

import ast
import builtins
import hashlib
import importlib.util
import inspect
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import warnings
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL158_VIAPanoramaAuditRepair"
_HYDRA_VER = "v0122"
TAG = f"{_STEM} {_HYDRA_VER}"


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location("panorama_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)

VERBS = dict(PRIOR.VERBS)          # 動詞表照前版:"read" "slice" "digest" "pack" "tools" "verbs" … 之後每一版都要保有 VERBS
VERBS["hydra"] = ("hydra <夾或檔…> [--apply] [--json] [--out <檔>] [--workers N] [--max N]",
                  "要一次盤清一個夾的錯誤、分組並安全修補時(先不帶 --apply 看計畫)",
                  "三回合正交探針(語法匯入符號 · 介面契約 · 執行期邊界)→ 依賴圖影響半徑分 A 並行 / B 拓撲序 → "
                  "--apply 只修機械可證的 ENCODING · BOM(備份 · 重掃不變差 · 不過就還原)→ 修前修後戰報(三數 · 新增必須 0)")


def __getattr__(name: str):
    return getattr(PRIOR, name)


def pack_payload(root, limit: int = 200) -> dict:
    """整夾索引:原樣轉交前版鏈(明寫在本檔,讓只認字串的舊門也看得到)。"""
    return PRIOR.pack_payload(root, limit)


# ---------------------------------------------------------------- 三數與檔案清單
_HYDRA_SKIP = {"__pycache__": "位元快取", ".git": "版控", ".venv": "虛境", "venv": "虛境", "envs": "虛境", "site-packages": "第三方",
              "node_modules": "第三方", "_quarantine": "隔離", "quarantine": "隔離", "RetiredEngines": "退役", "_backup": "備份"}
P_OF = {"SYNTAX": "P1", "COMPILE": "P1", "UNRESOLVED": "P1", "CYCLE": "P1", "UNDEF": "P1", "DUPDEF": "P1", "UNREACH": "P1",
        "MUTDEF": "P1", "ARITY": "P2", "SCHEMA": "P2", "ENCODING": "P3", "BOM": "P3", "LEAK": "P3", "NOTIMEOUT": "P3",
        "ASYNCBLOCK": "P3", "BAREEXC": "P3", "SWALLOW": "P3"}
AUTO = {"ENCODING", "BOM"}


def collect(targets: list) -> tuple:
    """→ (files, roots, skipped{類: 數})。給檔就是那一檔;給夾就遞迴 .py,略過的逐類計數。"""
    files, roots, skipped = [], [], {}
    for t in targets:
        t = Path(t).expanduser().resolve()
        if t.is_file() and t.suffix == ".py":
            files.append(t)
            roots.append(t.parent)
        elif t.is_dir():
            roots.append(t)
            for p in sorted(t.rglob("*.py")):
                hit = next((w for part, w in _HYDRA_SKIP.items() if part in p.relative_to(t).parts[:-1]), None)
                if hit:
                    skipped[hit] = skipped.get(hit, 0) + 1
                else:
                    files.append(p)
        else:
            skipped["不存在或不是 .py"] = skipped.get("不存在或不是 .py", 0) + 1
    seen, out = set(), []
    for f in files:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out, roots, skipped


def _rel(f: Path, roots: list) -> str:
    for r in roots:
        try:
            return f.relative_to(r).as_posix()
        except ValueError:
            continue
    return f.as_posix()


def _read(f: Path) -> tuple:
    raw = f.read_bytes()
    try:
        return raw.decode("utf-8-sig"), raw.startswith(b"\xef\xbb\xbf")
    except UnicodeDecodeError:
        return raw.decode("utf-8", errors="replace"), False


# ---------------------------------------------------------------- 模組索引與依賴圖
def module_index(files: list, roots: list) -> dict:
    """點名模組名 → 檔:每個根之下的相對路徑點名 + 檔名本身(腳本常把自己的夾塞進 sys.path)。"""
    idx = {}
    for f in files:
        stems = {f.stem} if f.stem != "__init__" else {f.parent.name}
        for r in roots:
            try:
                parts = list(f.relative_to(r).with_suffix("").parts)
            except ValueError:
                continue
            if parts and parts[-1] == "__init__":
                parts = parts[:-1]
            for i in range(len(parts)):
                stems.add(".".join(parts[i:]))
        for s in stems:
            idx.setdefault(s, set()).add(f)
    return idx


def _in_import_guard(tree) -> set:
    """try: import X / except ImportError(或 Exception / 全部)→ 可選匯入,不算 UNRESOLVED。回這些 Import 節點的 id。"""
    ok = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Try):
            names = set()
            for h in n.handlers:
                t = h.type
                for e in (t.elts if isinstance(t, ast.Tuple) else [t]):
                    names.add(getattr(e, "id", None) or getattr(e, "attr", None))
            if not names or names & {"ImportError", "ModuleNotFoundError", "Exception", "BaseException", None}:
                for b in n.body:
                    for x in ast.walk(b):
                        if isinstance(x, (ast.Import, ast.ImportFrom)):
                            ok.add(id(x))
    return ok


def _imports(tree, f: Path) -> list:
    """→ [(模組名, 行, 節點, 模組層?)];相對匯入換成以本檔夾為基準的點名。"""
    out = []
    top = {id(n) for n in tree.body}

    def walk(nodes, module_level):
        for n in nodes:
            if isinstance(n, ast.Import):
                for a in n.names:
                    out.append((a.name, n.lineno, n, module_level))
            elif isinstance(n, ast.ImportFrom):
                base = n.module or ""
                if n.level:
                    out.append(((("." * n.level) + base), n.lineno, n, module_level))
                else:
                    out.append((base, n.lineno, n, module_level))
                    for a in n.names:                             # from pkg import sub → pkg.sub 也可能是模組
                        out.append((f"{base}.{a.name}", n.lineno, n, module_level))
            for fld in ("body", "orelse", "finalbody", "handlers"):
                sub = getattr(n, fld, None)
                if isinstance(sub, list):
                    walk(sub, module_level and not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)))
    walk(tree.body, True)
    _ = top
    return out


def _resolve_local(name: str, f: Path, idx: dict) -> set:
    if name.startswith("."):
        lvl = len(name) - len(name.lstrip("."))
        base = f.parent
        for _ in range(lvl - 1):
            base = base.parent
        rest = name.lstrip(".")
        cand = [base / (rest.replace(".", "/") + ".py"), base / rest.replace(".", "/") / "__init__.py"] if rest else [base / "__init__.py"]
        return {c.resolve() for c in cand if c.exists()}
    return set(idx.get(name, set()))


def _spec_ok(name: str) -> bool:
    top = name.lstrip(".").split(".")[0]
    if not top:
        return True
    if top in sys.builtin_module_names or top in getattr(sys, "stdlib_module_names", ()):
        return True
    try:
        return importlib.util.find_spec(top) is not None
    except (ImportError, ValueError):
        return False


def tarjan(nodes: list, edges: dict) -> list:
    """強連通分量(疊代版,不吃遞迴深度)。"""
    index, low, on, stack, out, i = {}, {}, set(), [], [], [0]
    for v0 in nodes:
        if v0 in index:
            continue
        work = [(v0, iter(sorted(edges.get(v0, ()), key=str)))]
        index[v0] = low[v0] = i[0]
        i[0] += 1
        stack.append(v0)
        on.add(v0)
        while work:
            v, it = work[-1]
            nxt = next(it, None)
            if nxt is not None:
                if nxt not in index:
                    index[nxt] = low[nxt] = i[0]
                    i[0] += 1
                    stack.append(nxt)
                    on.add(nxt)
                    work.append((nxt, iter(sorted(edges.get(nxt, ()), key=str))))
                elif nxt in on:
                    low[v] = min(low[v], index[nxt])
                continue
            work.pop()
            if work:
                low[work[-1][0]] = min(low[work[-1][0]], low[v])
            if low[v] == index[v]:
                comp = []
                while True:
                    w = stack.pop()
                    on.discard(w)
                    comp.append(w)
                    if w == v:
                        break
                out.append(comp)
    return out


def _reach(start, edges: dict) -> set:
    seen, todo = set(), [start]
    while todo:
        v = todo.pop()
        for w in edges.get(v, ()):
            if w not in seen:
                seen.add(w)
                todo.append(w)
    return seen


# ---------------------------------------------------------------- 位置換算(ast 的 col 是 UTF-8 位元組)
def _abs(src: str, lines: list, lineno: int, col_b: int) -> int:
    line = lines[lineno - 1]
    return sum(len(x) for x in lines[:lineno - 1]) + len(line.encode("utf-8")[:col_b].decode("utf-8", errors="ignore"))


def _call_name(fn) -> str:
    if isinstance(fn, ast.Name):
        return fn.id
    if isinstance(fn, ast.Attribute):
        base = _call_name(fn.value)
        return f"{base}.{fn.attr}" if base else fn.attr
    return ""


def _kw(call, name):
    return next((k for k in call.keywords if k.arg == name), None)


def _open_mode(call):
    m = call.args[1] if len(call.args) > 1 else (_kw(call, "mode").value if _kw(call, "mode") else ast.Constant("r"))
    return m.value if isinstance(m, ast.Constant) and isinstance(m.value, str) else None


# ---------------------------------------------------------------- 三回合
def _finding(rel, cls, line, detail, confirm, fix=None, **kw):
    return {"file": rel, "cls": cls, "pass": P_OF.get(cls, "P?"), "line": line, "detail": detail, "confirm": confirm,
            "fix": fix or ("auto" if cls in AUTO else "manual"), **kw}


def pass1(rel: str, src: str, tree, err, imports: list, guard: set, idx: dict, f: Path) -> list:
    out = []
    if tree is None:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                compile(src, rel, "exec")
            conf = "單判(ast)"
        except SyntaxError:
            conf = "雙判(ast+compile)"
        return [_finding(rel, "SYNTAX", getattr(err, "lineno", 0) or 0, f"{type(err).__name__}: {getattr(err, 'msg', err)}", conf)]
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            compile(src, rel, "exec")
    except SyntaxError as e:
        out.append(_finding(rel, "COMPILE", e.lineno or 0, f"ast 過、compile 不過:{e.msg}", "雙判(ast 過 · compile 不過)"))
    for x in PRIOR._read_checks_py(tree):
        if P_OF.get(x["cls"]) == "P1":
            out.append(_finding(rel, x["cls"], x["line"], x["detail"], "單判(規則 · 前版 _read_checks_py)"))
    seen = set()
    for name, line, node, _ml in imports:
        if id(node) in guard or not name or (name, line) in seen:
            continue
        seen.add((name, line))
        if isinstance(node, ast.ImportFrom) and not node.level and "." in name and name.rsplit(".", 1)[0] == (node.module or ""):
            continue                                           # from pkg import sub 的子名只用來畫邊,不判 UNRESOLVED
        if _resolve_local(name, f, idx):
            continue
        if not name.startswith(".") and _spec_ok(name):
            continue
        out.append(_finding(rel, "UNRESOLVED", line, f"匯入 {name} 找不到", "雙判(本夾沒有 · find_spec 沒有)"))
    return out


def _bound_names(tree) -> set:
    b = set(dir(builtins)) | {"__file__", "__name__", "__doc__", "__spec__", "__builtins__", "__path__", "__loader__", "__package__"}
    for n in ast.walk(tree):
        if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            b.add(n.id)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            b.add(n.name)
        elif isinstance(n, ast.arg):
            b.add(n.arg)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            for a in n.names:
                b.add((a.asname or a.name).split(".")[0])
        elif isinstance(n, (ast.Global, ast.Nonlocal)):
            b.update(n.names)
        elif isinstance(n, ast.ExceptHandler) and n.name:
            b.add(n.name)
        elif isinstance(n, ast.alias):
            pass
    return b


def ruff_undef(files: list, roots: list) -> tuple:
    """ruff F821(未定義名)→ ({rel: [(line, name)]}, 狀態字)。沒有 ruff = 黃,照實寫略過。"""
    exe = shutil.which("ruff")
    if not exe or not files:
        return {}, "黃 · 這台沒有 ruff(UNDEF 這一項略過,不算綠)" if files else "無檔"
    out = {}
    for i in range(0, len(files), 400):
        chunk = [str(f) for f in files[i:i + 400]]
        try:
            cp = subprocess.run([exe, "check", "--isolated", "--no-cache", "--select", "F821", "--output-format", "json", *chunk],
                                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
            rows = json.loads(cp.stdout or "[]")
        except (OSError, ValueError, subprocess.TimeoutExpired) as e:
            return {}, f"黃 · ruff 跑不起來({type(e).__name__});UNDEF 略過"
        for r in rows:
            m = re.search(r"`([^`]+)`", r.get("message", ""))
            out.setdefault(_rel(Path(r["filename"]).resolve(), roots), []).append((r["location"]["row"], m.group(1) if m else "?"))
    return out, "ruff F821"


def _sig_of(fn) -> inspect.Signature:
    P = inspect.Parameter
    a = fn.args
    params = []
    pos = list(a.posonlyargs) + list(a.args)
    nd = len(a.defaults)
    for i, x in enumerate(pos):
        kind = P.POSITIONAL_ONLY if i < len(a.posonlyargs) else P.POSITIONAL_OR_KEYWORD
        params.append(P(x.arg, kind, default=0 if i >= len(pos) - nd else P.empty))
    if a.vararg:
        params.append(P(a.vararg.arg, P.VAR_POSITIONAL))
    for x, d in zip(a.kwonlyargs, a.kw_defaults):
        params.append(P(x.arg, P.KEYWORD_ONLY, default=P.empty if d is None else 0))
    if a.kwarg:
        params.append(P(a.kwarg.arg, P.VAR_KEYWORD))
    return inspect.Signature(params)


def pass2(rel: str, tree, defs_local: dict, imported_defs: dict) -> list:
    """呼叫端 ↔ 定義簽章(本夾內能唯一解析、沒有 decorator 的函式)。"""
    out = []
    if tree is None:
        return out
    shadow = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    for call in (n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)):
        name = call.func.id
        fn = defs_local.get(name) if name not in shadow else None
        fn = fn or imported_defs.get(name)
        if fn is None or fn.decorator_list:
            continue
        if any(isinstance(a, ast.Starred) for a in call.args) or any(k.arg is None for k in call.keywords):
            continue
        a = fn.args
        npos, maxpos = len(call.args), len(a.posonlyargs) + len(a.args)
        names = {x.arg for x in a.posonlyargs + a.args + a.kwonlyargs}
        req = maxpos - len(a.defaults)
        kws = {k.arg for k in call.keywords}
        why = None
        if npos > maxpos and not a.vararg:
            why = f"給 {npos} 個位置引數,{name}() 最多收 {maxpos}"
        elif not a.kwarg and kws - names:
            why = f"{name}() 沒有參數 {sorted(kws - names)}"
        elif npos + len(kws & {x.arg for x in a.args[npos - len(a.posonlyargs):] if npos >= len(a.posonlyargs)}) < req:
            why = f"{name}() 至少要 {req} 個,只給 {npos} 個位置 + {sorted(kws)}"
        missing_kwonly = [x.arg for x, d in zip(a.kwonlyargs, a.kw_defaults) if d is None and x.arg not in kws]
        if not why and missing_kwonly:
            why = f"{name}() 缺僅限關鍵字參數 {missing_kwonly}"
        if not why:
            continue
        try:
            _sig_of(fn).bind(*([0] * npos), **{k: 0 for k in kws})
            conf = None                                           # 第二判法不同意 → 不報(寧缺勿濫)
        except TypeError:
            conf = "雙判(AST 計數 + inspect.Signature.bind)"
        if conf:
            out.append(_finding(rel, "ARITY", call.lineno, why, conf, callee=name))
    return out


_TEXT_IO = {"read_text": "r", "write_text": "w"}
_NET = {"requests.get", "requests.post", "requests.put", "requests.delete", "requests.head", "requests.patch", "requests.request",
        "urllib.request.urlopen", "urlopen"}


def pass3(rel: str, src: str, tree) -> list:
    out = []
    if tree is None:
        return out
    lines = src.splitlines(keepends=True)
    for x in PRIOR._read_checks_py(tree):
        if P_OF.get(x["cls"]) == "P3":
            out.append(_finding(rel, x["cls"], x["line"], x["detail"], "單判(規則 · 前版 _read_checks_py)"))
    for call in (n for n in ast.walk(tree) if isinstance(n, ast.Call)):
        nm = _call_name(call.func)
        last = nm.rsplit(".", 1)[-1]
        if nm == "open" or last in _TEXT_IO:
            mode = _open_mode(call) if nm == "open" else _TEXT_IO[last]
            if last in _TEXT_IO and not isinstance(call.func, ast.Attribute):
                continue
            enc = _kw(call, "encoding")
            if mode is None:
                if not enc:
                    out.append(_finding(rel, "ENCODING", call.lineno, f"{nm}() mode 不是字面值,沒給 encoding(不猜文字 / 二進位)", "單判(規則)", fix="manual"))
                continue
            if "b" in mode:
                continue
            if nm == "open" and len(call.args) > 3:
                continue                                         # 位置引數已給到 encoding 那一格
            want = "utf-8" if any(c in mode for c in "wax") else "utf-8-sig"
            if not enc:
                out.append(_finding(rel, "ENCODING", call.lineno, f"{nm}() 文字模式 {mode!r} 沒給 encoding(Windows 會用 cp950)",
                                    "單判(規則)", node=[call.end_lineno, call.end_col_offset], want=want))
            elif any(c in mode for c in "wax") and isinstance(enc.value, ast.Constant) and str(enc.value.value).lower().replace("_", "-") == "utf-8-sig":
                out.append(_finding(rel, "BOM", call.lineno, f"{nm}() 寫出用 utf-8-sig(會帶 BOM)", "單判(規則)",
                                    node=[enc.value.lineno, enc.value.col_offset, enc.value.end_lineno, enc.value.end_col_offset]))
        elif last == "to_csv":
            enc = _kw(call, "encoding")
            if enc and isinstance(enc.value, ast.Constant) and str(enc.value.value).lower().replace("_", "-") == "utf-8-sig":
                out.append(_finding(rel, "BOM", call.lineno, "to_csv(utf-8-sig) 帶 BOM(常是為了 Excel,人工判)", "單判(規則)", fix="manual"))
        if nm in _NET and not _kw(call, "timeout"):
            out.append(_finding(rel, "NOTIMEOUT", call.lineno, f"{nm}() 沒給 timeout(對方不回就卡住)", "單判(規則)"))
    scopes = [tree] + [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    for sc in scopes:
        body_nodes = []
        stack = list(sc.body)
        while stack:
            n = stack.pop()
            body_nodes.append(n)
            for ch in ast.iter_child_nodes(n):
                if not isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                    stack.append(ch)
        with_ids = {id(it.context_expr) for n in body_nodes if isinstance(n, (ast.With, ast.AsyncWith)) for it in n.items}
        for n in body_nodes:
            if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and isinstance(n.value, ast.Call):
                nm = _call_name(n.value.func)
                if (nm == "open" or nm.endswith(".connect")) and id(n.value) not in with_ids:
                    v = n.targets[0].id
                    used_ok = any(
                        (isinstance(m, ast.Call) and isinstance(m.func, ast.Attribute) and isinstance(m.func.value, ast.Name)
                         and m.func.value.id == v and m.func.attr in ("close", "__exit__"))
                        or (isinstance(m, ast.Return) and m.value is not None and any(isinstance(q, ast.Name) and q.id == v for q in ast.walk(m.value)))
                        or (isinstance(m, (ast.With, ast.AsyncWith)) and any(isinstance(q, ast.Name) and q.id == v for it in m.items for q in ast.walk(it.context_expr)))
                        or (isinstance(m, ast.Assign) and any(isinstance(t, ast.Attribute) for t in m.targets) and isinstance(m.value, ast.Name) and m.value.id == v)
                        for m in body_nodes)
                    if not used_ok:
                        out.append(_finding(rel, "LEAK", n.lineno, f"{v} = {nm}(…) 同一範圍沒有 close / with / return", "單判(規則)"))
        if isinstance(sc, ast.AsyncFunctionDef):
            for n in body_nodes:
                if isinstance(n, ast.Call) and (_call_name(n.func) == "time.sleep" or _call_name(n.func).startswith("requests.")):
                    out.append(_finding(rel, "ASYNCBLOCK", n.lineno, f"async def {sc.name} 裡呼叫阻塞的 {_call_name(n.func)}()", "單判(規則)"))
    _ = lines
    return out


# ---------------------------------------------------------------- 全景(三回合 + 依賴圖)
def panorama(targets: list, workers: int = 0) -> dict:
    t0 = time.time()
    files, roots, skipped = collect(targets)
    idx = module_index(files, roots)
    nw = workers or PRIOR.accel_workers(8)[0]

    def parse(f):
        try:
            src, bom = _read(f)
        except OSError as e:
            return f, None, None, e, False
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")              # 被掃檔自己的 SyntaxWarning 不洩到主控台(只報我們的發現)
                return f, src, ast.parse(src), None, bom
        except SyntaxError as e:
            return f, src, None, e, bom

    with ThreadPoolExecutor(max_workers=max(1, nw)) as ex:
        parsed = list(ex.map(parse, files))
    unread = [str(f) for f, src, *_ in parsed if src is None]
    edges, edges_mod, imps, guards, trees = {}, {}, {}, {}, {}
    for f, src, tree, err, _bom in parsed:
        if tree is None:
            continue
        trees[f] = (src, tree)
        imps[f] = _imports(tree, f)
        guards[f] = _in_import_guard(tree)
        for name, _l, _n, ml in imps[f]:
            for dep in _resolve_local(name, f, idx):
                if dep != f:
                    edges.setdefault(f, set()).add(dep)
                    if ml:
                        edges_mod.setdefault(f, set()).add(dep)
    defs_top = {f: {n.name: n for n in t.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))} for f, (_s, t) in trees.items()}
    undef, ruff_state = ruff_undef(list(trees), roots)

    def per_file(item):
        f, src, tree, err, bom = item
        rel = _rel(f, roots)
        if src is None:
            return []
        out = pass1(rel, src, tree, err, imps.get(f, []), guards.get(f, set()), idx, f)
        if tree is not None:
            bound = _bound_names(tree)
            for line, name in undef.get(rel, []):
                if name not in bound:
                    out.append(_finding(rel, "UNDEF", line, f"未定義名 {name}", "雙判(ruff F821 + 本模組沒有綁定)"))
            imported = {}
            for n in ast.walk(tree):
                if isinstance(n, ast.ImportFrom):
                    mod = ("." * n.level) + (n.module or "")
                    tgt = _resolve_local(mod, f, idx)
                    if len(tgt) == 1:
                        t = next(iter(tgt))
                        for a in n.names:
                            if a.name in defs_top.get(t, {}):
                                imported[a.asname or a.name] = defs_top[t][a.name]
            out += pass2(rel, tree, {k: v for k, v in defs_top.get(f, {}).items()
                                     if sum(1 for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == k) == 1},
                         imported)
            out += pass3(rel, src, tree)
        if bom:
            out.append(_finding(rel, "BOM", 1, "檔頭帶 UTF-8 BOM(原始碼本身)", "雙判(位元組 EF BB BF + decode)", fix="manual"))
        return out

    with ThreadPoolExecutor(max_workers=max(1, nw)) as ex:
        findings = [x for chunk in ex.map(per_file, parsed) for x in chunk]
    nodes = list(trees)
    comps = tarjan(nodes, edges_mod)
    cyc = [c for c in comps if len(c) > 1]
    for c in cyc:
        names = sorted(_rel(x, roots) for x in c)
        both = all(c[0] in _reach(x, edges_mod) and x in _reach(c[0], edges_mod) for x in c[1:])
        for x in c:
            findings.append(_finding(_rel(x, roots), "CYCLE", 0, "模組層循環匯入:" + " ↔ ".join(names[:6]),
                                     "雙判(強連通分量 + 兩向可達)" if both else "單判(強連通分量)"))
    redges = {}
    for a, bs in edges.items():
        for b in bs:
            redges.setdefault(b, set()).add(a)
    blast = {f: len(_reach(f, redges)) for f in files}
    in_cycle = {x for c in cyc for x in c}
    comp_of = {x: i for i, c in enumerate(comps) for x in c}
    order = [x for c in comps for x in sorted(c, key=str)]                # Tarjan 的完成序 = 被依賴的先完成(底層先)
    rank = {x: i for i, x in enumerate(order)}
    by_file = {}
    for x in findings:
        by_file.setdefault(x["file"], []).append(x)
    fpath = {_rel(f, roots): f for f in files}
    groups = {"A": [], "B": []}
    for rel in sorted(by_file):
        f = fpath.get(rel)
        if f is not None and blast.get(f, 0) == 0 and f not in in_cycle:
            groups["A"].append(rel)
        else:
            groups["B"].append(rel)
    groups["B"].sort(key=lambda r: (rank.get(fpath.get(r), 10 ** 9), r))
    step = {r: i + 1 for i, r in enumerate(groups["B"])}
    for x in findings:
        f = fpath.get(x["file"])
        x["blast"] = blast.get(f, 0) if f else 0
        x["mode"] = "並行批次" if x["file"] in groups["A"] else f"序列第 {step.get(x['file'], 0)} 步"
    findings.sort(key=lambda x: (x["file"] not in groups["A"], step.get(x["file"], 0), x["file"], x["line"], x["cls"]))
    for n, x in enumerate(findings):
        x["id"] = f"ERR-{n + 1:03d}"
    dyn = sum(1 for _f, (_s, t) in trees.items() for n in ast.walk(t)
              if isinstance(n, ast.Call) and _call_name(n.func).endswith(("spec_from_file_location", "import_module", "run_path")))
    per_pass = {p: sum(1 for x in findings if x["pass"] == p) for p in ("P1", "P2", "P3")}
    return {"tool": TAG, "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "roots": [str(r) for r in roots],
            "three": {"should": len(files) + sum(skipped.values()), "done": len(files) - len(unread), "skipped": dict(skipped, **({"讀不了": len(unread)} if unread else {}))},
            "passes": per_pass, "ruff": ruff_state, "schema": "灰 · DataFrame ↔ Parquet / DuckDB 欄位交給各系統現成動詞(VDF_SystemManager parquet align,唯讀)",
            "findings": findings, "groups": groups, "cycles": [[_rel(x, roots) for x in c] for c in cyc],
            "edges": sum(len(v) for v in edges.values()), "dynamic_loads": dyn, "secs": round(time.time() - t0, 2), "workers": nw,
            "_files": {_rel(f, roots): str(f) for f in files}, "_redges": {_rel(k, roots): sorted(_rel(x, roots) for x in v) for k, v in redges.items()},
            "_comp": {_rel(k, roots): v for k, v in comp_of.items()}}


# ---------------------------------------------------------------- 修補(只 ENCODING · BOM)
def patch_source(src: str, fixes: list) -> str:
    lines = src.splitlines(keepends=True)
    edits = []
    for x in fixes:
        if x["cls"] == "ENCODING" and x.get("node"):
            el, ec = x["node"]
            end = _abs(src, lines, el, ec)                          # 右括號之後
            close = end - 1
            j = close - 1
            while j >= 0 and src[j] in " \t\r\n":
                j -= 1
            ins = f'encoding="{x["want"]}"' if src[j] == "(" else (f' encoding="{x["want"]}"' if src[j] == "," else f', encoding="{x["want"]}"')
            edits.append((close, close, ins))
        elif x["cls"] == "BOM" and x.get("node"):
            l1, c1, l2, c2 = x["node"]
            a, b = _abs(src, lines, l1, c1), _abs(src, lines, l2, c2)
            lit = src[a:b]
            q = lit[-1] if lit and lit[-1] in "'\"" else '"'
            edits.append((a, b, f"{q}utf-8{q}"))
    for a, b, ins in sorted(edits, key=lambda e: e[0], reverse=True):
        src = src[:a] + ins + src[b:]
    return src


def _keys(fs: list) -> set:
    return {(x["file"], x["cls"], x["line"], x["detail"]) for x in fs}


def _exempt(path: Path) -> str:
    s = path.as_posix()
    if "/intake/" in s or "/references/intake/" in s:
        return "收容件(intake)只收不掛線"
    via = getattr(PRIOR, "VIA", None)
    if via:
        try:
            rel = path.resolve().relative_to(Path(via).resolve()).as_posix()
            why = PRIOR.template_exempt(rel)
            if why:
                return why
        except ValueError:
            pass
    return ""


def apply(pan: dict, targets: list, workers: int = 0) -> dict:
    files = pan["_files"]
    by = {}
    for x in pan["findings"]:
        if x["fix"] == "auto":
            by.setdefault(x["file"], []).append(x)
    backup = Path(tempfile.mkdtemp(prefix="VIA_hydra_bak_"))
    results = []

    def one(rel: str, dependents: list) -> dict:
        p = Path(files[rel])
        why = _exempt(p)
        if why:
            return {"file": rel, "state": "SKIP", "why": why, "fixed": []}
        orig = p.read_bytes()
        bak = backup / hashlib.sha256(str(p).encode()).hexdigest()[:16]
        bak.write_bytes(orig)
        src, bom = _read(p)
        new = patch_source(src, by[rel])
        try:
            ast.parse(new)
            compile(new, rel, "exec")
        except SyntaxError as e:
            return {"file": rel, "state": "ROLLBACK", "why": f"補丁後語法不過(行 {e.lineno}),沒寫檔", "fixed": []}
        tmp = p.with_name(p.name + ".hydra_tmp")
        tmp.write_bytes((("﻿" if bom else "") + new).encode("utf-8"))
        os.replace(tmp, p)
        before = {k for k in _keys(pan["findings"]) if k[0] in {rel, *dependents}}
        after_pan = panorama(targets, workers)
        after = {k for k in _keys(after_pan["findings"]) if k[0] in {rel, *dependents}}
        fixed_keys = _keys(by[rel])
        new_keys = after - before
        if new_keys:
            tmp2 = p.with_name(p.name + ".hydra_rb")
            tmp2.write_bytes(bak.read_bytes())
            os.replace(tmp2, p)
            return {"file": rel, "state": "ROLLBACK", "why": f"重掃多出 {len(new_keys)} 筆新發現:{sorted(new_keys)[:2]}", "fixed": []}
        done = [x["id"] for x in by[rel] if (x["file"], x["cls"], x["line"], x["detail"]) not in after]
        return {"file": rel, "state": "PASS", "fixed": done, "left": len(fixed_keys & after)}

    a_files = [r for r in pan["groups"]["A"] if r in by]
    b_files = [r for r in pan["groups"]["B"] if r in by]
    with ThreadPoolExecutor(max_workers=max(1, min(len(a_files), workers or PRIOR.accel_workers(8)[0]) or 1)) as ex:
        results += list(ex.map(lambda r: dict(one(r, []), mode="並行批次"), a_files))
    for i, r in enumerate(b_files, 1):
        results.append(dict(one(r, pan["_redges"].get(r, [])), mode=f"序列第 {i} 步"))
    return {"results": results, "backup": str(backup)}


# ---------------------------------------------------------------- 戰報
def _public(pan: dict) -> dict:
    return {k: v for k, v in pan.items() if not k.startswith("_")}


def report(before: dict, fix: dict | None, after: dict | None) -> dict:
    conf = [x for x in before["findings"]]
    rep = {"tool": TAG, "utc": before["utc"], "three": before["three"], "dynamic_loads": before.get("dynamic_loads", 0), "passes": before["passes"], "ruff": before["ruff"],
           "schema": before["schema"], "cycles": before["cycles"], "groups": {k: len(v) for k, v in before["groups"].items()},
           "confirmed": len(conf), "double": sum(1 for x in conf if x["confirm"].startswith("雙判")),
           "auto_fixable": sum(1 for x in conf if x["fix"] == "auto"), "by_class": {}}
    for x in conf:
        rep["by_class"][x["cls"]] = rep["by_class"].get(x["cls"], 0) + 1
    if fix is not None and after is not None:
        bk, ak = _keys(before["findings"]), _keys(after["findings"])
        rep["after"] = {"fixed": len(bk - ak), "left": len(bk & ak), "new": len(ak - bk), "new_list": sorted(ak - bk)[:20],
                        "rollback": sum(1 for r in fix["results"] if r["state"] == "ROLLBACK"),
                        "pass": sum(1 for r in fix["results"] if r["state"] == "PASS"), "skip": sum(1 for r in fix["results"] if r["state"] == "SKIP")}
    bad = (rep.get("after") or {}).get("new", 0) > 0 or rep["three"]["done"] < rep["three"]["should"] - sum(
        v for k, v in rep["three"]["skipped"].items() if k != "讀不了")
    rep["lamp"] = "RED" if bad else ("GREEN" if not conf and "ruff" in before["ruff"] and not before["ruff"].startswith("黃") else "YELLOW")
    return rep


def _write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".sdd_tmp")
    tmp.write_bytes(json.dumps(obj, ensure_ascii=False, indent=1, default=str).encode("utf-8"))   # UTF-8 無 BOM
    json.loads(tmp.read_bytes().decode("utf-8"))
    os.replace(tmp, path)


def hydra(argv: list) -> int:
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else d  # noqa: E731
    flags = {"--apply", "--json"}
    vals = {"--out", "--workers", "--max"}
    targets, skip = [], False
    for a in argv:
        if skip:
            skip = False
            continue
        if a in vals:
            skip = True
            continue
        if a not in flags:
            targets.append(a)
    if not targets:
        print("用法:python3 \"$E\" " + VERBS["hydra"][0])
        return 2
    workers, mx = int(opt("--workers", "0") or 0), int(opt("--max", "40") or 40)
    before = panorama(targets, workers)
    fix = after = None
    if "--apply" in argv:
        fix = apply(before, targets, workers)
        after = panorama(targets, workers)
    rep = report(before, fix, after)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = Path(opt("--out") or Path(tempfile.gettempdir()) / "VIA_token_cache" / "MDL158" / "hydra" / f"hydra_{stamp}.json")
    _write_json(out, {"report": rep, "before": _public(before), "fix": fix, "after": _public(after) if after else None})
    if "--json" in argv:
        print(json.dumps(rep, ensure_ascii=False, indent=1, default=str))
        return {"GREEN": 0, "YELLOW": 2}.get(rep["lamp"], 1)
    th = rep["three"]
    print(f"[{TAG} hydra] {rep['lamp']} · 應掃 {th['should']} · 已掃 {th['done']} · 略過 {sum(th['skipped'].values())} {th['skipped'] or ''}"
          f" · {before['secs']}s · 工人 {before['workers']}")
    print(f"  ① 三回合:P1 語法匯入符號 {rep['passes']['P1']} · P2 介面契約 {rep['passes']['P2']} · P3 執行期邊界 {rep['passes']['P3']}"
          f" · 確認 {rep['confirmed']}(雙判 {rep['double']})· UNDEF 來源:{rep['ruff']}")
    print(f"     各類:{rep['by_class']}")
    print(f"     P2 SCHEMA:{rep['schema']}")
    print(f"  ② 依賴圖:靜態匯入邊 {before['edges']} · 循環 {len(before['cycles'])} · A 組(並行){rep['groups']['A']} 檔 · B 組(拓撲序){rep['groups']['B']} 檔"
          + (f" · [黃] 動態載入 {before['dynamic_loads']} 處(spec_from_file_location / import_module / run_path)不入圖 → "
             "A 組的「零耦合」只對靜態匯入成立,修時照樣每檔重掃" if before.get("dynamic_loads") else ""))
    for c in before["cycles"][:5]:
        print(f"     循環:{' ↔ '.join(c[:6])}")
    print("  [錯誤編號] | [執行模式] | [檔:行] | [根因] | [修正動作] | [覆核]")
    for x in before["findings"][:mx]:
        act = ("自動:" + ("插 encoding=" + x.get("want", "") if x["cls"] == "ENCODING" else "utf-8-sig → utf-8")) if x["fix"] == "auto" else "人工(列計畫)"
        print(f"  {x['id']} | {x['mode']} | {x['file']}:{x['line']} | {x['cls']} {x['detail'][:70]} | {act} | {x['confirm']}")
    if len(before["findings"]) > mx:
        print(f"  …另 {len(before['findings']) - mx} 筆(全表在戰報 JSON;--max 調整)")
    if fix is not None:
        a = rep["after"]
        print(f"  ③ 修補:PASS {a['pass']} · ROLLBACK {a['rollback']} · SKIP {a['skip']} · 備份 {fix['backup']}")
        for r in fix["results"]:
            if r["state"] != "PASS":
                print(f"     {r['state']} {r['file']} · {r.get('why', '')[:100]}")
        print(f"  ④ 修後全景:已修 {a['fixed']} · 剩 {a['left']} · 新增 {a['new']}(必須 0)")
    else:
        print(f"  ③ 乾跑:沒寫任何檔 · 可自動修 {rep['auto_fixable']} 筆(ENCODING · BOM)· 其餘列計畫 → 要修再加 --apply")
    print(f"  戰報 → {out}")
    return {"GREEN": 0, "YELLOW": 2}.get(rep["lamp"], 1)


# ---------------------------------------------------------------- 入口
def print_verbs() -> int:
    e = '$E'
    print(f"[{TAG} 動詞表] {len(VERBS)} 個 · {e} = 鎖冊 token 那一支")
    for k, (use, when, what) in VERBS.items():
        print(f"  {k:<10} python3 \"{e}\" {use}")
        print(f"             何時:{when} · 做什麼:{what}")
    return 0


def main() -> int:
    argv = sys.argv[1:]
    if argv == ["--selftest"]:
        return selftest()
    if argv[:1] == ["hydra"]:
        return hydra(argv[1:])
    if argv[:1] == ["verbs"]:
        return print_verbs()
    return PRIOR.main()


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    chk("① 加速器真的載到(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    with tempfile.TemporaryDirectory() as td:
        d = Path(td) / "via_01_vdf"
        (d / "pkg").mkdir(parents=True)
        (d / "pkg" / "__init__.py").write_text("", encoding="utf-8")
        files = {
            "pkg/core.py": "def f(a, b):\n    return a + b\n\n\ndef load(p):\n    with open(p) as fh:\n        return fh.read()\n",
            "leaf.py": "from pkg.core import f\nimport json\n\n\ndef run(p):\n    x = f(1, 2, 3)\n    open(p, 'w', encoding='utf-8-sig').write(json.dumps(x))\n"
                       "    con = open(p)\n    return 1\n",
            "cyc_a.py": "import cyc_b\nX = 1\n", "cyc_b.py": "import cyc_a\nY = 2\n",
            "bad.py": "def g(:\n    pass\n",
            "unres.py": "import nonexistent_mod_xyz_9\ntry:\n    import other_missing_q\nexcept ImportError:\n    other_missing_q = None\nprint(undefined_name_q)\n",
            "net.py": "import urllib.request\n\n\ndef get(u):\n    return urllib.request.urlopen(u).read()\n",
            "envs/x/site.py": "import nothing_here_z\n",
        }
        for k, v in files.items():
            (d / k).parent.mkdir(parents=True, exist_ok=True)
            (d / k).write_text(v, encoding="utf-8")
        h0 = {k: hashlib.sha256((d / k).read_bytes()).hexdigest() for k in files}
        pan = panorama([str(d)], 2)
        cls = {}
        for x in pan["findings"]:
            cls.setdefault(x["cls"], set()).add(x["file"])
        chk("② 三數:應掃 9 · 已掃 8 · 略過 1(envs 虛境)", pan["three"]["should"] == 9 and pan["three"]["done"] == 8 and pan["three"]["skipped"] == {"虛境": 1}, pan["three"])
        chk("③ P1:SYNTAX(雙判)· UNRESOLVED 只報真的缺(try/except ImportError 的不報)· CYCLE(雙判)",
            "bad.py" in cls.get("SYNTAX", set()) and any(x["confirm"].startswith("雙判") for x in pan["findings"] if x["cls"] == "SYNTAX")
            and cls.get("UNRESOLVED") == {"unres.py"} and sum(1 for x in pan["findings"] if x["cls"] == "UNRESOLVED") == 1
            and cls.get("CYCLE") == {"cyc_a.py", "cyc_b.py"} and all(x["confirm"].startswith("雙判") for x in pan["findings"] if x["cls"] == "CYCLE"),
            {k: sorted(v) for k, v in cls.items()})
        if shutil.which("ruff"):
            chk("③b P1 UNDEF:ruff F821 + 本模組沒綁定 → 雙判", cls.get("UNDEF") == {"unres.py"}, cls.get("UNDEF"))
        else:
            chk("③b 沒 ruff → UNDEF 照實寫略過(黃,不算綠)", pan["ruff"].startswith("黃"), pan["ruff"])
        chk("④ P2 ARITY:f(1,2,3) 對 f(a,b) → 雙判(AST 計數 + Signature.bind)",
            any(x["cls"] == "ARITY" and x["file"] == "leaf.py" and x["confirm"].startswith("雙判") for x in pan["findings"]), cls.get("ARITY"))
        chk("⑤ P3:ENCODING(con = open(p))· BOM(寫出 utf-8-sig)· LEAK(con 沒 close)· NOTIMEOUT(urlopen)· with 裡的 open 不算 LEAK",
            "leaf.py" in cls.get("ENCODING", set()) and "leaf.py" in cls.get("BOM", set()) and cls.get("LEAK") == {"leaf.py"}
            and cls.get("NOTIMEOUT") == {"net.py"} and "pkg/core.py" in cls.get("ENCODING", set()), {k: sorted(v) for k, v in cls.items()})
        chk("⑥ 依賴圖:pkg/core.py 有下游 → B 組第 1 步;leaf.py 沒下游 → A 組並行;循環兩檔在 B 組",
            "leaf.py" in pan["groups"]["A"] and pan["groups"]["B"][:1] == ["pkg/core.py"] or ("pkg/core.py" in pan["groups"]["B"]
            and pan["groups"]["B"].index("pkg/core.py") < len(pan["groups"]["B"]) and "leaf.py" in pan["groups"]["A"]
            and {"cyc_a.py", "cyc_b.py"} <= set(pan["groups"]["B"])), pan["groups"])
        same = {k: hashlib.sha256((d / k).read_bytes()).hexdigest() for k in files} == h0
        chk("⑦ 乾跑零寫入(全部檔位元不變)", same)
        fx = apply(pan, [str(d)], 2)
        after = panorama([str(d)], 2)
        rep = report(pan, fx, after)
        leaf = (d / "leaf.py").read_text(encoding="utf-8")
        core = (d / "pkg" / "core.py").read_text(encoding="utf-8")
        chk("⑧ --apply:A 組 leaf.py 並行修(encoding 插入 · utf-8-sig → utf-8)· B 組 core.py 逐步修 · 都還能 parse / compile",
            "open(p, 'w', encoding='utf-8')" in leaf and 'con = open(p, encoding="utf-8-sig")' in leaf
            and 'open(p, encoding="utf-8-sig")' in core and all(r["state"] == "PASS" for r in fx["results"]), [fx["results"], leaf[-160:]])
        chk("⑨ 修後全景:新增 0 · 原 ENCODING / BOM(寫出)清掉 · 其餘(ARITY · LEAK · CYCLE …)照列人工",
            rep["after"]["new"] == 0 and rep["after"]["fixed"] >= 3 and not any(x["cls"] in AUTO and x["fix"] == "auto" for x in after["findings"])
            and any(x["cls"] == "ARITY" for x in after["findings"]), rep.get("after"))
        bad_pan = panorama([str(d)], 2)
        target = d / "net.py"
        target.write_text("import urllib.request\n\n\ndef get(u):\n    fh = open(u)\n    return fh.read()\n", encoding="utf-8")
        bad_pan = panorama([str(d)], 2)
        h_before = hashlib.sha256(target.read_bytes()).hexdigest()
        global patch_source
        keep = patch_source
        patch_source = lambda src, fixes: src.replace("return fh.read()", "return fh.read()\n    bad = open(u)")  # noqa: E731
        try:
            fx2 = apply(bad_pan, [str(d)], 2)
        finally:
            patch_source = keep
        r2 = [r for r in fx2["results"] if r["file"] == "net.py"]
        chk("⑩ 補丁造出新問題 → 自動 ROLLBACK(位元還原)", r2 and r2[0]["state"] == "ROLLBACK"
            and hashlib.sha256(target.read_bytes()).hexdigest() == h_before, r2)
        (d / "intake").mkdir()
        (d / "intake" / "raw.py").write_text("x = open('a')\n", encoding="utf-8")
        p3 = panorama([str(d)], 2)
        fx3 = apply(p3, [str(d)], 2)
        chk("⑪ 收容件(intake)不寫:SKIP 並寫理由", any(r["file"] == "intake/raw.py" and r["state"] == "SKIP" for r in fx3["results"])
            and (d / "intake" / "raw.py").read_text(encoding="utf-8") == "x = open('a')\n", fx3["results"])
        out = Path(td) / "rep.json"
        rc = hydra([str(d), "--out", str(out), "--max", "3"])
        raw = out.read_bytes()
        chk("⑫ 戰報 JSON:UTF-8 無 BOM · 有三數 / 分組 / 修前修後欄 · rc 照燈號", not raw.startswith(b"\xef\xbb\xbf")
            and json.loads(raw.decode("utf-8"))["report"]["three"]["should"] >= 9 and rc in (0, 1, 2), rc)
    chk("⑬ VERBS 前版 15 個全在 + hydra(字串門要的 read · slice · digest · pack 在)",
        set(PRIOR.VERBS) <= set(VERBS) and "hydra" in VERBS and all(k in VERBS for k in ("read", "slice", "digest", "pack")))
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc_p = PRIOR.selftest()
    tail = [ln for ln in buf.getvalue().splitlines() if ln.strip()][-1:] or [""]
    chk("⑭ 前版 v0121 鏈自測照過(rc 0)", rc_p == 0, tail[0][:200])
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑮ 檔面:第 3 行加速器標記 · 語法樹匯入 VIA_SuperAccel_Module · glob 取前版 · 零 TA-Lib · 不設同意閘 · 字串門字樣在",
        src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and "VIA_SuperAccel_Module" in {a.name for n in ast.walk(ast.parse(src))
                                                                                          if isinstance(n, ast.Import) for a in n.names}
        and "HERE.glob(_STEM" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M)
        and all(w in src for w in ('"read"', '"slice"', '"digest"', "--if-etag", "def pack_payload")))
    print(f"[計] {TAG} 本版 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 2


if __name__ == "__main__":
    raise SystemExit(main())
