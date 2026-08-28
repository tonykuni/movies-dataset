#!/usr/bin/env python3
"""
VETF Consensus Enrichment Adapter v001

將主動式台股 ETF 最新持股與價格、FactSet、YFinance 共識資料做 as-of join，
計算目標價空間及 N / N+1 / N+2 Forward P/E。

治理原則：
1. 預設 sandbox candidate，不改寫來源或 canonical。
2. 所有輸出 append-only；同內容跳過，不同內容拒絕覆寫。
3. canonical 模式必須通過 P0/P1 與兩個獨立寫入授權因素。
4. FactSet 與 YFinance 永遠分欄保存，不跨來源平均。
"""

from __future__ import annotations

# =============================================================================
# 0. 全域參數（所有可調參數集中於此）
# =============================================================================

PARAMS = {
    "engine_name": "VETF_ConsensusEnrichment_Adapter",
    "engine_version": "v001",
    "schema_version": "VETF_CONSENSUS_ENRICHED/1.0",
    "default_asof": "latest",
    "default_write_mode": "candidate",
    "canonical_write_enabled": False,
    "require_double_identity": True,
    "max_price_stale_calendar_days": 7,
    "max_consensus_age_calendar_days": 120,
    "provider_divergence_review_pct": 30.0,
    "eps_horizons": ("n", "n1", "n2"),
    "eps_statistics": ("low", "mean", "median", "high"),
    "target_statistics": ("low", "mean", "median", "high"),
    "forward_pe_primary_eps_stat": "mean",
    "candidate_output_name": "tw_active_etf_holdings_consensus_enriched",
    "output_date_format": "%Y/%m/%d",
    "internal_date_format": "%Y-%m-%d",
    "float_precision": 8,
    "csv_encoding": "utf-8-sig",
    "allow_optional_parquet": True,
    "allow_optional_duckdb": True,
}


HOLDING_ALIASES = {
    "holding_date": ("holding_date", "date", "asof", "as_of", "資料日期", "持股日期"),
    "etf_code": ("etf_code", "fund_code", "etf", "基金代碼", "代碼"),
    "etf_name": ("etf_name", "fund_name", "基金名稱", "ETF名稱"),
    "ticker": ("ticker", "symbol", "holding_ticker", "stock_ticker", "股票代碼", "個股代碼"),
    "isin": ("isin", "holding_isin", "stock_isin", "ISIN"),
    "company_name": ("company_name", "name", "stock_name", "公司名稱", "個股"),
    "exchange": ("exchange", "market", "上市市場", "交易所"),
    "currency": ("currency", "price_currency", "幣別"),
    "holding_weight": ("holding_weight", "weight", "weight_pct", "權重", "持股權重"),
    "holding_shares": ("holding_shares", "shares", "quantity", "持股數量", "股數"),
    "estimated_cost": ("estimated_cost", "estimated_avg_cost", "估均價", "估計成本"),
    "manager_action": ("manager_action", "action_state", "經理人動作", "動作"),
    "provider_id": ("provider_id", "security_id", "factset_entity_id", "資料商代碼"),
}


PRICE_ALIASES = {
    "ticker": ("ticker", "symbol", "yfinance_ticker", "YFinance Ticker", "股票代碼"),
    "isin": ("isin", "stock_isin", "ISIN"),
    "company_name": ("company_name", "name", "公司名稱"),
    "exchange": ("exchange", "market", "交易所"),
    "price_date": ("price_date", "date", "captured_at", "YFinance Captured At UTC", "資料日期"),
    "adj_close": ("adj_close", "adjusted_close", "Adj Close", "YFinance Adj Close", "price_adj"),
    "close": ("close", "Close", "current_price", "Current Price"),
    "currency": ("currency", "price_currency", "Currency", "幣別"),
    "provider_id": ("provider_id", "security_id", "資料商代碼"),
}


TARGET_ALIASES = {
    "ticker": ("ticker", "symbol", "yfinance_ticker", "YFinance Ticker", "Code", "股票代碼"),
    "isin": ("isin", "stock_isin", "ISIN"),
    "company_name": ("company_name", "name", "Company Name", "公司名稱"),
    "exchange": ("exchange", "market", "交易所"),
    "snapshot_date": (
        "snapshot_date", "consensus_date", "target_rate_date", "Target Rate Date",
        "fetched_at_utc", "Fetched At UTC", "captured_at", "Last Updated", "資料日期",
    ),
    "currency": ("currency", "target_currency", "Currency", "幣別"),
    "provider_id": ("provider_id", "provider_security_id", "Provider ID", "factset_entity_id"),
    "target_low": ("target_low", "targetLowPrice", "Target Low", "Consensus Target Low"),
    "target_mean": ("target_mean", "targetMeanPrice", "Target Mean", "Consensus Target Mean"),
    "target_median": ("target_median", "targetMedianPrice", "Target Median", "Consensus Target Median"),
    "target_high": ("target_high", "targetHighPrice", "Target High", "Consensus Target High"),
    "target_analyst_count": (
        "target_analyst_count", "numberOfAnalystOpinions", "Target Analyst Count",
        "Consensus Analyst Count", "analyst_count",
    ),
    "period": ("period", "fiscal_period", "horizon", "年度標記"),
    "fiscal_year": ("fiscal_year", "year", "Fiscal Year", "財政年度"),
    "fiscal_period_end": ("fiscal_period_end", "period_end", "Fiscal Period End", "財年結束日"),
    "eps_low": ("eps_low", "EPS Low", "Consensus EPS Low"),
    "eps_mean": ("eps_mean", "EPS Mean", "Consensus EPS Mean"),
    "eps_median": ("eps_median", "EPS Median", "Consensus EPS Median"),
    "eps_high": ("eps_high", "EPS High", "Consensus EPS High"),
    "eps_analyst_count": ("eps_analyst_count", "EPS Analyst Count", "analysts", "Analysts"),
}


