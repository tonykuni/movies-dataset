#!/usr/bin/env python3
"""VIA TA-Lib OneEngine v1.0.0.

單一正典技術指標引擎：
DataSource -> Normalizer -> ActivityBasis -> TA-Lib Abstract API -> Registry -> Exporter

本檔不實作指標公式，也不以 pandas-ta 代替 TA-Lib。所有函數、輸入、輸出與
預設參數皆由目前安裝的 TA-Lib Abstract API 動態發現，升級 TA-Lib 後不必再
手動補函數清單。
"""

from __future__ import annotations

# ============================================================================
# 0. 所有可調參數（SSOT；外部 JSON 可覆寫）
# ============================================================================

ENGINE_ID = "VDF_ENG_TALIB_ONE"
ENGINE_NAME = "VIA TA-Lib OneEngine"
ENGINE_VERSION = "1.0.0"
CONNECTION_MANIFEST_VERSION = "VIA-VDF-VAP-CONNECTION-MANIFEST/1.0"
FEATURE_MANIFEST_VERSION = "VIA-TALIB-FEATURE-MANIFEST/1.0"
DEFAULT_PERIODS = [5, 10, 20, 60, 120, 240]

DEFAULT_SPECIAL_PRESETS: dict[str, list[dict[str, object]]] = {
    "RSI": [{"timeperiod": 14}],
    "MACD": [{"fastperiod": 12, "slowperiod": 26, "signalperiod": 9}],
    "MACDEXT": [{
        "fastperiod": 12, "fastmatype": 0,
        "slowperiod": 26, "slowmatype": 0,
        "signalperiod": 9, "signalmatype": 0,
    }],
    "MACDFIX": [{"signalperiod": 9}],
    "BBANDS": [{"timeperiod": 20, "nbdevup": 2.0, "nbdevdn": 2.0, "matype": 0}],
    "ATR": [{"timeperiod": 14}],
    "NATR": [{"timeperiod": 14}],
    "ADX": [{"timeperiod": 14}],
    "ADXR": [{"timeperiod": 14}],
    "DX": [{"timeperiod": 14}],
    "CCI": [{"timeperiod": 14}],
    "CMO": [{"timeperiod": 14}],
    "MFI": [{"timeperiod": 14}],
    "MINUS_DI": [{"timeperiod": 14}],
    "MINUS_DM": [{"timeperiod": 14}],
    "PLUS_DI": [{"timeperiod": 14}],
    "PLUS_DM": [{"timeperiod": 14}],
    "WILLR": [{"timeperiod": 14}],
    "AROON": [{"timeperiod": 14}],
    "AROONOSC": [{"timeperiod": 14}],
    "STOCH": [{
        "fastk_period": 9, "slowk_period": 3, "slowk_matype": 0,
        "slowd_period": 3, "slowd_matype": 0,
    }],
    "STOCHF": [{"fastk_period": 9, "fastd_period": 3, "fastd_matype": 0}],
    "STOCHRSI": [{
        "timeperiod": 14, "fastk_period": 5, "fastd_period": 3, "fastd_matype": 0,
    }],
    "ULTOSC": [{"timeperiod1": 7, "timeperiod2": 14, "timeperiod3": 28}],
    "APO": [{"fastperiod": 12, "slowperiod": 26, "matype": 0}],
    "PPO": [{"fastperiod": 12, "slowperiod": 26, "matype": 0}],
    "ADOSC": [{"fastperiod": 3, "slowperiod": 10}],
    "SAR": [{"acceleration": 0.02, "maximum": 0.2}],
}

DEFAULT_COLUMN_ALIASES: dict[str, list[str]] = {
    "date": ["date", "obs_date", "datetime", "timestamp", "trade_date", "trading_date", "日期", "交易日期"],
    "ticker": ["ticker", "symbol", "stock_id", "stock_no", "security_id", "證券代號", "股票代碼", "代號"],
    "adj_open": ["adj_open", "adj open", "adjusted_open", "adjusted open", "調整後開盤價", "還原開盤價"],
    "adj_high": ["adj_high", "adj high", "adjusted_high", "adjusted high", "調整後最高價", "還原最高價"],
    "adj_low": ["adj_low", "adj low", "adjusted_low", "adjusted low", "調整後最低價", "還原最低價"],
    "adj_close": ["adj_close", "adj", "adj close", "adjusted_close", "adjusted close", "調整後收盤價", "還原收盤價"],
    "benchmark_close": [
        "benchmark_close", "benchmark_adj_close", "market_close", "market_adj_close",
        "index_close", "index_adj_close", "基準收盤價", "大盤收盤價",
    ],
    "raw_open": ["open", "raw_open", "opening_price", "開盤價"],
    "raw_high": ["high", "raw_high", "highest_price", "最高價"],
    "raw_low": ["low", "raw_low", "lowest_price", "最低價"],
    "raw_close": ["close", "raw_close", "closing_price", "收盤價"],
    "volume_raw": ["volume", "raw_volume", "trade_volume", "trading_volume", "成交股數", "成交量"],
    "turnover_raw": ["turnover", "traded_value", "trade_value", "trading_value", "amount", "成交金額", "成交值"],
    "daytrade_volume": [
        "daytrade_volume", "day_trade_volume", "day_trading_volume", "day_trade_shares",
        "當沖成交股數", "當沖成交量", "現股當沖成交股數",
    ],
    "daytrade_turnover": [
        "daytrade_turnover", "day_trade_turnover", "day_trading_value", "day_trade_value",
        "當沖成交金額", "當沖成交值", "現股當沖成交金額",
    ],
}

GROUP_ZH = {
    "Cycle Indicators": "週期",
    "Math Operators": "數學運算",
    "Math Transform": "數學轉換",
    "Momentum Indicators": "動量",
    "Overlap Studies": "趨勢／重疊",
    "Pattern Recognition": "K線型態",
    "Price Transform": "價格轉換",
    "Statistic Functions": "統計",
    "Volatility Indicators": "波動",
    "Volume Indicators": "量能",
}

DEFAULT_SIGNAL_RULES: dict[str, dict[str, object]] = {
    "RSI": {"output": "real", "upper": 70.0, "lower": 30.0, "upper_state": "超買", "lower_state": "超賣"},
    "STOCH": {"output": "slowk", "upper": 80.0, "lower": 20.0, "upper_state": "超買", "lower_state": "超賣"},
    "STOCHF": {"output": "fastk", "upper": 85.0, "lower": 15.0, "upper_state": "極度超買", "lower_state": "極度超賣"},
    "STOCHRSI": {"output": "fastk", "upper": 80.0, "lower": 20.0, "upper_state": "超買", "lower_state": "超賣"},
    "WILLR": {"output": "real", "upper": -20.0, "lower": -80.0, "upper_state": "超買", "lower_state": "超賣"},
    "CCI": {"output": "real", "upper": 100.0, "lower": -100.0, "upper_state": "超買警戒", "lower_state": "超賣警戒"},
    "CMO": {"output": "real", "upper": 50.0, "lower": -50.0, "upper_state": "強勢", "lower_state": "弱勢"},
    "MFI": {"output": "real", "upper": 80.0, "lower": 20.0, "upper_state": "超買", "lower_state": "超賣"},
    "NATR": {"output": "real", "upper": 2.0, "lower": 0.5, "upper_state": "高波動", "lower_state": "低波動"},
    "ADX": {"output": "real", "upper": 40.0, "lower": 25.0, "upper_state": "強趨勢", "lower_state": "無明確趨勢", "middle_state": "趨勢明確"},
}

