"""Unified file/database discovery, profiling and chart-field suggestion."""

from __future__ import annotations

import json
import math
import re
import sqlite3
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import numpy as np
import pandas as pd

from vap_defaults import load_defaults
from vap_atomic_io import atomic_write_json, file_transaction_lock
from vap_quality_engine import DEFAULT_OUTLIER_IQR_MULTIPLIER, audit_frame


# =============================================================================
# 0. 資料層參數
# =============================================================================

SOURCE_SCHEMA = "VIA-VAP-DATA-SOURCE/2.2"
SOURCE_VERSION = "2.2.0"
DEFAULT_SAMPLE_ROWS = 5000
DEFAULT_MAX_ROWS = 500000
SQLITE_SUFFIXES = {".sqlite", ".sqlite3", ".db"}
DUCKDB_SUFFIXES = {".duckdb", ".ddb"}
PARQUET_SUFFIXES = {".parquet", ".pq"}
EXCEL_SUFFIXES = {".xlsx", ".xls"}
JSON_SUFFIXES = {".json", ".jsonl"}
TEXT_SUFFIXES = {".csv", ".txt", ".tsv"}
SAFE_READ_QUERY_PATTERN = re.compile(r"^\s*(select|with)\b", flags=re.IGNORECASE)
UNSAFE_QUERY_TOKEN_PATTERN = re.compile(
    r"\b(insert|update|delete|merge|drop|alter|create|attach|detach|copy|call|pragma|vacuum|truncate|replace)\b",
    flags=re.IGNORECASE,
)
NUMERIC_SEMANTIC_TYPES = {"price", "volume", "currency", "percentage", "flow", "count", "numeric"}
DATE_NAME_PATTERN = re.compile(r"(^|[_\s])(date|datetime|time|timestamp)([_\s]|$)|日期|時間", re.IGNORECASE)
SENSITIVE_QUERY_KEY_SUFFIXES = (
    "password",
    "passwd",
    "pwd",
    "token",
    "secret",
    "api_key",
    "apikey",
    "access_key",
    "secret_key",
    "signature",
    "credential",
    "private_key",
    "passphrase",
    "sig",
    "odbc_connect",
)
REDACTED_QUERY_VALUE = "REDACTED"


# =============================================================================
# 1. 來源正規化與型別偵測
# =============================================================================


def optional_import(module_name: str) -> Any | None:
    try:
        return __import__(module_name)
    except ImportError:
        return None


def resolve_source_path(raw_path: str, config_directory: Path | None = None) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path
    base = config_directory or Path.cwd()
    return (base / path).resolve()


def sniff_source_kind(path: Path) -> str:
    """Identify extensionless sources from conservative file signatures/content."""
    if not path.is_file():
        return "unknown"
    with path.open("rb") as handle:
        header = handle.read(16384)
    if header.startswith(b"PAR1"):
        return "parquet"
    if header.startswith(b"SQLite format 3\x00"):
        return "sqlite"
    if len(header) >= 12 and header[8:12] == b"DUCK":
        return "duckdb"
    if header.startswith(b"PK\x03\x04"):
        return "excel"
    if header.startswith(bytes.fromhex("D0CF11E0A1B11AE1")):
        return "excel"
    decoded = ""
    for encoding in ("utf-8-sig", "cp950", "big5"):
        try:
            decoded = header.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    stripped = decoded.lstrip()
    if stripped.startswith("[") or stripped.startswith("{"):
        first_lines = [line for line in stripped.splitlines() if line.strip()][:2]
        return "jsonl" if len(first_lines) > 1 and all(line.lstrip().startswith("{") for line in first_lines) else "json"
    if decoded:
        first_line = next((line for line in decoded.splitlines() if line.strip()), "")
        if "\t" in first_line and first_line.count("\t") >= first_line.count(","):
            return "tsv"
        if any(delimiter in first_line for delimiter in [",", ";", "|"]):
            return "csv"
    return "unknown"


def detect_source_kind(raw_source: str | Path) -> str:
    source_text = str(raw_source).strip()
    if "://" in source_text:
        return "sqlalchemy"
    path = Path(source_text).expanduser()
    if path.is_dir():
        parquet_files = list(path.rglob("*.parquet")) + list(path.rglob("*.pq"))
        return "parquet_dataset" if parquet_files else "directory"
    suffix = path.suffix.lower()
    if suffix in SQLITE_SUFFIXES:
        return "sqlite"
    if suffix in DUCKDB_SUFFIXES:
        return "duckdb"
    if suffix in EXCEL_SUFFIXES:
        return "excel"
    if suffix in JSON_SUFFIXES:
        return "jsonl" if suffix == ".jsonl" else "json"
    if suffix == ".tsv":
        return "tsv"
    if suffix in TEXT_SUFFIXES:
        return "csv"
    if suffix in PARQUET_SUFFIXES:
        return "parquet"
    if not suffix and path.exists():
        return sniff_source_kind(path)
    return "unknown"


