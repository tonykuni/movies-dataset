"""
vdf_fetchers_consensus.py — TW Stock YFinance + FactSet Consensus

Ports the VERITAS_Consensus_Database_OneShot.ps1 logic into VDF framework.
Drops the Playwright dependency by trying lighter HTTP-only scrape first;
falls back gracefully when JS-rendering is required.

Two data sources:
  1. YFinance Quote v7 + Chart v8 APIs (no key needed)
  2. Cnyes (鉅亨網) HTML scrape for FactSet consensus

This module exposes:
  fetch_yfinance_one(tw_ticker, yf_ticker)
  fetch_cnyes_consensus(tw_ticker)
  fetch_consensus_for_ticker(tw_ticker, yf_ticker)
  fetch_consensus_universe(tickers)
"""

from __future__ import annotations
import re
import datetime as _dt
from typing import Any

try:
    import vdf_supportive_bridge as bridge
except ImportError:
    from . import vdf_supportive_bridge as bridge  # type: ignore

TIMEOUT_S = 20

YF_QUOTE_URL = "https://query1.finance.yahoo.com/v7/finance/quote?symbols={ticker}"
YF_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=5d&interval=1d"
CNYES_URL    = "https://www.cnyes.com/twstock/{ticker}/summary/overview"

TW_TICKER_RE   = re.compile(r"^(?!202[1-9])(?!2030)[1-9]\d{3}$")
TW_YF_TICKER_RE = re.compile(r"^[1-9]\d{3}\.(TW|TWO)$")

FORWARD_YEARS = [2024, 2025, 2026, 2027, 2028]
ACTUAL_YEARS  = [2024, 2025]
ESTIMATE_YEARS = [2026, 2027, 2028]


# ============================================================
# Helpers
# ============================================================

def _now_str() -> str:
    return _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _to_float(x: Any) -> float | None:
    if x is None or x == "":
        return None
    try:
        return float(str(x).replace(",", "").replace("%", "").strip())
    except (ValueError, TypeError):
        return None


def _to_date(x: Any) -> str | None:
    if x is None or str(x).strip() == "":
        return None
    return str(x).replace("/", "-")[:10]


def _http_get_json(url: str) -> dict[str, Any]:
    data = bridge.http_get_json(url, timeout=TIMEOUT_S)
    if data is None:
        raise RuntimeError(f"GET-JSON failed: {url}")
    return data


def _http_get_html(url: str) -> str | None:
    return bridge.http_get(
        url,
        headers={"Accept-Language": "zh-TW,zh;q=0.9"},
        timeout=TIMEOUT_S,
    )


def tw_to_yfinance_candidates(tw: str) -> list[str]:
    return [f"{tw}.TW", f"{tw}.TWO"]


# ============================================================
# YFinance
# ============================================================

def fetch_yfinance_one(tw_ticker: str, yf_ticker: str | None = None) -> dict[str, Any]:
    """Fetch YFinance Quote+Chart for one TW stock.

    Tries yf_ticker first, then .TW, then .TWO.
    Returns a flat dict with all yf_* fields, plus yf_error on failure.
    """
    candidates = []
    if yf_ticker and TW_YF_TICKER_RE.match(yf_ticker):
        candidates.append(yf_ticker)
    candidates.extend(tw_to_yfinance_candidates(tw_ticker))
    candidates = list(dict.fromkeys(candidates))

    last_err = ""
    for yf in candidates:
        try:
            q = _http_get_json(YF_QUOTE_URL.format(ticker=yf))
            results = q.get("quoteResponse", {}).get("result", [])
            if not results:
                last_err = f"empty quote ({yf})"
                continue
            r = results[0]

            adj_close = None
            volume = None
            try:
                c = _http_get_json(YF_CHART_URL.format(ticker=yf))
                cres = c.get("chart", {}).get("result", [])
                if cres:
                    inds = cres[0].get("indicators", {})
                    adj_arr = inds.get("adjclose", [{}])[0].get("adjclose") or []
                    vol_arr = inds.get("quote",    [{}])[0].get("volume")   or []
                    if adj_arr:
                        adj_close = adj_arr[-1]
                    if vol_arr:
                        volume = vol_arr[-1]
            except Exception:
                pass

            return {
                "tw_ticker": tw_ticker,
                "tw_yfinance_ticker": yf,
                "yf_adj_close":                    adj_close,
                "yf_volume":                       volume,
                "yf_market_cap":                   r.get("marketCap"),
                "yf_target_mean_price":            r.get("targetMeanPrice"),
                "yf_target_high_price":            r.get("targetHighPrice"),
                "yf_target_low_price":             r.get("targetLowPrice"),
                "yf_recommendation_mean":          r.get("recommendationMean"),
                "yf_recommendation_key":           r.get("recommendationKey"),
                "yf_number_of_analyst_opinions":   r.get("numberOfAnalystOpinions"),
                "yf_currency":                     r.get("currency"),
                "yf_quote_time":                   _now_str(),
                "yf_error":                        "",
            }
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"

    return {
        "tw_ticker":                       tw_ticker,
        "tw_yfinance_ticker":              yf_ticker or "",
        "yf_adj_close":                    None,
        "yf_volume":                       None,
        "yf_market_cap":                   None,
        "yf_target_mean_price":            None,
        "yf_target_high_price":            None,
        "yf_target_low_price":             None,
        "yf_recommendation_mean":          None,
        "yf_recommendation_key":           None,
        "yf_number_of_analyst_opinions":   None,
        "yf_currency":                     None,
        "yf_quote_time":                   _now_str(),
        "yf_error":                        last_err,
    }


