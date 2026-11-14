#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL253_ToolingInventory v0104 — 薄尾:SSOT 引擎全景(凡出現 SSOT 冊的引擎抓出來 · 彙整 · 參數 · AST 邊界查詢)

操作員令(2026-11-14):「凡出現 ssot 的引擎抓出來 彙整 輸出 參數 輸出 ast 邊界查詢」。
v0100 … v0103 一字不動;本版多一個動詞 `ssot`(只經 VCGC:VIA_FROM_VCGC=YES):
  ssot [map] [--json] [--out <夾>]   全倉引擎尾版(functional modules / supportive modules 全部 .py,加倉根 VIA_MCP_Engine)
                                       逐支 ast.parse(不執行),凡原始碼字面出現 SSOT 冊的引擎一支一列:
                                       系統 · 路徑 · 引用的冊(行 · 所在函式 · 釘版 / 取尾版 / 名字 / 動態 · 讀 / 寫 / 掃)·
                                       參數(argparse 與手寫旗標 · 子令 · 環境變數 · 模組常數 · 引用處函式的簽章)
                                       → 冊彙整(誰在讀 / 寫 · 釘舊版 · 冊不在)· 邊界(引擎系統 ≠ 冊主系統;跨界寫 = 紅)
                                       寫 VIA_Reports/vcgc/ssot_engine_map/SSOT_ENGINE_MAP_latest.{json,html,csv}
  ssot query <字> [--json]           AST 查詢:引擎 / 冊 / 函式 / 旗標 / 環境變數 / 常數名(不分大小寫子字串)→ 命中(檔:行 · 所在函式)
  ssot book <冊族> [--json]          一本冊:引用它的引擎(行 · 函式 · 讀寫 · 釘版)· 冊主系統 · 冊尾版
  ssot engine <引擎> [--json]        一支引擎:SSOT 引用 + 參數卡
  ssot boundary [--json]             跨系統邊界:跨界讀(四系統互相只讀監控 · 允許,照列)· 跨界寫(紅)
系統歸屬:引擎照 v0100 sub_of(檔名前綴 / 夾);冊照「名稱前綴 VDF_ / VIA_VDF_ … → 該系統;否則所在夾 functional modules/<系統>;
  supportive modules/registry → VCGC(中央);其他 supportive → SUP」。
只讀:不執行被讀的檔、不寫他系統的檔(只寫 VCGC 自己的報表夾);零網路;不碰 TA-Lib。
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
import importlib.util
import re
import sys
import tempfile
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL253_ToolingInventory"
TAG = f"{_STEM} v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
import csv as _csv
import datetime as _dt
import html as _html
import io as _io
import json
import os


def _vnum_v0104(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0104(p) < _vnum_v0104(__file__)), key=_vnum_v0104)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)          # v0103 → v0102 → v0101 → v0100
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


def _own(name: str):
    m, seen = PRIOR, []
    while isinstance(m, types.ModuleType) and m not in seen:
        if name in vars(m):
            return m
        seen.append(m)
        m = getattr(m, "PRIOR", None)
    return None


V0100 = _own("targets")
V0101 = _own("books_v0101")
VIA = V0100.VIA
REPO = VIA.parent
OUT_DIR = VIA / "VIA_Reports" / "vcgc" / "ssot_engine_map"
SCAN_ROOTS = ("functional modules", "supportive modules")
REPO_EXTRA = ("VIA_MCP_Engine",)                       # 倉根 VIA 樹外的獨立工具(VCGC-REQ184)
SKIP_EXTRA_RX = re.compile(r"(^|/)(references|VIA_RetiredEngines|_superseded[^/]*|_rebuilds_superseded|tests?|_integration[^/]*)(/|$)", re.I)
SSOT_RX = re.compile(r"SSOT", re.I)
NAME_RX = re.compile(r"^[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)*_SSOT(?:_[A-Za-z0-9]+)*$")
READ_FUNCS = {"open", "read_text", "read_bytes", "load", "loads", "_json", "_load_json", "read_json", "jread", "json_load", "read_book", "_read"}
WRITE_FUNCS = {"write_text", "write_bytes", "dump", "dumps", "_write", "write_json", "save", "jwrite"}
SCAN_FUNCS = {"glob", "rglob", "iglob", "_newest", "newest", "tail", "_tail", "max", "sorted", "fnmatch", "match", "search", "fullmatch"}
SYS_PREFIX = (("VIA_VDF_", "VDF"), ("VIA_VRN_", "VRN"), ("VDF_", "VDF"), ("VRN2_", "VRN"), ("VRN_", "VRN"), ("VQG_", "VQG"),
              ("VAP_", "VAP"), ("VCGC_", "VCGC"), ("CGC_", "VCGC"), ("SUP_", "SUP"))


def rel_any(p: Path) -> str:
    """VIA 相對路徑;倉根(VIA 樹外)的檔回 ../ 相對路徑。"""
    try:
        return Path(p).resolve().relative_to(VIA.resolve()).as_posix()
    except ValueError:
        return Path(os.path.relpath(Path(p).resolve(), VIA.resolve())).as_posix()