def normalize_source_spec(source: str | Path | dict[str, Any]) -> dict[str, Any]:
    if isinstance(source, dict):
        result = dict(source)
    else:
        source_text = str(source)
        result = {"path": source_text, "kind": detect_source_kind(source_text)}
    if not result.get("kind"):
        locator = result.get("url") or result.get("path") or ""
        result["kind"] = detect_source_kind(str(locator))
    result["schema"] = SOURCE_SCHEMA
    result["version"] = SOURCE_VERSION
    result.setdefault("table", "")
    result.setdefault("sheet", "")
    result.setdefault("query", "")
    result.setdefault("encoding", "utf-8-sig")
    return result


def sanitize_connection_url(raw_url: str) -> str:
    parts = urlsplit(raw_url)
    hostname = parts.hostname or ""
    if ":" in hostname and not hostname.startswith("["):
        hostname = f"[{hostname}]"
    port = f":{parts.port}" if parts.port else ""
    username = f"{parts.username}@" if parts.username else ""
    safe_netloc = f"{username}{hostname}{port}"
    safe_query_items: list[tuple[str, str]] = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        with_acronym_boundaries = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", key)
        with_word_boundaries = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", with_acronym_boundaries)
        normalized_key = re.sub(r"[^a-z0-9]+", "_", with_word_boundaries.casefold()).strip("_")
        is_sensitive = normalized_key == "odbc_connect" or any(
            normalized_key == suffix or normalized_key.endswith(f"_{suffix}")
            for suffix in SENSITIVE_QUERY_KEY_SUFFIXES
        )
        safe_query_items.append((key, REDACTED_QUERY_VALUE if is_sensitive else value))
    safe_query = urlencode(safe_query_items, doseq=True)
    # URL fragments are never needed for a database connection and sometimes
    # carry bearer material in copied URLs, so omit them from saved manifests.
    return urlunsplit((parts.scheme, safe_netloc, parts.path, safe_query, ""))


def sqlite_readonly_uri(path: Path) -> str:
    """Build an encoded SQLite file URI whose read-only flag cannot be swallowed."""

    return f"{path.expanduser().resolve().as_uri()}?mode=ro"


def quote_identifier(identifier: str) -> str:
    if not identifier or "\x00" in identifier:
        raise ValueError("資料表或欄位名稱無效。")
    return '"' + identifier.replace('"', '""') + '"'


def ensure_read_only_query(query: str) -> str:
    stripped = query.strip().rstrip(";")
    if not SAFE_READ_QUERY_PATTERN.match(stripped):
        raise ValueError("只允許 SELECT 或 WITH 開頭的唯讀查詢。")
    if ";" in stripped:
        raise ValueError("查詢不可包含多重 SQL statement。")
    if UNSAFE_QUERY_TOKEN_PATTERN.search(stripped):
        raise ValueError("查詢含有非唯讀 SQL 關鍵字。")
    return stripped


# =============================================================================
# 2. 資料表與欄位擷取
# =============================================================================


def list_sqlite_tables(path: Path) -> list[str]:
    with sqlite3.connect(sqlite_readonly_uri(path), uri=True) as connection:
        rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table','view') "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
    return [str(row[0]) for row in rows]


def list_duckdb_tables(path: Path) -> list[str]:
    duckdb = optional_import("duckdb")
    if duckdb is None:
        raise RuntimeError("讀取 DuckDB 需要安裝 duckdb。")
    connection = duckdb.connect(str(path), read_only=True)
    try:
        rows = connection.execute(
            "SELECT table_schema, table_name FROM information_schema.tables "
            "WHERE table_schema NOT IN ('information_schema','pg_catalog') "
            "ORDER BY table_schema, table_name"
        ).fetchall()
    finally:
        connection.close()
    return [f"{schema}.{table}" if schema != "main" else str(table) for schema, table in rows]


def list_excel_sheets(path: Path) -> list[str]:
    with pd.ExcelFile(path) as workbook:
        return [str(name) for name in workbook.sheet_names]


def list_parquet_dataset_tables(path: Path) -> list[str]:
    files = list(path.rglob("*.parquet")) + list(path.rglob("*.pq"))
    return sorted(str(file.relative_to(path)) for file in files)


def list_sqlalchemy_tables(url: str) -> list[str]:
    sqlalchemy = optional_import("sqlalchemy")
    if sqlalchemy is None:
        raise RuntimeError("讀取遠端資料庫需要安裝 SQLAlchemy 與對應 driver。")
    engine = sqlalchemy.create_engine(url)
    try:
        inspector = sqlalchemy.inspect(engine)
        tables: list[str] = []
        for schema in inspector.get_schema_names():
            schema_name = str(schema or "")
            if schema_name.lower() in {"information_schema", "pg_catalog", "sys"}:
                continue
            table_names = list(inspector.get_table_names(schema=schema)) + list(inspector.get_view_names(schema=schema))
            for table in sorted(set(table_names)):
                tables.append(f"{schema_name}.{table}" if schema_name else table)
        return sorted(tables)
    finally:
        engine.dispose()


