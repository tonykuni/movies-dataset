#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lock the store-gate mapping. It does not read a report or write Parquet."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

VIA = Path(__file__).resolve().parents[2]
ENGINE = VIA / "functional modules" / "VRN" / "VRN_ENG109_GateMap_v0100.py"


def _engine():
    spec = importlib.util.spec_from_file_location("gate_map", ENGINE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check() -> dict:
    mod = _engine()
    basic, page, row = mod._sample()
    good = mod.map_report(basic, page, [row])
    dashed = dict(basic)
    dashed["companyName"] = mod.DASH
    blocked = mod.map_report(dashed, page, [row])
    drift = []
    if not good["ready"] or good["report"]["basic"]["validationStatus"] != "VERIFIED":
        drift.append("pass")
    if basic["validationStatus"] != "PHASE2_OK" or row["status"] != "ok":
        drift.append("mutated")
    if blocked["ready"]:
        drift.append("dash")
    return {
        "via": "vcgc",
        "door": "CGC_MDL193_GateMapLock_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": drift == [],
        "keeps_logic_words": True,
        "copy_word": "VERIFIED",
        "drift": drift,
        "written": 0,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": ["rewrite PHASE2_OK in the logic row", "store a dash as a filled field", "treat a later page as page 1"],
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
    print("  [OK]" if card["lock_success"] else "  [FAIL]")
    return 0 if card["lock_success"] else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