def engine_files() -> list:
    """全倉 .py 尾版(同夾同家族留最大版號;沒版號自成一家)。"""
    files = []
    for root in SCAN_ROOTS:
        base = VIA / root
        if base.is_dir():
            files += [q for q in base.rglob("*.py") if q.is_file()]
    for extra in REPO_EXTRA:
        base = REPO / extra
        if base.is_dir():
            files += [q for q in base.glob("*.py") if q.is_file()]
    tails = {}
    for f in files:
        r = rel_any(f)
        if V0100.SKIP_RX.search(r) or SKIP_EXTRA_RX.search(r) or V0100.family_of(f) == _STEM:   # 本工具自己的自測夾具不算
            continue
        key = (str(f.parent), V0100.family_of(f).lower())
        if key not in tails or V0100.version_of(f) > V0100.version_of(tails[key]):
            tails[key] = f
    return sorted(tails.values(), key=rel_any)


def book_owner(stem: str, relpath: str) -> str:
    for pre, sys_ in SYS_PREFIX:
        if stem.startswith(pre):
            return sys_
    if relpath.startswith("functional modules/"):
        return relpath.split("/")[1].upper()
    if relpath.startswith("supportive modules/registry/") or stem.startswith("VIA_"):
        return "VCGC"
    if relpath.startswith("supportive modules/"):
        return "SUP"
    return "?"


def engine_owner(relpath: str) -> str:
    """引擎系統:照 v0100 sub_of(檔名前綴優先,再看 functional modules/<系統>);沒前綴的 registry 模組歸 VCGC、
    其他支援模組歸 SUP(與冊主同一套);VIA 樹外的檔看檔名前綴,倉根 VIA_MCP_Engine 歸 VCGC。"""
    if relpath.startswith("../"):
        return "VCGC" if "VIA_MCP_Engine" in relpath else V0100.sub_of(Path(relpath).name, None)
    sub = V0100.sub_of(relpath, None)
    if sub == "VIA" and relpath.startswith("supportive modules/"):
        return "VCGC" if relpath.startswith("supportive modules/registry/") else "SUP"
    return sub


def _call_name(node) -> str:
    f = getattr(node, "func", None)
    if isinstance(f, ast.Attribute):
        return f.attr
    if isinstance(f, ast.Name):
        return f.id
    return ""


def _open_mode(call) -> str:
    mode = ""
    if len(call.args) >= 2 and isinstance(call.args[1], ast.Constant) and isinstance(call.args[1].value, str):
        mode = call.args[1].value
    for kw in call.keywords:
        if kw.arg == "mode" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
            mode = kw.value.value
    return mode


def ssot_refs(tree, idx: dict) -> dict:
    """AST 掃 SSOT 冊字面:[{book, literal, line, func, mode, access}] + 動態(f-string)次數 + 引用處函式簽章。說明字串不算。"""
    parents, sigs = {}, {}
    for node in ast.walk(tree):
        for ch in ast.iter_child_nodes(node):
            parents[ch] = node

    def qual(n):
        names, cur = [], parents.get(n)
        while cur is not None:
            if isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names.append(cur.name)
            cur = parents.get(cur)
        return ".".join(reversed(names)) or "<module>"

    def func_node(n):
        cur = parents.get(n)
        while cur is not None and not isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
            cur = parents.get(cur)
        return cur

    def access(n):
        cur, depth = n, 0
        while cur is not None and depth < 6:
            p = parents.get(cur)
            if isinstance(p, ast.Call):
                name = _call_name(p)
                if name == "open":
                    return "write" if any(c in _open_mode(p) for c in "wax") else "read"
                if name in WRITE_FUNCS:
                    return "write"
                if name in READ_FUNCS:
                    return "read"
                if name in SCAN_FUNCS:
                    return "scan"
            if isinstance(p, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                break
            cur, depth = p, depth + 1
        return "ref"

    refs, dyn = [], 0
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            txt = "".join(v.value for v in node.values if isinstance(v, ast.Constant) and isinstance(v.value, str))
            if SSOT_RX.search(txt):
                dyn += 1
            continue
        if not (isinstance(node, ast.Constant) and isinstance(node.value, str)) or len(node.value) > 300:
            continue
        if isinstance(parents.get(node), ast.Expr) or isinstance(parents.get(node), ast.JoinedStr):   # 說明字串 / f-string 片段不算
            continue
        val = node.value.replace("\\", "/")
        m = V0101.BOOK_RX_V0101.match(val)
        if m and SSOT_RX.search(m.group("stem")):
            stem, ver = m.group("stem"), m.group("ver") or ""
            mode = "pinned" if ver[2:].isdigit() else ("tail" if ver else "plain")
        elif NAME_RX.match(node.value):
            stem, ver, mode = node.value, "", "name"
        else:
            continue
        hits = sorted(idx.get(stem, []))
        if mode == "name" and not hits:                         # 只是名字、又對不到任何冊 → 是旗標 / 標籤 / 模組名(NO_SSOT_MUTATION 等),不是冊
            continue
        fn = func_node(node)
        if fn is not None and fn.name not in sigs:
            try:
                sigs[fn.name] = f"{fn.name}({ast.unparse(fn.args)})"
            except Exception:  # noqa: BLE001 — 還原不了的簽章就記名字(不中斷整支)
                sigs[fn.name] = fn.name + "(…)"
        tail = hits[-1] if hits else None
        refs.append({"book": stem, "literal": node.value[-100:], "line": node.lineno, "func": qual(node), "mode": mode,
                     "pinned_version": ver[2:] if mode == "pinned" else "", "access": access(node),
                     "tail": tail[1] if tail else "", "tail_version": (f"v{tail[0]:04d}" if tail and tail[0] >= 0 else ("—" if tail else "")),
                     "owner": book_owner(stem, tail[1] if tail else ""), "state": "OK" if tail else "ABSENT"})
    return {"refs": refs, "dynamic": dyn, "signatures": sorted(sigs.values())}


def module_constants(tree) -> list:
    """模組層全大寫常數(字面值 · 120 字內)。"""
    out = []
    for n in getattr(tree, "body", []):
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name) and re.fullmatch(r"[A-Z][A-Z0-9_]{1,40}", n.targets[0].id):
            try:
                txt = repr(ast.literal_eval(n.value))
            except (ValueError, SyntaxError, TypeError):
                txt = "(非字面:%s)" % type(n.value).__name__      # 運算式 / 呼叫:照列名字,值不猜
            out.append({"name": n.targets[0].id, "value": txt if len(txt) <= 120 else txt[:117] + "…", "line": n.lineno})
    return out