def list_source_tables(source: str | Path | dict[str, Any], config_directory: Path | None = None) -> list[str]:
    spec = normalize_source_spec(source)
    kind = str(spec["kind"])
    if kind == "sqlalchemy":
        return list_sqlalchemy_tables(str(spec.get("url") or spec.get("path") or ""))
    path = resolve_source_path(str(spec.get("path", "")), config_directory)
    if kind in {"unknown", "auto"} or (not path.suffix and kind == "parquet"):
        kind = sniff_source_kind(path)
        spec["kind"] = kind
    if kind == "sqlite":
        return list_sqlite_tables(path)
    if kind == "duckdb":
        return list_duckdb_tables(path)
    if kind == "excel":
        return list_excel_sheets(path)
    if kind == "parquet_dataset":
        return list_parquet_dataset_tables(path)
    if kind in {"csv", "tsv", "parquet", "json", "jsonl"}:
        return [path.name]
    return []


def selected_column_sql(columns: Iterable[str] | None) -> str:
    column_list = [str(column) for column in columns or []]
    if not column_list:
        return "*"
    return ", ".join(quote_identifier(column) for column in column_list)


def split_schema_table(name: str) -> tuple[str | None, str]:
    if "." not in name:
        return None, name
    schema, table = name.split(".", 1)
    return schema, table


def sqlite_declared_schema(path: Path, table: str) -> dict[str, Any]:
    with sqlite3.connect(sqlite_readonly_uri(path), uri=True) as connection:
        rows = connection.execute(f"PRAGMA table_info({quote_identifier(table)})").fetchall()
        index_rows = connection.execute(f"PRAGMA index_list({quote_identifier(table)})").fetchall()
    return {
        "columns": [
            {
                "ordinal": int(row[0]),
                "name": str(row[1]),
                "declared_type": str(row[2] or ""),
                "nullable": not bool(row[3]),
                "default": row[4],
                "primary_key_position": int(row[5]),
            }
            for row in rows
        ],
        "primary_key": [str(row[1]) for row in rows if int(row[5]) > 0],
        "indexes": [str(row[1]) for row in index_rows],
    }


def duckdb_declared_schema(path: Path, table: str) -> dict[str, Any]:
    duckdb = optional_import("duckdb")
    if duckdb is None:
        return {"columns": [], "primary_key": [], "indexes": [], "warning": "duckdb 未安裝"}
    schema, plain_table = split_schema_table(table)
    target_schema = schema or "main"
    connection = duckdb.connect(str(path), read_only=True)
    try:
        rows = connection.execute(
            "SELECT ordinal_position, column_name, data_type, is_nullable, column_default "
            "FROM information_schema.columns WHERE table_schema = ? AND table_name = ? ORDER BY ordinal_position",
            [target_schema, plain_table],
        ).fetchall()
    finally:
        connection.close()
    return {
        "columns": [
            {
                "ordinal": int(row[0]),
                "name": str(row[1]),
                "declared_type": str(row[2]),
                "nullable": str(row[3]).upper() == "YES",
                "default": row[4],
                "primary_key_position": 0,
            }
            for row in rows
        ],
        "primary_key": [],
        "indexes": [],
    }


def sqlalchemy_declared_schema(url: str, table: str) -> dict[str, Any]:
    sqlalchemy = optional_import("sqlalchemy")
    if sqlalchemy is None:
        return {"columns": [], "primary_key": [], "indexes": [], "warning": "SQLAlchemy 未安裝"}
    schema, plain_table = split_schema_table(table)
    engine = sqlalchemy.create_engine(url)
    try:
        inspector = sqlalchemy.inspect(engine)
        columns = inspector.get_columns(plain_table, schema=schema)
        primary_key = inspector.get_pk_constraint(plain_table, schema=schema).get("constrained_columns") or []
        indexes = inspector.get_indexes(plain_table, schema=schema)
        return {
            "columns": [
                {
                    "ordinal": index + 1,
                    "name": str(column.get("name", "")),
                    "declared_type": str(column.get("type", "")),
                    "nullable": bool(column.get("nullable", True)),
                    "default": str(column.get("default")) if column.get("default") is not None else None,
                    "primary_key_position": primary_key.index(column.get("name")) + 1 if column.get("name") in primary_key else 0,
                }
                for index, column in enumerate(columns)
            ],
            "primary_key": [str(column) for column in primary_key],
            "indexes": [str(index.get("name", "")) for index in indexes],
        }
    finally:
        engine.dispose()


def source_declared_schema(spec: dict[str, Any], config_directory: Path | None = None) -> dict[str, Any]:
    kind = str(spec.get("kind", ""))
    table = str(spec.get("table") or spec.get("sheet") or "")
    if not table:
        return {"columns": [], "primary_key": [], "indexes": []}
    if kind == "sqlalchemy":
        return sqlalchemy_declared_schema(str(spec.get("url") or spec.get("path") or ""), table)
    path = resolve_source_path(str(spec.get("path", "")), config_directory)
    if kind == "sqlite":
        return sqlite_declared_schema(path, table)
    if kind == "duckdb":
        return duckdb_declared_schema(path, table)
    return {"columns": [], "primary_key": [], "indexes": []}


