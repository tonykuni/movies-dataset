#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Record the financial rows that were shown. Do not reread the folder or replace the older empty locks."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
BOOK = HERE / "VIA_VRN_FinancialShown_v0100.json"
ENGINE = VIA / "functional modules" / "VRN" / "VRN_ENG110_TabReport_v0114.py"
KEPT = (
    HERE / "CGC_MDL193_TabFieldLock_v0100.py",
    HERE / "CGC_MDL193_ReportMeasureLock_v0101.py",
    HERE / "CGC_MDL198_Closeout_v0100.py",
)


def check() -> dict:
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    text = ENGINE.read_text(encoding="utf-8") if ENGINE.is_file() else ""
    drift = []
    if book["basic_written"] != 50 or book["financial_rows"] != 159 or book["financial_files"] != 46:
        drift.append("counts")
    if book["financial"] != "shown" or book["discuss"] != 0 or book["refetched"] is not False:
        drift.append("shown")
    for name in ("financial_rows", "financial_files", "basic_written"):
        if name not in text:
            drift.append(name)
    if "no labeled figure" not in text:
        drift.append("empty_case")
    if any(not path.is_file() for path in KEPT):
        drift.append("older_lock")
    return {
        "via": "vcgc",
        "door": "CGC_MDL193_FinancialShownLock_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": drift == [],
        "source": book["source"],
        "basic_written": book["basic_written"],
        "financial_rows": book["financial_rows"],
        "financial_files": book["financial_files"],
        "discuss": book["discuss"],
        "financial": book["financial"],
        "kept": book["kept"],
        "refetched": False,
        "drift": drift,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": [
            "replace the older empty locks",
            "reread the sample folder from this lock",
            "treat a broker figure as historical truth",
            "invent a financial value",
            "edit intake macro_ssot",
        ],
        "next": "none" if not drift else "do not unlock; name the drift",
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    card = check()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["lock_success"] else 2


def selftest() -> int:
    card = check()
    print("  [OK]" if card["lock_success"] else "  [FAIL] " + ",".join(card["drift"]))
    return 0 if card["lock_success"] else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
