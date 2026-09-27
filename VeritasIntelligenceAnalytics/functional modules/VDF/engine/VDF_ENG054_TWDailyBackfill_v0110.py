#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Backfill tail. An empty ticker starts at 2022-07-01. v0109 is not rewritten.

Status is read-only. A missing database is a failure, not a green zero.
This file does not fetch the universe.
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import os
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE / "VDF_ENG054_TWDailyBackfill_v0109.py"
START = "2022-07-01"


def _load():
    spec = importlib.util.spec_from_file_location("tw_backfill_v0109_for_v0110", PRIOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.START_DATE = START
    return module


def db_status() -> dict:
    eng = _load()
    end = eng.target_date(datetime.now())
    failed = []
    earliest = None
    rows = None
    if not eng.DB_TW.is_file():
        failed.append("database absent")
        failed.append("no measured rows from 2022-07-01")
    else:
        import duckdb
        con = duckdb.connect(str(eng.DB_TW), read_only=True)
        try:
            rows, earliest, latest = con.execute(
                "SELECT COUNT(*), MIN(CAST(date AS VARCHAR)), MAX(CAST(date AS VARCHAR)) FROM tw_daily_prices"
            ).fetchone()
        except Exception as exc:
            failed.append("tw_daily_prices unreadable: " + type(exc).__name__)
            latest = None
        finally:
            con.close()
        if earliest is None:
            failed.append("tw_daily_prices empty")
        elif str(earliest)[:10] > START:
            failed.append("earliest " + str(earliest)[:10] + " is after 2022-07-01")
        else:
            end = str(latest)[:10] if latest else end
    return {
        "via": "vcgc",
        "door": "VDF_ENG054_TWDailyBackfill_v0110",
        "enter": "vcgc",
        "exit": "vcgc",
        "start": START,
        "end": end,
        "database": str(eng.DB_TW),
        "present": eng.DB_TW.is_file(),
        "rows": rows,
        "earliest": None if earliest is None else str(earliest)[:10],
        "fetched": False,
        "lock_success": failed == [],
        "failed": failed,
        "rewritten": False,
        "intake_edited": False,
        "do_not": [
            "rewrite v0109",
            "treat a missing database as green",
            "commit the duckdb",
            "edit intake macro_ssot",
        ],
        "next": "none" if not failed else "do not unlock; name the failed check",
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    card = db_status()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["lock_success"] else 2


def selftest() -> int:
    os.environ["VIA_FROM_VCGC"] = "YES"
    eng = _load()
    planned = dict(eng.plan([{"yf_ticker": "2330.TW"}], {}, "2026-09-25"))
    card = db_status()
    ok = planned.get("2330.TW") == START and card["present"] is False and "database absent" in card["failed"] and card["fetched"] is False and card["lock_success"] is False
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
