#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC manager tail. Entering reads the policy book and runs the one panorama.

v0103 is not rewritten. A red panorama is not locked.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE / "CGC_SystemManager_v0103.py"
GATE = HERE / "CGC_MDL211_FlowGate_v0101.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-managers"}, ensure_ascii=False))
        return 2
    return _load(GATE, "flow_gate_v0101_for_cgc_v0104").main()


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    gate = _load(GATE, "flow_gate_v0101_self_cgc")
    card = gate.read_policy()
    ok = denied and card.get("lock_success") is True and card.get("panorama") == "MDL205" and PRIOR.is_file()
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
