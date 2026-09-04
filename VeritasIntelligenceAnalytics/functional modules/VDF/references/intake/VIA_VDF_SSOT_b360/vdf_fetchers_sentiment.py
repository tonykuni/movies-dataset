"""
vdf_fetchers_sentiment.py — Market sentiment indices

Two sources:
  1. AAII (American Association of Individual Investors) - weekly sentiment survey
     Endpoint: https://www.aaii.com/files/surveys/sentiment.xls (Excel file)
  2. CNN Fear & Greed Index
     Endpoint: https://production.dataviz.cnn.io/index/fearandgreed/graphdata

No API key required for either.
"""

from __future__ import annotations
import json
import io
import datetime as _dt
from typing import Any

try:
    import vdf_supportive_bridge as bridge
except ImportError:
    from . import vdf_supportive_bridge as bridge  # type: ignore

TIMEOUT_S = 30


# ============================================================
# AAII - Bull/Bear/Neutral weekly survey
# ============================================================

AAII_URL = "https://www.aaii.com/files/surveys/sentiment.xls"


def fetch_aaii(url: str = AAII_URL) -> bytes:
    """Download AAII sentiment.xls. Returns raw bytes."""
    data = bridge.http_get_bytes(url, timeout=TIMEOUT_S)
    if data is None:
        raise RuntimeError(f"AAII fetch failed: {url}")
    return data


def parse_aaii_xls(data: bytes, max_rows: int = 200) -> list[dict[str, Any]]:
    """Parse AAII sentiment xls into standardized records.

    Returns rows with: date, bullish, bearish, neutral, bull_bear_spread
    (all percentages 0-1 scale).
    """
    import pandas as pd
    bio = io.BytesIO(data)
    try:
        # AAII Excel has headers on row 4 (index 3) typically
        df = pd.read_excel(bio, sheet_name=0, header=3, engine="xlrd")
    except Exception:
        bio.seek(0)
        try:
            df = pd.read_excel(bio, sheet_name=0, header=3, engine="openpyxl")
        except Exception:
            bio.seek(0)
            df = pd.read_excel(bio, sheet_name=0, header=3)

    df.columns = [str(c).strip() for c in df.columns]

    # Identify columns flexibly
    date_col = None
    bull_col = None
    bear_col = None
    neut_col = None
    for c in df.columns:
        lc = c.lower()
        if "date" in lc and date_col is None:
            date_col = c
        elif "bullish" in lc and bull_col is None:
            bull_col = c
        elif "bearish" in lc and bear_col is None:
            bear_col = c
        elif "neutral" in lc and neut_col is None:
            neut_col = c

    if not all([date_col, bull_col, bear_col, neut_col]):
        return []

    df = df[[date_col, bull_col, bear_col, neut_col]].copy()
    df.columns = ["date", "bullish", "bearish", "neutral"]
    df = df.dropna(subset=["date"]).tail(max_rows)

    out: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        d = row["date"]
        if hasattr(d, "strftime"):
            ds = d.strftime("%Y-%m-%d")
        else:
            ds = str(d)[:10]
        try:
            b, x, n = float(row["bullish"]), float(row["bearish"]), float(row["neutral"])
        except (ValueError, TypeError):
            continue
        out.append({
            "date": ds,
            "bullish": b,
            "bearish": x,
            "neutral": n,
            "bull_bear_spread": b - x,
        })
    return out


