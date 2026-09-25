from __future__ import annotations

"""Directional capital lanes and non-directional attention for story groups.

``ETR`` (turnover less day-trade turnover) is attention/liquidity, not cash
inflow.  Direction comes only from separately reported institutional, leverage
or point-in-time ETF holding evidence.  The module never collapses those lanes
into a composite score.
"""

# =============================================================================
# def 00 PARAMETERS — structural windows only
# =============================================================================

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

try:
    from .via_time_utils import def_available_at_utc, def_local_calendar_date
except ImportError:  # standalone import from the engine directory
    from via_time_utils import def_available_at_utc, def_local_calendar_date


ENGINE_ID = "VIA_GROUP_FLOW_EVIDENCE_V0500"
ENGINE_VERSION = "0.5.0"
DEFAULT_WINDOWS = (60, 120, 240)
TSMC_BASE = "2330"
EPS = np.finfo(float).eps

DIRECTIONAL_LANES = (
    "ForeignNetAmount",
    "InvestmentTrustNetAmount",
    "DealerNetAmount",
    "MarginFinancingChangeAmount",
    "ShortSellingChangeAmount",
    "ETFActiveValue",
)

DIRECTIONAL_AVAILABILITY = {
    "ForeignNetAmount": "ForeignNetAmountAvailableAt",
    "InvestmentTrustNetAmount": "InvestmentTrustNetAmountAvailableAt",
    "DealerNetAmount": "DealerNetAmountAvailableAt",
    "MarginBalanceValue": "MarginBalanceValueAvailableAt",
    "ShortBalanceValue": "ShortBalanceValueAvailableAt",
    "ETFActiveValue": "ETFActiveValueAvailableAt",
}

# These are deliberately separate evidence lanes.  In particular, active ETF
# positioning must not be added to domestic institutional trading because the
# investment-trust figures can already contain the ETF manager's executions.
DYNAMIC_DIRECTIONAL_LANES = {
    "FOREIGN": (
        "ForeignNetAmount",
        "ForeignNetAmountAvailableAt",
    ),
    "DOMESTIC_EX_FOREIGN": (
        "InstitutionalDomesticNetAmount",
        "InstitutionalDomesticNetAmountAvailableAt",
    ),
    "ACTIVE_ETF": (
        "ETFActiveValue",
        "ETFActiveValueAvailableAt",
    ),
}

ORDINARY_EQUITY_TYPES = {
    "COMMON_STOCK",
    "COMMON",
    "EQUITY",
    "STOCK",
    "ORDINARY_SHARE",
    "普通股",
}


@dataclass(frozen=True)
class FlowEvidenceConfig:
    windows: tuple[int, ...] = DEFAULT_WINDOWS
    tsmc_ticker: str = TSMC_BASE


# =============================================================================
# def 01 NORMALIZATION
# =============================================================================


def def_ticker_base(value: object) -> str:
    text = str(value or "").strip().upper()
    return text.removesuffix(".TW").removesuffix(".TWO")


