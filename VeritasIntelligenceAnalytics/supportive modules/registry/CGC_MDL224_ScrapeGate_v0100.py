#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One scrape ruler. Empty and OFF stay closed. YES and the compliance token both count as open.

This module does not set VIA_NET_CONSENT or VIA_SCRAPE_CONSENT and does not fetch.
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

import os

TOKEN = "I_ACCEPT_RESPONSIBLE_SCRAPING"
OPEN = {"YES", TOKEN}


def gate_open(env=None) -> bool:
    env = os.environ if env is None else env
    return env.get("VIA_NET_CONSENT") == "YES" and (env.get("VIA_SCRAPE_CONSENT") or "") in OPEN


def scrape_value(env=None) -> str:
    env = os.environ if env is None else env
    raw = env.get("VIA_SCRAPE_CONSENT") or ""
    if raw == "YES":
        return "YES"
    if raw == TOKEN:
        return "TOKEN"
    if raw == "OFF":
        return "OFF"
    if not raw:
        return "UNSET"
    return "OTHER"


def selftest() -> int:
    ok = (
        gate_open({}) is False
        and gate_open({"VIA_NET_CONSENT": "YES", "VIA_SCRAPE_CONSENT": "OFF"}) is False
        and gate_open({"VIA_NET_CONSENT": "YES"}) is False
        and gate_open({"VIA_NET_CONSENT": "OFF", "VIA_SCRAPE_CONSENT": "YES"}) is False
        and gate_open({"VIA_NET_CONSENT": "YES", "VIA_SCRAPE_CONSENT": "YES"}) is True
        and gate_open({"VIA_NET_CONSENT": "YES", "VIA_SCRAPE_CONSENT": TOKEN}) is True
        and scrape_value({}) == "UNSET"
        and scrape_value({"VIA_SCRAPE_CONSENT": "OFF"}) == "OFF"
    )
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    raise SystemExit(selftest() if "--selftest" in sys.argv else 0)
