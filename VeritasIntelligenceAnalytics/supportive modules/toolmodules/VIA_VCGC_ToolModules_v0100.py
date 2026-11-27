#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_VCGC_ToolModules v0100 — VCGC 補強工具模組(操作員 2026-11-27 上傳 · 導入倉內)。
唯讀來源檢查:panorama · catalog · context · compare · module-check · skills · metrics · schema · graph · registration-plan(用法見 README.md)。
加速器:本檔與 vcgc_tools/* 每支都經 [VIA:ACCEL-BRIDGE] 橋真的匯入 VIA_SuperAccel_Module(執行時載到才算;--selftest 會查)。
不 import 他系統、不出網、不執行被檢查的來源;零 TA-Lib。--selftest = 套件 34 項回歸 + 各模組加速器實際載入。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:  # noqa: BLE001
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

VERSION = "v0100"

import sys
sys.dont_write_bytecode = True
from vcgc_tools.cli import main


def selftest() -> int:
    import importlib
    import unittest
    from pathlib import Path
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    suite = unittest.defaultTestLoader.discover(str(here / "tests"))
    res = unittest.TextTestRunner(verbosity=0).run(suite)
    mods = ["vcgc_tools.actions", "vcgc_tools.cli", "vcgc_tools.core", "vcgc_tools.inventory", "vcgc_tools.report"]
    accel = {m: importlib.import_module(m).VIA_ACCEL is not None for m in mods}
    accel["entry"] = VIA_ACCEL is not None
    bad = [m for m, ok in accel.items() if not ok]
    n_tests, n_fail = res.testsRun, len(res.failures) + len(res.errors)
    checks = [("套件回歸測試全過", n_fail == 0 and n_tests >= 34, "%d 項 · 失敗 %d" % (n_tests, n_fail)),
              ("入口與 vcgc_tools 五支都真的載到加速器(VIA_ACCEL 非空)", not bad, "沒載到:%s" % bad)]
    for name, ok, note in checks:
        print(("  [OK] " if ok else "  [FAIL] ") + name + ("" if ok else " · " + note), flush=True)
    okc = sum(1 for c in checks if c[1])
    print("[計] VIA_VCGC_ToolModules v0100 自測 OK %d · FAIL %d · 回歸 %d 項" % (okc, len(checks) - okc, n_tests), flush=True)
    return 0 if okc == len(checks) else 1


if __name__ == "__main__":
    if sys.argv[1:2] in (["--selftest"], ["selftest"]):
        raise SystemExit(selftest())
    raise SystemExit(main())
