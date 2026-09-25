#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG102 — one card for TWSE, TPEX, and yfinance.

Does not fetch. Price, volume, value, chips, and the two indexes stay on
the exchange. yfinance may overlap close and supply adj_close. A TWSE code
ends .TW. A TPEX code ends .TWO.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent

SUFFIX = {"TWSE": ".TW", "TPEX": ".TWO"}
LANES = {
    "tw_day": "VDF_ENG098_SameDayAlign_v0100.py",
    "tw_index": "VDF_ENG099_IndexSameDay_v0100.py",
    "identity": "VDF_ENG095_InstrumentIdentity_v0100.py",
    "intl_probe": "VDF_ENG101_SourceProbe_v0100.py",
}


def yahoo_symbol(code: str, market: str) -> str:
    market = str(market or "").strip().upper()
    if market not in SUFFIX:
        raise ValueError("market must be TWSE or TPEX")
    bare = str(code or "").strip().upper()
    for tail in (".TWO", ".TW", " TT"):
        if bare.endswith(tail):
            bare = bare[: -len(tail)].strip()
    if not bare:
        raise ValueError("empty code")
    return bare + SUFFIX[market]


def lane() -> dict:
    present = {name: (HERE / file).is_file() for name, file in LANES.items()}
    return {
        "exchange": ["TWSE", "TPEX"],
        "suffix": SUFFIX,
        "exchange_owns": ["open", "high", "low", "close", "volume", "value", "chips", "index"],
        "yfinance_owns": ["close_overlap", "adj_close", "shortName", "intl"],
        "yfinance_rejected": ["volume", "value", "chips", "tw_index"],
        "files": present,
    }


def selftest() -> int:
    checks = []

    def chk(name, ok):
        checks.append((name, bool(ok)))

    chk("twse", yahoo_symbol("2330", "TWSE") == "2330.TW")
    chk("tpex", yahoo_symbol("6488.TWO", "TPEX") == "6488.TWO")
    chk("strip", yahoo_symbol("2330.TW", "tpex") == "2330.TWO")
    card = lane()
    chk("files", all(card["files"].values()))
    chk("reject volume", "volume" in card["yfinance_rejected"])
    spec = importlib.util.spec_from_file_location("eng098", HERE / LANES["tw_day"])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    row = mod.align_day(
        {"date": "2026-09-25", "code": "2330", "close": 100, "volume": 10, "value": 1000},
        {"close": 100, "adj_close": 80, "volume": 999},
    )
    chk("yahoo volume ignored", row["volume"] == 10 and row["adj_close"] == 80)
    bad = [name for name, ok in checks if not ok]
    print(f"[VDF_ENG102 v0100] {len(checks) - len(bad)}/{len(checks)}" + (f" FAIL {bad}" if bad else " OK"))
    print(json.dumps({"via": "vdf", "lane": "twse-tpex-yfinance", "suffix": SUFFIX, "ok": not bad}, ensure_ascii=False))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(selftest())
