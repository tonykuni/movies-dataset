#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL253_ToolingInventory v0100 — 工具盤點矩陣:全景 AST + 中央編號 + 短令冊 + L103 三導入檢查,一張表

操作員(2026-10-02):貼來 Inspect-VCGC-Tooling.ps1 + py_accelerator_check.py,令「自動用目前的全景式工具 自動檢查注入 AST
搭配自動編號及分類及說明及子系統及來源 導入 PY 加速器 · VDF 導入網路工具 · PS 導入最強模板 HTML U/I」,並參考
VDF_MDL002_YFinanceFetchingEngine 的全景掃描。本支**不另寫一份規則**,每一欄都問既有正主:
  ① 定義樹 / 匯入 / 說明 / AST 問題(治理七類 + 通用類)= 全景讀檔 CGC_MDL158 鎖版那一支(VIA_ToolVersion_Lock token;雜湊不符就停)
  ② 編號 · 子系統 · 分類 · 發號時間 = 中央編號冊 VIA_NumberBooks/*.jsonl(CGC_MDL237 寫的;本支只讀)
  ③ 短令 = Register-VIA-Commands 尾版**順著點源鏈**往回讀(via-help 的 CommandRoster 只讀尾版一支,v0266 起只看得到 1 個;本支補這個洞)
  ④ L103 三導入:PY `[VIA:ACCEL-BRIDGE` · VDF 用到網路套件要 `[VIA:NET-BRIDGE`(套件清單問 via_bridge_sweeper 尾版)· PS `CELERITAS-TEMPLATE-JOIN`
  ⑤ 頁殼 = 排版規格 CGC_MDL173(page_html · html_table;零 CDN、亮暗兩色)+ 本支一小段排序 / 篩選 JS
  ⑥ 更新時間 = git log 一次掃(沒有 git 才退回檔案時間,照實標來源)
用法(只收 VCGC):
  via-vcgc run CGC_MDL253_ToolingInventory scan [路徑 …] [--all-versions] [--json] [--no-open]
  via-vcgc run CGC_MDL253_ToolingInventory cmds [--recent N] [--json]
  via-vcgc run CGC_MDL253_ToolingInventory card <檔>
  python CGC_MDL253_ToolingInventory_v0100.py --selftest
只讀:不改任何被掃的檔、不執行被掃的檔(只 ast.parse / 文字剖析);輸出只寫 VIA_Reports/tooling/(不進 git)。零網路;不用 TA-Lib。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====


import ast
import csv
import hashlib
import html
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPO = VIA.parent
ENGINE = Path(__file__).stem
OUT = VIA / "VIA_Reports" / "tooling"
LOCK = HERE / "VIA_ToolVersion_Lock_v0100.json"
BOOKS = HERE / "VIA_NumberBooks"
KIND_PREF = ("MDL", "ENG", "TOOL", "LIB", "SRC", "XSRC", "LGC")
PY_MARK = "[VIA:ACCEL-BRIDGE"
NET_MARK = "[VIA:NET-BRIDGE"
PS_MARK = "CELERITAS-TEMPLATE-" + "JOIN"          # 拆寫:本支是尺,不是接好模板的 PS
PS_ACCEL = "[VIA:PS-ACCEL"
ENTRY_FUNCS = ("main", "tool_run", "interactive_menu", "run", "cli")
RED_CLS = {"SYNTAX", "COMPILE", "PSPARSE"}
SKIP_RX = re.compile(r"(^|/)(ASSETS|SCOPE_COPY|__pycache__|_?archive|_?quarantine|_?backup|node_modules|history|evidence|\.git)(/|$)", re.I)
VER_RX = re.compile(r"[-_]v(\d{2,5})$")
NET_FALLBACK = re.compile(r"^\s*(?:import|from)\s+(urllib|requests|httpx|aiohttp|yfinance|akshare|playwright|websockets?)\b", re.M)
DEFAULT_SCOPE = (
    ("", ("*.ps1",)), ("launchers", ("*.ps1",)),
    ("supportive modules/registry", ("*.py", "*.ps1")), ("supportive modules", ("*.py", "*.ps1")),
    ("supportive modules/ps7", ("*.ps1",)), ("supportive modules/network", ("*.py", "*.ps1")),
    ("functional modules/VDF", ("**/*.py", "**/*.ps1")), ("functional modules/VRN", ("**/*.py", "**/*.ps1")),
    ("functional modules/VAP", ("**/*.py", "**/*.ps1")),
)
# 操作員點名的參考件:YFinance 抓取引擎(intake b716 原件與 VDF 正主版)一定進表
EXTRA = ("supportive modules/references/intake/VIA_VDF_Engines_b716/VDF_MDL002_YFinanceFetchingEngine_1.py",)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _newest(pattern: str):
    hits = [p for p in HERE.glob(pattern) if VER_RX.search(p.stem)]
    return max(hits, key=lambda p: int(VER_RX.search(p.stem).group(1))) if hits else None


def rel(p: Path) -> str:
    try:
        return p.resolve().relative_to(VIA).as_posix()
    except ValueError:
        return p.as_posix()


def family_of(path_or_name) -> str:
    stem = Path(str(path_or_name)).stem if str(path_or_name).endswith((".py", ".ps1")) else str(path_or_name)
    return re.sub(r"[-_]v$", "", VER_RX.sub("", stem.replace("-v*", "").replace("_v*", "")))   # 「…_v*.py」截出來的尾巴 _v 也去掉


def version_of(p: Path) -> int:
    m = VER_RX.search(p.stem)
    return int(m.group(1)) if m else -1


# ---------------------------------------------------------------- ① 全景讀檔(鎖版那一支;雜湊不符 = 停)
def panorama_path() -> tuple[Path | None, str]:
    try:
        tok = json.loads(LOCK.read_text(encoding="utf-8"))["token"]
    except (OSError, ValueError, KeyError) as e:
        return None, f"鎖冊讀不到:{e}"
    p = REPO / tok["path"]
    if not p.is_file():
        return None, f"鎖版全景不在:{tok['path']}"
    got = hashlib.sha256(p.read_bytes()).hexdigest()
    if tok.get("sha256") and got != tok["sha256"]:
        return None, f"鎖版全景雜湊不符(鎖 {tok['sha256'][:12]} ≠ 檔 {got[:12]});換版只經 via-vcgc tools activate"
    return p, tok.get("version", "")


_PAN = None


def _pan_init(path: str):
    global _PAN
    _PAN = _load(Path(path), "_mdl253_panorama")


def _card(path: str) -> dict:
    p = Path(path)
    try:
        card = _PAN.read_file(p)
    except Exception as e:                       # 一支讀壞不拖垮整表:照實記成 SYNTAX 級紅
        return {"path": path, "lines": 0, "imports": [], "defs": [], "issues": [{"cls": "PSPARSE" if p.suffix == ".ps1" else "SYNTAX",
                "line": 0, "how": "read", "detail": f"{type(e).__name__}: {e}"}], "module_doc": ""}
    src = p.read_text(encoding="utf-8", errors="ignore")
    card["_marks"] = {"accel": PY_MARK in src, "net": NET_MARK in src, "ps_tpl": PS_MARK in src, "ps_accel": PS_ACCEL in src}
    card["_cli"] = cli_surface(src) if p.suffix == ".py" else ps_params(src)
    card["_desc"] = describe(card, src, p)
    card["_netuse"] = bool(NET_RX.search(src)) if p.suffix == ".py" else False
    card["_main"] = ("__name__" in src and "__main__" in src) if p.suffix == ".py" else True
    return card


try:                                                 # VDF 網路套件清單問掃橋器尾版(問不到才用同一份字面備援)
    _sw = _newest("via_bridge_sweeper_v*.py")
    NET_RX = getattr(_load(_sw, "_mdl253_sweeper"), "NET_IMPORT_RX", NET_FALLBACK) if _sw else NET_FALLBACK
except Exception:
    NET_RX = NET_FALLBACK


def cli_surface(src: str) -> dict:
    """argparse 旗標 / 子令、sys.argv 比對的字面旗標(只 ast.parse,不執行)。"""
    flags, verbs = set(), set()
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return {"flags": [], "verbs": []}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            strs = [a.value for a in node.args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
            if node.func.attr == "add_argument":
                flags.update(s for s in strs if s.startswith("-"))
                for kw in node.keywords:
                    if kw.arg == "choices" and isinstance(kw.value, (ast.List, ast.Tuple, ast.Set)):
                        verbs.update(e.value for e in kw.value.elts if isinstance(e, ast.Constant) and isinstance(e.value, str))
            elif node.func.attr == "add_parser" and strs:
                verbs.add(strs[0])
        elif isinstance(node, ast.Compare):
            try:
                txt = ast.unparse(node)
            except Exception:                        # 罕見:無法還原的節點就當沒有旗標(不中斷整支)
                txt = ""
            if re.match(r"(verb|cmd|action|mode|sub)\s*(==|in)\s", txt):   # verb == "scan" 這種手寫子令
                for c in node.comparators:
                    for e in (c.elts if isinstance(c, (ast.List, ast.Tuple, ast.Set)) else [c]):
                        if isinstance(e, ast.Constant) and isinstance(e.value, str) and re.fullmatch(r"[a-z][a-z0-9-]{1,20}", e.value):
                            verbs.add(e.value)
            ops = [node.left, *node.comparators]
            for c in ops:                                     # `"--selftest" in a` / `a[1] == "--dry"`:比較式裡的 --xxx 字面一律算旗標
                for e in (c.elts if isinstance(c, (ast.List, ast.Tuple, ast.Set)) else [c]):
                    if isinstance(e, ast.Constant) and isinstance(e.value, str) and re.fullmatch(r"--?[a-z][\w-]{0,30}", e.value):
                        flags.add(e.value)
            if any(isinstance(c, ast.Subscript) and isinstance(c.value, ast.Name) and c.value.id in ("a", "args", "argv", "av")
                   for c in ops):                             # `a[0] == "status"`:位置參數比對字面 = 子令
                for c in ops:
                    if isinstance(c, ast.Constant) and isinstance(c.value, str) and re.fullmatch(r"[a-z][a-z0-9-]{1,20}", c.value):
                        verbs.add(c.value)
            if any("argv" in ast.unparse(c) for c in ops if not isinstance(c, ast.Constant)):   # 真的拿 sys.argv 來比,才算旗標
                for c in ops:
                    for e in (c.elts if isinstance(c, (ast.List, ast.Tuple, ast.Set)) else [c]):
                        if isinstance(e, ast.Constant) and isinstance(e.value, str) and e.value.startswith("-"):
                            flags.add(e.value)
                        elif isinstance(e, ast.Constant) and isinstance(e.value, str) and re.fullmatch(r"[a-z][a-z0-9-]{1,20}", e.value):
                            verbs.add(e.value)
    return {"flags": sorted(flags), "verbs": sorted(verbs)}


def ps_params(src: str) -> dict:
    """腳本層 param( … ) 的參數名(括號配對,吃得下 [Parameter(Mandatory)];只看檔頭那一個)。"""
    m = re.search(r"(?im)^\s*param\s*\(", src)
    names = []
    if m:
        depth, i = 1, m.end()
        while i < len(src) and depth:
            depth += {"(": 1, ")": -1}.get(src[i], 0)
            i += 1
        names = sorted(set(re.findall(r"\$([A-Za-z]\w*)", re.sub(r"=[^,\n]*", "", src[m.end():i - 1]))))
    return {"flags": ["-" + n for n in names][:40], "verbs": []}


def _wordy(s: str) -> bool:
    """橫幅線(====、----、####)不算說明;要有字。"""
    return bool(re.search(r"[A-Za-z0-9\u4e00-\u9fff]", s or ""))


def describe(card: dict, src: str, p: Path) -> str:
    if p.suffix == ".py":
        try:                                       # 全景卡只帶 docstring 第一行;橫幅開頭的檔要往下找第一行有字的
            full = ast.get_docstring(ast.parse(src)) or card.get("module_doc") or ""
        except SyntaxError:
            full = card.get("module_doc") or ""
        doc = [d.strip().strip("#").strip() for d in full.splitlines()]
        line = next((d for d in doc if _wordy(d) and not re.fullmatch(r"[\w.\-]+\.(?:py|ps1)", d)), "")   # 只寫檔名那行不算說明
    else:
        line = ""
        m = re.search(r"(?i)\.SYNOPSIS[ \t]*\r?\n[ \t]*([^\r\n]+)", src[:4000])
        if m:
            line = m.group(1).strip()
        else:
            for ln in src.splitlines()[:30]:
                t = ln.strip().lstrip("#").strip()
                if not t or t.startswith(("=", "Requires", PS_MARK, "requires")) or ln.strip().startswith("#Requires"):
                    continue
                if ln.lstrip().startswith("#") and _wordy(t):
                    line = t
                    break
    line = re.sub(r"^\S+\s+v\d{3,5}\s*[—-]\s*", "", line)    # 去掉「名稱 vNNNN —」前綴,留說明本身
    line = re.sub(r"^[\w.\-]+\.(?:py|ps1)\s*[—-]+\s*", "", line)   # 去掉「檔名.ps1 —」前綴
    return line[:160]


# ---------------------------------------------------------------- ② 中央編號冊(只讀)
def number_index() -> dict:
    idx, bad = {}, 0
    for book in sorted(BOOKS.glob("VIA_NumberBook_*_v*.jsonl")):
        for ln in book.read_text(encoding="utf-8", errors="ignore").splitlines():
            if '"source"' not in ln:
                continue
            try:
                r = json.loads(ln)
            except ValueError:
                bad += 1                              # 壞列照數,不靜默(冊是 MDL237 的,本支只讀不修)
                continue
            src = (r.get("source") or "").replace("\\", "/")
            if not src or r.get("gone_since"):
                continue
            k = r.get("kind", "")
            rank = KIND_PREF.index(k) if k in KIND_PREF else len(KIND_PREF)
            old = idx.get(src)
            if old is None or rank < old[0]:
                idx[src] = (rank, r)
    if bad:
        print(f"  [編號冊] {bad} 列讀不懂(跳過;冊歸 CGC_MDL237 管)")
    return {k: v[1] for k, v in idx.items()}


# ---------------------------------------------------------------- ③ 短令冊(Register 尾版順著點源鏈往回讀)
FUNC_RX = re.compile(r"(?m)^function\s+global:([A-Za-z][\w\-]*)\s*(?:\(|\{)")
ALIAS_RX = re.compile(r"Set-Alias\s+(?:-Name\s+)?(\S+)\s+(?:-Value\s+)?([A-Za-z][\w\-]*)")
CHAIN_RX = re.compile(r"Register-VIA-Commands-v(\d{4})\.ps1")
TARGET_RX = re.compile(r"\b([A-Z]{2,5}_(?:MDL|ENG|SUP|LGC|TOOL)\d{2,4}(?:_[A-Za-z0-9]+)*)|([A-Za-z][\w\.\-]*?)(?:[-_]v\*|[-_]v\d{4})?\.ps1")   # 名稱可多段底線
VCGC_RX = re.compile(r"via-vcgc\s+([a-z][\w\-]*(?:\s+[a-z][\w\-]*)?)")


def git_dates(paths=None) -> dict:
    """{VIA 相對路徑: 最後提交日};一次 git log 掃完。沒有 git 回 {}(呼叫端退回檔案時間並照實標)。"""
    try:
        out = subprocess.run(["git", "-C", str(VIA), "log", "--format=@%cs", "--name-only", "--", "."],
                             capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120).stdout
    except (OSError, subprocess.SubprocessError):
        return {}
    top = subprocess.run(["git", "-C", str(VIA), "rev-parse", "--show-prefix"], capture_output=True, text=True).stdout.strip()
    dates, cur = {}, ""
    for ln in out.splitlines():
        if ln.startswith("@"):
            cur = ln[1:]
        elif ln.strip():
            p = ln.strip()
            p = p[len(top):] if top and p.startswith(top) else p
            dates.setdefault(p, cur)
    return dates


def commands(dates: dict | None = None) -> list[dict]:
    regs = sorted(VIA.glob("Register-VIA-Commands-v*.ps1"))
    if not regs:
        return []
    dates = dates if dates is not None else {}
    chain, cur, seen = [], regs[-1], set()
    while cur and cur.name not in seen:              # 尾版 → 點源的前版 → …(只看 `. (Join-Path … "Register-…")` 那一行)
        seen.add(cur.name)
        chain.append(cur)
        src = cur.read_text(encoding="utf-8", errors="ignore")
        dot = re.search(r"(?m)^\.\s*\(Join-Path\s+\$PSScriptRoot\s+\"(Register-VIA-Commands-v\d{4}\.ps1)\"\)", src)
        nxt = VIA / dot.group(1) if dot else None
        cur = nxt if nxt and nxt.is_file() else None
    rows, aliases = {}, {}
    for f in chain:                                   # 新到舊:第一次看到的定義是生效那一份;最舊看到的是「新增於」
        src = f.read_text(encoding="utf-8", errors="ignore")
        ver = int(CHAIN_RX.search(f.name).group(1))
        heads = list(FUNC_RX.finditer(src))
        for i, m in enumerate(heads):
            name = m.group(1)
            if not re.match(r"[a-z]", name):              # Get-VIA… / Invoke-VIA… 是冊內輔助函數,不是給人打的短令
                continue
            body = src[m.start(): heads[i + 1].start() if i + 1 < len(heads) else min(len(src), m.start() + 6000)][:6000]
            r = rows.get(name)
            if r is None:
                fams = sorted({family_of(a or b) for a, b in TARGET_RX.findall(body) if (a or b)} - {"Register-VIA-Commands"})
                verbs = sorted({v.strip() for v in VCGC_RX.findall(body)})
                rows[name] = {"cmd": name, "alias": [], "active_in": f.name, "added_in": f.name, "added_ver": ver,
                              "targets": fams[:8], "vcgc": verbs[:6], "note": _cmd_note(src, name)}
            else:
                r["added_in"], r["added_ver"] = f.name, ver
                r["note"] = r["note"] or _cmd_note(src, name)
        for a, target in ALIAS_RX.findall(src):
            aliases.setdefault(a, target)
    for a, t in aliases.items():
        if t in rows and a not in rows[t]["alias"]:
            rows[t]["alias"].append(a)
    for r in rows.values():
        r["added_at"] = dates.get(r["added_in"], "")
    return sorted(rows.values(), key=lambda r: (-r["added_ver"], r["cmd"]))


def _cmd_note(src: str, name: str) -> str:
    m = re.search(r"\+" + re.escape(name) + r"(?:\(([^)]*)\))?[::—\s]*([^\n]{0,80})", src[:3000])
    if m:
        return ((m.group(1) or "") + " " + (m.group(2) or "")).strip(" 。,,;;")[:100]
    return ""


# ---------------------------------------------------------------- 盤點
def targets(paths=None, all_versions=False) -> list[Path]:
    files = []
    if paths:
        for a in paths:
            p = Path(a)
            p = p if p.is_absolute() else (VIA / a if (VIA / a).exists() else Path.cwd() / a)
            if p.is_dir():
                files += [q for q in p.rglob("*") if q.suffix in (".py", ".ps1") and q.is_file()]
            elif p.is_file():
                files.append(p)
    else:
        for base, pats in DEFAULT_SCOPE:
            root = VIA / base if base else VIA
            for pat in pats:
                files += [q for q in root.glob(pat) if q.is_file()]
        files += [VIA / x for x in EXTRA if (VIA / x).is_file()]
    uniq = {}
    for f in files:
        r = rel(f)
        if not paths and SKIP_RX.search(r):
            continue
        uniq[r] = f.resolve()
    if all_versions:
        return [uniq[k] for k in sorted(uniq)]
    tails = {}
    for r, f in uniq.items():                         # 尾版律:同夾同家族只留版號最大那支(沒版號的自成一家)
        key = (str(f.parent), family_of(f).lower(), f.suffix)
        if key not in tails or version_of(f) > version_of(tails[key]):
            tails[key] = f
    return sorted(tails.values(), key=rel)


def area_of(r: str) -> str:
    if r.startswith("supportive modules/references/intake/"):
        return "參考件(intake)"
    if r.startswith("supportive modules/registry/"):
        return "registry(中央)"
    if r.startswith("functional modules/"):
        return "子系統 " + r.split("/")[1]
    if r.startswith("supportive modules/"):
        return "支援模組"
    if r.startswith("launchers/"):
        return "launchers"
    return "倉根 PS" if "/" not in r else r.split("/")[0]


def sub_of(r: str, num: dict | None) -> str:
    if num and num.get("sub"):
        return num["sub"]
    name = Path(r).name
    for pre, sub in (("CGC_", "VCGC"), ("VDF_", "VDF"), ("VRN_", "VRN"), ("VAP_", "VAP"), ("SUP_", "SUP"), ("VETF", "VETF")):
        if name.startswith(pre):
            return sub
    if r.startswith("functional modules/"):
        return r.split("/")[1].upper()
    return "VIA"


def build_row(f: Path, card: dict, num: dict | None, dates: dict, cmd_by_fam: dict) -> dict:
    r = rel(f)
    is_py, fam = f.suffix == ".py", family_of(f)
    issues = [i for i in card.get("issues", []) if not i.get("exempt")]
    cls = {}
    for i in issues:
        cls[i["cls"]] = cls.get(i["cls"], 0) + 1
    m = card.get("_marks", {})
    vdf = r.startswith("functional modules/VDF/") or Path(r).name.startswith("VDF_")
    l103 = {
        "py_accel": ("OK" if m.get("accel") else "MISS") if is_py else "—",
        "vdf_net": ("OK" if m.get("net") else ("MISS" if card.get("_netuse") else "不需")) if (is_py and vdf) else "—",
        "ps_tpl": ("OK" if m.get("ps_tpl") else "MISS") if not is_py else "—",
    }
    entry = [d["name"] for d in card.get("defs", []) if d.get("depth", 0) == 0 and d["name"] in ENTRY_FUNCS]
    cli = card.get("_cli") or {"flags": [], "verbs": []}
    cmds = sorted({c for key in {fam.lower(), "_".join(fam.split("_")[:2]).lower()} for c in cmd_by_fam.get(key, [])})
    if is_py and r.startswith("supportive modules/registry/") and re.match(r"[A-Z]{2,5}_(MDL|ENG)\d", fam):
        vs = cli.get("verbs") or []
        pick = next((v for v in ("scan", "run", "status", "check", "audit", "print") if v in vs), vs[0] if vs else "")
        run = f"via-vcgc run {fam}" + (f" {pick}" if pick else "")
    elif is_py:
        run = f'python "{r}"'                          # 旗標另列一欄;這裡只給最短可跑的那一句
    else:
        run = f'& ".\\{r.replace("/", chr(92))}"'
    red = any(c in RED_CLS for c in cls)
    yellow = (not red) and ("MISS" in l103.values() or bool(cls) or not num)
    upd = dates.get(r)
    return {
        "code": (num or {}).get("code") or "未編號", "sub": sub_of(r, num), "kind": (num or {}).get("kind") or ("PS" if not is_py else "—"),
        "cat": (num or {}).get("cat") or ("PS 庫" if f.name.startswith("Register-") else ("PS 入口" if not is_py else ("引擎" if card.get("_main") else "模組"))),
        "name": f.name, "family": fam, "version": (f"v{version_of(f):04d}" if version_of(f) >= 0 else "—"),
        "desc": card.get("_desc", ""), "area": area_of(r), "path": r,
        "updated": upd or time.strftime("%Y-%m-%d", time.localtime(f.stat().st_mtime)), "updated_src": "git" if upd else "mtime",
        "numbered_at": (num or {}).get("numbered_at", ""), "lines": card.get("lines", 0), "defs": len(card.get("defs", [])),
        "entry": entry + (["__main__"] if is_py and card.get("_main") else []), "flags": cli.get("flags", []), "verbs": cli.get("verbs", []),
        "cmds": cmds, "run": run, "l103": l103, "issues": cls, "netuse": bool(card.get("_netuse")), "lamp": "RED" if red else ("YELLOW" if yellow else "GREEN"),
        "functions": [f"{d['name']}{d.get('sig', '')}" for d in card.get("defs", [])][:200],
        "anchors": [f"{r}:{i['line']} {i['cls']} {i.get('detail', '')[:80]}" for i in issues][:20],
    }


def scan(paths=None, all_versions=False, quiet=False) -> dict:
    pan, ver = panorama_path()
    if pan is None:
        return {"state": "RED", "why": ver, "rows": []}
    _pan_init(str(pan))
    files = targets(paths, all_versions)
    dates = git_dates()
    nums = number_index()
    cmds = commands(dates)
    cmd_by_fam = {}
    for c in cmds:
        for t in c["targets"]:
            for key in {t.lower(), "_".join(t.split("_")[:2]).lower()}:
                cmd_by_fam.setdefault(key, []).append(c["cmd"])
    rows, t0 = [], time.time()
    for i, f in enumerate(files, 1):
        rows.append(build_row(f, _card(str(f)), nums.get(rel(f)), dates, cmd_by_fam))
        if not quiet and i % 250 == 0:
            print(f"  [盤點] {i}/{len(files)} · {time.time() - t0:.0f}s", flush=True)
    return {"state": "OK", "engine": ENGINE, "panorama": f"{pan.name}({ver} 鎖版)", "at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "scope": "指定路徑" if paths else "預設範圍(倉根 PS · launchers · registry · 支援模組 · VDF/VRN/VAP · 參考件)",
            "tails_only": not all_versions, "rows": rows, "commands": cmds, "sec": round(time.time() - t0, 1)}


def summarize(res: dict) -> dict:
    rows = res["rows"]
    lamps = {k: sum(1 for r in rows if r["lamp"] == k) for k in ("GREEN", "YELLOW", "RED")}
    miss = {k: sum(1 for r in rows if r["l103"][k] == "MISS") for k in ("py_accel", "vdf_net", "ps_tpl")}
    subs = {}
    for r in rows:
        s = subs.setdefault(r["sub"], {"files": 0, "numbered": 0, "py_accel_miss": 0, "vdf_net_miss": 0, "ps_tpl_miss": 0, "red": 0, "entry": 0})
        s["files"] += 1
        s["numbered"] += r["code"] != "未編號"
        s["py_accel_miss"] += r["l103"]["py_accel"] == "MISS"
        s["vdf_net_miss"] += r["l103"]["vdf_net"] == "MISS"
        s["ps_tpl_miss"] += r["l103"]["ps_tpl"] == "MISS"
        s["red"] += r["lamp"] == "RED"
        s["entry"] += bool(r["entry"])
    return {"files": len(rows), "lamps": lamps, "unnumbered": sum(1 for r in rows if r["code"] == "未編號"),
            "l103_miss": miss, "subs": subs, "commands": len(res.get("commands", [])),
            "verdict": "RED" if lamps["RED"] else ("YELLOW" if lamps["YELLOW"] else "GREEN")}


# ---------------------------------------------------------------- 輸出(JSON · CSV · MD 貼回包 · HTML 矩陣)
COLS = ("lamp", "code", "sub", "cat", "name", "version", "desc", "area", "updated", "entry", "flags", "cmds", "l103", "issues", "defs", "run")
HEAD = ("燈", "編號", "子系統", "分類", "檔名", "版本", "說明", "來源", "更新", "入口", "旗標 / 子令", "短令", "L103 三導入", "AST 問題", "定義數", "怎麼跑")

_FILTER_JS = """<script>
(function(){var t=document.getElementById('tbx'),l=document.getElementById('tlamp'),s=document.getElementById('tsub');
function f(){var q=(t.value||'').toLowerCase(),lv=l.value,sv=s.value,n=0;document.querySelectorAll('#main table.m tbody tr').forEach(function(r){
var ok=(!q||r.textContent.toLowerCase().indexOf(q)>=0)&&(!lv||r.cells[0].textContent.indexOf(lv)>=0)&&(!sv||r.cells[2].textContent===sv);r.style.display=ok?'':'none';if(ok)n++;});
document.getElementById('tcnt').textContent=n+' 列';}
[t,l,s].forEach(function(e){e.addEventListener('input',f);});
document.querySelectorAll('table.m thead th').forEach(function(th,i){th.style.cursor='pointer';th.title='點一下排序';th.addEventListener('click',function(){
var tb=th.closest('table').tBodies[0],rs=Array.prototype.slice.call(tb.rows),d=th.dataset.d==='1'?-1:1;th.dataset.d=d===1?'1':'0';
rs.sort(function(a,b){var x=a.cells[i].textContent,y=b.cells[i].textContent,nx=parseFloat(x),ny=parseFloat(y);
return (!isNaN(nx)&&!isNaN(ny)?nx-ny:x.localeCompare(y,'zh-Hant'))*d;});rs.forEach(function(r){tb.appendChild(r);});});});f();})();
</script>"""


def _cell(r: dict, k: str):
    v = r[k]
    if k == "lamp":
        return {"t": v, "s": v}
    if k == "l103":
        return " · ".join(f"{n}:{v[key]}" for key, n in (("py_accel", "PY加速"), ("vdf_net", "VDF網路"), ("ps_tpl", "PS模板")) if v[key] != "—")
    if k == "issues":
        return " ".join(f"{c}×{n}" for c, n in sorted(v.items())) or "—"
    if k == "flags":                                  # 子令在前、旗標在後,一格看完怎麼叫
        both = list(r.get("verbs") or []) + list(v or [])
        return " ".join(both[:8]) + (" …" if len(both) > 8 else "") if both else "—"
    if isinstance(v, list):
        return " ".join(v[:6]) + (" …" if len(v) > 6 else "") if v else "—"
    return str(v) if v not in ("", None) else "—"


def to_md(res: dict, sm: dict, top: int = 40) -> str:
    out = [f"# 工具盤點 · {sm['verdict']} · {res['at']}", "",
           f"- 範圍:{res['scope']} · {'只看尾版' if res['tails_only'] else '全部版本'} · 檔 {sm['files']} · 綠 {sm['lamps']['GREEN']} · 黃 {sm['lamps']['YELLOW']} · 紅 {sm['lamps']['RED']}",
           f"- 未編號 {sm['unnumbered']} · L103 缺:PY 加速器 {sm['l103_miss']['py_accel']} · VDF 網路工具 {sm['l103_miss']['vdf_net']} · PS 模板 {sm['l103_miss']['ps_tpl']} · 短令 {sm['commands']}",
           f"- 全景:{res['panorama']} · 費時 {res['sec']}s", "", "## 紅燈(AST 精準錨點)"]
    reds = [r for r in res["rows"] if r["lamp"] == "RED"]
    out += [f"- {a}" for r in reds[:top] for a in r["anchors"][:2]] or ["- 無"]
    out += ["", "| 子系統 | 檔 | 有號 | 入口 | PY加速缺 | VDF網路缺 | PS模板缺 | 紅 |", "|---|---|---|---|---|---|---|---|"]
    out += [f"| {k} | {v['files']} | {v['numbered']} | {v['entry']} | {v['py_accel_miss']} | {v['vdf_net_miss']} | {v['ps_tpl_miss']} | {v['red']} |"
            for k, v in sorted(sm["subs"].items())]
    return "\n".join(out) + "\n"


def write_reports(res: dict, sm: dict, stamp: str) -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    paths = {}
    js = json.dumps({**res, "summary": sm}, ensure_ascii=False, indent=1)
    for nm in (f"TOOLING_{stamp}.json", "TOOLING_latest.json"):
        (OUT / nm).write_text(js, encoding="utf-8")
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(HEAD + ("路徑", "函數"))
    for r in res["rows"]:
        w.writerow([_cell(r, k) if not isinstance(_cell(r, k), dict) else r[k] for k in COLS] + [r["path"], " ;; ".join(r["functions"])])
    for nm in (f"TOOLING_{stamp}.csv", "TOOLING_latest.csv"):
        (OUT / nm).write_text(buf.getvalue(), encoding="utf-8-sig")
    md = to_md(res, sm)
    for nm in (f"TOOLING_{stamp}.md", "TOOLING_latest.md"):
        (OUT / nm).write_text(md, encoding="utf-8")
    paths["json"], paths["csv"], paths["md"] = OUT / "TOOLING_latest.json", OUT / "TOOLING_latest.csv", OUT / "TOOLING_latest.md"
    paths["html"] = write_html(res, sm, md, stamp)
    return paths


def write_html(res: dict, sm: dict, md: str, stamp: str) -> Path:
    spec_path = _newest("CGC_MDL173_MatrixReportSpec_v*.py")
    spec = _load(spec_path, "_mdl253_spec")
    subs = [[k, v["files"], v["numbered"], v["entry"], v["py_accel_miss"], v["vdf_net_miss"], v["ps_tpl_miss"],
             {"t": str(v["red"]), "s": "RED" if v["red"] else "GREEN"}] for k, v in sorted(sm["subs"].items())]
    body = [spec.html_table(["子系統", "檔", "有號", "有入口", "PY 加速器缺", "VDF 網路工具缺", "PS 模板缺", "紅"], subs,
                            caption="子系統總覽(L103:PY 導入加速器 · VDF 導入網路工具 · PS 導入模板)", num_cols={1, 2, 3, 4, 5, 6})]
    crow = [[c["cmd"], " ".join(c["alias"]) or "—", c["added_in"].replace("Register-VIA-Commands-", "").replace(".ps1", ""),
             c.get("added_at") or "—", " ".join(c["targets"][:3]) or "—", " / ".join(c["vcgc"][:3]) or "—", c["note"] or "—"]
            for c in res.get("commands", [])]
    body.append(spec.html_table(["短令", "別名", "新增於", "日期", "接到", "VCGC 動詞", "說明"], crow,
                                caption=f"短令冊(Register 尾版順點源鏈 · 共 {len(crow)} 個 · 新的在前)"))
    lamps = sorted({r["sub"] for r in res["rows"]})
    body.append("<div id='main'><div class='bar'><input id='tbx' placeholder='篩選:檔名 / 編號 / 說明 / 短令…' style='min-width:22em'> "
                "<select id='tlamp'><option value=''>全部燈</option><option>RED</option><option>YELLOW</option><option>GREEN</option></select> "
                "<select id='tsub'><option value=''>全部子系統</option>" + "".join(f"<option>{html.escape(s)}</option>" for s in lamps) +
                "</select> <span id='tcnt'></span></div>")
    body.append(spec.html_table(list(HEAD), [[_cell(r, k) for k in COLS] for r in res["rows"]],
                                caption="工具矩陣(點表頭排序;燈:紅 = AST 讀不過 · 黃 = 缺 L103 導入 / 有 AST 問題 / 未編號)",
                                num_cols={14}, center_cols={0}) + "</div>" + _FILTER_JS)
    kpis = [{"label": "檔", "value": sm["files"], "state": "NA"}, {"label": "綠", "value": sm["lamps"]["GREEN"], "state": "GREEN"},
            {"label": "黃", "value": sm["lamps"]["YELLOW"], "state": "YELLOW"}, {"label": "紅", "value": sm["lamps"]["RED"], "state": "RED" if sm["lamps"]["RED"] else "GREEN"},
            {"label": "未編號", "value": sm["unnumbered"], "state": "YELLOW" if sm["unnumbered"] else "GREEN"},
            {"label": "短令", "value": sm["commands"], "state": "NA"}]
    payload = {"summary": sm, "rows": [{k: v for k, v in r.items() if k not in ("functions",)} for r in res["rows"]]}
    out = spec.page_html("".join(body), title="VIA 工具盤點矩陣", out=OUT / f"TOOLING_{stamp}.html", md=md, payload=payload, kpis=kpis,
                         subtitle=f"{res['at']} · {res['scope']} · 全景 {res['panorama']} · 編號冊 VIA_NumberBooks · {ENGINE}",
                         law="L103 最高政策三條:PY 導入加速器 · VDF 導入網路工具 · PS 導入模板工具。本頁只讀,不改、不執行任何被掃的檔。")
    latest = OUT / "TOOLING_latest.html"
    latest.write_text(out.read_text(encoding="utf-8"), encoding="utf-8")
    return latest


def _open(p: Path):
    if os.environ.get("VIA_NO_OPEN") or not hasattr(os, "startfile"):
        return
    try:
        os.startfile(str(p))                          # Windows 直開(ShellExecute);容器 / 非 Windows 不開
    except OSError as e:
        print(f"  [頁] 沒自動開({e});自己開:{p}")



# ---------------------------------------------------------------- 單引擎:盤點 · 解析 · 啟動前閘(兩個 SYSTEM MANAGER 共用這一份,不各抄一套)
ENGINE_SPEC = {
    "VDF": {"root": "functional modules/VDF", "rx": re.compile(r"^VDF_(ENG|MDL)\d{2,4}_"), "need_net": True, "family": "vdf", "cmd": "via-vdfeng"},
    "VRN": {"root": "functional modules/VRN", "rx": re.compile(r"^VRN_(ENG|MDL)\d{2,4}_"), "need_net": False, "family": "vrn", "cmd": "via-vrneng"},
}
ENGINE_ID_RX = re.compile(r"^[A-Z]{2,5}_((?:ENG|MDL)\d{2,4})_")


def engines(sub: str, quiet: bool = True) -> list[dict]:
    """子系統的引擎尾版逐支一列(與 scan 同一套欄位)+ eid(ENG229 / MDL002)。"""
    spec = ENGINE_SPEC[sub.upper()]
    pan, ver = panorama_path()
    if pan is None:
        raise RuntimeError(ver)
    _pan_init(str(pan))
    root = VIA / spec["root"]
    files = [f for f in targets([str(root)]) if f.suffix == ".py" and spec["rx"].match(f.name) and not SKIP_RX.search(rel(f))
             and not re.search(r"_sha[0-9a-f]{6,}$", f.stem)]          # _sha… 是去重快照副本,不是另一支引擎
    dates, nums, cmds = git_dates(), number_index(), commands()
    by = {}
    for c in cmds:
        for tg in c["targets"]:
            for key in {family_of(tg).lower(), "_".join(tg.split("_")[:2]).lower()}:
                by.setdefault(key, []).append(c["cmd"])
    named = celeritas_named()
    rows = []
    for f in files:
        r = build_row(f, _card(str(f)), nums.get(rel(f)), dates, by)
        r["eid"] = ENGINE_ID_RX.match(f.name).group(1)
        r["named"] = named.get(r["path"], "")
        rows.append(r)
    return sorted(rows, key=lambda r: (r["eid"], r["family"], -version_of(VIA / r["path"])))


def celeritas_named() -> dict:
    """Celeritas 基線的具名名單(唯讀正典 / 凍結豁免):{VIA 相對路徑: 理由}。名單歸 CGC_MDL183 管,本支只讀。"""
    base = _newest("VIA_CeleritasPolicy_Baseline_v*.json") or (HERE / "VIA_CeleritasPolicy_Baseline_v0100.json")
    try:
        b = json.loads(base.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"  [Celeritas 基線] 讀不到({e});不套具名豁免")
        return {}
    out = {}
    for key, why in (("py_readonly", "正典唯讀本(不准注橋)"), ("py_exempt", "凍結夾具名豁免")):
        for f in (b.get(key) or {}).get("files") or []:
            out[str(f).replace("\\", "/")] = why
    return out


def resolve(rows: list[dict], key: str) -> tuple[dict | None, list[dict]]:
    """229 / ENG229 / MDL002 / 全名 / 名稱片段 → 一支;同號異名或片段命中多支 = 照實回候選,不猜。"""
    k = key.strip()
    if re.fullmatch(r"\d{2,4}", k):
        k = "ENG" + k.zfill(3)
    ku = k.upper()
    hits = [r for r in rows if r["eid"] == ku] or [r for r in rows if r["family"].upper() == family_of(ku).upper()] \
        or [r for r in rows if ku in r["family"].upper()]
    fams = {}
    for r in hits:                                     # 同家族在兩個夾:版號大的贏;同版 engine/ 夾優先
        best = fams.get(r["family"])
        if best is None or (version_of(VIA / r["path"]), "/engine/" in r["path"]) > (version_of(VIA / best["path"]), "/engine/" in best["path"]):
            fams[r["family"]] = r
    cands = list(fams.values())
    return (cands[0] if len(cands) == 1 else None), cands


def gate(row: dict, sub: str) -> dict:
    """啟動前閘:紅 = 不准啟動(讀不過 / 沒有入口 / 缺 L103 導入);黃 = 可以跑但要知道的事。"""
    spec = ENGINE_SPEC[sub.upper()]
    block, warn = [], []
    bad = sorted(c for c in row["issues"] if c in RED_CLS)
    if bad:
        block.append("AST 讀不過:" + " ".join(bad) + "(" + (row["anchors"][0] if row["anchors"] else row["path"]) + ")")
    library = "__main__" not in row["entry"]
    named = row.get("named", "")
    miss = [k for k in ("py_accel", "vdf_net") if row["l103"].get(k) == "MISS" and (k == "py_accel" or spec["need_net"])]
    if miss and named:                                  # 基線具名名單上的檔:不准注橋,照實列黃,不擋
        warn.append(f"缺 {'/'.join(miss)} 橋,但在 Celeritas 基線具名名單:{named}(CGC_MDL183 管;不注橋)")
    elif "py_accel" in miss:
        block.append("缺 PY 加速器橋 [VIA:ACCEL-BRIDGE(L103)→ via-bridge-sweep --subsystems --apply")
    if not named and "vdf_net" in miss:
        block.append("用到網路套件卻缺 VDF 網路工具橋 [VIA:NET-BRIDGE(L103)→ via-bridge-sweep --subsystems --apply")
    if row["code"] == "未編號":
        warn.append("未編號(下一輪 closeout 的 registry-sync + 編號會補)")
    if "--selftest" not in row["flags"] and "selftest" not in row["verbs"]:
        warn.append("沒看到 --selftest(無法先自測再跑)")
    if row.get("netuse"):                              # 原始碼真的匯入網路套件(清單問掃橋器尾版)
        warn.append("會觸網:要在你的視窗自己開 VIA_NET_CONSENT(" + ("已開" if os.environ.get("VIA_NET_CONSENT") == "YES" else "未開 → 引擎會照實 DENY") + ";AI 永不代設)")
    soft = sorted(c for c in row["issues"] if c not in RED_CLS)
    if soft:
        warn.append("AST 提醒:" + " ".join(f"{c}×{row['issues'][c]}" for c in soft))
    lamp = "RED" if block else ("NA" if library else ("YELLOW" if warn else "GREEN"))
    if library and not block:
        warn.insert(0, "沒有 __main__:這支是給別的引擎呼叫的程式庫,不單獨啟動")
    verb = next((v for v in ("status", "run", "scan", "check") if v in row["verbs"]), "")
    return {"sub": sub.upper(), "eid": row["eid"], "family": row["family"], "path": row["path"], "version": row["version"], "code": row["code"],
            "lamp": lamp, "block": block, "warn": warn, "verbs": row["verbs"], "flags": row["flags"], "desc": row["desc"],
            "launch": {"vcgc": ["run", "--family", spec["family"], row["family"]], "short": f"{spec['cmd']} {row['eid']}" + (f" {verb}" if verb else ""),
                       "selftest": f"{spec['cmd']} {row['eid']} --selftest"}}


def list_gates(rows: list[dict], sub: str) -> list[dict]:
    """一個家族一列(多夾副本取 resolve 的那一份,另記副本數);同號異名的引擎號短令改給全名(引擎號會被問候選)。"""
    by_fam = {}
    for r in rows:
        by_fam.setdefault(r["family"], []).append(r)
    picked = []
    for fam, rs in by_fam.items():
        one, _ = resolve(rs, fam)
        g = gate(one or rs[0], sub)
        g["copies"] = len(rs) - 1
        picked.append(g)
    eids = {}
    for g in picked:
        eids.setdefault(g["eid"], []).append(g)
    for eid, gs in eids.items():
        if len(gs) > 1:
            for g in gs:
                g["launch"]["short"] = g["launch"]["short"].replace(f" {eid}", f" {g['family']}", 1)
                g["launch"]["selftest"] = g["launch"]["selftest"].replace(f" {eid}", f" {g['family']}", 1)
                g["warn"].append(f"同號異名:{eid} 還有 " + " · ".join(x["family"] for x in gs if x is not g) + "(短令用全名)")
    return sorted(picked, key=lambda g: (g["eid"], g["family"]))


def engine_main(sub: str, args: list[str], tag: str) -> int:
    """SYSTEM MANAGER 的 `engine` 動詞本體:list · check <引擎> · card <引擎>(都只讀;真正啟動由短令經 VCGC 跑)。"""
    sub = sub.upper()
    verb, rest = (args[0], args[1:]) if args else ("list", [])
    as_json = "--json" in rest
    rest = [a for a in rest if a != "--json"]
    try:
        rows = engines(sub)
    except RuntimeError as e:
        print(json.dumps({"engine_gate": {"sub": sub, "lamp": "RED", "why": str(e)}}, ensure_ascii=False))
        return 1
    if verb == "list":
        gates = list_gates(rows, sub)
        if as_json:
            print(json.dumps({"engines": gates}, ensure_ascii=False))
            return 0
        lamps = {k: sum(1 for g in gates if g["lamp"] == k) for k in ("GREEN", "YELLOW", "RED", "NA")}
        print(f"[{tag} 引擎冊] {sub} 引擎尾版 {len(gates)} 支 · 可啟動 綠 {lamps['GREEN']} · 黃 {lamps['YELLOW']} · 紅(擋)  {lamps['RED']} · 程式庫(不單獨啟動)  {lamps['NA']}"
              f" · 單引擎短令 {ENGINE_SPEC[sub]['cmd']} <引擎號> [子令 / 旗標]")
        for g in gates:
            mark = {"GREEN": "綠", "YELLOW": "黃", "RED": "紅", "NA": "庫"}[g["lamp"]]
            print(f"  {mark} {g['eid']:<7} {g['family'][:44]:<44} {g['version']:<6} {g['code']:<18} → {g['launch']['short']}"
                  + (f"  ✗ {g['block'][0][:60]}" if g["block"] else ""))
        page = write_engine_page(sub, gates, tag)
        print(f"  [頁] {page}")
        return 0 if not lamps["RED"] else 2
    if verb in ("check", "card"):
        if not rest:
            print(f"用法:{verb} <引擎號 | 全名 | 名稱片段>")
            return 3
        row, cands = resolve(rows, rest[0])
        if row is None:
            out = {"sub": sub, "key": rest[0], "lamp": "NODATA" if not cands else "AMBIGUOUS",
                   "candidates": [{"eid": c["eid"], "family": c["family"], "path": c["path"]} for c in cands]}
            print(json.dumps({"engine_gate": out}, ensure_ascii=False))
            if not as_json:
                print(f"  [{tag}] {'找不到' if not cands else '同號異名 / 片段命中多支,請給全名'}:{rest[0]}"
                      + "".join(f"\n     · {c['eid']} {c['family']}  ({c['path']})" for c in cands))
            return 3
        g = gate(row, sub)
        if not as_json:
            print(f"[{tag} 啟動前閘] {g['lamp']} · {g['eid']} {g['family']} {g['version']} · 編號 {g['code']} · {g['path']}")
            print(f"  說明 {g['desc'] or '—'}")
            print(f"  子令 / 旗標 {' '.join(g['verbs'] + g['flags']) or '—'}")
            for b in g["block"]:
                print("  [擋] " + b)
            for w in g["warn"]:
                print("  [黃] " + w)
            print(f"  [啟動] {g['launch']['short']}   (= via-vcgc {' '.join(g['launch']['vcgc'])} …;先自測:{g['launch']['selftest']})")
            if verb == "card":
                print("  [函數] " + " · ".join(row["functions"][:15]) + (" …" if len(row["functions"]) > 15 else ""))
        print(json.dumps({"engine_gate": g}, ensure_ascii=False))
        return {"GREEN": 0, "YELLOW": 2, "RED": 1, "NA": 2}[g["lamp"]]
    print(f"用法:engine list | check <引擎> | card <引擎> [--json]")
    return 2


def write_engine_page(sub: str, gates: list[dict], tag: str) -> Path:
    spec = _load(_newest("CGC_MDL173_MatrixReportSpec_v*.py"), "_mdl253_spec")
    rows = [[{"t": g["lamp"], "s": g["lamp"]}, g["eid"], g["family"], g["version"], g["code"], g["desc"] or "—",
             " ".join(g["verbs"] + g["flags"])[:80] or "—", g["launch"]["short"], "; ".join(g["block"]) or "—", "; ".join(g["warn"]) or "—"] for g in gates]
    lamps = {k: sum(1 for g in gates if g["lamp"] == k) for k in ("GREEN", "YELLOW", "RED")}
    body = spec.html_table(["燈", "引擎號", "家族", "版本", "編號", "說明", "子令 / 旗標", "單引擎啟動", "擋(紅)", "提醒(黃)"], rows,
                           caption=f"{sub} 引擎冊:{len(gates)} 支尾版(點表頭排序)", center_cols={0}) + _FILTER_JS.replace("#main table.m", "table.m")
    body = ("<div id='main'><div class='bar'><input id='tbx' placeholder='篩選:引擎號 / 名稱 / 說明…'> <select id='tlamp'><option value=''>全部燈</option>"
            "<option>RED</option><option>YELLOW</option><option>GREEN</option></select> <select id='tsub'><option value=''>全部</option></select>"
            " <span id='tcnt'></span></div>" + body + "</div>")
    kpis = [{"label": "引擎", "value": len(gates), "state": "NA"}, {"label": "綠", "value": lamps["GREEN"], "state": "GREEN"},
            {"label": "黃", "value": lamps["YELLOW"], "state": "YELLOW"}, {"label": "紅(擋)", "value": lamps["RED"], "state": "RED" if lamps["RED"] else "GREEN"}]
    out = spec.page_html(body, title=f"{sub} 單引擎啟動冊", out=OUT / f"ENGINES_{sub}_latest.html", kpis=kpis,
                         payload={"engines": gates}, md="", subtitle=f"{time.strftime('%Y-%m-%d %H:%M:%S')} · {tag} engine list · {ENGINE}",
                         law="紅 = 啟動前閘擋下(讀不過 / 沒有入口 / 缺 L103 導入);黃 = 能跑但要知道(未編號 / 沒自測 / 要網路同意閘)。")
    return out


# ---------------------------------------------------------------- 動詞
def do_scan(args: list[str]) -> int:
    flags = {a for a in args if a.startswith("--")}
    paths = [a for a in args if not a.startswith("--")]
    res = scan(paths or None, all_versions="--all-versions" in flags)
    if res["state"] != "OK":
        print(json.dumps({"engine": ENGINE, "verb": "scan", "state": "RED", "why": res["why"]}, ensure_ascii=False))
        return 1
    sm = summarize(res)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    paths_out = write_reports(res, sm, stamp)
    print(f"[工具盤點] {sm['verdict']} · 檔 {sm['files']}(綠 {sm['lamps']['GREEN']} · 黃 {sm['lamps']['YELLOW']} · 紅 {sm['lamps']['RED']})"
          f" · 未編號 {sm['unnumbered']} · 短令 {sm['commands']} · {res['sec']}s")
    print(f"  [L103] 缺 PY 加速器 {sm['l103_miss']['py_accel']} · 缺 VDF 網路工具 {sm['l103_miss']['vdf_net']} · 缺 PS 模板 {sm['l103_miss']['ps_tpl']}")
    for k, v in sorted(sm["subs"].items()):
        print(f"  [{k:<8}] 檔 {v['files']:>4} · 有號 {v['numbered']:>4} · 入口 {v['entry']:>4} · 缺 PY加速 {v['py_accel_miss']:>3}"
              f" · 缺 VDF網路 {v['vdf_net_miss']:>3} · 缺 PS模板 {v['ps_tpl_miss']:>3} · 紅 {v['red']}")
    for r in [r for r in res["rows"] if r["lamp"] == "RED"][:15]:
        print("  [紅] " + (r["anchors"][0] if r["anchors"] else r["path"]))
    print(f"  [頁] {paths_out['html']} · 貼回包 {paths_out['md']} · CSV {paths_out['csv']}")
    if "--no-open" not in flags:
        _open(paths_out["html"])
    verdict = {"engine": ENGINE, "verb": "scan", "state": sm["verdict"], "files": sm["files"], "lamps": sm["lamps"],
               "unnumbered": sm["unnumbered"], "l103_miss": sm["l103_miss"], "html": rel(paths_out["html"])}
    print(json.dumps(verdict, ensure_ascii=False))
    return 0 if sm["verdict"] == "GREEN" else 2


def do_cmds(args: list[str]) -> int:
    n = 40
    if "--recent" in args:
        try:
            n = int(args[args.index("--recent") + 1])
        except (IndexError, ValueError):
            print("  [短令冊] --recent 後面要接數字;照預設 40")
    rows = commands(git_dates())
    if "--json" in args:
        print(json.dumps(rows[:n] if n > 0 else rows, ensure_ascii=False, indent=1))
        return 0
    print(f"[短令冊] Register 尾版順點源鏈 · 共 {len(rows)} 個 · 列新的 {min(n, len(rows)) if n > 0 else len(rows)} 個(--recent 0 = 全部)")
    for c in (rows[:n] if n > 0 else rows):
        alias = ("(" + " ".join(c["alias"]) + ")") if c["alias"] else ""
        tgt = " ".join(c["targets"][:2]) or (" / ".join(c["vcgc"][:2]) and "via-vcgc " + " / ".join(c["vcgc"][:2])) or ""
        ver = c["added_in"].replace("Register-VIA-Commands-", "").replace(".ps1", "")
        print(f"  {c['cmd']:<24}{alias:<14} {ver} {c.get('added_at') or '':<10} → {tgt[:60]}" + (f" · {c['note'][:50]}" if c["note"] else ""))
    return 0


def do_card(args: list[str]) -> int:
    if not args:
        print("用法:card <檔>")
        return 2
    pan, ver = panorama_path()
    if pan is None:
        print(json.dumps({"engine": ENGINE, "verb": "card", "state": "RED", "why": ver}, ensure_ascii=False))
        return 1
    _pan_init(str(pan))
    files = targets([args[0]], all_versions=True)
    if not files:
        print(f"找不到:{args[0]}")
        return 2
    dates = git_dates()
    cmds = commands(dates)
    by = {}
    for c in cmds:
        for t in c["targets"]:
            by.setdefault(t.lower(), []).append(c["cmd"])
            by.setdefault("_".join(t.split("_")[:2]).lower(), []).append(c["cmd"])
    row = build_row(files[0], _card(str(files[0])), number_index().get(rel(files[0])), dates, by)
    if "--json" in args:
        print(json.dumps(row, ensure_ascii=False, indent=1))
        return 0
    for k, h in zip(COLS, HEAD):
        c = _cell(row, k)
        print(f"  {h:<10} {c['t'] if isinstance(c, dict) else c}")
    print(f"  {'路徑':<10} {row['path']}")
    print(f"  {'函數':<10} {len(row['functions'])} 個:" + " · ".join(row["functions"][:12]) + (" …" if len(row["functions"]) > 12 else ""))
    for a in row["anchors"][:10]:
        print("  [錨] " + a)
    return 0


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    pan, ver = panorama_path()
    chk("① 全景用鎖版那一支(雜湊相符;不自己取尾版)", pan is not None, ver)
    if pan is not None:
        _pan_init(str(pan))
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        py = t / "VDF_ENG999_Demo_v0101.py"
        py.write_text('"""VDF_ENG999_Demo v0101 — 示範引擎"""\nimport argparse\nimport requests\n'
                      "def main():\n    ap = argparse.ArgumentParser()\n    ap.add_argument('verb', choices=['scan', 'fix'])\n"
                      "    ap.add_argument('--json')\n    return 0\n\nif __name__ == '__main__':\n    import sys\n"
                      "    if sys.argv[1:] == ['--menu']:\n        pass\n    main()\n", encoding="utf-8")
        ps = t / "Demo-Tool-v0100.ps1"
        ps.write_text("<#\n.SYNOPSIS\n  示範 PS 工具\n#>\nparam([string]$RepoPath = '.', [switch]$NoOpen)\nfunction Get-X { 1 }\n", encoding="utf-8")
        (t / "VDF_ENG999_Demo_v0100.py").write_text("x = 1\n", encoding="utf-8")
        tails = targets([str(t)])
        chk("② 尾版律:同家族只留版號最大那支", [p.name for p in tails] == ["Demo-Tool-v0100.ps1", "VDF_ENG999_Demo_v0101.py"], [p.name for p in tails])
        if pan is not None:
            cp, cs = _card(str(py)), _card(str(ps))
            rp = build_row(py, cp, None, {}, {"vdf_eng999_demo": ["via-demo"]})
            rs = build_row(ps, cs, {"code": "VIA-X-ENG001", "sub": "X", "kind": "ENG", "cat": "ps"}, {}, {})
            chk("③ 全景卡:定義樹 + 說明(去掉「名稱 vNNNN —」)", rp["defs"] >= 1 and rp["desc"] == "示範引擎", (rp["defs"], rp["desc"]))
            chk("④ CLI 面:argparse 子令 / 旗標 + sys.argv 字面旗標", {"scan", "fix"} <= set(rp["verbs"]) and {"--json", "--menu"} <= set(rp["flags"]),
                (rp["verbs"], rp["flags"]))
            chk("⑤ L103:PY 缺加速器 · VDF 用到 requests 缺網路橋 = MISS", rp["l103"]["py_accel"] == "MISS" and rp["l103"]["vdf_net"] == "MISS", rp["l103"])
            chk("⑥ PS:.SYNOPSIS 當說明 · param() 當旗標 · 缺模板章 = MISS",
                rs["desc"] == "示範 PS 工具" and "-RepoPath" in rs["flags"] and rs["l103"]["ps_tpl"] == "MISS", (rs["desc"], rs["flags"], rs["l103"]))
            chk("⑦ 編號冊有料就帶號 / 子系統;沒號 = 未編號 + 黃", rs["code"] == "VIA-X-ENG001" and rs["sub"] == "X" and rp["code"] == "未編號" and rp["lamp"] == "YELLOW")
            chk("⑧ 短令按家族接回檔", rp["cmds"] == ["via-demo"], rp["cmds"])
    cmds = commands({})
    names = {c["cmd"] for c in cmds}
    chk("⑨ 短令冊順點源鏈:看得到舊版定義的 via-in / via-vcgc 與尾版的 via-review", {"via-in", "via-vcgc", "via-review"} <= names, len(cmds))
    vin = next((c for c in cmds if c["cmd"] == "via-in"), {})
    chk("⑩ 別名接回(via-in = 進入環境)· 新增於 v0263", "進入環境" in vin.get("alias", []) and vin.get("added_ver") == 263, (vin.get("alias"), vin.get("added_ver")))
    def fake(eid, fam, path, entry=("__main__",), accel="OK", net="OK", netuse=False, named="", code="VIA-X-ENG001", flags=("--selftest",)):
        return {"eid": eid, "family": fam, "path": path, "version": "v0100", "code": code, "entry": list(entry), "flags": list(flags), "verbs": [],
                "issues": {}, "anchors": [], "desc": "", "functions": [], "l103": {"py_accel": accel, "vdf_net": net, "ps_tpl": "—"},
                "netuse": netuse, "named": named}
    rows = [fake("ENG110", "VDF_ENG110_AKShareProbe", "functional modules/VDF/engine/VDF_ENG110_AKShareProbe_v0102.py"),
            fake("ENG110", "VDF_ENG110_USMacroTree", "functional modules/VDF/engine/VDF_ENG110_USMacroTree_v0100.py"),
            fake("ENG229", "VDF_ENG229_CNNFearGreedHistory", "functional modules/VDF/engine/VDF_ENG229_CNNFearGreedHistory_v0100.py")]
    one, _ = resolve(rows, "229")
    none, cands = resolve(rows, "ENG110")
    chk("⑫ 引擎解析:229 → ENG229 一支;同號異名 ENG110 照實回 2 個候選不猜", one and one["eid"] == "ENG229" and none is None and len(cands) == 2)
    red = gate(fake("ENG001", "VDF_ENG001_X", "x.py", accel="MISS", net="MISS", netuse=True), "VDF")
    chk("⑬ 啟動前閘:缺加速器 / 用網路缺網路橋 = 紅擋", red["lamp"] == "RED" and len(red["block"]) == 2, red["block"])
    lib = gate(fake("MDL006", "VRN_MDL006_Lib", "y.py", entry=()), "VRN")
    named = gate(fake("ENG112", "VRN_ENG112_FinancialRead", "z.py", accel="MISS", named="正典唯讀本(不准注橋)"), "VRN")
    chk("⑭ 沒 __main__ = 程式庫 NA(不單獨啟動,不算紅);基線具名唯讀本缺橋 = 黃不擋",
        lib["lamp"] == "NA" and named["lamp"] == "YELLOW" and not named["block"], (lib["lamp"], named["lamp"]))
    lg = {g["family"]: g for g in list_gates(rows, "VDF")}
    chk("⑯ 引擎冊:同號異名的短令改給全名;不重號的照用引擎號",
        lg["VDF_ENG110_AKShareProbe"]["launch"]["short"] == "via-vdfeng VDF_ENG110_AKShareProbe"
        and lg["VDF_ENG229_CNNFearGreedHistory"]["launch"]["short"].startswith("via-vdfeng ENG229"), lg["VDF_ENG110_AKShareProbe"]["launch"]["short"])
    ok_ = gate(rows[2], "VDF")
    chk("⑮ 綠燈引擎給出單引擎短令與 VCGC 路徑", ok_["lamp"] == "GREEN" and ok_["launch"]["short"].startswith("via-vdfeng ENG229")
        and ok_["launch"]["vcgc"] == ["run", "--family", "vdf", "VDF_ENG229_CNNFearGreedHistory"], ok_["launch"])
    text = Path(__file__).read_text(encoding="utf-8")
    chk("⑪ 檔頭 · 加速器橋 · 網路橋在;只收 VCGC;不碰 TA-Lib", PY_MARK in text and NET_MARK in text and "VIA_FROM_VCGC" in text
        and not re.search(r"^\s*(import|from)\s+talib", text, re.M))
    print(f"[工具盤點 v0100] 自測 {sum(ok)}/{len(ok)}")
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "engine": ENGINE, "state": "DENY",
                          "why": "only via-vcgc(VIA_FROM_VCGC=YES);短令 via-tools / via-cmds"}, ensure_ascii=False))
        return 2
    verb, rest = (args[0], args[1:]) if args else ("scan", [])
    if verb == "scan":
        return do_scan(rest)
    if verb == "cmds":
        return do_cmds(rest)
    if verb == "card":
        return do_card(rest)
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
