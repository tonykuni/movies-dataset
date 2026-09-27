#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Handover of the successful VDF version. v0109 stays. This door does not refetch."""
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
VIA = HERE.parents[1]
RECORD = HERE / "VIA_VDFHandoverRestore_v0100.json"
ENGINE = VIA / "functional modules" / "VDF" / "engine" / "VDF_ENG054_TWDailyBackfill_v0109.py"
DROPPED = VIA / "functional modules" / "VDF" / "engine" / "VDF_ENG054_TWDailyBackfill_v0110.py"


def check() -> dict:
    rec = json.loads(RECORD.read_text(encoding="utf-8"))
    drift = []
    if not ENGINE.is_file():
        drift.append("v0109")
    if DROPPED.is_file():
        drift.append("v0110")
    if rec.get("retest") != "12/12" or rec.get("fetched") is not False:
        drift.append("record")
    return {
        "via": "vcgc",
        "door": "CGC_MDL214_VdfHandover_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": drift == [],
        "restored_to": rec["restored_to"],
        "retest": rec["retest"],
        "fetched": False,
        "drift": drift,
        "rewritten": False,
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
    return 0 if card["lock_success"] else 2


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = check()
    ok = denied and card["lock_success"] and card["retest"] == "12/12" and card["fetched"] is False
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