def read_sqlite_frame(
    path: Path,
    spec: dict[str, Any],
    columns: Iterable[str] | None,
    limit: int | None,
) -> pd.DataFrame:
    table = str(spec.get("table", ""))
    query = str(spec.get("query", "")).strip()
    if query:
        sql = ensure_read_only_query(query)
        sql = f"SELECT {selected_column_sql(columns)} FROM ({sql}) AS vap_query"
    elif table:
        sql = f"SELECT {selected_column_sql(columns)} FROM {quote_identifier(table)}"
    else:
        tables = list_sqlite_tables(path)
        if not tables:
            raise ValueError("SQLite 找不到資料表。")
        sql = f"SELECT {selected_column_sql(columns)} FROM {quote_identifier(tables[0])}"
    parameters: tuple[int, ...] = ()
    if limit is not None and limit > 0:
        sql += " LIMIT ?"
        parameters = (int(limit),)
    with sqlite3.connect(sqlite_readonly_uri(path), uri=True) as connection:
        return pd.read_sql_query(sql, connection, params=parameters)


def read_duckdb_frame(
    path: Path,
    spec: dict[str, Any],
    columns: Iterable[str] | None,
    limit: int | None,
) -> pd.DataFrame:
    duckdb = optional_import("duckdb")
    if duckdb is None:
        raise RuntimeError("讀取 DuckDB 需要安裝 duckdb。")
    table = str(spec.get("table", ""))
    query = str(spec.get("query", "")).strip()
    if query:
        sql = (
            f"SELECT {selected_column_sql(columns)} "
            f"FROM ({ensure_read_only_query(query)}) AS vap_query"
        )
    else:
        if not table:
            tables = list_duckdb_tables(path)
            if not tables:
                raise ValueError("DuckDB 找不到資料表。")
            table = tables[0]
        schema, plain_table = split_schema_table(table)
        quoted_table = quote_identifier(plain_table)
        if schema:
            quoted_table = f"{quote_identifier(schema)}.{quoted_table}"
        sql = f"SELECT {selected_column_sql(columns)} FROM {quoted_table}"
    if limit is not None and limit > 0:
        sql += f" LIMIT {int(limit)}"
    connection = duckdb.connect(str(path), read_only=True)
    try:
        return connection.execute(sql).fetchdf()
    finally:
        connection.close()


def read_sqlalchemy_frame(
    spec: dict[str, Any],
    columns: Iterable[str] | None,
    limit: int | None,
) -> pd.DataFrame:
    sqlalchemy = optional_import("sqlalchemy")
    if sqlalchemy is None:
        raise RuntimeError("讀取遠端資料庫需要安裝 SQLAlchemy 與對應 driver。")
    url = str(spec.get("url") or spec.get("path") or "")
    query = str(spec.get("query", "")).strip()
    table = str(spec.get("table", ""))
    engine = sqlalchemy.create_engine(url)
    try:
        if query:
            sql = ensure_read_only_query(query)
            dialect = str(engine.dialect.name).lower()
            selected_sql = "*"
            if columns:
                quote = engine.dialect.identifier_preparer.quote
                selected_sql = ", ".join(quote(str(column)) for column in columns)
            if limit is not None and limit > 0:
                if dialect in {"mssql"}:
                    sql = f"SELECT TOP {int(limit)} {selected_sql} FROM ({sql}) AS vap_query"
                elif dialect in {"oracle"}:
                    sql = f"SELECT {selected_sql} FROM ({sql}) vap_query FETCH FIRST {int(limit)} ROWS ONLY"
                else:
                    sql = f"SELECT {selected_sql} FROM ({sql}) AS vap_query LIMIT {int(limit)}"
            else:
                sql = f"SELECT {selected_sql} FROM ({sql}) AS vap_query"
            with engine.connect() as connection:
                transaction = connection.begin()
                try:
                    if dialect in {"postgresql", "mysql", "mariadb", "oracle"}:
                        connection.exec_driver_sql("SET TRANSACTION READ ONLY")
                    frame = pd.read_sql_query(sqlalchemy.text(sql), connection)
                finally:
                    transaction.rollback()
                return frame
        if not table:
            raise ValueError("SQLAlchemy 來源必須指定 table 或 query。")
        schema, plain_table = split_schema_table(table)
        metadata = sqlalchemy.MetaData()
        table_object = sqlalchemy.Table(plain_table, metadata, schema=schema, autoload_with=engine)
        selected = [table_object.c[str(column)] for column in columns] if columns else list(table_object.c)
        statement = sqlalchemy.select(*selected)
        if limit is not None and limit > 0:
            statement = statement.limit(int(limit))
        with engine.connect() as connection:
            return pd.read_sql(statement, connection)
    finally:
        engine.dispose()