def engine_card(p: Path, idx: dict) -> dict | None:
    r = rel_any(p)
    try:
        src = p.read_text(encoding="utf-8-sig", errors="replace")
    except OSError as exc:
        return {"engine": p.name, "path": r, "system": engine_owner(r), "error": f"讀不到 {type(exc).__name__}", "refs": []}
    if not SSOT_RX.search(src):
        return None
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return {"engine": p.name, "path": r, "system": engine_owner(r), "error": f"AST 壞 L{exc.lineno}", "refs": []}
    sr = ssot_refs(tree, idx)
    if not sr["refs"] and not sr["dynamic"]:
        return None
    cli = V0100.cli_surface(src)
    try:
        envs = V0101.env_vars_v0101(tree)
    except Exception as exc:  # noqa: BLE001 — 前版的抽取器出錯就照實記一筆
        envs = [f"(抽取失敗 {type(exc).__name__})"]
    return {"engine": p.name, "path": r, "system": engine_owner(r), "version": (f"v{V0100.version_of(p):04d}" if V0100.version_of(p) >= 0 else "—"),
            "refs": sr["refs"], "dynamic": sr["dynamic"], "books": sorted({x["book"] for x in sr["refs"]}),
            "params": {"flags": cli.get("flags") or [], "verbs": cli.get("verbs") or [], "env": sorted(set(envs)), "constants": module_constants(tree),
                       "signatures": sr["signatures"]}, "error": ""}


def boundary_of(card: dict) -> list:
    out = []
    for x in card.get("refs") or []:
        if x["owner"] in ("?", card["system"]) or x["state"] != "OK":
            continue
        fixture = x["access"] == "write" and re.search(r"(^|\.)(_?selftest|test_\w*|_?self_test)(\.|$)", x["func"] or "")
        crossing = "自測夾具寫" if fixture else ("跨界寫" if x["access"] == "write" else "跨界讀")
        out.append({"engine": card["engine"], "path": card["path"], "engine_system": card["system"], "book": x["book"], "book_system": x["owner"],
                    "line": x["line"], "func": x["func"], "access": x["access"], "kind": crossing, "lamp": "RED" if crossing == "跨界寫" else "GREEN"})
    return out


def build_map(files=None, idx=None) -> dict:
    idx = idx if idx is not None else V0101.book_index_v0101()
    flist = list(files) if files is not None else engine_files()
    cards, errors = [], []
    for p in flist:
        c = engine_card(Path(p), idx)
        if c is None:
            continue
        (errors if c.get("error") else cards).append(c)
    books = {}
    for c in cards:
        for x in c["refs"]:
            b = books.setdefault(x["book"], {"book": x["book"], "owner": x["owner"], "tail": x["tail"], "tail_version": x["tail_version"],
                                             "state": x["state"], "engines": set(), "systems": set(), "read": 0, "write": 0, "scan": 0, "ref": 0,
                                             "pinned_old": []})
            b["engines"].add(c["engine"])
            b["systems"].add(c["system"])
            b[x["access"]] = b.get(x["access"], 0) + 1
            if x["mode"] == "pinned" and x["tail_version"] not in ("", "—") and ("v" + x["pinned_version"]) < x["tail_version"]:
                b["pinned_old"].append(f"{c['engine']}:L{x['line']} 釘 v{x['pinned_version']}(尾 {x['tail_version']})")
    book_rows = [dict(b, engines=sorted(b["engines"]), systems=sorted(b["systems"])) for b in books.values()]
    book_rows.sort(key=lambda b: (-len(b["engines"]), b["book"]))
    bound = [row for c in cards for row in boundary_of(c)]
    by_sys = {}
    for c in cards:
        by_sys[c["system"]] = by_sys.get(c["system"], 0) + 1
    summary = {"scanned": len(flist), "engines": len(cards), "books": len(book_rows), "refs": sum(len(c["refs"]) for c in cards),
               "dynamic": sum(c["dynamic"] for c in cards), "by_system": dict(sorted(by_sys.items())),
               "absent_books": sum(1 for b in book_rows if b["state"] != "OK"), "pinned_old": sum(len(b["pinned_old"]) for b in book_rows),
               "cross_read": sum(1 for x in bound if x["kind"] == "跨界讀"), "cross_write": sum(1 for x in bound if x["kind"] == "跨界寫"),
               "fixture_write": sum(1 for x in bound if x["kind"] == "自測夾具寫"),
               "ast_errors": len(errors)}
    lamp = "RED" if summary["cross_write"] or summary["ast_errors"] else ("YELLOW" if summary["absent_books"] or summary["pinned_old"] else "GREEN")
    return {"schema": "VIA.VCGC.SSOTEngineMap.v1", "engine": TAG, "at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
            "lamp": lamp, "summary": summary, "engines": cards, "books": book_rows, "boundary": bound, "errors": errors}


