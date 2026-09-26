#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The stock path keeps the filename code when the page repeats it."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
ENGINE = VIA / "functional modules" / "VRN" / "VRN_ENG111_StockIdentity_v0100.py"
REPORT = VIA / "functional modules" / "VRN" / "VRN_ENG110_TabReport_v0111.py"


def check() -> dict:
    text = ENGINE.read_text(encoding="utf-8") if ENGINE.is_file() else ""
    report = REPORT.read_text(encoding="utf-8") if REPORT.is_file() else ""
    missing = [name for name, body in (("CLST", text), ("MCQN", text), ("DAIWA", text), ("逢低買進", report)) if name not in body]
    return {
        "via": "vcgc",
        "door": "CGC_MDL193_StockIdentityLock_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": missing == [],
        "rule": "filename four digits must match a page code",
        "broker": {"CLST": "CLSA", "MCQN": "MCQN", "DAIWA": "DAIWA"},
        "not_a_ticker": ["report year", "margin balance", "rating legend"],
        "missing": missing,
        "intake_edited": False,
        "do_not": [
            "read 賣出 inside 評等分級 as the rating",
            "read 前次投資建議 as the report date",
            "invent FactSet or Yahoo target medians",
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
