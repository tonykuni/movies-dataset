#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lock the 19:15 probe. Read-only. Does not refetch and does not rewrite the status lock."""
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
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOCK = HERE / "VIA_USMacroProbeLock_v0100.json"
PATH = (
    "Invoke-VIA-VCGC-ProbeLock.ps1",
    "CGC_MDL193_ProbeLock_v0100.py",
    "VIA_USMacroProbeLock_v0100.json",
)


def check() -> dict:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    m = lock["millions"]
    drift = []
    if m["WLRRAFOIAL"] + m["WLRRAOL"] != m["WLRRAL"]:
        drift.append("rrp_split")
    if m["WSHOTSL"] != m["TREAST"]:
        drift.append("wshotsl")
    if lock["stale"]["date"][:4] != "2020" or lock["stale"]["refresh"] is not False:
        drift.append("discborr")
    if lock["parked"] != ["NAPM", "NMFCI", "NAPMNOI", "USMFGPMI", "AMDMNO"]:
        drift.append("parked")
    if lock["counts"] != {"LIVE": 51, "PARKED": 5} or lock["series"] != 56:
        drift.append("counts")
    if m["DTS_TGA_CLOSE"] == m["WTREGEN"]:
        drift.append("tga_same_book")
    return {
        "via": "vcgc",
        "door": "CGC_MDL193_ProbeLock_v0100",
        "order": ["enter", "lock_success", "lock_record", "lock_path", "exit"],
        "enter": "vcgc",
        "lock_success": drift == [],
        "lock_record": LOCK.name,
        "lock_path": list(PATH),
        "exit": "vcgc",
        "name": "VIA",
        "same": True,
        "measured_at": lock["measured_at"],
        "series": lock["series"],
        "counts": lock["counts"],
        "parked": lock["parked"],
        "stale": lock["stale"]["id"],
        "drift": drift,
        "lock_edited": False,
        "intake_edited": False,
        "refetched": False,
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
    ok = card["lock_success"] and card["drift"] == [] and card["refetched"] is False and card["stale"] == "DISCBORR"
    print("  [OK]" if ok else "  [FAIL] " + json.dumps(card, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
