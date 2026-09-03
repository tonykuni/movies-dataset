from __future__ import annotations

"""Point-in-time monthly-revenue *reference* for VIA opportunity review.

Revenue is outside the classification, index, weighting, positioning-signal,
and candidate-selection systems.  The orchestrator may call this module only
after the price/volume/chip transition engine has independently reached strict
stage 3 or 4, so the output can be inspected as ex-post context without feeding
back into the decision path.  Only vintages known by the requested as-of time
are visible.  Legacy ``evidence`` names remain solely for API compatibility.
"""

# =============================================================================
# def 00 PARAMETERS — structural/statistical controls, never market cut-offs
# =============================================================================

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

if __package__:
    from .via_time_utils import def_available_at_utc, def_local_calendar_date
else:  # standalone script/import from the engine directory
    from via_time_utils import def_available_at_utc, def_local_calendar_date


ENGINE_ID = "VIA_MONTHLY_REVENUE_EVIDENCE_V0500"
ENGINE_VERSION = "0.5.0"

MONTHLY_WINDOWS = (3, 6, 12, 24)
DATE_COLUMN = "ReportMonth"
AVAILABLE_COLUMN = "AvailableAt"
TICKER_COLUMN = "Ticker"
EPS = np.finfo(float).eps

REQUIRED_COLUMNS = {
    DATE_COLUMN,
    AVAILABLE_COLUMN,
    TICKER_COLUMN,
    "Revenue",
}


@dataclass(frozen=True)
class RevenueEvidenceConfig:
    monthly_windows: tuple[int, ...] = MONTHLY_WINDOWS
    require_available_at: bool = True


# =============================================================================
# def 01 NORMALIZATION / PIT VINTAGE
# =============================================================================


def def_ticker_base(value: object) -> str:
    text = str(value or "").strip().upper()
    return text.removesuffix(".TW").removesuffix(".TWO")


def def_prepare_monthly_revenue(
    raw: pd.DataFrame,
    config: RevenueEvidenceConfig = RevenueEvidenceConfig(),
) -> pd.DataFrame:
    """Normalize monthly revenue and retain every disclosed vintage.

    Required grain is ``Ticker + ReportMonth + AvailableAt``.  Multiple
    vintages are valid because MOPS revisions must be visible in the audit
    history; the as-of materializer chooses only the latest known vintage.
    """

    missing = sorted(REQUIRED_COLUMNS.difference(raw.columns))
    if missing:
        raise ValueError(f"monthly revenue missing required columns: {missing}")
    frame = raw.copy()
    frame[TICKER_COLUMN] = frame[TICKER_COLUMN].map(def_ticker_base)
    frame[DATE_COLUMN] = frame[DATE_COLUMN].map(def_local_calendar_date).dt.to_period("M").dt.to_timestamp()
    frame[AVAILABLE_COLUMN] = frame[AVAILABLE_COLUMN].map(def_available_at_utc)
    for column in (
        "Revenue",
        "RevenuePreviousYear",
        "CumulativeRevenue",
        "CumulativeRevenuePreviousYear",
        "OfficialYoY",
        "OfficialMoM",
        "OfficialCumulativeYoY",
        "ReportingPeriodMonths",
    ):
        if column not in frame.columns:
            frame[column] = np.nan
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if "Source" not in frame:
        frame["Source"] = "UNSPECIFIED"
    if "EvidenceTier" not in frame:
        frame["EvidenceTier"] = "SOURCE_REPORTED"
    invalid = (
        frame[TICKER_COLUMN].eq("")
        | frame[DATE_COLUMN].isna()
        | frame[AVAILABLE_COLUMN].isna()
        | frame["Revenue"].lt(0)
    )
    if invalid.any():
        raise ValueError(f"monthly revenue has {int(invalid.sum())} invalid rows")
    duplicate = frame.duplicated([TICKER_COLUMN, DATE_COLUMN, AVAILABLE_COLUMN], keep=False)
    if duplicate.any():
        raise ValueError(f"monthly revenue has {int(duplicate.sum())} duplicate vintage rows")
    frame["ReportingPeriodMonths"] = frame["ReportingPeriodMonths"].fillna(1).astype(int)
    frame["ComparabilityStatus"] = np.where(
        frame["ReportingPeriodMonths"].eq(1),
        "COMPARABLE_SINGLE_MONTH",
        "HOLD_MULTI_MONTH_REPORTING_PERIOD",
    )
    return frame.sort_values([TICKER_COLUMN, DATE_COLUMN, AVAILABLE_COLUMN]).reset_index(drop=True)


