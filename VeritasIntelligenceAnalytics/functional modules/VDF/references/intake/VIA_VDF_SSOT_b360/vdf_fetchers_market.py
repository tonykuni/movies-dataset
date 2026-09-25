#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:MODULE_SPEC:START]
# MODULE_NAME:       vdf_fetchers_market
# MODULE_VERSION:    2.0.0
# MODULE_ROLE:       All market-data fetchers merged into one module:
#                      - yfinance OHLC+Adj OLH+Volume+Market Cap (universal)
#                      - TWSE/TPEX official indices (^TWII / ^TWO)
#                      - TWSE/TPEX per-stock chip data (T86/MI_MARGN/TWTB4U)
#                      - TW stock unified (yfinance prices + chips merge)
# MODULE_ZONE:       D4
# DEPENDENCIES:      pandas
# OPTIONAL_DEPENDENCIES: yfinance, requests, VeritasAegisNexus, VeritasCeleritas
# ERROR_POLICY:      RETURN_SAFE_DEFAULT
# SAFE_SKIP:         True
# MERGE_UNIT_ID:     VDF-D4-FETCH-MARKET-002
# [VIA:MODULE_SPEC:END]
"""
Public entry points exposed by this module:

    fetch_yfinance_prices(spec, ctx)      # tw_etf, intl_stock, intl_etf, commodity, fx
    fetch_tw_index_official(spec, ctx)    # ^TWII, ^TWO (TWSE/TPEX only)
    fetch_tw_stock_unified(spec, ctx)     # TW stocks: yfinance prices + TWSE/TPEX chips
    fetch_tw_chips(tickers, start, end)   # standalone chip fetcher
    compute_chip_derived(df)              # derived ratios on chip-enriched DataFrame

Adj_Open / Adj_Low / Adj_High derivation:
    ratio = Adj_Close / Close
    Adj_X = X * ratio   for X in {Open, Low, High}
"""

# [VIA:ANCHOR:D4_FETCH_MARKET:START]

from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

log = logging.getLogger("VDF.market")


# =========================================================================
# SECTION 1: yfinance fetcher (OHLC + Adj OLH + Volume + Market Cap)
# =========================================================================

def _imports_yf():
    import pandas as pd
    import yfinance as yf
    return pd, yf


def _compute_adj_olh(df):
    """Adj_X = X * (Adj_Close / Close). Verified by unit test."""
    pd, _ = _imports_yf()
    if df is None or len(df) == 0:
        return df
    df = df.copy()
    for c in ("Open", "Low", "High", "Close", "Adj Close"):
        if c not in df.columns:
            df[c] = pd.NA
    ratio = df["Adj Close"] / df["Close"]
    ratio = ratio.where(df["Close"].notna() & (df["Close"] != 0))
    df["Adj_Open"] = df["Open"] * ratio
    df["Adj_Low"] = df["Low"] * ratio
    df["Adj_High"] = df["High"] * ratio
    return df


def _normalize_columns(df, ticker: str, name: str, yf_ticker: str, bbg_ticker: str):
    pd, _ = _imports_yf()
    if df is None or len(df) == 0:
        return pd.DataFrame()
    df = _compute_adj_olh(df)

    out = pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        try:
            df = df.xs(ticker, axis=1, level=1)
        except Exception:
            try:
                df.columns = [c[0] for c in df.columns]
            except Exception:
                pass

    out["Date"] = pd.to_datetime(df.index).strftime("%Y-%m-%d")
    out["Ticker"] = ticker
    out["YFinance_Ticker"] = yf_ticker or ticker
    out["Bloomberg_Ticker"] = bbg_ticker or ""
    out["Name"] = name or ""
    for src, dst in [
        ("Open", "Open"), ("Low", "Low"), ("High", "High"), ("Close", "Close"),
        ("Adj_Open", "Adj_Open"), ("Adj_Low", "Adj_Low"), ("Adj_High", "Adj_High"),
        ("Adj Close", "Adj_Close"), ("Volume", "Volume"),
    ]:
        out[dst] = df[src] if src in df.columns else pd.NA

    try:
        out["Turnover"] = (out["Close"].astype(float) * out["Volume"].astype(float))
    except Exception:
        out["Turnover"] = pd.NA
    out["Market_Cap"] = pd.NA
    return out


def _get_market_cap(yf, ticker: str) -> Optional[float]:
    try:
        t = yf.Ticker(ticker)
        fi = getattr(t, "fast_info", None)
        if fi:
            mc = None
            try:
                mc = fi.get("market_cap") if hasattr(fi, "get") else fi.market_cap
            except Exception:
                mc = None
            if mc:
                return float(mc)
        info = t.info if hasattr(t, "info") else {}
        mc = info.get("marketCap")
        return float(mc) if mc else None
    except Exception as e:
        log.debug("[YF] market cap failed for %s: %s", ticker, e)
        return None


def _existing_window(store, output_file: str, ticker: str) -> Optional[str]:
    pd, _ = _imports_yf()
    try:
        existing = store.load_existing(output_file)
        if existing is None or existing.empty:
            return None
        if "Ticker" not in existing.columns or "Date" not in existing.columns:
            return None
        sub = existing[existing["Ticker"] == ticker]
        if sub.empty:
            return None
        return str(sub["Date"].max())
    except Exception as e:
        log.debug("[YF] _existing_window failed: %s", e)
        return None