def def_prepare_stock_flow_panel(
    stock_daily: pd.DataFrame,
    config: FlowEvidenceConfig = FlowEvidenceConfig(),
) -> pd.DataFrame:
    """Validate ETR and derive directional lanes without filling missing data."""

    frame = stock_daily.copy()
    alias_map = {
        "Market": "Exchange",
        "DayTradeTurnover": "DayTradeTurnoverValue",
        "TradingValue": "TurnoverValue",
    }
    for source, target in alias_map.items():
        if target not in frame.columns and source in frame.columns:
            frame[target] = frame[source]

    required = {"Date", "Ticker", "TurnoverValue", "DayTradeTurnoverValue"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"stock flow panel missing required columns: {missing}")
    frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce").dt.normalize()
    frame["Ticker"] = frame["Ticker"].map(def_ticker_base)
    if "Exchange" not in frame:
        frame["Exchange"] = "MISSING"
    if "AssetType" not in frame:
        frame["AssetType"] = "EQUITY"
    if "MarketDataAvailableAt" not in frame:
        frame["MarketDataAvailableAt"] = pd.NaT
    frame["MarketDataAvailableAt"] = pd.to_datetime(
        frame["MarketDataAvailableAt"].map(def_available_at_utc),
        errors="coerce",
        utc=True,
    )
    numeric_columns = {
        "TurnoverValue",
        "DayTradeTurnoverValue",
        "Adj_Close",
        "ForeignNetAmount",
        "InvestmentTrustNetAmount",
        "DealerNetAmount",
        "MarginBalanceValue",
        "ShortBalanceValue",
        "ETFActiveValue",
    }
    for column in numeric_columns:
        if column not in frame:
            frame[column] = np.nan
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    for value_column, available_column in DIRECTIONAL_AVAILABILITY.items():
        if available_column not in frame:
            frame[available_column] = pd.NaT
        # ``utc=True`` is deliberate even when an entire lane is missing.  An
        # all-NaT series otherwise becomes timezone-naive and cannot safely be
        # combined with populated UTC evidence lanes in a row-wise maximum.
        frame[available_column] = pd.to_datetime(
            frame[available_column].map(def_available_at_utc),
            errors="coerce",
            utc=True,
        )
        missing_timestamp = frame[value_column].notna() & frame[available_column].isna()
        frame.loc[missing_timestamp, value_column] = np.nan
        frame[f"{value_column}TimeStatus"] = np.where(
            missing_timestamp,
            "HOLD_VALUE_WITHOUT_AVAILABLE_AT",
            np.where(
                frame[value_column].notna(),
                "PASS_POINT_IN_TIME",
                "MISSING_VALUE",
            ),
        )
    invalid_key = frame["Date"].isna() | frame["Ticker"].eq("")
    if invalid_key.any():
        raise ValueError(f"stock flow panel has {int(invalid_key.sum())} invalid keys")
    duplicate = frame.duplicated(["Date", "Ticker"], keep=False)
    if duplicate.any():
        raise ValueError(f"stock flow panel has {int(duplicate.sum())} duplicate Date+Ticker rows")
    invalid_etr = (
        frame["TurnoverValue"].lt(0)
        | frame["DayTradeTurnoverValue"].lt(0)
        | frame["DayTradeTurnoverValue"].gt(frame["TurnoverValue"])
    )
    frame["ETR"] = frame["TurnoverValue"] - frame["DayTradeTurnoverValue"]
    frame.loc[invalid_etr, "ETR"] = np.nan
    frame["ETRStatus"] = np.select(
        [invalid_etr, frame[["TurnoverValue", "DayTradeTurnoverValue"]].isna().any(axis=1)],
        ["BLOCKED_INVALID_DAYTRADE", "MISSING_TURNOVER_OR_DAYTRADE"],
        default="PASS",
    )
    frame["IsTSMC"] = frame["Ticker"].eq(def_ticker_base(config.tsmc_ticker))
    frame["IsEligibleEquity"] = (
        frame["AssetType"].fillna("").astype(str).str.upper().isin(ORDINARY_EQUITY_TYPES)
    )

    frame = frame.sort_values(["Ticker", "Date"]).reset_index(drop=True)
    frame["MarginFinancingChangeAmount"] = frame.groupby("Ticker", sort=False)["MarginBalanceValue"].diff()
    # An increase in short balance is directional selling pressure, hence negative.
    frame["ShortSellingChangeAmount"] = -frame.groupby("Ticker", sort=False)["ShortBalanceValue"].diff()
    frame["InstitutionalAllNetAmount"] = frame[
        ["ForeignNetAmount", "InvestmentTrustNetAmount", "DealerNetAmount"]
    ].sum(axis=1, min_count=3)
    frame["InstitutionalDomesticNetAmount"] = frame[
        ["InvestmentTrustNetAmount", "DealerNetAmount"]
    ].sum(axis=1, min_count=2)
    frame["InstitutionalDomesticNetAmountAvailableAt"] = frame[
        [
            DIRECTIONAL_AVAILABILITY["InvestmentTrustNetAmount"],
            DIRECTIONAL_AVAILABILITY["DealerNetAmount"],
        ]
    ].max(axis=1)
    frame["InstitutionalAllNetAmountAvailableAt"] = frame[
        [
            DIRECTIONAL_AVAILABILITY["ForeignNetAmount"],
            DIRECTIONAL_AVAILABILITY["InvestmentTrustNetAmount"],
            DIRECTIONAL_AVAILABILITY["DealerNetAmount"],
        ]
    ].max(axis=1)
    frame["MarginFinancingChangeAmountAvailableAt"] = frame[
        DIRECTIONAL_AVAILABILITY["MarginBalanceValue"]
    ]
    frame["ShortSellingChangeAmountAvailableAt"] = frame[
        DIRECTIONAL_AVAILABILITY["ShortBalanceValue"]
    ]
    frame["DomesticOverlapNote"] = "INVESTMENT_TRUST_INCLUDES_ACTIVE_ETF_TRADING_DO_NOT_ADD_ETF_AGAIN"
    limit_up_known = (
        frame["IsLimitUpLocked"].notna()
        if "IsLimitUpLocked" in frame
        else pd.Series(False, index=frame.index)
    )
    limit_down_known = (
        frame["IsLimitDownLocked"].notna()
        if "IsLimitDownLocked" in frame
        else pd.Series(False, index=frame.index)
    )
    if "IsLimitUpLocked" not in frame:
        frame["IsLimitUpLocked"] = False
    if "IsLimitDownLocked" not in frame:
        frame["IsLimitDownLocked"] = False
    frame["IsLimitUpLocked"] = frame["IsLimitUpLocked"].fillna(False).astype(bool)
    frame["IsLimitDownLocked"] = frame["IsLimitDownLocked"].fillna(False).astype(bool)
    frame["LimitLockDataStatus"] = np.where(
        limit_up_known & limit_down_known,
        "PASS_LIMIT_LOCK_FLAGS",
        "HOLD_LIMIT_LOCK_STATUS_UNKNOWN",
    )
    frame["PriorSessionETR"] = frame.groupby("Ticker", sort=False)["ETR"].shift(1)
    frame["AttentionETR"] = frame["ETR"]
    protected = (
        frame["IsLimitUpLocked"]
        & frame["ETRStatus"].eq("PASS")
        & frame["PriorSessionETR"].notna()
    )
    frame.loc[protected, "AttentionETR"] = np.maximum(
        frame.loc[protected, "ETR"],
        frame.loc[protected, "PriorSessionETR"],
    )
    frame["LimitLockAttentionPolicy"] = np.where(
        protected,
        "LIMIT_UP_USES_MAX_CURRENT_OR_PRIOR_SESSION_ETR",
        "CURRENT_SESSION_ETR",
    )
    return frame


