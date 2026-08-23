from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

"""
VIA Taiwan Stock Group Classification & Price-Volume Volatility Engine v0100.

核心邊界：
1. SSOT 功能族群、低共動審查、Leader/Peer/Lagger 時序角色三者分離。
2. Lagger 只代表時間落後角色，不代表績效較差。
3. 成交量、資金流與波動資料不得 forward-fill；Adjusted OHLC 不得被原始 Close 覆寫。
4. 所有角色門檻由滾動分布、橫斷面分位數、樣本數與波動狀態動態產生。
5. 正式流程 fail-closed；測試資料只允許在 --self-test 使用。
"""

# =============================================================================
# def 00 PARAMETERS — 所有可調參數集中於檔案頂部
# =============================================================================

import argparse
import hashlib
import json
import logging
import math
import os
import re
import sys
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np
import pandas as pd


ENGINE_ID = "VIA_TW_GROUP_PRICE_VOLUME_VOLATILITY_ENGINE_V0100"
ENGINE_VERSION = "0.1.0"
TAXONOMY_VERSION = "VIA_SubGroup_SSOT_v0100"

DEFAULT_PRICE_PATH = Path(r"C:\Users\tonyk\OneDrive\桌面\tw_stock\StockData.parquet")
DEFAULT_GROUP_SSOT_PATH = Path(r"C:\Users\tonyk\Downloads\VIA_SubGroup_SSOT_v0100.xlsx")
DEFAULT_TICKER_LIST_PATH = Path(
    r"C:\Users\tonyk\OneDrive\桌面\tw_stock\dict\TickerList\AllStockYfinanceTickerList.txt"
)
DEFAULT_OUTPUT_ROOT = Path(r"C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\outputs\tw_group_price_volume")

DEFAULT_START_DATE = "2021-01-01"
DEFAULT_END_DATE = None
DEFAULT_NORMALIZED_DATE = None

DEFAULT_VOLATILITY_WINDOW = 20
DEFAULT_RELATION_WINDOW = 60
DEFAULT_LONG_WINDOW = 120
DEFAULT_LEAD_LAGS = (1, 2, 3, 5)
DEFAULT_MIN_OBSERVATIONS = 60
DEFAULT_MIN_GROUP_MEMBERS = 3
DEFAULT_WALK_FORWARD_TRAIN_DAYS = 120
DEFAULT_WALK_FORWARD_TEST_DAYS = 20
DEFAULT_WALK_FORWARD_STEP_DAYS = 20

# 這些是動態分位數的起始值，不是固定分類門檻。
DEFAULT_BASE_COMOVEMENT_QUANTILE = 0.40
DEFAULT_BASE_LEADERSHIP_QUANTILE = 0.70
DEFAULT_BASE_SIZE_QUANTILE_LOW = 0.40
DEFAULT_BASE_SIZE_QUANTILE_HIGH = 0.85
DEFAULT_FDR_ALPHA = 0.05
DEFAULT_ROLE_SEPARATION_Z = 1.96
DEFAULT_QUANTILE_ADJUSTMENT_LIMIT = 0.15

CSV_ENCODING = "utf-8-sig"
DATE_OUTPUT_FORMAT = "%Y/%m/%d"
DATE_CHART_FORMAT = "%Y-%m-%d"
PARQUET_COMPRESSION = "zstd"
OUTPUT_DATASETS = (
    "stock_price_volume_features",
    "group_role_classification",
    "group_index",
    "group_price_volume_observation",
    "walk_forward_validation",
    "validation_gates",
)

PRICE_COLUMN_ALIASES: Mapping[str, tuple[str, ...]] = {
    "Date": ("Date", "date", "TradingDate", "TradeDate"),
    "Ticker": ("Ticker", "ticker", "Symbol", "TW_YF_TICKER", "YFINANCE"),
    "Name": ("Name", "name", "StockName", "個股"),
    "Adj_Open": ("Adj_Open", "Adj Open", "AdjustedOpen", "adj_open"),
    "Adj_High": ("Adj_High", "Adj High", "AdjustedHigh", "adj_high"),
    "Adj_Low": ("Adj_Low", "Adj Low", "AdjustedLow", "adj_low"),
    "Adj_Close": (
        "Adj_Close",
        "Adj Close",
        "AdjustedClose",
        "adj_close",
        "normalized_close",
        "price_close",
    ),
    "Volume": ("Volume", "volume", "TradingVolume", "成交量"),
    "Turnover": ("Turnover", "turnover", "TradingValue", "成交值"),
    "DayTradeTurnover": (
        "DayTradeTurnover",
        "Day_Trade_Turnover",
        "day_trade_turnover",
        "當沖成交值",
    ),
    "MarketCap": ("MarketCap", "Market_Cap", "market_cap", "市值"),
}

SSOT_REQUIRED_COLUMNS = (
    "L1",
    "L2",
    "個股",
    "TW_TICKER",
    "市場",
    "市場驗證",
    "YFINANCE",
    "定位",
    "歸屬",
    "計入族群指數",
)


@dataclass(frozen=True)
class EngineConfig:
    price_path: Path = DEFAULT_PRICE_PATH
    group_ssot_path: Path = DEFAULT_GROUP_SSOT_PATH
    ticker_list_path: Path = DEFAULT_TICKER_LIST_PATH
    output_root: Path = DEFAULT_OUTPUT_ROOT
    start_date: str = DEFAULT_START_DATE
    end_date: str | None = DEFAULT_END_DATE
    normalized_date: str | None = DEFAULT_NORMALIZED_DATE
    volatility_window: int = DEFAULT_VOLATILITY_WINDOW
    relation_window: int = DEFAULT_RELATION_WINDOW
    long_window: int = DEFAULT_LONG_WINDOW
    lead_lags: tuple[int, ...] = DEFAULT_LEAD_LAGS
    min_observations: int = DEFAULT_MIN_OBSERVATIONS
    min_group_members: int = DEFAULT_MIN_GROUP_MEMBERS
    walk_forward_train_days: int = DEFAULT_WALK_FORWARD_TRAIN_DAYS
    walk_forward_test_days: int = DEFAULT_WALK_FORWARD_TEST_DAYS
    walk_forward_step_days: int = DEFAULT_WALK_FORWARD_STEP_DAYS
    base_comovement_quantile: float = DEFAULT_BASE_COMOVEMENT_QUANTILE
    base_leadership_quantile: float = DEFAULT_BASE_LEADERSHIP_QUANTILE
    fdr_alpha: float = DEFAULT_FDR_ALPHA
    role_separation_z: float = DEFAULT_ROLE_SEPARATION_Z
    quantile_adjustment_limit: float = DEFAULT_QUANTILE_ADJUSTMENT_LIMIT
    strict: bool = False
    use_yfinance_fallback: bool = False
    write_outputs: bool = True


@dataclass
class EngineResult:
    stock_features: pd.DataFrame
    role_classification: pd.DataFrame
    group_index: pd.DataFrame
    group_observation: pd.DataFrame
    walk_forward_validation: pd.DataFrame
    validation_gates: pd.DataFrame
    manifest: dict[str, object]


LOGGER = logging.getLogger(ENGINE_ID)


# =============================================================================
# def 01 LOGGING / COMMON UTILITIES
# =============================================================================


def def_configure_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="def [%(asctime)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def def_json_safe(value: object) -> object:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, pd.Timestamp):
        return value.strftime(DATE_CHART_FORMAT)
    raise TypeError(f"Unsupported JSON value: {type(value)!r}")


