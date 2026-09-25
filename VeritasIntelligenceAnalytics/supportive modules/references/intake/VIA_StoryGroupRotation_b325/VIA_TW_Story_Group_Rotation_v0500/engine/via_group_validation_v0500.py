from __future__ import annotations

"""Point-in-time validation for multi-label Taiwan story groups.

The engine consumes a residual-return panel whose market factor was already
built from the complete TWSE + TPEX common-equity universe with 2330 excluded.
It deliberately does not estimate that factor from the submitted story-group
members: doing so would re-introduce the very market/TSMC noise being removed.

There is no composite score and no fixed correlation, PCA, market-cap or
lead/lag cutoff.  Observed evidence is compared with three data-derived nulls:

* descriptor-matched pseudo groups;
* unrestricted random pseudo groups; and
* independent circular block shifts, which preserve each return series while
  destroying contemporaneous group alignment.

Group decisions use an intersection-union p-value followed by Benjamini-
Hochberg FDR control.  Member roles use a leave-one-out group return and the
same max-over-lags null discipline.  Statistical error control and finite-
sample requirements are structural governance parameters, not market gates.
"""

# =============================================================================
# def 00 PARAMETERS — structural inference controls only
# =============================================================================

from dataclasses import dataclass
import argparse
import hashlib
import json
import math
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd


ENGINE_ID = "VIA_STORY_GROUP_VALIDATION_V0500"
ENGINE_VERSION = "0.5.0"
DEFAULT_WINDOWS = (60, 120, 240)
EXPECTED_RESIDUAL_UNIVERSE = "TWSE_TPEX_COMMON_EQUITY_EX_2330"
TSMC_TICKER = "2330"
GROUP_METRICS = (
    "ResidualMedianCorrelation",
    "ResidualPositivePairRatio",
    "PCAAbsorption",
)
NULL_TYPES = ("MATCHED", "RANDOM", "CIRCULAR_BLOCK_SHIFT")
ROLE_VALUES = ("LEAD", "PEER", "LAG", "UNRELATED")
EPSILON = np.finfo(float).eps


@dataclass(frozen=True)
class GroupValidationConfig:
    """Structural controls; none is a market-value or correlation threshold."""

    windows: tuple[int, ...] = DEFAULT_WINDOWS
    fdr_control_level: float = 0.10
    null_repeats_override: int | None = None
    null_repeats_floor: int = 99
    null_repeats_cap: int = 399
    random_seed: int = 20260902
    minimum_group_members: int = 3
    tsmc_ticker: str = TSMC_TICKER
    expected_residual_universe: str = EXPECTED_RESIDUAL_UNIVERSE
    require_residual_provenance: bool = True
    match_columns: tuple[str, ...] = ("Market", "SizeTier", "LiquidityTier")


@dataclass
class GroupValidationResult:
    """Inspectable tables returned by :func:`def_run_group_validation`."""

    group_validation: pd.DataFrame
    member_roles: pd.DataFrame
    null_ledger: pd.DataFrame
    metadata: dict[str, Any]


# =============================================================================
# def 01 NORMALIZATION AND PIT BOUNDARIES
# =============================================================================


def def_ticker_base(value: object) -> str:
    text = str(value or "").strip().upper().replace(" ", "")
    if text.endswith(".TWO"):
        return text[:-4]
    if text.endswith(".TW"):
        return text[:-3]
    return text


def def_parse_date(value: object) -> pd.Timestamp | pd.NaT:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return pd.NaT
    stamp = pd.Timestamp(parsed)
    if stamp.tzinfo is not None:
        stamp = stamp.tz_convert("Asia/Taipei").tz_localize(None)
    return stamp.normalize()


def def_parse_taipei_timestamp_series(values: pd.Series) -> pd.Series:
    """Parse a uniform timestamp lane; naive values mean Taiwan local time."""

    parsed = pd.to_datetime(values, errors="coerce")
    try:
        timezone = parsed.dt.tz
    except AttributeError:
        # Mixed aware/naive sources are unusual but still fail row-wise rather
        # than silently treating a naive Taiwan publication time as UTC.
        def parse_one(value: object) -> pd.Timestamp | pd.NaT:
            try:
                stamp = pd.Timestamp(value)
            except (TypeError, ValueError):
                return pd.NaT
            if pd.isna(stamp):
                return pd.NaT
            if stamp.tzinfo is None:
                return stamp.tz_localize("Asia/Taipei")
            return stamp.tz_convert("Asia/Taipei")

        return values.map(parse_one)
    if timezone is None:
        return parsed.dt.tz_localize("Asia/Taipei", ambiguous="NaT", nonexistent="NaT")
    return parsed.dt.tz_convert("Asia/Taipei")


def def_decision_timestamp(as_of_date: pd.Timestamp, value: object | None) -> pd.Timestamp:
    if value is None:
        return as_of_date.tz_localize("Asia/Taipei") + pd.Timedelta(hours=23, minutes=59, seconds=59)
    parsed = pd.Timestamp(value)
    if parsed.tzinfo is None:
        return parsed.tz_localize("Asia/Taipei")
    return parsed.tz_convert("Asia/Taipei")


def def_prepare_trading_calendar(values: Iterable[object]) -> pd.DatetimeIndex:
    parsed = pd.to_datetime(pd.Index(list(values)), errors="coerce")
    if isinstance(parsed, pd.DatetimeIndex) and parsed.tz is not None:
        parsed = parsed.tz_convert("Asia/Taipei").tz_localize(None)
    return pd.DatetimeIndex(parsed).dropna().normalize().unique().sort_values()


def def_next_trading_session(
    snapshot_date: object,
    trading_calendar: Iterable[object],
) -> pd.Timestamp | pd.NaT:
    snapshot = def_parse_date(snapshot_date)
    if pd.isna(snapshot):
        return pd.NaT
    calendar = def_prepare_trading_calendar(trading_calendar)
    candidates = calendar[calendar > snapshot]
    return candidates[0] if len(candidates) else pd.NaT


def def_prepare_residual_panel(residual_panel: pd.DataFrame) -> pd.DataFrame:
    """Normalize long or Date-indexed wide residual returns.

    Long input requires ``Date``, ``Ticker`` and ``ResidualReturn``.  A wide
    frame may instead contain ``Date`` plus one column per ticker.  Optional
    ``KnownAt`` timestamps are retained and enforced by the runner.
    """

    frame = residual_panel.copy()
    if {"Date", "Ticker", "ResidualReturn"}.issubset(frame.columns):
        keep = ["Date", "Ticker", "ResidualReturn"]
        if "KnownAt" in frame.columns:
            keep.append("KnownAt")
        frame = frame[keep].copy()
    else:
        if "Date" not in frame.columns:
            if isinstance(frame.index, pd.DatetimeIndex):
                frame = frame.reset_index().rename(columns={frame.index.name or "index": "Date"})
            else:
                raise ValueError(
                    "residual panel requires Date+Ticker+ResidualReturn or a DatetimeIndex wide frame"
                )
        value_columns = [column for column in frame.columns if column != "Date"]
        if not value_columns:
            raise ValueError("wide residual panel contains no ticker columns")
        frame = frame.melt(
            id_vars=["Date"],
            value_vars=value_columns,
            var_name="Ticker",
            value_name="ResidualReturn",
        )

    frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce")
    if getattr(frame["Date"].dt, "tz", None) is not None:
        frame["Date"] = frame["Date"].dt.tz_convert("Asia/Taipei").dt.tz_localize(None)
    frame["Date"] = frame["Date"].dt.normalize()
    frame["Ticker"] = frame["Ticker"].map(def_ticker_base)
    frame["ResidualReturn"] = pd.to_numeric(frame["ResidualReturn"], errors="coerce")
    if "KnownAt" in frame.columns:
        frame["KnownAt"] = def_parse_taipei_timestamp_series(frame["KnownAt"])
    invalid_key = frame["Date"].isna() | frame["Ticker"].eq("")
    if invalid_key.any():
        raise ValueError(f"residual panel has {int(invalid_key.sum())} invalid Date/Ticker keys")
    duplicate = frame.duplicated(["Date", "Ticker"], keep=False)
    if duplicate.any():
        raise ValueError(f"residual panel has {int(duplicate.sum())} duplicate Date+Ticker rows")
    return frame.sort_values(["Date", "Ticker"]).reset_index(drop=True)


def def_metadata_value(frame: pd.DataFrame, names: Sequence[str]) -> object | None:
    attrs = {str(key).lower(): value for key, value in frame.attrs.items()}
    for name in names:
        if name.lower() in attrs:
            return attrs[name.lower()]
    lower_columns = {str(column).lower(): column for column in frame.columns}
    for name in names:
        column = lower_columns.get(name.lower())
        if column is None:
            continue
        unique = frame[column].dropna().unique()
        if len(unique) == 1:
            return unique[0]
    return None


def def_bool_value(value: object) -> bool | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    text = str(value).strip().upper()
    if text in {"TRUE", "T", "YES", "Y", "1", "PASS"}:
        return True
    if text in {"FALSE", "F", "NO", "N", "0", "FAIL"}:
        return False
    return None


