"""
vdf_fetchers_fiscal.py — Treasury FiscalData API fetcher

US Treasury Daily Statement (DTS) + Monthly Treasury Statement (MTS).
No API key required. Endpoint: https://api.fiscaldata.treasury.gov/services/api/fiscal_service/

Endpoints used:
  - DTS deposits/withdrawals:  v1/accounting/dts/deposits_withdrawals_operating_cash
  - DTS operating cash:        v1/accounting/dts/operating_cash_balance
  - DTS public debt:           v1/accounting/dts/public_debt_transactions
  - MTS receipts (Table 1):    v1/accounting/mts/mts_table_1
  - MTS receipts by source:    v1/accounting/mts/mts_table_4
  - MTS outlays by function:   v1/accounting/mts/mts_table_5
"""

from __future__ import annotations
import json
import urllib.parse
import datetime as _dt
from typing import Any

# Use the supportive bridge (Aegis-backed HTTP with retry/cache/throttle)
try:
    import vdf_supportive_bridge as bridge
except ImportError:
    from . import vdf_supportive_bridge as bridge  # type: ignore

BASE = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"
TIMEOUT_S = 30


def _http_get_json(url: str) -> dict[str, Any]:
    """Wrapped GET-JSON via supportive bridge."""
    result = bridge.http_get_json(url, headers={"Accept": "application/json"}, timeout=TIMEOUT_S)
    if result is None:
        raise RuntimeError(f"FiscalData HTTP error for {url}: bridge returned None")
    return result


def _build_url(endpoint: str, params: dict[str, Any]) -> str:
    qs_parts = []
    for k, v in params.items():
        qs_parts.append(f"{urllib.parse.quote(k, safe='[]')}={urllib.parse.quote(str(v))}")
    qs = "&".join(qs_parts)
    return f"{BASE}/{endpoint}?{qs}"


def fetch_paged(
    endpoint: str,
    fields: list[str] | None = None,
    filter_str: str | None = None,
    sort: str = "-record_date",
    page_size: int = 1000,
    max_pages: int = 50,
) -> list[dict[str, Any]]:
    """Paginate through a FiscalData endpoint.

    Returns a flat list of records.
    """
    rows: list[dict[str, Any]] = []
    page = 1
    while page <= max_pages:
        params: dict[str, Any] = {
            "page[number]": page,
            "page[size]":   page_size,
            "sort":         sort,
        }
        if fields:
            params["fields"] = ",".join(fields)
        if filter_str:
            params["filter"] = filter_str

        url = _build_url(endpoint, params)
        data = _http_get_json(url)
        batch = data.get("data", [])
        if not batch:
            break
        rows.extend(batch)
        meta = data.get("meta", {})
        pagination = meta.get("pagination", {}) if isinstance(meta, dict) else {}
        # FiscalData reports total-pages; bail when exhausted
        total_pages = pagination.get("total-pages") or pagination.get("total_pages")
        if total_pages and page >= int(total_pages):
            break
        page += 1
    return rows


def _fmt_date(d: _dt.date | str | None) -> str | None:
    if d is None:
        return None
    if isinstance(d, str):
        return d[:10]
    return d.strftime("%Y-%m-%d")


# ============================================================
# DTS - Daily Treasury Statement
# ============================================================

def fetch_dts_deposits_withdrawals(start: str | None = None, days: int = 30) -> list[dict[str, Any]]:
    """Daily deposits & withdrawals from operating cash (totals only)."""
    endpoint = "v1/accounting/dts/deposits_withdrawals_operating_cash"
    if start is None:
        start = (_dt.date.today() - _dt.timedelta(days=days)).strftime("%Y-%m-%d")
    filter_str = f"record_date:gte:{start},transaction_type:eq:Withdrawals"
    # We want both deposits and withdrawals; just pull all and post-filter
    rows = fetch_paged(endpoint, filter_str=f"record_date:gte:{start}", page_size=1000)
    return rows