def fetch_yfinance_prices(spec, ctx):
    """Entry point: tw_etf, intl_stock, intl_etf, commodity, fx."""
    try:
        pd, yf = _imports_yf()
    except Exception as e:
        log.error("[YF] missing pandas/yfinance: %s", e)
        return None

    store = ctx.get("store")
    start = ctx["start"]
    end = ctx["end"]
    full_refresh = ctx.get("full_refresh", False)
    limit = ctx.get("limit")
    ticker_override = ctx.get("ticker_override")

    tickers = list(spec.tickers or [])
    if ticker_override:
        match = [t for t in tickers if t.get("ticker", "").upper() == ticker_override.upper()]
        tickers = match if match else [{"ticker": ticker_override, "name": ticker_override}]

    if limit:
        tickers = tickers[:limit]

    log.info("[YF] %s: fetching %d tickers (%s -> %s)", spec.id, len(tickers), start, end)

    frames: List = []
    failures: List[Dict[str, Any]] = []

    for i, t in enumerate(tickers, 1):
        ticker = t["ticker"]
        name = t.get("name", "")
        yf_t = t.get("yf_ticker", ticker)
        bbg_t = t.get("bbg_ticker", "")

        fetch_start = start
        if not full_refresh and store is not None:
            last_known = _existing_window(store, spec.output_file, ticker)
            if last_known:
                fetch_start = (datetime.strptime(last_known, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
                if fetch_start > end:
                    log.info("[YF] %s up-to-date (%s) - skip", ticker, last_known)
                    continue

        log.info("[YF] %d/%d %s [%s -> %s]", i, len(tickers), ticker, fetch_start, end)

        retries = 0
        df = None
        last_err = None
        while retries < 3:
            try:
                df = yf.download(
                    tickers=yf_t,
                    start=fetch_start,
                    end=(datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d"),
                    auto_adjust=False, actions=False, progress=False, threads=False,
                )
                if df is not None and not df.empty:
                    break
            except Exception as e:
                last_err = e
                log.warning("[YF] %s attempt %d failed: %s", ticker, retries + 1, e)
            retries += 1
            time.sleep(1.5 * retries)

        if df is None or df.empty:
            failures.append({"ticker": ticker, "reason": str(last_err) if last_err else "empty"})
            log.warning("[YF] %s: no data after retries", ticker)
            continue

        norm = _normalize_columns(df, ticker, name, yf_t, bbg_t)
        if not norm.empty:
            mc = _get_market_cap(yf, yf_t)
            if mc:
                norm["Market_Cap"] = mc
            frames.append(norm)
        time.sleep(0.15)

    if not frames:
        log.warning("[YF] %s: produced 0 rows; failures=%d", spec.id, len(failures))
        return pd.DataFrame()

    result = pd.concat(frames, ignore_index=True)
    log.info("[YF] %s: total rows=%d, failures=%d", spec.id, len(result), len(failures))
    return result


# =========================================================================
# SECTION 2: TW date helpers + HTTP (shared by tw_index and tw_chips)
# =========================================================================

_KNOWN_TW_HOLIDAYS: set = {
    # 2024
    "2024-01-01", "2024-02-08", "2024-02-09", "2024-02-12", "2024-02-13",
    "2024-02-14", "2024-02-28", "2024-04-04", "2024-04-05", "2024-05-01",
    "2024-06-10", "2024-09-17", "2024-10-10",
    # 2025
    "2025-01-01", "2025-01-27", "2025-01-28", "2025-01-29", "2025-01-30",
    "2025-01-31", "2025-02-28", "2025-04-03", "2025-04-04", "2025-05-01",
    "2025-05-30", "2025-10-06", "2025-10-10",
    # 2026
    "2026-01-01", "2026-02-16", "2026-02-17", "2026-02-18", "2026-02-19",
    "2026-02-20", "2026-02-27", "2026-04-03", "2026-04-06", "2026-05-01",
    "2026-06-19", "2026-09-25", "2026-10-09", "2026-10-12",
}


def _is_weekend(d: datetime) -> bool:
    return d.weekday() >= 5


def _is_known_holiday(d: datetime) -> bool:
    return d.strftime("%Y-%m-%d") in _KNOWN_TW_HOLIDAYS


def _date_range(start: str, end: str) -> List[datetime]:
    s = datetime.strptime(start, "%Y-%m-%d")
    e = datetime.strptime(end, "%Y-%m-%d")
    out = []
    cur = s
    while cur <= e:
        if not _is_weekend(cur) and not _is_known_holiday(cur):
            out.append(cur)
        cur += timedelta(days=1)
    return out


def _to_yyyymmdd(d: datetime) -> str:
    return d.strftime("%Y%m%d")


def _to_roc_slash(d: datetime) -> str:
    return f"{d.year - 1911}/{d.month:02d}/{d.day:02d}"


def _to_iso(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")


def _safe_num(x: Any) -> Optional[float]:
    if x is None:
        return None
    try:
        if isinstance(x, str):
            x = x.replace(",", "").replace(" ", "").strip()
            if x in ("", "-", "--", "N/A", "X"):
                return None
        return float(x)
    except Exception:
        return None


class _Http:
    """HTTP client - delegates to the bridge (new v4 vdf_supportive_bridge → v3 vdf_bridge → urllib)."""
    def __init__(self):
        # Lazy import keeps cycle safe and lets vdf_fetchers_market be imported alone
        # PRIORITY 1: New v4 bridge (vdf_supportive_bridge) — direct Aegis+Celeritas
        try:
            import vdf_supportive_bridge as _new_bridge
            # Wrap new bridge's http_get_json to match the signature (url, params=, timeout=)
            def _new_http_get_json(url: str, params=None, timeout: int = 30):
                if params:
                    from urllib.parse import urlencode
                    sep = "&" if "?" in url else "?"
                    url = f"{url}{sep}{urlencode(params)}"
                return _new_bridge.http_get_json(url, timeout=timeout)
            self._http_get_json = _new_http_get_json
            log.info("[http] using vdf_supportive_bridge (v4 · Aegis+Celeritas)")
            return
        except Exception:
            pass

        # PRIORITY 2: v3 bridge (vdf_bridge)
        try:
            from vdf_bridge import http_get_json, get_bridge
            self._http_get_json = http_get_json
            self._bridge = get_bridge()
            caps = self._bridge.summary()["capabilities"]
            if caps["cached_fetch"]:
                log.info("[http] using VeritasCeleritas vdf_fetch_json (cached/retried)")
            elif caps["resilient_http"]:
                log.info("[http] using VeritasAegisNexus ResilientHTTPClient")
            else:
                log.info("[http] using stdlib fallback (requests/urllib)")
            return
        except Exception as e:
            log.warning("[http] bridge unavailable: %s - using bare requests", e)

        # PRIORITY 3: requests session
        try:
            import requests
            self._session = requests.Session()
            self._session.headers.update({
                "User-Agent": "Mozilla/5.0 (VDF/4.0)",
                "Accept": "application/json,text/html,*/*",
            })
            self._http_get_json = self._fallback_get_json
        except Exception:
            self._http_get_json = self._urllib_get_json

    def _fallback_get_json(self, url: str, params=None, timeout: int = 30):
        try:
            r = self._session.get(url, params=params, timeout=timeout)
            if r.status_code != 200:
                return None
            try:
                return r.json()
            except Exception:
                return None
        except Exception as e:
            log.debug("[http] requests failed: %s", e)
            return None

    def _urllib_get_json(self, url: str, params=None, timeout: int = 30):
        import json as _json
        from urllib import request as _ur, parse as _up
        try:
            qs = ("?" + _up.urlencode(params)) if params else ""
            req = _ur.Request(url + qs, headers={"User-Agent": "VDF/2.0"})
            with _ur.urlopen(req, timeout=timeout) as resp:
                return _json.loads(resp.read().decode("utf-8", errors="replace"))
        except Exception:
            return None

    def get_json(self, url: str, params: Optional[dict] = None, timeout: int = 30):
        return self._http_get_json(url, params=params, timeout=timeout)


# =========================================================================
# SECTION 3: TWSE/TPEX index endpoints + parsers
# =========================================================================

_TAIEX_FMTQIK = "https://www.twse.com.tw/exchangeReport/FMTQIK"
_TAIEX_INST = "https://www.twse.com.tw/fund/BFI82U"
_TAIEX_INST3 = "https://www.twse.com.tw/fund/MI_INDEX3"
_TAIEX_MARGN = "https://www.twse.com.tw/exchangeReport/MI_MARGN"
_TAIEX_DT = "https://www.twse.com.tw/exchangeReport/TWTB4U"

_TPEX_PRICE = "https://www.tpex.org.tw/web/stock/aftertrading/daily_market_statistics/dmsRpt.php"
_TPEX_INST = "https://www.tpex.org.tw/web/stock/3insti/daily_trade/3itrade_hedge_result.php"
_TPEX_MARGN = "https://www.tpex.org.tw/web/stock/margin_trading/margin_balance/margin_bal_result.php"
_TPEX_DT = "https://www.tpex.org.tw/web/stock/trading/intraday_trading_stat/intraday_trading_stat_result.php"


def _fetch_taiex_month(http: _Http, year: int, month: int) -> dict:
    yyyymm = f"{year:04d}{month:02d}01"
    resp = http.get_json(_TAIEX_FMTQIK, params={"response": "json", "date": yyyymm})
    return resp or {}


def _parse_taiex_price_row(month_data: dict, d: datetime) -> Dict[str, Any]:
    out = {"Open": None, "Low": None, "High": None, "Close": None, "Volume": None, "Turnover": None}
    if not month_data or "data" not in month_data:
        return out
    roc = _to_roc_slash(d)
    for row in month_data.get("data", []):
        if not row or len(row) < 5:
            continue
        rd = str(row[0]).strip()
        if rd == roc or rd == f"{d.year - 1911}/{d.month}/{d.day}":
            out["Volume"] = _safe_num(row[1])
            out["Turnover"] = _safe_num(row[2])
            out["Close"] = _safe_num(row[4])
            out["Open"] = out["Close"]
            out["Low"] = out["Close"]
            out["High"] = out["Close"]
            return out
    return out


def _fetch_taiex_inst_day(http: _Http, d: datetime) -> Dict[str, Any]:
    """TAIEX 整體三大法人 - TWSE MI_INDEX3 (BUG-2 fix: 7-column structure, gc index fi=1 it=2 dt=5 total=6).

    MI_INDEX3 endpoint returns the modern 7-column layout:
       [label, fi_net, it_net, fi_self_net, dealer_self_net, dealer_proprietary_net, total_net]
    BUG-2: previously parsing was label-based (fragile); now uses direct column indices.
    """
    out = {"FI_Net": None, "IT_Net": None, "Dealer_Net": None, "Total_Net": None}
    # Try MI_INDEX3 (modern endpoint) first
    resp = http.get_json(_TAIEX_INST3, params={"response": "json", "date": _to_yyyymmdd(d)})
    if resp and "data" in resp and resp["data"]:
        # BUG-2 fix: direct column indexing on the buy-sell-net aggregate row
        for r in resp["data"]:
            if not r or len(r) < 7:
                continue
            label = str(r[0])
            # Look for the "買賣超" aggregate row
            if "買賣超" in label or "差額" in label:
                try:
                    out["FI_Net"]     = _safe_num(r[1])  # gc=1 外資
                    out["IT_Net"]     = _safe_num(r[2])  # gc=2 投信
                    out["Dealer_Net"] = _safe_num(r[5])  # gc=5 自營商總計
                    out["Total_Net"]  = _safe_num(r[6])  # gc=6 合計
                    if any(v is not None for v in (out["FI_Net"], out["IT_Net"], out["Dealer_Net"])):
                        return out
                except Exception:
                    continue

    # Fallback to legacy BFI82U endpoint (label-based parsing)
    resp = http.get_json(_TAIEX_INST, params={"response": "json", "dayDate": _to_yyyymmdd(d), "type": "day"})
    if not resp or "data" not in resp:
        return out
    f = t = de = 0.0
    found = False
    for r in resp.get("data", []):
        if not r or len(r) < 4:
            continue
        label = str(r[0])
        net_val = _safe_num(r[3]) or 0.0
        if "外資" in label and "外資自營" not in label:
            f += net_val; found = True
        elif "投信" in label:
            t += net_val; found = True
        elif "自營商" in label:
            de += net_val; found = True
    if found:
        out["FI_Net"] = f; out["IT_Net"] = t; out["Dealer_Net"] = de; out["Total_Net"] = f + t + de
    return out


def _fetch_taiex_margin_day(http: _Http, d: datetime) -> Dict[str, Any]:
    out = {"Margin_Buy": None, "Margin_Sell": None, "Margin_Balance": None,
           "Short_Buy": None, "Short_Sell": None, "Short_Balance": None}
    resp = http.get_json(_TAIEX_MARGN, params={"response": "json", "date": _to_yyyymmdd(d), "selectType": "MS"})
    if not resp or "data" not in resp:
        return out
    for r in resp.get("data", []):
        if not r:
            continue
        label = str(r[0])
        if "融資" in label and "總計" in label or "融資(交易單位)" in label or "融資餘額" in label:
            try:
                if len(r) >= 6:
                    out["Margin_Buy"] = _safe_num(r[1])
                    out["Margin_Sell"] = _safe_num(r[2])
                    out["Margin_Balance"] = _safe_num(r[5])
                if len(r) >= 12:
                    out["Short_Buy"] = _safe_num(r[7])
                    out["Short_Sell"] = _safe_num(r[8])
                    out["Short_Balance"] = _safe_num(r[11])
                break
            except Exception:
                pass
    return out


def _fetch_taiex_daytrade_day(http: _Http, d: datetime) -> Dict[str, Any]:
    """TAIEX 整體當沖 - TWSE TWTB4U with selectType=MS (BUG-3 fix: was missing selectType)."""
    out = {"DayTrade_Volume": None, "DayTrade_Amount": None}
    resp = http.get_json(_TAIEX_DT, params={
        "response": "json",
        "date": _to_yyyymmdd(d),
        "selectType": "MS",   # BUG-3 fix: MS = market summary, was missing
    })
    if not resp or "data" not in resp:
        return out

    # BUG-3 fix: data structure has wrapper rows. Search for the MS aggregate row by
    # looking for the label that starts with "當日沖銷交易" or has only 2-3 numeric cols
    vol = amt = 0.0
    found = False
    for r in resp.get("data", []):
        if not r or len(r) < 3:
            continue
        label = str(r[0])
        # Skip non-aggregate rows; market summary row has the date string then totals
        if "當日沖銷" in label or "合計" in label or "/" in label:
            v = _safe_num(r[1]); a = _safe_num(r[2])
            if v and a:
                vol = v; amt = a; found = True
                break
    # Fallback to sum-all approach if specific row not found
    if not found:
        for r in resp.get("data", []):
            if not r or len(r) < 3:
                continue
            v = _safe_num(r[1]); a = _safe_num(r[2])
            if v: vol += v
            if a: amt += a

    out["DayTrade_Volume"] = vol if vol > 0 else None
    out["DayTrade_Amount"] = amt if amt > 0 else None
    return out


def _fetch_tpex_price_day(http: _Http, d: datetime) -> Dict[str, Any]:
    out = {"Open": None, "Low": None, "High": None, "Close": None, "Volume": None, "Turnover": None}
    resp = http.get_json(_TPEX_PRICE, params={"l": "zh-tw", "d": _to_roc_slash(d), "se": "EW"})
    if not resp or "aaData" not in resp:
        return out
    rows = resp.get("aaData") or []
    if not rows:
        return out
    r = rows[-1]
    try:
        if len(r) >= 5:
            out["Volume"] = _safe_num(r[1])
            out["Turnover"] = _safe_num(r[3])
            out["Close"] = _safe_num(r[4]) if len(r) > 4 else None
    except Exception:
        pass
    return out


def _fetch_tpex_inst_day(http: _Http, d: datetime) -> Dict[str, Any]:
    out = {"FI_Net": None, "IT_Net": None, "Dealer_Net": None, "Total_Net": None}
    resp = http.get_json(_TPEX_INST, params={"l": "zh-tw", "t": "D", "d": _to_iso(d), "se": "EW"})
    if not resp:
        return out
    rows = resp.get("aaData") or resp.get("data") or []
    f = t = de = 0.0
    found = False
    for r in rows:
        if not r or len(r) < 4:
            continue
        label = str(r[0])
        net_val = _safe_num(r[3]) or 0.0
        if "外資" in label and "外資自營" not in label:
            f += net_val; found = True
        elif "投信" in label:
            t += net_val; found = True
        elif "自營商" in label:
            de += net_val; found = True
    if found:
        out["FI_Net"] = f; out["IT_Net"] = t; out["Dealer_Net"] = de; out["Total_Net"] = f + t + de
    return out


def _fetch_tpex_margin_day(http: _Http, d: datetime) -> Dict[str, Any]:
    out = {"Margin_Buy": None, "Margin_Sell": None, "Margin_Balance": None,
           "Short_Buy": None, "Short_Sell": None, "Short_Balance": None}
    resp = http.get_json(_TPEX_MARGN, params={"l": "zh-tw", "d": _to_roc_slash(d), "se": "EW"})
    if not resp:
        return out
    rows = resp.get("aaData") or resp.get("data") or []
    if not rows:
        return out
    r = rows[-1]
    try:
        out["Margin_Balance"] = _safe_num(r[6]) if len(r) > 6 else None
        out["Short_Balance"] = _safe_num(r[12]) if len(r) > 12 else None
    except Exception:
        pass
    return out


def _fetch_tpex_daytrade_day(http: _Http, d: datetime) -> Dict[str, Any]:
    out = {"DayTrade_Volume": None, "DayTrade_Amount": None}
    resp = http.get_json(_TPEX_DT, params={"l": "zh-tw", "d": _to_roc_slash(d), "se": "EW"})
    if not resp:
        return out
    rows = resp.get("aaData") or resp.get("data") or []
    vol = amt = 0.0
    for r in rows:
        if not r or len(r) < 3:
            continue
        v = _safe_num(r[1]); a = _safe_num(r[2])
        if v: vol += v
        if a: amt += a
    out["DayTrade_Volume"] = vol if vol > 0 else None
    out["DayTrade_Amount"] = amt if amt > 0 else None
    return out


def _compute_derived_index(df):
    import pandas as pd
    if df is None or len(df) == 0:
        return df
    df = df.copy()
    if "Short_Balance" in df.columns and "Margin_Balance" in df.columns:
        try:
            df["Short_Margin_Ratio_Pct"] = (df["Short_Balance"].astype(float) /
                                            df["Margin_Balance"].astype(float).replace(0, pd.NA) * 100).round(2)
        except Exception:
            df["Short_Margin_Ratio_Pct"] = pd.NA
    if "DayTrade_Amount" in df.columns and "Turnover" in df.columns:
        try:
            df["DayTrade_Ratio_Pct"] = (df["DayTrade_Amount"].astype(float) /
                                        df["Turnover"].astype(float).replace(0, pd.NA) * 100).round(2)
        except Exception:
            df["DayTrade_Ratio_Pct"] = pd.NA
    if "Close" in df.columns and "Ticker" in df.columns and "Date" in df.columns:
        try:
            df = df.sort_values(["Ticker", "Date"]).reset_index(drop=True)
            for t in df["Ticker"].unique():
                mask = df["Ticker"] == t
                avg = df.loc[mask, "Close"].astype(float).rolling(window=60, min_periods=20).mean()
                df.loc[mask, "Margin_Maintenance_Pct"] = ((df.loc[mask, "Close"].astype(float) /
                                                          avg.replace(0, pd.NA)) * 166).round(2)
        except Exception:
            df["Margin_Maintenance_Pct"] = pd.NA
    return df


def fetch_tw_index_official(spec, ctx):
    """Entry point: ^TWII + ^TWO via TWSE/TPEX only (NOT yfinance)."""
    try:
        import pandas as pd
    except Exception:
        log.error("[twidx] pandas missing")
        return None

    http = _Http()
    start = ctx["start"]
    end = ctx["end"]
    store = ctx.get("store")
    full_refresh = ctx.get("full_refresh", False)

    if not full_refresh and store is not None:
        existing = store.load_existing(spec.output_file)
        if existing is not None and not existing.empty and "Date" in existing.columns:
            try:
                last = str(existing["Date"].max())
                new_start = (datetime.strptime(last, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
                if new_start > start:
                    log.info("[twidx] incremental: %s -> %s (existing last=%s)", new_start, end, last)
                    start = new_start
            except Exception:
                pass

    if start > end:
        log.info("[twidx] up-to-date")
        return pd.DataFrame()

    dates = _date_range(start, end)
    log.info("[twidx] business days: %d", len(dates))

    taiex_month_cache: Dict[str, dict] = {}
    rows: List[Dict[str, Any]] = []

    for i, d in enumerate(dates, 1):
        if i % 20 == 0 or i == 1:
            log.info("[twidx] %d/%d %s", i, len(dates), _to_iso(d))

        # TAIEX
        month_key = d.strftime("%Y%m")
        if month_key not in taiex_month_cache:
            taiex_month_cache[month_key] = _fetch_taiex_month(http, d.year, d.month)
            time.sleep(0.3)

        rec = {"Date": _to_iso(d), "Ticker": "^TWII", "YFinance_Ticker": "^TWII",
               "Bloomberg_Ticker": "TWSE Index", "Name": "TAIEX"}
        rec.update(_parse_taiex_price_row(taiex_month_cache[month_key], d))
        rec.update(_fetch_taiex_inst_day(http, d));    time.sleep(0.2)
        rec.update(_fetch_taiex_margin_day(http, d));  time.sleep(0.2)
        rec.update(_fetch_taiex_daytrade_day(http, d)); time.sleep(0.2)
        rows.append(rec)

        # TPEX
        rec2 = {"Date": _to_iso(d), "Ticker": "^TWO", "YFinance_Ticker": "^TWO",
                "Bloomberg_Ticker": "TPEX Index", "Name": "TPEX Index"}
        rec2.update(_fetch_tpex_price_day(http, d));    time.sleep(0.2)
        rec2.update(_fetch_tpex_inst_day(http, d));     time.sleep(0.2)
        rec2.update(_fetch_tpex_margin_day(http, d));   time.sleep(0.2)
        rec2.update(_fetch_tpex_daytrade_day(http, d)); time.sleep(0.2)
        rows.append(rec2)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    for src, dst in [("Open", "Adj_Open"), ("Low", "Adj_Low"),
                     ("High", "Adj_High"), ("Close", "Adj_Close")]:
        if src in df.columns:
            df[dst] = df[src]
    df = _compute_derived_index(df)
    log.info("[twidx] produced %d rows", len(df))
    return df


# =========================================================================
# SECTION 4: TWSE/TPEX per-stock chip data (T86 / Margin / DayTrade)
# =========================================================================

_TWSE_T86 = "https://www.twse.com.tw/fund/T86"
_TWSE_MARGN_STOCK = "https://www.twse.com.tw/exchangeReport/MI_MARGN"
_TWSE_DT_STOCK = "https://www.twse.com.tw/exchangeReport/TWTB4U"
_TPEX_3INST_STOCK = "https://www.tpex.org.tw/web/stock/3insti/daily_trade/3itrade_hedge_result.php"
_TPEX_MARGN_STOCK = "https://www.tpex.org.tw/web/stock/margin_trading/margin_balance/margin_bal_result.php"
_TPEX_DT_STOCK = "https://www.tpex.org.tw/web/stock/trading/intraday_trading_stat/intraday_trading_stat_result.php"


def _ticker_base(t: str) -> str:
    return t.split(".")[0].strip().upper()


def _ticker_market(t: str) -> str:
    tu = t.upper()
    if tu.endswith(".TW"):
        return "TWSE"
    if tu.endswith(".TWO"):
        return "TPEX"
    return ""


def _partition_universe(tickers: List[str]) -> Tuple[Set[str], Set[str]]:
    twse, tpex = set(), set()
    for t in tickers:
        m = _ticker_market(t)
        b = _ticker_base(t)
        if m == "TWSE":
            twse.add(b)
        elif m == "TPEX":
            tpex.add(b)
        else:
            twse.add(b); tpex.add(b)
    return twse, tpex


def _parse_twse_t86(resp: dict, wanted: Set[str]) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    if not resp or "data" not in resp:
        return out
    fields = [str(f).strip() for f in (resp.get("fields") or [])]
    rows = resp.get("data") or []

    def find_idx(*needles: str) -> int:
        for i, f in enumerate(fields):
            for n in needles:
                if n in f:
                    return i
        return -1

    code_i = find_idx("證券代號", "代號")
    fi_i = find_idx("外陸資買賣超股數", "外資及陸資買賣超", "外資買賣超")
    it_i = find_idx("投信買賣超")
    de_i = find_idx("自營商買賣超")
    tot_i = find_idx("三大法人買賣超")

    if code_i < 0:
        code_i = 0

    for r in rows:
        if not r or len(r) < 3:
            continue
        try:
            code = str(r[code_i]).strip().strip('"').strip("=").strip('"')
            if code not in wanted:
                continue
            fi = _safe_num(r[fi_i]) if 0 <= fi_i < len(r) else None
            it = _safe_num(r[it_i]) if 0 <= it_i < len(r) else None
            de = _safe_num(r[de_i]) if 0 <= de_i < len(r) else None
            tot = _safe_num(r[tot_i]) if 0 <= tot_i < len(r) else None
            if tot is None and any(x is not None for x in (fi, it, de)):
                tot = (fi or 0) + (it or 0) + (de or 0)
            out[code] = {"FI_Net": fi, "IT_Net": it, "Dealer_Net": de, "Total_Net": tot}
        except Exception:
            continue
    return out


def _parse_twse_margin(resp: dict, wanted: Set[str]) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    if not resp:
        return out
    fields = [str(f).strip() for f in (resp.get("fields") or [])]
    rows = (resp.get("data") or [])
    if not rows and "tables" in resp:
        for t in resp.get("tables", []):
            if "data" in t and t["data"]:
                rows = t["data"]
                fields = [str(f).strip() for f in (t.get("fields") or fields)]
                break

    def find_idx(*needles: str) -> int:
        for i, f in enumerate(fields):
            for n in needles:
                if n in f:
                    return i
        return -1

    code_i = find_idx("股票代號", "證券代號", "代號")
    mb_i = find_idx("融資買進", "融資-買進")
    ms_i = find_idx("融資賣出", "融資-賣出")
    mbal_i = find_idx("融資-今日餘額", "融資今日餘額", "今日餘額")
    sb_i = find_idx("融券買進", "融券-買進")
    ss_i = find_idx("融券賣出", "融券-賣出")
    sbal_i = find_idx("融券-今日餘額", "融券今日餘額")

    if code_i < 0:
        code_i = 0

    for r in rows:
        if not r or len(r) < 4:
            continue
        try:
            code = str(r[code_i]).strip().strip('"').strip("=")
            if code not in wanted:
                continue
            out[code] = {
                "Margin_Buy": _safe_num(r[mb_i]) if 0 <= mb_i < len(r) else None,
                "Margin_Sell": _safe_num(r[ms_i]) if 0 <= ms_i < len(r) else None,
                "Margin_Balance": _safe_num(r[mbal_i]) if 0 <= mbal_i < len(r) else None,
                "Short_Buy": _safe_num(r[sb_i]) if 0 <= sb_i < len(r) else None,
                "Short_Sell": _safe_num(r[ss_i]) if 0 <= ss_i < len(r) else None,
                "Short_Balance": _safe_num(r[sbal_i]) if 0 <= sbal_i < len(r) else None,
            }
        except Exception:
            continue
    return out


def _parse_twse_daytrade(resp: dict, wanted: Set[str]) -> Dict[str, Dict[str, float]]:
    """TWSE TWTB4U per-stock daytrade parser.

    BUG-1 fix: TWTB4U response sometimes wraps data in a 'tables' array (multi-table
    response). When that happens, the top-level 'fields' / 'data' may be the daily
    aggregate (wrapper), NOT the per-stock detail. We now check tables[] first and
    pick the table whose fields contain the per-stock day-trade columns.
    """
    out: Dict[str, Dict[str, float]] = {}
    if not resp:
        return out

    # BUG-1 fix: prefer tables[] containing per-stock columns
    candidate_tables = []
    if "tables" in resp and isinstance(resp["tables"], list) and resp["tables"]:
        candidate_tables.extend(resp["tables"])
    # Always also consider the top-level data
    candidate_tables.append({"fields": resp.get("fields", []), "data": resp.get("data", [])})

    def has_per_stock_cols(fields_list):
        joined = " ".join(str(f) for f in fields_list)
        return ("證券代號" in joined or "股票代號" in joined) and \
               ("當日沖銷" in joined or "當沖" in joined)

    chosen = None
    for tbl in candidate_tables:
        if not isinstance(tbl, dict):
            continue
        fields = tbl.get("fields") or []
        data = tbl.get("data") or []
        if has_per_stock_cols(fields) and data:
            chosen = tbl
            break

    if chosen is None:
        return out

    fields = [str(f).strip() for f in (chosen.get("fields") or [])]
    rows = chosen.get("data") or []

    def find_idx(*needles: str) -> int:
        for i, f in enumerate(fields):
            for n in needles:
                if n in f:
                    return i
        return -1

    code_i     = find_idx("證券代號", "股票代號", "代號")
    buy_vol_i  = find_idx("當日沖銷交易買進股數", "當沖買進股數")
    sell_vol_i = find_idx("當日沖銷交易賣出股數", "當沖賣出股數")
    vol_i      = find_idx("當日沖銷交易股數", "當沖股數", "當沖交易股數")
    amt_i      = find_idx("當日沖銷交易買進成交金額", "當沖成交金額", "當沖金額")

    if code_i < 0: code_i = 0

    for r in rows:
        if not r or len(r) <= code_i:
            continue
        try:
            code = str(r[code_i]).strip().strip('"').strip("=")
            if code not in wanted:
                continue
            row_out = {"DayTrade_Buy_Vol": None, "DayTrade_Sell_Vol": None,
                       "DayTrade_Volume": None, "DayTrade_Amount": None}
            if 0 <= buy_vol_i  < len(r): row_out["DayTrade_Buy_Vol"]  = _safe_num(r[buy_vol_i])
            if 0 <= sell_vol_i < len(r): row_out["DayTrade_Sell_Vol"] = _safe_num(r[sell_vol_i])
            if 0 <= vol_i      < len(r): row_out["DayTrade_Volume"]   = _safe_num(r[vol_i])
            if 0 <= amt_i      < len(r): row_out["DayTrade_Amount"]   = _safe_num(r[amt_i])
            # Derive vol from buy+sell if not present
            if row_out["DayTrade_Volume"] is None:
                bv = row_out["DayTrade_Buy_Vol"]; sv = row_out["DayTrade_Sell_Vol"]
                if bv is not None and sv is not None:
                    row_out["DayTrade_Volume"] = bv + sv
            out[code] = row_out
        except Exception:
            continue
    return out


def _parse_tpex_3inst(resp: dict, wanted: Set[str]) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    if not resp:
        return out
    rows = resp.get("aaData") or resp.get("data") or []
    for r in rows:
        if not r or len(r) < 5:
            continue
        try:
            code = str(r[0]).strip().strip('"').strip("=")
            if code not in wanted:
                continue
            def _g(i): return _safe_num(r[i]) if 0 <= i < len(r) else None
            fi = _g(4); it = _g(10); de = _g(22); tot = _g(23)
            if tot is None and any(x is not None for x in (fi, it, de)):
                tot = (fi or 0) + (it or 0) + (de or 0)
            out[code] = {"FI_Net": fi, "IT_Net": it, "Dealer_Net": de, "Total_Net": tot}
        except Exception:
            continue
    return out


def _parse_tpex_margin(resp: dict, wanted: Set[str]) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    if not resp:
        return out
    rows = resp.get("aaData") or resp.get("data") or []
    for r in rows:
        if not r or len(r) < 8:
            continue
        try:
            code = str(r[0]).strip().strip('"').strip("=")
            if code not in wanted:
                continue
            out[code] = {
                "Margin_Buy": _safe_num(r[2]) if len(r) > 2 else None,
                "Margin_Sell": _safe_num(r[3]) if len(r) > 3 else None,
                "Margin_Balance": _safe_num(r[6]) if len(r) > 6 else None,
                "Short_Buy": _safe_num(r[8]) if len(r) > 8 else None,
                "Short_Sell": _safe_num(r[9]) if len(r) > 9 else None,
                "Short_Balance": _safe_num(r[12]) if len(r) > 12 else None,
            }
        except Exception:
            continue
    return out


def _parse_tpex_daytrade(resp: dict, wanted: Set[str]) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    if not resp:
        return out
    rows = resp.get("aaData") or resp.get("data") or []
    for r in rows:
        if not r or len(r) < 4:
            continue
        try:
            code = str(r[0]).strip().strip('"').strip("=")
            if code not in wanted:
                continue
            out[code] = {"DayTrade_Volume": _safe_num(r[2]) if len(r) > 2 else None,
                         "DayTrade_Amount": _safe_num(r[3]) if len(r) > 3 else None}
        except Exception:
            continue
    return out


def _fetch_day_chips(http: _Http, d: datetime,
                    twse_wanted: Set[str], tpex_wanted: Set[str]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    date_iso = _to_iso(d)
    yyyymmdd = _to_yyyymmdd(d)
    roc = _to_roc_slash(d)

    twse_t86 = http.get_json(_TWSE_T86, params={"response": "json", "date": yyyymmdd, "selectType": "ALL"}) if twse_wanted else None
    time.sleep(0.3)
    twse_mg = http.get_json(_TWSE_MARGN_STOCK, params={"response": "json", "date": yyyymmdd, "selectType": "ALL"}) if twse_wanted else None
    time.sleep(0.3)
    twse_dt = http.get_json(_TWSE_DT_STOCK, params={"response": "json", "date": yyyymmdd, "selectType": "Day"}) if twse_wanted else None
    time.sleep(0.3)

    if twse_wanted:
        t86_map = _parse_twse_t86(twse_t86 or {}, twse_wanted)
        mg_map = _parse_twse_margin(twse_mg or {}, twse_wanted)
        dt_map = _parse_twse_daytrade(twse_dt or {}, twse_wanted)
        for code in set(t86_map) | set(mg_map) | set(dt_map):
            row = {"Date": date_iso, "Ticker": f"{code}.TW"}
            row.update(t86_map.get(code, {}))
            row.update(mg_map.get(code, {}))
            row.update(dt_map.get(code, {}))
            rows.append(row)

    tpex_3i = http.get_json(_TPEX_3INST_STOCK, params={"l": "zh-tw", "t": "D", "d": date_iso, "se": "EW"}) if tpex_wanted else None
    time.sleep(0.4)
    tpex_mg = http.get_json(_TPEX_MARGN_STOCK, params={"l": "zh-tw", "d": roc, "se": "EW"}) if tpex_wanted else None
    time.sleep(0.4)
    tpex_dt = http.get_json(_TPEX_DT_STOCK, params={"l": "zh-tw", "d": roc, "se": "EW"}) if tpex_wanted else None
    time.sleep(0.4)

    if tpex_wanted:
        i3_map = _parse_tpex_3inst(tpex_3i or {}, tpex_wanted)
        mg_map = _parse_tpex_margin(tpex_mg or {}, tpex_wanted)
        dt_map = _parse_tpex_daytrade(tpex_dt or {}, tpex_wanted)
        for code in set(i3_map) | set(mg_map) | set(dt_map):
            row = {"Date": date_iso, "Ticker": f"{code}.TWO"}
            row.update(i3_map.get(code, {}))
            row.update(mg_map.get(code, {}))
            row.update(dt_map.get(code, {}))
            rows.append(row)

    return rows


def fetch_tw_chips(tickers: List[str], start: str, end: str, progress_every: int = 10):
    """Public: standalone per-stock chip fetcher."""
    try:
        import pandas as pd
    except Exception:
        log.error("[twchip] pandas missing")
        return None

    if not tickers:
        return pd.DataFrame()

    twse_wanted, tpex_wanted = _partition_universe(tickers)
    log.info("[twchip] universe split: TWSE=%d TPEX=%d", len(twse_wanted), len(tpex_wanted))

    dates = _date_range(start, end)
    if not dates:
        log.info("[twchip] no business days in range")
        return pd.DataFrame()
    log.info("[twchip] %d business days to fetch", len(dates))

    http = _Http()
    all_rows: List[Dict[str, Any]] = []
    for i, d in enumerate(dates, 1):
        if i % progress_every == 0 or i == 1:
            log.info("[twchip] %d/%d %s", i, len(dates), _to_iso(d))
        try:
            all_rows.extend(_fetch_day_chips(http, d, twse_wanted, tpex_wanted))
        except Exception as e:
            log.warning("[twchip] %s failed: %s", _to_iso(d), e)
            continue

    if not all_rows:
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)
    log.info("[twchip] produced %d chip rows", len(df))
    return df


def compute_chip_derived(df):
    """Add Short_Margin_Ratio_Pct, DayTrade_Ratio_Pct, Margin_Maintenance_Pct."""
    import pandas as pd
    if df is None or df.empty:
        return df
    df = df.copy()

    if "Short_Balance" in df.columns and "Margin_Balance" in df.columns:
        try:
            mb = pd.to_numeric(df["Margin_Balance"], errors="coerce")
            sb = pd.to_numeric(df["Short_Balance"], errors="coerce")
            df["Short_Margin_Ratio_Pct"] = (sb / mb.replace(0, pd.NA) * 100).round(2)
        except Exception:
            df["Short_Margin_Ratio_Pct"] = pd.NA

    if "DayTrade_Amount" in df.columns and "Turnover" in df.columns:
        try:
            ta = pd.to_numeric(df["Turnover"], errors="coerce")
            da = pd.to_numeric(df["DayTrade_Amount"], errors="coerce")
            df["DayTrade_Ratio_Pct"] = (da / ta.replace(0, pd.NA) * 100).round(2)
        except Exception:
            df["DayTrade_Ratio_Pct"] = pd.NA

    if all(c in df.columns for c in ("Close", "Ticker", "Date")):
        try:
            df = df.sort_values(["Ticker", "Date"]).reset_index(drop=True)
            for t in df["Ticker"].unique():
                mask = df["Ticker"] == t
                close = pd.to_numeric(df.loc[mask, "Close"], errors="coerce")
                avg = close.rolling(window=60, min_periods=20).mean()
                df.loc[mask, "Margin_Maintenance_Pct"] = ((close / avg.replace(0, pd.NA)) * 166).round(2)
        except Exception:
            df["Margin_Maintenance_Pct"] = pd.NA

    return df


# =========================================================================
# SECTION 5: TW stock unified (yfinance prices + chips merge)
# =========================================================================

_DEFAULT_TW_UNIVERSE = [
    {"ticker": "2330.TW", "name": "台積電"},
    {"ticker": "2317.TW", "name": "鴻海"},
    {"ticker": "2454.TW", "name": "聯發科"},
    {"ticker": "2308.TW", "name": "台達電"},
    {"ticker": "2891.TW", "name": "中信金"},
    {"ticker": "2412.TW", "name": "中華電"},
    {"ticker": "2382.TW", "name": "廣達"},
    {"ticker": "1303.TW", "name": "南亞"},
    {"ticker": "1301.TW", "name": "台塑"},
    {"ticker": "2002.TW", "name": "中鋼"},
    {"ticker": "2881.TW", "name": "富邦金"},
    {"ticker": "2882.TW", "name": "國泰金"},
    {"ticker": "2884.TW", "name": "玉山金"},
    {"ticker": "2885.TW", "name": "元大金"},
    {"ticker": "2886.TW", "name": "兆豐金"},
    {"ticker": "2890.TW", "name": "永豐金"},
    {"ticker": "3008.TW", "name": "大立光"},
    {"ticker": "3711.TW", "name": "日月光投控"},
    {"ticker": "2303.TW", "name": "聯電"},
    {"ticker": "2357.TW", "name": "華碩"},
    {"ticker": "2376.TW", "name": "技嘉"},
    {"ticker": "2379.TW", "name": "瑞昱"},
    {"ticker": "2207.TW", "name": "和泰車"},
    {"ticker": "2912.TW", "name": "統一超"},
    {"ticker": "5871.TW", "name": "中租-KY"},
    {"ticker": "5880.TW", "name": "合庫金"},
    {"ticker": "6505.TW", "name": "台塑化"},
    {"ticker": "2880.TW", "name": "華南金"},
    {"ticker": "2887.TW", "name": "台新金"},
    {"ticker": "2892.TW", "name": "第一金"},
]


def _load_universe(universe_source: Optional[str], limit: Optional[int]) -> List[Dict[str, str]]:
    candidates = []
    if universe_source:
        candidates.append(Path(universe_source))
        candidates.append(Path(__file__).resolve().parent.parent / "config" / universe_source)
        candidates.append(Path(__file__).resolve().parent.parent / universe_source)
        candidates.append(
            Path(r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VDF") / universe_source
        )

    for p in candidates:
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    out = data
                elif isinstance(data, dict):
                    out = data.get("tickers") or data.get("universe") or []
                else:
                    out = []
                norm = []
                for entry in out:
                    if isinstance(entry, str):
                        norm.append({"ticker": entry, "name": entry})
                    elif isinstance(entry, dict) and "ticker" in entry:
                        norm.append(entry)
                if norm:
                    log.info("[twstock] universe loaded from %s (%d)", p, len(norm))
                    return norm[:limit] if limit else norm
            except Exception as e:
                log.warning("[twstock] universe load failed (%s): %s", p, e)
                continue

    log.info("[twstock] using default %d-ticker universe", len(_DEFAULT_TW_UNIVERSE))
    return _DEFAULT_TW_UNIVERSE[:limit] if limit else _DEFAULT_TW_UNIVERSE


def _bbg_from_tw_ticker(tw_t: str) -> str:
    base = tw_t.split(".")[0]
    return f"{base} TT Equity"


def _fetch_tw_prices(tickers: List[Dict[str, str]], start: str, end: str):
    try:
        pd, yf = _imports_yf()
    except Exception as e:
        log.error("[twstock] yf/pd missing: %s", e)
        return None

    frames = []
    for i, t in enumerate(tickers, 1):
        tk = t["ticker"]
        name = t.get("name", "")
        try:
            df = yf.download(
                tickers=tk, start=start,
                end=(datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d"),
                auto_adjust=False, actions=False, progress=False, threads=False,
            )
        except Exception as e:
            log.warning("[twstock] %s yf failed: %s", tk, e)
            continue

        if df is None or df.empty:
            continue
        norm = _normalize_columns(df, tk, name, tk, _bbg_from_tw_ticker(tk))
        if not norm.empty:
            mc = _get_market_cap(yf, tk)
            if mc:
                norm["Market_Cap"] = mc
            frames.append(norm)
        if i % 10 == 0:
            log.info("[twstock] yf %d/%d", i, len(tickers))
        time.sleep(0.1)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def _attach_chip_placeholders(df):
    import pandas as pd
    if df is None or df.empty:
        return df
    for c in [
        "FI_Net", "IT_Net", "Dealer_Net", "Total_Net",
        "FI_Hold_Pct", "IT_Hold_Pct", "Dealer_Hold_Pct",
        "Margin_Buy", "Margin_Sell", "Margin_Balance",
        "Short_Buy", "Short_Sell", "Short_Balance",
        "Margin_Maintenance_Pct", "Short_Margin_Ratio_Pct",
        "DayTrade_Volume", "DayTrade_Amount", "DayTrade_Ratio_Pct",
    ]:
        if c not in df.columns:
            df[c] = pd.NA
    return df


def _merge_prices_and_chips(prices_df, chips_df):
    import pandas as pd
    if prices_df is None or prices_df.empty:
        return prices_df
    if chips_df is None or chips_df.empty:
        return _attach_chip_placeholders(prices_df)

    prices_df = prices_df.copy(); chips_df = chips_df.copy()
    prices_df["Date"] = prices_df["Date"].astype(str)
    chips_df["Date"] = chips_df["Date"].astype(str)

    chip_cols = [c for c in chips_df.columns if c not in ("Date", "Ticker")]
    overlap = [c for c in chip_cols if c in prices_df.columns]
    if overlap:
        prices_df = prices_df.drop(columns=overlap)

    merged = prices_df.merge(chips_df[["Date", "Ticker"] + chip_cols],
                             on=["Date", "Ticker"], how="left")
    return _attach_chip_placeholders(merged)


def fetch_tw_stock_unified(spec, ctx):
    """Entry point: tw_stock (yfinance prices + TWSE/TPEX chips)."""
    try:
        import pandas as pd
    except Exception:
        log.error("[twstock] pandas missing")
        return None

    universe = _load_universe(spec.universe_source, ctx.get("limit"))
    ticker_override = ctx.get("ticker_override")
    if ticker_override:
        universe = [{"ticker": ticker_override, "name": ticker_override}]

    store = ctx.get("store")
    start = ctx["start"]
    end = ctx["end"]
    full_refresh = ctx.get("full_refresh", False)
    skip_chips = bool(ctx.get("skip_chips", False))

    if not full_refresh and store is not None:
        existing = store.load_existing(spec.output_file)
        if existing is not None and not existing.empty and "Date" in existing.columns:
            try:
                last = str(existing["Date"].max())
                new_start = (datetime.strptime(last, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
                if new_start > start:
                    log.info("[twstock] incremental: %s -> %s (existing last=%s)", new_start, end, last)
                    start = new_start
            except Exception:
                pass

    if start > end:
        log.info("[twstock] up-to-date")
        return pd.DataFrame()

    log.info("[twstock] universe size: %d  range: %s -> %s", len(universe), start, end)

    prices_df = _fetch_tw_prices(universe, start, end)
    if prices_df is None or prices_df.empty:
        log.warning("[twstock] zero rows from yfinance")
        return pd.DataFrame()
    log.info("[twstock] prices fetched: %d rows", len(prices_df))

    if skip_chips:
        log.info("[twstock] skip_chips=True - chip columns will be NA")
        final = _attach_chip_placeholders(prices_df)
    else:
        try:
            ticker_list = [t["ticker"] for t in universe]
            chips_df = fetch_tw_chips(ticker_list, start, end)
            log.info("[twstock] chips fetched: %d rows", 0 if chips_df is None else len(chips_df))
            merged = _merge_prices_and_chips(prices_df, chips_df)
            final = compute_chip_derived(merged)
        except Exception as e:
            log.error("[twstock] chip fetch failed: %s - falling back to prices-only", e)
            final = _attach_chip_placeholders(prices_df)

    log.info("[twstock] produced %d total rows", len(final))
    return final


# [VIA:ANCHOR:D4_FETCH_MARKET:END]
