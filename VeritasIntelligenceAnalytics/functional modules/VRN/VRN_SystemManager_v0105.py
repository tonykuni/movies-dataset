#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN. Same manager as the previous tail. Direct start is refused."""
# ===== [VIA:ACCEL-BRIDGE:v0100] 加速器橋(2026-10-08 accel sweep 注入;L103 最高政策 PY 導入加速器;缺席不擋,記黃) =====
import sys as _ab_sys
from pathlib import Path as _ab_Path
_ab_p = _ab_Path(__file__).resolve()
while _ab_p.parent != _ab_p:
    if (_ab_p / "supportive modules").is_dir():
        _ab_sys.path.insert(0, str(_ab_p / "supportive modules"))
        break
    _ab_p = _ab_p.parent
try:
    import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401
except Exception:  # noqa: BLE001
    _ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

_OLD = Path(__file__).resolve().parent / "VRN_SystemManager_v0104.py"
_body = None


def _load():
    global _body
    if _body is None:
        spec = importlib.util.spec_from_file_location(_OLD.stem, _OLD)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _body = mod
    return _body


def __getattr__(name: str):
    return getattr(_load(), name)


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VRN] 拒絕。只能經 via-vcgc。")
        return 2
    return _load().main()


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    ok = main() == 2
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
