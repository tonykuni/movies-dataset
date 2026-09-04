"""
vdf_fetchers_fed.py — Federal Reserve FOMC scraper

Sources (all public, no auth):
  1. Statement text:  https://www.federalreserve.gov/monetarypolicy/fomcprojtabl{YYYYMMDD}.htm
  2. SEP / Dot Plot:  https://www.federalreserve.gov/monetarypolicy/files/fomcprojtabl{YYYYMMDD}.pdf
  3. Press releases:  https://www.federalreserve.gov/feeds/press_monetary.xml
  4. SEP CSV:         https://www.federalreserve.gov/monetarypolicy/files/fomcprojtabl{YYYYMMDD}.csv (when available)

Output: SEP forecasts + sentiment-extracted policy signals.
"""

from __future__ import annotations
import re
import datetime as _dt
from typing import Any

try:
    import vdf_supportive_bridge as bridge
except ImportError:
    from . import vdf_supportive_bridge as bridge  # type: ignore

TIMEOUT_S = 30

FED_PRESS_RSS    = "https://www.federalreserve.gov/feeds/press_monetary.xml"
FED_FOMC_INDEX   = "https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm"


# ============================================================
# RSS feed — monetary press releases (most recent FOMC)
# ============================================================

def fetch_fomc_press_feed() -> list[dict[str, Any]]:
    """Fetch latest FOMC press releases via RSS.

    Cached 1 hour. Returns list of {title, link, pubDate, description}.
    """
    cache_key = f"fed_press::{_dt.date.today().isoformat()}"
    cached = bridge.cache_get(cache_key)
    if cached is not None:
        return cached

    text = bridge.http_get(FED_PRESS_RSS, timeout=TIMEOUT_S)
    if text is None:
        return []

    items: list[dict[str, Any]] = []
    # Simple XML parse (RSS structure is consistent)
    item_pattern = re.compile(r"<item>(.*?)</item>", re.DOTALL)
    title_p     = re.compile(r"<title[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>", re.DOTALL)
    link_p      = re.compile(r"<link[^>]*>(.*?)</link>", re.DOTALL)
    date_p      = re.compile(r"<pubDate[^>]*>(.*?)</pubDate>", re.DOTALL)
    desc_p      = re.compile(r"<description[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>", re.DOTALL)

    for m in item_pattern.finditer(text):
        block = m.group(1)
        title_m = title_p.search(block)
        link_m  = link_p.search(block)
        date_m  = date_p.search(block)
        desc_m  = desc_p.search(block)
        if not title_m:
            continue
        items.append({
            "title":       title_m.group(1).strip(),
            "link":        link_m.group(1).strip() if link_m else "",
            "pubDate":     date_m.group(1).strip() if date_m else "",
            "description": (desc_m.group(1).strip()[:500] + "...") if desc_m and len(desc_m.group(1)) > 500 else (desc_m.group(1).strip() if desc_m else ""),
        })
        if len(items) >= 20:
            break

    bridge.cache_set(cache_key, items, ttl_sec=3600)
    return items