def fetch_dts_operating_cash_balance(start: str | None = None, days: int = 30) -> list[dict[str, Any]]:
    """TGA — Treasury General Account balance."""
    endpoint = "v1/accounting/dts/operating_cash_balance"
    if start is None:
        start = (_dt.date.today() - _dt.timedelta(days=days)).strftime("%Y-%m-%d")
    return fetch_paged(endpoint, filter_str=f"record_date:gte:{start}", page_size=1000)


def fetch_dts_public_debt(start: str | None = None, days: int = 30) -> list[dict[str, Any]]:
    """DTS Public Debt Cash Issues & Redemptions."""
    endpoint = "v1/accounting/dts/public_debt_transactions"
    if start is None:
        start = (_dt.date.today() - _dt.timedelta(days=days)).strftime("%Y-%m-%d")
    return fetch_paged(endpoint, filter_str=f"record_date:gte:{start}", page_size=1000)


# ============================================================
# MTS - Monthly Treasury Statement
# ============================================================

def fetch_mts_table_1(start_year: int | None = None) -> list[dict[str, Any]]:
    """Monthly receipts, outlays, deficit/surplus (top-level totals).

    Cached for 6 hours — MTS publishes monthly so frequent fetches are wasteful.
    """
    if start_year is None:
        start_year = _dt.date.today().year - 2

    cache_key = f"mts_t1::{start_year}"
    cached = bridge.cache_get(cache_key)
    if cached is not None:
        return cached

    endpoint = "v1/accounting/mts/mts_table_1"
    rows = fetch_paged(endpoint, filter_str=f"record_fiscal_year:gte:{start_year}", page_size=1000)
    if rows:
        bridge.cache_set(cache_key, rows, ttl_sec=6 * 3600)
    return rows


def fetch_mts_table_4(start_year: int | None = None) -> list[dict[str, Any]]:
    """Receipts by source category. Cached 6h."""
    if start_year is None:
        start_year = _dt.date.today().year - 1

    cache_key = f"mts_t4::{start_year}"
    cached = bridge.cache_get(cache_key)
    if cached is not None:
        return cached

    endpoint = "v1/accounting/mts/mts_table_4"
    rows = fetch_paged(endpoint, filter_str=f"record_fiscal_year:gte:{start_year}", page_size=1000)
    if rows:
        bridge.cache_set(cache_key, rows, ttl_sec=6 * 3600)
    return rows


def fetch_mts_table_5(start_year: int | None = None) -> list[dict[str, Any]]:
    """Outlays by function. Cached 6h."""
    if start_year is None:
        start_year = _dt.date.today().year - 1

    cache_key = f"mts_t5::{start_year}"
    cached = bridge.cache_get(cache_key)
    if cached is not None:
        return cached

    endpoint = "v1/accounting/mts/mts_table_5"
    rows = fetch_paged(endpoint, filter_str=f"record_fiscal_year:gte:{start_year}", page_size=1000)
    if rows:
        bridge.cache_set(cache_key, rows, ttl_sec=6 * 3600)
    return rows


# ============================================================
# Unified entry point - returns standardized records
# ============================================================

def fetch_fiscal_all(start_date: str | None = None, days: int = 30) -> dict[str, list[dict[str, Any]]]:
    """Fetch every fiscal endpoint at once.

    Returns dict with keys: dts_dep_wd, dts_cash, dts_debt, mts_t1, mts_t4, mts_t5.
    Each value is a list of raw records.
    """
    if start_date is None:
        start_date = (_dt.date.today() - _dt.timedelta(days=days)).strftime("%Y-%m-%d")

    out: dict[str, list[dict[str, Any]]] = {}
    out["dts_dep_wd"]  = fetch_dts_deposits_withdrawals(start=start_date)
    out["dts_cash"]    = fetch_dts_operating_cash_balance(start=start_date)
    out["dts_debt"]    = fetch_dts_public_debt(start=start_date)
    out["mts_table_1"] = fetch_mts_table_1()
    out["mts_table_4"] = fetch_mts_table_4()
    out["mts_table_5"] = fetch_mts_table_5()
    return out