def def_residual_provenance(
    residual_panel: pd.DataFrame,
    config: GroupValidationConfig,
) -> dict[str, object]:
    universe = def_metadata_value(
        residual_panel,
        ("ResidualizationUniverse", "MarketUniverse", "market_universe"),
    )
    tsmc_excluded = def_bool_value(
        def_metadata_value(
            residual_panel,
            ("TSMCExcludedFromMarketFactor", "TSMCExcluded", "tsmc_excluded"),
        )
    )
    point_in_time = def_bool_value(
        def_metadata_value(residual_panel, ("PointInTime", "PIT", "point_in_time"))
    )
    normalized_universe = str(universe or "").strip().upper()
    expected = str(config.expected_residual_universe).strip().upper()
    reasons: list[str] = []
    if normalized_universe != expected:
        reasons.append("RESIDUAL_UNIVERSE_NOT_TWSE_TPEX_COMMON_EQUITY_EX_2330")
    if tsmc_excluded is not True:
        reasons.append("TSMC_EXCLUSION_NOT_PROVEN")
    if point_in_time is not True:
        reasons.append("POINT_IN_TIME_NOT_PROVEN")
    return {
        "EvidenceStatus": "READY" if not reasons else "BLOCKED",
        "EvidenceReason": "PASS" if not reasons else "|".join(reasons),
        "ResidualizationUniverse": normalized_universe or "MISSING",
        "TSMCExcludedFromMarketFactor": tsmc_excluded,
        "PointInTime": point_in_time,
    }


def def_prepare_active_membership(
    membership: pd.DataFrame,
    snapshot_date: pd.Timestamp,
    decision_at: pd.Timestamp,
) -> pd.DataFrame:
    """Return the PIT-approved and pre-approval validation cohorts separately.

    ``ValidationEligible=True`` is an explicit statistical-intake permission,
    not an approval event.  Such rows may be tested while ``_IndexEligible``
    remains false.  Ledger rows still need their approval/effective-date gates.
    """

    if "EventType" in membership.columns:
        raise ValueError(
            "raw membership events cannot enter validation; materialize PIT history first"
        )
    required = {"GroupId", "Ticker"}
    missing = sorted(required.difference(membership.columns))
    if missing:
        raise ValueError(f"membership missing required columns: {missing}")
    frame = membership.copy()
    frame["GroupId"] = frame["GroupId"].fillna("").astype(str).str.strip()
    frame["Ticker"] = frame["Ticker"].map(def_ticker_base)
    if "GroupName" not in frame.columns:
        frame["GroupName"] = frame["GroupId"]
    # Directly accepts the materialized output of via_pit_membership_engine.
    # If several materialization snapshots were concatenated, use one common
    # latest-as-of slice; otherwise a removed relationship could leak back from
    # an older snapshot.
    if "AsOfDate" in frame.columns:
        frame["AsOfDate"] = pd.to_datetime(frame["AsOfDate"], errors="coerce").dt.normalize()
        prior_snapshots = frame.loc[frame["AsOfDate"].le(snapshot_date), "AsOfDate"].dropna()
        if prior_snapshots.empty:
            frame = frame.iloc[0:0].copy()
        else:
            frame = frame.loc[frame["AsOfDate"].eq(prior_snapshots.max())].copy()
    effective_column = next(
        (
            column
            for column in ("EffectiveDate", "MembershipValidFrom", "ValidFrom")
            if column in frame.columns
        ),
        "",
    )
    if effective_column:
        frame[effective_column] = pd.to_datetime(frame[effective_column], errors="coerce").dt.normalize()
        active_from = frame[effective_column].isna() | frame[effective_column].le(snapshot_date)
    else:
        active_from = pd.Series(True, index=frame.index)
    valid_to_column = next(
        (column for column in ("MembershipValidTo", "ValidTo") if column in frame.columns),
        "",
    )
    if valid_to_column:
        frame[valid_to_column] = pd.to_datetime(frame[valid_to_column], errors="coerce").dt.normalize()
        active_to = frame[valid_to_column].isna() | frame[valid_to_column].ge(snapshot_date)
    else:
        active_to = pd.Series(True, index=frame.index)
    approved = pd.Series(True, index=frame.index)
    for column in ("ApprovalStatus", "Decision"):
        if column in frame.columns:
            approved &= frame[column].fillna("").astype(str).str.upper().eq("APPROVED")
    if "EvidenceStatus" in frame.columns:
        approved &= frame["EvidenceStatus"].fillna("").astype(str).str.upper().isin(
            {"APPROVED_EFFECTIVE", "READY", "PASS"}
        )
    validation_candidate = pd.Series(False, index=frame.index)
    if "ValidationEligible" in frame.columns:
        validation_candidate = frame["ValidationEligible"].fillna(False).astype(bool)
        if "ProposedAt" in frame.columns:
            proposed_at = def_parse_taipei_timestamp_series(frame["ProposedAt"])
            validation_candidate &= proposed_at.notna() & proposed_at.le(decision_at)
        else:
            # A proposed relationship without an observable proposal timestamp
            # cannot enter an earlier point-in-time validation snapshot.
            validation_candidate &= False
    known = pd.Series(True, index=frame.index)
    if "KnownAt" in frame.columns:
        known_at = def_parse_taipei_timestamp_series(frame["KnownAt"])
        known &= known_at.notna() & known_at.le(decision_at)
    valid_key = frame["GroupId"].ne("") & frame["Ticker"].ne("")
    admitted = (approved | validation_candidate) & known
    frame["_ValidationCohort"] = np.select(
        [approved, validation_candidate],
        ["APPROVED_PIT", "PROPOSED_VALIDATION"],
        default="BLOCKED",
    )
    if "IndexEligible" in frame.columns:
        declared_index_eligible = frame["IndexEligible"].fillna(False).astype(bool)
    else:
        declared_index_eligible = approved.copy()
    frame["_IndexEligible"] = declared_index_eligible & approved
    return (
        frame.loc[active_from & active_to & admitted & valid_key]
        .drop_duplicates(["GroupId", "Ticker"], keep="last")
        .reset_index(drop=True)
    )


# =============================================================================
# def 02 DYNAMIC THREE-TIER MARKET-CAP CLASSIFICATION
# =============================================================================


