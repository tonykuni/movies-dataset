#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:MODULE_SPEC:START]
# MODULE_NAME:       vdf_fetchers_macro
# MODULE_VERSION:    2.0.0
# MODULE_ROLE:       Macroeconomic / sentiment / shipping fetchers merged.
#                      - FRED macro (29 series)
#                      - Sentiment (VIX/MOVE/SKEW/...) via FRED or yfinance
#                      - Shipping (BDI/SCFI/CCFI) via akshare
# DEPENDENCIES:      pandas
# OPTIONAL_DEPENDENCIES: fredapi, yfinance, akshare, requests
# ERROR_POLICY:      WARN_AND_SKIP
# SAFE_SKIP:         True
# MERGE_UNIT_ID:     VDF-D4-FETCH-MACRO-002
# [VIA:MODULE_SPEC:END]
"""
Public entry points:

    fetch_macro_fred(spec, ctx)       # FRED macroeconomic series
    fetch_sentiment(spec, ctx)        # VIX / MOVE / SKEW / etc.
    fetch_shipping(spec, ctx)         # BDI / SCFI / CCFI via akshare
"""

# [VIA:ANCHOR:D4_FETCH_MACRO:START]

from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

log = logging.getLogger("VDF.macroish")


# =========================================================================
# SECTION 1: FRED helpers (used by both macro and sentiment)
# =========================================================================

def _fred_via_lib(api_key: str, series_id: str, start: str, end: str):
    try:
        from fredapi import Fred
        f = Fred(api_key=api_key)
        s = f.get_series(series_id, observation_start=start, observation_end=end)
        return s
    except Exception as e:
        log.debug("[macro] fredapi failed for %s: %s", series_id, e)
        return None


def _fred_via_http(api_key: str, series_id: str, start: str, end: str):
    try:
        import pandas as pd
        # Route via supportive bridge (Aegis retry/UA/throttle/circuit-breaker)
        try:
            import vdf_supportive_bridge as bridge
        except ImportError:
            bridge = None

        base = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": series_id,
            "api_key": api_key,
            "file_type": "json",
            "observation_start": start,
            "observation_end": end,
        }
        # Build URL with query string for bridge.http_get_json
        from urllib.parse import urlencode
        url = base + "?" + urlencode(params)

        if bridge is not None:
            data = bridge.http_get_json(url, timeout=30)
            if data is None:
                log.warning("[macro] bridge returned None for %s", series_id)
                return None
        else:
            import requests
            r = requests.get(base, params=params, timeout=30)
            if r.status_code != 200:
                log.warning("[macro] HTTP %d for %s", r.status_code, series_id)
                return None
            data = r.json()

        obs = data.get("observations", [])
        if not obs:
            return None
        df = pd.DataFrame(obs)
        df["date"] = pd.to_datetime(df["date"])
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna(subset=["value"])
        return df.set_index("date")["value"]
    except Exception as e:
        log.debug("[macro] HTTP fred failed for %s: %s", series_id, e)
        return None


def _from_fred(api_key: str, series_id: str, start: str, end: str):
    s = _fred_via_lib(api_key, series_id, start, end)
    if s is None:
        s = _fred_via_http(api_key, series_id, start, end)
    return s


# =========================================================================
# SECTION 2: Macro (FRED)
# =========================================================================

def fetch_macro_fred(spec, ctx):
    try:
        import pandas as pd
    except Exception:
        log.error("[macro] pandas missing")
        return None

    import os
    # Priority chain: explicit ctx > VDF_FRED_API_KEY env > FRED_API_KEY env > hardcoded default
    api_key = (
        ctx.get("fred_api_key", "")
        or os.environ.get("VDF_FRED_API_KEY", "")
        or os.environ.get("FRED_API_KEY", "")
        or "<REDACTED:VDF_FRED_API_KEY>"  # default (Tony's key)
    )
    start = ctx["start"]
    end = ctx["end"]
    if not api_key:
        log.warning("[macro] no FRED_API_KEY; skipping")
        return pd.DataFrame()

    rows: List[Dict[str, Any]] = []
    indicators = list(spec.indicators or [])

    log.info("[macro] fetching %d FRED series", len(indicators))
    for i, ind in enumerate(indicators, 1):
        sid = ind["series_id"]
        name = ind.get("name", sid)
        region = ind.get("region", "")
        category = ind.get("category", "")

        s = _from_fred(api_key, sid, start, end)
        if s is None or len(s) == 0:
            log.warning("[macro] %s empty", sid)
            continue

        for dt, val in s.items():
            try:
                if pd.isna(val):
                    continue
                rows.append({
                    "Date": dt.strftime("%Y-%m-%d") if hasattr(dt, "strftime") else str(dt)[:10],
                    "Series_Id": sid,
                    "Series_Name": name,
                    "Value": float(val),
                    "Unit": "",
                    "Source": "FRED",
                    "Region": region,
                    "Category": category,
                })
            except Exception:
                continue
        if i % 5 == 0:
            log.info("[macro] %d/%d series processed", i, len(indicators))
        time.sleep(0.3)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    log.info("[macro] produced %d rows", len(df))
    return df


