#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Console tail. `test` runs the VCGC selftest list. Other verbs stay on v0159.

The suite does not fetch and does not push.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE / "CGC_MDL149_VeritasCentralGovernanceConsole_v0159.py"
DOOR = HERE / "CGC_MDL224_TestAuto_v0100.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


prev = _load(PREVIOUS, "vcgc_v0159_for_v0160")


def __getattr__(name: str):
    return getattr(prev, name)


def main(argv=None):
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    if args[:1] == ["test"]:
        os.environ["VIA_VCGC_PUSH"] = "NO"
        return _load(DOOR, "test_for_console").main()
    return prev.main(argv)


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main(["test"]) == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    ok = denied and DOOR.is_file() and PREVIOUS.is_file()
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
