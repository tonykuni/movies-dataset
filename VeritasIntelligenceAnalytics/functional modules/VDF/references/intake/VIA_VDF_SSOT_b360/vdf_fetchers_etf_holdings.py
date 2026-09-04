"""
vdf_fetchers_etf_holdings.py — Taiwan Active ETF daily holdings (v4 production)

Per FSC regulation, all active ETFs (suffix 'A') must publish full daily holdings.
This module scrapes:
  1. TWSE e添富 hub (https://www.twse.com.tw/zh/ETFortune/etfInfo/{ticker})
  2. Per-issuer PCF pages (10 issuers, distinct HTML layouts)
  3. Aggregator fallbacks (Pocket, CMoney, MoneyDJ)
  4. TDCC 股權分散表 (weekly investor distribution — orthogonal data)

Canonical output schema (per holding row):
  Date | ETF_Ticker | ETF_Name | Holding_Ticker | Holding_Name |
  Shares | Market_Value | Weight_Pct | Sector | Asset_Type | Source

All HTTP routes through vdf_supportive_bridge (Aegis-protected).
"""

from __future__ import annotations
import re
import json
import datetime as _dt
from typing import Any

try:
    import vdf_supportive_bridge as bridge
except ImportError:
    from . import vdf_supportive_bridge as bridge  # type: ignore

TIMEOUT_S = 30


# ============================================================
# Active ETF registry (18 ETFs as of 2026-Q2)
# ============================================================

ACTIVE_ETF_REGISTRY: dict[str, dict[str, str]] = {
    "00980A": {"issuer": "NOM",   "name": "主動野村臺灣優選"},
    "00981A": {"issuer": "UNI",   "name": "主動統一台股增長"},
    "00982A": {"issuer": "CAP",   "name": "主動群益台灣強棒"},
    "00983A": {"issuer": "CTBC",  "name": "主動中信ARK創新"},
    "00984A": {"issuer": "AGI",   "name": "主動安聯台灣高息"},
    "00985A": {"issuer": "NOM",   "name": "主動野村台灣50"},
    "00987A": {"issuer": "TS",    "name": "主動台新優勢成長"},
    "00988A": {"issuer": "UNI",   "name": "主動統一全球創新"},
    "00989A": {"issuer": "JPM",   "name": "主動摩根美國科技"},
    "00990A": {"issuer": "YT",    "name": "主動元大AI新經濟"},
    "00991A": {"issuer": "FHTR",  "name": "主動復華未來50"},
    "00992A": {"issuer": "CAP",   "name": "主動群益科技創新"},
    "00994A": {"issuer": "FIRST", "name": "主動第一金台股優選"},
    "00995A": {"issuer": "CTBC",  "name": "主動中信台灣卓越"},
    "00997A": {"issuer": "CAP",   "name": "主動群益美國增長"},
    "00999A": {"issuer": "AGI",   "name": "主動安聯台股趨勢"},
    "00402A": {"issuer": "AGI",   "name": "主動安聯美國科技領航"},
    "00403A": {"issuer": "UNI",   "name": "主動統一升級版0050"},
}

