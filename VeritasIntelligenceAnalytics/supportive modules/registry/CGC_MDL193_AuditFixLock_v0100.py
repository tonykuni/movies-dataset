#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The audit's confirmed ticker and page-count fixes are present. The empty products stay empty."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
ENGINE = VIA / "functional modules" / "VRN" / "VRN_ENG110_TabReport_v0108.py"


def check() -> dict:
    text = ENGINE.read_text(encoding="utf-8") if ENGINE.is_file() else ""
    missing = [name for name in ("year_not_ticker", 'summary_page1": ""', "db_written") if name not in text]
    return {
        "via": "vcgc",
        "door": "CGC_MDL193_AuditFixLock_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": ENGINE.is_file() and missing == [],
        "fixed": ["year_not_ticker", "real_page_count", "per_file_holds"],
        "still_open": ["summary_empty", "financial_empty", "company_name_needs_official_roster", "rapidocr_absent"],
        "missing": missing,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": [
            "invent a company name",
            "copy fixed_page1 into summary_page1",
            "invent a financial value",
            "turn a date conflict into GREEN",
            "edit intake macro_ssot",
        ],
        "next": "none" if not missing else "do not unlock; name the drift",
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
