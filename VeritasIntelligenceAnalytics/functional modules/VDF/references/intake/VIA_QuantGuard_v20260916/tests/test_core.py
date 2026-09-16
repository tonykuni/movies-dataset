from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import polars as pl
import pytest

from quant_engine import (
    EngineConfig,
    IMPORTANT_INDICATORS,
    INDICATOR_CATEGORIES,
    analyze_foreign_intent,
    align_confirmed_closes,
    benchmark_catalog_table,
    build_feature_matrix,
    build_residual_returns,
    build_sector_index,
    build_toca,
    calculate_real_capital_flows,
    encode_category_label,
    encode_parameters,
    factor_table,
    logic_table,
    normalize_market_timestamp,
    policy_table,
    prepare_non_day_trade_activity,
    RiskConfig,
    calculate_risk_metrics,
    encode_risk_parameters,
    rolling_statistical_features,
    ssot_manifest,
    render_parameter_text,
    rolling_beta_corr,
    technical_indicators,
)


def prices(n: int = 140) -> pl.DataFrame:
    dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(n)]
    rows = []
    for ticker, base, slope in [("AAA", 100.0, 0.001), ("BBB", 80.0, 0.0005)]:
        for i, d in enumerate(dates):
            close = base * (1 + slope) ** i
            rows.append(
                {
                    "date": d,
                    "ticker": ticker,
                    "close": close,
                    "adj_close": close,
                    "high": close * 1.01,
                    "low": close * 0.99,
                    "non_day_trade_volume": 1000 + i,
                }
            )
    return pl.DataFrame(rows)


def test_config_windows_are_strict():
    assert EngineConfig().windows == (5, 10, 20, 60, 120)
    assert set(INDICATOR_CATEGORIES) == {
        "trend", "momentum", "volatility", "volume_flow",
        "relative_market", "microstructure_fundamental", "statistical_structure", "risk",
    }
    assert "rsi_14" in IMPORTANT_INDICATORS["momentum"]
    assert "rolling_sharpe" in IMPORTANT_INDICATORS["risk"]
    encoded = encode_parameters(EngineConfig(windows=(5, 20)))
    assert {"TRD_MACD_FAST", "VOL_ATR", "GOV_PRICE_BASIS"}.issubset(set(encoded["parameter_code"]))
    assert encoded.filter(pl.col("status") == "UNREGISTERED").height == 0
    assert encode_category_label("TREND") == "趨勢"
    assert "MACD" in render_parameter_text(EngineConfig(windows=(5, 20)))
    assert benchmark_catalog_table().height >= 6
    with pytest.raises(ValueError):
        EngineConfig(windows=(7,))


def test_technical_indicators_are_polars_only_and_have_expected_columns():
    result = technical_indicators(prices(), config=EngineConfig(windows=(5, 10)))
    expected = {
        "rsi_14", "atr", "atr_pct", "adx_14", "stoch_k_14", "mfi_14", "cci_20",
        "obv", "adl", "cmf_20", "rolling_vwap_20", "keltner_upper", "keltner_lower", "keltner_width", "macd_line", "macd_signal", "macd_histogram",
        "sma_5", "ema_5", "bb_upper_5", "bb_lower_5", "bb_width_5", "return_vol_5", "return_z_5",
        "return_autocorr_5", "return_volume_corr_5", "return_range_corr_5",
        "sma_10", "bb_upper_10", "bb_lower_10", "donchian_upper_10", "donchian_lower_10",
    }
    assert expected.issubset(set(result.columns))
    assert result.filter(pl.col("ticker") == "AAA").select("rsi_14").tail(1).item() == pytest.approx(100.0)
    assert result.filter(pl.col("ticker") == "AAA").select("return_autocorr_5").tail(1).item() is not None


def test_analysis_rejects_raw_volume_and_uses_only_ex_day_trade_volume():
    raw = prices(40).rename({"non_day_trade_volume": "volume"})
    with pytest.raises(ValueError, match="non_day_trade_volume"):
        technical_indicators(raw, config=EngineConfig(windows=(5,)))
    official = pl.DataFrame({
        "date": [date(2024, 1, 1)], "ticker": ["AAA"],
        "volume": [1000.0], "day_trade_volume": [250.0],
        "total_turnover": [100_000.0], "day_trade_turnover": [20_000.0],
    })
    prepared = prepare_non_day_trade_activity(official)
    assert prepared.row(0, named=True)["non_day_trade_volume"] == 750.0
    assert prepared.row(0, named=True)["non_day_trade_turnover"] == 80_000.0


