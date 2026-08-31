#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VIA_SuperAccel_Module — 相容轉接件(批124 正名令)
======================================================================
操作員令(批124,2026-08-24):「加速器依照我們的規定改名稱」。
正典本體:SUP_MDL737_SuperAccelModule_v*(命名冊 TOOL-047 既定號
SUP_MDL737;動態解析最新版,嚴禁寫死版號)。
本件=相容轉接:全樹 [VIA:ACCEL-BRIDGE] 正典塊以
`import VIA_SuperAccel_Module` 掛橋,路徑與模組名維持不變=零破壞;
API(accel_map/fetch/pip_install/run_fast/stats/selftest)全數
自正典本體再輸出。內容遷移非刪除:v0100 本體 byte-exact 存於正典檔
(原件 sha256 見台帳 TOOL-124)。
"""
from __future__ import annotations

import importlib.util as _ilu
import sys as _sys
from pathlib import Path as _Path

_HERE = _Path(__file__).resolve().parent
_hits = sorted(_HERE.glob("SUP_MDL737_SuperAccelModule_v*.py"))
if not _hits:
    raise ImportError("SUP_MDL737_SuperAccelModule 正典本體缺(誠實 fail)")
_spec = _ilu.spec_from_file_location("SUP_MDL737_SuperAccelModule", _hits[-1])
_canon = _ilu.module_from_spec(_spec)
_sys.modules["SUP_MDL737_SuperAccelModule"] = _canon
_spec.loader.exec_module(_canon)
globals().update({_k: _v for _k, _v in vars(_canon).items()
                  if not _k.startswith("__")})
CANONICAL = _hits[-1].name

if __name__ == "__main__":
    _sys.exit(_canon.selftest())
