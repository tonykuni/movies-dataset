from __future__ import annotations

"""Fail-closed contracts between the v0.5 market, size and index engines.

The bridge is intentionally mechanical.  It selects one explicitly requested
market-factor residual lane, performs a point-in-time quarterly-tier lookup,
and adds the ``IndexMethod`` alias required by the backtest engine.  It does
not combine evidence lanes or create a ranking field.
"""

# =============================================================================
# def 00 PARAMETERS -- contract names, not market thresholds
# =============================================================================

from collections.abc import Iterable
import hashlib
import json
import re
from typing import Any

import numpy as np
import pandas as pd


ENGINE_ID = "VIA_PIPELINE_CONTRACT_BRIDGE"
ENGINE_VERSION = "0.5.0"
RESIDUAL_FACTOR_LANES = ("LaggedCap", "LaggedETR")
RESIDUAL_UNIVERSE = "TWSE_TPEX_COMMON_EQUITY_EX_2330"
RESIDUAL_LINEAGE_SCHEMA = "VIA_FULL_MARKET_RESIDUAL_LINEAGE_V2"
RESIDUAL_LINEAGE_ENGINE_ID = "VIA_FULL_TAIWAN_MARKET_FACTOR_ENGINE"
RESIDUAL_LINEAGE_GATE_STATUS = "PASS_FULL_TWSE_TPEX_ORDINARY_STOCKS"
RESIDUAL_LINEAGE_SOURCE_UNIVERSE = "TWSE_TPEX_COMMON_EQUITY_WITH_2330_ANCHOR"
RESIDUAL_LINEAGE_UNIVERSE_VERSION_POLICY = (
    "LATEST_RECORDED_REVISION_KNOWN_BY_SESSION_MARKET_DATA_CUTOFF"
)
RESIDUAL_LINEAGE_UNIVERSE_KNOWLEDGE_CUTOFF_POLICY = (
    "UNIVERSE_EVENT_KNOWN_AT_NOT_AFTER_SESSION_MARKET_DATA_AVAILABLE_AT"
)
RESIDUAL_LINEAGE_COLUMNS = (
    "ResidualLineageSchema",
    "ResidualLineageEngineId",
    "ResidualLineageEngineVersion",
    "ResidualLineageSourceUniverse",
    "ResidualLineageMarketUniverse",
    "ResidualLineageFullMarketGateStatus",
    "ResidualLineageRequiredMarkets",
    "ResidualLineageTSMCExcluded",
    "ResidualLineageTSMCAnchorPresent",
    "ResidualLineagePointInTime",
    "ResidualLineageAvailabilityPolicy",
    "ResidualLineageUniverseVersionPolicy",
    "ResidualLineageUniverseKnowledgeCutoffPolicy",
    "ResidualLineageTradingCalendarCoverage",
    "ResidualLineageRosterPolicy",
    "ResidualLineageFactorLanes",
    "ResidualLineageWindows",
    "ResidualLineageId",
)
RESIDUAL_COVERAGE_COLUMNS = (
    "ResidualUniverseExpectedTickerCount",
    "ResidualUniverseExpectedTWSECount",
    "ResidualUniverseExpectedTPEXCount",
)
RESIDUAL_ROSTER_HASH_COLUMN = "ResidualUniverseRosterHash"
DEFAULT_SIZE_WINDOW_DAYS = 240
TSMC_BASE = "2330"
VALID_MARKETS = ("TWSE", "TPEX")
VALID_TIERS = ("SMALL", "MID", "LARGE")


# =============================================================================
# def 01 SHARED NORMALIZATION
# =============================================================================


def def_normalize_date(value: Any, field_name: str) -> pd.Timestamp:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        raise ValueError(f"{field_name} is invalid")
    stamp = pd.Timestamp(parsed)
    if stamp.tzinfo is not None:
        stamp = stamp.tz_convert("Asia/Taipei").tz_localize(None)
    return stamp.normalize()


def def_normalize_ticker(value: Any, *, strip_market_suffix: bool) -> str:
    ticker = str(value or "").strip().upper().replace(" ", "")
    if strip_market_suffix:
        if ticker.endswith(".TWO"):
            ticker = ticker[:-4]
        elif ticker.endswith(".TW"):
            ticker = ticker[:-3]
    return ticker


def def_forbidden_aggregate_columns(frame: pd.DataFrame) -> list[str]:
    """Return fields that would collapse the parallel evidence lanes."""

    return [column for column in frame.columns if "score" in str(column).lower()]