DEFAULT_CONFIG: dict[str, object] = {
    "engine": {
        "id": ENGINE_ID,
        "name": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "connection_manifest": CONNECTION_MANIFEST_VERSION,
        "read_only_source": True,
    },
    "source": {
        "type": "auto",
        "path": None,
        "format": "auto",
        "database_type": "auto",
        "database_path": None,
        "database_url": None,
        "table": None,
        "query": None,
        "csv_encodings": ["utf-8-sig", "utf-8", "cp950", "big5"],
        "directory_patterns": ["*.parquet", "*.csv", "*.json", "*.jsonl", "*.feather"],
    },
    "data": {
        "asset_class": "security",
        "require_adjusted_prices": True,
        "derive_adjusted_ohlc_from_adj_close": True,
        "adjustment_factor_zero_policy": "null",
        "price_missing_policy": "ffill_by_ticker",
        "volume_missing_policy": "zero_no_carry",
        "duplicate_policy": "last",
        "default_ticker": "__SINGLE__",
        "column_aliases": DEFAULT_COLUMN_ALIASES,
    },
    "activity": {
        "display_mode": "raw",
        "available_modes": ["raw", "ex_daytrade"],
        "indicator_volume_bases": ["raw", "ex_daytrade"],
        "missing_daytrade_column_policy": "null_and_warn",
        "missing_daytrade_cell_policy": "zero",
        "negative_net_policy": "clip_zero_and_warn",
    },
    "indicators": {
        "include_groups": ["ALL"],
        "include_functions": [],
        "exclude_functions": [],
        "generic_periods": DEFAULT_PERIODS,
        "special_presets": DEFAULT_SPECIAL_PRESETS,
        "function_overrides": {},
        "single_price_input": "close",
        "input_overrides": {},
        "calculation_dtype": "float64",
        "feature_prefix": "ta_",
        "on_function_error": "record_and_continue",
        "include_candlestick_patterns": True,
        "include_math_operators": True,
        "include_math_transform": True,
    },
    "signals": {
        "enabled": True,
        "rules": DEFAULT_SIGNAL_RULES,
        "include_macd_cross": True,
        "include_bbands_touch": True,
        "include_candlestick_events": True,
        "disclaimer": "技術指標訊號僅為量化狀態，不構成投資建議",
    },
    "quality": {
        "minimum_rows": 2,
        "required_function_coverage": 1.0,
        "fail_on_zero_functions": True,
        "fail_on_partial_coverage": False,
        "reject_infinite_input": True,
    },
    "output": {
        "directory": "output",
        "formats": ["parquet", "csv"],
        "parquet_name": "VIA_TALib_Features_Parquet",
        "csv_name": "VIA_TALib_Features_CSV",
        "manifest_name": "VIA_TALib_Feature_Manifest.json",
        "catalog_name": "VIA_TALib_Parameter_Catalog.json",
        "registry_name": "VIA_TALib_Feature_Registry.csv",
        "signals_name": "VIA_TALib_Latest_Signals.csv",
        "vap_catalog_name": "VIA_TALib_VAP_Catalog.json",
        "csv_encoding": "utf-8-sig",
        "csv_date_format": "%Y/%m/%d",
        "compression": "zstd",
        "include_file_extensions": False,
        "incremental_merge": True,
        "database_type": None,
        "database_path": None,
        "database_url": None,
        "database_table": "talib_features",
        "database_if_exists": "append_deduplicate",
    },
}


# ============================================================================
# 1. 基礎工具與設定
# ============================================================================

import argparse
import copy
import hashlib
import json
import math
import os
import re
import sqlite3
import sys
import tempfile
import traceback
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd


def utc_now_text() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def deep_merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(dict(base))
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(merged.get(key), Mapping):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    config = copy.deepcopy(DEFAULT_CONFIG)
    if config_path:
        path = Path(config_path).expanduser().resolve()
        with path.open("r", encoding="utf-8-sig") as handle:
            supplied = json.load(handle)
        if not isinstance(supplied, Mapping):
            raise ValueError("設定檔最外層必須是 JSON object")
        config = deep_merge(config, supplied)
    validate_config(config)
    return config


def validate_config(config: Mapping[str, Any]) -> None:
    periods = config["indicators"]["generic_periods"]
    if not periods or any(not isinstance(x, int) or x < 2 for x in periods):
        raise ValueError("indicators.generic_periods 必須是大於等於 2 的整數陣列")
    if len(periods) != len(set(periods)):
        raise ValueError("indicators.generic_periods 不可重複")
    display_mode = config["activity"]["display_mode"]
    if display_mode not in {"raw", "ex_daytrade"}:
        raise ValueError("activity.display_mode 僅接受 raw 或 ex_daytrade")
    volume_bases = config["activity"]["indicator_volume_bases"]
    if any(x not in {"raw", "ex_daytrade"} for x in volume_bases):
        raise ValueError("indicator_volume_bases 僅接受 raw、ex_daytrade")
    if config["data"]["require_adjusted_prices"] is not True:
        raise ValueError("本引擎為 ADJUSTED_PRICE_ONLY；require_adjusted_prices 不可關閉")
    if not isinstance(config["indicators"].get("single_price_input"), str):
        raise ValueError("indicators.single_price_input 必須是欄位名稱字串")
    if not isinstance(config["indicators"].get("input_overrides"), Mapping):
        raise ValueError("indicators.input_overrides 必須是 JSON object")
    database_mode = str(config["output"].get("database_if_exists") or "replace").lower()
    if database_mode not in {"replace", "append", "append_deduplicate"}:
        raise ValueError("output.database_if_exists 僅接受 replace、append、append_deduplicate")


def json_default(value: Any) -> Any:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return None if math.isnan(float(value)) else float(value)
    if isinstance(value, (np.ndarray, pd.Series, pd.Index)):
        return value.tolist()
    if isinstance(value, (datetime, pd.Timestamp)):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, OrderedDict):
        return dict(value)
    raise TypeError(f"無法 JSON 序列化：{type(value).__name__}")


def atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding=encoding, newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def atomic_write_json(path: Path, value: Any) -> None:
    atomic_write_text(path, json.dumps(value, ensure_ascii=False, indent=2, default=json_default) + "\n")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalize_name(value: object) -> str:
    text = str(value).strip().lower()
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", text)


