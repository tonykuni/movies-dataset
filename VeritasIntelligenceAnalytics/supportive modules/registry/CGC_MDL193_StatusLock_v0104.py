#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lock pass. Same door. The parameter hash ignores line endings."""
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


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    card = _load("CGC_MDL193_StatusLock_v0102.py").emit(_load("CGC_MDL193_StatusLock_v0103.py").check())
    card["door"] = "CGC_MDL193_StatusLock_v0104"
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["lock_success"] and card["same"] else 2


def selftest() -> int:
    param = _load("CGC_MDL192_MacroParamSync_v0101.py")
    lock = _load("CGC_MDL193_StatusLock_v0103.py")
    ok = param.selftest() == 0 and lock.selftest() == 0
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
