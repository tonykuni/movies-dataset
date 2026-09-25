#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Three ticker forms must share one core. Zones must agree before a field is kept.

Does not open a PDF and does not call Paddle. Those engines are named here
so the order stays in one place.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
FIELDS = (
    "report_date", "filename", "broker", "analyst", "ticker",
    "yfinance_ticker", "bloomberg_ticker", "rating", "target_price_adj",
    "upside_pct", "yfinance_target_median", "factset_target_median",
)
ORDER = ("layout", "restore", "plumber", "paddle")


def _hub():
    hits = sorted((VIA / "supportive modules" / "70_VRN_Rules").glob("SUP_MDL749_VRNFieldRuleHub_v*.py"))
    spec = importlib.util.spec_from_file_location("hub749b", hits[-1])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _core(token: str, hub) -> str:
    found = hub.ticker_platform(token) or {}
    code = str(found.get("canonical") or "")
    return code[:4] if len(code) >= 4 else ""


def confirm_codes(code: str, market: str | None) -> dict:
    hub = _hub()
    local = _core(code, hub)
    if not local:
        return {"ok": False, "why": "not a listed form"}
    yahoo = {"TWSE": local + ".TW", "TPEX": local + ".TWO"}.get(str(market or "").upper())
    bloomberg = f"{local} TT"
    cores = {"local": local, "bloomberg": _core(bloomberg, hub)}
    if yahoo:
        cores["yfinance"] = _core(yahoo, hub)
    ok = bool(yahoo) and len(set(cores.values())) == 1 and "" not in cores.values()
    return {
        "ok": ok,
        "why": "" if ok else ("market unknown" if not yahoo else "core mismatch"),
        "core": local,
        "yfinance_ticker": yahoo,
        "bloomberg_ticker": bloomberg if cores.get("bloomberg") == local else None,
    }


def upside(target_adj, price) -> float | None:
    try:
        target = float(target_adj)
        last = float(price)
    except (TypeError, ValueError):
        return None
    if last == 0:
        return None
    return (target / last - 1.0) * 100.0


def cross(info: dict, body: dict, annual: dict) -> dict:
    """info = left/right page zones, body = center, annual = statement page."""
    out = {}
    for field in FIELDS:
        seen = {}
        for zone, src in (("info", info), ("body", body), ("annual", annual)):
            value = src.get(field)
            if value not in (None, ""):
                seen[zone] = value
        vals = list(seen.values())
        if not vals:
            state = "NODATA"
        elif all(item == vals[0] for item in vals):
            state = "AGREE"
        else:
            state = "CONFLICT"
        out[field] = {"state": state, "seen": seen}
    return out


def engine_order() -> list[dict]:
    vrn = HERE
    layout = next(vrn.glob("20260804/VRN_MDL002_LayoutExtractor.py"), None)
    restore = sorted(vrn.glob("VRN_ENG085_MarkdownRestore_v*.py"))
    plumber = sorted(vrn.glob("VRN_ENG072_FirstPageText_v*.py"))
    return [
        {"id": "layout", "state": "PRESENT" if layout else "ABSENT", "file": layout.name if layout else None},
        {"id": "restore", "state": "PRESENT" if restore else "ABSENT", "file": restore[-1].name if restore else None},
        {"id": "plumber", "state": "PRESENT" if plumber else "ABSENT", "file": plumber[-1].name if plumber else None},
        {"id": "paddle", "state": "ABSENT", "file": None, "why": "no Paddle engine in this tree"},
    ]


def selftest() -> int:
    tw = confirm_codes("2330", "TWSE")
    two = confirm_codes("6488", "TPEX")
    bad = confirm_codes("2330", None)
    up = upside(100, 80)
    zones = cross(
        {"ticker": "2330", "target_price_adj": 100},
        {"ticker": "2330", "target_price_adj": 100},
        {"ticker": "2330"},
    )
    clash = cross({"rating": "Buy"}, {"rating": "Hold"}, {})
    ok = (
        tw["ok"] and tw["yfinance_ticker"] == "2330.TW" and tw["bloomberg_ticker"] == "2330 TT"
        and two["ok"] and two["yfinance_ticker"] == "6488.TWO"
        and bad["ok"] is False
        and abs(up - 25) < 1e-9
        and zones["ticker"]["state"] == "AGREE"
        and clash["rating"]["state"] == "CONFLICT"
        and [row["id"] for row in engine_order()] == list(ORDER)
    )
    print("  [OK]" if ok else f"  [FAIL] {tw} {two} {up} {zones['ticker']} {clash['rating']}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest())
