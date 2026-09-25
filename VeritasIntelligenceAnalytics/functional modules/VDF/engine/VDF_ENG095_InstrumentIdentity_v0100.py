#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG095 — display identity for a Taiwan ticker.

主動式台股 ETF 是主動式股票 ETF 的子集：代號是主動股票（A 碼），
而且持股這次抓得到。抓不到、或還沒抓，不算。

顯示名不抓全名。中文只用 TWSE/TPEX 回包裡的短名（台泥、亞泥）。
英文只用 yfinance shortName。台灣產業用交易所欄，國際產業用
yfinance 的 sector / industry。instrument 是這次 yfinance 清單的
quoteType 彙總，不另猜。

本支不自己出網。列資料由既有擷取器依 ticker 拿來。
"""
from __future__ import annotations

import re
from collections import Counter

# ===== [VIA:ACCEL-BRIDGE:v0100] =====
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
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

ACTIVE_EQUITY_ETF = re.compile(r"^00\d{2,3}A$")
LEGAL_NAME = ("股份有限公司", "有限公司")
ZH_SHORT = ("證券簡稱", "公司簡稱", "簡稱")
ZH_NAME = ("證券名稱", "名稱", "公司名稱")
TW_INDUSTRY = ("產業別", "產業名稱", "SecuritiesIndustryCode")
QUOTE_TYPE = {
    "EQUITY": "equity",
    "ETF": "etf",
    "MUTUALFUND": "fund",
    "INDEX": "index",
    "CURRENCY": "fx",
    "CRYPTOCURRENCY": "crypto",
    "FUTURE": "future",
    "OPTION": "option",
    "BOND": "bond",
}


def _clean(value) -> str:
    return str(value or "").strip()


def _bare(ticker: str) -> str:
    text = _clean(ticker).upper()
    for tail in (".TWO", ".TW", " TT"):
        if text.endswith(tail):
            text = text[: -len(tail)].strip()
    return text


def is_active_equity_etf(ticker: str) -> bool:
    return bool(ACTIVE_EQUITY_ETF.fullmatch(_bare(ticker)))


def is_active_tw_stock_etf(ticker: str, holdings_status: str | None) -> bool | None:
    """True only when this active equity ETF's holdings were fetched.

    holdings_status: FETCHED, EMPTY, FOREIGN, or None when not tried.
    """
    if not is_active_equity_etf(ticker):
        return False
    status = _clean(holdings_status).upper()
    if status == "FETCHED":
        return True
    if status in {"EMPTY", "FOREIGN"}:
        return False
    return None


def _short_zh(row: dict) -> str | None:
    for key in (*ZH_SHORT, *ZH_NAME):
        value = _clean(row.get(key))
        if value and not any(mark in value for mark in LEGAL_NAME):
            return value
    return None


def _instrument(quote_type: str) -> str | None:
    token = _clean(quote_type).upper()
    if not token:
        return None
    return QUOTE_TYPE.get(token, token.lower())


def display_identity(tw_row: dict | None, yf_row: dict | None = None) -> dict:
    """One ticker. Chinese short name from the exchange, English from shortName."""
    tw = tw_row or {}
    yf = yf_row or {}
    rejected = ""
    if _short_zh(tw) is None:
        for key in (*ZH_SHORT, *ZH_NAME):
            value = _clean(tw.get(key))
            if value:
                rejected = value
                break
    industry_tw = ""
    for key in TW_INDUSTRY:
        industry_tw = _clean(tw.get(key))
        if industry_tw:
            break
    return {
        "name_zh": _short_zh(tw),
        "name_zh_rejected": rejected or None,
        "name_en": _clean(yf.get("shortName")) or None,
        "industry_tw": industry_tw or None,
        "sector": _clean(yf.get("sector")) or None,
        "industry": _clean(yf.get("industry")) or None,
        "instrument": _instrument(yf.get("quoteType")),
    }


def rollup_instruments(yf_rows: list[dict]) -> dict:
    """Count quoteType across one yfinance list. Missing type stays out."""
    counts: Counter[str] = Counter()
    for row in yf_rows:
        name = _instrument((row or {}).get("quoteType"))
        if name:
            counts[name] += 1
    return dict(sorted(counts.items()))


def selftest() -> int:
    checks = []

    def chk(name, ok):
        checks.append((name, bool(ok)))

    cement = display_identity(
        {"公司簡稱": "台泥", "公司名稱": "台灣水泥股份有限公司", "產業別": "01"},
        {"shortName": "TCC", "longName": "Taiwan Cement Corp.", "sector": "Basic Materials",
         "industry": "Building Materials", "quoteType": "EQUITY"},
    )
    asia = display_identity({"證券名稱": "亞泥", "產業名稱": "水泥"}, {"shortName": "Asia Cement"})
    full = display_identity({"公司名稱": "台灣水泥股份有限公司"}, {"longName": "Taiwan Cement Corp."})
    chk("short zh", cement["name_zh"] == "台泥" and asia["name_zh"] == "亞泥")
    chk("reject legal", full["name_zh"] is None and full["name_zh_rejected"].endswith("股份有限公司"))
    chk("english short", cement["name_en"] == "TCC" and full["name_en"] is None)
    chk("industries", cement["industry_tw"] == "01" and cement["sector"] == "Basic Materials"
        and cement["industry"] == "Building Materials" and asia["industry_tw"] == "水泥")
    chk("instrument", cement["instrument"] == "equity")
    chk("active fetched", is_active_tw_stock_etf("00981A", "FETCHED") is True
        and is_active_equity_etf("00981A.TW"))
    chk("active empty", is_active_tw_stock_etf("00402A", "EMPTY") is False
        and is_active_equity_etf("00402A"))
    chk("not tried", is_active_tw_stock_etf("00981A", None) is None)
    chk("bond not equity etf", is_active_tw_stock_etf("00981D", "FETCHED") is False)
    chk("rollup", rollup_instruments([
        {"quoteType": "EQUITY"}, {"quoteType": "ETF"}, {"quoteType": "EQUITY"}, {},
    ]) == {"equity": 2, "etf": 1})
    bad = [name for name, ok in checks if not ok]
    print(f"[VDF_ENG095 v0100] {len(checks) - len(bad)}/{len(checks)}"
          + (f" FAIL {bad}" if bad else " OK"))
    return 1 if bad else 0


if __name__ == "__main__":
    import sys
    raise SystemExit(selftest())