def flatten_columns(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    if isinstance(result.columns, pd.MultiIndex):
        result.columns = ["__".join(str(part) for part in col if str(part) not in {"", "None"}) for col in result.columns]
    else:
        result.columns = [str(col) for col in result.columns]
    if result.index.name and str(result.index.name) not in result.columns:
        result = result.reset_index()
    return result


def resolve_column(columns: Sequence[str], aliases: Sequence[str]) -> str | None:
    normalized = {normalize_name(column): column for column in columns}
    for alias in aliases:
        found = normalized.get(normalize_name(alias))
        if found is not None:
            return found
    return None


def quote_identifier(identifier: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.$]*", identifier):
        raise ValueError(f"不安全的資料表識別字：{identifier!r}")
    return ".".join(f'"{part}"' for part in identifier.split("."))


def validate_read_query(query: str) -> str:
    stripped = query.strip().rstrip(";").strip()
    if not re.match(r"^(select|with)\b", stripped, flags=re.IGNORECASE):
        raise ValueError("唯讀橋接只允許 SELECT 或 WITH 查詢")
    forbidden = r"\b(insert|update|delete|drop|alter|create|attach|detach|copy|pragma|vacuum|truncate|replace)\b"
    if re.search(forbidden, stripped, flags=re.IGNORECASE):
        raise ValueError("查詢包含非唯讀關鍵字")
    return stripped


# ============================================================================
# 2. VDF／檔案／資料庫唯讀橋接
# ============================================================================

def detect_file_format(path: Path, explicit: str = "auto") -> str:
    if explicit and explicit.lower() != "auto":
        return explicit.lower()
    suffix = path.suffix.lower().lstrip(".")
    if suffix in {"parquet", "pq", "csv", "tsv", "json", "jsonl", "ndjson", "feather"}:
        return {"pq": "parquet", "ndjson": "jsonl"}.get(suffix, suffix)
    with path.open("rb") as handle:
        head = handle.read(8)
    if head[:4] == b"PAR1":
        return "parquet"
    if head[:6] == b"ARROW1":
        return "feather"
    text_head = head.lstrip()
    if text_head.startswith((b"{", b"[")):
        return "json"
    return "csv"


def read_csv_with_fallback(path: Path, encodings: Sequence[str], separator: str = ",") -> pd.DataFrame:
    last_error: Exception | None = None
    for encoding in encodings:
        try:
            return pd.read_csv(path, encoding=encoding, sep=separator, low_memory=False)
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error:
        raise last_error
    raise ValueError("未提供 CSV 編碼")


def read_one_file(path: str | Path, config: Mapping[str, Any]) -> pd.DataFrame:
    source_path = Path(path).expanduser().resolve()
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    source_config = config["source"]
    file_format = detect_file_format(source_path, str(source_config.get("format", "auto")))
    if file_format == "parquet":
        return pd.read_parquet(source_path)
    if file_format == "feather":
        return pd.read_feather(source_path)
    if file_format in {"csv", "tsv"}:
        separator = "\t" if file_format == "tsv" else ","
        return read_csv_with_fallback(source_path, source_config["csv_encodings"], separator)
    if file_format == "jsonl":
        return pd.read_json(source_path, lines=True)
    if file_format == "json":
        try:
            return pd.read_json(source_path)
        except ValueError:
            with source_path.open("r", encoding="utf-8-sig") as handle:
                payload = json.load(handle)
            if isinstance(payload, Mapping):
                for key in ("data", "rows", "records", "items"):
                    if isinstance(payload.get(key), list):
                        return pd.DataFrame(payload[key])
            return pd.DataFrame(payload)
    raise ValueError(f"不支援的資料格式：{file_format}")


def read_file_source(path: str | Path, config: Mapping[str, Any]) -> pd.DataFrame:
    source_path = Path(path).expanduser().resolve()
    if source_path.is_file():
        return read_one_file(source_path, config)
    if not source_path.is_dir():
        raise FileNotFoundError(source_path)
    files: list[Path] = []
    for pattern in config["source"]["directory_patterns"]:
        files.extend(source_path.glob(pattern))
    files = sorted({file.resolve() for file in files if file.is_file()})
    if not files:
        raise FileNotFoundError(f"資料夾內找不到可讀資料：{source_path}")
    frames = [read_one_file(file, config).assign(__source_file=str(file)) for file in files]
    return pd.concat(frames, ignore_index=True, sort=False)


def infer_database_type(config: Mapping[str, Any]) -> str:
    source = config["source"]
    explicit = str(source.get("database_type") or "auto").lower()
    if explicit != "auto":
        return explicit
    url = source.get("database_url")
    if url:
        return "sqlalchemy"
    path = Path(str(source.get("database_path") or ""))
    if path.suffix.lower() in {".sqlite", ".sqlite3", ".db"}:
        return "sqlite"
    return "duckdb"


def read_database_source(config: Mapping[str, Any]) -> pd.DataFrame:
    source = config["source"]
    database_type = infer_database_type(config)
    table = source.get("table")
    query = source.get("query")
    if query:
        sql = validate_read_query(str(query))
    elif table:
        sql = f"SELECT * FROM {quote_identifier(str(table))}"
    else:
        raise ValueError("資料庫來源必須設定 source.table 或 source.query")

    if database_type == "sqlite":
        database_path = Path(str(source.get("database_path"))).expanduser().resolve()
        uri = f"file:{database_path.as_posix()}?mode=ro"
        with sqlite3.connect(uri, uri=True) as connection:
            return pd.read_sql_query(sql, connection)
    if database_type == "duckdb":
        try:
            import duckdb  # type: ignore
        except ImportError as exc:
            raise RuntimeError("讀取 DuckDB 需要安裝 duckdb") from exc
        database_path = Path(str(source.get("database_path"))).expanduser().resolve()
        connection = duckdb.connect(str(database_path), read_only=True)
        try:
            return connection.execute(sql).fetchdf()
        finally:
            connection.close()
    if database_type == "sqlalchemy":
        try:
            import sqlalchemy as sa  # type: ignore
        except ImportError as exc:
            raise RuntimeError("讀取 PostgreSQL/MySQL 等資料庫需要安裝 SQLAlchemy 與對應 driver") from exc
        database_url = source.get("database_url")
        if not database_url:
            raise ValueError("SQLAlchemy 來源需要 source.database_url")
        engine = sa.create_engine(str(database_url))
        try:
            with engine.connect() as connection:
                return pd.read_sql_query(sa.text(sql), connection)
        finally:
            engine.dispose()
    raise ValueError(f"不支援的 database_type：{database_type}")


def read_source(config: Mapping[str, Any]) -> pd.DataFrame:
    source = config["source"]
    source_type = str(source.get("type") or "auto").lower()
    if source_type == "auto":
        source_type = "database" if source.get("database_path") or source.get("database_url") else "file"
    if source_type in {"file", "directory"}:
        if not source.get("path"):
            raise ValueError("檔案來源需要 source.path")
        return read_file_source(str(source["path"]), config)
    if source_type == "database":
        return read_database_source(config)
    raise ValueError(f"不支援的 source.type：{source_type}")


# ============================================================================
# 3. 調整後價格與台股原始／扣當沖量值
# ============================================================================

def build_column_resolution(frame: pd.DataFrame, config: Mapping[str, Any]) -> dict[str, str | None]:
    aliases = config["data"]["column_aliases"]
    return {canonical: resolve_column(list(frame.columns), names) for canonical, names in aliases.items()}


def numeric_series(frame: pd.DataFrame, column: str | None) -> pd.Series:
    if column is None:
        return pd.Series(np.nan, index=frame.index, dtype="float64")
    text = frame[column]
    if not pd.api.types.is_numeric_dtype(text):
        text = text.astype(str).str.replace(",", "", regex=False).str.replace("--", "", regex=False)
    return pd.to_numeric(text, errors="coerce").astype("float64")


def derive_adjusted_prices(
    frame: pd.DataFrame,
    resolution: Mapping[str, str | None],
    config: Mapping[str, Any],
) -> tuple[pd.DataFrame, dict[str, str], list[dict[str, Any]]]:
    result = frame.copy()
    warnings: list[dict[str, Any]] = []
    provenance: dict[str, str] = {}
    direct = {field: numeric_series(result, resolution.get(field)) for field in ("adj_open", "adj_high", "adj_low", "adj_close")}
    raw = {field: numeric_series(result, resolution.get(field)) for field in ("raw_open", "raw_high", "raw_low", "raw_close")}

    if direct["adj_close"].isna().all():
        raise ValueError("ADJUSTED_PRICE_ONLY：找不到 Adj Close，拒絕以 raw Close 代替")

    denominator = raw["raw_close"].replace(0, np.nan)
    factor = (direct["adj_close"] / denominator).replace([np.inf, -np.inf], np.nan)
    for adjusted_field, raw_field in (
        ("adj_open", "raw_open"),
        ("adj_high", "raw_high"),
        ("adj_low", "raw_low"),
        ("adj_close", "raw_close"),
    ):
        series = direct[adjusted_field]
        direct_column = resolution.get(adjusted_field)
        if not series.isna().all():
            provenance[adjusted_field] = f"direct:{direct_column}"
        elif config["data"]["derive_adjusted_ohlc_from_adj_close"] and not raw[raw_field].isna().all():
            series = raw[raw_field] * factor
            provenance[adjusted_field] = f"derived:{raw_field}*(adj_close/raw_close)"
            warnings.append({"code": "ADJ_DERIVED", "field": adjusted_field, "message": "以 Adj Close 調整因子還原"})
        else:
            raise ValueError(f"ADJUSTED_PRICE_ONLY：缺少 {adjusted_field}，且無法由 Adj Close 調整因子還原")
        result[adjusted_field] = series

    result["open"] = result["adj_open"]
    result["high"] = result["adj_high"]
    result["low"] = result["adj_low"]
    result["close"] = result["adj_close"]
    return result, provenance, warnings


def apply_activity_bases(
    frame: pd.DataFrame,
    resolution: Mapping[str, str | None],
    config: Mapping[str, Any],
) -> tuple[pd.DataFrame, dict[str, bool], list[dict[str, Any]]]:
    result = frame.copy()
    settings = config["activity"]
    warnings: list[dict[str, Any]] = []

    raw_volume_present = resolution.get("volume_raw") is not None
    raw_turnover_present = resolution.get("turnover_raw") is not None
    daytrade_volume_present = resolution.get("daytrade_volume") is not None
    daytrade_turnover_present = resolution.get("daytrade_turnover") is not None

    result["volume_raw"] = numeric_series(result, resolution.get("volume_raw"))
    result["turnover_raw"] = numeric_series(result, resolution.get("turnover_raw"))
    result["daytrade_volume"] = numeric_series(result, resolution.get("daytrade_volume"))
    result["daytrade_turnover"] = numeric_series(result, resolution.get("daytrade_turnover"))

    if raw_volume_present and config["data"]["volume_missing_policy"] == "zero_no_carry":
        result["volume_raw"] = result["volume_raw"].fillna(0.0)
    if raw_turnover_present and config["data"]["volume_missing_policy"] == "zero_no_carry":
        result["turnover_raw"] = result["turnover_raw"].fillna(0.0)

    if daytrade_volume_present:
        daytrade_volume = result["daytrade_volume"]
        if settings["missing_daytrade_cell_policy"] == "zero":
            daytrade_volume = daytrade_volume.fillna(0.0)
        result["volume_ex_daytrade"] = result["volume_raw"] - daytrade_volume
    else:
        result["volume_ex_daytrade"] = np.nan
        warnings.append({"code": "NO_DAYTRADE_VOLUME", "field": "volume_ex_daytrade", "message": "未提供當沖成交量；不以原始量冒充扣當沖量"})

    if daytrade_turnover_present:
        daytrade_turnover = result["daytrade_turnover"]
        if settings["missing_daytrade_cell_policy"] == "zero":
            daytrade_turnover = daytrade_turnover.fillna(0.0)
        result["turnover_ex_daytrade"] = result["turnover_raw"] - daytrade_turnover
    else:
        result["turnover_ex_daytrade"] = np.nan
        warnings.append({"code": "NO_DAYTRADE_TURNOVER", "field": "turnover_ex_daytrade", "message": "未提供當沖成交值；不以原始值冒充扣當沖值"})

    for field in ("volume_ex_daytrade", "turnover_ex_daytrade"):
        negatives = int((result[field] < 0).sum())
        if negatives:
            warnings.append({"code": "NEGATIVE_NET_ACTIVITY", "field": field, "rows": negatives, "message": "當沖值大於原始值"})
            if settings["negative_net_policy"] == "clip_zero_and_warn":
                result[field] = result[field].clip(lower=0.0)
            elif settings["negative_net_policy"] == "raise":
                raise ValueError(f"{field} 出現 {negatives} 筆負值")

    mode = settings["display_mode"]
    result["volume"] = result[f"volume_{mode}"]
    result["turnover"] = result[f"turnover_{mode}"]
    availability = {
        "volume_raw": raw_volume_present,
        "turnover_raw": raw_turnover_present,
        "volume_ex_daytrade": raw_volume_present and daytrade_volume_present,
        "turnover_ex_daytrade": raw_turnover_present and daytrade_turnover_present,
    }
    return result, availability, warnings


def normalize_market_data(frame: pd.DataFrame, config: Mapping[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        raise ValueError("輸入資料為空")
    result = flatten_columns(frame)
    resolution = build_column_resolution(result, config)
    warnings: list[dict[str, Any]] = []

    date_column = resolution.get("date")
    if date_column:
        result["date"] = pd.to_datetime(result[date_column], errors="coerce")
    elif isinstance(result.index, pd.DatetimeIndex):
        result["date"] = pd.to_datetime(result.index, errors="coerce")
    else:
        raise ValueError("找不到日期欄位")
    invalid_dates = int(result["date"].isna().sum())
    if invalid_dates:
        warnings.append({"code": "INVALID_DATE", "rows": invalid_dates, "message": "無法解析的日期列已移除"})
        result = result.loc[result["date"].notna()].copy()

    ticker_column = resolution.get("ticker")
    if ticker_column:
        result["ticker"] = result[ticker_column].astype(str).str.strip()
    else:
        result["ticker"] = str(config["data"]["default_ticker"])

    result, price_provenance, price_warnings = derive_adjusted_prices(result, resolution, config)
    warnings.extend(price_warnings)
    result, activity_availability, activity_warnings = apply_activity_bases(result, resolution, config)
    warnings.extend(activity_warnings)
    for canonical, source_column in resolution.items():
        if canonical in {"benchmark_close"} and source_column is not None:
            result[canonical] = numeric_series(result, source_column)

    result = result.replace([np.inf, -np.inf], np.nan)
    result = result.sort_values(["ticker", "date"], kind="stable")
    duplicate_count = int(result.duplicated(["ticker", "date"], keep=False).sum())
    if duplicate_count:
        policy = str(config["data"]["duplicate_policy"])
        keep = "last" if policy == "last" else "first"
        result = result.drop_duplicates(["ticker", "date"], keep=keep)
        warnings.append({"code": "DUPLICATE_GRAIN", "rows": duplicate_count, "message": f"Date+Ticker 去重，保留 {keep}"})

    price_fields = ["open", "high", "low", "close", "adj_open", "adj_high", "adj_low", "adj_close"]
    if config["data"]["price_missing_policy"] == "ffill_by_ticker":
        result[price_fields] = result.groupby("ticker", sort=False)[price_fields].ffill()

    if config["quality"]["reject_infinite_input"]:
        numeric = result.select_dtypes(include=[np.number])
        if np.isinf(numeric.to_numpy(dtype="float64", na_value=np.nan)).any():
            raise ValueError("輸入仍含無限值")
    if len(result) < int(config["quality"]["minimum_rows"]):
        raise ValueError(f"有效資料不足 {config['quality']['minimum_rows']} 列")

    canonical = [
        "date", "ticker", "adj_open", "adj_high", "adj_low", "adj_close",
        "open", "high", "low", "close", "volume_raw", "volume_ex_daytrade",
        "turnover_raw", "turnover_ex_daytrade", "daytrade_volume", "daytrade_turnover",
        "volume", "turnover", "benchmark_close",
    ]
    canonical = [column for column in canonical if column in result.columns]
    other = [column for column in result.columns if column not in canonical]
    result = result[canonical + other].reset_index(drop=True)
    metadata = {
        "grain": ["date", "ticker"],
        "rows": len(result),
        "tickers": int(result["ticker"].nunique()),
        "date_min": result["date"].min(),
        "date_max": result["date"].max(),
        "price_policy": "ADJUSTED_PRICE_ONLY",
        "price_provenance": price_provenance,
        "activity_availability": activity_availability,
        "column_resolution": resolution,
        "warnings": warnings,
    }
    return result, metadata


# ============================================================================
# 4. TA-Lib 全函數動態目錄與參數規劃
# ============================================================================

def load_talib() -> tuple[Any, Any]:
    try:
        import talib  # type: ignore
        from talib import abstract  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "找不到 TA-Lib。VIA 採 TA-Lib-only，不會改用其他指標公式；"
            "請在 via_vdf 環境安裝 requirements.txt。"
        ) from exc
    return talib, abstract


def to_plain_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): json_default(item) if isinstance(item, (np.generic, np.ndarray)) else item for key, item in value.items()}
    return {}


