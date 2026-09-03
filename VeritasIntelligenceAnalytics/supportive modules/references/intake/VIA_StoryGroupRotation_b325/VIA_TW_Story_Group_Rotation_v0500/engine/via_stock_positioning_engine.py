from __future__ import annotations

"""Point-in-time, all-stock positioning and exit evidence for Taiwan equities.

The engine operates before story-group aggregation.  It compares every TWSE
and TPEX ordinary share (with 2330 isolated) against strictly T-1 rolling
distributions and same-session dynamic peers.  ETR and ``AttentionETR`` are
used only as non-directional attention evidence.  Direction is kept in three
separate lanes: foreign institutions, domestic institutions excluding foreign
institutions, and active-ETF portfolio changes.

No weighted aggregate, ranking number, or automatic trade instruction is
produced.  A category is emitted independently for every stock, evidence
window, and directional lane.  The category cannot become effective until the
next trading session after the latest required evidence timestamp.
"""

from dataclasses import dataclass
import hashlib
from typing import Any, Iterable

import numpy as np
import pandas as pd

if __package__:
    from .via_group_flow_evidence_engine import (
        def_ticker_base,
        def_validate_full_market_coverage,
    )
    from .via_pipeline_contract_bridge import (
        RESIDUAL_COVERAGE_COLUMNS,
        RESIDUAL_FACTOR_LANES,
        RESIDUAL_LINEAGE_UNIVERSE_KNOWLEDGE_CUTOFF_POLICY,
        RESIDUAL_LINEAGE_UNIVERSE_VERSION_POLICY,
        RESIDUAL_ROSTER_HASH_COLUMN,
        def_validate_residual_availability,
        def_validate_residual_daily_coverage,
        def_validate_residual_lineage_fields,
        def_validate_residual_model_audit,
    )
    from .via_time_utils import def_available_at_utc, def_local_calendar_date
else:  # direct execution from the engine directory
    from via_group_flow_evidence_engine import (
        def_ticker_base,
        def_validate_full_market_coverage,
    )
    from via_pipeline_contract_bridge import (
        RESIDUAL_COVERAGE_COLUMNS,
        RESIDUAL_FACTOR_LANES,
        RESIDUAL_LINEAGE_UNIVERSE_KNOWLEDGE_CUTOFF_POLICY,
        RESIDUAL_LINEAGE_UNIVERSE_VERSION_POLICY,
        RESIDUAL_ROSTER_HASH_COLUMN,
        def_validate_residual_availability,
        def_validate_residual_daily_coverage,
        def_validate_residual_lineage_fields,
        def_validate_residual_model_audit,
    )
    from via_time_utils import def_available_at_utc, def_local_calendar_date


ENGINE_ID = "VIA_STOCK_POSITIONING_EVIDENCE_V0500"
ENGINE_VERSION = "0.5.0"
DEFAULT_WINDOWS = (60, 120, 240)
TSMC_BASE = "2330"
REQUIRED_FULL_MARKET_GATE_STATUS = "PASS_FULL_TWSE_TPEX_ORDINARY_STOCKS"
REQUIRED_RESIDUAL_UNIVERSE = "TWSE_TPEX_COMMON_EQUITY_EX_2330"
REQUIRED_RESIDUAL_LINEAGE_SCHEMA = "VIA_FULL_MARKET_RESIDUAL_LINEAGE_V2"
UNMAPPED_GROUP_ID = "UNMAPPED"
APPROVED_MEMBERSHIP_DECISIONS = ("APPROVED", "ACTIVE", "KEEP")

LANE_CONTRACT = {
    "FOREIGN": (
        "ForeignDirectionalAmount",
        "ForeignDirectionalAmountAvailableAt",
    ),
    "DOMESTIC_EX_FOREIGN": (
        "DomesticExForeignDirectionalAmount",
        "DomesticExForeignDirectionalAmountAvailableAt",
    ),
    "ACTIVE_ETF": (
        "ActiveETFDirectionalAmount",
        "ActiveETFDirectionalAmountAvailableAt",
    ),
}


@dataclass(frozen=True)
class StockPositioningConfig:
    """Structural choices; market cut-offs are intentionally absent."""

    windows: tuple[int, ...] = DEFAULT_WINDOWS
    tsmc_ticker: str = TSMC_BASE
    peer_bucket_candidates: tuple[str, ...] = (
        "SizeBucket",
        "SizeTier",
        "SizeClass",
    )


def def_resolve_windows(windows: Iterable[int]) -> tuple[int, ...]:
    resolved = tuple(sorted({int(window) for window in windows}))
    if not resolved or any(window < 2 for window in resolved):
        raise ValueError("windows must contain integers >= 2")
    return resolved


def def_safe_available_at_utc(value: Any) -> pd.Timestamp | pd.NaT:
    if value is None or pd.isna(value):
        return pd.NaT
    return def_available_at_utc(value)


def def_safe_local_date(value: Any) -> pd.Timestamp | pd.NaT:
    if value is None or pd.isna(value):
        return pd.NaT
    return def_local_calendar_date(value)


def def_latest_timestamp(values: Iterable[Any]) -> pd.Timestamp | pd.NaT:
    stamps = [def_safe_available_at_utc(value) for value in values]
    valid = [stamp for stamp in stamps if not pd.isna(stamp)]
    return max(valid) if valid else pd.NaT


def def_state_against_dynamic_medians(
    value: pd.Series,
    prior_median: pd.Series,
    peer_median: pd.Series,
    peer_count: pd.Series,
) -> pd.Series:
    complete = (
        value.notna()
        & prior_median.notna()
        & peer_median.notna()
        & peer_count.ge(2)
    )
    above = complete & value.gt(prior_median) & value.gt(peer_median)
    below = complete & value.lt(prior_median) & value.lt(peer_median)
    at_both = complete & value.eq(prior_median) & value.eq(peer_median)
    return pd.Series(
        np.select(
            [above, below, at_both, complete],
            [
                "ABOVE_PRIOR_AND_PEER_MEDIANS",
                "BELOW_PRIOR_AND_PEER_MEDIANS",
                "AT_PRIOR_AND_PEER_MEDIANS",
                "MIXED_DYNAMIC_THRESHOLDS",
            ],
            default="HOLD_INSUFFICIENT_T1_HISTORY_OR_PEERS",
        ),
        index=value.index,
        dtype="object",
    )


def def_leave_one_out_peer_median(values: pd.Series) -> pd.Series:
    """Return an exact peer median that excludes the current stock itself."""

    numeric = pd.to_numeric(values, errors="coerce")
    result = pd.Series(np.nan, index=values.index, dtype=float)
    valid = numeric.dropna()
    count = len(valid)
    if count <= 1:
        return result
    ordered_values = np.sort(valid.to_numpy(dtype=float))
    ranks = valid.rank(method="first").astype(int).to_numpy()
    if count % 2 == 0:
        half = count // 2
        medians = np.where(
            ranks <= half,
            ordered_values[half],
            ordered_values[half - 1],
        )
    else:
        half = count // 2
        lower_pair = (ordered_values[half] + ordered_values[half + 1]) / 2.0
        middle_pair = (ordered_values[half - 1] + ordered_values[half + 1]) / 2.0
        upper_pair = (ordered_values[half - 1] + ordered_values[half]) / 2.0
        medians = np.where(
            ranks <= half,
            lower_pair,
            np.where(ranks == half + 1, middle_pair, upper_pair),
        )
    result.loc[valid.index] = medians
    return result


