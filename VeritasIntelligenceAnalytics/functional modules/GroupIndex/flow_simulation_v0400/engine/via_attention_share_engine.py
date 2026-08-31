from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

from typing import Any

import numpy as np
import pandas as pd


ATTENTION_METHOD_ID = "M-1A"
ATTENTION_METHOD_VERSION = "1.1"


def def_compute_attention_share(
    stock_turnover: pd.DataFrame,
    market_turnover: pd.DataFrame,
    *,
    tsmc_ticker: str = "2330.TW",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compute non-day-trade Attention Share; fail closed on an incomplete market denominator."""
    stock_required = {"Date", "Ticker", "TurnoverValue", "DayTradeTurnover"}
    market_required = {"Date", "Market", "GrossTurnoverValue", "DayTradeTurnoverValue"}
    missing_stock = stock_required.difference(stock_turnover.columns)
    missing_market = market_required.difference(market_turnover.columns)
    if missing_stock or missing_market:
        raise ValueError(
            f"Attention Share missing columns: stock={sorted(missing_stock)}, market={sorted(missing_market)}"
        )
    stock = stock_turnover.copy()
    market = market_turnover.copy()
    stock["Date"] = pd.to_datetime(stock["Date"], errors="raise")
    market["Date"] = pd.to_datetime(market["Date"], errors="raise")
    if "AssetType" not in stock.columns:
        stock["AssetType"] = "EQUITY"
    stock["IncludedAsset"] = stock["AssetType"].astype(str).str.upper().eq("EQUITY")
    stock["StockNonDayTrade"] = stock["TurnoverValue"] - stock["DayTradeTurnover"]
    if "DayTradeEvidenceTier" not in stock.columns:
        stock["DayTradeEvidenceTier"] = "DERIVED"

    denominator_rows: list[dict[str, Any]] = []
    for date, daily_market in market.groupby("Date", sort=True):
        markets = set(daily_market["Market"].astype(str).str.upper())
        numeric_complete = daily_market[["GrossTurnoverValue", "DayTradeTurnoverValue"]].notna().all().all()
        tsmc = stock.loc[(stock["Date"] == date) & (stock["Ticker"] == tsmc_ticker)]
        complete = markets.issuperset({"TWSE", "TPEX"}) and numeric_complete and len(tsmc) == 1
        gross = float(daily_market["GrossTurnoverValue"].sum()) if numeric_complete else np.nan
        day_trade = float(daily_market["DayTradeTurnoverValue"].sum()) if numeric_complete else np.nan
        tsmc_non_day = float(tsmc["StockNonDayTrade"].iloc[0]) if len(tsmc) == 1 else np.nan
        net = gross - day_trade - tsmc_non_day if complete else np.nan
        if not complete:
            status = "BLOCKED_INCOMPLETE_BOTH_MARKETS_OR_TSMC"
        elif not np.isfinite(net) or net <= 0:
            status = "BLOCKED_NONPOSITIVE_DENOMINATOR"
        else:
            status = "PASS"
        denominator_rows.append(
            {
                "Date": date,
                "BothMarketsGross": gross,
                "BothMarketsDayTrade": day_trade,
                "TSMCNonDayTrade": tsmc_non_day,
                "NetDenominator": net,
                "DenominatorStatus": status,
                "MethodId": ATTENTION_METHOD_ID,
                "MethodVersion": ATTENTION_METHOD_VERSION,
            }
        )
    denominator = pd.DataFrame(denominator_rows)
    output = stock.merge(denominator, on="Date", how="left", validate="many_to_one")
    valid = output["DenominatorStatus"].eq("PASS") & output["IncludedAsset"]
    non_tsmc = valid & output["Ticker"].ne(tsmc_ticker)
    output["AttentionShareRaw"] = np.nan
    output.loc[non_tsmc, "AttentionShareRaw"] = (
        output.loc[non_tsmc, "StockNonDayTrade"] / output.loc[non_tsmc, "NetDenominator"]
    )
    output["TSMCBothMarketShare"] = np.nan
    tsmc_mask = valid & output["Ticker"].eq(tsmc_ticker)
    tsmc_base = output.loc[tsmc_mask, "BothMarketsGross"] - output.loc[tsmc_mask, "BothMarketsDayTrade"]
    output.loc[tsmc_mask, "TSMCBothMarketShare"] = output.loc[tsmc_mask, "TSMCNonDayTrade"] / tsmc_base
    output["AttentionStatus"] = np.where(
        ~output["IncludedAsset"],
        "EXCLUDED_NON_EQUITY",
        np.where(output["Ticker"].eq(tsmc_ticker), "TSMC_REPORTED_SEPARATELY", output["DenominatorStatus"]),
    )
    output["MethodId"] = ATTENTION_METHOD_ID
    output["MethodVersion"] = ATTENTION_METHOD_VERSION
    output["EvidenceTier"] = output["DayTradeEvidenceTier"].fillna("DERIVED")
    return output, denominator


def def_compute_group_attention_score(
    attention_rows: pd.DataFrame,
    membership: pd.DataFrame,
    *,
    smoothing_days: int = 20,
) -> pd.DataFrame:
    """Aggregate raw M-1A shares, smooth by group, then percentile-score cross-sectionally."""
    required_attention = {"Date", "Ticker", "AttentionShareRaw", "AttentionStatus"}
    required_membership = {"GroupName", "Ticker"}
    if not required_attention.issubset(attention_rows.columns) or not required_membership.issubset(membership.columns):
        raise ValueError("Group Attention Score inputs are missing required columns")
    unique_membership = membership[["GroupName", "Ticker"]].drop_duplicates()
    eligible = attention_rows.loc[
        attention_rows["AttentionStatus"].eq("PASS") & attention_rows["AttentionShareRaw"].notna()
    ]
    joined = eligible.merge(unique_membership, on="Ticker", how="inner", validate="many_to_many")
    daily = joined.groupby(["Date", "GroupName"], as_index=False)["AttentionShareRaw"].sum()
    daily = daily.sort_values(["GroupName", "Date"]).reset_index(drop=True)
    daily["AttentionShareMA20"] = daily.groupby("GroupName", sort=False)["AttentionShareRaw"].transform(
        lambda series: series.rolling(smoothing_days, min_periods=smoothing_days).mean()
    )
    daily["AttentionScorePct"] = daily.groupby("Date", sort=False)["AttentionShareMA20"].rank(
        method="average", pct=True
    )
    daily["MethodId"] = ATTENTION_METHOD_ID
    daily["MethodVersion"] = ATTENTION_METHOD_VERSION
    return daily
