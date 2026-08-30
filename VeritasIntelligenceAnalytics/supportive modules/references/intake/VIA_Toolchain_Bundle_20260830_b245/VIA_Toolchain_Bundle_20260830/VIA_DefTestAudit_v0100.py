# ---------------------------------------------------------------------
# VIA_DefTestAudit_v0100
#
# pytest collects functions named test_*. A generation defect prefixed
# many functions in this tree with "def_", so "def def_test_x()" is a
# test that can never be collected: pytest reports "no tests ran" and
# the run exits looking clean. That is a false green, and it is why the
# v035 backtest engine shipped with zero executed coverage.
#
# This tool finds every one of them, works out which are actually
# collectable once renamed, and writes a repair plan. Nothing is edited
# unless --apply is passed, and every edit keeps a .bak sibling.
# ---------------------------------------------------------------------

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

TOOL = "VIA_DefTestAudit"
VERSION = "v0100"

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}
DEF_TEST = re.compile(r"\bdef_test_[A-Za-z0-9_]+\b")


def scan_file(path: Path) -> dict:
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return {"path": str(path), "error": str(exc), "targets": []}
    if "def_test_" not in src:
        return None
    try:
        tree = ast.parse(src, filename=str(path))
    except SyntaxError as exc:
        return {"path": str(path), "error": "SyntaxError line {0}".format(exc.lineno),
                "targets": [], "parse_ok": False}

    module_level = set()
    nested = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("def_test_"):
            module_level.add(node.name)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("def_test_"):
            if node.name not in module_level:
                nested.add(node.name)

    names = sorted(set(DEF_TEST.findall(src)))
    targets = []
    for n in names:
        new = n[4:]  # strip the leading "def_"
        if n in module_level:
            verdict = "COLLECTABLE_AFTER_RENAME"
        elif n in nested:
            verdict = "NESTED_STILL_UNCOLLECTABLE"
        else:
            verdict = "REFERENCE_ONLY"
        collides = re.search(r"\bdef\s+" + re.escape(new) + r"\b", src) is not None
        targets.append({
            "old": n, "new": new, "verdict": verdict,
            "occurrences": len(re.findall(r"\b" + re.escape(n) + r"\b", src)),
            "name_collision": collides,
        })
    return {
        "path": str(path), "error": "", "parse_ok": True,
        "module_level": sorted(module_level), "nested": sorted(nested),
        "targets": targets,
    }


def repair_text(src: str, targets) -> tuple:
    changed = 0
    for t in targets:
        if t["name_collision"]:
            continue
        pattern = re.compile(r"\b" + re.escape(t["old"]) + r"\b")
        src, n = pattern.subn(t["new"], src)
        changed += n
    return src, changed


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="audit and repair def_test_ naming defect")
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--go-token", default="")
    args = ap.parse_args(argv)

    root = Path(args.root)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    apply_mode = args.apply and args.go_token == "GO_v1"

    findings = []
    scanned = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            scanned += 1
            if scanned % 2000 == 0:
                sys.stderr.write("SCAN|{0} files\n".format(scanned))
                sys.stderr.flush()
            res = scan_file(Path(dirpath) / fn)
            if res:
                findings.append(res)

    collectable = []
    nested_only = []
    for f in findings:
        if any(t["verdict"] == "COLLECTABLE_AFTER_RENAME" for t in f["targets"]):
            collectable.append(f)
        elif any(t["verdict"] == "NESTED_STILL_UNCOLLECTABLE" for t in f["targets"]):
            nested_only.append(f)

    repaired = []
    if apply_mode:
        stage = out / "_repaired"
        stage.mkdir(parents=True, exist_ok=True)
        for f in collectable:
            p = Path(f["path"])
            src = p.read_text(encoding="utf-8", errors="replace")
            new_src, n = repair_text(src, f["targets"])
            if n == 0:
                continue
            backup = p.with_suffix(p.suffix + ".predeftest.bak")
            if not backup.exists():
                shutil.copy2(p, backup)
            p.write_text(new_src, encoding="utf-8", newline="\n")
            repaired.append({"path": str(p), "replacements": n, "backup": str(backup)})

    total_names = sorted({t["old"] for f in findings for t in f["targets"]})
    payload = {
        "tool": TOOL, "version": VERSION,
        "at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "root": str(root), "python_files_scanned": scanned,
        "files_with_defect": len(findings),
        "files_collectable_after_rename": len(collectable),
        "files_nested_only": len(nested_only),
        "distinct_names": len(total_names),
        "mode": "APPLIED" if apply_mode else "DRY_RUN",
        "repaired": repaired,
        "findings": findings,
    }
    plan = out / "deftest_plan.json"
    plan.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                    encoding="utf-8", newline="\n")
    sys.stderr.write("DONE|files={0} collectable={1} nested={2} mode={3}\n".format(
        len(findings), len(collectable), len(nested_only), payload["mode"]))
    print(json.dumps({k: v for k, v in payload.items() if k != "findings"},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
