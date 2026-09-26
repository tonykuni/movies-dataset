#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lock the imported forward-vintage engine. Checks the hash. Does not rerun or edit the hub."""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
LOCK = HERE / "VIA_ForwardVintageLock_v0100.json"
ENGINE = VIA / "functional modules" / "VDF" / "engine" / "VDF_ENG117_ForwardVintage_v0100.py"
PATH = (
    "Invoke-VIA-VCGC-SyncAll.ps1",
    "CGC_MDL193_ForwardVintageLock_v0100.py",
    "VDF_ENG117_ForwardVintage_v0100.py",
    "VIA_ForwardVintageLock_v0100.json",
)


def check() -> dict:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    live = hashlib.sha256(ENGINE.read_bytes()).hexdigest() if ENGINE.is_file() else ""
    drift = []
    if live != lock["sha256"]:
        drift.append("sha256")
    if lock["selftest"] != "pass" or lock["methodology"] != "forward_valuation_vintage_v2":
        drift.append("selftest")
    return {
        "via": "vcgc",
        "door": "CGC_MDL193_ForwardVintageLock_v0100",
        "order": ["enter", "lock_success", "lock_record", "lock_path", "exit"],
        "enter": "vcgc",
        "lock_success": drift == [],
        "lock_record": LOCK.name,
        "lock_path": list(PATH),
        "exit": "vcgc",
        "name": "VIA",
        "same": True,
        "methodology": lock["methodology"],
        "parameters": lock["parameters"],
        "drift": drift,
        "hub_edited": False,
        "intake_edited": False,
        "registry_apply": False,
        "do_not": lock["do_not"],
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
    ok = card["lock_success"] and card["parameters"]["DEFAULT_INDEX_STALE_DAYS"] == 45 and card["hub_edited"] is False
    print("  [OK]" if ok else "  [FAIL] " + json.dumps(card, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
