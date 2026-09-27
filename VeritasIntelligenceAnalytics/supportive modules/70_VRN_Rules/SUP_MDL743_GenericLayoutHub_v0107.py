#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Layout tail. The newest filename must still expose the measured review route.

v0146 loads the last SUP_MDL743_GenericLayoutHub_v*.py and requires
def_run_batch. v0106 only gates entry, so registry-sync stopped with
ABSENT: complete layout review route. This tail keeps that gate and
forwards the v0104 route. Older files are not rewritten.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GATE = HERE / "SUP_MDL743_GenericLayoutHub_v0106.py"
ROUTE = HERE / "SUP_MDL743_GenericLayoutHub_v0105.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _gate():
    return _load(GATE, "layout_v0106_for_v0107")


def _route():
    return _load(ROUTE, "layout_v0105_for_v0107")


def __getattr__(name: str):
    gate = _gate()
    if name in gate.__dict__:
        return getattr(gate, name)
    return getattr(_route(), name)


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    gate = _gate()
    if "--selftest" in sys.argv:
        return gate.selftest()
    return gate.main() if hasattr(gate, "main") else 0


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    route = _route()
    ok = denied and GATE.is_file() and ROUTE.is_file() and callable(getattr(route, "def_run_batch", None)) and callable(getattr(route, "def_manifest", None))
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