def flatten_input_names(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, str):
        return [value]
    if isinstance(value, Mapping):
        for item in value.values():
            found.extend(flatten_input_names(item))
        return found
    if isinstance(value, Sequence):
        for item in value:
            found.extend(flatten_input_names(item))
    return found


def resolve_function_input_names(
    function_name: str,
    input_names: Any,
    config: Mapping[str, Any],
) -> Any:
    """Resolve configurable Abstract API input bindings without changing formulas."""
    if not isinstance(input_names, Mapping):
        return copy.deepcopy(input_names)
    resolved = OrderedDict((str(key), copy.deepcopy(value)) for key, value in input_names.items())
    settings = config["indicators"]
    if "price" in resolved:
        resolved["price"] = str(settings["single_price_input"])
    override = settings.get("input_overrides", {}).get(function_name.upper(), {})
    unknown = sorted(set(override) - set(resolved))
    if unknown:
        raise ValueError(f"{function_name} input_overrides 含未知輸入：{', '.join(unknown)}")
    for input_name, source_name in override.items():
        resolved[str(input_name)] = copy.deepcopy(source_name)
    return resolved


def function_group_map(talib_module: Any) -> dict[str, str]:
    result: dict[str, str] = {}
    for group, functions in talib_module.get_function_groups().items():
        for function_name in functions:
            result[str(function_name).upper()] = str(group)
    return result


def is_function_included(name: str, group: str, config: Mapping[str, Any]) -> bool:
    settings = config["indicators"]
    include_functions = {str(x).upper() for x in settings["include_functions"]}
    exclude_functions = {str(x).upper() for x in settings["exclude_functions"]}
    include_groups = {str(x).upper() for x in settings["include_groups"]}
    upper_name = name.upper()
    if upper_name in exclude_functions:
        return False
    if include_functions and upper_name not in include_functions:
        return False
    if "ALL" not in include_groups and group.upper() not in include_groups:
        return False
    if group == "Pattern Recognition" and not settings["include_candlestick_patterns"]:
        return False
    if group == "Math Operators" and not settings["include_math_operators"]:
        return False
    if group == "Math Transform" and not settings["include_math_transform"]:
        return False
    override = settings["function_overrides"].get(upper_name, {})
    return override.get("enabled", True) is not False


def merge_parameters(defaults: Mapping[str, Any], supplied: Mapping[str, Any]) -> dict[str, Any]:
    result = copy.deepcopy(dict(defaults))
    result.update(copy.deepcopy(dict(supplied)))
    return result


def plan_parameter_variants(name: str, defaults: Mapping[str, Any], config: Mapping[str, Any]) -> list[dict[str, Any]]:
    upper_name = name.upper()
    settings = config["indicators"]
    override = settings["function_overrides"].get(upper_name, {})
    if override.get("variants"):
        return [merge_parameters(defaults, variant) for variant in override["variants"]]
    if override.get("parameters"):
        return [merge_parameters(defaults, override["parameters"])]
    special = settings["special_presets"].get(upper_name)
    if special:
        return [merge_parameters(defaults, variant) for variant in special]
    if upper_name == "MAVP":
        variants: list[dict[str, Any]] = []
        for period in settings["generic_periods"]:
            variant = merge_parameters(defaults, {"minperiod": 2, "maxperiod": max(30, int(period))})
            variant["__periods_value"] = int(period)
            variants.append(variant)
        return variants
    if "timeperiod" in defaults:
        return [merge_parameters(defaults, {"timeperiod": int(period)}) for period in settings["generic_periods"]]
    return [copy.deepcopy(dict(defaults))]


def parameter_label(parameters: Mapping[str, Any]) -> str:
    if not parameters:
        return "default"
    short_names = {
        "timeperiod": "tp", "fastperiod": "fast", "slowperiod": "slow",
        "signalperiod": "signal", "fastk_period": "fk", "fastd_period": "fd",
        "slowk_period": "sk", "slowd_period": "sd", "timeperiod1": "tp1",
        "timeperiod2": "tp2", "timeperiod3": "tp3", "minperiod": "min",
        "maxperiod": "max", "__periods_value": "periods", "acceleration": "acc",
        "maximum": "max", "nbdevup": "up", "nbdevdn": "dn", "matype": "ma",
    }
    useful = []
    for key, value in parameters.items():
        if key.endswith("matype") and value == 0:
            continue
        label = short_names.get(key, key)
        value_text = str(value).replace(".", "p").replace("-", "m")
        useful.append(f"{label}{value_text}")
    text = "_".join(useful) or "default"
    return re.sub(r"[^A-Za-z0-9_]+", "", text).lower()


