from __future__ import annotations

"""Conserved and raw story-group flow views plus rotation associations.

A stock may legitimately appear in several story groups.  The raw story view
therefore repeats its full exposure in every approved group and is explicitly
non-additive.  The conserved view allocates each unique stock exactly once and
is the only view allowed to feed a cross-group matrix.

The resulting edges are named ``ROTATION_ASSOCIATION``.  They are a balanced
description of simultaneous source/destination pressure, not proof that an
identifiable dollar moved directly from group A to group B.  ETR remains a
non-directional attention/liquidity measure throughout this module.
"""

from dataclasses import dataclass
from typing import Any, Iterable

import numpy as np
import pandas as pd


# =============================================================================
# def 00 PARAMETERS -- structural/governance controls only
# =============================================================================

ENGINE_ID = "VIA_FLOW_TRANSFER_MATRIX_ENGINE"
ENGINE_VERSION = "0.5.0"
TSMC_BASE = "2330"
UNMAPPED_GROUP_ID = "UNMAPPED"
UNMAPPED_GROUP_NAME = "未映射"
EXTERNAL_NODE_ID = "OUTSIDE_OR_CASH"
EXTERNAL_NODE_NAME = "市場外部／現金／其他交易對手"
APPROVED_DECISIONS = ("APPROVED", "ACTIVE", "KEEP")
ALLOCATION_TOLERANCE = 1.0e-10
CONSERVATION_TOLERANCE = 1.0e-8
EPS = np.finfo(float).eps
REQUIRED_FULL_MARKET_GATE_STATUS = "PASS_FULL_TWSE_TPEX_ORDINARY_STOCKS"

DIRECTIONAL_LANES = (
    "ForeignNetAmount",
    "InvestmentTrustNetAmount",
    "DealerNetAmount",
    "DealerProprietaryNetAmount",
    "DealerHedgeNetAmount",
    "MarginFinancingChangeAmount",
    "ShortSellingChangeAmount",
    "ETFActiveValue",
)


@dataclass(frozen=True)
class FlowTransferConfig:
    etr_column: str = "AttentionETR"
    exposure_column: str = "ExposureShare"
    directional_lanes: tuple[str, ...] = DIRECTIONAL_LANES
    exclude_tsmc: bool = True
    tsmc_ticker: str = TSMC_BASE
    unmapped_group_id: str = UNMAPPED_GROUP_ID
    external_node_id: str = EXTERNAL_NODE_ID


# =============================================================================
# def 01 NORMALIZATION / PIT MEMBERSHIP
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


def def_prepare_transfer_stock_panel(
    stock_daily: pd.DataFrame,
    config: FlowTransferConfig = FlowTransferConfig(),
) -> pd.DataFrame:
    """Validate a unique stock panel; no volume or flow field is filled."""

    gate_status = str(stock_daily.attrs.get("FullMarketGateStatus", "")).strip().upper()
    if gate_status != REQUIRED_FULL_MARKET_GATE_STATUS:
        raise ValueError(
            "transfer associations require provenance from the complete TWSE+TPEX "
            "ordinary-stock gate"
        )
    frame = stock_daily.copy()
    if config.etr_column not in frame.columns and config.etr_column == "AttentionETR" and "ETR" in frame.columns:
        frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce").dt.normalize()
        frame["Ticker"] = frame["Ticker"].map(def_ticker_base)
        frame = frame.sort_values(["Ticker", "Date"], kind="stable")
        raw_etr = pd.to_numeric(frame["ETR"], errors="coerce")
        prior_etr = raw_etr.groupby(frame["Ticker"], sort=False).shift(1)
        if "IsLimitUpLocked" in frame.columns:
            lock_known = frame["IsLimitUpLocked"].notna()
            locked = frame["IsLimitUpLocked"].fillna(False).astype(bool)
            frame[config.etr_column] = raw_etr
            protected = locked & prior_etr.notna() & raw_etr.notna()
            frame.loc[protected, config.etr_column] = np.maximum(
                raw_etr.loc[protected], prior_etr.loc[protected]
            )
            frame["AttentionProtectionStatus"] = np.where(
                lock_known,
                "DERIVED_FROM_LIMIT_LOCK_FLAG",
                "HOLD_LIMIT_LOCK_STATUS_UNKNOWN",
            )
        else:
            frame[config.etr_column] = raw_etr
            frame["AttentionProtectionStatus"] = "HOLD_LIMIT_LOCK_STATUS_UNKNOWN"
    elif config.etr_column in frame.columns:
        known_limit_status = (
            frame["LimitLockDataStatus"].eq("PASS_LIMIT_LOCK_FLAGS")
            if "LimitLockDataStatus" in frame.columns
            else pd.Series(False, index=frame.index)
        )
        frame["AttentionProtectionStatus"] = np.where(
            known_limit_status,
            "SUPPLIED_CANONICAL_ATTENTION_ETR",
            "HOLD_LIMIT_LOCK_STATUS_UNKNOWN",
        )

    required = {"Date", "Ticker", config.etr_column}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"transfer stock panel missing required columns: {missing}")
    frame["Date"] = frame["Date"].map(def_normalize_date)
    frame["Ticker"] = frame["Ticker"].map(def_ticker_base)
    frame[config.etr_column] = pd.to_numeric(frame[config.etr_column], errors="coerce")
    if "ETFActiveValue" not in frame.columns and "EstimatedActiveValue" in frame.columns:
        frame["ETFActiveValue"] = frame["EstimatedActiveValue"]
    supplied_directional_lanes = tuple(
        lane for lane in config.directional_lanes if lane in frame.columns
    )
    for lane in config.directional_lanes:
        if lane not in frame.columns:
            frame[lane] = np.nan
        frame[lane] = pd.to_numeric(frame[lane], errors="coerce")
    invalid_key = frame["Date"].isna() | frame["Ticker"].eq("")
    if invalid_key.any():
        raise ValueError(f"transfer stock panel has {int(invalid_key.sum())} invalid keys")
    duplicate = frame.duplicated(["Date", "Ticker"], keep=False)
    if duplicate.any():
        raise ValueError(
            f"transfer stock panel has {int(duplicate.sum())} duplicate Date+Ticker rows"
        )
    frame["IsTSMC"] = frame["Ticker"].eq(def_ticker_base(config.tsmc_ticker))
    frame["ETRStatus"] = np.where(
        frame[config.etr_column].notna() & frame[config.etr_column].ge(0),
        "PASS_NON_DIRECTIONAL_ATTENTION",
        "BLOCKED_MISSING_OR_INVALID_ETR",
    )
    frame.loc[frame["ETRStatus"].ne("PASS_NON_DIRECTIONAL_ATTENTION"), config.etr_column] = np.nan
    valid_attention_provenance = frame["AttentionProtectionStatus"].isin(
        {
            "DERIVED_FROM_LIMIT_LOCK_FLAG",
            "SUPPLIED_CANONICAL_ATTENTION_ETR",
        }
    )
    if (~valid_attention_provenance).any():
        raise ValueError(
            "transfer attention associations require point-in-time limit-lock evidence"
        )
    result = frame.sort_values(["Date", "Ticker"], kind="stable").reset_index(drop=True)
    result.attrs.update(stock_daily.attrs)
    result.attrs["SuppliedDirectionalLanes"] = supplied_directional_lanes
    return result


