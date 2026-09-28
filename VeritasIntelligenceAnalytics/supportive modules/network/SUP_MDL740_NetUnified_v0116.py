#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Net-tool tail. OFF is not a scrape consent. YES and the compliance token are.

v0115 still treats any non-empty scrape value as set. This file does not fetch.
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
PRIOR = HERE / "SUP_MDL740_NetUnified_v0115.py"
GATE = HERE.parents[0] / "registry" / "CGC_MDL224_ScrapeGate_v0100.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_PRIOR = _load(PRIOR, "net_v0115_for_v0116")
_GATE = _load(GATE, "scrape_gate_for_net_v0116")


def gate_state() -> dict:
    g1 = os.environ.get("VIA_NET_CONSENT", "")
    g2 = os.environ.get("VIA_SCRAPE_CONSENT", "") or ""
    opened = g2 in _GATE.OPEN
    return {
        "gate1_net_consent": g1 == "YES",
        "gate2_scrape_token_set": opened,
        "gate1_raw": g1 or "(未設)",
        "open": g1 == "YES" and opened,
        "scrape_value": _GATE.scrape_value(),
    }


_PRIOR.gate_state = gate_state
for _name, _value in vars(_PRIOR).items():
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = _value
globals()["gate_state"] = gate_state


def selftest() -> int:
    saved = {key: os.environ.get(key) for key in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT")}
    try:
        os.environ.pop("VIA_NET_CONSENT", None)
        os.environ.pop("VIA_SCRAPE_CONSENT", None)
        unset = gate_state()
        os.environ["VIA_NET_CONSENT"] = "YES"
        os.environ["VIA_SCRAPE_CONSENT"] = "OFF"
        off = gate_state()
        os.environ["VIA_SCRAPE_CONSENT"] = "YES"
        yes = gate_state()
        os.environ["VIA_SCRAPE_CONSENT"] = _GATE.TOKEN
        token = gate_state()
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
    ok = (
        unset["open"] is False
        and off["gate2_scrape_token_set"] is False
        and off["open"] is False
        and yes["open"] is True
        and token["open"] is True
        and token["scrape_value"] == "TOKEN"
    )
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()
    return _PRIOR.main()


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
