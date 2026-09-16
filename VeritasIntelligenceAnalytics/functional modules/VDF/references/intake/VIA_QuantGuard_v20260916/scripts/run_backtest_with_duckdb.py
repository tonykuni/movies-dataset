#!/usr/bin/env python3
"""Run a point-in-time DuckDB backtest with a versioned factor composite.

The input revision Parquet must contain normalized, confirmed-capable rows for
both the Taiwan target and the US benchmark. The calendar Parquet must contain
versioned Taiwan sessions with ``market_code``, ``session_date``, ``status``,
and ``close_utc``; ``open_utc`` is used when present for execution timing.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any

import polars as pl

from quant_engine import (
    DeterministicReplay,
    DuckDBPointInTimeStore,
    EngineConfig,
    ReplayConfig,
    build_factor_composite,
    build_feature_matrix,
    build_replay_sessions,
    calculate_risk_metrics,
)

DEFAULT_WEIGHTS = {
    "trend_regime": 0.4,
    "momentum_confirmation": 0.3,
    "volume_flow_confirmation": 0.3,
}


def parse_factor_weights(value: str | None) -> dict[str, float]:
    """Read a JSON object from the CLI or return the documented default."""

    if value is None:
        return DEFAULT_WEIGHTS.copy()
    path = Path(value)
    payload: Any = json.loads(path.read_text(encoding="utf-8")) if path.exists() else json.loads(value)
    if not isinstance(payload, dict) or not payload:
        raise ValueError("factor weights must be a non-empty JSON object")
    return {str(key): float(weight) for key, weight in payload.items()}


def _parse_optional_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def load_revisions(
    store: DuckDBPointInTimeStore,
    revision_parquet: str | Path,
) -> int:
    """Create the schema and append one normalized revision batch."""

    revisions = pl.read_parquet(revision_parquet)
    store.create_schema()
    return store.append(revisions)


def build_strategy_returns(
    decisions: pl.DataFrame,
    *,
    ticker: str,
    long_threshold: float,
    short_threshold: float,
) -> pl.DataFrame:
    """Convert a t-signal into next-bar strategy returns without lookahead."""

    target = decisions.filter(pl.col("ticker") == ticker).sort("date")
    if target.is_empty():
        raise ValueError(f"no replay decisions for ticker {ticker}")
    target = target.with_columns(
        pl.when(pl.col("factor_composite") >= long_threshold)
        .then(1)
        .when(pl.col("factor_composite") <= short_threshold)
        .then(-1)
        .otherwise(0)
        .cast(pl.Int8)
        .alias("signal_t")
    ).with_columns(
        pl.col("signal_t").shift(1).fill_null(0).alias("position_t_plus_1")
    ).with_columns(
        (
            pl.col("position_t_plus_1")
            * pl.col("ret").fill_null(0.0)
        ).alias("strategy_return")
    ).with_columns(
        (1.0 + pl.col("strategy_return")).cum_prod().alias("strategy_equity")
    )
    return target.select([
        "date", "ticker", "replay_cutoff_utc", "execution_utc",
        "factor_composite", "factor_composite_quality_count",
        "signal_t", "position_t_plus_1", "ret", "strategy_return",
        "strategy_equity",
    ])


def run_duckdb_backtest(
    *,
    db_path: str | Path,
    revision_parquet: str | Path | None,
    calendar_parquet: str | Path,
    target_ticker: str,
    factor_weights: dict[str, float],
    start: date | None = None,
    end: date | None = None,
    long_threshold: float = 0.5,
    short_threshold: float = -0.5,
    load_revisions: bool = True,
    output_dir: str | Path = "backtest_output",
) -> dict[str, Path | int]:
    """Run the DuckDB-backed replay and write deterministic backtest artifacts."""

    if long_threshold <= short_threshold:
        raise ValueError("long_threshold must be greater than short_threshold")
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    store = DuckDBPointInTimeStore.connect(db_path)
    try:
        if load_revisions:
            if revision_parquet is None:
                raise ValueError("revision_parquet is required when load_revisions=True")
            loaded_rows = load_revisions_into_store(store, revision_parquet)
        else:
            store.create_schema()
            loaded_rows = 0

        calendar = pl.read_parquet(calendar_parquet)
        sessions = build_replay_sessions(
            calendar,
            market_code="TW",
            start=start,
            end=end,
            execution_lag_sessions=1,
        )
        if not sessions:
            raise ValueError("calendar produced no open Taiwan replay sessions")

        def feature_fn(frame: pl.DataFrame, *, benchmark: pl.DataFrame) -> pl.DataFrame:
            target = frame.filter(pl.col("ticker") == target_ticker)
            features = build_feature_matrix(
                target,
                config=EngineConfig(windows=(5, 10, 20, 60, 120)),
                benchmark=benchmark,
                include_risk_metrics=True,
                label_horizons=(),
            )
            return build_factor_composite(
                features,
                factor_weights=factor_weights,
                output_col="factor_composite",
                normalize_weights=True,
                require_complete=True,
            )

        result = DeterministicReplay(
            store,
            config=ReplayConfig(policy="confirmed_only"),
        ).run(sessions, feature_fn=feature_fn)
        if result.decisions.is_empty():
            raise ValueError("replay produced no decisions; check confirmed_at and calendar cutoffs")

        decisions_path = output / "replay_decisions.parquet"
        decisions = result.decisions.sort("date")
        decisions.write_parquet(decisions_path)
        strategy = build_strategy_returns(
            decisions,
            ticker=target_ticker,
            long_threshold=long_threshold,
            short_threshold=short_threshold,
        )
        strategy_path = output / "backtest_returns.parquet"
        strategy.write_parquet(strategy_path)
        risk_input = strategy.select([
            "date",
            pl.lit("FACTOR_COMPOSITE").alias("ticker"),
            pl.col("strategy_return"),
        ]).rename({"strategy_return": "ret"}).with_columns(
            (1.0 + pl.col("ret")).cum_prod().alias("adj_close")
        )
        risk = calculate_risk_metrics(
            risk_input,
            return_col="ret",
        )
        risk_path = output / "backtest_risk_metrics.parquet"
        risk.write_parquet(risk_path)
        manifest_path = output / "replay_manifests.json"
        manifest_path.write_text(
            json.dumps([manifest.to_dict() for manifest in result.manifests], ensure_ascii=False, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        summary_path = output / "backtest_summary.json"
        summary_path.write_text(
            json.dumps({
                "target_ticker": target_ticker,
                "factor_weights": factor_weights,
                "long_threshold": long_threshold,
                "short_threshold": short_threshold,
                "loaded_revision_rows": loaded_rows,
                "decision_rows": decisions.height,
                "strategy_rows": strategy.height,
                "latest_risk": risk.tail(1).to_dicts(),
            }, ensure_ascii=False, indent=2, default=str) + "\n",
            encoding="utf-8",
        )
        return {
            "loaded_revision_rows": loaded_rows,
            "decision_rows": decisions.height,
            "strategy_rows": strategy.height,
            "decisions": decisions_path,
            "strategy": strategy_path,
            "risk": risk_path,
            "manifests": manifest_path,
            "summary": summary_path,
        }
    finally:
        store.close()


def load_revisions_into_store(
    store: DuckDBPointInTimeStore,
    revision_parquet: str | Path,
) -> int:
    """Use a separate name to avoid shadowing the CLI flag in callers."""

    return load_revisions(store, revision_parquet)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--revision-parquet", required=False)
    parser.add_argument("--calendar-parquet", required=True)
    parser.add_argument("--target-ticker", default="2330")
    parser.add_argument("--factor-weights", help="JSON object or path to JSON object")
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument("--long-threshold", type=float, default=0.5)
    parser.add_argument("--short-threshold", type=float, default=-0.5)
    parser.add_argument("--skip-load", action="store_true")
    parser.add_argument("--output-dir", default="backtest_output")
    args = parser.parse_args()

    result = run_duckdb_backtest(
        db_path=args.db_path,
        revision_parquet=args.revision_parquet,
        calendar_parquet=args.calendar_parquet,
        target_ticker=args.target_ticker,
        factor_weights=parse_factor_weights(args.factor_weights),
        start=_parse_optional_date(args.start_date),
        end=_parse_optional_date(args.end_date),
        long_threshold=args.long_threshold,
        short_threshold=args.short_threshold,
        load_revisions=not args.skip_load,
        output_dir=args.output_dir,
    )
    print(json.dumps({key: str(value) for key, value in result.items()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
