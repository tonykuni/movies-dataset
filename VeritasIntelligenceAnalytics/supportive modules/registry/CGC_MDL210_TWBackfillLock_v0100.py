#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC record of the measured backfill tail. Read-only. No fetch."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
LOCK = HERE / "VIA_TWBackfillLock_v0100.json"
ENGINE = VIA / "functional modules" / "VDF" / "engine" / "VDF_ENG054_TWDailyBackfill_v0109.py"
PATH = (
    "CGC_MDL210_TWBackfillLock_v0100.py",
    "VIA_TWBackfillLock_v0100.json",
    "VDF_ENG054_TWDailyBackfill_v0109.py",
)


def check() -> dict:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    text = ENGINE.read_text(encoding="utf-8") if ENGINE.is_file() else ""
    drift = []
    if lock.get("version") != "0109":
        drift.append("version")
    if lock.get("measured_at") != "2026-09-27 22:49:21":
        drift.append("measured_at")
    if lock.get("checks") != "12/12" or lock.get("exit") != 0:
        drift.append("checks")
    if lock.get("fetched") is not False:
        drift.append("fetched")
    if "class _FakeNetETFFail" not in text or "v0109" not in text:
        drift.append("engine")
    return {
        "via": "vcgc",
        "door": "CGC_MDL210_TWBackfillLock_v0100",
        "order": ["enter", "lock_success", "lock_record", "lock_path", "exit"],
        "enter": "vcgc",
        "lock_success": drift == [],
        "lock_record": LOCK.name,
        "lock_path": list(PATH),
        "exit": "vcgc",
        "version": lock.get("version"),
        "measured_at": lock.get("measured_at"),
        "engine": lock.get("engine"),
        "checks": lock.get("checks"),
        "drift": drift,
        "fetched": False,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": lock.get("do_not"),
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
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = check()
    ok = denied and card["lock_success"] and card["version"] == "0109" and card["fetched"] is False
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
