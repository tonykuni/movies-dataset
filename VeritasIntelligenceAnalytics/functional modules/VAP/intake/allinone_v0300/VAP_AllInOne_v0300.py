#!/usr/bin/env python3
"""VeritasAutoPlot v0300 all-in-one read-only engine and HTML UI bridge."""

from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel bridge; graceful zero-behavior fallback =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve().parent
    for _ in range(5):
        if (_sa_p / "supportive modules").is_dir():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

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
APP_VERSION = "v0300"
RUNTIME_SCHEMA = "VIA-VAP-RUNTIME/1.0"
CATALOG_SCHEMA = "VIA-VAP-CATALOG/1.0"
IMAGE_SCHEMA = "VIA-VAP-GOVERNED-CHART-IMAGE/1.0"
TEMPLATE_SCHEMA = "VIA-VAP-REUSABLE-TEMPLATE/1.0"
VDF_SCHEMA = "VIA-VDF-VAP-CONNECTION-MANIFEST/1.0"
VQG_SCHEMA = "VIA-VQG-VAP-CONNECTION-MANIFEST/1.0"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
DEFAULT_MAX_ROWS = 5000
DEFAULT_MAX_BODY_BYTES = 20 * 1024 * 1024
DEFAULT_REQUEST_TIMEOUT_SECONDS = 20
DEFAULT_UI_RELATIVE_PATH = "VAP_AllInOne_UI_v0300.html"
DEFAULT_CONFIG_RELATIVE_PATH = "VAP_AllInOne_v0300.config.json"
DEFAULT_CACHE_RELATIVE_PATH = "state/catalog_cache.json"
DEFAULT_CHECKPOINT_RELATIVE_PATH = "state/refresh_checkpoint.json"
DEFAULT_IMAGE_DIRECTORY = "output/saved_images"
DEFAULT_TEMPLATE_DIRECTORY = "output/saved_templates"
DEFAULT_CONTEXT_RELATIVE_PATH = "spec/vap_context_ledger_v027.json"
DEFAULT_LOG_RELATIVE_PATH = "logs/vap_runtime_v027.jsonl"
DEFAULT_READY_RELATIVE_PATH = "state/runtime_ready.json"
DEFAULT_PID_RELATIVE_PATH = "state/runtime.pid"
ALLOWED_ENGINES = {"CSV", "TSV", "JSON", "JSON_ENDPOINT", "PARQUET", "SQLITE", "DUCKDB"}
VQG_DATASET_TYPES = {"ACTIVITY", "INDICATOR_RESULT", "SERIES", "RISK_QUALITY", "REPORT_LINKED"}
VQG_MAX_INPUT_ROWS = 5000
VQG_MAX_OUTPUT_ROWS = 100
VQG_MAX_WINDOW = 252
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
    return Path(__file__).resolve().parent


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


def def_load_vqg_manifest(package_root: Path, config: dict[str, Any]) -> dict[str, Any]:
    gateway = dict(config.get("vqgGateway", {}))
    location = str(gateway.get("manifest", "{PACKAGE_ROOT}/config/vqg_connection_manifest.json"))
    location = location.replace("{PACKAGE_ROOT}", str(package_root)).replace("{USER_HOME}", str(Path.home()))
    path = def_resolve_allowed_path(location, config.get("allowedRoots", []))
    manifest = def_load_json(path, {})
    if manifest.get("schema") != VQG_SCHEMA or not isinstance(manifest.get("connections"), list):
        raise ValueError("VQG_CONNECTION_MANIFEST_INVALID")
    return manifest


