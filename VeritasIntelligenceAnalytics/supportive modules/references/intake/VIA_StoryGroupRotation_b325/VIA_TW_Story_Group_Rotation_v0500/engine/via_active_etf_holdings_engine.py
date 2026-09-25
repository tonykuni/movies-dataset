from __future__ import annotations

"""Point-in-time Taiwan active-ETF holdings evidence engine.

The engine deliberately keeps three economically different quantities apart:

``RawDeltaShares``
    The observed change in the number of portfolio shares.
``FundScaleMechanicalQty``
    The part implied by a change in ETF units outstanding, assuming the prior
    portfolio was scaled proportionally.
``ActiveQty``
    The residual that may be attributed to the portfolio manager.  It is never
    reported when either holding shares or ETF units are unavailable.

ETF investor subscriptions/redemptions are emitted at ETF-snapshot grain by
``def_build_etf_fund_flows``.  They are not copied to every holding and must not
be added to investment-trust T86 flow, which already contains active-ETF
trading.  All analytical outputs are evidence lanes; this module has no
composite score.
"""

import argparse
import hashlib
import itertools
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd


# =============================================================================
# PARAMETERS — structural contracts only, never market cut-offs
# =============================================================================

ENGINE_ID = "VIA_ACTIVE_ETF_HOLDINGS_EVIDENCE_V0500"
ENGINE_VERSION = "0.5.0"
SOURCE_TIMEZONE = "Asia/Taipei"
TSMC_BASE = "2330"
STORY_COMPARISON_UNIVERSE = "ACTIVE_ETF_HOLDINGS_EX_2330"
TSMC_ANCHOR_POLICY = (
    "REPORTED_SEPARATELY_EXCLUDED_FROM_STORY_AND_CROSS_GROUP_COMPARISON"
)
ETF_ID_PATTERN = re.compile(r"^[0-9A-Z]+$")
UNIVERSE_EVENT_TYPES = (
    "DISCOVERED",
    "METADATA_CHANGED",
    "WENT_DORMANT",
    "REACTIVATED",
)
HOLDING_ACTIONS = (
    "INITIAL",
    "NEW_ENTRY",
    "REENTRY",
    "EXIT",
    "ACTIVE_INCREASE",
    "ACTIVE_DECREASE",
    "UNCHANGED_AFTER_UNIT_ADJUSTMENT",
    "HOLDING_CHANGE_UNATTRIBUTED",
    "WEIGHT_UP_ONLY",
    "WEIGHT_DOWN_ONLY",
    "WEIGHT_UNCHANGED_UNATTRIBUTED",
)
STORY_VIEWS = ("STORY_FULL", "CAPITAL_CONSERVED")

UNIVERSE_EVENT_COLUMNS = (
    "Sequence",
    "UniverseEventId",
    "EventType",
    "ETFId",
    "ETFName",
    "Issuer",
    "FundType",
    "AssetScope",
    "ListingStatus",
    "EligibilityStatus",
    "ObservedAt",
    "Source",
    "SourceURL",
    "SourcePayloadHash",
)

HOLDING_REQUIRED_COLUMNS = ("ETFId", "PortfolioDate", "AvailableAt", "Ticker")
HOLDING_OPTIONAL_DEFAULTS: dict[str, Any] = {
    "ETFName": "",
    "HoldingName": "",
    "Market": "",
    "Shares": np.nan,
    "WeightPct": np.nan,
    "ETFUnits": np.nan,
    "NAV": np.nan,
    "AUM": np.nan,
    "Price": np.nan,
    "Currency": "TWD",
    "IsComplete": False,
    "CompletenessReason": "UNSPECIFIED",
    "SourceType": "UNSPECIFIED",
    "SourceURL": "",
    "SourcePayloadHash": "",
    "FetchedAt": "",
    "SnapshotId": "",
}

NUMERIC_HOLDING_COLUMNS = (
    "Shares",
    "WeightPct",
    "ETFUnits",
    "NAV",
    "AUM",
    "Price",
)


@dataclass(frozen=True)
class ActiveETFAnalysisConfig:
    """Structural behavior for the evidence engine.

    There are intentionally no score weights or absolute trading thresholds.
    ``trading_calendar`` is supplied to the public build function because an
    evidence timestamp cannot safely become a trade date without a calendar.
    """

    source_timezone: str = SOURCE_TIMEZONE
    include_initial_rows: bool = True


# =============================================================================
# NORMALIZATION HELPERS
# =============================================================================


def def_normalize_etf_id(value: Any) -> str:
    """Normalize without assuming that the alphabetic character is a suffix.

    Both current styles such as ``00981A`` and ``009A01`` are valid identifiers.
    Official fund type/scope metadata, rather than the code shape, decides
    whether an instrument belongs to the Taiwan active-equity lane.
    """

    value_text = "" if value is None else str(value)
    text = value_text.strip().upper().replace(" ", "")
    if not text or ETF_ID_PATTERN.fullmatch(text) is None:
        raise ValueError(f"invalid ETFId: {value!r}")
    return text


def def_normalize_ticker(value: Any) -> str:
    value_text = "" if value is None else str(value)
    text = value_text.strip().upper().replace(" ", "")
    if text.endswith(".TW.TW"):
        text = text[:-3]
    if text.endswith(".TWO.TWO"):
        text = text[:-4]
    if not text:
        raise ValueError(f"invalid holding ticker: {value!r}")
    return text


def def_ticker_base(value: Any) -> str:
    text = def_normalize_ticker(value)
    if text.endswith(".TWO"):
        return text[:-4]
    if text.endswith(".TW"):
        return text[:-3]
    return text


def def_market_from_ticker(value: Any) -> str:
    text = def_normalize_ticker(value)
    if text.endswith(".TWO"):
        return "TPEX"
    if text.endswith(".TW"):
        return "TWSE"
    return "UNRESOLVED"


def def_parse_available_at(value: Any, source_timezone: str = SOURCE_TIMEZONE) -> pd.Timestamp:
    if value is None or str(value).strip() == "":
        return pd.NaT
    stamp = pd.Timestamp(value)
    if pd.isna(stamp):
        return pd.NaT
    if stamp.tzinfo is None:
        stamp = stamp.tz_localize(source_timezone)
    return stamp.tz_convert("UTC")


def def_parse_portfolio_date(value: Any) -> pd.Timestamp:
    if value is None or str(value).strip() == "":
        return pd.NaT
    stamp = pd.Timestamp(value)
    if pd.isna(stamp):
        return pd.NaT
    if stamp.tzinfo is not None:
        stamp = stamp.tz_convert(SOURCE_TIMEZONE).tz_localize(None)
    return stamp.normalize()


def def_local_evidence_date(value: Any) -> pd.Timestamp:
    stamp = def_parse_available_at(value)
    if pd.isna(stamp):
        return pd.NaT
    return stamp.tz_convert(SOURCE_TIMEZONE).tz_localize(None).normalize()


def def_prepare_trading_calendar(trading_calendar: Iterable[Any]) -> pd.DatetimeIndex:
    parsed = pd.to_datetime(pd.Index(list(trading_calendar)), errors="coerce")
    calendar = pd.DatetimeIndex(parsed).dropna()
    if calendar.tz is not None:
        calendar = calendar.tz_convert(SOURCE_TIMEZONE).tz_localize(None)
    calendar = calendar.normalize().unique().sort_values()
    if len(calendar) == 0:
        raise ValueError("trading_calendar contains no valid sessions")
    return calendar


def def_next_executable_session(
    available_at: Any,
    trading_calendar: Iterable[Any] | None,
) -> pd.Timestamp:
    """Return the first session strictly after the local disclosure date.

    The policy is intentionally conservative.  It prevents a post-close PCF
    from receiving a same-day return.  A source-specific release-time policy
    can be added upstream, but must never replace the exact ``AvailableAt``.
    """

    if trading_calendar is None:
        return pd.NaT
    date = def_local_evidence_date(available_at)
    calendar = def_prepare_trading_calendar(trading_calendar)
    candidates = calendar[calendar > date]
    return candidates[0] if len(candidates) else pd.NaT


def _to_bool(value: Any) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    return str(value).strip().upper() in {"TRUE", "1", "YES", "Y", "COMPLETE", "PASS"}


def _finite(value: Any) -> bool:
    try:
        return bool(np.isfinite(float(value)))
    except (TypeError, ValueError):
        return False


def _structural_sign(value: Any, *scale_values: Any) -> int | None:
    """Numerical sign with machine-precision tolerance, not a market threshold."""

    if not _finite(value):
        return None
    number = float(value)
    numeric_scales = [abs(float(item)) for item in scale_values if _finite(item)]
    tolerance = np.finfo(float).eps * max([1.0, abs(number), *numeric_scales]) * 32.0
    if abs(number) <= tolerance:
        return 0
    return 1 if number > 0 else -1


