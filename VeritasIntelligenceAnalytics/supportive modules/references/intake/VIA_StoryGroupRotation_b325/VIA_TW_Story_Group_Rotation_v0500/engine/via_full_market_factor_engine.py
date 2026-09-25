from __future__ import annotations

"""Full TWSE/TPEX market gate and ex-TSMC residual-return factors.

The engine keeps lagged-market-cap and lagged-ETR factors as separate evidence
series.  It never combines them into a composite score.  Rolling alpha/beta are
estimated with observations through T-1 only.
"""

import json
import hashlib
import math
from typing import Any, Iterable

import numpy as np
import pandas as pd

if __package__:
    from .via_time_utils import def_available_at_utc, def_local_calendar_date
else:  # direct execution from the engine directory
    from via_time_utils import def_available_at_utc, def_local_calendar_date


# =============================================================================
# PARAMETERS
# =============================================================================
ENGINE_ID = "VIA_FULL_TAIWAN_MARKET_FACTOR_ENGINE"
ENGINE_VERSION = "0.5.0"
DATE_COLUMN = "Date"
TICKER_COLUMN = "Ticker"
MARKET_COLUMN = "Market"
ASSET_TYPE_COLUMN = "AssetType"
TSMC_TICKER = "2330.TW"
REQUIRED_MARKETS = ("TWSE", "TPEX")
ORDINARY_STOCK_ASSET_TYPES = (
    "COMMON_STOCK",
    "COMMON",
    "EQUITY",
    "STOCK",
    "ORDINARY_SHARE",
    "普通股",
)
REQUIRED_UNIVERSE_COLUMNS = (
    TICKER_COLUMN,
    MARKET_COLUMN,
    ASSET_TYPE_COLUMN,
    "ValidFrom",
    "ValidTo",
    "KnownAt",
)
UNIVERSE_VERSION_COLUMNS = (
    "UniverseRecordId",
    "RevisionId",
    "RecordedAt",
    "RevisionAction",
)
UNIVERSE_REVISION_ACTIONS = ("UPSERT", "RETRACT")
UNIVERSE_VERSION_POLICY = (
    "LATEST_RECORDED_REVISION_KNOWN_BY_SESSION_MARKET_DATA_CUTOFF"
)
UNIVERSE_KNOWLEDGE_CUTOFF_POLICY = (
    "UNIVERSE_EVENT_KNOWN_AT_NOT_AFTER_SESSION_MARKET_DATA_AVAILABLE_AT"
)
REQUIRED_DAILY_COLUMNS = (
    DATE_COLUMN,
    TICKER_COLUMN,
    "Adj_Close",
    "TurnoverValue",
    "DayTradeTurnover",
    "MarketCap",
    "MarketDataAvailableAt",
)
ROLLING_BETA_WINDOWS = (60, 120, 240)
ROLLING_MINIMUM_OBSERVATION_RATIO = 0.67
FACTOR_MIN_DAILY_COVERAGE = 0.98
NUMERIC_EPSILON = 1.0e-12
FACTOR_COLUMNS = {
    "LaggedCap": "MarketReturnExTSMCLaggedCap",
    "LaggedETR": "MarketReturnExTSMCLaggedETR",
}
FACTOR_WEIGHT_COLUMNS = {
    "LaggedCap": "WeightExTSMCLaggedCap",
    "LaggedETR": "WeightExTSMCLaggedETR",
}
FULL_MARKET_GATE_STATUS = "PASS_FULL_TWSE_TPEX_ORDINARY_STOCKS"
FULL_MARKET_UNIVERSE_ID = "TWSE_TPEX_COMMON_EQUITY_WITH_2330_ANCHOR"
RESIDUAL_UNIVERSE_ID = "TWSE_TPEX_COMMON_EQUITY_EX_2330"
RESIDUAL_LINEAGE_SCHEMA = "VIA_FULL_MARKET_RESIDUAL_LINEAGE_V2"
INVALID_ETR_STATUSES = (
    "BLOCKED_MISSING_NUMERIC_INPUT",
    "BLOCKED_NEGATIVE_TURNOVER",
    "BLOCKED_NEGATIVE_DAY_TRADE",
    "BLOCKED_DAY_TRADE_EXCEEDS_TURNOVER",
    "BLOCKED_NONPOSITIVE_ADJ_CLOSE",
    "BLOCKED_NONPOSITIVE_MARKET_CAP",
)


