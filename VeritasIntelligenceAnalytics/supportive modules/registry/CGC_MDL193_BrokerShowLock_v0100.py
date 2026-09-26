#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The shown broker is the short canonical name, and a filename hit beats an email domain."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
LIST = VIA / "functional modules" / "VRN" / "registry" / "VRN_BROKER_LIST_v03.json"


def check() -> dict:
    text = LIST.read_text(encoding="utf-8") if LIST.is_file() else ""
    data = json.loads(text) if text else {}
    shows = {row.get("canonical"): row.get("show") for row in data.get("brokers") or []}
    want = {"中信": "中信", "台新": "台新", "兆豐": "兆豐", "MQ": "MQ", "GS": "GS", "Daiwa": "Daiwa"}
    missing = [key for key, value in want.items() if shows.get(key) != value]
    return {
        "via": "vcgc",
        "door": "CGC_MDL193_BrokerShowLock_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": missing == [],
        "show": "canonical",
        "missing": missing,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": [
            "show Megabank when the short name is 兆豐",
            "let daiwacm-cathay.com.tw choose 國泰",
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
