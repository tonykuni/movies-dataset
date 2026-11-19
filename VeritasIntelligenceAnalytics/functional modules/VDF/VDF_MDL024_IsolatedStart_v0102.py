#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF isolated start v0102. Same card as v0101, plus whether a FRED key is present. The value is never printed.

  py -3 VDF_MDL024_IsolatedStart_v0102.py start
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path


def load_accel():
    import VIA_SuperAccel_Module as via_accel
    return via_accel


def prior():
    path = Path(__file__).with_name("VDF_MDL024_IsolatedStart_v0101.py")
    spec = importlib.util.spec_from_file_location("vdf_iso_v0101", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fred_line() -> str:
    value = os.environ.get("FRED_API_KEY", "").strip()
    if value:
        return "fred_key=present source=env length=%d" % len(value)
    door = Path(__file__).resolve().parent / "output_hub" / "mega" / ".fred_api_key"
    if door.is_file():
        return "fred_key=present source=keyfile"
    return "fred_key=missing"


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    mod = prior()
    if argv[:1] == ["selftest"]:
        text = fred_line()
        if "FRED_API_KEY" in text or os.environ.get("FRED_API_KEY", "") and os.environ["FRED_API_KEY"] in text:
            print("[FAIL] key value leaked")
            return 1
        print("[OK] fred line does not contain the key")
        print(text)
        return mod.selftest()
    rc = mod.main(argv or ["start"])
    print(fred_line(), flush=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