def def_validate_residual_lineage_fields(
    rolling_residuals: pd.DataFrame,
) -> dict[str, Any]:
    """Validate durable row lineage and its deterministic integrity digest."""

    missing = sorted(set(RESIDUAL_LINEAGE_COLUMNS).difference(rolling_residuals.columns))
    if missing:
        raise ValueError(f"rolling_residuals missing row-level lineage columns: {missing}")
    values: dict[str, Any] = {}
    for column in RESIDUAL_LINEAGE_COLUMNS:
        observed = rolling_residuals[column].dropna().unique()
        if len(observed) != 1 or rolling_residuals[column].isna().any():
            raise ValueError(
                f"rolling_residuals row-level lineage is missing or inconsistent: {column}"
            )
        values[column] = observed[0]
    expected = {
        "ResidualLineageSchema": RESIDUAL_LINEAGE_SCHEMA,
        "ResidualLineageEngineId": RESIDUAL_LINEAGE_ENGINE_ID,
        "ResidualLineageEngineVersion": "0.5.0",
        "ResidualLineageSourceUniverse": RESIDUAL_LINEAGE_SOURCE_UNIVERSE,
        "ResidualLineageMarketUniverse": RESIDUAL_UNIVERSE,
        "ResidualLineageFullMarketGateStatus": RESIDUAL_LINEAGE_GATE_STATUS,
        "ResidualLineageRequiredMarkets": "TWSE|TPEX",
        "ResidualLineageTSMCExcluded": True,
        "ResidualLineageTSMCAnchorPresent": True,
        "ResidualLineagePointInTime": True,
        "ResidualLineageAvailabilityPolicy": (
            "MARKET_DATA_NONMISSING_SAME_LOCAL_SESSION;"
            "UNIVERSE_EVENT_KNOWN_AT_NOT_AFTER_SESSION_MARKET_DATA_AVAILABLE_AT"
        ),
        "ResidualLineageUniverseVersionPolicy": (
            RESIDUAL_LINEAGE_UNIVERSE_VERSION_POLICY
        ),
        "ResidualLineageUniverseKnowledgeCutoffPolicy": (
            RESIDUAL_LINEAGE_UNIVERSE_KNOWLEDGE_CUTOFF_POLICY
        ),
        "ResidualLineageTradingCalendarCoverage": "COMPLETE_OBSERVED_RANGE",
        "ResidualLineageRosterPolicy": "SHA256_SORTED_MARKET_TICKER_PER_DATE",
    }
    for column, expected_value in expected.items():
        observed_value = values[column]
        if isinstance(expected_value, bool):
            matches = isinstance(observed_value, (bool, np.bool_)) and bool(
                observed_value
            ) is expected_value
        else:
            matches = str(observed_value) == str(expected_value)
        if not matches:
            raise ValueError(
                f"rolling_residuals row-level lineage mismatch: {column}={observed_value!r}"
            )
    boolean_lineage = {
        "ResidualLineageTSMCExcluded",
        "ResidualLineageTSMCAnchorPresent",
        "ResidualLineagePointInTime",
    }
    digest_fields = {
        column: (
            bool(values[column])
            if column in boolean_lineage
            else str(values[column])
        )
        for column in RESIDUAL_LINEAGE_COLUMNS
        if column != "ResidualLineageId"
    }
    canonical = json.dumps(
        digest_fields,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    expected_digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest().upper()
    if str(values["ResidualLineageId"]) != expected_digest:
        raise ValueError("rolling_residuals row-level lineage digest mismatch")
    return values


def def_validate_residual_row_lineage(
    rolling_residuals: pd.DataFrame,
    *,
    factor_lane: str,
    window_days: int,
) -> dict[str, Any]:
    """Validate lineage plus the exact wide factor/window source grid."""

    values = def_validate_residual_lineage_fields(rolling_residuals)
    lanes = tuple(str(values["ResidualLineageFactorLanes"]).split("|"))
    try:
        windows = tuple(
            int(value)
            for value in str(values["ResidualLineageWindows"]).split("|")
            if value
        )
    except ValueError as error:
        raise ValueError("rolling_residuals lineage has invalid window identities") from error
    if lanes != tuple(RESIDUAL_FACTOR_LANES):
        raise ValueError("rolling_residuals lineage must declare both factor lanes")
    if (
        not windows
        or any(window < 2 for window in windows)
        or windows != tuple(sorted(set(windows)))
    ):
        raise ValueError(
            "rolling_residuals lineage windows must be unique sorted integers >= 2"
        )
    if factor_lane not in lanes or int(window_days) not in windows:
        raise ValueError(
            "requested residual lane/window is absent from row-level lineage"
        )
    source_pairs = {
        (match.group(1), int(match.group(2)))
        for column in rolling_residuals.columns
        if (
            match := re.fullmatch(
                r"Residual_(LaggedCap|LaggedETR)_(\d+)D", str(column)
            )
        )
    }
    declared_pairs = {(lane, window) for lane in lanes for window in windows}
    missing_source_pairs = declared_pairs.difference(source_pairs)
    unexpected_active_pairs: set[tuple[str, int]] = set()
    for lane, window in source_pairs.difference(declared_pairs):
        candidate_columns = (
            f"Residual_{lane}_{window}D",
            f"BetaStatus_{lane}_{window}D",
            f"BetaWindowPolicy_{lane}_{window}D",
            f"BetaObservations_{lane}_{window}D",
        )
        if any(
            column in rolling_residuals
            and rolling_residuals[column].notna().any()
            for column in candidate_columns
        ):
            unexpected_active_pairs.add((lane, window))
    if missing_source_pairs or unexpected_active_pairs:
        raise ValueError(
            "rolling_residuals declared lineage does not exactly match residual source columns"
        )
    missing_model_audit = sorted(
        column
        for lane, window in declared_pairs
        for column in (
            f"BetaStatus_{lane}_{window}D",
            f"BetaWindowPolicy_{lane}_{window}D",
            f"BetaObservations_{lane}_{window}D",
        )
        if column not in rolling_residuals.columns
    )
    if missing_model_audit:
        raise ValueError(
            f"rolling_residuals missing source-specific model audit columns: {missing_model_audit}"
        )
    return values


def def_validate_residual_daily_coverage(rolling_residuals: pd.DataFrame) -> None:
    """Prove every dated residual slice retains its complete ex-2330 roster."""

    required = {
        "Date",
        "Ticker",
        "Market",
        *RESIDUAL_COVERAGE_COLUMNS,
        RESIDUAL_ROSTER_HASH_COLUMN,
    }
    missing = sorted(required.difference(rolling_residuals.columns))
    if missing:
        raise ValueError(
            f"rolling_residuals missing durable universe coverage columns: {missing}"
        )
    if rolling_residuals.empty:
        raise ValueError("rolling_residuals universe coverage is empty")

    coverage = rolling_residuals[list(required)].copy()
    parsed_dates = pd.to_datetime(coverage["Date"], errors="coerce")
    if parsed_dates.isna().any():
        raise ValueError("rolling_residuals universe coverage has invalid dates")
    if getattr(parsed_dates.dt, "tz", None) is not None:
        parsed_dates = parsed_dates.dt.tz_convert("Asia/Taipei").dt.tz_localize(None)
    coverage["_LineageDate"] = parsed_dates.dt.normalize()
    coverage["_CanonicalTicker"] = coverage["Ticker"].map(
        lambda value: def_normalize_ticker(value, strip_market_suffix=False)
    )
    coverage["_LineageTicker"] = coverage["Ticker"].map(
        lambda value: def_normalize_ticker(value, strip_market_suffix=True)
    )
    coverage["_LineageMarket"] = (
        coverage["Market"].fillna("").astype(str).str.strip().str.upper()
    )
    canonical_ticker = coverage["_CanonicalTicker"]
    if not canonical_ticker.str.fullmatch(r"[0-9]{4}\.(TW|TWO)").all():
        raise ValueError(
            "rolling_residuals universe coverage requires canonical suffixed equity tickers"
        )
    suffix_market_match = (
        coverage["_LineageMarket"].eq("TWSE") & canonical_ticker.str.endswith(".TW")
    ) | (
        coverage["_LineageMarket"].eq("TPEX") & canonical_ticker.str.endswith(".TWO")
    )
    if not suffix_market_match.all():
        raise ValueError("rolling_residuals ticker suffix and market disagree")
    if coverage["_LineageTicker"].eq(TSMC_BASE).any():
        raise ValueError(
            "rolling_residuals contains 2330; the anchor must remain outside residual observations"
        )
    if not coverage["_LineageMarket"].isin(VALID_MARKETS).all():
        raise ValueError("rolling_residuals universe coverage has an invalid market")
    duplicates = coverage.duplicated(
        ["_LineageDate", "_LineageTicker"], keep=False
    )
    if duplicates.any():
        raise ValueError(
            "rolling_residuals universe coverage has duplicate Date+Ticker rows"
        )

    for column in RESIDUAL_COVERAGE_COLUMNS:
        numeric = pd.to_numeric(coverage[column], errors="coerce")
        integral = numeric.notna() & numeric.ge(0) & numeric.eq(numeric.round())
        if not integral.all():
            raise ValueError(f"rolling_residuals has invalid universe coverage: {column}")
        coverage[column] = numeric.astype("int64")

    for _, day in coverage.groupby("_LineageDate", sort=True):
        expected_values = {
            column: day[column].drop_duplicates().tolist()
            for column in RESIDUAL_COVERAGE_COLUMNS
        }
        if any(len(values) != 1 for values in expected_values.values()):
            raise ValueError("rolling_residuals universe coverage varies within a date")
        expected_total = int(expected_values["ResidualUniverseExpectedTickerCount"][0])
        expected_twse = int(expected_values["ResidualUniverseExpectedTWSECount"][0])
        expected_tpex = int(expected_values["ResidualUniverseExpectedTPEXCount"][0])
        actual_total = int(day["_LineageTicker"].nunique())
        actual_twse = int(day["_LineageMarket"].eq("TWSE").sum())
        actual_tpex = int(day["_LineageMarket"].eq("TPEX").sum())
        roster_hashes = day[RESIDUAL_ROSTER_HASH_COLUMN].drop_duplicates().tolist()
        if (
            len(roster_hashes) != 1
            or not re.fullmatch(r"[0-9A-F]{64}", str(roster_hashes[0]))
        ):
            raise ValueError("rolling_residuals has invalid daily roster hash")
        roster_lines = sorted(
            f"{market}|{ticker}"
            for market, ticker in zip(
                day["_LineageMarket"], day["_CanonicalTicker"], strict=True
            )
        )
        observed_roster_hash = hashlib.sha256(
            "\n".join(roster_lines).encode("utf-8")
        ).hexdigest().upper()
        if str(roster_hashes[0]) != observed_roster_hash:
            raise ValueError("rolling_residuals daily roster hash mismatch")
        if (
            expected_twse <= 0
            or expected_tpex <= 0
            or expected_total != expected_twse + expected_tpex
            or (
                actual_total,
                actual_twse,
                actual_tpex,
            )
            != (expected_total, expected_twse, expected_tpex)
        ):
            raise ValueError("rolling_residuals is not the complete ex-2330 daily universe")


def def_validate_residual_model_audit(
    frame: pd.DataFrame,
    *,
    window_days: int,
    residual_column: str,
    status_column: str,
    policy_column: str,
    observations_column: str,
) -> None:
    """Validate one residual model's finite-state and T-1 window accounting."""

    required = {
        "Date",
        "Ticker",
        residual_column,
        status_column,
        policy_column,
        observations_column,
    }
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"rolling_residuals missing model audit columns: {missing}")

    allowed_statuses = {
        "PASS",
        "BLOCKED_CURRENT_RETURN_OR_FACTOR",
        "BLOCKED_INSUFFICIENT_T1_HISTORY",
        "BLOCKED_ZERO_FACTOR_VARIANCE",
    }
    status = frame[status_column].fillna("").astype(str)
    if not status.isin(allowed_statuses).all():
        raise ValueError("rolling_residuals contains an unknown beta status")

    residual = pd.to_numeric(frame[residual_column], errors="coerce")
    pass_rows = status.eq("PASS")
    finite_residual = np.isfinite(residual.to_numpy(dtype=float))
    if (pass_rows.to_numpy() != finite_residual).any():
        raise ValueError("rolling_residuals beta status and residual value disagree")

    policy = frame[policy_column].fillna("").astype(str)
    pattern = re.compile(
        rf"T_MINUS_1_ONLY;window={int(window_days)};minimum=([0-9]+)"
    )
    extracted = policy.str.extract(pattern, expand=False)
    exact_match = policy.map(lambda value: pattern.fullmatch(value) is not None)
    if not exact_match.all() or extracted.isna().any():
        raise ValueError("rolling_residuals beta timing policy does not match requested window")
    minimum_value = pd.to_numeric(extracted, errors="coerce")
    if (
        minimum_value.isna().any()
        or not minimum_value.eq(minimum_value.round()).all()
        or minimum_value.lt(2).any()
        or minimum_value.gt(int(window_days)).any()
        or minimum_value.nunique(dropna=False) != 1
    ):
        raise ValueError("rolling_residuals beta timing policy has invalid minimum history")
    minimum = int(minimum_value.iloc[0])

    observations = pd.to_numeric(frame[observations_column], errors="coerce")
    valid_observations = (
        observations.notna()
        & observations.ge(0)
        & observations.le(int(window_days))
        & observations.eq(observations.round())
    )
    if not valid_observations.all():
        raise ValueError("rolling_residuals beta observations are invalid")
    chronology = frame[["Date", "Ticker"]].copy()
    chronology["Date"] = pd.to_datetime(chronology["Date"], errors="coerce")
    if chronology["Date"].isna().any():
        raise ValueError("rolling_residuals model audit has invalid dates")
    chronology["Ticker"] = chronology["Ticker"].astype(str)
    prior_row_count = (
        chronology.assign(_OriginalOrder=np.arange(len(chronology)))
        .sort_values(["Ticker", "Date", "_OriginalOrder"], kind="stable")
        .groupby("Ticker", sort=False)
        .cumcount()
        .reindex(chronology.index)
    )
    maximum_possible = prior_row_count.clip(upper=int(window_days))
    if observations.gt(maximum_possible).any():
        raise ValueError(
            "rolling_residuals beta observations exceed provable prior-row history"
        )
    insufficient = status.eq("BLOCKED_INSUFFICIENT_T1_HISTORY")
    zero_variance = status.eq("BLOCKED_ZERO_FACTOR_VARIANCE")
    if (pass_rows & observations.lt(minimum)).any():
        raise ValueError("rolling_residuals PASS status lacks its declared T-1 history")
    if (insufficient & observations.ge(minimum)).any():
        raise ValueError(
            "rolling_residuals insufficient-history status contradicts observations"
        )
    if (zero_variance & observations.lt(minimum)).any():
        raise ValueError(
            "rolling_residuals zero-variance status lacks its declared T-1 history"
        )


