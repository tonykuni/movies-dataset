#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-ENG009 · VRN_AstId_v0100 v0100 · REGISTRY AST 編號注入 =====
# AST 注入（只加註解，AST 不變）：類別 0 · 函式 15；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""
VRN_AstId v0100 -- every VRN module, class and function gets a number, a class and a description, injected by AST.

Operator 2026-10-10: 「注入AST 分類說明編號 · 所有引擎編號版本註冊 · 目前邏輯不可動」.

How:
  * the AST of each file lists its modules, classes and functions in source order;
  * each one gets a stable ID in ssot/VRN_ID_SSOT_v0100.json, in the same shape as the central hierarchy
    (VIA-<subsystem>-ENG001-FNC001) but issued by VRN itself: VRN-ENG001, VRN-ENG001-FNC045 ...
    IDs are never recycled: a function that disappears is marked RETIRED and its number is not given again;
  * the IDs are injected as comments only -- a header block per file and one tag line above each def/class --
    so the program does not change: before anything is written, ast.dump() of the new text must equal ast.dump()
    of the old text, otherwise the file is left alone and the run reports it;
  * the book also carries each module's version and description, and each function's class (TEST / GATE /
    EXTRACT / VALIDATE / IO / BUILD / REPORT / ENTRY / INIT / CLASS / LOGIC) and the first line of its docstring.