def def_materialize_revenue_asof(
    prepared: pd.DataFrame,
    as_of: str | pd.Timestamp,
) -> pd.DataFrame:
    """Return the latest vintage that was observable by ``as_of``."""

    timestamp = def_available_at_utc(as_of)
    if pd.isna(timestamp):
        raise ValueError(f"invalid as_of timestamp: {as_of!r}")
    known = prepared.loc[prepared[AVAILABLE_COLUMN].le(timestamp)].copy()
    if known.empty:
        return known
    return (
        known.sort_values(AVAILABLE_COLUMN)
        .drop_duplicates([TICKER_COLUMN, DATE_COLUMN], keep="last")
        .sort_values([TICKER_COLUMN, DATE_COLUMN])
        .reset_index(drop=True)
    )


# =============================================================================
# def 02 COMPANY REFERENCE — raw post-opportunity measures, no score
# =============================================================================


def def_safe_ratio_change(current: float, base: float) -> float:
    if not np.isfinite(current) or not np.isfinite(base) or base <= 0:
        return np.nan
    return float(current / base - 1.0)


def def_linear_slope(values: Iterable[float]) -> float:
    array = np.asarray(list(values), dtype=float)
    array = array[np.isfinite(array)]
    if len(array) < 2:
        return np.nan
    x = np.arange(len(array), dtype=float)
    return float(np.polyfit(x, array, 1)[0])


def def_consecutive_positive(values: Iterable[float]) -> int:
    count = 0
    for value in reversed(list(values)):
        if np.isfinite(value) and value > 0:
            count += 1
        else:
            break
    return count


