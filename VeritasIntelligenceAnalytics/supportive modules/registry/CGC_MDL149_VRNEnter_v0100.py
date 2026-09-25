#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lock the green lamps from the 03:23 measurement, then read VRN only through its manager."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
LOCK = HERE / "VIA_LampLock_v0100.json"
MANAGER = VIA / "functional modules" / "VRN" / "VRN_SystemManager_v0105.py"


def lock_body() -> dict:
    data = json.loads(LOCK.read_text(encoding="utf-8"))
    locked = list(data["locked"])
    opened = list(data["open"])
    clash = sorted(set(locked) & set(opened))
    return {
        "locked": locked,
        "open": opened,
        "clash": clash,
        "measured_at": data.get("measured_at"),
    }


def enter() -> dict:
    import importlib.util
    spec = importlib.util.spec_from_file_location("vrn_enter", MANAGER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    state = mod.collect()
    lamps = state.get("lamps") or {}
    return {
        "rc": state.get("rc"),
        "rc_name": state.get("rc_name"),
        "lamps": lamps,
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VRN] 拒絕。只能經 via-vcgc。")
        return 2
    book = lock_body()
    if book["clash"]:
        print("[鎖] 同一盞燈不能又鎖又開")
        return 2
    vrn = enter()
    body = {
        "via": "vcgc",
        "door": "VRN_SystemManager_v0105",
        "locked": book["locked"],
        "open": book["open"],
        "vrn": vrn,
        "do_not": ["page --publish", "hand-edit the card book", "reopen a locked lamp"],
        "next": "none",
        "logged_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    print("BEGIN_PASTE")
    print(json.dumps(body, ensure_ascii=False, indent=1))
    print("END_PASTE")
    return 0


def selftest() -> int:
    book = lock_body()
    ok = not book["clash"] and "vrn_policy" in book["locked"] and "vrn_logic" in book["open"]
    ok = ok and "vdf_bridge" in book["open"] and "vdf_engine" in book["locked"]
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
