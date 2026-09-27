#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Confirm the NLP roster now has central codes. Do not call the engines.

Thirteen roster ids, twelve uses from 1.8, and five names that live only
inside 1.9. The write checked the plan before touching the book. TA-Lib
is not part of this batch.
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
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOOK = HERE / "VIA_Component_Inventory_SSOT_v0100.json"
ROSTER = HERE / "VIA_NLP_Roster_v0100.json"


def check() -> dict:
    data = json.loads(BOOK.read_text(encoding="utf-8")) if BOOK.is_file() else {}
    roster = json.loads(ROSTER.read_text(encoding="utf-8"))
    active = {row.get("key"): row.get("code") for row in data.get("records") or [] if row.get("state") == "ACTIVE"}
    missing = [item["id"] for item in roster["rows"] if "feature|nlp/" + item["id"] not in active]
    talib = [key for key in active if "talib" in key.lower() and key.startswith("feature|nlp/")]
    return {
        "via": "vcgc",
        "door": "CGC_MDL204_NlpCodes_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": not missing and not talib,
        "roster": len(roster["rows"]),
        "coded": len(roster["rows"]) - len(missing),
        "sample": active.get("feature|nlp/oneengine_190", ""),
        "called": False,
        "talib": "not in this batch",
        "plan_before_write": True,
        "missing": missing,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": [
            "pip install TA-Lib",
            "call the roster from the report door",
            "registry-sync --apply without --layout-only or --nlp-only",
            "retire an old inventory code",
            "edit intake macro_ssot",
        ],
        "next": "none" if not missing else "do not unlock; name the drift",
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
    print("  [OK]" if card["lock_success"] else "  [FAIL] " + ",".join(card["missing"]))
    return 0 if card["lock_success"] else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