def def_company_revenue_evidence(
    prepared: pd.DataFrame,
    as_of: str | pd.Timestamp,
    config: RevenueEvidenceConfig = RevenueEvidenceConfig(),
) -> pd.DataFrame:
    """Build one latest, point-in-time reference row per opportunity company.

    Official growth fields are retained where available.  Derived values use
    only the materialized vintage history and are explicitly labelled.
    """

    known = def_materialize_revenue_asof(prepared, as_of)
    rows: list[dict[str, object]] = []
    for ticker, history in known.groupby(TICKER_COLUMN, sort=True):
        history = history.sort_values(DATE_COLUMN).copy()
        latest = history.iloc[-1]
        report_month = pd.Timestamp(latest[DATE_COLUMN])
        previous_year_month = report_month - pd.DateOffset(years=1)
        prior_year = history.loc[history[DATE_COLUMN].eq(previous_year_month)]
        prior_year_revenue = (
            float(latest["RevenuePreviousYear"])
            if np.isfinite(latest["RevenuePreviousYear"])
            else (float(prior_year["Revenue"].iloc[-1]) if not prior_year.empty else np.nan)
        )
        derived_yoy = def_safe_ratio_change(float(latest["Revenue"]), prior_year_revenue)
        yoy = float(latest["OfficialYoY"]) / 100.0 if np.isfinite(latest["OfficialYoY"]) else derived_yoy
        yoy_source = "OFFICIAL" if np.isfinite(latest["OfficialYoY"]) else "DERIVED_POINT_IN_TIME"

        cumulative_yoy = (
            float(latest["OfficialCumulativeYoY"]) / 100.0
            if np.isfinite(latest["OfficialCumulativeYoY"])
            else def_safe_ratio_change(
                float(latest["CumulativeRevenue"]),
                float(latest["CumulativeRevenuePreviousYear"]),
            )
        )
        cumulative_source = (
            "OFFICIAL" if np.isfinite(latest["OfficialCumulativeYoY"]) else "DERIVED_POINT_IN_TIME"
        )

        history["DerivedYoY"] = history["OfficialYoY"] / 100.0
        missing_yoy = history["DerivedYoY"].isna()
        history_lookup = history.set_index(DATE_COLUMN)["Revenue"]
        for index in history.index[missing_yoy]:
            month = pd.Timestamp(history.at[index, DATE_COLUMN])
            base = history_lookup.get(month - pd.DateOffset(years=1), np.nan)
            history.at[index, "DerivedYoY"] = def_safe_ratio_change(float(history.at[index, "Revenue"]), float(base))

        same_month_prior = history.loc[
            history[DATE_COLUMN].dt.month.eq(report_month.month)
            & history[DATE_COLUMN].lt(report_month),
            "Revenue",
        ].dropna()
        seasonal_median = float(same_month_prior.median()) if len(same_month_prior) else np.nan
        seasonal_deviation = def_safe_ratio_change(float(latest["Revenue"]), seasonal_median)

        evidence: dict[str, object] = {
            "Ticker": ticker,
            "ReportMonth": report_month,
            "AvailableAt": latest[AVAILABLE_COLUMN],
            "Revenue": float(latest["Revenue"]),
            "RevenuePreviousYear": prior_year_revenue,
            "RevenueYoY": yoy,
            "RevenueYoYSource": yoy_source,
            "CumulativeRevenueYoY": cumulative_yoy,
            "CumulativeRevenueYoYSource": cumulative_source,
            "SeasonalMedianPriorYears": seasonal_median,
            "SeasonalDeviation": seasonal_deviation,
            "ConsecutivePositiveYoYMonths": def_consecutive_positive(history["DerivedYoY"]),
            "ReportingPeriodMonths": int(latest["ReportingPeriodMonths"]),
            "ComparabilityStatus": latest["ComparabilityStatus"],
            "EvidenceTier": latest["EvidenceTier"],
            "Source": latest["Source"],
        }
        for window in config.monthly_windows:
            recent = history["DerivedYoY"].tail(window)
            evidence[f"YoYMedian_{window}M"] = float(recent.median()) if recent.notna().any() else np.nan
            evidence[f"YoYSlope_{window}M"] = def_linear_slope(recent)
            evidence[f"YoYPositiveBreadth_{window}M"] = float(recent.gt(0).mean()) if recent.notna().any() else np.nan
            evidence[f"Observations_{window}M"] = int(recent.notna().sum())
        rows.append(evidence)
    return pd.DataFrame(rows)


# =============================================================================
# def 03 STORY-GROUP AGGREGATION
# =============================================================================


def def_active_membership_asof(membership: pd.DataFrame, as_of: str | pd.Timestamp) -> pd.DataFrame:
    if "EventType" in membership.columns:
        raise ValueError(
            "raw membership events cannot enter revenue analysis; materialize PIT history first"
        )
    required = {"GroupId", "Ticker"}
    missing = sorted(required.difference(membership.columns))
    if missing:
        raise ValueError(f"membership missing required columns: {missing}")
    frame = membership.copy()
    frame["Ticker"] = frame["Ticker"].map(def_ticker_base)
    if "ValidFrom" not in frame and "MembershipValidFrom" in frame:
        frame["ValidFrom"] = frame["MembershipValidFrom"]
    if "ValidTo" not in frame and "MembershipValidTo" in frame:
        frame["ValidTo"] = frame["MembershipValidTo"]
    if "ValidFrom" not in frame:
        frame["ValidFrom"] = pd.NaT
    if "ValidTo" not in frame:
        frame["ValidTo"] = pd.NaT
    if "Decision" not in frame:
        frame["Decision"] = "APPROVED"
    frame["ValidFrom"] = pd.to_datetime(frame["ValidFrom"], errors="coerce")
    frame["ValidTo"] = pd.to_datetime(frame["ValidTo"], errors="coerce")
    timestamp = def_local_calendar_date(as_of)
    if pd.isna(timestamp):
        raise ValueError(f"invalid as_of date: {as_of!r}")
    if "AsOfDate" in frame.columns and "HistoryViewStatus" not in frame.columns:
        snapshot_dates = frame["AsOfDate"].map(def_local_calendar_date).dropna().unique()
        if len(snapshot_dates) != 1 or pd.Timestamp(snapshot_dates[0]) != timestamp:
            raise ValueError(
                "membership as-of snapshot date differs from revenue decision date; "
                "use replayable membership history"
            )
    active = (
        (frame["ValidFrom"].isna() | frame["ValidFrom"].le(timestamp))
        & (frame["ValidTo"].isna() | frame["ValidTo"].ge(timestamp))
        & frame["Decision"].astype(str).str.upper().eq("APPROVED")
    )
    return frame.loc[active].drop_duplicates(["GroupId", "Ticker"], keep="last")