# =========================================================================
# SECTION 3: Sentiment (mixed source per indicator)
# =========================================================================

def _from_yf_close(ticker: str, start: str, end: str):
    try:
        import yfinance as yf
        df = yf.download(ticker, start=start,
                         end=(datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d"),
                         auto_adjust=False, progress=False, threads=False)
        if df is None or df.empty:
            return None
        return df["Close"] if "Close" in df.columns else None
    except Exception as e:
        log.debug("[sent] yf %s failed: %s", ticker, e)
        return None


def fetch_sentiment(spec, ctx):
    try:
        import pandas as pd
    except Exception:
        log.error("[sent] pandas missing")
        return None

    import os
    api_key = (
        ctx.get("fred_api_key", "")
        or os.environ.get("VDF_FRED_API_KEY", "")
        or os.environ.get("FRED_API_KEY", "")
        or "<REDACTED:VDF_FRED_API_KEY>"
    )
    start = ctx["start"]
    end = ctx["end"]

    rows: List[Dict[str, Any]] = []
    indicators = list(spec.indicators or [])
    log.info("[sent] %d indicators", len(indicators))

    for i, ind in enumerate(indicators, 1):
        name = ind["indicator"]
        src = ind.get("source", "")
        cat = ind.get("category", "")
        s = None

        if src == "fred" and api_key:
            sid = ind.get("series_id")
            if sid:
                s = _from_fred(api_key, sid, start, end)
        elif src == "yfinance":
            tk = ind.get("ticker")
            if tk:
                s = _from_yf_close(tk, start, end)
        # akshare branch deliberately skipped here

        if s is None or len(s) == 0:
            log.warning("[sent] %s no data", name)
            continue

        for dt, val in s.items():
            try:
                if pd.isna(val):
                    continue
                rows.append({
                    "Date": dt.strftime("%Y-%m-%d") if hasattr(dt, "strftime") else str(dt)[:10],
                    "Indicator": name,
                    "Value": float(val),
                    "Source": src,
                    "Category": cat,
                })
            except Exception:
                continue
        if i % 3 == 0:
            log.info("[sent] %d/%d", i, len(indicators))
        time.sleep(0.3)

    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    log.info("[sent] produced %d rows", len(df))
    return df


# =========================================================================
# SECTION 4: Shipping (akshare)
# =========================================================================

def fetch_shipping(spec, ctx):
    try:
        import pandas as pd
    except Exception:
        log.error("[ship] pandas missing")
        return None

    try:
        import akshare as ak
    except Exception as e:
        log.warning("[ship] akshare unavailable: %s - skipping", e)
        return pd.DataFrame()

    rows: List[Dict[str, Any]] = []
    indicators = list(spec.indicators or [])

    for ind in indicators:
        name = ind["indicator"]
        fn = ind.get("function", "")
        cat = ind.get("category", "shipping")
        try:
            if not fn:
                continue
            ak_fn = getattr(ak, fn, None)
            if ak_fn is None:
                log.warning("[ship] %s function %s not in akshare", name, fn)
                continue
            df = ak_fn()
            if df is None or len(df) == 0:
                continue
            cols = [c.lower() for c in df.columns]
            date_col = next((c for c, lc in zip(df.columns, cols)
                             if "date" in lc or "日期" in c), None)
            val_col = next((c for c, lc in zip(df.columns, cols)
                            if any(k in lc for k in ["value", "index", "price", "close"])
                            or any(k in c for k in ["指數", "收盤"])), None)
            if not date_col or not val_col:
                log.warning("[ship] %s - couldn't infer date/value cols (%s)", name, df.columns.tolist())
                continue
            for _, r in df.iterrows():
                try:
                    rows.append({
                        "Date": pd.to_datetime(r[date_col]).strftime("%Y-%m-%d"),
                        "Series_Id": name,
                        "Series_Name": name,
                        "Value": float(r[val_col]),
                        "Unit": "",
                        "Source": "akshare",
                        "Region": "GLOBAL",
                        "Category": cat,
                    })
                except Exception:
                    continue
            log.info("[ship] %s ok", name)
        except Exception as e:
            log.warning("[ship] %s failed: %s", name, e)
        time.sleep(0.5)

    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    log.info("[ship] produced %d rows", len(df))
    return df


# [VIA:ANCHOR:D4_FETCH_MACRO:END]
