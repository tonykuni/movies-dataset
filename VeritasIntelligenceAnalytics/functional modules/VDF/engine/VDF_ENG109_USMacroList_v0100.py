#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC door into the US macro lists. Read-only. Does not fetch and does not edit the intake SSOT."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

VDF = Path(__file__).resolve().parents[1]
GAP = VDF / "VDF_USMacro_Gap_v0100.json"
ROSTER = VDF / "VDF_USMacro_Detail_Fetch_Roster_v0100.json"


def inventory() -> dict:
    gap = json.loads(GAP.read_text(encoding="utf-8"))
    roster = json.loads(ROSTER.read_text(encoding="utf-8"))
    sections = {name: len(items) for name, items in roster["sections"].items()}
    return {
        "via": "vcgc",
        "door": "VDF_ENG109",
        "ssot_rows": gap["ssot_rows"],
        "ssot_unique": gap["ssot_unique_fred"],
        "detail": gap["detail_items"],
        "sections": sections,
        "gap_verified": len(gap["verified"]),
        "no_fred_id": gap["no_fred_id"],
        "anchors": gap["anchors"],
        "engines": {
            "ENG074": "VDF_ENG074_FredMacroSSOT_v0103.py",
            "ENG047": "VDF_ENG047_USMacroDetailFetcher_v0101.py",
        },
        "do_not": ["edit intake macro_ssot", "full backfill", "store FRED_API_KEY"],
        "next": "none",
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "enter through via-vcgc"}, ensure_ascii=False))
        return 2
    print(json.dumps(inventory(), ensure_ascii=False, indent=1))
    return 0


def selftest() -> int:
    card = inventory()
    ok = card["ssot_rows"] == 190 and card["detail"] == 43 and card["gap_verified"] == 17
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