def def_validate_residual_availability(rolling_residuals: pd.DataFrame) -> str:
    """Return the authoritative complete same-session availability column."""

    if "Date" not in rolling_residuals:
        raise ValueError("rolling_residuals requires Date for availability provenance")
    observation_dates = pd.to_datetime(rolling_residuals["Date"], errors="coerce")
    if observation_dates.isna().any():
        raise ValueError("rolling_residuals has invalid dates for availability provenance")
    if getattr(observation_dates.dt, "tz", None) is not None:
        observation_dates = observation_dates.dt.tz_convert(
            "Asia/Taipei"
        ).dt.tz_localize(None)
    observation_dates = observation_dates.dt.normalize()

    for candidate in ("ResidualReturnAvailableAt", "MarketDataAvailableAt"):
        if candidate not in rolling_residuals.columns:
            continue
        populated = rolling_residuals[candidate].notna()
        if not populated.any():
            continue
        if not populated.all():
            raise ValueError(
                f"rolling_residuals has partial availability provenance: {candidate}"
            )
        parsed = pd.to_datetime(
            rolling_residuals[candidate], errors="coerce", utc=True
        )
        if parsed.isna().any():
            raise ValueError(
                f"rolling_residuals has invalid availability provenance: {candidate}"
            )
        local_date = parsed.dt.tz_convert("Asia/Taipei").dt.tz_localize(None).dt.normalize()
        if not local_date.eq(observation_dates).all():
            raise ValueError(
                f"rolling_residuals availability is not on its observation session: {candidate}"
            )
        return candidate
    raise ValueError("rolling_residuals has no complete availability provenance")


