#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF ticker class v0100. Old four-digit stock regex stays. This file only adds classification.

  py -3 VDF_TW_TickerClass_v0100.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOOK = json.loads((HERE / "VDF_TW_TickerClass_v0100.json").read_text(encoding="utf-8"))

LOCAL = {name: re.compile(pat) for name, pat in BOOK["TW_TICKER"]["by_security_type"].items()}
UNIFIED = {
    "local": re.compile(BOOK["TW_TICKER"]["unified_regex"]),
    "yahoo": re.compile(BOOK["TW_YF_TICKER"]["unified_regex"]),
    "bloomberg": re.compile(BOOK["TW_BB_TICKER"]["unified_regex"]),
}
ACTIVE_TW = re.compile(BOOK["active_tw_equity_etf"]["code_regex"])
HOLDING = re.compile(BOOK["active_tw_equity_etf"]["holdings_regex"])
ORDER = (
    "currency_tranche_etf",
    "active_bond_etf",
    "passive_bond_etf",
    "leveraged_etf",
    "inverse_etf",
    "futures_etf",
    "balanced_etf",
    "active_equity_etf",
    "passive_equity_etf",
    "stock",
)


def classify(code: str, platform: str = "local") -> str | None:
    text = str(code or "").strip()
    if platform != "local":
        return "unified" if UNIFIED[platform].fullmatch(text) else None
    for name in ORDER:
        if LOCAL[name].fullmatch(text):
            return name
    return None


def is_tw_holding(code: str) -> bool:
    return bool(HOLDING.fullmatch(str(code or "").strip()))


def is_active_tw_equity(code: str, etf_class: str | None) -> bool | None:
    """True only for domestic active equity. None when the active-list class was not supplied."""
    if not ACTIVE_TW.fullmatch(str(code or "").strip()):
        return False
    if etf_class is None or str(etf_class).strip() == "":
        return None
    return str(etf_class).strip() == BOOK["active_tw_equity_etf"]["etf_class"]


def selftest() -> int:
    fails = []
    expect = {
        "2330": "stock",
        "0050": "passive_equity_etf",
        "00646": "passive_equity_etf",
        "006203": "passive_equity_etf",
        "00981A": "active_equity_etf",
        "00402A": "active_equity_etf",
        "00982D": "active_bond_etf",
        "00710B": "passive_bond_etf",
        "00631L": "leveraged_etf",
        "00632R": "inverse_etf",
        "00635U": "futures_etf",
        "00981T": "balanced_etf",
        "00625K": "currency_tranche_etf",
        "00774C": "currency_tranche_etf",
    }
    for code, kind in expect.items():
        if classify(code) != kind or not UNIFIED["local"].fullmatch(code):
            fails.append(code)
    if classify("00981A.TW", "yahoo") != "unified" or classify("6488.TWO", "yahoo") != "unified":
        fails.append("yahoo")
    if classify("2330 TT", "bloomberg") != "unified" or classify("2330TT", "bloomberg") == "unified":
        fails.append("bloomberg")
    if is_active_tw_equity("00981A", "domestic") is not True:
        fails.append("domestic")
    if is_active_tw_equity("00402A", "foreign") is not False or is_active_tw_equity("00982D", "bfIncome") is not False:
        fails.append("not-tw")
    if is_active_tw_equity("00981A", None) is not None:
        fails.append("unknown-class")
    if not is_tw_holding("2330") or is_tw_holding("0050") or is_tw_holding("00981A"):
        fails.append("holding")
    if fails:
        print("[FAIL] " + ", ".join(fails))
        return 1
    print("[OK] ticker class v0100 kinds=%d" % len(expect))
    return 0


if __name__ == "__main__":
    sys.exit(selftest())
