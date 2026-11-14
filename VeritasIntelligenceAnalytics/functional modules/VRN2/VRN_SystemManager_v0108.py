#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN manager tail. via-vcgc calls read() and collect() on the newest file.

v0107 kept only `matrix` and `main`, so the console loaded v0107 as the newest
manager and found no read() and no collect(): 邏輯庫 / 因子庫 / VRN 系統管理 came
back BROKEN (AttributeError). v0105 and v0106 still forwarded every name to the
v0104 body; v0107 dropped that forward. This file puts the forward back.
v0107 is not rewritten; `matrix` and every other verb still go through v0107.
It does not read a PDF and does not write a tab.
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
PRIOR = HERE / "VRN_SystemManager_v0107.py"
CHAIN = HERE / "VRN_SystemManager_v0106.py"
_chain = None


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _facade():
    global _chain
    if _chain is None:
        _chain = _load(CHAIN, "vrn_v0106_for_v0108")
    return _chain


def read(domain: str, key: str | None = None, full: bool = False) -> dict:
    return _facade().read(domain, key, full)


def collect() -> dict:
    return _facade().collect()


def __getattr__(name: str):
    return getattr(_facade(), name)


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VRN] 拒絕。只能經 via-vcgc。")
        return 2
    return _load(PRIOR, "vrn_v0107_for_v0108").main()


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = collect()
    logic = read("logic")
    ok = (denied and PRIOR.is_file() and CHAIN.is_file()
          and card.get("schema") == "VIA.VRN.SystemManager.v1" and "state" in logic)
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())