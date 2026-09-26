#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One TWSE list and one TPEX list. A code that answers decides .TW or .TWO."""
from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = HERE.parent / "output_hub" / "tw_market_v0100.json"
CODE = re.compile(r"^[1-9]\d{3}$")
TWSE = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
TPEX = "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O"


def _get(url: str, timeout: int = 12) -> list:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data if isinstance(data, list) else []


def _keep(rows: list, code_key: str, name_key: str) -> dict:
    found = {}
    for row in rows:
        code = str(row.get(code_key) or "").strip()
        if CODE.fullmatch(code):
            found[code] = str(row.get(name_key) or "").strip()
    return found


def classify(twse: dict, tpex: dict) -> dict:
    out = {}
    for code in set(twse) | set(tpex):
        on_twse, on_tpex = code in twse, code in tpex
        if on_twse and on_tpex:
            market, yahoo = "", ""
        elif on_twse:
            market, yahoo = "TWSE", code + ".TW"
        else:
            market, yahoo = "TPEX", code + ".TWO"
        out[code] = {
            "market": market,
            "yfinance": yahoo,
            "bloomberg": code + " TT",
            "local": code,
            "name": twse.get(code) or tpex.get(code) or "",
            "both": on_twse and on_tpex,
        }
    return out


def load(refresh: bool = False) -> dict:
    if CACHE.is_file() and not refresh:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    table = classify(
        _keep(_get(TWSE), "Code", "Name"),
        _keep(_get(TPEX), "SecuritiesCompanyCode", "CompanyAbbreviation"),
    )
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(table, ensure_ascii=False), encoding="utf-8")
    return table


def selftest() -> int:
    table = classify({"2330": "台積電", "6873": "泓德能源"}, {"6488": "環球晶", "6873": "重複"})
    ok = table["2330"]["yfinance"] == "2330.TW" and table["6488"]["yfinance"] == "6488.TWO"
    ok = ok and table["6873"]["yfinance"] == "" and table["6873"]["both"] is True
    ok = ok and table["2330"]["bloomberg"] == "2330 TT"
    print("  [OK]" if ok else "  [FAIL] " + str(table["6873"]))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest())
