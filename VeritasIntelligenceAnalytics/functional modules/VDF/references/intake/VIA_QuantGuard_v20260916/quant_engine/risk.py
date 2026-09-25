"""Rolling risk metrics with explicit annualisation and tail-loss policies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import polars as pl

from .governance import PARAMETER_POLICIES, validate_governance_frame


@dataclass(frozen=True)
class RiskConfig:
    window: int = 60
    min_samples: int = 30
    periods_per_year: int = 252
    annual_risk_free_rate: float = 0.0
    annual_mar: float = 0.0
    var_confidence: float = 0.95

    def __post_init__(self) -> None:
        if self.window < 2:
            raise ValueError("risk window must be >= 2")
        if self.min_samples < 2 or self.min_samples > self.window:
            raise ValueError("risk min_samples must be between 2 and window")
        if self.periods_per_year <= 0:
            raise ValueError("periods_per_year must be positive")
        if not 0.0 < self.var_confidence < 1.0:
            raise ValueError("var_confidence must be between 0 and 1")
        if self.annual_risk_free_rate <= -1.0 or self.annual_mar <= -1.0:
            raise ValueError("annual rates must be greater than -100%")

    @property
    def periodic_risk_free_rate(self) -> float:
        return (1.0 + self.annual_risk_free_rate) ** (1.0 / self.periods_per_year) - 1.0

    @property
    def periodic_mar(self) -> float:
        return (1.0 + self.annual_mar) ** (1.0 / self.periods_per_year) - 1.0


def encode_risk_parameters(config: RiskConfig | None = None) -> pl.DataFrame:
    """Encode RiskConfig against the same central parameter policy vocabulary."""

    config = config or RiskConfig()
    values = {
        "risk_window": config.window,
        "risk_min_samples": config.min_samples,
        "risk_periods_per_year": config.periods_per_year,
        "risk_rf_annual": config.annual_risk_free_rate,
        "risk_mar_annual": config.annual_mar,
        "risk_var_confidence": config.var_confidence,
    }
    policies = {item.code: item for item in PARAMETER_POLICIES if item.category_code == "RISK"}
    rows: list[dict[str, object]] = []
    for key, value in values.items():
        code_key = key.upper()
        policy = policies.get(code_key)
        if policy is None:
            raise RuntimeError(f"risk parameter is not registered: {key}")
        rows.append({
            "parameter_key": key,
            "parameter_code": policy.code,
            "category_code": policy.category_code,
            "name_zh": policy.name_zh,
            "unit": policy.unit,
            "value": value,
            "default": policy.default,
            "status": "DEFAULT" if value == policy.default else "OVERRIDE",
            "description": policy.description,
            "validation": policy.validation,
        })
    return pl.DataFrame(rows).sort("parameter_code")


def _as_lazy(df: pl.DataFrame | pl.LazyFrame) -> pl.LazyFrame:
    return df.lazy() if isinstance(df, pl.DataFrame) else df


def _require_columns(df: pl.DataFrame | pl.LazyFrame, required: set[str]) -> None:
    columns = set(df.collect_schema().names()) if isinstance(df, pl.LazyFrame) else set(df.columns)
    missing = required - columns
    if missing:
        raise ValueError(f"missing risk columns: {sorted(missing)}")


def _cvar_value(series: pl.Series, confidence: float, min_samples: int) -> float | None:
    values = [float(value) for value in series.to_list() if value is not None]
    if len(values) < min_samples:
        return None
    quantile = series.drop_nulls().quantile(confidence, interpolation="linear")
    if quantile is None:
        return None
    tail = [value for value in values if value >= float(quantile)]
    return sum(tail) / len(tail) if tail else None


def _max_drawdown_value(series: pl.Series) -> float | None:
    """Return peak-to-trough drawdown inside one rolling equity window."""

    values = [float(value) for value in series.to_list() if value is not None]
    if not values:
        return None
    peak = values[0]
    maximum_drawdown = 0.0
    for value in values:
        peak = max(peak, value)
        maximum_drawdown = min(maximum_drawdown, value / peak - 1.0)
    return maximum_drawdown


def calculate_risk_metrics(
    df: pl.DataFrame | pl.LazyFrame,
    *,
    config: RiskConfig | None = None,
    return_col: str = "ret",
    ticker_col: str = "ticker",
    date_col: str = "date",
) -> pl.DataFrame:
    """Calculate rolling Sharpe, Sortino, Calmar, VaR, and CVaR.

    Input returns must be completed-bar returns. If ``ret`` is absent, the
    function derives it from ``adj_close`` only. The module rejects raw close
    and raw volume/turnover analysis inputs through the central governance
    policy. Tail metrics use loss ``-ret`` and an explicit linear quantile.
    """

    config = config or RiskConfig()
    _require_columns(df, {date_col, ticker_col})
    columns = set(df.collect_schema().names()) if isinstance(df, pl.LazyFrame) else set(df.columns)
    if return_col not in columns and "adj_close" not in columns:
        raise ValueError("risk metrics require ret or adj_close")
    validate_governance_frame(df, require_price="adj_close" in columns, require_non_day_trade_volume=False)
    q = _as_lazy(df).sort([ticker_col, date_col])
    if return_col not in columns:
        previous = pl.col("adj_close").shift(1).over(ticker_col)
        q = q.with_columns(
            pl.when((pl.col("adj_close") > 0) & (previous > 0))
            .then(pl.col("adj_close") / previous - 1.0)
            .otherwise(None)
            .alias(return_col)
        )
    periodic_rf = config.periodic_risk_free_rate
    periodic_mar = config.periodic_mar
    excess = pl.col(return_col) - periodic_rf
    downside = pl.when(pl.col(return_col).is_null()).then(None).when(
        pl.col(return_col) - periodic_mar < 0
    ).then((pl.col(return_col) - periodic_mar) ** 2).otherwise(0.0)
    q = q.with_columns([
        excess.alias("excess_return"),
        (-pl.col(return_col)).alias("loss"),
        downside.alias("downside_square"),
    ])
    window = config.window
    minimum = config.min_samples
    q = q.with_columns([
        pl.col("excess_return").rolling_mean(window_size=window, min_samples=minimum).over(ticker_col).alias("rolling_excess_mean"),
        pl.col("excess_return").rolling_std(window_size=window, min_samples=minimum, ddof=1).over(ticker_col).alias("rolling_excess_std"),
        pl.col("downside_square").rolling_mean(window_size=window, min_samples=minimum).over(ticker_col).sqrt().alias("rolling_downside_deviation"),
        pl.col("loss").rolling_quantile(
            quantile=config.var_confidence,
            interpolation="linear",
            window_size=window,
            min_samples=minimum,
        ).over(ticker_col).alias("rolling_var"),
        pl.col("loss").rolling_map(
            lambda values: _cvar_value(values, config.var_confidence, minimum),
            window_size=window,
            min_samples=minimum,
        ).over(ticker_col).alias("rolling_cvar"),
    ]).with_columns([
        pl.when(pl.col("rolling_excess_std").abs() > 1e-12)
        .then(pl.col("rolling_excess_mean") / pl.col("rolling_excess_std") * (config.periods_per_year ** 0.5))
        .otherwise(None).alias("rolling_sharpe"),
        pl.when(pl.col("rolling_downside_deviation").abs() > 1e-12)
        .then(pl.col("rolling_excess_mean") / pl.col("rolling_downside_deviation") * (config.periods_per_year ** 0.5))
        .otherwise(None).alias("rolling_sortino"),
    ])
    equity = (1.0 + pl.col(return_col)).cum_prod().over(ticker_col)
    q = q.with_columns(equity.alias("equity_curve")).with_columns([
        pl.col("equity_curve").rolling_map(
            _max_drawdown_value,
            window_size=window,
            min_samples=minimum,
        ).over(ticker_col).alias("rolling_max_drawdown"),
    ]).with_columns([
        pl.when(
            (pl.col("equity_curve") > 0)
            & (pl.col("equity_curve").shift(window - 1).over(ticker_col) > 0)
        ).then(
            (pl.col("equity_curve") / pl.col("equity_curve").shift(window - 1).over(ticker_col))
            ** (config.periods_per_year / (window - 1)) - 1.0
        ).otherwise(None).alias("rolling_cagr"),
    ]).with_columns(
        pl.when(pl.col("rolling_max_drawdown").abs() > 1e-12)
        .then(pl.col("rolling_cagr") / pl.col("rolling_max_drawdown").abs())
        .otherwise(None).alias("rolling_calmar")
    )
    return q.select([
        date_col, ticker_col, return_col, "excess_return", "rolling_sharpe",
        "rolling_sortino", "rolling_calmar", "rolling_var", "rolling_cvar",
        "rolling_max_drawdown", "rolling_cagr", "equity_curve",
    ]).collect()


def summarize_risk_metrics(
    df: pl.DataFrame | pl.LazyFrame,
    *,
    config: RiskConfig | None = None,
    return_col: str = "ret",
    ticker_col: str = "ticker",
) -> pl.DataFrame:
    """Return last available rolling risk values for each ticker."""

    metrics = calculate_risk_metrics(df, config=config, return_col=return_col, ticker_col=ticker_col)
    return metrics.sort([ticker_col, "date"]).group_by(ticker_col, maintain_order=True).tail(1)
