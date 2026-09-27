#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN manager tail. `matrix` shows the shared manager list. Every other verb stays on v0106.

v0106 is not rewritten. This verb does not read a PDF or write a tab.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
PRIOR = HERE / "VRN_SystemManager_v0106.py"
MATRIX = VIA / "supportive modules" / "registry" / "CGC_MDL217_ManagerMatrix_v0100.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VRN] 拒絕。只能經 via-vcgc。")
        return 2
    if "matrix" in sys.argv[1:]:
        return _load(MATRIX, "manager_matrix_for_vrn").main()
    return _load(PRIOR, "vrn_v0106_for_v0107").main()


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = _load(MATRIX, "manager_matrix_self_vrn").check()
    ok = denied and card["next"] == "none" and PRIOR.is_file()
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
