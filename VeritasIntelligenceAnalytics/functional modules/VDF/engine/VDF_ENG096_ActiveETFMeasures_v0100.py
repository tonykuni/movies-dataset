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
