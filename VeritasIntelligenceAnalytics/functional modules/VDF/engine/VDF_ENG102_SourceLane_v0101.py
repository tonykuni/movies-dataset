#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG102 v0101 — live check of two names. No database write.

TWSE daily board keeps 2330. TPEX daily board keeps 6488.
yfinance is the chart close and adj_close only. Its volume is not used.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
TARGETS = (("2330", "TWSE"), ("6488", "TPEX"))
URLS = {
    "TWSE": "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL",
    "TPEX": "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes",
}


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _rows(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("data", "tables", "aaData"):
            if isinstance(payload.get(key), list):
                return payload[key]
    return []


def _code(row: dict) -> str:
    for key in ("Code", "SecuritiesCompanyCode", "Symbol", "公司代號"):
        value = str(row.get(key) or "").strip()
        if value:
            return value.split(".")[0]
    return ""


def _num(row: dict, *keys):
    for key in keys:
        raw = row.get(key)
        if raw in (None, "", "--", "---"):
            continue
        try:
            return float(str(raw).replace(",", ""))
        except ValueError:
            continue
    return None


def exchange_row(payload, code: str) -> dict | None:
    for row in _rows(payload):
        if isinstance(row, dict) and _code(row) == code:
            return {
                "close": _num(row, "ClosingPrice", "Close", "收盤價"),
                "volume": _num(row, "TradeVolume", "TradingShares", "成交股數"),
                "value": _num(row, "TradeValue", "TransactionAmount", "成交金額"),
            }
    return None


def chart_close(payload) -> dict:
    try:
        result = payload["chart"]["result"][0]
        quote = result["indicators"]["quote"][0]
        adj = result["indicators"]["adjclose"][0]["adjclose"]
        closes = quote.get("close") or []
        close = next(x for x in reversed(closes) if x is not None)
        adj_close = next(x for x in reversed(adj) if x is not None)
        return {"close": float(close), "adj_close": float(adj_close)}
    except (KeyError, IndexError, StopIteration, TypeError, ValueError):
        return {}


def live(net) -> dict:
    lane = _load(HERE / "VDF_ENG102_SourceLane_v0100.py", "lane100")
    align = _load(HERE / "VDF_ENG098_SameDayAlign_v0100.py", "align098")
    out = []
    for code, market in TARGETS:
        board = net.http_json(URLS[market])
        if board.get("state") != "OK":
            out.append({"code": code, "market": market, "state": board.get("state") or "FAIL", "note": board.get("note")})
            continue
        exch = exchange_row(board.get("data"), code)
        symbol = lane.yahoo_symbol(code, market)
        chart = net.http_json(
            f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d"
        )
        yahoo = chart_close(chart.get("data")) if chart.get("state") == "OK" else {}
        if not exch:
            out.append({"code": code, "symbol": symbol, "state": "NODATA"})
            continue
        joined = align.align_day(
            {"date": None, "code": code, "close": exch["close"], "volume": exch["volume"], "value": exch["value"]},
            {"close": yahoo.get("close"), "adj_close": yahoo.get("adj_close"), "volume": 999999},
        )
        out.append({
            "code": code,
            "symbol": symbol,
            "state": "OK",
            "exchange_close": exch["close"],
            "exchange_volume": exch["volume"],
            "yahoo_close": yahoo.get("close"),
            "adj_close": joined["adj_close"],
            "overlap": joined["close_overlap"],
            "yahoo_volume_used": False,
        })
    return {"wrote": False, "rows": out}


def selftest() -> int:
    tw = exchange_row([{"Code": "2330", "ClosingPrice": "100", "TradeVolume": "10", "TradeValue": "1000"}], "2330")
    tp = exchange_row([{"SecuritiesCompanyCode": "6488", "Close": "50", "TradingShares": "4"}], "6488")
    chart = chart_close({"chart": {"result": [{"indicators": {
        "quote": [{"close": [None, 100]}],
        "adjclose": [{"adjclose": [80]}],
    }}]}})
    ok = tw["volume"] == 10 and tp["close"] == 50 and chart["adj_close"] == 80
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    sys.exit(selftest())