# Issuer endpoints — actual PCF page patterns observed
ISSUERS: dict[str, dict[str, Any]] = {
    "UNI": {
        "name":         "統一投信",
        "pcf_index":    "https://www.ezmoney.com.tw/ETF/Transaction/PCF",
        "holding_url":  "https://www.ezmoney.com.tw/ETF/Fund/Info",  # query string varies
        "parser":       "uni_html_table",
    },
    "NOM": {
        "name":         "野村投信",
        "pcf_index":    "https://www.nomurafunds.com.tw/Etf/Trade/Pcf.aspx",
        "holding_url":  "https://www.nomurafunds.com.tw/ETFWEB/product-description",
        "parser":       "nom_html_table",
    },
    "CAP": {
        "name":         "群益投信",
        "pcf_index":    "https://www.capitalfund.com.tw/CFTWeb/CFTMainAU.aspx?MainItemKey=ETF",
        "holding_url":  "https://www.capitalfund.com.tw/CFTWeb/CFTMainBI.aspx",
        "parser":       "cap_html_table",
    },
    "CTBC": {
        "name":         "中信投信",
        "pcf_index":    "https://www.ctbcinvestments.com/etf/trade/pcf",
        "holding_url":  "https://www.ctbcinvestments.com/etf/fund",
        "parser":       "ctbc_html_table",
    },
    "AGI": {
        "name":         "安聯投信",
        "pcf_index":    "https://tw.allianzgi.com/funds/etf/transaction",
        "holding_url":  "https://tw.allianzgi.com/funds/etf",
        "parser":       "agi_html_table",
    },
    "YT": {
        "name":         "元大投信",
        "pcf_index":    "https://www.yuantaetfs.com/api/Pcf",
        "holding_url":  "https://www.yuantaetfs.com/product",
        "parser":       "yt_html_table",
    },
    "FIRST": {
        "name":         "第一金投信",
        "pcf_index":    "https://www.firstrust.com.tw/Etf/Transaction/PCF",
        "holding_url":  "https://www.firstrust.com.tw/Etf/Product",
        "parser":       "first_html_table",
    },
    "FHTR": {
        "name":         "復華投信",
        "pcf_index":    "https://www.fhtrust.com.tw/etf/transaction/pcf",
        "holding_url":  "https://www.fhtrust.com.tw/etf/product",
        "parser":       "fhtr_html_table",
    },
    "TS": {
        "name":         "台新投信",
        "pcf_index":    "https://tsit.tsit.com.tw/ETF/Trade/Pcf",
        "holding_url":  "https://tsit.tsit.com.tw/ETF/Product",
        "parser":       "ts_html_table",
    },
    "JPM": {
        "name":         "摩根投信",
        "pcf_index":    "https://www.jpmorgan.com.tw/etf/transaction",
        "holding_url":  "https://www.jpmorgan.com.tw/etf/product",
        "parser":       "jpm_html_table",
    },
}

# Aggregator fallbacks (third-party, more stable HTML)
POCKET_URL = "https://www.pocket.tw/etf/tw/{ticker}/fundholding"
CMONEY_URL = "https://www.cmoney.tw/etf/tw/{ticker}/holdings"
MONEYDJ_URL = "https://www.moneydj.com/ETF/X/Basic/Basic0007.xdjhtm?etfid={ticker}.TW"
TWSE_AGG_URL = "https://www.twse.com.tw/zh/ETFortune/etfInfo/{ticker}"


# ============================================================
# Generic helpers
# ============================================================

def http_get(url: str, headers: dict[str, str] | None = None) -> str | None:
    """Robust GET via supportive bridge."""
    h = {"Accept-Language": "zh-TW,zh;q=0.9"}
    if headers:
        h.update(headers)
    return bridge.http_get(url, headers=h, timeout=TIMEOUT_S)


def http_get_json(url: str, headers: dict[str, str] | None = None) -> Any:
    return bridge.http_get_json(url, headers=headers, timeout=TIMEOUT_S)


def empty_holding_row(etf_ticker: str, date_str: str | None = None) -> dict[str, Any]:
    return {
        "Date":           date_str or _dt.date.today().strftime("%Y-%m-%d"),
        "ETF_Ticker":     etf_ticker,
        "ETF_Name":       ACTIVE_ETF_REGISTRY.get(etf_ticker, {}).get("name", ""),
        "Holding_Ticker": None,
        "Holding_Name":   None,
        "Shares":         None,
        "Market_Value":   None,
        "Weight_Pct":     None,
        "Sector":         None,
        "Asset_Type":     None,
        "Source":         None,
    }


