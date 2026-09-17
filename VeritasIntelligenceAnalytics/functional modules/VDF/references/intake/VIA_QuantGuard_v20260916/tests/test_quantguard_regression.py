from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import polars as pl
import pytest

from quant_engine import (
    EngineConfig,
    RiskConfig,
    build_factor_composite,
    build_feature_matrix,
    calculate_risk_metrics,
    technical_indicators,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "performance_regression_fixture.json"
pytestmark = pytest.mark.regression


def fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_via_quantguard_sharpe_and_max_drawdown_golden_values():
    data = fixture()["risk"]
    returns = data["returns"]
    equity = []
    value = 1.0
    for ret in returns:
        value *= 1.0 + ret
        equity.append(value)
    frame = pl.DataFrame({
        "date": [date(2024, 1, 1) + timedelta(days=i) for i in range(len(returns))],
        "ticker": ["REGRESSION"] * len(returns),
        "ret": returns,
        "adj_close": equity,
    })
    config = RiskConfig(
        window=data["window"],
        min_samples=data["min_samples"],
        periods_per_year=data["periods_per_year"],
        annual_risk_free_rate=data["annual_risk_free_rate"],
        annual_mar=data["annual_mar"],
    )
    result = calculate_risk_metrics(frame, config=config, return_col="ret")
    last = result.tail(1).row(0, named=True)
    expected = data["expected_last"]
    tolerances = data["tolerances"]
    assert last["rolling_sharpe"] == pytest.approx(expected["rolling_sharpe"], abs=tolerances["rolling_sharpe"])
    assert last["equity_curve"] == pytest.approx(expected["equity_curve"], abs=tolerances["equity_curve"])
    assert last["rolling_max_drawdown"] == pytest.approx(expected["rolling_max_drawdown"], abs=tolerances["rolling_max_drawdown"])


def test_via_quantguard_technical_indicator_golden_values():
    data = fixture()["feature"]
    prices = data["prices"]
    frame = pl.DataFrame({
        "date": [date(2024, 1, 1) + timedelta(days=i) for i in range(len(prices))],
        "ticker": ["REGRESSION"] * len(prices),
        "close": prices,
        "adj_close": prices,
        "high": [price * 1.01 for price in prices],
        "low": [price * 0.99 for price in prices],
        "non_day_trade_volume": [1000.0 + 10.0 * i for i in range(len(prices))],
    })
    result = technical_indicators(frame, config=EngineConfig(windows=(5,)))
    last = result.tail(1).row(0, named=True)
    expected = data["expected_last"]
    tolerances = data["tolerances"]
    assert last["sma_5"] == pytest.approx(expected["sma_5"], abs=tolerances["sma_5"])
    assert last["ema_5"] == pytest.approx(expected["ema_5"], abs=tolerances["ema_5"])


def test_via_quantguard_factor_outputs_golden_values():
    data = fixture()["factor"]
    dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(data["rows"])]
    rows = []
    for ticker, base, slope in [("AAA", data["base"], data["slope"]), ("BBB", 80.0, 0.0005)]:
        for i, session_date in enumerate(dates):
            close = base * (1.0 + slope) ** i
            adjusted = close * (1.0 + (i % 5) * data["periodic_adjustment"])
            rows.append({
                "date": session_date,
                "ticker": ticker,
                "close": close,
                "adj_close": adjusted,
                "high": adjusted * 1.01,
                "low": adjusted * 0.99,
                "non_day_trade_volume": 1000.0 + i,
            })
    result = build_feature_matrix(
        pl.DataFrame(rows),
        windows=(5, 20, 60),
        label_horizons=(5,),
    )
    last = result.filter(pl.col("ticker") == data["ticker"]).tail(1).row(0, named=True)
    expected = data["expected_last"]
    tolerances = data["tolerances"]
    assert last["trend_regime"] == expected["trend_regime"]
    assert last["momentum_confirmation"] == expected["momentum_confirmation"]
    assert last["volume_flow_confirmation"] == expected["volume_flow_confirmation"]
    assert last["feature_quality_count"] == expected["feature_quality_count"]
    assert last["volatility_ratio_20_60"] == pytest.approx(
        expected["volatility_ratio_20_60"], abs=tolerances["volatility_ratio_20_60"]
    )
    assert last["rolling_sharpe"] == pytest.approx(
        expected["rolling_sharpe"], abs=tolerances["rolling_sharpe"]
    )
    assert last["rolling_max_drawdown"] == pytest.approx(
        expected["rolling_max_drawdown"], abs=tolerances["rolling_max_drawdown"]
    )
    composite = build_factor_composite(
        result,
        factor_weights=data["weights"],
    ).filter(pl.col("ticker") == data["ticker"]).tail(1).row(0, named=True)
    assert composite["factor_composite"] == pytest.approx(
        expected["factor_composite"], abs=tolerances["factor_composite"]
    )
    assert composite["factor_composite_quality_count"] == expected["factor_composite_quality_count"]


def test_via_quantguard_factor_composite_fails_closed_on_missing_factor():
    frame = pl.DataFrame({
        "trend_regime": [1],
        "momentum_confirmation": [None],
        "volume_flow_confirmation": [0],
    })
    result = build_factor_composite(
        frame,
        factor_weights={
            "trend_regime": 0.4,
            "momentum_confirmation": 0.3,
            "volume_flow_confirmation": 0.3,
        },
    )
    assert result.row(0, named=True)["factor_composite"] is None
    assert result.row(0, named=True)["factor_composite_quality_count"] == 2


@pytest.mark.parametrize("scenario", fixture()["stress"], ids=lambda item: item["scenario_id"])
def test_via_quantguard_stress_scenarios(scenario):
    returns = scenario["returns"]
    equity = []
    value = 1.0
    for ret in returns:
        if ret is not None:
            value *= 1.0 + ret
        equity.append(value)
    frame = pl.DataFrame({
        "date": [date(2024, 1, 1) + timedelta(days=i) for i in range(len(returns))],
        "ticker": [scenario["scenario_id"]] * len(returns),
        "ret": returns,
        "adj_close": equity,
    })
    result = calculate_risk_metrics(
        frame,
        config=RiskConfig(
            window=scenario["window"],
            min_samples=scenario["min_samples"],
        ),
        return_col="ret",
    )
    last = result.tail(1).row(0, named=True)
    expected = scenario["expected_last"]
    for column in (
        "rolling_sharpe", "rolling_sortino", "rolling_var", "rolling_cvar",
        "rolling_max_drawdown", "equity_curve",
    ):
        assert last[column] == pytest.approx(expected[column], abs=1e-10)
    if scenario["scenario_id"] == "flash_crash":
        assert last["rolling_max_drawdown"] <= -0.20
        assert last["rolling_cvar"] >= 0.20
    if scenario["scenario_id"] == "missing_observations":
        assert frame.get_column("ret").null_count() == 2
