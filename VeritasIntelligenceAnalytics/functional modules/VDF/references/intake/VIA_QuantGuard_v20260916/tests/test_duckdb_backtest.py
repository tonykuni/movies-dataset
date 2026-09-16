from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import polars as pl

from scripts.run_backtest_with_duckdb import run_duckdb_backtest

UTC = timezone.utc


def _ts(day: date, hour: int, minute: int = 0) -> datetime:
    return datetime(day.year, day.month, day.day, hour, minute, tzinfo=UTC)


def _fixtures(days: int = 80) -> tuple[pl.DataFrame, pl.DataFrame]:
    start = date(2024, 1, 1)
    revisions: list[dict[str, object]] = []
    calendar: list[dict[str, object]] = []
    revision_id = 1
    for index in range(days):
        session = start + timedelta(days=index)
        calendar.append({
            "market_code": "TW",
            "session_date": session,
            "status": "open",
            "open_utc": _ts(session, 13),
            "close_utc": _ts(session, 12),
            "calendar_version": "test-v1",
        })
        for market, ticker, close_hour, base, slope in [
            ("TW", "2330", 6, 100.0, 0.001),
            ("US", "SPY", 21, 400.0, 0.0005),
        ]:
            close = base * (1.0 + slope) ** index * (1.0 + (index % 5) * 0.001)
            revisions.append({
                "market_code": market,
                "ticker": ticker,
                "interval": "1d",
                "field_group": "market_bar",
                "market_session_date": session,
                "revision_id": revision_id,
                "revision_no": 1,
                "available_at": _ts(session, close_hour + 1),
                "confirmed_at": _ts(session, close_hour + 2),
                "revision_status": "confirmed",
                "adj_open": close * 0.99,
                "adj_high": close * 1.01,
                "adj_low": close * 0.98,
                "adj_close": close,
                "non_day_trade_volume": 1000.0 + index,
                "close_utc": _ts(session, close_hour),
                "bar_closed_at": _ts(session, close_hour),
            })
            revision_id += 1
    return pl.DataFrame(revisions), pl.DataFrame(calendar)


def test_duckdb_cli_runs_pit_factor_composite_backtest(tmp_path):
    revisions, calendar = _fixtures()
    revision_path = tmp_path / "revisions.parquet"
    calendar_path = tmp_path / "calendar.parquet"
    revisions.write_parquet(revision_path)
    calendar.write_parquet(calendar_path)

    result = run_duckdb_backtest(
        db_path=tmp_path / "engine.duckdb",
        revision_parquet=revision_path,
        calendar_parquet=calendar_path,
        target_ticker="2330",
        factor_weights={
            "trend_regime": 0.4,
            "momentum_confirmation": 0.3,
            "volume_flow_confirmation": 0.3,
        },
        output_dir=tmp_path / "output",
    )

    assert result["loaded_revision_rows"] == 160
    assert result["decision_rows"] > 0
    assert result["strategy_rows"] == result["decision_rows"]
    assert result["decisions"].exists()
    assert result["strategy"].exists()
    assert result["risk"].exists()
    assert result["manifests"].exists()
    assert result["summary"].exists()

    decisions = pl.read_parquet(result["decisions"])
    strategy = pl.read_parquet(result["strategy"])
    risk = pl.read_parquet(result["risk"])
    assert "factor_composite" in decisions.columns
    assert "position_t_plus_1" in strategy.columns
    assert "rolling_sharpe" in risk.columns
    assert "rolling_max_drawdown" in risk.columns
    assert strategy.get_column("position_t_plus_1").head(1).item() == 0


def test_duckdb_cli_entrypoint_writes_summary(tmp_path):
    revisions, calendar = _fixtures(days=70)
    revision_path = tmp_path / "revisions.parquet"
    calendar_path = tmp_path / "calendar.parquet"
    output_dir = tmp_path / "cli-output"
    revisions.write_parquet(revision_path)
    calendar.write_parquet(calendar_path)
    weights = json.dumps({
        "trend_regime": 0.4,
        "momentum_confirmation": 0.3,
        "volume_flow_confirmation": 0.3,
    })
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).parents[1]))
    completed = subprocess.run([
        sys.executable,
        "scripts/run_backtest_with_duckdb.py",
        "--db-path", str(tmp_path / "cli.duckdb"),
        "--revision-parquet", str(revision_path),
        "--calendar-parquet", str(calendar_path),
        "--target-ticker", "2330",
        "--factor-weights", weights,
        "--output-dir", str(output_dir),
    ], cwd=Path(__file__).parents[1], env=env, check=True, capture_output=True, text=True)
    assert "backtest_summary.json" in completed.stdout
    summary = json.loads((output_dir / "backtest_summary.json").read_text(encoding="utf-8"))
    assert summary["factor_weights"]["trend_regime"] == 0.4