def query(m: dict, text: str) -> list:
    """AST 查詢:不分大小寫子字串比對 引擎 / 路徑 / 冊 / 函式 / 簽章 / 旗標 / 子令 / 環境變數 / 常數名 → 命中列。"""
    q, hits = text.lower(), []
    for c in m["engines"]:
        if q in c["engine"].lower() or q in c["path"].lower():
            hits.append({"kind": "engine", "engine": c["engine"], "path": c["path"], "line": 0, "func": "", "text": f"{len(c['refs'])} 處 SSOT 引用"})
        for x in c["refs"]:
            if q in x["book"].lower() or q in x["func"].lower() or q in x["literal"].lower():
                hits.append({"kind": "ssot", "engine": c["engine"], "path": c["path"], "line": x["line"], "func": x["func"],
                             "text": f"{x['book']} · {x['mode']} · {x['access']}"})
        prm = c["params"]
        for k in ("flags", "verbs", "env"):
            for v in prm[k]:
                if q in str(v).lower():
                    hits.append({"kind": k, "engine": c["engine"], "path": c["path"], "line": 0, "func": "", "text": str(v)})
        for k in prm["constants"]:
            if q in k["name"].lower():
                hits.append({"kind": "constant", "engine": c["engine"], "path": c["path"], "line": k["line"], "func": "<module>", "text": f"{k['name']} = {k['value']}"})
        for s in prm["signatures"]:
            if q in s.lower():
                hits.append({"kind": "signature", "engine": c["engine"], "path": c["path"], "line": 0, "func": s.split("(", 1)[0], "text": s})
    return hits


CSS = (":root{--bg:#f8f7f2;--fg:#26312f;--panel:#f1f3ec;--card:#fffefb;--line:#dedfd5;--th:#eeeee7;--mut:#5f6b67;--g:#16a34a;--y:#f59e0b;--r:#dc2626}"
       "@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#141817;--fg:#e6ebe8;--panel:#1b201f;--card:#1f2523;--line:#2f3734;--th:#252b29;--mut:#9aa6a1}}"
       ":root[data-theme=dark]{--bg:#141817;--fg:#e6ebe8;--panel:#1b201f;--card:#1f2523;--line:#2f3734;--th:#252b29;--mut:#9aa6a1}"
       "*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:12px/1.5 Inter,'Segoe UI','Noto Sans CJK TC','Microsoft JhengHei',sans-serif}"
       "main{max-width:1280px;margin:0 auto;padding:16px}h1{font-size:18px;margin:4px 0 2px}h2{font-size:14px;margin:18px 0 6px}.mut{color:var(--mut)}"
       ".cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px;margin:10px 0}"
       ".c{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:8px 10px}.c b{display:block;font-size:18px}"
       ".tbl{overflow-x:auto;border:1px solid var(--line);border-radius:8px;background:var(--card)}"
       "table{border-collapse:collapse;width:100%;font-size:11.5px}th{background:var(--th);text-align:left;font-size:10.5px;position:sticky;top:0}"
       "th,td{padding:5px 8px;border-bottom:1px solid var(--line);vertical-align:top}"
       "input{width:100%;max-width:420px;padding:6px 8px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg)}"
       ".l{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:4px}.GREEN{background:var(--g)}.YELLOW{background:var(--y)}.RED{background:var(--r)}"
       "code{font-size:11px;overflow-wrap:anywhere}td.p{min-width:260px;max-width:420px}")


