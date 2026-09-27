#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC manager tail. Shows the registered backfill version. Does not run it.

v0101 is not rewritten. The version and time come from the lock record.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE / "CGC_SystemManager_v0101.py"
DOOR = HERE / "CGC_MDL210_TWBackfillLock_v0100.py"
VDF = HERE.parents[1] / "functional modules" / "VDF" / "VDF_SystemManager_v0109.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-managers"}, ensure_ascii=False))
        return 2
    if {"start", "test", "register"}.intersection(sys.argv[1:]):
        return _load(PRIOR, "cgc_v0101_for_verbs").main()
    lock = _load(DOOR, "tw_backfill_lock_for_cgc_v0102").check()
    card = {
        "via": "vcgc",
        "door": "CGC_SystemManager_v0102",
        "enter": "vcgc",
        "exit": "vcgc",
        "vdf_manager": VDF.name,
        "registered_version": lock["version"],
        "measured_at": lock["measured_at"],
        "engine": lock["engine"],
        "checks": lock["checks"],
        "lock_record": lock["lock_record"],
        "lock_success": lock["lock_success"],
        "ran_backfill": False,
        "fetched": False,
        "intake_edited": False,
        "do_not": lock["do_not"],
        "next": lock["next"],
    }
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["lock_success"] else 2


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    lock = _load(DOOR, "tw_backfill_lock_self_cgc").check()
    ok = denied and lock["lock_success"] and lock["version"] == "0109" and VDF.is_file() and PRIOR.is_file()
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
