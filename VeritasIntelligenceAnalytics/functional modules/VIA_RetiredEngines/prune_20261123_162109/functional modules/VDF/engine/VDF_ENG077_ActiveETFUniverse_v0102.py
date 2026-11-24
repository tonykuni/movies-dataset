#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG077_ActiveETFUniverse tail. The scrape gate accepts YES or the compliance token.

OFF and an empty value stay closed. This file does not set a consent and does not fetch during selftest.
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0100] =====
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
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR = HERE / "VDF_ENG077_ActiveETFUniverse_v0101.py"
GATE = HERE.parents[2] / "supportive modules" / "registry" / "CGC_MDL224_ScrapeGate_v0100.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _prior():
    module = _load(PRIOR, "etfuniv_v0101_for_v0102")
    module.gate_open = _load(GATE, "scrape_gate_for_etfuniv_v0102").gate_open
    return module


def main() -> int:
    return _prior().main()


def selftest() -> int:
    gate = _load(GATE, "scrape_gate_etfuniv_test").gate_open
    ok = (
        gate({}) is False
        and gate({"VIA_NET_CONSENT": "YES", "VIA_SCRAPE_CONSENT": "OFF"}) is False
        and gate({"VIA_NET_CONSENT": "YES", "VIA_SCRAPE_CONSENT": "YES"}) is True
        and gate({"VIA_NET_CONSENT": "YES", "VIA_SCRAPE_CONSENT": "I_ACCEPT_RESPONSIBLE_SCRAPING"}) is True
    )
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
