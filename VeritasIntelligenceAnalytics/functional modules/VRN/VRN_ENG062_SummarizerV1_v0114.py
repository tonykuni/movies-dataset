#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ENG062_SummarizerV1 v0114 — v0113 薄尾(v0113 一字不動):--selftest 找不到測試檔 → 照實 NODATA(rc 2),不算壞。

實錄(2026-11-13 容器全量實跑 VRN_SystemManager v0264 test:VRN_ENG062 FAIL rc 1):
  v0113 的 --selftest 只在本檔所在夾找 test_summary*.py;倉內沒有這幾支測試檔(在 VRN-2 套件包裡)→ 跑 0 個測試 → rc 1。
  依 L16「缺件 ≠ 壞」:沒測到要照實說「沒測到」(NODATA · rc 2),不能當成失敗,也不能假裝通過。
本版只改 --selftest:依序找 本夾 → ../VRN2(VRN-2 套件夾)的 test_summary*.py;找到 → 照 v0113 跑(過 0 · 不過 1);
  都沒有 → 印原因 + rc 2。其餘(--input / --ticker / --status / --test)全部原樣交 v0113。
零網路;不用 TA-Lib;不寫同意閘。
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
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
# [VIA:NET-BRIDGE] 留名:本版不出網

import importlib.util
import re
import sys
from pathlib import Path

VERSION = "v0114"
TAG = "VRN_ENG062_SummarizerV1 " + VERSION
HERE = Path(__file__).resolve().parent
_STEM = "VRN_ENG062_SummarizerV1"
TEST_PATTERN = "test_summary*.py"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_PRIOR = None


def _prior():
    global _PRIOR
    if _PRIOR is None:
        spec = importlib.util.spec_from_file_location(_STEM + "_prior_for_" + Path(__file__).stem, PRIOR_PATH)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        _PRIOR = mod
    return _PRIOR


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(_prior(), name)


def test_dirs() -> list:
    return [d for d in (HERE, HERE.parent / "VRN2") if d.is_dir() and any(d.glob(TEST_PATTERN))]


def selftest() -> int:
    import unittest
    dirs = test_dirs()
    if not dirs:
        print("[NODATA] %s --selftest · 找不到 %s(本夾 %s · VRN-2 套件夾 %s 都沒有)→ 沒測到 ≠ 壞(L16)· 測試檔在 VRN-2 套件包"
              % (TAG, TEST_PATTERN, HERE.name, (HERE.parent / "VRN2").name), flush=True)
        return 2
    total, ok = 0, True
    for d in dirs:
        r = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover(str(d), pattern=TEST_PATTERN))
        total += r.testsRun
        ok = ok and r.wasSuccessful()
    print("[%s] %s --selftest · 夾 %s · 測 %d" % ("PASS" if ok and total else "FAIL", TAG, ", ".join(x.name for x in dirs), total), flush=True)
    return 0 if ok and total else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return _prior().main() or 0


if __name__ == "__main__":
    sys.exit(main())