def def_validate_full_market_coverage(prepared: pd.DataFrame) -> pd.DataFrame:
    """Daily fail-closed TWSE+TPEX denominator audit."""

    rows: list[dict[str, object]] = []
    eligible = prepared.loc[prepared["IsEligibleEquity"]]
    for date, day in eligible.groupby("Date", sort=True):
        exchanges = set(day["Exchange"].astype(str).str.upper())
        tsmc = day.loc[day["IsTSMC"]]
        complete = exchanges.issuperset({"TWSE", "TPEX"}) and len(tsmc) == 1
        valid_etr = day["ETRStatus"].eq("PASS")
        denominator = (
            day.loc[valid_etr & ~day["IsTSMC"], "AttentionETR"].sum(min_count=1)
            if complete and valid_etr.all()
            else np.nan
        )
        if not complete:
            status = "BLOCKED_REQUIRES_TWSE_TPEX_AND_ONE_TSMC"
        elif not valid_etr.all():
            status = "BLOCKED_PARTIAL_STOCK_ETR_COVERAGE"
        elif not np.isfinite(denominator) or denominator <= 0:
            status = "BLOCKED_NONPOSITIVE_ETR_DENOMINATOR"
        else:
            status = "PASS"
        rows.append(
            {
                "Date": date,
                "MarketETRExTSMC": denominator,
                "TWSEPresent": "TWSE" in exchanges,
                "TPEXPresent": "TPEX" in exchanges,
                "TSMCRowCount": len(tsmc),
                "EligibleEquityCount": int(day["Ticker"].nunique()),
                "ValidETRCount": int(valid_etr.sum()),
                "MarketAttentionAvailableAt": day.loc[
                    valid_etr, "MarketDataAvailableAt"
                ].max(),
                "CoverageStatus": status,
            }
        )
    return pd.DataFrame(rows)


# =============================================================================
# def 02 MULTI-LABEL GROUP AGGREGATION
# =============================================================================


def def_prepare_active_membership(membership: pd.DataFrame, date: pd.Timestamp) -> pd.DataFrame:
    if "EventType" in membership.columns:
        raise ValueError(
            "raw membership events cannot enter group flow; materialize PIT history first"
        )
    required = {"GroupId", "Ticker"}
    missing = sorted(required.difference(membership.columns))
    if missing:
        raise ValueError(f"membership missing required columns: {missing}")
    frame = membership.copy()
    frame["Ticker"] = frame["Ticker"].map(def_ticker_base)
    if "GroupName" not in frame:
        frame["GroupName"] = frame["GroupId"]
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
    active = (
        (frame["ValidFrom"].isna() | frame["ValidFrom"].le(date))
        & (frame["ValidTo"].isna() | frame["ValidTo"].ge(date))
        & frame["Decision"].astype(str).str.upper().eq("APPROVED")
    )
    return frame.loc[active].drop_duplicates(["GroupId", "Ticker"], keep="last")