def test_feature_matrix_is_cross_quadrant_and_labels_are_explicit():
    result = build_feature_matrix(
        prices(140),
        windows=(5, 20, 60),
        label_horizons=(5,),
    )
    expected = {
        "trend_regime", "momentum_confirmation", "volume_flow_confirmation",
        "volatility_ratio_20_60", "breakout_20", "correlation_confirmation_count",
        "cross_quadrant_long_confirmation",
        "rolling_sharpe", "rolling_sortino", "rolling_calmar", "rolling_var", "rolling_cvar",
        "feature_quality_count", "label_forward_return_5",
    }
    assert expected.issubset(set(result.columns))
    assert result.filter(pl.col("label_forward_return_5").is_null()).height > 0
    last = result.filter(pl.col("ticker") == "AAA").tail(1).row(0, named=True)
    assert last["label_forward_return_5"] is None


def test_feature_matrix_can_join_benchmark_features():
    df = prices(140)
    benchmark = df.filter(pl.col("ticker") == "AAA").select(["date", "adj_close"])
    result = build_feature_matrix(df, benchmark=benchmark)
    assert {"rolling_beta", "rolling_corr", "residual_return_60"}.issubset(result.columns)


def test_risk_and_statistical_modules_are_independently_usable():
    varied = prices(100).with_columns(
        (pl.col("adj_close") * (1.0 + (pl.int_range(0, pl.len()) % 5) * 0.001)).alias("adj_close")
    )
    risk = calculate_risk_metrics(
        varied,
        config=RiskConfig(window=20, min_samples=10),
    )
    assert {"rolling_sharpe", "rolling_sortino", "rolling_calmar", "rolling_var", "rolling_cvar"}.issubset(risk.columns)
    assert risk.filter(pl.col("ticker") == "AAA").tail(1).select("rolling_sharpe").item() is not None
    stats = rolling_statistical_features(varied, windows=(20,))
    assert {"return_autocorr_20", "return_skew_20", "return_excess_kurtosis_20"}.issubset(stats.columns)
    assert stats.filter(pl.col("ticker") == "AAA").tail(1).select("return_skew_20").item() is not None


def test_cross_market_asof_uses_last_confirmed_close_not_same_calendar_date():
    frame = pl.DataFrame({
        "market_code": ["TW", "TW", "US", "US"],
        "market_session_date": [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 1), date(2024, 1, 2)],
        "close_utc": [
            datetime(2024, 1, 2, 6, 30, tzinfo=timezone.utc),
            datetime(2024, 1, 3, 6, 30, tzinfo=timezone.utc),
            datetime(2024, 1, 1, 21, 0, tzinfo=timezone.utc),
            datetime(2024, 1, 2, 21, 0, tzinfo=timezone.utc),
        ],
        "adj_close": [100.0, 101.0, 200.0, 202.0],
    })
    aligned = align_confirmed_closes(frame, left_market="TW", right_market="US")
    assert aligned.select("right_session_date").to_series().to_list() == [date(2024, 1, 1), date(2024, 1, 2)]


def test_market_timestamp_normalization_uses_iana_timezones():
    frame = pl.DataFrame({
        "timestamp": [
            datetime(2024, 1, 2, 14, 30, tzinfo=timezone.utc),
            datetime(2024, 7, 1, 13, 30, tzinfo=timezone.utc),
        ],
        "market_code": ["US", "US"],
    })
    result = normalize_market_timestamp(frame).collect()
    assert result.get_column("timestamp_local").dt.hour().to_list() == [9, 9]
    assert result.get_column("market_session_date").to_list() == [date(2024, 1, 2), date(2024, 7, 1)]


def test_central_ssot_exposes_policy_logic_and_factor_libraries():
    manifest = ssot_manifest()
    assert manifest["global_invariants"]["price_basis"] == "adj_close_only"
    assert manifest["global_invariants"]["volume_basis"] == "non_day_trade_only"
    assert policy_table().height >= 8
    assert logic_table().filter(pl.col("logic_code") == "SHARPE").height == 1
    assert factor_table().filter(pl.col("factor_code") == "FACTOR_RISK_ADJUSTED").height == 1
    assert encode_risk_parameters(RiskConfig()).filter(pl.col("status") == "DEFAULT").height == 6


def test_feature_matrix_joins_capital_features_with_one_session_lag():
    source = prices(80).select(["date", "ticker"]).unique().sort(["ticker", "date"])
    source = source.with_columns([
        pl.int_range(0, pl.len()).over("ticker").cast(pl.Float64).alias("institutional_amount_ratio"),
        (pl.int_range(0, pl.len()).over("ticker") * 10.0).alias("toca_z_score"),
    ])
    result = build_feature_matrix(
        prices(80),
        institutional_features=source,
        toca_features=source,
        feature_lag_sessions=1,
    )
    aaa = result.filter(pl.col("ticker") == "AAA").sort("date")
    assert {
        "institutional_amount_ratio", "toca_z_score", "capital_feature_quality_count",
        "capital_flow_confirmation", "capital_flow_heat",
    }.issubset(result.columns)
    assert aaa.row(0, named=True)["institutional_amount_ratio"] is None
    assert aaa.row(1, named=True)["institutional_amount_ratio"] == pytest.approx(0.0)
    assert aaa.row(1, named=True)["toca_z_score"] == pytest.approx(0.0)
    assert aaa.row(70, named=True)["feature_quality_count"] == 8
    assert aaa.row(70, named=True)["capital_flow_confirmation"] == 1


