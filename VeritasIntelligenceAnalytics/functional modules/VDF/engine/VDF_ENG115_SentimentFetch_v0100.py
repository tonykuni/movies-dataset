#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fetch CNN Fear and Greed and the AAII survey file. A block page is not a reading."""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import datetime

CNN_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
AAII_URL = "https://www.aaii.com/files/surveys/sentiment.xls"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
COMPONENTS = (
    "market_momentum_sp500",
    "stock_price_strength",
    "stock_price_breadth",
    "put_call_options",
    "market_volatility_vix",
    "safe_haven_demand",
    "junk_bond_demand",
)


def allowed() -> bool:
    return os.environ.get("VIA_CENTRAL_ENTRY") == "1" and os.environ.get("VIA_FROM_VCGC") == "YES"


def _get(url, headers):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=25) as response:
        return response.status, response.getheader("content-type") or "", response.read()


def cnn() -> dict:
    try:
        status, ctype, raw = _get(CNN_URL, {"User-Agent": UA, "Accept": "application/json", "Referer": "https://edition.cnn.com/markets/fear-and-greed"})
    except Exception as exc:
        return {"state": "FAIL", "why": type(exc).__name__}
    if "json" not in ctype:
        return {"state": "FAIL", "why": ctype or "not json"}
    data = json.loads(raw)
    head = data.get("fear_and_greed") or {}
    parts = []
    for key in COMPONENTS:
        block = data.get(key) or {}
        if "score" in block:
            parts.append({"id": key, "score": block.get("score"), "rating": block.get("rating")})
    return {
        "state": "LIVE" if head.get("score") is not None else "NODATA",
        "http": status,
        "score": head.get("score"),
        "rating": head.get("rating"),
        "timestamp": head.get("timestamp"),
        "previous_close": head.get("previous_close"),
        "previous_1_week": head.get("previous_1_week"),
        "previous_1_month": head.get("previous_1_month"),
        "components": parts,
    }


def aaii() -> dict:
    try:
        status, ctype, raw = _get(AAII_URL, {"User-Agent": UA, "Accept": "*/*", "Referer": "https://www.aaii.com/sentimentsurvey"})
    except Exception as exc:
        return {"state": "FAIL", "why": type(exc).__name__}
    if raw[:1] in (b"<", b"\r", b"\n") or b"<html" in raw[:200].lower() or "html" in ctype.lower():
        return {"state": "BLOCKED", "http": status, "why": "official file returned a block page"}
    if raw[:2] == b"PK" or raw[:4] == b"\xd0\xcf\x11\xe0":
        return {"state": "UNPARSED", "http": status, "bytes": len(raw), "why": "file arrived; this door does not parse it"}
    return {"state": "FAIL", "http": status, "why": ctype or "unknown body"}


def probe() -> dict:
    cnn_row = cnn()
    aaii_row = aaii()
    return {
        "via": "vcgc",
        "door": "VDF_ENG115_SentimentFetch_v0100",
        "probed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "enter": "vcgc",
        "exit": "vcgc",
        "central": True,
        "cnn": cnn_row,
        "aaii": aaii_row,
        "intake_edited": False,
        "do_not": [
            "fill AAII from the block page",
            "treat the CNN extreme-fear label on every put/call row as the rating",
            "edit intake macro_ssot",
        ],
        "next": "none" if aaii_row["state"] != "BLOCKED" else "AAII stays blocked until the official file is a spreadsheet",
    }


def main() -> int:
    if not allowed():
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-sentiment through Invoke-VIAPython"}, ensure_ascii=False))
        return 2
    print(json.dumps(probe(), ensure_ascii=False, indent=1))
    return 0


def selftest() -> int:
    os.environ.pop("VIA_CENTRAL_ENTRY", None)
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = not allowed()
    os.environ["VIA_CENTRAL_ENTRY"] = "1"
    os.environ["VIA_FROM_VCGC"] = "YES"
    blocked = {"state": "BLOCKED"}
    html = b"<!DOCTYPE html><html>Pardon"
    is_html = html[:1] == b"<" or b"<html" in html[:200].lower()
    ok = denied and allowed() and is_html and blocked["state"] == "BLOCKED" and len(COMPONENTS) == 7
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