def def_vqg_evidence(source: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    source_id = str(source.get("id", source.get("alias", "")))
    contract_id = str(source.get("vqgContractId", ""))
    evidence = next(
        (
            item for item in manifest.get("connections", [])
            if str(item.get("sourceId")) == source_id and str(item.get("contractId")) == contract_id
        ),
        None,
    )
    if not evidence or evidence.get("state") != "AUTHORIZED" or not evidence.get("readOnly", False):
        raise PermissionError(f"VQG_AUTHORIZATION_REQUIRED:{source_id}")
    if evidence.get("sourceSystem") != "VQG":
        raise PermissionError(f"VQG_SOURCE_SYSTEM_REQUIRED:{source_id}")
    if str(evidence.get("engine", "")).upper() != str(source.get("engine", "")).upper():
        raise PermissionError(f"VQG_ENGINE_MISMATCH:{source_id}")
    dataset_type = str(evidence.get("datasetType", "")).upper()
    if dataset_type not in VQG_DATASET_TYPES:
        raise PermissionError(f"VQG_DATASET_TYPE_REJECTED:{source_id}")
    limits = dict(evidence.get("limits", {}))
    if (
        int(limits.get("maxInputRows", 0)) > VQG_MAX_INPUT_ROWS
        or int(limits.get("maxOutputRows", 0)) > VQG_MAX_OUTPUT_ROWS
        or int(limits.get("maxWindow", 0)) > VQG_MAX_WINDOW
        or min(int(limits.get("maxInputRows", 0)), int(limits.get("maxOutputRows", 0)), int(limits.get("maxWindow", 0))) <= 0
    ):
        raise PermissionError(f"VQG_LIMITS_REJECTED:{source_id}")
    upstream = dict(evidence.get("upstreamEvidence", {}))
    if not upstream.get("vdfAuthorized") or upstream.get("pricePolicy") != "ADJUSTED_PRICE_ONLY":
        raise PermissionError(f"VQG_UPSTREAM_VDF_ADJUSTED_PRICE_REQUIRED:{source_id}")
    if upstream.get("taLibPolicy") != "CALCULATE_ONLY_NO_FETCH":
        raise PermissionError(f"VQG_TALIB_POLICY_REQUIRED:{source_id}")
    supplied_fingerprint = str(evidence.get("fingerprint", ""))
    fingerprint_payload = {key: value for key, value in evidence.items() if key != "fingerprint"}
    expected_fingerprint = def_sha256_text(def_canonical_json(fingerprint_payload))
    if supplied_fingerprint != expected_fingerprint:
        raise PermissionError(f"VQG_FINGERPRINT_MISMATCH:{source_id}")
    return evidence


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


def def_source_tables(source: dict[str, Any], config: dict[str, Any], source_evidence: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
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
        # VAP is presentation-only. VQG output is accepted as-is: no price repair,
        # no indicator recalculation, no ticker mutation and no silent fill.
        dataset_type = str(source_evidence.get("datasetType", "")).upper()
        fingerprint = def_sha256_text(f"{signature}|{engine}|{table_name}|{len(rows)}")
        table = def_build_catalog_table(table_name, origin, alias, rows, fingerprint)
        semantic_overrides = dict(source_evidence.get("fieldSemantics", {}))
        for field in table["field_semantics"]:
            override = semantic_overrides.get(field["field"])
            if override:
                field.update({
                    "stableId": override.get("stableId", field["id"]),
                    "indicatorId": override.get("indicatorId"),
                    "subject": override.get("subject", field["subject"]),
                    "unit": override.get("unit", field["unit"]),
                    "dataType": override.get("dataType", field["dataType"]),
                    "frequency": override.get("frequency", field["frequency"]),
                    "role": override.get("role", field["role"]),
                    "source": "VQG_MANIFEST",
                })
        if semantic_overrides:
            table["numeric"] = [field for field in table["numeric"] if field in semantic_overrides]
            if not table["numeric"]:
                raise ValueError("VQG_NUMERIC_FIELD_ALLOWLIST_EMPTY")
        table["runtime"].update({
            "sourceId": source_id, "engine": engine, "refreshStatus": "UPDATED",
            "inputAuthority": "VQG", "vqgVerified": True,
            "vqgContractId": source_evidence.get("contractId"),
            "vqgVersion": source_evidence.get("vqgVersion"),
            "vqgDatasetType": dataset_type,
            "vqgLimits": source_evidence.get("limits"),
            "upstreamEvidence": source_evidence.get("upstreamEvidence"),
            "producerInputs": source_evidence.get("producerInputs", []),
            "missingValuePolicy": "PRESERVE_VQG_OUTPUT_NO_VAP_REPAIR",
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
        "formalInputAuthority": "VQG",
        "allowedRoots": [str(package_root), str(Path.home() / "Downloads")],
        "allowedHosts": [],
        "vdfGateway": {"required": True, "manifest": "{PACKAGE_ROOT}/config/vdf_connection_manifest.json"},
        "vqgGateway": {"required": True, "manifest": "{PACKAGE_ROOT}/config/vqg_connection_manifest.json"},
        "imageDirectory": DEFAULT_IMAGE_DIRECTORY,
        "templateDirectory": DEFAULT_TEMPLATE_DIRECTORY,
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
    if config.get("formalInputAuthority") != "VQG":
        raise PermissionError("FORMAL_INPUT_AUTHORITY_MUST_BE_VQG")
    if any(str(source.get("authority", "")).upper() != "VQG" for source in config["sources"]):
        raise PermissionError("NON_VQG_FORMAL_SOURCE_REJECTED")
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
        self.vqg_manifest = def_load_vqg_manifest(self.package_root, self.config)
        self.cache_path = self.package_root / DEFAULT_CACHE_RELATIVE_PATH
        self.checkpoint_path = self.package_root / DEFAULT_CHECKPOINT_RELATIVE_PATH
        self.image_root = def_resolve_allowed_path(
            str(self.package_root / self.config.get("imageDirectory", DEFAULT_IMAGE_DIRECTORY)),
            [str(self.package_root)],
            require_exists=False,
        )
        self.image_root.mkdir(parents=True, exist_ok=True)
        self.template_root = def_resolve_allowed_path(
            str(self.package_root / self.config.get("templateDirectory", DEFAULT_TEMPLATE_DIRECTORY)),
            [str(self.package_root)],
            require_exists=False,
        )
        self.template_root.mkdir(parents=True, exist_ok=True)
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
            "vqgGateway": {"status": "READY", "schema": self.vqg_manifest.get("schema"), "authorizedConnections": len(self.vqg_manifest.get("connections", [])), "formalInput": True},
            "inputAuthority": "VQG_ONLY",
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
                    evidence = def_vqg_evidence(source, self.vqg_manifest)
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

    def save_template(self, payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("schema") != TEMPLATE_SCHEMA or payload.get("policy") != "ROLE_BINDING_NO_EMBEDDED_DATA_VQG_ONLY":
            raise ValueError("TEMPLATE_CONTRACT_INVALID")
        if any(key in payload for key in ("rows", "data", "values", "labels")):
            raise ValueError("TEMPLATE_EMBEDDED_DATA_REJECTED")
        template_id = def_safe_identifier(payload.get("id"), "VAP-TPL")
        fingerprint = str(payload.get("fingerprint", ""))
        canonical_payload = {key: value for key, value in payload.items() if key != "fingerprint"}
        computed = def_sha256_text(def_canonical_json(canonical_payload))
        if fingerprint != computed:
            raise ValueError("TEMPLATE_FINGERPRINT_MISMATCH")
        target = self.template_root / f"{template_id}-{fingerprint[:12]}.json"
        if target.exists():
            return {"status": "EXISTS", "id": template_id, "fingerprint": fingerprint}
        def_atomic_write_json(target, payload)
        with (self.template_root / "template_registry.jsonl").open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(def_canonical_json({"event": "TEMPLATE_SAVED", "id": template_id, "fingerprint": fingerprint, "at": def_now_iso()}) + "\n")
        return {"status": "SAVED", "id": template_id, "fingerprint": fingerprint}

    def template_manifest(self) -> list[dict[str, Any]]:
        records = []
        for path in sorted(self.template_root.glob("VAP-TPL-*.json")):
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
            if parsed.path == "/api/templates":
                self._json(HTTPStatus.OK, {"schema": TEMPLATE_SCHEMA, "records": runtime.template_manifest()})
                return
            if parsed.path == "/api/functions":
                self._json(HTTPStatus.OK, EMBEDDED_FUNCTION_INVENTORY)
                return
            if parsed.path == "/api/spec":
                self._json(HTTPStatus.OK, {
                    "schema": "VIA-VAP-ALL-IN-ONE-SPEC-BUNDLE/1.0",
                    "version": APP_VERSION,
                    "systemSpec": EMBEDDED_SYSTEM_SPEC,
                    "chartRegistry": EMBEDDED_CHART_REGISTRY,
                    "templateRegistry": EMBEDDED_TEMPLATE_REGISTRY,
                    "legacyChartLibrary": EMBEDDED_LEGACY_CHART_LIBRARY,
                    "legacySpec": EMBEDDED_LEGACY_SPEC,
                })
                return
            if parsed.path == "/api/context":
                self._json(HTTPStatus.OK, EMBEDDED_CONTEXT_LEDGER)
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
                if self.path == "/api/templates":
                    self._json(HTTPStatus.CREATED, runtime.save_template(payload))
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
        "vqgGateway": runtime.vqg_manifest.get("schema") == VQG_SCHEMA,
        "vqgOnlyFormalInput": runtime.config.get("formalInputAuthority") == "VQG",
        "contextLedger": def_load_json(runtime.package_root / DEFAULT_CONTEXT_RELATIVE_PATH, {}).get("version") == APP_VERSION,
    }
    return {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks, "health": runtime.health()}


def def_parse_args() -> argparse.Namespace:
    root = def_package_root()
    parser = argparse.ArgumentParser(description="VeritasAutoPlot v027 local read-only runtime")
    parser.add_argument("--config", default=str(root / DEFAULT_CONFIG_RELATIVE_PATH))
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--once-refresh", action="store_true")
    parser.add_argument("--run-self-test", action="store_true")
    parser.add_argument("--sync-connect", action="store_true")
    parser.add_argument("--function-inventory", action="store_true")
    return parser.parse_args()


def def_main() -> int:
    args = def_parse_args()
    root = def_package_root()
    if args.function_inventory:
        print(json.dumps(EMBEDDED_FUNCTION_INVENTORY, ensure_ascii=False, indent=2))
        return 0
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



# def 08 EMBEDDED SSOT, LEGACY LINEAGE AND UNIFIED OVERRIDES
EMBEDDED_RUNTIME_CONFIG = {'schema': 'VIA-VAP-RUNTIME-CONFIG/1.0', 'version': 'v0300', 'host': '127.0.0.1', 'port': 8765, 'openBrowser': True, 'syncConnectOnStart': True, 'maxRows': 5000, 'maxBodyBytes': 20971520, 'requestTimeoutSeconds': 20, 'formalInputAuthority': 'VQG', 'allowedRoots': ['{PACKAGE_ROOT}', '{USER_HOME}/Downloads'], 'allowedHosts': [], 'vdfGateway': {'required': True, 'manifest': 'embedded://vdf_connection_manifest'}, 'vqgGateway': {'required': True, 'manifest': 'embedded://vqg_connection_manifest'}, 'imageDirectory': 'output/saved_images', 'templateDirectory': 'output/saved_templates', 'sources': [{'id': 'VAP-DEMO-VQG-ACTIVITY', 'vqgContractId': 'VQG-DEMO-ACTIVITY-v1', 'authority': 'VQG', 'alias': 'VQG_ACTIVITY', 'engine': 'CSV', 'location': '{PACKAGE_ROOT}/state/embedded/vqg_demo_activity.csv', 'table': 'vqg_activity', 'enabled': True, 'maxRows': 5000}], 'disabledSourceExamples': [{'id': 'VQG-PARQUET-EXAMPLE', 'vqgContractId': 'VQG-OUTPUT-v1', 'authority': 'VQG', 'alias': 'VQG_PARQUET', 'engine': 'PARQUET', 'location': '%USERPROFILE%/Downloads/vqg_result.parquet', 'enabled': False}, {'id': 'VQG-SQLITE-EXAMPLE', 'vqgContractId': 'VQG-OUTPUT-v1', 'authority': 'VQG', 'alias': 'VQG_SQLITE', 'engine': 'SQLITE', 'location': '%USERPROFILE%/Downloads/vqg.sqlite', 'enabled': False}, {'id': 'VQG-DUCKDB-EXAMPLE', 'vqgContractId': 'VQG-OUTPUT-v1', 'authority': 'VQG', 'alias': 'VQG_DUCKDB', 'engine': 'DUCKDB', 'location': '%USERPROFILE%/Downloads/vqg.duckdb', 'enabled': False}]}
EMBEDDED_VDF_MANIFEST = {'schema': 'VIA-VDF-VAP-CONNECTION-MANIFEST/1.0', 'version': 'v027', 'policy': 'VDF_AUTHORIZED_READ_ONLY_FAIL_CLOSED', 'connections': [{'contractId': 'VDF-DEMO-MARKET-v1', 'sourceId': 'VAP-DEMO-MARKET', 'state': 'AUTHORIZED', 'readOnly': True, 'engine': 'CSV', 'assetClass': 'STOCK_INDEX', 'sourceSystem': 'VDF_DEMO_EXPORT', 'adjustedPriceField': 'adjClose', 'volumeField': 'volume', 'splitAdjustedVolume': True, 'taLibEvidence': {'engine': 'TA-Lib', 'status': 'PASS', 'priceInput': 'adjClose', 'volumeInput': 'splitAdjustedVolume'}, 'fingerprint': 'd65309e49fe7384a21a67809388a0c234a41e7456bcf794ee3d74c6dc507ddfa', 'asofPolicy': 'SOURCE_TIMESTAMP', 'authorizedAt': '2026-08-31T00:00:00.000Z'}], 'stockConnectionTemplate': {'contractId': 'VDF-STOCK-ADJ-TALIB-v1', 'sourceId': 'REPLACE_WITH_SOURCE_ID', 'state': 'DRAFT', 'readOnly': True, 'engine': 'PARQUET', 'assetClass': 'STOCK', 'sourceSystem': 'VDF', 'adjustedPriceField': 'adjClose', 'volumeField': 'volume', 'splitAdjustedVolume': True, 'taLibEvidence': {'engine': 'TA-Lib', 'status': 'PENDING', 'priceInput': 'adjClose', 'volumeInput': 'splitAdjustedVolume'}}}
EMBEDDED_VQG_MANIFEST = {'schema': 'VIA-VQG-VAP-CONNECTION-MANIFEST/1.0', 'version': 'v027', 'policy': 'VQG_ONLY_READ_ONLY_FAIL_CLOSED', 'connections': [{'contractId': 'VQG-DEMO-ACTIVITY-v1', 'sourceId': 'VAP-DEMO-VQG-ACTIVITY', 'state': 'AUTHORIZED', 'readOnly': True, 'engine': 'CSV', 'sourceSystem': 'VQG', 'vqgVersion': 'v0104', 'datasetType': 'ACTIVITY', 'producerInputs': ['VDF', 'VRN'], 'limits': {'maxInputRows': 5000, 'maxOutputRows': 100, 'maxWindow': 252}, 'xField': 'date', 'fieldSemantics': {'date': {'stableId': 'VQG.FIELD.DATE', 'subject': 'Observation Date', 'unit': 'Date', 'dataType': 'Date', 'frequency': 'MONTHLY', 'role': 'X_TIME'}, 'net_volume': {'stableId': 'VQG.FACTOR.NET_VOLUME', 'subject': 'Net Volume Ex Day Trade', 'unit': 'Shares', 'dataType': 'Integer', 'frequency': 'MONTHLY', 'role': 'LEFT_VALUE'}, 'net_turnover': {'stableId': 'VQG.FACTOR.NET_TURNOVER', 'subject': 'Net Turnover Ex Day Trade', 'unit': 'TWD', 'dataType': 'Currency', 'frequency': 'MONTHLY', 'role': 'RIGHT_VALUE'}}, 'upstreamEvidence': {'vdfAuthorized': True, 'vrnAccepted': True, 'pricePolicy': 'ADJUSTED_PRICE_ONLY', 'volumePolicy': 'EX_DAYTRADE_ZERO_NO_CARRY', 'taLibPolicy': 'CALCULATE_ONLY_NO_FETCH', 'calendarVerified': True}, 'fingerprint': '98aa865fc194b7cb1dd8e7b6f81c52898a0c4088da88dd0288af78b1a205005d', 'authorizedAt': '2026-11-04T00:00:00.000Z'}], 'connectionTemplate': {'contractId': 'VQG-OUTPUT-v1', 'sourceId': 'REPLACE_WITH_SOURCE_ID', 'state': 'DRAFT', 'readOnly': True, 'engine': 'PARQUET', 'sourceSystem': 'VQG', 'vqgVersion': 'v0104', 'datasetType': 'SERIES', 'producerInputs': ['VDF', 'VRN'], 'limits': {'maxInputRows': 5000, 'maxOutputRows': 100, 'maxWindow': 252}, 'upstreamEvidence': {'vdfAuthorized': True, 'vrnAccepted': True, 'pricePolicy': 'ADJUSTED_PRICE_ONLY', 'volumePolicy': 'EX_DAYTRADE_ZERO_NO_CARRY', 'taLibPolicy': 'CALCULATE_ONLY_NO_FETCH', 'calendarVerified': True}}}
EMBEDDED_CONTEXT_LEDGER = {'schema': 'VIA-VAP-CONTEXT-LEDGER/1.0', 'version': 'v027', 'specVersion': '1.24.0', 'authority': 'LATEST_EXPLICIT_REQUIREMENT_WITH_APPEND_ONLY_LINEAGE', 'scope': 'All VAP requirements available from the consolidated conversation record, the v004-v025 Workbench changelog, the uploaded VAP Markdown record, and the v025 complete package', 'sourceRecords': [{'id': 'VAP-CTX-SRC-001', 'name': 'Uploaded VAP Conversation Markdown', 'file': '貼上的 Markdown (1)(20260830-160415).md', 'sha256': 'f28b6eb064c217fd520b121cb102543fa77e7de6961e3dc39b45621643cf5b1f', 'coverage': ['MacroMicro dual-axis', 'VAP pipeline', '51 data rules', '25 criteria', 'Connect contracts', 'Builder UX', 'collision', 'stack height', 'Seaborn and Plotly']}, {'id': 'VAP-CTX-SRC-002', 'name': 'VAP Workbench v025', 'file': 'VAP_Workbench_v025.html', 'sha256': 'efb92344aa1f5545218593a8128e7197c1f92df3663db0124e2d1313c29c103c', 'coverage': ['v004-v025 changelog', '40 canonical charts', '5 composite recipes', '136 diagnostics', '72 UAT definitions']}, {'id': 'VAP-CTX-SRC-003', 'name': 'VAP v025 Complete System Package', 'file': 'VAP_v025_Complete_System_Package.zip', 'sha256': '7ef8aee3e171c61656f53da3393f2ba47c5e180d20b73a9c0df7513d79c1bdc4', 'coverage': ['PowerShell', 'Python Runtime', 'VDF', 'Adjusted Price', 'TA-Lib', 'saved images', 'tests', 'manifest']}, {'id': 'VAP-CTX-SRC-004', 'name': 'Consolidated Conversation Context', 'file': 'conversation-context', 'coverage': ['v013-v019 delivery decisions', 'user corrections', 'latest system-package and ZIP requests']}], 'metrics': {'canonicalCharts': 40, 'compositeRecipes': 5, 'managedPlotCapabilities': 45, 'physicalYAxisMaximum': 2, 'axisIntervals': 4, 'axisTicks': 5, 'axisStepFamily': [1.25, 2.5, 5, 10], 'iconSeeds': 12, 'emojiSeeds': 16, 'lineageVersions': 24, 'capabilityGroups': 28, 'resolvedConflicts': 12}, 'lineage': [{'version': 'v004', 'decision': 'Bar 92/8、K 線紅漲綠跌與成交量同色'}, {'version': 'v005', 'decision': 'Seaborn 定性色盤與金融語意色優先'}, {'version': 'v006', 'decision': 'HTML Template 版本、SHA-256 與 Sandbox 預覽'}, {'version': 'v007', 'decision': '確定性 Full Test、UAT 與 Fail-Closed Gate'}, {'version': 'v008', 'decision': '一鍵 Test／Debug／Activate 與 Bundled Plotly'}, {'version': 'v009', 'decision': '單圖與共軸堆圖 HTML／PNG／PDF 輸出'}, {'version': 'v010', 'decision': '外部 SSOT Intake、Data Bridge 與 Append-Only Ledger'}, {'version': 'v011', 'decision': '8 種統計擴充與 Seaborn 視覺語法'}, {'version': 'v012', 'decision': '36 張 Canonical 圖的 SVG／Plotly 雙引擎'}, {'version': 'v013', 'decision': '圖型優先流程、真正單軸與左右獨立規格'}, {'version': 'v014', 'decision': '雙軸 4 間隔／5 刻度與合法步長硬鎖'}, {'version': 'v015', 'decision': '40 張 Canonical 圖、官方 Seaborn 色盤與 220→20 熱圖'}, {'version': 'v016', 'decision': '自動路由、互動量測、右鍵工具與 40 張結構快照'}, {'version': 'v017', 'decision': '資料轉換、技術疊圖、異常值、參考線與市場時差'}, {'version': 'v018', 'decision': '可見英文 Title Case 與技術識別字保護'}, {'version': 'v019', 'decision': 'Icon／Emoji／Visual Preset／Template Management'}, {'version': 'v020', 'decision': '確定性 Template Candidate Diff／Session Rollback'}, {'version': 'v021', 'decision': '欄位主詞／單位／資料類型與治理圖片保存／載回／堆圖'}, {'version': 'v022', 'decision': '5 個合成 Recipe、多序列雙實體軸、ASOF 與 Snap'}, {'version': 'v023', 'decision': 'Plotly Dashboard User Journey、連線真實狀態與可收參數欄'}, {'version': 'v024', 'decision': 'Python Runtime、VDF、Adjusted Price、TA-Lib 與 PowerShell 啟動'}, {'version': 'v025', 'decision': 'MacroMicro 互動基準、區間／頻率／數值模式與 Bookmark'}, {'version': 'v026', 'decision': '歷史對話、功能、衝突解析、規格與測試證據單一收斂'}, {'version': 'v027', 'decision': 'VQG 唯讀正式輸入、角色模板自動換資料、共軸堆圖與多圖 Dashboard'}], 'capabilities': [{'id': 'INGEST', 'scope': 'VQG 授權清單與 CSV／TSV／JSON／Endpoint／Parquet／SQLite／DuckDB 唯讀 Adapter；VDF／VRN 為上游證據', 'state': 'IMPLEMENTED'}, {'id': 'VQG_GATE', 'scope': 'VDF／VRN → VQG → VAP；Fingerprint、5000／100／252 限制、來源證據與禁止回寫', 'state': 'IMPLEMENTED'}, {'id': 'SEMANTIC', 'scope': '資料庫／資料表／欄位主詞、單位、資料類型、角色、頻率與彙總', 'state': 'IMPLEMENTED'}, {'id': 'STOCK_GATE', 'scope': '股票／ETF／股票指數只接受 Adjusted Price；TA-Lib 證據必填', 'state': 'IMPLEMENTED'}, {'id': 'MISSING_DATA', 'scope': 'VAP 保留 VQG 缺值輸出且不靜默補值；上游政策證據為價格前一交易日、扣當沖量值 0 且禁止 Carry', 'state': 'IMPLEMENTED'}, {'id': 'MARKET_TIME', 'scope': '美股 T 日映射下一個台股交易日；No-Future ASOF', 'state': 'IMPLEMENTED'}, {'id': 'SINGLE_DUAL', 'scope': '單軸或雙軸，左右系列、圖形、名稱、單位、線寬、透明度可獨立設定', 'state': 'IMPLEMENTED'}, {'id': 'AXIS_LOCK', 'scope': '左右各 4 間隔／5 刻度、相同刻度數、極值覆蓋與小數位一致', 'state': 'IMPLEMENTED'}, {'id': 'CANONICAL', 'scope': '40 張固定 Canonical 圖碼，Append-Only 且不得重新編號', 'state': 'IMPLEMENTED'}, {'id': 'COMPOSITE', 'scope': '5 個 VAP-CMP Recipe；40＋5＝45 項受管繪圖能力', 'state': 'IMPLEMENTED'}, {'id': 'OBSERVATION', 'scope': '1Y／3Y／5Y／All、Native～Yearly、Level／Change %／Rebase 100／YoY %', 'state': 'IMPLEMENTED'}, {'id': 'ANALYTICS', 'scope': 'SMA／EMA／Bollinger、異常值、參考線、Rolling、MaxDD 與反彈量測', 'state': 'IMPLEMENTED'}, {'id': 'INTERACTION', 'scope': '同步游標、點註記、框選、右鍵 Copy／Export／Inspect、Range Slider', 'state': 'IMPLEMENTED'}, {'id': 'COLLISION', 'scope': '九宮格標題、四象限 Legend、末值標籤與事件物件避碰', 'state': 'IMPLEMENTED'}, {'id': 'SNAP', 'scope': 'Grid／Data／Event Snap 與 10px／1px／0.2px 鍵盤微調', 'state': 'IMPLEMENTED'}, {'id': 'COLOR', 'scope': 'Seaborn Color Palette、220→20／VLAG 熱圖、台股紅漲綠跌', 'state': 'IMPLEMENTED'}, {'id': 'SAVE_IMAGE', 'scope': 'SVG Vector Master＋圖表契約＋語意＋Observation＋SHA-256', 'state': 'IMPLEMENTED'}, {'id': 'EXTRACT', 'scope': '搜尋、勾選、批次加入、特定保存圖與堆圖面板擷取', 'state': 'IMPLEMENTED'}, {'id': 'STACK', 'scope': 'Strict Intersection 共用時間軸、最下層唯一 X 軸、0.5×～4× 標準高度', 'state': 'IMPLEMENTED'}, {'id': 'EXPORT', 'scope': '使用者明確匯出 HTML／PNG／PDF／JSON；不自動下載', 'state': 'IMPLEMENTED'}, {'id': 'TEMPLATE', 'scope': 'Chart／HTML／Visual Preset 的 ID＋Version＋SHA Append-Only 治理', 'state': 'IMPLEMENTED'}, {'id': 'TEMPLATE_REBIND', 'scope': '模板保存角色、穩定欄位 ID、單位、型別、頻率、轉換與版面；更換 VQG 資料時自動重綁', 'state': 'IMPLEMENTED'}, {'id': 'DASHBOARD_LAYOUT', 'scope': '單圖、雙軸、共軸堆圖與其他 VAP 元件置入 12 欄防重疊 Dashboard', 'state': 'IMPLEMENTED'}, {'id': 'ASSET', 'scope': '12 Icon、16 Emoji、SVG Sanitizer、Code Point Lock', 'state': 'IMPLEMENTED'}, {'id': 'RUNTIME', 'scope': 'PowerShell → Python Loopback Runtime → VQG Sync Connect → Workbench', 'state': 'IMPLEMENTED'}, {'id': 'REFRESH', 'scope': 'Request ID、增量更新、Cache、Checkpoint 與真實回覆狀態', 'state': 'IMPLEMENTED'}, {'id': 'RESPONSIVE_UI', 'scope': 'PC 橫向／Mobile 直向、小字級、大圖＋右側可收參數', 'state': 'IMPLEMENTED'}, {'id': 'ADVANCED_RESEARCH', 'scope': '回測、Granger、Lead/Lag 與風險推論須有核准資料與獨立證據才可啟用', 'state': 'CONDITIONAL'}], 'conflicts': [{'id': 'CTX-001', 'topic': '圖表數量', 'earlier': '45 圖或 73／79 Builder 敘述', 'resolved': '40 個穩定 Canonical 圖碼＋5 個 Composite Recipe＝45 項受管能力；73／79 視為歷史別名與重複候選，不宣告為 Canonical', 'rule': 'DEDUP_PRESERVE_ALIAS'}, {'id': 'CTX-002', 'topic': '實體 Y 軸數', 'earlier': '三軸跨頻原型', 'resolved': '實體 Y 軸最多兩個；第三尺度以 Rebase／Min-Max／Z-Score 後掛入左或右軸', 'rule': 'TWO_PHYSICAL_AXES_MAX'}, {'id': 'CTX-003', 'topic': '軸步長家族', 'earlier': '2／2.5／5 × 10ⁿ', 'resolved': '採較新的明確要求 1.25／2.5／5 × 10ⁿ；10 僅作下一十進位邊界', 'rule': 'LATEST_EXPLICIT'}, {'id': 'CTX-004', 'topic': '線寬', 'earlier': '統一線粗 1.0', 'resolved': '資料線 1.2、Benchmark 1.0、重要線 1.4；個別規格可在合法範圍覆寫', 'rule': 'ROLE_BASED_STYLE'}, {'id': 'CTX-005', 'topic': 'Bar 透明度', 'earlier': '0.6 或 0.75', 'resolved': '單獨 Bar 預設 0.6；線＋Bar 雙軸混合時 Bar 預設 0.25', 'rule': 'CONTEXTUAL_STYLE'}, {'id': 'CTX-006', 'topic': '回測與進階推論', 'earlier': '先不做回測／Lead-Lag／Granger', 'resolved': '圖型與介面保留；正式計算維持 Conditional，未有核准來源、方法與 UAT 證據不得啟用', 'rule': 'FAIL_CLOSED_CAPABILITY'}, {'id': 'CTX-007', 'topic': '真實資料接線', 'earlier': '先不接真實資料源', 'resolved': '後續明確改為 VDF 授權、唯讀 Runtime 與 Sync Connect；Request 不等於成功，必須收到匹配回覆', 'rule': 'LATER_REQUIREMENT_SUPERSEDES'}, {'id': 'CTX-008', 'topic': '股票價格', 'earlier': 'Close 可作退路', 'resolved': '股票／ETF／股票指數只接受 VDF 核准 Adjusted Price，禁止 Raw Close Fallback；TA-Lib 只做計算不下載價格', 'rule': 'HARD_DATA_GATE'}, {'id': 'CTX-009', 'topic': '空值', 'earlier': '一般插值或平均', 'resolved': '價格只取前一交易日；成交量填 0 且不可沿用；禁止未來值與兩日平均', 'rule': 'NO_FUTURE_NO_DOUBLE_COUNT'}, {'id': 'CTX-010', 'topic': '啟用', 'earlier': '測試後啟用', 'resolved': '產生 Candidate Seal；Runtime Promotion 仍需明確外部審查，瀏覽器未執行不得宣稱全部啟用', 'rule': 'FAIL_CLOSED_ACTIVATION'}, {'id': 'CTX-011', 'topic': 'MacroMicro 基準', 'earlier': 'MACROMICRO 樣式', 'resolved': '只採先讀圖再調參數、區間／頻率／最新值等互動基準，不複製品牌視覺或內容', 'rule': 'UX_REFERENCE_NOT_BRAND_COPY'}, {'id': 'CTX-012', 'topic': 'VAP 正式資料入口', 'earlier': 'VAP 直接接 VDF Runtime Catalog', 'resolved': '正式管線改為 VDF／VRN → VQG 唯讀品質驗證 → VAP；VAP 不重算、不修補、不回寫上游', 'rule': 'VQG_ONLY_PRESENTATION_BOUNDARY'}], 'nonNegotiableRules': ['Append-Only stable identities; no destructive rewrite of historical chart, template, image, icon, emoji or preset records', 'VQG is the only formal VAP input; VDF and VRN remain upstream evidence and VAP never writes back', 'Stocks, ETFs and stock indices carry VDF-authorized Adjusted Price and TA-Lib evidence through VQG; raw Close is not an accepted fallback', 'VAP preserves VQG missing-value outputs and never silently repairs or interpolates them', 'US market observations align to the next Taiwan trading day; all ASOF joins reject future observations', 'Single or dual physical axes only; both sides use four intervals and five ticks with shared decimal precision', 'Saved charts preserve source, as-of, semantic metadata, observation settings, SVG and SHA-256 evidence', 'Stacked panels use strict shared-time intersection, standard-height multipliers and bottom-axis-only display', 'A refresh request is not connection success; activation and promotion remain fail-closed']}
EMBEDDED_SYSTEM_SPEC = {'schema': 'VIA-VAP-COMPLETE-SYSTEM-SPEC/1.0', 'version': 'v027', 'specVersion': '1.24.0', 'name': 'VeritasAutoPlot Complete System Package', 'authority': 'SSOT_APPEND_ONLY_FAIL_CLOSED', 'topology': {'launcher': 'PowerShell', 'frontend': 'Standalone Plotly-style Dashboard Workbench', 'backend': 'Python Loopback HTTP Runtime', 'dataAuthority': 'VQG Authorized Read-Only Manifest', 'upstreamEvidence': ['VDF', 'VRN'], 'host': '127.0.0.1', 'defaultPort': 8765}, 'modules': [{'id': 'VAP-MOD-CORE', 'file': 'js/vap-core-engine-v027.js', 'role': 'data semantics, time alignment, refresh and stack contracts'}, {'id': 'VAP-MOD-RENDERER', 'file': 'js/vap-plotly-renderer-v027.js', 'role': 'Plotly figure and dashboard tokens'}, {'id': 'VAP-MOD-BRIDGE', 'file': 'js/vap-runtime-bridge-v027.js', 'role': 'loopback health, catalog, refresh, image and context calls'}, {'id': 'VAP-MOD-CONTEXT', 'file': 'js/vap-context-engine-v027.js', 'role': 'historical lineage, capability inventory and deterministic conflict resolution'}, {'id': 'VAP-MOD-VQG-TEMPLATE', 'file': 'js/vap-vqg-template-engine-v027.js', 'role': 'VQG input gate, reusable role templates, automatic data rebind, shared-time stack and dashboard layout'}, {'id': 'VAP-MOD-RUNTIME', 'file': 'runtime/vap_data_runtime_v027.py', 'role': 'VQG formal-input gate, VDF/VRN upstream evidence, read-only adapters, cache, checkpoint, image and template persistence'}], 'adapters': ['CSV', 'TSV', 'JSON', 'JSON_ENDPOINT', 'PARQUET', 'SQLITE', 'DUCKDB'], 'vdfGate': {'required': True, 'schema': 'VIA-VDF-VAP-CONNECTION-MANIFEST/1.0', 'identity': 'sourceId + contractId + engine + fingerprint', 'statesAccepted': ['AUTHORIZED'], 'readOnlyRequired': True}, 'vqgGate': {'required': True, 'formalInput': True, 'schema': 'VIA-VQG-VAP-CONNECTION-MANIFEST/1.0', 'identity': 'sourceId + contractId + engine + fingerprint', 'statesAccepted': ['AUTHORIZED'], 'readOnlyRequired': True, 'limits': {'maxInputRows': 5000, 'maxOutputRows': 100, 'maxWindow': 252}, 'flow': 'VDF/VRN -> VQG -> VAP', 'vapMutation': False}, 'stockPolicy': {'assetClasses': ['STOCK', 'EQUITY', 'ETF', 'STOCK_INDEX'], 'priceInput': 'ADJUSTED_PRICE_ONLY', 'rawCloseFallback': False, 'taLibEvidenceRequired': True, 'technicalIndicators': ['SMA', 'EMA', 'RSI', 'MACD', 'BBANDS'], 'calculationOwner': 'VQG using VDF Adjusted Price evidence', 'vapRecalculation': False, 'volume': 'SPLIT_ADJUSTED_ZERO_NO_CARRY'}, 'missingData': {'vapPolicy': 'PRESERVE_VQG_OUTPUT_NO_SILENT_REPAIR', 'upstreamPricePolicy': 'PREVIOUS_TRADING_DAY_FORWARD_FILL_WHEN_EXPLICITLY_DECLARED_BY_VQG', 'upstreamVolumePolicy': 'EX_DAYTRADE_ZERO_NO_CARRY', 'futureLookingInterpolation': False, 'vapInterpolation': False}, 'marketTiming': 'US_T_TO_NEXT_TW_TRADING_DAY', 'chartSystem': {'canonicalCharts': 40, 'compositeRecipes': 5, 'physicalYAxisMaximum': 2, 'axisIntervals': 4, 'axisTicks': 5, 'axisStepFamily': [1.25, 2.5, 5, 10], 'styleProfile': {'dataLineWidth': 1.2, 'benchmarkLineWidth': 1.0, 'importantLineWidth': 1.4, 'standaloneBarOpacity': 0.6, 'mixedBarOpacity': 0.25}, 'savedImage': 'SVG + Contract + SHA-256', 'stackAlignment': 'STRICT_INTERSECTION_SHARED_DOMAIN_BOTTOM_AXIS_ONLY', 'heightMultipliers': [0.5, 0.75, 1, 1.25, 1.5, 2, 2.5, 3, 4]}, 'reusableTemplateEngine': {'schema': 'VIA-VAP-REUSABLE-TEMPLATE/1.0', 'registry': 'spec/vap_reusable_template_registry_v027.json', 'kinds': ['SINGLE_CHART', 'STACK', 'DASHBOARD'], 'savedContent': ['role', 'stable field id', 'indicator id', 'unit', 'data type', 'frequency', 'axis', 'form', 'transform', 'layout'], 'forbiddenContent': ['rows', 'values', 'labels', 'embedded dataset'], 'rebind': 'DETERMINISTIC_EXACT_OR_FAIL_CLOSED', 'ambiguity': 'REJECTED'}, 'dashboardEngine': {'schema': 'VIA-VAP-DASHBOARD/1.0', 'columns': 12, 'widgets': ['SINGLE_CHART', 'DUAL_AXIS_CHART', 'SHARED_TIME_STACK', 'HEATMAP', 'STAT_CARD', 'OTHER_VAP_COMPONENT'], 'autoPack': True, 'preventOverlap': True, 'sharedTimeWithinWidget': True}, 'observationEngine': {'schema': 'VIA-VAP-OBSERVATION-SPEC/1.0', 'uxReference': 'MACROMICRO_INTERACTION_MODEL_NOT_BRAND_COPY', 'timeRanges': ['1Y', '3Y', '5Y', 'ALL'], 'frequencies': ['native', 'weekly', 'monthly', 'quarterly', 'yearly'], 'valueModes': ['level', 'change_pct', 'rebase_100', 'yoy_pct'], 'aggregation': 'LAST_OBSERVATION_IN_BUCKET', 'transformOrder': ['resample', 'transform', 'timeWindow', 'finiteFilter'], 'latestValueStrip': True, 'evidence': ['source', 'asOf', 'fingerprint', 'VDF', 'Adjusted Price', 'TA-Lib', 'proxyDisclosure'], 'bookmarkPolicy': 'APPEND_ONLY_IDEMPOTENT_SHA256', 'savedImagePropagation': True, 'stackPropagation': True}, 'contextIntegration': {'schema': 'VIA-VAP-CONTEXT-LEDGER/1.0', 'file': 'spec/vap_context_ledger_v027.json', 'authority': 'LATEST_EXPLICIT_REQUIREMENT_WITH_APPEND_ONLY_LINEAGE', 'lineageVersions': 24, 'capabilityGroups': 28, 'resolvedConflicts': 12, 'managedPlotCapabilities': 45, 'resolutionRules': ['40_CANONICAL_PLUS_5_COMPOSITE', 'TWO_PHYSICAL_Y_AXES_MAX', 'LATEST_EXPLICIT_STYLE_RULE_WINS', 'FAIL_CLOSED_ADVANCED_RESEARCH', 'MACROMICRO_UX_REFERENCE_NOT_BRAND_COPY']}, 'userJourney': ['VQG Sync Connect', 'Add Chart', 'Single or Dual Axis Render', 'Save Reusable Template', 'Automatic VQG Data Rebind', 'Shared-Time Stack', 'Dashboard Placement', 'Explicit Export'], 'exports': ['HTML', 'PNG', 'PDF', 'JSON'], 'security': ['LOOPBACK_ONLY', 'PATH_ALLOWLIST', 'HOST_ALLOWLIST', 'DATABASE_READ_ONLY', 'SVG_ACTIVE_CONTENT_REJECTED', 'APPEND_ONLY_IMAGE_ID'], 'qualityGate': {'workbenchFullDiagnostics': 152, 'workbenchUserTests': 80, 'packageTests': 'tests/run_all_tests_v027.py', 'browserRule': 'MUST_REPORT_NOT_EXECUTED_WHEN_EXECUTABLE_IS_ABSENT'}}
EMBEDDED_CHART_REGISTRY = {'schema': 'VIA-VAP-CHART-REGISTRY/1.0', 'version': 'v027', 'policy': 'APPEND_ONLY_STABLE_CODE', 'canonicalCount': 40, 'compositeRecipeCount': 5, 'managedPlotCapabilityCount': 45, 'historicalCountResolution': '40_CANONICAL_PLUS_5_COMPOSITE; LEGACY_73_79_BUILDER_ITEMS_ARE_ALIASES_OR_DUPLICATE_CANDIDATES', 'physicalYAxisMaximum': 2, 'charts': [['VAP-CH-01', 'line', '折線圖', 'Line', 1], ['VAP-CH-02', 'area', '面積折線', 'Area', 1], ['VAP-CH-03', 'bar', '直條圖', 'Bar', 1], ['VAP-CH-04', 'hbar', '橫條圖', 'H-Bar', 1], ['VAP-CH-05', 'scatter', '散點圖', 'Scatter', 1], ['VAP-CH-06', 'sarea', '堆疊面積', 'Stacked Area', 1], ['VAP-CH-07', 'sbar', '堆疊直條', 'Stacked Bar', 1], ['VAP-CH-08', 'sbar100', '百分比堆疊', '100% Stacked', 1], ['VAP-CH-09', 'multi', '個別小圖', 'Small Multiples', 1], ['VAP-CH-10', 'gbar', '並列直條', 'Grouped Bar', 1], ['VAP-CH-11', 'dline', '底色面積 × 對比折線', 'Area × Line', 2], ['VAP-CH-12', 'dbarline', '條 + 線 雙軸', 'Bar × Line', 2], ['VAP-CH-13', 'evtmx', '事件矩陣', 'Event Matrix', 1], ['VAP-CH-14', 'corrheat', '相關熱力圖', 'Masked Corr', 0], ['VAP-CH-15', 'brush', '區間量測', 'Brush Measure', 1], ['VAP-CH-16', 'map', '地圖 × 數據', 'Map', 0], ['VAP-CH-17', 'roll', '滾動報酬', 'Rolling Returns', 1], ['VAP-CH-18', 'rollcorr', '滾動相關', 'Rolling Correlation', 1], ['VAP-CH-19', 'rollsharpe', '移動夏普', 'Trailing Sharpe', 1], ['VAP-CH-20', 'sortino', 'Sharpe × Sortino 比較', 'Sharpe × Sortino', 2], ['VAP-CH-21', 'radar', '風險雷達', 'Risk Radar', 0], ['VAP-CH-22', 'alpha', 'Alpha 策略', 'Alpha Strategy', 2], ['VAP-CH-23', 'econcal', '經濟日曆', 'Economic Calendar', 0], ['VAP-CH-24', 'consensus', '共識總覽', 'Consensus Overview', 1], ['VAP-CH-25', 'backtest', '回測驗證', 'Backtest Validation', 2], ['VAP-CH-26', 'intraday', '當日走勢 + 成交量', 'Intraday + Volume', 2], ['VAP-CH-27', 'candle', 'K線 × TA × Volume', 'Candlestick TA', 2], ['VAP-CH-28', 'spotfut', '現貨 × 期貨', 'Spot × Futures', 1], ['VAP-CH-29', 'hist', '直方圖', 'Histogram', 1], ['VAP-CH-30', 'box', '箱型圖', 'Box Plot', 1], ['VAP-CH-31', 'violin', '小提琴圖', 'Violin', 1], ['VAP-CH-32', 'kde', '核密度分布', 'KDE Distribution', 1], ['VAP-CH-33', 'reg', '迴歸散點圖', 'Regression Plot', 1], ['VAP-CH-34', 'density', '雙變量密度圖', 'Density Contour', 2], ['VAP-CH-35', 'pairgrid', '配對關係矩陣', 'Pair Grid', 0], ['VAP-CH-36', 'facet', '分面網格', 'Facet Grid', 1], ['VAP-CH-37', 'ecdf', '經驗累積分布', 'ECDF', 1], ['VAP-CH-38', 'rug', '邊際刻度圖', 'Rug Plot', 1], ['VAP-CH-39', 'resid', '迴歸殘差圖', 'Residual Plot', 1], ['VAP-CH-40', 'joint', '聯合分布網格', 'Joint Grid', 2]], 'compositeRecipes': ['VAP-CMP-001', 'VAP-CMP-002', 'VAP-CMP-003', 'VAP-CMP-004', 'VAP-CMP-005']}
EMBEDDED_TEMPLATE_REGISTRY = {'schema': 'VIA-VAP-REUSABLE-TEMPLATE-REGISTRY/1.0', 'version': 'v027', 'policy': 'APPEND_ONLY_ROLE_BINDING_VQG_ONLY', 'templates': [{'id': 'VAP-TPL-SINGLE-AXIS-001', 'version': 1, 'name': 'VQG Single Axis', 'kind': 'SINGLE_CHART', 'axisPolicy': 'ONE_PHYSICAL_Y_SHARED_TIME', 'panels': [{'id': 'P1', 'heightMultiple': 1, 'series': [{'roleId': 'PRIMARY', 'axis': 'left', 'form': 'line', 'required': True}]}]}, {'id': 'VAP-TPL-DUAL-AXIS-001', 'version': 1, 'name': 'VQG Dual Axis', 'kind': 'SINGLE_CHART', 'axisPolicy': 'TWO_PHYSICAL_Y_ONE_SHARED_TIME', 'panels': [{'id': 'P1', 'heightMultiple': 1, 'series': [{'roleId': 'PRIMARY', 'axis': 'left', 'form': 'line', 'required': True}, {'roleId': 'SECONDARY', 'axis': 'right', 'form': 'bar', 'required': True}]}]}, {'id': 'VAP-TPL-STACK-001', 'version': 1, 'name': 'VQG Shared-Time Stack', 'kind': 'STACK', 'axisPolicy': 'STRICT_INTERSECTION_SHARED_DOMAIN_BOTTOM_AXIS_ONLY', 'panels': [{'id': 'P1', 'heightMultiple': 1, 'series': [{'roleId': 'PRIMARY', 'axis': 'left', 'form': 'line', 'required': True}]}, {'id': 'P2', 'heightMultiple': 1, 'series': [{'roleId': 'SECONDARY', 'axis': 'left', 'form': 'bar', 'required': True}]}]}, {'id': 'VAP-TPL-DASHBOARD-001', 'version': 1, 'name': 'VQG Multi-Chart Dashboard', 'kind': 'DASHBOARD', 'axisPolicy': 'WIDGET_LOCAL_AXIS_SHARED_TIME_WITHIN_EACH_WIDGET', 'layout': {'columns': 12, 'rowHeight': 96, 'autoPack': True, 'preventOverlap': True}, 'widgets': [{'id': 'W1', 'type': 'SINGLE_CHART', 'x': 0, 'y': 0, 'w': 6, 'h': 4, 'templateRef': 'VAP-TPL-DUAL-AXIS-001@1'}, {'id': 'W2', 'type': 'STACK', 'x': 6, 'y': 0, 'w': 6, 'h': 6, 'templateRef': 'VAP-TPL-STACK-001@1'}, {'id': 'W3', 'type': 'VAP_COMPONENT', 'component': 'HEATMAP_OR_STAT_CARD', 'x': 0, 'y': 4, 'w': 6, 'h': 2}]}]}
EMBEDDED_LEGACY_CHART_LIBRARY = {'$schema': 'VIA-VAP-CHARTLIB/1.0', 'meta': {'code': 'VIA-SSOT-VAPLIB', 'seal': '觀 · VIA-SEAL-GUAN', 'name': 'VeritasAutoPlot 圖庫定義 SSOT', 'version': '1.0.0', 'updated': '2026-08-02', 'specRef': 'ssot/vap_spec.json', 'policy': '只增不減 · 每型唯一(同主題去重)· 新增圖型須配 VAP-CH 代碼'}, 'groups': [{'id': 'single', 'zh': '單軸', 'en': 'Single-Axis', 'charts': [{'code': 'VAP-CH-01', 'id': 'line', 'zh': '折線圖', 'en': 'Line', 'axes': 1, 'dataShape': 'series[]', 'fields': ['date', 'value'], 'use': '水準/指數趨勢'}, {'code': 'VAP-CH-02', 'id': 'area', 'zh': '面積折線', 'en': 'Area', 'axes': 1, 'dataShape': 'series', 'fields': ['date', 'value'], 'use': '單一序列強調量體', 'override': {'fill.areaUnderLine': 0.75}}, {'code': 'VAP-CH-03', 'id': 'bar', 'zh': '直條圖', 'en': 'Bar', 'axes': 1, 'dataShape': 'categorical', 'fields': ['label', 'value'], 'use': '分項比較'}, {'code': 'VAP-CH-04', 'id': 'hbar', 'zh': '橫條圖', 'en': 'H-Bar', 'axes': 1, 'dataShape': 'categorical', 'fields': ['label', 'value'], 'use': '長標籤分項(CPI 分項左負右正)'}, {'code': 'VAP-CH-05', 'id': 'scatter', 'zh': '散點圖', 'en': 'Scatter', 'axes': 1, 'dataShape': 'xy', 'fields': ['x', 'y'], 'use': '兩變數關係'}]}, {'id': 'stack', 'zh': '堆疊', 'en': 'Stacked', 'charts': [{'code': 'VAP-CH-06', 'id': 'sarea', 'zh': '堆疊面積', 'en': 'Stacked Area', 'axes': 1, 'dataShape': 'series[]', 'fields': ['date', 'value', 'group'], 'use': '組成消長'}, {'code': 'VAP-CH-07', 'id': 'sbar', 'zh': '堆疊直條', 'en': 'Stacked Bar', 'axes': 1, 'dataShape': 'categorical[]', 'fields': ['label', 'value', 'group'], 'use': '財政收支結構(間隙最小化)', 'override': {'bar.gapFactor': 'tight'}}, {'code': 'VAP-CH-08', 'id': 'sbar100', 'zh': '百分比堆疊', 'en': '100% Stacked', 'axes': 1, 'dataShape': 'categorical[]', 'fields': ['label', 'value', 'group'], 'use': '占比結構'}]}, {'id': 'indiv', 'zh': '個別', 'en': 'Small Multiples', 'charts': [{'code': 'VAP-CH-09', 'id': 'multi', 'zh': '個別小圖', 'en': 'Small Multiples', 'axes': 1, 'dataShape': 'series[]', 'fields': ['date', 'value', 'panel'], 'use': '多標的同軸比較', 'override': {'grid': '2x2'}}, {'code': 'VAP-CH-10', 'id': 'gbar', 'zh': '並列直條', 'en': 'Grouped Bar', 'axes': 1, 'dataShape': 'categorical[]', 'fields': ['label', 'value', 'group'], 'use': '官方×民間數據對照'}]}, {'id': 'dual', 'zh': '雙軸', 'en': 'Dual-Axis', 'charts': [{'code': 'VAP-CH-11', 'id': 'dline', 'zh': '底色面積 × 對比折線', 'en': 'Area × Line', 'axes': 2, 'dataShape': 'series×2', 'fields': ['date', 'left', 'right'], 'use': '一邊底色一邊折線(信心指數 × 零售年增率)', 'rule': '底色序列置右軸 α0.75;折線置左軸 lw1'}, {'code': 'VAP-CH-12', 'id': 'dbarline', 'zh': '條 + 線 雙軸', 'en': 'Bar × Line', 'axes': 2, 'dataShape': 'mixed', 'fields': ['date', 'bar', 'line'], 'use': '非農新增(條) × 失業率(線)'}]}, {'id': 'adv', 'zh': '進階', 'en': 'Advanced', 'charts': [{'code': 'VAP-CH-13', 'id': 'evtmx', 'zh': '事件矩陣', 'en': 'Event Matrix', 'axes': 1, 'dataShape': 'series+events', 'fields': ['date', 'value', 'events[]'], 'use': '危機事件對照', 'rule': '垂直虛線 0.8/0.8 · 區間陰影 0.3 · 無水平線'}, {'code': 'VAP-CH-14', 'id': 'corrheat', 'zh': '相關熱力圖', 'en': 'Masked Corr', 'axes': 0, 'dataShape': 'matrix', 'fields': ['corr'], 'use': '資產相關性', 'rule': '下三角遮罩 · zmid 0 · seaborn 15 級色階'}, {'code': 'VAP-CH-15', 'id': 'brush', 'zh': '區間量測', 'en': 'Brush Measure', 'axes': 1, 'dataShape': 'series', 'fields': ['date', 'value'], 'use': '拉選區間求高低/MaxDD/耗時'}, {'code': 'VAP-CH-16', 'id': 'map', 'zh': '地圖 × 數據', 'en': 'Map', 'axes': 0, 'dataShape': 'geo', 'fields': ['region', 'value', 'change'], 'use': '全球/美國/歐洲/東亞/台灣', 'engine': 'leaflet', 'rule': '漲跌以上下三角標示'}]}, {'id': 'rolling', 'zh': '滾動績效', 'en': 'Rolling Performance', 'charts': [{'code': 'VAP-CH-17', 'id': 'roll', 'zh': '滾動報酬', 'en': 'Rolling Returns', 'axes': 1, 'dataShape': 'series', 'fields': ['date', 'return'], 'use': '期間績效穩定度'}, {'code': 'VAP-CH-18', 'id': 'rollcorr', 'zh': '滾動相關', 'en': 'Rolling Correlation', 'axes': 1, 'dataShape': 'series×2', 'fields': ['date', 'a', 'b'], 'use': '關係變化'}, {'code': 'VAP-CH-19', 'id': 'rollsharpe', 'zh': '移動夏普', 'en': 'Trailing Sharpe', 'axes': 1, 'dataShape': 'series', 'fields': ['date', 'sharpe'], 'use': '風險調整後報酬'}, {'code': 'VAP-CH-20', 'id': 'sortino', 'zh': 'Sharpe × Sortino 比較', 'en': 'Sharpe × Sortino', 'axes': 2, 'dataShape': 'series×2', 'fields': ['date', 'sharpe', 'sortino'], 'use': '下行風險與總波動對照', 'rule': '左軸 Sharpe · 右軸 Sortino · 同等格數'}, {'code': 'VAP-CH-21', 'id': 'radar', 'zh': '風險雷達', 'en': 'Risk Radar', 'axes': 0, 'dataShape': 'radial', 'fields': ['metric', 'value', 'benchmark'], 'use': '多維風險輪廓(波動·MaxDD·Beta·集中度·流動性)', 'rule': '基準線為外圈虛線 · 填色 α0.3'}, {'code': 'VAP-CH-22', 'id': 'alpha', 'zh': 'Alpha 策略', 'en': 'Alpha Strategy', 'axes': 2, 'dataShape': 'series×3', 'fields': ['date', 'strategy', 'benchmark', 'excess'], 'use': '策略 vs 基準 + 超額報酬', 'rule': '累積績效置左軸 · 超額報酬置右軸直條(漇2跌綣) · 0 軸紅線'}, {'code': 'VAP-CH-23', 'id': 'econcal', 'zh': '經濟日曆', 'en': 'Economic Calendar', 'axes': 0, 'dataShape': 'events', 'fields': ['date', 'event', 'importance', 'actual', 'forecast', 'previous'], 'use': '重要數據發布時程與預期落差', 'rule': '重要度以紅黃綠三階 · 實際優於預期標紅'}, {'code': 'VAP-CH-25', 'id': 'backtest', 'zh': '回測驗證', 'en': 'Backtest Validation', 'axes': 2, 'dataShape': 'matrix+series', 'fields': ['lag', 'rankIC', 'tStat', 'pValue'], 'use': 'Rank-IC 衰減 × 顯著性', 'rule': '左軸 Rank-IC 直條 · 右軸 t 統計量折線 · |t|=1.96 水平基準線 0.8'}]}, {'id': 'ta', 'zh': '技術分析', 'en': 'Technical', 'charts': [{'code': 'VAP-CH-26', 'id': 'intraday', 'zh': '當日走勢 + 成交量', 'en': 'Intraday + Volume', 'axes': 2, 'dataShape': 'ohlcv', 'fields': ['time', 'price', 'volume'], 'use': '當日盤勢', 'rule': 'rows=2 · row_heights [.72,.28] · shared_xaxes'}, {'code': 'VAP-CH-27', 'id': 'candle', 'zh': 'K線 × SMA/EMA/BB × Volume', 'en': 'Candlestick TA', 'axes': 2, 'dataShape': 'ohlcv', 'fields': ['date', 'open', 'high', 'low', 'close', 'volume'], 'use': '技術分析', 'rule': 'adj price · split 調整'}, {'code': 'VAP-CH-28', 'id': 'spotfut', 'zh': '現貨 × 期貨', 'en': 'Spot × Futures', 'axes': 1, 'dataShape': 'series[]', 'fields': ['date', 'spot', 'futures'], 'use': 'BRENT / WTI / GOLD 基差', 'rule': '現貨實線 · 期貨虛線 · 基差標籤堆疊 ≥9px'}]}, {'id': 'fund', 'zh': '基本面', 'en': 'Consensus', 'charts': [{'code': 'VAP-CH-24', 'id': 'consensus', 'zh': '共識總覽', 'en': 'Consensus Overview', 'axes': 1, 'dataShape': 'table', 'fields': ['dilutedEPS', 'targetPrice', 'rating', 'analystCount', 'forwardPER', 'forwardPBR'], 'use': 'yfinance / FactSet 共識', 'rule': '綠黃紅 spectrum · 目標價取左右最長'}]}], 'dataSources': ['TWSE 台灣證交所', 'TPEX 櫃買中心', 'SITCA 投信投顧公會', 'MOPS 公開資訊觀測站', 'yfinance', 'FactSet (keyed)', 'FRED', 'EPFR', 'HKEX 港交所'], 'changelog': [{'version': '1.0.0', 'date': '2026-08-02', 'note': '自 Builder GROUPS 抽出 28 型全數建檔(VAP-CH-01…28)'}]}
EMBEDDED_LEGACY_SPEC = {'$schema': 'VIA-VAP-SPEC/1.0', 'meta': {'code': 'VIA-SSOT-VAPSPEC', 'seal': '觀 · VIA-SEAL-GUAN', 'name': 'VeritasAutoPlot 繪圖規範 SSOT', 'version': '1.0.0', 'updated': '2026-08-02', 'authority': '本檔為唯一真相。頁面不得寫死數值,一律讀取此檔。', 'policy': '只增不減 · 修改需升版並保留 changelog'}, 'line': {'width': 1, 'widthRange': [0.5, 6], 'widthStep': 0.5, 'opacity': 0.9, 'dashForSecondary': '5 3', 'note': '折線一律線粗 1;虛線僅用於期貨/對比序列'}, 'fill': {'areaUnderLine': 0.75, 'areaUnderLineWithShadow': 0.5, 'barFace': 0.6, 'barFaceDense': 0.8, 'eventBand': 0.3, 'note': '折線下方區域 0.75;若下方另有陰影則降為 0.5;事件區間陰影 0.3'}, 'bar': {'gapFactor': {'seamless': 1, 'tight': 0.86, 'normal': 0.8, 'grouped': 0.44}, 'edge': {'width': 0.8, 'style': 'solid', 'opacity': 1}, 'edgeRule': '有框者:edgecolor=color, lw=0.8, 不透明;框內 facecolor=rgba(color, 0.8)', 'stackedGapMin': True}, 'axis': {'tickStepMultiples': [2, 2.5, 5, 10], 'sameTickCountBothSides': True, 'decimalUnify': True, 'decimalExamples': {'0.2': '0.20', '0.25': '0.25'}, 'thousandsSeparator': True, 'headroomTicks': 1, 'rangeWrapsData': True, 'dualAxisAligned': True, 'note': '左右軸間隔數相同 → 格線對齊;間距值為 2/2.5/5/10 倍數;上方留一格給圖示'}, 'timeAxis': {'mode': 'tradingDaySequence', 'dropEmptyDates': True, 'normalizeBase': 'startDate', 'stackAlignment': 'absolute', 'mixedFrequencyRule': '日×月混用時自動對齊;價格類空值取前一交易日;成交量不得補值', 'dataStart': '1920-01-01', 'displayStart': '2007-01-01', 'zoomable': True}, 'referenceLines': {'benchmarkHorizontal': {'width': 0.8, 'style': 'solid', 'opacity': 0.8, 'color': 'grey'}, 'eventVertical': {'width': 0.8, 'style': 'dash', 'opacity': 0.8, 'colorOrder': ['red', 'grey']}, 'zeroAxis': {'width': 1, 'style': 'solid', 'color': '#c96b5a'}, 'noHorizontalOnEventMatrix': True}, 'palette': {'default': 'via', 'locked': True, 'combos': {'via': ['#c96b5a', '#c4943a', '#5a9e6f', '#439a9a', '#4c78a8', '#7a6daa'], 'deep': ['#4c78a8', '#e45756', '#f58518', '#72b7b2', '#54a24b', '#b279a2'], 'set2': ['#66c2a5', '#fc8d62', '#8da0cb', '#e78ac3', '#a6d854', '#ffd92f'], 'tab10': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b'], 'paired': ['#a6cee3', '#1f78b4', '#b2df8a', '#33a02c', '#fb9a99', '#e31a1c'], 'muted': ['#4878d0', '#ee854a', '#6acc64', '#d65f5f', '#956cb4', '#8c613c'], 'pastel': ['#a1c9f4', '#ffb482', '#8de5a1', '#ff9f9b', '#d0bbff', '#debb9b'], 'cb': ['#0173b2', '#de8f05', '#029e73', '#d55e00', '#cc78bc', '#ca9161']}, 'semantic': {'up': '#c96b5a', 'down': '#5a9e6f', 'neutral': '#9c9890', 'benchmark': '#9c9890', 'note': '漲紅跌綠(亞洲慣例)'}, 'correlation': {'mask': 'lowerTriangle', 'zmid': 0, 'scale': [[0, '#3f7f93'], [0.071, '#5890a1'], [0.143, '#72a1b0'], [0.214, '#8cb3bf'], [0.286, '#a7c5cf'], [0.357, '#c0d6dd'], [0.429, '#dae8ec'], [0.5, '#f2f2f2'], [0.571, '#f7d7d9'], [0.643, '#f2bcc0'], [0.714, '#eda3a9'], [0.786, '#e8888f'], [0.857, '#e36e76'], [0.929, '#de535e'], [1, '#d93a46']], 'gap': 1, 'heatmapContrast': '波動區間內加大紅黃綠色差'}}, 'typography': {'families': {'display': 'Syne', 'text': 'DM Sans', 'mono': 'DM Mono', 'cjk': 'Noto Sans TC'}, 'scale': {'eyebrow': 9, 'en': 9, 'badge': 9.5, 'hint': 11, 'tab': 13, 'brand': 16, 'chartTitle': 12, 'axisTitle': 10, 'tick': 9.5, 'legend': 10}, 'slideMin': 24, 'printMinPt': 12}, 'layout': {'margin': {'top': 30, 'right': 20, 'bottom': 34, 'left': 56}, 'stackStandardHeight': 280, 'chartsPerRow': 2, 'fullBleed': True, 'cardRadius': 9, 'borderColor': '#dbd9d3', 'gridColor': '#ecebe6', 'paper': '#f5f4f0', 'plot': '#ffffff', 'noOverlap': '物件不可重疊(含數據備註)· 標籤固定間距 ≥ 9px 堆疊'}, 'price': {'useAdjClose': True, 'adjustAllPrices': True, 'splitAdjustVolume': True, 'missingPrice': 'previousTradingDay', 'missingVolume': 'doNotFill', 'sourcePriority': ['adjClose', 'close'], 'fallbackWhenNoAdj': 'close', 'rule': '有 Adj 價格者一律以 Adj 價格為主(股票 · 股票指數 · ETF · 含息還原);無 Adj 欄位者(期貨 · 現貨 · 匯率 · 利率 · 商品 · 總經指標)以一般價格為主', 'labelSuffix': {'adj': ' (adj)', 'raw': ''}, 'mixedSeriesRule': '同一圖內若部分序列有 Adj 部分無,各自取其優先來源,並於圖註標明哪些序列為 adj'}, 'interaction': {'zoom': True, 'brushMeasure': ['high', 'low', 'maxDD', 'duration', 'recoveryTime'], 'hover': 'x unified', 'collapsible': True}, 'export': {'png': {'background': 'white', 'scale': 4}, 'html': {'interactive': True}, 'pdf': {'engine': 'print-based'}, 'pptx': {'mode': 'editable'}}, 'changelog': [{'version': '1.0.0', 'date': '2026-08-02', 'note': '自 Builder DEFAULTS / Spec v4 / 對話規範抽出建檔'}]}
EMBEDDED_FUNCTION_INVENTORY = {'schema': 'VIA-VAP-FUNCTION-INVENTORY/1.0', 'version': 'v0300', 'authority': 'VAP-ALL-IN-ONE-ENGINE', 'policy': 'V027_IMPLEMENTED_FUNCTIONS_PRESERVED; LEGACY_28_CHARTS_RETAINED_AS_LINEAGE; 40_CANONICAL_PLUS_5_COMPOSITE_IS_ACTIVE', 'counts': {'pythonFunctions': 70, 'pythonClasses': 4, 'javascriptModuleFunctions': 62, 'workbenchFunctions': 459, 'totalNamedFunctions': 591, 'canonicalCharts': 40, 'compositeRecipes': 5, 'managedPlotCapabilities': 45, 'capabilityGroups': 28, 'resolvedConflicts': 12, 'legacyCharts': 28, 'httpRoutes': 9}, 'python': {'functions': ['__init__', '_cors_headers', '_error', '_json', '_read_json', 'as_dict', 'def_apply_missing_value_policy', 'def_apply_talib_indicators', 'def_atomic_write', 'def_atomic_write_json', 'def_atomic_write_text', 'def_build_catalog_table', 'def_canonical_json', 'def_config_fingerprint', 'def_connection_fingerprint', 'def_default_config', 'def_expand_location', 'def_forward_fill_numeric', 'def_import_optional', 'def_infer_columns', 'def_infer_field_semantic', 'def_is_number', 'def_json_rows', 'def_json_safe', 'def_load_config', 'def_load_json', 'def_load_vdf_manifest', 'def_load_vqg_manifest', 'def_main', 'def_make_handler', 'def_manifest_status', 'def_normalize_rows', 'def_now_iso', 'def_origin_allowed', 'def_package_root', 'def_parse_args', 'def_prepare_embedded_runtime_assets', 'def_read_delimited', 'def_read_duckdb', 'def_read_json', 'def_read_json_endpoint', 'def_read_parquet', 'def_read_sqlite', 'def_resolve_allowed_path', 'def_resolve_allowed_url', 'def_run_self_test', 'def_safe_identifier', 'def_setup_logging', 'def_sha256_bytes', 'def_sha256_text', 'def_source_change_token', 'def_source_signature', 'def_source_tables', 'def_unified_inventory_summary', 'def_validate_connection', 'def_vdf_evidence', 'def_vqg_evidence', 'def_write_runtime_state', 'do_GET', 'do_OPTIONS', 'do_POST', 'expand_tokens', 'format', 'health', 'image_manifest', 'log_message', 'refresh', 'save_image', 'save_template', 'template_manifest'], 'classes': ['CatalogRuntime', 'JsonLineFormatter', 'RefreshResult', 'VAPRequestHandler']}, 'javascriptModules': {'vap-core-engine-v0300.js': ['def_align_us_to_next_tw', 'def_build_refresh_request', 'def_canonical_json', 'def_canonicalize', 'def_common_stack_labels', 'def_dedupe_saved_images', 'def_fill_missing', 'def_infer_semantic', 'def_next_target_day', 'def_normalize_height', 'def_safe_identifier', 'def_self_test', 'def_sha256_text', 'def_stack_panel_heights'], 'vap-plotly-renderer-v0300.js': ['def_apply_time_window', 'def_axis_contract', 'def_build_figure', 'def_date', 'def_frequency_bucket', 'def_last_annotation', 'def_layout', 'def_number', 'def_prepare_observation_series', 'def_render', 'def_resample_series', 'def_self_test', 'def_trace', 'def_transform_series', 'def_yoy_lag'], 'vap-runtime-bridge-v0300.js': ['def_catalog', 'def_context', 'def_endpoint', 'def_health', 'def_images', 'def_refresh', 'def_request', 'def_save_image', 'def_save_template', 'def_self_test', 'def_templates'], 'vap-context-engine-v0300.js': ['managedCapabilityCount', 'search', 'summary', 'validate'], 'vap-vqg-template-engine-v0300.js': ['def_array', 'def_auto_pack_widgets', 'def_build_dashboard', 'def_canonical_json', 'def_canonicalize', 'def_create_template', 'def_field_records', 'def_normalize_binding', 'def_rebind_template', 'def_rect_overlap', 'def_score_candidate', 'def_self_test', 'def_sha256_text', 'def_shared_time_domain', 'def_stack_layout', 'def_text', 'def_validate_vqg_table', 'def_vqg_tables']}, 'workbench': {'functions': ['activateVap', 'activationSnapshot', 'activationStore', 'activePalette', 'addCompositeToStack', 'addCurrentChartToStack', 'addCurrentChartToVqgDashboard', 'addCurrentStackToVqgDashboard', 'addSavedImageToStack', 'addSelectedSavedImagesToStack', 'addVapComponentToDashboard', 'alignCompositeSeries', 'alignMarketTiming', 'alignedAxisDomains', 'allEmojiAssets', 'allIconAssets', 'allManagedTemplates', 'allTemplates', 'allVisualPresets', 'appendBridgeLedger', 'appendCandidateEvent', 'applyChartRecordToPair', 'applyCompositeNormalization', 'applyObservationWindow', 'applyPlotlyAxisContract', 'applyRendererEnhancements', 'applyRendererInteractionState', 'applySelectedTemplateCandidate', 'applySemanticPairPreset', 'applyTemplate', 'applyUiEnglishTitleCase', 'applyVisualPreset', 'applyVqgRoleToPair', 'assetKey', 'attachRendererInteractions', 'autoLayoutVqgDashboard', 'autoRouteRenderer', 'axisDomain', 'axisStepDecimals', 'base64Bytes', 'boot', 'bridgeLedgerStore', 'buildCandidateRecord', 'buildCompositeContract', 'buildRendererContract', 'buildStructuralSnapshots', 'buildTemplateCandidatePackage', 'candidateEvents', 'candidatePairFromControls', 'candidateRecord', 'candidateState', 'canonicalIconSvg', 'canonicalJson', 'canonicalizeValue', 'canvasBlob', 'chartColors', 'chartPreviewSvg', 'chooseCompositeLayout', 'clampRendererNumber', 'clearQaSession', 'clearSavedImageSelection', 'clearStackComposer', 'clearVqgDashboard', 'closeManagedPreview', 'commonStackLabels', 'compareCompositeLabel', 'compareTemplateCandidate', 'compareVersions', 'composeFieldMarkup', 'composePresetKey', 'composePresetState', 'composePresetStore', 'compositeBuilderConfig', 'compositeChartRecord', 'compositeDensityGrid', 'compositeFieldSelection', 'compositeLegendPosition', 'compositePreviousPoint', 'compositeSeries', 'compositeSynthetic', 'compositeTimeKey', 'compositeZonePosition', 'computeSelectionAnalytics', 'computeTemplateDiff', 'connectorEffectiveStatus', 'connectorStore', 'contextLedgerPayload', 'copyRendererPayload', 'correlationMatrix', 'createTemplateVersion', 'cumulativeReturns', 'currentPairConfig', 'currentRendererRoute', 'currentVqgTemplateBindings', 'decodeGzipBase64', 'decodeManagedDependencyAsset', 'decodeManagedSeed', 'decodeSvgDataUrl', 'deliveryTaskState', 'dispatchTemplateCandidateVersion', 'downloadBlob', 'downloadJson', 'downloadManagedTemplate', 'downloadSavedImage', 'downloadSvg', 'drawCanonicalEngineSvg', 'drawChart', 'drawCompositeSvg', 'drawStackChart', 'drawStatisticalSvg', 'ecdfSeries', 'effectiveManagedState', 'effectivePresetState', 'effectiveTemplateState', 'effectiveVisualState', 'emojiCategories', 'emojiGraphemes', 'ensureMainPlotly', 'esc', 'executeQaCase', 'exponentialMovingAverage', 'exportComposePresetRegistry', 'exportCompositeJson', 'exportConnectors', 'exportConsolidatedSsot', 'exportContextLedger', 'exportCurrentChart', 'exportManagedManifest', 'exportQaReport', 'exportQualityProfile', 'exportRendererGraph', 'exportSavedSelectionManifest', 'exportSelectedTemplateCandidate', 'exportSemanticRegistry', 'exportStackChart', 'exportStructuralSnapshots', 'exportSvgAsset', 'exportTemplateManagementPackage', 'exportTemplates', 'exportVisualAssetManifest', 'exportVisualPresetRegistry', 'exportVqgTemplateRegistry', 'extractManagedDependencies', 'extractManagedTitle', 'extractSelectedSavedImage', 'extractStackItem', 'fieldSemantic', 'fillRendererMissing', 'fillSelect', 'filteredSavedImageRecords', 'findEmojiAsset', 'findIconAsset', 'findManagedTemplate', 'findTemplate', 'findVisualPreset', 'flattenDescriptor', 'fmt', 'formatAxisTick', 'formatBytes', 'fullDiagnosticDefinitions', 'getManagedContent', 'getSavedImage', 'governedImageFingerprintPayload', 'guardGeo', 'handleRendererContextAction', 'hideRendererContextMenu', 'histogramBins', 'iconCategories', 'iconSource', 'imageFromUrl', 'importDataFile', 'importIconFile', 'importIconFiles', 'importManagedFile', 'importManagedHtmlFiles', 'importSsotFile', 'importTemplateCandidateFile', 'importTemplatesFile', 'importVisualPresetFile', 'inferChartRoute', 'inferColumns', 'inferFieldUnit', 'inferManagedRole', 'inferNumericColumns', 'inferSemanticField', 'inferXColumn', 'installRuntimeBridge', 'installUiEnglishTitleCase', 'interactionDuration', 'jsonTables', 'kdeEstimate', 'latestActiveAssets', 'latestSemanticField', 'legalAxisStep', 'linearRegression', 'loadComposePreset', 'loadStore', 'loadVersionedStore', 'looksTemporal', 'managedDbOpen', 'managedDependencyAsset', 'managedDependencyAudit', 'managedDependencyRule', 'managedSeedMeta', 'managedTemplateKey', 'managedTemplateStore', 'marks', 'measureRendererSelection', 'moveStackItem', 'newId', 'nextAssetId', 'nextComposePresetId', 'nextLegalAxisStep', 'nextPresetId', 'niceTicks', 'normalizeCatalogTable', 'normalizeCompositeValues', 'normalizePairSpec', 'normalizeSeries', 'normalizeStackHeightMultiple', 'nowIso', 'numericValue', 'observationBookmarkStore', 'observationDisplayUnit', 'observationEvidence', 'observationSpec', 'onTableChange', 'openCanonicalPreview', 'openChartInEngine', 'openInPair', 'openSavedImageDb', 'openWorkflowStage', 'pairVisualSpec', 'paletteOptionsHtml', 'parseDelimited', 'parseReferenceLines', 'pctChange', 'pdfFromJpegImages', 'persistQaRun', 'persistSnapshotToRuntime', 'persistVqgTemplateToRuntime', 'plotlyBaseLayout', 'plotlyColorscale', 'plotlyFigure', 'plotlyStatFigure', 'pointGuide', 'prepareEmojiVersion', 'prepareManagedPreviewContent', 'preparePairObservation', 'prepareVisualPresetVersion', 'previewFrame', 'previewManagedTemplate', 'probeVapRuntime', 'process', 'putManagedContent', 'putSavedImage', 'qaCounts', 'qaGateSnapshot', 'qaSessionStore', 'qaValueText', 'quantile', 'readManagedContent', 'rebindSelectedVqgTemplate', 'recordWorkflowEvent', 'refreshCatalogUI', 'refreshCompositeCatalog', 'refreshCompositeFields', 'refreshPresetOptions', 'refreshRendererFields', 'refreshSemanticUi', 'refreshTemplateCandidateSelectors', 'registerCatalogTable', 'registerConnector', 'registerRendererTemplate', 'registerSemanticField', 'registerSemanticFieldFromUi', 'removeStackItem', 'renderActivationState', 'renderAssetRegistry', 'renderBridgeLedger', 'renderCanonicalGallery', 'renderComposePresetRegistry', 'renderCompositeChart', 'renderConnectors', 'renderContextLedger', 'renderDeliveryTasks', 'renderEmojiRegistry', 'renderEndpointRegistry', 'renderEngineGraph', 'renderEngineInventory', 'renderIconRegistry', 'renderManagedTemplates', 'renderObservationBookmarkCount', 'renderPair', 'renderQa', 'renderQaResults', 'renderQaState', 'renderRendererTemplateMatrix', 'renderSavedImageRegistry', 'renderSelectionReadout', 'renderSemanticRegistry', 'renderSpecMatrix', 'renderSsotSources', 'renderStackComposer', 'renderStackQueue', 'renderTemplateCandidateDiff', 'renderTemplateCandidateLedger', 'renderTemplateCandidateSession', 'renderTemplateManagementCenter', 'renderTemplates', 'renderUserResults', 'renderVisualPresets', 'renderVqgDashboard', 'renderVqgTemplateRegistry', 'renderVqgWorkspace', 'renderWorkflowDashboard', 'renderWorkflowLedger', 'rendererControlValue', 'rendererFieldPolicy', 'rendererInspectPayload', 'rendererInteractionState', 'rendererOutliers', 'rendererTable', 'rendererTypeChart', 'requestAllConnectorRefresh', 'requestConnectorRefresh', 'requestIconVersion', 'requestManagedVersion', 'resetTemplateCandidateComparison', 'resetWorkflowState', 'residualSeries', 'restorePairConfig', 'restoreSavedChartImage', 'rollbackTemplateCandidateSession', 'rollingCorrelation', 'rollingMean', 'rollingStd', 'runFullDiagnostics', 'runGuidedUserJourney', 'runTestDebugActivate', 'runUserTests', 'runtimeEndpointValue', 'safeExportName', 'sanitizeSvgText', 'saveComposePreset', 'saveCompositeChartImage', 'saveCurrentAsVqgTemplate', 'saveCurrentChartImage', 'saveCurrentTemplate', 'saveEmojiAsset', 'saveObservationBookmark', 'saveStore', 'saveVisualPreset', 'savedImageManifestStore', 'savedImageSearchText', 'savedImageUnitSummary', 'selectComposePreset', 'selectRendererTemplate', 'selectTemplateCandidate', 'selectVisualAsset', 'selectionGuideShapes', 'semanticFieldId', 'semanticFieldIdentity', 'semanticFieldStore', 'semanticUiCandidate', 'serializeExportSvg', 'seriesOf', 'seriesValues', 'setActivePalette', 'setNotice', 'setQaBusy', 'setRuntimeBridgeState', 'setSavedImageSelection', 'setStackHeightMultiple', 'setWorkflowStep', 'setupCanonicalLibrary', 'setupCompositeEngine', 'setupContextLedger', 'setupDataImport', 'setupDiagnostics', 'setupManagedTemplateControls', 'setupPaletteControls', 'setupRendererStudio', 'setupSemanticRegistry', 'setupSsotControls', 'setupTemplateCandidateControls', 'setupVisualAssetControls', 'sha256Text', 'shiftCompositeSeriesToNextTarget', 'simpleHash', 'sortedFinite', 'sourceCharts', 'ssotIntakeStore', 'stackAlignedValues', 'stackBaseHeight', 'stackPanelHeights', 'standaloneChartHtml', 'standalonePlotlyHtml', 'statisticReferenceShapes', 'structuralSnapshot', 'submitTemplateCandidateReview', 'svgBounds', 'svgPath', 'svgToCanvas', 'swapAxes', 'switchPage', 'syncCategorySelect', 'syncPaletteControls', 'tableByName', 'templateCandidatePayload', 'templateCandidateStore', 'templateContentDescriptor', 'templateDescriptor', 'templateInventoryItem', 'templateInventoryKey', 'templateKey', 'templateStore', 'titleCaseVisibleEnglish', 'toggleComposePresetState', 'toggleManagedArchive', 'togglePairParameters', 'togglePresetArchive', 'toggleRendererPoint', 'toggleSavedImageSelectAll', 'toggleSidebar', 'toggleTemplateArchive', 'toggleVisualAssetArchive', 'transformRendererSeries', 'unicodeCodePoints', 'unifiedTemplateInventory', 'updateObservationSummary', 'updatePairAxisLayout', 'updateSemanticFieldUi', 'userAcceptanceDefinitions', 'validEmojiGlyph', 'validateCatalogTable', 'validateChartlibSsot', 'validateCompositeConfig', 'validateSemanticField', 'validateSpecSsot', 'validateTemplateCandidatePair', 'validateTemplateManagement', 'validateTemplateRecord', 'validateVisualPreset', 'verifiedSavedImage', 'verifyCandidateRecord', 'verifyManagedTemplate', 'versionTuple', 'visualAssetStore', 'visualPresetKey', 'visualPresetStore', 'vqgBindingFromField', 'vqgCatalogTables', 'vqgDashboardStore', 'vqgTemplatePanels', 'vqgTemplateStore', 'vqgWidgetContent', 'waitForRuntimeRefresh', 'workflowStepNode']}, 'httpRoutes': ['/', '/api/catalog', '/api/context', '/api/functions', '/api/health', '/api/images', '/api/refresh', '/api/spec', '/api/templates'], 'canonicalCharts': [{'code': 'VAP-CH-01', 'id': 'line', 'nameZh': '折線圖', 'nameEn': 'Line', 'physicalYAxis': 1}, {'code': 'VAP-CH-02', 'id': 'area', 'nameZh': '面積折線', 'nameEn': 'Area', 'physicalYAxis': 1}, {'code': 'VAP-CH-03', 'id': 'bar', 'nameZh': '直條圖', 'nameEn': 'Bar', 'physicalYAxis': 1}, {'code': 'VAP-CH-04', 'id': 'hbar', 'nameZh': '橫條圖', 'nameEn': 'H-Bar', 'physicalYAxis': 1}, {'code': 'VAP-CH-05', 'id': 'scatter', 'nameZh': '散點圖', 'nameEn': 'Scatter', 'physicalYAxis': 1}, {'code': 'VAP-CH-06', 'id': 'sarea', 'nameZh': '堆疊面積', 'nameEn': 'Stacked Area', 'physicalYAxis': 1}, {'code': 'VAP-CH-07', 'id': 'sbar', 'nameZh': '堆疊直條', 'nameEn': 'Stacked Bar', 'physicalYAxis': 1}, {'code': 'VAP-CH-08', 'id': 'sbar100', 'nameZh': '百分比堆疊', 'nameEn': '100% Stacked', 'physicalYAxis': 1}, {'code': 'VAP-CH-09', 'id': 'multi', 'nameZh': '個別小圖', 'nameEn': 'Small Multiples', 'physicalYAxis': 1}, {'code': 'VAP-CH-10', 'id': 'gbar', 'nameZh': '並列直條', 'nameEn': 'Grouped Bar', 'physicalYAxis': 1}, {'code': 'VAP-CH-11', 'id': 'dline', 'nameZh': '底色面積 × 對比折線', 'nameEn': 'Area × Line', 'physicalYAxis': 2}, {'code': 'VAP-CH-12', 'id': 'dbarline', 'nameZh': '條 + 線 雙軸', 'nameEn': 'Bar × Line', 'physicalYAxis': 2}, {'code': 'VAP-CH-13', 'id': 'evtmx', 'nameZh': '事件矩陣', 'nameEn': 'Event Matrix', 'physicalYAxis': 1}, {'code': 'VAP-CH-14', 'id': 'corrheat', 'nameZh': '相關熱力圖', 'nameEn': 'Masked Corr', 'physicalYAxis': 0}, {'code': 'VAP-CH-15', 'id': 'brush', 'nameZh': '區間量測', 'nameEn': 'Brush Measure', 'physicalYAxis': 1}, {'code': 'VAP-CH-16', 'id': 'map', 'nameZh': '地圖 × 數據', 'nameEn': 'Map', 'physicalYAxis': 0}, {'code': 'VAP-CH-17', 'id': 'roll', 'nameZh': '滾動報酬', 'nameEn': 'Rolling Returns', 'physicalYAxis': 1}, {'code': 'VAP-CH-18', 'id': 'rollcorr', 'nameZh': '滾動相關', 'nameEn': 'Rolling Correlation', 'physicalYAxis': 1}, {'code': 'VAP-CH-19', 'id': 'rollsharpe', 'nameZh': '移動夏普', 'nameEn': 'Trailing Sharpe', 'physicalYAxis': 1}, {'code': 'VAP-CH-20', 'id': 'sortino', 'nameZh': 'Sharpe × Sortino 比較', 'nameEn': 'Sharpe × Sortino', 'physicalYAxis': 2}, {'code': 'VAP-CH-21', 'id': 'radar', 'nameZh': '風險雷達', 'nameEn': 'Risk Radar', 'physicalYAxis': 0}, {'code': 'VAP-CH-22', 'id': 'alpha', 'nameZh': 'Alpha 策略', 'nameEn': 'Alpha Strategy', 'physicalYAxis': 2}, {'code': 'VAP-CH-23', 'id': 'econcal', 'nameZh': '經濟日曆', 'nameEn': 'Economic Calendar', 'physicalYAxis': 0}, {'code': 'VAP-CH-24', 'id': 'consensus', 'nameZh': '共識總覽', 'nameEn': 'Consensus Overview', 'physicalYAxis': 1}, {'code': 'VAP-CH-25', 'id': 'backtest', 'nameZh': '回測驗證', 'nameEn': 'Backtest Validation', 'physicalYAxis': 2}, {'code': 'VAP-CH-26', 'id': 'intraday', 'nameZh': '當日走勢 + 成交量', 'nameEn': 'Intraday + Volume', 'physicalYAxis': 2}, {'code': 'VAP-CH-27', 'id': 'candle', 'nameZh': 'K線 × TA × Volume', 'nameEn': 'Candlestick TA', 'physicalYAxis': 2}, {'code': 'VAP-CH-28', 'id': 'spotfut', 'nameZh': '現貨 × 期貨', 'nameEn': 'Spot × Futures', 'physicalYAxis': 1}, {'code': 'VAP-CH-29', 'id': 'hist', 'nameZh': '直方圖', 'nameEn': 'Histogram', 'physicalYAxis': 1}, {'code': 'VAP-CH-30', 'id': 'box', 'nameZh': '箱型圖', 'nameEn': 'Box Plot', 'physicalYAxis': 1}, {'code': 'VAP-CH-31', 'id': 'violin', 'nameZh': '小提琴圖', 'nameEn': 'Violin', 'physicalYAxis': 1}, {'code': 'VAP-CH-32', 'id': 'kde', 'nameZh': '核密度分布', 'nameEn': 'KDE Distribution', 'physicalYAxis': 1}, {'code': 'VAP-CH-33', 'id': 'reg', 'nameZh': '迴歸散點圖', 'nameEn': 'Regression Plot', 'physicalYAxis': 1}, {'code': 'VAP-CH-34', 'id': 'density', 'nameZh': '雙變量密度圖', 'nameEn': 'Density Contour', 'physicalYAxis': 2}, {'code': 'VAP-CH-35', 'id': 'pairgrid', 'nameZh': '配對關係矩陣', 'nameEn': 'Pair Grid', 'physicalYAxis': 0}, {'code': 'VAP-CH-36', 'id': 'facet', 'nameZh': '分面網格', 'nameEn': 'Facet Grid', 'physicalYAxis': 1}, {'code': 'VAP-CH-37', 'id': 'ecdf', 'nameZh': '經驗累積分布', 'nameEn': 'ECDF', 'physicalYAxis': 1}, {'code': 'VAP-CH-38', 'id': 'rug', 'nameZh': '邊際刻度圖', 'nameEn': 'Rug Plot', 'physicalYAxis': 1}, {'code': 'VAP-CH-39', 'id': 'resid', 'nameZh': '迴歸殘差圖', 'nameEn': 'Residual Plot', 'physicalYAxis': 1}, {'code': 'VAP-CH-40', 'id': 'joint', 'nameZh': '聯合分布網格', 'nameEn': 'Joint Grid', 'physicalYAxis': 2}], 'compositeRecipes': ['VAP-CMP-001', 'VAP-CMP-002', 'VAP-CMP-003', 'VAP-CMP-004', 'VAP-CMP-005'], 'capabilityGroups': [{'id': 'INGEST', 'scope': 'VQG 授權清單與 CSV／TSV／JSON／Endpoint／Parquet／SQLite／DuckDB 唯讀 Adapter；VDF／VRN 為上游證據', 'state': 'IMPLEMENTED'}, {'id': 'VQG_GATE', 'scope': 'VDF／VRN → VQG → VAP；Fingerprint、5000／100／252 限制、來源證據與禁止回寫', 'state': 'IMPLEMENTED'}, {'id': 'SEMANTIC', 'scope': '資料庫／資料表／欄位主詞、單位、資料類型、角色、頻率與彙總', 'state': 'IMPLEMENTED'}, {'id': 'STOCK_GATE', 'scope': '股票／ETF／股票指數只接受 Adjusted Price；TA-Lib 證據必填', 'state': 'IMPLEMENTED'}, {'id': 'MISSING_DATA', 'scope': 'VAP 保留 VQG 缺值輸出且不靜默補值；上游政策證據為價格前一交易日、扣當沖量值 0 且禁止 Carry', 'state': 'IMPLEMENTED'}, {'id': 'MARKET_TIME', 'scope': '美股 T 日映射下一個台股交易日；No-Future ASOF', 'state': 'IMPLEMENTED'}, {'id': 'SINGLE_DUAL', 'scope': '單軸或雙軸，左右系列、圖形、名稱、單位、線寬、透明度可獨立設定', 'state': 'IMPLEMENTED'}, {'id': 'AXIS_LOCK', 'scope': '左右各 4 間隔／5 刻度、相同刻度數、極值覆蓋與小數位一致', 'state': 'IMPLEMENTED'}, {'id': 'CANONICAL', 'scope': '40 張固定 Canonical 圖碼，Append-Only 且不得重新編號', 'state': 'IMPLEMENTED'}, {'id': 'COMPOSITE', 'scope': '5 個 VAP-CMP Recipe；40＋5＝45 項受管繪圖能力', 'state': 'IMPLEMENTED'}, {'id': 'OBSERVATION', 'scope': '1Y／3Y／5Y／All、Native～Yearly、Level／Change %／Rebase 100／YoY %', 'state': 'IMPLEMENTED'}, {'id': 'ANALYTICS', 'scope': 'SMA／EMA／Bollinger、異常值、參考線、Rolling、MaxDD 與反彈量測', 'state': 'IMPLEMENTED'}, {'id': 'INTERACTION', 'scope': '同步游標、點註記、框選、右鍵 Copy／Export／Inspect、Range Slider', 'state': 'IMPLEMENTED'}, {'id': 'COLLISION', 'scope': '九宮格標題、四象限 Legend、末值標籤與事件物件避碰', 'state': 'IMPLEMENTED'}, {'id': 'SNAP', 'scope': 'Grid／Data／Event Snap 與 10px／1px／0.2px 鍵盤微調', 'state': 'IMPLEMENTED'}, {'id': 'COLOR', 'scope': 'Seaborn Color Palette、220→20／VLAG 熱圖、台股紅漲綠跌', 'state': 'IMPLEMENTED'}, {'id': 'SAVE_IMAGE', 'scope': 'SVG Vector Master＋圖表契約＋語意＋Observation＋SHA-256', 'state': 'IMPLEMENTED'}, {'id': 'EXTRACT', 'scope': '搜尋、勾選、批次加入、特定保存圖與堆圖面板擷取', 'state': 'IMPLEMENTED'}, {'id': 'STACK', 'scope': 'Strict Intersection 共用時間軸、最下層唯一 X 軸、0.5×～4× 標準高度', 'state': 'IMPLEMENTED'}, {'id': 'EXPORT', 'scope': '使用者明確匯出 HTML／PNG／PDF／JSON；不自動下載', 'state': 'IMPLEMENTED'}, {'id': 'TEMPLATE', 'scope': 'Chart／HTML／Visual Preset 的 ID＋Version＋SHA Append-Only 治理', 'state': 'IMPLEMENTED'}, {'id': 'TEMPLATE_REBIND', 'scope': '模板保存角色、穩定欄位 ID、單位、型別、頻率、轉換與版面；更換 VQG 資料時自動重綁', 'state': 'IMPLEMENTED'}, {'id': 'DASHBOARD_LAYOUT', 'scope': '單圖、雙軸、共軸堆圖與其他 VAP 元件置入 12 欄防重疊 Dashboard', 'state': 'IMPLEMENTED'}, {'id': 'ASSET', 'scope': '12 Icon、16 Emoji、SVG Sanitizer、Code Point Lock', 'state': 'IMPLEMENTED'}, {'id': 'RUNTIME', 'scope': 'PowerShell → Python Loopback Runtime → VQG Sync Connect → Workbench', 'state': 'IMPLEMENTED'}, {'id': 'REFRESH', 'scope': 'Request ID、增量更新、Cache、Checkpoint 與真實回覆狀態', 'state': 'IMPLEMENTED'}, {'id': 'RESPONSIVE_UI', 'scope': 'PC 橫向／Mobile 直向、小字級、大圖＋右側可收參數', 'state': 'IMPLEMENTED'}, {'id': 'ADVANCED_RESEARCH', 'scope': '回測、Granger、Lead/Lag 與風險推論須有核准資料與獨立證據才可啟用', 'state': 'CONDITIONAL'}], 'resolvedConflicts': [{'id': 'CTX-001', 'topic': '圖表數量', 'earlier': '45 圖或 73／79 Builder 敘述', 'resolved': '40 個穩定 Canonical 圖碼＋5 個 Composite Recipe＝45 項受管能力；73／79 視為歷史別名與重複候選，不宣告為 Canonical', 'rule': 'DEDUP_PRESERVE_ALIAS'}, {'id': 'CTX-002', 'topic': '實體 Y 軸數', 'earlier': '三軸跨頻原型', 'resolved': '實體 Y 軸最多兩個；第三尺度以 Rebase／Min-Max／Z-Score 後掛入左或右軸', 'rule': 'TWO_PHYSICAL_AXES_MAX'}, {'id': 'CTX-003', 'topic': '軸步長家族', 'earlier': '2／2.5／5 × 10ⁿ', 'resolved': '採較新的明確要求 1.25／2.5／5 × 10ⁿ；10 僅作下一十進位邊界', 'rule': 'LATEST_EXPLICIT'}, {'id': 'CTX-004', 'topic': '線寬', 'earlier': '統一線粗 1.0', 'resolved': '資料線 1.2、Benchmark 1.0、重要線 1.4；個別規格可在合法範圍覆寫', 'rule': 'ROLE_BASED_STYLE'}, {'id': 'CTX-005', 'topic': 'Bar 透明度', 'earlier': '0.6 或 0.75', 'resolved': '單獨 Bar 預設 0.6；線＋Bar 雙軸混合時 Bar 預設 0.25', 'rule': 'CONTEXTUAL_STYLE'}, {'id': 'CTX-006', 'topic': '回測與進階推論', 'earlier': '先不做回測／Lead-Lag／Granger', 'resolved': '圖型與介面保留；正式計算維持 Conditional，未有核准來源、方法與 UAT 證據不得啟用', 'rule': 'FAIL_CLOSED_CAPABILITY'}, {'id': 'CTX-007', 'topic': '真實資料接線', 'earlier': '先不接真實資料源', 'resolved': '後續明確改為 VDF 授權、唯讀 Runtime 與 Sync Connect；Request 不等於成功，必須收到匹配回覆', 'rule': 'LATER_REQUIREMENT_SUPERSEDES'}, {'id': 'CTX-008', 'topic': '股票價格', 'earlier': 'Close 可作退路', 'resolved': '股票／ETF／股票指數只接受 VDF 核准 Adjusted Price，禁止 Raw Close Fallback；TA-Lib 只做計算不下載價格', 'rule': 'HARD_DATA_GATE'}, {'id': 'CTX-009', 'topic': '空值', 'earlier': '一般插值或平均', 'resolved': '價格只取前一交易日；成交量填 0 且不可沿用；禁止未來值與兩日平均', 'rule': 'NO_FUTURE_NO_DOUBLE_COUNT'}, {'id': 'CTX-010', 'topic': '啟用', 'earlier': '測試後啟用', 'resolved': '產生 Candidate Seal；Runtime Promotion 仍需明確外部審查，瀏覽器未執行不得宣稱全部啟用', 'rule': 'FAIL_CLOSED_ACTIVATION'}, {'id': 'CTX-011', 'topic': 'MacroMicro 基準', 'earlier': 'MACROMICRO 樣式', 'resolved': '只採先讀圖再調參數、區間／頻率／最新值等互動基準，不複製品牌視覺或內容', 'rule': 'UX_REFERENCE_NOT_BRAND_COPY'}, {'id': 'CTX-012', 'topic': 'VAP 正式資料入口', 'earlier': 'VAP 直接接 VDF Runtime Catalog', 'resolved': '正式管線改為 VDF／VRN → VQG 唯讀品質驗證 → VAP；VAP 不重算、不修補、不回寫上游', 'rule': 'VQG_ONLY_PRESENTATION_BOUNDARY'}], 'legacyCompatibility': {'chartCount': 28, 'charts': [{'group': 'single', 'code': 'VAP-CH-01', 'id': 'line', 'zh': '折線圖', 'en': 'Line', 'axes': 1, 'dataShape': 'series[]', 'fields': ['date', 'value'], 'use': '水準/指數趨勢'}, {'group': 'single', 'code': 'VAP-CH-02', 'id': 'area', 'zh': '面積折線', 'en': 'Area', 'axes': 1, 'dataShape': 'series', 'fields': ['date', 'value'], 'use': '單一序列強調量體', 'override': {'fill.areaUnderLine': 0.75}}, {'group': 'single', 'code': 'VAP-CH-03', 'id': 'bar', 'zh': '直條圖', 'en': 'Bar', 'axes': 1, 'dataShape': 'categorical', 'fields': ['label', 'value'], 'use': '分項比較'}, {'group': 'single', 'code': 'VAP-CH-04', 'id': 'hbar', 'zh': '橫條圖', 'en': 'H-Bar', 'axes': 1, 'dataShape': 'categorical', 'fields': ['label', 'value'], 'use': '長標籤分項(CPI 分項左負右正)'}, {'group': 'single', 'code': 'VAP-CH-05', 'id': 'scatter', 'zh': '散點圖', 'en': 'Scatter', 'axes': 1, 'dataShape': 'xy', 'fields': ['x', 'y'], 'use': '兩變數關係'}, {'group': 'stack', 'code': 'VAP-CH-06', 'id': 'sarea', 'zh': '堆疊面積', 'en': 'Stacked Area', 'axes': 1, 'dataShape': 'series[]', 'fields': ['date', 'value', 'group'], 'use': '組成消長'}, {'group': 'stack', 'code': 'VAP-CH-07', 'id': 'sbar', 'zh': '堆疊直條', 'en': 'Stacked Bar', 'axes': 1, 'dataShape': 'categorical[]', 'fields': ['label', 'value', 'group'], 'use': '財政收支結構(間隙最小化)', 'override': {'bar.gapFactor': 'tight'}}, {'group': 'stack', 'code': 'VAP-CH-08', 'id': 'sbar100', 'zh': '百分比堆疊', 'en': '100% Stacked', 'axes': 1, 'dataShape': 'categorical[]', 'fields': ['label', 'value', 'group'], 'use': '占比結構'}, {'group': 'indiv', 'code': 'VAP-CH-09', 'id': 'multi', 'zh': '個別小圖', 'en': 'Small Multiples', 'axes': 1, 'dataShape': 'series[]', 'fields': ['date', 'value', 'panel'], 'use': '多標的同軸比較', 'override': {'grid': '2x2'}}, {'group': 'indiv', 'code': 'VAP-CH-10', 'id': 'gbar', 'zh': '並列直條', 'en': 'Grouped Bar', 'axes': 1, 'dataShape': 'categorical[]', 'fields': ['label', 'value', 'group'], 'use': '官方×民間數據對照'}, {'group': 'dual', 'code': 'VAP-CH-11', 'id': 'dline', 'zh': '底色面積 × 對比折線', 'en': 'Area × Line', 'axes': 2, 'dataShape': 'series×2', 'fields': ['date', 'left', 'right'], 'use': '一邊底色一邊折線(信心指數 × 零售年增率)', 'rule': '底色序列置右軸 α0.75;折線置左軸 lw1'}, {'group': 'dual', 'code': 'VAP-CH-12', 'id': 'dbarline', 'zh': '條 + 線 雙軸', 'en': 'Bar × Line', 'axes': 2, 'dataShape': 'mixed', 'fields': ['date', 'bar', 'line'], 'use': '非農新增(條) × 失業率(線)'}, {'group': 'adv', 'code': 'VAP-CH-13', 'id': 'evtmx', 'zh': '事件矩陣', 'en': 'Event Matrix', 'axes': 1, 'dataShape': 'series+events', 'fields': ['date', 'value', 'events[]'], 'use': '危機事件對照', 'rule': '垂直虛線 0.8/0.8 · 區間陰影 0.3 · 無水平線'}, {'group': 'adv', 'code': 'VAP-CH-14', 'id': 'corrheat', 'zh': '相關熱力圖', 'en': 'Masked Corr', 'axes': 0, 'dataShape': 'matrix', 'fields': ['corr'], 'use': '資產相關性', 'rule': '下三角遮罩 · zmid 0 · seaborn 15 級色階'}, {'group': 'adv', 'code': 'VAP-CH-15', 'id': 'brush', 'zh': '區間量測', 'en': 'Brush Measure', 'axes': 1, 'dataShape': 'series', 'fields': ['date', 'value'], 'use': '拉選區間求高低/MaxDD/耗時'}, {'group': 'adv', 'code': 'VAP-CH-16', 'id': 'map', 'zh': '地圖 × 數據', 'en': 'Map', 'axes': 0, 'dataShape': 'geo', 'fields': ['region', 'value', 'change'], 'use': '全球/美國/歐洲/東亞/台灣', 'engine': 'leaflet', 'rule': '漲跌以上下三角標示'}, {'group': 'rolling', 'code': 'VAP-CH-17', 'id': 'roll', 'zh': '滾動報酬', 'en': 'Rolling Returns', 'axes': 1, 'dataShape': 'series', 'fields': ['date', 'return'], 'use': '期間績效穩定度'}, {'group': 'rolling', 'code': 'VAP-CH-18', 'id': 'rollcorr', 'zh': '滾動相關', 'en': 'Rolling Correlation', 'axes': 1, 'dataShape': 'series×2', 'fields': ['date', 'a', 'b'], 'use': '關係變化'}, {'group': 'rolling', 'code': 'VAP-CH-19', 'id': 'rollsharpe', 'zh': '移動夏普', 'en': 'Trailing Sharpe', 'axes': 1, 'dataShape': 'series', 'fields': ['date', 'sharpe'], 'use': '風險調整後報酬'}, {'group': 'rolling', 'code': 'VAP-CH-20', 'id': 'sortino', 'zh': 'Sharpe × Sortino 比較', 'en': 'Sharpe × Sortino', 'axes': 2, 'dataShape': 'series×2', 'fields': ['date', 'sharpe', 'sortino'], 'use': '下行風險與總波動對照', 'rule': '左軸 Sharpe · 右軸 Sortino · 同等格數'}, {'group': 'rolling', 'code': 'VAP-CH-21', 'id': 'radar', 'zh': '風險雷達', 'en': 'Risk Radar', 'axes': 0, 'dataShape': 'radial', 'fields': ['metric', 'value', 'benchmark'], 'use': '多維風險輪廓(波動·MaxDD·Beta·集中度·流動性)', 'rule': '基準線為外圈虛線 · 填色 α0.3'}, {'group': 'rolling', 'code': 'VAP-CH-22', 'id': 'alpha', 'zh': 'Alpha 策略', 'en': 'Alpha Strategy', 'axes': 2, 'dataShape': 'series×3', 'fields': ['date', 'strategy', 'benchmark', 'excess'], 'use': '策略 vs 基準 + 超額報酬', 'rule': '累積績效置左軸 · 超額報酬置右軸直條(漇2跌綣) · 0 軸紅線'}, {'group': 'rolling', 'code': 'VAP-CH-23', 'id': 'econcal', 'zh': '經濟日曆', 'en': 'Economic Calendar', 'axes': 0, 'dataShape': 'events', 'fields': ['date', 'event', 'importance', 'actual', 'forecast', 'previous'], 'use': '重要數據發布時程與預期落差', 'rule': '重要度以紅黃綠三階 · 實際優於預期標紅'}, {'group': 'rolling', 'code': 'VAP-CH-25', 'id': 'backtest', 'zh': '回測驗證', 'en': 'Backtest Validation', 'axes': 2, 'dataShape': 'matrix+series', 'fields': ['lag', 'rankIC', 'tStat', 'pValue'], 'use': 'Rank-IC 衰減 × 顯著性', 'rule': '左軸 Rank-IC 直條 · 右軸 t 統計量折線 · |t|=1.96 水平基準線 0.8'}, {'group': 'ta', 'code': 'VAP-CH-26', 'id': 'intraday', 'zh': '當日走勢 + 成交量', 'en': 'Intraday + Volume', 'axes': 2, 'dataShape': 'ohlcv', 'fields': ['time', 'price', 'volume'], 'use': '當日盤勢', 'rule': 'rows=2 · row_heights [.72,.28] · shared_xaxes'}, {'group': 'ta', 'code': 'VAP-CH-27', 'id': 'candle', 'zh': 'K線 × SMA/EMA/BB × Volume', 'en': 'Candlestick TA', 'axes': 2, 'dataShape': 'ohlcv', 'fields': ['date', 'open', 'high', 'low', 'close', 'volume'], 'use': '技術分析', 'rule': 'adj price · split 調整'}, {'group': 'ta', 'code': 'VAP-CH-28', 'id': 'spotfut', 'zh': '現貨 × 期貨', 'en': 'Spot × Futures', 'axes': 1, 'dataShape': 'series[]', 'fields': ['date', 'spot', 'futures'], 'use': 'BRENT / WTI / GOLD 基差', 'rule': '現貨實線 · 期貨虛線 · 基差標籤堆疊 ≥9px'}, {'group': 'fund', 'code': 'VAP-CH-24', 'id': 'consensus', 'zh': '共識總覽', 'en': 'Consensus Overview', 'axes': 1, 'dataShape': 'table', 'fields': ['dilutedEPS', 'targetPrice', 'rating', 'analystCount', 'forwardPER', 'forwardPBR'], 'use': 'yfinance / FactSet 共識', 'rule': '綠黃紅 spectrum · 目標價取左右最長'}], 'legacySpecVersion': '1.0.0', 'resolution': 'Legacy 28-chart library is preserved for import/lineage only; active registry is append-only 40 canonical + 5 composite.'}, 'sourceEvidence': {'package': 'VAP_v027_Complete_System_Package(1).zip', 'requirementsTextSha256': 'df2d7fbeaa27f79be90221c20611508b0933b540357d8bbd1794624566fcdf3d', 'duplicateRequirementsAttachmentConfirmed': True}}
EMBEDDED_DEMO_CSV = 'date,factor,net_volume,net_turnover,status\n2024-01-31,TWSE_EX_2330,132000000,31800000000,OK\n2024-02-29,TWSE_EX_2330,141000000,33700000000,OK\n2024-03-29,TWSE_EX_2330,136000000,32900000000,OK\n2024-04-30,TWSE_EX_2330,152000000,36100000000,OK\n2024-05-31,TWSE_EX_2330,158000000,37400000000,OK\n2024-06-28,TWSE_EX_2330,149000000,35600000000,OK\n2024-07-31,TWSE_EX_2330,166000000,38900000000,OK\n2024-08-30,TWSE_EX_2330,171000000,40100000000,OK\n2024-09-30,TWSE_EX_2330,164000000,39200000000,OK\n2024-10-31,TWSE_EX_2330,178000000,41600000000,OK\n2024-11-29,TWSE_EX_2330,183000000,42900000000,OK\n2024-12-31,TWSE_EX_2330,176000000,41800000000,OK\n2025-01-31,TWSE_EX_2330,187000000,44100000000,OK\n2025-02-28,TWSE_EX_2330,193000000,45600000000,OK\n2025-03-31,TWSE_EX_2330,189000000,44900000000,OK\n2025-04-30,TWSE_EX_2330,201000000,47200000000,OK\n2025-05-30,TWSE_EX_2330,208000000,48700000000,OK\n2025-06-30,TWSE_EX_2330,204000000,48100000000,OK\n2025-07-31,TWSE_EX_2330,216000000,50600000000,OK\n2025-08-29,TWSE_EX_2330,221000000,51900000000,OK\n2025-09-30,TWSE_EX_2330,214000000,51100000000,OK\n2025-10-31,TWSE_EX_2330,229000000,53600000000,OK\n2025-11-28,TWSE_EX_2330,235000000,55100000000,OK\n2025-12-31,TWSE_EX_2330,231000000,54400000000,OK\n2026-01-30,TWSE_EX_2330,243000000,56800000000,OK\n2026-02-27,TWSE_EX_2330,249000000,58100000000,OK\n2026-03-31,TWSE_EX_2330,246000000,57500000000,OK\n2026-04-30,TWSE_EX_2330,258000000,60400000000,OK\n2026-05-29,TWSE_EX_2330,266000000,61900000000,OK\n2026-06-30,TWSE_EX_2330,279000000,64600000000,OK\n'


_def_load_config_external = def_load_config
_def_load_vdf_manifest_external = def_load_vdf_manifest
_def_load_vqg_manifest_external = def_load_vqg_manifest


def def_connection_fingerprint(connection: dict[str, Any]) -> str:
    payload = {key: value for key, value in connection.items() if key != "fingerprint"}
    return def_sha256_text(def_canonical_json(payload))


def def_atomic_write(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.parent.mkdir(parents=True, exist_ok=True)
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def def_validate_connection(connection: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ("contractId", "sourceId", "state", "engine", "assetClass"):
        if not str(connection.get(field, "")).strip():
            errors.append("MISSING_" + field.upper())
    if connection.get("state") == "AUTHORIZED" and not connection.get("readOnly", False):
        errors.append("AUTHORIZED_CONNECTION_MUST_BE_READ_ONLY")
    if str(connection.get("assetClass", "")).upper() in {"STOCK", "EQUITY", "ETF", "STOCK_INDEX"}:
        if not str(connection.get("adjustedPriceField", "")).lower().startswith(("adj", "adjusted")):
            errors.append("ADJUSTED_PRICE_FIELD_REQUIRED")
        ta_lib = dict(connection.get("taLibEvidence", {}))
        if ta_lib.get("engine") != "TA-Lib" or ta_lib.get("status") != "PASS":
            errors.append("TALIB_PASS_EVIDENCE_REQUIRED")
    if connection.get("fingerprint") != def_connection_fingerprint(connection):
        errors.append("FINGERPRINT_MISMATCH")
    return errors


def def_manifest_status(manifest: dict[str, Any], schema: str) -> dict[str, Any]:
    records = manifest.get("connections", []) if isinstance(manifest, dict) else []
    return {
        "schema": schema,
        "status": "PASS" if manifest.get("schema") == schema and isinstance(records, list) else "FAIL",
        "connections": len(records),
        "authorized": sum(1 for row in records if row.get("state") == "AUTHORIZED" and row.get("readOnly") is True),
    }


def def_prepare_embedded_runtime_assets(package_root: Path) -> Path:
    target = package_root / "state" / "embedded" / "vqg_demo_activity.csv"
    if not target.exists() or target.read_text(encoding="utf-8-sig") != EMBEDDED_DEMO_CSV:
        def_atomic_write_text(target, EMBEDDED_DEMO_CSV)
    return target


def def_load_config(path: Path) -> dict[str, Any]:
    root = def_package_root()
    def_prepare_embedded_runtime_assets(root)
    if path.is_file():
        return _def_load_config_external(path)
    config = json.loads(json.dumps(EMBEDDED_RUNTIME_CONFIG))
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
    config["port"] = int(config.get("port", DEFAULT_PORT))
    config["maxRows"] = max(3, min(int(config.get("maxRows", DEFAULT_MAX_ROWS)), 100_000))
    config["maxBodyBytes"] = max(1024, min(int(config.get("maxBodyBytes", DEFAULT_MAX_BODY_BYTES)), 100 * 1024 * 1024))
    config["sources"] = [source for source in config.get("sources", []) if source.get("enabled", True)]
    if config["host"] not in {"127.0.0.1", "localhost", "::1"}:
        raise PermissionError("RUNTIME_MUST_BIND_LOOPBACK")
    if not 1024 <= config["port"] <= 65535:
        raise ValueError("PORT_OUT_OF_RANGE")
    if config.get("formalInputAuthority") != "VQG":
        raise PermissionError("FORMAL_INPUT_AUTHORITY_MUST_BE_VQG")
    if any(str(source.get("authority", "")).upper() != "VQG" for source in config["sources"]):
        raise PermissionError("NON_VQG_FORMAL_SOURCE_REJECTED")
    return config


def def_load_vdf_manifest(package_root: Path, config: dict[str, Any]) -> dict[str, Any]:
    location = str(dict(config.get("vdfGateway", {})).get("manifest", ""))
    if location.startswith("embedded://"):
        return json.loads(json.dumps(EMBEDDED_VDF_MANIFEST))
    return _def_load_vdf_manifest_external(package_root, config)


def def_load_vqg_manifest(package_root: Path, config: dict[str, Any]) -> dict[str, Any]:
    location = str(dict(config.get("vqgGateway", {})).get("manifest", ""))
    if location.startswith("embedded://"):
        return json.loads(json.dumps(EMBEDDED_VQG_MANIFEST))
    return _def_load_vqg_manifest_external(package_root, config)


def def_unified_inventory_summary() -> dict[str, Any]:
    counts = dict(EMBEDDED_FUNCTION_INVENTORY.get("counts", {}))
    return {
        "schema": EMBEDDED_FUNCTION_INVENTORY.get("schema"),
        "version": APP_VERSION,
        "status": "PASS" if counts.get("managedPlotCapabilities") == 45 else "FAIL",
        "counts": counts,
    }


def def_run_self_test(runtime: CatalogRuntime) -> dict[str, Any]:
    refresh = runtime.refresh("VAP-V0300-SELFTEST", ["ALL"], "FULL")
    ui_path = runtime.package_root / DEFAULT_UI_RELATIVE_PATH
    ui_text = ui_path.read_text(encoding="utf-8-sig") if ui_path.is_file() else ""
    vdf_records = EMBEDDED_VDF_MANIFEST.get("connections", [])
    checks = {
        "loopback": runtime.config["host"] in {"127.0.0.1", "localhost", "::1"},
        "formalInputAuthority": runtime.config.get("formalInputAuthority") == "VQG",
        "vdfManifest": def_manifest_status(EMBEDDED_VDF_MANIFEST, VDF_SCHEMA)["status"] == "PASS",
        "vqgManifest": def_manifest_status(EMBEDDED_VQG_MANIFEST, VQG_SCHEMA)["status"] == "PASS",
        "vdfFingerprints": all(not def_validate_connection(row) for row in vdf_records),
        "demoRefresh": bool(refresh.tables) and not refresh.errors,
        "uiExists": ui_path.is_file(),
        "uiStandalone": '<script src="../js/' not in ui_text,
        "uiInventory": "vap-unified-function-inventory" in ui_text,
        "canonicalCharts": EMBEDDED_CHART_REGISTRY.get("canonicalCount") == 40,
        "compositeRecipes": EMBEDDED_CHART_REGISTRY.get("compositeRecipeCount") == 5,
        "managedPlotCapabilities": EMBEDDED_FUNCTION_INVENTORY.get("counts", {}).get("managedPlotCapabilities") == 45,
        "legacyLineage": EMBEDDED_FUNCTION_INVENTORY.get("counts", {}).get("legacyCharts") == 28,
        "functionInventory": EMBEDDED_FUNCTION_INVENTORY.get("counts", {}).get("totalNamedFunctions", 0) >= 580,
        "readOnlyEngines": ALLOWED_ENGINES == {"CSV", "TSV", "JSON", "JSON_ENDPOINT", "PARQUET", "SQLITE", "DUCKDB"},
        "sqlWriteGuard": bool(FORBIDDEN_SQL_PATTERN.search("UPDATE prices SET close=1")),
    }
    return {
        "schema": "VIA-VAP-ALL-IN-ONE-SELFTEST/1.0",
        "version": APP_VERSION,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "refresh": refresh.as_dict(),
        "inventory": def_unified_inventory_summary(),
        "health": runtime.health(),
    }


if __name__ == "__main__":
    raise SystemExit(def_main())
