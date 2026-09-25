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


def _load(path: Path, name: str):
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def live_lamps() -> dict:
    vdf = _load(VIA / "functional modules" / "VDF" / "VDF_SystemManager_v0104.py", "vdf_hold")
    vrn = _load(MANAGER, "vrn_hold")
    a, b = vdf.collect(), vrn.collect()
    return {"vdf": a.get("lamps") or {}, "vrn": b.get("lamps") or {}, "vrn_rc": {"rc": b.get("rc"), "rc_name": b.get("rc_name")}}


def hold_of(book: dict, lamps: dict) -> dict:
    rows = []
    drift = []
    for name in book["locked"]:
        side, _, domain = name.partition("_")
        lamp = (lamps.get(side) or {}).get(domain)
        holds = lamp == "GREEN"
        rows.append({"id": name, "lamp": lamp, "holds": holds})
        if not holds:
            drift.append(name)
    return {"rows": rows, "drift": drift}


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VRN] 拒絕。只能經 via-vcgc。")
        return 2
    book = lock_body()
    if book["clash"]:
        print("[鎖] 同一盞燈不能又鎖又開")
        return 2
    lamps = live_lamps()
    held = hold_of(book, lamps)
    body = {
        "via": "vcgc",
        "door": "VRN_SystemManager_v0105",
        "locked": book["locked"],
        "open": book["open"],
        "hold": held["rows"],
        "drift": held["drift"],
        "vrn": lamps["vrn_rc"] | {"lamps": lamps["vrn"]},
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
    sample = {"vdf": {"policy": "GREEN", "engine": "STALE"}, "vrn": {"ssot": "GREEN"}}
    held = hold_of(book, sample)
    ok = not book["clash"] and "vdf_policy" not in held["drift"] and "vdf_engine" in held["drift"]
    ok = ok and "vrn_ssot" not in held["drift"]
    print("  [OK]" if ok else "  [FAIL]", held["drift"])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