def def_prepare_transfer_membership(
    membership: pd.DataFrame,
    config: FlowTransferConfig = FlowTransferConfig(),
) -> pd.DataFrame:
    if "EventType" in membership.columns:
        raise ValueError(
            "raw membership events cannot enter transfer analysis; materialize PIT history first"
        )
    required = {"GroupId", "Ticker"}
    missing = sorted(required.difference(membership.columns))
    if missing:
        raise ValueError(f"transfer membership missing required columns: {missing}")
    frame = membership.copy()
    frame["GroupId"] = frame["GroupId"].fillna("").astype(str).str.strip()
    frame["Ticker"] = frame["Ticker"].map(def_ticker_base)
    if "GroupName" not in frame.columns:
        frame["GroupName"] = frame["GroupId"]
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
    if config.exposure_column not in frame.columns:
        frame[config.exposure_column] = np.nan
    frame[config.exposure_column] = pd.to_numeric(
        frame[config.exposure_column], errors="coerce"
    )
    invalid_share = frame[config.exposure_column].notna() & (
        frame[config.exposure_column].lt(0) | frame[config.exposure_column].gt(1)
    )
    if invalid_share.any():
        raise ValueError(f"membership has {int(invalid_share.sum())} invalid exposure shares")
    invalid_key = frame["GroupId"].eq("") | frame["Ticker"].eq("")
    if invalid_key.any():
        raise ValueError(f"membership has {int(invalid_key.sum())} invalid GroupId/Ticker keys")
    exact_duplicate = frame.duplicated(
        ["GroupId", "Ticker", "ValidFrom", "ValidTo"], keep=False
    )
    if exact_duplicate.any():
        raise ValueError(f"membership has {int(exact_duplicate.sum())} duplicate interval rows")
    return frame.sort_values(["Ticker", "GroupId", "ValidFrom"], kind="stable").reset_index(drop=True)


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


def def_previous_session_map(dates: Iterable[Any]) -> dict[pd.Timestamp, pd.Timestamp]:
    sessions = pd.DatetimeIndex(pd.to_datetime(list(dates), errors="coerce")).dropna().normalize().unique().sort_values()
    return {pd.Timestamp(right): pd.Timestamp(left) for left, right in zip(sessions[:-1], sessions[1:])}


# =============================================================================
# def 02 RAW STORY AND CONSERVED ALLOCATION LEDGERS
# =============================================================================


