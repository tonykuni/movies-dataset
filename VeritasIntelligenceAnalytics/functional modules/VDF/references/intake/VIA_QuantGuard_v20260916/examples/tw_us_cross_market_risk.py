"""Complete Taiwan/US cross-market alignment and risk-metric example.

Input Parquet contracts
-----------------------
1. Taiwan target security (for example, 2330):
   market_code, ticker, market_session_date, close_utc, adj_close,
   adj_high, adj_low, non_day_trade_volume
2. US benchmark (for example, SPY or an official US index):
   market_code, ticker, market_session_date, close_utc, adj_close

``close_utc`` must be the confirmed exchange close. If a source only has a
UTC-aware ``timestamp``, the loader normalizes it with the engine's IANA
timezone policy. This example never uses raw close or raw volume in analysis.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import polars as pl

from quant_engine import (
    EngineConfig,
    RiskConfig,
    align_confirmed_closes,
    build_feature_matrix,
    calculate_risk_metrics,
    normalize_market_timestamp,
)


CANONICAL_MARKET_COLUMNS = [
    "market_code",
    "market_session_date",
    "close_utc",
    "adj_close",
]


def load_confirmed_market_prices(
    path: str | Path,
    *,
    market_code: str,
    ticker: str,
) -> pl.DataFrame:
    """Load one confirmed adjusted-price line and normalize timestamps."""

    frame = pl.read_parquet(path)
    if "market_code" not in frame.columns:
        frame = frame.with_columns(pl.lit(market_code).alias("market_code"))
    frame = frame.filter(
        (pl.col("market_code") == market_code)
        & (pl.col("ticker") == ticker)
    )

    # Preferred production input is already normalized. This branch is useful
    # when a source fetcher stores a tz-aware timestamp instead of close_utc.
    if "close_utc" not in frame.columns:
        if "timestamp" not in frame.columns:
            raise ValueError("input must contain close_utc or timestamp")
        frame = normalize_market_timestamp(frame).collect().rename({
            "timestamp_utc": "close_utc",
        })

    required = set(CANONICAL_MARKET_COLUMNS)
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"{path} missing canonical market columns: {sorted(missing)}")

    # Keep only confirmed observations. The ingestion layer should have created
    # this flag from the exchange revision/confirmation state.
    if "confirmed_at" in frame.columns:
        frame = frame.filter(pl.col("confirmed_at").is_not_null())
    if "revision_status" in frame.columns:
        frame = frame.filter(pl.col("revision_status").is_in(["final", "confirmed"]))

    frame = frame.select(CANONICAL_MARKET_COLUMNS).unique(
        subset=["market_code", "market_session_date"],
        keep="last",
    ).sort("close_utc")
    if frame.is_empty():
        raise ValueError(f"{path} has no confirmed rows for {market_code}/{ticker}")
    return frame


def align_taiwan_signal_to_us_close(
    taiwan: pl.DataFrame,
    us: pl.DataFrame,
) -> pl.DataFrame:
    """Use the last US close known at each Taiwan close."""

    combined = pl.concat([taiwan, us], how="diagonal_relaxed").select(CANONICAL_MARKET_COLUMNS)
    aligned = align_confirmed_closes(
        combined,
        left_market="TW",
        right_market="US",
    )
    # This is a hard anti-lookahead assertion, not a cosmetic filter.
    if aligned.filter(pl.col("right_close_utc") > pl.col("left_close_utc")).height:
        raise AssertionError("future US close entered a Taiwan signal row")
    return aligned.with_columns([
        (pl.col("left_adj_close") / pl.col("left_adj_close").first() * 100.0).alias("tw_base100"),
        (pl.col("right_adj_close") / pl.col("right_adj_close").first() * 100.0).alias("us_base100"),
        pl.col("left_adj_close").pct_change().alias("tw_return"),
        pl.col("right_adj_close").pct_change().alias("us_return"),
    ])


def calculate_target_risk_and_features(
    target_ohlcv: pl.DataFrame,
    aligned_market: pl.DataFrame,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Calculate standalone risk metrics and the integrated feature matrix."""

    risk = calculate_risk_metrics(
        target_ohlcv,
        config=RiskConfig(
            window=60,
            min_samples=30,
            periods_per_year=252,
            annual_risk_free_rate=0.015,
            annual_mar=0.0,
            var_confidence=0.95,
        ),
    )

    benchmark = aligned_market.select([
        pl.col("session_date").alias("date"),
        pl.col("right_adj_close").alias("adj_close"),
    ])
    features = build_feature_matrix(
        target_ohlcv,
        config=EngineConfig(windows=(5, 10, 20, 60, 120)),
        benchmark=benchmark,
        include_risk_metrics=True,
        label_horizons=(5, 20),
    )
    return risk, features