def build_function_catalog(talib_module: Any, abstract_module: Any, config: Mapping[str, Any]) -> list[dict[str, Any]]:
    group_map = function_group_map(talib_module)
    catalog: list[dict[str, Any]] = []
    for function_name in sorted(str(name).upper() for name in talib_module.get_functions()):
        function = abstract_module.Function(function_name)
        group = group_map.get(function_name, str(getattr(function, "info", {}).get("group", "Unknown")))
        defaults = to_plain_mapping(getattr(function, "parameters", {}))
        default_input_names = getattr(function, "input_names", getattr(function, "info", {}).get("input_names", {}))
        input_names = resolve_function_input_names(function_name, default_input_names, config)
        output_names = list(getattr(function, "output_names", getattr(function, "info", {}).get("output_names", ["real"])))
        included = is_function_included(function_name, group, config)
        variants = plan_parameter_variants(function_name, defaults, config) if included else []
        catalog.append({
            "function": function_name,
            "group": group,
            "included": included,
            "input_names": input_names,
            "input_fields": flatten_input_names(input_names),
            "talib_default_input_names": default_input_names,
            "output_names": output_names,
            "talib_defaults": defaults,
            "resolved_variants": [
                {"label": parameter_label(variant), "parameters": variant} for variant in variants
            ],
        })
    return catalog


# ============================================================================
# 5. TA-Lib 計算核心（單一正典）
# ============================================================================

def uses_volume(catalog_entry: Mapping[str, Any]) -> bool:
    return any("volume" in str(field).lower() for field in catalog_entry.get("input_fields", []))


def prepare_talib_inputs(group: pd.DataFrame, volume_basis: str, periods_value: int | None = None) -> dict[str, np.ndarray]:
    inputs = {
        "open": group["open"].to_numpy(dtype="float64", copy=True),
        "high": group["high"].to_numpy(dtype="float64", copy=True),
        "low": group["low"].to_numpy(dtype="float64", copy=True),
        "close": group["close"].to_numpy(dtype="float64", copy=True),
        "volume": group[f"volume_{volume_basis}"].to_numpy(dtype="float64", copy=True),
    }
    if periods_value is not None:
        inputs["periods"] = np.full(len(group), float(periods_value), dtype="float64")
    for column in group.columns:
        if column in inputs or column in {"date", "ticker"}:
            continue
        converted = pd.to_numeric(group[column], errors="coerce")
        if converted.notna().any():
            inputs[str(column)] = converted.to_numpy(dtype="float64", copy=True)
    return inputs


def output_arrays(result: Any, output_names: Sequence[str], expected_length: int) -> list[tuple[str, np.ndarray]]:
    if isinstance(result, pd.DataFrame):
        arrays = [(str(column), result[column].to_numpy()) for column in result.columns]
    elif isinstance(result, pd.Series):
        arrays = [(str(output_names[0] if output_names else result.name or "real"), result.to_numpy())]
    elif isinstance(result, tuple):
        arrays = [(str(output_names[index] if index < len(output_names) else f"out{index}"), np.asarray(value)) for index, value in enumerate(result)]
    elif isinstance(result, list) and result and not np.isscalar(result[0]):
        arrays = [(str(output_names[index] if index < len(output_names) else f"out{index}"), np.asarray(value)) for index, value in enumerate(result)]
    else:
        arrays = [(str(output_names[0] if output_names else "real"), np.asarray(result))]
    normalized: list[tuple[str, np.ndarray]] = []
    for name, array in arrays:
        flat = np.asarray(array).reshape(-1)
        if len(flat) != expected_length:
            raise ValueError(f"輸出 {name} 長度 {len(flat)}，預期 {expected_length}")
        normalized.append((name, flat))
    return normalized


def feature_column_name(
    prefix: str,
    function_name: str,
    variant_label: str,
    output_name: str,
    volume_basis: str | None,
) -> str:
    parts = [prefix.rstrip("_"), function_name.lower(), variant_label.lower(), normalize_name(output_name) or "real"]
    if volume_basis:
        parts.append(f"vol_{volume_basis}")
    return "__".join(parts)


def calculate_one_ticker(
    ticker_frame: pd.DataFrame,
    catalog: Sequence[Mapping[str, Any]],
    abstract_module: Any,
    config: Mapping[str, Any],
) -> tuple[pd.DataFrame, list[dict[str, Any]], list[dict[str, Any]]]:
    features = pd.DataFrame(index=ticker_frame.index)
    registry: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    settings = config["indicators"]
    volume_settings = config["activity"]

    for entry in catalog:
        if not entry["included"]:
            continue
        function_name = str(entry["function"])
        function = abstract_module.Function(function_name)
        function.input_names = copy.deepcopy(entry["input_names"])
        volume_dependent = uses_volume(entry)
        volume_bases = list(volume_settings["indicator_volume_bases"]) if volume_dependent else [str(volume_settings["display_mode"])]
        for variant in entry["resolved_variants"]:
            variant_label = str(variant["label"])
            planned_parameters = copy.deepcopy(dict(variant["parameters"]))
            periods_value = planned_parameters.pop("__periods_value", None)
            for volume_basis in volume_bases:
                volume_column = f"volume_{volume_basis}"
                if volume_dependent and (volume_column not in ticker_frame or ticker_frame[volume_column].isna().all()):
                    errors.append({
                        "ticker": str(ticker_frame["ticker"].iloc[0]),
                        "function": function_name,
                        "variant": variant_label,
                        "volume_basis": volume_basis,
                        "error_type": "MissingActivityBasis",
                        "message": f"{volume_column} 不可用；未退回 raw",
                    })
                    continue
                try:
                    inputs = prepare_talib_inputs(ticker_frame, volume_basis, periods_value)
                    result = function(inputs, **planned_parameters)
                    arrays = output_arrays(result, entry["output_names"], len(ticker_frame))
                    for output_name, values in arrays:
                        column = feature_column_name(
                            str(settings["feature_prefix"]), function_name, variant_label,
                            output_name, volume_basis if volume_dependent else None,
                        )
                        features[column] = values
                        registry.append({
                            "feature": column,
                            "function": function_name,
                            "group": entry["group"],
                            "variant": variant_label,
                            "output": output_name,
                            "parameters": json.dumps(planned_parameters, ensure_ascii=False, sort_keys=True, default=json_default),
                            "inputs": json.dumps(entry["input_fields"], ensure_ascii=False),
                            "price_basis": "ADJUSTED_OHLC",
                            "volume_basis": volume_basis if volume_dependent else "N/A",
                            "engine_id": ENGINE_ID,
                            "engine_version": ENGINE_VERSION,
                        })
                except Exception as exc:
                    errors.append({
                        "ticker": str(ticker_frame["ticker"].iloc[0]),
                        "function": function_name,
                        "variant": variant_label,
                        "volume_basis": volume_basis if volume_dependent else "N/A",
                        "error_type": type(exc).__name__,
                        "message": str(exc),
                    })
                    if settings["on_function_error"] == "raise":
                        raise
    return features, registry, errors


def calculate_all_indicators(
    normalized: pd.DataFrame,
    config: Mapping[str, Any],
    talib_module: Any | None = None,
    abstract_module: Any | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, list[dict[str, Any]], list[dict[str, Any]]]:
    if talib_module is None or abstract_module is None:
        talib_module, abstract_module = load_talib()
    catalog = build_function_catalog(talib_module, abstract_module, config)
    output_parts: list[pd.DataFrame] = []
    all_registry: list[dict[str, Any]] = []
    all_errors: list[dict[str, Any]] = []
    base_columns = [
        "date", "ticker", "adj_open", "adj_high", "adj_low", "adj_close",
        "volume_raw", "volume_ex_daytrade", "turnover_raw", "turnover_ex_daytrade",
        "daytrade_volume", "daytrade_turnover",
    ]
    for _, ticker_frame in normalized.groupby("ticker", sort=False):
        ticker_frame = ticker_frame.sort_values("date", kind="stable").copy()
        feature_frame, registry, errors = calculate_one_ticker(
            ticker_frame, catalog, abstract_module, config,
        )
        part = pd.concat([ticker_frame[base_columns], feature_frame], axis=1)
        output_parts.append(part)
        all_registry.extend(registry)
        all_errors.extend(errors)
    output = pd.concat(output_parts, ignore_index=True, sort=False)
    registry_frame = pd.DataFrame(all_registry).drop_duplicates(subset=["feature"], keep="last") if all_registry else pd.DataFrame()
    return output, registry_frame, all_errors, catalog


# ============================================================================
# 6. 附件既有 SSOT 訊號層與 VAP Catalog 橋接
# ============================================================================

