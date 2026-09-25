#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Measures from rows already stored. This file does not fetch.

淨值 is the price of one unit. 規模 is units times that price, plus cash.
申購贖回 changes the unit count, not the 淨值.
市價 can sit above 淨值 (premium) or below it (discount):
(price - nav) / nav. That gap is not flow and it does not change 規模.

Flow estimate, same dates only:
today's AUM minus yesterday's AUM grown by the NAV return.
Positive is inflow, negative is outflow.
總買賣超 is buy minus sell on one stock row.
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
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====


def aum_flow(prev_aum: float, aum: float, nav_return: float) -> dict:
    expected = float(prev_aum) * (1.0 + float(nav_return))
    net = float(aum) - expected
    return {
        "aum": float(aum),
        "inflow": net if net > 0 else 0.0,
        "outflow": -net if net < 0 else 0.0,
        "net": net,
        "kind": "ESTIMATE",
    }


def net_buy_sell(buy: float, sell: float) -> float:
    return float(buy) - float(sell)


def selftest() -> int:
    checks = []

    def chk(name, ok):
        checks.append((name, bool(ok)))

    inn = aum_flow(100.0, 110.0, 0.0)
    out = aum_flow(100.0, 90.0, 0.0)
    flat = aum_flow(100.0, 101.0, 0.01)
    chk("inflow", inn["inflow"] == 10.0 and inn["outflow"] == 0.0)
    chk("outflow", out["outflow"] == 10.0 and out["inflow"] == 0.0)
    chk("return explains aum", flat["net"] == 0.0 and flat["kind"] == "ESTIMATE")
    chk("net buy", net_buy_sell(30, 12) == 18 and net_buy_sell(4, 9) == -5)
    bad = [name for name, ok in checks if not ok]
    print(f"[VDF_ENG096 v0100] {len(checks) - len(bad)}/{len(checks)}" + (f" FAIL {bad}" if bad else " OK"))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(selftest())
