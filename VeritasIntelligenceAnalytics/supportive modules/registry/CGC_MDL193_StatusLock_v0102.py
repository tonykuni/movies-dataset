#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lock pass. VIA is VCGC, so the same door enters and exits."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, HERE / name)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def emit(card: dict) -> dict:
    who = _load("CGC_MDL149_Identity_v0100.py").card()
    body = _load("CGC_MDL193_StatusLock_v0101.py").emit(card)
    body["door"] = "CGC_MDL193_StatusLock_v0102"
    body["name"] = who["name"]
    body["same"] = who["same"]
    body["enter"] = who["via"]
    body["exit"] = who["via"]
    return body


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    card = emit(_load("CGC_MDL193_StatusLock_v0100.py").check())
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["lock_success"] and card["same"] else 2


def selftest() -> int:
    ident = _load("CGC_MDL149_Identity_v0100.py")
    fails = []

    def chk(name, ok):
        if not ok:
            fails.append(name)
        print(f"  [{'OK' if ok else 'FAIL'}] {name}")

    chk("identity holds", ident.selftest() == 0)
    sample = emit({"locked": ["knowledge_assets", "usmacro_params", "method_selftest"], "drift": []})
    chk("enter and exit are the same door", sample["enter"] == sample["exit"] == "vcgc" and sample["name"] == "VIA" and sample["same"] is True)
    chk("the lock steps stay in order", sample["order"] == ["enter", "lock_success", "lock_record", "lock_path", "exit"])
    os.environ["VIA_FROM_VCGC"] = "YES"
    live = emit(_load("CGC_MDL193_StatusLock_v0100.py").check())
    chk("the live lock still holds through the one door", live["lock_success"] and live["lock_edited"] is False)
    print(f"  [計] FAIL {len(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