def write_outputs(m: dict, out_dir: Path | None = None) -> dict:
    out = Path(out_dir or OUT_DIR)
    out.mkdir(parents=True, exist_ok=True)
    jp, hp, cp = out / "SSOT_ENGINE_MAP_latest.json", out / "SSOT_ENGINE_MAP_latest.html", out / "SSOT_ENGINE_MAP_latest.csv"
    jp.write_text(json.dumps(m, ensure_ascii=False, indent=1, default=list), encoding="utf-8")
    buf = _io.StringIO()
    w = _csv.writer(buf)
    w.writerow(["system", "engine", "path", "book", "book_system", "line", "func", "mode", "access", "tail_version", "state"])
    for c in m["engines"]:
        for x in c["refs"]:
            w.writerow([c["system"], c["engine"], c["path"], x["book"], x["owner"], x["line"], x["func"], x["mode"], x["access"], x["tail_version"], x["state"]])
    cp.write_text("﻿" + buf.getvalue(), encoding="utf-8")
    e = _html.escape
    s = m["summary"]
    eng_rows = "".join(
        f"<tr><td>{e(c['system'])}</td><td class='p'><code>{e(c['path'])}</code></td><td>{len(c['refs'])}</td><td>{c['dynamic']}</td>"
        f"<td>{e(' · '.join(c['books'][:8]))}{' …' if len(c['books']) > 8 else ''}</td><td>{e(' '.join(c['params']['flags'][:10]))}</td>"
        f"<td>{e(' '.join(c['params']['env'][:6]))}</td><td>{len(c['params']['constants'])}</td></tr>"
        for c in sorted(m["engines"], key=lambda c: (-len(c["refs"]), -c["dynamic"], c["path"])))
    book_rows = "".join(
        f"<tr><td><span class='l {'GREEN' if b['state'] == 'OK' and not b['pinned_old'] else ('YELLOW' if b['state'] == 'OK' else 'RED')}'></span>{e(b['book'])}</td>"
        f"<td>{e(b['owner'])}</td><td>{e(b['tail_version'])}</td><td>{len(b['engines'])}</td><td>{e(' · '.join(b['systems']))}</td>"
        f"<td>{b.get('read', 0)}/{b.get('write', 0)}/{b.get('scan', 0)}/{b.get('ref', 0)}</td><td>{e('; '.join(b['pinned_old'][:3]))}</td></tr>" for b in m["books"])
    bnd_rows = "".join(
        f"<tr><td><span class='l {x['lamp']}'></span>{e(x['kind'])}</td><td>{e(x['engine_system'])} → {e(x['book_system'])}</td>"
        f"<td><code>{e(x['path'])}:{x['line']}</code></td><td>{e(x['func'])}</td><td>{e(x['book'])}</td><td>{e(x['access'])}</td></tr>"
        for x in sorted(m["boundary"], key=lambda x: (x["lamp"] != "RED", x["engine_system"], x["engine"])))
    cards = [(s["engines"], "出現 SSOT 的引擎"), (s["books"], "被引用的 SSOT 冊"), (s["refs"], "字面引用處"), (s["dynamic"], "動態冊名(f-string)"),
             (s["cross_read"], "跨界讀(允許)"), (s["cross_write"], "跨界寫(紅)"), (s["fixture_write"], "自測夾具寫(暫存夾)"), (s["pinned_old"], "釘舊版"), (s["absent_books"], "冊不在"), (s["ast_errors"], "AST 壞")]
    page = ("<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>SSOT 引擎全景</title><style>{CSS}</style></head><body><main>"
            f"<h1><span class='l {m['lamp']}'></span>SSOT 引擎全景</h1><div class='mut'>{e(m['engine'])} · {e(m['at'])} · 掃 {s['scanned']} 支尾版 · 只讀 AST(不執行被讀的檔)</div>"
            "<div class='cards'>" + "".join(f"<div class='c'><b>{n}</b>{e(t)}</div>" for n, t in cards) + "</div>"
            f"<div class='mut'>各系統引擎數:{e(' · '.join(f'{k} {v}' for k, v in s['by_system'].items()))}</div>"
            "<h2>引擎(凡出現 SSOT)</h2><input id='q' placeholder='篩選:系統 / 路徑 / 冊名 / 旗標 / 環境變數' oninput='f()'>"
            "<div class='tbl'><table id='t'><thead><tr><th>系統</th><th>引擎</th><th>字面引用</th><th>動態名</th><th>SSOT 冊</th><th>旗標</th><th>環境變數</th><th>常數</th></tr></thead>"
            f"<tbody>{eng_rows}</tbody></table></div>"
            "<h2>SSOT 冊彙整(讀 / 寫 / 掃 / 名字)</h2><div class='tbl'><table><thead><tr><th>冊</th><th>冊主</th><th>尾版</th><th>引擎數</th><th>系統</th>"
            f"<th>讀/寫/掃/名</th><th>釘舊版</th></tr></thead><tbody>{book_rows}</tbody></table></div>"
            "<h2>邊界(引擎系統 ≠ 冊主系統)</h2><div class='tbl'><table><thead><tr><th>類別</th><th>方向</th><th>位置</th><th>函式</th><th>冊</th><th>存取</th></tr></thead>"
            f"<tbody>{bnd_rows}</tbody></table></div>"
            "<p class='mut'>AST 查詢:<code>via-vcgc run CGC_MDL253_ToolingInventory ssot query &lt;字&gt;</code> · 一本冊 <code>ssot book &lt;冊族&gt;</code> · "
            "一支引擎 <code>ssot engine &lt;引擎&gt;</code> · 邊界 <code>ssot boundary</code></p></main>"
            "<script>function f(){var q=document.getElementById('q').value.toLowerCase();"
            "document.querySelectorAll('#t tbody tr').forEach(function(r){r.style.display=r.textContent.toLowerCase().indexOf(q)>=0?'':'none'})}</script></body></html>")
    hp.write_text(page, encoding="utf-8")
    return {"json": str(jp), "html": str(hp), "csv": str(cp)}