# =============================================================================
# def 02 FULL-MARKET RESIDUAL LANE -> GROUP-VALIDATION CONTRACT
# =============================================================================


def def_bridge_residual_lane(
    rolling_residuals: pd.DataFrame,
    *,
    factor_lane: str,
    window_days: int,
    as_of_date: Any | None = None,
) -> pd.DataFrame:
    """Select exactly one named residual lane without an implicit fallback.

    ``factor_lane`` and ``window_days`` are mandatory.  The selected source is
    always ``Residual_<factor_lane>_<window_days>D``; a missing source column
    raises instead of selecting a different lane or window.  An optional
    ``as_of_date`` bounds the returned evidence and makes historical reruns
    invariant to subsequently appended observations.
    """

    if factor_lane not in RESIDUAL_FACTOR_LANES:
        raise ValueError(
            f"factor_lane must be explicitly one of {RESIDUAL_FACTOR_LANES}; "
            f"received {factor_lane!r}"
        )
    if isinstance(window_days, bool):
        raise ValueError("window_days must be an integer >= 2")
    try:
        resolved_window = int(window_days)
    except (TypeError, ValueError) as error:
        raise ValueError("window_days must be an integer >= 2") from error
    if resolved_window < 2 or resolved_window != window_days:
        raise ValueError("window_days must be an integer >= 2")

    source_column = f"Residual_{factor_lane}_{resolved_window}D"
    status_column = f"BetaStatus_{factor_lane}_{resolved_window}D"
    policy_column = f"BetaWindowPolicy_{factor_lane}_{resolved_window}D"
    observations_column = f"BetaObservations_{factor_lane}_{resolved_window}D"
    required = {
        "Date",
        "Ticker",
        "Market",
        source_column,
        status_column,
        policy_column,
        observations_column,
        *RESIDUAL_COVERAGE_COLUMNS,
    }
    missing = sorted(required.difference(rolling_residuals.columns))
    if missing:
        raise ValueError(
            f"rolling_residuals does not contain the explicitly requested lane: {missing}"
        )

    # Establish the historical snapshot before validating any dated row-level
    # contract.  This is essential for a reproducible as-of rerun: a malformed
    # or incomplete observation appended after the requested boundary cannot
    # retroactively invalidate an otherwise identical historical snapshot.
    # An unparseable date remains a hard failure because its side of the
    # boundary cannot be proven.
    source_dates = pd.to_datetime(rolling_residuals["Date"], errors="coerce")
    if source_dates.isna().any():
        raise ValueError(
            f"rolling_residuals has {int(source_dates.isna().sum())} invalid dates"
        )
    if getattr(source_dates.dt, "tz", None) is not None:
        source_dates = source_dates.dt.tz_convert("Asia/Taipei").dt.tz_localize(None)
    source_dates = source_dates.dt.normalize()
    boundary = None
    if as_of_date is not None:
        boundary = def_normalize_date(as_of_date, "as_of_date")
    validation_source = rolling_residuals.loc[
        source_dates.le(boundary) if boundary is not None else source_dates.notna()
    ].copy()
    validation_source.attrs.update(rolling_residuals.attrs)
    validation_source["Date"] = source_dates.loc[validation_source.index]
    if validation_source.empty:
        raise ValueError("rolling_residuals has no observations on or before as_of_date")

    row_lineage = def_validate_residual_row_lineage(
        validation_source,
        factor_lane=factor_lane,
        window_days=resolved_window,
    )
    optional_attr_contract = {
        "MarketUniverse": RESIDUAL_UNIVERSE,
        "ResidualizationUniverse": RESIDUAL_UNIVERSE,
        "TSMCExcludedFromMarketFactor": True,
        "PointInTime": True,
    }
    for field, expected_value in optional_attr_contract.items():
        if field in validation_source.attrs and validation_source.attrs[field] != expected_value:
            raise ValueError(
                f"rolling_residuals attrs contradict row-level lineage: {field}"
            )
    for field in RESIDUAL_LINEAGE_COLUMNS:
        if (
            field in validation_source.attrs
            and validation_source.attrs[field] != row_lineage[field]
        ):
            raise ValueError(
                f"rolling_residuals attrs and row-level lineage disagree: {field}"
            )

    def_validate_residual_daily_coverage(validation_source)

    selected_columns = [
        "Date",
        "Ticker",
        "Market",
        source_column,
        status_column,
        policy_column,
        observations_column,
        *RESIDUAL_COVERAGE_COLUMNS,
        RESIDUAL_ROSTER_HASH_COLUMN,
        *RESIDUAL_LINEAGE_COLUMNS,
    ]
    availability_source = def_validate_residual_availability(validation_source)
    if availability_source is not None:
        selected_columns.append(availability_source)
    frame = validation_source[selected_columns].copy()
    frame["Ticker"] = frame["Ticker"].map(
        lambda value: def_normalize_ticker(value, strip_market_suffix=False)
    )
    frame[source_column] = pd.to_numeric(frame[source_column], errors="coerce")
    frame[observations_column] = pd.to_numeric(
        frame[observations_column], errors="coerce"
    )
    def_validate_residual_model_audit(
        frame,
        window_days=resolved_window,
        residual_column=source_column,
        status_column=status_column,
        policy_column=policy_column,
        observations_column=observations_column,
    )
    invalid_keys = frame["Date"].isna() | frame["Ticker"].eq("")
    if invalid_keys.any():
        raise ValueError(f"rolling_residuals has {int(invalid_keys.sum())} invalid keys")
    duplicates = frame.duplicated(["Date", "Ticker"], keep=False)
    if duplicates.any():
        raise ValueError(
            f"rolling_residuals has {int(duplicates.sum())} duplicate Date+Ticker rows"
        )

    rename_columns = {
        source_column: "ResidualReturn",
        status_column: "ResidualModelStatus",
        policy_column: "ResidualWindowPolicy",
        observations_column: "ResidualBetaObservations",
    }
    if availability_source is not None and availability_source != "ResidualReturnAvailableAt":
        rename_columns[availability_source] = "ResidualReturnAvailableAt"
    result = frame.rename(columns=rename_columns)
    result["MarketUniverse"] = RESIDUAL_UNIVERSE
    result["ResidualizationUniverse"] = RESIDUAL_UNIVERSE
    result["TSMCExcluded"] = True
    result["TSMCExcludedFromMarketFactor"] = True
    result["PointInTime"] = True
    result["FactorLane"] = factor_lane
    result["WindowDays"] = resolved_window
    result["ResidualSourceColumn"] = source_column
    result = result.sort_values(["Date", "Ticker"], kind="stable").reset_index(drop=True)

    result.attrs.update(
        {
            "EngineId": ENGINE_ID,
            "EngineVersion": ENGINE_VERSION,
            "MarketUniverse": RESIDUAL_UNIVERSE,
            "ResidualizationUniverse": RESIDUAL_UNIVERSE,
            "TSMCExcluded": True,
            "TSMCExcludedFromMarketFactor": True,
            "PointInTime": True,
            "FactorLane": factor_lane,
            "WindowDays": resolved_window,
            "ResidualSourceColumn": source_column,
            "AsOfDate": boundary,
            **row_lineage,
        }
    )
    return result


