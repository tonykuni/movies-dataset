#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VAP downward mouth. VCGC is the only caller. This file does not install or launch engines."""
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
import os
import sys


def enter() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VAP] 拒絕。只能經 via-vcgc。")
        return 2
    print("[VAP] 對接口在。不安裝,不啟動引擎。")
    return 0


def selftest() -> int:
    old = os.environ.pop("VIA_FROM_VCGC", None)
    denied = enter()
    os.environ["VIA_FROM_VCGC"] = "YES"
    allowed = enter()
    if old is None:
        os.environ.pop("VIA_FROM_VCGC", None)
    else:
        os.environ["VIA_FROM_VCGC"] = old
    ok = denied == 2 and allowed == 0
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else enter())
