#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
via_net_unified_v0101 — 橋容轉接件(批124 正名令)
======================================================================
正典本體:SUP_MDL740_NetUnified_v*(命名冊規則;動態最新,嚴禁寫死
版號)。全樹 [VIA:NET-BRIDGE] 以 glob via_net_unified_v*.py 取最新版
掛橋——本件維持該名系=零斷鏈;API 全數自正典本體再輸出。
v0100 原件原樣在位(只增不減)。
"""
from __future__ import annotations

import importlib.util as _ilu
import sys as _sys
from pathlib import Path as _Path

_HERE = _Path(__file__).resolve().parent
_hits = sorted(_HERE.glob("SUP_MDL740_NetUnified_v*.py"))
if not _hits:
    raise ImportError("SUP_MDL740_NetUnified 正典本體缺(誠實 fail)")
_spec = _ilu.spec_from_file_location("SUP_MDL740_NetUnified", _hits[-1])
_canon = _ilu.module_from_spec(_spec)
_sys.modules["SUP_MDL740_NetUnified"] = _canon
_spec.loader.exec_module(_canon)
globals().update({_k: _v for _k, _v in vars(_canon).items()
                  if not _k.startswith("__")})
CANONICAL = _hits[-1].name

if __name__ == "__main__":
    _sys.exit(_canon.main())