PowerShell launchers get the header only (no Python AST for them).  Byte copies in ssot/ and the frozen intake
package are never touched.  Stdlib only.
"""

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
import json
import re
import sys
from pathlib import Path

ASTID_VERSION = "v0100"
VRN_ROOT = Path(__file__).resolve().parents[1]
ID_BOOK = VRN_ROOT / "ssot" / "VRN_ID_SSOT_v0100.json"
HEADER_OPEN = "# ===== [VRN:ID:v0100]"
HEADER_CLOSE = "# ===== [VRN:ID:END] ====="
TAG_PREFIX = "# [VRN-ID] "
# built, not quoted: a quoted "<name>.py" counts as a call for the central G08 cycle gate, and VRN_Main calls this module
MAIN_FILE = "VRN_Main_" + "v0100.py"
TAG_RX = re.compile(r"^[ \t]*# \[VRN-ID\] VRN-[A-Z]{3}\d{3}-[A-Z]{3}\d{3} · [A-Z]+[ \t]*\r?\n", re.M)
HEADER_RX = re.compile(r"^# ===== \[VRN:ID:v0100\][^\n]*\n(?:#[^\n]*\n)*?# ===== \[VRN:ID:END\] =====[ \t]*\r?\n", re.M)
# fixed engine order: numbers are issued once in this order, later engines get the next free number
ENGINE_ORDER = ("engine/VIA_VRN_FirstPageEngine.py", "engine/VRN_Integrated_ReportDatabase_Engine.py",
                "engine/VRN_Evidence_Core.py", "engine/VRN_AutoTestLoop.py", "engine/VIA_TW_Ticker_Master_v0210.py",
                "engine/VRN_PanoramaProbe.py", "engine/VRN_BookCheck_v0100.py", "engine/VRN_TempStore_v0100.py",
                "engine/VRN_AstId_v0100.py")
MODULE_CATEGORY = {
    MAIN_FILE: ("ENTRY", "獨立 MAIN：實測、自測、建冊、驗冊"),
    "engine/VIA_VRN_FirstPageEngine.py": ("EXTRACT", "首頁判讀"),
    "engine/VRN_Integrated_ReportDatabase_Engine.py": ("DATABASE", "整批入庫"),
    "engine/VRN_Evidence_Core.py": ("RULES", "兩支引擎共用的證據規則"),
    "engine/VRN_AutoTestLoop.py": ("TEST-LOOP", "實測閘門 G01–G13"),
    "engine/VIA_TW_Ticker_Master_v0210.py": ("SSOT-TICKER", "台股代碼主檔"),
    "engine/VRN_PanoramaProbe.py": ("PROBE", "全景探針"),
    "engine/VRN_BookCheck_v0100.py": ("MEASURE", "收來的冊當量尺"),
    "engine/VRN_TempStore_v0100.py": ("RUNTIME", "TEMP 與刪除原則"),
    "engine/VRN_AstId_v0100.py": ("REGISTRY", "AST 編號注入"),
}
LAYER_OF = {"MAN": "MAIN", "ENG": "ENGINE", "TST": "TEST", "PSL": "LAUNCHER"}
ITEM_RULES = (
    ("TEST", lambda n: n.startswith("test")),
    ("ENTRY", lambda n: n in ("main", "selftest") or n.startswith("def_cmd_")),
    ("GATE", lambda n: n.startswith(("def_gate_", "gate_", "def_check_"))),
    ("EXTRACT", lambda n: n.startswith(("extract_", "parse_", "page_", "def_parse")) or n.endswith("_evidence")),
    ("VALIDATE", lambda n: n.startswith(("validate_", "check_", "compare_", "verify_", "def_compare", "def_verify")) or "verdict" in n),
    ("IO", lambda n: n.startswith(("load_", "read_", "write_", "def_load", "def_read", "def_write", "save_", "open_", "close_",
                                   "put_", "get_json"))),
    ("BUILD", lambda n: n.startswith(("build_", "def_build_", "make_"))),
    ("REPORT", lambda n: n.startswith(("render", "def_render", "report", "def_report")) or n.endswith("_html")),
    ("INIT", lambda n: n.startswith("__") and n.endswith("__")),
)


# [VRN-ID] VRN-ENG009-FNC001 · LOGIC
def item_category(kind: str, name: str) -> str:
    for category, rule in ITEM_RULES:
        if rule(name):
            return category
    return "CLASS" if kind == "CLS" else "LOGIC"


# [VRN-ID] VRN-ENG009-FNC002 · LOGIC
def targets(root: Path = VRN_ROOT):
    """(rel, layer) of every file that is numbered: MAIN, engines, tests, launchers (never ssot/ copies or references/)."""
    out = [(MAIN_FILE, "MAN")] if (root / MAIN_FILE).is_file() else []
    out += [(p.relative_to(root).as_posix(), "ENG") for p in sorted((root / "engine").glob("*.py"))]
    out += [(p.relative_to(root).as_posix(), "TST") for p in sorted((root / "tests").glob("*.py"))]
    out += [(p.relative_to(root).as_posix(), "PSL") for p in sorted(root.glob("*.ps1"))]
    return out


# [VRN-ID] VRN-ENG009-FNC003 · LOGIC
def strip(text: str) -> str:
    """The file without any VRN-ID header or tag (what the program is; comments only were added).  A leading BOM stays."""
    bom = "\ufeff" if text.startswith("\ufeff") else ""
    return bom + TAG_RX.sub("", HEADER_RX.sub("", text[len(bom):]))


# [VRN-ID] VRN-ENG009-FNC015 · IO
def read_exact(path: Path) -> str:
    """The text with its own line endings (no newline translation), so a rewrite keeps CRLF where CRLF was."""
    with open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


# [VRN-ID] VRN-ENG009-FNC004 · LOGIC
def split_lines(text: str):
    """Lines as the Python tokenizer counts them (\n only; form feeds and U+2028 stay inside their line)."""
    return re.findall(r"[^\n]*\n|[^\n]+$", text)


# [VRN-ID] VRN-ENG009-FNC005 · LOGIC
def items_of(tree: ast.AST):
    """(kind, qualname, insert_line, indent_col, doc) for every class / function, in source order."""
    out = []

    # [VRN-ID] VRN-ENG009-FNC006 · LOGIC
    def visit(node, stack):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                kind = "CLS" if isinstance(child, ast.ClassDef) else "FNC"
                first = min([d.lineno for d in child.decorator_list] + [child.lineno])
                doc = (ast.get_docstring(child) or "").strip().splitlines()
                out.append((kind, ".".join(stack + [child.name]), first, child.name, doc[0][:120] if doc else ""))
                visit(child, stack + [child.name])
            else:
                visit(child, stack)
    visit(tree, [])
    return sorted(out, key=lambda x: x[2])


# [VRN-ID] VRN-ENG009-FNC007 · LOGIC
def module_version(tree: ast.AST, rel: str) -> str:
    for node in getattr(tree, "body", []):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name.endswith("_VERSION") and name != "SCHEMA_VERSION" and isinstance(node.value, ast.Constant) \
                    and isinstance(node.value.value, str):
                return node.value.value
    m = re.search(r"_v(\d{2,4})(?=[._])", rel)
    return "v" + m.group(1) if m else ""


# [VRN-ID] VRN-ENG009-FNC008 · LOGIC
def book_path(root: Path = VRN_ROOT) -> Path:
    return root / "ssot" / ID_BOOK.name


# [VRN-ID] VRN-ENG009-FNC009 · IO
def load_book(root: Path = VRN_ROOT) -> dict:
    try:
        book = json.loads(book_path(root).read_text(encoding="utf-8"))
    except Exception:
        book = {}
    book.setdefault("modules", {})
    book.setdefault("items", {})
    book.setdefault("serials", {})
    return book


# [VRN-ID] VRN-ENG009-FNC010 · LOGIC
def module_id(book: dict, rel: str, layer: str) -> str:
    entry = book["modules"].get(rel)
    if entry:
        return entry["id"]
    if layer == "ENG" and rel in ENGINE_ORDER:
        used = {m["id"] for m in book["modules"].values()}
        for i, path in enumerate(ENGINE_ORDER, 1):          # the fixed order claims its numbers first
            if path == rel and f"VRN-ENG{i:03d}" not in used:
                book["serials"]["ENG"] = max(book["serials"].get("ENG", 0), i)
                return f"VRN-ENG{i:03d}"
    if layer == "ENG":
        book["serials"]["ENG"] = max(book["serials"].get("ENG", 0), len(ENGINE_ORDER))
    n = book["serials"].get(layer, 0) + 1
    book["serials"][layer] = n
    return f"VRN-{layer}{n:03d}"


# [VRN-ID] VRN-ENG009-FNC011 · LOGIC
def plan(rel: str, layer: str, text: str, book: dict) -> dict:
    """IDs for one file and its new text; never writes.  ok=False when the AST would change (file left alone)."""
    nl = "\r\n" if "\r\n" in text else "\n"
    clean = strip(text)
    mid = module_id(book, rel, layer)
    category, zh = MODULE_CATEGORY.get(rel, ("TEST" if layer == "TST" else ("LAUNCHER" if layer == "PSL" else "ENGINE"), ""))
    if layer == "PSL":
        bom = "﻿" if clean.startswith("﻿") else ""
        body = clean[len(bom):]
        header = [f"{HEADER_OPEN} {mid} · {Path(rel).name} · {category} 啟動器 =====",
                  "# 編號登記在 ssot/VRN_ID_SSOT_v0100.json（只加註解）", HEADER_CLOSE]
        new = bom + nl.join(header) + nl + body
        entry = {"id": mid, "layer": LAYER_OF[layer], "category": category, "name": Path(rel).name, "version": module_version(ast.Module(body=[], type_ignores=[]), rel),
                 "description": zh, "classes": 0, "functions": 0, "state": "ACTIVE"}
        return {"rel": rel, "id": mid, "new": new, "changed": new != text, "ok": True, "module": entry, "items": []}
    try:
        tree = ast.parse(clean)
    except SyntaxError as error:
        return {"rel": rel, "id": mid, "ok": False, "why": f"SyntaxError: {error}", "changed": False}
    found = items_of(tree)
    seen: dict = {}
    tags = {}
    items = []
    for kind, qual, line, name, doc in found:
        seen[(kind, qual)] = seen.get((kind, qual), 0) + 1
        key = f"{rel}|{kind}|{qual}|{seen[(kind, qual)]}"
        prev = book["items"].get(key)
        if prev:
            iid = prev["id"]
        else:
            slot = f"{mid}|{kind}"
            book["serials"][slot] = book["serials"].get(slot, 0) + 1
            iid = f"{mid}-{kind}{book['serials'][slot]:03d}"
        cat = item_category(kind, name)
        items.append({"key": key, "id": iid, "module": mid, "kind": kind, "qualname": qual, "category": cat,
                      "line": line, "description": doc, "state": "ACTIVE"})
        tags[line] = f"{TAG_PREFIX}{iid} · {cat}"
    lines = split_lines(clean)
    out = []
    for no, raw in enumerate(lines, 1):
        if no in tags:
            indent = raw[:len(raw) - len(raw.lstrip(" \t"))]
            out.append(indent + tags[no] + nl)
        out.append(raw)
    doc = (ast.get_docstring(tree) or "").strip().splitlines()
    version = module_version(tree, rel)
    n_cls = sum(1 for i in items if i["kind"] == "CLS")
    n_fn = len(items) - n_cls
    header = [f"{HEADER_OPEN} {mid} · {Path(rel).stem}{(' ' + version) if version else ''} · {category}{(' ' + zh) if zh else ''} =====",
              f"# AST 注入（只加註解，AST 不變）：類別 {n_cls} · 函式 {n_fn}；逐一編號在 ssot/VRN_ID_SSOT_v0100.json",
              HEADER_CLOSE]
    # the header goes after a shebang / coding line (the coding cookie must stay in line 1 or 2)
    at = 0
    while at < len(out) and at < 2 and (out[at].startswith("#!") or re.match(r"^#.*coding[:=]", out[at])):
        at += 1
    new = "".join(out[:at]) + nl.join(header) + nl + "".join(out[at:])
    same = ast.dump(ast.parse(new)) == ast.dump(tree) == ast.dump(ast.parse(text))
    module = {"id": mid, "layer": LAYER_OF[layer], "category": category, "name": Path(rel).stem, "version": version,
              "description": zh or (doc[0][:120] if doc else ""), "classes": n_cls, "functions": n_fn, "state": "ACTIVE"}
    return {"rel": rel, "id": mid, "new": new, "changed": new != text, "ok": same,
            "why": "" if same else "AST would change: not written", "module": module, "items": items}


# [VRN-ID] VRN-ENG009-FNC012 · LOGIC
def run(write: bool = True, root: Path = VRN_ROOT, mapper=None, backup=None) -> dict:
    """Plan every file (through `mapper`, e.g. the accelerator lane), write only those whose AST is unchanged,
    then write the ID book.  `backup(rel, text)` is called before a file is overwritten."""
    book = load_book(root)
    pairs = targets(root)
    texts = {rel: read_exact(root / rel) for rel, _ in pairs}            # CRLF stays CRLF on a Windows checkout
    for rel, layer in pairs:                                  # numbers are issued in a fixed order, before any parallel work
        module_id_issued = module_id(book, rel, layer)
        book["modules"].setdefault(rel, {"id": module_id_issued})
    plans = (mapper or (lambda fn, xs: [fn(x) for x in xs]))(lambda p: plan(p[0], p[1], texts[p[0]], book), pairs)
    live_keys = set()
    report = {"files": 0, "changed": 0, "refused": [], "written": []}
    for res in plans:
        report["files"] += 1
        if not res.get("ok"):
            report["refused"].append(f"{res['rel']}: {res.get('why')}")
            continue
        book["modules"][res["rel"]] = res["module"]
        for it in res["items"]:
            live_keys.add(it["key"])
            book["items"][it["key"]] = {k: v for k, v in it.items() if k != "key"}
        if res["changed"]:
            report["changed"] += 1
            if write:
                if backup is not None:
                    backup(res["rel"], texts[res["rel"]])
                (root / res["rel"]).write_text(res["new"], encoding="utf-8", newline="")
                report["written"].append(res["rel"])
    for key, it in book["items"].items():                     # never recycled: gone = RETIRED, number kept
        if key not in live_keys and it.get("state") == "ACTIVE" and not report["refused"]:
            it["state"] = "RETIRED"
    for rel, m in book["modules"].items():
        if rel not in texts:
            m["state"] = "RETIRED"
    counts = {"modules": sum(1 for m in book["modules"].values() if m.get("state") == "ACTIVE"),
              "classes": sum(1 for i in book["items"].values() if i["state"] == "ACTIVE" and i["kind"] == "CLS"),
              "functions": sum(1 for i in book["items"].values() if i["state"] == "ACTIVE" and i["kind"] == "FNC"),
              "retired": sum(1 for i in book["items"].values() if i["state"] == "RETIRED")}
    out = {"schema": "VRN_ID_SSOT_v0100", "owner": "VRN 獨立子系統（engine/VRN_AstId_v0100.py；VRN_Main build 生成）",
           "policy": "編號由 VRN 自己發（VRN-ENG001、VRN-ENG001-FNC045 …），形狀同中央階層；只加註解注入，寫回前 AST 必須相同。"
                     "編號永不回收：消失的函式標 RETIRED，號碼不再發。類別規則見 item_rules。",
           "module_layers": LAYER_OF, "item_rules": [c for c, _ in ITEM_RULES] + ["CLASS", "LOGIC"],
           "counts": counts, "serials": dict(sorted(book["serials"].items())),
           "modules": dict(sorted(book["modules"].items())), "items": dict(sorted(book["items"].items()))}
    if write and not report["refused"]:
        book_path(root).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    report["book"] = out
    return report


# [VRN-ID] VRN-ENG009-FNC013 · LOGIC
def check(root: Path = VRN_ROOT) -> list:
    """What disagrees with the book: missing / stale header or tags, unregistered defs, AST drift.  [] = clean."""
    problems = []
    book = load_book(root)
    probe = json.loads(json.dumps(book))
    for rel, layer in targets(root):
        text = (root / rel).read_text(encoding="utf-8")
        if rel not in book["modules"]:
            problems.append(f"{rel}: not in the ID book")
            continue
        res = plan(rel, layer, text, probe)
        if not res.get("ok"):
            problems.append(f"{rel}: {res.get('why')}")
        elif res["new"].replace("\r\n", "\n") != text.replace("\r\n", "\n"):
            problems.append(f"{rel}: IDs not injected or stale (run build)")
        for it in res.get("items", []):
            known = book["items"].get(it["key"])
            if not known or known["id"] != it["id"]:
                problems.append(f"{rel}: {it['qualname']} has no number in the book")
    return problems


# [VRN-ID] VRN-ENG009-FNC014 · ENTRY
def main(argv=None):
    parser = argparse.ArgumentParser(description="VRN AST IDs: number, class and describe every module and function")
    parser.add_argument("command", nargs="?", default="check", choices=("check", "inject", "plan"))
    args = parser.parse_args(argv)
    if args.command == "check":
        problems = check()
        for p in problems[:40]:
            print("  [FAIL] " + p)
        print(f"[ASTID] {'GREEN' if not problems else 'RED'} · {len(problems)} problem(s)")
        return 1 if problems else 0
    report = run(write=args.command == "inject")
    print(f"[ASTID] files {report['files']} · changed {report['changed']} · refused {len(report['refused'])} · "
          f"modules {report['book']['counts']['modules']} · functions {report['book']['counts']['functions']} · "
          f"classes {report['book']['counts']['classes']}")
    for r in report["refused"]:
        print("  [REFUSED] " + r)
    return 1 if report["refused"] else 0


if __name__ == "__main__":
    sys.exit(main())