def read_source_frame(
    source: str | Path | dict[str, Any],
    columns: Iterable[str] | None = None,
    limit: int | None = None,
    config_directory: Path | None = None,
) -> pd.DataFrame:
    if limit is not None:
        if isinstance(limit, bool) or int(limit) != limit or not 1 <= int(limit) <= DEFAULT_MAX_ROWS:
            raise ValueError(f"limit 必須介於 1 與 {DEFAULT_MAX_ROWS}。")
        limit = int(limit)
    spec = normalize_source_spec(source)
    kind = str(spec["kind"])
    if kind == "sqlalchemy":
        return read_sqlalchemy_frame(spec, columns, limit)
    path = resolve_source_path(str(spec.get("path", "")), config_directory)
    if not path.exists():
        raise FileNotFoundError(f"找不到資料來源：{path}")
    if kind in {"unknown", "auto"} or (not path.suffix and kind == "parquet"):
        kind = sniff_source_kind(path)
        spec["kind"] = kind
    if kind == "sqlite":
        return read_sqlite_frame(path, spec, columns, limit)
    if kind == "duckdb":
        return read_duckdb_frame(path, spec, columns, limit)
    if kind == "parquet_dataset":
        table = str(spec.get("table", ""))
        dataset_root = path.expanduser().resolve()
        target = (dataset_root / table).resolve() if table and table != "__all__" else dataset_root
        try:
            target.relative_to(dataset_root)
        except ValueError as exc:
            raise ValueError("Parquet dataset table 不可離開資料集根目錄。") from exc
        return read_parquet_frame(target, columns=columns, limit=limit)
    if kind == "parquet":
        frame = read_parquet_frame(path, columns=columns, limit=limit)
    elif kind in {"csv", "tsv"}:
        # Let the Python parser sniff comma, semicolon or pipe CSVs.  TSV keeps
        # its explicit delimiter for speed and predictability.
        separator: str | None = "\t" if kind == "tsv" else None
        parser_options: dict[str, Any] = {"sep": separator}
        if separator is None:
            parser_options["engine"] = "python"
        try:
            frame = pd.read_csv(
                path,
                encoding=str(spec.get("encoding", "utf-8-sig")),
                usecols=list(columns) if columns else None,
                nrows=limit,
                **parser_options,
            )
        except UnicodeDecodeError:
            frame = pd.read_csv(
                path,
                encoding="cp950",
                usecols=list(columns) if columns else None,
                nrows=limit,
                **parser_options,
            )
        except ValueError as exc:
            if "Usecols do not match" in str(exc):
                raise ValueError(f"找不到欄位：{', '.join(str(column) for column in columns or [])}") from exc
            raise
    elif kind == "excel":
        sheet = spec.get("sheet") or spec.get("table") or 0
        frame = pd.read_excel(path, sheet_name=sheet, usecols=list(columns) if columns else None, nrows=limit)
    elif kind in {"json", "jsonl"}:
        json_options: dict[str, Any] = {"lines": kind == "jsonl"}
        if kind == "jsonl" and limit is not None and limit > 0:
            json_options["nrows"] = int(limit)
        frame = pd.read_json(path, **json_options)
        if columns:
            frame = frame[list(columns)]
    else:
        raise ValueError(f"不支援的資料來源類型：{kind}")
    return frame.head(limit) if limit is not None and limit > 0 else frame


def read_parquet_frame(
    path: Path,
    columns: Iterable[str] | None = None,
    limit: int | None = None,
) -> pd.DataFrame:
    """Read projected Parquet rows without materializing the full dataset."""

    selected_columns = list(columns) if columns else None
    if limit is not None and limit > 0:
        try:
            import pyarrow.dataset as pyarrow_dataset
        except ImportError:
            # A fastparquet-only installation remains supported, although
            # pyarrow (included in requirements.txt) is the bounded-read path.
            return pd.read_parquet(path, columns=selected_columns).head(int(limit))
        dataset_options: dict[str, Any] = {"format": "parquet"}
        if path.is_dir():
            dataset_options["partitioning"] = "hive"
        dataset = pyarrow_dataset.dataset(str(path), **dataset_options)
        return dataset.head(int(limit), columns=selected_columns).to_pandas()
    return pd.read_parquet(path, columns=selected_columns)


# =============================================================================
# 3. 欄位語意、品質摘要與圖表建議
# =============================================================================


def normalized_name(column_name: str) -> str:
    with_acronym_boundaries = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", column_name.strip())
    with_word_boundaries = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", with_acronym_boundaries)
    return re.sub(r"[\W_]+", " ", with_word_boundaries.casefold(), flags=re.UNICODE).strip()


def name_tokens(value: str) -> tuple[str, ...]:
    normalized = normalized_name(value)
    return tuple(normalized.split()) if normalized else ()


def alias_match(column_name: str, aliases: list[str]) -> bool:
    column_tokens = name_tokens(column_name)
    if not column_tokens:
        return False
    for alias in aliases:
        alias_tokens = name_tokens(alias)
        if not alias_tokens:
            continue
        alias_width = len(alias_tokens)
        if any(
            column_tokens[index : index + alias_width] == alias_tokens
            for index in range(len(column_tokens) - alias_width + 1)
        ):
            return True
        if "".join(column_tokens) == "".join(alias_tokens):
            return True
        normalized_alias = " ".join(alias_tokens)
        normalized_column = " ".join(column_tokens)
        if re.search(r"[\u3400-\u9fff]", normalized_alias) and normalized_alias in normalized_column:
            return True
    return False