def def_group_revenue_evidence(
    company_evidence: pd.DataFrame,
    membership: pd.DataFrame,
    as_of: str | pd.Timestamp,
) -> pd.DataFrame:
    """Aggregate PIT company reference rows to multi-label story groups.

    A ticker may appear in multiple groups.  Each group receives the full
    exposure view; callers must not sum these rows across groups as cash flow.
    """

    active = def_active_membership_asof(membership, as_of)
    joined = active.merge(company_evidence, on="Ticker", how="left", validate="many_to_one")
    rows: list[dict[str, object]] = []
    for group_id, group in joined.groupby("GroupId", sort=True):
        covered = group.loc[group["RevenueYoY"].notna() & group["ComparabilityStatus"].eq("COMPARABLE_SINGLE_MONTH")]
        revenue_now = covered["Revenue"].sum(min_count=1)
        revenue_base = covered["RevenuePreviousYear"].sum(min_count=1)
        aggregate_yoy = def_safe_ratio_change(float(revenue_now), float(revenue_base))
        member_yoy = covered["RevenueYoY"]
        acceleration = covered.get("YoYSlope_6M", pd.Series(index=covered.index, dtype=float))
        positive_count = int(member_yoy.gt(0).sum()) if len(covered) else 0
        accelerating_count = int(acceleration.gt(0).sum()) if len(covered) else 0
        positive_breadth = float(member_yoy.gt(0).mean()) if len(covered) else np.nan
        accelerating_breadth = float(acceleration.gt(0).mean()) if len(covered) else np.nan
        nonpositive_count = len(covered) - positive_count
        nonaccelerating_count = len(covered) - accelerating_count
        if not len(covered):
            state = "MISSING_REVENUE_EVIDENCE"
        elif aggregate_yoy > 0 and accelerating_count > nonaccelerating_count and positive_count > nonpositive_count:
            state = "BROAD_ACCELERATION"
        elif aggregate_yoy > 0 and accelerating_count > 0:
            state = "NARROW_OR_MIXED_ACCELERATION"
        elif aggregate_yoy < 0 and accelerating_count <= nonaccelerating_count:
            state = "BROAD_DECELERATION"
        else:
            state = "MIXED"
        rows.append(
            {
                "AsOfDate": def_local_calendar_date(as_of),
                "GroupId": group_id,
                "GroupName": group["GroupName"].iloc[0] if "GroupName" in group else group_id,
                "MemberCount": int(group["Ticker"].nunique()),
                "CoveredMemberCount": int(covered["Ticker"].nunique()),
                "CoverageRatio": float(covered["Ticker"].nunique() / max(group["Ticker"].nunique(), 1)),
                "AggregateRevenueYoY": aggregate_yoy,
                "MedianMemberRevenueYoY": float(member_yoy.median()) if len(covered) else np.nan,
                "PositiveRevenueBreadth": positive_breadth,
                "AcceleratingRevenueBreadth": accelerating_breadth,
                "RevenueEvidenceState": state,
                "AggregationView": "RAW_STORY_EXPOSURE_NOT_CASH_ADDITIVE",
            }
        )
    return pd.DataFrame(rows)