def _clean_text(s: str | None) -> str:
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"&nbsp;|&#160;", " ", s)
    s = re.sub(r"&amp;", "&", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _to_float(s: Any) -> float | None:
    if s is None:
        return None
    txt = str(s).replace(",", "").replace("%", "").strip()
    if not txt or txt in ("-", "--", "N/A", "n/a"):
        return None
    try:
        return float(txt)
    except (ValueError, TypeError):
        return None


def _to_int(s: Any) -> int | None:
    v = _to_float(s)
    return int(v) if v is not None else None


# ============================================================
# Universal HTML table parser
# ============================================================

def parse_holdings_table(html: str, etf_ticker: str, source_tag: str) -> list[dict[str, Any]]:
    """Generic table-based extractor.

    Looks for any <table> containing rows with the pattern:
      [4-digit ticker] [stock name] [shares/qty]? [market value]? [weight%]
    Returns canonical schema rows.

    Robust to multiple table layouts because we match on row CONTENT (ticker
    regex), not column position.
    """
    if not html:
        return []

    rows: list[dict[str, Any]] = []
    seen_tickers: set[str] = set()

    # Strategy: extract every <tr>...</tr> block, then scan cells
    tr_pattern = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL | re.IGNORECASE)
    td_pattern = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.DOTALL | re.IGNORECASE)

    # Stock ticker regex (TW 4-digit, optional .TW suffix, allow leading 0 for ETFs)
    tkr_pat = re.compile(r"^\s*(\d{4,6}[A-Z]?)(?:\.TW)?\s*$")
    # Weight % pattern
    weight_pat = re.compile(r"^\s*([\d.]+)\s*%?\s*$")

    for tr_match in tr_pattern.finditer(html):
        tr_inner = tr_match.group(1)
        cells = [_clean_text(c) for c in td_pattern.findall(tr_inner)]
        if len(cells) < 2:
            continue

        # Find ticker cell
        ticker = None
        name   = None
        weight = None
        shares = None
        market_value = None

        for i, cell in enumerate(cells):
            if ticker is None and tkr_pat.match(cell):
                ticker = tkr_pat.match(cell).group(1)
                # Adjacent cell is usually the name
                if i + 1 < len(cells):
                    cand_name = cells[i + 1]
                    if cand_name and not re.match(r"^[\d.,%\-]+$", cand_name):
                        name = cand_name[:40]
                # Look for weight in subsequent cells
                for j in range(i + 1, len(cells)):
                    c = cells[j]
                    if "%" in c or weight_pat.match(c):
                        w = _to_float(c)
                        if w is not None and 0 < w < 100:
                            weight = w
                            break
                # Look for shares (large integer, no %)
                for j in range(i + 1, len(cells)):
                    c = cells[j]
                    if "%" in c:
                        continue
                    v = _to_float(c)
                    if v is not None and v > 100 and "." not in c.replace(",", ""):
                        if shares is None:
                            shares = int(v)
                        elif market_value is None:
                            market_value = v
                break

        if ticker and ticker not in seen_tickers:
            seen_tickers.add(ticker)
            row = empty_holding_row(etf_ticker)
            row["Holding_Ticker"] = ticker
            row["Holding_Name"]   = name
            row["Shares"]         = shares
            row["Market_Value"]   = market_value
            row["Weight_Pct"]     = weight
            row["Source"]         = source_tag
            rows.append(row)
            if len(rows) >= 100:
                break

    return rows


# ============================================================
# Per-issuer scrapers (use generic parser + issuer URL)
# ============================================================

def fetch_uni_holdings(etf_ticker: str) -> list[dict[str, Any]]:
    """統一投信 - ezmoney."""
    url = f"https://www.ezmoney.com.tw/ETF/Fund/Info?fundCode={etf_ticker}"
    html = http_get(url)
    return parse_holdings_table(html or "", etf_ticker, "UNI/ezmoney")


def fetch_nom_holdings(etf_ticker: str) -> list[dict[str, Any]]:
    """野村投信."""
    url = f"https://www.nomurafunds.com.tw/ETFWEB/product-description?fundNo={etf_ticker}"
    html = http_get(url)
    return parse_holdings_table(html or "", etf_ticker, "NOM/nomurafunds")


def fetch_cap_holdings(etf_ticker: str) -> list[dict[str, Any]]:
    """群益投信."""
    url = f"https://www.capitalfund.com.tw/CFTWeb/CFTMainBI.aspx?BItemKey=BI04&fundCode={etf_ticker}"
    html = http_get(url)
    return parse_holdings_table(html or "", etf_ticker, "CAP/capitalfund")


def fetch_ctbc_holdings(etf_ticker: str) -> list[dict[str, Any]]:
    """中信投信."""
    url = f"https://www.ctbcinvestments.com/etf/fund?ticker={etf_ticker}"
    html = http_get(url)
    return parse_holdings_table(html or "", etf_ticker, "CTBC/ctbcinvestments")


def fetch_agi_holdings(etf_ticker: str) -> list[dict[str, Any]]:
    """安聯投信."""
    url = f"https://tw.allianzgi.com/funds/etf?id={etf_ticker}"
    html = http_get(url)
    return parse_holdings_table(html or "", etf_ticker, "AGI/allianzgi")