def _hash_payload(prefix: str, payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    digest = hashlib.blake2s(canonical.encode("utf-8"), digest_size=10).hexdigest().upper()
    return f"{prefix}-{digest}"


def _sum_or_nan(series: pd.Series) -> float:
    numeric = pd.to_numeric(series, errors="coerce")
    return float(numeric.sum()) if numeric.notna().any() else np.nan


def _split_tsmc_anchor(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split comparison and 2330 anchor rows without changing source evidence.

    The split is deliberately downstream of snapshot/event construction.  The
    original per-ETF holdings and holding-event tables therefore remain a full
    fund audit, while any story/group comparison is built only from the
    ex-2330 side of this boundary.
    """

    if frame.empty:
        return frame.copy(), frame.copy()
    if "TickerBase" not in frame.columns:
        raise ValueError("TSMC anchor isolation requires TickerBase")
    ticker_base = frame["TickerBase"].astype(str).str.strip().str.upper()
    is_anchor = ticker_base.eq(TSMC_BASE)
    comparison = frame.loc[~is_anchor].copy().reset_index(drop=True)
    anchor = frame.loc[is_anchor].copy().reset_index(drop=True)
    if not anchor.empty:
        anchor["AnchorPolicy"] = TSMC_ANCHOR_POLICY
    return comparison, anchor


def _conservation_with_scope(
    result: Mapping[str, Any],
    scope: str,
) -> dict[str, Any]:
    scoped = dict(result)
    scoped["Scope"] = scope
    return scoped


def _mark_story_comparison_scope(frame: pd.DataFrame) -> pd.DataFrame:
    scoped = frame.copy()
    scoped["ComparisonUniverse"] = STORY_COMPARISON_UNIVERSE
    scoped["TSMCExcluded"] = True
    return scoped


# =============================================================================
# APPEND-ONLY ETF UNIVERSE EVENTS
# =============================================================================


def def_current_universe_state(ledger: pd.DataFrame) -> dict[str, dict[str, Any]]:
    if ledger.empty:
        return {}
    required = {"Sequence", "EventType", "ETFId"}
    missing = sorted(required.difference(ledger.columns))
    if missing:
        raise ValueError(f"universe ledger missing required columns: {missing}")
    state: dict[str, dict[str, Any]] = {}
    for row in ledger.sort_values("Sequence", kind="stable").to_dict(orient="records"):
        etf_id = def_normalize_etf_id(row["ETFId"])
        event_type = str(row["EventType"]).strip().upper()
        if event_type not in UNIVERSE_EVENT_TYPES:
            raise ValueError(f"unsupported universe EventType: {event_type}")
        current = dict(state.get(etf_id, {}))
        current.update(row)
        current["ETFId"] = etf_id
        current["IsActive"] = event_type != "WENT_DORMANT"
        state[etf_id] = current
    return state


def def_materialize_universe_asof(
    ledger: pd.DataFrame,
    as_of: Any,
    *,
    verified_only: bool = False,
) -> pd.DataFrame:
    """Materialize the universe state that was observable at an exact time."""

    if ledger.empty:
        return pd.DataFrame(columns=UNIVERSE_EVENT_COLUMNS)
    cutoff = def_parse_available_at(as_of)
    if pd.isna(cutoff):
        raise ValueError("as_of is required for PIT universe materialization")
    frame = ledger.copy()
    frame["ObservedAt"] = frame["ObservedAt"].map(def_parse_available_at)
    known = frame.loc[frame["ObservedAt"].le(cutoff)].copy()
    state = def_current_universe_state(known)
    rows = [row for row in state.values() if bool(row.get("IsActive", True))]
    if verified_only:
        rows = [row for row in rows if str(row.get("EligibilityStatus", "")).upper() == "VERIFIED"]
    if not rows:
        return pd.DataFrame(columns=[*UNIVERSE_EVENT_COLUMNS, "IsActive"])
    return pd.DataFrame(rows).sort_values("ETFId").reset_index(drop=True)


def def_append_universe_events(
    ledger: pd.DataFrame,
    observations: pd.DataFrame,
    observed_at: Any,
    *,
    snapshot_complete: bool,
) -> pd.DataFrame:
    """Append discovery/state-change events while preserving every old row.

    A missing code can produce ``WENT_DORMANT`` only when the caller declares
    the universe snapshot complete.  Eligibility is carried as source evidence
    and is never inferred from whether ``A`` appears at a particular code
    position.
    """

    observed_timestamp = def_parse_available_at(observed_at)
    if pd.isna(observed_timestamp):
        raise ValueError("observed_at is required for PIT universe discovery")
    if "ETFId" not in observations.columns:
        raise ValueError("universe observations missing required column: ETFId")

    current_observations = observations.copy()
    current_observations["ETFId"] = current_observations["ETFId"].map(def_normalize_etf_id)
    if current_observations["ETFId"].duplicated().any():
        duplicates = current_observations.loc[
            current_observations["ETFId"].duplicated(keep=False), "ETFId"
        ].tolist()
        raise ValueError(f"duplicate ETFId in universe snapshot: {duplicates}")
    defaults = {
        "ETFName": "",
        "Issuer": "",
        "FundType": "UNVERIFIED",
        "AssetScope": "UNVERIFIED",
        "ListingStatus": "LISTED",
        "EligibilityStatus": "PENDING_OFFICIAL_VERIFICATION",
        "Source": "UNSPECIFIED",
        "SourceURL": "",
        "SourcePayloadHash": "",
    }
    for column, default in defaults.items():
        if column not in current_observations:
            current_observations[column] = default
        current_observations[column] = current_observations[column].fillna(default).astype(str).str.strip()

    if ledger.empty:
        existing = pd.DataFrame(columns=UNIVERSE_EVENT_COLUMNS)
    else:
        existing = ledger.copy(deep=True)
        missing = sorted(set(UNIVERSE_EVENT_COLUMNS).difference(existing.columns))
        if missing:
            raise ValueError(f"universe ledger missing columns: {missing}")
        if existing["Sequence"].tolist() != list(range(1, len(existing) + 1)):
            raise ValueError("universe Sequence must be contiguous and append-only")
        if existing["UniverseEventId"].duplicated().any():
            raise ValueError("UniverseEventId must be unique")

    previous_state = def_current_universe_state(existing)
    metadata_fields = (
        "ETFName",
        "Issuer",
        "FundType",
        "AssetScope",
        "ListingStatus",
        "EligibilityStatus",
    )
    new_rows: list[dict[str, Any]] = []
    for observation in current_observations.sort_values("ETFId").to_dict(orient="records"):
        etf_id = observation["ETFId"]
        prior = previous_state.get(etf_id)
        if prior is None:
            event_type = "DISCOVERED"
        elif not bool(prior.get("IsActive", True)):
            event_type = "REACTIVATED"
        elif any(str(prior.get(field, "")) != str(observation.get(field, "")) for field in metadata_fields):
            event_type = "METADATA_CHANGED"
        else:
            continue
        payload = {
            "EventType": event_type,
            "ETFId": etf_id,
            "ObservedAt": observed_timestamp.isoformat(),
            "SourcePayloadHash": observation.get("SourcePayloadHash", ""),
            **{field: observation.get(field, "") for field in metadata_fields},
        }
        new_rows.append(
            {
                "Sequence": len(existing) + len(new_rows) + 1,
                "UniverseEventId": _hash_payload("ETFREG", payload),
                "EventType": event_type,
                "ETFId": etf_id,
                "ObservedAt": observed_timestamp,
                **{column: observation.get(column, defaults.get(column, "")) for column in UNIVERSE_EVENT_COLUMNS if column not in {"Sequence", "UniverseEventId", "EventType", "ETFId", "ObservedAt"}},
            }
        )

    if snapshot_complete:
        observed_ids = set(current_observations["ETFId"])
        for etf_id, prior in sorted(previous_state.items()):
            if bool(prior.get("IsActive", True)) and etf_id not in observed_ids:
                payload = {
                    "EventType": "WENT_DORMANT",
                    "ETFId": etf_id,
                    "ObservedAt": observed_timestamp.isoformat(),
                    "PriorEventId": prior.get("UniverseEventId", ""),
                }
                row = {column: prior.get(column, "") for column in UNIVERSE_EVENT_COLUMNS}
                row.update(
                    {
                        "Sequence": len(existing) + len(new_rows) + 1,
                        "UniverseEventId": _hash_payload("ETFREG", payload),
                        "EventType": "WENT_DORMANT",
                        "ETFId": etf_id,
                        "ListingStatus": "DORMANT_UNOBSERVED",
                        "ObservedAt": observed_timestamp,
                    }
                )
                new_rows.append(row)

    if not new_rows:
        return existing
    additions = pd.DataFrame(new_rows, columns=UNIVERSE_EVENT_COLUMNS)
    result = (
        additions.reset_index(drop=True)
        if existing.empty
        else pd.concat([existing, additions], ignore_index=True)
    )
    if result["UniverseEventId"].duplicated().any():
        raise ValueError("universe event replay would create a duplicate event")
    if not existing.empty:
        pd.testing.assert_frame_equal(
            existing.reset_index(drop=True),
            result.iloc[: len(existing)][existing.columns].reset_index(drop=True),
            check_dtype=False,
        )
    return result


# =============================================================================
# HOLDING SNAPSHOT CONTRACT AND PIT MATERIALIZATION
# =============================================================================


def def_prepare_holdings_snapshots(
    raw: pd.DataFrame,
    config: ActiveETFAnalysisConfig = ActiveETFAnalysisConfig(),
) -> pd.DataFrame:
    """Normalize append-only snapshot vintages at holding-row grain."""

    aliases = {
        "etf_ticker": "ETFId",
        "portfolio_date": "PortfolioDate",
        "holding_ticker": "Ticker",
        "shares": "Shares",
        "weight_pct": "WeightPct",
        "available_at": "AvailableAt",
        "fetched_at": "FetchedAt",
        "SnapshotComplete": "IsComplete",
        "Weight": "WeightPct",
        "ETFUnitsOutstanding": "ETFUnits",
        "SourceHash": "SourcePayloadHash",
    }
    frame = raw.rename(columns={key: value for key, value in aliases.items() if key in raw.columns and value not in raw.columns}).copy()
    missing = sorted(set(HOLDING_REQUIRED_COLUMNS).difference(frame.columns))
    if missing:
        raise ValueError(f"holdings snapshots missing required columns: {missing}")
    for column, default in HOLDING_OPTIONAL_DEFAULTS.items():
        if column not in frame:
            frame[column] = default

    frame["ETFId"] = frame["ETFId"].map(def_normalize_etf_id)
    frame["Ticker"] = frame["Ticker"].map(def_normalize_ticker)
    frame["TickerBase"] = frame["Ticker"].map(def_ticker_base)
    frame["PortfolioDate"] = frame["PortfolioDate"].map(def_parse_portfolio_date)
    frame["AvailableAt"] = frame["AvailableAt"].map(
        lambda value: def_parse_available_at(value, config.source_timezone)
    )
    frame["FetchedAt"] = frame["FetchedAt"].map(
        lambda value: def_parse_available_at(value, config.source_timezone)
        if value is not None and str(value).strip()
        else pd.NaT
    )
    frame["EvidenceDate"] = frame["AvailableAt"].map(def_local_evidence_date)
    for column in NUMERIC_HOLDING_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["IsComplete"] = frame["IsComplete"].map(_to_bool)
    for column in ("ETFName", "HoldingName", "Currency", "CompletenessReason", "SourceType", "SourceURL", "SourcePayloadHash"):
        frame[column] = frame[column].fillna("").astype(str).str.strip()
    frame["Market"] = frame["Market"].fillna("").astype(str).str.strip().str.upper()
    unresolved_market = frame["Market"].eq("")
    frame.loc[unresolved_market, "Market"] = frame.loc[unresolved_market, "Ticker"].map(def_market_from_ticker)

    invalid_key = frame["PortfolioDate"].isna() | frame["AvailableAt"].isna()
    if invalid_key.any():
        raise ValueError(f"holdings snapshots contain {int(invalid_key.sum())} invalid PIT keys")
    for column in ("Shares", "WeightPct", "AUM", "NAV", "Price"):
        if frame[column].dropna().lt(0).any():
            raise ValueError(f"{column} cannot be negative")
    if frame["ETFUnits"].dropna().le(0).any():
        raise ValueError("ETFUnits must be positive when supplied")

    def build_snapshot_id(row: pd.Series) -> str:
        supplied = str(row["SnapshotId"]).strip()
        if supplied:
            return supplied
        return _hash_payload(
            "ETFSNAP",
            {
                "ETFId": row["ETFId"],
                "PortfolioDate": row["PortfolioDate"].strftime("%Y-%m-%d"),
                "AvailableAt": row["AvailableAt"].isoformat(),
                "SourceType": row["SourceType"],
                "SourcePayloadHash": row["SourcePayloadHash"],
            },
        )

    frame["SnapshotId"] = frame.apply(build_snapshot_id, axis=1)
    duplicate = frame.duplicated(["SnapshotId", "TickerBase"], keep=False)
    if duplicate.any():
        sample = frame.loc[duplicate, ["SnapshotId", "Ticker"]].to_dict(orient="records")
        raise ValueError(f"duplicate holding identity within snapshot: {sample}")

    invariant_columns = (
        "ETFId",
        "PortfolioDate",
        "AvailableAt",
        "ETFUnits",
        "NAV",
        "AUM",
        "IsComplete",
        "SourceType",
        "SourcePayloadHash",
    )
    for snapshot_id, snapshot in frame.groupby("SnapshotId", sort=False):
        for column in invariant_columns:
            values = snapshot[column].dropna().astype(str).unique()
            if len(values) > 1:
                raise ValueError(f"snapshot {snapshot_id} has inconsistent {column}")
    return frame.sort_values(["ETFId", "PortfolioDate", "AvailableAt", "TickerBase"]).reset_index(drop=True)


def _ensure_prepared_holdings(frame: pd.DataFrame) -> pd.DataFrame:
    required_prepared = {"TickerBase", "SnapshotId", "EvidenceDate"}
    return frame.copy() if required_prepared.issubset(frame.columns) else def_prepare_holdings_snapshots(frame)


def def_materialize_holdings_asof(
    prepared: pd.DataFrame,
    as_of: Any,
    *,
    latest_only: bool = True,
    complete_only: bool = False,
) -> pd.DataFrame:
    """Select each snapshot vintage using only information known by ``as_of``."""

    frame = _ensure_prepared_holdings(prepared)
    cutoff = def_parse_available_at(as_of)
    if pd.isna(cutoff):
        raise ValueError("as_of must be an exact point-in-time timestamp")
    known = frame.loc[frame["AvailableAt"].le(cutoff)].copy()
    if known.empty:
        return known
    snapshot_meta = known[["ETFId", "PortfolioDate", "AvailableAt", "SnapshotId", "IsComplete"]].drop_duplicates()
    selected = (
        snapshot_meta.sort_values(["ETFId", "PortfolioDate", "AvailableAt", "SnapshotId"])
        .drop_duplicates(["ETFId", "PortfolioDate"], keep="last")
    )
    if complete_only:
        selected = selected.loc[selected["IsComplete"]]
    if latest_only and not selected.empty:
        selected = (
            selected.sort_values(["ETFId", "PortfolioDate", "AvailableAt"])
            .drop_duplicates("ETFId", keep="last")
        )
    result = known.loc[known["SnapshotId"].isin(selected["SnapshotId"])].copy()
    return result.sort_values(["ETFId", "PortfolioDate", "TickerBase"]).reset_index(drop=True)


def def_build_snapshot_quality(prepared: pd.DataFrame, as_of: Any) -> pd.DataFrame:
    """Expose source completeness and expanding baselines without hard gates."""

    history = def_materialize_holdings_asof(prepared, as_of, latest_only=False, complete_only=False)
    if history.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for snapshot_id, snapshot in history.groupby("SnapshotId", sort=False):
        rows.append(
            {
                "SnapshotId": snapshot_id,
                "ETFId": snapshot["ETFId"].iloc[0],
                "PortfolioDate": snapshot["PortfolioDate"].iloc[0],
                "AvailableAt": snapshot["AvailableAt"].iloc[0],
                "IsComplete": bool(snapshot["IsComplete"].iloc[0]),
                "CompletenessReason": snapshot["CompletenessReason"].iloc[0],
                "HoldingCount": int(snapshot["TickerBase"].nunique()),
                "WeightSumPct": _sum_or_nan(snapshot["WeightPct"]),
                "SharesCoverage": float(snapshot["Shares"].notna().mean()),
                "ETFUnitsAvailable": bool(snapshot["ETFUnits"].notna().all()),
                "AUMAvailable": bool(snapshot["AUM"].notna().all()),
                "MarketIdentityResolved": bool(snapshot["Market"].ne("UNRESOLVED").all()),
                "SourceType": snapshot["SourceType"].iloc[0],
                "SourcePayloadHash": snapshot["SourcePayloadHash"].iloc[0],
            }
        )
    quality = pd.DataFrame(rows).sort_values(["ETFId", "PortfolioDate", "AvailableAt"]).reset_index(drop=True)
    for column in ("HoldingCount", "WeightSumPct"):
        quality[f"Prior{column}Median"] = quality.groupby("ETFId", sort=False)[column].transform(
            lambda series: series.shift(1).expanding().median()
        )
        quality[f"Prior{column}MAD"] = quality.groupby("ETFId", sort=False)[column].transform(
            lambda series: series.shift(1).expanding().apply(
                lambda values: float(np.median(np.abs(values - np.median(values)))), raw=True
            )
        )
    quality["SnapshotUseStatus"] = np.where(
        quality["IsComplete"], "ELIGIBLE_FOR_EVENT_COMPARISON", "BLOCKED_SOURCE_INCOMPLETE"
    )
    quality["ThresholdPolicy"] = "RAW_AND_EXPANDING_BASELINES_NO_FIXED_MARKET_THRESHOLD"
    return quality


# =============================================================================
# HOLDING EVENTS AND ETF-LEVEL FUND FLOW
# =============================================================================


def _row_value(row: pd.Series | None, column: str, default: Any = np.nan) -> Any:
    return default if row is None or column not in row else row[column]


def _holding_event_id(record: Mapping[str, Any]) -> str:
    return _hash_payload(
        "ETFACT",
        {
            "ETFId": record["ETFId"],
            "Ticker": record["Ticker"],
            "CurrentSnapshotId": record["CurrentSnapshotId"],
            "PreviousSnapshotId": record["PreviousSnapshotId"],
            "Action": record["Action"],
        },
    )


def def_build_holding_events(
    prepared: pd.DataFrame,
    as_of: Any,
    *,
    trading_calendar: Iterable[Any] | None = None,
    include_initial_rows: bool = True,
) -> pd.DataFrame:
    """Derive presence and unit-normalized manager events from complete snapshots.

    Incomplete vintages never advance state, so an omitted row cannot emit a
    false exit and cannot turn the following observation into a false re-entry.
    Presence is determined by row existence, never by whether ``Shares`` is
    null.
    """

    history = def_materialize_holdings_asof(prepared, as_of, latest_only=False, complete_only=False)
    if history.empty:
        return pd.DataFrame()
    events: list[dict[str, Any]] = []
    for etf_id, etf_history in history.groupby("ETFId", sort=True):
        snapshot_order = (
            etf_history[["PortfolioDate", "AvailableAt", "SnapshotId", "IsComplete"]]
            .drop_duplicates()
            .sort_values(["PortfolioDate", "AvailableAt", "SnapshotId"])
        )
        previous: pd.DataFrame | None = None
        previous_snapshot_id = ""
        previous_date = pd.NaT
        ever_seen: set[str] = set()
        for meta in snapshot_order.itertuples(index=False):
            current = etf_history.loc[etf_history["SnapshotId"].eq(meta.SnapshotId)].copy()
            if not bool(meta.IsComplete):
                continue
            current_by = {row.TickerBase: pd.Series(row._asdict()) for row in current.itertuples(index=False)}
            previous_by = (
                {row.TickerBase: pd.Series(row._asdict()) for row in previous.itertuples(index=False)}
                if previous is not None
                else {}
            )
            tickers = sorted(set(current_by) | set(previous_by))
            if previous is None and not include_initial_rows:
                ever_seen.update(current_by)
                previous = current
                previous_snapshot_id = meta.SnapshotId
                previous_date = meta.PortfolioDate
                continue
            current_units = current["ETFUnits"].iloc[0]
            previous_units = previous["ETFUnits"].iloc[0] if previous is not None else np.nan
            unit_ratio = (
                float(current_units) / float(previous_units)
                if _finite(current_units) and _finite(previous_units) and float(previous_units) > 0
                else np.nan
            )
            current_available_at = current["AvailableAt"].iloc[0]
            previous_available_at = (
                previous["AvailableAt"].iloc[0] if previous is not None else pd.NaT
            )
            # A change comparison is knowable only after both vintages are
            # available.  This matters when an older portfolio date receives a
            # late correction after the newer snapshot was already published.
            available_at = (
                max(current_available_at, previous_available_at)
                if previous is not None and not pd.isna(previous_available_at)
                else current_available_at
            )
            for ticker_base in tickers:
                prior_row = previous_by.get(ticker_base)
                current_row = current_by.get(ticker_base)
                present_previous = prior_row is not None
                present_current = current_row is not None
                ticker = str(_row_value(current_row, "Ticker", _row_value(prior_row, "Ticker", ticker_base)))
                shares_previous = _row_value(prior_row, "Shares") if present_previous else 0.0
                shares_current = _row_value(current_row, "Shares") if present_current else 0.0
                weight_previous = _row_value(prior_row, "WeightPct") if present_previous else 0.0
                weight_current = _row_value(current_row, "WeightPct") if present_current else 0.0
                raw_delta = (
                    float(shares_current) - float(shares_previous)
                    if _finite(shares_current) and _finite(shares_previous)
                    else np.nan
                )
                if previous is None:
                    raw_delta = np.nan
                    mechanical_qty = np.nan
                    active_qty = np.nan
                    attribution_status = "NOT_APPLICABLE_INITIAL_SNAPSHOT"
                    action = "INITIAL"
                    manager_direction = "NOT_APPLICABLE_INITIAL_SNAPSHOT"
                else:
                    shares_known = _finite(shares_current) and _finite(shares_previous)
                    units_known = _finite(unit_ratio)
                    if shares_known and units_known:
                        mechanical_qty = float(shares_previous) * (float(unit_ratio) - 1.0)
                        active_qty = float(shares_current) - float(shares_previous) * float(unit_ratio)
                        attribution_status = "UNIT_NORMALIZED_MANAGER_RESIDUAL"
                        active_sign = _structural_sign(
                            active_qty,
                            shares_current,
                            float(shares_previous) * float(unit_ratio),
                        )
                        if active_sign == 0:
                            active_qty = 0.0
                        manager_direction = (
                            "ACTIVE_BUY"
                            if active_sign == 1
                            else "ACTIVE_SELL"
                            if active_sign == -1
                            else "FLAT"
                        )
                    else:
                        mechanical_qty = np.nan
                        active_qty = np.nan
                        active_sign = None
                        if not shares_known:
                            attribution_status = "UNRESOLVED_MISSING_HOLDING_SHARES"
                            manager_direction = "NOT_INFERRED_MISSING_HOLDING_SHARES"
                        else:
                            attribution_status = "UNRESOLVED_MISSING_ETF_UNITS"
                            manager_direction = "NOT_INFERRED_MISSING_ETF_UNITS"

                    # Presence events take precedence over numeric availability.
                    # This prevents a null Shares field from becoming the proxy
                    # for entry/exit, while quantities remain fail-closed.
                    if not present_previous:
                        action = "REENTRY" if ticker_base in ever_seen else "NEW_ENTRY"
                    elif not present_current:
                        action = "EXIT"
                    elif not shares_known:
                        weight_delta_for_action = (
                            float(weight_current) - float(weight_previous)
                            if _finite(weight_current) and _finite(weight_previous)
                            else np.nan
                        )
                        weight_sign = _structural_sign(
                            weight_delta_for_action,
                            weight_current,
                            weight_previous,
                        )
                        action = (
                            "WEIGHT_UP_ONLY"
                            if weight_sign == 1
                            else "WEIGHT_DOWN_ONLY"
                            if weight_sign == -1
                            else "WEIGHT_UNCHANGED_UNATTRIBUTED"
                        )
                    elif not units_known:
                        action = "HOLDING_CHANGE_UNATTRIBUTED"
                    elif active_sign == 1:
                        action = "ACTIVE_INCREASE"
                    elif active_sign == -1:
                        action = "ACTIVE_DECREASE"
                    else:
                        action = "UNCHANGED_AFTER_UNIT_ADJUSTMENT"

                weight_delta = (
                    float(weight_current) - float(weight_previous)
                    if _finite(weight_current) and _finite(weight_previous)
                    else np.nan
                )
                if previous is None:
                    weight_delta = np.nan
                price = _row_value(current_row, "Price") if present_current else _row_value(prior_row, "Price")
                price_status = (
                    "CURRENT_SNAPSHOT_PRICE"
                    if present_current and _finite(price)
                    else "STALE_PREVIOUS_SNAPSHOT_PRICE"
                    if not present_current and _finite(price)
                    else "MISSING_PRICE"
                )
                estimated_active_value = float(active_qty) * float(price) if _finite(active_qty) and _finite(price) else np.nan
                raw_value = float(raw_delta) * float(price) if _finite(raw_delta) and _finite(price) else np.nan
                mechanical_value = (
                    float(mechanical_qty) * float(price)
                    if _finite(mechanical_qty) and _finite(price)
                    else np.nan
                )
                record: dict[str, Any] = {
                    "EventId": "",
                    "ETFId": etf_id,
                    "ETFName": _row_value(current_row, "ETFName", _row_value(prior_row, "ETFName", "")),
                    "Ticker": ticker,
                    "TickerBase": ticker_base,
                    "HoldingName": _row_value(current_row, "HoldingName", _row_value(prior_row, "HoldingName", "")),
                    "Market": _row_value(current_row, "Market", _row_value(prior_row, "Market", "UNRESOLVED")),
                    "CurrentSnapshotId": meta.SnapshotId,
                    "PreviousSnapshotId": previous_snapshot_id,
                    "PortfolioDate": meta.PortfolioDate,
                    "PreviousPortfolioDate": previous_date,
                    "AvailableAt": available_at,
                    "EvidenceDate": def_local_evidence_date(available_at),
                    "EffectiveDate": def_next_executable_session(available_at, trading_calendar),
                    "Action": action,
                    "PresentPrevious": present_previous,
                    "PresentCurrent": present_current,
                    "SharesPrevious": shares_previous,
                    "SharesCurrent": shares_current,
                    "RawDeltaShares": raw_delta,
                    "ETFUnitsPrevious": previous_units,
                    "ETFUnitsCurrent": current_units,
                    "ETFUnitRatio": unit_ratio,
                    "FundScaleMechanicalQty": mechanical_qty,
                    "ActiveQty": active_qty,
                    "ManagerDirection": manager_direction,
                    "AttributionStatus": attribution_status,
                    "WeightPctPrevious": weight_previous,
                    "WeightPctCurrent": weight_current,
                    "WeightPctDelta": weight_delta,
                    "ValuationPrice": price,
                    "ValuationPriceStatus": price_status,
                    "RawDeltaValue": raw_value,
                    "FundScaleMechanicalValue": mechanical_value,
                    "EstimatedActiveValue": estimated_active_value,
                    "SnapshotComplete": True,
                    "SourceType": current["SourceType"].iloc[0],
                    "SourceURL": current["SourceURL"].iloc[0],
                    "SourcePayloadHash": current["SourcePayloadHash"].iloc[0],
                }
                record["EventId"] = _holding_event_id(record)
                events.append(record)
            ever_seen.update(current_by)
            previous = current
            previous_snapshot_id = meta.SnapshotId
            previous_date = meta.PortfolioDate
    result = pd.DataFrame(events)
    if result.empty:
        return result
    if result["EventId"].duplicated().any():
        raise ValueError("derived holding EventId must be unique")
    invalid_action = sorted(set(result["Action"]).difference(HOLDING_ACTIONS))
    if invalid_action:
        raise AssertionError(f"engine emitted unsupported holding actions: {invalid_action}")
    return result.sort_values(["AvailableAt", "ETFId", "TickerBase"]).reset_index(drop=True)


def def_append_holding_event_ledger(existing: pd.DataFrame, derived: pd.DataFrame) -> pd.DataFrame:
    """Append new event vintages without deleting or rewriting prior evidence."""

    if derived.empty:
        return existing.copy(deep=True)
    if "EventId" not in derived:
        raise ValueError("derived events missing EventId")
    if existing.empty:
        result = derived.copy().reset_index(drop=True)
        result.insert(0, "Sequence", range(1, len(result) + 1))
        return result
    if "EventId" not in existing or "Sequence" not in existing:
        raise ValueError("existing event ledger requires Sequence and EventId")
    frozen = existing.copy(deep=True)
    additions = derived.loc[~derived["EventId"].isin(set(existing["EventId"]))].copy()
    if additions.empty:
        return frozen
    additions.insert(0, "Sequence", range(len(existing) + 1, len(existing) + len(additions) + 1))
    result = pd.concat([frozen, additions], ignore_index=True, sort=False)
    pd.testing.assert_frame_equal(
        frozen.reset_index(drop=True),
        result.iloc[: len(frozen)][frozen.columns].reset_index(drop=True),
        check_dtype=False,
    )
    return result


def def_build_etf_fund_flows(
    prepared: pd.DataFrame,
    as_of: Any,
    *,
    trading_calendar: Iterable[Any] | None = None,
) -> pd.DataFrame:
    """ETF investor subscription/redemption evidence at ETF-snapshot grain."""

    history = def_materialize_holdings_asof(prepared, as_of, latest_only=False, complete_only=True)
    if history.empty:
        return pd.DataFrame()
    meta_columns = [
        "ETFId",
        "ETFName",
        "PortfolioDate",
        "AvailableAt",
        "EvidenceDate",
        "SnapshotId",
        "ETFUnits",
        "NAV",
        "AUM",
        "SourceType",
        "SourcePayloadHash",
    ]
    meta = history[meta_columns].drop_duplicates("SnapshotId").sort_values(["ETFId", "PortfolioDate", "AvailableAt"])
    rows: list[dict[str, Any]] = []
    for etf_id, group in meta.groupby("ETFId", sort=True):
        previous: pd.Series | None = None
        for current in (pd.Series(row._asdict()) for row in group.itertuples(index=False)):
            units_previous = _row_value(previous, "ETFUnits")
            units_current = current["ETFUnits"]
            delta_units = (
                float(units_current) - float(units_previous)
                if previous is not None and _finite(units_current) and _finite(units_previous)
                else np.nan
            )
            nav = current["NAV"]
            amount = float(delta_units) * float(nav) if _finite(delta_units) and _finite(nav) else np.nan
            status = (
                "INITIAL_NO_FLOW_INFERENCE"
                if previous is None
                else "ETF_INVESTOR_FLOW_ESTIMATE"
                if _finite(amount)
                else "UNRESOLVED_MISSING_UNITS_OR_NAV"
            )
            current_available_at = current["AvailableAt"]
            previous_available_at = _row_value(previous, "AvailableAt", pd.NaT)
            comparison_available_at = (
                max(current_available_at, previous_available_at)
                if previous is not None and not pd.isna(previous_available_at)
                else current_available_at
            )
            rows.append(
                {
                    "ETFId": etf_id,
                    "ETFName": current["ETFName"],
                    "PortfolioDate": current["PortfolioDate"],
                    "PreviousPortfolioDate": _row_value(previous, "PortfolioDate", pd.NaT),
                    "AvailableAt": comparison_available_at,
                    "EvidenceDate": def_local_evidence_date(comparison_available_at),
                    "EffectiveDate": def_next_executable_session(comparison_available_at, trading_calendar),
                    "SnapshotId": current["SnapshotId"],
                    "PreviousSnapshotId": _row_value(previous, "SnapshotId", ""),
                    "ETFUnitsPrevious": units_previous,
                    "ETFUnitsCurrent": units_current,
                    "DeltaETFUnits": delta_units,
                    "NAV": nav,
                    "FundSubscriptionRedemptionAmount": amount,
                    "FundFlowDirection": (
                        "SUBSCRIPTION" if _structural_sign(amount) == 1 else "REDEMPTION" if _structural_sign(amount) == -1 else "FLAT" if _structural_sign(amount) == 0 else "NOT_INFERRED"
                    ),
                    "FundFlowStatus": status,
                    "FlowGrain": "ETF_SNAPSHOT_DO_NOT_COPY_TO_HOLDINGS",
                    "T86CombinationPolicy": "REPORT_SEPARATELY_DO_NOT_ADD",
                    "SourceType": current["SourceType"],
                    "SourcePayloadHash": current["SourcePayloadHash"],
                }
            )
            previous = current
    return pd.DataFrame(rows).sort_values(["AvailableAt", "ETFId"]).reset_index(drop=True)


# =============================================================================
# INDIVIDUAL ETF AND CROSS-ETF CONSENSUS
# =============================================================================


def def_aggregate_security_consensus(events: pd.DataFrame) -> pd.DataFrame:
    """Aggregate one daily observation per ETF/security into explicit breadth lanes."""

    if events.empty:
        return pd.DataFrame()
    required = {"ETFId", "TickerBase", "EvidenceDate", "AvailableAt", "Action", "ManagerDirection"}
    missing = sorted(required.difference(events.columns))
    if missing:
        raise ValueError(f"holding events missing consensus columns: {missing}")
    latest = (
        events.sort_values("AvailableAt")
        .drop_duplicates(["EvidenceDate", "ETFId", "TickerBase"], keep="last")
        .copy()
    )
    latest["HasAddEvidence"] = latest["ManagerDirection"].eq("ACTIVE_BUY") | latest["Action"].isin(["NEW_ENTRY", "REENTRY"])
    latest["HasReduceEvidence"] = latest["ManagerDirection"].eq("ACTIVE_SELL") | latest["Action"].eq("EXIT")
    latest["HasAttributableManagerQty"] = latest["ActiveQty"].notna()
    rows: list[dict[str, Any]] = []
    for (date, ticker), group in latest.groupby(["EvidenceDate", "TickerBase"], sort=True):
        etf_count = int(group["ETFId"].nunique())
        add_count = int(group.loc[group["HasAddEvidence"], "ETFId"].nunique())
        reduce_count = int(group.loc[group["HasReduceEvidence"], "ETFId"].nunique())
        attributable_count = int(group.loc[group["HasAttributableManagerQty"], "ETFId"].nunique())
        rows.append(
            {
                "EvidenceDate": date,
                "Ticker": group["Ticker"].iloc[-1],
                "TickerBase": ticker,
                "ETFObservedCount": etf_count,
                "AttributableManagerETFCount": attributable_count,
                "AttributionCoverage": attributable_count / etf_count if etf_count else np.nan,
                "ActiveBuyETFCount": int(group.loc[group["ManagerDirection"].eq("ACTIVE_BUY"), "ETFId"].nunique()),
                "ActiveSellETFCount": int(group.loc[group["ManagerDirection"].eq("ACTIVE_SELL"), "ETFId"].nunique()),
                "NewEntryETFCount": int(group.loc[group["Action"].eq("NEW_ENTRY"), "ETFId"].nunique()),
                "ReentryETFCount": int(group.loc[group["Action"].eq("REENTRY"), "ETFId"].nunique()),
                "ExitETFCount": int(group.loc[group["Action"].eq("EXIT"), "ETFId"].nunique()),
                "AddEvidenceETFCount": add_count,
                "ReduceEvidenceETFCount": reduce_count,
                "AddConsensusBreadth": add_count / etf_count if etf_count else np.nan,
                "ReduceConsensusBreadth": reduce_count / etf_count if etf_count else np.nan,
                "NetConsensusBreadth": (add_count - reduce_count) / etf_count if etf_count else np.nan,
                "RawDeltaSharesSum": _sum_or_nan(group["RawDeltaShares"]),
                "FundScaleMechanicalQtySum": _sum_or_nan(group["FundScaleMechanicalQty"]),
                "ActiveQtySum": _sum_or_nan(group["ActiveQty"]),
                "EstimatedActiveValueSum": _sum_or_nan(group["EstimatedActiveValue"]),
                "ETFIds": "|".join(sorted(group["ETFId"].unique())),
            }
        )
    return pd.DataFrame(rows).sort_values(["EvidenceDate", "TickerBase"]).reset_index(drop=True)


# =============================================================================
# OVERLAP AND CROWDING
# =============================================================================


def def_compute_etf_overlap(latest_holdings: pd.DataFrame) -> pd.DataFrame:
    if latest_holdings.empty:
        return pd.DataFrame()
    complete = latest_holdings.loc[latest_holdings["IsComplete"]].copy()
    etf_ids = sorted(complete["ETFId"].unique())
    rows: list[dict[str, Any]] = []
    for left_id, right_id in itertools.combinations(etf_ids, 2):
        left = complete.loc[complete["ETFId"].eq(left_id)].drop_duplicates("TickerBase")
        right = complete.loc[complete["ETFId"].eq(right_id)].drop_duplicates("TickerBase")
        left_set = set(left["TickerBase"])
        right_set = set(right["TickerBase"])
        union = left_set | right_set
        intersection = left_set & right_set
        presence_jaccard = len(intersection) / len(union) if union else np.nan

        left_weight = left.set_index("TickerBase")["WeightPct"].dropna()
        right_weight = right.set_index("TickerBase")["WeightPct"].dropna()
        if len(left_weight) and len(right_weight) and left_weight.sum() > 0 and right_weight.sum() > 0:
            left_norm = left_weight / left_weight.sum()
            right_norm = right_weight / right_weight.sum()
            all_tickers = left_norm.index.union(right_norm.index)
            left_aligned = left_norm.reindex(all_tickers, fill_value=0.0)
            right_aligned = right_norm.reindex(all_tickers, fill_value=0.0)
            denominator = np.maximum(left_aligned, right_aligned).sum()
            weighted_jaccard = float(np.minimum(left_aligned, right_aligned).sum() / denominator) if denominator > 0 else np.nan
            weight_status = "NORMALIZED_WEIGHT_OVERLAP"
        else:
            weighted_jaccard = np.nan
            weight_status = "UNRESOLVED_MISSING_PORTFOLIO_WEIGHTS"
        rows.append(
            {
                "ETFIdLeft": left_id,
                "ETFIdRight": right_id,
                "PortfolioDateLeft": left["PortfolioDate"].iloc[0],
                "PortfolioDateRight": right["PortfolioDate"].iloc[0],
                "HoldingCountLeft": len(left_set),
                "HoldingCountRight": len(right_set),
                "CommonHoldingCount": len(intersection),
                "PresenceJaccard": presence_jaccard,
                "WeightedJaccard": weighted_jaccard,
                "WeightedOverlapStatus": weight_status,
            }
        )
    return pd.DataFrame(rows)


def def_compute_holding_crowding(latest_holdings: pd.DataFrame) -> pd.DataFrame:
    if latest_holdings.empty:
        return pd.DataFrame()
    complete = latest_holdings.loc[latest_holdings["IsComplete"]].copy()
    etf_count = int(complete["ETFId"].nunique())
    complete["EstimatedPositionValue"] = np.where(
        complete["AUM"].notna() & complete["WeightPct"].notna(),
        complete["AUM"] * complete["WeightPct"] / 100.0,
        np.nan,
    )
    rows: list[dict[str, Any]] = []
    for ticker, group in complete.groupby("TickerBase", sort=True):
        holders = int(group["ETFId"].nunique())
        position_values = group.groupby("ETFId")["EstimatedPositionValue"].sum(min_count=1).dropna()
        weights = group.groupby("ETFId")["WeightPct"].sum(min_count=1).dropna()
        if len(position_values) and position_values.sum() > 0:
            shares = position_values / position_values.sum()
            hhi = float(np.square(shares).sum())
            basis = "ESTIMATED_AUM_POSITION_VALUE"
        elif len(weights) and weights.sum() > 0:
            shares = weights / weights.sum()
            hhi = float(np.square(shares).sum())
            basis = "PORTFOLIO_WEIGHT_FALLBACK"
        else:
            hhi = np.nan
            basis = "UNRESOLVED_MISSING_AUM_AND_WEIGHT"
        rows.append(
            {
                "Ticker": group["Ticker"].iloc[-1],
                "TickerBase": ticker,
                "ETFUniverseCount": etf_count,
                "ETFHolderCount": holders,
                "ETFHolderBreadth": holders / etf_count if etf_count else np.nan,
                "SumPortfolioWeightPct": _sum_or_nan(group["WeightPct"]),
                "MedianPortfolioWeightPct": float(group["WeightPct"].median()) if group["WeightPct"].notna().any() else np.nan,
                "EstimatedAUMExposure": _sum_or_nan(group["EstimatedPositionValue"]),
                "HolderConcentrationHHI": hhi,
                "ConcentrationBasis": basis,
                "ETFIds": "|".join(sorted(group["ETFId"].unique())),
            }
        )
    return pd.DataFrame(rows).sort_values("TickerBase").reset_index(drop=True)


# =============================================================================
# MULTI-LABEL STORY GROUPS: FULL VIEW AND CAPITAL-CONSERVED VIEW
# =============================================================================


def def_prepare_story_membership(membership: pd.DataFrame) -> pd.DataFrame:
    if "EventType" in membership.columns:
        raise ValueError(
            "raw membership events cannot enter ETF story mapping; materialize PIT history first"
        )
    required = {"GroupId", "Ticker"}
    missing = sorted(required.difference(membership.columns))
    if missing:
        raise ValueError(f"story membership missing required columns: {missing}")
    frame = membership.copy()
    frame["Ticker"] = frame["Ticker"].map(def_normalize_ticker)
    frame["TickerBase"] = frame["Ticker"].map(def_ticker_base)
    if "GroupName" not in frame:
        frame["GroupName"] = frame["GroupId"]
    if "MembershipValidFrom" in frame and "ValidFrom" not in frame:
        frame["ValidFrom"] = frame["MembershipValidFrom"]
    if "MembershipValidTo" in frame and "ValidTo" not in frame:
        frame["ValidTo"] = frame["MembershipValidTo"]
    if "ValidFrom" not in frame:
        frame["ValidFrom"] = pd.NaT
    if "ValidTo" not in frame:
        frame["ValidTo"] = pd.NaT
    frame["ValidFrom"] = pd.to_datetime(frame["ValidFrom"], errors="coerce").dt.normalize()
    frame["ValidTo"] = pd.to_datetime(frame["ValidTo"], errors="coerce").dt.normalize()
    if "Decision" not in frame:
        frame["Decision"] = "APPROVED"
    if "AllocationWeight" not in frame:
        if "ExposureShare" in frame:
            frame["AllocationWeight"] = frame["ExposureShare"]
        elif "RelevanceWeight" in frame:
            frame["AllocationWeight"] = frame["RelevanceWeight"]
        else:
            frame["AllocationWeight"] = np.nan
    frame["AllocationWeight"] = pd.to_numeric(frame["AllocationWeight"], errors="coerce")
    invalid_weight = frame["AllocationWeight"].dropna().lt(0) | frame[
        "AllocationWeight"
    ].dropna().gt(1)
    if invalid_weight.any():
        raise ValueError("story AllocationWeight must be within [0, 1]")
    duplicate = frame.duplicated(["GroupId", "TickerBase", "ValidFrom"], keep=False)
    if duplicate.any():
        raise ValueError("duplicate story membership relationship/version")
    return frame


def _active_memberships_for_date(prepared_membership: pd.DataFrame, ticker: str, date: pd.Timestamp) -> pd.DataFrame:
    candidates = prepared_membership.loc[
        prepared_membership["TickerBase"].eq(ticker)
        & prepared_membership["Decision"].astype(str).str.upper().eq("APPROVED")
        & (prepared_membership["ValidFrom"].isna() | prepared_membership["ValidFrom"].le(date))
        & (prepared_membership["ValidTo"].isna() | prepared_membership["ValidTo"].ge(date))
    ].copy()
    if candidates.empty:
        return candidates
    return candidates.sort_values("ValidFrom").drop_duplicates("GroupId", keep="last")


def _membership_allocations(active: pd.DataFrame) -> list[tuple[str, str, float]]:
    if active.empty:
        return [("UNMAPPED", "未映射", 1.0)]
    weights = active["AllocationWeight"]
    known = weights.notna()
    known_total = float(weights.loc[known].sum()) if known.any() else 0.0
    if known_total > 1.0 + 1.0e-10:
        raise ValueError("audited story allocations exceed one")
    resolved = pd.Series(0.0, index=active.index)
    if not known.any():
        resolved[:] = 1.0 / len(active)
    elif (~known).any():
        resolved.loc[known] = weights.loc[known]
        resolved.loc[~known] = max(0.0, 1.0 - known_total) / int((~known).sum())
    else:
        resolved[:] = weights
    allocations = [
        (str(row.GroupId), str(row.GroupName), float(resolved.loc[index]))
        for index, row in active.iterrows()
        if resolved.loc[index] > 1.0e-10
    ]
    residual = max(0.0, 1.0 - float(resolved.sum()))
    if residual > 1.0e-10:
        allocations.append(("UNMAPPED", "未映射", residual))
    if not np.isclose(sum(item[2] for item in allocations), 1.0, atol=1.0e-10):
        raise ValueError("story allocations do not conserve one unit")
    return allocations


def def_map_events_to_story_groups(events: pd.DataFrame, membership: pd.DataFrame) -> pd.DataFrame:
    if events.empty:
        return pd.DataFrame()
    prepared_membership = def_prepare_story_membership(membership)
    quantity_columns = (
        "RawDeltaShares",
        "FundScaleMechanicalQty",
        "ActiveQty",
        "RawDeltaValue",
        "FundScaleMechanicalValue",
        "EstimatedActiveValue",
    )
    rows: list[dict[str, Any]] = []
    for event in events.to_dict(orient="records"):
        # The holding change and story constituent set are both executable on
        # EffectiveDate.  EvidenceDate is retained only for legacy event rows
        # that do not yet carry the explicit trading-calendar result.
        effective_date = pd.to_datetime(event.get("EffectiveDate"), errors="coerce")
        membership_date_source = "EffectiveDate"
        if pd.isna(effective_date):
            effective_date = pd.to_datetime(event.get("EvidenceDate"), errors="coerce")
            membership_date_source = "EvidenceDate_Fallback"
        if pd.isna(effective_date):
            raise ValueError("ETF story event has neither EffectiveDate nor EvidenceDate")
        date = pd.Timestamp(effective_date).normalize()
        active = _active_memberships_for_date(prepared_membership, str(event["TickerBase"]), date)
        allocations = _membership_allocations(active)
        for group_id, group_name, conserved_fraction in allocations:
            for view in STORY_VIEWS:
                if view == "STORY_FULL" and group_id == "UNMAPPED" and not active.empty:
                    continue
                fraction = 1.0 if view == "STORY_FULL" else conserved_fraction
                row = dict(event)
                row.update(
                    {
                        "GroupId": group_id,
                        "GroupName": group_name,
                        "MembershipAsOfDate": date,
                        "MembershipDateSource": membership_date_source,
                        "StoryView": view,
                        "AllocationFraction": fraction,
                        "CrossGroupAdditivity": "NOT_ADDITIVE" if view == "STORY_FULL" else "CAPITAL_CONSERVED",
                    }
                )
                for column in quantity_columns:
                    row[f"Source{column}"] = event.get(column, np.nan)
                    row[f"Allocated{column}"] = (
                        float(event[column]) * fraction if _finite(event.get(column)) else np.nan
                    )
                rows.append(row)
    return pd.DataFrame(rows).sort_values(["EvidenceDate", "ETFId", "TickerBase", "StoryView", "GroupId"]).reset_index(drop=True)


def def_validate_capital_conservation(mapped_events: pd.DataFrame) -> dict[str, Any]:
    if mapped_events.empty:
        return {"Status": "PASS_EMPTY", "EventCount": 0, "CheckedQuantities": 0}
    conserved = mapped_events.loc[mapped_events["StoryView"].eq("CAPITAL_CONSERVED")]
    checked = 0
    for event_id, group in conserved.groupby("EventId", sort=False):
        if not np.isclose(group["AllocationFraction"].sum(), 1.0):
            raise AssertionError(f"capital allocation does not sum to one for {event_id}")
        for column in ("RawDeltaShares", "FundScaleMechanicalQty", "ActiveQty", "EstimatedActiveValue"):
            source = group[f"Source{column}"].iloc[0]
            if _finite(source):
                allocated = group[f"Allocated{column}"].sum()
                if not np.isclose(float(source), float(allocated)):
                    raise AssertionError(f"{column} is not conserved for {event_id}")
                checked += 1
    return {"Status": "PASS", "EventCount": int(conserved["EventId"].nunique()), "CheckedQuantities": checked}


def def_map_holdings_to_story_groups(latest_holdings: pd.DataFrame, membership: pd.DataFrame) -> pd.DataFrame:
    if latest_holdings.empty:
        return pd.DataFrame()
    prepared_membership = def_prepare_story_membership(membership)
    rows: list[dict[str, Any]] = []
    for holding in latest_holdings.to_dict(orient="records"):
        date = pd.Timestamp(holding["EvidenceDate"]).normalize()
        active = _active_memberships_for_date(prepared_membership, str(holding["TickerBase"]), date)
        allocations = _membership_allocations(active)
        position_value = (
            float(holding["AUM"]) * float(holding["WeightPct"]) / 100.0
            if _finite(holding.get("AUM")) and _finite(holding.get("WeightPct"))
            else np.nan
        )
        for group_id, group_name, conserved_fraction in allocations:
            for view in STORY_VIEWS:
                if view == "STORY_FULL" and group_id == "UNMAPPED" and not active.empty:
                    continue
                fraction = 1.0 if view == "STORY_FULL" else conserved_fraction
                row = dict(holding)
                row.update(
                    {
                        "GroupId": group_id,
                        "GroupName": group_name,
                        "StoryView": view,
                        "AllocationFraction": fraction,
                        "CrossGroupAdditivity": "NOT_ADDITIVE" if view == "STORY_FULL" else "CAPITAL_CONSERVED",
                        "AllocatedWeightPct": float(holding["WeightPct"]) * fraction if _finite(holding.get("WeightPct")) else np.nan,
                        "EstimatedPositionValue": position_value,
                        "AllocatedPositionValue": position_value * fraction if _finite(position_value) else np.nan,
                        "AllocatedShares": float(holding["Shares"]) * fraction if _finite(holding.get("Shares")) else np.nan,
                    }
                )
                rows.append(row)
    return pd.DataFrame(rows).sort_values(["ETFId", "StoryView", "GroupId", "TickerBase"]).reset_index(drop=True)


def def_validate_holding_conservation(mapped_holdings: pd.DataFrame) -> dict[str, Any]:
    if mapped_holdings.empty:
        return {"Status": "PASS_EMPTY", "HoldingCount": 0, "CheckedQuantities": 0}
    conserved = mapped_holdings.loc[mapped_holdings["StoryView"].eq("CAPITAL_CONSERVED")]
    checked = 0
    for keys, group in conserved.groupby(["SnapshotId", "TickerBase"], sort=False):
        if not np.isclose(group["AllocationFraction"].sum(), 1.0):
            raise AssertionError(f"holding allocation does not sum to one for {keys}")
        source_pairs = (
            ("WeightPct", "AllocatedWeightPct"),
            ("Shares", "AllocatedShares"),
            ("EstimatedPositionValue", "AllocatedPositionValue"),
        )
        for source_column, allocated_column in source_pairs:
            source = group[source_column].iloc[0]
            if _finite(source):
                if not np.isclose(float(source), float(group[allocated_column].sum())):
                    raise AssertionError(f"{source_column} is not conserved for {keys}")
                checked += 1
    return {
        "Status": "PASS",
        "HoldingCount": int(conserved.groupby(["SnapshotId", "TickerBase"]).ngroups),
        "CheckedQuantities": checked,
    }


def def_aggregate_group_exposure(mapped_holdings: pd.DataFrame, as_of: Any) -> pd.DataFrame:
    if mapped_holdings.empty:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for (view, group_id), group in mapped_holdings.groupby(["StoryView", "GroupId"], sort=True):
        rows.append(
            {
                "AsOf": def_parse_available_at(as_of),
                "StoryView": view,
                "GroupId": group_id,
                "GroupName": group["GroupName"].iloc[0],
                "ETFCount": int(group["ETFId"].nunique()),
                "HoldingCount": int(group["TickerBase"].nunique()),
                "AllocatedWeightPctSum": _sum_or_nan(group["AllocatedWeightPct"]),
                "AllocatedPositionValueSum": _sum_or_nan(group["AllocatedPositionValue"]),
                "AUMCoveredETFCount": int(group.loc[group["AUM"].notna(), "ETFId"].nunique()),
                "CrossGroupAdditivity": group["CrossGroupAdditivity"].iloc[0],
            }
        )
    return pd.DataFrame(rows)


def def_aggregate_group_event_consensus(mapped_events: pd.DataFrame) -> pd.DataFrame:
    if mapped_events.empty:
        return pd.DataFrame()
    work = mapped_events.copy()
    work["HasAddEvidence"] = work["ManagerDirection"].eq("ACTIVE_BUY") | work["Action"].isin(["NEW_ENTRY", "REENTRY"])
    work["HasReduceEvidence"] = work["ManagerDirection"].eq("ACTIVE_SELL") | work["Action"].eq("EXIT")
    etf_rows: list[dict[str, Any]] = []
    for keys, group in work.groupby(["EvidenceDate", "StoryView", "GroupId", "GroupName", "ETFId"], sort=True):
        date, view, group_id, group_name, etf_id = keys
        etf_rows.append(
            {
                "EvidenceDate": date,
                "StoryView": view,
                "GroupId": group_id,
                "GroupName": group_name,
                "ETFId": etf_id,
                "HasAddEvidence": bool(group["HasAddEvidence"].any()),
                "HasReduceEvidence": bool(group["HasReduceEvidence"].any()),
                "HasAttributableManagerQty": bool(group["ActiveQty"].notna().any()),
                "AllocatedActiveQty": _sum_or_nan(group["AllocatedActiveQty"]),
                "AllocatedEstimatedActiveValue": _sum_or_nan(group["AllocatedEstimatedActiveValue"]),
            }
        )
    per_etf = pd.DataFrame(etf_rows)
    rows: list[dict[str, Any]] = []
    for keys, group in per_etf.groupby(["EvidenceDate", "StoryView", "GroupId", "GroupName"], sort=True):
        date, view, group_id, group_name = keys
        etf_count = int(group["ETFId"].nunique())
        add_count = int(group["HasAddEvidence"].sum())
        reduce_count = int(group["HasReduceEvidence"].sum())
        attributable = int(group["HasAttributableManagerQty"].sum())
        rows.append(
            {
                "EvidenceDate": date,
                "StoryView": view,
                "GroupId": group_id,
                "GroupName": group_name,
                "ETFObservedCount": etf_count,
                "AttributableManagerETFCount": attributable,
                "AttributionCoverage": attributable / etf_count if etf_count else np.nan,
                "AddEvidenceETFCount": add_count,
                "ReduceEvidenceETFCount": reduce_count,
                "AddConsensusBreadth": add_count / etf_count if etf_count else np.nan,
                "ReduceConsensusBreadth": reduce_count / etf_count if etf_count else np.nan,
                "NetConsensusBreadth": (add_count - reduce_count) / etf_count if etf_count else np.nan,
                "AllocatedActiveQtySum": _sum_or_nan(group["AllocatedActiveQty"]),
                "AllocatedEstimatedActiveValueSum": _sum_or_nan(group["AllocatedEstimatedActiveValue"]),
                "ETFIds": "|".join(sorted(group["ETFId"].unique())),
                "CrossGroupAdditivity": "NOT_ADDITIVE" if view == "STORY_FULL" else "CAPITAL_CONSERVED",
            }
        )
    return pd.DataFrame(rows)


# =============================================================================
# PUBLIC ORCHESTRATION API
# =============================================================================


def def_build_active_etf_analysis(
    raw_holdings: pd.DataFrame,
    as_of: Any,
    *,
    membership: pd.DataFrame | None = None,
    trading_calendar: Iterable[Any] | None = None,
    config: ActiveETFAnalysisConfig = ActiveETFAnalysisConfig(),
) -> dict[str, Any]:
    cutoff = def_parse_available_at(as_of, config.source_timezone)
    if pd.isna(cutoff):
        raise ValueError("as_of must be an exact point-in-time timestamp")

    # ``prepared_snapshots`` is a formal output of this function (and the
    # system orchestrator publishes every returned DataFrame).  Therefore the
    # normalization/audit view must obey the same knowledge boundary as every
    # derived table.  Keep all *known* append-only vintages, including a late
    # correction once its own AvailableAt has arrived, but never publish raw
    # rows whose AvailableAt is still in the future.
    prepared_all = def_prepare_holdings_snapshots(raw_holdings, config)
    prepared = (
        prepared_all.loc[prepared_all["AvailableAt"].le(cutoff)]
        .copy()
        .reset_index(drop=True)
    )
    quality = def_build_snapshot_quality(prepared, cutoff)
    latest = def_materialize_holdings_asof(
        prepared, cutoff, latest_only=True, complete_only=True
    )
    events = def_build_holding_events(
        prepared,
        cutoff,
        trading_calendar=trading_calendar,
        include_initial_rows=config.include_initial_rows,
    )
    _, tsmc_anchor_events = _split_tsmc_anchor(events)
    _, tsmc_anchor_latest = _split_tsmc_anchor(latest)
    tsmc_anchor_consensus = def_aggregate_security_consensus(tsmc_anchor_events)
    if not tsmc_anchor_consensus.empty:
        tsmc_anchor_consensus["AnchorPolicy"] = TSMC_ANCHOR_POLICY
    result: dict[str, Any] = {
        "prepared_snapshots": prepared,
        "snapshot_quality": quality,
        "latest_holdings_by_etf": latest,
        "individual_holding_events": events,
        "etf_fund_flows": def_build_etf_fund_flows(
            prepared, cutoff, trading_calendar=trading_calendar
        ),
        "security_consensus": def_aggregate_security_consensus(events),
        "etf_pair_overlap": def_compute_etf_overlap(latest),
        "holding_crowding": def_compute_holding_crowding(latest),
        "tsmc_anchor_holding_events": tsmc_anchor_events,
        "tsmc_anchor_latest_holdings": tsmc_anchor_latest,
        "tsmc_anchor_security_consensus": tsmc_anchor_consensus,
        "policy": {
            "EngineId": ENGINE_ID,
            "EngineVersion": ENGINE_VERSION,
            "PITColumn": "AvailableAt",
            "ManagerAttribution": "ActiveQty = Shares_t - Shares_prev * ETFUnits_t / ETFUnits_prev",
            "MissingUnitsPolicy": "NO_MANAGER_BUY_OR_SELL_INFERENCE",
            "InvestmentTrustPolicy": "ACTIVE_ETF_EVIDENCE_SEPARATE_FROM_T86_DO_NOT_ADD",
            "AggregationPolicy": "SEPARATE_EVIDENCE_LANES_NO_WEIGHTED_COMBINATION",
            "StoryComparisonUniverse": STORY_COMPARISON_UNIVERSE,
            "TSMCAnchorPolicy": TSMC_ANCHOR_POLICY,
            "FullFundAuditPolicy": (
                "PREPARED_SNAPSHOTS_LATEST_HOLDINGS_INDIVIDUAL_EVENTS_AND_"
                "CONSERVATION_INCLUDE_2330"
            ),
        },
    }
    if membership is not None:
        # Map the complete portfolio first so conservation continues to audit
        # every fund holding, including 2330.  Only after that audit boundary
        # do we remove the anchor from published story/group comparisons.
        all_mapped_events = def_map_events_to_story_groups(events, membership)
        all_mapped_holdings = def_map_holdings_to_story_groups(latest, membership)
        mapped_events, mapped_anchor_events = _split_tsmc_anchor(all_mapped_events)
        mapped_holdings, mapped_anchor_holdings = _split_tsmc_anchor(
            all_mapped_holdings
        )
        mapped_events = _mark_story_comparison_scope(mapped_events)
        mapped_holdings = _mark_story_comparison_scope(mapped_holdings)
        group_event_consensus = _mark_story_comparison_scope(
            def_aggregate_group_event_consensus(mapped_events)
        )
        group_exposure = _mark_story_comparison_scope(
            def_aggregate_group_exposure(mapped_holdings, cutoff)
        )
        result.update(
            {
                "story_event_views": mapped_events,
                "story_event_conservation": _conservation_with_scope(
                    def_validate_capital_conservation(all_mapped_events),
                    "ALL_ETF_HOLDING_EVENTS_INCLUDING_2330_FUND_AUDIT",
                ),
                "story_event_comparison_conservation": _conservation_with_scope(
                    def_validate_capital_conservation(mapped_events),
                    "STORY_COMPARISON_EX_2330",
                ),
                "group_event_consensus": group_event_consensus,
                "story_holding_views": mapped_holdings,
                "story_holding_conservation": _conservation_with_scope(
                    def_validate_holding_conservation(all_mapped_holdings),
                    "ALL_LATEST_ETF_HOLDINGS_INCLUDING_2330_FUND_AUDIT",
                ),
                "story_holding_comparison_conservation": _conservation_with_scope(
                    def_validate_holding_conservation(mapped_holdings),
                    "STORY_COMPARISON_EX_2330",
                ),
                "group_exposure": group_exposure,
                "tsmc_anchor_story_event_audit": mapped_anchor_events,
                "tsmc_anchor_story_holding_audit": mapped_anchor_holdings,
            }
        )
    return result


# =============================================================================
# OFFLINE SELF-TEST API
# =============================================================================


def def_run_self_test() -> dict[str, Any]:
    checks: list[str] = []

    observations = pd.DataFrame(
        [
            {"ETFId": "00981A", "ETFName": "主動台股甲", "FundType": "ACTIVE_EQUITY", "AssetScope": "TAIWAN_EQUITY", "EligibilityStatus": "VERIFIED"},
            {"ETFId": "009A01", "ETFName": "主動台股乙", "FundType": "ACTIVE_EQUITY", "AssetScope": "TAIWAN_EQUITY", "EligibilityStatus": "VERIFIED"},
        ]
    )
    registry = def_append_universe_events(pd.DataFrame(), observations, "2026-01-02 18:00+08:00", snapshot_complete=True)
    frozen = registry.copy(deep=True)
    registry = def_append_universe_events(registry, observations.iloc[[0]], "2026-01-05 18:00+08:00", snapshot_complete=True)
    registry = def_append_universe_events(registry, observations, "2026-01-06 18:00+08:00", snapshot_complete=True)
    pd.testing.assert_frame_equal(frozen, registry.iloc[: len(frozen)][frozen.columns].reset_index(drop=True), check_dtype=False)
    if registry["EventType"].tolist() != ["DISCOVERED", "DISCOVERED", "WENT_DORMANT", "REACTIVATED"]:
        raise AssertionError("append-only discovery/dormancy/reactivation contract failed")
    checks.append("append_only_universe_accepts_both_code_shapes")

    rows: list[dict[str, Any]] = []

    def add_snapshot(
        etf: str,
        date: str,
        available: str,
        units: float | None,
        holdings: list[tuple[str, float | None, float, float]],
        *,
        complete: bool = True,
    ) -> None:
        for ticker, shares, weight, price in holdings:
            rows.append(
                {
                    "ETFId": etf,
                    "ETFName": etf,
                    "PortfolioDate": date,
                    "AvailableAt": available,
                    "Ticker": ticker,
                    "Shares": shares,
                    "WeightPct": weight,
                    "ETFUnits": units,
                    "NAV": 20.0,
                    "AUM": 1_000_000.0,
                    "Price": price,
                    "IsComplete": complete,
                    "CompletenessReason": "SELF_TEST",
                    "SourceType": "OFFICIAL_PCF",
                    "SourcePayloadHash": f"{etf}-{date}-{complete}",
                }
            )

    add_snapshot("00981A", "2026-01-02", "2026-01-02 18:00+08:00", 1_000.0, [("1111.TW", 100.0, 10.0, 50.0)])
    add_snapshot("00981A", "2026-01-05", "2026-01-05 18:00+08:00", 1_100.0, [("1111.TW", 110.0, 10.0, 51.0), ("2222.TWO", 60.0, 5.0, 30.0)])
    # An incomplete omission must not advance the comparison state.
    add_snapshot("00981A", "2026-01-06", "2026-01-06 18:00+08:00", 1_150.0, [("1111.TW", 115.0, 10.0, 52.0)], complete=False)
    add_snapshot("00981A", "2026-01-07", "2026-01-07 18:00+08:00", 1_200.0, [("2222.TWO", 65.0, 5.0, 31.0)])
    add_snapshot("00981A", "2026-01-08", "2026-01-08 18:00+08:00", 1_250.0, [("1111.TW", 20.0, 2.0, 53.0), ("2222.TWO", 67.0, 5.0, 32.0)])
    # Missing ETF units: raw shares may change, but manager direction is unknown.
    add_snapshot("009A01", "2026-01-02", "2026-01-02 19:00+08:00", None, [("1111.TW", 200.0, 20.0, 50.0), ("3333.TW", None, 4.0, 40.0)])
    add_snapshot("009A01", "2026-01-05", "2026-01-05 19:00+08:00", None, [("1111.TW", 220.0, 20.0, 51.0), ("3333.TW", None, 5.0, 41.0)])

    raw = pd.DataFrame(rows)
    calendar = pd.bdate_range("2026-01-02", "2026-01-16")
    membership = pd.DataFrame(
        [
            {"GroupId": "AI", "GroupName": "AI", "Ticker": "1111.TW", "ValidFrom": "2025-01-01", "ExposureShare": 0.75, "Decision": "APPROVED"},
            {"GroupId": "COOL", "GroupName": "AI散熱", "Ticker": "1111.TW", "ValidFrom": "2025-01-01", "ExposureShare": 0.25, "Decision": "APPROVED"},
            {"GroupId": "CPO", "GroupName": "CPO", "Ticker": "2222.TWO", "ValidFrom": "2025-01-01", "Decision": "APPROVED"},
        ]
    )
    before = def_build_active_etf_analysis(raw, "2026-01-05 17:59+08:00", membership=membership, trading_calendar=calendar)
    if set(before["latest_holdings_by_etf"]["PortfolioDate"].dt.strftime("%Y-%m-%d")) != {"2026-01-02"}:
        raise AssertionError("future AvailableAt leaked into the PIT materialization")
    checks.append("available_at_point_in_time")

    late_revision_raw = pd.DataFrame(
        [
            {"ETFId": "00981A", "PortfolioDate": "2026-02-02", "AvailableAt": "2026-02-02 18:00+08:00", "Ticker": "1111.TW", "Shares": 100.0, "WeightPct": 10.0, "ETFUnits": 1_000.0, "IsComplete": True, "SourcePayloadHash": "ORIGINAL"},
            {"ETFId": "00981A", "PortfolioDate": "2026-02-02", "AvailableAt": "2026-02-04 18:00+08:00", "Ticker": "1111.TW", "Shares": 90.0, "WeightPct": 9.0, "ETFUnits": 1_000.0, "IsComplete": True, "SourcePayloadHash": "LATE_CORRECTION"},
            {"ETFId": "00981A", "PortfolioDate": "2026-02-03", "AvailableAt": "2026-02-03 18:00+08:00", "Ticker": "1111.TW", "Shares": 100.0, "WeightPct": 10.0, "ETFUnits": 1_000.0, "IsComplete": True, "SourcePayloadHash": "NEXT_DATE"},
        ]
    )
    late_revision = def_prepare_holdings_snapshots(late_revision_raw)
    pre_correction = def_build_holding_events(late_revision, "2026-02-03 23:00+08:00")
    post_correction = def_build_holding_events(late_revision, "2026-02-05 00:00+08:00")
    old_event = pre_correction.loc[pre_correction["PortfolioDate"].eq(pd.Timestamp("2026-02-03"))].iloc[0]
    revised_event = post_correction.loc[post_correction["PortfolioDate"].eq(pd.Timestamp("2026-02-03"))].iloc[0]
    if not np.isclose(old_event["ActiveQty"], 0.0) or not np.isclose(revised_event["ActiveQty"], 10.0):
        raise AssertionError("late prior-date correction was not represented as a new event vintage")
    if revised_event["AvailableAt"] != pd.Timestamp("2026-02-04 10:00:00+00:00"):
        raise AssertionError("late correction backdated the revised event AvailableAt")
    checks.append("late_revision_cannot_backdate_event_evidence")

    analysis = def_build_active_etf_analysis(raw, "2026-01-09 00:00+08:00", membership=membership, trading_calendar=calendar)
    events = analysis["individual_holding_events"]
    proportional = events.loc[
        events["ETFId"].eq("00981A")
        & events["PortfolioDate"].eq(pd.Timestamp("2026-01-05"))
        & events["TickerBase"].eq("1111")
    ].iloc[0]
    if proportional["Action"] != "UNCHANGED_AFTER_UNIT_ADJUSTMENT" or not np.isclose(proportional["ActiveQty"], 0.0):
        raise AssertionError("proportional ETF-unit creation was misclassified as manager buying")
    checks.append("unit_normalized_manager_quantity")

    unresolved = events.loc[
        events["ETFId"].eq("009A01")
        & events["PortfolioDate"].eq(pd.Timestamp("2026-01-05"))
        & events["TickerBase"].eq("1111")
    ].iloc[0]
    if unresolved["ManagerDirection"].startswith("ACTIVE_") or _finite(unresolved["ActiveQty"]):
        raise AssertionError("missing ETFUnits produced a false manager direction")
    weight_only = events.loc[
        events["ETFId"].eq("009A01")
        & events["PortfolioDate"].eq(pd.Timestamp("2026-01-05"))
        & events["TickerBase"].eq("3333")
    ].iloc[0]
    if weight_only["Action"] != "WEIGHT_UP_ONLY":
        raise AssertionError("missing holding shares did not remain weight-only evidence")
    checks.append("missing_units_and_shares_fail_closed")

    actions = events.loc[events["ETFId"].eq("00981A"), ["PortfolioDate", "TickerBase", "Action"]]
    expected = {
        ("2026-01-05", "2222", "NEW_ENTRY"),
        ("2026-01-07", "1111", "EXIT"),
        ("2026-01-08", "1111", "REENTRY"),
    }
    actual = {(row.PortfolioDate.strftime("%Y-%m-%d"), row.TickerBase, row.Action) for row in actions.itertuples(index=False)}
    if not expected.issubset(actual) or any(date == "2026-01-06" for date, _, _ in actual):
        raise AssertionError("entry/exit/re-entry or incomplete-snapshot policy failed")
    checks.append("new_exit_reentry_and_incomplete_snapshot")

    if events["ETFId"].nunique() != 2 or analysis["security_consensus"].empty:
        raise AssertionError("individual ETF identity or aggregate consensus was lost")
    checks.append("individual_and_consensus_preserve_etf_identity")

    conservation = analysis["story_event_conservation"]
    if conservation["Status"] != "PASS":
        raise AssertionError("capital-conserved story allocation failed")
    first_event = analysis["story_event_views"].loc[
        analysis["story_event_views"]["TickerBase"].eq("1111")
        & analysis["story_event_views"]["StoryView"].eq("CAPITAL_CONSERVED")
    ].groupby("EventId")["AllocationFraction"].sum()
    if not np.allclose(first_event.values, 1.0):
        raise AssertionError("multi-story conserved fractions do not sum to one")
    checks.append("story_full_and_capital_conserved_views")

    if analysis["etf_pair_overlap"].empty or analysis["holding_crowding"].empty:
        raise AssertionError("overlap/crowding outputs are missing")
    if any("score" in str(column).lower() for value in analysis.values() if isinstance(value, pd.DataFrame) for column in value.columns):
        raise AssertionError("composite score column leaked into the engine")
    checks.append("overlap_crowding_without_composite_score")

    ledger = def_append_holding_event_ledger(pd.DataFrame(), events)
    replay = def_append_holding_event_ledger(ledger, events)
    if len(replay) != len(ledger):
        raise AssertionError("holding event replay is not idempotent")
    checks.append("append_only_holding_event_replay")

    return {
        "EngineId": ENGINE_ID,
        "EngineVersion": ENGINE_VERSION,
        "Status": "PASS",
        "ChecksPassed": len(checks),
        "Checks": checks,
        "PreparedSnapshotRows": int(len(analysis["prepared_snapshots"])),
        "IndividualEventRows": int(len(events)),
        "ConsensusRows": int(len(analysis["security_consensus"])),
        "OverlapRows": int(len(analysis["etf_pair_overlap"])),
        "CrowdingRows": int(len(analysis["holding_crowding"])),
        "StoryEventRows": int(len(analysis["story_event_views"])),
        "PublicAPIs": [
            "def_append_universe_events",
            "def_materialize_universe_asof",
            "def_prepare_holdings_snapshots",
            "def_materialize_holdings_asof",
            "def_build_holding_events",
            "def_build_etf_fund_flows",
            "def_aggregate_security_consensus",
            "def_compute_etf_overlap",
            "def_compute_holding_crowding",
            "def_map_events_to_story_groups",
            "def_map_holdings_to_story_groups",
            "def_validate_capital_conservation",
            "def_validate_holding_conservation",
            "def_build_active_etf_analysis",
        ],
    }


def _json_default(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    raise TypeError(f"not JSON serializable: {type(value).__name__}")


def def_main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true", help="run the fully offline evidence-contract test")
    args = parser.parse_args(argv)
    if not args.selftest:
        parser.error("this standalone module currently supports --selftest; import its public APIs for pipelines")
    print(json.dumps(def_run_self_test(), ensure_ascii=False, indent=2, default=_json_default))
    return 0


if __name__ == "__main__":
    raise SystemExit(def_main())