def filter_fomc_decisions(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """From press feed, extract only FOMC policy decisions (not speeches/testimony)."""
    keywords = ("FOMC statement", "Federal funds rate", "monetary policy", "policy decisions")
    decisions = []
    for item in items:
        title_lower = item.get("title", "").lower()
        desc_lower  = item.get("description", "").lower()
        if any(k.lower() in title_lower or k.lower() in desc_lower for k in keywords):
            decisions.append(item)
    return decisions


# ============================================================
# Dot Plot / SEP — Summary of Economic Projections
# ============================================================

# Hard-coded dot plot dates (Fed publishes 4× per year)
# Auto-detect via FOMC calendar page would be ideal but the URL pattern is well-known
def get_recent_sep_dates() -> list[str]:
    """Return likely SEP release dates (YYYYMMDD strings) for the last ~12 months.

    Fed releases SEP in March, June, September, December of each year.
    """
    today = _dt.date.today()
    candidates = []
    for year in (today.year, today.year - 1):
        for month, day_range in [(3, [18, 19, 20]), (6, [12, 13, 14, 18, 19, 20]),
                                   (9, [17, 18, 19, 20]), (12, [11, 12, 13, 18, 19])]:
            for day in day_range:
                d = _dt.date(year, month, day)
                if d <= today:
                    candidates.append(d.strftime("%Y%m%d"))
    return sorted(candidates, reverse=True)


def fetch_sep_table(date_str: str) -> dict[str, Any] | None:
    """Fetch Summary of Economic Projections table for a given meeting date.

    Returns parsed table with median projections for Fed Funds, GDP, PCE, Unemployment.
    """
    url = f"https://www.federalreserve.gov/monetarypolicy/fomcprojtabl{date_str}.htm"
    cache_key = f"fed_sep::{date_str}"
    cached = bridge.cache_get(cache_key)
    if cached is not None:
        return cached

    html = bridge.http_get(url, timeout=TIMEOUT_S)
    if not html or "fomcprojtabl" not in url:
        return None

    # Parse the projection table
    # Typical structure: rows for each variable (Change in real GDP, Unemployment rate, PCE, Federal funds rate)
    # × columns for each year (this year, next year, longer run) × percentile (median, central tendency)

    projections: dict[str, Any] = {"meeting_date": date_str, "variables": {}}
    
    # Find tables with class="data-table" or just plain table
    table_pattern = re.compile(r"<table[^>]*>(.*?)</table>", re.DOTALL | re.IGNORECASE)
    row_pattern   = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL | re.IGNORECASE)
    cell_pattern  = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.DOTALL | re.IGNORECASE)

    # Variables we want to extract
    variables_to_extract = {
        "Change in real GDP":      "gdp_growth",
        "Unemployment rate":       "unemployment",
        "PCE inflation":           "pce_headline",
        "Core PCE inflation":      "pce_core",
        "Federal funds rate":      "fed_funds_rate",
        "Memo: Projected appropriate":  "fed_funds_rate_appropriate",
    }

    for table_html in table_pattern.findall(html):
        rows = row_pattern.findall(table_html)
        for row_html in rows:
            cells = [_clean(c) for c in cell_pattern.findall(row_html)]
            if not cells:
                continue
            # First cell is usually the variable name
            label = cells[0].strip()
            for var_label, key in variables_to_extract.items():
                if var_label.lower() in label.lower():
                    # Extract numeric values from remaining cells
                    nums = []
                    for c in cells[1:]:
                        try:
                            v = float(c.replace("%", "").replace(",", ""))
                            nums.append(v)
                        except (ValueError, TypeError):
                            nums.append(None)
                    if any(v is not None for v in nums):
                        projections["variables"].setdefault(key, []).append(nums)
                    break

    bridge.cache_set(cache_key, projections, ttl_sec=24 * 3600)  # SEP data is stable
    return projections


# ============================================================
# Forward guidance keyword scan
# ============================================================

HAWKISH_TERMS = (
    "tighten", "raise rates", "rate hike", "higher for longer",
    "additional firming", "restrictive", "vigilant",
    "inflation risks", "above target",
)
DOVISH_TERMS = (
    "ease", "rate cut", "accommodative", "patient", "support employment",
    "stable prices achieved", "softening labor market",
)


def score_policy_tone(text: str) -> dict[str, Any]:
    """Simple keyword-based sentiment for FOMC statements.

    Returns:
      hawkish_count, dovish_count, net_score (positive = hawkish), classification
    """
    text_lower = text.lower()
    hawk = sum(1 for t in HAWKISH_TERMS if t in text_lower)
    dove = sum(1 for t in DOVISH_TERMS if t in text_lower)
    net = hawk - dove
    if net >= 3:    cls = "Very Hawkish"
    elif net >= 1:  cls = "Hawkish"
    elif net == 0:  cls = "Neutral"
    elif net >= -2: cls = "Dovish"
    else:           cls = "Very Dovish"
    return {
        "hawkish_count": hawk,
        "dovish_count":  dove,
        "net_score":     net,
        "classification": cls,
    }


# ============================================================
# Helpers
# ============================================================

def _clean(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"&nbsp;|&#160;", " ", s)
    s = re.sub(r"&amp;", "&", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


# ============================================================
# Unified entry
# ============================================================

def fetch_fed_full_snapshot() -> dict[str, Any]:
    """One-shot: get latest press feed + most recent SEP + tone score.

    Returns:
      {
        'recent_decisions': [...],
        'latest_sep':       {...},
        'policy_tone':      {...},
      }
    """
    snap: dict[str, Any] = {
        "fetched_at": _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "recent_decisions": [],
        "latest_sep": None,
        "policy_tone": None,
    }

    # Press feed
    try:
        feed = fetch_fomc_press_feed()
        snap["recent_decisions"] = filter_fomc_decisions(feed)[:5]
    except Exception as e:
        snap["press_error"] = f"{type(e).__name__}: {e}"

    # Try most recent SEP date(s)
    for date_str in get_recent_sep_dates()[:4]:
        try:
            sep = fetch_sep_table(date_str)
            if sep and sep.get("variables"):
                snap["latest_sep"] = sep
                break
        except Exception:
            continue

    # Tone score from most recent decision
    if snap["recent_decisions"]:
        latest_desc = snap["recent_decisions"][0].get("description", "")
        snap["policy_tone"] = score_policy_tone(latest_desc)

    return snap


if __name__ == "__main__":
    print("Testing FED FOMC fetcher...")
    print()
    # Test tone scoring (no network)
    test_text = "The Committee will continue to assess additional firming that may be appropriate. Inflation risks remain elevated."
    tone = score_policy_tone(test_text)
    print(f"  Tone scoring test: {tone}")
    print()
    print(f"  Recent SEP dates to try: {get_recent_sep_dates()[:6]}")