for _horizon in PARAMS["eps_horizons"]:
    TARGET_ALIASES[f"eps_{_horizon}_fiscal_year"] = (
        f"eps_{_horizon}_fiscal_year", f"EPS {_horizon.upper()} Fiscal Year",
        f"{_horizon.upper()} Fiscal Year",
    )
    TARGET_ALIASES[f"eps_{_horizon}_fiscal_period_end"] = (
        f"eps_{_horizon}_fiscal_period_end", f"EPS {_horizon.upper()} Fiscal Period End",
    )
    TARGET_ALIASES[f"eps_{_horizon}_analyst_count"] = (
        f"eps_{_horizon}_analyst_count", f"EPS {_horizon.upper()} Analyst Count",
    )
    for _stat in PARAMS["eps_statistics"]:
        _legacy_names: tuple[str, ...] = ()
        if _horizon == "n" and _stat == "mean":
            _legacy_names = ("Consensus EPS Current Year", "EPS Current Year")
        elif _horizon == "n1" and _stat == "mean":
            _legacy_names = ("Consensus EPS Next Year", "EPS Next Year")
        elif _horizon == "n2" and _stat == "mean":
            _legacy_names = ("Consensus EPS Next 2 Year", "EPS Next 2 Year")
        TARGET_ALIASES[f"eps_{_horizon}_{_stat}"] = (
            f"eps_{_horizon}_{_stat}",
            f"EPS {_horizon.upper()} {_stat.title()}",
            f"Consensus EPS {_horizon.upper()} {_stat.title()}",
            *_legacy_names,
        )


# =============================================================================
# 1. 基礎工具
# =============================================================================

import argparse
import csv
import datetime as dt
import hashlib
import importlib.util
import json
import math
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def normalize_field_name(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).strip().lower())


def clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"none", "null", "nan", "na", "n/a", "-", "--"}:
        return None
    return text


def to_float(value: Any) -> float | None:
    text = clean_text(value)
    if text is None:
        return None
    try:
        normalized = text.replace(",", "").replace("%", "")
        number = float(normalized)
        return number if math.isfinite(number) else None
    except (TypeError, ValueError):
        return None


def to_int(value: Any) -> int | None:
    number = to_float(value)
    return None if number is None else int(number)


def round_number(value: float | None) -> float | None:
    if value is None or not math.isfinite(value):
        return None
    return round(value, int(PARAMS["float_precision"]))


def parse_date(value: Any) -> dt.date | None:
    text = clean_text(value)
    if text is None:
        return None
    normalized = text.replace("/", "-")
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        return dt.datetime.fromisoformat(normalized).date()
    except ValueError:
        pass
    for pattern in ("%Y-%m-%d", "%Y%m%d", "%Y-%m", "%Y"):
        try:
            parsed = dt.datetime.strptime(normalized[:10], pattern)
            return parsed.date()
        except ValueError:
            continue
    return None


def format_date(value: dt.date | None) -> str | None:
    return value.strftime(PARAMS["internal_date_format"]) if value else None


def canonicalize_record(record: Mapping[str, Any], aliases: Mapping[str, Sequence[str]]) -> dict[str, Any]:
    normalized_source = {normalize_field_name(key): value for key, value in record.items()}
    result: dict[str, Any] = {}
    for canonical, candidates in aliases.items():
        for candidate in (canonical, *candidates):
            normalized_candidate = normalize_field_name(candidate)
            if normalized_candidate in normalized_source:
                result[canonical] = normalized_source[normalized_candidate]
                break
    return result


def normalize_ticker(value: Any, exchange: Any = None) -> str | None:
    ticker = clean_text(value)
    if ticker is None:
        return None
    ticker = ticker.upper().replace(" ", "")
    if "." in ticker:
        return ticker
    market = (clean_text(exchange) or "").upper()
    if re.fullmatch(r"[0-9A-Z]{4,6}", ticker):
        return f"{ticker}.TWO" if market in {"TPEX", "OTC", "上櫃"} else f"{ticker}.TW"
    return ticker


def normalize_currency(value: Any, fallback: str = "TWD") -> str:
    text = clean_text(value)
    return (text or fallback).upper()


def normalize_period(value: Any) -> str | None:
    text = clean_text(value)
    if text is None:
        return None
    key = re.sub(r"[\s_+-]+", "", text.upper())
    mapping = {
        "N": "n", "FY0": "n", "CURRENTYEAR": "n", "CURRENT": "n",
        "N1": "n1", "FY1": "n1", "NEXTYEAR": "n1", "NEXT": "n1",
        "N2": "n2", "FY2": "n2", "NEXT2YEAR": "n2", "NEXT2": "n2",
    }
    return mapping.get(key)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def detect_optional_backends() -> dict[str, bool]:
    return {
        "pandas": importlib.util.find_spec("pandas") is not None,
        "polars": importlib.util.find_spec("polars") is not None,
        "pyarrow": importlib.util.find_spec("pyarrow") is not None,
        "duckdb": importlib.util.find_spec("duckdb") is not None,
    }


# =============================================================================
# 2. 輸入讀取器
# =============================================================================

def split_path_table(value: str | Path) -> tuple[Path, str | None]:
    text = str(value)
    if "::" in text:
        path_text, table = text.rsplit("::", 1)
        return Path(path_text), clean_text(table)
    return Path(text), None


