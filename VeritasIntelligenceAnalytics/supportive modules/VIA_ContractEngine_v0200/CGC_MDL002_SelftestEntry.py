#!/usr/bin/env python3
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
# 契約介面引擎自測入口(自測矩陣站用):pytest 缺=rc3 誠實(env 類→SKIP)
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
try:
    import pytest  # noqa: F401
    import pydantic  # noqa: F401
except ImportError as exc:
    print(f"[SKIP] 依賴缺({exc.name})——via-install pytest pydantic 後重跑")
    sys.exit(3)
env = dict(os.environ, PYTHONPATH=str(HERE / "src"))
r = subprocess.run([sys.executable, "-m", "pytest", str(HERE / "tests"), "-q"],
                   env=env, stdin=subprocess.DEVNULL)
sys.exit(r.returncode)
