#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lock the VRN tab store rule. Replays the reject. Does not read a report."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
ENGINE = VIA / "functional modules" / "VRN" / "VRN_ENG109_TabStore_v0100.py"


def _engine():
    spec = importlib.util.spec_from_file_location("vrn_tab_store", ENGINE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check() -> dict:
    mod = _engine()
    rejected = mod.store({"basic": {}, "page1": {}, "financial": []}, Path("/tmp/vrn_tab_lock_reject"))
    drift = []
    if rejected["written"] != 0:
        drift.append("reject")
    if len(mod.BASIC) != 22 or len(mod.FINANCIAL) != 14:
        drift.append("schema")
    if mod.cloud_of(Path(r"C:\Users\tonyk\OneDrive\Documents")) != "onedrive":
        drift.append("cloud")
    return {
        "via": "vcgc",
        "door": "CGC_MDL193_VrnTabLock_v0100",
        "order": ["enter", "lock_success", "lock_record", "lock_path", "exit"],
        "enter": "vcgc",
        "lock_success": drift == [],
        "lock_record": "VRN_ENG109_TabStore_v0100.py",
        "lock_path": ["Invoke-VIA-VCGC-SyncAll.ps1", "CGC_MDL193_VrnTabLock_v0100.py", "VRN_ENG109_TabStore_v0100.py"],
        "exit": "vcgc",
        "tabs": ["BASIC INFO", "PAGE 1", "FINANCIAL DATA"],
        "basic_fields": 22,
        "financial_fields": 14,
        "drift": drift,
        "written": rejected["written"],
        "intake_edited": False,
        "hub_edited": False,
        "do_not": ["write an unverified tab", "edit intake macro_ssot", "scan every cloud account"],
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
    ok = card["lock_success"] and card["written"] == 0
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