def fetch_yt_holdings(etf_ticker: str) -> list[dict[str, Any]]:
    """元大投信 — has JSON API."""
    # Try JSON API first
    api_url = f"https://www.yuantaetfs.com/api/Pcf?fundId={etf_ticker}"
    j = http_get_json(api_url)
    rows: list[dict[str, Any]] = []
    if isinstance(j, dict):
        items = j.get("data") or j.get("items") or j.get("constituents") or []
        if isinstance(items, list):
            for item in items[:100]:
                if not isinstance(item, dict):
                    continue
                tkr = item.get("ticker") or item.get("code") or item.get("symbol")
                if not tkr:
                    continue
                row = empty_holding_row(etf_ticker)
                row["Holding_Ticker"] = str(tkr)[:8]
                row["Holding_Name"]   = item.get("name") or item.get("stockName") or ""
                row["Weight_Pct"]     = _to_float(item.get("weight") or item.get("ratio"))
                row["Shares"]         = _to_int(item.get("shares") or item.get("quantity"))
                row["Market_Value"]   = _to_float(item.get("market_value") or item.get("amount"))
                row["Source"]         = "YT/yuantaetfs(api)"
                rows.append(row)
            if rows:
                return rows

    # Fallback to HTML
    url = f"https://www.yuantaetfs.com/product?fundId={etf_ticker}"
    html = http_get(url)
    return parse_holdings_table(html or "", etf_ticker, "YT/yuantaetfs(html)")


def fetch_first_holdings(etf_ticker: str) -> list[dict[str, Any]]:
    """第一金投信."""
    url = f"https://www.firstrust.com.tw/Etf/Product?fund={etf_ticker}"
    html = http_get(url)
    return parse_holdings_table(html or "", etf_ticker, "FIRST/firstrust")


def fetch_fhtr_holdings(etf_ticker: str) -> list[dict[str, Any]]:
    """復華投信."""
    url = f"https://www.fhtrust.com.tw/etf/product?fund={etf_ticker}"
    html = http_get(url)
    return parse_holdings_table(html or "", etf_ticker, "FHTR/fhtrust")


def fetch_ts_holdings(etf_ticker: str) -> list[dict[str, Any]]:
    """台新投信."""
    url = f"https://tsit.tsit.com.tw/ETF/Product?code={etf_ticker}"
    html = http_get(url)
    return parse_holdings_table(html or "", etf_ticker, "TS/tsit")


def fetch_jpm_holdings(etf_ticker: str) -> list[dict[str, Any]]:
    """摩根投信."""
    url = f"https://www.jpmorgan.com.tw/etf/product?fund={etf_ticker}"
    html = http_get(url)
    return parse_holdings_table(html or "", etf_ticker, "JPM/jpmorgan")


# Per-issuer dispatcher map
ISSUER_FETCHERS = {
    "UNI":   fetch_uni_holdings,
    "NOM":   fetch_nom_holdings,
    "CAP":   fetch_cap_holdings,
    "CTBC":  fetch_ctbc_holdings,
    "AGI":   fetch_agi_holdings,
    "YT":    fetch_yt_holdings,
    "FIRST": fetch_first_holdings,
    "FHTR":  fetch_fhtr_holdings,
    "TS":    fetch_ts_holdings,
    "JPM":   fetch_jpm_holdings,
}


# ============================================================
# Aggregator fallbacks
# ============================================================

def fetch_pocket_holdings(etf_ticker: str) -> list[dict[str, Any]]:
    """Pocket Securities aggregator. Returns canonical schema rows."""
    url = POCKET_URL.format(ticker=etf_ticker)
    html = http_get(url)
    return parse_holdings_table(html or "", etf_ticker, "pocket.tw")


def fetch_cmoney_holdings(etf_ticker: str) -> list[dict[str, Any]]:
    """CMoney aggregator."""
    url = CMONEY_URL.format(ticker=etf_ticker)
    html = http_get(url)
    return parse_holdings_table(html or "", etf_ticker, "cmoney.tw")


def fetch_moneydj_holdings(etf_ticker: str) -> list[dict[str, Any]]:
    """MoneyDJ aggregator."""
    url = MONEYDJ_URL.format(ticker=etf_ticker)
    html = http_get(url)
    return parse_holdings_table(html or "", etf_ticker, "moneydj.com")


def fetch_twse_aggregator(etf_ticker: str) -> list[dict[str, Any]]:
    """TWSE e添富 hub (JS-rendered, often empty without browser)."""
    url = TWSE_AGG_URL.format(ticker=etf_ticker)
    html = http_get(url)
    return parse_holdings_table(html or "", etf_ticker, "twse.com.tw")


# ============================================================
# Unified entry
# ============================================================

