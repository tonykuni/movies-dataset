#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lock the shipping, container, and sentiment prints. Does not refetch or apply registry sync."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOCK = HERE / "VIA_MarketSyncLock_v0100.json"
PATH = (
    "Invoke-VIA-VCGC-SyncAll.ps1",
    "CGC_MDL193_MarketSync_v0100.py",
    "VIA_MarketSyncLock_v0100.json",
)


def check() -> dict:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    ship = lock["shipping"]
    box = lock["container"]
    sent = lock["sentiment"]
    drift = []
    if ship["BDI"] != 3426 or ship["date"] != "2026-09-25":
        drift.append("bdi")
    if box["akshare"] is not False or box["source"] != "SSE":
        drift.append("container")
    if not (sent["vix"] < sent["vix50"]):
        drift.append("vix")
    if not (sent["vix_fg_level"] < 0 < sent["vix_pc_level"]):
        drift.append("corr")
    if not (sent["vix_pc_change"] < sent["vix_pc_level"]):
        drift.append("corr_change")
    if not (0.5 < sent["put_call"] < 1):
        drift.append("put_call")
    if sent["cnn"] != 37 or sent["rating"] != "fear" or sent["aaii"] != "ABSENT":
        drift.append("sentiment")
    if lock["us_owner"] != "FRED":
        drift.append("owner")
    return {
        "via": "vcgc",
        "door": "CGC_MDL193_MarketSync_v0100",
        "order": ["enter", "lock_success", "lock_record", "lock_path", "exit"],
        "enter": "vcgc",
        "lock_success": drift == [],
        "lock_record": LOCK.name,
        "lock_path": list(PATH),
        "exit": "vcgc",
        "name": "VIA",
        "same": True,
        "shipping_date": ship["date"],
        "container_source": box["source"],
        "cnn": sent["cnn"],
        "aaii": sent["aaii"],
        "drift": drift,
        "refetched": False,
        "registry_apply": False,
        "intake_edited": False,
        "lock_edited": False,
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
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = check()
    ok = card["lock_success"] and card["drift"] == [] and card["registry_apply"] is False and card["aaii"] == "ABSENT"
    print("  [OK]" if ok else "  [FAIL] " + json.dumps(card, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