def def_resolve_conserved_ticker_allocation(
    ticker: str,
    active_ticker_membership: pd.DataFrame,
    allocation_date: pd.Timestamp,
    applied_date: pd.Timestamp,
    config: FlowTransferConfig = FlowTransferConfig(),
) -> list[dict[str, Any]]:
    """Allocate one ticker once, using audited shares or an explicit fallback."""

    if active_ticker_membership.empty:
        return [
            {
                "AllocationDate": allocation_date,
                "AppliedDate": applied_date,
                "MembershipAsOfDate": applied_date,
                "Ticker": ticker,
                "GroupId": config.unmapped_group_id,
                "GroupName": UNMAPPED_GROUP_NAME,
                "AllocationWeight": 1.0,
                "AllocationMethod": "UNMAPPED_NO_ACTIVE_GROUP",
                "AggregationView": "CONSERVED_MARKET_FLOW",
            }
        ]

    members = active_ticker_membership.sort_values("GroupId", kind="stable").reset_index(drop=True)
    shares = pd.to_numeric(members[config.exposure_column], errors="coerce")
    known = shares.notna()
    known_total = float(shares[known].sum()) if known.any() else 0.0
    if known_total > 1.0 + ALLOCATION_TOLERANCE:
        raise ValueError(
            f"audited exposure shares exceed one for {ticker} at {allocation_date:%Y-%m-%d}"
        )

    weights = pd.Series(0.0, index=members.index)
    unmapped_weight = 0.0
    if not known.any():
        weights[:] = 1.0 / len(members)
        method = "EQUAL_SPLIT_NO_AUDITED_EXPOSURE"
    elif (~known).any():
        weights.loc[known] = shares.loc[known]
        residual = max(0.0, 1.0 - known_total)
        weights.loc[~known] = residual / int((~known).sum())
        method = "AUDITED_EXPOSURE_PLUS_EQUAL_RESIDUAL"
    else:
        weights[:] = shares
        unmapped_weight = max(0.0, 1.0 - known_total)
        method = "AUDITED_EXPOSURE"

    rows: list[dict[str, Any]] = []
    for index, row in members.iterrows():
        if weights.loc[index] <= ALLOCATION_TOLERANCE:
            continue
        rows.append(
            {
                "AllocationDate": allocation_date,
                "AppliedDate": applied_date,
                "MembershipAsOfDate": applied_date,
                "Ticker": ticker,
                "GroupId": row["GroupId"],
                "GroupName": row["GroupName"],
                "AllocationWeight": float(weights.loc[index]),
                "AllocationMethod": method,
                "AggregationView": "CONSERVED_MARKET_FLOW",
            }
        )
    if unmapped_weight > ALLOCATION_TOLERANCE:
        rows.append(
            {
                "AllocationDate": allocation_date,
                "AppliedDate": applied_date,
                "MembershipAsOfDate": applied_date,
                "Ticker": ticker,
                "GroupId": config.unmapped_group_id,
                "GroupName": UNMAPPED_GROUP_NAME,
                "AllocationWeight": unmapped_weight,
                "AllocationMethod": "UNMAPPED_AUDITED_EXPOSURE_RESIDUAL",
                "AggregationView": "CONSERVED_MARKET_FLOW",
            }
        )
    total = sum(float(row["AllocationWeight"]) for row in rows)
    if not np.isclose(total, 1.0, atol=ALLOCATION_TOLERANCE):
        raise ValueError(f"allocation does not conserve ticker {ticker}: {total}")
    return rows


def def_build_lagged_allocation_ledgers(
    prepared_stock: pd.DataFrame,
    prepared_membership: pd.DataFrame,
    config: FlowTransferConfig = FlowTransferConfig(),
) -> dict[str, pd.DataFrame]:
    """Build T-1 allocation ledgers for membership active on applied date T.

    ``AllocationDate`` remains the prior session and documents the lagged
    allocation-input boundary.  Constituent inclusion is evaluated at
    ``AppliedDate`` so an approved ADD/REMOVE is synchronized with its PIT
    membership effective session.
    """

    previous_map = def_previous_session_map(prepared_stock["Date"].unique())
    raw_rows: list[dict[str, Any]] = []
    conserved_rows: list[dict[str, Any]] = []
    for applied_date, day in prepared_stock.groupby("Date", sort=True):
        allocation_date = previous_map.get(pd.Timestamp(applied_date))
        if allocation_date is None:
            continue
        active = def_active_membership_asof(prepared_membership, applied_date)
        for ticker in sorted(day["Ticker"].unique()):
            if config.exclude_tsmc and ticker == def_ticker_base(config.tsmc_ticker):
                continue
            ticker_membership = active.loc[active["Ticker"].eq(ticker)]
            conserved_rows.extend(
                def_resolve_conserved_ticker_allocation(
                    ticker,
                    ticker_membership,
                    allocation_date,
                    pd.Timestamp(applied_date),
                    config,
                )
            )
            if ticker_membership.empty:
                raw_rows.append(
                    {
                        "AllocationDate": allocation_date,
                        "AppliedDate": applied_date,
                        "MembershipAsOfDate": applied_date,
                        "Ticker": ticker,
                        "GroupId": config.unmapped_group_id,
                        "GroupName": UNMAPPED_GROUP_NAME,
                        "AllocationWeight": 1.0,
                        "AllocationMethod": "UNMAPPED_NO_ACTIVE_GROUP",
                        "AggregationView": "RAW_STORY_EXPOSURE",
                    }
                )
            else:
                for row in ticker_membership.itertuples(index=False):
                    raw_rows.append(
                        {
                            "AllocationDate": allocation_date,
                            "AppliedDate": applied_date,
                            "MembershipAsOfDate": applied_date,
                            "Ticker": ticker,
                            "GroupId": row.GroupId,
                            "GroupName": row.GroupName,
                            "AllocationWeight": 1.0,
                            "AllocationMethod": "FULL_WEIGHT_EACH_APPROVED_STORY",
                            "AggregationView": "RAW_STORY_EXPOSURE",
                        }
                    )
    raw = pd.DataFrame(raw_rows)
    conserved = pd.DataFrame(conserved_rows)
    for frame in (raw, conserved):
        if not frame.empty:
            frame["AllocationLagSessions"] = 1
            frame["AllocationTiming"] = (
                "APPLIED_DATE_MEMBERSHIP_WITH_PRIOR_SESSION_ALLOCATION_INPUTS"
            )
    return {"raw_story_ledger": raw, "conserved_ledger": conserved}