def fetch_active_etf_holdings(etf_ticker: str, max_attempts: int = 5) -> list[dict[str, Any]]:
    """Fetch one active ETF's holdings.

    Tries in order:
      1. Issuer-specific scraper
      2. Pocket aggregator
      3. CMoney aggregator
      4. MoneyDJ aggregator
      5. TWSE e添富 hub

    Returns first non-empty result. Empty list if all sources fail.
    """
    info = ACTIVE_ETF_REGISTRY.get(etf_ticker)
    if not info:
        return []
    issuer = info["issuer"]

    attempts: list[tuple[str, callable]] = []
    fetcher = ISSUER_FETCHERS.get(issuer)
    if fetcher:
        attempts.append((f"issuer:{issuer}", fetcher))
    attempts.extend([
        ("pocket",   fetch_pocket_holdings),
        ("cmoney",   fetch_cmoney_holdings),
        ("moneydj",  fetch_moneydj_holdings),
        ("twse",     fetch_twse_aggregator),
    ])

    for tag, fn in attempts[:max_attempts]:
        try:
            rows = fn(etf_ticker)
            if rows:
                return rows
        except Exception:
            continue
    return []


def fetch_all_active_etfs(
    etfs: list[str] | None = None,
    parallel: bool = True,
) -> dict[str, list[dict[str, Any]]]:
    """Fetch holdings for all (or specified) active ETFs.

    Uses bridge.parallel_map when parallel=True (Celeritas-backed thread budget).
    """
    # None means "all 18"; empty list [] means "no targets"
    if etfs is None:
        targets = list(ACTIVE_ETF_REGISTRY.keys())
    else:
        targets = list(etfs)

    if not targets:
        return {}

    if parallel and len(targets) > 1:
        results = bridge.parallel_map(fetch_active_etf_holdings, targets)
        return dict(zip(targets, results))

    return {t: fetch_active_etf_holdings(t) for t in targets}


def compute_fund_flow(
    yesterday: list[dict[str, Any]],
    today:     list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute fund flow signals from two days of holdings.

    Returns:
      {
        'date': '2026-05-26',
        'holdings_added':    [tkr...],     # new positions
        'holdings_removed':  [tkr...],     # exited positions
        'shares_increased':  [{tkr, delta}, ...],
        'shares_decreased':  [{tkr, delta}, ...],
        'aum_estimate':      sum(market_value),
        'top_5_buys':        [...],
        'top_5_sells':       [...],
      }
    """
    by_tkr_y = {r["Holding_Ticker"]: r for r in yesterday if r.get("Holding_Ticker")}
    by_tkr_t = {r["Holding_Ticker"]: r for r in today     if r.get("Holding_Ticker")}

    added   = sorted(set(by_tkr_t) - set(by_tkr_y))
    removed = sorted(set(by_tkr_y) - set(by_tkr_t))

    delta_shares: list[tuple[str, float]] = []
    for tkr in set(by_tkr_y) & set(by_tkr_t):
        s_y = by_tkr_y[tkr].get("Shares") or 0
        s_t = by_tkr_t[tkr].get("Shares") or 0
        if s_y == 0 and s_t == 0:
            continue
        delta = s_t - s_y
        if delta != 0:
            delta_shares.append((tkr, delta))

    delta_shares.sort(key=lambda x: x[1], reverse=True)

    aum = sum((r.get("Market_Value") or 0) for r in today)

    return {
        "date":              _dt.date.today().strftime("%Y-%m-%d"),
        "holdings_added":    added,
        "holdings_removed":  removed,
        "shares_increased":  [{"ticker": t, "delta": d} for t, d in delta_shares if d > 0][:20],
        "shares_decreased":  [{"ticker": t, "delta": d} for t, d in delta_shares if d < 0][:20],
        "aum_estimate":      aum,
        "top_5_buys":        [t for t, d in delta_shares[:5]],
        "top_5_sells":       [t for t, d in delta_shares[-5:]],
    }


if __name__ == "__main__":
    print(f"Active ETFs registered: {len(ACTIVE_ETF_REGISTRY)}")
    print(f"Issuers registered:     {len(ISSUERS)}")
    print(f"Per-issuer scrapers:    {len(ISSUER_FETCHERS)}")
    print()
    # Smoke test (network)
    print("Smoke test: 00981A")
    rows = fetch_active_etf_holdings("00981A", max_attempts=2)
    print(f"  Got {len(rows)} holding rows")
    if rows:
        print(f"  Sample: {rows[0]}")
