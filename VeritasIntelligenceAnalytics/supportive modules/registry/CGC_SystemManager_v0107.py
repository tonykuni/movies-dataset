#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC manager tail. `books` reads the policy, logic, and parameter pointer.

matrix and every older verb stay on v0106. The three books are not rewritten.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE / "CGC_SystemManager_v0106.py"
BOOKS = HERE / "CGC_MDL218_BookPointer_v0100.py"


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
    if "books" in sys.argv[1:]:
        return _load(BOOKS, "book_pointer_for_vcgc").main()
    return _load(PRIOR, "cgc_v0106_for_v0107").main()


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = _load(BOOKS, "book_pointer_self_vcgc").check()
    ok = denied and card["next"] == "none" and PRIOR.is_file()
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