# =============================================================================
# def 03 GROUP AGGREGATION
# =============================================================================


def def_aggregate_allocation_view(
    prepared_stock: pd.DataFrame,
    allocation_ledger: pd.DataFrame,
    view_name: str,
    config: FlowTransferConfig = FlowTransferConfig(),
) -> pd.DataFrame:
    if allocation_ledger.empty:
        return pd.DataFrame()
    stock = prepared_stock.rename(columns={"Date": "AppliedDate"}).copy()
    if config.exclude_tsmc:
        stock = stock.loc[~stock["IsTSMC"]]
    merged = allocation_ledger.merge(
        stock,
        on=["AppliedDate", "Ticker"],
        how="left",
        validate="many_to_one",
    )
    merged["AllocatedETR"] = merged["AllocationWeight"] * merged[config.etr_column]
    for lane in config.directional_lanes:
        merged[f"Allocated_{lane}"] = merged["AllocationWeight"] * merged[lane]

    market = stock.groupby("AppliedDate", sort=True).agg(
        MarketETRExTSMC=(config.etr_column, lambda values: values.sum(min_count=1)),
        MarketUniqueTickerCount=("Ticker", "nunique"),
        MarketValidETRCount=("ETRStatus", lambda values: int(values.eq("PASS_NON_DIRECTIONAL_ATTENTION").sum())),
    ).reset_index()

    rows: list[dict[str, Any]] = []
    keys = ["AppliedDate", "AllocationDate", "GroupId", "GroupName"]
    for key, group in merged.groupby(keys, sort=True, dropna=False):
        applied_date, allocation_date, group_id, group_name = key
        record: dict[str, Any] = {
            "Date": applied_date,
            "AllocationDate": allocation_date,
            "GroupId": group_id,
            "GroupName": group_name,
            "GroupETR": group["AllocatedETR"].sum(min_count=1),
            "UniqueTickerCount": int(group["Ticker"].nunique()),
            "ETRCoveredTickerCount": int(group["AllocatedETR"].notna().sum()),
            "AggregationView": view_name,
            "AdditiveAcrossGroups": view_name == "CONSERVED_MARKET_FLOW",
            "ETRInterpretation": "NON_DIRECTIONAL_ATTENTION_NOT_NET_INFLOW",
            "AllocationUsesPriorSession": bool(pd.Timestamp(allocation_date) < pd.Timestamp(applied_date)),
        }
        for lane in config.directional_lanes:
            allocated = f"Allocated_{lane}"
            record[lane] = group[allocated].sum(min_count=1)
            record[f"{lane}CoveredTickerCount"] = int(group[allocated].notna().sum())
        rows.append(record)
    result = pd.DataFrame(rows).merge(
        market.rename(columns={"AppliedDate": "Date"}),
        on="Date",
        how="left",
        validate="many_to_one",
    )
    complete_market_etr = (
        result["MarketValidETRCount"].eq(result["MarketUniqueTickerCount"])
        & result["MarketUniqueTickerCount"].gt(0)
        & result["MarketETRExTSMC"].notna()
        & result["MarketETRExTSMC"].gt(0)
    )
    complete_group_etr = (
        result["ETRCoveredTickerCount"].eq(result["UniqueTickerCount"])
        & result["UniqueTickerCount"].gt(0)
        & result["GroupETR"].notna()
    )
    valid_attention_share = complete_market_etr & complete_group_etr
    result["ETRCoverageStatus"] = np.where(
        valid_attention_share,
        "PASS_COMPLETE_ETR_COVERAGE",
        "HOLD_PARTIAL_OR_INVALID_ETR_COVERAGE",
    )
    # Fail closed: a partial market denominator must never produce an
    # apparently precise group share.  The raw GroupETR and coverage counts
    # remain available for diagnosis, but AttentionShare is deliberately NaN.
    result["AttentionShare"] = np.where(
        valid_attention_share,
        result["GroupETR"] / result["MarketETRExTSMC"],
        np.nan,
    )
    result["AttentionShareStatus"] = np.where(
        valid_attention_share,
        "PASS",
        "HOLD_PARTIAL_OR_INVALID_MARKET_ETR",
    )
    supplied_lanes = set(prepared_stock.attrs.get("SuppliedDirectionalLanes", ()))
    for lane in config.directional_lanes:
        coverage_column = f"{lane}CoverageStatus"
        if lane not in supplied_lanes:
            result[coverage_column] = "NOT_SUPPLIED_NO_ASSOCIATION"
            continue
        complete_lane = (
            result[f"{lane}CoveredTickerCount"].eq(result["UniqueTickerCount"])
            & result["UniqueTickerCount"].gt(0)
            & result[lane].notna()
        )
        result[coverage_column] = np.where(
            complete_lane,
            "PASS_COMPLETE_DIRECTIONAL_COVERAGE",
            "HOLD_PARTIAL_OR_INVALID_DIRECTIONAL_COVERAGE",
        )
    return result.sort_values(["Date", "GroupId"], kind="stable").reset_index(drop=True)