def def_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def def_column_key(value: object) -> str:
    return re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]", "", str(value)).lower()


def def_find_column(columns: Iterable[object], candidates: Sequence[str]) -> str | None:
    keyed = {def_column_key(column): str(column) for column in columns}
    for candidate in candidates:
        match = keyed.get(def_column_key(candidate))
        if match is not None:
            return match
    return None


def def_ticker_base(value: object) -> str:
    text = str(value).strip().upper()
    match = re.match(r"^(\d{4}[A-Z]?)", text)
    return match.group(1) if match else text.split(".", 1)[0]


def def_normalize_ticker(value: object, market: object = "") -> str:
    text = str(value).strip().upper().replace(" ", "")
    if not text or text in {"NAN", "NONE", "<NA>"}:
        return ""
    text = text.replace(".TPE", ".TW")
    if text.endswith((".TW", ".TWO")):
        return text
    base = def_ticker_base(text)
    market_text = str(market).strip()
    suffix = ".TWO" if any(token in market_text for token in ("上櫃", "興櫃", "TPEX", "OTC")) else ".TW"
    return f"{base}{suffix}"


def def_validate_config(config: EngineConfig) -> None:
    if config.volatility_window < 5:
        raise ValueError("volatility_window must be >= 5")
    if config.relation_window < 20:
        raise ValueError("relation_window must be >= 20")
    if config.min_observations < config.relation_window:
        raise ValueError("min_observations must be >= relation_window")
    if config.min_group_members < 2:
        raise ValueError("min_group_members must be >= 2")
    if not config.lead_lags or min(config.lead_lags) < 1:
        raise ValueError("lead_lags must contain positive integers")
    for value in (
        config.base_comovement_quantile,
        config.base_leadership_quantile,
        config.fdr_alpha,
    ):
        if not 0 < value < 1:
            raise ValueError("quantile and alpha parameters must be between 0 and 1")


# =============================================================================
# def 02 SSOT INGESTION / VALIDATION
# =============================================================================