def standardize_dts_for_ssot(raw_records: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    """Convert raw FiscalData JSON to flat (date, series_id, value) rows.

    Maps to SSOT codes:
        US.Fiscal.DTS.TotalReceipts
        US.Fiscal.DTS.TotalOutlays
        US.Fiscal.DTS.OperatingCashBalance
        US.Fiscal.DTS.PublicDebtIssues
        US.Fiscal.DTS.PublicDebtRedemptions
        US.Fiscal.MTS.GrossReceipts
        US.Fiscal.MTS.GrossOutlays
        US.Fiscal.MTS.DeficitSurplus
    """
    out: list[dict[str, Any]] = []

    # DTS deposits/withdrawals
    for r in raw_records.get("dts_dep_wd", []):
        d = r.get("record_date")
        if not d:
            continue
        ttype = (r.get("transaction_type") or "").lower()
        amt_str = r.get("transaction_today_amt") or r.get("transaction_today_amt") or "0"
        try:
            amt = float(amt_str)
        except (ValueError, TypeError):
            continue
        if "deposit" in ttype:
            out.append({"date": d, "series_id": "US.Fiscal.DTS.TotalReceipts", "value": amt, "source": "Treasury_FD"})
        elif "withdrawal" in ttype:
            out.append({"date": d, "series_id": "US.Fiscal.DTS.TotalOutlays",  "value": amt, "source": "Treasury_FD"})

    # DTS operating cash balance
    for r in raw_records.get("dts_cash", []):
        d = r.get("record_date")
        bal = r.get("close_today_bal") or r.get("opening_today_bal")
        if d and bal not in (None, ""):
            try:
                out.append({"date": d, "series_id": "US.Fiscal.DTS.OperatingCashBalance", "value": float(bal), "source": "Treasury_FD"})
            except (ValueError, TypeError):
                pass

    # DTS public debt transactions
    for r in raw_records.get("dts_debt", []):
        d = r.get("record_date")
        ttype = (r.get("transaction_type") or "").lower()
        amt_str = r.get("transaction_today_amt") or "0"
        if not d:
            continue
        try:
            amt = float(amt_str)
        except (ValueError, TypeError):
            continue
        if "issue" in ttype:
            out.append({"date": d, "series_id": "US.Fiscal.DTS.PublicDebtIssues",      "value": amt, "source": "Treasury_FD"})
        elif "redempt" in ttype:
            out.append({"date": d, "series_id": "US.Fiscal.DTS.PublicDebtRedemptions", "value": amt, "source": "Treasury_FD"})

    # MTS table 1
    for r in raw_records.get("mts_table_1", []):
        d = r.get("record_date")
        cls = (r.get("classification_desc") or "").lower()
        if not d:
            continue
        # Map to series based on classification
        if "total" in cls and "receipts" in cls:
            sid = "US.Fiscal.MTS.GrossReceipts"
        elif "total" in cls and "outlays" in cls:
            sid = "US.Fiscal.MTS.GrossOutlays"
        elif "deficit" in cls or "surplus" in cls:
            sid = "US.Fiscal.MTS.DeficitSurplus"
        else:
            continue
        amt_str = r.get("current_month_gross_rcpt_amt") or r.get("current_month_gross_outly_amt") or r.get("current_fytd_dft_sur_amt") or "0"
        try:
            out.append({"date": d, "series_id": sid, "value": float(amt_str), "source": "Treasury_FD"})
        except (ValueError, TypeError):
            pass

    return out


if __name__ == "__main__":
    # Smoke test (requires network)
    print("Testing Treasury FiscalData fetchers...")
    try:
        cash = fetch_dts_operating_cash_balance(days=7)
        print(f"  DTS cash balance: {len(cash)} rows")
        if cash:
            print(f"    sample: {cash[0]}")
    except Exception as e:
        print(f"  DTS cash FAILED: {e}")

    try:
        mts = fetch_mts_table_1()
        print(f"  MTS table 1: {len(mts)} rows")
    except Exception as e:
        print(f"  MTS FAILED: {e}")