def def_build_story_and_conserved_views(
    prepared_stock: pd.DataFrame,
    prepared_membership: pd.DataFrame,
    config: FlowTransferConfig = FlowTransferConfig(),
) -> dict[str, pd.DataFrame]:
    ledgers = def_build_lagged_allocation_ledgers(prepared_stock, prepared_membership, config)
    raw = def_aggregate_allocation_view(
        prepared_stock,
        ledgers["raw_story_ledger"],
        "RAW_STORY_EXPOSURE_NOT_ADDITIVE",
        config,
    )
    conserved = def_aggregate_allocation_view(
        prepared_stock,
        ledgers["conserved_ledger"],
        "CONSERVED_MARKET_FLOW",
        config,
    )
    return {**ledgers, "raw_story_view": raw, "conserved_view": conserved}


# =============================================================================
# def 04 BALANCED ASSOCIATION MATRICES -- never labelled actual transfer
# =============================================================================


def def_balance_source_destination_nodes(
    sources: pd.Series,
    destinations: pd.Series,
    external_node_id: str,
) -> tuple[pd.Series, pd.Series]:
    source = sources.loc[sources.gt(0)].astype(float).copy()
    destination = destinations.loc[destinations.gt(0)].astype(float).copy()
    source_total = float(source.sum())
    destination_total = float(destination.sum())
    if source_total <= EPS and destination_total <= EPS:
        return source, destination
    if source_total < destination_total:
        source.loc[external_node_id] = destination_total - source_total
    elif destination_total < source_total:
        destination.loc[external_node_id] = source_total - destination_total
    return source, destination


def def_cartesian_association_edges(
    date: pd.Timestamp,
    lane: str,
    sources: pd.Series,
    destinations: pd.Series,
    amount_unit: str,
    external_node_id: str,
) -> list[dict[str, Any]]:
    balanced_sources, balanced_destinations = def_balance_source_destination_nodes(
        sources, destinations, external_node_id
    )
    total = float(balanced_sources.sum())
    if total <= EPS or float(balanced_destinations.sum()) <= EPS:
        return []
    rows: list[dict[str, Any]] = []
    for source_group, source_amount in balanced_sources.items():
        for destination_group, destination_amount in balanced_destinations.items():
            association_amount = float(source_amount * destination_amount / total)
            if association_amount <= EPS:
                continue
            rows.append(
                {
                    "Date": date,
                    "Lane": lane,
                    "SourceGroupId": source_group,
                    "DestinationGroupId": destination_group,
                    "AssociationAmount": association_amount,
                    "AmountUnit": amount_unit,
                    "AssociationType": "ROTATION_ASSOCIATION",
                    "CausalClaim": False,
                    "Interpretation": "BALANCED_ASSOCIATION_NOT_IDENTIFIED_DOLLAR_TRANSFER",
                }
            )
    return rows


def def_build_attention_transfer_associations(
    conserved_view: pd.DataFrame,
    config: FlowTransferConfig = FlowTransferConfig(),
) -> pd.DataFrame:
    """Associate losses and gains in conserved ETR attention share."""

    if conserved_view.empty:
        return pd.DataFrame()
    required = {"Date", "GroupId", "AttentionShare", "AttentionShareStatus"}
    if not required.issubset(conserved_view.columns):
        # Association generation is fail-closed when coverage provenance is
        # absent.  Callers can still inspect the conserved aggregation view.
        return pd.DataFrame()
    dates = pd.DatetimeIndex(
        pd.to_datetime(conserved_view["Date"], errors="coerce")
    ).dropna().normalize().unique().sort_values()
    groups = sorted(conserved_view["GroupId"].dropna().astype(str).unique())
    coverage_valid = (
        conserved_view.assign(
            _CoverageValid=conserved_view["AttentionShareStatus"].eq("PASS")
            & pd.to_numeric(conserved_view["AttentionShare"], errors="coerce").notna()
        )
        .groupby("Date", sort=True)["_CoverageValid"]
        .all()
        .reindex(dates, fill_value=False)
    )
    # A group may disappear after an approved membership change.  Zero-filling
    # the derived share grid (not the underlying ETR) is necessary to record
    # that complete loss of allocation instead of mislabelling it as an
    # external source.  Zero-fill is allowed only on fully covered dates;
    # invalid dates remain NaN and break the change chain so that the next
    # valid observation is not compared across a coverage gap.
    share_grid = conserved_view.pivot_table(
        index="Date",
        columns="GroupId",
        values="AttentionShare",
        aggfunc="first",
    ).reindex(index=dates, columns=groups)
    valid_dates = coverage_valid.index[coverage_valid]
    share_grid.loc[valid_dates] = share_grid.loc[valid_dates].fillna(0.0)
    change_grid = share_grid.diff()
    comparable_date = coverage_valid & coverage_valid.shift(1, fill_value=False)
    rows: list[dict[str, Any]] = []
    for date, changes in change_grid.iterrows():
        if not bool(comparable_date.get(pd.Timestamp(date), False)):
            continue
        changes = changes.dropna()
        sources = (-changes).clip(lower=0)
        destinations = changes.clip(lower=0)
        rows.extend(
            def_cartesian_association_edges(
                pd.Timestamp(date),
                "ETR_ATTENTION_SHARE_CHANGE",
                sources,
                destinations,
                "MARKET_SHARE_CHANGE",
                config.external_node_id,
            )
        )
    return pd.DataFrame(rows)