def registry_features(
    registry: pd.DataFrame,
    function_name: str,
    output_name: str | None = None,
) -> pd.DataFrame:
    if registry.empty:
        return registry.copy()
    selected = registry.loc[registry["function"].astype(str).str.upper() == function_name.upper()].copy()
    if output_name is not None:
        selected = selected.loc[selected["output"].astype(str).str.lower() == output_name.lower()]
    return selected


def last_finite(series: pd.Series) -> tuple[float | None, float | None]:
    numeric = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if numeric.empty:
        return None, None
    current = float(numeric.iloc[-1])
    previous = float(numeric.iloc[-2]) if len(numeric) >= 2 else None
    return current, previous


def threshold_state(value: float, rule: Mapping[str, Any]) -> str:
    upper = float(rule["upper"])
    lower = float(rule["lower"])
    if "middle_state" in rule:
        if value >= upper:
            return str(rule["upper_state"])
        if value >= lower:
            return str(rule["middle_state"])
        return str(rule["lower_state"])
    if value >= upper:
        return str(rule["upper_state"])
    if value <= lower:
        return str(rule["lower_state"])
    return "中性"


def generate_latest_signals(features: pd.DataFrame, registry: pd.DataFrame, config: Mapping[str, Any]) -> pd.DataFrame:
    columns = [
        "date", "ticker", "function", "variant", "feature", "volume_basis",
        "state", "value", "previous_value", "basis", "disclaimer",
    ]
    if not config["signals"]["enabled"] or features.empty or registry.empty:
        return pd.DataFrame(columns=columns)
    rows: list[dict[str, Any]] = []
    disclaimer = str(config["signals"]["disclaimer"])
    for ticker, ticker_frame in features.groupby("ticker", sort=False):
        ticker_frame = ticker_frame.sort_values("date", kind="stable")
        latest_date = ticker_frame["date"].max()
        for function_name, rule in config["signals"]["rules"].items():
            matches = registry_features(registry, function_name, str(rule["output"]))
            for _, meta in matches.iterrows():
                feature = str(meta["feature"])
                if feature not in ticker_frame:
                    continue
                value, previous = last_finite(ticker_frame[feature])
                if value is None:
                    continue
                rows.append({
                    "date": latest_date,
                    "ticker": ticker,
                    "function": function_name,
                    "variant": meta["variant"],
                    "feature": feature,
                    "volume_basis": meta["volume_basis"],
                    "state": threshold_state(value, rule),
                    "value": value,
                    "previous_value": previous,
                    "basis": json.dumps({"upper": rule["upper"], "lower": rule["lower"]}, ensure_ascii=False),
                    "disclaimer": disclaimer,
                })

        if config["signals"]["include_macd_cross"]:
            macd_registry = registry_features(registry, "MACD")
            for variant, variant_rows in macd_registry.groupby("variant", sort=False):
                mapping = {str(row["output"]).lower(): str(row["feature"]) for _, row in variant_rows.iterrows()}
                dif_col = mapping.get("macd")
                signal_col = mapping.get("macdsignal")
                hist_col = mapping.get("macdhist")
                if not dif_col or not signal_col or dif_col not in ticker_frame or signal_col not in ticker_frame:
                    continue
                dif, prev_dif = last_finite(ticker_frame[dif_col])
                signal, prev_signal = last_finite(ticker_frame[signal_col])
                hist, prev_hist = last_finite(ticker_frame[hist_col]) if hist_col and hist_col in ticker_frame else (None, None)
                if dif is None or signal is None:
                    continue
                if prev_dif is not None and prev_signal is not None and prev_dif <= prev_signal < dif:
                    state = "黃金交叉"
                elif prev_dif is not None and prev_signal is not None and prev_dif >= prev_signal > dif:
                    state = "死亡交叉"
                else:
                    state = "多頭" if dif > signal else "空頭"
                rows.append({
                    "date": latest_date, "ticker": ticker, "function": "MACD", "variant": variant,
                    "feature": hist_col or dif_col, "volume_basis": "N/A", "state": state,
                    "value": hist if hist is not None else dif - signal,
                    "previous_value": prev_hist,
                    "basis": "DIF/Signal 交叉與柱狀體", "disclaimer": disclaimer,
                })

        if config["signals"]["include_bbands_touch"]:
            bb_registry = registry_features(registry, "BBANDS")
            for variant, variant_rows in bb_registry.groupby("variant", sort=False):
                mapping = {str(row["output"]).lower(): str(row["feature"]) for _, row in variant_rows.iterrows()}
                upper_col = mapping.get("upperband")
                lower_col = mapping.get("lowerband")
                if not upper_col or not lower_col or upper_col not in ticker_frame or lower_col not in ticker_frame:
                    continue
                close, _ = last_finite(ticker_frame["adj_close"])
                upper, _ = last_finite(ticker_frame[upper_col])
                lower, _ = last_finite(ticker_frame[lower_col])
                if close is None or upper is None or lower is None:
                    continue
                state = "觸及上軌" if close >= upper else "觸及下軌" if close <= lower else "通道內"
                rows.append({
                    "date": latest_date, "ticker": ticker, "function": "BBANDS", "variant": variant,
                    "feature": upper_col, "volume_basis": "N/A", "state": state,
                    "value": close, "previous_value": None,
                    "basis": json.dumps({"upper": upper, "lower": lower}, ensure_ascii=False), "disclaimer": disclaimer,
                })

        if config["signals"]["include_candlestick_events"]:
            candle_registry = registry.loc[registry["function"].astype(str).str.upper().str.startswith("CDL")]
            for _, meta in candle_registry.iterrows():
                feature = str(meta["feature"])
                if feature not in ticker_frame:
                    continue
                value, previous = last_finite(ticker_frame[feature])
                if value is None or value == 0:
                    continue
                rows.append({
                    "date": latest_date, "ticker": ticker, "function": meta["function"],
                    "variant": meta["variant"], "feature": feature, "volume_basis": "N/A",
                    "state": "看漲型態" if value > 0 else "看跌型態", "value": value,
                    "previous_value": previous, "basis": "TA-Lib CDL 原始整數輸出", "disclaimer": disclaimer,
                })
    return pd.DataFrame(rows, columns=columns)


def build_vap_catalog(
    registry: pd.DataFrame,
    output_files: Sequence[Mapping[str, Any]],
    config: Mapping[str, Any],
) -> dict[str, Any]:
    fields: list[dict[str, Any]] = []
    for _, row in registry.iterrows():
        group = str(row["group"])
        fields.append({
            "identity": {
                "database": str(config["output"].get("database_path") or "VIA_TALib_FeatureLake"),
                "table": str(config["output"]["database_table"]),
                "field": str(row["feature"]),
                "version": ENGINE_VERSION,
            },
            "field": str(row["feature"]),
            "subject": str(row["function"]),
            "unit": "TA-Lib native output",
            "data_type": "float64",
            "role": "overlay" if group in {"Overlap Studies", "Price Transform"} else "panel",
            "aggregation": "none",
            "frequency": "source_frequency",
            "group": group,
            "group_zh": GROUP_ZH.get(group, group),
            "parameters": json.loads(str(row["parameters"])),
            "price_basis": str(row["price_basis"]),
            "volume_basis": str(row["volume_basis"]),
        })
    return {
        "schema": CONNECTION_MANIFEST_VERSION,
        "producer": {"id": ENGINE_ID, "version": ENGINE_VERSION},
        "consumer": "VAP-ENG-3050-001 AutoPlot Render Engine",
        "mode": "READ_ONLY",
        "grain": ["date", "ticker"],
        "price_policy": "ADJUSTED_PRICE_ONLY",
        "activity_toggle": {
            "default": config["activity"]["display_mode"],
            "options": [
                {"id": "raw", "volume_field": "volume_raw", "turnover_field": "turnover_raw", "label": "原始成交量值"},
                {"id": "ex_daytrade", "volume_field": "volume_ex_daytrade", "turnover_field": "turnover_ex_daytrade", "label": "扣除當沖成交量值"},
            ],
        },
        "runtime_injection": ["window.VeritasAutoPlot.registerCatalog(table)", "vap:catalog"],
        "request_correlation": "only matching Request ID may become Updated",
        "datasets": list(output_files),
        "fields": fields,
    }


# ============================================================================
# 7. 輸出、增量合併與資料庫回寫
# ============================================================================

def output_path(output_dir: Path, name: str, file_format: str, include_extension: bool) -> Path:
    return output_dir / (f"{name}.{file_format}" if include_extension else name)


def read_existing_feature_file(path: Path, file_format: str, config: Mapping[str, Any]) -> pd.DataFrame | None:
    if not path.exists():
        return None
    local_config = copy.deepcopy(dict(config))
    local_config["source"] = copy.deepcopy(dict(config["source"]))
    local_config["source"]["format"] = file_format
    return read_one_file(path, local_config)


