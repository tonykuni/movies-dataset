#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Emit one lock pass, in order, and only through VCGC.

enter, then lock success, then the lock record, then the lock path, then exit.
Does not rewrite the lock.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ORDER = ("enter", "lock_success", "lock_record", "lock_path", "exit")
PATH = (
    "Invoke-VIA-VCGC-StatusLock.ps1",
    "CGC_MDL193_StatusLock_v0100.py",
    "VIA_StatusLock_v0100.json",
)


def _prior():
    spec = importlib.util.spec_from_file_location("status_lock_v0100", HERE / "CGC_MDL193_StatusLock_v0100.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def emit(card: dict) -> dict:
    return {
        "via": "vcgc",
        "door": "CGC_MDL193_StatusLock_v0101",
        "order": list(ORDER),
        "enter": "VIA_FROM_VCGC",
        "lock_success": card.get("drift") == [] and len(card.get("locked") or []) == 3,
        "lock_record": "VIA_StatusLock_v0100.json",
        "lock_path": list(PATH),
        "exit": "vcgc",
        "locked": card.get("locked") or [],
        "drift": card.get("drift") or [],
        "lock_edited": False,
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "order": list(ORDER)}, ensure_ascii=False))
        return 2
    card = emit(_prior().check())
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["lock_success"] else 2


def selftest() -> int:
    fails = []

    def chk(name, ok):
        if not ok:
            fails.append(name)
        print(f"  [{'OK' if ok else 'FAIL'}] {name}")

    sample = emit({"locked": ["knowledge_assets", "usmacro_params", "method_selftest"], "drift": []})
    chk("the five steps stay in order", tuple(sample["order"]) == ORDER)
    chk("success comes before the record and the path",
        sample["order"].index("lock_success") < sample["order"].index("lock_record") < sample["order"].index("lock_path"))
    chk("the path is the launcher, the checker, then the record", sample["lock_path"] == list(PATH))
    chk("a clean card is a success and does not edit the lock", sample["lock_success"] and sample["lock_edited"] is False)
    chk("a drift is not a success", emit({"locked": [], "drift": ["usmacro_params"]})["lock_success"] is False)
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main()
    chk("without VCGC the door denies", denied == 2)
    os.environ["VIA_FROM_VCGC"] = "YES"
    live = emit(_prior().check())
    chk("the live lock still holds", live["lock_success"] is True and live["drift"] == [])
    print(f"  [計] FAIL {len(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
