"""Point-in-time forward valuation vintage reference implementation v2.1.

The module keeps index and ETF valuation anchors independent. It never updates
an old Parquet part in place and never calls an implied value source-reported.
Version 2.1 adds public FactSet release discovery, deterministic extraction,
content-hash de-duplication and cutoff-aware promotion gates on top of v2.
"""

from __future__ import annotations

import argparse
import html
import hashlib
import json
import math
import os
import re
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from dataclasses import asdict, dataclass
from datetime import date, datetime, time as datetime_time, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

try:
    import duckdb
except ModuleNotFoundError:
    duckdb = None


# ---------------------------------------------------------------------------
# Parameters: keep operational thresholds at the top of the file.
# ---------------------------------------------------------------------------

METHODOLOGY_VERSION = "forward_valuation_vintage_v2.1_factset_press_release"
INDEX_EPS_RELATIVE_TOLERANCE = 0.005
DEFAULT_INDEX_STALE_DAYS = 45
DEFAULT_ETF_STALE_DAYS = 45
DEFAULT_PUBLISHED_PE_INCREMENT = 0.1
APPROXIMATE_PE_HALF_WIDTH_MULTIPLIER = 1.0
DYNAMIC_STALE_MULTIPLIER = 1.5
DYNAMIC_STALE_MIN_DAYS = 7
DYNAMIC_STALE_MAX_DAYS = 62
MIN_HOLDINGS_MARKET_VALUE_COVERAGE = 0.95
MIN_HOLDINGS_COUNT_COVERAGE = 0.90
MAX_NEGATIVE_EARNINGS_WEIGHT_WARNING = 0.20
VALUATION_REGIME_WINDOW = 756
VALUATION_REGIME_MIN_PERIODS = 252
VALUATION_CHEAP_QUANTILE = 0.20
VALUATION_EXPENSIVE_QUANTILE = 0.80
ALLOWED_EARNINGS_BASIS = {"operating", "gaap_as_reported", "normalized"}
ALLOWED_HORIZONS = {"NTM", "FY1", "FY2", "CY1", "vendor_forward"}
ALLOWED_MAPPING_QUALITY = {"exact", "near_exact", "proxy"}
ALLOWED_QUALITY_STATUS = {"pass", "warning", "quarantine"}
ALLOWED_PRICE_CUTOFF_STATUS = {"exact", "external_same_close", "date_only", "mismatch"}
ALLOWED_INDEX_WEIGHTING_METHODS = {
    "float_market_cap",
    "market_cap",
    "price_weighted",
    "equal_weighted",
    "capped_market_cap",
    "provider_published",
}
ALLOWED_NAV_VALUATION_METHODS = {
    "issuer_nav",
    "issuer_fair_value_nav",
    "non_fair_value_nav",
    "holdings_reconstructed",
    "unknown",
}
ALLOWED_CUTOFF_ALIGNMENT = {"same_cutoff", "fair_value_adjusted", "stale_local_close", "unknown"}
FACTSET_INSIGHT_HOST = "insight.factset.com"
FACTSET_HTTP_USER_AGENT = (
    "VeritasForwardValuation/2.1 (+research; public-pages-only; contact=local-user)"
)
FACTSET_HTTP_TIMEOUT_SECONDS = 30
FACTSET_HTTP_RETRY_COUNT = 3
FACTSET_HTTP_BACKOFF_SECONDS = 2.0
FACTSET_REQUEST_INTERVAL_SECONDS = 1.5
FACTSET_MAX_DISCOVERED_URLS_PER_INDEX = 40
FACTSET_RESPECT_ROBOTS_TXT = True
FACTSET_DISCOVERY_URLS = (
    "https://insight.factset.com/topic/earnings",
    "https://insight.factset.com/sitemap.xml",
    "https://insight.factset.com/hs-sitemap.xml",
)
FACTSET_INDEX_RELEASE_REGISTRY: dict[str, dict[str, Any]] = {
    "SP500": {
        "display_name": "S&P 500",
        "aliases": ("s&p 500", "s&p500", "sp 500", "sp500"),
        "slug_tokens": ("sp-500", "s-p-500"),
        "expected_horizon": "NTM",
        "earnings_basis": "operating",
        "expected_cadence": "weekly_during_earnings_season",
    },
    "NASDAQ100": {
        "display_name": "Nasdaq-100",
        "aliases": ("nasdaq-100", "nasdaq 100", "nasdaq100"),
        "slug_tokens": ("nasdaq-100", "nasdaq-100-index"),
        "expected_horizon": "NTM",
        "earnings_basis": "normalized",
        "expected_cadence": "ad_hoc",
    },
    "RUSSELL2000": {
        "display_name": "Russell 2000",
        "aliases": ("russell 2000", "russell-2000"),
        "slug_tokens": ("russell-2000",),
        "expected_horizon": "NTM",
        "earnings_basis": "normalized",
        "expected_cadence": "ad_hoc",
    },
    "MSCI_TAIWAN": {
        "display_name": "MSCI Taiwan",
        "aliases": ("msci taiwan", "taiwan index", "taiwan market"),
        "slug_tokens": ("msci-taiwan", "taiwan-market"),
        "expected_horizon": "NTM",
        "earnings_basis": "normalized",
        "expected_cadence": "ad_hoc",
    },
    "MSCI_JAPAN": {
        "display_name": "MSCI Japan",
        "aliases": ("msci japan", "japan index", "japanese market"),
        "slug_tokens": ("msci-japan", "japan-market", "japanese-market"),
        "expected_horizon": "NTM",
        "earnings_basis": "normalized",
        "expected_cadence": "ad_hoc",
    },
    "MSCI_KOREA": {
        "display_name": "MSCI Korea",
        "aliases": ("msci korea", "korea index", "korean market"),
        "slug_tokens": ("msci-korea", "korea-market", "korean-market"),
        "expected_horizon": "NTM",
        "earnings_basis": "normalized",
        "expected_cadence": "ad_hoc",
    },
    "MSCI_INDIA": {
        "display_name": "MSCI India",
        "aliases": ("msci india", "india index", "indian market"),
        "slug_tokens": ("msci-india", "india-market", "indian-market"),
        "expected_horizon": "NTM",
        "earnings_basis": "normalized",
        "expected_cadence": "ad_hoc",
    },
    "STOXX600": {
        "display_name": "STOXX Europe 600",
        "aliases": ("stoxx europe 600", "stoxx 600", "stoxx600"),
        "slug_tokens": ("stoxx-600", "stoxx-europe-600"),
        "expected_horizon": "NTM",
        "earnings_basis": "normalized",
        "expected_cadence": "earnings_season_and_ad_hoc",
    },
    "EUROSTOXX50": {
        "display_name": "EURO STOXX 50",
        "aliases": ("euro stoxx 50", "eurostoxx 50", "eurostoxx50"),
        "slug_tokens": ("euro-stoxx-50", "eurostoxx-50"),
        "expected_horizon": "NTM",
        "earnings_basis": "normalized",
        "expected_cadence": "ad_hoc",
    },
    "MSCI_ACWI": {
        "display_name": "MSCI ACWI",
        "aliases": ("msci acwi", "all country world index"),
        "slug_tokens": ("msci-acwi", "all-country-world"),
        "expected_horizon": "NTM",
        "earnings_basis": "normalized",
        "expected_cadence": "ad_hoc",
    },
}
FACTSET_FORWARD_PE_PATTERNS = (
    (
        "forward_12m_ratio_is",
        r"forward\s+12[-\s]?month\s+p\s*/?\s*e\s+ratio"
        r"(?:\s+for\s+(?:the\s+)?.{1,80}?)?\s+(?:is|was)\s+"
        r"(?P<approx>~|approximately\s+|about\s+)?(?P<value>\d+(?:\.\d+)?)\s*x?",
    ),
    (
        "trades_at_12m_forward_pe",
        r"trades?\s+(?:at|on)\s+(?:a\s+)?(?:12[-\s]?month\s+)?forward\s+p\s*/?\s*e\s+(?:of\s+)?(?P<approx>~|approximately\s+|about\s+)?(?P<value>\d+(?:\.\d+)?)\s*x?",
    ),
    (
        "trades_on_forward_earnings",
        r"trades?\s+(?:at|on)\s+(?P<approx>~|approximately\s+|about\s+)?(?P<value>\d+(?:\.\d+)?)\s*x\s+forward\s+(?:12[-\s]?month\s+)?earnings",
    ),
    (
        "forward_pe_compressed",
        r"forward\s+p\s*/?\s*e\s+(?:ratio\s+)?(?:has\s+)?(?:compressed|expanded|moved|fell|rose)\s+to\s+(?P<approx>~|approximately\s+|about\s+)?(?P<value>\d+(?:\.\d+)?)\s*x?",
    ),
)
FACTSET_PRICE_EPS_PATTERNS = (
    (
        "closing_price_and_eps",
        r"closing\s+price\s+of\s+[$€£¥]?\s*(?P<price>[\d,]+(?:\.\d+)?)"
        r".{0,180}?forward\s+12[-\s]?month\s+eps\s+estimate\s+of\s+[$€£¥]?\s*(?P<eps>[\d,]+(?:\.\d+)?)",
    ),
    (
        "index_level_and_eps",
        r"(?:index\s+(?:level|close)|closing\s+level)\s+(?:of|at)\s+[$€£¥]?\s*(?P<price>[\d,]+(?:\.\d+)?)"
        r".{0,180}?(?:forward\s+12[-\s]?month|ntm)\s+eps\s+(?:estimate\s+)?(?:of|at)\s+[$€£¥]?\s*(?P<eps>[\d,]+(?:\.\d+)?)",
    ),
)
FACTSET_PUBLICATION_META_KEYS = (
    "article:published_time",
    "og:published_time",
    "datePublished",
    "publish-date",
)
FACTSET_DATE_MONTH_PATTERN = (
    r"(?P<month>January|February|March|April|May|June|July|August|"
    r"September|October|November|December)\s+(?P<day>\d{1,2})"
    r"(?:,\s*(?P<year>\d{4}))?"
)
FACTSET_EXTRACTION_MIN_CONFIDENCE = 0.75
DEFAULT_FACTSET_OUTPUT_ROOT = Path("data/forward_valuation/factset_public_releases")
UTC = timezone.utc


@dataclass(frozen=True)
class IndexReleaseObservation:
    index_id: str
    provider: str
    source_as_of_date: date
    release_ts_utc: datetime
    retrieved_ts_utc: datetime
    available_from_date: date
    horizon: str
    earnings_basis: str
    index_level_anchor: float
    source_url: str
    raw_document_hash: str
    published_forward_pe: float | None = None
    forward_eps_points_reported: float | None = None
    float_adjusted_market_cap: float | None = None
    published_pb: float | None = None
    currency: str | None = None
    max_stale_days: int = DEFAULT_INDEX_STALE_DAYS
    published_forward_pe_increment: float = DEFAULT_PUBLISHED_PE_INCREMENT
    is_approximate: bool = False
    anchor_price_source: str = "same_source"
    price_cutoff_status: str = "exact"
    index_weighting_method: str = "provider_published"
    aggregation_method: str = "provider_published"


@dataclass(frozen=True)
class ETFReleaseObservation:
    ticker: str
    provider: str
    source_as_of_date: date
    release_ts_utc: datetime
    retrieved_ts_utc: datetime
    available_from_date: date
    horizon: str
    earnings_basis: str
    nav_per_share_anchor: float
    source_url: str
    raw_document_hash: str
    market_close_anchor: float | None = None
    portfolio_forward_pe: float | None = None
    mapped_index_id: str | None = None
    mapped_index_forward_pe: float | None = None
    mapping_quality: str | None = None
    max_stale_days: int = DEFAULT_ETF_STALE_DAYS
    nav_valuation_method: str = "issuer_nav"
    cutoff_alignment: str = "same_cutoff"
    holdings_as_of_date: date | None = None
    fx_as_of_ts_utc: datetime | None = None


