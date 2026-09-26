#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The report command exists, and the new door does not invent a financial row."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
ENGINE = VIA / "functional modules" / "VRN" / "VRN_ENG110_TabReport_v0109.py"
LAUNCH = VIA / "Invoke-VIA-VRNReport.ps1"


def check() -> dict:
    text = ENGINE.read_text(encoding="utf-8") if ENGINE.is_file() else ""
    missing = []
    if not LAUNCH.is_file():
        missing.append("launcher")
    for name in ("allow_web=False", "不是第 1 頁原文", "actual labeled figure"):
        if name not in text:
            missing.append(name)
    return {
        "via": "vcgc",
        "door": "CGC_MDL193_ReportWireLock_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": missing == [],
        "launcher": LAUNCH.name,
        "report": ENGINE.name,
        "financial": "not invented",
        "web_lookup": False,
        "missing": missing,
        "intake_edited": False,
        "do_not": [
            "invent a financial value",
            "copy fixed_page1 into summary_page1",
            "look up a company name on the web from this door",
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
    print("  [OK]" if card["lock_success"] else "  [FAIL] " + ",".join(card["missing"]))
    return 0 if card["lock_success"] else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