def _line(m: dict, files: dict | None = None) -> str:
    s = m["summary"]
    return ("[SSOT 引擎全景] %s · 掃 %d 支 · 出現 SSOT 的引擎 %d(%s)· 冊 %d · 引用 %d · 動態 %d · 跨界讀 %d · 跨界寫 %d · 釘舊版 %d · 冊不在 %d · AST 壞 %d%s" % (
        m["lamp"], s["scanned"], s["engines"], " · ".join(f"{k} {v}" for k, v in s["by_system"].items()), s["books"], s["refs"], s["dynamic"],
        s["cross_read"], s["cross_write"], s["pinned_old"], s["absent_books"], s["ast_errors"], (" · 頁 " + files["html"]) if files else ""))


def ssot_main(args: list) -> int:
    js = "--json" in args
    rest = [a for a in args if a != "--json"]
    out = None
    if "--out" in rest:
        i = rest.index("--out")
        out = rest[i + 1] if i + 1 < len(rest) else None
        rest = rest[:i] + rest[i + 2:]
    verb = rest[0] if rest else "map"
    if verb not in ("map", "query", "book", "engine", "boundary") or (verb in ("query", "book", "engine") and len(rest) < 2):
        print("用法:ssot [map] [--json] [--out 夾] | ssot query <字> | ssot book <冊族> | ssot engine <引擎> | ssot boundary")
        return 2
    m = build_map()
    if verb == "map":
        files = write_outputs(m, out)
        print(json.dumps({k: v for k, v in m.items() if k in ("lamp", "summary")}, ensure_ascii=False, indent=1) if js else _line(m, files))
        return 0 if m["lamp"] != "RED" else 1
    if verb == "query":
        hits = query(m, " ".join(rest[1:]))
        if js:
            print(json.dumps(hits, ensure_ascii=False, indent=1))
        else:
            for h in hits[:200]:
                print("  %-9s %s%s · %s · %s" % (h["kind"], h["path"], (":%d" % h["line"]) if h["line"] else "", h["func"] or "—", h["text"]))
            print("[SSOT 查詢] 「%s」命中 %d 處%s" % (" ".join(rest[1:]), len(hits), "(只印前 200)" if len(hits) > 200 else ""))
        return 0
    if verb == "book":
        want = rest[1].lower()
        bs = [b for b in m["books"] if want in b["book"].lower()]
        uses = [{"engine": c["engine"], "path": c["path"], "system": c["system"], "line": x["line"], "func": x["func"], "mode": x["mode"], "access": x["access"]}
                for c in m["engines"] for x in c["refs"] if want in x["book"].lower()]
        print(json.dumps({"books": bs, "uses": uses}, ensure_ascii=False, indent=1, default=list) if js else
              "\n".join(["  %s · 冊主 %s · 尾版 %s · 引擎 %d" % (b["book"], b["owner"], b["tail_version"], len(b["engines"])) for b in bs]
                        + ["    %s:%d · %s · %s · %s" % (u["path"], u["line"], u["func"], u["mode"], u["access"]) for u in uses[:200]]))
        return 0 if bs else 2
    if verb == "engine":
        want = rest[1].lower()
        cs = [c for c in m["engines"] if want in c["engine"].lower() or want in c["path"].lower()]
        print(json.dumps(cs, ensure_ascii=False, indent=1) if js else "\n".join(
            "  %s(%s)· SSOT %d 處 · 冊 %s · 旗標 %s · 環境變數 %s · 常數 %d · 簽章 %s" % (
                c["path"], c["system"], len(c["refs"]), ", ".join(c["books"]), " ".join(c["params"]["flags"]) or "—", " ".join(c["params"]["env"]) or "—",
                len(c["params"]["constants"]), "; ".join(c["params"]["signatures"][:4]) or "—") for c in cs))
        return 0 if cs else 2
    b = m["boundary"]
    print(json.dumps(b, ensure_ascii=False, indent=1) if js else "\n".join(
        ["  %-5s %s %s → %s · %s:%d · %s · %s" % (x["lamp"], x["kind"], x["engine_system"], x["book_system"], x["path"], x["line"], x["func"], x["book"]) for x in b]
        + ["[SSOT 邊界] 跨界讀 %d(允許)· 跨界寫 %d(紅)" % (m["summary"]["cross_read"], m["summary"]["cross_write"])]))
    return 1 if m["summary"]["cross_write"] else 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["--selftest"]:
        return selftest()
    if argv[:1] == ["ssot"]:
        if os.environ.get("VIA_FROM_VCGC") != "YES":
            print(json.dumps({"via": "vcgc", "engine": TAG, "state": "DENY", "why": "only via-vcgc(VIA_FROM_VCGC=YES)"}, ensure_ascii=False))
            return 2
        return ssot_main(argv[1:])
    return PRIOR.main(argv)


