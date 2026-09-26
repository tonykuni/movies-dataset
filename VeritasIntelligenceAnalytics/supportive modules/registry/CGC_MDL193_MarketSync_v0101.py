#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Same market lock. AAII is the loaded workbook, not the old absent flag."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOCK = HERE / "VIA_MarketSyncLock_v0101.json"


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
    if sent["cnn"] != 37 or sent["rating"] != "fear":
        drift.append("cnn")
    if sent["aaii"] != "LIVE" or sent["aaii_rows"] != 2042 or sent["aaii_last"] != "2026-09-24":
        drift.append("aaii")
    if lock["us_owner"] != "FRED":
        drift.append("owner")
    return {
        "via": "vcgc",
        "door": "CGC_MDL193_MarketSync_v0101",
        "order": ["enter", "lock_success", "lock_record", "lock_path", "exit"],
        "enter": "vcgc",
        "lock_success": drift == [],
        "lock_record": LOCK.name,
        "lock_path": ["Invoke-VIA-VCGC-SyncAll.ps1", "CGC_MDL193_MarketSync_v0101.py", LOCK.name],
        "exit": "vcgc",
        "name": "VIA",
        "same": True,
        "shipping_date": ship["date"],
        "container_source": box["source"],
        "cnn": sent["cnn"],
        "aaii": sent["aaii"],
        "aaii_rows": sent["aaii_rows"],
        "aaii_last": sent["aaii_last"],
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
    card = check()
    ok = card["lock_success"] and card["aaii"] == "LIVE" and card["aaii_rows"] == 2042 and card["refetched"] is False
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
