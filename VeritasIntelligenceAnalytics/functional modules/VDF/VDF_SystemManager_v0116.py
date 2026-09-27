#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF manager tail. via-vcgc calls collect() on the newest file.

v0115 still counts commands inside a dotted register. This file only puts collect() back on the module. It does not fetch.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE / "VDF_SystemManager_v0115.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _facade():
    return _load(PRIOR, "vdf_v0115_for_v0116")._body()


def collect() -> dict:
    return _facade().collect()


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VDF] 拒絕。只能經 via-vcgc。")
        return 2
    return _load(PRIOR, "vdf_v0115_passthrough").main()


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = collect()
    lamps = card.get("lamps") if isinstance(card, dict) else None
    ok = denied and isinstance(lamps, dict) and "engine" in lamps
    print("  [OK] " + str(card.get("rc_name")) if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