def merge_incremental(existing: pd.DataFrame | None, current: pd.DataFrame) -> pd.DataFrame:
    if existing is None or existing.empty:
        return current.sort_values(["ticker", "date"], kind="stable").reset_index(drop=True)
    old = existing.copy()
    old["date"] = pd.to_datetime(old["date"], errors="coerce")
    new = current.copy()
    new["date"] = pd.to_datetime(new["date"], errors="coerce")
    merged = pd.concat([old, new], ignore_index=True, sort=False)
    merged = merged.drop_duplicates(["ticker", "date"], keep="last")
    return merged.sort_values(["ticker", "date"], kind="stable").reset_index(drop=True)


def atomic_write_csv(frame: pd.DataFrame, path: Path, config: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    os.close(descriptor)
    try:
        frame.to_csv(
            temp_name,
            index=False,
            encoding=str(config["output"]["csv_encoding"]),
            date_format=str(config["output"]["csv_date_format"]),
        )
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def atomic_write_parquet(frame: pd.DataFrame, path: Path, config: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".parquet", dir=path.parent)
    os.close(descriptor)
    try:
        frame.to_parquet(temp_name, index=False, compression=str(config["output"]["compression"]))
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def write_feature_database(frame: pd.DataFrame, config: Mapping[str, Any]) -> dict[str, Any] | None:
    output = config["output"]
    database_type = output.get("database_type")
    if not database_type:
        return None
    table = str(output["database_table"])
    quoted_table = quote_identifier(table)
    result = frame.copy()
    write_mode = str(output.get("database_if_exists") or "replace").lower()
    allowed_modes = {"replace", "append", "append_deduplicate"}
    if write_mode not in allowed_modes:
        raise ValueError(f"不支援的 output.database_if_exists：{write_mode}")

    def merged_for_write(existing: pd.DataFrame | None) -> tuple[pd.DataFrame, str]:
        if write_mode == "append":
            return result, "append"
        if write_mode == "append_deduplicate":
            return merge_incremental(existing, result), "replace"
        return result, "replace"

    if database_type == "sqlite":
        if not output.get("database_path"):
            raise ValueError("SQLite 輸出需要 output.database_path")
        database_path = Path(str(output["database_path"])).expanduser().resolve()
        with sqlite3.connect(database_path) as connection:
            exists = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1", (table,)
            ).fetchone() is not None
            existing = pd.read_sql_query(f"SELECT * FROM {quoted_table}", connection) if exists and write_mode == "append_deduplicate" else None
            result_to_write, pandas_mode = merged_for_write(existing)
            result_to_write.to_sql(table, connection, if_exists=pandas_mode, index=False)
        return {"type": "sqlite", "path": str(database_path), "table": table, "mode": write_mode, "rows": len(result_to_write)}
    if database_type == "duckdb":
        try:
            import duckdb  # type: ignore
        except ImportError as exc:
            raise RuntimeError("寫入 DuckDB 需要安裝 duckdb") from exc
        if not output.get("database_path"):
            raise ValueError("DuckDB 輸出需要 output.database_path")
        database_path = Path(str(output["database_path"])).expanduser().resolve()
        connection = duckdb.connect(str(database_path))
        try:
            exists = connection.execute(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?", [table.split(".")[-1]]
            ).fetchone()[0] > 0
            existing = connection.execute(f"SELECT * FROM {quoted_table}").fetchdf() if exists and write_mode == "append_deduplicate" else None
            result_to_write, pandas_mode = merged_for_write(existing)
            connection.register("_via_talib_frame", result_to_write)
            if pandas_mode == "append" and exists:
                connection.execute(f"INSERT INTO {quoted_table} SELECT * FROM _via_talib_frame")
            else:
                connection.execute(f"CREATE OR REPLACE TABLE {quoted_table} AS SELECT * FROM _via_talib_frame")
        finally:
            connection.close()
        return {"type": "duckdb", "path": str(database_path), "table": table, "mode": write_mode, "rows": len(result_to_write)}
    if database_type == "sqlalchemy":
        try:
            import sqlalchemy as sa  # type: ignore
        except ImportError as exc:
            raise RuntimeError("寫入 SQLAlchemy 資料庫需要安裝 SQLAlchemy 與對應 driver") from exc
        if not output.get("database_url"):
            raise ValueError("SQLAlchemy 輸出需要 output.database_url")
        engine = sa.create_engine(str(output["database_url"]))
        try:
            exists = sa.inspect(engine).has_table(table)
            existing = pd.read_sql_query(sa.text(f"SELECT * FROM {quoted_table}"), engine) if exists and write_mode == "append_deduplicate" else None
            result_to_write, pandas_mode = merged_for_write(existing)
            result_to_write.to_sql(table, engine, if_exists=pandas_mode, index=False, chunksize=10_000, method="multi")
        finally:
            engine.dispose()
        return {"type": "sqlalchemy", "table": table, "mode": write_mode, "rows": len(result_to_write)}
    raise ValueError(f"不支援的 output.database_type：{database_type}")


