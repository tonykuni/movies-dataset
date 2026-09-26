#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lock the measured report successes. It does not reread the sample folder."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
BOOK = HERE / "VIA_VRN_ReportMeasure_v0100.json"
ENGINE = VIA / "functional modules" / "VRN" / "VRN_ENG110_TabReport_v0103.py"


def check() -> dict:
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    drift = []
    if book["pdf"] != 97 or book["written"] != 0 or book["opened"] is not True:
        drift.append("measure")
    if book["columns"] != {"basic": 22, "page": 5, "financial": 14}:
        drift.append("columns")
    if book["why"] != ["basic_status", "page_not_1", "financial_empty"]:
        drift.append("why")
    if book["reader_error"] != "fitz:ModuleNotFoundError":
        drift.append("reader")
    if book["text"] != 0:
        drift.append("text")
    if not ENGINE.is_file():
        drift.append("engine")
    return {
        "via": "vcgc",
        "door": "CGC_MDL193_ReportMeasureLock_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": drift == [],
        "locked_success": book["locked_success"],
        "open": book["open"],
        "pdf": book["pdf"],
        "written": book["written"],
        "opened": book["opened"],
        "drift": drift,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": ["mark the missing PyMuPDF as a successful read", "reread the sample folder from this lock", "edit intake macro_ssot"],
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
    print("  [OK]" if card["lock_success"] else "  [FAIL]")
    return 0 if card["lock_success"] else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
