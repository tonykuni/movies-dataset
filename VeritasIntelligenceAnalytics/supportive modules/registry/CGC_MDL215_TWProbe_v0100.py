#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The one-ticker probe stays a record. It does not refetch and it does not fill the market database."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RECORD = HERE / "VIA_TWProbe_2330_v0100.json"


def check() -> dict:
    rec = json.loads(RECORD.read_text(encoding="utf-8"))
    drift = []
    if rec.get("rows") != 1030 or rec.get("start") != "2022-07-01" or rec.get("end") != "2026-09-24":
        drift.append("probe")
    if rec.get("universe_written") is not False or rec.get("production_db") != "absent":
        drift.append("scope")
    return {
        "via": "vcgc",
        "door": "CGC_MDL215_TWProbe_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "ticker": rec["ticker"],
        "rows": rec["rows"],
        "start": rec["start"],
        "end": rec["end"],
        "lane": rec["lane"],
        "passed": rec["passed"],
        "failed": rec["failed"],
        "lock_success": False,
        "refetched": False,
        "drift": drift,
        "intake_edited": False,
        "do_not": rec["do_not"],
        "next": "none" if not drift else "do not unlock; name the drift",
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    card = check()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if not card["drift"] else 2


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = check()
    ok = denied and card["rows"] == 1030 and card["lock_success"] is False and "database absent" in card["failed"] and card["refetched"] is False
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