def def_prepare_residual_evidence(
    residual_returns: pd.DataFrame,
) -> pd.DataFrame:
    """Validate one explicit ex-2330 point-in-time residual lane."""

    required = {
        "Date",
        "Ticker",
        "Market",
        "ResidualReturn",
        "MarketUniverse",
        "ResidualizationUniverse",
        "TSMCExcluded",
        "TSMCExcludedFromMarketFactor",
        "PointInTime",
        "FactorLane",
        "WindowDays",
        "ResidualSourceColumn",
        "ResidualModelStatus",
        "ResidualWindowPolicy",
        "ResidualBetaObservations",
        "ResidualLineageSchema",
        "ResidualLineageId",
        "ResidualLineageUniverseVersionPolicy",
        "ResidualLineageUniverseKnowledgeCutoffPolicy",
        *RESIDUAL_COVERAGE_COLUMNS,
        RESIDUAL_ROSTER_HASH_COLUMN,
    }
    missing = sorted(required.difference(residual_returns.columns))
    if missing:
        raise ValueError(f"residual evidence missing required columns: {missing}")
    lineage = def_validate_residual_lineage_fields(residual_returns)
    def_validate_residual_daily_coverage(residual_returns)
    def_validate_residual_availability(residual_returns)

    attributes = residual_returns.attrs
    row_policy = {
        "MarketUniverse": REQUIRED_RESIDUAL_UNIVERSE,
        "ResidualizationUniverse": REQUIRED_RESIDUAL_UNIVERSE,
        "TSMCExcluded": True,
        "TSMCExcludedFromMarketFactor": True,
        "PointInTime": True,
        "ResidualLineageSchema": REQUIRED_RESIDUAL_LINEAGE_SCHEMA,
        "ResidualLineageUniverseVersionPolicy": (
            RESIDUAL_LINEAGE_UNIVERSE_VERSION_POLICY
        ),
        "ResidualLineageUniverseKnowledgeCutoffPolicy": (
            RESIDUAL_LINEAGE_UNIVERSE_KNOWLEDGE_CUTOFF_POLICY
        ),
    }
    for column, expected in row_policy.items():
        if residual_returns[column].isna().any() or residual_returns[column].nunique(
            dropna=False
        ) != 1:
            raise ValueError(
                f"residual evidence row-level provenance is missing or inconsistent: {column}"
            )
        observed = residual_returns[column].iloc[0]
        matches = (
            isinstance(expected, bool)
            and isinstance(observed, (bool, np.bool_))
            and bool(observed) is expected
        ) or (not isinstance(expected, bool) and str(observed) == str(expected))
        if not matches:
            raise ValueError(
                f"residual evidence row-level provenance mismatch: {column}={observed!r}"
            )
        if column in attributes and attributes[column] != observed:
            raise ValueError(
                f"residual evidence attrs and row-level provenance disagree: {column}"
            )
    if residual_returns["ResidualLineageId"].isna().any() or residual_returns[
        "ResidualLineageId"
    ].nunique(dropna=False) != 1:
        raise ValueError("residual evidence has missing or inconsistent lineage identity")
    lineage_id = residual_returns["ResidualLineageId"].iloc[0]
    if not str(lineage_id).strip():
        raise ValueError("residual evidence row-level lineage identity is blank")
    if (
        "ResidualLineageId" in attributes
        and attributes["ResidualLineageId"] != lineage_id
    ):
        raise ValueError("residual evidence attrs contradict row-level lineage identity")

    for column in ("FactorLane", "WindowDays", "ResidualSourceColumn"):
        if residual_returns[column].isna().any() or residual_returns[column].nunique(
            dropna=False
        ) != 1:
            raise ValueError(f"residual evidence has inconsistent model identity: {column}")
    factor_lane = str(residual_returns["FactorLane"].iloc[0])
    if factor_lane not in RESIDUAL_FACTOR_LANES:
        raise ValueError("residual evidence has an unsupported factor lane")
    raw_window_days = residual_returns["WindowDays"].iloc[0]
    if isinstance(raw_window_days, (bool, np.bool_)):
        raise ValueError("residual evidence has invalid WindowDays")
    try:
        numeric_window_days = float(raw_window_days)
    except (TypeError, ValueError) as error:
        raise ValueError("residual evidence has invalid WindowDays") from error
    if (
        not np.isfinite(numeric_window_days)
        or not numeric_window_days.is_integer()
        or numeric_window_days < 2
    ):
        raise ValueError("residual evidence has invalid WindowDays")
    window_days = int(numeric_window_days)
    expected_source = f"Residual_{factor_lane}_{window_days}D"
    if str(residual_returns["ResidualSourceColumn"].iloc[0]) != expected_source:
        raise ValueError("residual evidence factor/window/source identity mismatch")
    declared_lane_sequence = tuple(
        str(lineage["ResidualLineageFactorLanes"]).split("|")
    )
    if declared_lane_sequence != tuple(RESIDUAL_FACTOR_LANES):
        raise ValueError("residual evidence lineage must declare exactly both factor lanes")
    declared_lanes = set(declared_lane_sequence)
    try:
        declared_window_sequence = tuple(
            int(value)
            for value in str(lineage["ResidualLineageWindows"]).split("|")
            if value
        )
    except ValueError as error:
        raise ValueError("residual evidence lineage has invalid window identities") from error
    if (
        not declared_window_sequence
        or any(value < 2 for value in declared_window_sequence)
        or declared_window_sequence != tuple(sorted(set(declared_window_sequence)))
    ):
        raise ValueError("residual evidence lineage has invalid window identities")
    declared_windows = set(declared_window_sequence)
    if factor_lane not in declared_lanes or window_days not in declared_windows:
        raise ValueError("residual evidence model identity is absent from lineage")
    optional_model_attrs = {
        "FactorLane": factor_lane,
        "WindowDays": window_days,
        "ResidualSourceColumn": expected_source,
    }
    for field, expected in optional_model_attrs.items():
        if field not in attributes:
            continue
        observed = attributes[field]
        if field == "WindowDays":
            try:
                matches = float(observed) == float(expected)
            except (TypeError, ValueError):
                matches = False
        else:
            matches = str(observed) == str(expected)
        if not matches:
            raise ValueError(
                f"residual evidence attrs contradict model identity: {field}"
            )
    def_validate_residual_model_audit(
        residual_returns,
        window_days=window_days,
        residual_column="ResidualReturn",
        status_column="ResidualModelStatus",
        policy_column="ResidualWindowPolicy",
        observations_column="ResidualBetaObservations",
    )

    frame = residual_returns.copy()
    frame["Date"] = frame["Date"].map(def_safe_local_date)
    frame["Ticker"] = frame["Ticker"].map(def_ticker_base)
    if frame["Ticker"].eq(TSMC_BASE).any():
        raise ValueError("residual evidence contains the isolated 2330 anchor")
    frame["ResidualReturn"] = pd.to_numeric(frame["ResidualReturn"], errors="coerce")
    duplicate = frame.duplicated(["Date", "Ticker"], keep=False)
    if duplicate.any():
        raise ValueError(
            f"residual evidence has {int(duplicate.sum())} duplicate Date+Ticker rows"
        )
    if "ResidualReturnAvailableAt" in frame.columns:
        frame["ResidualReturnAvailableAt"] = pd.to_datetime(
            frame["ResidualReturnAvailableAt"].map(def_safe_available_at_utc),
            errors="coerce",
            utc=True,
        )
        frame["ResidualAvailabilityPolicy"] = "EXPLICIT_EVIDENCE_TIMESTAMP"
    else:
        frame["ResidualReturnAvailableAt"] = pd.Series(
            pd.NaT, index=frame.index, dtype="datetime64[ns, UTC]"
        )
        frame["ResidualAvailabilityPolicy"] = (
            "INHERIT_VALIDATED_MARKET_CLOSE_TIMESTAMP"
        )

    keep = [
        "Date",
        "Ticker",
        "Market",
        "ResidualReturn",
        "ResidualReturnAvailableAt",
        "ResidualAvailabilityPolicy",
        "FactorLane",
        "WindowDays",
        "ResidualSourceColumn",
        "ResidualModelStatus",
        "ResidualWindowPolicy",
        "ResidualBetaObservations",
        *RESIDUAL_COVERAGE_COLUMNS,
        RESIDUAL_ROSTER_HASH_COLUMN,
    ]
    return frame[keep].sort_values(["Ticker", "Date"], kind="stable").reset_index(
        drop=True
    )


def def_choose_peer_bucket(
    frame: pd.DataFrame,
    config: StockPositioningConfig,
) -> pd.DataFrame:
    result = frame.copy()
    selected = next(
        (
            column
            for column in config.peer_bucket_candidates
            if column in result.columns and result[column].notna().any()
        ),
        None,
    )
    if selected is None:
        result["PeerBucket"] = "ALL_TWSE_TPEX_EX_2330"
        result["PeerDefinitionStatus"] = (
            "FALLBACK_ALL_TWSE_TPEX_EX_2330_NO_SIZE_HISTORY"
        )
        result["PeerBucketSource"] = "FULL_MARKET"
    else:
        labels = result[selected].fillna("").astype(str).str.strip().str.upper()
        result["PeerBucket"] = labels.where(labels.ne(""))
        result["PeerDefinitionStatus"] = np.where(
            labels.ne(""),
            "PASS_DYNAMIC_GLOBAL_SIZE_BUCKET",
            "HOLD_SIZE_BUCKET_MISSING",
        )
        result["PeerBucketSource"] = selected
    return result


