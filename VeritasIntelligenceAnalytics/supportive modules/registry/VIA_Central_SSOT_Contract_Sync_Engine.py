#!/usr/bin/env python3
"""
Veritas Intelligence Analytics (VIA)
Central SSOT / Contract Mapping, Synchronization and Connection Engine

Local-first, fail-closed governance engine for:
  - JSON / YAML / OpenAPI contracts
  - Protocol Buffers and GraphQL schema discovery
  - SQLite database schema introspection
  - canonical field and alias mapping
  - compatibility / breaking-change gates
  - code-generator command planning and controlled execution
  - append-only SQLite evidence registry
  - JSON / CSV / HTML evidence reports

No external command is executed unless --apply is explicitly supplied.
"""

from __future__ import annotations

# =============================================================================
# def 00 PARAMETERS — all user-modifiable parameters are kept at the top
# =============================================================================

ENGINE_NAME = "VIA Central SSOT Contract Sync Engine"
ENGINE_VERSION = "1.1.0"
DEFAULT_ENCODING = "utf-8"
DEFAULT_SIMILARITY_THRESHOLD = 0.88
DEFAULT_FAIL_ON_BREAKING = True
DEFAULT_OUTPUT_DIR = "_via_contract_sync_runs"
DEFAULT_REGISTRY_DB = "via_contract_registry.sqlite"
DEFAULT_MAX_FILE_BYTES = 50 * 1024 * 1024
DEFAULT_COMMAND_TIMEOUT_SECONDS = 300

SUPPORTED_CONTRACT_SUFFIXES = {
    ".json", ".yaml", ".yml", ".proto", ".graphql", ".gql", ".prisma", ".sqlite", ".db"
}

ALLOWED_GENERATOR_EXECUTABLES = {
    "protoc",
    "openapi-generator",
    "openapi-generator-cli",
    "graphql-codegen",
    "prisma",
    "npx",
}

GENERATOR_PROFILES = {
    "protobuf_python": {
        "tool": "protoc",
        "input_kinds": ["PROTOBUF"],
        "command": ["protoc", "--python_out={output_dir}", "--grpc_python_out={output_dir}", "{input}"],
    },
    "openapi_python": {
        "tool": "openapi-generator",
        "input_kinds": ["OPENAPI"],
        "command": ["openapi-generator", "generate", "-i", "{input}", "-g", "python", "-o", "{output_dir}"],
    },
    "openapi_typescript": {
        "tool": "openapi-generator",
        "input_kinds": ["OPENAPI"],
        "command": ["openapi-generator", "generate", "-i", "{input}", "-g", "typescript-fetch", "-o", "{output_dir}"],
    },
    "graphql_typescript": {
        "tool": "graphql-codegen",
        "input_kinds": ["GRAPHQL"],
        "command": ["graphql-codegen", "--schema", "{input}", "--out", "{output_dir}/graphql-types.ts"],
    },
    "prisma_generate": {
        "tool": "prisma",
        "input_kinds": ["PRISMA"],
        "command": ["prisma", "generate", "--schema", "{input}"],
    },
}

# Canonical domain vocabulary accumulated for VIA financial-data interfaces.
DOMAIN_ALIAS_REGISTRY = {
    "TW_TICKER": {
        "aliases": ["TaiwanTicker", "TwTicker", "StockCode", "股票代碼", "證券代號"],
        "regex": r"^[1-9][0-9]{3}$",
    },
    "TW_YFINANCE_TICKER": {
        "aliases": ["TW_YF_TICKER", "YFinanceTicker", "YahooTicker", "Yahoo Finance Ticker"],
        "regex": r"^[1-9][0-9]{3}\.(?:TW|TWO)$",
    },
    "TW_BLOOMBERG_TICKER": {
        "aliases": ["BloombergTicker", "BBGTicker", "Bloomberg Ticker"],
        "regex": r"^[1-9][0-9]{3}\sTT$",
    },
    "BROKER_ID": {
        "aliases": ["BrokerId", "BrokerCode", "券商代號", "券商代碼", "券商識別碼"],
    },
    "BROKER_NAME_ZH_TW": {
        "aliases": ["BrokerNameZhTw", "券商名稱", "券商全名", "中文券商名稱"],
    },
    "BROKER_SHORT_NAME_ZH_TW": {
        "aliases": ["BrokerShortNameZhTw", "券商簡稱", "中文簡稱"],
    },
    "BROKER_NAME_EN": {
        "aliases": ["BrokerNameEn", "EnglishBrokerName", "券商英文名稱"],
    },
    "BROKER_ACRONYM_EN": {
        "aliases": ["BrokerAcronymEn", "BrokerAbbreviation", "英文縮寫", "券商英文縮寫"],
    },
    "INVESTMENT_RATING": {
        "aliases": ["Rating", "Recommendation", "投資評等", "評等", "投資建議"],
    },
    "TARGET_PRICE": {
        "aliases": ["TargetPrice", "PriceTarget", "Price Objective", "TP", "目標價", "目標股價", "目標價格"],
    },
    "RATING_DATE": {
        "aliases": ["RatingDate", "ReportDate", "評等日期", "報告日期"],
    },
    "FORECAST_PERIOD": {
        "aliases": ["ForecastPeriod", "FiscalPeriod", "Period", "預估期間", "財報期間", "年季"],
    },
}

INVESTMENT_RATING_ALIASES = {
    "STRONG_BUY": ["Strong Buy", "Conviction Buy", "強力買進", "積極買進"],
    "BUY": ["Buy", "買進", "買入", "推薦"],
    "OUTPERFORM": ["Outperform", "Market Outperform", "優於大盤", "優於市場"],
    "OVERWEIGHT": ["Overweight", "加碼", "優於基準權重"],
    "ACCUMULATE": ["Accumulate", "Add", "累積持股", "逢低承接"],
    "HOLD": ["Hold", "持有", "觀望"],
    "NEUTRAL": ["Neutral", "Market Perform", "Equal Weight", "中立", "符合大盤"],
    "UNDERPERFORM": ["Underperform", "劣於大盤", "劣於市場"],
    "UNDERWEIGHT": ["Underweight", "Reduce", "減碼", "降低持股"],
    "SELL": ["Sell", "賣出"],
    "STRONG_SELL": ["Strong Sell", "Avoid", "強力賣出", "避開"],
    "NOT_RATED": ["Not Rated", "No Opinion", "未評等", "無意見"],
    "SUSPENDED": ["Rating Suspended", "Suspended", "暫停評等"],
    "RESTRICTED": ["Restricted", "限制評等"],
}