def def_compute_group_flow_daily(
    prepared: pd.DataFrame,
    membership: pd.DataFrame,
) -> pd.DataFrame:
    """Return the full story-exposure view for each group and day.

    Because one ticker may belong to several story groups, rows are not cash
    additive across groups.  A separate conserved allocation is built by the
    transfer-matrix module.
    """

    if "AsOfDate" in membership.columns and "HistoryViewStatus" not in membership.columns:
        snapshot_dates = pd.to_datetime(membership["AsOfDate"], errors="coerce").dt.normalize().dropna().unique()
        market_dates = pd.to_datetime(prepared["Date"], errors="coerce").dt.normalize().dropna().unique()
        if len(snapshot_dates) != 1 or any(date != snapshot_dates[0] for date in market_dates):
            raise ValueError(
                "an as-of membership snapshot cannot be replayed across history; "
                "use def_materialize_membership_history"
            )
    coverage = def_validate_full_market_coverage(prepared)
    rows: list[dict[str, object]] = []
    for date, day in prepared.groupby("Date", sort=True):
        active = def_prepare_active_membership(membership, pd.Timestamp(date))
        if active.empty:
            continue
        merged = active.merge(day, on="Ticker", how="left", validate="many_to_one")
        denominator_row = coverage.loc[coverage["Date"].eq(date)]
        denominator = (
            float(denominator_row["MarketETRExTSMC"].iloc[0]) if not denominator_row.empty else np.nan
        )
        denominator_status = (
            str(denominator_row["CoverageStatus"].iloc[0]) if not denominator_row.empty else "BLOCKED_NO_MARKET_AUDIT"
        )
        for group_id, group in merged.groupby("GroupId", sort=True):
            # Determine the anchor from the relationship key as well as the
            # market row.  A missing 2330 observation must not be mistaken for
            # an ordinary comparison member after the left join.
            is_tsmc = group["Ticker"].astype(str).eq(TSMC_BASE)
            comparison_group = group.loc[~is_tsmc].copy()
            anchor_group = group.loc[is_tsmc].copy()
            limit_up_locked = comparison_group["IsLimitUpLocked"].eq(True)
            limit_down_locked = comparison_group["IsLimitDownLocked"].eq(True)
            valid = comparison_group.loc[comparison_group["ETRStatus"].eq("PASS")]
            member_count = int(group["Ticker"].nunique())
            comparison_member_count = int(comparison_group["Ticker"].nunique())
            observed_count = int(comparison_group["Date"].notna().sum())
            covered_count = int(valid["Ticker"].nunique())
            group_complete = (
                comparison_member_count > 0
                and observed_count == comparison_member_count
                and covered_count == comparison_member_count
            )
            raw_group_etr = valid["ETR"].sum(min_count=1)
            group_etr = valid["AttentionETR"].sum(min_count=1)
            anchor_valid = anchor_group.loc[anchor_group["ETRStatus"].eq("PASS")]
            anchor_raw_etr = anchor_valid["ETR"].sum(min_count=1)
            anchor_attention_etr = anchor_valid["AttentionETR"].sum(min_count=1)
            if not group_complete:
                raw_group_etr = np.nan
                group_etr = np.nan
            record: dict[str, object] = {
                "Date": date,
                "GroupId": group_id,
                "GroupName": group["GroupName"].iloc[0],
                "MemberCount": member_count,
                "ComparisonMemberCountExTSMC": comparison_member_count,
                "TSMCAnchorMemberCount": int(anchor_group["Ticker"].nunique()),
                "TSMCAnchorETRCoveredMemberCount": int(
                    anchor_valid["Ticker"].nunique()
                ),
                "TSMCAnchorRawETR": anchor_raw_etr,
                "TSMCAnchorAttentionETR": anchor_attention_etr,
                "ObservedMemberCount": observed_count,
                "ETRCoveredMemberCount": covered_count,
                "GroupCoverageStatus": (
                    "PASS" if group_complete else "HOLD_PARTIAL_GROUP_MEMBER_COVERAGE"
                ),
                "RawGroupETR": raw_group_etr,
                "GroupETR": group_etr,
                "MarketETRExTSMC": denominator,
                "AttentionShare": group_etr / denominator if np.isfinite(group_etr) and np.isfinite(denominator) and denominator > 0 else np.nan,
                "AttentionDirection": "NON_DIRECTIONAL",
                "MarketCoverageStatus": denominator_status,
                "AttentionAvailableAt": (
                    denominator_row["MarketAttentionAvailableAt"].iloc[0]
                    if not denominator_row.empty
                    else pd.NaT
                ),
                "LimitUpLockedCount": int(limit_up_locked.sum()),
                "LimitUpProtectedMemberCount": int(
                    comparison_group["LimitLockAttentionPolicy"]
                    .eq("LIMIT_UP_USES_MAX_CURRENT_OR_PRIOR_SESSION_ETR")
                    .sum()
                ),
                "LimitDownLockedCount": int(limit_down_locked.sum()),
                "LimitLockUnknownCount": int(
                    comparison_group["LimitLockDataStatus"]
                    .ne("PASS_LIMIT_LOCK_FLAGS")
                    .sum()
                ),
                "TSMCAnchorLimitUpLockedCount": int(
                    anchor_group["IsLimitUpLocked"].eq(True).sum()
                ),
                "TSMCAnchorLimitDownLockedCount": int(
                    anchor_group["IsLimitDownLocked"].eq(True).sum()
                ),
                "AggregationView": "RAW_STORY_EXPOSURE_NOT_CASH_ADDITIVE",
                "TSMCPolicy": "SEPARATE_ANCHOR_EXCLUDED_FROM_CROSS_GROUP_COMPARISON",
            }
            lane_columns = [
                "ForeignNetAmount",
                "InvestmentTrustNetAmount",
                "DealerNetAmount",
                "InstitutionalAllNetAmount",
                "InstitutionalDomesticNetAmount",
                "MarginFinancingChangeAmount",
                "ShortSellingChangeAmount",
                "ETFActiveValue",
            ]
            for lane in lane_columns:
                values = pd.to_numeric(comparison_group[lane], errors="coerce")
                record[lane] = values.sum(min_count=1)
                record[f"{lane}PositiveBreadth"] = float(values.gt(0).sum() / values.notna().sum()) if values.notna().any() else np.nan
                record[f"{lane}Coverage"] = int(values.notna().sum())
                available_column = f"{lane}AvailableAt"
                record[available_column] = (
                    comparison_group.loc[values.notna(), available_column].max()
                    if available_column in comparison_group.columns and values.notna().any()
                    else pd.NaT
                )
                anchor_values = pd.to_numeric(anchor_group[lane], errors="coerce")
                record[f"TSMCAnchor_{lane}"] = anchor_values.sum(min_count=1)
                record[f"TSMCAnchor_{lane}AvailableAt"] = (
                    anchor_group.loc[anchor_values.notna(), available_column].max()
                    if available_column in anchor_group.columns and anchor_values.notna().any()
                    else pd.NaT
                )
            rows.append(record)
    return pd.DataFrame(rows).sort_values(["GroupId", "Date"]).reset_index(drop=True) if rows else pd.DataFrame()