def test_capital_feature_keys_must_be_unique():
    duplicate = pl.DataFrame({
        "date": [date(2024, 1, 1), date(2024, 1, 1)],
        "ticker": ["AAA", "AAA"],
        "institutional_amount_ratio": [0.1, 0.2],
    })
    with pytest.raises(ValueError, match="unique"):
        build_feature_matrix(prices(40), institutional_features=duplicate)


def test_rolling_beta_and_corr_use_effective_samples_with_missing_data():
    raw = prices(80).filter(pl.col("ticker") == "AAA").select(
        ["date", "ticker", "adj_close"]
    ).with_row_index("i").with_columns(
        (pl.col("adj_close") * (1.0 + (pl.col("i") % 5) * 0.0001)).alias("adj_close")
    ).with_columns(
        pl.col("adj_close").alias("bench_adj_close")
    ).drop("i")
    # A missing observation must not be forward-filled by default.
    raw = raw.with_columns(
        pl.when(pl.col("date") == date(2024, 1, 20)).then(None).otherwise(pl.col("adj_close")).alias("adj_close")
    )
    result = rolling_beta_corr(raw, window=20, min_samples=18)
    valid = result.filter(pl.col("rolling_beta").is_not_null())
    assert valid.height > 0
    assert valid.select(pl.col("effective_n").min()).item() >= 18
    assert valid.select(pl.col("rolling_beta").tail(1)).item() == pytest.approx(1.0, abs=1e-8)
    assert valid.select(pl.col("rolling_corr").tail(1)).item() == pytest.approx(1.0, abs=1e-8)


def test_toca_zscore_is_lagged_to_avoid_lookahead():
    dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(30)]
    rows = []
    for i, d in enumerate(dates):
        rows.extend([
                {"date": d, "ticker": "2330", "non_day_trade_turnover": 900.0},
                    {"date": d, "ticker": "AAA", "non_day_trade_turnover": 90.0 + (i % 3)},
                    {"date": d, "ticker": "BBB", "non_day_trade_turnover": 180.0},
        ])
    rows[-2]["non_day_trade_turnover"] = 900.0
    result = build_toca(pl.DataFrame(rows), ewm_half_life=5, z_min_samples=10)
    last = result.filter((pl.col("ticker") == "AAA") & (pl.col("date") == dates[-1])).row(0, named=True)
    assert last["toca_z_score"] is not None
    assert last["toca_z_score"] > 0


def test_real_capital_flow_uses_adj_price_and_ex_day_trade_turnover():
    df = pl.DataFrame({
        "date": [date(2024, 1, 1)], "ticker": ["AAA"],
        "adj_close": [100.0], "non_day_trade_turnover": [900_000.0],
        "foreign_net_shares": [10], "trust_net_shares": [5],
        "margin_change_shares": [-2],
    })
    result = calculate_real_capital_flows(df)
    row = result.row(0, named=True)
    assert row["foreign_net_amount"] == pytest.approx(1_000_000.0)
    assert row["trust_net_amount"] == pytest.approx(500_000.0)
    assert row["institutional_amount_ratio"] == pytest.approx(1.6666666667)


def test_foreign_intent_schema_and_labels():
    dates = [date(2024, 1, 1) + timedelta(days=i) for i in range(40)]
    df = pl.DataFrame({
        "date": dates,
        "spot_net_buy": [10.0] * 35 + [-100.0] * 5,
        "futures_net_oi": [-10_000.0] * 35 + [-40_000.0] * 5,
    })
    result = analyze_foreign_intent(df, ewm_half_life=5, oi_z_threshold=1.0, spot_sell_threshold=-100.0)
    assert "foreign_intent_signal" in result.columns
    assert result.height == 40


def test_residual_returns_and_adjusted_price_requirement():
    df = prices(80)
    bench = df.filter(pl.col("ticker") == "AAA").select(["date", "adj_close"])
    result = build_residual_returns(df, benchmark=bench, min_samples=10)
    assert {"dynamic_beta", "residual_ret", "clean_residual_ret"}.issubset(result.columns)
    bad = df.drop("adj_close")
    with pytest.raises(ValueError):
        technical_indicators(bad, config=EngineConfig(windows=(5,)))


def test_sector_index_equal_weight_is_an_average():
    df = pl.DataFrame({
        "date": [date(2024, 1, 1), date(2024, 1, 2)] * 2,
        "ticker": ["AAA", "AAA", "BBB", "BBB"],
        "adj_close": [100.0, 110.0, 100.0, 90.0],
    })
    result = build_sector_index(df, weight_col="missing_weight")
    assert result.filter(pl.col("date") == date(2024, 1, 2)).select("sector_return").item() == pytest.approx(0.0)
