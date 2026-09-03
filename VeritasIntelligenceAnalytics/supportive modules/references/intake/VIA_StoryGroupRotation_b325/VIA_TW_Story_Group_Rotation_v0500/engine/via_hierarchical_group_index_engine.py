from __future__ import annotations

"""Point-in-time price indices for overlapping Taiwan story groups.

The module publishes three parallel indices and deliberately does not combine
them into a score:

``GI_EW``
    Equal-weight breadth/audit benchmark.
``GI_HIER``
    L3 story branch -> market-cap bucket -> constituent hierarchy.  Roles are
    outputs of group validation and never enter the weight formula.
``GI_ETR``
    Non-day-trade turnover (ETR) attention-weighted price index.  ETR is
    attention/liquidity, not directional cash inflow.

Every return on session ``t`` uses weights calculated on the immediately prior
session.  Missing member data blocks the affected method rather than silently
changing the constituent set.
"""

from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np
import pandas as pd


# =============================================================================
# def 00 PARAMETERS -- structural/governance controls only
# =============================================================================

ENGINE_ID = "VIA_HIERARCHICAL_GROUP_INDEX_ENGINE"
ENGINE_VERSION = "0.5.0"
INDEX_METHODS = ("GI_EW", "GI_HIER", "GI_ETR")
INDEX_BASE_LEVEL = 100.0
TSMC_BASE = "2330"
APPROVED_DECISIONS = ("APPROVED", "ACTIVE", "KEEP")
SIZE_BUCKET_ORDER = ("LARGE", "MID", "SMALL")
SIZE_LOWER_QUANTILE = 0.60
SIZE_UPPER_QUANTILE = 0.90
DYNAMIC_TRUNCATE_LOWER_QUANTILE = 0.05
DYNAMIC_TRUNCATE_UPPER_QUANTILE = 0.95
MINIMUM_TRUNCATE_CROSS_SECTION = 4
WEIGHT_SUM_TOLERANCE = 1.0e-10
EPS = np.finfo(float).eps


@dataclass(frozen=True)
class HierarchicalIndexConfig:
    price_column: str = "Adj_Close"
    free_float_cap_column: str = "FreeFloatMarketCap"
    fallback_cap_column: str = "MarketCap"
    etr_column: str = "ETR"
    lower_size_quantile: float = SIZE_LOWER_QUANTILE
    upper_size_quantile: float = SIZE_UPPER_QUANTILE
    truncate_lower_quantile: float = DYNAMIC_TRUNCATE_LOWER_QUANTILE
    truncate_upper_quantile: float = DYNAMIC_TRUNCATE_UPPER_QUANTILE
    minimum_truncate_cross_section: int = MINIMUM_TRUNCATE_CROSS_SECTION
    size_history_window_days: int = 240
    require_pit_size_history: bool = False
    exclude_tsmc_from_primary: bool = True
    tsmc_ticker: str = TSMC_BASE
    base_level: float = INDEX_BASE_LEVEL


# =============================================================================
# def 01 NORMALIZATION / INPUT CONTRACTS
# =============================================================================


def def_ticker_base(value: Any) -> str:
    text = str(value or "").strip().upper().replace(" ", "")
    return text.removesuffix(".TWO").removesuffix(".TW")


def def_normalize_date(value: Any) -> pd.Timestamp | pd.NaT:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return pd.NaT
    stamp = pd.Timestamp(parsed)
    if stamp.tzinfo is not None:
        stamp = stamp.tz_convert("Asia/Taipei").tz_localize(None)
    return stamp.normalize()


def def_first_existing_column(frame: pd.DataFrame, candidates: Iterable[str]) -> str | None:
    return next((column for column in candidates if column in frame.columns), None)


