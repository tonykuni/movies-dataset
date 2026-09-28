#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC manager tail. The default card is the database seat, not GitHub.

v0104 still owns the panorama. This file does not rewrite it or the law book.
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

import importlib.util
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE / "CGC_SystemManager_v0104.py"
SEAT = HERE / "CGC_MDL212_DataSeat_v0100.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        seat = _load(SEAT, "data_seat_deny_v0105")
        return seat.main()
    if "policy" in sys.argv[1:]:
        return _load(PRIOR, "cgc_v0104_for_policy").main()
    return _load(SEAT, "data_seat_for_v0105").main()


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    os.environ.pop("VIA_VRN_DATA", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = _load(SEAT, "data_seat_self_v0105").check()
    ok = denied and card["status"] == "OFF_PC" and card["opened"] is False and PRIOR.is_file()
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
