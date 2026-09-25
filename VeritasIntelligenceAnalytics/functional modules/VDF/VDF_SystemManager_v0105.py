#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF. Same manager as the previous tail. Direct start is refused."""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

_OLD = Path(__file__).resolve().parent / "VDF_SystemManager_v0104.py"
_body = None


def _load():
    global _body
    if _body is None:
        spec = importlib.util.spec_from_file_location(_OLD.stem, _OLD)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _body = mod
    return _body


def __getattr__(name: str):
    return getattr(_load(), name)


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VDF] 拒絕。只能經 via-vcgc。")
        return 2
    return _load().main()


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    ok = main() == 2
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
