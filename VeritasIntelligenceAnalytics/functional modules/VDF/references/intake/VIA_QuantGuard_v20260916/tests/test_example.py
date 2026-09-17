from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import polars as pl

from examples.tw_us_cross_market_risk import (
    align_taiwan_signal_to_us_close,
    build_target_ohlcv,
    calculate_target_risk_and_features,
    load_confirmed_market_prices,
)


def test_complete_tw_us_example_pipeline(tmp_path):
    tw_rows = []
    us_rows = []
    start = date(2024, 1, 1)
    for i in range(120):
        session = start + timedelta(days=i)
        tw_close = 100.0 * (1.0 + 0.0005) ** i * (1.0 + (i % 5) * 0.0002)
        us_close = 400.0 * (1.0 + 0.0003) ** i * (1.0 + (i % 7) * 0.0003)
        tw_rows.append({
            "market_code": "TW", "ticker": "2330", "market_session_date": session,
            "close_utc": datetime(session.year, session.month, session.day, 6, 30, tzinfo=timezone.utc),
            "adj_close": tw_close, "adj_high": tw_close * 1.01,
            "adj_low": tw_close * 0.99, "non_day_trade_volume": 1000.0 + i,
            "confirmed_at": datetime(session.year, session.month, session.day, 7, 0, tzinfo=timezone.utc),
            "revision_status": "confirmed",
        })
        us_rows.append({
            "market_code": "US", "ticker": "SPY", "market_session_date": session,
            "close_utc": datetime(session.year, session.month, session.day, 21, 0, tzinfo=timezone.utc),
            "adj_close": us_close,
            "confirmed_at": datetime(session.year, session.month, session.day, 22, 0, tzinfo=timezone.utc),
            "revision_status": "confirmed",
        })

    tw_path = tmp_path / "tw.parquet"
    us_path = tmp_path / "us.parquet"
    pl.DataFrame(tw_rows).write_parquet(tw_path)
    pl.DataFrame(us_rows).write_parquet(us_path)

    tw = load_confirmed_market_prices(tw_path, market_code="TW", ticker="2330")
    us = load_confirmed_market_prices(us_path, market_code="US", ticker="SPY")
    aligned = align_taiwan_signal_to_us_close(tw, us)
    # The first Taiwan cutoff has no prior confirmed US close; the as-of join
    # preserves that data gap instead of forward-filling a fictional value.
    assert aligned.height == 119
    assert aligned.filter(pl.col("right_close_utc") > pl.col("left_close_utc")).height == 0
    assert aligned.select("cross_session_lag").tail(1).item() == 1

    full_tw = pl.read_parquet(tw_path)
    target = build_target_ohlcv(full_tw, "2330")
    risk, features = calculate_target_risk_and_features(target, aligned)
    assert {"rolling_sharpe", "rolling_sortino", "rolling_var", "rolling_cvar"}.issubset(risk.columns)
    assert {"rolling_beta", "rolling_corr", "rolling_sharpe", "label_forward_return_5"}.issubset(features.columns)
