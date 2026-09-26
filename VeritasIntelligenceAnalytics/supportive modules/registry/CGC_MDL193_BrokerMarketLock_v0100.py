#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DAIWA and HuaNan are on the broker list. The exchange list picks the Yahoo suffix."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
LIST = VIA / "functional modules" / "VRN" / "registry" / "VRN_BROKER_LIST_v02.json"
MARKET = VIA / "functional modules" / "VDF" / "engine" / "VDF_ENG118_TWMarket_v0100.py"


def check() -> dict:
    text = LIST.read_text(encoding="utf-8") if LIST.is_file() else ""
    engine = MARKET.read_text(encoding="utf-8") if MARKET.is_file() else ""
    missing = [name for name in ("DAIWA", "MCQN", "華南投顧", "華南證券") if name not in text]
    if ".TW" not in engine or ".TWO" not in engine:
        missing.append("suffix")
    return {
        "via": "vcgc",
        "door": "CGC_MDL193_BrokerMarketLock_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": missing == [],
        "broker_list": LIST.name,
        "market": "TWSE .TW / TPEX .TWO / both unresolved",
        "missing": missing,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": [
            "guess .TW when the exchange list did not answer",
            "let an email domain choose the broker",
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
