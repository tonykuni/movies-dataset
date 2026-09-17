"""Central SSOT governance for the adjusted-price and ex-day-trade engine.

This module is deliberately dependency-light and can be used independently by
fetchers, validation jobs, feature builders, and downstream dashboards.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Mapping

import polars as pl


SSOT_VERSION = "TW-QUANT-ENGINE-SSOT/0.3.0"
POLICY_VERSION = "TW-QUANT-POLICY/0.3.0"


@dataclass(frozen=True)
class MarketPolicy:
    market_code: str
    timezone: str
    default_session_label: str
    price_basis: str = "adj_close"
    volume_basis: str = "non_day_trade"
    signal_available_at: str = "close_confirmed"
    execution_rule: str = "signal_t_execute_t_plus_1"


MARKET_POLICIES: dict[str, MarketPolicy] = {
    "TW": MarketPolicy("TW", "Asia/Taipei", "TWSE_TPEX_DAY", "adj_close", "non_day_trade"),
    "US": MarketPolicy("US", "America/New_York", "NYSE_NASDAQ_REGULAR", "adj_close", "non_day_trade"),
}


@dataclass(frozen=True)
class ParameterPolicy:
    code: str
    name_zh: str
    category_code: str
    unit: str
    default: Any
    description: str
    validation: str


PARAMETER_POLICIES: tuple[ParameterPolicy, ...] = (
    ParameterPolicy("GOV_PRICE_BASIS", "價格基準", "DATA_GOVERNANCE", "enum", "adj_close", "所有價格線、報酬與技術面只使用 adjusted price", "must_equal_adj_close"),
    ParameterPolicy("GOV_VOLUME_BASIS", "成交量基準", "DATA_GOVERNANCE", "enum", "non_day_trade", "成交量與成交值先扣除當沖，不得同時輸入 raw 與 ex-day-trade volume", "must_equal_non_day_trade"),
    ParameterPolicy("GOV_TZ", "市場時區", "DATA_GOVERNANCE", "IANA_timezone", "market_specific", "以 IANA 時區與交易所 session 日曆處理跨市場資料", "must_be_iana_timezone"),
    ParameterPolicy("GOV_CALENDAR", "交易日曆", "DATA_GOVERNANCE", "versioned_table", "official_exchange", "區分 open、closed、settlement_only 與 early_close", "must_have_market_date_status"),
    ParameterPolicy("GOV_CONFIRMATION", "資料確認狀態", "DATA_GOVERNANCE", "enum", "confirmed_only", "訊號只能使用已確認 bar，HTF 只能使用已完成資料", "must_be_confirmed"),
    ParameterPolicy("GOV_LAG", "跨市場資料滯後", "DATA_GOVERNANCE", "trading_sessions", 1, "當來源收盤晚於台灣收盤，移至下一個台灣交易日可用", "must_not_be_negative"),
    ParameterPolicy("GOV_MISSING", "缺值政策", "DATA_GOVERNANCE", "enum", "NA_NEVER_ZERO_FILL", "休市與缺資料不得轉成零報酬或零成交量", "must_preserve_null"),
    ParameterPolicy("GOV_EXECUTION", "執行日規則", "DATA_GOVERNANCE", "enum", "T_PLUS_1", "t 日收盤產生訊號，最早 t+1 執行", "must_equal_t_plus_1"),
    ParameterPolicy("RISK_WINDOW", "風險 rolling 週期", "RISK", "trading_days", 60, "Sharpe、Sortino、VaR 與 CVaR 的尾端觀察窗", "must_be_ge_min_samples"),
    ParameterPolicy("RISK_MIN_SAMPLES", "風險最小樣本", "RISK", "observations", 30, "風險統計的最小有效觀測數", "must_be_ge_2_and_le_window"),
    ParameterPolicy("RISK_PERIODS_PER_YEAR", "年化週期", "RISK", "periods", 252, "將日頻風險統計年化的週期數", "must_be_positive"),
    ParameterPolicy("RISK_RF_ANNUAL", "年化無風險率", "RISK", "decimal_return", 0.0, "Sharpe/Sortino 超額報酬的年化無風險率", "must_be_greater_than_minus_one"),
    ParameterPolicy("RISK_MAR_ANNUAL", "年化 MAR", "RISK", "decimal_return", 0.0, "Sortino 下行報酬的最低可接受年化報酬", "must_be_greater_than_minus_one"),
    ParameterPolicy("RISK_VAR_CONFIDENCE", "VaR 信賴水準", "RISK", "probability", 0.95, "歷史 VaR/CVaR 的損失分位數", "must_be_between_zero_and_one"),
)


INDICATOR_LOGIC_LIBRARY: dict[str, dict[str, str]] = {
    "SMA": {"category": "TREND", "formula": "mean(source[t-n+1:t])", "source": "adj_close", "warmup": "null_until_n"},
    "EMA": {"category": "TREND", "formula": "alpha*source[t]+(1-alpha)*ema[t-1]", "source": "adj_close", "warmup": "seed_policy_required"},
    "RSI": {"category": "MOMENTUM", "formula": "100-100/(1+RMA(gain,n)/RMA(loss,n))", "source": "adj_close", "warmup": "null_until_rma_seed"},
    "STOCHASTIC": {"category": "MOMENTUM", "formula": "100*(close-lowest(low,n))/(highest(high,n)-lowest(low,n)) then SMA smooth", "source": "adjusted_ohlc", "warmup": "null_until_n_and_smoothing"},
    "ROC": {"category": "MOMENTUM", "formula": "100*(adj_close/adj_close[n]-1)", "source": "adj_close", "warmup": "null_until_n"},
    "WILLIAMS_R": {"category": "MOMENTUM", "formula": "-100*(highest(high,n)-close)/(highest(high,n)-lowest(low,n))", "source": "adjusted_ohlc", "warmup": "null_until_n"},
    "CCI": {"category": "MOMENTUM", "formula": "(hlc3-SMA(hlc3,n))/(0.015*mean_absolute_deviation)", "source": "adjusted_ohlc", "warmup": "null_until_n"},
    "MACD": {"category": "TREND", "formula": "EMA(fast)-EMA(slow); signal=EMA(macd)", "source": "adj_close", "warmup": "slow_plus_signal"},
    "TR": {"category": "VOLATILITY", "formula": "max(high-low,abs(high-prev_close),abs(low-prev_close))", "source": "adjusted_ohlc", "warmup": "first_bar_high_low"},
    "ATR": {"category": "VOLATILITY", "formula": "RMA(TR,n)", "source": "adjusted_ohlc", "warmup": "rma_seed_required"},
    "BOLLINGER": {"category": "VOLATILITY", "formula": "SMA(source,n)+/-k*rolling_std(source,n)", "source": "adj_close", "warmup": "null_until_n"},
    "KELTNER": {"category": "VOLATILITY", "formula": "EMA(source,basis_n)+/-multiplier*RMA(TR,atr_n)", "source": "adjusted_ohlc", "warmup": "basis_and_atr_warmup"},
    "DONCHIAN": {"category": "VOLATILITY", "formula": "upper=max(high,n); lower=min(low,n)", "source": "adjusted_ohlc", "warmup": "null_until_n"},
    "VWAP": {"category": "VOLUME_FLOW", "formula": "sum(hlc3*non_day_trade_volume)/sum(non_day_trade_volume)", "source": "adjusted_ohlc_and_non_day_trade_volume", "warmup": "session_reset"},
    "OBV": {"category": "VOLUME_FLOW", "formula": "cumsum(sign(adj_close-prev_adj_close)*non_day_trade_volume)", "source": "adj_close_and_non_day_trade_volume", "warmup": "seed_zero_or_null"},
    "MFI": {"category": "VOLUME_FLOW", "formula": "100-100/(1+positive_mf/negative_mf)", "source": "adjusted_ohlc_and_non_day_trade_volume", "warmup": "null_until_n"},
    "CMF": {"category": "VOLUME_FLOW", "formula": "sum(mfm*non_day_trade_volume)/sum(non_day_trade_volume)", "source": "adjusted_ohlc_and_non_day_trade_volume", "warmup": "null_until_n"},
    "ADL": {"category": "VOLUME_FLOW", "formula": "cumsum(((2*close-high-low)/(high-low))*non_day_trade_volume)", "source": "adjusted_ohlc_and_non_day_trade_volume", "warmup": "seed_zero_or_null"},
    "BETA": {"category": "RISK", "formula": "cov(asset_ret,benchmark_ret)/var(benchmark_ret)", "source": "aligned_adjusted_returns", "warmup": "min_samples"},
    "SHARPE": {"category": "RISK", "formula": "mean(excess_ret)/sample_std(excess_ret)*sqrt(annualization)", "source": "aligned_strategy_returns_and_rf", "warmup": "min_samples"},
    "SORTINO": {"category": "RISK", "formula": "mean(excess_ret)/downside_deviation", "source": "aligned_strategy_returns_and_rf", "warmup": "min_samples"},
    "CALMAR": {"category": "RISK", "formula": "CAGR/abs(max_drawdown)", "source": "equity_curve", "warmup": "window_and_nonzero_drawdown"},
    "VAR": {"category": "RISK", "formula": "rolling_loss_quantile(alpha)", "source": "loss_series", "warmup": "min_samples"},
    "CVAR": {"category": "RISK", "formula": "mean(loss[loss>=VaR_alpha])", "source": "loss_series", "warmup": "tail_sample_required"},
    "DRAWDOWN": {"category": "RISK", "formula": "equity/cumulative_peak-1", "source": "equity_curve", "warmup": "first_equity_seed"},
    "CORRELATION": {"category": "STATISTICAL_STRUCTURE", "formula": "cov(x,y)/(std(x)*std(y))", "source": "aligned_returns", "warmup": "min_samples_and_nonzero_std"},
    "AUTOCORRELATION": {"category": "STATISTICAL_STRUCTURE", "formula": "corr(return[t],return[t-lag])", "source": "ordered_returns", "warmup": "lag_plus_window"},
    "R2": {"category": "STATISTICAL_STRUCTURE", "formula": "1-SSE/SST", "source": "rolling_regression", "warmup": "min_samples_and_nonzero_sst"},
    "SKEWNESS": {"category": "STATISTICAL_STRUCTURE", "formula": "third_central_moment/std^3", "source": "ordered_returns", "warmup": "min_samples"},
    "KURTOSIS": {"category": "STATISTICAL_STRUCTURE", "formula": "fourth_central_moment/std^4[-3 if excess]", "source": "ordered_returns", "warmup": "min_samples"},
}


FACTOR_LIBRARY: dict[str, dict[str, Any]] = {
    "FACTOR_TREND": {"name_zh": "趨勢因子", "inputs": ["ema_spread_20_60", "adx_14", "price_vs_ema_60"], "direction": "higher_is_stronger", "requires": ["adj_close"]},
    "FACTOR_MOMENTUM": {"name_zh": "動能因子", "inputs": ["momentum_score", "roc_14", "return_autocorr_20"], "direction": "context_dependent", "requires": ["adj_close"]},
    "FACTOR_VOLATILITY": {"name_zh": "波動因子", "inputs": ["atr_pct", "return_vol_20", "bb_width_20"], "direction": "risk_not_alpha", "requires": ["adj_close"]},
    "FACTOR_VOLUME_CONFIRMATION": {"name_zh": "量價確認因子", "inputs": ["volume_ratio_20", "cmf_20", "return_volume_corr_20"], "direction": "confirmation", "requires": ["non_day_trade_volume"]},
    "FACTOR_MARKET_RELATIVE": {"name_zh": "相對市場因子", "inputs": ["rolling_beta", "rolling_corr", "residual_return_60"], "direction": "relative", "requires": ["adj_close", "benchmark_adj_close"]},
    "FACTOR_RISK_ADJUSTED": {"name_zh": "風險調整因子", "inputs": ["rolling_sharpe", "rolling_sortino", "rolling_calmar", "rolling_var", "rolling_cvar"], "direction": "higher_is_better_except_tail_risk", "requires": ["strategy_return_or_asset_return", "risk_free_rate_policy"]},
    "FACTOR_CAPITAL_FLOW": {"name_zh": "籌碼流量因子", "inputs": ["institutional_amount_ratio", "toca_z_score"], "direction": "confirmation", "requires": ["non_day_trade_turnover", "available_at"]},
}


def ssot_manifest() -> dict[str, Any]:
    return {
        "ssot_version": SSOT_VERSION,
        "policy_version": POLICY_VERSION,
        "market_policies": {key: asdict(value) for key, value in MARKET_POLICIES.items()},
        "parameter_policies": [asdict(value) for value in PARAMETER_POLICIES],
        "indicator_logic_library": INDICATOR_LOGIC_LIBRARY,
        "factor_library": FACTOR_LIBRARY,
        "global_invariants": {
            "price_basis": "adj_close_only",
            "volume_basis": "non_day_trade_only",
            "raw_volume_allowed_in_analysis": False,
            "raw_turnover_allowed_in_analysis": False,
            "missing_volume_policy": "NA_NEVER_ZERO_FILL",
            "missing_price_policy": "NA_NEVER_ZERO_FILL",
            "htf_policy": "confirmed_only",
            "cross_market_policy": "timezone_aware_close_utc_asof",
        "execution_policy": "signal_t_execute_t_plus_1",
        "risk_policy": {
            "return_basis": "completed_bar_return",
            "risk_free_rate_conversion": "annual_compound_to_periodic",
            "sharpe_std_ddof": 1,
            "var_loss_sign": "loss=-return",
            "var_interpolation": "linear",
            "cvar_tail": "loss_greater_or_equal_var",
            "calmar_equity_basis": "cumulative_product_of_one_plus_return",
        },
    },
}


def validate_governance_frame(
    df: pl.DataFrame | pl.LazyFrame,
    *,
    require_price: bool = True,
    require_non_day_trade_volume: bool = False,
) -> None:
    columns = set(df.collect_schema().names()) if isinstance(df, pl.LazyFrame) else set(df.columns)
    if require_price and "adj_close" not in columns:
        raise ValueError("governance policy requires adj_close; raw close cannot replace it")
    if "close" in columns and "adj_close" not in columns:
        raise ValueError("raw close is not an analysis price")
    if require_non_day_trade_volume and "non_day_trade_volume" not in columns:
        raise ValueError("governance policy requires non_day_trade_volume")
    if "volume" in columns and "non_day_trade_volume" not in columns:
        raise ValueError("raw volume is forbidden in analysis; provide non_day_trade_volume")
    if "total_turnover" in columns and "non_day_trade_turnover" not in columns:
        raise ValueError("raw turnover is forbidden in analysis; provide non_day_trade_turnover")


def prepare_non_day_trade_activity(
    df: pl.DataFrame | pl.LazyFrame,
    *,
    volume_col: str = "volume",
    day_trade_volume_col: str = "day_trade_volume",
    turnover_col: str = "total_turnover",
    day_trade_turnover_col: str = "day_trade_turnover",
) -> pl.DataFrame:
    """Convert official raw activity to the only analysis volume/value fields.

    This is an ingestion-boundary operation. Downstream indicator modules do
    not accept raw volume or raw turnover, which prevents accidental double
    counting of day-trade activity.
    """

    columns = set(df.collect_schema().names()) if isinstance(df, pl.LazyFrame) else set(df.columns)
    q = df.lazy() if isinstance(df, pl.DataFrame) else df
    expressions: list[pl.Expr] = []
    if {volume_col, day_trade_volume_col}.issubset(columns):
        expressions.append(
            pl.when(
                (pl.col(volume_col) >= 0)
                & (pl.col(day_trade_volume_col) >= 0)
                & (pl.col(day_trade_volume_col) <= pl.col(volume_col))
            ).then(pl.col(volume_col) - pl.col(day_trade_volume_col))
            .otherwise(None)
            .alias("non_day_trade_volume")
        )
    if {turnover_col, day_trade_turnover_col}.issubset(columns):
        expressions.append(
            pl.when(
                (pl.col(turnover_col) >= 0)
                & (pl.col(day_trade_turnover_col) >= 0)
                & (pl.col(day_trade_turnover_col) <= pl.col(turnover_col))
            ).then(pl.col(turnover_col) - pl.col(day_trade_turnover_col))
            .otherwise(None)
            .alias("non_day_trade_turnover")
        )
    if not expressions:
        raise ValueError("official input must contain raw volume/day-trade or turnover/day-trade pairs")
    return q.with_columns(expressions).collect()


def normalize_market_timestamp(
    df: pl.DataFrame | pl.LazyFrame,
    *,
    timestamp_col: str = "timestamp",
    market_col: str = "market_code",
) -> pl.LazyFrame:
    """Attach UTC and local session dates without assuming a fixed offset."""

    columns = set(df.collect_schema().names()) if isinstance(df, pl.LazyFrame) else set(df.columns)
    required = {timestamp_col, market_col}
    missing = required - columns
    if missing:
        raise ValueError(f"missing timestamp normalization columns: {sorted(missing)}")
    q = df.lazy() if isinstance(df, pl.DataFrame) else df
    # Polars requires a tz-aware Datetime for conversion. Unknown market codes
    # are rejected rather than silently assigned a wrong holiday/session rule.
    known = set(MARKET_POLICIES)
    invalid = q.select(pl.col(market_col).unique()).collect().get_column(market_col).to_list()
    unknown = sorted(set(invalid) - known)
    if unknown:
        raise ValueError(f"unknown market codes: {unknown}")
    q = q.with_columns(
        pl.col(timestamp_col).cast(pl.Datetime(time_zone="UTC")).alias("timestamp_utc")
    )
    tw = pl.col(market_col) == "TW"
    q = q.with_columns(
        pl.when(tw).then(pl.lit("Asia/Taipei")).otherwise(pl.lit("America/New_York")).alias("market_timezone"),
        pl.when(tw)
        .then(pl.col("timestamp_utc").dt.convert_time_zone("Asia/Taipei").dt.replace_time_zone(None))
        .otherwise(pl.col("timestamp_utc").dt.convert_time_zone("America/New_York").dt.replace_time_zone(None))
        .alias("timestamp_local")
    ).with_columns(
        pl.col("timestamp_local").dt.date().alias("market_session_date")
    )
    return q


def align_confirmed_closes(
    prices: pl.DataFrame | pl.LazyFrame,
    *,
    left_market: str,
    right_market: str,
    left_date_col: str = "market_session_date",
    right_date_col: str = "market_session_date",
) -> pl.DataFrame:
    """Align two confirmed price lines by a backward ``close_utc`` as-of join.

    The right-market close is included only when it is no later than the left
    market's cutoff. Thus a US close that occurs after a Taiwan close cannot
    enter the same Taiwan signal row; it becomes available on the next Taiwan
    session. This function does not forward-fill closed sessions.
    """

    validate_governance_frame(prices, require_price=True)
    columns = set(prices.collect_schema().names()) if isinstance(prices, pl.LazyFrame) else set(prices.columns)
    required = {"market_code", left_date_col, right_date_col, "close_utc", "adj_close"}
    missing = required - columns
    if missing:
        raise ValueError(f"missing cross-market alignment columns: {sorted(missing)}")
    frame = prices.collect() if isinstance(prices, pl.LazyFrame) else prices
    left = frame.filter(pl.col("market_code") == left_market).select([
        pl.col(left_date_col).alias("session_date"),
        pl.col("close_utc").alias("left_close_utc"),
        pl.col("adj_close").alias("left_adj_close"),
    ]).sort("left_close_utc")
    right = frame.filter(pl.col("market_code") == right_market).select([
        pl.col(right_date_col).alias("right_session_date"),
        pl.col("close_utc").alias("right_close_utc"),
        pl.col("adj_close").alias("right_adj_close"),
    ]).sort("right_close_utc")
    aligned = left.join_asof(
        right,
        left_on="left_close_utc",
        right_on="right_close_utc",
        strategy="backward",
    )
    return aligned.filter(pl.col("right_adj_close").is_not_null()).with_columns(
        (pl.col("session_date") != pl.col("right_session_date")).cast(pl.Int8).alias("cross_session_lag")
    ).sort("session_date")


def policy_table() -> pl.DataFrame:
    return pl.DataFrame([asdict(item) for item in PARAMETER_POLICIES])


def factor_table() -> pl.DataFrame:
    rows = []
    for code, item in FACTOR_LIBRARY.items():
        rows.append({"factor_code": code, **item, "inputs": ",".join(item["inputs"]), "requires": ",".join(item["requires"])})
    return pl.DataFrame(rows)


def logic_table() -> pl.DataFrame:
    return pl.DataFrame([{"logic_code": key, **value} for key, value in INDICATOR_LOGIC_LIBRARY.items()])