def def_build_directional_flow_associations(
    conserved_view: pd.DataFrame,
    config: FlowTransferConfig = FlowTransferConfig(),
) -> pd.DataFrame:
    """Build lane-specific associations; different lanes are never summed."""

    if conserved_view.empty:
        return pd.DataFrame()
    if "AttentionShareStatus" not in conserved_view.columns:
        return pd.DataFrame()
    rows: list[dict[str, Any]] = []
    for date, day in conserved_view.groupby("Date", sort=True):
        # Directional amounts are distinct from ETR, but rotation associations
        # are a joint cross-group product.  A date that cannot establish the
        # complete ex-TSMC comparison universe is held in every lane.
        if not day["AttentionShareStatus"].eq("PASS").all():
            continue
        indexed = day.set_index("GroupId")
        for lane in config.directional_lanes:
            coverage_column = f"{lane}CoverageStatus"
            if coverage_column not in day.columns or not day[coverage_column].eq(
                "PASS_COMPLETE_DIRECTIONAL_COVERAGE"
            ).all():
                continue
            values = pd.to_numeric(indexed[lane], errors="coerce")
            if values.isna().any():
                continue
            sources = (-values).clip(lower=0)
            destinations = values.clip(lower=0)
            rows.extend(
                def_cartesian_association_edges(
                    pd.Timestamp(date),
                    lane,
                    sources,
                    destinations,
                    "SOURCE_CURRENCY_AMOUNT",
                    config.external_node_id,
                )
            )
    return pd.DataFrame(rows)


def def_build_rotation_association_matrix(
    conserved_view: pd.DataFrame,
    config: FlowTransferConfig = FlowTransferConfig(),
) -> pd.DataFrame:
    attention = def_build_attention_transfer_associations(conserved_view, config)
    directional = def_build_directional_flow_associations(conserved_view, config)
    available = [frame for frame in (attention, directional) if not frame.empty]
    if not available:
        return pd.DataFrame()
    result = pd.concat(available, ignore_index=True)
    return result.sort_values(
        ["Date", "Lane", "SourceGroupId", "DestinationGroupId"], kind="stable"
    ).reset_index(drop=True)


# =============================================================================
# def 05 CONSERVATION / CONTRACT VALIDATION
# =============================================================================