def write_outputs(
    features: pd.DataFrame,
    registry: pd.DataFrame,
    catalog: Sequence[Mapping[str, Any]],
    errors: Sequence[Mapping[str, Any]],
    normalization: Mapping[str, Any],
    config: Mapping[str, Any],
    talib_module: Any,
) -> dict[str, Any]:
    output = config["output"]
    directory = Path(str(output["directory"])).expanduser().resolve()
    directory.mkdir(parents=True, exist_ok=True)
    include_extension = bool(output["include_file_extensions"])
    formats = [str(value).lower() for value in output["formats"]]
    preferred = "parquet" if "parquet" in formats else formats[0]
    preferred_name = output["parquet_name"] if preferred == "parquet" else output["csv_name"]
    preferred_path = output_path(directory, str(preferred_name), preferred, include_extension)

    merged = features
    if output["incremental_merge"]:
        try:
            existing = read_existing_feature_file(preferred_path, preferred, config)
        except (ImportError, ValueError, OSError):
            existing = None
        merged = merge_incremental(existing, features)

    written: list[dict[str, Any]] = []
    for file_format in formats:
        if file_format == "parquet":
            path = output_path(directory, str(output["parquet_name"]), "parquet", include_extension)
            atomic_write_parquet(merged, path, config)
        elif file_format == "csv":
            path = output_path(directory, str(output["csv_name"]), "csv", include_extension)
            atomic_write_csv(merged, path, config)
        else:
            raise ValueError(f"不支援的輸出格式：{file_format}")
        written.append({"format": file_format, "path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)})

    registry_path = directory / str(output["registry_name"])
    atomic_write_csv(registry, registry_path, config)
    catalog_path = directory / str(output["catalog_name"])
    atomic_write_json(catalog_path, list(catalog))
    signals = generate_latest_signals(merged, registry, config)
    signals_path = directory / str(output["signals_name"])
    atomic_write_csv(signals, signals_path, config)
    vap_catalog = build_vap_catalog(registry, written, config)
    vap_catalog_path = directory / str(output["vap_catalog_name"])
    atomic_write_json(vap_catalog_path, vap_catalog)
    database_result = write_feature_database(merged, config)

    discovered = {str(entry["function"]) for entry in catalog if entry["included"]}
    successful = set(registry["function"].astype(str)) if not registry.empty else set()
    failed = sorted(discovered - successful)
    coverage = len(successful) / len(discovered) if discovered else 0.0
    status = "GREEN" if coverage >= float(config["quality"]["required_function_coverage"]) else "YELLOW"
    manifest = {
        "schema": FEATURE_MANIFEST_VERSION,
        "connection_manifest": CONNECTION_MANIFEST_VERSION,
        "engine": {"id": ENGINE_ID, "name": ENGINE_NAME, "version": ENGINE_VERSION},
        "generated_at": utc_now_text(),
        "status": status,
        "source_mode": "READ_ONLY",
        "price_basis": "ADJUSTED_OHLC_ONLY",
        "activity_modes": config["activity"]["available_modes"],
        "activity_display_default": config["activity"]["display_mode"],
        "normalization": normalization,
        "talib": {
            "python_wrapper_version": getattr(talib_module, "__version__", "unknown"),
            "core_version": getattr(talib_module, "__ta_version__", "unknown"),
            "functions_discovered": len(discovered),
            "functions_successful": len(successful),
            "function_coverage": coverage,
            "failed_functions": failed,
        },
        "features": {"rows": len(merged), "columns": len(merged.columns), "registry_rows": len(registry)},
        "function_errors": list(errors),
        "outputs": written,
        "registry": {"path": str(registry_path), "sha256": sha256_file(registry_path)},
        "catalog": {"path": str(catalog_path), "sha256": sha256_file(catalog_path)},
        "signals": {"path": str(signals_path), "rows": len(signals), "sha256": sha256_file(signals_path)},
        "vap_catalog": {"path": str(vap_catalog_path), "fields": len(vap_catalog["fields"]), "sha256": sha256_file(vap_catalog_path)},
        "database_output": database_result,
    }
    manifest_path = directory / str(output["manifest_name"])
    atomic_write_json(manifest_path, manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest


# ============================================================================
# 8. 執行入口、VIA Registry 摘要與自測
# ============================================================================

def apply_cli_overrides(config: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    result = copy.deepcopy(config)
    if getattr(args, "source", None):
        result["source"].update({"type": "file", "path": args.source})
    if getattr(args, "database", None):
        result["source"].update({"type": "database", "database_path": args.database})
    if getattr(args, "database_type", None):
        result["source"]["database_type"] = args.database_type
    if getattr(args, "database_url", None):
        result["source"].update({"type": "database", "database_url": args.database_url, "database_type": "sqlalchemy"})
    if getattr(args, "table", None):
        result["source"]["table"] = args.table
    if getattr(args, "query", None):
        result["source"]["query"] = args.query
    if getattr(args, "output_dir", None):
        result["output"]["directory"] = args.output_dir
    if getattr(args, "display_mode", None):
        result["activity"]["display_mode"] = args.display_mode
    if getattr(args, "functions", None):
        result["indicators"]["include_functions"] = [item.strip().upper() for item in args.functions.split(",") if item.strip()]
    if getattr(args, "formats", None):
        result["output"]["formats"] = [item.strip().lower() for item in args.formats.split(",") if item.strip()]
    validate_config(result)
    return result


def run_engine(
    config: Mapping[str, Any],
    frame: pd.DataFrame | None = None,
    talib_module: Any | None = None,
    abstract_module: Any | None = None,
    write: bool = True,
) -> dict[str, Any]:
    started = utc_now_text()
    source_frame = frame if frame is not None else read_source(config)
    normalized, normalization = normalize_market_data(source_frame, config)
    if talib_module is None or abstract_module is None:
        talib_module, abstract_module = load_talib()
    features, registry, errors, catalog = calculate_all_indicators(
        normalized, config, talib_module, abstract_module,
    )
    discovered = {str(entry["function"]) for entry in catalog if entry["included"]}
    successful = set(registry["function"].astype(str)) if not registry.empty else set()
    if not successful and config["quality"]["fail_on_zero_functions"]:
        raise RuntimeError("沒有任何 TA-Lib 函數成功計算")
    coverage = len(successful) / len(discovered) if discovered else 0.0
    if config["quality"]["fail_on_partial_coverage"] and coverage < float(config["quality"]["required_function_coverage"]):
        raise RuntimeError(f"TA-Lib 函數覆蓋率 {coverage:.2%} 未達門檻")
    if write:
        manifest = write_outputs(features, registry, catalog, errors, normalization, config, talib_module)
    else:
        manifest = {
            "schema": FEATURE_MANIFEST_VERSION,
            "engine": {"id": ENGINE_ID, "version": ENGINE_VERSION},
            "started_at": started,
            "generated_at": utc_now_text(),
            "normalization": normalization,
            "talib": {
                "functions_discovered": len(discovered),
                "functions_successful": len(successful),
                "function_coverage": coverage,
            },
            "features": {"rows": len(features), "columns": len(features.columns)},
            "function_errors": errors,
            "feature_frame": features,
            "registry_frame": registry,
            "catalog": catalog,
        }
    return manifest


def generate_demo_frame(rows: int = 360) -> pd.DataFrame:
    rng = np.random.default_rng(20260909)
    dates = pd.bdate_range("2025-01-02", periods=rows)
    raw_close = 100 + np.cumsum(rng.normal(0.08, 1.1, rows))
    raw_open = raw_close + rng.normal(0, 0.5, rows)
    raw_high = np.maximum(raw_open, raw_close) + rng.uniform(0.1, 1.2, rows)
    raw_low = np.minimum(raw_open, raw_close) - rng.uniform(0.1, 1.2, rows)
    factor = np.where(np.arange(rows) < rows // 2, 0.8, 1.0)
    volume = rng.integers(1_000_000, 8_000_000, rows).astype(float)
    daytrade_volume = volume * rng.uniform(0.10, 0.45, rows)
    turnover = volume * raw_close
    daytrade_turnover = daytrade_volume * raw_close
    return pd.DataFrame({
        "Date": dates,
        "Ticker": "2330.TW",
        "Open": raw_open,
        "High": raw_high,
        "Low": raw_low,
        "Close": raw_close,
        "Adj Close": raw_close * factor,
        "Volume": volume,
        "Traded_Value": turnover,
        "Day_Trade_Volume": daytrade_volume,
        "Day_Trade_Value": daytrade_turnover,
    })


def self_test(config: Mapping[str, Any]) -> dict[str, Any]:
    demo = generate_demo_frame()
    result = run_engine(config, frame=demo, write=False)
    return {
        "engine": ENGINE_ID,
        "version": ENGINE_VERSION,
        "status": "PASS",
        "rows": result["features"]["rows"],
        "columns": result["features"]["columns"],
        "function_coverage": result["talib"]["function_coverage"],
        "errors": len(result["function_errors"]),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"{ENGINE_NAME} v{ENGINE_VERSION}")
    parser.add_argument("--version", action="version", version=ENGINE_VERSION)
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="讀取資料並計算 TA-Lib 全指標")
    run.add_argument("--config", help="JSON 設定檔")
    run.add_argument("--source", help="Parquet/CSV/JSON/Feather 檔或資料夾")
    run.add_argument("--database", help="DuckDB/SQLite 路徑")
    run.add_argument("--database-type", choices=["auto", "duckdb", "sqlite", "sqlalchemy"])
    run.add_argument("--database-url", help="SQLAlchemy URL；不會寫入 log")
    run.add_argument("--table", help="唯讀資料表")
    run.add_argument("--query", help="唯讀 SELECT/WITH")
    run.add_argument("--output-dir", help="輸出資料夾")
    run.add_argument("--display-mode", choices=["raw", "ex_daytrade"], help="VAP 預設顯示量值")
    run.add_argument("--functions", help="逗號分隔函數；空白表示全部")
    run.add_argument("--formats", help="例如 parquet,csv")

    validate = subparsers.add_parser("validate", help="只驗證資料與 adjusted/activity 規格")
    validate.add_argument("--config", help="JSON 設定檔")
    validate.add_argument("--source", help="資料檔或資料夾")
    validate.add_argument("--database", help="DuckDB/SQLite 路徑")
    validate.add_argument("--database-type", choices=["auto", "duckdb", "sqlite", "sqlalchemy"])
    validate.add_argument("--database-url")
    validate.add_argument("--table")
    validate.add_argument("--query")

    catalog = subparsers.add_parser("catalog", help="列出已安裝 TA-Lib 的所有函數與全部可改參數")
    catalog.add_argument("--config", help="JSON 設定檔")
    catalog.add_argument("--output", help="JSON 輸出；未指定則印至 stdout")

    defaults = subparsers.add_parser("defaults", help="印出完整 SSOT 預設設定")
    defaults.add_argument("--output", help="JSON 輸出；未指定則印至 stdout")

    test = subparsers.add_parser("self-test", help="以 360 筆合成 OHLCV 執行真實 TA-Lib")
    test.add_argument("--config", help="JSON 設定檔")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "defaults":
            text = json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2, default=json_default) + "\n"
            if args.output:
                atomic_write_text(Path(args.output).expanduser().resolve(), text)
            else:
                print(text, end="")
            return 0

        config = load_config(getattr(args, "config", None))
        config = apply_cli_overrides(config, args)
        if args.command == "validate":
            normalized, metadata = normalize_market_data(read_source(config), config)
            print(json.dumps({"status": "PASS", "rows": len(normalized), "metadata": metadata}, ensure_ascii=False, indent=2, default=json_default))
            return 0
        if args.command == "catalog":
            talib_module, abstract_module = load_talib()
            value = {
                "engine": {"id": ENGINE_ID, "version": ENGINE_VERSION},
                "talib_version": getattr(talib_module, "__version__", "unknown"),
                "generic_periods": config["indicators"]["generic_periods"],
                "special_presets": config["indicators"]["special_presets"],
                "functions": build_function_catalog(talib_module, abstract_module, config),
            }
            text = json.dumps(value, ensure_ascii=False, indent=2, default=json_default) + "\n"
            if args.output:
                atomic_write_text(Path(args.output).expanduser().resolve(), text)
            else:
                print(text, end="")
            return 0
        if args.command == "self-test":
            print(json.dumps(self_test(config), ensure_ascii=False, indent=2, default=json_default))
            return 0
        if args.command == "run":
            manifest = run_engine(config)
            print(json.dumps({
                "status": manifest["status"],
                "manifest": manifest["manifest_path"],
                "rows": manifest["features"]["rows"],
                "columns": manifest["features"]["columns"],
                "function_coverage": manifest["talib"]["function_coverage"],
            }, ensure_ascii=False, indent=2, default=json_default))
            return 0 if manifest["status"] == "GREEN" else 2
        parser.error("未知命令")
        return 2
    except Exception as exc:
        print(json.dumps({
            "status": "FAIL",
            "engine": ENGINE_ID,
            "error_type": type(exc).__name__,
            "message": str(exc),
            "traceback": traceback.format_exc(limit=8),
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
