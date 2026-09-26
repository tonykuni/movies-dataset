#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lock the later report measurement. It does not reread the folder or replace v0100."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOOK = HERE / "VIA_VRN_ReportMeasure_v0101.json"
PRIOR = HERE / "VIA_VRN_ReportMeasure_v0100.json"


def check() -> dict:
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    prior = json.loads(PRIOR.read_text(encoding="utf-8"))
    drift = []
    if book["text"] != 87 or book["readers"] != {"ENG072_FITZ_LAYOUT": 81, "ENG072_PYPDF": 6, "none": 10}:
        drift.append("text")
    if book["written"] != 0 or book["verified"] != 0 or book["logic_error"] != "":
        drift.append("gate")
    if book["columns"] != {"basic": 22, "page": 5, "financial": 14} or book["opened"] is not True:
        drift.append("page")
    if "via_vrn_312" not in book["python"] or book["ocr_budget"] != "not called":
        drift.append("python")
    if book["reader_error"] != "NEEDS_VISUAL:few_chars" or book["ticker_mismatch"] != 7:
        drift.append("open")
    if prior["text"] != 0:
        drift.append("prior")
    return {
        "via": "vcgc",
        "door": "CGC_MDL193_ReportMeasureLock_v0101",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": drift == [],
        "measured_at": book["measured_at"],
        "locked_success": book["locked_success"],
        "open": book["open"],
        "text": book["text"],
        "readers": book["readers"],
        "written": book["written"],
        "prior_text": prior["text"],
        "drift": drift,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": [
            "mark the 10 short pages as read",
            "copy the page text into the summary",
            "invent a financial value",
            "replace the older text-zero lock with this one",
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