def load_csv_records(path: Path) -> list[dict[str, Any]]:
    for encoding in ("utf-8-sig", "utf-8", "cp950", "big5"):
        try:
            with path.open("r", encoding=encoding, newline="") as handle:
                return [dict(row) for row in csv.DictReader(handle)]
        except UnicodeDecodeError:
            continue
    raise UnicodeError(f"無法解碼 CSV：{path}")


def load_json_records(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    if isinstance(payload, list):
        return [dict(row) for row in payload if isinstance(row, Mapping)]
    if isinstance(payload, Mapping):
        for key in ("records", "data", "rows", "items"):
            if isinstance(payload.get(key), list):
                return [dict(row) for row in payload[key] if isinstance(row, Mapping)]
        return [dict(payload)]
    raise ValueError(f"JSON 必須是 object 或 array：{path}")


def load_jsonl_records(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, Mapping):
                raise ValueError(f"JSONL 第 {line_number} 行不是 object：{path}")
            rows.append(dict(payload))
    return rows


def validate_sql_identifier(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise ValueError(f"不安全的資料表名稱：{value}")
    return value


def load_sqlite_records(path: Path, table: str | None) -> list[dict[str, Any]]:
    if not table:
        raise ValueError(f"SQLite 輸入必須指定資料表：{path}::table_name")
    safe_table = validate_sql_identifier(table)
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        rows = connection.execute(f'SELECT * FROM "{safe_table}"').fetchall()
        return [dict(row) for row in rows]
    finally:
        connection.close()


def load_parquet_records(path: Path) -> list[dict[str, Any]]:
    if importlib.util.find_spec("pyarrow") is not None:
        import pyarrow.parquet as parquet  # type: ignore

        return parquet.read_table(path).to_pylist()
    if importlib.util.find_spec("pandas") is not None:
        import pandas as pandas_module  # type: ignore

        try:
            return pandas_module.read_parquet(path).to_dict(orient="records")
        except ImportError as exc:
            raise RuntimeError("讀取 Parquet 需要 pyarrow 或 fastparquet") from exc
    raise RuntimeError("讀取 Parquet 需要 pyarrow、fastparquet 或 pandas")


def load_duckdb_records(path: Path, table: str | None) -> list[dict[str, Any]]:
    if importlib.util.find_spec("duckdb") is None:
        raise RuntimeError("讀取 DuckDB 需要 duckdb 套件")
    if not table:
        raise ValueError(f"DuckDB 輸入必須指定資料表：{path}::table_name")
    safe_table = validate_sql_identifier(table)
    import duckdb  # type: ignore

    connection = duckdb.connect(str(path), read_only=True)
    try:
        cursor = connection.execute(f'SELECT * FROM "{safe_table}"')
        columns = [item[0] for item in cursor.description]
        return [dict(zip(columns, row, strict=True)) for row in cursor.fetchall()]
    finally:
        connection.close()


def load_records(value: str | Path | None) -> list[dict[str, Any]]:
    if value is None:
        return []
    path, table = split_path_table(value)
    if not path.exists():
        raise FileNotFoundError(path)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return load_csv_records(path)
    if suffix == ".json":
        return load_json_records(path)
    if suffix in {".jsonl", ".ndjson"}:
        return load_jsonl_records(path)
    if suffix in {".sqlite", ".sqlite3", ".db"}:
        return load_sqlite_records(path, table)
    if suffix == ".parquet":
        return load_parquet_records(path)
    if suffix in {".duckdb", ".ddb"}:
        return load_duckdb_records(path, table)
    raise ValueError(f"不支援的輸入格式：{path}")


# =============================================================================
# 3. 正規化與身分驗證
# =============================================================================

def normalize_holding_records(records: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for source in records:
        row = canonicalize_record(source, HOLDING_ALIASES)
        row["holding_date"] = format_date(parse_date(row.get("holding_date")))
        row["exchange"] = (clean_text(row.get("exchange")) or "TWSE").upper()
        row["ticker"] = normalize_ticker(row.get("ticker"), row.get("exchange"))
        row["etf_code"] = (clean_text(row.get("etf_code")) or "").upper() or None
        row["isin"] = (clean_text(row.get("isin")) or "").upper() or None
        row["company_name"] = clean_text(row.get("company_name"))
        row["currency"] = normalize_currency(row.get("currency"))
        row["holding_weight"] = to_float(row.get("holding_weight"))
        row["holding_shares"] = to_float(row.get("holding_shares"))
        row["estimated_cost"] = to_float(row.get("estimated_cost"))
        row["provider_id"] = clean_text(row.get("provider_id"))
        result.append(row)
    return result


def normalize_price_records(records: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for source in records:
        row = canonicalize_record(source, PRICE_ALIASES)
        row["exchange"] = (clean_text(row.get("exchange")) or "TWSE").upper()
        row["ticker"] = normalize_ticker(row.get("ticker"), row.get("exchange"))
        row["price_date"] = format_date(parse_date(row.get("price_date")))
        row["adj_close"] = to_float(row.get("adj_close"))
        row["close"] = to_float(row.get("close"))
        row["currency"] = normalize_currency(row.get("currency"))
        row["isin"] = (clean_text(row.get("isin")) or "").upper() or None
        row["company_name"] = clean_text(row.get("company_name"))
        row["provider_id"] = clean_text(row.get("provider_id"))
        result.append(row)
    return result


def normalize_consensus_records(records: Iterable[Mapping[str, Any]], provider: str) -> list[dict[str, Any]]:
    normalized_rows: list[dict[str, Any]] = []
    for source in records:
        row = canonicalize_record(source, TARGET_ALIASES)
        row["exchange"] = (clean_text(row.get("exchange")) or "TWSE").upper()
        row["ticker"] = normalize_ticker(row.get("ticker"), row.get("exchange"))
        row["snapshot_date"] = format_date(parse_date(row.get("snapshot_date")))
        row["currency"] = normalize_currency(row.get("currency"))
        row["isin"] = (clean_text(row.get("isin")) or "").upper() or None
        row["company_name"] = clean_text(row.get("company_name"))
        row["provider_id"] = clean_text(row.get("provider_id"))
        row["provider"] = provider.upper()
        apply_year_based_eps_mapping(source, row)
        for stat in PARAMS["target_statistics"]:
            row[f"target_{stat}"] = to_float(row.get(f"target_{stat}"))
        row["target_analyst_count"] = to_int(row.get("target_analyst_count"))
        period = normalize_period(row.get("period"))
        if period:
            for stat in PARAMS["eps_statistics"]:
                row[f"eps_{period}_{stat}"] = to_float(row.get(f"eps_{stat}"))
            row[f"eps_{period}_analyst_count"] = to_int(row.get("eps_analyst_count"))
            row[f"eps_{period}_fiscal_year"] = to_int(row.get("fiscal_year"))
            row[f"eps_{period}_fiscal_period_end"] = format_date(parse_date(row.get("fiscal_period_end")))
        for horizon in PARAMS["eps_horizons"]:
            for stat in PARAMS["eps_statistics"]:
                row[f"eps_{horizon}_{stat}"] = to_float(row.get(f"eps_{horizon}_{stat}"))
            row[f"eps_{horizon}_analyst_count"] = to_int(row.get(f"eps_{horizon}_analyst_count"))
            row[f"eps_{horizon}_fiscal_year"] = to_int(row.get(f"eps_{horizon}_fiscal_year"))
            row[f"eps_{horizon}_fiscal_period_end"] = format_date(
                parse_date(row.get(f"eps_{horizon}_fiscal_period_end"))
            )
        normalized_rows.append(row)
    return merge_consensus_fragments(normalized_rows)


def extract_year_based_eps(source: Mapping[str, Any]) -> dict[int, dict[str, Any]]:
    """擷取 EPS 2026 Mean / EPS_2027_Median 等舊式年度欄位。"""
    result: dict[int, dict[str, Any]] = {}
    for raw_key, raw_value in source.items():
        key = normalize_field_name(raw_key)
        match = re.fullmatch(
            r"(?:consensus)?eps(20\d{2})(low|mean|median|high|analystcount|analysts|fiscalperiodend|updatedate)",
            key,
        )
        if not match:
            continue
        year = int(match.group(1))
        field = match.group(2)
        if field == "analysts":
            field = "analystcount"
        result.setdefault(year, {})[field] = raw_value
    return result


def apply_year_based_eps_mapping(source: Mapping[str, Any], row: dict[str, Any]) -> None:
    yearly = extract_year_based_eps(source)
    if not yearly:
        return
    snapshot_date = parse_date(row.get("snapshot_date"))
    reference_year = snapshot_date.year if snapshot_date else min(yearly)
    eligible_years = sorted(year for year in yearly if year >= reference_year)
    if not eligible_years:
        eligible_years = sorted(yearly)
    selected_years = eligible_years[: len(PARAMS["eps_horizons"])]
    for horizon, year in zip(PARAMS["eps_horizons"], selected_years, strict=False):
        values = yearly[year]
        row.setdefault(f"eps_{horizon}_fiscal_year", year)
        for stat in PARAMS["eps_statistics"]:
            if stat in values and row.get(f"eps_{horizon}_{stat}") is None:
                row[f"eps_{horizon}_{stat}"] = values[stat]
        if "analystcount" in values and row.get(f"eps_{horizon}_analyst_count") is None:
            row[f"eps_{horizon}_analyst_count"] = values["analystcount"]
        if "fiscalperiodend" in values and row.get(f"eps_{horizon}_fiscal_period_end") is None:
            row[f"eps_{horizon}_fiscal_period_end"] = values["fiscalperiodend"]
    row["eps_horizon_mapping_method"] = "INFERRED_FROM_EXPLICIT_FISCAL_YEAR_COLUMNS"


def merge_consensus_fragments(records: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str | None, str | None, str | None], dict[str, Any]] = {}
    for source in records:
        key = (clean_text(source.get("ticker")), clean_text(source.get("snapshot_date")), clean_text(source.get("provider")))
        target = grouped.setdefault(key, {})
        for field, value in source.items():
            if value is not None:
                target[field] = value
    return list(grouped.values())


def identity_evidence(record: Mapping[str, Any]) -> tuple[bool, list[str]]:
    primary = clean_text(record.get("ticker"))
    secondary_fields = ("isin", "company_name", "provider_id")
    secondary = [field for field in secondary_fields if clean_text(record.get(field))]
    return bool(primary and secondary), (["ticker"] if primary else []) + secondary


def validate_double_identity(records: Iterable[Mapping[str, Any]], source_name: str) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        passed, evidence = identity_evidence(record)
        if not passed:
            issues.append({
                "source": source_name,
                "row_index": index,
                "ticker": record.get("ticker"),
                "issue": "DOUBLE_IDENTITY_NOT_VERIFIED",
                "evidence": evidence,
            })
    return issues


# =============================================================================
# 4. As-of 選取與計算
# =============================================================================

def resolve_asof(value: str | None) -> dt.date:
    text = clean_text(value) or str(PARAMS["default_asof"])
    if text.lower() == "latest":
        return dt.datetime.now(dt.timezone.utc).date()
    parsed = parse_date(text)
    if parsed is None:
        raise ValueError(f"無效的 as-of 日期：{value}")
    return parsed


def select_latest_holdings(records: Iterable[Mapping[str, Any]], asof: dt.date) -> list[dict[str, Any]]:
    eligible: list[dict[str, Any]] = []
    latest_by_etf: dict[str, dt.date] = {}
    for source in records:
        row = dict(source)
        row_date = parse_date(row.get("holding_date"))
        etf_code = clean_text(row.get("etf_code"))
        if row_date is None or etf_code is None or row_date > asof:
            continue
        eligible.append(row)
        if etf_code not in latest_by_etf or row_date > latest_by_etf[etf_code]:
            latest_by_etf[etf_code] = row_date
    return [
        row for row in eligible
        if parse_date(row.get("holding_date")) == latest_by_etf.get(str(row.get("etf_code")))
    ]


def latest_index(
    records: Iterable[Mapping[str, Any]],
    asof: dt.date,
    date_field: str,
    key_field: str = "ticker",
) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    dates: dict[str, dt.date] = {}
    for source in records:
        row = dict(source)
        key = clean_text(row.get(key_field))
        row_date = parse_date(row.get(date_field))
        if key is None or row_date is None or row_date > asof:
            continue
        if key not in dates or row_date > dates[key]:
            dates[key] = row_date
            index[key] = row
    return index


def currency_matches(left: Any, right: Any) -> bool:
    return normalize_currency(left) == normalize_currency(right)


def target_upside_pct(target: Any, price: Any) -> float | None:
    target_value = to_float(target)
    price_value = to_float(price)
    if target_value is None or price_value is None or price_value <= 0:
        return None
    return round_number((target_value / price_value - 1.0) * 100.0)


def forward_pe(price: Any, eps: Any) -> tuple[float | None, str]:
    price_value = to_float(price)
    eps_value = to_float(eps)
    if price_value is None or price_value <= 0:
        return None, "MISSING_OR_INVALID_PRICE"
    if eps_value is None:
        return None, "MISSING_EPS"
    if eps_value == 0:
        return None, "ZERO_EPS"
    if eps_value < 0:
        return None, "NEGATIVE_EPS"
    return round_number(price_value / eps_value), "VALID"


def difference_pct(left: Any, right: Any) -> float | None:
    left_value = to_float(left)
    right_value = to_float(right)
    if left_value is None or right_value is None or right_value == 0:
        return None
    return round_number((left_value - right_value) / abs(right_value) * 100.0)


def validate_target_order(prefix: str, row: Mapping[str, Any]) -> bool | None:
    values = [to_float(row.get(f"{prefix}_target_{stat}")) for stat in PARAMS["target_statistics"]]
    low, mean, median, high = values
    available = [value for value in values if value is not None]
    if len(available) < 2:
        return None
    if low is not None and high is not None and low > high:
        return False
    if mean is not None and low is not None and mean < low:
        return False
    if mean is not None and high is not None and mean > high:
        return False
    if median is not None and low is not None and median < low:
        return False
    if median is not None and high is not None and median > high:
        return False
    return True


def copy_provider_fields(target: dict[str, Any], source: Mapping[str, Any] | None, provider_prefix: str) -> None:
    if source is None:
        target[f"{provider_prefix}_snapshot_date"] = None
        return
    target[f"{provider_prefix}_snapshot_date"] = source.get("snapshot_date")
    target[f"{provider_prefix}_currency"] = source.get("currency")
    target[f"{provider_prefix}_provider_id"] = source.get("provider_id")
    target[f"{provider_prefix}_target_analyst_count"] = source.get("target_analyst_count")
    for stat in PARAMS["target_statistics"]:
        target[f"{provider_prefix}_target_{stat}"] = source.get(f"target_{stat}")
    if provider_prefix == "fs":
        for horizon in PARAMS["eps_horizons"]:
            target[f"fs_eps_{horizon}_fiscal_year"] = source.get(f"eps_{horizon}_fiscal_year")
            target[f"fs_eps_{horizon}_fiscal_period_end"] = source.get(f"eps_{horizon}_fiscal_period_end")
            target[f"fs_eps_{horizon}_analyst_count"] = source.get(f"eps_{horizon}_analyst_count")
            for stat in PARAMS["eps_statistics"]:
                target[f"fs_eps_{horizon}_{stat}"] = source.get(f"eps_{horizon}_{stat}")


def calculate_quality_status(row: Mapping[str, Any], flags: Sequence[str]) -> tuple[str, float]:
    fatal = {"MISSING_PRICE", "PRICE_CURRENCY_MISMATCH", "DOUBLE_IDENTITY_NOT_VERIFIED"}
    status = "FAIL" if any(flag in fatal for flag in flags) else ("REVIEW" if flags else "PASS")
    score = 100.0
    penalties = {
        "MISSING_PRICE": 60.0,
        "STALE_PRICE": 20.0,
        "DOUBLE_IDENTITY_NOT_VERIFIED": 35.0,
        "PRICE_CURRENCY_MISMATCH": 50.0,
        "FS_TARGET_ORDER_INVALID": 20.0,
        "YF_TARGET_ORDER_INVALID": 20.0,
        "PROVIDER_DIVERGENCE": 15.0,
        "STALE_FACTSET_CONSENSUS": 15.0,
        "STALE_YFINANCE_CONSENSUS": 15.0,
        "MISSING_FACTSET_CONSENSUS": 10.0,
        "MISSING_YFINANCE_CONSENSUS": 5.0,
    }
    for flag in set(flags):
        score -= penalties.get(flag, 2.0)
    return status, max(0.0, round_number(score) or 0.0)


def enrich_holdings(
    holdings: Iterable[Mapping[str, Any]],
    prices: Iterable[Mapping[str, Any]],
    factset: Iterable[Mapping[str, Any]],
    yfinance: Iterable[Mapping[str, Any]],
    asof: dt.date,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    selected_holdings = select_latest_holdings(holdings, asof)
    price_index = latest_index(prices, asof, "price_date")
    factset_index = latest_index(factset, asof, "snapshot_date")
    yfinance_index = latest_index(yfinance, asof, "snapshot_date")
    enriched: list[dict[str, Any]] = []

    for source in selected_holdings:
        row = dict(source)
        ticker = clean_text(row.get("ticker"))
        price_source = price_index.get(ticker or "")
        fs_source = factset_index.get(ticker or "")
        yf_source = yfinance_index.get(ticker or "")
        price = None if price_source is None else to_float(price_source.get("adj_close"))
        if price is None and price_source is not None:
            price = to_float(price_source.get("close"))

        output = dict(row)
        output["analysis_date"] = format_date(asof)
        output["price_date"] = None if price_source is None else price_source.get("price_date")
        output["price_adj_close"] = price
        output["price_close"] = None if price_source is None else price_source.get("close")
        output["price_currency"] = None if price_source is None else price_source.get("currency")
        output["price_stale_days"] = None
        if price_source is not None:
            price_date = parse_date(price_source.get("price_date"))
            if price_date:
                output["price_stale_days"] = (asof - price_date).days

        copy_provider_fields(output, fs_source, "fs")
        copy_provider_fields(output, yf_source, "yf")
        flags: list[str] = []

        identity_passed, identity_fields = identity_evidence(output)
        output["double_identity_verified"] = identity_passed
        output["identity_evidence"] = "+".join(identity_fields)
        if PARAMS["require_double_identity"] and not identity_passed:
            flags.append("DOUBLE_IDENTITY_NOT_VERIFIED")

        if price is None:
            flags.append("MISSING_PRICE")
        if output.get("price_stale_days") is not None and output["price_stale_days"] > PARAMS["max_price_stale_calendar_days"]:
            flags.append("STALE_PRICE")

        for provider_prefix, provider_source in (("fs", fs_source), ("yf", yf_source)):
            if provider_source is None:
                flags.append(f"MISSING_{'FACTSET' if provider_prefix == 'fs' else 'YFINANCE'}_CONSENSUS")
                for stat in PARAMS["target_statistics"]:
                    output[f"{provider_prefix}_target_{stat}_upside_pct"] = None
                continue

            snapshot_date = parse_date(provider_source.get("snapshot_date"))
            age_days = None if snapshot_date is None else (asof - snapshot_date).days
            output[f"{provider_prefix}_consensus_age_days"] = age_days
            if age_days is not None and age_days > PARAMS["max_consensus_age_calendar_days"]:
                flags.append(f"STALE_{'FACTSET' if provider_prefix == 'fs' else 'YFINANCE'}_CONSENSUS")

            provider_currency_ok = currency_matches(output.get("price_currency"), provider_source.get("currency"))
            output[f"{provider_prefix}_currency_match"] = provider_currency_ok
            if not provider_currency_ok:
                flags.append("PRICE_CURRENCY_MISMATCH")
            for stat in PARAMS["target_statistics"]:
                output[f"{provider_prefix}_target_{stat}_upside_pct"] = (
                    target_upside_pct(provider_source.get(f"target_{stat}"), price)
                    if provider_currency_ok else None
                )

        fs_order = validate_target_order("fs", output)
        yf_order = validate_target_order("yf", output)
        if fs_order is False:
            flags.append("FS_TARGET_ORDER_INVALID")
        if yf_order is False:
            flags.append("YF_TARGET_ORDER_INVALID")

        output["target_median_yf_vs_fs_difference_pct"] = difference_pct(
            output.get("yf_target_median"), output.get("fs_target_median")
        )
        median_gap = output["target_median_yf_vs_fs_difference_pct"]
        if median_gap is not None and abs(median_gap) > PARAMS["provider_divergence_review_pct"]:
            flags.append("PROVIDER_DIVERGENCE")

        for horizon in PARAMS["eps_horizons"]:
            for eps_stat in ("mean", "median"):
                pe_value, pe_status = forward_pe(price, output.get(f"fs_eps_{horizon}_{eps_stat}"))
                output[f"fs_forward_pe_{horizon}_{eps_stat}"] = pe_value
                output[f"fs_forward_pe_{horizon}_{eps_stat}_status"] = pe_status
            primary_stat = str(PARAMS["forward_pe_primary_eps_stat"])
            output[f"fs_forward_pe_{horizon}"] = output.get(f"fs_forward_pe_{horizon}_{primary_stat}")
            output[f"fs_forward_pe_{horizon}_status"] = output.get(
                f"fs_forward_pe_{horizon}_{primary_stat}_status"
            )

        output["quality_flags"] = sorted(set(flags))
        output["record_status"], output["consensus_trust_score"] = calculate_quality_status(output, flags)
        enriched.append(output)

    audit = build_audit(enriched, asof)
    return enriched, audit


def coverage_pct(records: Sequence[Mapping[str, Any]], predicate: Any) -> float:
    if not records:
        return 0.0
    matched = sum(1 for row in records if predicate(row))
    return round_number(matched / len(records) * 100.0) or 0.0


def build_audit(records: Sequence[Mapping[str, Any]], asof: dt.date) -> dict[str, Any]:
    return {
        "engine": PARAMS["engine_name"],
        "version": PARAMS["engine_version"],
        "schema_version": PARAMS["schema_version"],
        "generated_at_utc": utc_now_iso(),
        "analysis_date": format_date(asof),
        "record_count": len(records),
        "status_counts": {
            status: sum(1 for row in records if row.get("record_status") == status)
            for status in ("PASS", "REVIEW", "FAIL")
        },
        "coverage_pct": {
            "price": coverage_pct(records, lambda row: row.get("price_adj_close") is not None),
            "factset_target": coverage_pct(records, lambda row: row.get("fs_target_mean") is not None),
            "yfinance_target": coverage_pct(records, lambda row: row.get("yf_target_mean") is not None),
            "factset_eps_n": coverage_pct(records, lambda row: row.get("fs_eps_n_mean") is not None),
            "factset_eps_n1": coverage_pct(records, lambda row: row.get("fs_eps_n1_mean") is not None),
            "factset_eps_n2": coverage_pct(records, lambda row: row.get("fs_eps_n2_mean") is not None),
            "forward_pe_n": coverage_pct(records, lambda row: row.get("fs_forward_pe_n") is not None),
            "forward_pe_n1": coverage_pct(records, lambda row: row.get("fs_forward_pe_n1") is not None),
            "forward_pe_n2": coverage_pct(records, lambda row: row.get("fs_forward_pe_n2") is not None),
            "double_identity": coverage_pct(records, lambda row: row.get("double_identity_verified") is True),
        },
        "optional_backends": detect_optional_backends(),
    }


# =============================================================================
# 5. 寫入閘門與 Append-Only 輸出
# =============================================================================

def load_mapping_file(path: str | Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    if not isinstance(payload, Mapping):
        raise ValueError(f"閘門檔案必須是 JSON object：{path}")
    return dict(payload)


def validate_canonical_write_gate(
    write_mode: str,
    acceptance_file: str | Path | None,
    authorization_file: str | Path | None,
) -> dict[str, Any]:
    if write_mode != "canonical":
        return {"mode": write_mode, "passed": True, "reason": "CANDIDATE_SANDBOX_ONLY"}
    if not PARAMS["canonical_write_enabled"]:
        raise PermissionError("SSOT 尚未啟用 canonical_write_enabled")
    acceptance = load_mapping_file(acceptance_file)
    authorization = load_mapping_file(authorization_file)
    p0 = acceptance.get("p0") == "ACCEPTED"
    p1 = acceptance.get("p1") == "ACCEPTED"
    factor_a = clean_text(authorization.get("factor_a_attestation"))
    factor_b = clean_text(authorization.get("factor_b_attestation"))
    distinct = bool(factor_a and factor_b and factor_a != factor_b)
    if not (p0 and p1 and distinct):
        raise PermissionError("canonical 寫入需要 P0/P1 ACCEPTED 與兩個不同的授權證明")
    return {"mode": write_mode, "passed": True, "reason": "P0_P1_AND_DUAL_AUTH_PASSED"}


def write_json_file(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def write_csv_file(path: Path, records: Sequence[Mapping[str, Any]]) -> None:
    fields = sorted({key for row in records for key in row.keys()})
    with path.open("w", encoding=str(PARAMS["csv_encoding"]), newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in records:
            normalized = {
                key: json.dumps(value, ensure_ascii=False, sort_keys=True) if isinstance(value, (list, dict)) else value
                for key, value in row.items()
            }
            writer.writerow(normalized)


def write_optional_parquet(path: Path, records: Sequence[Mapping[str, Any]]) -> str:
    if not PARAMS["allow_optional_parquet"]:
        return "DISABLED"
    if importlib.util.find_spec("pyarrow") is not None:
        import pyarrow as arrow  # type: ignore
        import pyarrow.parquet as parquet  # type: ignore

        parquet.write_table(arrow.Table.from_pylist([dict(row) for row in records]), path, compression="zstd")
        return "WRITTEN_PYARROW"
    return "SKIPPED_MISSING_BACKEND"


def write_optional_duckdb(path: Path, records: Sequence[Mapping[str, Any]]) -> str:
    if not PARAMS["allow_optional_duckdb"]:
        return "DISABLED"
    if importlib.util.find_spec("duckdb") is None or importlib.util.find_spec("pandas") is None:
        return "SKIPPED_MISSING_BACKEND"
    import duckdb  # type: ignore
    import pandas as pandas_module  # type: ignore

    frame = pandas_module.DataFrame(records)
    connection = duckdb.connect(str(path))
    try:
        connection.register("candidate_frame", frame)
        connection.execute("CREATE TABLE holdings_consensus_enriched AS SELECT * FROM candidate_frame")
    finally:
        connection.close()
    return "WRITTEN_CANDIDATE_DUCKDB"


def write_outputs_append_only(
    output_dir: str | Path,
    records: Sequence[Mapping[str, Any]],
    audit: Mapping[str, Any],
    write_mode: str = "candidate",
    acceptance_file: str | Path | None = None,
    authorization_file: str | Path | None = None,
) -> dict[str, Any]:
    gate = validate_canonical_write_gate(write_mode, acceptance_file, authorization_file)
    analysis_date = str(audit.get("analysis_date") or "unknown")
    safe_date = analysis_date.replace("/", "-")
    run_dir = Path(output_dir) / f"asof={safe_date}"
    run_dir.mkdir(parents=True, exist_ok=True)
    content_hash = sha256_bytes(stable_json_bytes(records))
    manifest_path = run_dir / "manifest.json"

    if manifest_path.exists():
        previous = load_mapping_file(manifest_path)
        if previous.get("content_sha256") == content_hash:
            return {
                "status": "SKIPPED_IDENTICAL",
                "run_dir": str(run_dir),
                "content_sha256": content_hash,
                "gate": gate,
            }
        raise FileExistsError(f"APPEND_ONLY_CONFLICT：{manifest_path} 已存在不同內容")

    base_name = str(PARAMS["candidate_output_name"])
    json_path = run_dir / f"{base_name}.json"
    csv_path = run_dir / f"{base_name}.csv"
    parquet_path = run_dir / f"{base_name}.parquet"
    duckdb_path = run_dir / f"{base_name}.duckdb"
    audit_path = run_dir / "audit.json"

    write_json_file(json_path, records)
    write_csv_file(csv_path, records)
    parquet_status = write_optional_parquet(parquet_path, records)
    duckdb_status = write_optional_duckdb(duckdb_path, records)
    write_json_file(audit_path, dict(audit))

    manifest = {
        "engine": PARAMS["engine_name"],
        "version": PARAMS["engine_version"],
        "schema_version": PARAMS["schema_version"],
        "created_at_utc": utc_now_iso(),
        "write_mode": write_mode,
        "gate": gate,
        "record_count": len(records),
        "content_sha256": content_hash,
        "outputs": {
            "json": str(json_path),
            "csv": str(csv_path),
            "parquet": parquet_status,
            "duckdb": duckdb_status,
            "audit": str(audit_path),
        },
    }
    write_json_file(manifest_path, manifest)
    return {"status": "WRITTEN", "run_dir": str(run_dir), **manifest}


# =============================================================================
# 6. 執行入口
# =============================================================================

def build_input_provenance(paths: Mapping[str, str | Path | None]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in paths.items():
        if value is None:
            result[name] = {"status": "NOT_PROVIDED"}
            continue
        path, table = split_path_table(value)
        result[name] = {
            "path": str(path),
            "table": table,
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else None,
            "sha256": sha256_file(path) if path.exists() and path.is_file() else None,
        }
    return result


def run_pipeline(
    holdings_path: str | Path,
    prices_path: str | Path,
    factset_path: str | Path | None,
    yfinance_path: str | Path | None,
    output_dir: str | Path,
    asof_value: str = "latest",
    write_mode: str = "candidate",
    acceptance_file: str | Path | None = None,
    authorization_file: str | Path | None = None,
) -> dict[str, Any]:
    asof = resolve_asof(asof_value)
    raw_holdings = load_records(holdings_path)
    raw_prices = load_records(prices_path)
    raw_factset = load_records(factset_path)
    raw_yfinance = load_records(yfinance_path)

    holdings = normalize_holding_records(raw_holdings)
    prices = normalize_price_records(raw_prices)
    factset = normalize_consensus_records(raw_factset, "FACTSET")
    yfinance = normalize_consensus_records(raw_yfinance, "YFINANCE")

    identity_issues = []
    identity_issues.extend(validate_double_identity(holdings, "holdings"))
    identity_issues.extend(validate_double_identity(prices, "prices"))
    identity_issues.extend(validate_double_identity(factset, "factset"))
    identity_issues.extend(validate_double_identity(yfinance, "yfinance"))

    enriched, audit = enrich_holdings(holdings, prices, factset, yfinance, asof)
    audit["source_counts"] = {
        "holdings": len(holdings),
        "prices": len(prices),
        "factset": len(factset),
        "yfinance": len(yfinance),
    }
    audit["identity_issues"] = identity_issues
    audit["input_provenance"] = build_input_provenance({
        "holdings": holdings_path,
        "prices": prices_path,
        "factset": factset_path,
        "yfinance": yfinance_path,
    })
    if write_mode == "canonical" and identity_issues:
        raise PermissionError("canonical 寫入被雙重身分驗證閘門拒絕")

    write_result = write_outputs_append_only(
        output_dir=output_dir,
        records=enriched,
        audit=audit,
        write_mode=write_mode,
        acceptance_file=acceptance_file,
        authorization_file=authorization_file,
    )
    return {"audit": audit, "write_result": write_result, "records": enriched}


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VETF FactSet/YFinance Consensus Enrichment Adapter")
    parser.add_argument("--holdings", required=True, help="持股檔；資料庫可用 path::table")
    parser.add_argument("--prices", required=True, help="Adj Close 價格檔；資料庫可用 path::table")
    parser.add_argument("--factset", help="FactSet target/EPS snapshot")
    parser.add_argument("--yfinance", help="YFinance target snapshot")
    parser.add_argument("--output-dir", required=True, help="候選輸出資料夾")
    parser.add_argument("--asof", default=str(PARAMS["default_asof"]), help="YYYY-MM-DD 或 latest")
    parser.add_argument("--write-mode", choices=("candidate", "canonical"), default=str(PARAMS["default_write_mode"]))
    parser.add_argument("--acceptance-file", help="P0/P1 acceptance JSON")
    parser.add_argument("--authorization-file", help="雙因素寫入授權 JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_argument_parser()
    args = parser.parse_args(argv)
    try:
        result = run_pipeline(
            holdings_path=args.holdings,
            prices_path=args.prices,
            factset_path=args.factset,
            yfinance_path=args.yfinance,
            output_dir=args.output_dir,
            asof_value=args.asof,
            write_mode=args.write_mode,
            acceptance_file=args.acceptance_file,
            authorization_file=args.authorization_file,
        )
        summary = {
            "status": result["write_result"].get("status"),
            "analysis_date": result["audit"].get("analysis_date"),
            "record_count": result["audit"].get("record_count"),
            "status_counts": result["audit"].get("status_counts"),
            "coverage_pct": result["audit"].get("coverage_pct"),
            "run_dir": result["write_result"].get("run_dir"),
        }
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        error = {
            "status": "FAIL_CLOSED",
            "engine": PARAMS["engine_name"],
            "error_type": type(exc).__name__,
            "message": str(exc),
        }
        print(json.dumps(error, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
