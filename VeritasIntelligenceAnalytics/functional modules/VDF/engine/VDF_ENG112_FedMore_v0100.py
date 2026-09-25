#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC door for the extra Fed series. Read-only."""
from __future__ import annotations
import json, os, sys
from pathlib import Path
BOOK = Path(__file__).resolve().parents[1] / "VDF_USMacro_FedMore_v0100.json"

def check() -> dict:
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    ids = [r["fred_id"] for r in book["add"]]
    return {
        "via": "vcgc", "door": "VDF_ENG112",
        "added": len(ids), "ids": ids,
        "already": len(book["already_in_parent"]),
        "stale": [r["fred_id"] for r in book["stale"]],
        "intake_edited": False,
        "do_not": ["fetch DISCBORR", "edit intake macro_ssot", "full backfill"],
        "next": "none",
    }

def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False)); return 2
    print(json.dumps(check(), ensure_ascii=False, indent=1)); return 0

def selftest() -> int:
    card = check()
    ok = card["added"] == 15 and card["stale"] == ["DISCBORR"] and len(set(card["ids"])) == 15
    print("  [OK]" if ok else "  [FAIL]"); return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