# =============================================================================
# def 03 DYNAMIC EVIDENCE STATES — no weighted score
# =============================================================================


def def_trailing_relative_state(series: pd.Series, window: int) -> pd.Series:
    """Compare each observation with its strictly prior rolling distribution."""

    minimum = max(2, int(np.sqrt(window)))
    prior_median = series.shift(1).rolling(window, min_periods=minimum).median()
    delta = series - prior_median
    return pd.Series(
        np.select(
            [delta.gt(0), delta.lt(0), delta.eq(0) & prior_median.notna()],
            ["ABOVE_PRIOR_MEDIAN", "BELOW_PRIOR_MEDIAN", "AT_PRIOR_MEDIAN"],
            default="HOLD_INSUFFICIENT_HISTORY",
        ),
        index=series.index,
        dtype="object",
    )


def def_add_dynamic_flow_states(
    group_daily: pd.DataFrame,
    group_price: pd.DataFrame | None = None,
    config: FlowEvidenceConfig = FlowEvidenceConfig(),
    trading_calendar: Iterable[object] | pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Add dynamic states without synthesizing independent capital lanes.

    The result is long by ``DirectionalLane``.  The compatibility columns
    ``EarlyPositioningState_*`` and ``EarlyExitState_*`` therefore describe
    exactly one directional lane on each row; they never represent an
    ``any``/vote/weighted combination of foreign, domestic and active-ETF
    evidence.

    A formal ``trading_calendar`` is required before a state can become
    actionable.  Omitting it remains API-compatible but fails closed instead
    of treating the set of observed rows as proof of the next tradable day.
    """

    if group_daily.empty:
        return group_daily.copy()
    frame = group_daily.copy()
    frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce").dt.normalize()
    required = {"Date", "GroupId"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"group flow daily missing required columns: {missing}")
    invalid_keys = frame["Date"].isna() | frame["GroupId"].isna()
    if invalid_keys.any():
        raise ValueError(f"group flow daily has {int(invalid_keys.sum())} invalid keys")
    duplicate_keys = frame.duplicated(["Date", "GroupId"], keep=False)
    if duplicate_keys.any():
        raise ValueError(
            "group flow daily must contain one row per Date+GroupId before "
            "directional-lane expansion"
        )

    price_status_column: str | None = None
    price_time_column: str | None = None
    if group_price is not None and not group_price.empty:
        price = group_price.copy()
        price["Date"] = pd.to_datetime(price["Date"], errors="coerce").dt.normalize()
        price_column = next(
            (column for column in ("GroupReturn", "GPI_HIER_Return", "GPI_ETR_Return", "Return") if column in price),
            None,
        )
        if price_column:
            price_status_column = next(
                (
                    column
                    for column in ("IndexStatus", "GroupPriceStatus", "PriceStatus")
                    if column in price
                ),
                None,
            )
            price_time_column = next(
                (
                    column
                    for column in (
                        "GroupPriceReturnAvailableAt",
                        "IndexAvailableAt",
                        "AvailableAt",
                        "MarketDataAvailableAt",
                    )
                    if column in price
                ),
                None,
            )
            selected = ["Date", "GroupId", price_column]
            selected.extend(
                column
                for column in (price_status_column, price_time_column)
                if column is not None and column not in selected
            )
            price = price[selected].copy()
            duplicate_price = price.duplicated(["Date", "GroupId"], keep=False)
            if duplicate_price.any():
                raise ValueError(
                    "group price must contain one index method per Date+GroupId"
                )
            rename = {price_column: "GroupPriceReturn"}
            if price_status_column is not None:
                rename[price_status_column] = "GroupPriceIndexStatus"
            if price_time_column is not None:
                rename[price_time_column] = "GroupPriceReturnAvailableAt"
            price = price.rename(columns=rename)
            frame = frame.drop(
                columns=[
                    column
                    for column in (
                        "GroupPriceReturn",
                        "GroupPriceIndexStatus",
                        "GroupPriceReturnAvailableAt",
                    )
                    if column in frame
                ]
            )
            frame = frame.merge(
                price,
                on=["Date", "GroupId"],
                how="left",
                validate="one_to_one",
            )
    if "GroupPriceReturn" not in frame:
        frame["GroupPriceReturn"] = np.nan
    if "GroupPriceIndexStatus" not in frame:
        frame["GroupPriceIndexStatus"] = "UNSPECIFIED_PRICE_STATUS"
    if "AttentionAvailableAt" not in frame:
        frame["AttentionAvailableAt"] = pd.NaT
    frame["AttentionAvailableAt"] = pd.to_datetime(
        frame["AttentionAvailableAt"], errors="coerce", utc=True
    )
    if "GroupPriceReturnAvailableAt" not in frame:
        # The group index and AttentionShare both originate from the same
        # point-in-time closing market panel in this pipeline.  Until the index
        # module carries its own timestamp, retain this explicit provenance
        # rather than silently omitting price timing.
        frame["GroupPriceReturnAvailableAt"] = frame["AttentionAvailableAt"]
        frame["GroupPriceTimeProvenance"] = (
            "DERIVED_FROM_SAME_MARKET_PANEL_AS_ATTENTION"
        )
    else:
        frame["GroupPriceReturnAvailableAt"] = pd.to_datetime(
            frame["GroupPriceReturnAvailableAt"], errors="coerce", utc=True
        )
        frame["GroupPriceTimeProvenance"] = "SUPPLIED_PRICE_EVIDENCE_TIME"

    state_columns = [
        "AttentionShare",
        "ForeignNetAmount",
        "InstitutionalDomesticNetAmount",
        "InvestmentTrustNetAmount",
        "DealerNetAmount",
        "MarginFinancingChangeAmount",
        "ShortSellingChangeAmount",
        "ETFActiveValue",
        "GroupPriceReturn",
    ]
    for column in state_columns:
        if column not in frame:
            frame[column] = np.nan
        frame[column] = pd.to_numeric(frame[column], errors="coerce")

    state_output: list[pd.DataFrame] = []
    for _, group in frame.groupby("GroupId", sort=True):
        group = group.sort_values("Date").copy()
        for window in config.windows:
            for column in state_columns:
                group[f"{column}State_{window}D"] = def_trailing_relative_state(group[column], window)
        state_output.append(group)
    base = pd.concat(state_output, ignore_index=True, sort=False)

    formal_calendar = trading_calendar is not None
    if isinstance(trading_calendar, pd.DataFrame):
        if "Date" not in trading_calendar:
            raise ValueError("trading_calendar DataFrame requires Date")
        calendar_values: Iterable[object] = trading_calendar["Date"].tolist()
    elif trading_calendar is None:
        calendar_values = base["Date"].tolist()
    else:
        calendar_values = trading_calendar
    calendar = pd.DatetimeIndex(
        sorted(
            {
                pd.Timestamp(local_date)
                for value in calendar_values
                if pd.notna(local_date := def_local_calendar_date(value))
            }
        )
    )
    if calendar.empty:
        raise ValueError("trading_calendar contains no valid sessions")
    if formal_calendar:
        unknown_observation_dates = set(base["Date"].dropna()).difference(calendar)
        if unknown_observation_dates:
            raise ValueError(
                "formal trading_calendar is missing group observation dates"
            )

    lane_output: list[pd.DataFrame] = []
    for lane_name, (value_column, available_column) in DYNAMIC_DIRECTIONAL_LANES.items():
        lane = base.copy()
        lane["DirectionalLane"] = lane_name
        lane["DirectionalValueColumn"] = value_column
        lane["DirectionalAvailableAtColumn"] = available_column
        lane["DirectionalAmount"] = pd.to_numeric(lane[value_column], errors="coerce")
        if available_column not in lane:
            lane[available_column] = pd.NaT
        lane["DirectionalAmountAvailableAt"] = pd.to_datetime(
            lane[available_column], errors="coerce", utc=True
        )

        coverage_column = f"{value_column}Coverage"
        lane["DirectionalCoverage"] = (
            pd.to_numeric(lane[coverage_column], errors="coerce")
            if coverage_column in lane
            else np.nan
        )
        expected_coverage = (
            pd.to_numeric(lane["ComparisonMemberCountExTSMC"], errors="coerce")
            if "ComparisonMemberCountExTSMC" in lane
            else pd.Series(np.nan, index=lane.index, dtype=float)
        )
        group_coverage_pass = (
            lane["GroupCoverageStatus"].eq("PASS")
            if "GroupCoverageStatus" in lane
            else pd.Series(False, index=lane.index)
        )
        market_coverage_pass = (
            lane["MarketCoverageStatus"].eq("PASS")
            if "MarketCoverageStatus" in lane
            else pd.Series(False, index=lane.index)
        )
        lane["DirectionalCoverageStatus"] = np.select(
            [
                ~group_coverage_pass | ~market_coverage_pass,
                expected_coverage.isna(),
                expected_coverage.le(0),
                lane["DirectionalCoverage"].isna(),
                lane["DirectionalCoverage"].ne(expected_coverage),
                lane["DirectionalAmount"].isna(),
                lane["DirectionalAmountAvailableAt"].isna(),
            ],
            [
                "HOLD_GROUP_OR_MARKET_COVERAGE_INCOMPLETE",
                "HOLD_EXPECTED_DIRECTIONAL_COVERAGE_UNKNOWN",
                "HOLD_NO_EX_TSMC_COMPARISON_MEMBER",
                "HOLD_DIRECTIONAL_COVERAGE_UNKNOWN",
                "HOLD_PARTIAL_DIRECTIONAL_LANE_COVERAGE",
                "HOLD_DIRECTIONAL_VALUE_MISSING",
                "HOLD_DIRECTIONAL_AVAILABLE_AT_MISSING",
            ],
            default="PASS_COMPLETE_DIRECTIONAL_LANE",
        )
        lane["AttentionEvidenceStatus"] = np.select(
            [
                ~group_coverage_pass | ~market_coverage_pass,
                lane["AttentionShare"].isna(),
                lane["AttentionAvailableAt"].isna(),
            ],
            [
                "HOLD_GROUP_OR_MARKET_COVERAGE_INCOMPLETE",
                "HOLD_ATTENTION_VALUE_MISSING",
                "HOLD_ATTENTION_AVAILABLE_AT_MISSING",
            ],
            default="PASS_COMPLETE_ATTENTION_EVIDENCE",
        )
        valid_price_status = lane["GroupPriceIndexStatus"].isin(
            ["PASS", "UNSPECIFIED_PRICE_STATUS"]
        )
        lane["PriceEvidenceStatus"] = np.select(
            [
                lane["GroupPriceReturn"].isna(),
                ~valid_price_status,
                lane["GroupPriceReturnAvailableAt"].isna(),
            ],
            [
                "HOLD_PRICE_VALUE_MISSING",
                "HOLD_PRICE_INDEX_STATUS_NOT_PASS",
                "HOLD_PRICE_AVAILABLE_AT_MISSING",
            ],
            default="PASS_COMPLETE_PRICE_EVIDENCE",
        )
        complete_point_in_time = (
            lane["DirectionalCoverageStatus"].eq("PASS_COMPLETE_DIRECTIONAL_LANE")
            & lane["AttentionEvidenceStatus"].eq("PASS_COMPLETE_ATTENTION_EVIDENCE")
            & lane["PriceEvidenceStatus"].eq("PASS_COMPLETE_PRICE_EVIDENCE")
        )
        evidence_times = lane[
            [
                "AttentionAvailableAt",
                "DirectionalAmountAvailableAt",
                "GroupPriceReturnAvailableAt",
            ]
        ]
        lane["SignalAvailableAt"] = evidence_times.max(axis=1).where(
            complete_point_in_time, pd.NaT
        )

        def next_session(row: pd.Series) -> pd.Timestamp | pd.NaT:
            if not formal_calendar or pd.isna(row["SignalAvailableAt"]):
                return pd.NaT
            available_local_date = def_local_calendar_date(row["SignalAvailableAt"])
            boundary = max(pd.Timestamp(row["Date"]), available_local_date)
            later = calendar[calendar > boundary]
            return pd.Timestamp(later[0]) if len(later) else pd.NaT

        lane["EffectiveDate"] = lane.apply(next_session, axis=1)
        formal_calendar_missing = pd.Series(
            not formal_calendar, index=lane.index, dtype=bool
        )
        lane["SignalTimingStatus"] = np.select(
            [
                formal_calendar_missing,
                ~complete_point_in_time,
                lane["EffectiveDate"].isna(),
            ],
            [
                "HOLD_FORMAL_TRADING_CALENDAR_REQUIRED",
                "HOLD_INCOMPLETE_POINT_IN_TIME_EVIDENCE",
                "HOLD_NEXT_TRADABLE_SESSION_UNAVAILABLE",
            ],
            default="PASS_NEXT_TRADABLE_SESSION_AFTER_LATEST_EVIDENCE",
        )
        lane["TradingCalendarStatus"] = (
            "PASS_FORMAL_TRADING_CALENDAR_SUPPLIED"
            if formal_calendar
            else "HOLD_OBSERVED_DATES_ARE_NOT_A_TRADING_CALENDAR"
        )

        lock_up = (
            lane["LimitUpLockedCount"].gt(0)
            if "LimitUpLockedCount" in lane
            else pd.Series(False, index=lane.index)
        )
        limit_status_unknown = (
            lane["LimitLockUnknownCount"].gt(0)
            if "LimitLockUnknownCount" in lane
            else pd.Series(True, index=lane.index)
        )
        for window in config.windows:
            attention_state = lane[f"AttentionShareState_{window}D"]
            direction_state = lane[f"{value_column}State_{window}D"]
            price_state = lane[f"GroupPriceReturnState_{window}D"]
            history_complete = (
                ~attention_state.eq("HOLD_INSUFFICIENT_HISTORY")
                & ~direction_state.eq("HOLD_INSUFFICIENT_HISTORY")
                & ~price_state.eq("HOLD_INSUFFICIENT_HISTORY")
            )
            evidence_complete = (
                complete_point_in_time
                & history_complete
                & lane["SignalTimingStatus"].eq(
                    "PASS_NEXT_TRADABLE_SESSION_AFTER_LATEST_EVIDENCE"
                )
            )
            direction_up = (
                direction_state.eq("ABOVE_PRIOR_MEDIAN")
                & lane["DirectionalAmount"].gt(0)
            )
            direction_down = (
                direction_state.eq("BELOW_PRIOR_MEDIAN")
                & lane["DirectionalAmount"].lt(0)
            )
            # Explicit finite price states are essential.  Negating price-up
            # or price-down would also classify missing/insufficient evidence.
            price_pullback_or_sideways = price_state.isin(
                ["BELOW_PRIOR_MEDIAN", "AT_PRIOR_MEDIAN"]
            )
            price_rising_or_sideways = price_state.isin(
                ["ABOVE_PRIOR_MEDIAN", "AT_PRIOR_MEDIAN"]
            )
            attention_up = attention_state.eq("ABOVE_PRIOR_MEDIAN")
            attention_down = attention_state.eq("BELOW_PRIOR_MEDIAN")

            lane[f"SignalEvidenceStatus_{window}D"] = np.select(
                [
                    ~complete_point_in_time,
                    ~history_complete,
                    ~lane["SignalTimingStatus"].eq(
                        "PASS_NEXT_TRADABLE_SESSION_AFTER_LATEST_EVIDENCE"
                    ),
                ],
                [
                    "HOLD_INCOMPLETE_POINT_IN_TIME_EVIDENCE",
                    "HOLD_INSUFFICIENT_ROLLING_HISTORY",
                    "HOLD_SIGNAL_TIMING_INCOMPLETE",
                ],
                default="PASS_LANE_EVIDENCE",
            )
            lane[f"EarlyPositioningState_{window}D"] = np.select(
                [
                    ~complete_point_in_time,
                    ~history_complete,
                    ~lane["SignalTimingStatus"].eq(
                        "PASS_NEXT_TRADABLE_SESSION_AFTER_LATEST_EVIDENCE"
                    ),
                    attention_up & direction_up & price_pullback_or_sideways,
                    attention_up & ~direction_up,
                ],
                [
                    "HOLD_INCOMPLETE_POINT_IN_TIME_EVIDENCE",
                    "HOLD_INSUFFICIENT_ROLLING_HISTORY",
                    "HOLD_SIGNAL_TIMING_INCOMPLETE",
                    "DIRECTIONAL_ACCUMULATION_WATCH",
                    "ATTENTION_EXPANSION_ONLY",
                ],
                default="NO_EARLY_POSITIONING_EVIDENCE",
            )
            exit_condition = (
                attention_down & direction_down & price_rising_or_sideways
            )
            lane[f"EarlyExitState_{window}D"] = np.select(
                [
                    ~complete_point_in_time,
                    ~history_complete,
                    ~lane["SignalTimingStatus"].eq(
                        "PASS_NEXT_TRADABLE_SESSION_AFTER_LATEST_EVIDENCE"
                    ),
                    limit_status_unknown,
                    exit_condition,
                    lock_up,
                ],
                [
                    "HOLD_INCOMPLETE_POINT_IN_TIME_EVIDENCE",
                    "HOLD_INSUFFICIENT_ROLLING_HISTORY",
                    "HOLD_SIGNAL_TIMING_INCOMPLETE",
                    "HOLD_LIMIT_STATUS_UNKNOWN",
                    "EARLY_EXIT_RISK",
                    "LIMIT_UP_ATTENTION_PROTECTED",
                ],
                default="NO_EARLY_EXIT_EVIDENCE",
            )
            # Guard the compatibility columns against future predicate edits.
            actionable = lane[f"EarlyPositioningState_{window}D"].eq(
                "DIRECTIONAL_ACCUMULATION_WATCH"
            ) | lane[f"EarlyExitState_{window}D"].eq("EARLY_EXIT_RISK")
            if (actionable & ~evidence_complete).any():
                raise AssertionError(
                    "actionable group-flow state escaped the lane evidence gate"
                )
        lane_output.append(lane)

    result = pd.concat(lane_output, ignore_index=True, sort=False)
    result["DecisionAggregationPolicy"] = (
        "SEPARATE_DIRECTIONAL_LANE_ROWS_NO_CROSS_LANE_ANY_OR_VOTE"
    )
    result["DomesticOverlapNote"] = (
        "DOMESTIC_EX_FOREIGN_AND_ACTIVE_ETF_ARE_SEPARATE_NON_ADDITIVE_LANES"
    )
    return result.sort_values(
        ["GroupId", "Date", "DirectionalLane"], kind="stable"
    ).reset_index(drop=True)
