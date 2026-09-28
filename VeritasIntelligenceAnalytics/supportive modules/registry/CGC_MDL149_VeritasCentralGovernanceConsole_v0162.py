#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Console tail v0162. Only `layout ... --selftest` changes.

From v0150 on, each console tail answered any `--selftest` in argv with its
own self-check, so `via-vcgc layout --selftest` printed the console's DENY
line and [OK] and never reached the layout hub. The result looked green
while nothing about layout was tested (Z225). v0162 sends `layout` with
`--selftest` to the hub the chain already resolves (def_layout_hub, the
v0146 route, reached through the tails' __getattr__). Every other argument
list goes to v0161 unchanged. v0161 stays on disk (L04).
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
PREVIOUS = HERE / "CGC_MDL149_VeritasCentralGovernanceConsole_v0161.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


prev = _load(PREVIOUS, "vcgc_v0161_for_v0162")


def __getattr__(name: str):
    return getattr(prev, name)


def _is_layout_selftest(args) -> bool:
    return bool(args) and args[0] == "layout" and "--selftest" in args[1:]


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if _is_layout_selftest(args):
        if os.environ.get("VIA_FROM_VCGC") != "YES":
            print('{"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}')
            return 2
        hub = prev.def_layout_hub()
        print(f"[layout] 樞紐自測 {Path(hub.__file__).name}")
        return hub.selftest()
    return prev.main(argv)


def selftest() -> int:
    routed = _is_layout_selftest(["layout", "--selftest"]) and not _is_layout_selftest(["status"]) \
        and not _is_layout_selftest(["--selftest"]) and not _is_layout_selftest(["layout", "--dir", "x"])
    hub = prev.def_layout_hub()
    hub_ok = callable(getattr(hub, "selftest", None)) and Path(hub.__file__).name.startswith("SUP_MDL743_GenericLayoutHub_v")
    print(f"  [{'OK' if routed else 'FAIL'}] layout --selftest 走樞紐,其餘參數照舊給 v0161")
    print(f"  [{'OK' if hub_ok else 'FAIL'}] 樞紐尾版 {Path(hub.__file__).name}")
    if not (routed and hub_ok):
        return 1
    return prev.selftest()


if __name__ == "__main__":
    args = sys.argv[1:]
    raise SystemExit(selftest() if args == ["--selftest"] else main())