SAMPLE_V0104 = "\n".join([
    '"""說明字串裡的 VDF_X_SSOT_v0100.json 不算引用"""',
    "import argparse, json, os",
    "from pathlib import Path",
    'BOOK_GLOB = "VDF_InputUniverse_SSOT_v[0-9][0-9][0-9][0-9].json"',
    "LIMIT = 5",
    "",
    "",
    "def load(home):",
    '    """函式說明裡的 VIA_Numbering_SSOT_v0100.json 也不算"""',
    '    a = json.loads(Path(home, "VIA_Numbering_SSOT_v0100.json").read_text())',
    "    b = sorted(Path(home).glob(BOOK_GLOB))",
    '    with open(home + "/VRN_FieldRules_SSOT_v0101.json", "w") as fh:',
    '        fh.write("x")',
    '    fam = "VDF_TableHeader_SSOT"',
    '    dyn = f"{fam}_v0100.json SSOT"',
    '    return a, b, os.environ.get("VIA_HOME"), dyn',
    "",
    "",
    'if __name__ == "__main__":',
    "    ap = argparse.ArgumentParser()",
    '    ap.add_argument("--home", default=".")',
    ""])


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)[:300]) if note and not cond else ''}", flush=True)

    print(f"=== {TAG} · 薄尾自測(SSOT 引擎全景 · 參數 · AST 邊界查詢)===", flush=True)
    tree = ast.parse(SAMPLE_V0104)
    idx = {"VDF_InputUniverse_SSOT": [(103, "functional modules/VDF/VDF_InputUniverse_SSOT_v0103.json"), (104, "functional modules/VDF/VDF_InputUniverse_SSOT_v0104.json")],
           "VIA_Numbering_SSOT": [(100, "supportive modules/registry/VIA_Numbering_SSOT_v0100.json")],
           "VRN_FieldRules_SSOT": [(101, "supportive modules/registry/VRN_FieldRules_SSOT_v0101.json")]}
    sr = ssot_refs(tree, idx)
    got = {x["book"]: x for x in sr["refs"]}
    idx = dict(idx, VDF_TableHeader_SSOT=[(100, "functional modules/VDF/registry/VDF_TableHeader_SSOT_v0100.json")])
    sr = ssot_refs(tree, idx)
    got = {x["book"]: x for x in sr["refs"]}
    lab = ssot_refs(ast.parse('FLAG = "NO_SSOT_MUTATION"\n'), idx)
    chk("① AST 抓 SSOT 字面:glob 尾版(常數)· 釘版讀(json.loads)· 釘版寫(open 'w')· 名字(對得到冊才算;NO_SSOT_MUTATION 這種標籤不算)· 說明字串不算 · f-string 記動態 · 行號與所在函式",
        set(got) == {"VDF_InputUniverse_SSOT", "VIA_Numbering_SSOT", "VRN_FieldRules_SSOT", "VDF_TableHeader_SSOT"}
        and got["VDF_InputUniverse_SSOT"]["mode"] == "tail" and got["VIA_Numbering_SSOT"]["mode"] == "pinned" and got["VIA_Numbering_SSOT"]["access"] == "read"
        and got["VRN_FieldRules_SSOT"]["access"] == "write" and got["VDF_TableHeader_SSOT"]["mode"] == "name" and sr["dynamic"] == 1
        and got["VIA_Numbering_SSOT"]["func"] == "load" and got["VIA_Numbering_SSOT"]["line"] == 10 and "load(home)" in sr["signatures"]
        and not lab["refs"],
        (sorted(got), {k: (v["mode"], v["access"], v["line"], v["func"]) for k, v in got.items()}, sr["dynamic"], sr["signatures"]))
    chk("② 冊主:名稱前綴 VDF_ → VDF · VRN_ → VRN · VIA_ / registry → VCGC · functional modules/<系統> → 該系統",
        book_owner("VDF_X_SSOT", "") == "VDF" and book_owner("VRN_FieldRules_SSOT", "supportive modules/registry/x.json") == "VRN"
        and book_owner("VIA_Numbering_SSOT", "supportive modules/registry/x.json") == "VCGC" and book_owner("Foo_SSOT", "functional modules/VQG/x.json") == "VQG")
    with tempfile.TemporaryDirectory(prefix="cgc253_v0104_") as td:
        d = Path(td)
        fp = d / "VDF_ENG900_Demo_v0100.py"
        fp.write_text(SAMPLE_V0104, encoding="utf-8")
        (d / "Plain_v0100.py").write_text("X = 1\n", encoding="utf-8")
        card = engine_card(fp, idx)
        chk("③ 參數卡:旗標 --home · 環境變數 VIA_HOME · 模組常數 BOOK_GLOB / LIMIT · 簽章 load(home);沒提 SSOT 的檔不出卡",
            card and "--home" in card["params"]["flags"] and "VIA_HOME" in card["params"]["env"]
            and {"BOOK_GLOB", "LIMIT"} <= {k["name"] for k in card["params"]["constants"]} and engine_card(d / "Plain_v0100.py", idx) is None, card and card["params"])
        m = build_map(files=[fp, d / "Plain_v0100.py"], idx=idx)
        bd = {(x["book"], x["kind"]) for x in m["boundary"]}
        chk("④ 邊界:VDF 引擎讀 VCGC 中央冊 = 跨界讀(允許 · 綠)· 寫 VRN 冊 = 跨界寫(紅)· 自己系統的冊不列 · 總燈 RED",
            ("VIA_Numbering_SSOT", "跨界讀") in bd and ("VRN_FieldRules_SSOT", "跨界寫") in bd and not any(b == "VDF_InputUniverse_SSOT" for b, _ in bd)
            and m["lamp"] == "RED" and m["summary"]["cross_write"] == 1, (bd, m["lamp"]))
        bk = {b["book"]: b for b in m["books"]}
        chk("⑤ 冊彙整:引擎數 · 讀寫掃計數 · 尾版;釘 v0100 的 VIA_Numbering 尾版就是 v0100 → 不算釘舊版",
            bk["VIA_Numbering_SSOT"]["read"] == 1 and bk["VRN_FieldRules_SSOT"]["write"] == 1 and not bk["VIA_Numbering_SSOT"]["pinned_old"]
            and bk["VDF_InputUniverse_SSOT"]["tail_version"] == "v0104", bk)
        hits = query(m, "numbering")
        hits2 = query(m, "VIA_HOME")
        chk("⑥ AST 查詢:冊名 → 檔:行 · 所在函式;環境變數名也查得到",
            any(h["kind"] == "ssot" and h["line"] == 10 and h["func"] == "load" for h in hits) and any(h["kind"] == "env" for h in hits2), (hits, hits2))
        fx = d / "VDF_ENG901_Fixture_v0100.py"
        fx.write_text("def selftest():\n    with open('/tmp/x/VRN_FieldRules_SSOT_v0101.json', 'w') as fh:\n        fh.write('x')\n", encoding="utf-8")
        mf = build_map(files=[fx], idx=idx)
        chk("④b 自測函式裡寫冊(夾具寫到暫存夾)→ 記「自測夾具寫」、不算跨界寫(不紅)· 沒前綴的 registry 模組歸 VCGC、其他支援模組歸 SUP",
            [x["kind"] for x in mf["boundary"]] == ["自測夾具寫"] and mf["summary"]["cross_write"] == 0 and mf["lamp"] != "RED"
            and engine_owner("supportive modules/registry/VIA_Panorama_v0105.py") == "VCGC" and engine_owner("supportive modules/VIA_TempSpill_v0100.py") == "SUP",
            (mf["boundary"], mf["lamp"]))
        files = write_outputs(m, d / "out")
        page = Path(files["html"]).read_text(encoding="utf-8")
        chk("⑦ 輸出 json / html / csv(寫到指定夾)· html 有引擎表 · 冊彙整 · 邊界表 · 深淺色",
            all(Path(files[k]).is_file() for k in ("json", "html", "csv")) and "SSOT 冊彙整" in page and "邊界" in page and "prefers-color-scheme:dark" in page
            and json.loads(Path(files["json"]).read_text(encoding="utf-8"))["summary"]["engines"] == 1)
    real = build_map()
    rs = real["summary"]
    names = {c["engine"] for c in real["engines"]}
    chk("⑧ 實樹:全倉掃完不炸(掃 %d 支)· 出現 SSOT 的引擎 %d 支(%s)· 冊 %d · 已知引擎在(CGC_MDL237 尾版 · VDF_SSOTSync · ENG087 尾版)"
        % (rs["scanned"], rs["engines"], " · ".join(f"{k} {v}" for k, v in rs["by_system"].items()), rs["books"]),
        rs["engines"] > 50 and any(n.startswith("CGC_MDL237_NumberingSystem_v") for n in names) and "VDF_SSOTSync_v0100.py" in names
        and any(n.startswith("VDF_ENG087_MarketListGovernance_v") for n in names), sorted(names)[:10])
    src2 = Path(__file__).read_text(encoding="utf-8")
    body = src2.split("def selftest", 1)[0]
    chk("⑨ 加速器橋 · 網路工具橋在;只 ast.parse 不執行被讀的檔;寫檔只在 VCGC 報表夾(write_outputs 三處);不碰 TA-Lib",
        "[VIA:ACCEL-BRIDGE" in src2 and "[VIA:NET-BRIDGE" in src2 and not re.search(r"^\s*(import|from)\s+talib", src2, re.M)
        and "exec(" not in body and body.count(".write_text(") == 3)
    import contextlib
    buf = _io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = PRIOR.selftest()
    for ln in [x for x in buf.getvalue().splitlines() if "[計]" in x][-3:]:
        print("  ── 前版 " + ln.strip()[:200], flush=True)
    chk("⑩ 前版 v0103 自測 rc 0", rc == 0, "rc %s" % rc)
    good = all(ok)
    print(f"  [計] {TAG} 本版 {sum(ok)}/{len(ok)} · 前版 {'PASS' if rc == 0 else 'rc ' + str(rc)} · 合計 {'PASS' if good else 'FAIL'}", flush=True)
    return 0 if good else 1


if __name__ == "__main__":
    raise SystemExit(main())
