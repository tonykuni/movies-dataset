from __future__ import annotations

"""Point-in-time event study for story-group rotation evidence.

Signals are observed after session T and enter no earlier than the next
tradable session.  The engine evaluates evidence states; it does not optimize
or rank a composite score.
"""

# =============================================================================
# def 00 PARAMETERS — evaluation/governance controls only
# =============================================================================

from dataclasses import dataclass, replace
from typing import Sequence

import numpy as np
import pandas as pd

try:
    from .via_fx_context_engine import (
        SHA256_HEX_PATTERN,
        def_official_taiwan_10y_provenance_mask,
    )
    from .via_time_utils import def_available_at_utc, def_local_calendar_date
except ImportError:  # standalone script/import from the engine directory
    from via_fx_context_engine import (
        SHA256_HEX_PATTERN,
        def_official_taiwan_10y_provenance_mask,
    )
    from via_time_utils import def_available_at_utc, def_local_calendar_date


ENGINE_ID = "VIA_PIT_ROTATION_BACKTEST_V0500"
ENGINE_VERSION = "0.5.0"
DEFAULT_START_DATE = "2024-01-01"
DEFAULT_WARMUP_START_DATE = "2023-01-01"
DEFAULT_WINDOWS = (60, 120, 240)
DEFAULT_HORIZONS = (1, 3, 5, 20)
DEFAULT_EVALUATION_START_DATES = ("2024-01-01", "2025-01-01", "2026-01-01")
TRADING_DAYS_PER_YEAR = 252


@dataclass(frozen=True)
class BacktestConfig:
    start_date: str = DEFAULT_START_DATE
    end_date: str | None = None
    windows: tuple[int, ...] = DEFAULT_WINDOWS
    horizons: tuple[int, ...] = DEFAULT_HORIZONS
    evaluation_start_dates: tuple[str, ...] = DEFAULT_EVALUATION_START_DATES
    round_trip_cost_bps: float = 0.0
    execution_price_policy: str = "NEXT_SESSION_CLOSE_CONSERVATIVE"
    warmup_start_date: str = DEFAULT_WARMUP_START_DATE


def def_prepare_group_indices(index_daily: pd.DataFrame) -> pd.DataFrame:
    index_daily = index_daily.copy()
    if "IndexMethod" not in index_daily.columns and "Method" in index_daily.columns:
        index_daily = index_daily.rename(columns={"Method": "IndexMethod"})
    required = {"Date", "GroupId", "IndexMethod", "IndexLevel", "IndexStatus"}
    missing = sorted(required.difference(index_daily.columns))
    if missing:
        raise ValueError(f"group index input missing required columns: {missing}")
    frame = index_daily.copy()
    frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce").dt.normalize()
    frame["IndexLevel"] = pd.to_numeric(frame["IndexLevel"], errors="coerce")
    invalid = frame["Date"].isna() | frame["GroupId"].isna() | frame["IndexLevel"].le(0)
    if invalid.any():
        raise ValueError(f"group index input has {int(invalid.sum())} invalid rows")
    duplicate = frame.duplicated(["Date", "GroupId", "IndexMethod"], keep=False)
    if duplicate.any():
        raise ValueError(f"group index input has {int(duplicate.sum())} duplicate keys")
    return frame.sort_values(["GroupId", "IndexMethod", "Date"]).reset_index(drop=True)