# =============================================================================
# def 03 QUARTERLY HISTORY -> POINT-IN-TIME MATCHING FEATURES
# =============================================================================


def def_bridge_size_tiers_asof(
    quarterly_size_history: pd.DataFrame,
    decision_date: Any,
    *,
    window_days: int = DEFAULT_SIZE_WINDOW_DAYS,
    required_tickers: Iterable[Any] | None = None,
) -> pd.DataFrame:
    """Return the last effective tiers known on ``decision_date``.

    Rows with a future or missing ``EffectiveDate`` are never eligible.  A
    duplicate Ticker+EffectiveDate for the selected window blocks the lookup.
    ``required_tickers`` may be supplied by a validation cohort to fail closed
    when any requested member does not yet have an effective classification.
    """

    required = {
        "Ticker",
        "EffectiveDate",
        "WindowDays",
        "MarketCapTier",
        "EffectiveTurnoverTier",
    }
    missing = sorted(required.difference(quarterly_size_history.columns))
    if missing:
        raise ValueError(f"quarterly_size_history missing required columns: {missing}")
    market_column = (
        "Market"
        if "Market" in quarterly_size_history.columns
        else "Exchange"
        if "Exchange" in quarterly_size_history.columns
        else None
    )
    if market_column is None:
        raise ValueError("quarterly_size_history requires Market or Exchange")

    if isinstance(window_days, bool):
        raise ValueError("window_days must be a positive integer")
    try:
        resolved_window = int(window_days)
    except (TypeError, ValueError) as error:
        raise ValueError("window_days must be a positive integer") from error
    if resolved_window <= 0 or resolved_window != window_days:
        raise ValueError("window_days must be a positive integer")
    as_of = def_normalize_date(decision_date, "decision_date")

    frame = quarterly_size_history.copy()
    frame["Ticker"] = frame["Ticker"].map(
        lambda value: def_normalize_ticker(value, strip_market_suffix=True)
    )
    frame["WindowDays"] = pd.to_numeric(frame["WindowDays"], errors="coerce")
    raw_effective = frame["EffectiveDate"]
    blank_effective = raw_effective.isna() | raw_effective.astype(str).str.strip().eq("")
    parsed_effective = pd.to_datetime(raw_effective.where(~blank_effective), errors="coerce")
    invalid_effective = (~blank_effective) & parsed_effective.isna()
    if invalid_effective.any():
        raise ValueError(
            f"quarterly_size_history has {int(invalid_effective.sum())} invalid EffectiveDate values"
        )
    if getattr(parsed_effective.dt, "tz", None) is not None:
        parsed_effective = parsed_effective.dt.tz_convert("Asia/Taipei").dt.tz_localize(None)
    frame["EffectiveDate"] = parsed_effective.dt.normalize()
    frame["Market"] = frame[market_column].fillna("").astype(str).str.strip().str.upper()
    frame["SizeTier"] = frame["MarketCapTier"].fillna("").astype(str).str.strip().str.upper()
    frame["LiquidityTier"] = (
        frame["EffectiveTurnoverTier"].fillna("").astype(str).str.strip().str.upper()
    )
    frame = frame.loc[frame["WindowDays"].eq(resolved_window)].copy()
    if frame.empty:
        raise ValueError(f"quarterly_size_history has no rows for window_days={resolved_window}")
    if frame["Ticker"].eq("").any():
        raise ValueError("quarterly_size_history contains an empty ticker")
    duplicates = frame.duplicated(["Ticker", "EffectiveDate"], keep=False)
    if duplicates.any():
        raise ValueError(
            f"quarterly_size_history has {int(duplicates.sum())} duplicate effective keys "
            f"for window_days={resolved_window}"
        )

    requested: set[str] | None = None
    if required_tickers is not None:
        requested = {
            def_normalize_ticker(value, strip_market_suffix=True) for value in required_tickers
        }
        if "" in requested:
            raise ValueError("required_tickers contains an empty ticker")
        frame = frame.loc[frame["Ticker"].isin(requested)].copy()

    effective = frame.loc[
        frame["EffectiveDate"].notna() & frame["EffectiveDate"].le(as_of)
    ].copy()
    if effective.empty:
        raise ValueError(
            f"no size classification is effective by decision_date={as_of:%Y-%m-%d}"
        )
    selected = (
        effective.sort_values(["Ticker", "EffectiveDate"], kind="stable")
        .groupby("Ticker", sort=False, as_index=False)
        .tail(1)
        .copy()
    )
    if selected["EffectiveDate"].gt(as_of).any():
        raise AssertionError("future size classification crossed the backward-asof boundary")

    if requested is not None:
        unavailable = sorted(requested.difference(selected["Ticker"]))
        if unavailable:
            raise ValueError(
                "required tickers do not yet have an effective size classification: "
                f"{unavailable}"
            )

    # 2330 is reported as an isolated anchor by the source engine; it is not a
    # member of the ex-2330 comparison-tier contract.
    selected = selected.loc[selected["Ticker"].ne(TSMC_BASE)].copy()
    if requested is not None and TSMC_BASE in requested:
        raise ValueError("2330 is excluded from the size comparison-tier contract")
    invalid_market = ~selected["Market"].isin(VALID_MARKETS)
    invalid_tier = ~selected["SizeTier"].isin(VALID_TIERS) | ~selected[
        "LiquidityTier"
    ].isin(VALID_TIERS)
    if invalid_market.any() or invalid_tier.any():
        bad = selected.loc[
            invalid_market | invalid_tier,
            ["Ticker", "Market", "SizeTier", "LiquidityTier", "EffectiveDate"],
        ].to_dict("records")
        raise ValueError(f"selected size classifications are not usable: {bad}")

    result = selected[
        ["Ticker", "Market", "SizeTier", "LiquidityTier", "EffectiveDate"]
    ].rename(columns={"EffectiveDate": "TierEffectiveDate"})
    result["WindowDays"] = resolved_window
    result = result.sort_values("Ticker", kind="stable").reset_index(drop=True)
    result.attrs.update(
        {
            "EngineId": ENGINE_ID,
            "EngineVersion": ENGINE_VERSION,
            "DecisionDate": as_of,
            "WindowDays": resolved_window,
            "PointInTime": True,
            "AsOfJoinPolicy": "BACKWARD_EFFECTIVE_DATE_LE_DECISION_DATE",
            "TSMCExcluded": True,
        }
    )
    return result