def def_validate_flow_conservation(
    prepared_stock: pd.DataFrame,
    allocations: pd.DataFrame,
    conserved_view: pd.DataFrame,
    associations: pd.DataFrame,
    config: FlowTransferConfig = FlowTransferConfig(),
) -> dict[str, Any]:
    if allocations.empty or conserved_view.empty:
        return {
            "EngineId": ENGINE_ID,
            "EngineVersion": ENGINE_VERSION,
            "Status": "HOLD_NO_APPLIED_ALLOCATION_SESSION",
            "BadTickerAllocationSums": 0,
            "BadETRConservationDates": 0,
            "NonLaggedAllocationRows": 0,
            "BadMembershipEffectiveTimingRows": 0,
            "BadAssociationLabels": 0,
            "PartialOrInvalidETRCoverageDates": 0,
            "HeldAttentionShareRows": 0,
            "AssociationRowsOnHeldETRDates": 0,
            "HeldETRCoverageDateList": [],
            "PartialOrInvalidDirectionalLaneDates": 0,
            "AssociationRowsOnHeldDirectionalLaneDates": 0,
            "HeldDirectionalLaneDateList": [],
            "NotSuppliedDirectionalLanes": [],
            "ForbiddenScoreColumns": [],
            "AssociationRows": int(len(associations)),
            "Interpretation": "ROTATION_ASSOCIATION_NOT_CAUSAL_TRANSFER",
        }
    stock = prepared_stock.loc[~prepared_stock["IsTSMC"]].copy() if config.exclude_tsmc else prepared_stock.copy()
    allocation_sums = allocations.groupby(["AppliedDate", "Ticker"])["AllocationWeight"].sum()
    bad_allocation = int(
        (~np.isclose(allocation_sums.to_numpy(dtype=float), 1.0, atol=ALLOCATION_TOLERANCE)).sum()
    )

    market_etr = stock.groupby("Date")[config.etr_column].sum(min_count=1)
    group_etr = conserved_view.groupby("Date")["GroupETR"].sum(min_count=1)
    common_dates = market_etr.index.intersection(group_etr.index)
    difference = (market_etr.loc[common_dates] - group_etr.loc[common_dates]).abs()
    bad_etr_dates = int((difference > CONSERVATION_TOLERANCE * market_etr.loc[common_dates].abs().clip(lower=1.0)).sum())

    nonlagged = int(
        (
            allocations["AppliedDate"].notna()
            & allocations["AllocationDate"].ge(allocations["AppliedDate"])
        ).sum()
    )
    if "MembershipAsOfDate" not in allocations.columns:
        bad_membership_timing = int(len(allocations))
    else:
        membership_as_of = pd.to_datetime(
            allocations["MembershipAsOfDate"], errors="coerce"
        ).dt.normalize()
        applied = pd.to_datetime(
            allocations["AppliedDate"], errors="coerce"
        ).dt.normalize()
        bad_membership_timing = int(
            (membership_as_of.isna() | applied.isna() | membership_as_of.ne(applied)).sum()
        )
    bad_association_label = (
        int(associations["AssociationType"].ne("ROTATION_ASSOCIATION").sum())
        if not associations.empty
        else 0
    )
    if "AttentionShareStatus" in conserved_view.columns:
        valid_coverage_by_date = conserved_view.groupby("Date", sort=True).apply(
            lambda day: bool(
                day["AttentionShareStatus"].eq("PASS").all()
                and pd.to_numeric(day["AttentionShare"], errors="coerce").notna().all()
            ),
            include_groups=False,
        )
    else:
        valid_coverage_by_date = pd.Series(
            False,
            index=pd.DatetimeIndex(conserved_view["Date"].dropna().unique()).sort_values(),
            dtype=bool,
        )
    held_dates = pd.DatetimeIndex(valid_coverage_by_date.index[~valid_coverage_by_date])
    held_attention_rows = int(
        conserved_view.get(
            "AttentionShareStatus",
            pd.Series("HOLD_MISSING_COVERAGE_PROVENANCE", index=conserved_view.index),
        ).ne("PASS").sum()
    )
    associations_on_held_dates = (
        int(pd.to_datetime(associations["Date"], errors="coerce").isin(held_dates).sum())
        if not associations.empty and "Date" in associations.columns
        else 0
    )
    held_directional_lane_dates: list[tuple[pd.Timestamp, str]] = []
    not_supplied_lanes: list[str] = []
    for lane in config.directional_lanes:
        coverage_column = f"{lane}CoverageStatus"
        if coverage_column not in conserved_view.columns:
            held_directional_lane_dates.extend(
                (pd.Timestamp(date), lane)
                for date in pd.DatetimeIndex(
                    conserved_view["Date"].dropna().unique()
                )
            )
            continue
        statuses = conserved_view[coverage_column].astype(str)
        if statuses.eq("NOT_SUPPLIED_NO_ASSOCIATION").all():
            not_supplied_lanes.append(lane)
            continue
        for date, day in conserved_view.groupby("Date", sort=True):
            if not day[coverage_column].eq(
                "PASS_COMPLETE_DIRECTIONAL_COVERAGE"
            ).all():
                held_directional_lane_dates.append((pd.Timestamp(date), lane))
    held_directional_keys = set(held_directional_lane_dates)
    associations_on_held_directional = 0
    if not associations.empty and {"Date", "Lane"}.issubset(associations.columns):
        associations_on_held_directional = int(
            sum(
                (pd.Timestamp(row.Date), str(row.Lane)) in held_directional_keys
                for row in associations[["Date", "Lane"]].itertuples(index=False)
            )
        )
    forbidden_columns = [
        column
        for column in list(allocations.columns) + list(conserved_view.columns) + list(associations.columns)
        if "score" in column.lower()
    ]
    structural_pass = (
        bad_allocation == 0
        and bad_etr_dates == 0
        and nonlagged == 0
        and bad_membership_timing == 0
        and bad_association_label == 0
        and associations_on_held_dates == 0
        and associations_on_held_directional == 0
        and not forbidden_columns
    )
    if not structural_pass:
        status = "FAIL"
    elif len(held_dates):
        status = "HOLD_PARTIAL_OR_INVALID_ETR_COVERAGE"
    elif held_directional_lane_dates:
        status = "HOLD_PARTIAL_OR_INVALID_DIRECTIONAL_COVERAGE"
    else:
        status = "PASS"
    return {
        "EngineId": ENGINE_ID,
        "EngineVersion": ENGINE_VERSION,
        "Status": status,
        "BadTickerAllocationSums": bad_allocation,
        "BadETRConservationDates": bad_etr_dates,
        "NonLaggedAllocationRows": nonlagged,
        "BadMembershipEffectiveTimingRows": bad_membership_timing,
        "BadAssociationLabels": bad_association_label,
        "PartialOrInvalidETRCoverageDates": int(len(held_dates)),
        "HeldAttentionShareRows": held_attention_rows,
        "AssociationRowsOnHeldETRDates": associations_on_held_dates,
        "HeldETRCoverageDateList": [
            pd.Timestamp(date).strftime("%Y-%m-%d") for date in held_dates
        ],
        "PartialOrInvalidDirectionalLaneDates": len(held_directional_lane_dates),
        "AssociationRowsOnHeldDirectionalLaneDates": associations_on_held_directional,
        "HeldDirectionalLaneDateList": [
            f"{pd.Timestamp(date):%Y-%m-%d}|{lane}"
            for date, lane in held_directional_lane_dates
        ],
        "NotSuppliedDirectionalLanes": sorted(not_supplied_lanes),
        "ForbiddenScoreColumns": forbidden_columns,
        "AssociationRows": int(len(associations)),
        "Interpretation": "ROTATION_ASSOCIATION_NOT_CAUSAL_TRANSFER",
    }