@dataclass(frozen=True)
class FactSetArticleDocument:
    index_id: str
    source_url: str
    canonical_url: str
    title: str
    publication_ts_utc: datetime
    retrieved_ts_utc: datetime
    date_precision_only: bool
    raw_document_hash: str
    raw_html: str
    plain_text: str


@dataclass(frozen=True)
class FactSetValuationCandidate:
    index_id: str
    source_url: str
    canonical_url: str
    title: str
    publication_ts_utc: datetime
    retrieved_ts_utc: datetime
    date_precision_only: bool
    source_as_of_date: date
    available_from_date: date
    horizon: str
    earnings_basis: str
    published_forward_pe: float | None
    forward_eps_points_reported: float | None
    index_level_anchor: float | None
    published_forward_pe_increment: float
    is_approximate: bool
    anchor_price_source: str
    price_cutoff_status: str
    raw_document_hash: str
    extraction_pattern_id: str | None
    extraction_excerpt: str | None
    extraction_confidence: float
    extraction_status: str
    extraction_warnings: tuple[str, ...]


def _normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _strip_html_to_text(raw_html: str) -> str:
    without_inert = re.sub(
        r"<(script|style|noscript)\b[^>]*>.*?</\1>",
        " ",
        raw_html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    without_comments = re.sub(r"<!--.*?-->", " ", without_inert, flags=re.DOTALL)
    without_tags = re.sub(r"<[^>]+>", " ", without_comments)
    return _normalize_whitespace(html.unescape(without_tags))


def _parse_html_attributes(tag: str) -> dict[str, str]:
    attributes: dict[str, str] = {}
    for match in re.finditer(
        r"([:\w-]+)\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s>]+))",
        tag,
        flags=re.IGNORECASE,
    ):
        attributes[match.group(1).lower()] = html.unescape(
            match.group(2) or match.group(3) or match.group(4) or ""
        ).strip()
    return attributes


def _extract_meta_value(raw_html: str, keys: Sequence[str]) -> str | None:
    normalized_keys = {key.lower() for key in keys}
    for tag_match in re.finditer(
        r"<meta\b[^>]*>", raw_html, flags=re.IGNORECASE | re.DOTALL
    ):
        attributes = _parse_html_attributes(tag_match.group(0))
        key = (
            attributes.get("property")
            or attributes.get("name")
            or attributes.get("itemprop")
        )
        if key and key.lower() in normalized_keys and attributes.get("content"):
            return attributes["content"]
    return None


def _extract_html_title(raw_html: str) -> str:
    meta_title = _extract_meta_value(raw_html, ("og:title", "twitter:title"))
    if meta_title:
        return _normalize_whitespace(meta_title)
    match = re.search(
        r"<title\b[^>]*>(.*?)</title>",
        raw_html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return _normalize_whitespace(html.unescape(match.group(1))) if match else ""


def _parse_datetime_utc(value: str) -> datetime | None:
    cleaned = value.strip()
    if not cleaned:
        return None
    candidates = (cleaned, cleaned.replace("Z", "+00:00"))
    for candidate in candidates:
        try:
            parsed = datetime.fromisoformat(candidate)
        except ValueError:
            continue
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    return None


def _extract_publication_timestamp(raw_html: str) -> datetime | None:
    meta_value = _extract_meta_value(raw_html, FACTSET_PUBLICATION_META_KEYS)
    if meta_value:
        parsed = _parse_datetime_utc(meta_value)
        if parsed is not None:
            return parsed
    json_ld_match = re.search(
        r'"datePublished"\s*:\s*"([^"]+)"', raw_html, flags=re.IGNORECASE
    )
    if json_ld_match:
        return _parse_datetime_utc(json_ld_match.group(1))
    return None


def _canonicalize_factset_url(source_url: str) -> str:
    parsed = urllib.parse.urlsplit(source_url.strip())
    scheme = parsed.scheme.lower() or "https"
    host = parsed.netloc.lower()
    if not host and parsed.path:
        parsed = urllib.parse.urlsplit(f"https://{parsed.path}")
        scheme = parsed.scheme.lower()
        host = parsed.netloc.lower()
    if host != FACTSET_INSIGHT_HOST:
        raise ValueError(f"Only public {FACTSET_INSIGHT_HOST} pages are accepted")
    path = re.sub(r"/{2,}", "/", parsed.path).rstrip("/") or "/"
    return urllib.parse.urlunsplit((scheme, host, path, "", ""))


def _next_weekday(value: date) -> date:
    candidate = value + timedelta(days=1)
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate


def _previous_named_weekday(value: date, weekday: int) -> date:
    delta = (value.weekday() - weekday) % 7
    if delta == 0:
        delta = 7
    return value - timedelta(days=delta)


def _month_number(month_name: str) -> int:
    return datetime.strptime(month_name, "%B").month


def _parse_number(value: str) -> float:
    return float(value.replace(",", "").strip())


def _published_increment(number_text: str) -> float:
    decimals = len(number_text.partition(".")[2]) if "." in number_text else 0
    return 10.0 ** (-decimals)


def _factset_article_matches_index(
    index_id: str,
    title: str,
    plain_text: str,
) -> bool:
    if index_id not in FACTSET_INDEX_RELEASE_REGISTRY:
        raise ValueError(f"Unknown FactSet index registry id: {index_id}")
    registry = FACTSET_INDEX_RELEASE_REGISTRY[index_id]
    searchable = f"{title} {plain_text[:5000]}".lower()
    return any(alias in searchable for alias in registry["aliases"])


def extract_factset_article_document(
    *,
    index_id: str,
    source_url: str,
    raw_html: str,
    retrieved_ts_utc: datetime | None = None,
    publication_ts_utc: datetime | None = None,
) -> FactSetArticleDocument:
    """Normalize one public FactSet page without assigning valuation meaning."""
    canonical_url = _canonicalize_factset_url(source_url)
    retrieved = retrieved_ts_utc or datetime.now(tz=UTC)
    _require_utc("retrieved_ts_utc", retrieved)
    extracted_publication = publication_ts_utc or _extract_publication_timestamp(
        raw_html
    )
    date_precision_only = extracted_publication is None
    if extracted_publication is None:
        extracted_publication = datetime.combine(
            retrieved.date(), datetime_time(23, 59, 59), tzinfo=UTC
        )
    _require_utc("publication_ts_utc", extracted_publication)
    if retrieved < extracted_publication:
        raise ValueError("retrieved_ts_utc cannot precede publication_ts_utc")
    plain_text = _strip_html_to_text(raw_html)
    title = _extract_html_title(raw_html)
    if not _factset_article_matches_index(index_id, title, plain_text):
        raise ValueError(f"FactSet page does not match registry aliases for {index_id}")
    return FactSetArticleDocument(
        index_id=index_id,
        source_url=source_url,
        canonical_url=canonical_url,
        title=title,
        publication_ts_utc=extracted_publication,
        retrieved_ts_utc=retrieved,
        date_precision_only=date_precision_only,
        raw_document_hash=hashlib.sha256(raw_html.encode("utf-8")).hexdigest(),
        raw_html=raw_html,
        plain_text=plain_text,
    )


def _extract_factset_forward_pe(
    plain_text: str,
) -> tuple[float | None, float, bool, str | None, tuple[int, int] | None]:
    for pattern_id, pattern in FACTSET_FORWARD_PE_PATTERNS:
        match = re.search(pattern, plain_text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            value_text = match.group("value")
            approximate = bool((match.groupdict().get("approx") or "").strip())
            return (
                _parse_number(value_text),
                _published_increment(value_text),
                approximate,
                pattern_id,
                match.span(),
            )
    return None, DEFAULT_PUBLISHED_PE_INCREMENT, False, None, None


def _extract_factset_price_and_eps(
    plain_text: str,
) -> tuple[float | None, float | None, str | None, tuple[int, int] | None]:
    for pattern_id, pattern in FACTSET_PRICE_EPS_PATTERNS:
        match = re.search(pattern, plain_text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return (
                _parse_number(match.group("price")),
                _parse_number(match.group("eps")),
                pattern_id,
                match.span(),
            )
    return None, None, None, None


def _factset_extraction_excerpt(
    plain_text: str,
    spans: Sequence[tuple[int, int] | None],
    radius: int = 260,
) -> str | None:
    valid_spans = [span for span in spans if span is not None]
    if not valid_spans:
        return None
    start = max(0, min(span[0] for span in valid_spans) - radius)
    end = min(len(plain_text), max(span[1] for span in valid_spans) + radius)
    return _normalize_whitespace(plain_text[start:end])


def _infer_factset_source_as_of_date(
    excerpt: str | None,
    publication_date: date,
) -> tuple[date, str]:
    context = excerpt or ""
    month_match = re.search(
        rf"(?:as\s+of|on|dated?)\s+{FACTSET_DATE_MONTH_PATTERN}",
        context,
        flags=re.IGNORECASE,
    )
    if month_match:
        year = int(month_match.group("year") or publication_date.year)
        inferred = date(
            year,
            _month_number(month_match.group("month").title()),
            int(month_match.group("day")),
        )
        if inferred > publication_date:
            inferred = inferred.replace(year=inferred.year - 1)
        return inferred, "explicit_article_date"
    weekday_map = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
    }
    weekday_match = re.search(
        r"(Monday|Tuesday|Wednesday|Thursday|Friday)[’']s\s+closing\s+price",
        context,
        flags=re.IGNORECASE,
    )
    if weekday_match:
        weekday = weekday_map[weekday_match.group(1).lower()]
        return _previous_named_weekday(publication_date, weekday), "named_weekday_close"
    return publication_date, "publication_date_proxy"


def parse_factset_forward_valuation(
    document: FactSetArticleDocument,
    *,
    external_index_level: float | None = None,
    external_index_level_date: date | None = None,
) -> FactSetValuationCandidate:
    """Extract a conservative candidate; only complete cutoff-aligned rows promote."""
    registry = FACTSET_INDEX_RELEASE_REGISTRY[document.index_id]
    pe, increment, approximate, pe_pattern, pe_span = _extract_factset_forward_pe(
        document.plain_text
    )
    article_price, reported_eps, price_eps_pattern, price_eps_span = (
        _extract_factset_price_and_eps(document.plain_text)
    )
    excerpt = _factset_extraction_excerpt(
        document.plain_text, (pe_span, price_eps_span)
    )
    source_as_of_date, source_date_basis = _infer_factset_source_as_of_date(
        excerpt, document.publication_ts_utc.date()
    )
    warnings: list[str] = []
    if source_date_basis == "publication_date_proxy":
        warnings.append("source_as_of_date_inferred_from_publication_date")
    if document.date_precision_only:
        warnings.append("publication_time_date_precision_only")
    anchor_price_source = "missing"
    price_cutoff_status = "date_only"
    selected_index_level = article_price
    if article_price is not None:
        anchor_price_source = "factset_article"
        price_cutoff_status = (
            "exact" if source_date_basis != "publication_date_proxy" else "date_only"
        )
    elif external_index_level is not None:
        _require_positive("external_index_level", external_index_level, False)
        selected_index_level = external_index_level
        anchor_price_source = "external_market_close"
        if external_index_level_date == source_as_of_date:
            price_cutoff_status = (
                "external_same_close"
                if source_date_basis != "publication_date_proxy"
                else "date_only"
            )
        else:
            price_cutoff_status = "mismatch"
            warnings.append("external_price_date_mismatch")
    else:
        warnings.append("same_cutoff_index_level_missing")

    if approximate:
        warnings.append("published_forward_pe_is_approximate")
    confidence = 0.0
    if pe is not None:
        confidence += 0.40
    if reported_eps is not None:
        confidence += 0.20
    if selected_index_level is not None:
        confidence += 0.20
    if source_date_basis != "publication_date_proxy":
        confidence += 0.10
    if not document.date_precision_only:
        confidence += 0.05
    if _factset_article_matches_index(
        document.index_id, document.title, document.plain_text
    ):
        confidence += 0.10
    if approximate:
        confidence -= 0.05
    confidence = max(0.0, min(1.0, confidence))

    if pe is None and reported_eps is None:
        extraction_status = "no_forward_valuation_found"
    elif selected_index_level is None:
        extraction_status = "needs_same_cutoff_index_level"
    elif price_cutoff_status == "mismatch":
        extraction_status = "quarantine_cutoff_mismatch"
    elif price_cutoff_status == "date_only":
        extraction_status = "review_date_only_cutoff"
    elif confidence < FACTSET_EXTRACTION_MIN_CONFIDENCE:
        extraction_status = "review_low_confidence"
    elif reported_eps is not None:
        extraction_status = "ready_reported_eps"
    else:
        extraction_status = "ready_implied_eps"

    pattern_parts = [part for part in (pe_pattern, price_eps_pattern) if part]
    return FactSetValuationCandidate(
        index_id=document.index_id,
        source_url=document.source_url,
        canonical_url=document.canonical_url,
        title=document.title,
        publication_ts_utc=document.publication_ts_utc,
        retrieved_ts_utc=document.retrieved_ts_utc,
        date_precision_only=document.date_precision_only,
        source_as_of_date=source_as_of_date,
        available_from_date=_next_weekday(document.publication_ts_utc.date()),
        horizon=registry["expected_horizon"],
        earnings_basis=registry["earnings_basis"],
        published_forward_pe=pe,
        forward_eps_points_reported=reported_eps,
        index_level_anchor=selected_index_level,
        published_forward_pe_increment=increment,
        is_approximate=approximate,
        anchor_price_source=anchor_price_source,
        price_cutoff_status=price_cutoff_status,
        raw_document_hash=document.raw_document_hash,
        extraction_pattern_id="+".join(pattern_parts) or None,
        extraction_excerpt=excerpt,
        extraction_confidence=confidence,
        extraction_status=extraction_status,
        extraction_warnings=tuple(sorted(set(warnings))),
    )


def factset_candidate_to_index_observation(
    candidate: FactSetValuationCandidate,
) -> IndexReleaseObservation:
    """Promote only a parser candidate that passed source and cutoff gates."""
    if not candidate.extraction_status.startswith("ready_"):
        raise ValueError(
            f"FactSet candidate is not promotion-ready: {candidate.extraction_status}"
        )
    if candidate.index_level_anchor is None:
        raise ValueError("Promotion-ready candidate unexpectedly lacks index level")
    return IndexReleaseObservation(
        index_id=candidate.index_id,
        provider="FactSet Insight public release",
        source_as_of_date=candidate.source_as_of_date,
        release_ts_utc=candidate.publication_ts_utc,
        retrieved_ts_utc=candidate.retrieved_ts_utc,
        available_from_date=candidate.available_from_date,
        horizon=candidate.horizon,
        earnings_basis=candidate.earnings_basis,
        index_level_anchor=candidate.index_level_anchor,
        source_url=candidate.canonical_url,
        raw_document_hash=candidate.raw_document_hash,
        published_forward_pe=candidate.published_forward_pe,
        forward_eps_points_reported=candidate.forward_eps_points_reported,
        published_forward_pe_increment=candidate.published_forward_pe_increment,
        is_approximate=candidate.is_approximate,
        anchor_price_source=candidate.anchor_price_source,
        price_cutoff_status=candidate.price_cutoff_status,
        index_weighting_method="provider_published",
        aggregation_method="provider_published",
    )


def discover_factset_article_urls(
    discovery_document: str,
    *,
    base_url: str,
    index_id: str | None = None,
) -> list[str]:
    """Discover canonical FactSet article URLs from sitemap XML or listing HTML."""
    candidates: list[str] = []
    candidates.extend(
        html.unescape(value)
        for value in re.findall(
            r"<loc\b[^>]*>(.*?)</loc>",
            discovery_document,
            flags=re.IGNORECASE | re.DOTALL,
        )
    )
    candidates.extend(
        html.unescape(value)
        for value in re.findall(
            r"href\s*=\s*[\"']([^\"']+)[\"']",
            discovery_document,
            flags=re.IGNORECASE,
        )
    )
    registry = FACTSET_INDEX_RELEASE_REGISTRY.get(index_id) if index_id else None
    urls: list[str] = []
    for candidate in candidates:
        absolute = urllib.parse.urljoin(base_url, candidate.strip())
        try:
            canonical = _canonicalize_factset_url(absolute)
        except ValueError:
            continue
        path = urllib.parse.urlsplit(canonical).path.lower()
        if path in {"/", "/topic/earnings", "/sitemap.xml", "/hs-sitemap.xml"}:
            continue
        if path.startswith(("/hubfs/", "/_hcms/", "/favicon")):
            continue
        if registry and not any(token in path for token in registry["slug_tokens"]):
            continue
        urls.append(canonical)
    return sorted(set(urls))[:FACTSET_MAX_DISCOVERED_URLS_PER_INDEX]


def _robots_allows_url(source_url: str) -> bool:
    if not FACTSET_RESPECT_ROBOTS_TXT:
        return True
    parsed = urllib.parse.urlsplit(source_url)
    robots_url = urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, "/robots.txt", "", "")
    )
    parser = urllib.robotparser.RobotFileParser()
    parser.set_url(robots_url)
    try:
        parser.read()
    except (OSError, urllib.error.URLError):
        return False
    return parser.can_fetch(FACTSET_HTTP_USER_AGENT, source_url)


def fetch_public_factset_document(source_url: str) -> str:
    """Fetch one allowed public FactSet page with bounded retries and backoff."""
    canonical_url = _canonicalize_factset_url(source_url)
    if not _robots_allows_url(canonical_url):
        raise PermissionError(f"robots.txt does not allow fetching {canonical_url}")
    request = urllib.request.Request(
        canonical_url,
        headers={"User-Agent": FACTSET_HTTP_USER_AGENT, "Accept": "text/html,*/*"},
    )
    last_error: Exception | None = None
    for attempt in range(FACTSET_HTTP_RETRY_COUNT):
        try:
            with urllib.request.urlopen(
                request, timeout=FACTSET_HTTP_TIMEOUT_SECONDS
            ) as response:
                content_type = response.headers.get_content_type()
                if content_type not in {"text/html", "application/xml", "text/xml"}:
                    raise ValueError(f"Unsupported FactSet content type: {content_type}")
                charset = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(charset, errors="replace")
        except (OSError, ValueError, urllib.error.URLError) as exc:
            last_error = exc
            if attempt + 1 < FACTSET_HTTP_RETRY_COUNT:
                time.sleep(FACTSET_HTTP_BACKOFF_SECONDS * (2**attempt))
    raise RuntimeError(f"FactSet fetch failed after retries: {canonical_url}") from last_error


def crawl_factset_release_batch(
    release_requests: Sequence[Mapping[str, Any]],
    *,
    known_document_hashes: Iterable[str] = (),
    fetcher: Callable[[str], str] = fetch_public_factset_document,
    retrieved_ts_utc: datetime | None = None,
) -> dict[str, pd.DataFrame]:
    """Fetch, parse, de-duplicate and promote a deterministic request batch."""
    retrieval_time = retrieved_ts_utc or datetime.now(tz=UTC)
    _require_utc("retrieved_ts_utc", retrieval_time)
    known_hashes = set(known_document_hashes)
    candidate_rows: list[dict[str, Any]] = []
    anchor_rows: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []
    for request_number, item in enumerate(release_requests):
        index_id = str(item["index_id"])
        source_url = str(item["source_url"])
        try:
            raw_html = fetcher(source_url)
            document = extract_factset_article_document(
                index_id=index_id,
                source_url=source_url,
                raw_html=raw_html,
                retrieved_ts_utc=retrieval_time,
                publication_ts_utc=item.get("publication_ts_utc"),
            )
            if document.raw_document_hash in known_hashes:
                audit_rows.append(
                    {
                        "request_number": request_number,
                        "index_id": index_id,
                        "source_url": document.canonical_url,
                        "raw_document_hash": document.raw_document_hash,
                        "status": "skipped_idempotent_document_hash",
                        "message": None,
                    }
                )
                continue
            candidate = parse_factset_forward_valuation(
                document,
                external_index_level=item.get("external_index_level"),
                external_index_level_date=item.get("external_index_level_date"),
            )
            candidate_rows.append(asdict(candidate))
            if candidate.extraction_status.startswith("ready_"):
                anchor_rows.append(
                    build_index_anchor(factset_candidate_to_index_observation(candidate))
                )
                status = "promoted_to_anchor"
            else:
                status = candidate.extraction_status
            known_hashes.add(document.raw_document_hash)
            audit_rows.append(
                {
                    "request_number": request_number,
                    "index_id": index_id,
                    "source_url": document.canonical_url,
                    "raw_document_hash": document.raw_document_hash,
                    "status": status,
                    "message": None,
                }
            )
        except Exception as exc:
            audit_rows.append(
                {
                    "request_number": request_number,
                    "index_id": index_id,
                    "source_url": source_url,
                    "raw_document_hash": None,
                    "status": "failed",
                    "message": f"{type(exc).__name__}: {exc}",
                }
            )
        if request_number + 1 < len(release_requests):
            time.sleep(FACTSET_REQUEST_INTERVAL_SECONDS)
    return {
        "candidates": pd.DataFrame(candidate_rows),
        "anchors": pd.DataFrame(anchor_rows),
        "audit": pd.DataFrame(audit_rows),
    }


def _parse_optional_date_value(value: Any) -> date | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value).strip())