def infer_semantic_type(
    column_name: str,
    series: pd.Series,
    aliases: dict[str, list[str]] | None = None,
) -> str:
    alias_map = aliases or load_defaults().get("semantic_aliases", {})
    name = normalized_name(column_name)
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if alias_match(name, alias_map.get("datetime", [])):
        date_sample = series.dropna().astype(str).head(100)
        if not date_sample.empty and pd.to_datetime(date_sample, errors="coerce").notna().mean() >= 0.8:
            return "datetime"
    if alias_match(name, alias_map.get("identifier", [])):
        return "identifier"
    if pd.api.types.is_numeric_dtype(series):
        for semantic in ["price", "percentage", "flow", "currency", "volume"]:
            if alias_match(name, alias_map.get(semantic, [])):
                return semantic
        non_null = pd.to_numeric(series, errors="coerce").dropna()
        if not non_null.empty and pd.api.types.is_integer_dtype(non_null) and non_null.min() >= 0:
            return "count"
        return "numeric"
    non_null_text = series.dropna().astype(str)
    if DATE_NAME_PATTERN.search(name) and not non_null_text.empty:
        parsed = pd.to_datetime(non_null_text.head(100), errors="coerce")
        if parsed.notna().mean() >= 0.8:
            return "datetime"
    distinct = int(non_null_text.nunique())
    if distinct <= max(20, int(len(series) * 0.05)):
        return "category"
    return "text"


def infer_unit(column_name: str, semantic_type: str) -> str:
    name = normalized_name(column_name)
    if semantic_type == "percentage":
        return "%"
    if semantic_type == "volume":
        return "Shares"
    if semantic_type in {"currency", "flow"}:
        if any(token in name for token in ["usd", "dollar", "美元"]):
            return "USD"
        return "TWD"
    if semantic_type == "price":
        return "Price"
    return ""


def numeric_profile(
    series: pd.Series,
    outlier_multiplier: float = DEFAULT_OUTLIER_IQR_MULTIPLIER,
) -> dict[str, Any]:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return {"min": None, "max": None, "mean": None, "q1": None, "median": None, "q3": None, "outlier_count": 0}
    q1 = float(values.quantile(0.25))
    q3 = float(values.quantile(0.75))
    iqr = q3 - q1
    outlier_count = int(
        (
            (values < q1 - outlier_multiplier * iqr)
            | (values > q3 + outlier_multiplier * iqr)
        ).sum()
    ) if iqr > 0 else 0
    return {
        "min": finite_or_none(values.min()),
        "max": finite_or_none(values.max()),
        "mean": finite_or_none(values.mean()),
        "q1": finite_or_none(q1),
        "median": finite_or_none(values.median()),
        "q3": finite_or_none(q3),
        "outlier_count": outlier_count,
    }


def infer_time_frequency(series: pd.Series) -> str:
    values = pd.to_datetime(series, errors="coerce").dropna().drop_duplicates().sort_values()
    if len(values) < 3:
        return "insufficient"
    median_days = float(values.diff().dropna().dt.total_seconds().median() / 86400)
    if median_days <= 1.5:
        return "daily"
    if median_days <= 8:
        return "weekly"
    if median_days <= 35:
        return "monthly"
    if median_days <= 100:
        return "quarterly"
    if median_days <= 370:
        return "yearly"
    return "irregular"


def finite_or_none(value: Any) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if math.isfinite(numeric) else None


def profile_frame(frame: pd.DataFrame, sample_limit: int = DEFAULT_SAMPLE_ROWS) -> list[dict[str, Any]]:
    sample = frame.head(sample_limit)
    defaults = load_defaults()
    aliases = defaults.get("semantic_aliases", {})
    outlier_multiplier = float(
        defaults.get("chart", {}).get(
            "outlier_iqr_multiplier",
            DEFAULT_OUTLIER_IQR_MULTIPLIER,
        )
    )
    profiles: list[dict[str, Any]] = []
    for column in sample.columns:
        series = sample[column]
        semantic_type = infer_semantic_type(str(column), series, aliases)
        profile: dict[str, Any] = {
            "name": str(column),
            "dtype": str(series.dtype),
            "semantic_type": semantic_type,
            "unit": infer_unit(str(column), semantic_type),
            "nullable": bool(series.isna().any()),
            "null_count": int(series.isna().sum()),
            "null_pct": round(float(series.isna().mean()), 6),
            "distinct_count": int(series.nunique(dropna=True)),
            "sample_values": [str(value)[:80] for value in series.dropna().head(3).tolist()],
        }
        if semantic_type in NUMERIC_SEMANTIC_TYPES:
            profile.update(numeric_profile(series, outlier_multiplier))
        if semantic_type == "datetime":
            profile["frequency"] = infer_time_frequency(series)
        profiles.append(profile)
    return profiles


def pick_first(profiles: list[dict[str, Any]], semantic_types: set[str]) -> str:
    for profile in profiles:
        if profile["semantic_type"] in semantic_types:
            return str(profile["name"])
    return ""