def def_build_flow_transfer_outputs(
    stock_daily: pd.DataFrame,
    membership: pd.DataFrame,
    config: FlowTransferConfig = FlowTransferConfig(),
) -> dict[str, Any]:
    prepared_stock = def_prepare_transfer_stock_panel(stock_daily, config)
    prepared_membership = def_prepare_transfer_membership(membership, config)
    views = def_build_story_and_conserved_views(prepared_stock, prepared_membership, config)
    associations = def_build_rotation_association_matrix(views["conserved_view"], config)
    quality = def_validate_flow_conservation(
        prepared_stock,
        views["conserved_ledger"],
        views["conserved_view"],
        associations,
        config,
    )
    return {
        "prepared_stock": prepared_stock,
        "prepared_membership": prepared_membership,
        **views,
        "rotation_associations": associations,
        "quality": quality,
    }


# =============================================================================
# def 06 SELF-TEST
# =============================================================================


def def_build_synthetic_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    dates = pd.bdate_range("2026-01-02", periods=7)
    tickers = ["1101.TW", "2308.TW", "3017.TW", "2330.TW"]
    rows: list[dict[str, Any]] = []
    for date_number, date in enumerate(dates):
        etr_values = {
            "1101.TW": 100.0 + 12.0 * date_number,
            "2308.TW": 180.0 - 8.0 * date_number,
            "3017.TW": 70.0 + 2.0 * date_number,
            "2330.TW": 1000.0 + 30.0 * date_number,
        }
        for ticker_number, ticker in enumerate(tickers):
            direction = 1.0 if ticker in ("1101.TW", "3017.TW") else -1.0
            rows.append(
                {
                    "Date": date,
                    "Ticker": ticker,
                    "ETR": etr_values[ticker],
                    "ForeignNetAmount": direction * (10.0 + date_number),
                    "InvestmentTrustNetAmount": direction * (4.0 + ticker_number),
                    "DealerProprietaryNetAmount": direction * 2.0,
                    "DealerHedgeNetAmount": -direction,
                    "MarginFinancingChangeAmount": direction * 3.0,
                    "ShortSellingChangeAmount": -direction * 2.0,
                    "ETFActiveValue": direction * 5.0,
                }
            )
    membership = pd.DataFrame(
        [
            {"GroupId": "CEMENT", "GroupName": "水泥", "Ticker": "1101.TW", "Decision": "APPROVED"},
            {"GroupId": "POWER", "GroupName": "電源", "Ticker": "2308.TW", "Decision": "APPROVED"},
            {"GroupId": "AI_COOL", "GroupName": "AI散熱", "Ticker": "2308.TW", "Decision": "APPROVED"},
            {"GroupId": "AI_COOL", "GroupName": "AI散熱", "Ticker": "3017.TW", "Decision": "APPROVED", "ExposureShare": 0.8},
            {"GroupId": "FOUNDRY", "GroupName": "晶圓代工", "Ticker": "2330.TW", "Decision": "APPROVED"},
        ]
    )
    stock = pd.DataFrame(rows)
    stock["IsLimitUpLocked"] = False
    stock["IsLimitDownLocked"] = False
    stock.attrs["FullMarketGateStatus"] = REQUIRED_FULL_MARKET_GATE_STATUS
    return stock, membership


def def_run_self_test() -> dict[str, Any]:
    stock, membership = def_build_synthetic_inputs()
    result = def_build_flow_transfer_outputs(stock, membership)
    raw_ledger = result["raw_story_ledger"]
    conserved_ledger = result["conserved_ledger"]
    raw = result["raw_story_view"]
    conserved = result["conserved_view"]
    associations = result["rotation_associations"]

    assert result["quality"]["Status"] == "PASS"
    assert (conserved_ledger.groupby(["AppliedDate", "Ticker"])["AllocationWeight"].sum().round(12) == 1.0).all()
    assert (conserved_ledger["AllocationDate"] < conserved_ledger["AppliedDate"]).all()
    assert raw_ledger.loc[raw_ledger["Ticker"].eq("2308"), "GroupId"].nunique() == 2
    assert conserved_ledger.loc[conserved_ledger["Ticker"].eq("2308"), "AllocationWeight"].drop_duplicates().eq(0.5).all()
    assert "UNMAPPED" in set(conserved_ledger["GroupId"])
    assert "2330" not in set(conserved_ledger["Ticker"])
    assert raw.groupby("Date")["GroupETR"].sum().gt(raw.groupby("Date")["MarketETRExTSMC"].first()).any()
    assert conserved.groupby("Date")["GroupETR"].sum().round(10).equals(
        conserved.groupby("Date")["MarketETRExTSMC"].first().round(10)
    )
    assert associations["AssociationType"].eq("ROTATION_ASSOCIATION").all()
    assert not associations["CausalClaim"].any()
    assert not any("score" in column.lower() for column in associations.columns)
    return {
        "Status": "PASS",
        "Assertions": 12,
        "Quality": result["quality"],
        "RawViewRows": int(len(raw)),
        "ConservedViewRows": int(len(conserved)),
        "AssociationRows": int(len(associations)),
    }


if __name__ == "__main__":
    print(def_run_self_test())