# =============================================================================
# def 04 GROUP INDEX -> BACKTEST CONTRACT
# =============================================================================


def def_bridge_index_method(index_output: pd.DataFrame) -> pd.DataFrame:
    """Add ``IndexMethod`` as an alias while retaining source ``Method``."""

    required = {"Date", "GroupId", "Method", "IndexLevel", "IndexStatus"}
    missing = sorted(required.difference(index_output.columns))
    if missing:
        raise ValueError(f"index_output missing required columns: {missing}")
    result = index_output.copy()
    result["Method"] = result["Method"].fillna("").astype(str).str.strip()
    if result["Method"].eq("").any():
        raise ValueError("index_output contains an empty Method")
    if "IndexMethod" in result.columns:
        existing = result["IndexMethod"].fillna("").astype(str).str.strip()
        mismatch = existing.ne(result["Method"])
        if mismatch.any():
            raise ValueError(
                f"IndexMethod conflicts with Method on {int(mismatch.sum())} rows"
            )
    result["IndexMethod"] = result["Method"]
    parsed_dates = pd.to_datetime(result["Date"], errors="coerce")
    if parsed_dates.isna().any():
        raise ValueError(f"index_output contains {int(parsed_dates.isna().sum())} invalid dates")
    if getattr(parsed_dates.dt, "tz", None) is not None:
        parsed_dates = parsed_dates.dt.tz_convert("Asia/Taipei").dt.tz_localize(None)
    result["Date"] = parsed_dates.dt.normalize()
    duplicate = result.duplicated(["Date", "GroupId", "IndexMethod"], keep=False)
    if duplicate.any():
        raise ValueError(f"index_output contains {int(duplicate.sum())} duplicate index keys")
    result.attrs.update(index_output.attrs)
    result.attrs.update(
        {
            "EngineId": ENGINE_ID,
            "EngineVersion": ENGINE_VERSION,
            "IndexMethodAliasPolicy": "IndexMethod_EQUALS_Method_SOURCE_RETAINED",
        }
    )
    return result.sort_values(["GroupId", "IndexMethod", "Date"], kind="stable").reset_index(
        drop=True
    )