TARGET_PRICE_ALIASES = {
    "TARGET_PRICE": ["Target Price", "Price Target", "TP", "目標價", "目標價格", "目標股價"],
    "PRICE_OBJECTIVE": ["Price Objective", "PO", "價格目標", "股價目標"],
    "CONSENSUS_TARGET_PRICE": ["Consensus Target Price", "Consensus Price Target", "共識目標價"],
    "MEAN_TARGET_PRICE": ["Mean Target Price", "Average Target Price", "平均目標價"],
    "MEDIAN_TARGET_PRICE": ["Median Target Price", "中位數目標價"],
    "HIGH_TARGET_PRICE": ["High Target Price", "Highest Target Price", "最高目標價"],
    "LOW_TARGET_PRICE": ["Low Target Price", "Lowest Target Price", "最低目標價"],
    "BASE_CASE_TARGET_PRICE": ["Base-Case Target Price", "基準情境目標價"],
    "BULL_CASE_TARGET_PRICE": ["Bull-Case Target Price", "樂觀情境目標價", "多頭情境目標價"],
    "BEAR_CASE_TARGET_PRICE": ["Bear-Case Target Price", "悲觀情境目標價", "空頭情境目標價"],
    "TWELVE_MONTH_TARGET_PRICE": ["12-Month Target Price", "One-Year Target Price", "十二個月目標價"],
}

PERIOD_PATTERNS = {
    "ROC_YEAR_QUARTER": r"(?<!\d)(?:民國)?(?P<roc_year>\d{2,3})\s*(?:年)?[\s\-_/]*Q(?P<quarter>[1-4])(?P<status>[AEFPRC])?(?![A-Z0-9])",
    "CHINESE_YEAR_QUARTER": r"(?<!\d)(?P<year>19\d{2}|20\d{2})\s*年?\s*第?\s*(?P<quarter>[1-4一二三四])\s*(?:季|季度)(?P<status>[AEFPRC])?",
    "YEAR_QUARTER": r"(?<!\d)(?P<year>19\d{2}|20\d{2})[\s\-_/]*Q(?P<quarter>[1-4])(?P<status>[AEFPRC])?\b",
    "QUARTER_YEAR": r"\b(?P<quarter>[1-4])Q['’]?(?P<year>\d{2}|\d{4})(?P<status>[AEFPRC])?\b",
    "Q_PREFIX_YEAR": r"\bQ(?P<quarter>[1-4])[\s'’\-_/]*(?P<year>\d{2}|\d{4})(?P<status>[AEFPRC])?\b",
    "YEAR_HALF": r"(?<!\d)(?P<year>19\d{2}|20\d{2})[\s\-_/]*H(?P<half>[12])(?P<status>[AEFPRC])?\b",
    "HALF_YEAR": r"\b(?P<half>[12])H['’]?(?P<year>\d{2}|\d{4})(?P<status>[AEFPRC])?\b",
    "FISCAL_YEAR": r"\b(?P<calendar>FY|CY)['’]?(?P<year>\d{2}|\d{4})(?P<status>[AEFPRC])?\b",
    "ROC_YEAR": r"(?<!\d)(?:民國)?(?P<roc_year>\d{2,3})\s*年",
    "YEAR": r"(?<!\d)(?P<year>19\d{2}|20\d{2})(?P<status>[AEFPRC])?(?!\d)",
    "ROLLING": r"\b(?P<rolling>LTM|TTM|NTM|F12M|FY[12]|CY[12])\b",
}

# =============================================================================
# def 01 IMPORTS
# =============================================================================

import argparse
import csv
import dataclasses
import datetime as dt
import difflib
import hashlib
import html
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

try:
    import yaml  # type: ignore
except ImportError:  # optional; JSON remains available
    yaml = None

try:
    import jsonschema  # type: ignore
except ImportError:  # optional; structural validation remains available
    jsonschema = None


# =============================================================================
# def 02 DATA MODELS
# =============================================================================

class Gate(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL_CLOSED = "FAIL_CLOSED"


class ChangeKind(str, Enum):
    ADDED = "ADDED"
    REMOVED = "REMOVED"
    TYPE_CHANGED = "TYPE_CHANGED"
    REQUIRED_CHANGED = "REQUIRED_CHANGED"
    UNCHANGED = "UNCHANGED"


@dataclass(frozen=True)
class FieldSpec:
    canonical_name: str
    data_type: str = "any"
    required: bool = False
    description: str = ""
    aliases: tuple[str, ...] = ()
    pattern: str | None = None


@dataclass
class ContractDocument:
    source_path: str
    kind: str
    name: str
    version: str
    digest: str
    fields: dict[str, FieldSpec] = field(default_factory=dict)
    raw: Any = None
    diagnostics: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MappingDecision:
    source_field: str
    target_field: str | None
    method: str
    confidence: float
    status: str
    reason: str


@dataclass(frozen=True)
class ContractChange:
    field_name: str
    change_kind: str
    breaking: bool
    old_value: str | None
    new_value: str | None


@dataclass
class GeneratorPlan:
    profile: str
    tool: str
    available: bool
    command: list[str]
    applied: bool = False
    return_code: int | None = None
    stdout: str = ""
    stderr: str = ""


@dataclass
class RunEvidence:
    run_id: str
    created_at: str
    gate: str
    source_contract: dict[str, Any]
    target_contract: dict[str, Any] | None
    mappings: list[dict[str, Any]]
    changes: list[dict[str, Any]]
    generators: list[dict[str, Any]]
    diagnostics: list[str]
    outputs: dict[str, str]


@dataclass
class UserTestEvidence:
    created_at: str
    gate: str
    passed: int
    failed: int
    checks: list[dict[str, Any]]


@dataclass
class ActivationEvidence:
    activation_id: str
    created_at: str
    engine_name: str
    engine_version: str
    gate: str
    contract_path: str
    contract_digest: str
    registry_path: str
    self_test_passed: bool
    user_test_passed: bool
    external_runtime_executed: bool


# =============================================================================
# def 03 GENERAL UTILITIES
# =============================================================================

def def_utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def def_run_id() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("RUN_%Y%m%d_%H%M%S_%fZ")


def def_sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest().upper()


def def_read_bytes(path: Path) -> bytes:
    size = path.stat().st_size
    if size > DEFAULT_MAX_FILE_BYTES:
        raise ValueError(f"File exceeds safety limit: {path} ({size} bytes)")
    return path.read_bytes()


def def_atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding=DEFAULT_ENCODING, delete=False, dir=path.parent) as handle:
        handle.write(content)
        temporary = Path(handle.name)
    os.replace(temporary, path)


