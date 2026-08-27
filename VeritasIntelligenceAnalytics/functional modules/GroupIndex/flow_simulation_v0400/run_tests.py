#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""run_tests — 族群流模擬系統 v0400 測試套統一入口(收容整合層,原件零觸碰)
容器/工作站皆可:PYTHONPATH 掛包根後跑 30 檢 unittest;rc0=全過。"""
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
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py",
                                                top_level_dir=str(ROOT))
    r = unittest.TextTestRunner(verbosity=1).run(suite)
    print(f"[計] 族群流模擬 v0400 測試 {r.testsRun} 跑 · FAIL {len(r.failures)} · ERR {len(r.errors)}")
    sys.exit(0 if r.wasSuccessful() else 1)