def def_prepare_index_panel(
    stock_daily: pd.DataFrame,
    config: HierarchicalIndexConfig = HierarchicalIndexConfig(),
) -> pd.DataFrame:
    """Normalize a unique Date+Ticker panel without forward-filling raw data."""

    required = {"Date", "Ticker", config.price_column}
    missing = sorted(required.difference(stock_daily.columns))
    if missing:
        raise ValueError(f"index panel missing required columns: {missing}")
    frame = stock_daily.copy()
    frame["Date"] = frame["Date"].map(def_normalize_date)
    frame["Ticker"] = frame["Ticker"].map(def_ticker_base)
    frame[config.price_column] = pd.to_numeric(frame[config.price_column], errors="coerce")

    invalid_key = frame["Date"].isna() | frame["Ticker"].eq("")
    if invalid_key.any():
        raise ValueError(f"index panel has {int(invalid_key.sum())} invalid Date/Ticker keys")
    duplicate = frame.duplicated(["Date", "Ticker"], keep=False)
    if duplicate.any():
        raise ValueError(f"index panel has {int(duplicate.sum())} duplicate Date+Ticker rows")

    free_float = (
        pd.to_numeric(frame[config.free_float_cap_column], errors="coerce")
        if config.free_float_cap_column in frame.columns
        else pd.Series(np.nan, index=frame.index, dtype=float)
    )
    fallback_cap = (
        pd.to_numeric(frame[config.fallback_cap_column], errors="coerce")
        if config.fallback_cap_column in frame.columns
        else pd.Series(np.nan, index=frame.index, dtype=float)
    )
    frame["IndexCapitalization"] = free_float.combine_first(fallback_cap)
    frame["CapitalizationSource"] = np.select(
        [free_float.notna(), free_float.isna() & fallback_cap.notna()],
        ["FREE_FLOAT_MARKET_CAP", "TOTAL_MARKET_CAP_FALLBACK"],
        default="MISSING",
    )

    if config.etr_column not in frame.columns:
        turnover = def_first_existing_column(frame, ("TurnoverValue", "TradingValue"))
        day_trade = def_first_existing_column(
            frame,
            ("DayTradeTurnover", "DayTradeTurnoverValue", "DayTradeValue"),
        )
        if turnover and day_trade:
            total = pd.to_numeric(frame[turnover], errors="coerce")
            intraday = pd.to_numeric(frame[day_trade], errors="coerce")
            valid = total.ge(0) & intraday.ge(0) & intraday.le(total)
            frame[config.etr_column] = (total - intraday).where(valid)
        else:
            frame[config.etr_column] = np.nan
    frame[config.etr_column] = pd.to_numeric(frame[config.etr_column], errors="coerce")
    frame.loc[frame[config.etr_column].lt(0), config.etr_column] = np.nan

    frame["IsTSMC"] = frame["Ticker"].eq(def_ticker_base(config.tsmc_ticker))
    frame = frame.sort_values(["Ticker", "Date"], kind="stable").reset_index(drop=True)
    frame["StockReturn"] = frame.groupby("Ticker", sort=False)[config.price_column].pct_change(
        fill_method=None
    )
    frame["PriceDataStatus"] = np.where(
        frame[config.price_column].gt(0),
        "PASS",
        "BLOCKED_MISSING_OR_NONPOSITIVE_PRICE",
    )
    frame["ETRDataStatus"] = np.where(
        frame[config.etr_column].notna(),
        "PASS_NON_DIRECTIONAL_ATTENTION",
        "BLOCKED_MISSING_OR_INVALID_ETR",
    )
    return frame.sort_values(["Date", "Ticker"], kind="stable").reset_index(drop=True)


