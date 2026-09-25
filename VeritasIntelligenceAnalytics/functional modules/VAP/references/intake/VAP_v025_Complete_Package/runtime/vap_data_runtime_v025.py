#!/usr/bin/env python3
"""VeritasAutoPlot v025 local read-only data runtime and file bridge."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import logging
import mimetypes
import os
import re
import sqlite3
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from dataclasses import dataclass
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Iterable


# def 01 PARAMETERS
APP_VERSION = "v025"
RUNTIME_SCHEMA = "VIA-VAP-RUNTIME/1.0"
CATALOG_SCHEMA = "VIA-VAP-CATALOG/1.0"
IMAGE_SCHEMA = "VIA-VAP-GOVERNED-CHART-IMAGE/1.0"
VDF_SCHEMA = "VIA-VDF-VAP-CONNECTION-MANIFEST/1.0"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
DEFAULT_MAX_ROWS = 5000
DEFAULT_MAX_BODY_BYTES = 20 * 1024 * 1024
DEFAULT_REQUEST_TIMEOUT_SECONDS = 20
DEFAULT_UI_RELATIVE_PATH = "ui/VAP_Workbench_v025.html"
DEFAULT_CONFIG_RELATIVE_PATH = "config/vap_runtime_config.json"
DEFAULT_CACHE_RELATIVE_PATH = "state/catalog_cache.json"
DEFAULT_CHECKPOINT_RELATIVE_PATH = "state/refresh_checkpoint.json"
DEFAULT_IMAGE_DIRECTORY = "output/saved_images"
DEFAULT_LOG_RELATIVE_PATH = "logs/vap_runtime_v025.jsonl"
DEFAULT_READY_RELATIVE_PATH = "state/runtime_ready.json"
DEFAULT_PID_RELATIVE_PATH = "state/runtime.pid"
ALLOWED_ENGINES = {"CSV", "TSV", "JSON", "JSON_ENDPOINT", "PARQUET", "SQLITE", "DUCKDB"}
DATE_FIELD_CANDIDATES = (
    "date", "datetime", "timestamp", "time", "period", "month", "日期", "時間"
)
VOLUME_PATTERN = re.compile(r"volume|turnover|成交量|成交值", re.I)
PRICE_PATTERN = re.compile(r"adj(?:usted)?[_ ]?(open|high|low|close|price)|adj(Open|High|Low|Close|Price)|open|high|low|close|price|價格|收盤", re.I)
ADJUSTED_PRICE_PATTERN = re.compile(r"^adj(?:usted)?[_ ]?(open|high|low|close|price)$", re.I)
PERCENT_PATTERN = re.compile(r"pct|percent|percentage|rate|yield|ratio|報酬率|殖利率|比率", re.I)
FORBIDDEN_SQL_PATTERN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|replace|truncate|attach|detach|pragma)\b", re.I
)
FORBIDDEN_SVG_PATTERN = re.compile(
    r"<\s*(script|foreignObject|iframe|object|embed|link|image)\b|\bon\w+\s*=|(?:href|src)\s*=\s*['\"]\s*(?:https?:|data:|javascript:)",
    re.I,
)


# def 02 BASIC UTILITIES
def def_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def def_package_root() -> Path:
    return Path(__file__).resolve().parents[1]


def def_canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def def_sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def def_sha256_text(value: str) -> str:
    return def_sha256_bytes(value.encode("utf-8"))


def def_atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    os.replace(temporary, path)


def def_atomic_write_json(path: Path, value: Any) -> None:
    def_atomic_write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def def_load_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError):
        return fallback


def def_safe_identifier(value: Any, fallback: str = "table") -> str:
    cleaned = re.sub(r"[^0-9A-Za-z_\-\u4e00-\u9fff]+", "_", str(value or "")).strip("_")
    return (cleaned[:96] or fallback)


def def_json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime, Path)):
        return str(value)
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except (TypeError, ValueError):
            pass
    return str(value)


def def_normalize_rows(rows: Iterable[dict[str, Any]], max_rows: int) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if index >= max_rows:
            break
        normalized.append({str(key): def_json_safe(value) for key, value in dict(row).items()})
    return normalized


def def_expand_location(value: str) -> Path:
    expanded = os.path.expandvars(os.path.expanduser(value))
    return Path(expanded).resolve(strict=False)


def def_resolve_allowed_path(value: str, allowed_roots: Iterable[str], require_exists: bool = True) -> Path:
    candidate = def_expand_location(value)
    roots = [def_expand_location(root) for root in allowed_roots if str(root).strip()]
    if not roots:
        raise PermissionError("ALLOWED_ROOTS_EMPTY")
    allowed = any(candidate == root or root in candidate.parents for root in roots)
    if not allowed:
        raise PermissionError(f"PATH_OUTSIDE_ALLOWED_ROOTS:{candidate}")
    if require_exists and not candidate.exists():
        raise FileNotFoundError(candidate)
    return candidate


def def_source_signature(path: Path) -> str:
    stat = path.stat()
    payload = f"{path}|{stat.st_size}|{stat.st_mtime_ns}"
    return def_sha256_text(payload)


def def_resolve_allowed_url(value: str, allowed_hosts: Iterable[str]) -> str:
    parsed = urllib.parse.urlparse(value)
    hosts = {str(host).strip().lower() for host in allowed_hosts if str(host).strip()}
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise PermissionError("ENDPOINT_HTTP_OR_HTTPS_REQUIRED")
    if parsed.username or parsed.password:
        raise PermissionError("ENDPOINT_EMBEDDED_CREDENTIALS_REJECTED")
    if parsed.hostname.lower() not in hosts:
        raise PermissionError(f"ENDPOINT_HOST_NOT_ALLOWED:{parsed.hostname}")
    return urllib.parse.urlunparse(parsed)


def def_config_fingerprint(config: dict[str, Any]) -> str:
    masked = json.loads(json.dumps(config))
    for source in masked.get("sources", []):
        source.pop("headers", None)
        source.pop("token", None)
    return def_sha256_text(def_canonical_json(masked))


def def_load_vdf_manifest(package_root: Path, config: dict[str, Any]) -> dict[str, Any]:
    gateway = dict(config.get("vdfGateway", {}))
    location = str(gateway.get("manifest", "{PACKAGE_ROOT}/config/vdf_connection_manifest.json"))
    location = location.replace("{PACKAGE_ROOT}", str(package_root)).replace("{USER_HOME}", str(Path.home()))
    path = def_resolve_allowed_path(location, config.get("allowedRoots", []))
    manifest = def_load_json(path, {})
    if manifest.get("schema") != VDF_SCHEMA or not isinstance(manifest.get("connections"), list):
        raise ValueError("VDF_CONNECTION_MANIFEST_INVALID")
    return manifest


def def_vdf_evidence(source: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    source_id = str(source.get("id", source.get("alias", "")))
    contract_id = str(source.get("vdfContractId", ""))
    evidence = next((item for item in manifest.get("connections", []) if str(item.get("sourceId")) == source_id and str(item.get("contractId")) == contract_id), None)
    if not evidence or evidence.get("state") != "AUTHORIZED" or not evidence.get("readOnly", False):
        raise PermissionError(f"VDF_AUTHORIZATION_REQUIRED:{source_id}")
    supplied_fingerprint = str(evidence.get("fingerprint", ""))
    fingerprint_payload = {key: value for key, value in evidence.items() if key != "fingerprint"}
    expected_fingerprint = def_sha256_text(def_canonical_json(fingerprint_payload))
    if supplied_fingerprint != expected_fingerprint:
        raise PermissionError(f"VDF_FINGERPRINT_MISMATCH:{source_id}")
    if str(evidence.get("engine", "")).upper() != str(source.get("engine", "")).upper():
        raise PermissionError(f"VDF_ENGINE_MISMATCH:{source_id}")
    asset_class = str(evidence.get("assetClass", "OTHER")).upper()
    if asset_class in {"STOCK", "EQUITY", "ETF", "STOCK_INDEX"}:
        adjusted = str(evidence.get("adjustedPriceField", ""))
        ta_lib = dict(evidence.get("taLibEvidence", {}))
        if not ADJUSTED_PRICE_PATTERN.fullmatch(adjusted):
            raise PermissionError(f"VDF_ADJUSTED_PRICE_REQUIRED:{source_id}")
        if ta_lib.get("engine") != "TA-Lib" or ta_lib.get("status") != "PASS":
            raise PermissionError(f"VDF_TALIB_EVIDENCE_REQUIRED:{source_id}")
    return evidence


# def 03 SEMANTIC AND CATALOG CONTRACTS
def def_is_number(value: Any) -> bool:
    if value is None or isinstance(value, bool):
        return False
    try:
        float(str(value).replace(",", ""))
        return True
    except (TypeError, ValueError):
        return False


def def_infer_columns(rows: list[dict[str, Any]]) -> tuple[list[str], list[str], str]:
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    numeric: list[str] = []
    for column in columns:
        values = [row.get(column) for row in rows if row.get(column) not in (None, "")]
        if values and sum(def_is_number(value) for value in values) / len(values) >= 0.8:
            numeric.append(column)
    lowered = {column.lower(): column for column in columns}
    x_column = next((lowered[name] for name in DATE_FIELD_CANDIDATES if name in lowered), columns[0] if columns else "date")
    return columns, numeric, x_column


def def_infer_field_semantic(database: str, table: str, field: str, x_field: str) -> dict[str, Any]:
    lowered = field.lower()
    if field == x_field:
        data_type, unit, role, aggregation = "Date", "Date", "X_TIME", "NONE"
    elif VOLUME_PATTERN.search(lowered):
        data_type, unit, role, aggregation = "Integer", "Shares", "RIGHT_VALUE", "SUM"
    elif PERCENT_PATTERN.search(lowered):
        data_type, unit, role, aggregation = "Percentage", "%", "LEFT_VALUE", "LAST"
    elif PRICE_PATTERN.search(lowered):
        data_type, unit, role, aggregation = "Currency", "TWD", "LEFT_VALUE", "LAST"
    else:
        data_type, unit, role, aggregation = "Number", "Unitless", "LEFT_VALUE", "LAST"
    if ADJUSTED_PRICE_PATTERN.fullmatch(field):
        component = ADJUSTED_PRICE_PATTERN.fullmatch(field).group(1) or ADJUSTED_PRICE_PATTERN.fullmatch(field).group(2) or "Price"
        subject = "Adjusted " + component.title()
    else:
        subject = field.replace("_", " ").strip().title()
    identity = f"{database}|{table}|{field}|1"
    return {
        "schema": "VIA-VAP-SEMANTIC-FIELD-REGISTRY/1.0",
        "id": "VAP-FIELD-" + def_sha256_text(identity)[:16].upper(),
        "version": 1,
        "database": database,
        "tableName": table,
        "field": field,
        "subject": subject,
        "unit": unit,
        "dataType": data_type,
        "role": role,
        "aggregation": aggregation,
        "frequency": "INFERRED",
        "source": "RUNTIME_INFERRED",
    }


def def_build_catalog_table(
    name: str,
    origin: str,
    database_alias: str,
    rows: list[dict[str, Any]],
    source_fingerprint: str,
) -> dict[str, Any]:
    columns, numeric, x_column = def_infer_columns(rows)
    if not columns or len(numeric) < 1 or len(rows) < 3:
        raise ValueError("CATALOG_GATE_REJECTED:ROWS_OR_NUMERIC_FIELDS")
    safe_name = def_safe_identifier(name)
    return {
        "schema": CATALOG_SCHEMA,
        "name": safe_name,
        "origin": origin,
        "database_alias": database_alias,
        "x": x_column,
        "all_columns": columns,
        "numeric": numeric,
        "rows": rows,
        "field_semantics": [
            def_infer_field_semantic(database_alias, safe_name, column, x_column) for column in columns
        ],
        "source_fingerprint": source_fingerprint,
        "asof": str(rows[-1].get(x_column, "")),
        "runtime": {"version": APP_VERSION, "readOnly": True, "loadedAt": def_now_iso()},
    }


# def 04 READ-ONLY ADAPTERS
def def_read_delimited(path: Path, delimiter: str, max_rows: int) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return def_normalize_rows(csv.DictReader(handle, delimiter=delimiter), max_rows)


def def_read_json(path: Path, max_rows: int) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(payload, dict):
        payload = payload.get("rows", payload.get("data", payload.get("records", [])))
    if not isinstance(payload, list) or not all(isinstance(row, dict) for row in payload):
        raise ValueError("JSON_ROWS_REQUIRED")
    return def_normalize_rows(payload, max_rows)


def def_json_rows(payload: Any, max_rows: int) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        payload = payload.get("rows", payload.get("data", payload.get("records", [])))
    if not isinstance(payload, list) or not all(isinstance(row, dict) for row in payload):
        raise ValueError("JSON_ROWS_REQUIRED")
    return def_normalize_rows(payload, max_rows)


def def_read_json_endpoint(source: dict[str, Any], config: dict[str, Any], max_rows: int) -> tuple[list[dict[str, Any]], str, str]:
    endpoint = def_resolve_allowed_url(str(source.get("location", "")), config.get("allowedHosts", []))
    headers = {"Accept": "application/json", "User-Agent": f"VeritasAutoPlot/{APP_VERSION}"}
    for header, environment_name in dict(source.get("headersFromEnvironment", {})).items():
        if not re.fullmatch(r"[A-Za-z0-9-]{1,64}", str(header)):
            raise ValueError("ENDPOINT_HEADER_NAME_REJECTED")
        secret = os.environ.get(str(environment_name), "")
        if secret:
            headers[str(header)] = secret
    request = urllib.request.Request(endpoint, headers=headers, method="GET")
    timeout = max(1, min(int(config.get("requestTimeoutSeconds", DEFAULT_REQUEST_TIMEOUT_SECONDS)), 120))
    maximum = int(config.get("maxBodyBytes", DEFAULT_MAX_BODY_BYTES))
    with urllib.request.urlopen(request, timeout=timeout) as response:
        final_url = def_resolve_allowed_url(response.geturl(), config.get("allowedHosts", []))
        raw = response.read(maximum + 1)
        if len(raw) > maximum:
            raise ValueError("ENDPOINT_RESPONSE_TOO_LARGE")
    payload = json.loads(raw.decode("utf-8-sig"))
    return def_json_rows(payload, max_rows), def_sha256_bytes(raw), final_url


def def_read_sqlite(path: Path, table: str | None, max_rows: int) -> list[tuple[str, list[dict[str, Any]]]]:
    uri = path.as_uri() + "?mode=ro"
    results: list[tuple[str, list[dict[str, Any]]]] = []
    with sqlite3.connect(uri, uri=True) as connection:
        connection.row_factory = sqlite3.Row
        names = [table] if table else [
            row[0] for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        for name in names:
            if not name or not re.fullmatch(r"[0-9A-Za-z_\-\u4e00-\u9fff]+", name):
                raise ValueError("SQLITE_TABLE_IDENTIFIER_REJECTED")
            query = f'SELECT * FROM "{name}" LIMIT ?'
            rows = [dict(row) for row in connection.execute(query, (max_rows,))]
            results.append((name, def_normalize_rows(rows, max_rows)))
    return results


def def_import_optional(module_name: str) -> Any:
    try:
        return __import__(module_name)
    except ImportError:
        return None


def def_read_parquet(path: Path, max_rows: int) -> list[dict[str, Any]]:
    duckdb = def_import_optional("duckdb")
    if duckdb:
        connection = duckdb.connect(database=":memory:")
        try:
            cursor = connection.execute("SELECT * FROM read_parquet(?) LIMIT ?", [str(path), max_rows])
            columns = [item[0] for item in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        finally:
            connection.close()
    polars = def_import_optional("polars")
    if polars:
        return def_normalize_rows(polars.read_parquet(path, n_rows=max_rows).to_dicts(), max_rows)
    try:
        import pyarrow.parquet as parquet
    except ImportError as error:
        raise RuntimeError("PARQUET_REQUIRES_DUCKDB_POLARS_OR_PYARROW") from error
    return def_normalize_rows(parquet.read_table(path).slice(0, max_rows).to_pylist(), max_rows)


def def_read_duckdb(path: Path, table: str | None, max_rows: int) -> list[tuple[str, list[dict[str, Any]]]]:
    duckdb = def_import_optional("duckdb")
    if not duckdb:
        raise RuntimeError("DUCKDB_PACKAGE_REQUIRED")
    connection = duckdb.connect(str(path), read_only=True)
    try:
        names = [table] if table else [row[0] for row in connection.execute("SHOW TABLES").fetchall()]
        results: list[tuple[str, list[dict[str, Any]]]] = []
        for name in names:
            if not name or not re.fullmatch(r"[0-9A-Za-z_\-\u4e00-\u9fff]+", name):
                raise ValueError("DUCKDB_TABLE_IDENTIFIER_REJECTED")
            cursor = connection.execute(f'SELECT * FROM "{name}" LIMIT ?', [max_rows])
            columns = [item[0] for item in cursor.description]
            results.append((name, [dict(zip(columns, row)) for row in cursor.fetchall()]))
        return results
    finally:
        connection.close()


def def_forward_fill_numeric(values: Iterable[Any]) -> list[float]:
    output: list[float] = []
    prior: float | None = None
    for value in values:
        try:
            numeric = float(value) if value not in (None, "") else None
        except (TypeError, ValueError):
            numeric = None
        if numeric is None:
            numeric = prior
        output.append(float("nan") if numeric is None else numeric)
        if numeric is not None:
            prior = numeric
    return output


def def_apply_talib_indicators(rows: list[dict[str, Any]], adjusted_field: str, indicators: Iterable[str]) -> list[dict[str, Any]]:
    requested = [str(item).upper() for item in indicators]
    if not requested:
        return rows
    talib = def_import_optional("talib")
    numpy = def_import_optional("numpy")
    if not talib or not numpy:
        raise RuntimeError("TALIB_AND_NUMPY_REQUIRED_FOR_TECHNICAL_INDICATORS")
    values = numpy.asarray(def_forward_fill_numeric(row.get(adjusted_field) for row in rows), dtype=float)
    outputs: dict[str, Any] = {}
    for indicator in requested:
        if indicator == "SMA":
            outputs["ta_sma_20"] = talib.SMA(values, timeperiod=20)
        elif indicator == "EMA":
            outputs["ta_ema_20"] = talib.EMA(values, timeperiod=20)
        elif indicator == "RSI":
            outputs["ta_rsi_14"] = talib.RSI(values, timeperiod=14)
        elif indicator == "MACD":
            macd, signal, histogram = talib.MACD(values, fastperiod=12, slowperiod=26, signalperiod=9)
            outputs.update({"ta_macd": macd, "ta_macd_signal": signal, "ta_macd_hist": histogram})
        elif indicator in {"BB", "BBANDS"}:
            upper, middle, lower = talib.BBANDS(values, timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
            outputs.update({"ta_bb_upper": upper, "ta_bb_middle": middle, "ta_bb_lower": lower})
        else:
            raise ValueError(f"TALIB_INDICATOR_NOT_ALLOWED:{indicator}")
    for index, row in enumerate(rows):
        for field, series in outputs.items():
            value = float(series[index])
            row[field] = None if not numpy.isfinite(value) else value
    return rows


def def_apply_missing_value_policy(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return rows
    fields = list(rows[0])
    price_fields = [field for field in fields if PRICE_PATTERN.search(field)]
    volume_fields = [field for field in fields if VOLUME_PATTERN.search(field)]
    prior: dict[str, Any] = {field: None for field in price_fields}
    for row in rows:
        for field in price_fields:
            value = row.get(field)
            if value in (None, ""):
                row[field] = prior[field]
            else:
                prior[field] = value
        for field in volume_fields:
            if row.get(field) in (None, ""):
                row[field] = 0
    return rows


def def_source_change_token(source: dict[str, Any], config: dict[str, Any]) -> str | None:
    engine = str(source.get("engine", "")).upper()
    if engine == "JSON_ENDPOINT":
        return None
    location = def_resolve_allowed_path(str(source.get("location", "")), config.get("allowedRoots", []))
    return def_source_signature(location)


def def_source_tables(source: dict[str, Any], config: dict[str, Any], vdf_evidence: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    engine = str(source.get("engine", "")).upper()
    if engine not in ALLOWED_ENGINES:
        raise ValueError(f"ENGINE_NOT_ALLOWED:{engine}")
    max_rows = min(int(source.get("maxRows", config.get("maxRows", DEFAULT_MAX_ROWS))), 100_000)
    roots = config.get("allowedRoots", [])
    location: Path | None = None
    origin: str
    if engine == "JSON_ENDPOINT":
        origin = str(source.get("location", ""))
        default_name = "json_endpoint"
    else:
        location = def_resolve_allowed_path(str(source.get("location", "")), roots)
        origin = str(location)
        default_name = location.stem
    alias = def_safe_identifier(source.get("alias", source.get("id", default_name)), "VAP_DATA")
    source_id = def_safe_identifier(source.get("id", alias), alias)
    table_hint = source.get("table")
    table_rows: list[tuple[str, list[dict[str, Any]]]]
    if engine == "CSV":
        assert location is not None
        table_rows = [(table_hint or location.stem, def_read_delimited(location, ",", max_rows))]
    elif engine == "TSV":
        assert location is not None
        table_rows = [(table_hint or location.stem, def_read_delimited(location, "\t", max_rows))]
    elif engine == "JSON":
        assert location is not None
        table_rows = [(table_hint or location.stem, def_read_json(location, max_rows))]
    elif engine == "JSON_ENDPOINT":
        rows, signature, origin = def_read_json_endpoint(source, config, max_rows)
        table_rows = [(table_hint or default_name, rows)]
    elif engine == "PARQUET":
        assert location is not None
        table_rows = [(table_hint or location.stem, def_read_parquet(location, max_rows))]
    elif engine == "SQLITE":
        assert location is not None
        table_rows = def_read_sqlite(location, table_hint, max_rows)
    else:
        assert location is not None
        table_rows = def_read_duckdb(location, table_hint, max_rows)
    if engine != "JSON_ENDPOINT":
        assert location is not None
        signature = def_source_signature(location)
    tables = []
    for table_name, rows in table_rows:
        if len(rows) < 3:
            continue
        rows = def_apply_missing_value_policy(rows)
        asset_class = str(vdf_evidence.get("assetClass", "OTHER")).upper()
        adjusted_field = str(vdf_evidence.get("adjustedPriceField", ""))
        if asset_class in {"STOCK", "EQUITY", "ETF", "STOCK_INDEX"}:
            if not rows or adjusted_field not in rows[0]:
                raise ValueError(f"ADJUSTED_PRICE_FIELD_MISSING:{adjusted_field}")
            rows = def_apply_talib_indicators(rows, adjusted_field, source.get("technicalIndicators", []))
        fingerprint = def_sha256_text(f"{signature}|{engine}|{table_name}|{len(rows)}")
        table = def_build_catalog_table(table_name, origin, alias, rows, fingerprint)
        if asset_class in {"STOCK", "EQUITY", "ETF", "STOCK_INDEX"}:
            table["numeric"] = [field for field in table["numeric"] if not PRICE_PATTERN.search(field) or ADJUSTED_PRICE_PATTERN.fullmatch(field)]
            if adjusted_field not in table["numeric"]:
                raise ValueError("ADJUSTED_PRICE_NOT_NUMERIC")
        table["runtime"].update({
            "sourceId": source_id, "engine": engine, "refreshStatus": "UPDATED",
            "vdfContractId": vdf_evidence.get("contractId"), "vdfAuthorized": True,
            "assetClass": asset_class, "adjustedPriceField": adjusted_field or None,
            "taLibEvidence": vdf_evidence.get("taLibEvidence")
            ,"missingValuePolicy": {"price": "PREVIOUS_TRADING_DAY", "volume": "ZERO_NO_CARRY"}
        })
        tables.append(table)
    return tables, signature


# def 05 CONFIGURATION, CACHE AND REFRESH
def def_default_config(package_root: Path) -> dict[str, Any]:
    return {
        "schema": "VIA-VAP-RUNTIME-CONFIG/1.0",
        "version": APP_VERSION,
        "host": DEFAULT_HOST,
        "port": DEFAULT_PORT,
        "openBrowser": True,
        "syncConnectOnStart": True,
        "maxRows": DEFAULT_MAX_ROWS,
        "maxBodyBytes": DEFAULT_MAX_BODY_BYTES,
        "requestTimeoutSeconds": DEFAULT_REQUEST_TIMEOUT_SECONDS,
        "allowedRoots": [str(package_root), str(Path.home() / "Downloads")],
        "allowedHosts": [],
        "vdfGateway": {"required": True, "manifest": "{PACKAGE_ROOT}/config/vdf_connection_manifest.json"},
        "imageDirectory": DEFAULT_IMAGE_DIRECTORY,
        "sources": [],
    }


def def_load_config(path: Path) -> dict[str, Any]:
    root = def_package_root()
    config = def_default_config(root)
    supplied = def_load_json(path, {})
    if not isinstance(supplied, dict):
        raise ValueError("CONFIG_OBJECT_REQUIRED")
    config.update(supplied)
    token_map = {"{PACKAGE_ROOT}": str(root), "{USER_HOME}": str(Path.home())}
    def expand_tokens(value: Any) -> Any:
        if not isinstance(value, str):
            return value
        for token, replacement in token_map.items():
            value = value.replace(token, replacement)
        return value
    config["allowedRoots"] = [expand_tokens(item) for item in config.get("allowedRoots", [])]
    for source in config.get("sources", []):
        source["location"] = expand_tokens(source.get("location", ""))
    config["host"] = str(config.get("host", DEFAULT_HOST))
    if config["host"] not in {"127.0.0.1", "localhost", "::1"}:
        raise PermissionError("RUNTIME_MUST_BIND_LOOPBACK")
    config["port"] = int(config.get("port", DEFAULT_PORT))
    if not 1024 <= config["port"] <= 65535:
        raise ValueError("PORT_OUT_OF_RANGE")
    config["maxRows"] = max(3, min(int(config.get("maxRows", DEFAULT_MAX_ROWS)), 100_000))
    config["maxBodyBytes"] = max(1024, min(int(config.get("maxBodyBytes", DEFAULT_MAX_BODY_BYTES)), 100 * 1024 * 1024))
    config["sources"] = [source for source in config.get("sources", []) if source.get("enabled", True)]
    return config


@dataclass
class RefreshResult:
    request_id: str
    mode: str
    tables: list[dict[str, Any]]
    errors: list[dict[str, str]]
    started_at: str
    completed_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema": "VIA-VAP-REFRESH-RESPONSE/1.0",
            "version": APP_VERSION,
            "requestId": self.request_id,
            "mode": self.mode,
            "tables": self.tables,
            "errors": self.errors,
            "startedAt": self.started_at,
            "completedAt": self.completed_at,
            "status": "UPDATED" if self.tables else "RESPONSE_REJECTED",
            "readOnly": True,
        }


class CatalogRuntime:
    def __init__(self, package_root: Path, config_path: Path):
        self.package_root = package_root.resolve()
        self.config_path = config_path.resolve()
        self.config = def_load_config(self.config_path)
        self.vdf_manifest = def_load_vdf_manifest(self.package_root, self.config)
        self.cache_path = self.package_root / DEFAULT_CACHE_RELATIVE_PATH
        self.checkpoint_path = self.package_root / DEFAULT_CHECKPOINT_RELATIVE_PATH
        self.image_root = def_resolve_allowed_path(
            str(self.package_root / self.config.get("imageDirectory", DEFAULT_IMAGE_DIRECTORY)),
            [str(self.package_root)],
            require_exists=False,
        )
        self.image_root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.catalog = def_load_json(self.cache_path, {}).get("tables", [])
        self.last_refresh = def_load_json(self.checkpoint_path, {})

    def health(self) -> dict[str, Any]:
        optional = {
            name: bool(def_import_optional(name)) for name in ("duckdb", "polars", "pyarrow", "talib", "numpy")
        }
        return {
            "schema": RUNTIME_SCHEMA,
            "version": APP_VERSION,
            "status": "READY",
            "host": self.config["host"],
            "port": self.config["port"],
            "readOnly": True,
            "catalogTables": len(self.catalog),
            "optionalLibraries": optional,
            "configFingerprint": def_config_fingerprint(self.config),
            "lastRefresh": self.last_refresh.get("completedAt"),
            "vdfGateway": {"status": "READY", "schema": self.vdf_manifest.get("schema"), "authorizedConnections": len(self.vdf_manifest.get("connections", []))},
        }

    def refresh(self, request_id: str, targets: list[str] | None = None, mode: str = "INCREMENTAL") -> RefreshResult:
        started = def_now_iso()
        mode = mode.upper()
        if mode not in {"INCREMENTAL", "FULL"}:
            raise ValueError("REFRESH_MODE_INVALID")
        targets_set = {str(item) for item in (targets or []) if str(item)}
        tables: list[dict[str, Any]] = []
        errors: list[dict[str, str]] = []
        with self.lock:
            prior_by_source: dict[str, list[dict[str, Any]]] = {}
            for table in self.catalog:
                source_id = str(table.get("runtime", {}).get("sourceId", "UNKNOWN"))
                prior_by_source.setdefault(source_id, []).append(table)
            selected_sources: list[tuple[str, dict[str, Any]]] = []
            for source in self.config.get("sources", []):
                source_id = def_safe_identifier(source.get("id", source.get("alias", "UNKNOWN")), "UNKNOWN")
                if targets_set and "ALL" not in targets_set and source_id not in targets_set and str(source.get("alias", "")) not in targets_set:
                    continue
                selected_sources.append((source_id, source))
            selected_ids = {item[0] for item in selected_sources}
            if targets_set and "ALL" not in targets_set:
                for source_id, previous in prior_by_source.items():
                    if source_id not in selected_ids:
                        tables.extend(previous)
            prior_signatures = dict(self.last_refresh.get("sourceSignatures", {}))
            next_signatures = dict(prior_signatures) if targets_set and "ALL" not in targets_set else {}
            for source_id, source in selected_sources:
                try:
                    evidence = def_vdf_evidence(source, self.vdf_manifest)
                    change_token = def_source_change_token(source, self.config)
                    previous = prior_by_source.get(source_id, [])
                    if mode == "INCREMENTAL" and change_token and prior_signatures.get(source_id) == change_token and previous:
                        reused = json.loads(json.dumps(previous))
                        for table in reused:
                            table.setdefault("runtime", {})["refreshStatus"] = "UNCHANGED"
                        tables.extend(reused)
                        next_signatures[source_id] = change_token
                        continue
                    fresh, source_signature = def_source_tables(source, self.config, evidence)
                    if mode == "INCREMENTAL" and prior_signatures.get(source_id) == source_signature and previous:
                        reused = json.loads(json.dumps(previous))
                        for table in reused:
                            table.setdefault("runtime", {})["refreshStatus"] = "UNCHANGED"
                        tables.extend(reused)
                    else:
                        tables.extend(fresh)
                    next_signatures[source_id] = source_signature
                except Exception as error:  # fail one source without hiding the evidence
                    errors.append({"source": source_id, "type": type(error).__name__, "message": str(error)})
                    if prior_by_source.get(source_id):
                        retained = json.loads(json.dumps(prior_by_source[source_id]))
                        for table in retained:
                            table.setdefault("runtime", {})["refreshStatus"] = "ERROR_CACHED"
                        tables.extend(retained)
            unique: dict[str, dict[str, Any]] = {}
            for table in tables:
                source_id = table.get("runtime", {}).get("sourceId", "UNKNOWN")
                unique[f"{source_id}|{table['name']}"] = table
            tables = list(unique.values())
            self.catalog = tables
            completed = def_now_iso()
            cache = {
                "schema": CATALOG_SCHEMA,
                "version": APP_VERSION,
                "generatedAt": completed,
                "requestId": request_id,
                "tables": tables,
            }
            checkpoint = {
                "schema": "VIA-VAP-REFRESH-CHECKPOINT/1.0",
                "version": APP_VERSION,
                "requestId": request_id,
                "mode": mode,
                "startedAt": started,
                "completedAt": completed,
                "tableCount": len(tables),
                "errorCount": len(errors),
                "tableFingerprints": {
                    table["name"]: table["source_fingerprint"] for table in tables
                },
                "sourceSignatures": next_signatures,
            }
            def_atomic_write_json(self.cache_path, cache)
            def_atomic_write_json(self.checkpoint_path, checkpoint)
            self.last_refresh = checkpoint
        return RefreshResult(request_id, mode, tables, errors, started, completed)

    def save_image(self, payload: dict[str, Any]) -> dict[str, Any]:
        schema = str(payload.get("schema", ""))
        image_id = def_safe_identifier(payload.get("id"), "VAP-IMG")
        svg_markup = str(payload.get("svgMarkup", ""))
        chart_record = payload.get("chartRecord")
        fingerprint = str(payload.get("fingerprint", ""))
        if schema != IMAGE_SCHEMA or not isinstance(chart_record, dict):
            raise ValueError("IMAGE_CONTRACT_INVALID")
        if not svg_markup.lstrip().startswith("<svg") or FORBIDDEN_SVG_PATTERN.search(svg_markup):
            raise ValueError("SVG_SECURITY_GATE_REJECTED")
        computed = def_sha256_text(def_canonical_json({
            "schema": IMAGE_SCHEMA,
            "chartRecord": chart_record,
            "svgMarkup": svg_markup,
        }))
        if fingerprint and fingerprint != computed:
            raise ValueError("IMAGE_FINGERPRINT_MISMATCH")
        fingerprint = computed
        svg_path = self.image_root / f"{image_id}.svg"
        json_path = self.image_root / f"{image_id}.json"
        event_path = self.image_root / "image_registry.jsonl"
        if svg_path.exists() or json_path.exists():
            existing = def_load_json(json_path, {})
            if existing.get("fingerprint") == fingerprint:
                return {"status": "EXISTS", "id": image_id, "fingerprint": fingerprint}
            raise FileExistsError("IMAGE_ID_COLLISION")
        metadata = {
            "schema": IMAGE_SCHEMA,
            "version": APP_VERSION,
            "id": image_id,
            "fingerprint": fingerprint,
            "chartRecord": chart_record,
            "savedAt": def_now_iso(),
            "svgFile": svg_path.name,
            "policy": "APPEND_ONLY_IMMUTABLE",
        }
        def_atomic_write_text(svg_path, svg_markup)
        def_atomic_write_json(json_path, metadata)
        with event_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(def_canonical_json({
                "event": "IMAGE_SAVED", "id": image_id, "fingerprint": fingerprint, "at": metadata["savedAt"]
            }) + "\n")
        return {"status": "SAVED", "id": image_id, "fingerprint": fingerprint, "metadata": metadata}

    def image_manifest(self) -> list[dict[str, Any]]:
        records = []
        for path in sorted(self.image_root.glob("VAP-IMG-*.json")):
            record = def_load_json(path, {})
            if record:
                records.append(record)
        return records


# def 06 HTTP BRIDGE
def def_origin_allowed(origin: str | None, host: str, port: int) -> bool:
    if origin in (None, "", "null"):
        return True
    return origin in {f"http://{host}:{port}", f"http://localhost:{port}", f"http://127.0.0.1:{port}"}


def def_make_handler(runtime: CatalogRuntime):
    class VAPRequestHandler(BaseHTTPRequestHandler):
        server_version = "VAPRuntime/1.0"

        def log_message(self, format_string: str, *args: Any) -> None:
            logging.info("http", extra={"messageArgs": format_string % args, "client": self.client_address[0]})

        def _cors_headers(self) -> None:
            origin = self.headers.get("Origin")
            if def_origin_allowed(origin, runtime.config["host"], runtime.config["port"]):
                self.send_header("Access-Control-Allow-Origin", origin or "null")
                self.send_header("Vary", "Origin")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "SAMEORIGIN")

        def _json(self, status: int, payload: Any) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self._cors_headers()
            self.end_headers()
            self.wfile.write(body)

        def _error(self, status: int, code: str, message: str) -> None:
            self._json(status, {"schema": "VIA-VAP-ERROR/1.0", "code": code, "message": message, "at": def_now_iso()})

        def _read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > runtime.config["maxBodyBytes"]:
                raise ValueError("REQUEST_BODY_SIZE_INVALID")
            raw = self.rfile.read(length)
            payload = json.loads(raw.decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("REQUEST_JSON_OBJECT_REQUIRED")
            return payload

        def do_OPTIONS(self) -> None:
            origin = self.headers.get("Origin")
            if not def_origin_allowed(origin, runtime.config["host"], runtime.config["port"]):
                self._error(HTTPStatus.FORBIDDEN, "ORIGIN_REJECTED", str(origin))
                return
            self.send_response(HTTPStatus.NO_CONTENT)
            self._cors_headers()
            self.end_headers()

        def do_GET(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == "/api/health":
                self._json(HTTPStatus.OK, runtime.health())
                return
            if parsed.path == "/api/catalog":
                self._json(HTTPStatus.OK, {"schema": CATALOG_SCHEMA, "version": APP_VERSION, "tables": runtime.catalog})
                return
            if parsed.path == "/api/images":
                self._json(HTTPStatus.OK, {"schema": IMAGE_SCHEMA, "records": runtime.image_manifest()})
                return
            if parsed.path == "/":
                self.send_response(HTTPStatus.TEMPORARY_REDIRECT)
                self.send_header("Location", "/" + DEFAULT_UI_RELATIVE_PATH)
                self._cors_headers()
                self.end_headers()
                return
            relative = urllib.parse.unquote(parsed.path.lstrip("/"))
            try:
                target = def_resolve_allowed_path(str(runtime.package_root / relative), [str(runtime.package_root)])
            except (PermissionError, FileNotFoundError):
                self._error(HTTPStatus.NOT_FOUND, "STATIC_FILE_NOT_FOUND", relative)
                return
            if not target.is_file():
                self._error(HTTPStatus.NOT_FOUND, "STATIC_FILE_NOT_FOUND", relative)
                return
            content = target.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", mimetypes.guess_type(target.name)[0] or "application/octet-stream")
            self.send_header("Content-Length", str(len(content)))
            self._cors_headers()
            self.end_headers()
            self.wfile.write(content)

        def do_POST(self) -> None:
            origin = self.headers.get("Origin")
            if not def_origin_allowed(origin, runtime.config["host"], runtime.config["port"]):
                self._error(HTTPStatus.FORBIDDEN, "ORIGIN_REJECTED", str(origin))
                return
            try:
                payload = self._read_json()
                if self.path == "/api/refresh":
                    request_id = def_safe_identifier(payload.get("requestId"), "VAP-REFRESH")
                    targets = payload.get("targets") if isinstance(payload.get("targets"), list) else []
                    result = runtime.refresh(request_id, targets, str(payload.get("mode", "INCREMENTAL")))
                    self._json(HTTPStatus.OK, result.as_dict())
                    return
                if self.path == "/api/images":
                    self._json(HTTPStatus.CREATED, runtime.save_image(payload))
                    return
                self._error(HTTPStatus.NOT_FOUND, "API_NOT_FOUND", self.path)
            except (ValueError, PermissionError, FileNotFoundError, FileExistsError) as error:
                self._error(HTTPStatus.BAD_REQUEST, type(error).__name__.upper(), str(error))
            except Exception as error:
                logging.exception("request failed")
                self._error(HTTPStatus.INTERNAL_SERVER_ERROR, "RUNTIME_ERROR", str(error))

    return VAPRequestHandler


# def 07 LOGGING, SERVER AND CLI
class JsonLineFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return def_canonical_json({
            "at": def_now_iso(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        })


def def_setup_logging(package_root: Path) -> None:
    path = package_root / DEFAULT_LOG_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(JsonLineFormatter())
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter("[VAP] %(levelname)s · %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[handler, console], force=True)


def def_write_runtime_state(runtime: CatalogRuntime) -> None:
    ready = runtime.package_root / DEFAULT_READY_RELATIVE_PATH
    pid = runtime.package_root / DEFAULT_PID_RELATIVE_PATH
    def_atomic_write_json(ready, {**runtime.health(), "readyAt": def_now_iso(), "url": f"http://{runtime.config['host']}:{runtime.config['port']}/"})
    def_atomic_write_text(pid, str(os.getpid()) + "\n")


def def_run_self_test(runtime: CatalogRuntime) -> dict[str, Any]:
    checks = {
        "loopback": runtime.config["host"] in {"127.0.0.1", "localhost", "::1"},
        "configSchema": runtime.config.get("schema") == "VIA-VAP-RUNTIME-CONFIG/1.0",
        "allowedRoots": bool(runtime.config.get("allowedRoots")),
        "imageDirectory": runtime.image_root.exists(),
        "readOnlyEngines": ALLOWED_ENGINES == {"CSV", "TSV", "JSON", "JSON_ENDPOINT", "PARQUET", "SQLITE", "DUCKDB"},
        "sqlWriteGuard": bool(FORBIDDEN_SQL_PATTERN.search("UPDATE prices SET close=1")),
        "vdfGateway": runtime.vdf_manifest.get("schema") == VDF_SCHEMA,
    }
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks, "health": runtime.health()}


def def_parse_args() -> argparse.Namespace:
    root = def_package_root()
    parser = argparse.ArgumentParser(description="VeritasAutoPlot v025 local read-only runtime")
    parser.add_argument("--config", default=str(root / DEFAULT_CONFIG_RELATIVE_PATH))
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--once-refresh", action="store_true")
    parser.add_argument("--run-self-test", action="store_true")
    parser.add_argument("--sync-connect", action="store_true")
    return parser.parse_args()


def def_main() -> int:
    args = def_parse_args()
    root = def_package_root()
    def_setup_logging(root)
    try:
        runtime = CatalogRuntime(root, Path(args.config))
        if args.host:
            runtime.config["host"] = args.host
        if args.port:
            runtime.config["port"] = args.port
        if runtime.config["host"] not in {"127.0.0.1", "localhost", "::1"}:
            raise PermissionError("RUNTIME_MUST_BIND_LOOPBACK")
        if args.run_self_test:
            result = def_run_self_test(runtime)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result["status"] == "PASS" else 2
        if args.once_refresh:
            result = runtime.refresh("VAP-REFRESH-CLI-" + str(int(time.time())), [], "INCREMENTAL")
            print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))
            return 0 if result.tables or not runtime.config.get("sources") else 3
        if args.sync_connect or runtime.config.get("syncConnectOnStart", True):
            result = runtime.refresh("VAP-SYNC-CONNECT-" + str(int(time.time())), ["ALL"], "INCREMENTAL")
            if runtime.config.get("sources") and not result.tables:
                raise RuntimeError("SYNC_CONNECT_NO_CATALOG_TABLES")
            logging.info("SYNC CONNECT ready · %s tables · %s errors", len(result.tables), len(result.errors))
        handler = def_make_handler(runtime)
        server = ThreadingHTTPServer((runtime.config["host"], runtime.config["port"]), handler)
        def_write_runtime_state(runtime)
        url = f"http://{runtime.config['host']}:{runtime.config['port']}/"
        logging.info("runtime ready at %s", url)
        if runtime.config.get("openBrowser", True) and not args.no_browser:
            threading.Timer(0.7, lambda: webbrowser.open(url)).start()
        try:
            server.serve_forever(poll_interval=0.25)
        except KeyboardInterrupt:
            logging.info("runtime stopped by user")
        finally:
            server.server_close()
        return 0
    except Exception as error:
        logging.exception("runtime startup failed")
        print(f"[VAP] FAIL · {type(error).__name__}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(def_main())
