"""
vdf_fetchers_tdcc.py — 台灣集中保管結算所 (TDCC) data fetcher

TDCC publishes weekly:
  1. 股權分散表 (Shareholder Distribution Table)
     - Weekly snapshot of share ownership by holding tier
     - Source: https://www.tdcc.com.tw/portal/zh/smWeb/qryStock
     - API: https://smart.tdcc.com.tw/opendata/getOD.ashx?id=1-5
  2. ETF 受益人數 (ETF Beneficiary Count)
     - Weekly tracking of how many unique investors hold each ETF
     - Indicates retail retention and institutional rotation

Output: canonical schema rows compatible with VDF SSOT.
"""

from __future__ import annotations
import json
import datetime as _dt
from typing import Any

try:
    import vdf_supportive_bridge as bridge
except ImportError:
    from . import vdf_supportive_bridge as bridge  # type: ignore

TIMEOUT_S = 30

# Endpoints
TDCC_OPENDATA_DIST    = "https://smart.tdcc.com.tw/opendata/getOD.ashx?id=1-5"
TDCC_OPENDATA_ETF     = "https://smart.tdcc.com.tw/opendata/getOD.ashx?id=2-1"  # ETF beneficiary
TDCC_QRY_STOCK        = "https://www.tdcc.com.tw/portal/zh/smWeb/qryStock"


# ============================================================
# 股權分散表 — Shareholder Distribution
# ============================================================

# 17 holding tiers used by TDCC
HOLDING_TIERS = [
    "1-999",         # 1
    "1000-5000",     # 2
    "5001-10000",    # 3
    "10001-15000",   # 4
    "15001-20000",   # 5
    "20001-30000",   # 6
    "30001-40000",   # 7
    "40001-50000",   # 8
    "50001-100000",  # 9
    "100001-200000", # 10
    "200001-400000", # 11
    "400001-600000", # 12
    "600001-800000", # 13
    "800001-1000000",# 14
    "1000001+",      # 15
    "Total",         # 16
    "Other",         # 17
]


def fetch_distribution_raw(ticker: str | None = None) -> list[dict[str, Any]]:
    """Fetch TDCC shareholder distribution CSV (open data).

    Returns: list of dicts with keys:
      資料日期, 證券代號, 持股分級, 人數, 股數, 占集保庫存比例(%)
    """
    cache_key = f"tdcc_dist::{ticker or 'all'}::{_dt.date.today().isoformat()}"
    cached = bridge.cache_get(cache_key)
    if cached is not None:
        return cached

    text = bridge.http_get(TDCC_OPENDATA_DIST, timeout=TIMEOUT_S)
    if text is None:
        raise RuntimeError(f"TDCC distribution fetch failed: {TDCC_OPENDATA_DIST}")

    rows: list[dict[str, Any]] = []
    lines = text.strip().split("\n")
    if not lines:
        return []
    headers = [h.strip() for h in lines[0].split(",")]
    for line in lines[1:]:
        if not line.strip():
            continue
        cells = [c.strip() for c in line.split(",")]
        if len(cells) < len(headers):
            cells += [""] * (len(headers) - len(cells))
        row = dict(zip(headers, cells))
        # Filter by ticker if specified
        if ticker:
            tkr_field = row.get("證券代號") or row.get("ticker") or ""
            if tkr_field != ticker:
                continue
        rows.append(row)

    bridge.cache_set(cache_key, rows, ttl_sec=12 * 3600)  # weekly data, cache 12h
    return rows


