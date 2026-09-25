#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parameter hub v0110. v0109 plus the US macro parameter book.

The index is not rebuilt here. A later scan of this module keeps USMACRO_PARAMS.
"""
from __future__ import annotations
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("via_params_central_v0109", HERE / "via_params_central_v0109.py")
prev = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = prev
spec.loader.exec_module(prev)

BOOKS = list(prev.BOOKS)
if not any(b["id"] == "USMACRO_PARAMS" for b in BOOKS):
    BOOKS.append({
        "id": "USMACRO_PARAMS",
        "domain": "REGISTRY",
        "conflict_scope": False,
        "path": "supportive modules/registry/VIA_USMacro_Params_v0100.json",
        "note": "US macro unit, frequency, and scale. Source books stay put.",
    })

def selftest() -> int:
    ids = [b["id"] for b in BOOKS]
    paths = [b["path"] for b in BOOKS]
    ok = ("USMACRO_PARAMS" in ids and len(ids) == len(set(ids)) and len(paths) == len(set(paths))
          and len(BOOKS) == len(prev.BOOKS) + 1)
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(selftest())