def _parse_optional_datetime_value(value: Any) -> datetime | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = _parse_datetime_utc(str(value))
        if parsed is None:
            raise ValueError(f"Invalid ISO timestamp: {value!r}")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def load_factset_release_requests(request_file: str | Path) -> list[dict[str, Any]]:
    """Load a JSON, JSONL or CSV intake file and normalize optional timestamps."""
    path = Path(request_file)
    if not path.exists():
        raise FileNotFoundError(path)
    suffix = path.suffix.lower()
    if suffix == ".json":
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        records = payload["requests"] if isinstance(payload, dict) else payload
    elif suffix in {".jsonl", ".ndjson"}:
        records = [
            json.loads(line)
            for line in path.read_text(encoding="utf-8-sig").splitlines()
            if line.strip()
        ]
    elif suffix == ".csv":
        records = pd.read_csv(path, encoding="utf-8-sig").to_dict(orient="records")
    else:
        raise ValueError("FactSet request file must be .json, .jsonl, .ndjson or .csv")
    if not isinstance(records, list):
        raise ValueError("FactSet request payload must be a list or {'requests': [...]} object")
    normalized: list[dict[str, Any]] = []
    for row_number, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise ValueError(f"Request row {row_number} is not an object")
        if not record.get("index_id") or not record.get("source_url"):
            raise ValueError(f"Request row {row_number} needs index_id and source_url")
        index_id = str(record["index_id"])
        if index_id not in FACTSET_INDEX_RELEASE_REGISTRY:
            raise ValueError(f"Request row {row_number} has unknown index_id: {index_id}")
        external_level = record.get("external_index_level")
        if external_level is not None and not pd.isna(external_level):
            external_level = float(external_level)
        else:
            external_level = None
        normalized.append(
            {
                "index_id": index_id,
                "source_url": str(record["source_url"]),
                "external_index_level": external_level,
                "external_index_level_date": _parse_optional_date_value(
                    record.get("external_index_level_date")
                ),
                "publication_ts_utc": _parse_optional_datetime_value(
                    record.get("publication_ts_utc")
                ),
            }
        )
    return normalized


def load_known_factset_document_hashes(output_root: str | Path) -> set[str]:
    """Read only the hash column from existing immutable candidate parts."""
    candidate_dir = Path(output_root) / "candidates"
    hashes: set[str] = set()
    for part_path in sorted(candidate_dir.glob("part-*.parquet")):
        part = pd.read_parquet(part_path, columns=["raw_document_hash"])
        hashes.update(part["raw_document_hash"].dropna().astype(str))
    return hashes


