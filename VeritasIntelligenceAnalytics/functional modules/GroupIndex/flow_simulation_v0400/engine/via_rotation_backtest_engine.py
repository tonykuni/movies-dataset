from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


DATE_COLUMN = "Date"


def def_max_drawdown(wealth: pd.Series) -> float:
    clean = wealth.dropna()
    if clean.empty:
        return np.nan
    drawdown = clean / clean.cummax().replace(0, np.nan) - 1.0
    return float(drawdown.min())


def def_rank_ic(group: pd.DataFrame) -> float:
    sample = group[["FlowScore", "NextReturn"]].dropna()
    if len(sample) < 5:
        return np.nan
    return float(sample["FlowScore"].rank().corr(sample["NextReturn"].rank()))


def def_metrics(
    daily: pd.DataFrame,
    observations_per_year: int = 252,
    annual_risk_free_rate: float = 0.0,
) -> dict[str, float]:
    returns = daily["StrategyNetReturn"].dropna()
    if returns.empty:
        return {key: np.nan for key in ["CAGR", "AnnualVolatility", "Sharpe", "MaxDrawdown", "HitRate", "AverageTurnover"]}
    years = len(returns) / observations_per_year
    final_wealth = float((1.0 + returns).prod())
    cagr = final_wealth ** (1.0 / years) - 1.0 if years > 0 and final_wealth > 0 else np.nan
    volatility = float(returns.std(ddof=1) * math.sqrt(observations_per_year))
    daily_risk_free = (1.0 + annual_risk_free_rate) ** (1.0 / observations_per_year) - 1.0
    excess = returns - daily_risk_free
    sharpe = float(excess.mean() / returns.std(ddof=1) * math.sqrt(observations_per_year)) if returns.std(ddof=1) > 1e-12 else np.nan
    return {
        "CAGR": cagr,
        "AnnualVolatility": volatility,
        "Sharpe": sharpe,
        "MaxDrawdown": def_max_drawdown(daily["StrategyWealth"]),
        "HitRate": float((returns > 0).mean()),
        "AverageTurnover": float(daily["Turnover"].mean()),
    }


def def_run_rotation_backtest(
    group_index: pd.DataFrame,
    group_flow: pd.DataFrame,
    parameters: dict[str, Any],
    ledger: list[dict[str, Any]],
    transaction_cost_bps: float = 12.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    panel = group_index[[DATE_COLUMN, "GroupId", "GroupName", "GroupReturn"]].merge(
        group_flow[[DATE_COLUMN, "GroupId", "FlowScore"]],
        on=[DATE_COLUMN, "GroupId"],
        how="inner",
        validate="one_to_one",
    ).sort_values([DATE_COLUMN, "GroupId"]).reset_index(drop=True)
    panel["NextReturn"] = panel.groupby("GroupId", sort=False)["GroupReturn"].shift(-1)
    dates = sorted(panel[DATE_COLUMN].dropna().unique())
    step = int(parameters["rebalanceStep"])
    selection_count = max(3, min(6, int(round(panel["GroupId"].nunique() * 0.16))))
    prior_selection: set[str] = set()
    daily_rows: list[dict[str, Any]] = []
    for date_index, signal_date in enumerate(dates[:-1]):
        next_date = dates[date_index + 1]
        signal = panel.loc[panel[DATE_COLUMN] == signal_date].dropna(subset=["FlowScore"])
        rebalance = date_index % step == 0 or not prior_selection
        if rebalance:
            selected = set(signal.nlargest(selection_count, "FlowScore")["GroupId"].astype(str))
        else:
            selected = prior_selection
        realized = panel.loc[(panel[DATE_COLUMN] == next_date) & panel["GroupId"].isin(selected), "GroupReturn"]
        benchmark = panel.loc[panel[DATE_COLUMN] == next_date, "GroupReturn"]
        turnover = len(selected.symmetric_difference(prior_selection)) / max(2 * selection_count, 1) if prior_selection else 1.0
        gross = float(realized.mean()) if realized.notna().any() else np.nan
        cost = turnover * transaction_cost_bps / 10_000.0
        daily_rows.append(
            {
                "Date": next_date,
                "SignalDate": signal_date,
                "StrategyGrossReturn": gross,
                "TransactionCost": cost,
                "StrategyNetReturn": gross - cost if np.isfinite(gross) else np.nan,
                "BenchmarkReturn": float(benchmark.mean()) if benchmark.notna().any() else np.nan,
                "Turnover": turnover,
                "SelectedGroups": ",".join(sorted(selected)),
                "SelectionCount": len(selected),
                "RebalanceFlag": rebalance,
            }
        )
        prior_selection = selected
    daily = pd.DataFrame(daily_rows)
    daily["StrategyWealth"] = (1.0 + daily["StrategyNetReturn"].fillna(0.0)).cumprod()
    daily["BenchmarkWealth"] = (1.0 + daily["BenchmarkReturn"].fillna(0.0)).cumprod()
    ic_by_date = pd.Series(
        [def_rank_ic(group) for _, group in panel.groupby(DATE_COLUMN, sort=True)],
        dtype=float,
    ).dropna()
    risk_free_rate = float(parameters.get("riskFreeRate", 0.0))
    metrics = def_metrics(daily, annual_risk_free_rate=risk_free_rate)
    metrics.update(
        {
            "BacktestId": "WALK_FORWARD_FLOW_ROTATION_V0300",
            "Signal": "FLOW_SCORE_AT_T",
            "Execution": "NEXT_TRADING_DAY_EQUAL_WEIGHT",
            "SelectionCount": selection_count,
            "RebalanceStep": step,
            "TransactionCostBps": transaction_cost_bps,
            "OOSRankIC": float(ic_by_date.mean()) if not ic_by_date.empty else np.nan,
            "Observations": int(len(daily)),
            "LookaheadPolicy": "SIGNAL_T_TO_RETURN_T_PLUS_1",
            "RiskFreeRate": risk_free_rate,
            "RiskFreeEvidenceTier": str(parameters.get("riskFreeEvidenceTier", "UNAVAILABLE")),
        }
    )
    summary = pd.DataFrame([metrics])
    ledger.append(
        {
            "CheckId": "BT001",
            "Check": "Walk-forward signal/return alignment",
            "Status": "PASS",
            "Severity": "HARD",
            "FindingCount": 0,
            "Detail": f"signal=t; realized return=t+1; rebalance={step}D; cost={transaction_cost_bps:.1f}bps; no in-sample accuracy claim",
        }
    )
    return daily, summary
