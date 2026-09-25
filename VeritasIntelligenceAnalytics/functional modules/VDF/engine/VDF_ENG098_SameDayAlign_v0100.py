#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG098 — one Taiwan stock, one date.

TWSE/TPEX owns the row. yfinance close is only a check against that close.
The adjustment factor is adj_close / close, and it is applied only when the
two closes overlap. QuantGuard uses volume and value after day-trade is
removed. Display may ask for the gross figures instead.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
POLICY = VIA / "supportive modules" / "registry" / "VIA_TW_SameDayAlign_Policy_v0100.json"
CLOSE_TOL = 0.001

EXCHANGE_FIELDS = (
    "open", "high", "low", "close", "volume", "value",
    "foreign_net", "trust_net", "dealer_net", "total_net",
    "foreign_holding_pct", "trust_holding_pct", "dealer_holding_pct",
    "margin_bal", "short_bal", "short_margin_ratio",
    "margin_maint_pct", "margin_usage_pct", "short_usage_pct",
    "daytrade_volume", "daytrade_value",
)


def _num(value):
    if value is None or value == "":
        return None
    return float(value)


def closes_overlap(exchange_close, yahoo_close, tol: float = CLOSE_TOL) -> bool:
    left, right = _num(exchange_close), _num(yahoo_close)
    if left is None or right is None or left == 0:
        return False
    return abs(left - right) / abs(left) <= tol


def align_day(exchange: dict, yahoo: dict | None = None, view: str = "net") -> dict:
    """Join one date. view is 'net' (QuantGuard) or 'gross' (display)."""
    if view not in {"net", "gross"}:
        raise ValueError("view must be net or gross")
    yahoo = yahoo or {}
    out = {
        "date": exchange.get("date"),
        "code": exchange.get("code"),
        "view": view,
    }
    for key in EXCHANGE_FIELDS:
        out[key] = _num(exchange.get(key)) if key not in {"date"} else exchange.get(key)
    volume = out["volume"]
    value = out["value"]
    dt_vol = out["daytrade_volume"]
    dt_val = out["daytrade_value"]
    out["daytrade_ratio"] = (dt_vol / volume) if volume not in (None, 0) and dt_vol is not None else None
    if volume is None or dt_vol is None:
        out["volume_net"] = None
    else:
        out["volume_net"] = volume - dt_vol
    if value is None or dt_val is None:
        out["value_net"] = None
    else:
        out["value_net"] = value - dt_val
    out["volume_gross"] = volume
    out["value_gross"] = value
    if view == "net":
        out["quant_volume"] = out["volume_net"]
        out["quant_value"] = out["value_net"]
    else:
        out["quant_volume"] = volume
        out["quant_value"] = value
    overlap = closes_overlap(out["close"], yahoo.get("close"))
    out["close_overlap"] = overlap
    y_close, y_adj = _num(yahoo.get("close")), _num(yahoo.get("adj_close"))
    factor = (y_adj / y_close) if overlap and y_close not in (None, 0) and y_adj is not None else None
    out["adj_factor"] = factor
    for src, dst in (("open", "adj_open"), ("high", "adj_high"), ("low", "adj_low"), ("close", "adj_close")):
        out[dst] = None if factor is None or out[src] is None else out[src] * factor
    return out


def selftest() -> int:
    checks = []

    def chk(name, ok):
        checks.append((name, bool(ok)))

    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    chk("policy", policy["rank"] == "major" and policy["quantguard"]["volume_value"].startswith("扣除當沖"))
    row = {
        "date": "2026-09-25", "code": "2330",
        "open": 100, "high": 110, "low": 90, "close": 100,
        "volume": 1000, "value": 100000,
        "foreign_net": 10, "trust_net": -2, "dealer_net": 1, "total_net": 9,
        "margin_bal": 50, "short_bal": 5, "short_margin_ratio": 10,
        "daytrade_volume": 200, "daytrade_value": 20000,
    }
    net = align_day(row, {"close": 100, "adj_close": 80})
    chk("overlap", net["close_overlap"] is True and closes_overlap(100, 100.05))
    chk("adj", abs(net["adj_high"] - 88) < 1e-9 and abs(net["adj_close"] - 80) < 1e-6)
    chk("net default", net["quant_volume"] == 800 and net["quant_value"] == 80000 and net["daytrade_ratio"] == 0.2)
    chk("inst same day", net["total_net"] == 9 and net["short_margin_ratio"] == 10)
    chk("maint empty", net["margin_maint_pct"] is None and net["margin_usage_pct"] is None)
    gross = align_day(row, {"close": 100, "adj_close": 100}, view="gross")
    chk("display gross", gross["quant_volume"] == 1000 and gross["view"] == "gross")
    bad = align_day(row, {"close": 90, "adj_close": 70})
    chk("misalign", bad["close_overlap"] is False and bad["adj_close"] is None)
    missing = align_day({"date": "2026-09-25", "code": "1101", "close": 40, "volume": 10, "value": 400})
    chk("no daytrade", missing["volume_net"] is None and missing["quant_volume"] is None)
    bad_names = [name for name, ok in checks if not ok]
    print(f"[VDF_ENG098 v0100] {len(checks) - len(bad_names)}/{len(checks)}"
          + (f" FAIL {bad_names}" if bad_names else " OK"))
    return 1 if bad_names else 0


if __name__ == "__main__":
    raise SystemExit(selftest())