def _normalize_factset_output_frame(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = frame.copy()
    for column in normalized.select_dtypes(include=["object"]).columns:
        normalized[column] = normalized[column].map(
            lambda value: json.dumps(
                sorted(value) if isinstance(value, set) else value,
                ensure_ascii=False,
                default=_json_default,
            )
            if isinstance(value, (dict, list, tuple, set))
            else value
        )
    return normalized


def persist_factset_ingestion_batch(
    batch: Mapping[str, pd.DataFrame],
    output_root: str | Path,
) -> dict[str, Any]:
    """Persist candidate, anchor and audit tables as separate append-only datasets."""
    root = Path(output_root)
    results: dict[str, Any] = {}
    for table_name in ("candidates", "anchors", "audit"):
        frame = _normalize_factset_output_frame(batch[table_name])
        results[table_name] = append_immutable_parquet_part(
            frame,
            root / table_name,
            f"factset_public_release_{table_name}",
        )
    if duckdb is None:
        results["duckdb"] = {
            "status": "skipped_dependency_missing",
            "message": "Install duckdb in the active VIA environment to refresh views",
        }
    else:
        database_path = root / "factset_public_releases.duckdb"
        view_rows: dict[str, int] = {}
        for table_name in ("candidates", "anchors", "audit"):
            if list((root / table_name).glob("part-*.parquet")):
                view_rows[table_name] = refresh_duckdb_view(
                    database_path,
                    f"factset_{table_name}",
                    root / table_name,
                )
        results["duckdb"] = {"status": "refreshed", "view_rows": view_rows}
    return results


def run_factset_ingestion_file(
    request_file: str | Path,
    output_root: str | Path = DEFAULT_FACTSET_OUTPUT_ROOT,
) -> dict[str, Any]:
    """Operational entrypoint for incremental public-release ingestion."""
    requests = load_factset_release_requests(request_file)
    known_hashes = load_known_factset_document_hashes(output_root)
    batch = crawl_factset_release_batch(
        requests,
        known_document_hashes=known_hashes,
    )
    writes = persist_factset_ingestion_batch(batch, output_root)
    return {
        "status": "completed",
        "request_rows": len(requests),
        "candidate_rows": len(batch["candidates"]),
        "anchor_rows": len(batch["anchors"]),
        "audit_rows": len(batch["audit"]),
        "writes": writes,
    }


def _require_positive(name: str, value: float | None, allow_none: bool = True) -> None:
    if value is None and allow_none:
        return
    if value is None or value <= 0:
        raise ValueError(f"{name} must be positive; received {value!r}")


def _require_utc(name: str, value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{name} must be timezone-aware UTC")


def _stable_id(prefix: str, values: Iterable[Any]) -> str:
    payload = "|".join("" if value is None else str(value) for value in values)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]
    return f"{prefix}_{digest}"


def _validate_common_release_fields(
    *,
    horizon: str,
    earnings_basis: str,
    release_ts_utc: datetime,
    retrieved_ts_utc: datetime,
    available_from_date: date,
) -> None:
    if horizon not in ALLOWED_HORIZONS:
        raise ValueError(f"Unsupported horizon: {horizon}")
    if earnings_basis not in ALLOWED_EARNINGS_BASIS:
        raise ValueError(f"Unsupported earnings basis: {earnings_basis}")
    _require_utc("release_ts_utc", release_ts_utc)
    _require_utc("retrieved_ts_utc", retrieved_ts_utc)
    if retrieved_ts_utc < release_ts_utc:
        raise ValueError("retrieved_ts_utc cannot precede release_ts_utc")
    if available_from_date < release_ts_utc.date():
        raise ValueError("available_from_date cannot precede the release date")


def calculate_rounding_interval(
    index_level: float,
    published_forward_pe: float,
    published_increment: float = DEFAULT_PUBLISHED_PE_INCREMENT,
    is_approximate: bool = False,
) -> dict[str, float]:
    """Propagate a rounded or approximate published P/E into an EPS interval."""
    _require_positive("index_level", index_level, False)
    _require_positive("published_forward_pe", published_forward_pe, False)
    _require_positive("published_increment", published_increment, False)
    multiplier = APPROXIMATE_PE_HALF_WIDTH_MULTIPLIER if is_approximate else 0.5
    pe_half_width = published_increment * multiplier
    pe_lower = published_forward_pe - pe_half_width
    pe_upper = published_forward_pe + pe_half_width
    if pe_lower <= 0:
        raise ValueError("Published P/E interval crosses zero")
    eps_central = index_level / published_forward_pe
    eps_lower = index_level / pe_upper
    eps_upper = index_level / pe_lower
    relative_half_width = (eps_upper - eps_lower) / (2.0 * eps_central)
    return {
        "published_forward_pe_lower": pe_lower,
        "published_forward_pe_upper": pe_upper,
        "forward_eps_points_interval_lower": eps_lower,
        "forward_eps_points_interval_upper": eps_upper,
        "rounding_relative_half_width": relative_half_width,
    }


def calculate_anchor_readiness(
    *,
    value_origin: str,
    quality_status: str,
    price_cutoff_status: str,
    is_approximate: bool,
    mapping_quality: str | None = None,
    holdings_market_value_coverage: float | None = None,
) -> dict[str, Any]:
    """Return a transparent score and readiness label; do not blend source values."""
    score = 100
    blockers: list[str] = []
    if value_origin in {"calculated_not_original", "index_mapped_proxy"}:
        score -= 12 if value_origin == "calculated_not_original" else 25
    if is_approximate:
        score -= 8
    if price_cutoff_status == "external_same_close":
        score -= 5
    elif price_cutoff_status == "date_only":
        score -= 12
    elif price_cutoff_status == "mismatch":
        score -= 40
        blockers.append("price_cutoff_mismatch")
    if mapping_quality == "near_exact":
        score -= 15
    elif mapping_quality == "proxy":
        score -= 30
        blockers.append("proxy_benchmark_mismatch")
    if holdings_market_value_coverage is not None:
        if holdings_market_value_coverage < MIN_HOLDINGS_MARKET_VALUE_COVERAGE:
            score -= 20
            blockers.append("insufficient_holdings_coverage")
    if quality_status == "warning":
        score -= 10
    elif quality_status == "quarantine":
        score = min(score, 39)
        blockers.append("quality_quarantine")
    score = max(0, min(100, score))
    if blockers or score < 60:
        readiness = "quarantine"
    elif score < 80:
        readiness = "screen_grade"
    else:
        readiness = "research_grade"
    return {
        "confidence_score": score,
        "readiness": readiness,
        "readiness_blockers": blockers,
    }


def build_index_anchor(
    observation: IndexReleaseObservation,
    relative_tolerance: float = INDEX_EPS_RELATIVE_TOLERANCE,
) -> dict[str, Any]:
    """Validate one index release and return a normalized immutable anchor."""
    _validate_common_release_fields(
        horizon=observation.horizon,
        earnings_basis=observation.earnings_basis,
        release_ts_utc=observation.release_ts_utc,
        retrieved_ts_utc=observation.retrieved_ts_utc,
        available_from_date=observation.available_from_date,
    )
    _require_positive("index_level_anchor", observation.index_level_anchor, False)
    _require_positive("published_forward_pe", observation.published_forward_pe)
    _require_positive(
        "forward_eps_points_reported", observation.forward_eps_points_reported
    )
    _require_positive(
        "float_adjusted_market_cap", observation.float_adjusted_market_cap
    )
    _require_positive("published_pb", observation.published_pb)
    _require_positive(
        "published_forward_pe_increment",
        observation.published_forward_pe_increment,
        False,
    )
    if observation.price_cutoff_status not in ALLOWED_PRICE_CUTOFF_STATUS:
        raise ValueError(
            f"Unsupported price_cutoff_status: {observation.price_cutoff_status}"
        )
    if observation.index_weighting_method not in ALLOWED_INDEX_WEIGHTING_METHODS:
        raise ValueError(
            "Unsupported index_weighting_method: "
            f"{observation.index_weighting_method}"
        )

    if (
        observation.published_forward_pe is None
        and observation.forward_eps_points_reported is None
    ):
        raise ValueError("An index anchor needs forward P/E or reported forward EPS")

    implied_eps = None
    rounding_interval: dict[str, float | None] = {
        "published_forward_pe_lower": None,
        "published_forward_pe_upper": None,
        "forward_eps_points_interval_lower": None,
        "forward_eps_points_interval_upper": None,
        "rounding_relative_half_width": None,
    }
    if observation.published_forward_pe is not None:
        implied_eps = (
            observation.index_level_anchor / observation.published_forward_pe
        )
        rounding_interval = calculate_rounding_interval(
            index_level=observation.index_level_anchor,
            published_forward_pe=observation.published_forward_pe,
            published_increment=observation.published_forward_pe_increment,
            is_approximate=observation.is_approximate,
        )

    relative_gap = None
    quality_status = "pass"
    if observation.forward_eps_points_reported is not None and implied_eps is not None:
        relative_gap = abs(observation.forward_eps_points_reported - implied_eps) / (
            observation.forward_eps_points_reported
        )
        if relative_gap > relative_tolerance:
            quality_status = "quarantine"
    if observation.price_cutoff_status == "mismatch":
        quality_status = "quarantine"
    elif (
        observation.price_cutoff_status != "exact"
        and quality_status == "pass"
    ):
        quality_status = "warning"

    selected_eps = observation.forward_eps_points_reported or implied_eps
    if selected_eps is None:
        raise AssertionError("selected_eps unexpectedly missing")

    if observation.forward_eps_points_reported is not None:
        value_origin = "reported_forward_eps"
        evidence_label = "fact_source_reported"
    else:
        value_origin = "calculated_not_original"
        evidence_label = "derived_calculation"

    readiness = calculate_anchor_readiness(
        value_origin=value_origin,
        quality_status=quality_status,
        price_cutoff_status=observation.price_cutoff_status,
        is_approximate=observation.is_approximate,
    )

    earnings_value = None
    if (
        observation.float_adjusted_market_cap is not None
        and observation.published_forward_pe is not None
    ):
        earnings_value = (
            observation.float_adjusted_market_cap
            / observation.published_forward_pe
        )

    book_points = None
    book_value = None
    if observation.published_pb is not None:
        book_points = observation.index_level_anchor / observation.published_pb
        if observation.float_adjusted_market_cap is not None:
            book_value = (
                observation.float_adjusted_market_cap / observation.published_pb
            )

    vintage_id = _stable_id(
        "idxv",
        (
            observation.index_id,
            observation.provider,
            observation.source_as_of_date,
            observation.release_ts_utc.isoformat(),
            observation.horizon,
            observation.earnings_basis,
            observation.raw_document_hash,
        ),
    )

    return {
        "vintage_id": vintage_id,
        "index_id": observation.index_id,
        "provider": observation.provider,
        "source_as_of_date": observation.source_as_of_date,
        "release_ts_utc": observation.release_ts_utc,
        "retrieved_ts_utc": observation.retrieved_ts_utc,
        "available_from_date": observation.available_from_date,
        "horizon": observation.horizon,
        "earnings_basis": observation.earnings_basis,
        "index_level_anchor": observation.index_level_anchor,
        "published_forward_pe": observation.published_forward_pe,
        **rounding_interval,
        "forward_eps_points_reported": observation.forward_eps_points_reported,
        "forward_eps_points_implied": implied_eps,
        "forward_eps_points_selected": selected_eps,
        "forward_earnings_value": earnings_value,
        "published_pb": observation.published_pb,
        "book_points_implied": book_points,
        "book_value_implied": book_value,
        "value_origin": value_origin,
        "evidence_label": evidence_label,
        "currency": observation.currency,
        "anchor_price_source": observation.anchor_price_source,
        "price_cutoff_status": observation.price_cutoff_status,
        "is_approximate": observation.is_approximate,
        "published_forward_pe_increment": (
            observation.published_forward_pe_increment
        ),
        "index_weighting_method": observation.index_weighting_method,
        "aggregation_method": observation.aggregation_method,
        "source_url": observation.source_url,
        "raw_document_hash": observation.raw_document_hash,
        "methodology_version": METHODOLOGY_VERSION,
        "relative_eps_gap": relative_gap,
        "quality_status": quality_status,
        **readiness,
        "max_stale_days": observation.max_stale_days,
    }


def build_etf_anchor(observation: ETFReleaseObservation) -> dict[str, Any]:
    """Validate one ETF release and return an ETF-specific EPS/share anchor."""
    _validate_common_release_fields(
        horizon=observation.horizon,
        earnings_basis=observation.earnings_basis,
        release_ts_utc=observation.release_ts_utc,
        retrieved_ts_utc=observation.retrieved_ts_utc,
        available_from_date=observation.available_from_date,
    )
    _require_positive("nav_per_share_anchor", observation.nav_per_share_anchor, False)
    _require_positive("market_close_anchor", observation.market_close_anchor)
    _require_positive("portfolio_forward_pe", observation.portfolio_forward_pe)
    _require_positive(
        "mapped_index_forward_pe", observation.mapped_index_forward_pe
    )

    if observation.mapping_quality is not None:
        if observation.mapping_quality not in ALLOWED_MAPPING_QUALITY:
            raise ValueError(
                f"Unsupported mapping_quality: {observation.mapping_quality}"
            )
    if observation.nav_valuation_method not in ALLOWED_NAV_VALUATION_METHODS:
        raise ValueError(
            f"Unsupported nav_valuation_method: {observation.nav_valuation_method}"
        )
    if observation.cutoff_alignment not in ALLOWED_CUTOFF_ALIGNMENT:
        raise ValueError(
            f"Unsupported cutoff_alignment: {observation.cutoff_alignment}"
        )
    if observation.fx_as_of_ts_utc is not None:
        _require_utc("fx_as_of_ts_utc", observation.fx_as_of_ts_utc)

    if observation.portfolio_forward_pe is not None:
        selected_pe = observation.portfolio_forward_pe
        value_origin = "etf_source_reported_forward_pe"
        evidence_label = "fact_provider_standardized"
        quality_status = "pass"
    elif observation.mapped_index_forward_pe is not None:
        if observation.mapped_index_id is None or observation.mapping_quality is None:
            raise ValueError(
                "Index-mapped ETF proxy needs mapped_index_id and mapping_quality"
            )
        selected_pe = observation.mapped_index_forward_pe
        value_origin = "index_mapped_proxy"
        evidence_label = "derived_calculation"
        quality_status = (
            "warning" if observation.mapping_quality == "exact" else "quarantine"
        )
    else:
        raise ValueError(
            "An ETF anchor needs portfolio forward P/E or mapped index forward P/E"
        )

    if observation.cutoff_alignment in {"stale_local_close", "unknown"}:
        quality_status = "quarantine"
    elif (
        observation.cutoff_alignment == "fair_value_adjusted"
        and quality_status == "pass"
    ):
        quality_status = "warning"

    forward_eps_per_share = observation.nav_per_share_anchor / selected_pe
    readiness = calculate_anchor_readiness(
        value_origin=value_origin,
        quality_status=quality_status,
        price_cutoff_status=(
            "exact"
            if observation.cutoff_alignment == "same_cutoff"
            else "external_same_close"
            if observation.cutoff_alignment == "fair_value_adjusted"
            else "mismatch"
        ),
        is_approximate=False,
        mapping_quality=observation.mapping_quality,
    )
    vintage_id = _stable_id(
        "etfv",
        (
            observation.ticker,
            observation.provider,
            observation.source_as_of_date,
            observation.release_ts_utc.isoformat(),
            observation.horizon,
            observation.earnings_basis,
            observation.raw_document_hash,
        ),
    )

    return {
        "vintage_id": vintage_id,
        "ticker": observation.ticker,
        "mapped_index_id": observation.mapped_index_id,
        "mapping_quality": observation.mapping_quality,
        "provider": observation.provider,
        "source_as_of_date": observation.source_as_of_date,
        "release_ts_utc": observation.release_ts_utc,
        "retrieved_ts_utc": observation.retrieved_ts_utc,
        "available_from_date": observation.available_from_date,
        "horizon": observation.horizon,
        "earnings_basis": observation.earnings_basis,
        "nav_per_share_anchor": observation.nav_per_share_anchor,
        "market_close_anchor": observation.market_close_anchor,
        "portfolio_forward_pe": observation.portfolio_forward_pe,
        "mapped_index_forward_pe": observation.mapped_index_forward_pe,
        "forward_eps_per_share": forward_eps_per_share,
        "value_origin": value_origin,
        "evidence_label": evidence_label,
        "nav_valuation_method": observation.nav_valuation_method,
        "cutoff_alignment": observation.cutoff_alignment,
        "holdings_as_of_date": observation.holdings_as_of_date,
        "fx_as_of_ts_utc": observation.fx_as_of_ts_utc,
        "source_url": observation.source_url,
        "raw_document_hash": observation.raw_document_hash,
        "methodology_version": METHODOLOGY_VERSION,
        "quality_status": quality_status,
        **readiness,
        "max_stale_days": observation.max_stale_days,
    }


def _prepare_asof_inputs(
    observations: pd.DataFrame,
    anchors: pd.DataFrame,
    entity_column: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    obs = observations.copy()
    anc = anchors.copy()
    # pandas 3.x 會依來源給出不同 datetime64 單位(s/us/ns);merge_asof 要求同型,統一鎖 ns。
    obs["observation_date"] = pd.to_datetime(obs["observation_date"]).astype("datetime64[ns]")
    anc["available_from_date"] = pd.to_datetime(anc["available_from_date"]).astype("datetime64[ns]")
    anc["source_as_of_date"] = pd.to_datetime(anc["source_as_of_date"]).astype("datetime64[ns]")
    obs = obs.sort_values([entity_column, "observation_date"]).reset_index(drop=True)
    anc = anc.sort_values([entity_column, "available_from_date"]).reset_index(drop=True)
    return obs, anc


def apply_index_vintages(
    daily_index_levels: pd.DataFrame,
    index_anchors: pd.DataFrame,
) -> pd.DataFrame:
    """Attach the latest available anchor and compute price-only index P/E."""
    obs, anc = _prepare_asof_inputs(
        daily_index_levels, index_anchors, entity_column="index_id"
    )
    result_parts: list[pd.DataFrame] = []
    for index_id, group in obs.groupby("index_id", sort=False):
        entity_anchors = anc.loc[anc["index_id"] == index_id]
        if entity_anchors.empty:
            continue
        merged = pd.merge_asof(
            group.sort_values("observation_date"),
            entity_anchors.sort_values("available_from_date"),
            left_on="observation_date",
            right_on="available_from_date",
            direction="backward",
            suffixes=("", "_anchor"),
        )
        result_parts.append(merged)
    if not result_parts:
        return pd.DataFrame()

    result = pd.concat(result_parts, ignore_index=True)
    result = result.loc[result["vintage_id"].notna()].copy()
    _require_columns(result, ["index_level", "forward_eps_points_selected"])
    if (result["index_level"] <= 0).any():
        raise ValueError("daily index_level must be positive")
    result["frozen_forward_eps_points"] = result[
        "forward_eps_points_selected"
    ]
    result["price_only_forward_pe"] = (
        result["index_level"] / result["frozen_forward_eps_points"]
    )
    result["forward_earnings_yield"] = 1.0 / result["price_only_forward_pe"]
    result["stale_days"] = (
        result["observation_date"] - result["source_as_of_date"]
    ).dt.days
    result["is_stale"] = result["stale_days"] > result["max_stale_days"]
    return result.sort_values(["index_id", "observation_date"]).reset_index(
        drop=True
    )


def apply_etf_vintages(
    daily_etf_prices: pd.DataFrame,
    etf_anchors: pd.DataFrame,
) -> pd.DataFrame:
    """Attach the latest ETF anchor and compute NAV and market-price P/E."""
    obs, anc = _prepare_asof_inputs(
        daily_etf_prices, etf_anchors, entity_column="ticker"
    )
    result_parts: list[pd.DataFrame] = []
    for ticker, group in obs.groupby("ticker", sort=False):
        entity_anchors = anc.loc[anc["ticker"] == ticker]
        if entity_anchors.empty:
            continue
        merged = pd.merge_asof(
            group.sort_values("observation_date"),
            entity_anchors.sort_values("available_from_date"),
            left_on="observation_date",
            right_on="available_from_date",
            direction="backward",
            suffixes=("", "_anchor"),
        )
        result_parts.append(merged)
    if not result_parts:
        return pd.DataFrame()

    result = pd.concat(result_parts, ignore_index=True)
    result = result.loc[result["vintage_id"].notna()].copy()
    _require_columns(
        result,
        ["nav_per_share", "market_close", "forward_eps_per_share"],
    )
    if (result[["nav_per_share", "market_close"]] <= 0).any().any():
        raise ValueError("daily ETF NAV and market_close must be positive")
    result["frozen_forward_eps_per_share"] = result["forward_eps_per_share"]
    result["nav_forward_pe"] = (
        result["nav_per_share"] / result["frozen_forward_eps_per_share"]
    )
    result["market_forward_pe"] = (
        result["market_close"] / result["frozen_forward_eps_per_share"]
    )
    result["premium_discount"] = (
        result["market_close"] / result["nav_per_share"] - 1.0
    )
    result["stale_days"] = (
        result["observation_date"] - result["source_as_of_date"]
    ).dt.days
    result["is_stale"] = result["stale_days"] > result["max_stale_days"]
    return result.sort_values(["ticker", "observation_date"]).reset_index(
        drop=True
    )


def estimate_dynamic_stale_days(
    release_dates: Sequence[date | datetime | str],
    fallback_days: int = DEFAULT_INDEX_STALE_DAYS,
    multiplier: float = DYNAMIC_STALE_MULTIPLIER,
    minimum_days: int = DYNAMIC_STALE_MIN_DAYS,
    maximum_days: int = DYNAMIC_STALE_MAX_DAYS,
) -> int:
    """Estimate a source-specific stale threshold from historical release cadence."""
    if multiplier <= 0 or minimum_days <= 0 or maximum_days < minimum_days:
        raise ValueError("Invalid dynamic staleness parameters")
    parsed = pd.Series(pd.to_datetime(list(release_dates))).dropna().drop_duplicates()
    parsed = parsed.sort_values()
    if len(parsed) < 2:
        return int(max(minimum_days, min(maximum_days, fallback_days)))
    intervals = parsed.diff().dt.days.dropna()
    intervals = intervals.loc[intervals > 0]
    if intervals.empty:
        return int(max(minimum_days, min(maximum_days, fallback_days)))
    threshold = int(math.ceil(float(intervals.median()) * multiplier))
    return int(max(minimum_days, min(maximum_days, threshold)))


def reconstruct_cap_weighted_forward_valuation(
    constituents: pd.DataFrame,
    market_value_column: str = "float_adjusted_market_value",
    forward_earnings_column: str = "forward_earnings_value",
    entity_id_column: str = "security_id",
) -> dict[str, Any]:
    """Reconstruct a cap-weighted P/E from aggregate value and earnings.

    Missing earnings are not treated as zero and source/provider rows are never
    averaged. The covered-only multiple is reported with explicit coverage.
    """
    _require_columns(
        constituents,
        [entity_id_column, market_value_column, forward_earnings_column],
    )
    frame = constituents.copy()
    if frame[entity_id_column].duplicated().any():
        raise ValueError("Duplicate constituent identifiers at the intended grain")
    frame[market_value_column] = pd.to_numeric(
        frame[market_value_column], errors="coerce"
    )
    frame[forward_earnings_column] = pd.to_numeric(
        frame[forward_earnings_column], errors="coerce"
    )
    if frame[market_value_column].isna().any() or (
        frame[market_value_column] < 0
    ).any():
        raise ValueError("Constituent market values must be non-negative and present")
    total_market_value = float(frame[market_value_column].sum())
    _require_positive("total_market_value", total_market_value, False)

    covered = frame[forward_earnings_column].notna()
    covered_market_value = float(frame.loc[covered, market_value_column].sum())
    covered_earnings = float(frame.loc[covered, forward_earnings_column].sum())
    market_value_coverage = covered_market_value / total_market_value
    count_coverage = float(covered.mean()) if len(frame) else 0.0
    negative_earnings_weight = float(
        frame.loc[
            covered & (frame[forward_earnings_column] < 0), market_value_column
        ].sum()
        / total_market_value
    )
    covered_forward_pe = (
        covered_market_value / covered_earnings if covered_earnings > 0 else None
    )
    full_forward_pe = (
        total_market_value / covered_earnings
        if market_value_coverage >= 1.0 - 1e-12 and covered_earnings > 0
        else None
    )
    quality_status = "pass"
    if (
        market_value_coverage < MIN_HOLDINGS_MARKET_VALUE_COVERAGE
        or count_coverage < MIN_HOLDINGS_COUNT_COVERAGE
    ):
        quality_status = "quarantine"
    elif negative_earnings_weight > MAX_NEGATIVE_EARNINGS_WEIGHT_WARNING:
        quality_status = "warning"
    readiness = calculate_anchor_readiness(
        value_origin="holdings_reconstructed",
        quality_status=quality_status,
        price_cutoff_status="exact",
        is_approximate=False,
        holdings_market_value_coverage=market_value_coverage,
    )
    return {
        "total_market_value": total_market_value,
        "covered_market_value": covered_market_value,
        "covered_forward_earnings": covered_earnings,
        "market_value_coverage": market_value_coverage,
        "count_coverage": count_coverage,
        "negative_earnings_weight": negative_earnings_weight,
        "covered_forward_pe": covered_forward_pe,
        "full_forward_pe": full_forward_pe,
        "aggregation_method": "aggregate_market_value_over_aggregate_earnings",
        "evidence_label": "derived_calculation",
        "quality_status": quality_status,
        **readiness,
    }


def reconstruct_etf_holdings_forward_valuation(
    holdings: pd.DataFrame,
    etf_shares_outstanding: float,
    security_id_column: str = "security_id",
    market_value_column: str = "market_value_fund_currency",
    quantity_column: str = "quantity",
    forward_eps_column: str = "forward_eps_local_currency",
    fx_column: str = "fx_to_fund_currency",
    equity_flag_column: str = "is_equity",
) -> dict[str, Any]:
    """Reconstruct ETF earnings from actual holdings, consensus EPS and FX."""
    _require_positive("etf_shares_outstanding", etf_shares_outstanding, False)
    required = [
        security_id_column,
        market_value_column,
        quantity_column,
        forward_eps_column,
        fx_column,
    ]
    _require_columns(holdings, required)
    frame = holdings.copy()
    if frame[security_id_column].duplicated().any():
        raise ValueError("Duplicate ETF holding identifiers at the intended grain")
    if equity_flag_column not in frame.columns:
        frame[equity_flag_column] = True
    equity = frame.loc[frame[equity_flag_column].fillna(False).astype(bool)].copy()
    if equity.empty:
        raise ValueError("No equity holdings available for reconstruction")
    for column in [market_value_column, quantity_column, forward_eps_column, fx_column]:
        equity[column] = pd.to_numeric(equity[column], errors="coerce")
    if equity[market_value_column].isna().any() or (
        equity[market_value_column] < 0
    ).any():
        raise ValueError("ETF equity market values must be non-negative and present")
    if equity[fx_column].dropna().le(0).any():
        raise ValueError("FX conversion factors must be positive")

    covered = equity[[quantity_column, forward_eps_column, fx_column]].notna().all(axis=1)
    equity["forward_earnings_fund_currency"] = np.where(
        covered,
        equity[quantity_column]
        * equity[forward_eps_column]
        * equity[fx_column],
        np.nan,
    )
    aggregate = reconstruct_cap_weighted_forward_valuation(
        constituents=equity.rename(
            columns={
                market_value_column: "float_adjusted_market_value",
                "forward_earnings_fund_currency": "forward_earnings_value",
            }
        ),
        market_value_column="float_adjusted_market_value",
        forward_earnings_column="forward_earnings_value",
        entity_id_column=security_id_column,
    )
    aggregate["covered_forward_earnings_per_etf_share"] = (
        aggregate["covered_forward_earnings"] / etf_shares_outstanding
    )
    aggregate["etf_shares_outstanding"] = etf_shares_outstanding
    aggregate["aggregation_method"] = "holdings_quantity_times_forward_eps_times_fx"
    return aggregate


def reconstruct_price_weighted_forward_valuation(
    constituents: pd.DataFrame,
    index_divisor: float,
    security_id_column: str = "security_id",
    adjusted_price_column: str = "adjusted_price",
    forward_eps_column: str = "forward_eps",
) -> dict[str, Any]:
    """Reconstruct a price-weighted index without applying cap-weighted logic."""
    _require_positive("index_divisor", index_divisor, False)
    _require_columns(
        constituents,
        [security_id_column, adjusted_price_column, forward_eps_column],
    )
    frame = constituents.copy()
    if frame[security_id_column].duplicated().any():
        raise ValueError("Duplicate constituents in price-weighted reconstruction")
    frame[adjusted_price_column] = pd.to_numeric(
        frame[adjusted_price_column], errors="coerce"
    )
    frame[forward_eps_column] = pd.to_numeric(
        frame[forward_eps_column], errors="coerce"
    )
    if frame[adjusted_price_column].isna().any() or (
        frame[adjusted_price_column] <= 0
    ).any():
        raise ValueError("Adjusted constituent prices must be positive and present")
    covered = frame[forward_eps_column].notna()
    price_coverage = float(
        frame.loc[covered, adjusted_price_column].sum()
        / frame[adjusted_price_column].sum()
    )
    index_level = float(frame[adjusted_price_column].sum() / index_divisor)
    covered_eps_points = float(
        frame.loc[covered, forward_eps_column].sum() / index_divisor
    )
    covered_forward_pe = (
        float(frame.loc[covered, adjusted_price_column].sum())
        / float(frame.loc[covered, forward_eps_column].sum())
        if float(frame.loc[covered, forward_eps_column].sum()) > 0
        else None
    )
    full_forward_pe = (
        index_level / covered_eps_points
        if price_coverage >= 1.0 - 1e-12 and covered_eps_points > 0
        else None
    )
    return {
        "index_level_reconstructed": index_level,
        "covered_forward_eps_points": covered_eps_points,
        "price_coverage": price_coverage,
        "covered_forward_pe": covered_forward_pe,
        "full_forward_pe": full_forward_pe,
        "aggregation_method": "price_weighted_sum_over_divisor",
        "quality_status": (
            "pass"
            if price_coverage >= MIN_HOLDINGS_MARKET_VALUE_COVERAGE
            else "quarantine"
        ),
        "evidence_label": "derived_calculation",
    }


def compute_vintage_revision_bridge(
    anchors: pd.DataFrame,
    entity_column: str = "index_id",
    date_column: str = "available_from_date",
    price_column: str = "index_level_anchor",
    earnings_column: str = "forward_eps_points_selected",
) -> pd.DataFrame:
    """Separate anchor-to-anchor price re-rating from forward-earnings revision."""
    _require_columns(
        anchors,
        [entity_column, date_column, price_column, earnings_column, "vintage_id"],
    )
    frame = anchors.copy()
    frame[date_column] = pd.to_datetime(frame[date_column])
    frame = frame.sort_values([entity_column, date_column]).reset_index(drop=True)
    if (frame[[price_column, earnings_column]] <= 0).any().any():
        raise ValueError("Revision bridge inputs must be positive")
    grouped = frame.groupby(entity_column, sort=False)
    frame["previous_vintage_id"] = grouped["vintage_id"].shift(1)
    frame["previous_price_anchor"] = grouped[price_column].shift(1)
    frame["previous_forward_eps"] = grouped[earnings_column].shift(1)
    frame["price_log_change"] = np.log(
        frame[price_column] / frame["previous_price_anchor"]
    )
    frame["earnings_revision_log_change"] = np.log(
        frame[earnings_column] / frame["previous_forward_eps"]
    )
    frame["forward_pe_log_change"] = (
        frame["price_log_change"] - frame["earnings_revision_log_change"]
    )
    frame["revision_only_pe_log_change"] = -frame[
        "earnings_revision_log_change"
    ]
    frame["price_only_pe_at_new_anchor_using_old_eps"] = (
        frame[price_column] / frame["previous_forward_eps"]
    )
    frame["new_anchor_forward_pe"] = frame[price_column] / frame[earnings_column]
    return frame


def validate_join_cardinality(
    left: pd.DataFrame,
    right: pd.DataFrame,
    keys: Sequence[str],
    require_right_unique: bool = True,
) -> dict[str, Any]:
    """Fail before a join can multiply rows or silently lose key coverage."""
    _require_columns(left, list(keys))
    _require_columns(right, list(keys))
    right_duplicate_rows = int(right.duplicated(list(keys), keep=False).sum())
    if require_right_unique and right_duplicate_rows:
        raise ValueError(
            f"Right-side join keys are not unique: {right_duplicate_rows} row(s)"
        )
    left_keys = left[list(keys)].drop_duplicates()
    right_keys = right[list(keys)].drop_duplicates()
    coverage = left_keys.merge(right_keys, on=list(keys), how="left", indicator=True)
    unmatched = int((coverage["_merge"] == "left_only").sum())
    coverage_rate = 1.0 - unmatched / len(left_keys) if len(left_keys) else 1.0
    return {
        "left_rows": len(left),
        "right_rows": len(right),
        "left_distinct_keys": len(left_keys),
        "right_distinct_keys": len(right_keys),
        "right_duplicate_rows": right_duplicate_rows,
        "unmatched_left_keys": unmatched,
        "join_key_coverage_rate": coverage_rate,
    }


def compare_source_vintages_without_averaging(
    anchors: pd.DataFrame,
    value_column: str = "published_forward_pe",
) -> pd.DataFrame:
    """Expose cross-source divergence while preserving every provider series."""
    keys = ["index_id", "source_as_of_date", "horizon", "earnings_basis"]
    _require_columns(anchors, [*keys, "provider", value_column])
    frame = anchors.loc[anchors[value_column].notna()].copy()
    grouped = frame.groupby(keys, dropna=False)
    result = grouped.agg(
        source_count=("provider", "nunique"),
        providers=("provider", lambda values: "|".join(sorted(set(values)))),
        minimum_value=(value_column, "min"),
        maximum_value=(value_column, "max"),
    ).reset_index()
    result["relative_source_spread"] = (
        result["maximum_value"] / result["minimum_value"] - 1.0
    )
    result["conflict_status"] = np.where(
        result["source_count"] <= 1,
        "single_source",
        np.where(
            result["relative_source_spread"] <= 0.02,
            "aligned_not_blended",
            "material_definition_or_timing_conflict",
        ),
    )
    return result


def add_dynamic_valuation_regime(
    daily_values: pd.DataFrame,
    entity_column: str,
    date_column: str,
    forward_pe_column: str,
    window: int = VALUATION_REGIME_WINDOW,
    min_periods: int = VALUATION_REGIME_MIN_PERIODS,
    cheap_quantile: float = VALUATION_CHEAP_QUANTILE,
    expensive_quantile: float = VALUATION_EXPENSIVE_QUANTILE,
) -> pd.DataFrame:
    """Create point-in-time valuation states using only preceding observations."""
    _require_columns(
        daily_values, [entity_column, date_column, forward_pe_column]
    )
    if not 0 < cheap_quantile < expensive_quantile < 1:
        raise ValueError("Valuation regime quantiles must be ordered inside (0, 1)")
    frame = daily_values.copy()
    frame[date_column] = pd.to_datetime(frame[date_column])
    frame = frame.sort_values([entity_column, date_column]).reset_index(drop=True)

    def add_entity_thresholds(group: pd.DataFrame) -> pd.DataFrame:
        result = group.copy()
        historical = result[forward_pe_column].shift(1)
        result["cheap_pe_threshold"] = historical.rolling(
            window=window, min_periods=min_periods
        ).quantile(cheap_quantile)
        result["expensive_pe_threshold"] = historical.rolling(
            window=window, min_periods=min_periods
        ).quantile(expensive_quantile)
        result["valuation_regime"] = np.select(
            [
                result[forward_pe_column] <= result["cheap_pe_threshold"],
                result[forward_pe_column] >= result["expensive_pe_threshold"],
            ],
            ["cheap", "expensive"],
            default="neutral_or_insufficient_history",
        )
        return result

    parts = [
        add_entity_thresholds(group)
        for _, group in frame.groupby(entity_column, sort=False)
    ]
    return pd.concat(parts, ignore_index=True) if parts else frame


def calculate_multiclass_brier_score(
    actual_labels: Sequence[str],
    probability_frame: pd.DataFrame,
) -> float:
    """Score probabilistic regime classifications; lower is better."""
    if len(actual_labels) != len(probability_frame):
        raise ValueError("Actual labels and probabilities must have equal length")
    probabilities = probability_frame.astype(float)
    row_sums = probabilities.sum(axis=1)
    if not np.allclose(row_sums, 1.0, atol=1e-8):
        raise ValueError("Each probability row must sum to one")
    if ((probabilities < 0) | (probabilities > 1)).any().any():
        raise ValueError("Probabilities must lie inside [0, 1]")
    classes = list(probabilities.columns)
    unknown = set(actual_labels) - set(classes)
    if unknown:
        raise ValueError(f"Actual labels missing from probability columns: {unknown}")
    one_hot = np.zeros_like(probabilities.to_numpy())
    class_index = {label: idx for idx, label in enumerate(classes)}
    for row_index, label in enumerate(actual_labels):
        one_hot[row_index, class_index[label]] = 1.0
    return float(np.mean(np.sum((probabilities.to_numpy() - one_hot) ** 2, axis=1)))


def validate_no_future_leakage(
    frame: pd.DataFrame,
    decision_ts_column: str = "decision_ts_utc",
    available_ts_column: str = "available_ts_utc",
) -> None:
    """Fail if a row was not yet available at its simulated decision time."""
    _require_columns(frame, [decision_ts_column, available_ts_column])
    decision = pd.to_datetime(frame[decision_ts_column], utc=True)
    available = pd.to_datetime(frame[available_ts_column], utc=True)
    bad = frame.loc[available > decision]
    if not bad.empty:
        raise ValueError(f"Future leakage detected in {len(bad)} row(s)")


def validate_natural_key_conflicts(
    existing: pd.DataFrame,
    incoming: pd.DataFrame,
    natural_key_columns: Sequence[str],
    hash_column: str = "raw_document_hash",
) -> pd.DataFrame:
    """Return only new rows; fail on same key with a different source hash."""
    _require_columns(existing, [*natural_key_columns, hash_column])
    _require_columns(incoming, [*natural_key_columns, hash_column])
    old = existing[[*natural_key_columns, hash_column]].drop_duplicates()
    merged = incoming.merge(
        old,
        on=list(natural_key_columns),
        how="left",
        suffixes=("_incoming", "_existing"),
    )
    conflicts = merged.loc[
        merged[f"{hash_column}_existing"].notna()
        & (
            merged[f"{hash_column}_incoming"]
            != merged[f"{hash_column}_existing"]
        )
    ]
    if not conflicts.empty:
        raise ValueError(
            f"Natural-key conflict with different source hash: {len(conflicts)} row(s)"
        )

    existing_hashes = set(existing[hash_column].dropna().astype(str))
    return incoming.loc[
        ~incoming[hash_column].astype(str).isin(existing_hashes)
    ].copy()


def _require_columns(frame: pd.DataFrame, columns: Sequence[str]) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _snapshot_part_hashes(dataset_dir: Path) -> dict[str, str]:
    return {
        path.name: _file_sha256(path)
        for path in sorted(dataset_dir.glob("part-*.parquet"))
    }


def _canonical_dataframe_hash(frame: pd.DataFrame) -> str:
    canonical = frame.copy()
    canonical = canonical.reindex(sorted(canonical.columns), axis=1)
    canonical = canonical.sort_values(list(canonical.columns)).reset_index(drop=True)
    payload = canonical.to_json(
        orient="records",
        date_format="iso",
        date_unit="us",
        force_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _dataframe_schema_hash(frame: pd.DataFrame) -> str:
    schema = "|".join(
        f"{column}:{frame[column].dtype}" for column in sorted(frame.columns)
    )
    return hashlib.sha256(schema.encode("utf-8")).hexdigest()


def _dataframe_date_bounds(frame: pd.DataFrame) -> tuple[str | None, str | None]:
    preferred = [
        "observation_date",
        "source_as_of_date",
        "available_from_date",
        "date",
    ]
    selected = next((column for column in preferred if column in frame.columns), None)
    if selected is None:
        return None, None
    parsed = pd.to_datetime(frame[selected], errors="coerce").dropna()
    if parsed.empty:
        return None, None
    return parsed.min().date().isoformat(), parsed.max().date().isoformat()


def append_immutable_parquet_part(
    frame: pd.DataFrame,
    dataset_dir: str | Path,
    dataset_name: str,
) -> dict[str, Any]:
    """Write one new immutable Parquet part plus an append-only JSONL manifest."""
    if frame.empty:
        return {"status": "skipped_empty", "rows": 0}

    target_dir = Path(dataset_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    before_hashes = _snapshot_part_hashes(target_dir)
    payload_hash = _canonical_dataframe_hash(frame)
    schema_hash = _dataframe_schema_hash(frame)
    minimum_date, maximum_date = _dataframe_date_bounds(frame)
    part_name = f"part-{payload_hash[:20]}.parquet"
    target_path = target_dir / part_name

    if target_path.exists():
        return {
            "status": "skipped_idempotent",
            "rows": len(frame),
            "part": str(target_path),
            "payload_hash": payload_hash,
        }

    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix="pending-",
            suffix=".parquet",
            dir=target_dir,
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
        frame.to_parquet(temporary_path, index=False)
        os.replace(temporary_path, target_path)
        temporary_path = None
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()

    after_hashes = _snapshot_part_hashes(target_dir)
    for name, old_hash in before_hashes.items():
        if after_hashes.get(name) != old_hash:
            raise RuntimeError(f"Existing Parquet part changed: {name}")
    if part_name not in after_hashes:
        raise RuntimeError("New Parquet part was not committed")
    if len(after_hashes) != len(before_hashes) + 1:
        raise RuntimeError("Expected exactly one new Parquet part")

    manifest_path = target_dir / "manifest.jsonl"
    manifest_record = {
        "dataset": dataset_name,
        "part": part_name,
        "rows": len(frame),
        "payload_hash": payload_hash,
        "file_sha256": after_hashes[part_name],
        "schema_hash": schema_hash,
        "minimum_date": minimum_date,
        "maximum_date": maximum_date,
        "committed_ts_utc": datetime.now(UTC).isoformat(),
        "updated_at": datetime.now(UTC).isoformat(),
        "methodology_version": METHODOLOGY_VERSION,
        "status": "committed",
    }
    with manifest_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(manifest_record, ensure_ascii=False) + "\n")

    return {"status": "committed", **manifest_record, "path": str(target_path)}


def refresh_duckdb_view(
    database_path: str | Path,
    view_name: str,
    dataset_dir: str | Path,
) -> int:
    """Refresh a DuckDB view over the immutable Parquet dataset and return rows."""
    if duckdb is None:
        raise RuntimeError(
            "DuckDB integration requires the optional 'duckdb' package; "
            "install it in the active VIA environment before refreshing views"
        )
    if not view_name.replace("_", "").isalnum():
        raise ValueError("view_name may contain only letters, numbers and underscores")
    parquet_glob = str(Path(dataset_dir) / "part-*.parquet").replace("'", "''")
    connection = duckdb.connect(str(database_path))
    try:
        connection.execute(
            f"CREATE OR REPLACE VIEW {view_name} AS "
            f"SELECT * FROM read_parquet('{parquet_glob}', union_by_name=true)"
        )
        row_count = connection.execute(
            f"SELECT COUNT(*) FROM {view_name}"
        ).fetchone()[0]
    finally:
        connection.close()
    return int(row_count)


def run_self_test() -> dict[str, Any]:
    """Run deterministic formula, data-quality and append-only checks."""
    factset_sp500_html = """
    <html><head>
      <title>Highest Forward 12-Month P/E Ratio For the S&amp;P 500</title>
      <meta property="article:published_time" content="2025-11-04T12:00:00+00:00">
    </head><body>
      <p>On October 29, the forward 12-month P/E ratio for the S&amp;P 500
      was 23.1. This forward 12-month P/E ratio was based on a closing price
      of 6,890.59 and a forward 12-month EPS estimate of $298.56.</p>
    </body></html>
    """
    factset_document = extract_factset_article_document(
        index_id="SP500",
        source_url=(
            "https://insight.factset.com/"
            "highest-forward-12-month-p/e-ratio-for-the-sp-500-in-more-than-5-years"
        ),
        raw_html=factset_sp500_html,
        retrieved_ts_utc=datetime(2025, 11, 4, 12, 5, tzinfo=UTC),
    )
    factset_candidate = parse_factset_forward_valuation(factset_document)
    if factset_candidate.extraction_status != "ready_reported_eps":
        raise AssertionError("Complete FactSet article should promote reported EPS")
    if factset_candidate.source_as_of_date != date(2025, 10, 29):
        raise AssertionError("FactSet article cutoff date parsing failed")
    factset_anchor = build_index_anchor(
        factset_candidate_to_index_observation(factset_candidate)
    )
    if not math.isclose(factset_anchor["forward_eps_points_selected"], 298.56):
        raise AssertionError("FactSet reported EPS must outrank implied EPS")

    factset_stoxx_html = """
    <html><head>
      <title>STOXX 600 Q2 Earnings Beat Rate Review</title>
      <meta property="article:published_time" content="2026-08-14T12:00:00+00:00">
    </head><body>
      <p>The STOXX 600 currently trades at a 12-month forward P/E of ~14.2x,
      in line with its 10-year average.</p>
    </body></html>
    """
    factset_stoxx_document = extract_factset_article_document(
        index_id="STOXX600",
        source_url="https://insight.factset.com/stoxx-600-q2-earnings-beat-rate-review",
        raw_html=factset_stoxx_html,
        retrieved_ts_utc=datetime(2026, 8, 14, 12, 5, tzinfo=UTC),
    )
    factset_stoxx_candidate = parse_factset_forward_valuation(
        factset_stoxx_document,
        external_index_level=550.0,
        external_index_level_date=date(2026, 8, 14),
    )
    if factset_stoxx_candidate.extraction_status != "review_date_only_cutoff":
        raise AssertionError("Approximate current P/E must not bypass cutoff review")

    discovered_urls = discover_factset_article_urls(
        """
        <urlset>
          <url><loc>https://insight.factset.com/sp-500-earnings-season-update</loc></url>
          <url><loc>https://insight.factset.com/stoxx-600-q2-review</loc></url>
        </urlset>
        """,
        base_url="https://insight.factset.com/sitemap.xml",
        index_id="SP500",
    )
    if discovered_urls != [
        "https://insight.factset.com/sp-500-earnings-season-update"
    ]:
        raise AssertionError("FactSet discovery registry filtering failed")

    batch = crawl_factset_release_batch(
        [
            {
                "index_id": "SP500",
                "source_url": factset_document.canonical_url,
            }
        ],
        fetcher=lambda _: factset_sp500_html,
        retrieved_ts_utc=datetime(2025, 11, 4, 12, 5, tzinfo=UTC),
    )
    if (
        len(batch["anchors"]) != 1
        or batch["audit"].iloc[0]["status"] != "promoted_to_anchor"
    ):
        raise AssertionError("FactSet deterministic batch ingestion failed")

    index_observation = IndexReleaseObservation(
        index_id="SP500",
        provider="FACTSET_EXAMPLE",
        source_as_of_date=date(2025, 10, 29),
        release_ts_utc=datetime(2025, 11, 4, 12, 0, tzinfo=UTC),
        retrieved_ts_utc=datetime(2025, 11, 4, 12, 5, tzinfo=UTC),
        available_from_date=date(2025, 11, 5),
        horizon="NTM",
        earnings_basis="operating",
        index_level_anchor=6890.59,
        published_forward_pe=23.1,
        forward_eps_points_reported=298.56,
        source_url="https://example.invalid/factset-release",
        raw_document_hash="synthetic_factset_hash_v2",
        max_stale_days=14,
    )
    index_anchor = build_index_anchor(index_observation)
    if index_anchor["quality_status"] != "pass":
        raise AssertionError("Synthetic index anchor should pass")
    if not (
        index_anchor["forward_eps_points_interval_lower"]
        < index_anchor["forward_eps_points_implied"]
        < index_anchor["forward_eps_points_interval_upper"]
    ):
        raise AssertionError("Rounding interval must contain implied EPS")

    index_daily = apply_index_vintages(
        pd.DataFrame(
            [
                {
                    "observation_date": "2025-11-05",
                    "index_id": "SP500",
                    "index_level": 6900.0,
                },
                {
                    "observation_date": "2025-11-06",
                    "index_id": "SP500",
                    "index_level": 7000.0,
                },
            ]
        ),
        pd.DataFrame([index_anchor]),
    )

    etf_observation = ETFReleaseObservation(
        ticker="IVV",
        provider="SYNTHETIC_ETF_SOURCE",
        source_as_of_date=date(2025, 10, 29),
        release_ts_utc=datetime(2025, 11, 4, 12, 0, tzinfo=UTC),
        retrieved_ts_utc=datetime(2025, 11, 4, 12, 5, tzinfo=UTC),
        available_from_date=date(2025, 11, 5),
        horizon="NTM",
        earnings_basis="operating",
        nav_per_share_anchor=620.0,
        mapped_index_id="SP500",
        mapped_index_forward_pe=23.1,
        mapping_quality="exact",
        source_url="https://example.invalid/ivv-source",
        raw_document_hash="synthetic_ivv_hash_v2",
        max_stale_days=14,
    )
    etf_anchor = build_etf_anchor(etf_observation)
    etf_daily = apply_etf_vintages(
        pd.DataFrame(
            [
                {
                    "observation_date": "2025-11-05",
                    "ticker": "IVV",
                    "nav_per_share": 621.0,
                    "market_close": 621.5,
                }
            ]
        ),
        pd.DataFrame([etf_anchor]),
    )

    dynamic_stale_days = estimate_dynamic_stale_days(
        ["2026-01-02", "2026-01-09", "2026-01-16", "2026-01-23"]
    )
    if dynamic_stale_days != 11:
        raise AssertionError("Weekly cadence should produce an 11-day stale threshold")

    cap_weighted = reconstruct_cap_weighted_forward_valuation(
        pd.DataFrame(
            [
                {
                    "security_id": "A",
                    "float_adjusted_market_value": 100.0,
                    "forward_earnings_value": 5.0,
                },
                {
                    "security_id": "B",
                    "float_adjusted_market_value": 200.0,
                    "forward_earnings_value": 10.0,
                },
                {
                    "security_id": "C",
                    "float_adjusted_market_value": 700.0,
                    "forward_earnings_value": 35.0,
                },
            ]
        )
    )
    if not math.isclose(cap_weighted["full_forward_pe"], 20.0):
        raise AssertionError("Cap-weighted aggregate P/E formula failed")

    etf_holdings = reconstruct_etf_holdings_forward_valuation(
        holdings=pd.DataFrame(
            [
                {
                    "security_id": "A",
                    "market_value_fund_currency": 100.0,
                    "quantity": 10.0,
                    "forward_eps_local_currency": 0.5,
                    "fx_to_fund_currency": 1.0,
                    "is_equity": True,
                },
                {
                    "security_id": "B",
                    "market_value_fund_currency": 200.0,
                    "quantity": 20.0,
                    "forward_eps_local_currency": 0.5,
                    "fx_to_fund_currency": 1.0,
                    "is_equity": True,
                },
            ]
        ),
        etf_shares_outstanding=30.0,
    )
    if not math.isclose(etf_holdings["full_forward_pe"], 20.0):
        raise AssertionError("ETF holdings reconstruction failed")

    price_weighted = reconstruct_price_weighted_forward_valuation(
        constituents=pd.DataFrame(
            [
                {"security_id": "A", "adjusted_price": 100.0, "forward_eps": 5.0},
                {"security_id": "B", "adjusted_price": 200.0, "forward_eps": 10.0},
            ]
        ),
        index_divisor=10.0,
    )
    if not math.isclose(price_weighted["full_forward_pe"], 20.0):
        raise AssertionError("Price-weighted aggregate P/E formula failed")

    second_anchor = dict(index_anchor)
    second_anchor.update(
        {
            "vintage_id": "idxv_second",
            "available_from_date": date(2025, 11, 12),
            "index_level_anchor": 7100.0,
            "forward_eps_points_selected": 305.0,
        }
    )
    revision_bridge = compute_vintage_revision_bridge(
        pd.DataFrame([index_anchor, second_anchor])
    )
    last_bridge = revision_bridge.iloc[-1]
    if not math.isclose(
        last_bridge["forward_pe_log_change"],
        last_bridge["price_log_change"]
        - last_bridge["earnings_revision_log_change"],
    ):
        raise AssertionError("Price/earnings revision bridge identity failed")

    join_profile = validate_join_cardinality(
        left=pd.DataFrame([{"security_id": "A"}, {"security_id": "B"}]),
        right=pd.DataFrame([{"security_id": "A"}, {"security_id": "B"}]),
        keys=["security_id"],
    )
    if not math.isclose(join_profile["join_key_coverage_rate"], 1.0):
        raise AssertionError("Join coverage test failed")

    source_comparison = compare_source_vintages_without_averaging(
        pd.DataFrame(
            [
                {
                    "index_id": "SP500",
                    "source_as_of_date": date(2025, 10, 29),
                    "horizon": "NTM",
                    "earnings_basis": "operating",
                    "provider": "A",
                    "published_forward_pe": 23.1,
                },
                {
                    "index_id": "SP500",
                    "source_as_of_date": date(2025, 10, 29),
                    "horizon": "NTM",
                    "earnings_basis": "operating",
                    "provider": "B",
                    "published_forward_pe": 24.0,
                },
            ]
        )
    )
    if source_comparison.iloc[0]["conflict_status"] != (
        "material_definition_or_timing_conflict"
    ):
        raise AssertionError("Source divergence should be surfaced, not averaged")

    regime_input = pd.DataFrame(
        {
            "index_id": ["SP500"] * 10,
            "observation_date": pd.date_range("2026-01-01", periods=10),
            "forward_pe": [20.0, 19.0, 21.0, 18.0, 22.0, 17.0, 23.0, 16.0, 24.0, 25.0],
        }
    )
    regime = add_dynamic_valuation_regime(
        regime_input,
        entity_column="index_id",
        date_column="observation_date",
        forward_pe_column="forward_pe",
        window=5,
        min_periods=3,
    )
    if regime.iloc[-1]["valuation_regime"] != "expensive":
        raise AssertionError("Point-in-time valuation regime test failed")

    brier_score = calculate_multiclass_brier_score(
        actual_labels=["up", "down"],
        probability_frame=pd.DataFrame(
            [{"up": 0.8, "down": 0.2}, {"up": 0.3, "down": 0.7}]
        ),
    )
    if not math.isclose(brier_score, 0.13):
        raise AssertionError("Multiclass Brier score test failed")

    with tempfile.TemporaryDirectory(prefix="forward-vintage-v2-test-") as tmp:
        root = Path(tmp)
        part_frame = pd.DataFrame(
            [
                {
                    "observation_date": date(2026, 1, 2),
                    "vintage_id": "v1",
                    "value": 1.0,
                }
            ]
        )
        first_write = append_immutable_parquet_part(
            part_frame, root / "dataset", "self_test"
        )
        second_write = append_immutable_parquet_part(
            part_frame, root / "dataset", "self_test"
        )
        duckdb_rows: int | str
        if duckdb is None:
            duckdb_rows = "skipped_dependency_missing"
        else:
            duckdb_rows = refresh_duckdb_view(
                root / "self_test.duckdb", "self_test_view", root / "dataset"
            )
        if (
            first_write["status"] != "committed"
            or second_write["status"] != "skipped_idempotent"
            or (duckdb is not None and duckdb_rows != 1)
        ):
            raise AssertionError("Append-only or DuckDB integration test failed")
        factset_persist = persist_factset_ingestion_batch(
            batch,
            root / "factset_public_release",
        )
        if any(
            factset_persist[table_name]["status"] != "committed"
            for table_name in ("candidates", "anchors", "audit")
        ):
            raise AssertionError("FactSet append-only persistence test failed")

    return {
        "status": "pass",
        "methodology_version": METHODOLOGY_VERSION,
        "tests": {
            "factset_complete_article": factset_candidate.extraction_status,
            "factset_date_only_gate": factset_stoxx_candidate.extraction_status,
            "factset_discovery_urls": len(discovered_urls),
            "factset_batch_anchor_rows": len(batch["anchors"]),
            "factset_append_only_persistence": "pass",
            "rounding_interval": "pass",
            "index_vintage_assignment": len(index_daily) == 2,
            "etf_nav_and_market_pe": len(etf_daily) == 1,
            "dynamic_staleness": dynamic_stale_days,
            "cap_weighted_forward_pe": cap_weighted["full_forward_pe"],
            "etf_holdings_forward_pe": etf_holdings["full_forward_pe"],
            "price_weighted_forward_pe": price_weighted["full_forward_pe"],
            "revision_bridge": "pass",
            "join_key_coverage_rate": join_profile["join_key_coverage_rate"],
            "source_conflict_detection": source_comparison.iloc[0][
                "conflict_status"
            ],
            "valuation_regime": regime.iloc[-1]["valuation_regime"],
            "brier_score": brier_score,
            "append_first": first_write["status"],
            "append_replay": second_write["status"],
            "duckdb_rows": duckdb_rows,
        },
    }


def _json_default(value: Any) -> Any:
    if isinstance(value, (date, datetime, pd.Timestamp)):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Point-in-time forward valuation and FactSet public-release utilities"
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run deterministic formula and vintage-assignment checks",
    )
    parser.add_argument(
        "--factset-request-file",
        type=Path,
        help=(
            "JSON/JSONL/CSV rows containing index_id, source_url and optional "
            "same-cutoff external_index_level fields"
        ),
    )
    parser.add_argument(
        "--factset-output-root",
        type=Path,
        default=DEFAULT_FACTSET_OUTPUT_ROOT,
        help="Append-only output root for candidates, anchors, audit and DuckDB",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test and args.factset_request_file is not None:
        raise SystemExit("Choose either --self-test or --factset-request-file")
    if args.self_test:
        result = run_self_test()
    elif args.factset_request_file is not None:
        result = run_factset_ingestion_file(
            args.factset_request_file,
            args.factset_output_root,
        )
    else:
        raise SystemExit(
            "Use --self-test, --factset-request-file, or import the module"
        )
    print(json.dumps(result, ensure_ascii=False, indent=2, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