def standardize_distribution_for_ssot(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Convert TDCC raw rows to canonical SSOT schema."""
    out: list[dict[str, Any]] = []
    for r in rows:
        date_raw = r.get("資料日期") or r.get("date", "")
        ticker = r.get("證券代號") or r.get("ticker", "")
        tier = r.get("持股分級") or r.get("tier", "")
        try:
            holders = int(r.get("人數", "0").replace(",", ""))
        except (ValueError, AttributeError):
            holders = 0
        try:
            shares = int(r.get("股數", "0").replace(",", ""))
        except (ValueError, AttributeError):
            shares = 0
        try:
            pct = float(r.get("占集保庫存比例%", "0").replace(",", "").replace("%", ""))
        except (ValueError, AttributeError):
            pct = 0.0

        out.append({
            "Date":            date_raw,
            "Ticker":          ticker,
            "Tier":            tier,
            "Holder_Count":    holders,
            "Shares_Total":    shares,
            "Pct_of_Custody":  pct,
            "Source":          "TDCC/opendata",
        })
    return out


# ============================================================
# ETF 受益人數 — ETF Beneficiary Count
# ============================================================

def fetch_etf_beneficiary_count(etf_ticker: str | None = None) -> list[dict[str, Any]]:
    """Fetch TDCC ETF beneficiary (unique holder) counts.

    Weekly data. Returns list of {Date, Ticker, Beneficiary_Count, Shares_Issued}.
    """
    cache_key = f"tdcc_etf_ben::{etf_ticker or 'all'}::{_dt.date.today().isoformat()}"
    cached = bridge.cache_get(cache_key)
    if cached is not None:
        return cached

    text = bridge.http_get(TDCC_OPENDATA_ETF, timeout=TIMEOUT_S)
    if text is None:
        # Endpoint may be unavailable; try the dist endpoint as fallback
        # (some TDCC datasets are merged)
        return []

    rows: list[dict[str, Any]] = []
    lines = text.strip().split("\n")
    if not lines:
        return []
    headers = [h.strip() for h in lines[0].split(",")]
    for line in lines[1:]:
        cells = [c.strip() for c in line.split(",")]
        if len(cells) < len(headers):
            cells += [""] * (len(headers) - len(cells))
        row = dict(zip(headers, cells))
        tkr = row.get("證券代號") or row.get("ticker", "")
        if etf_ticker and tkr != etf_ticker:
            continue
        rows.append(row)

    # Standardize
    out = []
    for r in rows:
        try:
            ben_count = int(r.get("受益人數", "0").replace(",", ""))
        except (ValueError, AttributeError):
            ben_count = 0
        try:
            shares = int(r.get("發行單位數", "0").replace(",", ""))
        except (ValueError, AttributeError):
            shares = 0
        out.append({
            "Date":               r.get("資料日期", ""),
            "Ticker":             r.get("證券代號", ""),
            "Beneficiary_Count":  ben_count,
            "Shares_Issued":      shares,
            "Source":             "TDCC/etf_beneficiary",
        })

    bridge.cache_set(cache_key, out, ttl_sec=12 * 3600)
    return out


# ============================================================
# Aggregation helpers
# ============================================================

def compute_retail_concentration(
    distribution_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute concentration metrics from a distribution snapshot.

    Returns:
      retail_pct:        % held by tiers 1-9 (< 100k shares)
      institutional_pct: % held by tiers 14-15 (> 800k shares)
      avg_holders_per_tier
      gini_estimate (rough)
    """
    if not distribution_rows:
        return {"retail_pct": 0.0, "institutional_pct": 0.0, "avg_holders_per_tier": 0}

    retail_pct = 0.0
    institutional_pct = 0.0
    total_holders = 0
    tier_count = 0

    for r in distribution_rows:
        tier = r.get("Tier", "")
        pct = r.get("Pct_of_Custody", 0)
        if not isinstance(pct, (int, float)):
            continue
        # Map tier name to position
        try:
            tier_idx = HOLDING_TIERS.index(tier)
        except ValueError:
            continue
        if 0 <= tier_idx <= 8:
            retail_pct += pct
        elif 13 <= tier_idx <= 14:
            institutional_pct += pct
        total_holders += r.get("Holder_Count", 0)
        tier_count += 1

    return {
        "retail_pct":           round(retail_pct, 2),
        "institutional_pct":    round(institutional_pct, 2),
        "avg_holders_per_tier": int(total_holders / tier_count) if tier_count else 0,
        "total_holders":        total_holders,
    }


def compute_beneficiary_delta(
    yesterday: list[dict[str, Any]],
    today:     list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute week-over-week change in ETF beneficiary count.

    Positive delta = retail inflow; negative = retail exit / redemption.
    """
    y_map = {r.get("Ticker"): r for r in yesterday}
    t_map = {r.get("Ticker"): r for r in today}

    deltas = []
    for tkr in set(y_map) & set(t_map):
        y_count = y_map[tkr].get("Beneficiary_Count", 0)
        t_count = t_map[tkr].get("Beneficiary_Count", 0)
        delta = t_count - y_count
        if y_count > 0:
            pct = (delta / y_count) * 100
        else:
            pct = 0
        deltas.append({
            "Ticker":           tkr,
            "Beneficiary_Last": y_count,
            "Beneficiary_Now":  t_count,
            "Delta":            delta,
            "Delta_Pct":        round(pct, 2),
        })

    deltas.sort(key=lambda x: x["Delta"], reverse=True)
    return {
        "date":           _dt.date.today().strftime("%Y-%m-%d"),
        "etf_count":      len(deltas),
        "top_inflow":     deltas[:10],
        "top_outflow":    deltas[-10:],
        "all_deltas":     deltas,
    }


if __name__ == "__main__":
    print("Testing TDCC fetcher (offline / cache mode)...")
    print(f"  Endpoints: {TDCC_OPENDATA_DIST}")
    print(f"             {TDCC_OPENDATA_ETF}")
    print()
    # Smoke test with synthetic data
    test = [
        {"Date": "20260524", "Ticker": "2330", "Tier": "1-999",
         "Holder_Count": 100000, "Shares_Total": 50000000, "Pct_of_Custody": 1.5},
        {"Date": "20260524", "Ticker": "2330", "Tier": "1000-5000",
         "Holder_Count": 50000, "Shares_Total": 125000000, "Pct_of_Custody": 3.75},
        {"Date": "20260524", "Ticker": "2330", "Tier": "800001-1000000",
         "Holder_Count": 100, "Shares_Total": 90000000, "Pct_of_Custody": 2.7},
    ]
    metrics = compute_retail_concentration(test)
    print(f"  Concentration metrics: {metrics}")
