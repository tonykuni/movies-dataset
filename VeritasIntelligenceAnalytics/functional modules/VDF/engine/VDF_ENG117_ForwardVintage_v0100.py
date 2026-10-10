"""Point-in-time forward valuation vintage reference implementation v2.

The module keeps index and ETF valuation anchors independent. It never updates
an old Parquet part in place and never calls an implied value source-reported.
Version 2 adds rounding intervals, source readiness, holdings reconstruction,
dynamic staleness, revision bridges, join-cardinality checks and regime inputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import duckdb
import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Parameters: keep operational thresholds at the top of the file.
# ---------------------------------------------------------------------------

METHODOLOGY_VERSION = "forward_valuation_vintage_v2"
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
    obs["observation_date"] = pd.to_datetime(obs["observation_date"])
    anc["available_from_date"] = pd.to_datetime(anc["available_from_date"])
    anc["source_as_of_date"] = pd.to_datetime(anc["source_as_of_date"])
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
        duckdb_rows = refresh_duckdb_view(
            root / "self_test.duckdb", "self_test_view", root / "dataset"
        )
        if (
            first_write["status"] != "committed"
            or second_write["status"] != "skipped_idempotent"
            or duckdb_rows != 1
        ):
            raise AssertionError("Append-only or DuckDB integration test failed")

    return {
        "status": "pass",
        "methodology_version": METHODOLOGY_VERSION,
        "tests": {
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
        description="Point-in-time forward valuation vintage utilities"
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run deterministic formula and vintage-assignment checks",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.self_test:
        raise SystemExit("Use --self-test or import the module from your pipeline")
    result = run_self_test()
    print(json.dumps(result, ensure_ascii=False, indent=2, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
