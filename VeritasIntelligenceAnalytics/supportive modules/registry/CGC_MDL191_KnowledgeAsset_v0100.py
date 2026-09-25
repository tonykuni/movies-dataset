#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC knowledge-asset check. Read-only. Does not move files or edit the intake SSOT."""
from __future__ import annotations
import json, os, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
BOOK = HERE / "VIA_KnowledgeAsset_Book_v0100.json"

def _cycles(assets: list[dict]) -> list[str]:
    deps = {a["id"]: a["depends_on"] for a in assets}
    seen, stack = set(), []
    bad = []
    def walk(node: str) -> None:
        if node in stack:
            bad.append(">".join(stack[stack.index(node):] + [node]))
            return
        if node in seen:
            return
        stack.append(node)
        for nxt in deps.get(node, []):
            walk(nxt)
        stack.pop()
        seen.add(node)
    for node in deps:
        walk(node)
    return bad

def check() -> dict:
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    ids = {a["id"] for a in book["assets"]}
    rank = {name: i for i, name in enumerate(book["classes"])}
    rows, missing = [], []
    for asset in book["assets"]:
        ok = (VIA / asset["path"]).is_file()
        unknown = [d for d in asset["depends_on"] if d not in ids]
        if not ok:
            missing.append(asset["id"])
        rows.append({
            "id": asset["id"], "class": asset["class"], "lamp": "GREEN" if ok and not unknown else "RED",
            "depends_on": asset["depends_on"],
        })
    rows.sort(key=lambda r: (rank.get(r["class"], 99), r["id"]))
    method = next(a for a in book["assets"] if a["id"] == "fed_method")
    log = next(a for a in book["assets"] if a["id"] == "fed_method_log")
    linked = json.loads((VIA / method["path"]).read_text(encoding="utf-8")).get("log") == log["path"]
    lamps = {"GREEN": sum(r["lamp"] == "GREEN" for r in rows), "RED": sum(r["lamp"] == "RED" for r in rows)}
    return {
        "via": "vcgc", "door": "CGC_MDL191", "governor": book["governor"], "entry": book["entry"],
        "assets": len(rows), "lamps": lamps, "order": [r["id"] for r in rows],
        "cycles": _cycles(book["assets"]), "method_log_linked": linked,
        "missing": missing, "intake_edited": False,
        "rows": rows,
        "do_not": ["move an asset file", "edit intake macro_ssot", "start a refresh from this door"],
        "next": "none" if lamps["RED"] == 0 and not _cycles(book["assets"]) and linked else "fix the red asset",
    }

def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    print(json.dumps(check(), ensure_ascii=False, indent=1))
    return 0

def selftest() -> int:
    card = check()
    ok = (card["assets"] == 11 and card["lamps"]["RED"] == 0 and card["cycles"] == []
          and card["method_log_linked"] and card["order"][0] == "usmacro_process")
    print("  [OK]" if ok else "  [FAIL] " + json.dumps(card, ensure_ascii=False))
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