# ============================================================
# Cnyes scrape (FactSet)
# ============================================================

def _norm_html_text(text: str) -> str:
    """Strip HTML tags and collapse whitespace."""
    text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.DOTALL)
    text = re.sub(r"<style[^>]*>.*?</style>",   " ", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>",                   " ", text)
    text = re.sub(r"&nbsp;",                    " ", text)
    text = re.sub(r"&amp;",                     "&", text)
    text = re.sub(r"\s+",                       " ", text)
    return text.strip()


def parse_target_block(text: str) -> dict[str, Any]:
    out: dict[str, Any] = {
        "factset_updated_at":            None,
        "factset_target_analyst_count":  None,
        "factset_target_current_price":  None,
        "factset_target_low":            None,
        "factset_target_median":         None,
        "factset_target_high":           None,
    }
    m = re.search(r"(\d{4}/\d{2}/\d{2})\s*更新", text)
    if m:
        out["factset_updated_at"] = _to_date(m.group(1))
    m = re.search(r"目前有\s*(\d+)\s*位分析師", text)
    if m:
        out["factset_target_analyst_count"] = int(m.group(1))
    patterns = {
        "factset_target_current_price": r"目前\s*([0-9]+(?:\.[0-9]+)?)",
        "factset_target_low":           r"最低估值\s*([0-9]+(?:\.[0-9]+)?)",
        "factset_target_median":        r"中位數\s*([0-9]+(?:\.[0-9]+)?)",
        "factset_target_high":          r"最高估值\s*([0-9]+(?:\.[0-9]+)?)",
    }
    for key, pat in patterns.items():
        m = re.search(pat, text)
        if m:
            out[key] = _to_float(m.group(1))
    return out


def parse_rating_block(text: str) -> dict[str, Any]:
    out: dict[str, Any] = {
        "factset_rating_updated_at":         None,
        "factset_rating_analyst_count":      None,
        "factset_rating_optimistic_count":   None,
        "factset_rating_neutral_count":      None,
        "factset_rating_pessimistic_count":  None,
    }
    m = re.search(r"(\d{4}/\d{2}/\d{2})\s*更新", text)
    if m:
        out["factset_rating_updated_at"] = _to_date(m.group(1))
    patterns = {
        "factset_rating_analyst_count":      r"有\s*(\d+)\s*位分析師",
        "factset_rating_optimistic_count":   r"積極樂觀\s*(\d+)\s*位",
        "factset_rating_neutral_count":      r"保持中立\s*(\d+)\s*位",
        "factset_rating_pessimistic_count":  r"保守悲觀\s*(\d+)\s*位",
    }
    for key, pat in patterns.items():
        m = re.search(pat, text)
        if m:
            out[key] = int(m.group(1))
    return out


def parse_eps_block(text: str) -> dict[str, Any]:
    out: dict[str, Any] = {"factset_eps_updated_at": None}
    for y in FORWARD_YEARS:
        out[f"factset_diluted_eps_median_{y}"] = None
        out[f"factset_diluted_eps_high_{y}"]   = None
        out[f"factset_diluted_eps_low_{y}"]    = None
    m = re.search(r"(\d{4}/\d{2}/\d{2})\s*更新", text)
    if m:
        out["factset_eps_updated_at"] = _to_date(m.group(1))

    years_str = [str(y) for y in FORWARD_YEARS]
    label_map = {"中位數": "median", "最高價": "high", "最低價": "low"}
    for row_name, label in label_map.items():
        pat = row_name + r"\s+" + r"\s+".join([r"([0-9]+(?:\.[0-9]+)?)"] * len(years_str))
        m = re.search(pat, text)
        if not m:
            continue
        for idx, year in enumerate(years_str, start=1):
            out[f"factset_diluted_eps_{label}_{year}"] = _to_float(m.group(idx))
    return out


def fetch_cnyes_consensus(tw_ticker: str) -> dict[str, Any]:
    """HTTP-only scrape (no Playwright). May return empty values if Cnyes
    renders these blocks client-side. Best for nightly batch."""
    row: dict[str, Any] = {"tw_ticker": tw_ticker, "factset_error": ""}
    url = CNYES_URL.format(ticker=tw_ticker)
    html = _http_get_html(url)
    if html is None:
        row["factset_error"] = "fetch failed"
        return row
    text = _norm_html_text(html)

    target = parse_target_block(text)
    rating = parse_rating_block(text)
    eps    = parse_eps_block(text)

    row.update(target)
    row.update(rating)
    row.update(eps)

    # Check for total emptiness
    if (target.get("factset_target_median") is None and
        rating.get("factset_rating_analyst_count") is None and
        eps.get("factset_diluted_eps_median_2026") is None):
        row["factset_error"] = "no consensus blocks parseable (may require JS render)"

    return row


# ============================================================
# Unified
# ============================================================

def fetch_consensus_for_ticker(tw_ticker: str, yf_ticker: str | None = None, name: str = "") -> dict[str, Any]:
    """Fetch full consensus row for one TW stock. Combines YFinance + Cnyes."""
    yf_row     = fetch_yfinance_one(tw_ticker, yf_ticker)
    cnyes_row  = fetch_cnyes_consensus(tw_ticker)

    merged: dict[str, Any] = {
        "tw_ticker": tw_ticker,
        "tw_yfinance_ticker": yf_ticker or yf_row.get("tw_yfinance_ticker", ""),
        "name": name,
        "display_name": f"{name} ({tw_ticker})" if name else tw_ticker,
        "run_time": _now_str(),
    }
    merged.update({k: v for k, v in yf_row.items() if k not in merged})
    merged.update({k: v for k, v in cnyes_row.items() if k not in merged or merged.get(k) is None})
    return merged


def fetch_consensus_universe(
    universe: list[dict[str, str]],
    max_tickers: int | None = None,
    parallel: bool = True,
    max_workers: int | None = None,
) -> list[dict[str, Any]]:
    """Iterate universe and fetch consensus for each.

    universe items: {"tw_ticker": "2330", "tw_yfinance_ticker": "2330.TW", "name": "台積電"}

    When parallel=True (default), uses Celeritas-backed parallel_map for adaptive thread budgeting.
    """
    iter_uni = universe[:max_tickers] if max_tickers else universe
    valid = [r for r in iter_uni if TW_TICKER_RE.match(r.get("tw_ticker", ""))]

    def _one(r: dict[str, str]) -> dict[str, Any]:
        return fetch_consensus_for_ticker(
            r["tw_ticker"],
            r.get("tw_yfinance_ticker"),
            r.get("name", ""),
        )

    if parallel and len(valid) > 1:
        results = bridge.parallel_map(_one, valid, max_workers=max_workers)
        # Filter out None (failed) entries and replace with error rows
        out = []
        for r, res in zip(valid, results):
            if res is not None:
                out.append(res)
            else:
                out.append({
                    "tw_ticker":    r["tw_ticker"],
                    "factset_error": "parallel fetch failed",
                    "yf_error":     "parallel fetch failed",
                })
        return out

    return [_one(r) for r in valid]


if __name__ == "__main__":
    print("Consensus fetcher smoke test")
    row = fetch_consensus_for_ticker("2330", "2330.TW", "台積電")
    for k, v in row.items():
        print(f"  {k}: {v}")