def def_prepare_membership(membership: pd.DataFrame) -> pd.DataFrame:
    """Normalize append-only membership intervals while preserving overlap."""

    if "EventType" in membership.columns:
        raise ValueError(
            "raw membership events cannot enter an index; materialize PIT history first"
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
    l3_column = def_first_existing_column(
        frame,
        ("L3", "StoryL3", "HierarchyL3", "Level3", "SubGroup"),
    )
    frame["L3"] = (
        frame[l3_column].fillna("").astype(str).str.strip()
        if l3_column
        else frame["GroupId"]
    )
    frame.loc[frame["L3"].eq(""), "L3"] = frame.loc[frame["L3"].eq(""), "GroupId"]
    if "ValidFrom" not in frame.columns and "MembershipValidFrom" in frame.columns:
        frame["ValidFrom"] = frame["MembershipValidFrom"]
    if "ValidTo" not in frame.columns and "MembershipValidTo" in frame.columns:
        frame["ValidTo"] = frame["MembershipValidTo"]
    for column in ("ValidFrom", "ValidTo"):
        if column not in frame.columns:
            frame[column] = pd.NaT
        frame[column] = pd.to_datetime(frame[column], errors="coerce").dt.normalize()
    if "Decision" not in frame.columns:
        frame["Decision"] = np.where(
            frame.get("EvidenceStatus", pd.Series("APPROVED", index=frame.index))
            .astype(str)
            .str.upper()
            .str.contains("APPROVED|ACTIVE", regex=True),
            "APPROVED",
            "PENDING",
        )
    frame["Decision"] = frame["Decision"].fillna("").astype(str).str.strip().str.upper()
    invalid = frame["GroupId"].eq("") | frame["Ticker"].eq("")
    if invalid.any():
        raise ValueError(f"membership has {int(invalid.sum())} invalid GroupId/Ticker keys")
    exact_duplicate = frame.duplicated(
        ["GroupId", "Ticker", "ValidFrom", "ValidTo"], keep=False
    )
    if exact_duplicate.any():
        raise ValueError(f"membership has {int(exact_duplicate.sum())} duplicate interval rows")
    frame["RoleWeightPolicy"] = "ROLE_IS_EVIDENCE_NOT_A_WEIGHT_INPUT"
    return frame.sort_values(["GroupId", "Ticker", "ValidFrom"], kind="stable").reset_index(drop=True)


def def_attach_size_bucket_history(
    prepared_panel: pd.DataFrame,
    size_history: pd.DataFrame,
    config: HierarchicalIndexConfig = HierarchicalIndexConfig(),
) -> pd.DataFrame:
    """Backward as-of join the quarterly size history produced by v0.5.

    The size engine already makes each quarterly snapshot effective on a later
    session.  This join never uses a bucket whose EffectiveDate is after the
    index information date.
    """

    required = {"Ticker", "EffectiveDate", "MarketCapTier"}
    missing = sorted(required.difference(size_history.columns))
    if missing:
        raise ValueError(f"size history missing required columns: {missing}")
    history = size_history.copy()
    history["Ticker"] = history["Ticker"].map(def_ticker_base)
    history["EffectiveDate"] = pd.to_datetime(
        history["EffectiveDate"], errors="coerce"
    ).dt.normalize()
    history["MarketCapTier"] = history["MarketCapTier"].astype(str).str.upper()
    if "WindowDays" in history.columns:
        window = pd.to_numeric(history["WindowDays"], errors="coerce")
        history = history.loc[window.eq(config.size_history_window_days)]
    invalid = history["Ticker"].eq("") | history["EffectiveDate"].isna()
    if invalid.any():
        raise ValueError(f"size history has {int(invalid.sum())} invalid keys")
    duplicate = history.duplicated(["Ticker", "EffectiveDate"], keep=False)
    if duplicate.any():
        raise ValueError(f"size history has {int(duplicate.sum())} duplicate effective keys")

    attached: list[pd.DataFrame] = []
    for ticker, panel_ticker in prepared_panel.groupby("Ticker", sort=False):
        left = panel_ticker.sort_values("Date", kind="stable").copy()
        right = history.loc[history["Ticker"].eq(ticker)].sort_values(
            "EffectiveDate", kind="stable"
        )
        if right.empty:
            left["SizeBucket"] = pd.NA
            left["SizeBucketEffectiveDate"] = pd.NaT
            left["SizeBucketSource"] = "HOLD_NO_POINT_IN_TIME_SIZE_HISTORY"
        else:
            selected = right[["EffectiveDate", "MarketCapTier"]].rename(
                columns={"MarketCapTier": "SizeBucket"}
            )
            left = pd.merge_asof(
                left.sort_values("Date"),
                selected.sort_values("EffectiveDate"),
                left_on="Date",
                right_on="EffectiveDate",
                direction="backward",
                allow_exact_matches=True,
            )
            left = left.rename(columns={"EffectiveDate": "SizeBucketEffectiveDate"})
            left["SizeBucketSource"] = np.where(
                left["SizeBucket"].notna(),
                "SUPPLIED_POINT_IN_TIME_QUARTERLY_HISTORY",
                "HOLD_BEFORE_FIRST_SIZE_BUCKET_EFFECTIVE_DATE",
            )
        attached.append(left)
    return pd.concat(attached, ignore_index=True).sort_values(
        ["Date", "Ticker"], kind="stable"
    ).reset_index(drop=True)


def def_active_membership_asof(
    prepared_membership: pd.DataFrame,
    as_of: Any,
) -> pd.DataFrame:
    date = def_normalize_date(as_of)
    active = (
        (prepared_membership["ValidFrom"].isna() | prepared_membership["ValidFrom"].le(date))
        & (prepared_membership["ValidTo"].isna() | prepared_membership["ValidTo"].ge(date))
        & prepared_membership["Decision"].isin(APPROVED_DECISIONS)
    )
    result = prepared_membership.loc[active].copy()
    duplicate = result.duplicated(["GroupId", "Ticker"], keep=False)
    if duplicate.any():
        raise ValueError(
            f"overlapping active membership intervals at {date:%Y-%m-%d}: "
            f"{int(duplicate.sum())} rows"
        )
    return result


# =============================================================================
# def 02 DYNAMIC SIZE / TRUNCATION
# =============================================================================


def def_assign_dynamic_size_bucket(
    day: pd.DataFrame,
    config: HierarchicalIndexConfig = HierarchicalIndexConfig(),
) -> pd.DataFrame:
    """Assign market-wide ex-TSMC P60/P90 buckets for one information date."""

    result = day.copy()
    if "SizeBucket" in result.columns:
        result["SizeBucket"] = result["SizeBucket"].where(
            result["SizeBucket"].notna(), pd.NA
        )
        result.loc[result["SizeBucket"].notna(), "SizeBucket"] = (
            result.loc[result["SizeBucket"].notna(), "SizeBucket"].astype(str).str.upper()
        )
        if "SizeBucketSource" not in result.columns:
            result["SizeBucketSource"] = "SUPPLIED_POINT_IN_TIME_HISTORY"
        return result

    universe = result.loc[
        result["IndexCapitalization"].gt(0)
        & (~result["IsTSMC"] if config.exclude_tsmc_from_primary else True),
        "IndexCapitalization",
    ]
    if universe.empty:
        result["SizeBucket"] = pd.NA
        result["SizeBucketSource"] = "BLOCKED_NO_MARKET_CAP_UNIVERSE"
        return result
    lower = float(universe.quantile(config.lower_size_quantile))
    upper = float(universe.quantile(config.upper_size_quantile))
    cap = result["IndexCapitalization"]
    result["SizeBucket"] = np.select(
        [cap.ge(upper), cap.ge(lower) & cap.lt(upper), cap.lt(lower)],
        ["LARGE", "MID", "SMALL"],
        default=pd.NA,
    )
    result["SizeBucketSource"] = "DYNAMIC_EX_TSMC_MARKET_P90_P60"
    result["SizeLowerCutoff"] = lower
    result["SizeUpperCutoff"] = upper
    return result


def def_dynamic_truncate(
    values: pd.Series,
    config: HierarchicalIndexConfig = HierarchicalIndexConfig(),
) -> tuple[pd.Series, float, float, str]:
    numeric = pd.to_numeric(values, errors="coerce")
    valid = numeric.dropna()
    if len(valid) < config.minimum_truncate_cross_section:
        return numeric.copy(), np.nan, np.nan, "NOT_APPLIED_SMALL_CROSS_SECTION"
    lower = float(valid.quantile(config.truncate_lower_quantile))
    upper = float(valid.quantile(config.truncate_upper_quantile))
    if not np.isfinite(lower) or not np.isfinite(upper) or upper < lower:
        return numeric.copy(), np.nan, np.nan, "BLOCKED_INVALID_DYNAMIC_BOUNDS"
    return numeric.clip(lower=lower, upper=upper), lower, upper, "APPLIED_POINT_IN_TIME_QUANTILES"


def def_next_session_map(dates: Iterable[Any]) -> dict[pd.Timestamp, pd.Timestamp]:
    sessions = pd.DatetimeIndex(pd.to_datetime(list(dates), errors="coerce")).dropna().normalize().unique().sort_values()
    return {pd.Timestamp(left): pd.Timestamp(right) for left, right in zip(sessions[:-1], sessions[1:])}


# =============================================================================
# def 03 PARALLEL SOURCE WEIGHTS -- no role weighting, no score
# =============================================================================


def def_weight_records(
    group: pd.DataFrame,
    method: str,
    weights: pd.Series | None,
    raw_measure: pd.Series | None,
    status: str,
    lower_bound: float = np.nan,
    upper_bound: float = np.nan,
    truncation_status: str = "NOT_APPLICABLE",
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for position, (_, row) in enumerate(group.reset_index(drop=True).iterrows()):
        records.append(
            {
                "WeightDate": row["Date"],
                "GroupId": row["GroupId"],
                "GroupName": row["GroupName"],
                "L3": row["L3"],
                "SizeBucket": row.get("SizeBucket", pd.NA),
                "Ticker": row["Ticker"],
                "MembershipAsOfDate": row.get("MembershipAsOfDate", pd.NaT),
                "Method": method,
                "Weight": float(weights.iloc[position]) if weights is not None else np.nan,
                "RawMeasure": float(raw_measure.iloc[position]) if raw_measure is not None and np.isfinite(raw_measure.iloc[position]) else np.nan,
                "DynamicLowerBound": lower_bound,
                "DynamicUpperBound": upper_bound,
                "DynamicTruncationStatus": truncation_status,
                "WeightStatus": status,
                "RoleWeightPolicy": "ROLE_IS_EVIDENCE_NOT_A_WEIGHT_INPUT",
                "InformationTiming": "KNOWN_AT_WEIGHT_DATE_APPLIED_NEXT_SESSION",
            }
        )
    return records


def def_equal_weights(group: pd.DataFrame) -> tuple[pd.Series | None, str]:
    if group.empty:
        return None, "BLOCKED_NO_ELIGIBLE_MEMBERS"
    if group["PriceDataStatus"].ne("PASS").any():
        return None, "BLOCKED_MISSING_MEMBER_PRICE"
    return pd.Series(np.repeat(1.0 / len(group), len(group))), "PASS"


def def_hierarchical_weights(
    group: pd.DataFrame,
    config: HierarchicalIndexConfig = HierarchicalIndexConfig(),
) -> tuple[pd.Series | None, pd.Series | None, float, float, str, str]:
    """L3 -> size -> stock; equal node budgets and capped FFMC in leaves."""

    if group["PriceDataStatus"].ne("PASS").any():
        return None, None, np.nan, np.nan, "NOT_APPLIED", "BLOCKED_MISSING_MEMBER_PRICE"
    if group["SizeBucket"].isna().any():
        return None, None, np.nan, np.nan, "NOT_APPLIED", "BLOCKED_MISSING_SIZE_BUCKET"
    if group["IndexCapitalization"].isna().any() or group["IndexCapitalization"].le(0).any():
        return None, None, np.nan, np.nan, "NOT_APPLIED", "BLOCKED_MISSING_MEMBER_CAPITALIZATION"

    truncated, lower, upper, truncate_status = def_dynamic_truncate(
        group["IndexCapitalization"], config
    )
    work = group[["L3", "SizeBucket"]].copy().reset_index(drop=True)
    work["Measure"] = truncated.reset_index(drop=True)
    result = pd.Series(0.0, index=work.index)
    branches = list(dict.fromkeys(work["L3"].astype(str)))
    if not branches:
        return None, truncated, lower, upper, truncate_status, "BLOCKED_NO_L3_BRANCH"
    branch_budget = 1.0 / len(branches)
    for branch in branches:
        branch_mask = work["L3"].astype(str).eq(branch)
        sizes = [
            bucket
            for bucket in SIZE_BUCKET_ORDER
            if (branch_mask & work["SizeBucket"].astype(str).eq(bucket)).any()
        ]
        other_sizes = sorted(
            set(work.loc[branch_mask, "SizeBucket"].astype(str)).difference(sizes)
        )
        sizes.extend(other_sizes)
        if not sizes:
            return None, truncated, lower, upper, truncate_status, "BLOCKED_NO_SIZE_NODE"
        size_budget = branch_budget / len(sizes)
        for size in sizes:
            cell = branch_mask & work["SizeBucket"].astype(str).eq(size)
            total = float(work.loc[cell, "Measure"].sum())
            if not np.isfinite(total) or total <= 0:
                return None, truncated, lower, upper, truncate_status, "BLOCKED_NONPOSITIVE_LEAF_CAPITALIZATION"
            result.loc[cell] = size_budget * work.loc[cell, "Measure"] / total
    if not np.isclose(float(result.sum()), 1.0, atol=WEIGHT_SUM_TOLERANCE):
        return None, truncated, lower, upper, truncate_status, "BLOCKED_WEIGHT_SUM"
    return result, truncated, lower, upper, truncate_status, "PASS"


def def_etr_weights(
    group: pd.DataFrame,
    config: HierarchicalIndexConfig = HierarchicalIndexConfig(),
) -> tuple[pd.Series | None, pd.Series | None, float, float, str, str]:
    if group["PriceDataStatus"].ne("PASS").any():
        return None, None, np.nan, np.nan, "NOT_APPLIED", "BLOCKED_MISSING_MEMBER_PRICE"
    etr = pd.to_numeric(group[config.etr_column], errors="coerce")
    if etr.isna().any() or etr.lt(0).any():
        return None, etr, np.nan, np.nan, "NOT_APPLIED", "BLOCKED_MISSING_OR_INVALID_ETR"
    truncated, lower, upper, truncate_status = def_dynamic_truncate(etr, config)
    total = float(truncated.sum())
    if not np.isfinite(total) or total <= 0:
        return None, truncated, lower, upper, truncate_status, "BLOCKED_NONPOSITIVE_GROUP_ETR"
    weights = truncated.reset_index(drop=True) / total
    return weights, truncated, lower, upper, truncate_status, "PASS_NON_DIRECTIONAL_ATTENTION"


def def_build_parallel_source_weights(
    prepared_panel: pd.DataFrame,
    prepared_membership: pd.DataFrame,
    config: HierarchicalIndexConfig = HierarchicalIndexConfig(),
) -> pd.DataFrame:
    """Calculate T-1 weights for the constituent set active on applied date T.

    ``WeightDate`` remains the only session from which price, capitalization,
    and ETR inputs are read.  Membership is selected as of ``AppliedDate`` so
    an approved ADD/REMOVE is reflected on exactly its effective session,
    without reading same-day weight inputs.
    """

    records: list[dict[str, Any]] = []
    session_map = def_next_session_map(prepared_panel["Date"].unique())
    for weight_date, raw_day in prepared_panel.groupby("Date", sort=True):
        if weight_date not in session_map:
            continue
        applied_date = session_map[pd.Timestamp(weight_date)]
        day = def_assign_dynamic_size_bucket(raw_day, config)
        active = def_active_membership_asof(prepared_membership, applied_date)
        if config.exclude_tsmc_from_primary:
            active = active.loc[~active["Ticker"].eq(def_ticker_base(config.tsmc_ticker))]
        if active.empty:
            continue
        merged = active.merge(day, on="Ticker", how="left", validate="many_to_one")
        merged["Date"] = weight_date
        merged["MembershipAsOfDate"] = applied_date
        for _, raw_group in merged.groupby("GroupId", sort=True):
            group = raw_group.sort_values("Ticker", kind="stable").reset_index(drop=True)

            ew_weights, ew_status = def_equal_weights(group)
            records.extend(
                def_weight_records(
                    group,
                    "GI_EW",
                    ew_weights,
                    pd.Series(np.ones(len(group))),
                    ew_status,
                )
            )

            hier_weights, hier_measure, lower, upper, truncation, hier_status = def_hierarchical_weights(
                group, config
            )
            records.extend(
                def_weight_records(
                    group,
                    "GI_HIER",
                    hier_weights,
                    hier_measure,
                    hier_status,
                    lower,
                    upper,
                    truncation,
                )
            )

            etr_weights, etr_measure, lower, upper, truncation, etr_status = def_etr_weights(
                group, config
            )
            records.extend(
                def_weight_records(
                    group,
                    "GI_ETR",
                    etr_weights,
                    etr_measure,
                    etr_status,
                    lower,
                    upper,
                    truncation,
                )
            )

    if not records:
        return pd.DataFrame()
    result = pd.DataFrame(records)
    result["AppliedDate"] = result["WeightDate"].map(session_map)
    result["WeightLagSessions"] = 1
    result["MembershipTiming"] = "ACTIVE_ON_APPLIED_DATE"
    return result.sort_values(
        ["GroupId", "Method", "AppliedDate", "Ticker"], kind="stable"
    ).reset_index(drop=True)


# =============================================================================
# def 04 INDEX RETURNS / LEVELS
# =============================================================================


def def_compute_parallel_index_returns(
    prepared_panel: pd.DataFrame,
    source_weights: pd.DataFrame,
) -> pd.DataFrame:
    if source_weights.empty:
        return pd.DataFrame()
    returns = prepared_panel[["Date", "Ticker", "StockReturn"]].rename(
        columns={"Date": "AppliedDate"}
    )
    merged = source_weights.merge(
        returns,
        on=["AppliedDate", "Ticker"],
        how="left",
        validate="many_to_one",
    )
    rows: list[dict[str, Any]] = []
    keys = ["AppliedDate", "WeightDate", "GroupId", "GroupName", "Method"]
    for key, group in merged.groupby(keys, sort=True, dropna=False):
        applied_date, weight_date, group_id, group_name, method = key
        weight_valid = group["Weight"].notna().all() and np.isclose(
            float(group["Weight"].sum()), 1.0, atol=WEIGHT_SUM_TOLERANCE
        )
        return_valid = group["StockReturn"].notna().all()
        if not weight_valid:
            status = str(group["WeightStatus"].iloc[0])
            group_return = np.nan
        elif not return_valid:
            status = "HOLD_MISSING_MEMBER_RETURN"
            group_return = np.nan
        else:
            status = "PASS"
            group_return = float((group["Weight"] * group["StockReturn"]).sum())
        hhi = float((group["Weight"] ** 2).sum()) if weight_valid else np.nan
        rows.append(
            {
                "Date": applied_date,
                "WeightDate": weight_date,
                "GroupId": group_id,
                "GroupName": group_name,
                "Method": method,
                "GroupReturn": group_return,
                "IndexStatus": status,
                "ConstituentCount": int(group["Ticker"].nunique()),
                "WeightSum": float(group["Weight"].sum()) if group["Weight"].notna().any() else np.nan,
                "HHI": hhi,
                "EffectiveConstituentCount": 1.0 / hhi if np.isfinite(hhi) and hhi > 0 else np.nan,
                "ReturnUsesPriorSessionWeight": bool(pd.Timestamp(weight_date) < pd.Timestamp(applied_date)),
            }
        )
    return pd.DataFrame(rows).sort_values(["GroupId", "Method", "Date"]).reset_index(drop=True)


def def_chain_index_levels(
    index_returns: pd.DataFrame,
    config: HierarchicalIndexConfig = HierarchicalIndexConfig(),
) -> pd.DataFrame:
    if index_returns.empty:
        return index_returns.copy()
    output: list[pd.DataFrame] = []
    for _, group in index_returns.groupby(["GroupId", "Method"], sort=True):
        group = group.sort_values("Date", kind="stable").copy()
        level = float(config.base_level)
        levels: list[float] = []
        level_status: list[str] = []
        for row in group.itertuples(index=False):
            if row.IndexStatus == "PASS" and np.isfinite(row.GroupReturn):
                level *= 1.0 + float(row.GroupReturn)
                levels.append(level)
                level_status.append("CHAINED_FROM_PRIOR_LEVEL")
            else:
                levels.append(level)
                level_status.append("LEVEL_HELD_RETURN_NOT_PUBLISHED")
        group["IndexLevel"] = levels
        group["IndexLevelStatus"] = level_status
        group["BaseLevel"] = config.base_level
        output.append(group)
    return pd.concat(output, ignore_index=True).sort_values(
        ["GroupId", "Method", "Date"], kind="stable"
    ).reset_index(drop=True)


def def_pivot_parallel_indices(index_levels: pd.DataFrame) -> pd.DataFrame:
    if index_levels.empty:
        return pd.DataFrame()
    levels = index_levels.pivot_table(
        index=["Date", "GroupId", "GroupName"],
        columns="Method",
        values="IndexLevel",
        aggfunc="first",
    )
    returns = index_levels.pivot_table(
        index=["Date", "GroupId", "GroupName"],
        columns="Method",
        values="GroupReturn",
        aggfunc="first",
    ).add_suffix("_Return")
    result = levels.join(returns, how="outer").reset_index()
    result.columns.name = None
    result["IndexFamilyPolicy"] = "PARALLEL_INDICES_NOT_A_COMPOSITE_SCORE"
    return result.sort_values(["GroupId", "Date"], kind="stable").reset_index(drop=True)


def def_validate_parallel_indices(
    source_weights: pd.DataFrame,
    index_levels: pd.DataFrame,
) -> dict[str, Any]:
    if source_weights.empty:
        return {
            "EngineId": ENGINE_ID,
            "EngineVersion": ENGINE_VERSION,
            "Status": "HOLD_NO_APPLIED_WEIGHT_SESSION",
            "Methods": [],
            "BadWeightSums": 0,
            "NonLaggedWeightRows": 0,
            "BadMembershipEffectiveTimingRows": 0,
            "ForbiddenScoreColumns": [],
            "IndexRows": int(len(index_levels)),
            "WeightRows": 0,
        }
    valid = source_weights.loc[source_weights["Weight"].notna()].copy()
    sums = valid.groupby(["WeightDate", "GroupId", "Method"])["Weight"].sum()
    bad_sums = int((~np.isclose(sums.to_numpy(dtype=float), 1.0, atol=WEIGHT_SUM_TOLERANCE)).sum())
    same_or_future = int(
        (
            source_weights["AppliedDate"].notna()
            & source_weights["WeightDate"].ge(source_weights["AppliedDate"])
        ).sum()
    )
    if "MembershipAsOfDate" not in source_weights.columns:
        bad_membership_timing = int(len(source_weights))
    else:
        membership_as_of = pd.to_datetime(
            source_weights["MembershipAsOfDate"], errors="coerce"
        ).dt.normalize()
        applied = pd.to_datetime(
            source_weights["AppliedDate"], errors="coerce"
        ).dt.normalize()
        bad_membership_timing = int(
            (membership_as_of.isna() | applied.isna() | membership_as_of.ne(applied)).sum()
        )
    forbidden = [column for column in list(source_weights.columns) + list(index_levels.columns) if "score" in column.lower()]
    status = (
        "PASS"
        if bad_sums == 0
        and same_or_future == 0
        and bad_membership_timing == 0
        and not forbidden
        else "FAIL"
    )
    return {
        "EngineId": ENGINE_ID,
        "EngineVersion": ENGINE_VERSION,
        "Status": status,
        "Methods": sorted(source_weights["Method"].dropna().unique().tolist()),
        "BadWeightSums": bad_sums,
        "NonLaggedWeightRows": same_or_future,
        "BadMembershipEffectiveTimingRows": bad_membership_timing,
        "ForbiddenScoreColumns": forbidden,
        "IndexRows": int(len(index_levels)),
        "WeightRows": int(len(source_weights)),
    }


def def_build_parallel_group_indices(
    stock_daily: pd.DataFrame,
    membership: pd.DataFrame,
    config: HierarchicalIndexConfig = HierarchicalIndexConfig(),
    size_history: pd.DataFrame | None = None,
) -> dict[str, Any]:
    if config.require_pit_size_history and size_history is None:
        raise ValueError(
            "formal GI_HIER publication requires quarterly point-in-time size history"
        )
    panel = def_prepare_index_panel(stock_daily, config)
    if size_history is not None:
        panel = def_attach_size_bucket_history(panel, size_history, config)
    members = def_prepare_membership(membership)
    weights = def_build_parallel_source_weights(panel, members, config)
    returns = def_compute_parallel_index_returns(panel, weights)
    levels = def_chain_index_levels(returns, config)
    wide = def_pivot_parallel_indices(levels)
    quality = def_validate_parallel_indices(weights, levels)
    return {
        "prepared_panel": panel,
        "prepared_membership": members,
        "weights": weights,
        "index_long": levels,
        "index_wide": wide,
        "quality": quality,
    }


# =============================================================================
# def 05 SELF-TEST
# =============================================================================


def def_build_synthetic_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    dates = pd.bdate_range("2026-01-02", periods=8)
    tickers = ["1101.TW", "2308.TW", "3017.TW", "3324.TWO", "6669.TW", "2330.TW"]
    rows: list[dict[str, Any]] = []
    for date_number, date in enumerate(dates):
        for ticker_number, ticker in enumerate(tickers):
            rows.append(
                {
                    "Date": date,
                    "Ticker": ticker,
                    "Adj_Close": 50.0 + 3.0 * ticker_number + date_number * (0.3 + 0.05 * ticker_number),
                    "FreeFloatMarketCap": float((ticker_number + 1) * 1_000_000_000),
                    "ETR": float((ticker_number + 2) * 100_000_000 + date_number * 2_000_000),
                }
            )
    membership = pd.DataFrame(
        [
            {"GroupId": "AI_COOL", "GroupName": "AI散熱", "L3": "LIQUID", "Ticker": "2308.TW", "Decision": "APPROVED", "Role": "LEAD"},
            {"GroupId": "AI_COOL", "GroupName": "AI散熱", "L3": "LIQUID", "Ticker": "3017.TW", "Decision": "APPROVED", "Role": "PEER"},
            {"GroupId": "AI_COOL", "GroupName": "AI散熱", "L3": "AIR", "Ticker": "3324.TWO", "Decision": "APPROVED", "Role": "LAG"},
            {"GroupId": "AI_COOL", "GroupName": "AI散熱", "L3": "AIR", "Ticker": "6669.TW", "Decision": "APPROVED", "Role": "PEER"},
            {"GroupId": "POWER", "GroupName": "電源", "L3": "POWER", "Ticker": "2308.TW", "Decision": "APPROVED", "Role": "LAG"},
            {"GroupId": "POWER", "GroupName": "電源", "L3": "POWER", "Ticker": "1101.TW", "Decision": "APPROVED", "Role": "PEER"},
            {"GroupId": "FOUNDRY", "GroupName": "晶圓代工", "L3": "ANCHOR", "Ticker": "2330.TW", "Decision": "APPROVED", "Role": "LEAD"},
        ]
    )
    return pd.DataFrame(rows), membership


def def_run_self_test() -> dict[str, Any]:
    stock, membership = def_build_synthetic_inputs()
    result = def_build_parallel_group_indices(stock, membership)
    weights = result["weights"]
    levels = result["index_long"]
    assert result["quality"]["Status"] == "PASS"
    assert set(weights["Method"].unique()) == set(INDEX_METHODS)
    assert (weights["WeightDate"] < weights["AppliedDate"]).all()
    assert not weights["Ticker"].eq("2330").any()
    assert weights.loc[weights["Ticker"].eq("2308"), "GroupId"].nunique() == 2
    assert not any("score" in column.lower() for column in weights.columns)
    assert not any("score" in column.lower() for column in levels.columns)

    role_changed = membership.copy()
    role_changed["Role"] = role_changed["Role"].iloc[::-1].to_numpy()
    second = def_build_parallel_group_indices(stock, role_changed)["weights"]
    compare_columns = ["WeightDate", "GroupId", "Ticker", "Method", "Weight"]
    pd.testing.assert_frame_equal(
        weights[compare_columns].reset_index(drop=True),
        second[compare_columns].reset_index(drop=True),
    )
    return {
        "Status": "PASS",
        "Assertions": 8,
        "Quality": result["quality"],
        "ParallelIndexRows": int(len(levels)),
    }


if __name__ == "__main__":
    print(def_run_self_test())