def def_residual_lineage_values(windows: Iterable[int]) -> dict[str, Any]:
    """Build auditable row-level lineage for the wide residual panel.

    The digest is an integrity checksum for accidental lineage drift, not an
    authentication signature.  Formal consumers also validate every explicit
    lineage field instead of trusting transient ``DataFrame.attrs`` alone.
    """

    resolved_windows = tuple(sorted({int(window) for window in windows}))
    values: dict[str, Any] = {
        "ResidualLineageSchema": RESIDUAL_LINEAGE_SCHEMA,
        "ResidualLineageEngineId": ENGINE_ID,
        "ResidualLineageEngineVersion": ENGINE_VERSION,
        "ResidualLineageSourceUniverse": FULL_MARKET_UNIVERSE_ID,
        "ResidualLineageMarketUniverse": RESIDUAL_UNIVERSE_ID,
        "ResidualLineageFullMarketGateStatus": FULL_MARKET_GATE_STATUS,
        "ResidualLineageRequiredMarkets": "TWSE|TPEX",
        "ResidualLineageTSMCExcluded": True,
        "ResidualLineageTSMCAnchorPresent": True,
        "ResidualLineagePointInTime": True,
        "ResidualLineageAvailabilityPolicy": (
            "MARKET_DATA_NONMISSING_SAME_LOCAL_SESSION;"
            "UNIVERSE_EVENT_KNOWN_AT_NOT_AFTER_SESSION_MARKET_DATA_AVAILABLE_AT"
        ),
        "ResidualLineageUniverseVersionPolicy": UNIVERSE_VERSION_POLICY,
        "ResidualLineageUniverseKnowledgeCutoffPolicy": (
            UNIVERSE_KNOWLEDGE_CUTOFF_POLICY
        ),
        "ResidualLineageTradingCalendarCoverage": "COMPLETE_OBSERVED_RANGE",
        "ResidualLineageRosterPolicy": "SHA256_SORTED_MARKET_TICKER_PER_DATE",
        "ResidualLineageFactorLanes": "LaggedCap|LaggedETR",
        "ResidualLineageWindows": "|".join(str(window) for window in resolved_windows),
    }
    canonical = json.dumps(values, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    values["ResidualLineageId"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest().upper()
    return values


def def_normalize_ticker(value: Any) -> str:
    ticker = str(value).strip().upper().replace(" ", "")
    if ticker.endswith(".TW.TW"):
        ticker = ticker[:-3]
    if ticker.endswith(".TWO.TWO"):
        ticker = ticker[:-4]
    return ticker


def def_parse_date_series(values: pd.Series, column_name: str, allow_missing: bool) -> pd.Series:
    blank = values.isna() | values.astype(str).str.strip().eq("")
    parsed = pd.to_datetime(values.where(~blank), errors="coerce")
    invalid = (~blank) & parsed.isna()
    if invalid.any():
        raise ValueError(f"{column_name} contains {int(invalid.sum())} invalid dates")
    if not allow_missing and parsed.isna().any():
        raise ValueError(f"{column_name} cannot be missing")
    if getattr(parsed.dt, "tz", None) is not None:
        parsed = parsed.dt.tz_localize(None)
    return parsed.dt.normalize()


def def_parse_available_at_series(
    values: pd.Series,
    column_name: str,
    *,
    allow_missing: bool,
) -> pd.Series:
    """Parse PIT timestamps without treating a blank value as UTC midnight."""

    blank = values.isna() | values.astype("string").str.strip().eq("").fillna(True)
    parsed_values: list[pd.Timestamp | pd.NaT] = []
    invalid_count = 0
    for value, is_blank in zip(values.tolist(), blank.tolist(), strict=True):
        if bool(is_blank):
            parsed_values.append(pd.NaT)
            continue
        try:
            parsed_values.append(def_available_at_utc(value))
        except (TypeError, ValueError):
            parsed_values.append(pd.NaT)
            invalid_count += 1
    parsed = pd.Series(
        pd.to_datetime(parsed_values, errors="coerce", utc=True),
        index=values.index,
    )
    if invalid_count:
        raise ValueError(f"universe_history {column_name} contains invalid timestamps")
    if not allow_missing and parsed.isna().any():
        raise ValueError(f"universe_history {column_name} cannot be missing")
    return parsed


def def_prepare_universe_history(
    universe_history: pd.DataFrame,
    *,
    as_of_at: Any | None = None,
) -> pd.DataFrame:
    """Normalize an immutable legacy roster or an append-only revision ledger.

    Versioned rows use ``UniverseRecordId`` as the stable logical interval and
    ``RevisionId`` as an immutable revision key.  A revision cannot be known
    before both its source ``KnownAt`` and ingestion ``RecordedAt`` timestamps.
    When ``as_of_at`` is supplied, rows learned later are removed before their
    payload is validated so a future append cannot alter an earlier replay.
    """

    missing = sorted(set(REQUIRED_UNIVERSE_COLUMNS).difference(universe_history.columns))
    if missing:
        raise ValueError(f"universe_history missing required columns: {missing}")
    universe = universe_history.copy().reset_index(drop=True)

    universe["KnownAt"] = def_parse_available_at_series(
        universe["KnownAt"], "KnownAt", allow_missing=False
    )
    if "RecordedAt" in universe.columns:
        universe["RecordedAt"] = def_parse_available_at_series(
            universe["RecordedAt"], "RecordedAt", allow_missing=True
        )
    else:
        universe["RecordedAt"] = pd.Series(
            pd.NaT, index=universe.index, dtype="datetime64[ns, UTC]"
        )
    universe["UniverseEventKnownAt"] = universe["KnownAt"].where(
        universe["RecordedAt"].isna()
        | universe["KnownAt"].ge(universe["RecordedAt"]),
        universe["RecordedAt"],
    )
    universe["_KnownLocalDate"] = universe["UniverseEventKnownAt"].map(
        def_local_calendar_date
    )
    if as_of_at is not None:
        try:
            cutoff = def_available_at_utc(as_of_at)
        except (TypeError, ValueError) as error:
            raise ValueError("universe_history as_of_at is invalid") from error
        if pd.isna(cutoff):
            raise ValueError("universe_history as_of_at cannot be missing")
        universe = universe.loc[
            universe["UniverseEventKnownAt"].le(cutoff)
        ].copy()

    supplied_version_columns = set(UNIVERSE_VERSION_COLUMNS).intersection(
        universe_history.columns
    )
    for column in UNIVERSE_VERSION_COLUMNS:
        if column not in universe.columns:
            universe[column] = pd.NA
    identifier_columns = ("UniverseRecordId", "RevisionId")
    for column in identifier_columns:
        universe[column] = universe[column].astype("string").str.strip()
    universe["RevisionAction"] = (
        universe["RevisionAction"].astype("string").str.strip().str.upper()
    )
    version_value_present = pd.Series(False, index=universe.index)
    for column in UNIVERSE_VERSION_COLUMNS:
        if column == "RecordedAt":
            present = universe[column].notna()
        else:
            present = universe[column].notna() & universe[column].ne("")
        version_value_present |= present
    versioned_mode = bool(version_value_present.any())
    if versioned_mode:
        missing_version_columns = sorted(
            set(UNIVERSE_VERSION_COLUMNS).difference(supplied_version_columns)
        )
        if missing_version_columns:
            raise ValueError(
                "versioned universe_history missing append-only fields: "
                f"{missing_version_columns}"
            )
        incomplete_version = (
            universe["UniverseRecordId"].isna()
            | universe["UniverseRecordId"].eq("")
            | universe["RevisionId"].isna()
            | universe["RevisionId"].eq("")
            | universe["RecordedAt"].isna()
            | universe["RevisionAction"].isna()
            | universe["RevisionAction"].eq("")
        )
        if incomplete_version.any():
            raise ValueError(
                "versioned universe_history requires complete UniverseRecordId, "
                "RevisionId, RecordedAt and RevisionAction on every known row"
            )
        invalid_actions = ~universe["RevisionAction"].isin(UNIVERSE_REVISION_ACTIONS)
        if invalid_actions.any():
            actions = sorted(universe.loc[invalid_actions, "RevisionAction"].unique())
            raise ValueError(f"unsupported universe revision actions: {actions}")
        version_mode = "VERSIONED_APPEND_ONLY"
    else:
        version_mode = "LEGACY_IMMUTABLE_SINGLE_VERSION"

    universe[TICKER_COLUMN] = universe[TICKER_COLUMN].map(def_normalize_ticker)
    universe[MARKET_COLUMN] = universe[MARKET_COLUMN].fillna("").astype(str).str.strip().str.upper()
    universe[ASSET_TYPE_COLUMN] = (
        universe[ASSET_TYPE_COLUMN].fillna("").astype(str).str.strip().str.upper()
    )
    universe["ValidFrom"] = def_parse_date_series(universe["ValidFrom"], "ValidFrom", False)
    universe["ValidTo"] = def_parse_date_series(universe["ValidTo"], "ValidTo", True)
    if "SourcePayloadHash" not in universe.columns:
        universe["SourcePayloadHash"] = pd.NA
    universe["SourcePayloadHash"] = (
        universe["SourcePayloadHash"].astype("string").str.strip().str.upper()
    )
    supplied_hash = universe["SourcePayloadHash"].notna() & universe[
        "SourcePayloadHash"
    ].ne("")
    invalid_hash = supplied_hash & ~universe["SourcePayloadHash"].str.fullmatch(
        r"[0-9A-F]{64}", na=False
    )
    if invalid_hash.any():
        raise ValueError("SourcePayloadHash must be a 64-character SHA-256 hex digest")
    invalid_market = ~universe[MARKET_COLUMN].isin(REQUIRED_MARKETS)
    if invalid_market.any():
        values = sorted(universe.loc[invalid_market, MARKET_COLUMN].unique())
        raise ValueError(f"universe_history contains unsupported markets: {values}")
    invalid_interval = universe["ValidTo"].notna() & (universe["ValidTo"] < universe["ValidFrom"])
    if invalid_interval.any():
        raise ValueError("universe_history contains ValidTo before ValidFrom")
    suffix_market_mismatch = (
        universe[MARKET_COLUMN].eq("TWSE") & ~universe[TICKER_COLUMN].str.endswith(".TW")
    ) | (
        universe[MARKET_COLUMN].eq("TPEX") & ~universe[TICKER_COLUMN].str.endswith(".TWO")
    )
    if suffix_market_mismatch.any():
        bad = universe.loc[suffix_market_mismatch, [TICKER_COLUMN, MARKET_COLUMN]].to_dict("records")
        raise ValueError(f"ticker suffix and market mismatch: {bad}")

    if versioned_mode:
        duplicate_revision = universe.duplicated(
            ["UniverseRecordId", "RevisionId"], keep=False
        )
        if duplicate_revision.any():
            raise ValueError(
                "versioned universe_history contains duplicate UniverseRecordId+RevisionId"
            )
        ambiguous_order = universe.duplicated(
            ["UniverseRecordId", "UniverseEventKnownAt"], keep=False
        )
        if ambiguous_order.any():
            raise ValueError(
                "versioned universe_history has multiple revisions for one record at the "
                "same effective knowledge timestamp"
            )
        unstable_ticker = universe.groupby("UniverseRecordId", dropna=False)[
            TICKER_COLUMN
        ].nunique(dropna=False).gt(1)
        if unstable_ticker.any():
            records = unstable_ticker.index[unstable_ticker].astype(str).tolist()
            raise ValueError(
                "UniverseRecordId must retain one stable ticker across revisions: "
                f"{records[:20]}"
            )
    else:
        universe["UniverseRecordId"] = (
            "LEGACY|"
            + universe[TICKER_COLUMN]
            + "|"
            + universe["ValidFrom"].dt.strftime("%Y-%m-%d")
        )
        universe["RevisionId"] = "LEGACY_V1"
        universe["RecordedAt"] = universe["KnownAt"]
        universe["RevisionAction"] = "UPSERT"
        duplicate_legacy_record = universe.duplicated(
            ["UniverseRecordId", "RevisionId"], keep=False
        )
        if duplicate_legacy_record.any():
            raise ValueError(
                "legacy universe_history contains duplicate Ticker+ValidFrom rows"
            )
        ordinary = universe[ASSET_TYPE_COLUMN].isin(ORDINARY_STOCK_ASSET_TYPES)
        ordered = universe.loc[ordinary].sort_values(
            [TICKER_COLUMN, "ValidFrom"]
        ).copy()
        for ticker, rows in ordered.groupby(TICKER_COLUMN, sort=False):
            previous_to: pd.Timestamp | pd.NaT = pd.NaT
            first = True
            for row in rows.itertuples(index=False):
                if not first and (pd.isna(previous_to) or row.ValidFrom <= previous_to):
                    raise ValueError(
                        f"overlapping ordinary-stock universe intervals for {ticker}; "
                        "use append-only version fields for a revision"
                    )
                previous_to = row.ValidTo
                first = False
    universe["UniverseVersionMode"] = version_mode
    return universe.sort_values(
        ["UniverseRecordId", "UniverseEventKnownAt", "RevisionId"],
        kind="stable",
    ).reset_index(drop=True)


def def_prepare_daily_market(market_daily: pd.DataFrame) -> pd.DataFrame:
    missing = sorted(set(REQUIRED_DAILY_COLUMNS).difference(market_daily.columns))
    if missing:
        raise ValueError(f"market_daily missing required columns: {missing}")
    frame = market_daily.copy().reset_index(drop=True)
    frame[DATE_COLUMN] = pd.to_datetime(frame[DATE_COLUMN], errors="coerce")
    if getattr(frame[DATE_COLUMN].dt, "tz", None) is not None:
        frame[DATE_COLUMN] = frame[DATE_COLUMN].dt.tz_localize(None)
    frame[DATE_COLUMN] = frame[DATE_COLUMN].dt.normalize()
    if frame[DATE_COLUMN].isna().any():
        raise ValueError(f"market_daily contains {int(frame[DATE_COLUMN].isna().sum())} invalid dates")
    frame[TICKER_COLUMN] = frame[TICKER_COLUMN].map(def_normalize_ticker)
    duplicates = frame.duplicated([DATE_COLUMN, TICKER_COLUMN], keep=False)
    if duplicates.any():
        raise ValueError(
            f"market_daily contains {int(duplicates.sum())} duplicate Date+Ticker rows"
        )
    for column in ["Adj_Close", "TurnoverValue", "DayTradeTurnover", "MarketCap"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    try:
        available_at = frame["MarketDataAvailableAt"].map(def_available_at_utc)
    except (TypeError, ValueError) as error:
        raise ValueError("MarketDataAvailableAt contains invalid timestamps") from error
    if available_at.isna().any():
        raise ValueError("MarketDataAvailableAt cannot be missing")
    available_local_date = available_at.map(def_local_calendar_date)
    if not available_local_date.eq(frame[DATE_COLUMN]).all():
        raise ValueError(
            "MarketDataAvailableAt must prove each market row was available on its own session"
        )
    frame["MarketDataAvailableAt"] = pd.to_datetime(
        available_at, errors="coerce", utc=True
    )
    return frame.sort_values([TICKER_COLUMN, DATE_COLUMN]).reset_index(drop=True)


def def_compute_strict_etr(
    ordinary_panel: pd.DataFrame,
    *,
    raise_on_invalid: bool = True,
) -> pd.DataFrame:
    required = set(REQUIRED_DAILY_COLUMNS) | {MARKET_COLUMN, ASSET_TYPE_COLUMN}
    missing = sorted(required.difference(ordinary_panel.columns))
    if missing:
        raise ValueError(f"ordinary_panel missing required columns: {missing}")
    frame = ordinary_panel.copy()
    for column in ["Adj_Close", "TurnoverValue", "DayTradeTurnover", "MarketCap"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["ETRStatus"] = "PASS"
    numeric_missing = frame[["Adj_Close", "TurnoverValue", "DayTradeTurnover", "MarketCap"]].isna().any(axis=1)
    frame.loc[numeric_missing, "ETRStatus"] = "BLOCKED_MISSING_NUMERIC_INPUT"
    frame.loc[
        frame["ETRStatus"].eq("PASS") & frame["TurnoverValue"].lt(0), "ETRStatus"
    ] = "BLOCKED_NEGATIVE_TURNOVER"
    frame.loc[
        frame["ETRStatus"].eq("PASS") & frame["DayTradeTurnover"].lt(0), "ETRStatus"
    ] = "BLOCKED_NEGATIVE_DAY_TRADE"
    frame.loc[
        frame["ETRStatus"].eq("PASS")
        & frame["DayTradeTurnover"].gt(frame["TurnoverValue"]),
        "ETRStatus",
    ] = "BLOCKED_DAY_TRADE_EXCEEDS_TURNOVER"
    frame.loc[
        frame["ETRStatus"].eq("PASS") & frame["Adj_Close"].le(0), "ETRStatus"
    ] = "BLOCKED_NONPOSITIVE_ADJ_CLOSE"
    frame.loc[
        frame["ETRStatus"].eq("PASS") & frame["MarketCap"].le(0), "ETRStatus"
    ] = "BLOCKED_NONPOSITIVE_MARKET_CAP"
    frame["ETR"] = np.where(
        frame["ETRStatus"].eq("PASS"),
        frame["TurnoverValue"] - frame["DayTradeTurnover"],
        np.nan,
    )
    frame["TSMCIsolation"] = np.where(
        frame[TICKER_COLUMN].eq(TSMC_TICKER),
        "ISOLATED_ANCHOR_NOT_IN_MARKET_FACTOR",
        "ELIGIBLE_EX_TSMC",
    )
    frame["FactorEligibleExTSMC"] = (
        frame["ETRStatus"].eq("PASS")
        & frame[ASSET_TYPE_COLUMN].isin(ORDINARY_STOCK_ASSET_TYPES)
        & frame[TICKER_COLUMN].ne(TSMC_TICKER)
    )
    invalid_count = int(frame["ETRStatus"].isin(INVALID_ETR_STATUSES).sum())
    if raise_on_invalid and invalid_count:
        counts = frame.loc[
            frame["ETRStatus"].isin(INVALID_ETR_STATUSES), "ETRStatus"
        ].value_counts().to_dict()
        raise ValueError(f"strict ETR gate rejected {invalid_count} rows: {counts}")
    return frame


def def_active_ordinary_universe(
    universe: pd.DataFrame,
    date: pd.Timestamp,
    *,
    knowledge_cutoff_at: Any,
) -> pd.DataFrame:
    """Materialize the one universe revision knowable at a session cutoff."""

    session_date = def_local_calendar_date(date)
    try:
        cutoff = def_available_at_utc(knowledge_cutoff_at)
    except (TypeError, ValueError) as error:
        raise ValueError("universe knowledge_cutoff_at is invalid") from error
    if pd.isna(session_date) or pd.isna(cutoff):
        raise ValueError("universe session date and knowledge cutoff are required")
    if def_local_calendar_date(cutoff) != session_date:
        raise ValueError(
            "universe knowledge cutoff must be a MarketDataAvailableAt timestamp "
            "from the same local session"
        )
    required = {
        TICKER_COLUMN,
        MARKET_COLUMN,
        ASSET_TYPE_COLUMN,
        "ValidFrom",
        "ValidTo",
        "UniverseRecordId",
        "RevisionId",
        "RevisionAction",
        "UniverseEventKnownAt",
        "UniverseVersionMode",
    }
    missing = sorted(required.difference(universe.columns))
    if missing:
        raise ValueError(f"prepared universe missing revision fields: {missing}")
    known = universe.loc[universe["UniverseEventKnownAt"].le(cutoff)].copy()
    if known.empty:
        return known
    latest = (
        known.sort_values(
            ["UniverseRecordId", "UniverseEventKnownAt", "RevisionId"],
            kind="stable",
        )
        .groupby("UniverseRecordId", sort=False, as_index=False, group_keys=False)
        .tail(1)
    )
    active = latest.loc[
        latest["RevisionAction"].eq("UPSERT")
        & latest[ASSET_TYPE_COLUMN].isin(ORDINARY_STOCK_ASSET_TYPES)
        & latest["ValidFrom"].le(session_date)
        & (latest["ValidTo"].isna() | latest["ValidTo"].ge(session_date))
    ].copy()
    duplicate_ticker = active.duplicated(TICKER_COLUMN, keep=False)
    if duplicate_ticker.any():
        records = active.loc[
            duplicate_ticker,
            [TICKER_COLUMN, "UniverseRecordId", "RevisionId"],
        ].to_dict("records")
        raise ValueError(
            "multiple active universe records overlap for one ordinary-stock ticker: "
            f"{records[:20]}"
        )
    return active.sort_values(TICKER_COLUMN, kind="stable").reset_index(drop=True)


def def_validate_trading_session_coverage(
    market_daily: pd.DataFrame,
    trading_calendar: Iterable[Any],
) -> dict[str, Any]:
    """Reject a missing whole-market session hidden between observed dates."""

    if DATE_COLUMN not in market_daily:
        raise ValueError("market_daily requires Date for trading-calendar coverage")
    raw_dates = market_daily[DATE_COLUMN]
    try:
        observed_dates = raw_dates.map(def_local_calendar_date)
    except (TypeError, ValueError) as error:
        raise ValueError("market_daily contains invalid dates") from error
    if observed_dates.isna().any() or observed_dates.empty:
        raise ValueError("market_daily has no valid dates for trading-calendar coverage")
    calendar_values = list(trading_calendar)
    if not calendar_values:
        raise ValueError("trading_calendar contains no sessions")
    try:
        parsed_calendar = pd.Series(calendar_values, dtype="object").map(
            def_local_calendar_date
        )
    except (TypeError, ValueError) as error:
        raise ValueError("trading_calendar contains invalid sessions") from error
    if parsed_calendar.isna().any():
        raise ValueError("trading_calendar contains invalid sessions")
    calendar = pd.DatetimeIndex(parsed_calendar).unique().sort_values()
    observed = pd.DatetimeIndex(observed_dates.unique()).sort_values()
    outside = observed.difference(calendar)
    if len(outside):
        raise ValueError(
            "market_daily contains dates absent from the formal trading_calendar: "
            f"{[f'{value:%Y-%m-%d}' for value in outside[:5]]}"
        )
    expected = calendar[(calendar >= observed.min()) & (calendar <= observed.max())]
    missing = expected.difference(observed)
    if len(missing):
        raise ValueError(
            "full TWSE/TPEX market input is missing entire trading sessions: "
            f"{[f'{value:%Y-%m-%d}' for value in missing[:5]]}"
        )
    return {
        "TradingCalendarCoverage": "COMPLETE_OBSERVED_RANGE",
        "ObservedFirstSession": observed.min(),
        "ObservedLastSession": observed.max(),
        "ObservedSessionCount": int(len(observed)),
        "ExpectedSessionCount": int(len(expected)),
    }


def def_validate_full_market_gate(
    market_daily: pd.DataFrame,
    universe_history: pd.DataFrame,
    *,
    fail_closed: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    daily = def_prepare_daily_market(market_daily)
    if daily.empty:
        raise ValueError("market_daily contains no observations")
    universe = def_prepare_universe_history(
        universe_history,
        as_of_at=daily["MarketDataAvailableAt"].max(),
    )
    panel_parts: list[pd.DataFrame] = []
    quality_rows: list[dict[str, Any]] = []
    for date, observed_date in daily.groupby(DATE_COLUMN, sort=True):
        session_cutoff_at = observed_date["MarketDataAvailableAt"].max()
        expected = def_active_ordinary_universe(
            universe,
            pd.Timestamp(date),
            knowledge_cutoff_at=session_cutoff_at,
        )
        expected_keys = set(expected[TICKER_COLUMN])
        observed_keys = set(observed_date[TICKER_COLUMN])
        observed_expected = observed_date.loc[
            observed_date[TICKER_COLUMN].isin(expected_keys)
        ].copy()
        missing_tickers = sorted(expected_keys.difference(observed_expected[TICKER_COLUMN]))
        unexpected_tickers = sorted(observed_keys.difference(expected_keys))
        metadata_columns = [
            TICKER_COLUMN,
            MARKET_COLUMN,
            ASSET_TYPE_COLUMN,
            "ValidFrom",
            "ValidTo",
            "KnownAt",
            "RecordedAt",
            "UniverseEventKnownAt",
            "_KnownLocalDate",
            "UniverseRecordId",
            "RevisionId",
            "RevisionAction",
            "SourcePayloadHash",
            "UniverseVersionMode",
        ]
        metadata = expected[metadata_columns]
        selected = observed_expected.merge(
            metadata,
            on=TICKER_COLUMN,
            how="left",
            validate="one_to_one",
        )
        panel_parts.append(selected)
        counts_expected = expected[MARKET_COLUMN].value_counts()
        counts_observed = selected[MARKET_COLUMN].value_counts()
        both_markets = all(int(counts_expected.get(market, 0)) > 0 for market in REQUIRED_MARKETS)
        both_complete = all(
            int(counts_observed.get(market, 0)) == int(counts_expected.get(market, 0))
            for market in REQUIRED_MARKETS
        )
        tsmc_expected = TSMC_TICKER in expected_keys
        tsmc_observed = TSMC_TICKER in set(observed_expected[TICKER_COLUMN])
        quality_rows.append(
            {
                DATE_COLUMN: pd.Timestamp(date),
                "ExpectedTWSE": int(counts_expected.get("TWSE", 0)),
                "ObservedTWSE": int(counts_observed.get("TWSE", 0)),
                "ExpectedTPEX": int(counts_expected.get("TPEX", 0)),
                "ObservedTPEX": int(counts_observed.get("TPEX", 0)),
                "MissingOrdinaryStocks": len(missing_tickers),
                "MissingTickerSample": "|".join(missing_tickers[:20]),
                "UnexpectedObservedTickers": len(unexpected_tickers),
                "UnexpectedTickerSample": "|".join(unexpected_tickers[:20]),
                "BothMarketsInUniverse": both_markets,
                "BothMarketsComplete": both_complete,
                "TSMCExpected": tsmc_expected,
                "TSMCObserved": tsmc_observed,
                "UniverseKnowledgeCutoffAt": session_cutoff_at,
            }
        )
    panel = pd.concat(panel_parts, ignore_index=True) if panel_parts else pd.DataFrame()
    panel = def_compute_strict_etr(panel, raise_on_invalid=False)
    invalid_by_date = panel.loc[~panel["ETRStatus"].eq("PASS")].groupby(DATE_COLUMN).size()
    quality = pd.DataFrame(quality_rows)
    quality["InvalidETRRows"] = quality[DATE_COLUMN].map(invalid_by_date).fillna(0).astype(int)
    quality["DateGateStatus"] = np.where(
        quality["BothMarketsInUniverse"]
        & quality["BothMarketsComplete"]
        & quality["TSMCExpected"]
        & quality["TSMCObserved"]
        & quality["MissingOrdinaryStocks"].eq(0)
        & quality["UnexpectedObservedTickers"].eq(0)
        & quality["InvalidETRRows"].eq(0),
        FULL_MARKET_GATE_STATUS,
        "BLOCKED_INCOMPLETE_OR_INVALID_FULL_MARKET",
    )
    blocked_dates = int((quality["DateGateStatus"] != FULL_MARKET_GATE_STATUS).sum())
    summary = {
        "EngineId": ENGINE_ID,
        "EngineVersion": ENGINE_VERSION,
        "GateStatus": FULL_MARKET_GATE_STATUS if blocked_dates == 0 else "BLOCKED_FULL_MARKET_GATE",
        "Dates": int(len(quality)),
        "BlockedDates": blocked_dates,
        "OrdinaryPanelRows": int(len(panel)),
        "DistinctOrdinaryTickers": int(panel[TICKER_COLUMN].nunique()),
        "TSMCRowsSeparated": int(panel[TICKER_COLUMN].eq(TSMC_TICKER).sum()),
        "InvalidETRRows": int((panel["ETRStatus"] != "PASS").sum()),
        "UnexpectedObservedTickerRows": int(
            quality["UnexpectedObservedTickers"].sum()
        ),
        "RequiredMarkets": list(REQUIRED_MARKETS),
        "UniverseVersionModes": sorted(
            universe["UniverseVersionMode"].dropna().unique().tolist()
        ),
        "UniverseVersionPolicy": UNIVERSE_VERSION_POLICY,
    }
    if fail_closed and blocked_dates:
        failed = quality.loc[quality["DateGateStatus"] != FULL_MARKET_GATE_STATUS]
        sample = failed.head(5).to_dict(orient="records")
        raise ValueError(f"full TWSE/TPEX ordinary-stock gate failed: {sample}")
    panel = panel.sort_values([TICKER_COLUMN, DATE_COLUMN]).reset_index(drop=True)
    provenance = {
        "FullMarketGateStatus": summary["GateStatus"],
        "FullMarketUniverse": FULL_MARKET_UNIVERSE_ID,
        "RequiredMarkets": REQUIRED_MARKETS,
        "TSMCAnchorPresent": bool(summary["TSMCRowsSeparated"] > 0),
        "MarketDataAvailabilityPolicy": "NONMISSING_SAME_LOCAL_SESSION",
        "UniverseKnowledgePolicy": "KNOWN_AT_NOT_AFTER_OBSERVATION_SESSION",
        "UniverseKnowledgeCutoffPolicy": (
            UNIVERSE_KNOWLEDGE_CUTOFF_POLICY
        ),
        "UniverseVersionPolicy": UNIVERSE_VERSION_POLICY,
        "PointInTime": True,
    }
    panel.attrs.update(provenance)
    quality.attrs.update(provenance)
    return panel, quality, summary


def def_weighted_return(
    returns: pd.Series,
    weights: pd.Series,
) -> tuple[float, float, int, int]:
    valid = returns.notna() & weights.notna() & weights.gt(0)
    eligible = weights.notna() & weights.ge(0)
    valid_count = int(valid.sum())
    eligible_count = int(eligible.sum())
    denominator = float(weights.loc[valid].sum()) if valid_count else np.nan
    if valid_count == 0 or not np.isfinite(denominator) or denominator <= NUMERIC_EPSILON:
        return np.nan, np.nan, valid_count, eligible_count
    result = float((returns.loc[valid] * weights.loc[valid]).sum() / denominator)
    coverage = valid_count / max(eligible_count, 1)
    return result, coverage, valid_count, eligible_count


def def_build_ex_tsmc_market_factors(
    validated_panel: pd.DataFrame,
    *,
    minimum_daily_coverage: float = FACTOR_MIN_DAILY_COVERAGE,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    required = set(REQUIRED_DAILY_COLUMNS) | {
        MARKET_COLUMN,
        ASSET_TYPE_COLUMN,
        "ETR",
        "ETRStatus",
        "FactorEligibleExTSMC",
    }
    missing = sorted(required.difference(validated_panel.columns))
    if missing:
        raise ValueError(f"validated_panel missing required columns: {missing}")
    if not 0 < minimum_daily_coverage <= 1:
        raise ValueError("minimum_daily_coverage must be in (0, 1]")
    panel = validated_panel.copy().sort_values([TICKER_COLUMN, DATE_COLUMN]).reset_index(drop=True)
    panel["Return"] = panel.groupby(TICKER_COLUMN, sort=False)["Adj_Close"].pct_change(fill_method=None)
    panel["LaggedMarketCap"] = panel.groupby(TICKER_COLUMN, sort=False)["MarketCap"].shift(1)
    panel["LaggedETR"] = panel.groupby(TICKER_COLUMN, sort=False)["ETR"].shift(1)
    panel["FactorWeightNumeratorLaggedCap"] = panel["LaggedMarketCap"].where(
        panel["FactorEligibleExTSMC"] & panel["LaggedMarketCap"].gt(0)
    )
    panel["FactorWeightNumeratorLaggedETR"] = panel["LaggedETR"].where(
        panel["FactorEligibleExTSMC"] & panel["LaggedETR"].gt(0)
    )
    cap_denominator = panel.groupby(DATE_COLUMN)["FactorWeightNumeratorLaggedCap"].transform("sum")
    etr_denominator = panel.groupby(DATE_COLUMN)["FactorWeightNumeratorLaggedETR"].transform("sum")
    panel[FACTOR_WEIGHT_COLUMNS["LaggedCap"]] = (
        panel["FactorWeightNumeratorLaggedCap"] / cap_denominator.where(cap_denominator > 0)
    )
    panel[FACTOR_WEIGHT_COLUMNS["LaggedETR"]] = (
        panel["FactorWeightNumeratorLaggedETR"] / etr_denominator.where(etr_denominator > 0)
    )

    factor_rows: list[dict[str, Any]] = []
    for date, daily in panel.groupby(DATE_COLUMN, sort=True):
        eligible = daily.loc[daily["FactorEligibleExTSMC"]]
        cap_return, cap_coverage, cap_valid, cap_eligible = def_weighted_return(
            eligible["Return"], eligible["FactorWeightNumeratorLaggedCap"]
        )
        etr_return, etr_coverage, etr_valid, etr_eligible = def_weighted_return(
            eligible["Return"], eligible["FactorWeightNumeratorLaggedETR"]
        )
        cap_pass = np.isfinite(cap_coverage) and cap_coverage >= minimum_daily_coverage
        etr_pass = np.isfinite(etr_coverage) and etr_coverage >= minimum_daily_coverage
        tsmc = daily.loc[daily[TICKER_COLUMN].eq(TSMC_TICKER)]
        factor_rows.append(
            {
                DATE_COLUMN: pd.Timestamp(date),
                FACTOR_COLUMNS["LaggedCap"]: cap_return if cap_pass else np.nan,
                FACTOR_COLUMNS["LaggedETR"]: etr_return if etr_pass else np.nan,
                "LaggedCapCoverage": cap_coverage,
                "LaggedETRCoverage": etr_coverage,
                "LaggedCapValidMembers": cap_valid,
                "LaggedCapEligibleMembers": cap_eligible,
                "LaggedETRValidMembers": etr_valid,
                "LaggedETREligibleMembers": etr_eligible,
                "LaggedCapFactorStatus": "PASS" if cap_pass else "WARMUP_OR_INSUFFICIENT_COVERAGE",
                "LaggedETRFactorStatus": "PASS" if etr_pass else "WARMUP_OR_INSUFFICIENT_COVERAGE",
                "TSMCReturnSeparated": float(tsmc["Return"].iloc[0]) if len(tsmc) == 1 else np.nan,
                "TSMCETRSeparated": float(tsmc["ETR"].iloc[0]) if len(tsmc) == 1 else np.nan,
                "TSMCMarketCapSeparated": float(tsmc["MarketCap"].iloc[0]) if len(tsmc) == 1 else np.nan,
                "MarketFactorPolicy": "TWSE_TPEX_ORDINARY_EX_2330_T_MINUS_1_WEIGHTS",
            }
        )
    factors = pd.DataFrame(factor_rows).sort_values(DATE_COLUMN).reset_index(drop=True)
    provenance = {
        **validated_panel.attrs,
        "MarketFactorUniverse": "TWSE_TPEX_COMMON_EQUITY_EX_2330",
        "ResidualizationUniverse": "TWSE_TPEX_COMMON_EQUITY_EX_2330",
        "TSMCExcludedFromMarketFactor": True,
        "PointInTime": True,
    }
    panel.attrs.update(provenance)
    factors.attrs.update(provenance)
    return panel, factors


def def_compute_pairwise_t1_parameters(
    stock_return: pd.Series,
    factor_return: pd.Series,
    window: int,
    minimum_observations: int,
) -> tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    stock_t1 = stock_return.shift(1)
    factor_t1 = factor_return.shift(1)
    valid = stock_t1.notna() & factor_t1.notna()
    x = stock_t1.where(valid)
    m = factor_t1.where(valid)
    observations = valid.rolling(window, min_periods=1).sum()
    denominator = observations.replace(0, np.nan)
    mean_x = x.rolling(window, min_periods=1).sum() / denominator
    mean_m = m.rolling(window, min_periods=1).sum() / denominator
    mean_xm = (x * m).rolling(window, min_periods=1).sum() / denominator
    mean_m2 = (m * m).rolling(window, min_periods=1).sum() / denominator
    covariance = mean_xm - mean_x * mean_m
    variance = mean_m2 - mean_m * mean_m
    sufficient = observations >= minimum_observations
    beta = (covariance / variance.where(variance.abs() > NUMERIC_EPSILON)).where(sufficient)
    alpha = (mean_x - beta * mean_m).where(sufficient)
    residual = stock_return - alpha - beta * factor_return
    return alpha, beta, residual, observations


def def_compute_t1_rolling_beta_residuals(
    stock_panel: pd.DataFrame,
    factor_daily: pd.DataFrame,
    *,
    windows: Iterable[int] = ROLLING_BETA_WINDOWS,
    minimum_observation_ratio: float = ROLLING_MINIMUM_OBSERVATION_RATIO,
) -> pd.DataFrame:
    required_provenance = (
        stock_panel.attrs.get("FullMarketGateStatus") == FULL_MARKET_GATE_STATUS
        and stock_panel.attrs.get("FullMarketUniverse") == FULL_MARKET_UNIVERSE_ID
        and stock_panel.attrs.get("TSMCAnchorPresent") is True
        and stock_panel.attrs.get("TradingCalendarCoverage")
        == "COMPLETE_OBSERVED_RANGE"
        and stock_panel.attrs.get("MarketDataAvailabilityPolicy")
        == "NONMISSING_SAME_LOCAL_SESSION"
        and stock_panel.attrs.get("UniverseKnowledgePolicy")
        == "KNOWN_AT_NOT_AFTER_OBSERVATION_SESSION"
        and stock_panel.attrs.get("UniverseKnowledgeCutoffPolicy")
        == UNIVERSE_KNOWLEDGE_CUTOFF_POLICY
        and stock_panel.attrs.get("UniverseVersionPolicy")
        == UNIVERSE_VERSION_POLICY
        and factor_daily.attrs.get("TSMCExcludedFromMarketFactor") is True
        and factor_daily.attrs.get("ResidualizationUniverse")
        == "TWSE_TPEX_COMMON_EQUITY_EX_2330"
        and factor_daily.attrs.get("UniverseKnowledgeCutoffPolicy")
        == UNIVERSE_KNOWLEDGE_CUTOFF_POLICY
        and factor_daily.attrs.get("UniverseVersionPolicy")
        == UNIVERSE_VERSION_POLICY
        and factor_daily.attrs.get("PointInTime") is True
    )
    if not required_provenance:
        raise ValueError(
            "rolling residual inputs cannot prove revision-aware full-market PIT "
            "ex-2330 provenance"
        )
    required_stock = {DATE_COLUMN, TICKER_COLUMN, "Return"}
    required_factors = {DATE_COLUMN, *FACTOR_COLUMNS.values()}
    missing_stock = sorted(required_stock.difference(stock_panel.columns))
    missing_factors = sorted(required_factors.difference(factor_daily.columns))
    if missing_stock or missing_factors:
        raise ValueError(
            f"rolling residual inputs missing columns: stock={missing_stock}; factors={missing_factors}"
        )
    if not 0 < minimum_observation_ratio <= 1:
        raise ValueError("minimum_observation_ratio must be in (0, 1]")
    resolved_windows = tuple(sorted({int(window) for window in windows}))
    if not resolved_windows or any(window < 2 for window in resolved_windows):
        raise ValueError("rolling beta windows must contain integers >= 2")
    duplicate_stock = stock_panel.duplicated([DATE_COLUMN, TICKER_COLUMN], keep=False)
    duplicate_factor = factor_daily.duplicated([DATE_COLUMN], keep=False)
    if duplicate_stock.any() or duplicate_factor.any():
        raise ValueError("rolling residual inputs contain duplicate keys")
    # 2330 remains available through the dedicated market-factor anchor
    # columns.  It must not also appear as an ordinary residual observation.
    residual_source = stock_panel.loc[
        stock_panel[TICKER_COLUMN].ne(TSMC_TICKER)
    ].copy()
    if residual_source.empty:
        raise ValueError("rolling residual universe is empty after 2330 isolation")
    result = residual_source.merge(
        factor_daily[[DATE_COLUMN, *FACTOR_COLUMNS.values()]],
        on=DATE_COLUMN,
        how="left",
        validate="many_to_one",
    ).sort_values([TICKER_COLUMN, DATE_COLUMN]).reset_index(drop=True)

    output_parts: list[pd.DataFrame] = []
    for _, history in result.groupby(TICKER_COLUMN, sort=False):
        history = history.copy().sort_values(DATE_COLUMN)
        for label, factor_column in FACTOR_COLUMNS.items():
            for window in resolved_windows:
                minimum = max(2, int(math.ceil(window * minimum_observation_ratio)))
                alpha, beta, residual, observations = def_compute_pairwise_t1_parameters(
                    history["Return"], history[factor_column], window, minimum
                )
                suffix = f"{label}_{window}D"
                history[f"Alpha_{suffix}"] = alpha
                history[f"Beta_{suffix}"] = beta
                history[f"Residual_{suffix}"] = residual
                history[f"BetaObservations_{suffix}"] = observations.astype("Int64")
                current_missing = history["Return"].isna() | history[factor_column].isna()
                insufficient = observations < minimum
                zero_variance = (~insufficient) & beta.isna() & ~current_missing
                history[f"BetaStatus_{suffix}"] = np.select(
                    [current_missing, insufficient, zero_variance],
                    [
                        "BLOCKED_CURRENT_RETURN_OR_FACTOR",
                        "BLOCKED_INSUFFICIENT_T1_HISTORY",
                        "BLOCKED_ZERO_FACTOR_VARIANCE",
                    ],
                    default="PASS",
                )
                history[f"BetaWindowPolicy_{suffix}"] = (
                    f"T_MINUS_1_ONLY;window={window};minimum={minimum}"
                )
        output_parts.append(history)
    result = pd.concat(output_parts, ignore_index=True).sort_values(
        [TICKER_COLUMN, DATE_COLUMN]
    ).reset_index(drop=True)
    result["ResidualUniverseExpectedTickerCount"] = result.groupby(
        DATE_COLUMN, sort=False
    )[TICKER_COLUMN].transform("nunique")
    result["ResidualUniverseExpectedTWSECount"] = (
        result[MARKET_COLUMN]
        .eq("TWSE")
        .groupby(result[DATE_COLUMN], sort=False)
        .transform("sum")
        .astype(int)
    )
    result["ResidualUniverseExpectedTPEXCount"] = (
        result[MARKET_COLUMN]
        .eq("TPEX")
        .groupby(result[DATE_COLUMN], sort=False)
        .transform("sum")
        .astype(int)
    )
    roster_hash_by_date = {
        pd.Timestamp(date): hashlib.sha256(
            "\n".join(
                sorted(
                    f"{market}|{ticker}"
                    for market, ticker in zip(
                        day[MARKET_COLUMN], day[TICKER_COLUMN], strict=True
                    )
                )
            ).encode("utf-8")
        )
        .hexdigest()
        .upper()
        for date, day in result.groupby(DATE_COLUMN, sort=False)
    }
    result["ResidualUniverseRosterHash"] = result[DATE_COLUMN].map(
        roster_hash_by_date
    )
    lineage = def_residual_lineage_values(resolved_windows)
    for column, value in lineage.items():
        result[column] = value
    result.attrs.update(
        {
            **factor_daily.attrs,
            **lineage,
            "MarketUniverse": RESIDUAL_UNIVERSE_ID,
            "ResidualizationUniverse": RESIDUAL_UNIVERSE_ID,
            "TSMCExcluded": True,
            "TSMCExcludedFromMarketFactor": True,
            "PointInTime": True,
        }
    )
    return result


def def_run_full_market_factor_pipeline(
    market_daily: pd.DataFrame,
    universe_history: pd.DataFrame,
    *,
    trading_calendar: Iterable[Any],
    windows: Iterable[int] = ROLLING_BETA_WINDOWS,
) -> dict[str, Any]:
    session_audit = def_validate_trading_session_coverage(
        market_daily, trading_calendar
    )
    validated, gate_daily, gate_summary = def_validate_full_market_gate(
        market_daily, universe_history, fail_closed=True
    )
    validated.attrs.update(session_audit)
    gate_daily.attrs.update(session_audit)
    gate_summary.update(session_audit)
    weighted_panel, factors = def_build_ex_tsmc_market_factors(validated)
    residuals = def_compute_t1_rolling_beta_residuals(
        weighted_panel, factors, windows=windows
    )
    return {
        "validated_panel": validated,
        "gate_daily": gate_daily,
        "gate_summary": gate_summary,
        "weighted_panel": weighted_panel,
        "market_factors": factors,
        "rolling_residuals": residuals,
    }


def def_build_self_test_fixture() -> tuple[pd.DataFrame, pd.DataFrame]:
    dates = pd.bdate_range("2024-01-02", periods=310)
    universe = pd.DataFrame(
        [
            {"Ticker": "2330.TW", "Market": "TWSE", "AssetType": "COMMON_STOCK", "ValidFrom": dates[0], "ValidTo": "", "KnownAt": f"{dates[0]:%Y-%m-%d} 08:00:00+08:00"},
            {"Ticker": "1101.TW", "Market": "TWSE", "AssetType": "COMMON_STOCK", "ValidFrom": dates[0], "ValidTo": "", "KnownAt": f"{dates[0]:%Y-%m-%d} 08:00:00+08:00"},
            {"Ticker": "6488.TWO", "Market": "TPEX", "AssetType": "COMMON_STOCK", "ValidFrom": dates[0], "ValidTo": "", "KnownAt": f"{dates[0]:%Y-%m-%d} 08:00:00+08:00"},
        ]
    )
    generator = np.random.default_rng(20260902)
    factor = generator.normal(0.0003, 0.009, len(dates))
    returns = {
        "2330.TW": 1.35 * factor + generator.normal(0, 0.003, len(dates)),
        "1101.TW": 1.10 * factor + generator.normal(0, 0.004, len(dates)),
        "6488.TWO": 0.82 * factor + generator.normal(0, 0.005, len(dates)),
    }
    rows: list[dict[str, Any]] = []
    for member_index, (ticker, values) in enumerate(returns.items(), start=1):
        close = (70 + member_index * 20) * np.cumprod(1 + values)
        turnover = 80_000_000 + member_index * 10_000_000 + np.arange(len(dates)) * 10_000
        day_trade = turnover * (0.18 + member_index * 0.02)
        cap = close * (80_000_000 + member_index * 15_000_000)
        for index, date in enumerate(dates):
            rows.append(
                {
                    "Date": date,
                    "Ticker": ticker,
                    "Adj_Close": float(close[index]),
                    "TurnoverValue": float(turnover[index]),
                    "DayTradeTurnover": float(day_trade[index]),
                    "MarketCap": float(cap[index]),
                    "MarketDataAvailableAt": f"{date:%Y-%m-%d} 14:30:00+08:00",
                }
            )
    return pd.DataFrame(rows), universe


def def_run_self_test() -> dict[str, Any]:
    daily, universe = def_build_self_test_fixture()
    dates = pd.DatetimeIndex(sorted(daily[DATE_COLUMN].unique()))
    output = def_run_full_market_factor_pipeline(
        daily,
        universe,
        trading_calendar=dates,
    )
    summary = output["gate_summary"]
    if summary["GateStatus"] != FULL_MARKET_GATE_STATUS:
        raise AssertionError("full-market gate did not pass controlled complete data")
    weighted = output["weighted_panel"]
    factors = output["market_factors"]
    latest_date = weighted[DATE_COLUMN].max()
    latest = weighted.loc[weighted[DATE_COLUMN] == latest_date]
    for column in FACTOR_WEIGHT_COLUMNS.values():
        if not np.isclose(latest[column].sum(), 1.0):
            raise AssertionError(f"factor weights do not sum to one: {column}")
    tsmc = latest.loc[latest[TICKER_COLUMN].eq(TSMC_TICKER)].iloc[0]
    if bool(tsmc["FactorEligibleExTSMC"]) or any(
        np.isfinite(tsmc[column]) for column in FACTOR_WEIGHT_COLUMNS.values()
    ):
        raise AssertionError("TSMC was not isolated from market factors")
    residuals = output["rolling_residuals"]
    latest_residuals = residuals.loc[residuals[DATE_COLUMN] == latest_date]
    expected_statuses = [
        f"BetaStatus_{label}_{window}D"
        for label in FACTOR_COLUMNS
        for window in ROLLING_BETA_WINDOWS
    ]
    if not all(latest_residuals[column].eq("PASS").all() for column in expected_statuses):
        raise AssertionError("60/120/240 T-1 beta residuals did not reach PASS")

    current_stock_mutation = output["weighted_panel"].copy()
    current_factor_mutation = factors.copy()
    current_stock_mutation.loc[
        current_stock_mutation[DATE_COLUMN] == latest_date, "Return"
    ] *= 50.0
    for factor_column in FACTOR_COLUMNS.values():
        current_factor_mutation.loc[
            current_factor_mutation[DATE_COLUMN] == latest_date, factor_column
        ] *= 50.0
    mutation_residuals = def_compute_t1_rolling_beta_residuals(
        current_stock_mutation, current_factor_mutation
    )
    mutation_latest = mutation_residuals.loc[mutation_residuals[DATE_COLUMN] == latest_date]
    beta_columns = [
        f"Beta_{label}_{window}D"
        for label in FACTOR_COLUMNS
        for window in ROLLING_BETA_WINDOWS
    ]
    baseline_beta = latest_residuals.sort_values(TICKER_COLUMN)[beta_columns].to_numpy(dtype=float)
    mutated_beta = mutation_latest.sort_values(TICKER_COLUMN)[beta_columns].to_numpy(dtype=float)
    if not np.allclose(baseline_beta, mutated_beta, equal_nan=True):
        raise AssertionError("T observations leaked into T-1 rolling beta estimates")

    mutated = output["validated_panel"].copy()
    original_factor = factors.loc[
        factors[DATE_COLUMN] == latest_date, FACTOR_COLUMNS["LaggedCap"]
    ].iloc[0]
    mutated.loc[mutated[DATE_COLUMN] == latest_date, "MarketCap"] *= 1000.0
    _, mutated_factors = def_build_ex_tsmc_market_factors(mutated)
    mutated_factor = mutated_factors.loc[
        mutated_factors[DATE_COLUMN] == latest_date, FACTOR_COLUMNS["LaggedCap"]
    ].iloc[0]
    if not np.isclose(original_factor, mutated_factor):
        raise AssertionError("T market cap changed a T-1 weighted factor")

    invalid = output["validated_panel"].head(1).copy()
    invalid["DayTradeTurnover"] = invalid["TurnoverValue"] + 1.0
    try:
        def_compute_strict_etr(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("invalid ETR row was not rejected")

    incomplete = daily.loc[
        ~((daily[DATE_COLUMN] == daily[DATE_COLUMN].min()) & daily[TICKER_COLUMN].eq("6488.TWO"))
    ]
    try:
        def_validate_full_market_gate(incomplete, universe, fail_closed=True)
    except ValueError:
        pass
    else:
        raise AssertionError("missing TPEX ordinary stock was not rejected")
    return {
        "EngineId": ENGINE_ID,
        "EngineVersion": ENGINE_VERSION,
        "SelfTestStatus": "PASS",
        "GateDates": summary["Dates"],
        "FactorRows": int(len(factors)),
        "ResidualRows": int(len(residuals)),
        "BetaWindows": list(ROLLING_BETA_WINDOWS),
    }


if __name__ == "__main__":
    print(json.dumps(def_run_self_test(), ensure_ascii=False, indent=2))
