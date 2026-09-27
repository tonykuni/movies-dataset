#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC manager tail. `backup` reads the VCGC and VDF register.

ledger and older verbs stay on v0109. This tail does not fetch.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE / "CGC_SystemManager_v0109.py"
DOOR = HERE / "CGC_MDL221_SystemBackup_v0100.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VCGC] 拒絕。只能經 via-vcgc。")
        return 2
    if "backup" in sys.argv[1:]:
        return _load(DOOR, "backup_for_vcgc").main()
    return _load(PRIOR, "cgc_v0109_for_v0110").main()


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = _load(DOOR, "backup_self_vcgc").check()
    ok = denied and card["lock_success"] and PRIOR.is_file()
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
