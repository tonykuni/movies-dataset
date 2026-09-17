"""Rolling statistical structure metrics."""

from __future__ import annotations

import math

import polars as pl

from .governance import validate_governance_frame


def _as_lazy(df: pl.DataFrame | pl.LazyFrame) -> pl.LazyFrame:
    return df.lazy() if isinstance(df, pl.DataFrame) else df


def _require_columns(df: pl.DataFrame | pl.LazyFrame, required: set[str]) -> None:
    columns = set(df.collect_schema().names()) if isinstance(df, pl.LazyFrame) else set(df.columns)
    missing = required - columns
    if missing:
        raise ValueError(f"missing statistical columns: {sorted(missing)}")


def rolling_statistical_features(
    df: pl.DataFrame | pl.LazyFrame,
    *,
    windows: tuple[int, ...] = (20, 60, 120),
    return_col: str = "ret",
    value_col: str = "adj_close",
    volume_col: str = "non_day_trade_volume",
    ticker_col: str = "ticker",
    date_col: str = "date",
) -> pl.DataFrame:
    """Return autocorrelation, correlation, R2, skewness and kurtosis.

    All windows are trailing and group-scoped. The module only accepts adjusted
    prices and ex-day-trade volume when those inputs are used.
    """

    if not windows or any(window < 3 for window in windows):
        raise ValueError("windows must contain values >= 3")
    _require_columns(df, {date_col, ticker_col})
    columns = set(df.collect_schema().names()) if isinstance(df, pl.LazyFrame) else set(df.columns)
    if return_col not in columns and value_col not in columns:
        raise ValueError("statistics require ret or adj_close")
    validate_governance_frame(df, require_price=value_col in columns, require_non_day_trade_volume=volume_col in columns)
    q = _as_lazy(df).sort([ticker_col, date_col])
    if return_col not in columns:
        previous = pl.col(value_col).shift(1).over(ticker_col)
        q = q.with_columns(
            pl.when((pl.col(value_col) > 0) & (previous > 0))
            .then(pl.col(value_col) / previous - 1.0)
            .otherwise(None)
            .alias(return_col)
        )
    if volume_col in columns:
        previous_volume = pl.col(volume_col).shift(1).over(ticker_col)
        q = q.with_columns(
            pl.when((pl.col(volume_col) > 0) & (previous_volume > 0))
            .then((pl.col(volume_col) / previous_volume).log())
            .otherwise(None)
            .alias("volume_log_return")
        )
    expressions: list[pl.Expr] = []
    for window in windows:
        lag_return = pl.col(return_col).shift(1).over(ticker_col)
        expressions.extend([
            pl.rolling_corr(
                pl.col(return_col), lag_return,
                window_size=window, min_samples=window, ddof=1,
            ).over(ticker_col).alias(f"return_autocorr_{window}"),
        ])
        if volume_col in columns:
            expressions.append(
                pl.rolling_corr(
                    pl.col(return_col), pl.col("volume_log_return"),
                    window_size=window, min_samples=window, ddof=1,
                ).over(ticker_col).alias(f"return_volume_corr_{window}")
            )
        mean = pl.col(return_col).rolling_mean(window_size=window, min_samples=window).over(ticker_col)
        centered = pl.col(return_col) - mean
        m2 = (centered ** 2).rolling_mean(window_size=window, min_samples=window).over(ticker_col)
        m3 = (centered ** 3).rolling_mean(window_size=window, min_samples=window).over(ticker_col)
        m4 = (centered ** 4).rolling_mean(window_size=window, min_samples=window).over(ticker_col)
        expressions.extend([
            pl.when(m2 > 1e-24).then(m3 / m2.sqrt() ** 3).otherwise(None).alias(f"return_skew_{window}"),
            pl.when(m2 > 1e-24).then(m4 / m2 ** 2 - 3.0).otherwise(None).alias(f"return_excess_kurtosis_{window}"),
            pl.when(
                (pl.col(return_col).rolling_var(window_size=window, min_samples=window, ddof=1).over(ticker_col) > 1e-24)
            ).then(
                pl.rolling_corr(
                    pl.col(return_col), pl.col(return_col).shift(1).over(ticker_col),
                    window_size=window, min_samples=window, ddof=1,
                ).over(ticker_col) ** 2
            ).otherwise(None).alias(f"return_r2_lag1_{window}"),
        ])
    q = q.with_columns(expressions)
    return q.select([date_col, ticker_col, return_col] + [column for column in q.collect_schema().names() if column.startswith("return_") and column != return_col]).collect()


def rolling_r2(
    df: pl.DataFrame | pl.LazyFrame,
    *,
    x_col: str,
    y_col: str,
    window: int = 60,
    min_samples: int | None = None,
    group_col: str = "ticker",
) -> pl.DataFrame:
    """Calculate rolling R2 as squared paired Pearson correlation.

    This is the zero-intercept-independent, one-predictor-with-intercept R2
    identity and is valid only when the same paired window and ddof policy are
    used for both variables.
    """

    min_samples = min_samples or window
    if window < 3 or min_samples < 3 or min_samples > window:
        raise ValueError("R2 window/min_samples invalid")
    _require_columns(df, {x_col, y_col, group_col})
    q = _as_lazy(df).sort(group_col).with_columns(
        pl.rolling_corr(
            pl.col(x_col), pl.col(y_col),
            window_size=window, min_samples=min_samples, ddof=1,
        ).over(group_col).pow(2).alias("rolling_r2")
    )
    return q.collect()