def standardize_aaii_for_ssot(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert to (date, series_id, value, source) rows."""
    out: list[dict[str, Any]] = []
    for r in records:
        d = r["date"]
        out.append({"date": d, "series_id": "US.Sentiment.AAII.Bullish",        "value": r["bullish"],         "source": "AAII"})
        out.append({"date": d, "series_id": "US.Sentiment.AAII.Bearish",        "value": r["bearish"],         "source": "AAII"})
        out.append({"date": d, "series_id": "US.Sentiment.AAII.Neutral",        "value": r["neutral"],         "source": "AAII"})
        out.append({"date": d, "series_id": "US.Sentiment.AAII.BullBearSpread", "value": r["bull_bear_spread"],"source": "AAII"})
    return out


# ============================================================
# CNN Fear & Greed Index
# ============================================================

CNN_URL_TEMPLATE = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata/{start}"
CNN_URL_LATEST = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"


def fetch_cnn_fear_greed(start_date: str | None = None) -> dict[str, Any]:
    """Fetch CNN Fear & Greed data. Returns raw JSON dict.

    Cached for 1 hour via supportive bridge (CNN updates daily).
    """
    if start_date:
        url = CNN_URL_TEMPLATE.format(start=start_date)
    else:
        url = CNN_URL_LATEST

    # Check cache first
    cache_key = f"cnn_fg::{start_date or 'latest'}"
    cached = bridge.cache_get(cache_key)
    if cached is not None:
        return cached

    data = bridge.http_get_json(
        url,
        headers={
            "Accept": "application/json",
            "Origin": "https://edition.cnn.com",
        },
        timeout=TIMEOUT_S,
    )
    if data is None:
        raise RuntimeError(f"CNN F&G fetch failed: {url}")

    # Cache for 1 hour
    bridge.cache_set(cache_key, data, ttl_sec=3600)
    return data


def parse_cnn_fear_greed(raw: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse CNN F&G JSON into standardized records (one row per date, all components)."""
    rows_by_date: dict[str, dict[str, Any]] = {}

    # Top-level composite
    fg = raw.get("fear_and_greed_historical", {})
    for entry in fg.get("data", []):
        ts = entry.get("x")
        score = entry.get("y")
        if ts is None or score is None:
            continue
        d = _dt.date.fromtimestamp(ts / 1000).strftime("%Y-%m-%d")
        rows_by_date.setdefault(d, {"date": d})["composite"] = float(score)

    # Components
    component_keys = {
        "put_call_options":         "put_call",
        "market_momentum_sp500":    "momentum",
        "stock_price_strength":     "strength",
        "stock_price_breadth":      "breadth",
        "safe_haven_demand":        "safe_haven",
        "junk_bond_demand":         "junk_bond",
        "market_volatility_vix":    "vix",
    }
    for raw_key, field in component_keys.items():
        comp = raw.get(raw_key, {})
        for entry in comp.get("data", []):
            ts = entry.get("x")
            score = entry.get("y")
            if ts is None or score is None:
                continue
            d = _dt.date.fromtimestamp(ts / 1000).strftime("%Y-%m-%d")
            rows_by_date.setdefault(d, {"date": d})[field] = float(score)

    return sorted(rows_by_date.values(), key=lambda r: r["date"])


def standardize_cnn_for_ssot(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert to (date, series_id, value, source) rows."""
    mapping = {
        "composite":  "US.Sentiment.CNN.FearGreed",
        "put_call":   "US.Sentiment.CNN.FG.PutCall",
        "momentum":   "US.Sentiment.CNN.FG.Momentum",
        "strength":   "US.Sentiment.CNN.FG.Strength",
        "breadth":    "US.Sentiment.CNN.FG.Breadth",
        "safe_haven": "US.Sentiment.CNN.FG.SafeHaven",
        "junk_bond":  "US.Sentiment.CNN.FG.JunkBond",
        "vix":        "US.Sentiment.CNN.FG.VIX",
    }
    out: list[dict[str, Any]] = []
    for r in records:
        d = r["date"]
        for key, sid in mapping.items():
            if key in r:
                out.append({"date": d, "series_id": sid, "value": r[key], "source": "CNN"})
    return out


# ============================================================
# Unified entry
# ============================================================

def fetch_sentiment_all() -> dict[str, list[dict[str, Any]]]:
    """Fetch both AAII and CNN. Returns dict with 'aaii' and 'cnn' keys."""
    result: dict[str, list[dict[str, Any]]] = {"aaii": [], "cnn": []}
    try:
        aaii_bytes = fetch_aaii()
        result["aaii"] = parse_aaii_xls(aaii_bytes)
    except Exception as e:
        result["aaii_error"] = str(e)  # type: ignore
    try:
        cnn_raw = fetch_cnn_fear_greed()
        result["cnn"] = parse_cnn_fear_greed(cnn_raw)
    except Exception as e:
        result["cnn_error"] = str(e)  # type: ignore
    return result


if __name__ == "__main__":
    print("Sentiment fetcher smoke test")
    try:
        res = fetch_sentiment_all()
        print(f"  AAII: {len(res.get('aaii', []))} rows; error={res.get('aaii_error', '')}")
        print(f"  CNN:  {len(res.get('cnn',  []))} rows; error={res.get('cnn_error',  '')}")
    except Exception as e:
        print(f"  FAILED: {e}")