# =============================================================================
# def 05 SELF TEST
# =============================================================================


def def_run_self_test() -> dict[str, Any]:
    dates = pd.bdate_range("2024-01-02", periods=5)
    residual_source = pd.DataFrame(
        {
            "Date": list(dates) * 2,
            "Ticker": ["1101.TW"] * len(dates) + ["6488.TWO"] * len(dates),
            "Market": ["TWSE"] * len(dates) + ["TPEX"] * len(dates),
            "MarketDataAvailableAt": [
                f"{date:%Y-%m-%d} 14:30:00+08:00" for date in dates
            ]
            * 2,
            "Residual_LaggedCap_5D": [np.nan, np.nan, np.nan, np.nan, 0.01] * 2,
            "Residual_LaggedETR_5D": [np.nan, np.nan, np.nan, np.nan, 0.02] * 2,
            "BetaStatus_LaggedCap_5D": (
                ["BLOCKED_INSUFFICIENT_T1_HISTORY"] * 4 + ["PASS"]
            )
            * 2,
            "BetaStatus_LaggedETR_5D": (
                ["BLOCKED_INSUFFICIENT_T1_HISTORY"] * 4 + ["PASS"]
            )
            * 2,
            "BetaWindowPolicy_LaggedCap_5D": "T_MINUS_1_ONLY;window=5;minimum=4",
            "BetaWindowPolicy_LaggedETR_5D": "T_MINUS_1_ONLY;window=5;minimum=4",
            "BetaObservations_LaggedCap_5D": [0, 1, 2, 3, 4] * 2,
            "BetaObservations_LaggedETR_5D": [0, 1, 2, 3, 4] * 2,
            "ResidualUniverseExpectedTickerCount": 2,
            "ResidualUniverseExpectedTWSECount": 1,
            "ResidualUniverseExpectedTPEXCount": 1,
            "ResidualUniverseRosterHash": hashlib.sha256(
                "TPEX|6488.TWO\nTWSE|1101.TW".encode("utf-8")
            )
            .hexdigest()
            .upper(),
        }
    )
    row_lineage = {
        "ResidualLineageSchema": RESIDUAL_LINEAGE_SCHEMA,
        "ResidualLineageEngineId": RESIDUAL_LINEAGE_ENGINE_ID,
        "ResidualLineageEngineVersion": "0.5.0",
        "ResidualLineageSourceUniverse": RESIDUAL_LINEAGE_SOURCE_UNIVERSE,
        "ResidualLineageMarketUniverse": RESIDUAL_UNIVERSE,
        "ResidualLineageFullMarketGateStatus": RESIDUAL_LINEAGE_GATE_STATUS,
        "ResidualLineageRequiredMarkets": "TWSE|TPEX",
        "ResidualLineageTSMCExcluded": True,
        "ResidualLineageTSMCAnchorPresent": True,
        "ResidualLineagePointInTime": True,
        "ResidualLineageAvailabilityPolicy": (
            "MARKET_DATA_NONMISSING_SAME_LOCAL_SESSION;"
            "UNIVERSE_EVENT_KNOWN_AT_NOT_AFTER_SESSION_MARKET_DATA_AVAILABLE_AT"
        ),
        "ResidualLineageUniverseVersionPolicy": (
            RESIDUAL_LINEAGE_UNIVERSE_VERSION_POLICY
        ),
        "ResidualLineageUniverseKnowledgeCutoffPolicy": (
            RESIDUAL_LINEAGE_UNIVERSE_KNOWLEDGE_CUTOFF_POLICY
        ),
        "ResidualLineageTradingCalendarCoverage": "COMPLETE_OBSERVED_RANGE",
        "ResidualLineageRosterPolicy": "SHA256_SORTED_MARKET_TICKER_PER_DATE",
        "ResidualLineageFactorLanes": "LaggedCap|LaggedETR",
        "ResidualLineageWindows": "5",
    }
    canonical = json.dumps(
        row_lineage,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    row_lineage["ResidualLineageId"] = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest().upper()
    for column, value in row_lineage.items():
        residual_source[column] = value
    residual_source.attrs.update(
        {
            "MarketUniverse": RESIDUAL_UNIVERSE,
            "ResidualizationUniverse": RESIDUAL_UNIVERSE,
            "TSMCExcludedFromMarketFactor": True,
            "PointInTime": True,
            **row_lineage,
        }
    )
    residual = def_bridge_residual_lane(
        residual_source,
        factor_lane="LaggedETR",
        window_days=5,
        as_of_date=dates[-1],
    )
    expected_residual = {"Date", "Ticker", "ResidualReturn"}
    if not expected_residual.issubset(residual.columns):
        raise AssertionError("residual bridge field contract failed")
    if residual.attrs.get("MarketUniverse") != RESIDUAL_UNIVERSE:
        raise AssertionError("residual universe provenance was not attached")
    tsmc = residual_source.iloc[:1].copy()
    tsmc["Ticker"] = "2330.TW"
    try:
        def_bridge_residual_lane(
            tsmc,
            factor_lane="LaggedETR",
            window_days=5,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("2330 entered the ex-2330 residual bridge")
    future_residual = residual_source.iloc[:1].copy()
    future_residual["Date"] = pd.Timestamp("2025-01-02")
    future_residual["Residual_LaggedETR_5D"] = 9999.0
    future_residual["ResidualReturnAvailableAt"] = "2025-01-02 14:30:00+08:00"
    future_residual["Residual_LaggedCap_99D"] = 9999.0
    future_residual["BetaStatus_LaggedCap_99D"] = "PASS"
    future_residual["BetaWindowPolicy_LaggedCap_99D"] = (
        "T_MINUS_1_ONLY;window=99;minimum=67"
    )
    future_residual["BetaObservations_LaggedCap_99D"] = 99
    residual_with_future = def_bridge_residual_lane(
        pd.concat([residual_source, future_residual], ignore_index=True),
        factor_lane="LaggedETR",
        window_days=5,
        as_of_date=dates[-1],
    )
    if not residual.equals(residual_with_future):
        raise AssertionError("future residual observations changed a historical as-of result")
    try:
        def_bridge_residual_lane(  # type: ignore[call-arg]
            residual_source,
            window_days=5,
        )
    except TypeError:
        pass
    else:
        raise AssertionError("factor_lane unexpectedly had an implicit default")
    try:
        def_bridge_residual_lane(
            residual_source,
            factor_lane="LaggedCap",
            window_days=120,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("a nonexistent residual source column did not block")

    size_history = pd.DataFrame(
        [
            {
                "Ticker": ticker,
                "Exchange": market,
                "EffectiveDate": effective,
                "WindowDays": 240,
                "MarketCapTier": size,
                "EffectiveTurnoverTier": liquidity,
            }
            for ticker, market, size, liquidity in (
                ("1101", "TWSE", "LARGE", "MID"),
                ("6488", "TPEX", "SMALL", "LARGE"),
            )
            for effective in (pd.Timestamp("2024-01-03"), pd.Timestamp("2024-04-02"))
        ]
    )
    size = def_bridge_size_tiers_asof(
        size_history,
        "2024-05-01",
        required_tickers=("1101.TW", "6488.TWO"),
    )
    expected_size = {"Ticker", "Market", "SizeTier", "LiquidityTier"}
    if not expected_size.issubset(size.columns):
        raise AssertionError("size bridge field contract failed")
    future = size_history.groupby("Ticker", sort=False, as_index=False).head(1).copy()
    future["EffectiveDate"] = pd.Timestamp("2025-01-02")
    future["MarketCapTier"] = "SMALL"
    with_future = def_bridge_size_tiers_asof(
        pd.concat([size_history, future], ignore_index=True),
        "2024-05-01",
        required_tickers=("1101", "6488"),
    )
    compare = ["Ticker", "Market", "SizeTier", "LiquidityTier", "TierEffectiveDate"]
    if not size[compare].equals(with_future[compare]):
        raise AssertionError("future size history changed a historical as-of result")

    index_source = pd.DataFrame(
        {
            "Date": dates[:2],
            "GroupId": ["G-CPO", "G-CPO"],
            "Method": ["GI_HIER", "GI_HIER"],
            "IndexLevel": [100.0, 101.0],
            "IndexStatus": ["PASS", "PASS"],
        }
    )
    index = def_bridge_index_method(index_source)
    expected_index = {"Date", "GroupId", "Method", "IndexMethod", "IndexLevel"}
    if not expected_index.issubset(index.columns):
        raise AssertionError("index bridge field contract failed")
    if not index["Method"].equals(index["IndexMethod"]):
        raise AssertionError("Method source column was not retained as the alias source")

    for name, output in (("residual", residual), ("size", size), ("index", index)):
        forbidden = def_forbidden_aggregate_columns(output)
        if forbidden:
            raise AssertionError(f"{name} bridge emitted forbidden aggregate fields: {forbidden}")
    return {
        "Status": "PASS",
        "EngineId": ENGINE_ID,
        "ResidualRows": len(residual),
        "SizeRows": len(size),
        "IndexRows": len(index),
        "FutureInvariant": True,
    }


if __name__ == "__main__":
    print(def_run_self_test())
