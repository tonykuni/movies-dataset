#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AKShare probe. Refuses a raw python call. The central launcher must enter first."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _prior():
    spec = importlib.util.spec_from_file_location("ak_v0101", HERE / "VDF_ENG110_AKShareProbe_v0101.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def allowed() -> bool:
    return os.environ.get("VIA_CENTRAL_ENTRY") == "1" and os.environ.get("VIA_FROM_VCGC") == "YES"


def main() -> int:
    if not allowed():
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-akshare through Invoke-VIAPython"}, ensure_ascii=False))
        return 2
    card = _prior().probe()
    card["door"] = "VDF_ENG110_AKShareProbe_v0102"
    card["enter"] = "vcgc"
    card["exit"] = "vcgc"
    card["central"] = True
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["installed"] else 2


def selftest() -> int:
    os.environ.pop("VIA_CENTRAL_ENTRY", None)
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = not allowed()
    os.environ["VIA_CENTRAL_ENTRY"] = "1"
    still = not allowed()
    os.environ["VIA_FROM_VCGC"] = "YES"
    opened = allowed()
    ok = denied and still and opened
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