def def_atomic_write_json(path: Path, value: Any) -> None:
    def_atomic_write_text(path, json.dumps(def_jsonable(value), ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def def_normalize_name(value: str) -> str:
    return re.sub(r"[^A-Z0-9\u4e00-\u9fff]+", "", value.strip().upper())


def def_expand_short_year(value: str, pivot: int = 70) -> int:
    year = int(value)
    if len(value) == 4:
        return year
    return 2000 + year if year < pivot else 1900 + year


def def_jsonable(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return {key: def_jsonable(item) for key, item in dataclasses.asdict(value).items()}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): def_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [def_jsonable(item) for item in value]
    return value


# =============================================================================
# def 04 PERIOD AND DOMAIN NORMALIZATION
# =============================================================================

def def_parse_period(text: str) -> dict[str, Any] | None:
    normalized = unicodedata.normalize("NFKC", text).upper().replace("’", "'")
    for period_type, pattern in PERIOD_PATTERNS.items():
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if not match:
            continue
        values = {key: value for key, value in match.groupdict().items() if value is not None}
        if "year" in values:
            values["year"] = def_expand_short_year(values["year"])
        if "roc_year" in values:
            values["year"] = int(values.pop("roc_year")) + 1911
            values["calendar"] = "ROC"
        chinese_integer_map = {"一": 1, "二": 2, "三": 3, "四": 4}
        for integer_key in ("quarter", "half"):
            if integer_key in values:
                values[integer_key] = chinese_integer_map.get(values[integer_key], int(values[integer_key]) if values[integer_key].isdigit() else values[integer_key])
        return {
            "period_type": period_type,
            "period_raw": match.group(0),
            "start": match.start(),
            "end": match.end(),
            **values,
        }
    return None


def def_build_reverse_alias_map(source: Mapping[str, Sequence[str]]) -> dict[str, str]:
    output: dict[str, str] = {}
    for canonical, aliases in source.items():
        output[def_normalize_name(canonical)] = canonical
        for alias in aliases:
            output[def_normalize_name(alias)] = canonical
    return output


def def_normalize_investment_rating(value: str) -> str | None:
    return def_build_reverse_alias_map(INVESTMENT_RATING_ALIASES).get(def_normalize_name(value))


def def_normalize_target_price_term(value: str) -> str | None:
    return def_build_reverse_alias_map(TARGET_PRICE_ALIASES).get(def_normalize_name(value))


def def_validate_domain_value(canonical_field: str, value: str) -> tuple[bool, str]:
    rule = DOMAIN_ALIAS_REGISTRY.get(canonical_field, {})
    pattern = rule.get("regex")
    if pattern and not re.fullmatch(pattern, value.strip(), flags=re.IGNORECASE):
        return False, f"Value does not match {canonical_field} contract"
    return True, "PASS"


# =============================================================================
# def 05 CONTRACT LOADERS
# =============================================================================

def def_detect_contract_kind(path: Path, raw: Any | None = None) -> str:
    suffix = path.suffix.lower()
    if suffix in {".yaml", ".yml", ".json"}:
        if isinstance(raw, dict) and ("openapi" in raw or "swagger" in raw):
            return "OPENAPI"
        return "JSON_SCHEMA" if isinstance(raw, dict) and any(key in raw for key in ("$schema", "properties")) else "STRUCTURED"
    if suffix == ".proto":
        return "PROTOBUF"
    if suffix in {".graphql", ".gql"}:
        return "GRAPHQL"
    if suffix in {".sqlite", ".db"}:
        return "SQLITE"
    if path.name == "schema.prisma" or suffix == ".prisma":
        return "PRISMA"
    return "UNKNOWN"


def def_load_structured(path: Path) -> tuple[Any, bytes]:
    content = def_read_bytes(path)
    text = content.decode(DEFAULT_ENCODING)
    if path.suffix.lower() == ".json":
        return json.loads(text), content
    if yaml is None:
        try:
            return json.loads(text), content
        except json.JSONDecodeError as exc:
            raise RuntimeError("PyYAML is required for YAML contracts: pip install pyyaml") from exc
    return yaml.safe_load(text), content


def def_schema_type(schema: Mapping[str, Any]) -> str:
    value = schema.get("type", "any")
    if isinstance(value, list):
        return "|".join(str(item) for item in value)
    if value == "array":
        item_type = schema.get("items", {}).get("type", "any") if isinstance(schema.get("items"), dict) else "any"
        return f"array[{item_type}]"
    return str(value)


def def_extract_json_schema_fields(raw: Mapping[str, Any]) -> dict[str, FieldSpec]:
    schema: Mapping[str, Any] = raw
    if "components" in raw and isinstance(raw.get("components"), dict):
        schemas = raw["components"].get("schemas", {})
        merged: dict[str, FieldSpec] = {}
        for schema_name, component in schemas.items():
            if not isinstance(component, dict):
                continue
            required = set(component.get("required", []))
            for name, spec in component.get("properties", {}).items():
                if not isinstance(spec, dict):
                    continue
                qualified = f"{schema_name}.{name}"
                merged[qualified] = FieldSpec(
                    canonical_name=qualified,
                    data_type=def_schema_type(spec),
                    required=name in required,
                    description=str(spec.get("description", "")),
                    aliases=tuple(spec.get("x-via-aliases", [])),
                    pattern=spec.get("pattern"),
                )
        if merged:
            return merged
    required = set(schema.get("required", []))
    fields: dict[str, FieldSpec] = {}
    for name, spec in schema.get("properties", {}).items():
        if not isinstance(spec, dict):
            spec = {}
        fields[name] = FieldSpec(
            canonical_name=name,
            data_type=def_schema_type(spec),
            required=name in required,
            description=str(spec.get("description", "")),
            aliases=tuple(spec.get("x-via-aliases", [])),
            pattern=spec.get("pattern"),
        )
    return fields


def def_extract_proto_fields(text: str) -> dict[str, FieldSpec]:
    fields: dict[str, FieldSpec] = {}
    message_name = "Message"
    for line in text.splitlines():
        message = re.match(r"\s*message\s+(\w+)", line)
        if message:
            message_name = message.group(1)
        field_match = re.match(r"\s*(?:repeated\s+)?([\w.<>]+)\s+(\w+)\s*=\s*\d+", line)
        if field_match:
            data_type, name = field_match.groups()
            qualified = f"{message_name}.{name}"
            fields[qualified] = FieldSpec(qualified, data_type=data_type)
    return fields


def def_extract_graphql_fields(text: str) -> dict[str, FieldSpec]:
    fields: dict[str, FieldSpec] = {}
    current_type: str | None = None
    for line in text.splitlines():
        type_match = re.match(r"\s*(?:type|input|interface)\s+(\w+)", line)
        if type_match:
            current_type = type_match.group(1)
            continue
        if current_type and "}" in line:
            current_type = None
            continue
        field_match = re.match(r"\s*(\w+)\s*(?:\([^)]*\))?\s*:\s*([\[\]!\w]+)", line)
        if current_type and field_match:
            name, data_type = field_match.groups()
            qualified = f"{current_type}.{name}"
            fields[qualified] = FieldSpec(qualified, data_type=data_type, required=data_type.endswith("!"))
    return fields


def def_extract_prisma_fields(text: str) -> dict[str, FieldSpec]:
    fields: dict[str, FieldSpec] = {}
    model_name: str | None = None
    for line in text.splitlines():
        model_match = re.match(r"\s*model\s+(\w+)", line)
        if model_match:
            model_name = model_match.group(1)
            continue
        if model_name and "}" in line:
            model_name = None
            continue
        field_match = re.match(r"\s*(\w+)\s+([\w\[\]?]+)", line)
        if model_name and field_match and not line.strip().startswith(("//", "@@")):
            name, data_type = field_match.groups()
            qualified = f"{model_name}.{name}"
            fields[qualified] = FieldSpec(qualified, data_type=data_type, required=not data_type.endswith("?"))
    return fields


def def_extract_sqlite_fields(path: Path) -> dict[str, FieldSpec]:
    uri = f"file:{path.resolve().as_posix()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    try:
        tables = connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
        fields: dict[str, FieldSpec] = {}
        for (table_name,) in tables:
            safe_table = str(table_name).replace('"', '""')
            for column in connection.execute(f'PRAGMA table_info("{safe_table}")').fetchall():
                _, name, data_type, not_null, _, primary_key = column
                qualified = f"{table_name}.{name}"
                fields[qualified] = FieldSpec(
                    canonical_name=qualified,
                    data_type=str(data_type or "any"),
                    required=bool(not_null or primary_key),
                )
        return fields
    finally:
        connection.close()


def def_load_contract(path_value: str) -> ContractDocument:
    path = Path(path_value).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.suffix.lower() not in SUPPORTED_CONTRACT_SUFFIXES and path.name != "schema.prisma":
        raise ValueError(f"Unsupported contract type: {path}")

    raw: Any = None
    content = def_read_bytes(path)
    kind = def_detect_contract_kind(path)
    fields: dict[str, FieldSpec]

    if path.suffix.lower() in {".json", ".yaml", ".yml"}:
        raw, content = def_load_structured(path)
        kind = def_detect_contract_kind(path, raw)
        if not isinstance(raw, dict):
            raise ValueError("Structured contract root must be an object")
        fields = def_extract_json_schema_fields(raw)
    elif kind == "PROTOBUF":
        raw = content.decode(DEFAULT_ENCODING)
        fields = def_extract_proto_fields(raw)
    elif kind == "GRAPHQL":
        raw = content.decode(DEFAULT_ENCODING)
        fields = def_extract_graphql_fields(raw)
    elif kind == "PRISMA":
        raw = content.decode(DEFAULT_ENCODING)
        fields = def_extract_prisma_fields(raw)
    elif kind == "SQLITE":
        fields = def_extract_sqlite_fields(path)
    else:
        raise ValueError(f"No loader for contract kind: {kind}")

    version = str(raw.get("info", {}).get("version", raw.get("version", "UNVERSIONED"))) if isinstance(raw, dict) else "UNVERSIONED"
    name = str(raw.get("info", {}).get("title", raw.get("title", path.stem))) if isinstance(raw, dict) else path.stem
    diagnostics = [] if fields else ["No fields were extracted from the contract"]
    return ContractDocument(str(path), kind, name, version, def_sha256_bytes(content), fields, raw, diagnostics)


# =============================================================================
# def 06 VALIDATION, MAPPING AND COMPATIBILITY
# =============================================================================

def def_validate_contract(document: ContractDocument) -> list[str]:
    findings = list(document.diagnostics)
    if not document.fields:
        findings.append("Contract contains no addressable fields")
    normalized_seen: dict[str, str] = {}
    for name, spec in document.fields.items():
        normalized = def_normalize_name(name.split(".")[-1])
        if not normalized:
            findings.append(f"Invalid empty normalized field name: {name}")
        elif normalized in normalized_seen and normalized_seen[normalized] != name:
            findings.append(f"Normalized field collision: {normalized_seen[normalized]} <-> {name}")
        else:
            normalized_seen[normalized] = name
        if spec.pattern:
            try:
                re.compile(spec.pattern)
            except re.error as exc:
                findings.append(f"Invalid regex for {name}: {exc}")
    if document.kind in {"OPENAPI", "JSON_SCHEMA"} and jsonschema is not None and isinstance(document.raw, dict):
        try:
            if document.kind == "JSON_SCHEMA":
                jsonschema.Draft202012Validator.check_schema(document.raw)
        except Exception as exc:
            findings.append(f"JSON Schema validation failed: {exc}")
    return findings


def def_canonical_alias_index() -> dict[str, str]:
    index: dict[str, str] = {}
    for canonical, rule in DOMAIN_ALIAS_REGISTRY.items():
        index[def_normalize_name(canonical)] = canonical
        for alias in rule.get("aliases", []):
            index[def_normalize_name(alias)] = canonical
    return index


def def_field_leaf(name: str) -> str:
    return name.rsplit(".", 1)[-1]


def def_map_fields(source: ContractDocument, target: ContractDocument | None) -> list[MappingDecision]:
    alias_index = def_canonical_alias_index()
    target_names = list(target.fields) if target else list(DOMAIN_ALIAS_REGISTRY)
    target_normalized = {def_normalize_name(def_field_leaf(name)): name for name in target_names}
    decisions: list[MappingDecision] = []

    for source_name in source.fields:
        leaf = def_field_leaf(source_name)
        normalized = def_normalize_name(leaf)
        if normalized in target_normalized:
            decisions.append(MappingDecision(source_name, target_normalized[normalized], "EXACT_NORMALIZED", 1.0, "MAPPED", "Exact normalized name"))
            continue
        canonical = alias_index.get(normalized)
        if canonical:
            candidates = [name for name in target_names if def_normalize_name(def_field_leaf(name)) == def_normalize_name(canonical)]
            mapped = candidates[0] if candidates else canonical
            decisions.append(MappingDecision(source_name, mapped, "SSOT_ALIAS", 0.99, "MAPPED", f"Alias of {canonical}"))
            continue
        candidates = difflib.get_close_matches(normalized, list(target_normalized), n=2, cutoff=DEFAULT_SIMILARITY_THRESHOLD)
        if len(candidates) == 1:
            candidate = candidates[0]
            confidence = difflib.SequenceMatcher(None, normalized, candidate).ratio()
            decisions.append(MappingDecision(source_name, target_normalized[candidate], "FUZZY_REVIEW", confidence, "REVIEW_REQUIRED", "Similarity match requires approval"))
        elif len(candidates) > 1:
            decisions.append(MappingDecision(source_name, None, "AMBIGUOUS", 0.0, "REVIEW_REQUIRED", f"Ambiguous candidates: {candidates}"))
        else:
            decisions.append(MappingDecision(source_name, None, "UNMAPPED", 0.0, "UNMAPPED", "No canonical candidate"))
    return decisions


def def_compare_contracts(old: ContractDocument, new: ContractDocument) -> list[ContractChange]:
    changes: list[ContractChange] = []
    all_names = sorted(set(old.fields) | set(new.fields))
    for name in all_names:
        before = old.fields.get(name)
        after = new.fields.get(name)
        if before is None and after is not None:
            changes.append(ContractChange(name, ChangeKind.ADDED.value, bool(after.required), None, after.data_type))
        elif before is not None and after is None:
            changes.append(ContractChange(name, ChangeKind.REMOVED.value, True, before.data_type, None))
        elif before and after and before.data_type != after.data_type:
            changes.append(ContractChange(name, ChangeKind.TYPE_CHANGED.value, True, before.data_type, after.data_type))
        elif before and after and before.required != after.required:
            breaking = not before.required and after.required
            changes.append(ContractChange(name, ChangeKind.REQUIRED_CHANGED.value, breaking, str(before.required), str(after.required)))
    return changes


def def_resolve_gate(validation_findings: Sequence[str], mappings: Sequence[MappingDecision], changes: Sequence[ContractChange]) -> Gate:
    if validation_findings:
        return Gate.FAIL_CLOSED
    if DEFAULT_FAIL_ON_BREAKING and any(change.breaking for change in changes):
        return Gate.FAIL_CLOSED
    if any(item.status in {"UNMAPPED", "REVIEW_REQUIRED"} for item in mappings):
        return Gate.WARN
    return Gate.PASS


# =============================================================================
# def 07 GENERATOR AND CONNECTOR ORCHESTRATION
# =============================================================================

def def_detect_local_tools() -> dict[str, str | None]:
    tools = {profile["tool"] for profile in GENERATOR_PROFILES.values()}
    tools.update({"buf", "spectral", "openapi-diff", "graphql-inspector", "prisma", "node", "npm"})
    return {tool: shutil.which(tool) for tool in sorted(tools)}


def def_render_command(template: Sequence[str], input_path: str, output_dir: str) -> list[str]:
    return [part.format(input=input_path, output_dir=output_dir) for part in template]


def def_build_generator_plans(document: ContractDocument, profiles: Sequence[str], output_dir: Path) -> list[GeneratorPlan]:
    detected = def_detect_local_tools()
    plans: list[GeneratorPlan] = []
    for profile_name in profiles:
        profile = GENERATOR_PROFILES.get(profile_name)
        if profile is None:
            raise ValueError(f"Unknown generator profile: {profile_name}")
        if document.kind not in profile["input_kinds"]:
            raise ValueError(f"Profile {profile_name} does not accept {document.kind}")
        tool = str(profile["tool"])
        command = def_render_command(profile["command"], document.source_path, str(output_dir / profile_name))
        plans.append(GeneratorPlan(profile_name, tool, bool(detected.get(tool)), command))
    return plans


def def_execute_generator_plan(plan: GeneratorPlan, apply: bool, gate: Gate, allow_warn_apply: bool = False) -> GeneratorPlan:
    if not apply or gate == Gate.FAIL_CLOSED or (gate == Gate.WARN and not allow_warn_apply) or not plan.available:
        return plan
    executable = Path(plan.command[0]).name
    if executable not in ALLOWED_GENERATOR_EXECUTABLES:
        plan.stderr = f"Executable is not allow-listed: {executable}"
        return plan
    for part in plan.command:
        if part.startswith("--") and "_out=" in part:
            Path(part.split("=", 1)[1]).mkdir(parents=True, exist_ok=True)
    process = subprocess.run(
        plan.command,
        check=False,
        capture_output=True,
        text=True,
        timeout=DEFAULT_COMMAND_TIMEOUT_SECONDS,
    )
    plan.applied = True
    plan.return_code = process.returncode
    plan.stdout = process.stdout[-10000:]
    plan.stderr = process.stderr[-10000:]
    return plan


# =============================================================================
# def 08 APPEND-ONLY REGISTRY AND REPORTS
# =============================================================================

def def_initialize_registry(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS contract_runs (
                run_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                engine_version TEXT NOT NULL,
                gate TEXT NOT NULL,
                source_digest TEXT NOT NULL,
                target_digest TEXT,
                evidence_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS contract_artifacts (
                artifact_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                artifact_kind TEXT NOT NULL,
                artifact_path TEXT NOT NULL,
                artifact_digest TEXT,
                FOREIGN KEY(run_id) REFERENCES contract_runs(run_id)
            );
            """
        )
        connection.commit()
    finally:
        connection.close()


def def_append_evidence(path: Path, evidence: RunEvidence) -> None:
    def_initialize_registry(path)
    connection = sqlite3.connect(path)
    try:
        connection.execute(
            "INSERT INTO contract_runs VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                evidence.run_id,
                evidence.created_at,
                ENGINE_VERSION,
                evidence.gate,
                evidence.source_contract["digest"],
                evidence.target_contract["digest"] if evidence.target_contract else None,
                json.dumps(def_jsonable(evidence), ensure_ascii=False, sort_keys=True),
            ),
        )
        for kind, output_path in evidence.outputs.items():
            artifact = Path(output_path)
            digest = def_sha256_bytes(def_read_bytes(artifact)) if artifact.is_file() else None
            connection.execute(
                "INSERT INTO contract_artifacts(run_id, artifact_kind, artifact_path, artifact_digest) VALUES (?, ?, ?, ?)",
                (evidence.run_id, kind, output_path, digest),
            )
        connection.commit()
    finally:
        connection.close()


def def_contract_summary(document: ContractDocument) -> dict[str, Any]:
    return {
        "name": document.name,
        "kind": document.kind,
        "version": document.version,
        "source_path": document.source_path,
        "digest": document.digest,
        "field_count": len(document.fields),
    }


def def_write_mapping_csv(path: Path, mappings: Sequence[MappingDecision]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8-sig", newline="", delete=False, dir=path.parent) as handle:
        writer = csv.DictWriter(handle, fieldnames=["source_field", "target_field", "method", "confidence", "status", "reason"])
        writer.writeheader()
        for item in mappings:
            writer.writerow(def_jsonable(item))
        temporary = Path(handle.name)
    os.replace(temporary, path)


def def_html_table(rows: Sequence[Mapping[str, Any]], columns: Sequence[str]) -> str:
    header = "".join(f"<th>{html.escape(column)}</th>" for column in columns)
    body = "".join(
        "<tr>" + "".join(f"<td>{html.escape(str(row.get(column, '')))}</td>" for column in columns) + "</tr>"
        for row in rows
    )
    return f"<table><thead><tr>{header}</tr></thead><tbody>{body}</tbody></table>"


def def_write_html_report(path: Path, evidence: RunEvidence) -> None:
    mapping_columns = ["source_field", "target_field", "method", "confidence", "status", "reason"]
    change_columns = ["field_name", "change_kind", "breaking", "old_value", "new_value"]
    generator_columns = ["profile", "tool", "available", "applied", "return_code"]
    diagnostics = "".join(f"<li>{html.escape(item)}</li>" for item in evidence.diagnostics) or "<li>None</li>"
    content = f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(ENGINE_NAME)}</title>
<style>
body{{font-family:Inter,'Noto Sans TC',sans-serif;background:#f4f7fb;color:#243447;margin:0;padding:24px}}
.wrap{{max-width:1440px;margin:auto}} .hero,.card{{background:#fff;border:1px solid #dce5ef;border-radius:14px;padding:20px;margin-bottom:16px;box-shadow:0 4px 18px #26405f12}}
.gate{{display:inline-block;padding:6px 12px;border-radius:999px;background:#e8f1fb;color:#175b91;font-weight:700}}
.metrics{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px}} .metric{{background:#f7fafc;border-radius:10px;padding:12px}}
table{{border-collapse:collapse;width:100%;font-size:13px}} th,td{{text-align:left;border-bottom:1px solid #e5ebf1;padding:9px;vertical-align:top}} th{{background:#edf4fa;position:sticky;top:0}}
h1,h2{{margin-top:0}} .scroll{{overflow:auto;max-height:520px}} code{{font-family:'DM Mono',monospace}}
</style></head><body><div class="wrap">
<section class="hero"><h1>{html.escape(ENGINE_NAME)}</h1><p>Run: <code>{evidence.run_id}</code> · Version: {ENGINE_VERSION}</p><span class="gate">{evidence.gate}</span></section>
<section class="card metrics"><div class="metric"><b>Source Fields</b><br>{evidence.source_contract['field_count']}</div><div class="metric"><b>Mappings</b><br>{len(evidence.mappings)}</div><div class="metric"><b>Changes</b><br>{len(evidence.changes)}</div><div class="metric"><b>Generators</b><br>{len(evidence.generators)}</div></section>
<section class="card"><h2>Contract</h2><pre>{html.escape(json.dumps({'source': evidence.source_contract, 'target': evidence.target_contract}, ensure_ascii=False, indent=2))}</pre></section>
<section class="card"><h2>Diagnostics</h2><ul>{diagnostics}</ul></section>
<section class="card"><h2>Field Mapping</h2><div class="scroll">{def_html_table(evidence.mappings, mapping_columns)}</div></section>
<section class="card"><h2>Compatibility Changes</h2><div class="scroll">{def_html_table(evidence.changes, change_columns)}</div></section>
<section class="card"><h2>Generator Plans</h2><div class="scroll">{def_html_table(evidence.generators, generator_columns)}</div></section>
</div></body></html>"""
    def_atomic_write_text(path, content)


# =============================================================================
# def 09 INITIAL CONTRACT TEMPLATE AND SELF-TEST
# =============================================================================

def def_default_contract() -> dict[str, Any]:
    properties: dict[str, Any] = {}
    required = ["TW_TICKER", "BROKER_ID", "INVESTMENT_RATING", "TARGET_PRICE"]
    for canonical, rule in DOMAIN_ALIAS_REGISTRY.items():
        item: dict[str, Any] = {
            "type": "string" if canonical != "TARGET_PRICE" else "number",
            "x-via-aliases": rule.get("aliases", []),
        }
        if rule.get("regex"):
            item["pattern"] = rule["regex"]
        properties[canonical] = item
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "VIA Financial Interface Canonical Contract",
        "version": "1.0.0",
        "type": "object",
        "additionalProperties": False,
        "required": required,
        "properties": properties,
        "x-via-rating-aliases": INVESTMENT_RATING_ALIASES,
        "x-via-target-price-aliases": TARGET_PRICE_ALIASES,
        "x-via-period-patterns": PERIOD_PATTERNS,
    }


def def_initialize_contract_file(path: Path) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing contract: {path}")
    def_atomic_write_text(path, json.dumps(def_default_contract(), ensure_ascii=False, indent=2) + "\n")


def def_run_self_test() -> list[str]:
    failures: list[str] = []
    period_cases = {
        "2026Q1E Target Price": (2026, 1),
        "Target Price 1Q26E": (2026, 1),
        "Target Price Q1’26": (2026, 1),
        "2026年第一季目標價": (2026, 1),
        "115Q1E目標價": (2026, 1),
        "２０２６Ｑ２Ｅ Target Price": (2026, 2),
        "115年目標價": (2026, None),
        "FY27E TP": (2027, None),
        "2026H2F": (2026, None),
    }
    for text, expected in period_cases.items():
        parsed = def_parse_period(text)
        actual = (parsed.get("year"), parsed.get("quarter")) if parsed else None
        if actual != expected:
            failures.append(f"Period parse failed: {text}: {actual} != {expected}")
    if def_normalize_investment_rating("優於大盤") != "OUTPERFORM":
        failures.append("Investment rating alias normalization failed")
    if def_normalize_target_price_term("Price Target") != "TARGET_PRICE":
        failures.append("Target price alias normalization failed")
    for field_name, value, expected in [
        ("TW_TICKER", "2330", True),
        ("TW_TICKER", "0230", False),
        ("TW_YFINANCE_TICKER", "8069.TWO", True),
        ("TW_BLOOMBERG_TICKER", "2330 TT", True),
    ]:
        actual, _ = def_validate_domain_value(field_name, value)
        if actual != expected:
            failures.append(f"Domain validation failed: {field_name}={value}")
    return failures


def def_user_test_check(checks: list[dict[str, Any]], name: str, condition: bool, detail: str) -> None:
    checks.append({"name": name, "status": "PASS" if condition else "FAIL", "detail": detail})


def def_run_user_test() -> UserTestEvidence:
    checks: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="via_user_test_") as temporary_directory:
        root = Path(temporary_directory)
        canonical_path = root / "canonical.json"
        incoming_path = root / "incoming.json"
        breaking_path = root / "breaking.json"
        output_root = root / "runs"

        def_atomic_write_json(canonical_path, def_default_contract())
        canonical = def_default_contract()
        incoming = json.loads(json.dumps(canonical))
        incoming["title"] = "User Incoming Financial Interface"
        incoming["properties"]["BrokerNameZhTw"] = {"type": "string"}
        def_atomic_write_json(incoming_path, incoming)

        breaking = json.loads(json.dumps(canonical))
        del breaking["properties"]["TW_TICKER"]
        breaking["required"] = [name for name in breaking["required"] if name != "TW_TICKER"]
        def_atomic_write_json(breaking_path, breaking)

        canonical_doc = def_load_contract(str(canonical_path))
        incoming_doc = def_load_contract(str(incoming_path))
        alias_mappings = def_map_fields(incoming_doc, canonical_doc)
        broker_mapping = next((item for item in alias_mappings if item.source_field == "BrokerNameZhTw"), None)
        def_user_test_check(
            checks,
            "SSOT alias mapping",
            broker_mapping is not None and broker_mapping.target_field == "BROKER_NAME_ZH_TW",
            str(def_jsonable(broker_mapping)) if broker_mapping else "missing mapping",
        )

        breaking_doc = def_load_contract(str(breaking_path))
        breaking_changes = def_compare_contracts(canonical_doc, breaking_doc)
        def_user_test_check(
            checks,
            "Breaking removal detection",
            any(item.field_name == "TW_TICKER" and item.breaking for item in breaking_changes),
            str([def_jsonable(item) for item in breaking_changes]),
        )

        evidence, run_dir = def_run_engine(
            source_path=str(canonical_path),
            target_path=str(canonical_path),
            output_root=str(output_root),
            registry_db=None,
            generator_profiles=[],
            apply=False,
            allow_warn_apply=False,
        )
        def_user_test_check(checks, "End-to-end PASS gate", evidence.gate == Gate.PASS.value, evidence.gate)
        def_user_test_check(
            checks,
            "Evidence artifacts",
            all(Path(value).is_file() and Path(value).stat().st_size > 0 for value in evidence.outputs.values()),
            str(run_dir),
        )
        registry_path = output_root / DEFAULT_REGISTRY_DB
        registry_rows = 0
        if registry_path.is_file():
            connection = sqlite3.connect(registry_path)
            try:
                registry_rows = int(connection.execute("SELECT COUNT(*) FROM contract_runs").fetchone()[0])
            finally:
                connection.close()
        def_user_test_check(checks, "Append-only registry", registry_rows == 1, f"rows={registry_rows}")

        failure_evidence, _ = def_run_engine(
            source_path=str(breaking_path),
            target_path=str(canonical_path),
            output_root=str(root / "breaking_runs"),
            registry_db=None,
            generator_profiles=[],
            apply=False,
            allow_warn_apply=False,
        )
        def_user_test_check(checks, "Breaking Gate fail-closed", failure_evidence.gate == Gate.FAIL_CLOSED.value, failure_evidence.gate)

        blocked_plan = GeneratorPlan(
            profile="warn_safety_test",
            tool="protoc",
            available=True,
            command=["protoc", "--version"],
        )
        blocked_plan = def_execute_generator_plan(blocked_plan, apply=True, gate=Gate.WARN, allow_warn_apply=False)
        def_user_test_check(
            checks,
            "WARN execution blocked by default",
            not blocked_plan.applied and blocked_plan.return_code is None,
            str(def_jsonable(blocked_plan)),
        )

    failed = sum(item["status"] == "FAIL" for item in checks)
    return UserTestEvidence(
        created_at=def_utc_now(),
        gate=Gate.PASS.value if failed == 0 else Gate.FAIL_CLOSED.value,
        passed=len(checks) - failed,
        failed=failed,
        checks=checks,
    )


def def_activate_engine(contract_path: str, activation_dir: str, registry_db: str | None) -> tuple[ActivationEvidence, Path]:
    contract = def_load_contract(contract_path)
    findings = def_validate_contract(contract)
    self_test_failures = def_run_self_test()
    user_test = def_run_user_test()
    gate = Gate.PASS
    if findings or self_test_failures or user_test.gate != Gate.PASS.value:
        gate = Gate.FAIL_CLOSED

    activation_root = Path(activation_dir).expanduser().resolve()
    activation_root.mkdir(parents=True, exist_ok=True)
    registry_path = Path(registry_db).expanduser().resolve() if registry_db else activation_root / DEFAULT_REGISTRY_DB
    def_initialize_registry(registry_path)
    activation = ActivationEvidence(
        activation_id=f"ACTIVATION_{def_run_id()}",
        created_at=def_utc_now(),
        engine_name=ENGINE_NAME,
        engine_version=ENGINE_VERSION,
        gate=gate.value,
        contract_path=contract.source_path,
        contract_digest=contract.digest,
        registry_path=str(registry_path),
        self_test_passed=not self_test_failures,
        user_test_passed=user_test.gate == Gate.PASS.value,
        external_runtime_executed=False,
    )
    activation_path = activation_root / "VIA_CONTRACT_ENGINE_ACTIVATION.json"
    def_atomic_write_json(activation_path, activation)
    return activation, activation_path


# =============================================================================
# def 10 ORCHESTRATOR
# =============================================================================

def def_run_engine(
    source_path: str,
    target_path: str | None,
    output_root: str,
    registry_db: str | None,
    generator_profiles: Sequence[str],
    apply: bool,
    allow_warn_apply: bool = False,
) -> tuple[RunEvidence, Path]:
    run_id = def_run_id()
    run_dir = Path(output_root).expanduser().resolve() / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    source = def_load_contract(source_path)
    target = def_load_contract(target_path) if target_path else None
    findings = def_validate_contract(source)
    if target:
        findings.extend(f"Target: {item}" for item in def_validate_contract(target))

    mappings = def_map_fields(source, target)
    changes = def_compare_contracts(target, source) if target else []
    gate = def_resolve_gate(findings, mappings, changes)
    generator_output = run_dir / "generated"
    plans = def_build_generator_plans(source, generator_profiles, generator_output) if generator_profiles else []
    plans = [def_execute_generator_plan(plan, apply, gate, allow_warn_apply) for plan in plans]

    if any(plan.applied and plan.return_code != 0 for plan in plans):
        gate = Gate.FAIL_CLOSED
        findings.append("One or more generator commands failed")

    outputs = {
        "json": str(run_dir / "evidence.json"),
        "csv": str(run_dir / "field_mapping.csv"),
        "html": str(run_dir / "evidence.html"),
    }
    evidence = RunEvidence(
        run_id=run_id,
        created_at=def_utc_now(),
        gate=gate.value,
        source_contract=def_contract_summary(source),
        target_contract=def_contract_summary(target) if target else None,
        mappings=[def_jsonable(item) for item in mappings],
        changes=[def_jsonable(item) for item in changes],
        generators=[def_jsonable(item) for item in plans],
        diagnostics=findings,
        outputs=outputs,
    )

    def_write_mapping_csv(Path(outputs["csv"]), mappings)
    def_write_html_report(Path(outputs["html"]), evidence)
    def_atomic_write_json(Path(outputs["json"]), evidence)

    registry_path = Path(registry_db).expanduser().resolve() if registry_db else Path(output_root).expanduser().resolve() / DEFAULT_REGISTRY_DB
    def_append_evidence(registry_path, evidence)
    return evidence, run_dir


# =============================================================================
# def 11 CLI
# =============================================================================

def def_build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=ENGINE_NAME)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create the canonical VIA JSON contract")
    init_parser.add_argument("--output", default="via_financial_contract.json")

    run_parser = subparsers.add_parser("run", help="Validate, map, compare and optionally generate interfaces")
    run_parser.add_argument("--source", required=True, help="Incoming/new contract")
    run_parser.add_argument("--target", help="Existing/canonical contract")
    run_parser.add_argument("--output-root", default=DEFAULT_OUTPUT_DIR)
    run_parser.add_argument("--registry-db", default=None)
    run_parser.add_argument("--generator", action="append", choices=sorted(GENERATOR_PROFILES), default=[])
    run_parser.add_argument("--apply", action="store_true", help="Execute available allow-listed generators after Gate")
    run_parser.add_argument("--allow-warn-apply", action="store_true", help="Explicitly allow generator execution when Gate is WARN")

    subparsers.add_parser("self-test", help="Run deterministic local tests")
    subparsers.add_parser("user-test", help="Run isolated end-to-end user acceptance tests")
    subparsers.add_parser("tools", help="Show locally detected integration tools")
    activate_parser = subparsers.add_parser("activate", help="Create a governed activation manifest after all tests pass")
    activate_parser.add_argument("--contract", required=True)
    activate_parser.add_argument("--activation-dir", default="_via_contract_engine_active")
    activate_parser.add_argument("--registry-db", default=None)
    return parser


def def_main(argv: Sequence[str] | None = None) -> int:
    args = def_build_parser().parse_args(argv)
    if args.command == "init":
        output = Path(args.output).expanduser().resolve()
        def_initialize_contract_file(output)
        print(json.dumps({"gate": "PASS", "output": str(output)}, ensure_ascii=False))
        return 0
    if args.command == "self-test":
        failures = def_run_self_test()
        print(json.dumps({"gate": "PASS" if not failures else "FAIL_CLOSED", "failures": failures}, ensure_ascii=False, indent=2))
        return 0 if not failures else 2
    if args.command == "user-test":
        evidence = def_run_user_test()
        print(json.dumps(def_jsonable(evidence), ensure_ascii=False, indent=2))
        return 0 if evidence.gate == Gate.PASS.value else 2
    if args.command == "tools":
        print(json.dumps(def_detect_local_tools(), ensure_ascii=False, indent=2))
        return 0
    if args.command == "activate":
        evidence, activation_path = def_activate_engine(args.contract, args.activation_dir, args.registry_db)
        print(json.dumps({"activation": def_jsonable(evidence), "activation_path": str(activation_path)}, ensure_ascii=False, indent=2))
        return 0 if evidence.gate == Gate.PASS.value else 2
    if args.command == "run":
        evidence, run_dir = def_run_engine(
            source_path=args.source,
            target_path=args.target,
            output_root=args.output_root,
            registry_db=args.registry_db,
            generator_profiles=args.generator,
            apply=args.apply,
            allow_warn_apply=args.allow_warn_apply,
        )
        print(json.dumps({"gate": evidence.gate, "run_id": evidence.run_id, "run_dir": str(run_dir), "outputs": evidence.outputs}, ensure_ascii=False, indent=2))
        return 0 if evidence.gate in {Gate.PASS.value, Gate.WARN.value} else 2
    return 2


if __name__ == "__main__":
    raise SystemExit(def_main())
