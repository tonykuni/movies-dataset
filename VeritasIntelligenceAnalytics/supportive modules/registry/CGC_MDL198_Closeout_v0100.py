#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Closeout. VCGC and VDF managers pass their own tests. VRN stock scope is next."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent


def check() -> dict:
    needed = [
        VIA / "supportive modules" / "registry" / "CGC_SystemManager_v0100.py",
        VIA / "functional modules" / "VDF" / "VDF_SystemManager_v0105.py",
        VIA / "functional modules" / "VRN" / "VRN_SystemManager_v0105.py",
        VIA / "functional modules" / "VRN" / "VRN_ENG110_TabReport_v0110.py",
    ]
    missing = [path.name for path in needed if not path.is_file()]
    return {
        "via": "vcgc",
        "door": "CGC_MDL198_Closeout_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": missing == [],
        "vcgc": "manager selftest passed; no new fetch",
        "vdf": "manager selftest passed; no new fetch",
        "vrn": {
            "last_measured_door": "VRN_ENG110_TabReport_v0109",
            "pdf": 97,
            "text": 97,
            "readers": {"ENG072_FITZ_LAYOUT": 81, "RAPIDOCR": 16},
            "financial_empty": 97,
            "basic_status": 89,
            "company_blank": 8,
            "names": "no_official",
            "written": 0,
            "next_scope": "stock",
            "later": "non-stock reports stay out of this path",
        },
        "missing": missing,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": [
            "parse a morning note as a stock",
            "invent a financial value",
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