def def_prepare_positioning_panel(
    prepared_stock: pd.DataFrame,
    *,
    residual_returns: pd.DataFrame | None = None,
    as_of_date: Any | None = None,
    config: StockPositioningConfig = StockPositioningConfig(),
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Validate the all-stock gate and create auditable daily base features."""

    gate_status = str(prepared_stock.attrs.get("FullMarketGateStatus", "")).upper()
    if gate_status != REQUIRED_FULL_MARKET_GATE_STATUS:
        raise ValueError(
            "stock positioning requires provenance from the complete TWSE+TPEX "
            "ordinary-share gate"
        )
    required = {
        "Date",
        "Ticker",
        "Exchange",
        "IsEligibleEquity",
        "IsTSMC",
        "ETR",
        "ETRStatus",
        "AttentionETR",
        "LimitLockDataStatus",
        "IsLimitUpLocked",
        "IsLimitDownLocked",
        "MarketDataAvailableAt",
        "Adj_Close",
        "ForeignNetAmount",
        "ForeignNetAmountAvailableAt",
        "ETFActiveValue",
        "ETFActiveValueAvailableAt",
    }
    missing = sorted(required.difference(prepared_stock.columns))
    if missing:
        raise ValueError(f"prepared stock flow panel missing required columns: {missing}")

    frame = prepared_stock.copy()
    frame["Date"] = frame["Date"].map(def_safe_local_date)
    frame["Ticker"] = frame["Ticker"].map(def_ticker_base)
    boundary: pd.Timestamp | None = None
    if as_of_date is not None:
        boundary = def_safe_local_date(as_of_date)
        frame = frame.loc[frame["Date"].le(boundary)].copy()
    invalid_key = frame["Date"].isna() | frame["Ticker"].eq("")
    if invalid_key.any():
        raise ValueError(f"prepared stock flow panel has {int(invalid_key.sum())} invalid keys")
    duplicate = frame.duplicated(["Date", "Ticker"], keep=False)
    if duplicate.any():
        raise ValueError(
            f"prepared stock flow panel has {int(duplicate.sum())} duplicate Date+Ticker rows"
        )

    # Domestic institutions remain distinct from foreign institutions.  The
    # active-ETF lane is not added here because investment-trust trading can
    # overlap with portfolio changes.
    if "InstitutionalDomesticNetAmount" in frame.columns:
        domestic = pd.to_numeric(
            frame["InstitutionalDomesticNetAmount"], errors="coerce"
        )
        domestic_available = frame.get(
            "InstitutionalDomesticNetAmountAvailableAt",
            pd.Series(pd.NaT, index=frame.index),
        )
    elif {"InvestmentTrustNetAmount", "DealerNetAmount"}.issubset(frame.columns):
        domestic = frame[["InvestmentTrustNetAmount", "DealerNetAmount"]].apply(
            pd.to_numeric, errors="coerce"
        ).sum(axis=1, min_count=2)
        domestic_available = frame[
            ["InvestmentTrustNetAmountAvailableAt", "DealerNetAmountAvailableAt"]
        ].apply(lambda row: def_latest_timestamp(row), axis=1)
    else:
        domestic = pd.Series(np.nan, index=frame.index)
        domestic_available = pd.Series(pd.NaT, index=frame.index)

    frame["ForeignDirectionalAmount"] = pd.to_numeric(
        frame["ForeignNetAmount"], errors="coerce"
    )
    frame["ForeignDirectionalAmountAvailableAt"] = frame[
        "ForeignNetAmountAvailableAt"
    ].map(def_safe_available_at_utc)
    frame["DomesticExForeignDirectionalAmount"] = domestic
    frame["DomesticExForeignDirectionalAmountAvailableAt"] = domestic_available.map(
        def_safe_available_at_utc
    )
    frame["ActiveETFDirectionalAmount"] = pd.to_numeric(
        frame["ETFActiveValue"], errors="coerce"
    )
    frame["ActiveETFDirectionalAmountAvailableAt"] = frame[
        "ETFActiveValueAvailableAt"
    ].map(def_safe_available_at_utc)
    frame["MarketDataAvailableAt"] = frame["MarketDataAvailableAt"].map(
        def_safe_available_at_utc
    )

    coverage = def_validate_full_market_coverage(frame)
    if coverage.empty:
        raise ValueError("prepared stock flow panel has no market sessions")
    coverage["FullMarketGateStatus"] = gate_status
    limit_audit = (
        frame.groupby("Date", as_index=False)
        .agg(
            MarketLimitStatusUnknownCount=(
                "LimitLockDataStatus",
                lambda values: int(values.ne("PASS_LIMIT_LOCK_FLAGS").sum()),
            ),
            MarketAvailabilityMissingCount=(
                "MarketDataAvailableAt",
                lambda values: int(values.isna().sum()),
            ),
        )
    )
    coverage = coverage.merge(limit_audit, on="Date", how="left", validate="one_to_one")
    coverage["PositioningGateStatus"] = np.select(
        [
            coverage["CoverageStatus"].ne("PASS"),
            coverage["MarketLimitStatusUnknownCount"].gt(0),
            coverage["MarketAvailabilityMissingCount"].gt(0),
        ],
        [
            "HOLD_FULL_MARKET_ETR_COVERAGE",
            "HOLD_MARKET_LIMIT_LOCK_COVERAGE",
            "HOLD_MARKET_AVAILABILITY_COVERAGE",
        ],
        default="PASS",
    )

    ordinary = frame.loc[
        frame["IsEligibleEquity"].fillna(False)
        & frame["Ticker"].ne(def_ticker_base(config.tsmc_ticker))
    ].copy()
    ordinary = ordinary.merge(
        coverage[
            [
                "Date",
                "MarketETRExTSMC",
                "MarketAttentionAvailableAt",
                "CoverageStatus",
                "PositioningGateStatus",
            ]
        ],
        on="Date",
        how="left",
        validate="many_to_one",
    )
    ordinary["AttentionShare"] = np.where(
        ordinary["PositioningGateStatus"].eq("PASS")
        & ordinary["MarketETRExTSMC"].gt(0),
        pd.to_numeric(ordinary["AttentionETR"], errors="coerce")
        / ordinary["MarketETRExTSMC"],
        np.nan,
    )
    ordinary["AttentionInterpretation"] = "NON_DIRECTIONAL_MARKET_ATTENTION"
    ordinary["TSMCExcluded"] = True
    ordinary["FullMarketGateStatus"] = gate_status
    ordinary["FullMarketUniverse"] = prepared_stock.attrs.get(
        "FullMarketUniverse", "TWSE_TPEX_COMMON_EQUITY_WITH_2330_ANCHOR"
    )

    ordinary = ordinary.sort_values(["Ticker", "Date"], kind="stable")
    ordinary["StockReturn"] = ordinary.groupby("Ticker", sort=False)[
        "Adj_Close"
    ].pct_change(fill_method=None)
    ordinary["StockReturnAvailableAt"] = ordinary["MarketDataAvailableAt"]

    formal_residual_supplied = residual_returns is not None and not residual_returns.empty
    if formal_residual_supplied:
        residual_input = residual_returns
        if boundary is not None:
            residual_dates = residual_returns["Date"].map(def_safe_local_date)
            if residual_dates.isna().any():
                raise ValueError("residual evidence contains invalid dates")
            residual_input = residual_returns.loc[
                residual_dates.le(boundary)
            ].copy()
            residual_input.attrs.update(residual_returns.attrs)
        residual = def_prepare_residual_evidence(residual_input)
        market_roster = ordinary[["Date", "Ticker", "Exchange"]].rename(
            columns={"Exchange": "Market"}
        )
        market_roster["Market"] = (
            market_roster["Market"].fillna("").astype(str).str.strip().str.upper()
        )
        residual_roster = residual[["Date", "Ticker", "Market"]].copy()
        residual_roster["Market"] = (
            residual_roster["Market"].fillna("").astype(str).str.strip().str.upper()
        )
        roster_comparison = market_roster.merge(
            residual_roster,
            on=["Date", "Ticker", "Market"],
            how="outer",
            indicator=True,
            validate="one_to_one",
        )
        if not roster_comparison["_merge"].eq("both").all():
            mismatch = roster_comparison.loc[
                roster_comparison["_merge"].ne("both"),
                ["Date", "Ticker", "Market", "_merge"],
            ].head(10)
            raise ValueError(
                "prepared stock and residual ex-2330 daily rosters disagree: "
                f"{mismatch.to_dict('records')}"
            )
        ordinary = ordinary.merge(
            residual,
            on=["Date", "Ticker"],
            how="left",
            validate="one_to_one",
        )
        inherit_time = (
            ordinary["ResidualReturn"].notna()
            & ordinary["ResidualReturnAvailableAt"].isna()
            & ordinary["ResidualAvailabilityPolicy"].eq(
                "INHERIT_VALIDATED_MARKET_CLOSE_TIMESTAMP"
            )
        )
        ordinary.loc[inherit_time, "ResidualReturnAvailableAt"] = ordinary.loc[
            inherit_time, "MarketDataAvailableAt"
        ]
    else:
        ordinary["ResidualReturn"] = np.nan
        ordinary["ResidualReturnAvailableAt"] = pd.NaT
        ordinary["ResidualAvailabilityPolicy"] = "NO_RESIDUAL_EVIDENCE_SUPPLIED"
        ordinary["FactorLane"] = None
        ordinary["WindowDays"] = pd.NA
        ordinary["ResidualSourceColumn"] = None

    has_residual_value = ordinary["ResidualReturn"].notna()
    if formal_residual_supplied:
        # A formal broad-market-adjusted run must never silently mix raw
        # returns into the residual history during beta warm-up or data gaps.
        ordinary["PriceEvidenceValue"] = ordinary["ResidualReturn"]
        ordinary["PriceEvidenceAvailableAt"] = ordinary[
            "ResidualReturnAvailableAt"
        ].where(has_residual_value)
        ordinary["PriceEvidenceBasis"] = np.where(
            has_residual_value,
            "EX_TSMC_RESIDUAL_RETURN",
            "HOLD_EX_TSMC_RESIDUAL_NOT_AVAILABLE",
        )
    else:
        ordinary["PriceEvidenceValue"] = ordinary["StockReturn"]
        ordinary["PriceEvidenceAvailableAt"] = ordinary[
            "StockReturnAvailableAt"
        ].where(ordinary["StockReturn"].notna())
        ordinary["PriceEvidenceBasis"] = np.where(
            ordinary["StockReturn"].notna(),
            "RAW_STOCK_RETURN_EXPLORATORY_ONLY",
            "HOLD_RAW_STOCK_RETURN_NOT_AVAILABLE",
        )
    ordinary = def_choose_peer_bucket(ordinary, config)
    ordinary = ordinary.sort_values(["Ticker", "Date"], kind="stable").reset_index(
        drop=True
    )
    ordinary.attrs.update(prepared_stock.attrs)
    ordinary.attrs.update(
        {
            "EngineId": ENGINE_ID,
            "EngineVersion": ENGINE_VERSION,
            "TSMCExcluded": True,
            "AttentionDirection": "NON_DIRECTIONAL",
            "DirectionalLanes": tuple(LANE_CONTRACT),
        }
    )
    coverage.attrs.update(ordinary.attrs)
    return ordinary, coverage


def def_build_stock_window_features(
    panel: pd.DataFrame,
    config: StockPositioningConfig = StockPositioningConfig(),
) -> pd.DataFrame:
    """Build T-1 temporal and same-day cross-sectional evidence thresholds."""

    windows = def_resolve_windows(config.windows)
    pieces: list[pd.DataFrame] = []
    for _, ticker_history in panel.groupby("Ticker", sort=True):
        history = ticker_history.sort_values("Date", kind="stable").copy()
        history["PriceThresholdValue"] = history["PriceEvidenceValue"].where(
            history["PriceEvidenceAvailableAt"].notna()
        )
        for window in windows:
            part = history.copy()
            part["EvidenceWindowDays"] = window
            for column, prefix in (
                ("AttentionShare", "Attention"),
                ("PriceThresholdValue", "Price"),
            ):
                part[f"{prefix}PriorMedian"] = (
                    history[column]
                    .shift(1)
                    .rolling(window, min_periods=window)
                    .median()
                )
                part[f"{prefix}WindowMedian"] = history[column].rolling(
                    window, min_periods=window
                ).median()
            pieces.append(part)
    result = pd.concat(pieces, ignore_index=True, sort=False)
    peer_keys = ["Date", "PeerBucket", "EvidenceWindowDays"]
    for column, prefix in (
        ("AttentionShare", "Attention"),
        ("PriceThresholdValue", "Price"),
    ):
        peer_group = result.groupby(peer_keys, dropna=False)[column]
        result[f"{prefix}PeerMedian"] = peer_group.transform(
            def_leave_one_out_peer_median
        )
        result[f"{prefix}PeerCount"] = (
            peer_group.transform("count") - result[column].notna().astype(int)
        ).astype("Int64")
        result[f"{prefix}DynamicState"] = def_state_against_dynamic_medians(
            result[column],
            result[f"{prefix}PriorMedian"],
            result[f"{prefix}PeerMedian"],
            result[f"{prefix}PeerCount"],
        )
    price_peer_group = result.groupby(peer_keys, dropna=False)
    result["PricePeerAvailableAt"] = price_peer_group[
        "PriceEvidenceAvailableAt"
    ].transform("max")
    price_untimed = result["PriceEvidenceValue"].notna() & result[
        "PriceEvidenceAvailableAt"
    ].isna()
    result["PricePeerUntimedValueCount"] = (
        price_untimed.groupby(
            [result[key] for key in peer_keys], dropna=False
        )
        .transform("sum")
        .astype("Int64")
    )
    result["AttentionPersistenceState"] = np.select(
        [
            result["AttentionWindowMedian"].gt(result["AttentionPriorMedian"]),
            result["AttentionWindowMedian"].lt(result["AttentionPriorMedian"]),
            result["AttentionWindowMedian"].notna()
            & result["AttentionPriorMedian"].notna(),
        ],
        [
            "WINDOW_ATTENTION_ABOVE_PRIOR_MEDIAN",
            "WINDOW_ATTENTION_BELOW_PRIOR_MEDIAN",
            "WINDOW_ATTENTION_AT_PRIOR_MEDIAN",
        ],
        default="HOLD_INSUFFICIENT_WINDOW_HISTORY",
    )
    result["PricePersistenceState"] = np.select(
        [
            result["PriceWindowMedian"].gt(0),
            result["PriceWindowMedian"].lt(0),
            result["PriceWindowMedian"].eq(0),
        ],
        [
            "WINDOW_PRICE_POSITIVE",
            "WINDOW_PRICE_NEGATIVE",
            "WINDOW_PRICE_FLAT",
        ],
        default="HOLD_INSUFFICIENT_WINDOW_HISTORY",
    )
    result["DynamicThresholdPolicy"] = (
        "CURRENT_VS_STRICT_T_MINUS_1_ROLLING_MEDIAN_AND_SAME_DAY_LEAVE_ONE_OUT_PEER_MEDIAN"
    )
    result.attrs.update(panel.attrs)
    return result.sort_values(
        ["Date", "Ticker", "EvidenceWindowDays"], kind="stable"
    ).reset_index(drop=True)


def def_classify_lane_category(frame: pd.DataFrame) -> pd.Series:
    lane_accumulation = (
        frame["DirectionalAmount"].gt(0)
        & frame["DirectionalDynamicState"].eq(
            "ABOVE_PRIOR_AND_PEER_MEDIANS"
        )
    )
    lane_distribution = (
        frame["DirectionalAmount"].lt(0)
        & frame["DirectionalDynamicState"].eq(
            "BELOW_PRIOR_AND_PEER_MEDIANS"
        )
    )
    stable_positive = frame["DirectionalWindowMedian"].gt(0)
    attention_expansion = frame["AttentionDynamicState"].eq(
        "ABOVE_PRIOR_AND_PEER_MEDIANS"
    )
    attention_contraction = frame["AttentionDynamicState"].eq(
        "BELOW_PRIOR_AND_PEER_MEDIANS"
    )
    price_strength = frame["PriceEvidenceValue"].gt(0) & frame[
        "PriceDynamicState"
    ].eq("ABOVE_PRIOR_AND_PEER_MEDIANS")
    price_weakness = frame["PriceEvidenceValue"].lt(0) & frame[
        "PriceDynamicState"
    ].eq("BELOW_PRIOR_AND_PEER_MEDIANS")

    dynamic_ready = ~frame[
        ["DirectionalDynamicState", "AttentionDynamicState", "PriceDynamicState"]
    ].apply(lambda column: column.str.startswith("HOLD_"), axis=0).any(axis=1)
    local_lock_known = frame["LimitLockDataStatus"].eq("PASS_LIMIT_LOCK_FLAGS")
    session_locked = frame["IsLimitUpLocked"].fillna(False) | frame[
        "IsLimitDownLocked"
    ].fillna(False)
    lane_ready = frame["DirectionalAmount"].notna() & frame[
        "DirectionalAmountAvailableAt"
    ].notna()
    price_ready = frame["PriceEvidenceValue"].notna() & frame[
        "PriceEvidenceAvailableAt"
    ].notna()
    peer_ready = ~frame["PeerDefinitionStatus"].astype(str).str.startswith("HOLD_")
    peer_time_ready = frame["DirectionalPeerUntimedValueCount"].eq(0) & frame[
        "PricePeerUntimedValueCount"
    ].eq(0)

    categories = np.select(
        [
            ~local_lock_known,
            session_locked,
            frame["PositioningGateStatus"].ne("PASS"),
            ~peer_ready,
            ~lane_ready,
            ~price_ready,
            ~peer_time_ready,
            ~dynamic_ready,
            lane_accumulation & attention_expansion & ~price_strength & stable_positive,
            lane_accumulation & attention_expansion & ~price_strength,
            lane_accumulation & attention_expansion & price_strength,
            lane_distribution & attention_contraction & ~price_weakness,
            lane_distribution & attention_contraction & price_weakness,
            lane_accumulation,
            lane_distribution,
            attention_expansion,
            attention_contraction,
        ],
        [
            "HOLD_LIMIT_STATUS_UNKNOWN",
            "HOLD_LIMIT_LOCKED_SESSION",
            "HOLD_FULL_MARKET_EVIDENCE_GATE",
            "HOLD_PEER_BUCKET_MISSING",
            "HOLD_DIRECTIONAL_VALUE_OR_TIME_MISSING",
            "HOLD_PRICE_VALUE_OR_TIME_MISSING",
            "HOLD_PEER_EVIDENCE_TIME_INCOMPLETE",
            "HOLD_INSUFFICIENT_DYNAMIC_HISTORY_OR_PEERS",
            "EARLY_POSITIONING_STABLE_BEFORE_PRICE",
            "EARLY_POSITIONING_PULSE_BEFORE_PRICE",
            "POSITIONING_WITH_PRICE_CONFIRMATION",
            "EARLY_EXIT_BEFORE_PRICE_WEAKNESS",
            "EXIT_WITH_PRICE_WEAKNESS_CONFIRMATION",
            "DIRECTIONAL_ACCUMULATION_WITHOUT_ATTENTION_CONFIRMATION",
            "DIRECTIONAL_DISTRIBUTION_WITHOUT_ATTENTION_CONFIRMATION",
            "ATTENTION_EXPANSION_WITHOUT_DIRECTIONAL_CONFIRMATION",
            "ATTENTION_CONTRACTION_WITHOUT_DIRECTIONAL_CONFIRMATION",
        ],
        default="NO_CONVERGENT_EVIDENCE",
    )
    return pd.Series(categories, index=frame.index, dtype="object")


def def_classify_positioning_sequence(frame: pd.DataFrame) -> pd.Series:
    """Describe the observable capital/price phase without asserting causality."""

    lane_accumulation = (
        frame["DirectionalAmount"].gt(0)
        & frame["DirectionalDynamicState"].eq(
            "ABOVE_PRIOR_AND_PEER_MEDIANS"
        )
    )
    lane_distribution = (
        frame["DirectionalAmount"].lt(0)
        & frame["DirectionalDynamicState"].eq(
            "BELOW_PRIOR_AND_PEER_MEDIANS"
        )
    )
    attention_expansion = frame["AttentionDynamicState"].eq(
        "ABOVE_PRIOR_AND_PEER_MEDIANS"
    )
    stable_capital = frame["DirectionalWindowMedian"].gt(0)
    price_pullback_or_sideways = frame["PriceWindowMedian"].le(0)
    price_restart = frame["PriceEvidenceValue"].gt(0) & frame[
        "PriceDynamicState"
    ].eq("ABOVE_PRIOR_AND_PEER_MEDIANS")
    price_weakness = frame["PriceEvidenceValue"].lt(0) & frame[
        "PriceDynamicState"
    ].eq("BELOW_PRIOR_AND_PEER_MEDIANS")
    stable_positioning = stable_capital & lane_accumulation & attention_expansion
    held_category = frame["EvidenceCategory"].astype(str).str.startswith("HOLD_")

    phases = np.select(
        [
            held_category,
            lane_distribution & stable_capital & price_weakness,
            lane_distribution & stable_capital & ~price_weakness,
            stable_positioning & price_restart & price_pullback_or_sideways,
            stable_positioning & price_pullback_or_sideways,
            stable_capital & price_pullback_or_sideways,
            stable_capital,
        ],
        [
            "HOLD_REQUIRED_EVIDENCE",
            "EXIT_WITH_PRICE_BREAKDOWN_OBSERVED",
            "EARLY_DISTRIBUTION_WHILE_PRICE_HOLDS_OBSERVED",
            "PRICE_RESTART_AFTER_STABLE_POSITIONING_OBSERVED",
            "STABLE_POSITIONING_DURING_PRICE_PULLBACK_OR_SIDEWAYS_OBSERVED",
            "PRICE_PULLBACK_OR_SIDEWAYS_WITH_SETTLED_CAPITAL_OBSERVED",
            "DIRECTIONAL_CAPITAL_SETTLEMENT_OBSERVED",
        ],
        default="NO_ORDERED_POSITIONING_PHASE_EVIDENCE",
    )
    return pd.Series(phases, index=frame.index, dtype="object")


def def_next_session(
    evidence_date: Any,
    available_at: Any,
    trading_calendar: pd.DatetimeIndex,
) -> pd.Timestamp | pd.NaT:
    if pd.isna(available_at):
        return pd.NaT
    local_available_date = def_safe_local_date(available_at)
    boundary = max(def_safe_local_date(evidence_date), local_available_date)
    later = trading_calendar[trading_calendar > boundary]
    return pd.Timestamp(later[0]) if len(later) else pd.NaT


def def_next_session_series(
    evidence_date: pd.Series,
    available_at: pd.Series,
    trading_calendar: pd.DatetimeIndex,
) -> pd.Series:
    """Vectorized equivalent of :func:`def_next_session`.

    The stock grid contains one row for every stock/window/directional lane.
    Calling the scalar helper with ``DataFrame.apply(axis=1)`` therefore
    dominated runtime at full-universe scale.  ``searchsorted`` preserves the
    exact strict-next-session rule while doing one calendar lookup per array.
    """

    evidence = pd.to_datetime(evidence_date, errors="coerce").dt.normalize()
    available = pd.to_datetime(available_at, errors="coerce", utc=True)
    available_local = (
        available.dt.tz_convert("Asia/Taipei").dt.tz_localize(None).dt.normalize()
    )
    complete = evidence.notna() & available_local.notna()
    boundary_values = evidence.to_numpy(dtype="datetime64[ns]", na_value=np.datetime64("NaT"))
    available_values = available_local.to_numpy(
        dtype="datetime64[ns]", na_value=np.datetime64("NaT")
    )
    boundary_values[complete.to_numpy()] = np.maximum(
        boundary_values[complete.to_numpy()],
        available_values[complete.to_numpy()],
    )
    positions = trading_calendar.searchsorted(boundary_values, side="right")
    result = np.full(len(evidence), np.datetime64("NaT"), dtype="datetime64[ns]")
    has_next = complete.to_numpy() & (positions < len(trading_calendar))
    result[has_next] = trading_calendar.to_numpy(dtype="datetime64[ns]")[
        positions[has_next]
    ]
    return pd.Series(result, index=evidence_date.index)


def def_build_stock_lane_evidence(
    window_features: pd.DataFrame,
    trading_calendar: Iterable[Any],
) -> pd.DataFrame:
    """Emit one non-aggregated decision row per stock, window, and lane."""

    calendar = pd.DatetimeIndex(
        sorted(
            {
                def_safe_local_date(value)
                for value in trading_calendar
                if not pd.isna(def_safe_local_date(value))
            }
        )
    )
    if calendar.empty:
        raise ValueError("trading_calendar cannot be empty")

    lane_frames: list[pd.DataFrame] = []
    peer_keys = ["Date", "PeerBucket", "EvidenceWindowDays"]
    for lane_name, (amount_column, time_column) in LANE_CONTRACT.items():
        lane = window_features.copy()
        lane["DirectionalLane"] = lane_name
        lane["DirectionalAmount"] = pd.to_numeric(lane[amount_column], errors="coerce")
        lane["DirectionalAmountAvailableAt"] = lane[time_column].map(
            def_safe_available_at_utc
        )
        lane["DirectionalThresholdValue"] = lane["DirectionalAmount"].where(
            lane["DirectionalAmountAvailableAt"].notna()
        )
        prior_parts: list[pd.Series] = []
        window_parts: list[pd.Series] = []
        for (_, window), positions in lane.groupby(
            ["Ticker", "EvidenceWindowDays"], sort=False
        ).groups.items():
            ordered = lane.loc[positions].sort_values("Date")
            amount = ordered["DirectionalThresholdValue"]
            prior = amount.shift(1).rolling(int(window), min_periods=int(window)).median()
            current_window = amount.rolling(
                int(window), min_periods=int(window)
            ).median()
            prior_parts.append(pd.Series(prior.to_numpy(), index=ordered.index))
            window_parts.append(
                pd.Series(current_window.to_numpy(), index=ordered.index)
            )
        lane["DirectionalPriorMedian"] = pd.concat(prior_parts).sort_index()
        lane["DirectionalWindowMedian"] = pd.concat(window_parts).sort_index()
        peer_groups = lane.groupby(peer_keys, dropna=False)
        peer_group = peer_groups["DirectionalThresholdValue"]
        lane["DirectionalPeerMedian"] = peer_group.transform(
            def_leave_one_out_peer_median
        )
        lane["DirectionalPeerCount"] = (
            peer_group.transform("count")
            - lane["DirectionalThresholdValue"].notna().astype(int)
        ).astype("Int64")
        lane["DirectionalDynamicState"] = def_state_against_dynamic_medians(
            lane["DirectionalThresholdValue"],
            lane["DirectionalPriorMedian"],
            lane["DirectionalPeerMedian"],
            lane["DirectionalPeerCount"],
        )
        lane["DirectionalPeerAvailableAt"] = peer_groups[
            "DirectionalAmountAvailableAt"
        ].transform("max")
        directional_untimed = lane["DirectionalAmount"].notna() & lane[
            "DirectionalAmountAvailableAt"
        ].isna()
        lane["DirectionalPeerUntimedValueCount"] = (
            directional_untimed.groupby(
                [lane[key] for key in peer_keys], dropna=False
            )
            .transform("sum")
            .astype("Int64")
        )
        lane["DirectionalPersistenceState"] = np.select(
            [
                lane["DirectionalWindowMedian"].gt(0),
                lane["DirectionalWindowMedian"].lt(0),
                lane["DirectionalWindowMedian"].eq(0),
            ],
            [
                "WINDOW_DIRECTIONAL_AMOUNT_POSITIVE",
                "WINDOW_DIRECTIONAL_AMOUNT_NEGATIVE",
                "WINDOW_DIRECTIONAL_AMOUNT_FLAT",
            ],
            default="HOLD_INSUFFICIENT_WINDOW_HISTORY",
        )
        lane["EvidenceCategory"] = def_classify_lane_category(lane)
        lane["PositioningSequencePhase"] = def_classify_positioning_sequence(lane)
        lane["SequenceInterpretation"] = (
            "OBSERVED_CAPITAL_PRICE_PHASE_NOT_CAUSAL_OR_COMPLETE_SEQUENCE"
        )
        required_time_columns = [
            "MarketAttentionAvailableAt",
            "DirectionalAmountAvailableAt",
            "DirectionalPeerAvailableAt",
            "PriceEvidenceAvailableAt",
            "PricePeerAvailableAt",
        ]
        required_times_complete = lane[required_time_columns].notna().all(axis=1)
        # Every input is normalized to UTC-aware datetime before this point.
        # Comparing the int64 nanosecond representations avoids the very slow
        # object-producing row-wise ``max`` path for timezone-aware values.
        time_values = np.column_stack(
            [lane[column].astype("int64").to_numpy() for column in required_time_columns]
        )
        latest_time_values = time_values.max(axis=1)
        lane["SignalAvailableAt"] = pd.to_datetime(
            latest_time_values, errors="coerce", utc=True
        )
        lane.loc[~required_times_complete, "SignalAvailableAt"] = pd.NaT
        lane["EffectiveDate"] = def_next_session_series(
            lane["Date"], lane["SignalAvailableAt"], calendar
        )
        no_next_session = (
            lane["SignalAvailableAt"].notna()
            & lane["EffectiveDate"].isna()
            & ~lane["EvidenceCategory"].astype(str).str.startswith("HOLD_")
        )
        lane.loc[no_next_session, "EvidenceCategory"] = (
            "HOLD_NO_NEXT_TRADABLE_SESSION"
        )
        lane["SignalTimingStatus"] = np.where(
            lane["SignalAvailableAt"].notna() & lane["EffectiveDate"].notna(),
            "PASS_NEXT_SESSION_AFTER_LATEST_REQUIRED_EVIDENCE",
            "HOLD_MISSING_TIME_OR_NEXT_SESSION",
        )
        lane["LaneAggregationPolicy"] = "EACH_DIRECTIONAL_LANE_REMAINS_SEPARATE"
        lane["TradeInstruction"] = False
        lane_frames.append(lane)

    result = pd.concat(lane_frames, ignore_index=True, sort=False)
    result.attrs.update(window_features.attrs)
    return result.sort_values(
        ["Date", "Ticker", "EvidenceWindowDays", "DirectionalLane"],
        kind="stable",
    ).reset_index(drop=True)


def def_prepare_membership_intervals(membership: pd.DataFrame) -> pd.DataFrame:
    if "EventType" in membership.columns:
        raise ValueError(
            "raw membership events cannot enter stock positioning; materialize PIT intervals first"
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
    if "ValidFrom" not in frame.columns and "MembershipValidFrom" in frame.columns:
        frame["ValidFrom"] = frame["MembershipValidFrom"]
    if "ValidTo" not in frame.columns and "MembershipValidTo" in frame.columns:
        frame["ValidTo"] = frame["MembershipValidTo"]
    if "ValidFrom" not in frame.columns:
        frame["ValidFrom"] = pd.NaT
    if "ValidTo" not in frame.columns:
        frame["ValidTo"] = pd.NaT
    frame["ValidFrom"] = frame["ValidFrom"].map(def_safe_local_date)
    frame["ValidTo"] = frame["ValidTo"].map(def_safe_local_date)
    if "Decision" not in frame.columns:
        frame["Decision"] = "APPROVED"
    frame["Decision"] = frame["Decision"].fillna("").astype(str).str.upper()
    if "ExposureShare" not in frame.columns:
        frame["ExposureShare"] = np.nan
    frame["ExposureShare"] = pd.to_numeric(frame["ExposureShare"], errors="coerce")
    invalid_share = frame["ExposureShare"].notna() & ~frame["ExposureShare"].between(
        0, 1
    )
    if invalid_share.any():
        raise ValueError(f"membership has {int(invalid_share.sum())} invalid exposure shares")
    if frame["GroupId"].eq("").any() or frame["Ticker"].eq("").any():
        raise ValueError("membership has blank GroupId or Ticker")
    return frame.sort_values(["Ticker", "GroupId", "ValidFrom"], kind="stable")


def def_active_membership(
    membership: pd.DataFrame,
    date: pd.Timestamp,
) -> pd.DataFrame:
    active = membership.loc[
        (membership["ValidFrom"].isna() | membership["ValidFrom"].le(date))
        & (membership["ValidTo"].isna() | membership["ValidTo"].ge(date))
        & membership["Decision"].isin(APPROVED_MEMBERSHIP_DECISIONS)
    ].copy()
    duplicate = active.duplicated(["GroupId", "Ticker"], keep=False)
    if duplicate.any():
        raise ValueError(
            f"membership has overlapping active intervals at {date:%Y-%m-%d}"
        )
    return active


def def_ticker_group_allocations(
    ticker: str,
    members: pd.DataFrame,
    *,
    conserved: bool,
) -> list[dict[str, Any]]:
    if members.empty:
        return [
            {
                "Ticker": ticker,
                "GroupId": UNMAPPED_GROUP_ID,
                "GroupName": "未映射",
                "AllocationWeight": 1.0,
                "AllocationMethod": "UNMAPPED_NO_ACTIVE_GROUP",
            }
        ]
    ordered = members.sort_values("GroupId", kind="stable").reset_index(drop=True)
    if not conserved:
        return [
            {
                "Ticker": ticker,
                "GroupId": row.GroupId,
                "GroupName": row.GroupName,
                "AllocationWeight": 1.0,
                "AllocationMethod": "FULL_WEIGHT_EACH_APPROVED_STORY",
            }
            for row in ordered.itertuples(index=False)
        ]

    shares = ordered["ExposureShare"]
    known = shares.notna()
    known_total = float(shares[known].sum()) if known.any() else 0.0
    if known_total > 1 + np.finfo(float).eps * 16:
        raise ValueError(f"audited exposure shares exceed one for {ticker}")
    weights = pd.Series(0.0, index=ordered.index)
    residual_to_unmapped = 0.0
    if not known.any():
        weights[:] = 1.0 / len(ordered)
        method = "EQUAL_SPLIT_NO_AUDITED_EXPOSURE"
    elif (~known).any():
        weights.loc[known] = shares.loc[known]
        weights.loc[~known] = (1.0 - known_total) / int((~known).sum())
        method = "AUDITED_EXPOSURE_PLUS_EQUAL_RESIDUAL"
    else:
        weights[:] = shares
        residual_to_unmapped = max(0.0, 1.0 - known_total)
        method = "AUDITED_EXPOSURE"
    rows = [
        {
            "Ticker": ticker,
            "GroupId": ordered.loc[index, "GroupId"],
            "GroupName": ordered.loc[index, "GroupName"],
            "AllocationWeight": float(weight),
            "AllocationMethod": method,
        }
        for index, weight in weights.items()
        if weight > 0
    ]
    if residual_to_unmapped > 0:
        rows.append(
            {
                "Ticker": ticker,
                "GroupId": UNMAPPED_GROUP_ID,
                "GroupName": "未映射",
                "AllocationWeight": residual_to_unmapped,
                "AllocationMethod": "UNMAPPED_AUDITED_EXPOSURE_RESIDUAL",
            }
        )
    if not np.isclose(sum(row["AllocationWeight"] for row in rows), 1.0):
        raise ValueError(f"conserved allocation failed for {ticker}")
    return rows


def def_map_evidence_to_story_groups(
    stock_evidence: pd.DataFrame,
    membership: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Map stock evidence to multi-label RAW and capital-conserved views."""

    prepared = def_prepare_membership_intervals(membership)
    evidence = stock_evidence.copy()
    evidence["Date"] = evidence["Date"].map(def_safe_local_date)
    evidence["Ticker"] = evidence["Ticker"].map(def_ticker_base)
    if "EffectiveDate" in evidence.columns:
        effective = evidence["EffectiveDate"].map(def_safe_local_date)
        evidence["MembershipLookupDate"] = effective.where(
            effective.notna(), evidence["Date"]
        )
        membership_timing = "ACTIVE_PIT_INTERVAL_AT_SIGNAL_EFFECTIVE_DATE"
    else:
        evidence["MembershipLookupDate"] = evidence["Date"]
        membership_timing = "ACTIVE_PIT_INTERVAL_AT_EVIDENCE_DATE"
    unique_keys = evidence[
        ["Date", "Ticker", "MembershipLookupDate"]
    ].drop_duplicates().reset_index(drop=True)
    unique_keys["_EvidenceKey"] = np.arange(len(unique_keys), dtype=np.int64)

    # Interval-join all evidence keys at once.  The previous nested
    # date→ticker→view loops performed hundreds of thousands of tiny frame
    # filters for a full TWSE+TPEX run.  This vectorized form applies the same
    # PIT interval and approval rules and then derives both allocation views
    # from one joined table.
    candidates = unique_keys.merge(
        prepared[
            [
                "Ticker",
                "GroupId",
                "GroupName",
                "ValidFrom",
                "ValidTo",
                "Decision",
                "ExposureShare",
            ]
        ],
        on="Ticker",
        how="left",
        validate="many_to_many",
    )
    active_mask = (
        candidates["GroupId"].notna()
        & (
            candidates["ValidFrom"].isna()
            | candidates["ValidFrom"].le(candidates["MembershipLookupDate"])
        )
        & (
            candidates["ValidTo"].isna()
            | candidates["ValidTo"].ge(candidates["MembershipLookupDate"])
        )
        & candidates["Decision"].isin(APPROVED_MEMBERSHIP_DECISIONS)
    )
    active = candidates.loc[active_mask].copy()
    duplicate = active.duplicated(["_EvidenceKey", "GroupId", "Ticker"], keep=False)
    if duplicate.any():
        first = active.loc[duplicate, "MembershipLookupDate"].iloc[0]
        raise ValueError(
            f"membership has overlapping active intervals at {pd.Timestamp(first):%Y-%m-%d}"
        )

    active_key_ids = pd.Index(active["_EvidenceKey"].unique())
    unmapped = unique_keys.loc[
        ~unique_keys["_EvidenceKey"].isin(active_key_ids)
    ].copy()

    allocation_columns = [
        "Date",
        "MembershipLookupDate",
        "Ticker",
        "GroupId",
        "GroupName",
        "AllocationWeight",
        "AllocationMethod",
        "AggregationView",
        "AdditiveAcrossGroups",
        "MembershipTiming",
    ]

    raw_active = active[
        ["Date", "MembershipLookupDate", "Ticker", "GroupId", "GroupName"]
    ].copy()
    raw_active["AllocationWeight"] = 1.0
    raw_active["AllocationMethod"] = "FULL_WEIGHT_EACH_APPROVED_STORY"
    raw_unmapped = unmapped[
        ["Date", "MembershipLookupDate", "Ticker"]
    ].copy()
    raw_unmapped["GroupId"] = UNMAPPED_GROUP_ID
    raw_unmapped["GroupName"] = "未映射"
    raw_unmapped["AllocationWeight"] = 1.0
    raw_unmapped["AllocationMethod"] = "UNMAPPED_NO_ACTIVE_GROUP"
    raw_allocation = pd.concat(
        [raw_active, raw_unmapped], ignore_index=True, sort=False
    )
    raw_allocation["AggregationView"] = "RAW_STORY_EXPOSURE_NOT_ADDITIVE"
    raw_allocation["AdditiveAcrossGroups"] = False
    raw_allocation["MembershipTiming"] = membership_timing

    if active.empty:
        conserved_active = active[
            ["Date", "MembershipLookupDate", "Ticker", "GroupId", "GroupName"]
        ].copy()
        conserved_active["AllocationWeight"] = pd.Series(dtype=float)
        conserved_active["AllocationMethod"] = pd.Series(dtype="object")
        residual_unmapped = pd.DataFrame(
            columns=[
                "Date",
                "MembershipLookupDate",
                "Ticker",
                "GroupId",
                "GroupName",
                "AllocationWeight",
                "AllocationMethod",
            ]
        )
    else:
        allocation_group = active.groupby("_EvidenceKey", sort=False, observed=True)
        known = active["ExposureShare"].notna()
        active["_KnownExposure"] = known.astype(np.int8)
        active["_KnownExposureValue"] = active["ExposureShare"].fillna(0.0)
        known_count = allocation_group["_KnownExposure"].transform("sum")
        known_total = allocation_group["_KnownExposureValue"].transform("sum")
        member_count = allocation_group["GroupId"].transform("size")
        unknown_count = member_count - known_count
        tolerance = np.finfo(float).eps * 16
        if known_total.gt(1.0 + tolerance).any():
            ticker = active.loc[known_total.gt(1.0 + tolerance), "Ticker"].iloc[0]
            raise ValueError(f"audited exposure shares exceed one for {ticker}")

        no_known = known_count.eq(0)
        some_unknown = unknown_count.gt(0)
        active["AllocationWeight"] = np.select(
            [no_known, known, some_unknown],
            [
                1.0 / member_count,
                active["ExposureShare"],
                (1.0 - known_total) / unknown_count.where(unknown_count.gt(0)),
            ],
            default=active["ExposureShare"],
        ).astype(float)
        active["AllocationMethod"] = np.select(
            [no_known, some_unknown],
            ["EQUAL_SPLIT_NO_AUDITED_EXPOSURE", "AUDITED_EXPOSURE_PLUS_EQUAL_RESIDUAL"],
            default="AUDITED_EXPOSURE",
        )
        conserved_active = active.loc[
            active["AllocationWeight"].gt(0),
            [
                "Date",
                "MembershipLookupDate",
                "Ticker",
                "GroupId",
                "GroupName",
                "AllocationWeight",
                "AllocationMethod",
            ],
        ].copy()

        all_known = unknown_count.eq(0)
        residual_mask = all_known & known_total.lt(1.0)
        residual_source = active.loc[residual_mask].drop_duplicates(
            "_EvidenceKey", keep="first"
        )
        residual_unmapped = residual_source[
            ["Date", "MembershipLookupDate", "Ticker"]
        ].copy()
        residual_unmapped["GroupId"] = UNMAPPED_GROUP_ID
        residual_unmapped["GroupName"] = "未映射"
        residual_unmapped["AllocationWeight"] = (
            1.0
            - known_total.loc[residual_source.index].to_numpy(dtype=float)
        )
        residual_unmapped["AllocationMethod"] = (
            "UNMAPPED_AUDITED_EXPOSURE_RESIDUAL"
        )

    conserved_unmapped = unmapped[
        ["Date", "MembershipLookupDate", "Ticker"]
    ].copy()
    conserved_unmapped["GroupId"] = UNMAPPED_GROUP_ID
    conserved_unmapped["GroupName"] = "未映射"
    conserved_unmapped["AllocationWeight"] = 1.0
    conserved_unmapped["AllocationMethod"] = "UNMAPPED_NO_ACTIVE_GROUP"
    conserved_allocation = pd.concat(
        [conserved_active, residual_unmapped, conserved_unmapped],
        ignore_index=True,
        sort=False,
    )
    conserved_allocation["AggregationView"] = "CONSERVED_STORY_ALLOCATION"
    conserved_allocation["AdditiveAcrossGroups"] = True
    conserved_allocation["MembershipTiming"] = membership_timing

    for allocation in (raw_allocation, conserved_allocation):
        allocation.sort_values(
            ["MembershipLookupDate", "Ticker", "Date", "GroupId"],
            kind="stable",
            inplace=True,
        )
        allocation.reset_index(drop=True, inplace=True)
    raw_allocation = raw_allocation[allocation_columns]
    conserved_allocation = conserved_allocation[allocation_columns]

    # Encode allocation labels before joining them to the wide evidence
    # frame.  This keeps both story views compact even while the second merge
    # is being built, rather than waiting for the orchestrator's final output
    # compaction pass.
    allocation_text_columns = (
        "Ticker",
        "GroupId",
        "GroupName",
        "AllocationMethod",
        "AggregationView",
        "MembershipTiming",
    )
    for allocation in (raw_allocation, conserved_allocation):
        for column in allocation_text_columns:
            categories = allocation[column].dropna().astype(object).unique().tolist()
            if "" not in categories:
                categories.append("")
            try:
                categories = sorted(categories)
            except TypeError:
                pass
            allocation[column] = pd.Categorical(
                allocation[column], categories=categories
            )

    def attach(allocation: pd.DataFrame) -> pd.DataFrame:
        mapped = evidence.merge(
            allocation,
            on=["Date", "Ticker", "MembershipLookupDate"],
            how="left",
            validate="many_to_many",
        )
        mapped["AllocatedDirectionalAmount"] = (
            mapped["AllocationWeight"] * mapped["DirectionalAmount"]
        )
        mapped["AllocatedAttentionETR"] = (
            mapped["AllocationWeight"] * mapped["AttentionETR"]
        )
        return mapped.sort_values(
            [
                "Date",
                "GroupId",
                "Ticker",
                "EvidenceWindowDays",
                "DirectionalLane",
            ],
            kind="stable",
        ).reset_index(drop=True)

    return {
        "raw_story_allocation": raw_allocation,
        "conserved_story_allocation": conserved_allocation,
        "raw_story_evidence": attach(raw_allocation),
        "conserved_story_evidence": attach(conserved_allocation),
    }


def def_build_stock_positioning_outputs(
    prepared_stock: pd.DataFrame,
    trading_calendar: Iterable[Any],
    *,
    residual_returns: pd.DataFrame | None = None,
    membership: pd.DataFrame | None = None,
    as_of_date: Any | None = None,
    config: StockPositioningConfig = StockPositioningConfig(),
) -> dict[str, pd.DataFrame]:
    """Public integration API for all-stock positioning evidence."""

    panel, market_gate = def_prepare_positioning_panel(
        prepared_stock,
        residual_returns=residual_returns,
        as_of_date=as_of_date,
        config=config,
    )
    features = def_build_stock_window_features(panel, config)
    evidence = def_build_stock_lane_evidence(features, trading_calendar)
    outputs: dict[str, pd.DataFrame] = {
        "market_gate_daily": market_gate,
        "stock_daily_base": panel,
        "stock_window_features": features,
        "stock_lane_evidence": evidence,
    }
    if membership is not None:
        outputs.update(def_map_evidence_to_story_groups(evidence, membership))
    for output in outputs.values():
        output.attrs.update(panel.attrs)
    return outputs


def def_self_test() -> dict[str, Any]:
    if __package__:
        from .via_full_market_factor_engine import def_residual_lineage_values
        from .via_group_flow_evidence_engine import def_prepare_stock_flow_panel
    else:
        from via_full_market_factor_engine import def_residual_lineage_values
        from via_group_flow_evidence_engine import def_prepare_stock_flow_panel

    dates = pd.bdate_range("2023-01-02", periods=510)
    tickers = (
        ("2330.TW", "TWSE"),
        ("1111.TW", "TWSE"),
        ("2222.TW", "TWSE"),
        ("3333.TWO", "TPEX"),
        ("4444.TWO", "TPEX"),
    )
    rows: list[dict[str, Any]] = []
    residual_rows: list[dict[str, Any]] = []
    for date_number, date in enumerate(dates):
        for ticker_number, (ticker, exchange) in enumerate(tickers):
            is_latest = date == dates[-1]
            base_turnover = 1_000.0 + 40.0 * ticker_number
            attention_shift = 0.0
            foreign = 0.5 * ticker_number
            residual = 0.0002 * (ticker_number - 2)
            if ticker.startswith("1111"):
                foreign = 2.0 if not is_latest else 12.0
                attention_shift = 800.0 if is_latest else 0.0
                residual = (
                    -0.001
                    if date_number >= len(dates) - 60 and not is_latest
                    else (0.001 if not is_latest else -0.004)
                )
            if ticker.startswith("2222"):
                foreign = 1.0 if not is_latest else -12.0
                attention_shift = -700.0 if is_latest else 0.0
                residual = -0.001 if not is_latest else 0.004
            turnover = max(150.0, base_turnover + attention_shift)
            rows.append(
                {
                    "Date": date,
                    "Ticker": ticker,
                    "Exchange": exchange,
                    "AssetType": "EQUITY",
                    "Adj_Close": 50.0
                    * (1.0 + 0.0005 * ticker_number) ** date_number,
                    "TurnoverValue": turnover,
                    "DayTradeTurnoverValue": 0.20 * turnover,
                    "MarketDataAvailableAt": f"{date:%Y-%m-%d} 13:40:00+08:00",
                    "ForeignNetAmount": foreign,
                    "ForeignNetAmountAvailableAt": f"{date:%Y-%m-%d} 18:00:00+08:00",
                    "InvestmentTrustNetAmount": 0.5 * foreign,
                    "InvestmentTrustNetAmountAvailableAt": f"{date:%Y-%m-%d} 18:01:00+08:00",
                    "DealerNetAmount": 0.25 * foreign,
                    "DealerNetAmountAvailableAt": f"{date:%Y-%m-%d} 18:02:00+08:00",
                    "MarginBalanceValue": 100.0 + date_number,
                    "MarginBalanceValueAvailableAt": f"{date:%Y-%m-%d} 19:00:00+08:00",
                    "ShortBalanceValue": 20.0,
                    "ShortBalanceValueAvailableAt": f"{date:%Y-%m-%d} 19:00:00+08:00",
                    "ETFActiveValue": 0.2 * foreign,
                    "ETFActiveValueAvailableAt": f"{date:%Y-%m-%d} 20:00:00+08:00",
                    "IsLimitUpLocked": False,
                    "IsLimitDownLocked": False,
                    "SizeBucket": "SMALL",
                }
            )
            if not ticker.startswith("2330"):
                beta_observations = min(date_number, 240)
                beta_ready = beta_observations >= 161
                residual_rows.append(
                    {
                        "Date": date,
                        "Ticker": ticker,
                        "Market": exchange,
                        "ResidualReturn": residual if beta_ready else np.nan,
                        "ResidualReturnAvailableAt": f"{date:%Y-%m-%d} 18:10:00+08:00",
                        "FactorLane": "LaggedETR",
                        "WindowDays": 240,
                        "ResidualSourceColumn": "Residual_LaggedETR_240D",
                        "ResidualModelStatus": (
                            "PASS"
                            if beta_ready
                            else "BLOCKED_INSUFFICIENT_T1_HISTORY"
                        ),
                        "ResidualWindowPolicy": "T_MINUS_1_ONLY;window=240;minimum=161",
                        "ResidualBetaObservations": beta_observations,
                        "ResidualUniverseExpectedTickerCount": 4,
                        "ResidualUniverseExpectedTWSECount": 2,
                        "ResidualUniverseExpectedTPEXCount": 2,
                        "ResidualUniverseRosterHash": hashlib.sha256(
                            (
                                "TPEX|3333.TWO\nTPEX|4444.TWO\n"
                                "TWSE|1111.TW\nTWSE|2222.TW"
                            ).encode("utf-8")
                        )
                        .hexdigest()
                        .upper(),
                    }
                )

    prepared = def_prepare_stock_flow_panel(pd.DataFrame(rows))
    prepared.attrs.update(
        {
            "FullMarketGateStatus": REQUIRED_FULL_MARKET_GATE_STATUS,
            "FullMarketUniverse": "TWSE_TPEX_COMMON_EQUITY_WITH_2330_ANCHOR",
            "PointInTime": True,
        }
    )
    residuals = pd.DataFrame(residual_rows)
    residual_row_provenance = {
        **def_residual_lineage_values((240,)),
        "MarketUniverse": REQUIRED_RESIDUAL_UNIVERSE,
        "ResidualizationUniverse": REQUIRED_RESIDUAL_UNIVERSE,
        "TSMCExcluded": True,
        "TSMCExcludedFromMarketFactor": True,
        "PointInTime": True,
    }
    for column, value in residual_row_provenance.items():
        residuals[column] = value
    residuals.attrs.update(
        {
            **residual_row_provenance,
            "FactorLane": "LaggedETR",
            "WindowDays": 240,
            "ResidualSourceColumn": "Residual_LaggedETR_240D",
        }
    )
    next_session = dates[-1] + pd.offsets.BDay(1)
    calendar = dates.append(pd.DatetimeIndex([next_session]))
    membership = pd.DataFrame(
        [
            {
                "GroupId": "G-A",
                "GroupName": "Story A",
                "Ticker": "1111.TW",
                "ValidFrom": dates[0],
                "Decision": "APPROVED",
                "ExposureShare": 0.7,
            },
            {
                "GroupId": "G-B",
                "GroupName": "Story B",
                "Ticker": "1111.TW",
                "ValidFrom": dates[0],
                "Decision": "APPROVED",
                "ExposureShare": 0.3,
            },
        ]
    )
    output = def_build_stock_positioning_outputs(
        prepared,
        calendar,
        residual_returns=residuals,
        membership=membership,
        as_of_date=dates[-1],
    )
    evidence = output["stock_lane_evidence"]
    latest = evidence.loc[
        evidence["Date"].eq(dates[-1])
        & evidence["EvidenceWindowDays"].eq(60)
        & evidence["DirectionalLane"].eq("FOREIGN")
    ].set_index("Ticker")

    assertions = 0
    assert "EARLY_POSITIONING" in latest.loc["1111", "EvidenceCategory"]
    assertions += 1
    assert latest.loc["2222", "EvidenceCategory"] == "EARLY_EXIT_BEFORE_PRICE_WEAKNESS"
    assertions += 1
    assert latest.loc["1111", "PositioningSequencePhase"] == (
        "STABLE_POSITIONING_DURING_PRICE_PULLBACK_OR_SIDEWAYS_OBSERVED"
    )
    assertions += 1
    assert latest.loc["2222", "PositioningSequencePhase"] == (
        "EARLY_DISTRIBUTION_WHILE_PRICE_HOLDS_OBSERVED"
    )
    assertions += 1
    assert latest.loc["1111", "EffectiveDate"] == next_session.normalize()
    assertions += 1
    assert latest.loc["1111", "SignalAvailableAt"] == pd.Timestamp(
        f"{dates[-1]:%Y-%m-%d} 10:10:00+00:00"
    )
    assertions += 1
    active_etf_time = evidence.loc[
        evidence["Date"].eq(dates[-1])
        & evidence["Ticker"].eq("1111")
        & evidence["EvidenceWindowDays"].eq(60)
        & evidence["DirectionalLane"].eq("ACTIVE_ETF"),
        "SignalAvailableAt",
    ].iloc[0]
    assert active_etf_time == pd.Timestamp(
        f"{dates[-1]:%Y-%m-%d} 12:00:00+00:00"
    )
    assertions += 1
    assert not evidence["Ticker"].eq(TSMC_BASE).any()
    assertions += 1
    assert set(evidence["EvidenceWindowDays"].unique()) == {60, 120, 240}
    assertions += 1
    assert set(evidence["DirectionalLane"].unique()) == set(LANE_CONTRACT)
    assertions += 1
    assert evidence["AttentionInterpretation"].eq(
        "NON_DIRECTIONAL_MARKET_ATTENTION"
    ).all()
    assertions += 1
    assert not any("score" in str(column).lower() for column in evidence.columns)
    assertions += 1

    raw = output["raw_story_allocation"]
    conserved = output["conserved_story_allocation"]
    raw_sum = raw.loc[
        raw["Date"].eq(dates[-1]) & raw["Ticker"].eq("1111"),
        "AllocationWeight",
    ].sum()
    conserved_sum = conserved.loc[
        conserved["Date"].eq(dates[-1]) & conserved["Ticker"].eq("1111"),
        "AllocationWeight",
    ].sum()
    assert raw_sum == 2.0 and np.isclose(conserved_sum, 1.0)
    assertions += 1

    missing_time = prepared.copy()
    missing_time.attrs.update(prepared.attrs)
    affected = missing_time["Date"].eq(dates[-1]) & missing_time["Ticker"].eq("1111")
    missing_time.loc[affected, "ForeignNetAmountAvailableAt"] = pd.NaT
    missing_output = def_build_stock_positioning_outputs(
        missing_time,
        calendar,
        residual_returns=residuals,
        as_of_date=dates[-1],
        config=StockPositioningConfig(windows=(60,)),
    )["stock_lane_evidence"]
    missing_category = missing_output.loc[
        missing_output["Date"].eq(dates[-1])
        & missing_output["Ticker"].eq("1111")
        & missing_output["EvidenceWindowDays"].eq(60)
        & missing_output["DirectionalLane"].eq("FOREIGN"),
        "EvidenceCategory",
    ].iloc[0]
    assert missing_category == "HOLD_DIRECTIONAL_VALUE_OR_TIME_MISSING"
    assertions += 1
    peer_time_category = missing_output.loc[
        missing_output["Date"].eq(dates[-1])
        & missing_output["Ticker"].eq("3333")
        & missing_output["EvidenceWindowDays"].eq(60)
        & missing_output["DirectionalLane"].eq("FOREIGN"),
        "EvidenceCategory",
    ].iloc[0]
    assert peer_time_category == "HOLD_PEER_EVIDENCE_TIME_INCOMPLETE"
    assertions += 1

    unknown_lock = prepared.copy()
    unknown_lock.attrs.update(prepared.attrs)
    unknown_lock.loc[affected, "LimitLockDataStatus"] = "HOLD_LIMIT_LOCK_STATUS_UNKNOWN"
    lock_output = def_build_stock_positioning_outputs(
        unknown_lock,
        calendar,
        residual_returns=residuals,
        as_of_date=dates[-1],
        config=StockPositioningConfig(windows=(60,)),
    )["stock_lane_evidence"]
    lock_category = lock_output.loc[
        lock_output["Date"].eq(dates[-1])
        & lock_output["Ticker"].eq("1111")
        & lock_output["EvidenceWindowDays"].eq(60)
        & lock_output["DirectionalLane"].eq("FOREIGN"),
        "EvidenceCategory",
    ].iloc[0]
    assert lock_category == "HOLD_LIMIT_STATUS_UNKNOWN"
    assertions += 1

    blocked = prepared.copy()
    blocked.attrs.update(prepared.attrs)
    blocked.attrs["FullMarketGateStatus"] = "BLOCKED_FULL_MARKET_GATE"
    try:
        def_build_stock_positioning_outputs(blocked, calendar)
    except ValueError:
        assertions += 1
    else:
        raise AssertionError("full-market provenance gate did not fail closed")

    future = prepared.loc[prepared["Date"].eq(dates[-1])].copy()
    future["Date"] = next_session
    future["ForeignNetAmount"] = 99_999.0
    future["ForeignDirectionalAmount"] = 99_999.0
    future_prepared = pd.concat([prepared, future], ignore_index=True, sort=False)
    future_prepared.attrs.update(prepared.attrs)
    future_residual = residuals.loc[residuals["Date"].eq(dates[-1])].copy()
    future_residual["Date"] = next_session
    future_residual["ResidualReturn"] = 99.0
    future_residuals = pd.concat([residuals, future_residual], ignore_index=True)
    future_residuals.attrs.update(residuals.attrs)
    future_output = def_build_stock_positioning_outputs(
        future_prepared,
        calendar.append(pd.DatetimeIndex([next_session + pd.offsets.BDay(1)])),
        residual_returns=future_residuals,
        as_of_date=dates[-1],
        config=StockPositioningConfig(windows=(60,)),
    )["stock_lane_evidence"]
    future_latest = future_output.loc[
        future_output["Date"].eq(dates[-1])
        & future_output["EvidenceWindowDays"].eq(60)
        & future_output["DirectionalLane"].eq("FOREIGN")
    ].set_index("Ticker")
    invariant_columns = [
        "EvidenceCategory",
        "PositioningSequencePhase",
        "DirectionalPriorMedian",
        "AttentionPriorMedian",
        "PricePriorMedian",
    ]
    pd.testing.assert_frame_equal(
        latest[invariant_columns].sort_index(),
        future_latest[invariant_columns].sort_index(),
    )
    assertions += 1

    return {
        "EngineId": ENGINE_ID,
        "EngineVersion": ENGINE_VERSION,
        "Status": "PASS",
        "Assertions": assertions,
        "StockEvidenceRows": int(len(evidence)),
        "LatestForeignCategories": latest["EvidenceCategory"].to_dict(),
        "Windows": sorted(evidence["EvidenceWindowDays"].unique().tolist()),
        "DirectionalLanes": sorted(evidence["DirectionalLane"].unique().tolist()),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(def_self_test(), ensure_ascii=False, indent=2, default=str))
