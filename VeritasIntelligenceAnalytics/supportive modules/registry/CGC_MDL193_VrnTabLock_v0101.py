#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lock the split between the engine tree and the database root."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
ENGINE = VIA / "functional modules" / "VRN" / "VRN_ENG109_TabStore_v0101.py"


def _engine():
    spec = importlib.util.spec_from_file_location("tab_v0101", ENGINE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check() -> dict:
    mod = _engine()
    os.environ.pop("VIA_VRN_DATA", None)
    together = mod.place()
    os.environ["VIA_VRN_DATA"] = r"C:\Users\tonyk\OneDrive\VIA-DATA"
    apart = mod.place()
    os.environ.pop("VIA_VRN_DATA", None)
    drift = []
    if together["same"] is not True:
        drift.append("same")
    if apart["off_pc"] is not True or apart["cloud"] != "onedrive":
        drift.append("off_pc")
    if mod._prior().store({"basic": {}, "page1": {}, "financial": []}, Path("/tmp/vrn_tab_lock_v0101"))["written"] != 0:
        drift.append("reject")
    return {
        "via": "vcgc",
        "door": "CGC_MDL193_VrnTabLock_v0101",
        "order": ["enter", "lock_success", "lock_record", "lock_path", "exit"],
        "enter": "vcgc",
        "lock_success": drift == [],
        "lock_record": ENGINE.name,
        "lock_path": ["Invoke-VIA-VCGC-SyncAll.ps1", "CGC_MDL193_VrnTabLock_v0101.py", ENGINE.name],
        "exit": "vcgc",
        "same_by_default": together["same"],
        "split_cloud": apart["cloud"],
        "off_pc": apart["off_pc"],
        "drift": drift,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": [
            "write an unverified tab",
            "treat a powered-off computer as the server",
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
    print("  [OK]" if card["lock_success"] else "  [FAIL]")
    return 0 if card["lock_success"] else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