def def_one_dimensional_three_clusters(values: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Deterministic three-cluster partition with data-derived breakpoints."""

    finite = np.isfinite(values)
    if finite.sum() < 3:
        return np.full(len(values), -1, dtype=int), np.full(3, np.nan)
    x = values[finite].astype(float)
    centers = np.quantile(x, [1.0 / 6.0, 0.5, 5.0 / 6.0])
    labels = np.zeros(len(x), dtype=int)
    for _ in range(100):
        distances = np.abs(x[:, None] - centers[None, :])
        next_labels = distances.argmin(axis=1)
        if len(set(next_labels.tolist())) < 3:
            ordering = np.argsort(x, kind="mergesort")
            chunks = np.array_split(ordering, 3)
            next_labels = np.empty(len(x), dtype=int)
            for cluster, positions in enumerate(chunks):
                next_labels[positions] = cluster
        next_centers = np.asarray(
            [np.median(x[next_labels == cluster]) for cluster in range(3)], dtype=float
        )
        if np.array_equal(labels, next_labels) and np.allclose(centers, next_centers, equal_nan=True):
            labels = next_labels
            centers = next_centers
            break
        labels = next_labels
        centers = next_centers
    rank = np.argsort(centers)
    remap = {int(original): int(position) for position, original in enumerate(rank)}
    ordered_labels = np.asarray([remap[int(label)] for label in labels], dtype=int)
    ordered_centers = centers[rank]
    output = np.full(len(values), -1, dtype=int)
    output[np.flatnonzero(finite)] = ordered_labels
    return output, ordered_centers


def def_build_dynamic_size_tiers(
    market_cap_panel: pd.DataFrame,
    as_of_date: object,
    *,
    decision_at: object | None = None,
    tsmc_ticker: str = TSMC_TICKER,
) -> pd.DataFrame:
    """Build SMALL/MID/LARGE from current ex-2330 log-cap clusters.

    No absolute market-cap or fixed percentile boundary is used.  Only the most
    recent point-in-time row known by the decision timestamp enters each
    ticker's cross-section.
    """

    required = {"Date", "Ticker", "MarketCap"}
    missing = sorted(required.difference(market_cap_panel.columns))
    if missing:
        raise ValueError(f"market-cap panel missing required columns: {missing}")
    snapshot = def_parse_date(as_of_date)
    if pd.isna(snapshot):
        raise ValueError("as_of_date is invalid")
    decision = def_decision_timestamp(snapshot, decision_at)
    frame = market_cap_panel.copy()
    frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce").dt.normalize()
    frame["Ticker"] = frame["Ticker"].map(def_ticker_base)
    frame["MarketCap"] = pd.to_numeric(frame["MarketCap"], errors="coerce")
    eligible = frame["Date"].notna() & frame["Date"].le(snapshot) & frame["MarketCap"].gt(0)
    if "KnownAt" in frame.columns:
        known = def_parse_taipei_timestamp_series(frame["KnownAt"])
        eligible &= known.notna() & known.le(decision)
    if "AssetType" in frame.columns:
        eligible &= frame["AssetType"].fillna("").astype(str).str.upper().eq("EQUITY")
    market_column = "Market" if "Market" in frame.columns else "Exchange" if "Exchange" in frame.columns else ""
    if market_column:
        eligible &= frame[market_column].fillna("").astype(str).str.upper().isin({"TWSE", "TPEX"})
    eligible &= frame["Ticker"].ne(def_ticker_base(tsmc_ticker))
    current = (
        frame.loc[eligible]
        .sort_values(["Ticker", "Date"])
        .drop_duplicates("Ticker", keep="last")
        .reset_index(drop=True)
    )
    if current.empty:
        return pd.DataFrame(
            columns=[
                "Ticker",
                "SizeTier",
                "SizeAsOfDate",
                "SizeClusterCenterLogCap",
                "SizeTierMethod",
                "EvidenceStatus",
            ]
        )
    values = np.log(current["MarketCap"].to_numpy(dtype=float))
    cluster, centers = def_one_dimensional_three_clusters(values)
    tier_map = {0: "SMALL", 1: "MID", 2: "LARGE"}
    current["SizeTier"] = pd.Series(cluster, index=current.index).map(tier_map)
    current["SizeAsOfDate"] = current["Date"]
    current["SizeClusterCenterLogCap"] = [
        centers[label] if label >= 0 and label < len(centers) else np.nan for label in cluster
    ]
    current["SizeTierMethod"] = "EX_2330_POINT_IN_TIME_LOG_CAP_THREE_CLUSTER"
    current["EvidenceStatus"] = np.where(current["SizeTier"].notna(), "READY", "BLOCKED")
    output_columns = [
        "Ticker",
        "SizeTier",
        "SizeAsOfDate",
        "SizeClusterCenterLogCap",
        "SizeTierMethod",
        "EvidenceStatus",
    ]
    if market_column:
        current["Market"] = current[market_column].astype(str).str.upper()
        output_columns.insert(1, "Market")
    return current[output_columns].sort_values("Ticker").reset_index(drop=True)


def def_prepare_match_features(
    membership: pd.DataFrame,
    match_features: pd.DataFrame | None,
    dynamic_size_tiers: pd.DataFrame | None,
) -> pd.DataFrame:
    descriptor_names = ("Market", "SizeTier", "LiquidityTier")
    sources: list[pd.DataFrame] = []
    if match_features is not None:
        if "Ticker" not in match_features.columns:
            raise ValueError("match_features requires Ticker")
        sources.append(match_features.copy())
    else:
        available = [column for column in descriptor_names if column in membership.columns]
        if available:
            sources.append(membership[["Ticker", *available]].copy())
    if dynamic_size_tiers is not None and not dynamic_size_tiers.empty:
        keep = [column for column in ("Ticker", "Market", "SizeTier") if column in dynamic_size_tiers.columns]
        sources.append(dynamic_size_tiers[keep].copy())
    if not sources:
        return pd.DataFrame(columns=["Ticker", *descriptor_names])

    prepared: list[pd.DataFrame] = []
    for source_index, source in enumerate(sources):
        frame = source.copy()
        if "Exchange" in frame.columns and "Market" not in frame.columns:
            frame = frame.rename(columns={"Exchange": "Market"})
        frame["Ticker"] = frame["Ticker"].map(def_ticker_base)
        keep = [column for column in ("Ticker", *descriptor_names) if column in frame.columns]
        frame = frame[keep].drop_duplicates()
        for column in descriptor_names:
            if column in frame.columns:
                frame[column] = frame[column].fillna("MISSING").astype(str).str.strip().str.upper()
        frame["_SourceOrder"] = source_index
        prepared.append(frame)
    combined = pd.concat(prepared, ignore_index=True, sort=False)
    rows: list[dict[str, object]] = []
    for ticker, ticker_rows in combined.groupby("Ticker", sort=True):
        record: dict[str, object] = {"Ticker": ticker}
        for column in descriptor_names:
            if column not in ticker_rows.columns:
                continue
            values = ticker_rows.loc[
                ticker_rows[column].notna() & ticker_rows[column].ne("MISSING"),
                [column, "_SourceOrder"],
            ].sort_values("_SourceOrder")
            unique = values[column].unique()
            if len(unique) > 1:
                raise ValueError(f"conflicting {column} descriptors for ticker {ticker}: {unique.tolist()}")
            record[column] = unique[-1] if len(unique) else "MISSING"
        rows.append(record)
    result = pd.DataFrame(rows)
    for column in descriptor_names:
        if column not in result.columns:
            result[column] = "MISSING"
        result[column] = result[column].fillna("MISSING")
    return result[["Ticker", *descriptor_names]].sort_values("Ticker").reset_index(drop=True)


# =============================================================================
# def 03 ROBUST GROUP AND LEAD/LAG STATISTICS
# =============================================================================


def def_validate_config(config: GroupValidationConfig) -> None:
    if not config.windows or any(int(window) <= 0 for window in config.windows):
        raise ValueError("windows must contain positive trading-session counts")
    if len(set(config.windows)) != len(config.windows):
        raise ValueError("windows must be unique")
    if not 0.0 < float(config.fdr_control_level) < 1.0:
        raise ValueError("fdr_control_level must be between zero and one")
    if config.minimum_group_members < 3:
        raise ValueError("minimum_group_members must be at least three")
    if config.null_repeats_floor < 1 or config.null_repeats_cap < config.null_repeats_floor:
        raise ValueError("invalid null repeat floor/cap")


def def_minimum_observations(window: int) -> int:
    """Sample adequacy grows with the requested horizon; it is not a return gate."""

    return max(8, int(math.ceil(2.0 * math.sqrt(window))))


def def_dynamic_max_lag(observations: int) -> int:
    return max(1, min(int(math.ceil(math.log2(max(observations, 2)))), max(1, observations // 8)))


def def_dynamic_block_length(observations: int) -> int:
    return max(2, min(int(math.ceil(observations ** (1.0 / 3.0))), max(2, observations // 4)))


def def_dynamic_null_repeats(
    window: int,
    member_count: int,
    config: GroupValidationConfig,
) -> int:
    if config.null_repeats_override is not None:
        return max(1, int(config.null_repeats_override))
    requested = int(math.ceil(6.0 * math.sqrt(max(window, 1) * max(member_count, 1))))
    repeats = max(config.null_repeats_floor, min(config.null_repeats_cap, requested))
    return repeats if repeats % 2 else repeats + 1 if repeats < config.null_repeats_cap else repeats - 1


def def_minimum_null_draws(config: GroupValidationConfig) -> int:
    return max(19, int(math.ceil(2.0 / config.fdr_control_level)) - 1)


def def_stable_seed(*parts: object, base_seed: int) -> int:
    payload = "|".join(str(part) for part in (base_seed, *parts))
    digest = hashlib.blake2s(payload.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big") % (2**32 - 1)


def def_pairwise_values(correlation: pd.DataFrame) -> np.ndarray:
    if correlation.empty or correlation.shape[0] < 2:
        return np.asarray([], dtype=float)
    values = correlation.to_numpy(dtype=float)
    upper = values[np.triu_indices_from(values, k=1)]
    return upper[np.isfinite(upper)]


def def_group_metrics(matrix: pd.DataFrame, minimum_observations: int) -> dict[str, float]:
    if matrix.empty:
        return {metric: np.nan for metric in GROUP_METRICS}
    numeric = matrix.apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    columns = [
        column
        for column in numeric.columns
        if numeric[column].notna().sum() >= minimum_observations
        and numeric[column].std(skipna=True, ddof=1) > 0
    ]
    numeric = numeric[columns]
    if numeric.shape[1] < 2:
        return {metric: np.nan for metric in GROUP_METRICS}
    correlation = numeric.corr(min_periods=minimum_observations)
    pairwise = def_pairwise_values(correlation)
    median_correlation = float(np.median(pairwise)) if pairwise.size else np.nan
    positive_ratio = float(np.mean(pairwise > 0.0)) if pairwise.size else np.nan

    complete = numeric.dropna(how="all").copy()
    for column in complete.columns:
        complete[column] = complete[column].fillna(complete[column].median(skipna=True))
    values = complete.to_numpy(dtype=float)
    pca_absorption = np.nan
    if values.shape[0] >= minimum_observations and values.shape[1] >= 2 and np.isfinite(values).all():
        centered = values - values.mean(axis=0, keepdims=True)
        scale = centered.std(axis=0, ddof=1)
        valid = np.isfinite(scale) & (scale > 0)
        standardized = centered[:, valid] / scale[valid] if valid.sum() >= 2 else np.empty((0, 0))
        if standardized.size:
            singular = np.linalg.svd(standardized, full_matrices=False, compute_uv=False)
            variance = singular**2
            if variance.sum() > 0:
                pca_absorption = float(variance[0] / variance.sum())
    return {
        "ResidualMedianCorrelation": median_correlation,
        "ResidualPositivePairRatio": positive_ratio,
        "PCAAbsorption": pca_absorption,
    }


def def_array_correlation(x: np.ndarray, y: np.ndarray) -> float:
    mask = np.isfinite(x) & np.isfinite(y)
    if int(mask.sum()) < 3:
        return np.nan
    xv = x[mask].astype(float)
    yv = y[mask].astype(float)
    xscale = xv.std(ddof=1)
    yscale = yv.std(ddof=1)
    if not np.isfinite(xscale) or not np.isfinite(yscale) or xscale <= 0 or yscale <= 0:
        return np.nan
    return float(np.corrcoef(xv, yv)[0, 1])


def def_lag_correlation(x: np.ndarray, y: np.ndarray, lag: int) -> float:
    """Positive lag means x(t) leads the leave-one-out group y(t+lag)."""

    if lag > 0:
        return def_array_correlation(x[:-lag], y[lag:]) if len(x) > lag else np.nan
    if lag < 0:
        offset = -lag
        return def_array_correlation(x[offset:], y[:-offset]) if len(x) > offset else np.nan
    return def_array_correlation(x, y)


def def_lead_lag_profile(
    member: pd.Series,
    leave_one_out: pd.Series,
    minimum_observations: int,
) -> dict[str, float]:
    paired = pd.concat(
        [member.rename("member"), leave_one_out.rename("leave_one_out")], axis=1
    ).dropna()
    if len(paired) < minimum_observations:
        return {
            "BestLag": np.nan,
            "BestLagCorrelation": np.nan,
            "ZeroLagCorrelation": np.nan,
            "LagSearchRadius": np.nan,
            "PairedObservations": float(len(paired)),
        }
    x = paired["member"].to_numpy(dtype=float)
    y = paired["leave_one_out"].to_numpy(dtype=float)
    max_lag = def_dynamic_max_lag(len(paired))
    lags = np.arange(-max_lag, max_lag + 1, dtype=int)
    correlations = np.asarray([def_lag_correlation(x, y, int(lag)) for lag in lags], dtype=float)
    finite = np.flatnonzero(np.isfinite(correlations))
    if not len(finite):
        return {
            "BestLag": np.nan,
            "BestLagCorrelation": np.nan,
            "ZeroLagCorrelation": np.nan,
            "LagSearchRadius": float(max_lag),
            "PairedObservations": float(len(paired)),
        }
    maximum = np.nanmax(correlations[finite])
    candidates = finite[np.isclose(correlations[finite], maximum, rtol=0.0, atol=EPSILON * 16)]
    best_position = min(candidates.tolist(), key=lambda position: (abs(int(lags[position])), -int(lags[position])))
    zero_position = int(np.flatnonzero(lags == 0)[0])
    return {
        "BestLag": float(lags[best_position]),
        "BestLagCorrelation": float(correlations[best_position]),
        "ZeroLagCorrelation": float(correlations[zero_position]),
        "LagSearchRadius": float(max_lag),
        "PairedObservations": float(len(paired)),
    }


def def_circular_block_shift_matrix(matrix: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    shifted = matrix.copy()
    observations = len(shifted)
    if observations < 4:
        return shifted
    block = def_dynamic_block_length(observations)
    offsets = np.arange(block, observations, block, dtype=int)
    if not len(offsets):
        offsets = np.arange(1, observations, dtype=int)
    for column in shifted.columns:
        offset = int(rng.choice(offsets))
        shifted[column] = np.roll(shifted[column].to_numpy(dtype=float), offset)
    return shifted


def def_empirical_upper_p(observed: float, null_values: Sequence[float]) -> float:
    null = np.asarray(null_values, dtype=float)
    null = null[np.isfinite(null)]
    if not np.isfinite(observed) or not len(null):
        return np.nan
    return float((1.0 + np.sum(null >= observed)) / (len(null) + 1.0))


def def_benjamini_hochberg(pvalues: pd.Series | Sequence[float]) -> pd.Series:
    series = pd.Series(pvalues, copy=True, dtype=float)
    output = pd.Series(np.nan, index=series.index, dtype=float)
    valid = series[np.isfinite(series) & series.between(0.0, 1.0)]
    if valid.empty:
        return output
    ordered = valid.sort_values(kind="mergesort")
    count = len(ordered)
    adjusted = ordered.to_numpy(dtype=float) * count / np.arange(1, count + 1, dtype=float)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    adjusted = np.clip(adjusted, 0.0, 1.0)
    output.loc[ordered.index] = adjusted
    return output


# =============================================================================
# def 04 MATCHED, RANDOM AND CIRCULAR NULL GENERATORS
# =============================================================================


def def_available_match_columns(
    descriptors: pd.DataFrame,
    tickers: Sequence[str],
    config: GroupValidationConfig,
) -> list[str]:
    subset = descriptors.loc[descriptors["Ticker"].isin(tickers)]
    return [
        column
        for column in config.match_columns
        if column in subset.columns and subset[column].notna().any() and subset[column].ne("MISSING").any()
    ]


def def_sample_matched_tickers(
    target_tickers: Sequence[str],
    outside_tickers: Sequence[str],
    descriptors: pd.DataFrame,
    match_columns: Sequence[str],
    rng: np.random.Generator,
) -> tuple[list[str], str]:
    if not match_columns:
        return [], "BLOCKED_NO_MATCH_COLUMNS"
    descriptor = descriptors.drop_duplicates("Ticker", keep="last").set_index("Ticker")
    available = list(dict.fromkeys(str(ticker) for ticker in outside_tickers))
    chosen: list[str] = []
    depths: list[int] = []
    for target in target_tickers:
        remaining = [ticker for ticker in available if ticker not in set(chosen)]
        if not remaining:
            return [], "BLOCKED_OUTSIDE_POOL_EXHAUSTED"
        selected_pool: list[str] = []
        selected_depth = 0
        if target in descriptor.index:
            for depth in range(len(match_columns), 0, -1):
                keys = list(match_columns[:depth])
                desired = descriptor.loc[target, keys]
                if isinstance(desired, pd.DataFrame):
                    desired = desired.iloc[-1]
                candidates: list[str] = []
                for candidate in remaining:
                    if candidate not in descriptor.index:
                        continue
                    observed = descriptor.loc[candidate, keys]
                    if isinstance(observed, pd.DataFrame):
                        observed = observed.iloc[-1]
                    if all(str(observed[key]) == str(desired[key]) for key in keys):
                        candidates.append(candidate)
                if candidates:
                    selected_pool = candidates
                    selected_depth = depth
                    break
        if not selected_pool:
            selected_pool = remaining
            selected_depth = 0
        chosen.append(str(rng.choice(np.asarray(selected_pool, dtype=object))))
        depths.append(selected_depth)
    minimum_depth = min(depths) if depths else 0
    if minimum_depth == len(match_columns):
        mode = "EXACT:" + "+".join(match_columns)
    elif minimum_depth > 0:
        mode = "RELAXED:" + "+".join(match_columns[:minimum_depth])
    else:
        mode = "RANDOM_FALLBACK"
    return chosen, mode


def def_group_null_distributions(
    window_panel: pd.DataFrame,
    group_id: str,
    group_tickers: Sequence[str],
    eligible_tickers: Sequence[str],
    descriptors: pd.DataFrame,
    minimum_observations: int,
    repeats: int,
    snapshot_date: pd.Timestamp,
    window: int,
    config: GroupValidationConfig,
) -> tuple[dict[str, dict[str, list[float]]], list[dict[str, object]], dict[str, object]]:
    outside = [ticker for ticker in eligible_tickers if ticker not in set(group_tickers)]
    distributions = {
        null_type: {metric: [] for metric in GROUP_METRICS} for null_type in NULL_TYPES
    }
    ledger: list[dict[str, object]] = []
    match_columns = def_available_match_columns(descriptors, [*group_tickers, *outside], config)
    if len(outside) < len(group_tickers):
        return distributions, ledger, {
            "MatchColumns": "+".join(match_columns) or "NONE",
            "NullReason": "OUTSIDE_POOL_SMALLER_THAN_GROUP",
        }
    group_matrix = window_panel[list(group_tickers)]
    rng = np.random.default_rng(
        def_stable_seed(snapshot_date.date(), window, group_id, "GROUP_NULL", base_seed=config.random_seed)
    )
    match_modes: dict[str, int] = {}
    for draw in range(repeats):
        matched, match_mode = def_sample_matched_tickers(
            group_tickers,
            outside,
            descriptors,
            match_columns,
            rng,
        )
        if matched:
            metrics = def_group_metrics(window_panel[matched], minimum_observations)
            match_modes[match_mode] = match_modes.get(match_mode, 0) + 1
            for metric, value in metrics.items():
                if np.isfinite(value):
                    distributions["MATCHED"][metric].append(float(value))
            ledger.append(
                {
                    "NullLevel": "GROUP",
                    "SnapshotDate": snapshot_date,
                    "Window": window,
                    "GroupId": group_id,
                    "Ticker": pd.NA,
                    "NullType": "MATCHED",
                    "Draw": draw,
                    "MatchMode": match_mode,
                    **metrics,
                    "BestLagCorrelation": np.nan,
                }
            )

        random_tickers = list(rng.choice(np.asarray(outside, dtype=object), size=len(group_tickers), replace=False))
        random_metrics = def_group_metrics(window_panel[random_tickers], minimum_observations)
        for metric, value in random_metrics.items():
            if np.isfinite(value):
                distributions["RANDOM"][metric].append(float(value))
        ledger.append(
            {
                "NullLevel": "GROUP",
                "SnapshotDate": snapshot_date,
                "Window": window,
                "GroupId": group_id,
                "Ticker": pd.NA,
                "NullType": "RANDOM",
                "Draw": draw,
                "MatchMode": "UNRESTRICTED",
                **random_metrics,
                "BestLagCorrelation": np.nan,
            }
        )

        shifted = def_circular_block_shift_matrix(group_matrix, rng)
        shifted_metrics = def_group_metrics(shifted, minimum_observations)
        for metric, value in shifted_metrics.items():
            if np.isfinite(value):
                distributions["CIRCULAR_BLOCK_SHIFT"][metric].append(float(value))
        ledger.append(
            {
                "NullLevel": "GROUP",
                "SnapshotDate": snapshot_date,
                "Window": window,
                "GroupId": group_id,
                "Ticker": pd.NA,
                "NullType": "CIRCULAR_BLOCK_SHIFT",
                "Draw": draw,
                "MatchMode": "INDEPENDENT_MEMBER_OFFSETS",
                **shifted_metrics,
                "BestLagCorrelation": np.nan,
            }
        )
    effective_match = any(
        mode.startswith("EXACT:") or mode.startswith("RELAXED:") for mode in match_modes
    )
    return distributions, ledger, {
        "MatchColumns": "+".join(match_columns) or "NONE",
        "NullReason": (
            "PASS"
            if match_columns and effective_match
            else "NO_EFFECTIVE_MATCH"
            if match_columns
            else "NO_MATCH_COLUMNS"
        ),
        "MatchModeCounts": json.dumps(match_modes, ensure_ascii=False, sort_keys=True),
    }


def def_member_null_distributions(
    window_panel: pd.DataFrame,
    group_id: str,
    ticker: str,
    group_tickers: Sequence[str],
    eligible_tickers: Sequence[str],
    descriptors: pd.DataFrame,
    leave_one_out: pd.Series,
    minimum_observations: int,
    repeats: int,
    snapshot_date: pd.Timestamp,
    window: int,
    config: GroupValidationConfig,
) -> tuple[dict[str, list[float]], list[dict[str, object]], dict[str, object]]:
    outside = [candidate for candidate in eligible_tickers if candidate not in set(group_tickers)]
    distributions = {null_type: [] for null_type in NULL_TYPES}
    ledger: list[dict[str, object]] = []
    match_columns = def_available_match_columns(descriptors, [ticker, *outside], config)
    if not outside:
        return distributions, ledger, {
            "MatchColumns": "+".join(match_columns) or "NONE",
            "NullReason": "EMPTY_OUTSIDE_POOL",
        }
    paired = pd.concat(
        [window_panel[ticker].rename("member"), leave_one_out.rename("leave_one_out")], axis=1
    ).dropna()
    rng = np.random.default_rng(
        def_stable_seed(
            snapshot_date.date(), window, group_id, ticker, "MEMBER_NULL", base_seed=config.random_seed
        )
    )
    match_modes: dict[str, int] = {}
    for draw in range(repeats):
        matched, match_mode = def_sample_matched_tickers(
            [ticker], outside, descriptors, match_columns, rng
        )
        if matched:
            matched_profile = def_lead_lag_profile(
                window_panel[matched[0]], leave_one_out, minimum_observations
            )
            matched_value = matched_profile["BestLagCorrelation"]
            if np.isfinite(matched_value):
                distributions["MATCHED"].append(float(matched_value))
            match_modes[match_mode] = match_modes.get(match_mode, 0) + 1
            ledger.append(
                {
                    "NullLevel": "MEMBER",
                    "SnapshotDate": snapshot_date,
                    "Window": window,
                    "GroupId": group_id,
                    "Ticker": ticker,
                    "NullType": "MATCHED",
                    "Draw": draw,
                    "MatchMode": match_mode,
                    **{metric: np.nan for metric in GROUP_METRICS},
                    "BestLagCorrelation": matched_value,
                }
            )

        random_ticker = str(rng.choice(np.asarray(outside, dtype=object)))
        random_profile = def_lead_lag_profile(
            window_panel[random_ticker], leave_one_out, minimum_observations
        )
        random_value = random_profile["BestLagCorrelation"]
        if np.isfinite(random_value):
            distributions["RANDOM"].append(float(random_value))
        ledger.append(
            {
                "NullLevel": "MEMBER",
                "SnapshotDate": snapshot_date,
                "Window": window,
                "GroupId": group_id,
                "Ticker": ticker,
                "NullType": "RANDOM",
                "Draw": draw,
                "MatchMode": "UNRESTRICTED",
                **{metric: np.nan for metric in GROUP_METRICS},
                "BestLagCorrelation": random_value,
            }
        )

        shifted_value = np.nan
        if len(paired) >= minimum_observations:
            values = paired["member"].to_numpy(dtype=float)
            block = def_dynamic_block_length(len(values))
            offsets = np.arange(block, len(values), block, dtype=int)
            if not len(offsets):
                offsets = np.arange(1, len(values), dtype=int)
            shifted_member = pd.Series(
                np.roll(values, int(rng.choice(offsets))), index=paired.index, dtype=float
            )
            shifted_profile = def_lead_lag_profile(
                shifted_member,
                paired["leave_one_out"],
                minimum_observations,
            )
            shifted_value = shifted_profile["BestLagCorrelation"]
            if np.isfinite(shifted_value):
                distributions["CIRCULAR_BLOCK_SHIFT"].append(float(shifted_value))
        ledger.append(
            {
                "NullLevel": "MEMBER",
                "SnapshotDate": snapshot_date,
                "Window": window,
                "GroupId": group_id,
                "Ticker": ticker,
                "NullType": "CIRCULAR_BLOCK_SHIFT",
                "Draw": draw,
                "MatchMode": "CIRCULAR_BLOCK_OFFSET",
                **{metric: np.nan for metric in GROUP_METRICS},
                "BestLagCorrelation": shifted_value,
            }
        )
    effective_match = any(
        mode.startswith("EXACT:") or mode.startswith("RELAXED:") for mode in match_modes
    )
    return distributions, ledger, {
        "MatchColumns": "+".join(match_columns) or "NONE",
        "NullReason": (
            "PASS"
            if match_columns and effective_match
            else "NO_EFFECTIVE_MATCH"
            if match_columns
            else "NO_MATCH_COLUMNS"
        ),
        "MatchModeCounts": json.dumps(match_modes, ensure_ascii=False, sort_keys=True),
    }


def def_null_reference(
    observed: float,
    distributions: Mapping[str, Sequence[float]],
    minimum_draws: int,
) -> tuple[float, float, dict[str, float], dict[str, int]]:
    medians: dict[str, float] = {}
    pvalues: dict[str, float] = {}
    counts: dict[str, int] = {}
    for null_type in NULL_TYPES:
        values = np.asarray(distributions.get(null_type, []), dtype=float)
        values = values[np.isfinite(values)]
        counts[null_type] = int(len(values))
        if len(values) >= minimum_draws:
            medians[null_type] = float(np.median(values))
            pvalues[null_type] = def_empirical_upper_p(observed, values)
        else:
            medians[null_type] = np.nan
            pvalues[null_type] = np.nan
    if not all(np.isfinite(pvalues.get(null_type, np.nan)) for null_type in NULL_TYPES):
        return np.nan, np.nan, pvalues, counts
    reference = float(max(medians.values()))
    conservative_p = float(max(pvalues.values()))
    return reference, conservative_p, pvalues, counts


# =============================================================================
# def 05 GROUP VALIDATION AND FOUR-ROLE CLASSIFICATION
# =============================================================================


def def_evidence_status(reasons: Sequence[str]) -> tuple[str, str]:
    clean = sorted(set(reason for reason in reasons if reason and reason != "PASS"))
    return ("READY", "PASS") if not clean else ("BLOCKED", "|".join(clean))


def def_empty_group_record(
    snapshot_date: pd.Timestamp,
    effective_date: pd.Timestamp | pd.NaT,
    window: int,
    group_id: str,
    group_name: str,
    candidate_count: int,
) -> dict[str, object]:
    record: dict[str, object] = {
        "SnapshotDate": snapshot_date,
        "EffectiveDate": effective_date,
        "Window": window,
        "GroupId": group_id,
        "GroupName": group_name,
        "CandidateMemberCount": candidate_count,
        "EvaluatedMemberCount": 0,
        "WindowSessionCount": 0,
        "MinimumObservations": def_minimum_observations(window),
        "NullRepeats": 0,
        "MatchColumns": "NONE",
        "MatchModeCounts": "{}",
        "EvidenceStatus": "BLOCKED",
        "EvidenceReason": "UNINITIALIZED",
        "GroupIntersectionPValue": np.nan,
        "GroupQValue": np.nan,
        "PositiveEvidenceAxes": 0,
        "FDRConfirmedAxes": 0,
        "GroupDecision": "HOLD",
    }
    for metric in GROUP_METRICS:
        record[metric] = np.nan
        record[f"NullReference_{metric}"] = np.nan
        record[f"Lift_{metric}"] = np.nan
        record[f"RawP_{metric}"] = np.nan
        record[f"QValue_{metric}"] = np.nan
        for null_type in NULL_TYPES:
            record[f"P_{null_type}_{metric}"] = np.nan
            record[f"NullN_{null_type}_{metric}"] = 0
    return record


def def_group_record(
    window_panel: pd.DataFrame,
    membership_rows: pd.DataFrame,
    eligible_tickers: Sequence[str],
    descriptors: pd.DataFrame,
    snapshot_date: pd.Timestamp,
    effective_date: pd.Timestamp | pd.NaT,
    window: int,
    provenance: Mapping[str, object],
    config: GroupValidationConfig,
) -> tuple[dict[str, object], list[dict[str, object]], list[str]]:
    group_id = str(membership_rows["GroupId"].iloc[0])
    group_name = str(membership_rows["GroupName"].iloc[0])
    candidate = membership_rows["Ticker"].drop_duplicates().tolist()
    record = def_empty_group_record(
        snapshot_date, effective_date, window, group_id, group_name, len(candidate)
    )
    cohort_values = sorted(set(membership_rows["_ValidationCohort"].astype(str)))
    record["ValidationCohort"] = (
        cohort_values[0] if len(cohort_values) == 1 else "MIXED:" + "+".join(cohort_values)
    )
    record["IndexEligible"] = bool(membership_rows["_IndexEligible"].all())
    record["ApprovalBoundary"] = "STATISTICAL_PASS_DOES_NOT_APPROVE_PROPOSED_MEMBERSHIP"
    reasons: list[str] = []
    if provenance["EvidenceStatus"] != "READY" and config.require_residual_provenance:
        reasons.append(str(provenance["EvidenceReason"]))
    if pd.isna(effective_date):
        reasons.append("NO_NEXT_TRADING_SESSION")
    if len(window_panel) < window:
        reasons.append("INCOMPLETE_WINDOW_HISTORY")
    minimum_observations = def_minimum_observations(window)
    evaluated = [
        ticker
        for ticker in candidate
        if ticker in window_panel.columns
        and window_panel[ticker].notna().sum() >= minimum_observations
        and window_panel[ticker].std(skipna=True, ddof=1) > 0
    ]
    record["EvaluatedMemberCount"] = len(evaluated)
    record["WindowSessionCount"] = len(window_panel)
    if len(evaluated) < config.minimum_group_members:
        reasons.append("INSUFFICIENT_EVALUATED_MEMBERS")
    if len(eligible_tickers) - len(evaluated) < len(evaluated):
        reasons.append("INSUFFICIENT_OUTSIDE_NULL_POOL")
    metrics = def_group_metrics(window_panel[evaluated], minimum_observations) if evaluated else {
        metric: np.nan for metric in GROUP_METRICS
    }
    record.update(metrics)
    if any(not np.isfinite(metrics[metric]) for metric in GROUP_METRICS):
        reasons.append("NONFINITE_GROUP_METRICS")

    repeats = def_dynamic_null_repeats(window, len(evaluated), config)
    record["NullRepeats"] = repeats
    null_ledger: list[dict[str, object]] = []
    if not reasons or set(reasons).issubset({str(provenance.get("EvidenceReason", ""))}):
        distributions, null_ledger, null_meta = def_group_null_distributions(
            window_panel,
            group_id,
            evaluated,
            eligible_tickers,
            descriptors,
            minimum_observations,
            repeats,
            snapshot_date,
            window,
            config,
        )
        record["MatchColumns"] = null_meta.get("MatchColumns", "NONE")
        record["MatchModeCounts"] = null_meta.get("MatchModeCounts", "{}")
        if null_meta.get("NullReason") != "PASS":
            reasons.append(str(null_meta.get("NullReason")))
        minimum_draws = def_minimum_null_draws(config)
        axis_pvalues: list[float] = []
        positive_axes = 0
        for metric in GROUP_METRICS:
            metric_distributions = {
                null_type: distributions[null_type][metric] for null_type in NULL_TYPES
            }
            reference, raw_p, p_by_type, counts = def_null_reference(
                float(metrics[metric]), metric_distributions, minimum_draws
            )
            lift = float(metrics[metric] - reference) if np.isfinite(reference) else np.nan
            record[f"NullReference_{metric}"] = reference
            record[f"Lift_{metric}"] = lift
            record[f"RawP_{metric}"] = raw_p
            for null_type in NULL_TYPES:
                record[f"P_{null_type}_{metric}"] = p_by_type[null_type]
                record[f"NullN_{null_type}_{metric}"] = counts[null_type]
            if np.isfinite(lift) and lift > 0:
                positive_axes += 1
            if np.isfinite(raw_p):
                axis_pvalues.append(raw_p)
        record["PositiveEvidenceAxes"] = positive_axes
        if len(axis_pvalues) == len(GROUP_METRICS):
            record["GroupIntersectionPValue"] = float(max(axis_pvalues))
        else:
            reasons.append("INCOMPLETE_THREE_NULL_EVIDENCE")
    status, reason = def_evidence_status(reasons)
    record["EvidenceStatus"] = status
    record["EvidenceReason"] = reason
    return record, null_ledger, evaluated


def def_member_record(
    window_panel: pd.DataFrame,
    group_id: str,
    group_name: str,
    ticker: str,
    group_tickers: Sequence[str],
    eligible_tickers: Sequence[str],
    descriptors: pd.DataFrame,
    snapshot_date: pd.Timestamp,
    effective_date: pd.Timestamp | pd.NaT,
    window: int,
    provenance: Mapping[str, object],
    config: GroupValidationConfig,
    validation_cohort: str,
    index_eligible: bool,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    minimum_observations = def_minimum_observations(window)
    repeats = def_dynamic_null_repeats(window, len(group_tickers), config)
    reasons: list[str] = []
    if provenance["EvidenceStatus"] != "READY" and config.require_residual_provenance:
        reasons.append(str(provenance["EvidenceReason"]))
    if pd.isna(effective_date):
        reasons.append("NO_NEXT_TRADING_SESSION")
    if len(window_panel) < window:
        reasons.append("INCOMPLETE_WINDOW_HISTORY")
    if ticker not in window_panel.columns:
        reasons.append("TICKER_MISSING_FROM_RESIDUAL_PANEL")
        member = pd.Series(index=window_panel.index, dtype=float)
    else:
        member = window_panel[ticker]
    other_tickers = [candidate for candidate in group_tickers if candidate != ticker]
    if len(other_tickers) < 2:
        reasons.append("INSUFFICIENT_LEAVE_ONE_OUT_MEMBERS")
        leave_one_out = pd.Series(index=window_panel.index, dtype=float)
    else:
        leave_one_out = window_panel[other_tickers].median(axis=1, skipna=True)
    profile = def_lead_lag_profile(member, leave_one_out, minimum_observations)
    if not np.isfinite(profile["BestLagCorrelation"]):
        reasons.append("INSUFFICIENT_PAIRED_OBSERVATIONS")
    record: dict[str, object] = {
        "SnapshotDate": snapshot_date,
        "EffectiveDate": effective_date,
        "Window": window,
        "GroupId": group_id,
        "GroupName": group_name,
        "Ticker": ticker,
        "ValidationCohort": validation_cohort,
        "IndexEligible": bool(index_eligible),
        "ApprovalBoundary": "STATISTICAL_ROLE_DOES_NOT_APPROVE_PROPOSED_MEMBERSHIP",
        "LeaveOneOutMethod": "CROSS_SECTIONAL_MEDIAN_EXCLUDING_MEMBER",
        "MinimumObservations": minimum_observations,
        "NullRepeats": repeats,
        **profile,
        "NullReferenceBestLagCorrelation": np.nan,
        "AssociationLiftVsNull": np.nan,
        "AssociationPValue": np.nan,
        "AssociationQValue": np.nan,
        "P_MATCHED": np.nan,
        "P_RANDOM": np.nan,
        "P_CIRCULAR_BLOCK_SHIFT": np.nan,
        "NullN_MATCHED": 0,
        "NullN_RANDOM": 0,
        "NullN_CIRCULAR_BLOCK_SHIFT": 0,
        "MatchColumns": "NONE",
        "MatchModeCounts": "{}",
        "EvidenceStatus": "BLOCKED",
        "EvidenceReason": "UNINITIALIZED",
        "Role": pd.NA,
    }
    null_ledger: list[dict[str, object]] = []
    if not reasons or set(reasons).issubset({str(provenance.get("EvidenceReason", ""))}):
        distributions, null_ledger, null_meta = def_member_null_distributions(
            window_panel,
            group_id,
            ticker,
            group_tickers,
            eligible_tickers,
            descriptors,
            leave_one_out,
            minimum_observations,
            repeats,
            snapshot_date,
            window,
            config,
        )
        record["MatchColumns"] = null_meta.get("MatchColumns", "NONE")
        record["MatchModeCounts"] = null_meta.get("MatchModeCounts", "{}")
        if null_meta.get("NullReason") != "PASS":
            reasons.append(str(null_meta.get("NullReason")))
        reference, raw_p, p_by_type, counts = def_null_reference(
            float(profile["BestLagCorrelation"]),
            distributions,
            def_minimum_null_draws(config),
        )
        record["NullReferenceBestLagCorrelation"] = reference
        record["AssociationLiftVsNull"] = (
            float(profile["BestLagCorrelation"] - reference) if np.isfinite(reference) else np.nan
        )
        record["AssociationPValue"] = raw_p
        for null_type in NULL_TYPES:
            record[f"P_{null_type}"] = p_by_type[null_type]
            record[f"NullN_{null_type}"] = counts[null_type]
        if not np.isfinite(raw_p):
            reasons.append("INCOMPLETE_THREE_NULL_EVIDENCE")
    status, reason = def_evidence_status(reasons)
    record["EvidenceStatus"] = status
    record["EvidenceReason"] = reason
    return record, null_ledger


def def_apply_group_fdr(group_validation: pd.DataFrame, config: GroupValidationConfig) -> pd.DataFrame:
    result = group_validation.copy()
    for window, index in result.groupby("Window", sort=True).groups.items():
        ready_index = [position for position in index if result.at[position, "EvidenceStatus"] == "READY"]
        if not ready_index:
            continue
        result.loc[ready_index, "GroupQValue"] = def_benjamini_hochberg(
            result.loc[ready_index, "GroupIntersectionPValue"]
        )
        for metric in GROUP_METRICS:
            result.loc[ready_index, f"QValue_{metric}"] = def_benjamini_hochberg(
                result.loc[ready_index, f"RawP_{metric}"]
            )
    for index, row in result.iterrows():
        if row["EvidenceStatus"] != "READY":
            result.at[index, "GroupDecision"] = "HOLD"
            result.at[index, "FDRConfirmedAxes"] = 0
            continue
        axis_q = np.asarray([row[f"QValue_{metric}"] for metric in GROUP_METRICS], dtype=float)
        confirmed = int(np.sum(np.isfinite(axis_q) & (axis_q <= config.fdr_control_level)))
        result.at[index, "FDRConfirmedAxes"] = confirmed
        positive = int(row["PositiveEvidenceAxes"])
        group_q = float(row["GroupQValue"]) if np.isfinite(row["GroupQValue"]) else np.nan
        if positive == len(GROUP_METRICS) and np.isfinite(group_q) and group_q <= config.fdr_control_level:
            decision = "PASS"
        elif positive == 0:
            decision = "FAIL"
        else:
            decision = "HOLD"
        result.at[index, "GroupDecision"] = decision
    return result


def def_apply_member_fdr(member_roles: pd.DataFrame, config: GroupValidationConfig) -> pd.DataFrame:
    result = member_roles.copy()
    for window, index in result.groupby("Window", sort=True).groups.items():
        ready_index = [position for position in index if result.at[position, "EvidenceStatus"] == "READY"]
        if not ready_index:
            continue
        result.loc[ready_index, "AssociationQValue"] = def_benjamini_hochberg(
            result.loc[ready_index, "AssociationPValue"]
        )
    for index, row in result.iterrows():
        if row["EvidenceStatus"] != "READY":
            result.at[index, "Role"] = pd.NA
            continue
        qvalue = float(row["AssociationQValue"]) if np.isfinite(row["AssociationQValue"]) else np.nan
        lift = float(row["AssociationLiftVsNull"]) if np.isfinite(row["AssociationLiftVsNull"]) else np.nan
        if not np.isfinite(qvalue) or qvalue > config.fdr_control_level or not np.isfinite(lift) or lift <= 0:
            role = "UNRELATED"
        else:
            lag = int(row["BestLag"])
            role = "LEAD" if lag > 0 else "LAG" if lag < 0 else "PEER"
        result.at[index, "Role"] = role
    return result


def def_run_group_validation(
    residual_panel: pd.DataFrame,
    membership: pd.DataFrame,
    *,
    as_of_date: object | None = None,
    decision_at: object | None = None,
    trading_calendar: Iterable[object] | None = None,
    match_features: pd.DataFrame | None = None,
    market_cap_panel: pd.DataFrame | None = None,
    config: GroupValidationConfig = GroupValidationConfig(),
) -> GroupValidationResult:
    """Validate story groups and assign LEAD/PEER/LAG/UNRELATED per window.

    The residual input must prove, through constant columns or ``DataFrame``
    attrs, ``MarketUniverse=TWSE_TPEX_COMMON_EQUITY_EX_2330``,
    ``TSMCExcluded=True`` and ``PointInTime=True``.  Missing proof fails closed
    to ``EvidenceStatus=BLOCKED``.  Computed classifications become effective
    only on the first supplied trading session strictly after ``SnapshotDate``.
    """

    def_validate_config(config)
    provenance = def_residual_provenance(residual_panel, config)
    prepared = def_prepare_residual_panel(residual_panel)
    if prepared.empty:
        raise ValueError("residual panel is empty")
    snapshot = def_parse_date(as_of_date) if as_of_date is not None else prepared["Date"].max()
    if pd.isna(snapshot):
        raise ValueError("as_of_date is invalid")
    decision = def_decision_timestamp(snapshot, decision_at)
    all_sessions = (
        def_prepare_trading_calendar(trading_calendar)
        if trading_calendar is not None
        else def_prepare_trading_calendar(prepared["Date"].unique())
    )
    effective_date = def_next_trading_session(snapshot, all_sessions)

    analysis_rows = prepared.loc[prepared["Date"].le(snapshot)].copy()
    if "KnownAt" in analysis_rows.columns:
        analysis_rows = analysis_rows.loc[
            analysis_rows["KnownAt"].notna() & analysis_rows["KnownAt"].le(decision)
        ]
    if analysis_rows.empty:
        raise ValueError("no residual observations are known by the requested decision timestamp")
    wide = analysis_rows.pivot(index="Date", columns="Ticker", values="ResidualReturn").sort_index()
    active = def_prepare_active_membership(membership, snapshot, decision)
    if active.empty:
        raise ValueError("no approved membership is active at the snapshot date")

    size_tiers = None
    if market_cap_panel is not None:
        size_tiers = def_build_dynamic_size_tiers(
            market_cap_panel,
            snapshot,
            decision_at=decision,
            tsmc_ticker=config.tsmc_ticker,
        )
    descriptors = def_prepare_match_features(active, match_features, size_tiers)

    group_records: list[dict[str, object]] = []
    member_records: list[dict[str, object]] = []
    null_records: list[dict[str, object]] = []
    for window in config.windows:
        window_panel = wide.tail(int(window)).copy()
        minimum_observations = def_minimum_observations(int(window))
        eligible_tickers = [
            ticker
            for ticker in window_panel.columns
            if window_panel[ticker].notna().sum() >= minimum_observations
            and window_panel[ticker].std(skipna=True, ddof=1) > 0
        ]
        evaluated_by_group: dict[str, list[str]] = {}
        for group_id, membership_rows in active.groupby("GroupId", sort=True):
            group_record, group_null, evaluated = def_group_record(
                window_panel,
                membership_rows,
                eligible_tickers,
                descriptors,
                snapshot,
                effective_date,
                int(window),
                provenance,
                config,
            )
            group_records.append(group_record)
            null_records.extend(group_null)
            evaluated_by_group[str(group_id)] = evaluated

        for group_id, membership_rows in active.groupby("GroupId", sort=True):
            group_name = str(membership_rows["GroupName"].iloc[0])
            evaluated = evaluated_by_group[str(group_id)]
            candidate = membership_rows["Ticker"].drop_duplicates().tolist()
            role_group = evaluated if len(evaluated) >= config.minimum_group_members else candidate
            for ticker in candidate:
                membership_entry = membership_rows.loc[membership_rows["Ticker"].eq(ticker)].iloc[-1]
                member_record, member_null = def_member_record(
                    window_panel,
                    str(group_id),
                    group_name,
                    ticker,
                    role_group,
                    eligible_tickers,
                    descriptors,
                    snapshot,
                    effective_date,
                    int(window),
                    provenance,
                    config,
                    str(membership_entry["_ValidationCohort"]),
                    bool(membership_entry["_IndexEligible"]),
                )
                member_records.append(member_record)
                null_records.extend(member_null)

    group_validation = def_apply_group_fdr(pd.DataFrame(group_records), config)
    member_roles = def_apply_member_fdr(pd.DataFrame(member_records), config)
    group_decisions = group_validation[
        ["SnapshotDate", "Window", "GroupId", "GroupDecision"]
    ].drop_duplicates()
    member_roles = member_roles.merge(
        group_decisions,
        on=["SnapshotDate", "Window", "GroupId"],
        how="left",
        validate="many_to_one",
    )
    null_ledger = pd.DataFrame(null_records)
    metadata = {
        "EngineId": ENGINE_ID,
        "EngineVersion": ENGINE_VERSION,
        "SnapshotDate": snapshot,
        "EffectiveDate": effective_date,
        "DecisionAt": decision,
        "Windows": tuple(int(window) for window in config.windows),
        "FDRControlLevel": config.fdr_control_level,
        "GroupTest": "THREE_NULL_INTERSECTION_UNION_THEN_BH_FDR",
        "MemberTest": "LOO_MAX_OVER_LAGS_THREE_NULL_THEN_BH_FDR",
        "CompositeScorePolicy": "PROHIBITED",
        "MarketThresholdPolicy": "NO_FIXED_MARKET_THRESHOLDS",
        "MultiLabelMembership": bool(active.duplicated("Ticker", keep=False).any()),
        "ActiveMembershipRows": int(len(active)),
        "ActiveUniqueTickers": int(active["Ticker"].nunique()),
        "ApprovedPITRows": int(active["_ValidationCohort"].eq("APPROVED_PIT").sum()),
        "ProposedValidationRows": int(active["_ValidationCohort"].eq("PROPOSED_VALIDATION").sum()),
        "IndexEligibleRows": int(active["_IndexEligible"].sum()),
        "ApprovalPolicy": "VALIDATION_COHORT_PASS_REQUIRES_SEPARATE_HUMAN_APPROVAL",
        **provenance,
    }
    return GroupValidationResult(
        group_validation=group_validation.sort_values(["Window", "GroupId"]).reset_index(drop=True),
        member_roles=member_roles.sort_values(["Window", "GroupId", "Ticker"]).reset_index(drop=True),
        null_ledger=null_ledger.sort_values(
            ["Window", "GroupId", "NullLevel", "Ticker", "NullType", "Draw"],
            na_position="first",
        ).reset_index(drop=True)
        if not null_ledger.empty
        else null_ledger,
        metadata=metadata,
    )


# =============================================================================
# def 06 DETERMINISTIC SELF-TEST
# =============================================================================


def def_self_test_fixture() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DatetimeIndex, pd.Timestamp]:
    rng = np.random.default_rng(50200)
    calendar = pd.bdate_range("2024-01-02", periods=302)
    snapshot = calendar[-2]
    observations = len(calendar)
    driver_a = rng.normal(0.0, 0.012, observations + 2)
    driver_b = rng.normal(0.0, 0.010, observations + 2)
    data: dict[str, np.ndarray] = {}
    group_a: list[str] = []
    for position in range(8):
        ticker = f"A{position + 1:03d}"
        group_a.append(ticker)
        data[ticker] = driver_a[1 : observations + 1] + rng.normal(0.0, 0.0015, observations)
    data["ALEAD"] = driver_a[2 : observations + 2] + rng.normal(0.0, 0.0015, observations)
    data["ALAG"] = driver_a[:observations] + rng.normal(0.0, 0.0015, observations)
    data["AUNR"] = rng.normal(0.0, 0.012, observations)
    group_a.extend(["ALEAD", "ALAG", "AUNR"])

    group_b: list[str] = []
    for position in range(6):
        ticker = f"B{position + 1:03d}"
        group_b.append(ticker)
        data[ticker] = driver_b[1 : observations + 1] + rng.normal(0.0, 0.0020, observations)
    group_noise: list[str] = []
    for position in range(6):
        ticker = f"N{position + 1:03d}"
        group_noise.append(ticker)
        data[ticker] = rng.normal(0.0, 0.012, observations)
    for position in range(36):
        data[f"X{position + 1:03d}"] = rng.normal(0.0, 0.012, observations)

    wide = pd.DataFrame(data, index=calendar)
    residual = wide.rename_axis("Date").reset_index().melt(
        id_vars="Date", var_name="Ticker", value_name="ResidualReturn"
    )
    residual.attrs.update(
        {
            "MarketUniverse": EXPECTED_RESIDUAL_UNIVERSE,
            "TSMCExcluded": True,
            "PointInTime": True,
        }
    )
    membership_rows: list[dict[str, object]] = []
    for group_id, tickers in (
        ("G_COHERENT", group_a),
        ("G_SECOND", group_b),
        ("G_NOISE", group_noise),
    ):
        for ticker in tickers:
            membership_rows.append(
                {
                    "GroupId": group_id,
                    "GroupName": group_id,
                    "Ticker": ticker,
                    "EffectiveDate": calendar[0],
                    "ApprovalStatus": "APPROVED",
                }
            )
    membership_rows.append(
        {
            "GroupId": "G_SECOND",
            "GroupName": "G_SECOND",
            "Ticker": "A001",
            "EffectiveDate": calendar[0],
            "ApprovalStatus": "APPROVED",
        }
    )
    membership = pd.DataFrame(membership_rows)
    descriptors = pd.DataFrame({"Ticker": list(data)})
    descriptors["Market"] = np.where(np.arange(len(descriptors)) % 2 == 0, "TWSE", "TPEX")
    descriptors["SizeTier"] = np.asarray(["SMALL", "MID", "LARGE"], dtype=object)[
        np.arange(len(descriptors)) % 3
    ]
    descriptors["LiquidityTier"] = np.asarray(["LOW", "MID", "HIGH"], dtype=object)[
        (np.arange(len(descriptors)) // 3) % 3
    ]
    return residual, membership, descriptors, calendar, snapshot


def def_run_self_test() -> dict[str, object]:
    residual, membership, descriptors, calendar, snapshot = def_self_test_fixture()
    # Nineteen draws are the structural minimum at q=0.10.  Production calls
    # leave the override unset and therefore use the larger dynamic 99–399 run.
    config = GroupValidationConfig(null_repeats_override=19)
    result = def_run_group_validation(
        residual,
        membership,
        as_of_date=snapshot,
        trading_calendar=calendar,
        match_features=descriptors,
        config=config,
    )
    expected_effective = calendar[-1]
    assert set(result.group_validation["Window"]) == set(DEFAULT_WINDOWS)
    assert set(result.group_validation["GroupDecision"]).issubset({"PASS", "HOLD", "FAIL"})
    ready_roles = result.member_roles.loc[result.member_roles["EvidenceStatus"].eq("READY"), "Role"]
    assert set(ready_roles.dropna()).issubset(set(ROLE_VALUES))
    assert result.group_validation["EffectiveDate"].eq(expected_effective).all()
    assert result.member_roles["EffectiveDate"].eq(expected_effective).all()
    assert set(result.null_ledger["NullType"]) == set(NULL_TYPES)
    assert result.metadata["MultiLabelMembership"] is True
    assert not any("score" in str(column).lower() for column in result.group_validation.columns)
    assert not any("score" in str(column).lower() for column in result.member_roles.columns)

    lead_roles = set(
        result.member_roles.loc[result.member_roles["Ticker"].eq("ALEAD"), "Role"].dropna()
    )
    lag_roles = set(result.member_roles.loc[result.member_roles["Ticker"].eq("ALAG"), "Role"].dropna())
    unrelated_roles = set(
        result.member_roles.loc[result.member_roles["Ticker"].eq("AUNR"), "Role"].dropna()
    )
    assert "LEAD" in lead_roles
    assert "LAG" in lag_roles
    assert "UNRELATED" in unrelated_roles

    candidate = pd.DataFrame(
        {
            "GroupId": ["G_PROPOSED", "G_FUTURE"],
            "GroupName": ["G_PROPOSED", "G_FUTURE"],
            "Ticker": ["A001.TW", "A002.TW"],
            "Decision": ["PROPOSED", "PROPOSED"],
            "ValidationEligible": [True, True],
            "IndexEligible": [False, False],
            "ProposedAt": [snapshot, snapshot + pd.Timedelta(days=2)],
        }
    )
    candidate_active = def_prepare_active_membership(
        candidate,
        snapshot,
        def_decision_timestamp(snapshot, None),
    )
    assert candidate_active["GroupId"].tolist() == ["G_PROPOSED"]
    assert candidate_active["_ValidationCohort"].eq("PROPOSED_VALIDATION").all()
    assert not candidate_active["_IndexEligible"].any()

    future_changed = residual.copy()
    future_changed.attrs = residual.attrs.copy()
    future_mask = future_changed["Date"].gt(snapshot)
    future_changed.loc[future_mask, "ResidualReturn"] = 9999.0
    future_result = def_run_group_validation(
        future_changed,
        membership,
        as_of_date=snapshot,
        trading_calendar=calendar,
        match_features=descriptors,
        config=config,
    )
    group_compare_columns = [
        "Window",
        "GroupId",
        *GROUP_METRICS,
        "GroupIntersectionPValue",
        "GroupQValue",
        "GroupDecision",
    ]
    pd.testing.assert_frame_equal(
        result.group_validation[group_compare_columns],
        future_result.group_validation[group_compare_columns],
        check_exact=True,
    )
    member_compare_columns = [
        "Window",
        "GroupId",
        "Ticker",
        "BestLag",
        "BestLagCorrelation",
        "AssociationPValue",
        "AssociationQValue",
        "Role",
    ]
    pd.testing.assert_frame_equal(
        result.member_roles[member_compare_columns],
        future_result.member_roles[member_compare_columns],
        check_exact=True,
    )

    blocked = residual.copy()
    blocked.attrs = {}
    blocked_result = def_run_group_validation(
        blocked,
        membership,
        as_of_date=snapshot,
        trading_calendar=calendar,
        match_features=descriptors,
        config=GroupValidationConfig(null_repeats_override=1),
    )
    assert blocked_result.group_validation["EvidenceStatus"].eq("BLOCKED").all()
    assert blocked_result.member_roles["EvidenceStatus"].eq("BLOCKED").all()
    assert blocked_result.member_roles["Role"].isna().all()
    return {
        "status": "PASS",
        "engine": ENGINE_ID,
        "windows": sorted(result.group_validation["Window"].unique().tolist()),
        "group_decisions": result.group_validation.groupby(["Window", "GroupDecision"]).size().to_dict(),
        "roles": result.member_roles.groupby(["Window", "Role"], dropna=False).size().to_dict(),
        "null_rows": int(len(result.null_ledger)),
        "effective_date": expected_effective.strftime("%Y-%m-%d"),
        "lookahead_invariance": "PASS",
        "provenance_fail_closed": "PASS",
        "candidate_validation_without_approval": "PASS_NON_INDEX_ELIGIBLE",
    }


def def_main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="run deterministic synthetic validation")
    arguments = parser.parse_args(argv)
    if not arguments.self_test:
        parser.print_help()
        return 0
    result = def_run_self_test()
    printable = {
        key: ({str(inner_key): value for inner_key, value in item.items()} if isinstance(item, dict) else item)
        for key, item in result.items()
    }
    print(json.dumps(printable, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(def_main())