def pick_all(profiles: list[dict[str, Any]], semantic_types: set[str], maximum: int = 5) -> list[str]:
    return [str(profile["name"]) for profile in profiles if profile["semantic_type"] in semantic_types][:maximum]


def is_adjusted_price_column(column_name: str) -> bool:
    tokens = set(name_tokens(column_name))
    return bool(tokens.intersection({"adj", "adjusted"}))


def price_field_role(column_name: str) -> str:
    tokens = set(name_tokens(column_name))
    for role in ("open", "high", "low", "close"):
        if role in tokens:
            return role
    return ""


def pick_prices_prefer_adjusted(column_profiles: list[dict[str, Any]], maximum: int = 4) -> list[str]:
    price_profiles = [profile for profile in column_profiles if profile.get("semantic_type") == "price"]
    ranked = sorted(
        enumerate(price_profiles),
        key=lambda item: (not is_adjusted_price_column(str(item[1].get("name", ""))), item[0]),
    )
    return [str(profile.get("name", "")) for _index, profile in ranked[:maximum]]


def detect_ohlcv_mapping(column_profiles: list[dict[str, Any]]) -> dict[str, Any]:
    mapping: dict[str, Any] = {"open": "", "high": "", "low": "", "close": "", "volume": ""}
    price_candidates: dict[str, list[tuple[int, int, str]]] = {role: [] for role in ("open", "high", "low", "close")}
    volume_candidates: list[tuple[int, int, str]] = []
    for index, profile in enumerate(column_profiles):
        name = str(profile.get("name", ""))
        semantic_type = str(profile.get("semantic_type", ""))
        if semantic_type == "price":
            role = price_field_role(name)
            if role:
                adjusted_rank = 0 if is_adjusted_price_column(name) else 1
                price_candidates[role].append((adjusted_rank, index, name))
        if semantic_type == "volume":
            exact_rank = 0 if normalized_name(name) == "volume" else 1
            volume_candidates.append((exact_rank, index, name))
    for role, candidates in price_candidates.items():
        if candidates:
            mapping[role] = min(candidates)[2]
    if volume_candidates:
        mapping["volume"] = min(volume_candidates)[2]
    price_fields = [str(mapping[role]) for role in ("open", "high", "low", "close")]
    mapping["adjusted_ohlc"] = bool(
        all(price_fields) and all(is_adjusted_price_column(column) for column in price_fields)
    )
    mapping["complete"] = bool(all(price_fields) and mapping["volume"])
    mapping["price_basis"] = "adjusted" if mapping["adjusted_ohlc"] else "source"
    mapping["derive_adjusted_prices"] = False
    return mapping


def suggest_chart_mapping(column_profiles: list[dict[str, Any]]) -> dict[str, Any]:
    datetime_column = pick_first(column_profiles, {"datetime"})
    category_column = pick_first(column_profiles, {"category", "identifier"})
    prices = pick_prices_prefer_adjusted(column_profiles, 4)
    volumes = pick_all(column_profiles, {"volume"}, 2)
    flows = pick_all(column_profiles, {"flow"}, 5)
    percentages = pick_all(column_profiles, {"percentage"}, 4)
    numeric = pick_all(column_profiles, {"numeric", "currency", "count"}, 5)
    suggestion: dict[str, Any] = {
        "chart_type": "line",
        "axis_mode": "single",
        "preset": "multi_series",
        "x": datetime_column or category_column,
        "y": [],
        "secondary_y": [],
        "confidence": 0.45,
        "reason": "使用第一個可用維度與數值欄位。",
    }
    ohlcv_mapping = detect_ohlcv_mapping(column_profiles)
    if datetime_column and ohlcv_mapping["complete"] and ohlcv_mapping["adjusted_ohlc"]:
        suggestion.update(
            {
                "chart_type": "candlestick",
                "axis_mode": "single",
                "preset": "candlestick_volume",
                "x": datetime_column,
                "y": [],
                "secondary_y": [],
                "open": ohlcv_mapping["open"],
                "high": ohlcv_mapping["high"],
                "low": ohlcv_mapping["low"],
                "close": ohlcv_mapping["close"],
                "volume": ohlcv_mapping["volume"],
                "normalized_y": [],
                "price_basis": "adjusted",
                "derive_adjusted_prices": False,
                "confidence": 0.99,
                "reason": "偵測到日期、完整調整後 OHLC 與成交量，建議紅漲綠跌 K 線／量上下雙列單軸。",
            }
        )
    elif datetime_column and prices:
        suggestion.update({"chart_type": "line", "preset": "price", "y": prices, "confidence": 0.92, "reason": "偵測到日期與價格欄位，適合趨勢線。"})
        if volumes:
            suggestion.update({"axis_mode": "dual", "preset": "price_volume_dual", "secondary_y": [volumes[0]], "confidence": 0.96, "reason": "偵測到日期、價格與成交量，建議價格／量雙軸。"})
    elif datetime_column and len(flows) >= 2:
        suggestion.update({"chart_type": "stacked_bar", "preset": "signed_flow", "y": flows, "confidence": 0.9, "reason": "偵測到多個資金流欄位，適合正負堆疊柱狀圖。"})
    elif datetime_column and percentages:
        suggestion.update({"chart_type": "line", "preset": "multi_series", "y": percentages, "confidence": 0.84, "reason": "偵測到日期與比率欄位，適合百分比趨勢。"})
    elif datetime_column and numeric:
        suggestion.update({"chart_type": "line", "preset": "multi_series", "y": numeric, "confidence": 0.78, "reason": "偵測到日期與數值欄位，適合多序列趨勢。"})
    elif category_column and numeric:
        suggestion.update({"chart_type": "bar", "preset": "multi_series", "x": category_column, "y": [numeric[0]], "confidence": 0.8, "reason": "偵測到類別與數值欄位，適合類別比較。"})
    elif numeric:
        suggestion.update({"x": str(column_profiles[0]["name"]) if column_profiles else "", "y": [numeric[0]], "confidence": 0.55})
    if suggestion["chart_type"] != "candlestick" and not suggestion["y"] and flows:
        suggestion["y"] = flows
    if suggestion["chart_type"] != "candlestick" and not suggestion["y"] and volumes:
        suggestion["y"] = volumes
    return suggestion