def build_target_ohlcv(taiwan_source: pl.DataFrame, target_ticker: str) -> pl.DataFrame:
    """Select the adjusted OHLCV contract used by technical_indicators."""

    source = taiwan_source.filter(pl.col("market_code") == "TW")
    source = source.filter(pl.col("ticker") == target_ticker)
    if "confirmed_at" in source.columns:
        source = source.filter(pl.col("confirmed_at").is_not_null())
    if "revision_status" in source.columns:
        source = source.filter(pl.col("revision_status").is_in(["final", "confirmed"]))
    if {"ticker", "market_session_date"}.issubset(source.columns):
        source = source.unique(
            subset=["ticker", "market_session_date"],
            keep="last",
        )
    required = {"market_session_date", "ticker", "adj_close", "non_day_trade_volume"}
    missing = required - set(source.columns)
    if missing:
        raise ValueError(f"Taiwan target is missing: {sorted(missing)}")

    if {"adj_high", "adj_low"}.issubset(source.columns):
        ohlc = source.select([
            pl.col("market_session_date").alias("date"),
            "ticker", "adj_close", "adj_high", "adj_low", "non_day_trade_volume",
        ])
    elif {"high", "low", "close"}.issubset(source.columns):
        # The engine derives adjusted high/low from adj_close/close. Raw close
        # is retained only at this boundary and never becomes an indicator input.
        ohlc = source.select([
            pl.col("market_session_date").alias("date"),
            "ticker", "adj_close", "high", "low", "close", "non_day_trade_volume",
        ])
    else:
        raise ValueError("Taiwan target needs adj_high/adj_low or high/low/close")
    return ohlc.sort(["ticker", "date"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tw-parquet", required=True, help="confirmed Taiwan target Parquet")
    parser.add_argument("--us-parquet", required=True, help="confirmed US benchmark Parquet")
    parser.add_argument("--tw-ticker", default="2330")
    parser.add_argument("--us-ticker", default="SPY")
    parser.add_argument("--output-dir", default="./example_output")
    args = parser.parse_args()

    tw = load_confirmed_market_prices(args.tw_parquet, market_code="TW", ticker=args.tw_ticker)
    us = load_confirmed_market_prices(args.us_parquet, market_code="US", ticker=args.us_ticker)
    aligned = align_taiwan_signal_to_us_close(tw, us)

    # The market line files used for alignment contain only canonical prices.
    # The Taiwan target file must additionally contain adjusted OHLCV fields.
    tw_full = pl.read_parquet(args.tw_parquet)
    if "market_code" not in tw_full.columns:
        tw_full = tw_full.with_columns(pl.lit("TW").alias("market_code"))
    target_ohlcv = build_target_ohlcv(tw_full, args.tw_ticker)
    risk, features = calculate_target_risk_and_features(target_ohlcv, aligned)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    aligned.write_parquet(output_dir / "tw_us_aligned_close.parquet")
    risk.write_parquet(output_dir / "target_risk_metrics.parquet")
    features.write_parquet(output_dir / "target_feature_matrix.parquet")

    print("Aligned market rows:", aligned.height)
    print("Latest aligned row:")
    print(aligned.tail(1))
    print("Latest risk row:")
    print(risk.tail(1))
    print("Feature columns:", len(features.columns))
    print("Wrote:", output_dir.resolve())


if __name__ == "__main__":
    main()