def def_load_group_ssot(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Group SSOT not found: {path}")
    frame = pd.read_excel(path, sheet_name="20_成員名冊", dtype=object, engine="openpyxl")
    missing = [column for column in SSOT_REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"SSOT missing required columns: {missing}")

    output = pd.DataFrame(
        {
            "L1": frame["L1"].astype("string").str.strip(),
            "GroupId": frame["L2"].astype("string").str.strip(),
            "Name": frame["個股"].astype("string").str.strip(),
            "TickerBase": frame["TW_TICKER"].map(def_ticker_base),
            "Market": frame["市場"].astype("string").str.strip(),
            "MarketValidation": frame["市場驗證"].astype("string").str.strip().str.upper(),
            "Position": frame["定位"].astype("string").str.strip().str.upper(),
            "Ownership": frame["歸屬"].astype("string").str.strip().str.upper(),
            "IncludeFromSource": frame["計入族群指數"].astype("string").str.strip().str.upper().eq("Y"),
            "SourceRole": frame.get("MethodA角色(來源)", pd.Series(index=frame.index, dtype="object")),
            "SourceSize": frame.get("MethodB規模(來源)", pd.Series(index=frame.index, dtype="object")),
            "Source": frame.get("來源", pd.Series(index=frame.index, dtype="object")),
        }
    )
    output["Ticker"] = [
        def_normalize_ticker(base, market)
        for base, market in zip(output["TickerBase"], output["Market"], strict=False)
    ]
    output["TaxonomyVersion"] = TAXONOMY_VERSION
    output = output.loc[output["Ticker"].ne("") & output["GroupId"].notna()].copy()
    output = output.drop_duplicates(["GroupId", "Ticker"], keep="last").reset_index(drop=True)

    primary_count = output.groupby("Ticker")["Ownership"].apply(
        lambda values: int(values.eq("PRIMARY").sum())
    )
    invalid_primary = primary_count.loc[primary_count.ne(1)]
    if not invalid_primary.empty:
        raise ValueError(f"SSOT PRIMARY uniqueness failed for {invalid_primary.index.tolist()[:10]}")
    return output


def def_ssot_summary(ssot: pd.DataFrame) -> dict[str, int]:
    return {
        "l1_count": int(ssot["L1"].nunique()),
        "l2_count": int(ssot["GroupId"].nunique()),
        "membership_rows": int(len(ssot)),
        "unique_tickers": int(ssot["Ticker"].nunique()),
        "cross_group_tickers": int((ssot.groupby("Ticker")["GroupId"].nunique() > 1).sum()),
        "market_locked_rows": int(ssot["MarketValidation"].eq("LOCKED").sum()),
        "market_pending_rows": int(ssot["MarketValidation"].eq("PENDING").sum()),
    }


# =============================================================================
# def 03 PRICE DATA INGESTION / INCREMENTAL FALLBACK
# =============================================================================


def def_read_price_file(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    suffix = path.suffix.lower()
    if suffix in {".csv", ".txt"}:
        return pd.read_csv(path, low_memory=False)
    if suffix in {".parquet", ".pq", ""}:
        try:
            return pd.read_parquet(path)
        except Exception as parquet_error:
            if suffix == "":
                try:
                    return pd.read_csv(path, low_memory=False)
                except Exception:
                    pass
            raise RuntimeError(f"Unable to read parquet {path}: {parquet_error}") from parquet_error
    raise ValueError(f"Unsupported price file: {path}")


def def_fetch_yfinance_incremental(
    tickers: Sequence[str], start_date: str, end_date: str | None
) -> pd.DataFrame:
    try:
        import yfinance as yf  # type: ignore
    except ImportError as exc:
        raise RuntimeError("yfinance fallback requested but yfinance is not installed") from exc

    frames: list[pd.DataFrame] = []
    for ticker in tickers:
        LOGGER.info("yfinance fallback fetch: %s", ticker)
        raw = yf.download(
            ticker,
            start=start_date,
            end=end_date,
            auto_adjust=False,
            actions=False,
            progress=False,
            threads=False,
        )
        if raw.empty:
            continue
        raw = raw.reset_index()
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = [column[0] for column in raw.columns]
        raw["Ticker"] = ticker
        required = {"Open", "High", "Low", "Close", "Adj Close"}
        if not required.issubset(raw.columns):
            LOGGER.warning("yfinance adjusted OHLC unavailable for %s", ticker)
            continue
        adjustment_factor = raw["Adj Close"] / raw["Close"].replace(0, np.nan)
        raw["Adj_Open"] = raw["Open"] * adjustment_factor
        raw["Adj_High"] = raw["High"] * adjustment_factor
        raw["Adj_Low"] = raw["Low"] * adjustment_factor
        raw["Adj_Close"] = raw["Adj Close"]
        frames.append(raw)
    if not frames:
        raise RuntimeError("yfinance fallback returned no rows")
    return pd.concat(frames, ignore_index=True, sort=False)


def def_standardize_price_data(
    raw: pd.DataFrame, ssot: pd.DataFrame, config: EngineConfig
) -> pd.DataFrame:
    column_map: dict[str, str] = {}
    for canonical, aliases in PRICE_COLUMN_ALIASES.items():
        found = def_find_column(raw.columns, aliases)
        if found is not None:
            column_map[canonical] = found

    for required in ("Date", "Ticker", "Adj_Close"):
        if required not in column_map:
            if required == "Adj_Close":
                raise ValueError(
                    "Adjusted Close is required. Raw Close fallback is intentionally fail-closed."
                )
            raise ValueError(f"Price data missing required column: {required}")

    output = pd.DataFrame(index=raw.index)
    for canonical, source in column_map.items():
        output[canonical] = raw[source]

    canonical_ticker = (
        ssot.sort_values("Ownership")
        .drop_duplicates("TickerBase")
        .set_index("TickerBase")["Ticker"]
        .to_dict()
    )
    output["TickerBase"] = output["Ticker"].map(def_ticker_base)
    output["Ticker"] = output["TickerBase"].map(canonical_ticker).fillna(
        output["Ticker"].map(def_normalize_ticker)
    )
    output["Date"] = pd.to_datetime(output["Date"], errors="coerce").dt.normalize()

    numeric_columns = [
        "Adj_Open",
        "Adj_High",
        "Adj_Low",
        "Adj_Close",
        "Volume",
        "Turnover",
        "DayTradeTurnover",
        "MarketCap",
    ]
    for column in numeric_columns:
        if column not in output:
            output[column] = np.nan
        output[column] = pd.to_numeric(output[column], errors="coerce")

    start = pd.Timestamp(config.start_date)
    end = pd.Timestamp(config.end_date) if config.end_date else None
    output = output.loc[output["Date"].notna() & output["Ticker"].ne("")]
    output = output.loc[output["Date"].ge(start)]
    if end is not None:
        output = output.loc[output["Date"].le(end)]

    output["PriceSource"] = "ADJUSTED_CLOSE"
    output["TurnoverEstimated"] = output["Turnover"].isna() & output["Volume"].notna()
    output["TurnoverEffective"] = output["Turnover"].where(
        output["Turnover"].notna(), output["Adj_Close"] * output["Volume"]
    )
    output["NonDayTradeTurnover"] = (
        output["TurnoverEffective"] - output["DayTradeTurnover"]
    ).where(
        output["TurnoverEffective"].notna() & output["DayTradeTurnover"].notna()
    ).clip(lower=0)

    output = output.sort_values(["Ticker", "Date"])
    duplicate_count = int(output.duplicated(["Date", "Ticker"], keep=False).sum())
    if duplicate_count:
        LOGGER.warning("Deduplicating %s duplicated Date+Ticker rows", duplicate_count)
    output = output.drop_duplicates(["Date", "Ticker"], keep="last").reset_index(drop=True)
    return output


def def_load_price_data(ssot: pd.DataFrame, config: EngineConfig) -> pd.DataFrame:
    if config.price_path.exists():
        raw = def_read_price_file(config.price_path)
    elif config.use_yfinance_fallback:
        raw = def_fetch_yfinance_incremental(
            sorted(ssot["Ticker"].unique()), config.start_date, config.end_date
        )
    else:
        raise FileNotFoundError(
            f"Local price source not found: {config.price_path}. "
            "Use --use-yfinance-fallback only when network fallback is explicitly intended."
        )
    return def_standardize_price_data(raw, ssot, config)


# =============================================================================
# def 04 STOCK PRICE / VOLUME / VOLATILITY FEATURES
# =============================================================================


def def_rolling_robust_z(series: pd.Series, window: int) -> pd.Series:
    minimum = max(5, window // 2)
    median = series.rolling(window, min_periods=minimum).median()
    deviation = (series - median).abs()
    mad = deviation.rolling(window, min_periods=minimum).median()
    return (series - median) / (1.4826 * mad.replace(0, np.nan))


def def_garman_klass(group: pd.DataFrame, window: int) -> pd.Series:
    valid = (
        group[["Adj_Open", "Adj_High", "Adj_Low", "Adj_Close"]]
        .replace([np.inf, -np.inf], np.nan)
        .gt(0)
        .all(axis=1)
    )
    log_hl = np.log(group["Adj_High"] / group["Adj_Low"]).where(valid)
    log_co = np.log(group["Adj_Close"] / group["Adj_Open"]).where(valid)
    variance = 0.5 * log_hl.pow(2) - (2 * np.log(2) - 1) * log_co.pow(2)
    return np.sqrt(252 * variance.clip(lower=0).rolling(window, min_periods=window // 2).mean())


def def_compute_stock_features(prices: pd.DataFrame, config: EngineConfig) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    window = config.volatility_window
    relation_window = config.relation_window

    for ticker, source in prices.groupby("Ticker", sort=True):
        group = source.sort_values("Date").copy()
        close = group["Adj_Close"].where(group["Adj_Close"].gt(0))
        group["LogReturn"] = np.log(close).diff()
        group["SimpleReturn"] = close.pct_change(fill_method=None)
        group["AbsReturn"] = group["LogReturn"].abs()
        group["LogVolume"] = np.log1p(group["Volume"].where(group["Volume"].ge(0)))
        group["VolumeChange"] = group["LogVolume"].diff()
        group["VolumeShockZ"] = def_rolling_robust_z(group["LogVolume"], window)
        group["TurnoverShockZ"] = def_rolling_robust_z(
            np.log1p(group["TurnoverEffective"].where(group["TurnoverEffective"].ge(0))),
            window,
        )
        group["RealizedVolatility20D"] = (
            group["LogReturn"].rolling(window, min_periods=window // 2).std(ddof=1)
            * math.sqrt(252)
        )
        log_hl = np.log(group["Adj_High"] / group["Adj_Low"]).where(
            group["Adj_High"].gt(0) & group["Adj_Low"].gt(0)
        )
        group["ParkinsonVolatility20D"] = np.sqrt(
            252
            * log_hl.pow(2).rolling(window, min_periods=window // 2).mean()
            / (4 * np.log(2))
        )
        group["GarmanKlassVolatility20D"] = def_garman_klass(group, window)
        group["ReturnVolumeCorrelation"] = group["LogReturn"].rolling(
            relation_window, min_periods=relation_window // 2
        ).corr(group["VolumeChange"])
        group["AbsReturnVolumeCorrelation"] = group["AbsReturn"].rolling(
            relation_window, min_periods=relation_window // 2
        ).corr(group["VolumeShockZ"])
        group["AmihudIlliquidity"] = group["AbsReturn"] / group[
            "NonDayTradeTurnover"
        ].replace(0, np.nan)
        obv_increment = np.sign(group["SimpleReturn"]) * group["Volume"]
        group["OBV"] = obv_increment.cumsum()
        rolling_mean = close.rolling(window, min_periods=window // 2).mean()
        rolling_std = close.rolling(window, min_periods=window // 2).std(ddof=1)
        group["PriceZScore20D"] = (close - rolling_mean) / rolling_std.replace(0, np.nan)
        group["Ticker"] = ticker
        frames.append(group)

    output = pd.concat(frames, ignore_index=True, sort=False)
    return output.sort_values(["Ticker", "Date"]).reset_index(drop=True)


# =============================================================================
# def 05 STATISTICS / DYNAMIC CRITERIA / FDR
# =============================================================================


def def_safe_correlation(left: pd.Series, right: pd.Series) -> tuple[float, int]:
    pair = pd.concat([left, right], axis=1).dropna()
    count = len(pair)
    if count < 8 or pair.iloc[:, 0].nunique() < 2 or pair.iloc[:, 1].nunique() < 2:
        return math.nan, count
    return float(pair.iloc[:, 0].corr(pair.iloc[:, 1])), count


def def_correlation_pvalue(correlation: float, observations: int) -> float:
    if not math.isfinite(correlation) or observations <= 3:
        return math.nan
    clipped = min(max(correlation, -0.999999), 0.999999)
    fisher_z = abs(np.arctanh(clipped)) * math.sqrt(observations - 3)
    return float(math.erfc(fisher_z / math.sqrt(2)))


def def_benjamini_hochberg(pvalues: pd.Series) -> pd.Series:
    result = pd.Series(np.nan, index=pvalues.index, dtype="float64")
    valid = pvalues.dropna().clip(0, 1).sort_values()
    count = len(valid)
    if count == 0:
        return result
    adjusted = valid * count / np.arange(1, count + 1)
    adjusted = np.minimum.accumulate(adjusted.iloc[::-1])[::-1].clip(upper=1)
    result.loc[adjusted.index] = adjusted
    return result


def def_dynamic_quantile(
    base_quantile: float,
    volatility_ratio: float,
    member_count: int,
    config: EngineConfig,
) -> float:
    volatility_adjustment = 0.08 * np.tanh(volatility_ratio - 1)
    sample_adjustment = 0.08 * np.tanh(
        (config.min_group_members - member_count) / max(config.min_group_members, 1)
    )
    adjustment = float(
        np.clip(
            volatility_adjustment + sample_adjustment,
            -config.quantile_adjustment_limit,
            config.quantile_adjustment_limit,
        )
    )
    return float(np.clip(base_quantile + adjustment, 0.05, 0.95))


def def_latest_volatility_ratio(group_return: pd.Series, window: int) -> float:
    rolling = group_return.rolling(window, min_periods=max(10, window // 2)).std(ddof=1)
    valid = rolling.dropna()
    if valid.empty or not math.isfinite(float(valid.median())) or float(valid.median()) == 0:
        return 1.0
    return float(valid.iloc[-1] / valid.median())


# =============================================================================
# def 06 MEMBERSHIP / LEADER-PEER-LAGGER CLASSIFICATION
# =============================================================================


def def_group_relationship_table(
    group_id: str,
    returns: pd.DataFrame,
    config: EngineConfig,
) -> tuple[pd.DataFrame, str, float]:
    provisional = returns.median(axis=1, skipna=True)
    latest_window = returns.tail(config.relation_window)
    volatility_ratio = def_latest_volatility_ratio(provisional, config.volatility_window)
    rows: list[dict[str, object]] = []

    for ticker in returns.columns:
        stock_window = latest_window[ticker]
        group_window = latest_window.drop(columns=ticker).median(axis=1, skipna=True)
        concurrent, concurrent_n = def_safe_correlation(stock_window, group_window)
        lead_candidates: list[tuple[int, float, int]] = []
        lag_candidates: list[tuple[int, float, int]] = []
        for lag in config.lead_lags:
            lead_corr, lead_n = def_safe_correlation(stock_window.shift(lag), group_window)
            lag_corr, lag_n = def_safe_correlation(stock_window, group_window.shift(lag))
            lead_candidates.append((lag, lead_corr, lead_n))
            lag_candidates.append((lag, lag_corr, lag_n))

        best_lead = max(
            lead_candidates,
            key=lambda item: item[1] if math.isfinite(item[1]) else -np.inf,
        )
        best_lag = max(
            lag_candidates,
            key=lambda item: item[1] if math.isfinite(item[1]) else -np.inf,
        )
        rows.append(
            {
                "GroupId": group_id,
                "Ticker": ticker,
                "AsOfDate": returns.index.max(),
                "ConcurrentCorrelation": concurrent,
                "ConcurrentObservations": concurrent_n,
                "ConcurrentPValue": def_correlation_pvalue(concurrent, concurrent_n),
                "BestLeadLagDays": best_lead[0],
                "BestLeadCorrelation": best_lead[1],
                "BestLeadObservations": best_lead[2],
                "BestLeadPValue": min(
                    def_correlation_pvalue(best_lead[1], best_lead[2])
                    * len(config.lead_lags),
                    1.0,
                ),
                "BestLaggerLagDays": best_lag[0],
                "BestLaggerCorrelation": best_lag[1],
                "BestLaggerObservations": best_lag[2],
                "BestLaggerPValue": min(
                    def_correlation_pvalue(best_lag[1], best_lag[2])
                    * len(config.lead_lags),
                    1.0,
                ),
            }
        )

    table = pd.DataFrame(rows)
    table["ConcurrentFDR"] = def_benjamini_hochberg(table["ConcurrentPValue"])
    table["LeadFDR"] = def_benjamini_hochberg(table["BestLeadPValue"])
    table["LaggerFDR"] = def_benjamini_hochberg(table["BestLaggerPValue"])

    # 族群歸屬的「共動」允許股票與族群存在可驗證的時間位移。
    # 若只看同日相關，真正的 Leader / Lagger 反而會被誤判為低共動。
    relationship_columns = [
        "ConcurrentCorrelation",
        "BestLeadCorrelation",
        "BestLaggerCorrelation",
    ]
    pvalue_columns = {
        "ConcurrentCorrelation": "ConcurrentPValue",
        "BestLeadCorrelation": "BestLeadPValue",
        "BestLaggerCorrelation": "BestLaggerPValue",
    }
    relationship_matrix = table[relationship_columns]
    table["MembershipRelationship"] = relationship_matrix.idxmax(axis=1)
    table["MembershipCorrelation"] = relationship_matrix.max(axis=1, skipna=True)
    table["MembershipPValue"] = [
        row[pvalue_columns.get(str(row["MembershipRelationship"]), "ConcurrentPValue")]
        for _, row in table.iterrows()
    ]
    table["MembershipFDR"] = def_benjamini_hochberg(table["MembershipPValue"])

    comovement_quantile = def_dynamic_quantile(
        config.base_comovement_quantile, volatility_ratio, len(table), config
    )
    finite_concurrent = table["MembershipCorrelation"].dropna()
    comovement_cutoff = (
        float(finite_concurrent.quantile(comovement_quantile))
        if not finite_concurrent.empty
        else math.nan
    )
    table["MembershipStatus"] = np.where(
        table["MembershipCorrelation"].ge(comovement_cutoff)
        & table["MembershipFDR"].le(config.fdr_alpha),
        "PASS",
        "REVIEW_LOW_COMOVEMENT",
    )
    table["LeadershipAdvantage"] = (
        table["BestLeadCorrelation"] - table["ConcurrentCorrelation"]
    )
    table["LaggerAdvantage"] = (
        table["BestLaggerCorrelation"] - table["ConcurrentCorrelation"]
    )
    concurrent_z = np.arctanh(table["ConcurrentCorrelation"].clip(-0.999999, 0.999999))
    lead_z = np.arctanh(table["BestLeadCorrelation"].clip(-0.999999, 0.999999))
    lagger_z = np.arctanh(table["BestLaggerCorrelation"].clip(-0.999999, 0.999999))
    table["LeadershipZAdvantage"] = lead_z - concurrent_z
    table["LaggerZAdvantage"] = lagger_z - concurrent_z

    passed = table.loc[table["MembershipStatus"].eq("PASS")]
    separation = config.role_separation_z / math.sqrt(
        max(config.relation_window - 3, 1)
    )
    maximum_advantage = passed[["LeadershipZAdvantage", "LaggerZAdvantage"]].max().max()
    group_valid = (
        len(passed) >= config.min_group_members
        and math.isfinite(float(maximum_advantage))
        and float(maximum_advantage) > separation
    )
    group_validity = "VALID" if group_valid else "INVALID_NO_SIGNIFICANT_ROLE_SEPARATION"

    if not group_valid:
        table["TimingRole"] = "UNRESOLVED"
    else:
        leadership_quantile = def_dynamic_quantile(
            config.base_leadership_quantile, volatility_ratio, len(passed), config
        )
        leader_cutoff = float(passed["LeadershipZAdvantage"].quantile(leadership_quantile))
        lagger_cutoff = float(passed["LaggerZAdvantage"].quantile(leadership_quantile))

        def def_assign_role(row: pd.Series) -> str:
            if row["MembershipStatus"] != "PASS":
                return "UNRESOLVED"
            leader_significant = (
                row["LeadershipZAdvantage"] >= max(leader_cutoff, separation)
                and row["LeadFDR"] <= config.fdr_alpha
            )
            lagger_significant = (
                row["LaggerZAdvantage"] >= max(lagger_cutoff, separation)
                and row["LaggerFDR"] <= config.fdr_alpha
            )
            if leader_significant and row["LeadershipZAdvantage"] >= row["LaggerZAdvantage"]:
                return "LEADER"
            if lagger_significant:
                return "LAGGER"
            return "PEER"

        table["TimingRole"] = table.apply(def_assign_role, axis=1)

    table["GroupValidity"] = group_validity
    table["DynamicComovementQuantile"] = comovement_quantile
    table["DynamicComovementCutoff"] = comovement_cutoff
    table["RoleSeparationThreshold"] = separation
    table["VolatilityRegimeRatio"] = volatility_ratio
    return table, group_validity, comovement_cutoff


def def_classify_groups(
    stock_features: pd.DataFrame,
    ssot: pd.DataFrame,
    config: EngineConfig,
) -> pd.DataFrame:
    return_panel = stock_features.pivot(index="Date", columns="Ticker", values="LogReturn")
    tables: list[pd.DataFrame] = []

    for group_id, membership in ssot.groupby("GroupId", sort=True):
        tickers = [ticker for ticker in membership["Ticker"].unique() if ticker in return_panel]
        if len(tickers) < config.min_group_members:
            for ticker in membership["Ticker"].unique():
                tables.append(
                    pd.DataFrame(
                        [
                            {
                                "GroupId": group_id,
                                "Ticker": ticker,
                                "AsOfDate": stock_features["Date"].max(),
                                "MembershipStatus": "INSUFFICIENT_GROUP_DATA",
                                "TimingRole": "UNRESOLVED",
                                "GroupValidity": "INVALID_INSUFFICIENT_MEMBERS",
                            }
                        ]
                    )
                )
            continue
        panel = return_panel[tickers].dropna(how="all")
        relationship, _, _ = def_group_relationship_table(group_id, panel, config)
        tables.append(relationship)

    role_table = pd.concat(tables, ignore_index=True, sort=False)
    role_table = role_table.merge(
        ssot[
            [
                "L1",
                "GroupId",
                "Ticker",
                "Name",
                "Market",
                "MarketValidation",
                "Position",
                "Ownership",
                "IncludeFromSource",
                "TaxonomyVersion",
            ]
        ],
        on=["GroupId", "Ticker"],
        how="left",
        validate="one_to_one",
    )
    role_table["IndexEligible"] = (
        role_table["MembershipStatus"].eq("PASS")
        & role_table["TimingRole"].isin(["LEADER", "PEER"])
        & role_table["GroupValidity"].eq("VALID")
        & role_table["Ownership"].eq("PRIMARY")
        & role_table["IncludeFromSource"].fillna(False)
    )
    role_table["Interpretation"] = np.select(
        [
            role_table["MembershipStatus"].eq("REVIEW_LOW_COMOVEMENT"),
            role_table["TimingRole"].eq("LAGGER"),
        ],
        [
            "LOW_COMOVEMENT_SSOT_REVIEW_NOT_AUTO_DELETE",
            "TIMING_LAG_NOT_POOR_PERFORMANCE",
        ],
        default="ROLE_AND_MEMBERSHIP_SEPARATED",
    )
    return role_table.sort_values(["GroupId", "Ticker"]).reset_index(drop=True)


# =============================================================================
# def 07 GROUP INDEX / PRICE-VOLUME OBSERVATION
# =============================================================================


def def_build_group_index(
    stock_features: pd.DataFrame,
    roles: pd.DataFrame,
    config: EngineConfig,
) -> pd.DataFrame:
    outputs: list[pd.DataFrame] = []
    return_panel = stock_features.pivot(index="Date", columns="Ticker", values="SimpleReturn")

    for group_id, table in roles.groupby("GroupId", sort=True):
        tickers = [ticker for ticker in table.loc[table["IndexEligible"], "Ticker"] if ticker in return_panel]
        if len(tickers) < config.min_group_members:
            continue
        group_return = return_panel[tickers].mean(axis=1, skipna=True).dropna()
        constituent_count = return_panel[tickers].notna().sum(axis=1).reindex(group_return.index)
        if group_return.empty:
            continue
        requested_base = pd.Timestamp(config.normalized_date) if config.normalized_date else group_return.index.min()
        eligible_dates = group_return.index[group_return.index >= requested_base]
        if len(eligible_dates) == 0:
            continue
        normalized_date = eligible_dates[0]
        active = group_return.loc[group_return.index >= normalized_date].copy()
        chain = (1 + active.fillna(0)).cumprod()
        index_value = 100 * chain / chain.iloc[0]
        index_value.iloc[0] = 100.0
        outputs.append(
            pd.DataFrame(
                {
                    "Date": active.index,
                    "GroupId": group_id,
                    "GroupReturn": active.values,
                    "GroupIndex": index_value.values,
                    "ConstituentCount": constituent_count.reindex(active.index).values,
                    "NormalizedDate": normalized_date,
                    "WeightMethod": "EQUAL_WEIGHT_CHAIN_LINKED_LEADER_PEER",
                    "PriceField": "ADJUSTED_CLOSE",
                }
            )
        )
    if not outputs:
        return pd.DataFrame(
            columns=[
                "Date",
                "GroupId",
                "GroupReturn",
                "GroupIndex",
                "ConstituentCount",
                "NormalizedDate",
                "WeightMethod",
                "PriceField",
            ]
        )
    return pd.concat(outputs, ignore_index=True).sort_values(["GroupId", "Date"])


def def_price_volume_quadrant(group_return: float, volume_shock: float) -> str:
    if not math.isfinite(group_return) or not math.isfinite(volume_shock):
        return "INSUFFICIENT_DATA"
    if abs(group_return) < 1e-12 and abs(volume_shock) < 1e-12:
        return "NEUTRAL"
    direction = "UP" if group_return >= 0 else "DOWN"
    volume_state = "VOLUME_EXPANSION" if volume_shock >= 0 else "VOLUME_CONTRACTION"
    return f"{direction}_{volume_state}"


def def_build_group_observation(
    stock_features: pd.DataFrame,
    ssot: pd.DataFrame,
    roles: pd.DataFrame,
    group_index: pd.DataFrame,
) -> pd.DataFrame:
    membership = ssot[["GroupId", "Ticker"]].drop_duplicates()
    joined = stock_features.merge(membership, on="Ticker", how="inner", validate="many_to_many")
    status = roles[["GroupId", "Ticker", "MembershipStatus"]]
    joined = joined.merge(status, on=["GroupId", "Ticker"], how="left", validate="many_to_one")
    joined = joined.loc[joined["MembershipStatus"].eq("PASS")]
    if joined.empty:
        return pd.DataFrame()

    group = (
        joined.groupby(["Date", "GroupId"], as_index=False)
        .agg(
            ObservedMemberCount=("Ticker", "nunique"),
            MedianStockReturn=("SimpleReturn", "median"),
            PositiveBreadth=("SimpleReturn", lambda values: float((values > 0).mean())),
            TotalVolume=("Volume", lambda values: values.sum(min_count=1)),
            TotalTurnover=("TurnoverEffective", lambda values: values.sum(min_count=1)),
            TotalNonDayTradeTurnover=(
                "NonDayTradeTurnover", lambda values: values.sum(min_count=1)
            ),
            MeanVolumeShockZ=("VolumeShockZ", "mean"),
            MeanTurnoverShockZ=("TurnoverShockZ", "mean"),
            MeanRealizedVolatility20D=("RealizedVolatility20D", "mean"),
            MeanReturnVolumeCorrelation=("ReturnVolumeCorrelation", "mean"),
            MeanAmihudIlliquidity=("AmihudIlliquidity", "mean"),
        )
    )
    group = group.merge(
        group_index[["Date", "GroupId", "GroupReturn", "GroupIndex", "NormalizedDate"]],
        on=["Date", "GroupId"],
        how="left",
        validate="one_to_one",
    )
    group["PriceVolumeQuadrant"] = [
        def_price_volume_quadrant(ret, shock)
        for ret, shock in zip(group["GroupReturn"], group["MeanVolumeShockZ"], strict=False)
    ]
    group["VolatilityState"] = np.where(
        group["MeanRealizedVolatility20D"]
        >= group.groupby("Date")["MeanRealizedVolatility20D"].transform("median"),
        "HIGH_RELATIVE_VOLATILITY",
        "LOW_RELATIVE_VOLATILITY",
    )
    return group.sort_values(["GroupId", "Date"]).reset_index(drop=True)


# =============================================================================
# def 08 PURGED WALK-FORWARD VALIDATION
# =============================================================================


def def_walk_forward_validate(
    stock_features: pd.DataFrame,
    ssot: pd.DataFrame,
    config: EngineConfig,
) -> pd.DataFrame:
    return_panel = stock_features.pivot(index="Date", columns="Ticker", values="LogReturn")
    results: list[dict[str, object]] = []

    for group_id, membership in ssot.groupby("GroupId", sort=True):
        tickers = [ticker for ticker in membership["Ticker"].unique() if ticker in return_panel]
        if len(tickers) < config.min_group_members:
            continue
        panel = return_panel[tickers].dropna(how="all")
        if len(panel) < config.walk_forward_train_days + config.walk_forward_test_days + 1:
            continue

        for train_end in range(
            config.walk_forward_train_days,
            len(panel) - config.walk_forward_test_days - 1,
            config.walk_forward_step_days,
        ):
            purge_days = max(config.lead_lags)
            train_full = panel.iloc[:train_end]
            train = train_full.iloc[:-purge_days] if len(train_full) > purge_days else train_full.iloc[0:0]
            test = panel.iloc[train_end : train_end + config.walk_forward_test_days + 1]
            if len(train) < config.min_observations:
                continue
            group_train = train.median(axis=1, skipna=True)
            membership_scores: dict[str, float] = {}
            leadership_scores: dict[str, float] = {}

            for ticker in tickers:
                peer_group_train = train.drop(columns=ticker).median(axis=1, skipna=True)
                concurrent, _ = def_safe_correlation(train[ticker], peer_group_train)
                best_lead = -np.inf
                best_lagger = -np.inf
                for lag in config.lead_lags:
                    lead, _ = def_safe_correlation(
                        train[ticker].shift(lag), peer_group_train
                    )
                    lagger, _ = def_safe_correlation(
                        train[ticker], peer_group_train.shift(lag)
                    )
                    if math.isfinite(lead):
                        best_lead = max(best_lead, lead)
                    if math.isfinite(lagger):
                        best_lagger = max(best_lagger, lagger)
                valid_relationships = [
                    value
                    for value in (concurrent, best_lead, best_lagger)
                    if math.isfinite(value)
                ]
                membership_scores[ticker] = max(valid_relationships) if valid_relationships else math.nan
                leadership_scores[ticker] = best_lead - concurrent if math.isfinite(concurrent) else math.nan

            membership_series = pd.Series(membership_scores).dropna()
            leadership_series = pd.Series(leadership_scores).dropna()
            if len(membership_series) < config.min_group_members or leadership_series.empty:
                continue
            volatility_ratio = def_latest_volatility_ratio(group_train, config.volatility_window)
            membership_quantile = def_dynamic_quantile(
                config.base_comovement_quantile,
                volatility_ratio,
                len(membership_series),
                config,
            )
            membership_cutoff = membership_series.quantile(membership_quantile)
            passed = membership_series.loc[membership_series.ge(membership_cutoff)].index
            leadership_quantile = def_dynamic_quantile(
                config.base_leadership_quantile,
                volatility_ratio,
                len(passed),
                config,
            )
            leader_cutoff = leadership_series.reindex(passed).quantile(
                leadership_quantile
            )
            leaders = leadership_series.reindex(passed).loc[
                leadership_series.reindex(passed).ge(leader_cutoff)
            ].index.tolist()
            peers = [ticker for ticker in passed if ticker not in leaders]
            if not leaders or not peers:
                continue

            leader_predictor = test[leaders].mean(axis=1, skipna=True).iloc[:-1]
            group_target = test[tickers].median(axis=1, skipna=True).shift(-1).iloc[:-1]
            peer_return = test[peers].mean(axis=1, skipna=True).iloc[:-1]
            aligned = pd.concat(
                [leader_predictor, group_target, peer_return], axis=1, keys=["Leader", "Target", "Peer"]
            ).dropna()
            if len(aligned) < 5:
                continue
            directional_accuracy = float(
                (np.sign(aligned["Leader"]) == np.sign(aligned["Target"])).mean()
            )
            information_coefficient = float(aligned["Leader"].corr(aligned["Target"]))
            results.append(
                {
                    "GroupId": group_id,
                    "TrainEnd": train.index.max(),
                    "TestStart": test.index.min(),
                    "TestEnd": test.index.max(),
                    "PurgeDays": purge_days,
                    "LeaderCount": len(leaders),
                    "PeerCount": len(peers),
                    "Observations": len(aligned),
                    "DirectionalAccuracy": directional_accuracy,
                    "InformationCoefficient": information_coefficient,
                    "LeaderMinusPeerMeanReturn": float(
                        (aligned["Leader"] - aligned["Peer"]).mean()
                    ),
                    "ValidationMethod": "PURGED_EXPANDING_WALK_FORWARD_NO_LOOKAHEAD",
                }
            )
    return pd.DataFrame(results)


# =============================================================================
# def 09 S01–S12 VALIDATION GATES
# =============================================================================


def def_validation_row(gate: str, status: str, findings: int, detail: str) -> dict[str, object]:
    return {"Gate": gate, "Status": status, "Findings": int(findings), "Detail": detail}


def def_run_validation(
    ssot: pd.DataFrame,
    prices: pd.DataFrame,
    stock_features: pd.DataFrame,
    roles: pd.DataFrame,
    group_index: pd.DataFrame,
    synthetic_mode: bool,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    rows.append(def_validation_row("S01_SCHEMA", "PASS", 0, "Required SSOT and price fields resolved"))

    price_duplicates = int(prices.duplicated(["Date", "Ticker"]).sum())
    rows.append(
        def_validation_row(
            "S02_PRICE_PRIMARY_KEY",
            "PASS" if price_duplicates == 0 else "FAIL",
            price_duplicates,
            "Date+Ticker must be unique",
        )
    )
    invalid_adjusted = int(prices["Adj_Close"].isna().sum())
    rows.append(
        def_validation_row(
            "S03_ADJUSTED_CLOSE",
            "PASS" if invalid_adjusted == 0 else "HOLD",
            invalid_adjusted,
            "Raw Close is never used as an automatic replacement",
        )
    )
    volume_missing = int(prices["Volume"].isna().sum())
    rows.append(
        def_validation_row(
            "S04_VOLUME_NO_FORWARD_FILL",
            "PASS" if volume_missing == 0 else "HOLD",
            volume_missing,
            "Missing Volume remains Null and is excluded from volume indicators",
        )
    )
    ssot_duplicates = int(ssot.duplicated(["GroupId", "Ticker"]).sum())
    rows.append(
        def_validation_row(
            "S05_SSOT_PRIMARY_KEY",
            "PASS" if ssot_duplicates == 0 else "FAIL",
            ssot_duplicates,
            "GroupId+Ticker must be unique",
        )
    )
    primary_errors = int(
        ssot.groupby("Ticker")["Ownership"]
        .apply(lambda values: int(values.eq("PRIMARY").sum()))
        .ne(1)
        .sum()
    )
    rows.append(
        def_validation_row(
            "S06_PRIMARY_OWNERSHIP",
            "PASS" if primary_errors == 0 else "FAIL",
            primary_errors,
            "Exactly one PRIMARY group per ticker",
        )
    )
    market_pending = int(ssot["MarketValidation"].eq("PENDING").sum())
    rows.append(
        def_validation_row(
            "S07_MARKET_VERIFICATION",
            "PASS" if market_pending == 0 else "HOLD",
            market_pending,
            "PENDING rows require TWSE/TPEX verification before production lock",
        )
    )
    bad_lagger = int(
        (
            roles["TimingRole"].eq("LAGGER")
            & roles["MembershipStatus"].ne("PASS")
        ).sum()
    )
    rows.append(
        def_validation_row(
            "S08_ROLE_MEMBERSHIP_SEPARATION",
            "PASS" if bad_lagger == 0 else "FAIL",
            bad_lagger,
            "Low co-movement cannot be relabeled as LAGGER",
        )
    )
    future_columns = [column for column in stock_features.columns if "future" in column.lower()]
    rows.append(
        def_validation_row(
            "S09_NO_LOOKAHEAD_FEATURES",
            "PASS" if not future_columns else "FAIL",
            len(future_columns),
            "Operational features use current and historical observations only",
        )
    )
    base_errors = 0
    if not group_index.empty:
        bases = group_index.sort_values("Date").groupby("GroupId", as_index=False).first()
        base_errors = int((bases["GroupIndex"].sub(100).abs() > 1e-9).sum())
    rows.append(
        def_validation_row(
            "S10_GROUP_INDEX_BASE",
            "PASS" if base_errors == 0 else "FAIL",
            base_errors,
            "Each emitted group index starts at 100 on its NormalizedDate",
        )
    )
    missing_groups = int(ssot["GroupId"].nunique() - group_index["GroupId"].nunique()) if not group_index.empty else int(ssot["GroupId"].nunique())
    rows.append(
        def_validation_row(
            "S11_GROUP_READINESS",
            "PASS" if missing_groups == 0 else "HOLD",
            missing_groups,
            "Groups without significant role separation remain INVALID and do not emit production index",
        )
    )
    rows.append(
        def_validation_row(
            "S12_SYNTHETIC_DATA_BOUNDARY",
            "HOLD" if synthetic_mode else "PASS",
            1 if synthetic_mode else 0,
            "Synthetic data is allowed only inside --self-test",
        )
    )
    return pd.DataFrame(rows)


# =============================================================================
# def 10 OUTPUT / CHECKPOINT / MANIFEST
# =============================================================================


def def_prepare_output_frame(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    for column in output.columns:
        if pd.api.types.is_datetime64_any_dtype(output[column]):
            output[column] = output[column].dt.strftime(DATE_OUTPUT_FORMAT)
    return output


def def_atomic_write_csv(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding=CSV_ENCODING, newline="", delete=False, dir=path.parent
    ) as stream:
        temp_path = Path(stream.name)
        def_prepare_output_frame(frame).to_csv(stream, index=False)
    os.replace(temp_path, path)


def def_atomic_write_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(path.name + ".tmp")
    try:
        frame.to_parquet(temp_path, index=False, compression=PARQUET_COMPRESSION, engine="pyarrow")
    except ImportError as exc:
        raise RuntimeError("pyarrow is required for governed Parquet output") from exc
    os.replace(temp_path, path)


def def_write_dual_outputs(result: EngineResult, config: EngineConfig) -> dict[str, dict[str, str]]:
    datasets = {
        "stock_price_volume_features": result.stock_features,
        "group_role_classification": result.role_classification,
        "group_index": result.group_index,
        "group_price_volume_observation": result.group_observation,
        "walk_forward_validation": result.walk_forward_validation,
        "validation_gates": result.validation_gates,
    }
    outputs: dict[str, dict[str, str]] = {}
    for name, frame in datasets.items():
        parquet_path = config.output_root / "parquet" / f"{name}.parquet"
        csv_path = config.output_root / "csv" / f"{name}.csv"
        def_atomic_write_parquet(frame, parquet_path)
        def_atomic_write_csv(frame, csv_path)
        outputs[name] = {
            "parquet": str(parquet_path),
            "parquet_sha256": def_sha256(parquet_path),
            "csv": str(csv_path),
            "csv_sha256": def_sha256(csv_path),
        }
    return outputs


def def_write_manifest(manifest: dict[str, object], output_root: Path) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    path = output_root / "VIA_TW_Group_PriceVolume_manifest.json"
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, default=def_json_safe),
        encoding="utf-8",
    )
    os.replace(temporary, path)
    return path


# =============================================================================
# def 11 ENGINE ORCHESTRATION
# =============================================================================


def def_run_from_frames(
    prices: pd.DataFrame,
    ssot: pd.DataFrame,
    config: EngineConfig,
    synthetic_mode: bool = False,
) -> EngineResult:
    def_validate_config(config)
    stock_features = def_compute_stock_features(prices, config)
    roles = def_classify_groups(stock_features, ssot, config)
    group_index = def_build_group_index(stock_features, roles, config)
    group_observation = def_build_group_observation(stock_features, ssot, roles, group_index)
    walk_forward = def_walk_forward_validate(stock_features, ssot, config)
    gates = def_run_validation(
        ssot, prices, stock_features, roles, group_index, synthetic_mode=synthetic_mode
    )
    gate = "FAIL" if gates["Status"].eq("FAIL").any() else "HOLD" if gates["Status"].eq("HOLD").any() else "PASS"
    manifest: dict[str, object] = {
        "engine_id": ENGINE_ID,
        "engine_version": ENGINE_VERSION,
        "taxonomy_version": TAXONOMY_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "gate": gate,
        "synthetic_mode": synthetic_mode,
        "config": asdict(config),
        "ssot_summary": def_ssot_summary(ssot),
        "row_counts": {
            "stock_features": len(stock_features),
            "role_classification": len(roles),
            "group_index": len(group_index),
            "group_observation": len(group_observation),
            "walk_forward_validation": len(walk_forward),
        },
    }
    result = EngineResult(
        stock_features=stock_features,
        role_classification=roles,
        group_index=group_index,
        group_observation=group_observation,
        walk_forward_validation=walk_forward,
        validation_gates=gates,
        manifest=manifest,
    )
    if config.strict and gate != "PASS":
        raise RuntimeError(f"Strict governance gate is {gate}; outputs were not written")
    if config.write_outputs:
        outputs = def_write_dual_outputs(result, config)
        result.manifest["outputs"] = outputs
        manifest_path = def_write_manifest(result.manifest, config.output_root)
        result.manifest["manifest_path"] = str(manifest_path)
    return result


def def_run_engine(config: EngineConfig) -> EngineResult:
    def_validate_config(config)
    ssot = def_load_group_ssot(config.group_ssot_path)
    prices = def_load_price_data(ssot, config)
    return def_run_from_frames(prices, ssot, config, synthetic_mode=False)


# =============================================================================
# def 12 DETERMINISTIC SELF-TEST — 不進正式輸出
# =============================================================================


def def_make_synthetic_inputs(config: EngineConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(20260819)
    dates = pd.bdate_range("2024-01-02", periods=280)
    records: list[dict[str, object]] = []
    memberships: list[dict[str, object]] = []

    for group_number, group_id in enumerate(("T1 SYNTHETIC AI", "T2 SYNTHETIC SHIPPING"), start=1):
        latent = rng.normal(0, 0.012 + group_number * 0.001, len(dates) + 2)
        ticker_specs = (
            (f"9{group_number}01.TW", "LEADER", latent[2:]),
            (f"9{group_number}02.TW", "PEER", latent[1:-1]),
            (f"9{group_number}03.TW", "PEER", latent[1:-1] + rng.normal(0, 0.002, len(dates))),
            (f"9{group_number}06.TW", "PEER", latent[1:-1] + rng.normal(0, 0.0015, len(dates))),
            (f"9{group_number}04.TW", "LAGGER", latent[:-2]),
            (f"9{group_number}05.TW", "LOW_COMOVEMENT", rng.normal(0, 0.018, len(dates))),
        )
        for ticker, expected_role, returns in ticker_specs:
            close = 100 * np.exp(np.cumsum(returns))
            volume = np.round(
                1_000_000
                * np.exp(2.5 * np.abs(returns) + rng.normal(0, 0.12, len(dates)))
            )
            for index, date in enumerate(dates):
                records.append(
                    {
                        "Date": date,
                        "Ticker": ticker,
                        "TickerBase": def_ticker_base(ticker),
                        "Adj_Open": close[index] * (1 - returns[index] * 0.25),
                        "Adj_High": close[index] * (1 + abs(returns[index]) * 0.55 + 0.001),
                        "Adj_Low": close[index] * (1 - abs(returns[index]) * 0.55 - 0.001),
                        "Adj_Close": close[index],
                        "Volume": volume[index],
                        "Turnover": close[index] * volume[index],
                        "DayTradeTurnover": close[index] * volume[index] * 0.18,
                        "MarketCap": close[index] * 100_000_000,
                        "PriceSource": "ADJUSTED_CLOSE",
                        "TurnoverEstimated": False,
                        "TurnoverEffective": close[index] * volume[index],
                        "NonDayTradeTurnover": close[index] * volume[index] * 0.82,
                    }
                )
            memberships.append(
                {
                    "L1": "T SYNTHETIC",
                    "GroupId": group_id,
                    "Ticker": ticker,
                    "TickerBase": def_ticker_base(ticker),
                    "Name": ticker,
                    "Market": "上市",
                    "MarketValidation": "LOCKED",
                    "Position": "CORE" if expected_role != "LOW_COMOVEMENT" else "WATCH",
                    "Ownership": "PRIMARY",
                    "IncludeFromSource": True,
                    "SourceRole": expected_role,
                    "SourceSize": None,
                    "Source": "SELF_TEST_ONLY",
                    "TaxonomyVersion": TAXONOMY_VERSION,
                }
            )
    return pd.DataFrame(records), pd.DataFrame(memberships)


def def_self_test(verbose: bool = False) -> EngineResult:
    config = EngineConfig(
        relation_window=60,
        min_observations=60,
        min_group_members=3,
        walk_forward_train_days=120,
        walk_forward_test_days=20,
        walk_forward_step_days=20,
        strict=False,
        write_outputs=False,
    )
    prices, ssot = def_make_synthetic_inputs(config)
    result = def_run_from_frames(prices, ssot, config, synthetic_mode=True)

    assert not result.stock_features.duplicated(["Date", "Ticker"]).any()
    assert {"VolumeShockZ", "RealizedVolatility20D", "ReturnVolumeCorrelation"}.issubset(
        result.stock_features.columns
    )
    assert (
        result.role_classification.loc[
            result.role_classification["MembershipStatus"].ne("PASS"), "TimingRole"
        ]
        != "LAGGER"
    ).all()
    assert not result.group_index.empty
    bases = result.group_index.sort_values("Date").groupby("GroupId").first()["GroupIndex"]
    assert np.allclose(bases, 100.0)
    assert result.validation_gates["Status"].ne("FAIL").all()
    if verbose:
        LOGGER.info("Self-test role counts: %s", result.role_classification["TimingRole"].value_counts().to_dict())
    return result


# =============================================================================
# def 13 CLI
# =============================================================================


def def_build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="VIA 台股族群分類及量價波動觀察引擎"
    )
    parser.add_argument("--price-path", type=Path, default=DEFAULT_PRICE_PATH)
    parser.add_argument("--group-ssot", type=Path, default=DEFAULT_GROUP_SSOT_PATH)
    parser.add_argument("--ticker-list", type=Path, default=DEFAULT_TICKER_LIST_PATH)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    parser.add_argument("--end-date", default=DEFAULT_END_DATE)
    parser.add_argument("--normalized-date", default=DEFAULT_NORMALIZED_DATE)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--use-yfinance-fallback", action="store_true")
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser


def def_main(argv: Sequence[str] | None = None) -> int:
    arguments = def_build_parser().parse_args(argv)
    def_configure_logging(arguments.verbose)
    if arguments.self_test:
        result = def_self_test(verbose=arguments.verbose)
    else:
        config = EngineConfig(
            price_path=arguments.price_path,
            group_ssot_path=arguments.group_ssot,
            ticker_list_path=arguments.ticker_list,
            output_root=arguments.output_root,
            start_date=arguments.start_date,
            end_date=arguments.end_date,
            normalized_date=arguments.normalized_date,
            strict=arguments.strict,
            use_yfinance_fallback=arguments.use_yfinance_fallback,
            write_outputs=not arguments.no_write,
        )
        result = def_run_engine(config)
    print(json.dumps(result.manifest, ensure_ascii=False, indent=2, default=def_json_safe))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(def_main())
    except Exception as error:
        LOGGER.exception("Engine failed: %s", error)
        raise SystemExit(1) from error
