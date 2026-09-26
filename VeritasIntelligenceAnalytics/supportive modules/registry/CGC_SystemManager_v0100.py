#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC system manager. One dock to VDF and one dock to VRN. It does not run their work."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

VIA = Path(__file__).resolve().parents[2]
VDF = VIA / "functional modules" / "VDF" / "VDF_SystemManager_v0105.py"
VRN = VIA / "functional modules" / "VRN" / "VRN_SystemManager_v0105.py"
LOGIC = VIA / "functional modules" / "VRN" / "references" / "intake" / "VIA_VRNLogic_AllInOne_v0201_b504" / "VIA_VRNLogic_AllInOne_v0201.py"


def _fields(text: str, key: str) -> list[str]:
    body = text.split(f'"{key}": (', 1)[1].split("),", 1)[0]
    return [part.strip().strip('"') for part in body.split(",") if part.strip()]


def review() -> dict:
    text = LOGIC.read_text(encoding="utf-8")
    basic = _fields(text, "basic_info")
    financial = _fields(text, "financial_data")
    return {
        "logic": LOGIC.name,
        "moved": False,
        "basic_info": len(basic),
        "financial_data": len(financial),
        "basic_has": ["ticker", "rating", "validationStatus"],
        "financial_has": ["statement", "item", "value", "unit"],
        "basic_ok": {"ticker", "rating", "validationStatus"}.issubset(basic),
        "financial_ok": {"statement", "item", "value", "unit"}.issubset(financial),
    }


def check() -> dict:
    looked = review()
    return {
        "via": "vcgc",
        "door": "CGC_SystemManager_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "docks": [
            {"from": "external", "to": "vcgc", "n": 1},
            {"from": "vcgc", "to": "vdf", "file": VDF.name, "n": 1},
            {"from": "vcgc", "to": "vrn", "file": VRN.name, "n": 1},
        ],
        "selftest_lives_in": ["CGC_SystemManager_v0100", "VDF_SystemManager_v0105", "VRN_SystemManager_v0105"],
        "ran_vdf": False,
        "ran_vrn": False,
        "review": looked,
        "hub_edited": False,
        "intake_edited": False,
        "pushed_by_door": False,
        "do_not": [
            "merge the three managers",
            "run VRN basic or financial from this manager",
            "move the intake logic file",
            "fix and test and finish in one pass",
        ],
        "next": "none" if looked["basic_ok"] and looked["financial_ok"] else "stop; the schema moved",
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-managers"}, ensure_ascii=False))
        return 2
    card = check()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["review"]["basic_ok"] and card["review"]["financial_ok"] else 2


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = check()
    ok = denied and card["ran_vdf"] is False and card["ran_vrn"] is False and card["review"]["basic_info"] == 22 and card["review"]["financial_data"] == 14 and VDF.is_file() and VRN.is_file()
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