def infer_data_roles(column_profiles: list[dict[str, Any]]) -> dict[str, Any]:
    time_columns = pick_all(column_profiles, {"datetime"}, 3)
    entity_columns = pick_all(column_profiles, {"identifier"}, 5)
    dimensions = pick_all(column_profiles, {"category", "text", "boolean"}, 10)
    metrics = pick_all(column_profiles, NUMERIC_SEMANTIC_TYPES, 50)
    grain_parts = entity_columns[:1] + time_columns[:1]
    grain = " + ".join(grain_parts) if grain_parts else "row"
    return {
        "grain": grain,
        "time": time_columns,
        "entity": entity_columns,
        "dimensions": dimensions,
        "metrics": metrics,
    }


def discover_source(
    source: str | Path | dict[str, Any],
    config_directory: Path | None = None,
    sample_rows: int = DEFAULT_SAMPLE_ROWS,
) -> dict[str, Any]:
    if isinstance(sample_rows, bool) or int(sample_rows) != sample_rows or not 1 <= int(sample_rows) <= DEFAULT_MAX_ROWS:
        raise ValueError(f"sample_rows 必須介於 1 與 {DEFAULT_MAX_ROWS}。")
    sample_rows = int(sample_rows)
    spec = normalize_source_spec(source)
    if spec.get("kind") in {"unknown", "auto"} and spec.get("path"):
        resolved_path = resolve_source_path(str(spec["path"]), config_directory)
        spec["kind"] = detect_source_kind(resolved_path)
    tables = list_source_tables(spec, config_directory)
    if not spec.get("table") and tables:
        if spec["kind"] == "excel":
            spec["sheet"] = tables[0]
        elif spec["kind"] not in {"csv", "tsv", "parquet", "json", "jsonl"}:
            spec["table"] = tables[0]
    frame = read_source_frame(spec, limit=sample_rows, config_directory=config_directory)
    profiles = profile_frame(frame, sample_limit=sample_rows)
    roles = infer_data_roles(profiles)
    date_column = str(roles.get("time", [""])[0]) if roles.get("time") else ""
    grain_columns = list(roles.get("entity", [])[:1]) + list(roles.get("time", [])[:1])
    quality = audit_frame(
        frame,
        date_column=date_column,
        columns=list(frame.columns),
        grain_columns=grain_columns,
    )
    locator = str(spec.get("url") or spec.get("path") or "")
    safe_locator = sanitize_connection_url(locator) if spec["kind"] == "sqlalchemy" else locator
    safe_source = {
        "schema": SOURCE_SCHEMA,
        "version": SOURCE_VERSION,
        "kind": spec["kind"],
        "path": safe_locator if spec.get("path") else spec.get("path"),
        "url": safe_locator if spec.get("url") else spec.get("url"),
        "table": spec.get("table", ""),
        "sheet": spec.get("sheet", ""),
        "encoding": spec.get("encoding", "utf-8-sig"),
        "query": "REDACTED" if str(spec.get("query", "")).strip() else "",
        "query_present": bool(str(spec.get("query", "")).strip()),
    }
    public_profiles = [
        {key: value for key, value in profile.items() if key != "sample_values"}
        for profile in profiles
    ]
    return {
        "schema": SOURCE_SCHEMA,
        "version": SOURCE_VERSION,
        "status": "OK",
        "source": safe_source,
        "kind": spec["kind"],
        "tables": tables,
        "selected_table": spec.get("table") or spec.get("sheet") or (tables[0] if tables else ""),
        "declared_schema": source_declared_schema(spec, config_directory),
        "sample_rows": int(len(frame)),
        "sample_columns": int(len(frame.columns)),
        "columns": public_profiles,
        "roles": roles,
        "quality": quality,
        "suggestion": suggest_chart_mapping(profiles),
    }


def write_discovery_manifest(path: Path, manifest: dict[str, Any]) -> None:
    with file_transaction_lock(path):
        atomic_write_json(path, manifest)