def def_prepare_risk_free(risk_free_daily: pd.DataFrame) -> pd.DataFrame:
    risk_free_daily = risk_free_daily.copy()
    if "Date" not in risk_free_daily.columns and "ObservationDate" in risk_free_daily.columns:
        risk_free_daily = risk_free_daily.rename(columns={"ObservationDate": "Date"})
    required = {"Date", "Taiwan10YYield", "AvailableAt"}
    missing = sorted(required.difference(risk_free_daily.columns))
    if missing:
        raise ValueError(f"risk-free input missing required columns: {missing}")
    frame = risk_free_daily.copy()
    frame["Date"] = frame["Date"].map(def_local_calendar_date)
    frame["AvailableAt"] = frame["AvailableAt"].map(def_available_at_utc)
    frame["Taiwan10YYield"] = pd.to_numeric(frame["Taiwan10YYield"], errors="coerce")
    for column in ("Source", "SourceURL"):
        if column in frame.columns:
            frame[column] = frame[column].fillna("").astype(str).str.strip()
    for column in ("SourceAuthority", "YieldUnit", "InstrumentId"):
        if column in frame.columns:
            frame[column] = (
                frame[column].fillna("").astype(str).str.strip().str.upper()
            )
    if "SourcePayloadHash" in frame.columns:
        frame["SourcePayloadHash"] = (
            frame["SourcePayloadHash"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.lower()
        )
    # Always reconstruct source status from canonical row evidence.  A caller-
    # supplied RiskFreeSourceStatus must never bypass provenance validation.
    verified = def_official_taiwan_10y_provenance_mask(frame)
    frame["RiskFreeSourceStatus"] = np.where(
        verified & np.isfinite(frame["Taiwan10YYield"]),
        "OFFICIAL_TAIWAN_10Y_POINT_IN_TIME",
        "HOLD_UNVERIFIED_OR_MISSING_TAIWAN_10Y_SOURCE",
    )
    frame["SourcePayloadIntegrityStatus"] = np.where(
        frame["SourcePayloadHash"]
        .fillna("")
        .astype(str)
        .str.strip()
        .map(lambda value: bool(SHA256_HEX_PATTERN.fullmatch(value))),
        "SHA256_PAYLOAD_DIGEST_PRESENT_FORMAT_VALID_NOT_SOURCE_SIGNATURE",
        "HOLD_MISSING_OR_INVALID_SHA256_PAYLOAD_DIGEST",
    )
    invalid = frame["Date"].isna() | frame["AvailableAt"].isna()
    if invalid.any():
        raise ValueError(f"risk-free input has {int(invalid.sum())} invalid PIT rows")
    if frame["Taiwan10YYield"].dropna().le(-100).any():
        raise ValueError("Taiwan10YYield must be greater than -100 percent")
    supplied_yield = frame.loc[
        frame["Taiwan10YYield"].notna(), "Taiwan10YYield"
    ]
    if (~np.isfinite(supplied_yield)).any():
        raise ValueError("Taiwan10YYield must be finite when supplied")
    # Macro-context tables are keyed by the market decision date while retaining
    # the actual source observation date.  Preserve that provenance instead of
    # relabelling a stale yield as a fresh observation on every trading day.
    if "ObservationDate" in frame.columns:
        frame["SourceObservationDate"] = frame["ObservationDate"].map(
            def_local_calendar_date
        )
    else:
        frame["SourceObservationDate"] = frame["Date"]
    available_local_date = (
        frame["AvailableAt"]
        .dt.tz_convert("Asia/Taipei")
        .dt.tz_localize(None)
        .dt.normalize()
    )
    frame["UsableDate"] = pd.concat(
        [frame["SourceObservationDate"], available_local_date], axis=1
    ).max(axis=1)

    materialized: list[dict[str, object]] = []
    for usable_date in sorted(frame["UsableDate"].dropna().unique()):
        known = frame.loc[frame["UsableDate"].le(usable_date)].copy()
        known = (
            known.sort_values(["SourceObservationDate", "AvailableAt"])
            .drop_duplicates("SourceObservationDate", keep="last")
            .sort_values(["SourceObservationDate", "AvailableAt"])
        )
        if known.empty:
            continue
        current = known.iloc[-1].to_dict()
        current["Date"] = pd.Timestamp(usable_date)
        materialized.append(current)
    result = pd.DataFrame(materialized)
    if result.empty:
        return result
    verified_yield = result["Taiwan10YYield"].where(
        result["RiskFreeSourceStatus"].eq("OFFICIAL_TAIWAN_10Y_POINT_IN_TIME")
    )
    result["DailyRiskFree"] = np.power(
        1.0 + verified_yield / 100.0,
        1.0 / TRADING_DAYS_PER_YEAR,
    ) - 1.0
    result["PointInTimeStatus"] = "LATEST_OBSERVATION_KNOWN_BY_USABLE_DATE"
    return result.sort_values("Date").drop_duplicates("Date", keep="last").reset_index(drop=True)


def def_attach_risk_free_to_dates(
    dates: Sequence[pd.Timestamp],
    risk_free: pd.DataFrame,
) -> pd.DataFrame:
    requested = pd.DataFrame({"Date": pd.DatetimeIndex(dates)})
    requested["_Order"] = np.arange(len(requested))
    joined = pd.merge_asof(
        requested.sort_values("Date"),
        risk_free[
            ["Date", "DailyRiskFree", "SourceObservationDate", "RiskFreeSourceStatus"]
        ].sort_values("Date"),
        on="Date",
        direction="backward",
        allow_exact_matches=True,
    )
    return joined.sort_values("_Order").drop(columns="_Order").reset_index(drop=True)


def def_signal_columns(config: BacktestConfig) -> tuple[str, ...]:
    return tuple(
        column
        for window in config.windows
        for column in (f"EarlyPositioningState_{window}D", f"EarlyExitState_{window}D")
    )


def def_long_signals(
    signal_daily: pd.DataFrame,
    config: BacktestConfig = BacktestConfig(),
) -> pd.DataFrame:
    required = {"Date", "GroupId", "SignalAvailableAt", "EffectiveDate"}
    missing = sorted(required.difference(signal_daily.columns))
    if missing:
        raise ValueError(f"signal input missing required columns: {missing}")
    available_columns = [column for column in def_signal_columns(config) if column in signal_daily]
    if not available_columns:
        raise ValueError("signal input contains no configured 60/120/240 state columns")
    frame = signal_daily.copy()
    frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce").dt.normalize()
    frame["SignalAvailableAt"] = frame["SignalAvailableAt"].map(def_available_at_utc)
    frame["EffectiveDate"] = pd.to_datetime(
        frame["EffectiveDate"], errors="coerce"
    ).dt.normalize()
    available_local_date = frame["SignalAvailableAt"].map(def_local_calendar_date)
    if (
        frame["EffectiveDate"].notna()
        & frame["EffectiveDate"].le(available_local_date)
    ).any():
        raise ValueError("signal effective date must be after its availability date")
    id_columns = [column for column in frame.columns if column not in available_columns]
    long = frame.melt(
        id_vars=id_columns,
        value_vars=available_columns,
        var_name="SignalLane",
        value_name="SignalState",
    )
    long["WindowDays"] = long["SignalLane"].str.extract(r"_(\d+)D$")[0].astype(int)
    actionable = {
        "DIRECTIONAL_ACCUMULATION_WATCH",
        "EARLY_EXIT_RISK",
    }
    long = long.loc[long["SignalState"].isin(actionable)].copy()
    long["SignalDirection"] = np.where(
        long["SignalState"].eq("DIRECTIONAL_ACCUMULATION_WATCH"), "POSITIVE", "NEGATIVE"
    )
    return long.sort_values(["GroupId", "EffectiveDate", "SignalLane"]).reset_index(drop=True)


def def_nonoverlapping_events(events: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Purge overlaps within group, method, signal, and directional lane."""

    group_columns = ["GroupId", "IndexMethod", "SignalLane"]
    if "DirectionalLane" in events.columns:
        group_columns.append("DirectionalLane")
    kept: list[pd.Series] = []
    for _, group in events.sort_values("ExecutionPosition").groupby(group_columns, sort=True):
        last_exit = -1
        for _, row in group.iterrows():
            position = int(row["ExecutionPosition"])
            if position <= last_exit:
                continue
            kept.append(row)
            last_exit = position + horizon
    return pd.DataFrame(kept).reset_index(drop=True) if kept else events.iloc[0:0].copy()


def def_compound_risk_free(
    dates: Sequence[pd.Timestamp],
    risk_free: pd.DataFrame,
) -> tuple[float, str]:
    aligned = def_attach_risk_free_to_dates(dates, risk_free)
    values = aligned["DailyRiskFree"]
    if values.isna().any():
        return np.nan, "HOLD_UNVERIFIED_OR_MISSING_TAIWAN_10Y_WITHIN_HORIZON"
    return float(np.prod(1.0 + values.to_numpy(dtype=float)) - 1.0), "PASS_OFFICIAL_TAIWAN_10Y"


def def_run_multi_horizon_event_study(
    signal_daily: pd.DataFrame,
    index_daily: pd.DataFrame,
    risk_free_daily: pd.DataFrame,
    config: BacktestConfig = BacktestConfig(),
) -> pd.DataFrame:
    """Evaluate signals at 1/3/5/20 sessions with PIT and overlap controls."""

    signals = def_long_signals(signal_daily, config)
    indices = def_prepare_group_indices(index_daily)
    risk_free = def_prepare_risk_free(risk_free_daily)
    start = pd.Timestamp(config.start_date)
    end = pd.Timestamp(config.end_date) if config.end_date else None
    signals = signals.loc[signals["EffectiveDate"].ge(start)]
    if end is not None:
        signals = signals.loc[
            signals["Date"].le(end) & signals["EffectiveDate"].le(end)
        ]
        # The event path is deliberately truncated before maturity is tested.
        # An event effective by the research cut may not borrow an exit price
        # (or risk-free observation) published after that cut.
        indices = indices.loc[indices["Date"].le(end)].copy()
        risk_free = risk_free.loc[risk_free["Date"].le(end)].copy()
    event_rows: list[dict[str, object]] = []
    for (group_id, method), path in indices.groupby(["GroupId", "IndexMethod"], sort=True):
        path = path.sort_values("Date").reset_index(drop=True)
        positions = {date: position for position, date in enumerate(path["Date"])}
        group_signals = signals.loc[signals["GroupId"].eq(group_id)].copy()
        for _, signal in group_signals.iterrows():
            execution_date = signal["EffectiveDate"]
            if execution_date not in positions:
                later = path.loc[path["Date"].ge(execution_date), "Date"]
                execution_date = later.iloc[0] if len(later) else pd.NaT
            if pd.isna(execution_date):
                continue
            position = int(positions[execution_date])
            tradable = bool(signal.get("TradableAtExecution", True))
            for horizon in config.horizons:
                exit_position = position + horizon
                if exit_position >= len(path):
                    maturity = "UNMATURED"
                    exit_date = pd.NaT
                    raw_return = np.nan
                elif not tradable:
                    maturity = "BLOCKED_NOT_TRADABLE"
                    exit_date = pd.NaT
                    raw_return = np.nan
                elif path.loc[position:exit_position, "IndexStatus"].ne("PASS").any():
                    maturity = "BLOCKED_INDEX_EVIDENCE"
                    exit_date = pd.NaT
                    raw_return = np.nan
                else:
                    maturity = "MATURED"
                    exit_date = path.at[exit_position, "Date"]
                    raw_return = float(path.at[exit_position, "IndexLevel"] / path.at[position, "IndexLevel"] - 1.0)
                rf_return, rf_status = (
                    def_compound_risk_free(path.loc[position + 1 : exit_position, "Date"], risk_free)
                    if maturity == "MATURED"
                    else (np.nan, "NOT_EVALUATED")
                )
                signed_return = raw_return if signal["SignalDirection"] == "POSITIVE" else -raw_return
                cost = config.round_trip_cost_bps / 10000.0
                event_rows.append(
                    {
                        "GroupId": group_id,
                        "IndexMethod": method,
                        "SignalDate": signal["Date"],
                        "SignalAvailableAt": signal["SignalAvailableAt"],
                        "ExecutionDate": execution_date,
                        "ExecutionPosition": position,
                        "ExitDate": exit_date,
                        "SignalLane": signal["SignalLane"],
                        "DirectionalLane": signal.get(
                            "DirectionalLane", "UNSPECIFIED_DIRECTIONAL_LANE"
                        ),
                        "SignalState": signal["SignalState"],
                        "SignalDirection": signal["SignalDirection"],
                        "WindowDays": int(signal["WindowDays"]),
                        "HorizonSessions": horizon,
                        "RawForwardReturn": raw_return,
                        "DirectionalForwardReturn": signed_return,
                        "Taiwan10YHorizonReturn": rf_return,
                        "ExcessDirectionalReturn": signed_return - rf_return if np.isfinite(signed_return) and np.isfinite(rf_return) else np.nan,
                        "AfterCostDirectionalReturn": signed_return - cost if np.isfinite(signed_return) else np.nan,
                        "MaturityStatus": maturity,
                        "RiskFreeStatus": rf_status,
                        "ExecutionPolicy": config.execution_price_policy,
                        "TaxonomyBacktestStatus": signal.get("TaxonomyBacktestStatus", "UNSPECIFIED_REQUIRES_VALID_FROM_REVIEW"),
                    }
                )
    all_events = pd.DataFrame(event_rows)
    if all_events.empty:
        return all_events
    purged: list[pd.DataFrame] = []
    for horizon, events in all_events.groupby("HorizonSessions", sort=True):
        mature = events.loc[events["MaturityStatus"].eq("MATURED")]
        immature = events.loc[~events["MaturityStatus"].eq("MATURED")]
        purged.append(def_nonoverlapping_events(mature, int(horizon)))
        purged.append(immature)
    result = pd.concat(purged, ignore_index=True, sort=False)
    return result.sort_values(["GroupId", "IndexMethod", "SignalDate", "HorizonSessions"]).reset_index(drop=True)


def def_summarize_event_study(events: pd.DataFrame) -> pd.DataFrame:
    """Summarize raw, excess and hit-rate evidence without Sharpe ranking."""

    mature = events.loc[events["MaturityStatus"].eq("MATURED")].copy()
    if mature.empty:
        return pd.DataFrame()
    period_keys = ["EvaluationStart"] if "EvaluationStart" in mature.columns else []
    # Split inside each evaluation period.  A global midpoint would leak the
    # longer 2024 replay into the 2025/2026 walk-forward labels.
    if period_keys:
        midpoint = mature.groupby(period_keys)["SignalDate"].transform(
            lambda values: values.sort_values().iloc[len(values) // 2]
        )
    else:
        midpoint = mature["SignalDate"].sort_values().iloc[len(mature) // 2]
    mature["WalkForwardHalf"] = np.where(
        mature["SignalDate"].le(midpoint), "FIRST_HALF", "SECOND_HALF"
    )
    directional_keys = (
        ["DirectionalLane"] if "DirectionalLane" in mature.columns else []
    )
    keys = period_keys + directional_keys + [
        "IndexMethod",
        "SignalState",
        "WindowDays",
        "HorizonSessions",
        "WalkForwardHalf",
    ]
    summary = (
        mature.groupby(keys, as_index=False)
        .agg(
            EventCount=("DirectionalForwardReturn", "count"),
            MeanDirectionalReturn=("DirectionalForwardReturn", "mean"),
            MedianDirectionalReturn=("DirectionalForwardReturn", "median"),
            PositiveHitRate=("DirectionalForwardReturn", lambda values: float(values.gt(0).mean())),
            MeanExcessReturn=("ExcessDirectionalReturn", "mean"),
            RiskFreeCoverage=("RiskFreeStatus", lambda values: float(values.eq("PASS_OFFICIAL_TAIWAN_10Y").mean())),
        )
    )
    summary["SelectionPolicy"] = "NO_COMPOSITE_SCORE_NO_BEST_METHOD_POST_SELECTION"
    return summary


def def_run_multi_period_event_study(
    signal_daily: pd.DataFrame,
    index_daily: pd.DataFrame,
    risk_free_daily: pd.DataFrame,
    config: BacktestConfig = BacktestConfig(),
) -> pd.DataFrame:
    """Replay the same PIT event study from 2024, 2025 and 2026 starts."""

    outputs: list[pd.DataFrame] = []
    for start_date in config.evaluation_start_dates:
        period_config = replace(config, start_date=start_date)
        events = def_run_multi_horizon_event_study(
            signal_daily,
            index_daily,
            risk_free_daily,
            period_config,
        )
        if events.empty:
            continue
        events.insert(0, "EvaluationStart", pd.Timestamp(start_date))
        events.insert(
            1,
            "EvaluationEnd",
            pd.Timestamp(config.end_date) if config.end_date else pd.NaT,
        )
        outputs.append(events)
    return pd.concat(outputs, ignore_index=True, sort=False) if outputs else pd.DataFrame()


def def_compute_index_performance(
    index_daily: pd.DataFrame,
    risk_free_daily: pd.DataFrame,
    benchmark_daily: pd.DataFrame | None = None,
    config: BacktestConfig = BacktestConfig(),
) -> pd.DataFrame:
    """Publish parallel period evidence; never rank or pick a winning method."""

    indices = def_prepare_group_indices(index_daily)
    risk_free = def_prepare_risk_free(risk_free_daily)
    evaluation_end = (
        pd.Timestamp(config.end_date) if config.end_date else indices["Date"].max()
    )
    if config.end_date:
        # Keep the performance function safe when called directly with an
        # uncapped live table; orchestration is not a substitute for this PIT
        # boundary.
        indices = indices.loc[indices["Date"].le(evaluation_end)].copy()
        risk_free = risk_free.loc[risk_free["Date"].le(evaluation_end)].copy()
    benchmark = None
    if benchmark_daily is not None and not benchmark_daily.empty:
        benchmark = benchmark_daily.copy()
        if "MarketReturn" not in benchmark.columns:
            candidate = next(
                (
                    column
                    for column in (
                        "MarketReturnExTSMCLaggedCap",
                        "MarketReturnExTSMCLaggedETR",
                        "BenchmarkReturn",
                    )
                    if column in benchmark.columns
                ),
                None,
            )
            if candidate is None:
                raise ValueError("benchmark input has no supported return column")
            benchmark = benchmark.rename(columns={candidate: "MarketReturn"})
        benchmark["Date"] = pd.to_datetime(benchmark["Date"], errors="coerce").dt.normalize()
        benchmark["MarketReturn"] = pd.to_numeric(benchmark["MarketReturn"], errors="coerce")
        if benchmark.duplicated("Date", keep=False).any():
            raise ValueError("benchmark input contains duplicate dates")
        if config.end_date:
            benchmark = benchmark.loc[benchmark["Date"].le(evaluation_end)].copy()

    rows: list[dict[str, object]] = []
    for start_date in config.evaluation_start_dates:
        start = pd.Timestamp(start_date)
        period = indices.loc[indices["Date"].between(start, evaluation_end)].copy()
        for (group_id, method), path in period.groupby(["GroupId", "IndexMethod"], sort=True):
            path = path.sort_values("Date").copy()
            path["IndexReturn"] = path["IndexLevel"].pct_change(fill_method=None)
            blocked_index_rows = int(path["IndexStatus"].ne("PASS").sum())
            aligned_risk_free = def_attach_risk_free_to_dates(path["Date"], risk_free)
            path["DailyRiskFree"] = aligned_risk_free["DailyRiskFree"].to_numpy()
            if benchmark is not None:
                path = path.merge(
                    benchmark[["Date", "MarketReturn"]],
                    on="Date",
                    how="left",
                    validate="many_to_one",
                )
            returns = path["IndexReturn"].dropna()
            observations = int(len(returns))
            if observations and blocked_index_rows == 0:
                total_return = float(np.prod(1.0 + returns.to_numpy(dtype=float)) - 1.0)
                annualized_return = float((1.0 + total_return) ** (TRADING_DAYS_PER_YEAR / observations) - 1.0)
                annualized_volatility = float(returns.std(ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR)) if observations > 1 else np.nan
                downside = returns.loc[returns.lt(0)]
                downside_deviation = float(
                    np.sqrt(np.mean(np.square(downside.to_numpy(dtype=float))))
                    * np.sqrt(TRADING_DAYS_PER_YEAR)
                ) if len(downside) else 0.0
            else:
                total_return = annualized_return = annualized_volatility = downside_deviation = np.nan
            wealth = path["IndexLevel"] / path["IndexLevel"].iloc[0]
            drawdown = wealth / wealth.cummax() - 1.0
            maximum_drawdown = (
                float(drawdown.min()) if len(drawdown) and blocked_index_rows == 0 else np.nan
            )

            paired = path[["IndexReturn", "DailyRiskFree"]].dropna()
            rf_coverage = float(
                path.loc[path["IndexReturn"].notna(), "DailyRiskFree"].notna().mean()
            ) if observations else np.nan
            if len(paired) > 1 and rf_coverage == 1.0 and blocked_index_rows == 0:
                excess = paired["IndexReturn"] - paired["DailyRiskFree"]
                excess_std = float(excess.std(ddof=1))
                sharpe = float(excess.mean() / excess_std * np.sqrt(TRADING_DAYS_PER_YEAR)) if excess_std > 0 else np.nan
                negative_excess = excess.loc[excess.lt(0)]
                downside_excess = float(np.sqrt(np.mean(np.square(negative_excess)))) if len(negative_excess) else 0.0
                sortino = float(excess.mean() / downside_excess * np.sqrt(TRADING_DAYS_PER_YEAR)) if downside_excess > 0 else np.nan
                risk_free_status = "PASS_OFFICIAL_TAIWAN_10Y_COMPLETE"
            else:
                sharpe = sortino = np.nan
                risk_free_status = "HOLD_INCOMPLETE_POINT_IN_TIME_TAIWAN_10Y"

            beta = alpha_annualized = tracking_error = information_ratio = np.nan
            benchmark_n = 0
            if benchmark is not None:
                compared = path[["IndexReturn", "MarketReturn"]].dropna()
                benchmark_n = len(compared)
                if benchmark_n > 1 and blocked_index_rows == 0:
                    x = compared["MarketReturn"].to_numpy(dtype=float)
                    y = compared["IndexReturn"].to_numpy(dtype=float)
                    variance = float(np.var(x, ddof=1))
                    if variance > 0:
                        beta = float(np.cov(y, x, ddof=1)[0, 1] / variance)
                        alpha_annualized = float((np.mean(y) - beta * np.mean(x)) * TRADING_DAYS_PER_YEAR)
                    active = y - x
                    active_std = float(np.std(active, ddof=1))
                    tracking_error = active_std * np.sqrt(TRADING_DAYS_PER_YEAR)
                    information_ratio = float(np.mean(active) / active_std * np.sqrt(TRADING_DAYS_PER_YEAR)) if active_std > 0 else np.nan

            rows.append(
                {
                    "EvaluationStart": start,
                    "EvaluationEnd": evaluation_end,
                    "GroupId": group_id,
                    "IndexMethod": method,
                    "ObservationCount": observations,
                    "BlockedIndexEvidenceRows": blocked_index_rows,
                    "TotalReturn": total_return,
                    "AnnualizedReturn": annualized_return,
                    "AnnualizedVolatility": annualized_volatility,
                    "DownsideDeviation": downside_deviation,
                    "MaximumDrawdown": maximum_drawdown,
                    "SharpeTaiwan10Y": sharpe,
                    "SortinoTaiwan10Y": sortino,
                    "Taiwan10YCoverage": rf_coverage,
                    "RiskFreeStatus": risk_free_status,
                    "PerformanceStatus": (
                        "PASS"
                        if blocked_index_rows == 0
                        else "BLOCKED_INDEX_EVIDENCE_LEVEL_WAS_HELD"
                    ),
                    "BenchmarkObservationCount": benchmark_n,
                    "BetaExTSMCMarket": beta,
                    "AnnualizedAlphaExTSMCMarket": alpha_annualized,
                    "TrackingErrorExTSMCMarket": tracking_error,
                    "InformationRatioExTSMCMarket": information_ratio,
                    "SelectionPolicy": "PARALLEL_EVIDENCE_NO_METHOD_RANKING",
                }
            )
    return pd.DataFrame(rows).sort_values(
        ["EvaluationStart", "GroupId", "IndexMethod"]
    ).reset_index(drop=True) if rows else pd.DataFrame()
