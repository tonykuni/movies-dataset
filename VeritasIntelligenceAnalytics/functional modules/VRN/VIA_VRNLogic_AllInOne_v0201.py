#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA / VRN report logic engine — all-in-one edition.

Single-file, standard-library-first implementation for filename, first-page and
financial-page normalization, evidence reconciliation, resumable batch staging,
deterministic output, sixteen-check acceptance testing and guarded atomic
installation.  The module is intentionally offline and has no import-time writes.
"""
from __future__ import annotations

# =============================================================================
# def 00 PARAMETERS / SSOT BINDINGS
# =============================================================================

MODULE_ID = "VIA-VRN-LOGIC-001"
MODULE_NAME = "vrn_logic"
MODULE_VERSION = "3.2.0"
SCHEMA_VERSION = "VIA.VRN.Logic.v3"
WORLDLINE = "WL-MAIN"
AUTHORITY = "VIA-SYSTEM-MASTER-001"
DEFAULT_CONFIDENCE = 0.80
MATCH_CONFIDENCE_BONUS = 0.15
UNRESOLVED_CONFIDENCE_PENALTY = 0.20
MAX_CONFIDENCE = 1.00
MIN_TARGET_PRICE = 0.20
MAX_TARGET_PRICE = 1_000_000.00
DEFAULT_ENCODING = "utf-8-sig"
DATE_OUTPUT_FORMAT = "%Y/%m/%d"
DATE_CANONICAL_FORMAT = "%Y-%m-%d"
DEFAULT_OUTPUT_STEM_BASIC = "StockReportBasicInfo"
DEFAULT_OUTPUT_STEM_FINANCIAL = "StockReportFinancialData"
DEFAULT_OUTPUT_STEM_EVIDENCE = "VRNLogicEvidence"
DEFAULT_FORMATS = ("json", "csv", "sqlite")
DEFAULT_PDF_DPI = 150
DEFAULT_PDF_MAX_PAGES = 0
DEFAULT_FINANCIAL_PAGE_SCORE = 3
DEFAULT_VDF_MAX_FILES = 40
DEFAULT_VDF_MAX_ROWS = 100_000
DEFAULT_SQLITE_NAME = "VRN_ReportDatabase.sqlite"
DEFAULT_DUCKDB_NAME = "VRN_ReportDatabase.duckdb"
DEFAULT_BATCH_CHECKPOINT_NAME = "VRN_BatchCheckpoint.json"
DEFAULT_BATCH_SUMMARY_NAME = "VRN_BatchSummary.json"
DEFAULT_BATCH_MATRIX_NAME = "VRN_BatchMatrix.csv"
DEFAULT_BATCH_REPORT_NAME = "VRN_BatchReport.html"
DEFAULT_BATCH_EVIDENCE_NAME = "VRNLogicEvidence.jsonl"
DEFAULT_BATCH_MAX_FILES = 10_000
DEFAULT_SQLITE_RETRY_ATTEMPTS = 3
DEFAULT_SQLITE_BUSY_TIMEOUT_MS = 5_000
DEFAULT_INSTALL_MODE = "audit"
DEFAULT_REPO_RELATIVE = "movies-dataset"
DEFAULT_PROJECT_RELATIVE = "VeritasIntelligenceAnalytics"
DEFAULT_TARGET_RELATIVE = "via/vrn_logic.py"
DEFAULT_REPORT_RELATIVE = "VIA_Reports"
DEFAULT_INSTALL_TIMEOUT_SECONDS = 90
DEFAULT_REQUIRED_CHECKS = 16
INSTALL_REPORT_SCHEMA = "VIA.VRN.Logic.AllInOneInstall.v3.2"
BATCH_CHECKPOINT_SCHEMA = "VIA.VRN.BatchCheckpoint.v1"
BATCH_SUMMARY_SCHEMA = "VIA.VRN.BatchSummary.v1"
STAGE_OUTPUT_CONTRACT = (
    ("checkpoint", DEFAULT_BATCH_CHECKPOINT_NAME, "json"),
    ("summary", DEFAULT_BATCH_SUMMARY_NAME, "json_self"),
    ("matrix", DEFAULT_BATCH_MATRIX_NAME, "csv_matrix"),
    ("report", DEFAULT_BATCH_REPORT_NAME, "html"),
    ("evidence", DEFAULT_BATCH_EVIDENCE_NAME, "jsonl_evidence"),
    ("basic_info", f"{DEFAULT_OUTPUT_STEM_BASIC}.csv", "csv_basic"),
    ("financial_data", f"{DEFAULT_OUTPUT_STEM_FINANCIAL}.csv", "csv_financial"),
    ("database", DEFAULT_SQLITE_NAME, "sqlite"),
    ("backup", f"backups/{DEFAULT_SQLITE_NAME}.*.bak", "sqlite_backup"),
)
SOURCE_PRIORITY = ("official", "vdf", "financial_page", "first_page", "filename", "unknown")
VALIDATION_STATES = ("GREEN", "YELLOW", "RED")
FINANCIAL_GRADES = ("V", "M", "P")
MISSING_TEXT_MARKERS = ("", "—", "-", "N/A", "NA", "NONE", "NULL")
REPORT_TYPES = (
    "COMPANY_UPDATE",
    "INITIATION",
    "EARNINGS_REVIEW",
    "CONFERENCE_CALL",
    "INDUSTRY_REPORT",
    "MARKET_REPORT",
    "MEMO",
    "FINANCIAL_SHEET",
    "OTHER",
)

TICKER_REGEX_DICT = {
    "TW_STOCK": r"(?<!\d)([1-9]\d{3})(?!\d)",
    "TW_ACTIVE_ETF": r"(?<!\d)(00\d{3}[AD])(?![A-Z0-9])",
    "YFINANCE_TWSE": r"(?<!\d)([1-9]\d{3})\.TW(?![A-Z0-9])",
    "YFINANCE_TPEX": r"(?<!\d)([1-9]\d{3})\.TWO(?![A-Z0-9])",
    "BLOOMBERG_TW": r"(?<!\d)([1-9]\d{3})\s+TT(?![A-Z0-9])",
}

COMPANY_NAME_DICT = {
    "1101": "台泥",
    "2303": "聯電",
    "2317": "鴻海",
    "2330": "台積電",
    "2454": "聯發科",
    "2603": "長榮",
    "3017": "奇鋐",
    "3324": "雙鴻",
    "6533": "晶心科",
    "8069": "元太",
}
COMPANY_ALIAS_DICT = {
    "1101": ("台泥", "TAIWAN CEMENT"),
    "2303": ("聯電", "UMC"),
    "2317": ("鴻海", "HON HAI", "FOXCONN"),
    "2330": ("台積電", "TSMC", "TAIWAN SEMICONDUCTOR"),
    "2454": ("聯發科", "MEDIATEK"),
    "2603": ("長榮", "EVERGREEN"),
    "3017": ("奇鋐", "AVC"),
    "3324": ("雙鴻", "AURAS"),
    "6533": ("晶心科", "ANDES"),
    "8069": ("元太", "E INK"),
}

BROKER_DICT = {
    "CTBC": {"name": "中信證券", "aliases": ("CTBC", "中信", "中國信託", "中信投顧", "中信證券")},
    "CATHAY": {"name": "國泰證券", "aliases": ("CATHAY", "國泰", "國泰證券", "國泰投顧")},
    "FUBON": {"name": "富邦證券", "aliases": ("FUBON", "富邦", "富邦證券", "富邦投顧")},
    "YUANTA": {"name": "元大證券", "aliases": ("YUANTA", "元大", "元大證券", "元大投顧")},
    "MEGA": {"name": "兆豐證券", "aliases": ("MEGA", "兆豐", "兆豐證券", "兆豐投顧")},
    "KGI": {"name": "凱基證券", "aliases": ("KGI", "凱基", "凱基證券", "凱基投顧")},
    "SINO": {"name": "永豐金證券", "aliases": ("SINO", "SINOPAC", "永豐", "永豐金", "永豐金證券", "永豐投顧")},
    "TAISHIN": {"name": "台新證券", "aliases": ("TAISHIN", "台新", "台新證券", "台新投顧")},
    "CAPITAL": {"name": "群益證券", "aliases": ("CAPITAL", "群益", "群益證券", "群益投顧")},
    "MASTERLINK": {"name": "元富證券", "aliases": ("MASTERLINK", "元富", "元富證券", "元富投顧")},
    "PRESIDENT": {"name": "統一證券", "aliases": ("PRESIDENT", "統一", "統一證券", "統一投顧")},
    "UBS": {"name": "瑞銀", "aliases": ("UBS", "瑞銀")},
    "MS": {"name": "摩根士丹利", "aliases": ("MORGAN STANLEY", "MORGANSTANLEY", "大摩", "摩根士丹利")},
    "GS": {"name": "高盛", "aliases": ("GOLDMAN SACHS", "GOLDMANSACHS", "高盛")},
    "CITI": {"name": "花旗", "aliases": ("CITI", "CITIGROUP", "花旗")},
    "JPM": {"name": "摩根大通", "aliases": ("JPM", "J.P. MORGAN", "JP MORGAN", "摩根大通")},
    "DAIWA": {"name": "大和", "aliases": ("DAIWA", "大和")},
    "NOMURA": {"name": "野村", "aliases": ("NOMURA", "野村")},
    "MACQUARIE": {"name": "麥格理", "aliases": ("MACQUARIE", "麥格理")},
}

# Compatibility for historical misspelling used in some VRN specifications.
BRIKER_DICT = BROKER_DICT
BROKER_ALIASES = {key: tuple(value["aliases"]) for key, value in BROKER_DICT.items()}
BROKER_NAMES = {key: str(value["name"]) for key, value in BROKER_DICT.items()}

RATING_DICT = {
    "STRONG_BUY": {"score": 2.0, "label": "強力買進", "aliases": ("STRONG BUY", "STRONGBUY", "強力買進")},
    "BUY": {"score": 1.0, "label": "買進", "aliases": ("BUY", "OVERWEIGHT", "OUTPERFORM", "買進", "加碼", "優於大盤", "增持")},
    "HOLD": {"score": 0.0, "label": "持有", "aliases": ("HOLD", "NEUTRAL", "MARKET PERFORM", "中立", "持有", "續抱", "與大盤持平")},
    "SELL": {"score": -1.0, "label": "賣出", "aliases": ("SELL", "UNDERWEIGHT", "UNDERPERFORM", "賣出", "減碼", "低配", "劣於大盤")},
    "NOT_RATED": {"score": 0.0, "label": "未評等", "aliases": ("NOT RATED", "NOT-RATED", "NR", "未評等", "未評級")},
}
RATING_LIST = tuple(RATING_DICT)
RATING_ALIASES = {key: tuple(value["aliases"]) for key, value in RATING_DICT.items()}

ANNUAL_FINANCIAL_PAGE_KEYWORDS = (
    "資產負債表", "損益表", "綜合損益表", "現金流量表", "財務預測",
    "balance sheet", "income statement", "cash flow", "financial forecast",
    "營業收入", "營業利益", "稅後淨利", "每股盈餘", "eps",
)

FINANCIAL_SYNONYMS = {
    "revenue": ("revenue", "sales", "net sales", "營業收入", "營收", "銷貨收入"),
    "gross_profit": ("gross profit", "gross income", "毛利", "營業毛利"),
    "operating_income": ("operating income", "operating profit", "ebit", "營業利益", "營業利潤"),
    "net_income": ("net income", "net profit", "pat", "稅後淨利", "本期淨利", "歸母淨利"),
    "eps": ("eps", "diluted eps", "basic eps", "每股盈餘", "稀釋每股盈餘", "基本每股盈餘"),
    "total_assets": ("total assets", "資產總計", "總資產"),
    "equity": ("total equity", "shareholders equity", "權益總計", "股東權益"),
    "ocf": ("operating cash flow", "cash from operations", "營業活動現金流", "營運現金流"),
    "fcf": ("free cash flow", "自由現金流"),
    "target_price": ("target price", "tp", "目標價", "目標價格"),
}

UNIT_MULTIPLIERS_TO_MILLION = {
    "": 1.0,
    "million": 1.0,
    "mn": 1.0,
    "mn_twd": 1.0,
    "百萬": 1.0,
    "百萬元": 1.0,
    "thousand": 0.001,
    "千": 0.001,
    "千元": 0.001,
    "billion": 1000.0,
    "bn": 1000.0,
    "十億": 1000.0,
    "十億元": 1000.0,
    "hundred_million": 100.0,
    "億": 100.0,
    "億元": 100.0,
    "%": 1.0,
    "percent": 1.0,
    "twd": 1.0,
    "ntd": 1.0,
    "元": 1.0,
}

MODULE_META = {
    "id": MODULE_ID,
    "name": MODULE_NAME,
    "version": MODULE_VERSION,
    "schema": SCHEMA_VERSION,
    "authority": AUTHORITY,
    "worldline": WORLDLINE,
    "role": "VRN logic, validation and guarded-install authority candidate",
    "writer": False,
    "installer_writer": "explicit_apply_only",
    "network_default": False,
    "live_default": False,
    "max_analysis_rounds": 3,
}

SSOT_CONTRACT = {
    "root": "config/ssot/VIA_SystemMaster.via",
    "domain": "src/lib/via/vrn-ssot.ts",
    "synonym_regex": "src/lib/via/vrn-lexicon.ts",
    "ticker_date_regex": "attachments/VRN_TickerDate_Regex_v0100.json",
    "method": "attachments/VRN_Method_SSOT_v0100.json",
    "annual": "attachments/VRN_AnnualExtract_SSOT_v0100.json",
    "lifecycle": ("AUDIT", "STAGE", "APPROVE", "PROMOTE"),
    "evidence_order": ("filename", "first_page", "financial_page", "official"),
    "quote_or_abstain": True,
    "staging_before_canonical": True,
    "single_writer": "CGC-PROMOTE-WORKER-001",
}

VDF_BRIDGE_CONTRACT = {
    "mode": "LOCAL_SNAPSHOT_FIRST",
    "network_owner": "VeritasAegisNexus",
    "data_owner": "VeritasDataForge",
    "accepted_formats": ("parquet", "csv", "json", "jsonl", "sqlite", "duckdb"),
    "ticker_keys": ("ticker", "symbol", "code", "stock_id", "yfinanceTicker", "證券代號"),
    "stock_price_rule": "ADJUSTED_OHLC",
    "missing_price_rule": "PRICE_FORWARD_FILL_VOLUME_NEVER_FILL",
    "vrn_network_calls": False,
}

BATCH_CONTRACT = {
    "modes": ("AUDIT", "STAGE"),
    "checkpoint_after_each_file": True,
    "resume_default": True,
    "deduplicate_by": "SHA256",
    "red_policy": "QUARANTINE_NO_DATABASE_WRITE",
    "database_role": "STAGING_ONLY",
    "canonical_mutation": False,
    "promotion": False,
    "stage_output_contract": tuple(item[1] for item in STAGE_OUTPUT_CONTRACT),
}

REGISTRY = {
    "module": MODULE_META,
    "ssot": SSOT_CONTRACT,
    "vdf_bridge": VDF_BRIDGE_CONTRACT,
    "batch": BATCH_CONTRACT,
    "schemas": {
        "basic_info": (
            "fileId", "fileName", "reportType", "ticker", "market",
            "yfinanceTicker", "bloombergTicker", "tickerKind", "companyName",
            "broker", "brokerAbbr", "reportDate", "reportCode", "language",
            "period", "pages", "issuer", "rating", "ratingCat",
            "targetPrice", "fileNameTokens", "fileNameParts", "identityDigest",
            "TICKER", "YFINANCE_TICKER", "BLOOMBERG_TICKER", "NAME",
            "RATING", "TARGET_PRICE", "BROKER", "BROKER_KEY",
            "REPORT_DATE", "MARKET", "FILENAME", "FILENAME_TOKENS", "FILENAME_PARTS",
            "validationStatus", "validationRisk", "status",
        ),
        "financial_data": (
            "fileId", "fileName", "category", "statement", "item", "dataName",
            "period", "value", "unit", "confidence", "source", "status",
            "grade", "defects", "page", "tableId", "cellId", "engine", "rawValue",
        ),
        "identity": (
            "TICKER", "YFINANCE_TICKER", "BLOOMBERG_TICKER", "NAME",
            "RATING", "TARGET_PRICE", "BROKER", "BROKER_KEY",
            "REPORT_DATE", "MARKET", "FILENAME", "FILENAME_TOKENS",
            "FILENAME_PARTS",
        ),
        "batch_matrix": (
            "relativePath", "sourceSHA256", "bytes", "status", "lastAction",
            "validation", "ticker", "yfinanceTicker", "bloombergTicker", "name",
            "rating", "targetPrice", "broker", "financialRows", "vdfRows",
            "attempts", "duplicateOf", "resultDigest", "errorType", "errorMessage",
        ),
    },
}

ALIASES = {
    "parse_report_filename": "parse_filename",
    "extract_filename_entities": "parse_filename",
    "extract_report_metadata": "parse_filename",
    "parse_ticker": "extract_ticker",
    "resolve_ticker": "extract_ticker",
    "parse_report_date": "extract_report_date",
    "normalize_temporal": "normalize_period",
    "normalize_financial_value": "parse_financial_value",
    "reconcile": "reconcile_evidence",
    "validate_report": "reconcile_evidence",
    "run_vrn_logic": "process_report",
    "run": "process_report",
    "run_selftest": "selftest",
    "process_pdf": "process_pdf_report",
    "extract_annual_tables": "extract_annual_financial_rows",
    "load_vdf": "load_vdf_evidence",
    "run_batch": "process_batch_reports",
    "verify_batch_outputs": "validate_batch_output_contract",
}


# =============================================================================
# def 01 IMPORTS — stdlib only, kept after parameters by project convention
# =============================================================================

import argparse
import ast
import contextlib
import csv
import hashlib
import importlib.util
import io
import json
import math
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import traceback
import unicodedata
from datetime import date, datetime
from html import escape as html_escape
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


# =============================================================================
# def 02 PRIMITIVES
# =============================================================================

def clamp_confidence(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = DEFAULT_CONFIDENCE
    if not math.isfinite(number):
        number = DEFAULT_CONFIDENCE
    return round(max(0.0, min(MAX_CONFIDENCE, number)), 6)


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    text = unicodedata.normalize("NFKC", str(value))
    text = text.replace("\u200b", "").replace("\ufeff", "")
    text = re.sub(r"[\t\v\f]+", " ", text)
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r" *\r?\n *", "\n", text)
    return text.strip()


def is_missing(value: Any) -> bool:
    return normalize_text(value).upper() in MISSING_TEXT_MARKERS


def stable_json(value: Any, *, pretty: bool = False) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        allow_nan=False,
        indent=2 if pretty else None,
        separators=None if pretty else (",", ":"),
    )


def stable_digest(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest().upper()


def sha256_file(path: str | os.PathLike[str]) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def source_priority(source: Any) -> int:
    normalized = normalize_text(source).lower()
    try:
        return SOURCE_PRIORITY.index(normalized)
    except ValueError:
        return len(SOURCE_PRIORITY)


def atomic_write_text(path: str | os.PathLike[str], text: str, encoding: str = "utf-8") -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    temporary.write_text(text, encoding=encoding, newline="\n")
    os.replace(temporary, target)
    return target


def atomic_write_csv(path: str | os.PathLike[str], rows: Sequence[Mapping[str, Any]], columns: Sequence[str]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding=DEFAULT_ENCODING, newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            safe = {key: stable_json(value) if isinstance(value, (list, dict, tuple)) else value for key, value in row.items()}
            writer.writerow(safe)
    os.replace(temporary, target)
    return target


# =============================================================================
# def 03 FILENAME / ENTITY LOGIC
# =============================================================================

def tokenize_filename(filename: Any) -> list[str]:
    stem = Path(normalize_text(filename)).stem
    stem = re.sub(r"[\[\]{}()（）【】<>《》,，;；:：_+|\\/–—-]+", " ", stem)
    stem = re.sub(r"(?<=[\u4e00-\u9fff])(?=[A-Za-z0-9])", " ", stem)
    stem = re.sub(r"(?<=[A-Za-z])(?=[\u4e00-\u9fff0-9])", " ", stem)
    stem = re.sub(r"(?<=[0-9])(?=[A-Za-z\u4e00-\u9fff])", " ", stem)
    return [token for token in re.split(r"\s+", stem) if token]


def extract_ticker(value: Any) -> str:
    text = normalize_text(value).upper()
    if not text:
        return ""
    suffix_match = re.search(r"(?<!\d)([1-9]\d{3})(?:\s*TT|\.(?:TW|TWO))(?![A-Z0-9])", text)
    if suffix_match:
        return suffix_match.group(1)
    for token in tokenize_filename(text):
        if re.fullmatch(r"[1-9]\d{3}", token):
            return token
    standalone = re.search(r"(?<!\d)([1-9]\d{3})(?!\d)", text)
    return standalone.group(1) if standalone else ""


def extract_active_etf_ticker(value: Any) -> str:
    text = normalize_text(value).upper()
    match = re.search(r"(?<!\d)(00\d{3}[AD])(?![A-Z0-9])", text)
    return match.group(1) if match else ""


def infer_market(value: Any, ticker: str = "", market_hint: str = "") -> str:
    text = normalize_text(value).upper()
    hint = normalize_text(market_hint).upper()
    if ".TWO" in text or hint in {"TPEX", "OTC", "TWO"}:
        return "TPEX"
    if ".TW" in text or re.search(r"\bTT\b", text) or hint in {"TWSE", "TW", "SII"}:
        return "TWSE"
    if ticker and re.fullmatch(r"[1-9]\d{3}", ticker):
        return "UNKNOWN_TW"
    return "UNKNOWN"


def expand_ticker(ticker: str, market: str) -> dict[str, str]:
    core = normalize_text(ticker)
    if not re.fullmatch(r"[1-9]\d{3}|00\d{3}[AD]", core, re.I):
        return {"ticker": "", "market": "UNKNOWN", "yfinance": "", "bloomberg": ""}
    normalized_market = normalize_text(market).upper()
    yfinance_suffix = "TWO" if normalized_market == "TPEX" else "TW"
    return {
        "ticker": core.upper(),
        "market": normalized_market or "UNKNOWN_TW",
        "yfinance": f"{core.upper()}.{yfinance_suffix}",
        "bloomberg": f"{core.upper()} TT",
    }


def valid_date(year: int, month: int, day: int) -> str:
    try:
        return date(year, month, day).strftime(DATE_CANONICAL_FORMAT)
    except ValueError:
        return ""


def extract_report_date(value: Any) -> str:
    text = normalize_text(value)
    patterns = (
        r"(?<!\d)(20\d{2})[./_\-年](\d{1,2})[./_\-月](\d{1,2})日?(?!\d)",
        r"(?<!\d)(20\d{2})(\d{2})(\d{2})(?!\d)",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            result = valid_date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            if result:
                return result
    roc_marked = re.search(r"(?:民國\s*)?(1\d{2})[./_\-年]?(\d{2})[./_\-月]?(\d{2})日?", text)
    if roc_marked:
        result = valid_date(int(roc_marked.group(1)) + 1911, int(roc_marked.group(2)), int(roc_marked.group(3)))
        if result:
            return result
    for short in re.finditer(r"(?<!\d)(\d{2})(\d{2})(\d{2})(?!\d)", text, re.I):
        yy = int(short.group(1))
        year = 2000 + yy if yy <= 50 else 1900 + yy
        result = valid_date(year, int(short.group(2)), int(short.group(3)))
        if result:
            return result
    return ""


def normalize_period(value: Any) -> str:
    raw = normalize_text(value).upper().replace(" ", "")
    if not raw:
        return ""
    match = re.fullmatch(r"([1-4])Q(\d{2}|\d{4})([EFA])?", raw)
    if match:
        year = int(match.group(2))
        year = 2000 + year if year <= 50 else 1900 + year if year < 100 else year
        return f"{year}-Q{match.group(1)}{match.group(3) or ''}"
    match = re.fullmatch(r"(\d{2}|\d{4})Q([1-4])([EFA])?", raw)
    if match:
        year = int(match.group(1))
        year = 2000 + year if year <= 50 else 1900 + year if year < 100 else year
        return f"{year}-Q{match.group(2)}{match.group(3) or ''}"
    match = re.fullmatch(r"([12])H(\d{2}|\d{4})([EFA])?", raw)
    if match:
        year = int(match.group(2))
        year = 2000 + year if year <= 50 else 1900 + year if year < 100 else year
        return f"{year}-H{match.group(1)}{match.group(3) or ''}"
    match = re.fullmatch(r"FY(\d{2}|\d{4})([EFA])?", raw)
    if match:
        year = int(match.group(1))
        year = 2000 + year if year <= 50 else 1900 + year if year < 100 else year
        return f"FY{year}{match.group(2) or ''}"
    match = re.fullmatch(r"(20\d{2})([EFA])?", raw)
    if match:
        return f"{match.group(1)}{match.group(2) or ''}"
    if re.fullmatch(r"20\d{2}-\d{2}(?:-\d{2})?", raw):
        return raw
    return ""


def find_alias(value: Any, aliases: Mapping[str, Sequence[str]]) -> str:
    text = normalize_text(value).upper()
    compact = re.sub(r"[^A-Z0-9\u4e00-\u9fff]+", "", text)
    candidates: list[tuple[int, str]] = []
    for canonical, words in aliases.items():
        for word in words:
            normalized_word = normalize_text(word).upper()
            compact_word = re.sub(r"[^A-Z0-9\u4e00-\u9fff]+", "", normalized_word)
            if normalized_word in text or compact_word in compact:
                candidates.append((len(compact_word), canonical))
    return max(candidates, default=(0, ""))[1]


def canonicalize_broker(value: Any) -> dict[str, str]:
    key = find_alias(value, BROKER_ALIASES)
    return {"key": key, "name": BROKER_NAMES.get(key, "")}


def canonicalize_rating(value: Any) -> str:
    return find_alias(value, RATING_ALIASES)


def load_company_dictionary(path: str | os.PathLike[str] | None = None) -> dict[str, str]:
    """Load ticker→name SSOT while preserving the built-in safe minimum."""
    result = dict(COMPANY_NAME_DICT)
    if path is None:
        return result
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"COMPANY_DICTIONARY_NOT_FOUND：{source}")
    suffix = source.suffix.lower()
    if suffix == ".json":
        payload = json.loads(source.read_text(encoding="utf-8-sig"))
        if isinstance(payload, Mapping):
            records = [{"ticker": key, "name": value} for key, value in payload.items()]
        elif isinstance(payload, Sequence):
            records = [item for item in payload if isinstance(item, Mapping)]
        else:
            records = []
    elif suffix in {".csv", ".txt"}:
        with source.open("r", encoding="utf-8-sig", newline="") as handle:
            records = list(csv.DictReader(handle))
    else:
        raise ValueError(f"UNSUPPORTED_COMPANY_DICTIONARY：{suffix}")
    for row in records:
        lowered = {normalize_text(key).casefold(): value for key, value in row.items()}
        ticker = normalize_text(lowered.get("ticker", lowered.get("code", lowered.get("stockid", "")))).upper()
        name = normalize_text(lowered.get("name", lowered.get("companyname", lowered.get("證券名稱", ""))))
        ticker = re.sub(r"\.(?:TW|TWO)$", "", ticker, flags=re.I)
        if re.fullmatch(r"[1-9]\d{3}|00\d{3}[AD]", ticker) and name:
            result[ticker] = name
    return result


def resolve_company_name(ticker: Any, text: Any = "", company_dict: Mapping[str, Any] | None = None) -> str:
    dictionary = dict(COMPANY_NAME_DICT)
    if company_dict:
        for key, value in company_dict.items():
            normalized_key = normalize_text(key).upper()
            if isinstance(value, Mapping):
                name = normalize_text(value.get("name", value.get("companyName", "")))
            else:
                name = normalize_text(value)
            if normalized_key and name:
                dictionary[normalized_key] = name
    normalized_ticker = normalize_text(ticker).upper()
    if normalized_ticker in dictionary:
        return dictionary[normalized_ticker]
    normalized_text = normalize_text(text)
    matches = [name for name in dictionary.values() if name and name in normalized_text]
    if matches:
        return max(matches, key=len)
    ignored = set()
    for aliases in BROKER_ALIASES.values():
        ignored.update(normalize_text(item).upper() for item in aliases)
    for aliases in RATING_ALIASES.values():
        ignored.update(normalize_text(item).upper() for item in aliases)
    candidates: list[str] = []
    for token in tokenize_filename(normalized_text):
        upper = token.upper()
        if upper in ignored or token == normalized_ticker or extract_report_date(token):
            continue
        if re.fullmatch(r"20\d{6}|\d{6}|[1-9]\d{3}|00\d{3}[AD]", upper):
            continue
        if re.fullmatch(r"[\u4e00-\u9fff]{2,12}", token):
            candidates.append(token)
    return max(candidates, key=len, default="")


def classify_filename_tokens(filename: Any, company_dict: Mapping[str, Any] | None = None) -> list[dict[str, str]]:
    tokens = tokenize_filename(filename)
    ticker = extract_ticker(filename) or extract_active_etf_ticker(filename)
    company = resolve_company_name(ticker, filename, company_dict)
    company_aliases = {normalize_text(item).upper() for item in COMPANY_ALIAS_DICT.get(ticker, ())}
    records: list[dict[str, str]] = []
    for index, token in enumerate(tokens):
        kind = "TEXT"
        normalized = token
        if token.upper() in {ticker.upper(), f"{ticker.upper()}.TW", f"{ticker.upper()}.TWO"}:
            kind, normalized = "TICKER", ticker.upper()
        elif extract_report_date(token):
            kind, normalized = "REPORT_DATE", extract_report_date(token)
        elif canonicalize_broker(token)["key"]:
            kind, normalized = "BROKER", canonicalize_broker(token)["key"]
        elif canonicalize_rating(token):
            kind, normalized = "RATING", canonicalize_rating(token)
        elif (company and company in token) or token.upper() in company_aliases:
            kind, normalized = "NAME", company
        elif token.upper() in {"TP", "TARGET", "TARGETPRICE"}:
            kind, normalized = "TARGET_PRICE_LABEL", "TARGET_PRICE"
        elif index > 0 and tokens[index - 1].upper() in {"TP", "TARGET", "TARGETPRICE"} and re.fullmatch(r"\d+(?:\.\d+)?", token):
            kind, normalized = "TARGET_PRICE", token
        elif re.fullmatch(r"(?:TP|TARGET)(?:PRICE)?\d+(?:\.\d+)?", token, re.I):
            kind, normalized = "TARGET_PRICE", str(extract_target_price(token) or "")
        records.append({"index": str(index), "raw": token, "type": kind, "normalized": normalized})
    return records


def detect_report_type(value: Any, extension: str = "") -> str:
    text = normalize_text(value)
    ext = normalize_text(extension or Path(text).suffix).lower().lstrip(".")
    if re.search(r"產業|industry|sector", text, re.I):
        return "INDUSTRY_REPORT"
    if re.search(r"大盤|晨報|market\s*(?:report|update)", text, re.I):
        return "MARKET_REPORT"
    if re.search(r"初次|initiation", text, re.I):
        return "INITIATION"
    if re.search(r"法說|conference", text, re.I):
        return "CONFERENCE_CALL"
    if re.search(r"年報|annual|earnings", text, re.I):
        return "EARNINGS_REVIEW"
    if ext in {"xlsx", "xls", "csv"}:
        return "FINANCIAL_SHEET"
    if ext in {"doc", "docx", "md", "markdown"}:
        return "MEMO"
    if ext == "pdf":
        return "COMPANY_UPDATE"
    return "OTHER"


def parse_filename(filename: Any, market_hint: str = "", company_dict: Mapping[str, Any] | None = None) -> dict[str, Any]:
    text = normalize_text(filename)
    ticker = extract_ticker(text)
    etf_ticker = extract_active_etf_ticker(text)
    if not ticker and etf_ticker:
        ticker = etf_ticker
    market = infer_market(text, ticker, market_hint)
    forms = expand_ticker(ticker, market)
    broker = canonicalize_broker(text)
    rating = canonicalize_rating(text)
    report_date = extract_report_date(text)
    company_name = resolve_company_name(ticker, text, company_dict)
    target_price = extract_target_price(text)
    tokens = tokenize_filename(text)
    parts = classify_filename_tokens(text, company_dict)
    result = {
        "fileName": Path(text).name,
        "tokens": tokens,
        "parts": parts,
        "ticker": ticker,
        "market": market,
        "yfinanceTicker": forms["yfinance"],
        "bloombergTicker": forms["bloomberg"],
        "tickerKind": "active_etf" if etf_ticker else "tw_equity" if ticker else "",
        "companyName": company_name,
        "reportDate": report_date,
        "brokerAbbr": broker["key"],
        "broker": broker["name"],
        "rating": rating,
        "targetPrice": target_price,
        "reportType": detect_report_type(text),
    }
    result.update(
        {
            "TICKER": ticker,
            "YFINANCE_TICKER": forms["yfinance"],
            "BLOOMBERG_TICKER": forms["bloomberg"],
            "NAME": company_name,
            "RATING": rating,
            "TARGET_PRICE": target_price,
            "BROKER": broker["name"],
            "BROKER_KEY": broker["key"],
            "REPORT_DATE": report_date,
            "MARKET": market,
            "FILENAME": Path(text).name,
            "FILENAME_TOKENS": tokens,
            "FILENAME_PARTS": parts,
        }
    )
    return result


# =============================================================================
# def 04 FIRST-PAGE / FINANCIAL LOGIC
# =============================================================================

def extract_target_price(value: Any) -> float | None:
    text = normalize_text(value)
    patterns = (
        r"(?:目標價(?:格)?|target\s*price|\bTP)\s*[:：=]?[\s]*(?:NT\$?|TWD|新台幣)?\s*([0-9][0-9,]*(?:\.[0-9]+)?)",
        r"(?:NT\$?|TWD)\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*(?:目標價|target)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            number = float(match.group(1).replace(",", ""))
            if MIN_TARGET_PRICE <= number < MAX_TARGET_PRICE:
                return number
    return None


def parse_first_page(text: Any, market_hint: str = "", company_dict: Mapping[str, Any] | None = None) -> dict[str, Any]:
    normalized = normalize_text(text)
    parsed = parse_filename(normalized, market_hint=market_hint, company_dict=company_dict)
    target_price = extract_target_price(normalized)
    company_name = resolve_company_name(parsed.get("ticker"), normalized, company_dict)
    parsed.update(
        {
            "source": "first_page",
            "targetPrice": target_price,
            "companyName": company_name,
            "textLength": len(normalized),
            "language": "zh-Hant" if re.search(r"[\u4e00-\u9fff]", normalized) else "en",
            "NAME": company_name,
            "TARGET_PRICE": target_price,
        }
    )
    return parsed


def canonical_financial_name(value: Any) -> str:
    text = normalize_text(value).casefold()
    compact = re.sub(r"[\s_\-()（）]+", "", text)
    candidates: list[tuple[int, str]] = []
    for canonical, aliases in FINANCIAL_SYNONYMS.items():
        for alias in aliases:
            normalized_alias = normalize_text(alias).casefold()
            compact_alias = re.sub(r"[\s_\-()（）]+", "", normalized_alias)
            if normalized_alias in text or compact_alias in compact:
                candidates.append((len(compact_alias), canonical))
    return max(candidates, default=(0, compact))[1]


def infer_financial_category(data_name: Any) -> tuple[str, str]:
    name = canonical_financial_name(data_name)
    if name in {"revenue", "gross_profit", "operating_income", "net_income"}:
        return "IS", "損益表"
    if name in {"total_assets", "equity"}:
        return "BS", "資產負債表"
    if name in {"ocf", "fcf"}:
        return "CF", "現金流量表"
    if name in {"eps", "target_price"}:
        return "RATIO", "每股／估值"
    return "OTHER", "其他"


def parse_financial_value(value: Any, unit: Any = "") -> tuple[float | None, str]:
    if value is None:
        return None, normalize_text(unit)
    raw = normalize_text(value)
    if is_missing(raw):
        return None, normalize_text(unit)
    percent = "%" in raw or normalize_text(unit).lower() in {"%", "percent"}
    number_match = re.search(r"[-+]?\d[\d,，]*(?:\.\d+)?", raw)
    if not number_match:
        return None, normalize_text(unit)
    # Parenthesized accounting negatives may be followed by a unit, e.g.
    # ``(1,234.50) 百萬元``.  Inspect the delimiters around the matched number
    # instead of requiring the complete input string to end in ``)``.
    prefix = raw[: number_match.start()]
    suffix = raw[number_match.end() :]
    negative = bool(re.search(r"\(\s*$", prefix) and re.match(r"^\s*\)", suffix))
    number = float(number_match.group(0).replace(",", "").replace("，", ""))
    if negative:
        number = -abs(number)
    detected_unit = normalize_text(unit)
    if not detected_unit:
        for candidate in ("十億元", "百萬元", "億元", "千元", "billion", "million", "bn", "mn", "%", "元"):
            if candidate.casefold() in raw.casefold():
                detected_unit = candidate
                break
    if percent:
        return number, "%"
    unit_key = detected_unit.casefold()
    multiplier = UNIT_MULTIPLIERS_TO_MILLION.get(unit_key, 1.0)
    scaled_to_million = unit_key in UNIT_MULTIPLIERS_TO_MILLION and unit_key not in {"", "%", "percent", "元", "twd", "ntd"}
    output_unit = "million" if scaled_to_million else detected_unit
    return round(number * multiplier, 10), output_unit


def grade_financial_row(row: Mapping[str, Any]) -> dict[str, Any]:
    defects: list[str] = []
    period = normalize_period(row.get("period"))
    value = row.get("value")
    if not period:
        defects.append("PERIOD_UNPARSEABLE")
    if value is None or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        defects.append("VALUE_NO_NUMBER")
    if normalize_text(row.get("unit")) == "":
        defects.append("UNIT_EMPTY")
    if value is not None and normalize_text(row.get("item")) == normalize_text(value):
        defects.append("VALUE_ECHOES_METRIC")
    grade = "V" if not defects else "M" if defects == ["UNIT_EMPTY"] else "P"
    status = "ok" if grade == "V" else "warn" if grade == "M" else "bad"
    return {"grade": grade, "defects": defects, "status": status, "period": period}


def normalize_financial_row(
    raw: Mapping[str, Any],
    *,
    file_id: str = "",
    file_name: str = "",
    default_source: str = "financial_page",
) -> dict[str, Any]:
    item = raw.get("item", raw.get("metric", raw.get("name", raw.get("dataName", ""))))
    data_name = canonical_financial_name(raw.get("dataName", item))
    category, statement = infer_financial_category(data_name)
    value, normalized_unit = parse_financial_value(raw.get("value"), raw.get("unit", ""))
    base = {
        "fileId": normalize_text(raw.get("fileId", file_id)),
        "fileName": normalize_text(raw.get("fileName", file_name)),
        "category": normalize_text(raw.get("category", category)) or category,
        "statement": normalize_text(raw.get("statement", statement)) or statement,
        "item": normalize_text(item),
        "dataName": data_name,
        "period": normalize_text(raw.get("period", "")),
        "value": value,
        "unit": normalized_unit,
        "confidence": clamp_confidence(raw.get("confidence", DEFAULT_CONFIDENCE)),
        "source": normalize_text(raw.get("source", default_source)).lower() or default_source,
        "page": int(raw.get("page", 0) or 0),
        "tableId": normalize_text(raw.get("tableId", "")),
        "cellId": normalize_text(raw.get("cellId", "")),
        "engine": normalize_text(raw.get("engine", "")),
        "rawValue": normalize_text(raw.get("rawValue", raw.get("value", ""))),
    }
    grade = grade_financial_row(base)
    base["period"] = grade["period"]
    base["grade"] = grade["grade"]
    base["defects"] = grade["defects"]
    base["status"] = grade["status"]
    return base


def deduplicate_financial_rows(rows: Iterable[Mapping[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    selected: dict[tuple[str, str, str], dict[str, Any]] = {}
    duplicate_count = 0
    for raw in rows:
        row = dict(raw)
        key = (normalize_text(row.get("fileId")), normalize_text(row.get("dataName")), normalize_text(row.get("period")))
        previous = selected.get(key)
        if previous is None:
            selected[key] = row
            continue
        duplicate_count += 1
        current_rank = (clamp_confidence(row.get("confidence")), -source_priority(row.get("source")), stable_digest(row))
        previous_rank = (clamp_confidence(previous.get("confidence")), -source_priority(previous.get("source")), stable_digest(previous))
        if current_rank > previous_rank:
            selected[key] = row
    ordered = sorted(selected.values(), key=lambda row: (row.get("fileId", ""), row.get("dataName", ""), row.get("period", "")))
    return ordered, duplicate_count


def validate_financial_formulas(rows: Sequence[Mapping[str, Any]], tolerance: float = 0.02) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, float]] = {}
    for row in rows:
        value = row.get("value")
        if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            continue
        grouped.setdefault(normalize_text(row.get("period")), {})[normalize_text(row.get("dataName"))] = float(value)
    checks: list[dict[str, Any]] = []
    for period, values in sorted(grouped.items()):
        if {"revenue", "gross_profit"}.issubset(values):
            ok = abs(values["gross_profit"]) <= abs(values["revenue"]) * (1.0 + tolerance)
            checks.append({"period": period, "formula": "abs(gross_profit)<=abs(revenue)", "status": "PASS" if ok else "FAIL"})
        if {"revenue", "operating_income"}.issubset(values):
            ok = abs(values["operating_income"]) <= abs(values["revenue"]) * (1.0 + tolerance)
            checks.append({"period": period, "formula": "abs(operating_income)<=abs(revenue)", "status": "PASS" if ok else "FAIL"})
    return checks


# =============================================================================
# def 05 EVIDENCE RECONCILIATION / PIPELINE
# =============================================================================

def evidence_value(source: Mapping[str, Any], key: str) -> Any:
    value = source.get(key)
    return None if is_missing(value) else value


def reconcile_field(key: str, sources: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    observations: list[dict[str, Any]] = []
    for source in sources:
        value = evidence_value(source, key)
        if value is None:
            continue
        observations.append({"source": normalize_text(source.get("source", "unknown")).lower(), "value": value})
    if not observations:
        return {"field": key, "value": None, "status": "MISSING", "confidence": 0.0, "observations": []}
    buckets: dict[str, list[dict[str, Any]]] = {}
    for observation in observations:
        bucket_key = stable_json(observation["value"])
        buckets.setdefault(bucket_key, []).append(observation)
    winner = sorted(
        buckets.values(),
        key=lambda group: (len(group), -min(source_priority(item["source"]) for item in group), stable_json(group[0]["value"])),
        reverse=True,
    )[0]
    conflict = len(buckets) > 1
    confidence = DEFAULT_CONFIDENCE + (MATCH_CONFIDENCE_BONUS if len(winner) > 1 else 0.0)
    if conflict:
        confidence -= UNRESOLVED_CONFIDENCE_PENALTY
    return {
        "field": key,
        "value": winner[0]["value"],
        "status": "CONFLICT" if conflict else "MATCH" if len(winner) > 1 else "SINGLE_SOURCE",
        "confidence": clamp_confidence(confidence),
        "observations": observations,
    }


def reconcile_evidence(
    filename: Mapping[str, Any],
    first_page: Mapping[str, Any] | None = None,
    financial_page: Mapping[str, Any] | None = None,
    official: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    sources: list[dict[str, Any]] = []
    for label, source in (
        ("filename", filename),
        ("first_page", first_page),
        ("financial_page", financial_page),
        ("official", official),
    ):
        if source:
            item = dict(source)
            item.setdefault("source", label)
            sources.append(item)
    fields = {
        key: reconcile_field(key, sources)
        for key in ("ticker", "companyName", "reportDate", "brokerAbbr", "rating", "targetPrice")
    }
    blocking = [key for key in ("ticker",) if fields[key]["status"] == "CONFLICT"]
    warnings = [key for key, row in fields.items() if row["status"] in {"CONFLICT", "MISSING"} and key not in blocking]
    status = "RED" if blocking else "YELLOW" if warnings else "GREEN"
    return {
        "status": status,
        "fields": fields,
        "blocking": blocking,
        "warnings": warnings,
        "sourceCount": len(sources),
        "digest": stable_digest({"fields": fields, "blocking": blocking, "warnings": warnings}),
    }


def report_code(basic: Mapping[str, Any]) -> str:
    broker = normalize_text(basic.get("brokerAbbr")) or "UNK"
    ticker = normalize_text(basic.get("ticker")) or "0000"
    report_date = normalize_text(basic.get("reportDate")).replace("-", "") or "00000000"
    return f"{broker}-{ticker}-{report_date}"


def build_basic_info(
    *,
    file_id: str,
    filename: str,
    file_size: int = 1,
    first_page_text: str = "",
    market_hint: str = "",
    official: Mapping[str, Any] | None = None,
    company_dict: Mapping[str, Any] | None = None,
    pages: int = 1,
) -> tuple[dict[str, Any], dict[str, Any]]:
    filename_evidence = parse_filename(filename, market_hint=market_hint, company_dict=company_dict)
    filename_evidence["source"] = "filename"
    first_page_evidence = parse_first_page(first_page_text, market_hint=market_hint, company_dict=company_dict) if first_page_text else None
    validation = reconcile_evidence(filename_evidence, first_page_evidence, official=official)
    values = {key: row["value"] for key, row in validation["fields"].items()}
    ticker = normalize_text(values.get("ticker") or filename_evidence.get("ticker"))
    market = infer_market(filename + " " + first_page_text, ticker, market_hint)
    forms = expand_ticker(ticker, market)
    broker_key = normalize_text(values.get("brokerAbbr") or filename_evidence.get("brokerAbbr"))
    report_date = normalize_text(values.get("reportDate") or filename_evidence.get("reportDate"))
    company = normalize_text(values.get("companyName") or (official or {}).get("companyName", ""))
    if not company:
        company = resolve_company_name(ticker, filename + " " + first_page_text, company_dict)
    rating = normalize_text(values.get("rating") or filename_evidence.get("rating"))
    target_price = values.get("targetPrice")
    if target_price is None:
        target_price = filename_evidence.get("targetPrice")
    risk = "RED" if file_size <= 0 else validation["status"]
    basic = {
        "fileId": normalize_text(file_id) or stable_digest(filename)[:16],
        "fileName": Path(normalize_text(filename)).name,
        "reportType": detect_report_type(filename + " " + first_page_text),
        "ticker": ticker or "—",
        "market": market,
        "yfinanceTicker": forms["yfinance"] or "—",
        "bloombergTicker": forms["bloomberg"] or "—",
        "tickerKind": filename_evidence.get("tickerKind") or "—",
        "companyName": company or "—",
        "broker": BROKER_NAMES.get(broker_key, "") or "—",
        "brokerAbbr": broker_key or "—",
        "reportDate": report_date or "—",
        "reportCode": "",
        "language": "zh-Hant" if re.search(r"[\u4e00-\u9fff]", filename + first_page_text) else "en",
        "period": report_date[:4] if report_date else "—",
        "pages": max(1, int(pages or 1)),
        "issuer": company or BROKER_NAMES.get(broker_key, "") or "—",
        "rating": rating or "—",
        "ratingCat": rating or "—",
        "targetPrice": target_price,
        "fileNameTokens": filename_evidence.get("tokens", []),
        "fileNameParts": filename_evidence.get("parts", []),
        "identityDigest": "",
        "TICKER": ticker or "—",
        "YFINANCE_TICKER": forms["yfinance"] or "—",
        "BLOOMBERG_TICKER": forms["bloomberg"] or "—",
        "NAME": company or "—",
        "RATING": rating or "—",
        "TARGET_PRICE": target_price,
        "BROKER": BROKER_NAMES.get(broker_key, "") or "—",
        "BROKER_KEY": broker_key or "—",
        "REPORT_DATE": report_date or "—",
        "MARKET": market,
        "FILENAME": Path(normalize_text(filename)).name,
        "FILENAME_TOKENS": filename_evidence.get("tokens", []),
        "FILENAME_PARTS": filename_evidence.get("parts", []),
        "validationStatus": "PHASE2_OK" if risk == "GREEN" else "REVIEW_REQUIRED" if risk == "YELLOW" else "FAIL_CLOSED",
        "validationRisk": risk,
        "status": "ok" if risk == "GREEN" else "warn" if risk == "YELLOW" else "bad",
    }
    basic["reportCode"] = report_code(basic)
    basic["identityDigest"] = stable_digest({key: basic[key] for key in REGISTRY["schemas"]["identity"] if key in basic})
    return basic, validation


def process_report(payload: Mapping[str, Any]) -> dict[str, Any]:
    filename = normalize_text(payload.get("filename", payload.get("fileName", "")))
    if not filename:
        raise ValueError("filename is required")
    file_id = normalize_text(payload.get("file_id", payload.get("fileId", "")))
    first_page_text = normalize_text(payload.get("first_page_text", payload.get("firstPageText", "")))
    market_hint = normalize_text(payload.get("market", payload.get("market_hint", "")))
    official = payload.get("official") if isinstance(payload.get("official"), Mapping) else None
    supplied_company_dict = payload.get("company_dict", payload.get("companyDict"))
    company_dict = supplied_company_dict if isinstance(supplied_company_dict, Mapping) else None
    basic, validation = build_basic_info(
        file_id=file_id,
        filename=filename,
        file_size=int(payload.get("file_size", payload.get("fileSize", 1)) or 0),
        first_page_text=first_page_text,
        market_hint=market_hint,
        official=official,
        company_dict=company_dict,
        pages=int(payload.get("pages", 1) or 1),
    )
    raw_rows = payload.get("financial_rows", payload.get("financialRows", []))
    if raw_rows is None:
        raw_rows = []
    if not isinstance(raw_rows, Sequence) or isinstance(raw_rows, (str, bytes, bytearray)):
        raise TypeError("financial_rows must be a list of row objects")
    normalized_rows = [
        normalize_financial_row(row, file_id=basic["fileId"], file_name=basic["fileName"])
        for row in raw_rows
        if isinstance(row, Mapping)
    ]
    financial_rows, duplicates = deduplicate_financial_rows(normalized_rows)
    formulas = validate_financial_formulas(financial_rows)
    formula_failures = sum(1 for row in formulas if row["status"] == "FAIL")
    p_grade = sum(1 for row in financial_rows if row["grade"] == "P")
    if formula_failures or p_grade:
        validation = dict(validation)
        validation["status"] = "RED" if formula_failures else "YELLOW"
        validation["financialFormulaFailures"] = formula_failures
        validation["financialProvisionalRows"] = p_grade
        basic["validationRisk"] = validation["status"]
        basic["validationStatus"] = "FAIL_CLOSED" if validation["status"] == "RED" else "REVIEW_REQUIRED"
        basic["status"] = "bad" if validation["status"] == "RED" else "warn"
    result = {
        "schema": SCHEMA_VERSION,
        "module": MODULE_META,
        "basic_info": basic,
        "financial_data": financial_rows,
        "validation": validation,
        "formula_checks": formulas,
        "duplicates_removed": duplicates,
    }
    result["digest"] = stable_digest(result)
    return result


# =============================================================================
# def 06 PDF / FIRST PAGE / ANNUAL FINANCIAL TABLE RESTORATION
# =============================================================================

def available_pdf_engines() -> dict[str, bool]:
    return {
        "pymupdf": importlib.util.find_spec("fitz") is not None,
        "pdfplumber": importlib.util.find_spec("pdfplumber") is not None,
        "pypdf": importlib.util.find_spec("pypdf") is not None,
    }


def extract_pdf_document(pdf_path: str | os.PathLike[str], max_pages: int = DEFAULT_PDF_MAX_PAGES) -> dict[str, Any]:
    path = Path(pdf_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"PDF_NOT_FOUND：{path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"NOT_A_PDF：{path}")
    engines = available_pdf_engines()
    errors: list[str] = []
    limit = max(0, int(max_pages or 0))

    if engines["pymupdf"]:
        try:
            import fitz  # type: ignore

            pages: list[dict[str, Any]] = []
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                with fitz.open(path) as document:
                    count = len(document) if limit == 0 else min(len(document), limit)
                    for index in range(count):
                        page = document[index]
                        text = normalize_text(page.get_text("text", sort=True))
                        blocks = []
                        for block in page.get_text("blocks", sort=True):
                            if len(block) >= 5 and normalize_text(block[4]):
                                blocks.append(
                                    {
                                        "bbox": [round(float(value), 3) for value in block[:4]],
                                        "text": normalize_text(block[4]),
                                    }
                                )
                        pages.append(
                            {
                                "page": index + 1,
                                "text": text,
                                "width": round(float(page.rect.width), 3),
                                "height": round(float(page.rect.height), 3),
                                "blocks": blocks,
                            }
                        )
                    total_pages = len(document)
            return {"path": str(path), "engine": "pymupdf", "pageCount": total_pages, "pages": pages, "errors": errors}
        except Exception as error:
            errors.append(f"pymupdf:{type(error).__name__}:{error}")

    if engines["pdfplumber"]:
        try:
            import pdfplumber  # type: ignore

            pages = []
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                with pdfplumber.open(path) as document:
                    selected = document.pages if limit == 0 else document.pages[:limit]
                    for index, page in enumerate(selected, start=1):
                        pages.append(
                            {
                                "page": index,
                                "text": normalize_text(page.extract_text(x_tolerance=2, y_tolerance=3) or ""),
                                "width": round(float(page.width), 3),
                                "height": round(float(page.height), 3),
                                "blocks": [],
                            }
                        )
                    total_pages = len(document.pages)
            return {"path": str(path), "engine": "pdfplumber", "pageCount": total_pages, "pages": pages, "errors": errors}
        except Exception as error:
            errors.append(f"pdfplumber:{type(error).__name__}:{error}")

    if engines["pypdf"]:
        try:
            from pypdf import PdfReader  # type: ignore

            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                reader = PdfReader(str(path))
                count = len(reader.pages) if limit == 0 else min(len(reader.pages), limit)
                pages = [
                    {"page": index + 1, "text": normalize_text(reader.pages[index].extract_text() or ""), "width": 0.0, "height": 0.0, "blocks": []}
                    for index in range(count)
                ]
            return {"path": str(path), "engine": "pypdf", "pageCount": len(reader.pages), "pages": pages, "errors": errors}
        except Exception as error:
            errors.append(f"pypdf:{type(error).__name__}:{error}")

    raise RuntimeError("PDF_EXTRACTION_ENGINE_FAILED：" + " | ".join(errors or ["no supported PDF engine installed"]))


def score_financial_page(text: Any) -> dict[str, Any]:
    normalized = normalize_text(text).casefold()
    hits = [keyword for keyword in ANNUAL_FINANCIAL_PAGE_KEYWORDS if keyword.casefold() in normalized]
    periods = sorted(set(re.findall(r"(?:20\d{2}|\d{2})[QH][1-4]?[EFA]?|[1-4]Q(?:20\d{2}|\d{2})[EFA]?|20\d{2}[EFA]?", normalized.upper())))
    numeric_lines = sum(1 for line in normalized.splitlines() if len(re.findall(r"[-+()]?\d[\d,.]*%?", line)) >= 2)
    score = len(hits) + min(3, len(periods)) + min(3, numeric_lines // 3)
    return {"score": score, "keywords": hits, "periods": periods, "numericLines": numeric_lines}


def classify_pdf_pages(document: Mapping[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in document.get("pages", []):
        if not isinstance(item, Mapping):
            continue
        page_number = int(item.get("page", len(result) + 1))
        score = score_financial_page(item.get("text", ""))
        page_type = "FIRST_PAGE" if page_number == 1 else "FINANCIAL_PAGE" if score["score"] >= DEFAULT_FINANCIAL_PAGE_SCORE else "BODY"
        result.append({"page": page_number, "type": page_type, **score})
    return result


def _clean_table_matrix(rows: Any) -> list[list[str]]:
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes, bytearray)):
        return []
    cleaned: list[list[str]] = []
    width = 0
    for row in rows:
        if not isinstance(row, Sequence) or isinstance(row, (str, bytes, bytearray)):
            continue
        values = [normalize_text(cell) for cell in row]
        if any(values):
            cleaned.append(values)
            width = max(width, len(values))
    return [row + [""] * (width - len(row)) for row in cleaned]


def _table_quality(rows: Sequence[Sequence[str]]) -> dict[str, Any]:
    row_count = len(rows)
    column_count = max((len(row) for row in rows), default=0)
    cells = [cell for row in rows for cell in row if normalize_text(cell)]
    numeric = sum(1 for cell in cells if re.search(r"[-+()]?\d[\d,.]*%?", normalize_text(cell)))
    numeric_ratio = round(numeric / max(1, len(cells)), 6)
    return {
        "rows": row_count,
        "columns": column_count,
        "cells": len(cells),
        "numericRatio": numeric_ratio,
        "valid": row_count >= 2 and column_count >= 2 and len(cells) >= 4,
    }


def _text_table_candidates(text: Any) -> list[list[list[str]]]:
    lines = [normalize_text(line) for line in normalize_text(text).splitlines() if normalize_text(line)]
    tables: list[list[list[str]]] = []
    current: list[list[str]] = []
    for line in lines:
        cells = [normalize_text(cell) for cell in re.split(r"\t+|\s{2,}", line) if normalize_text(cell)]
        if len(cells) >= 2 and (any(normalize_period(cell) for cell in cells) or len(re.findall(r"[-+()]?\d[\d,.]*%?", line)) >= 1):
            current.append(cells)
        elif len(current) >= 2:
            tables.append(_clean_table_matrix(current))
            current = []
        else:
            current = []
    if len(current) >= 2:
        tables.append(_clean_table_matrix(current))
    return tables


def extract_pdf_tables(
    pdf_path: str | os.PathLike[str],
    pages: Sequence[int] | None = None,
    document: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    path = Path(pdf_path).expanduser().resolve()
    selected_pages = sorted({int(page) for page in pages or [] if int(page) > 0})
    tables: list[dict[str, Any]] = []
    seen: set[str] = set()

    if importlib.util.find_spec("fitz") is not None:
        try:
            import fitz  # type: ignore

            with fitz.open(path) as pdf:
                page_numbers = selected_pages or list(range(1, len(pdf) + 1))
                for page_number in page_numbers:
                    if page_number > len(pdf):
                        continue
                    page = pdf[page_number - 1]
                    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                        finder = page.find_tables()
                    for table_index, table in enumerate(finder.tables, start=1):
                        matrix = _clean_table_matrix(table.extract())
                        digest = stable_digest(matrix)
                        if matrix and digest not in seen:
                            seen.add(digest)
                            tables.append({"page": page_number, "tableIndex": table_index, "engine": "pymupdf", "bbox": list(table.bbox), "rows": matrix, "quality": _table_quality(matrix)})
        except Exception:
            pass

    if importlib.util.find_spec("pdfplumber") is not None:
        try:
            import pdfplumber  # type: ignore

            with pdfplumber.open(path) as pdf:
                page_numbers = selected_pages or list(range(1, len(pdf.pages) + 1))
                for page_number in page_numbers:
                    if page_number > len(pdf.pages):
                        continue
                    for table_index, raw in enumerate(pdf.pages[page_number - 1].extract_tables(), start=1):
                        matrix = _clean_table_matrix(raw)
                        digest = stable_digest(matrix)
                        if matrix and digest not in seen:
                            seen.add(digest)
                            tables.append({"page": page_number, "tableIndex": table_index, "engine": "pdfplumber", "bbox": [], "rows": matrix, "quality": _table_quality(matrix)})
        except Exception:
            pass

    source_document = document or extract_pdf_document(path)
    page_filter = set(selected_pages)
    for page in source_document.get("pages", []):
        if not isinstance(page, Mapping):
            continue
        page_number = int(page.get("page", 0))
        if page_filter and page_number not in page_filter:
            continue
        for table_index, matrix in enumerate(_text_table_candidates(page.get("text", "")), start=1):
            digest = stable_digest(matrix)
            if matrix and digest not in seen:
                seen.add(digest)
                tables.append({"page": page_number, "tableIndex": table_index, "engine": "text_fallback", "bbox": [], "rows": matrix, "quality": _table_quality(matrix)})
    return tables


def restore_financial_table(
    table: Mapping[str, Any],
    *,
    file_id: str = "",
    file_name: str = "",
) -> dict[str, Any]:
    matrix = _clean_table_matrix(table.get("rows", []))
    table_id = f"{normalize_text(file_id) or 'DOC'}_P{int(table.get('page', 0)):03d}_T{int(table.get('tableIndex', 0)):02d}"
    best_header_index = -1
    best_periods: list[tuple[int, str]] = []
    for row_index, row in enumerate(matrix[:5]):
        periods = [(column, normalize_period(cell)) for column, cell in enumerate(row) if normalize_period(cell)]
        if len(periods) > len(best_periods):
            best_header_index = row_index
            best_periods = periods
    if best_header_index < 0:
        return {"tableId": table_id, "rows": [], "audit": {"decision": "BLOCK", "reason": "PERIOD_HEADER_NOT_FOUND", **_table_quality(matrix)}}

    header_context = " ".join(cell for row in matrix[: best_header_index + 1] for cell in row)
    unit = next((candidate for candidate in UNIT_MULTIPLIERS_TO_MILLION if candidate and candidate.casefold() in header_context.casefold()), "million")
    restored: list[dict[str, Any]] = []
    last_item = ""
    for source_row_index, row in enumerate(matrix[best_header_index + 1 :], start=best_header_index + 2):
        item = normalize_text(row[0] if row else "")
        if item:
            last_item = item
        elif last_item:
            item = last_item
        if not item:
            continue
        for column_index, period in best_periods:
            raw_value = row[column_index] if column_index < len(row) else ""
            if is_missing(raw_value):
                continue
            data_name = canonical_financial_name(item)
            row_unit = "%" if "%" in raw_value else "TWD/share" if data_name == "eps" else unit
            normalized = normalize_financial_row(
                {
                    "item": item,
                    "dataName": data_name,
                    "period": period,
                    "value": raw_value,
                    "unit": row_unit,
                    "confidence": 0.90 if table.get("engine") != "text_fallback" else 0.72,
                    "source": "financial_page",
                },
                file_id=file_id,
                file_name=file_name,
            )
            if normalized["value"] is None:
                continue
            normalized.update(
                {
                    "page": int(table.get("page", 0)),
                    "tableId": table_id,
                    "cellId": f"{table_id}_R{source_row_index:03d}_C{column_index + 1:02d}",
                    "engine": normalize_text(table.get("engine", "unknown")),
                    "rawValue": raw_value,
                }
            )
            restored.append(normalized)
    decision = "PASS" if restored else "BLOCK"
    return {
        "tableId": table_id,
        "rows": restored,
        "audit": {
            "decision": decision,
            "engine": normalize_text(table.get("engine", "unknown")),
            "headerRow": best_header_index + 1,
            "periods": [period for _, period in best_periods],
            "restoredRows": len(restored),
            **_table_quality(matrix),
        },
    }


def extract_annual_financial_rows(
    pdf_path: str | os.PathLike[str],
    *,
    document: Mapping[str, Any] | None = None,
    file_id: str = "",
    file_name: str = "",
) -> dict[str, Any]:
    source_document = dict(document or extract_pdf_document(pdf_path))
    classifications = classify_pdf_pages(source_document)
    selected_pages = [row["page"] for row in classifications if row["type"] == "FINANCIAL_PAGE"]
    if not selected_pages:
        selected_pages = [row["page"] for row in classifications if row["score"] > 0]
    tables = extract_pdf_tables(pdf_path, selected_pages, source_document)
    restored_tables = [restore_financial_table(table, file_id=file_id, file_name=file_name or Path(pdf_path).name) for table in tables]
    rows = [row for table in restored_tables for row in table["rows"]]
    deduped, duplicates = deduplicate_financial_rows(rows)
    return {
        "rows": deduped,
        "tables": restored_tables,
        "classifications": classifications,
        "selectedPages": selected_pages,
        "duplicatesRemoved": duplicates,
        "status": "PASS" if deduped else "REVIEW_REQUIRED",
    }


# =============================================================================
# def 07 VDF LOCAL BRIDGE / EXTERNAL EVIDENCE
# =============================================================================

def _safe_table_identifier(value: Any) -> str:
    name = normalize_text(value)
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError(f"UNSAFE_TABLE_IDENTIFIER：{name}")
    return name


def _records_from_json(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [dict(item) for item in payload if isinstance(item, Mapping)]
    if isinstance(payload, Mapping):
        for key in ("records", "rows", "data", "items", "result"):
            value = payload.get(key)
            if isinstance(value, list):
                return [dict(item) for item in value if isinstance(item, Mapping)]
        return [dict(payload)]
    return []


def load_structured_records(
    source: str | os.PathLike[str],
    *,
    table: str = "",
    max_rows: int = DEFAULT_VDF_MAX_ROWS,
) -> list[dict[str, Any]]:
    path = Path(source).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"VDF_SOURCE_NOT_FOUND：{path}")
    suffix = path.suffix.lower()
    limit = max(1, int(max_rows))
    if suffix == ".json":
        return _records_from_json(json.loads(path.read_text(encoding="utf-8-sig")))[:limit]
    if suffix in {".jsonl", ".ndjson"}:
        records = []
        with path.open("r", encoding="utf-8-sig") as handle:
            for line in handle:
                if len(records) >= limit:
                    break
                if normalize_text(line):
                    item = json.loads(line)
                    if isinstance(item, Mapping):
                        records.append(dict(item))
        return records
    if suffix in {".csv", ".tsv", ".txt"}:
        delimiter = "\t" if suffix == ".tsv" else ","
        records = []
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle, delimiter=delimiter):
                records.append(dict(row))
                if len(records) >= limit:
                    break
        return records
    if suffix == ".parquet":
        if importlib.util.find_spec("pyarrow.parquet") is not None:
            import pyarrow.parquet as pq  # type: ignore

            return pq.read_table(path).slice(0, limit).to_pylist()
        if importlib.util.find_spec("pandas") is not None:
            import pandas as pd  # type: ignore

            return pd.read_parquet(path).head(limit).to_dict(orient="records")
        raise RuntimeError("PARQUET_READER_NOT_AVAILABLE：install pyarrow in the selected VDF environment")
    if suffix in {".sqlite", ".sqlite3", ".db"}:
        connection = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        try:
            selected_table = table
            if not selected_table:
                row = connection.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name LIMIT 1").fetchone()
                selected_table = str(row[0]) if row else ""
            if not selected_table:
                return []
            selected_table = _safe_table_identifier(selected_table)
            return [dict(row) for row in connection.execute(f'SELECT * FROM "{selected_table}" LIMIT ?', (limit,)).fetchall()]
        finally:
            connection.close()
    if suffix == ".duckdb":
        if importlib.util.find_spec("duckdb") is None:
            raise RuntimeError("DUCKDB_READER_NOT_AVAILABLE：install duckdb in the selected VDF environment")
        import duckdb  # type: ignore

        connection = duckdb.connect(str(path), read_only=True)
        try:
            selected_table = table
            if not selected_table:
                tables = connection.execute("SHOW TABLES").fetchall()
                selected_table = str(tables[0][0]) if tables else ""
            if not selected_table:
                return []
            selected_table = _safe_table_identifier(selected_table)
            cursor = connection.execute(f'SELECT * FROM "{selected_table}" LIMIT ?', [limit])
            columns = [item[0] for item in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        finally:
            connection.close()
    raise ValueError(f"UNSUPPORTED_VDF_SOURCE：{suffix}")


def discover_vdf_sources(root: str | os.PathLike[str], max_files: int = DEFAULT_VDF_MAX_FILES) -> list[Path]:
    directory = Path(root).expanduser().resolve()
    if not directory.is_dir():
        return [directory] if directory.is_file() else []
    supported = {".json", ".jsonl", ".ndjson", ".csv", ".tsv", ".parquet", ".sqlite", ".sqlite3", ".db", ".duckdb"}
    candidates = [
        path
        for path in directory.rglob("*")
        if path.is_file() and path.suffix.lower() in supported and not any(part.startswith(".") for part in path.parts)
    ]
    candidates.sort(key=lambda path: (path.stat().st_mtime_ns, str(path)), reverse=True)
    return candidates[: max(1, int(max_files))]


def _row_lookup(row: Mapping[str, Any], names: Sequence[str]) -> Any:
    normalized = {normalize_text(key).casefold().replace("_", ""): value for key, value in row.items()}
    for name in names:
        key = normalize_text(name).casefold().replace("_", "")
        if key in normalized and not is_missing(normalized[key]):
            return normalized[key]
    return None


def _normalized_record_ticker(row: Mapping[str, Any]) -> str:
    value = _row_lookup(row, ("ticker", "symbol", "code", "stock_id", "stockid", "yfinanceTicker", "證券代號"))
    text = normalize_text(value).upper()
    active = extract_active_etf_ticker(text)
    return extract_ticker(text) or active


def vdf_records_to_financial_rows(
    records: Sequence[Mapping[str, Any]],
    *,
    file_id: str = "",
    file_name: str = "",
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    metric_columns = {
        "revenue": ("revenue", "sales", "營收", "營業收入"),
        "gross_profit": ("gross_profit", "grossprofit", "毛利", "營業毛利"),
        "operating_income": ("operating_income", "operatingincome", "營業利益"),
        "net_income": ("net_income", "netincome", "稅後淨利", "本期淨利"),
        "eps": ("eps", "diluted_eps", "dilutedeps", "每股盈餘"),
        "total_assets": ("total_assets", "totalassets", "總資產"),
        "equity": ("equity", "total_equity", "股東權益"),
        "ocf": ("ocf", "operating_cash_flow", "營業活動現金流"),
        "fcf": ("fcf", "free_cash_flow", "自由現金流"),
    }
    for record in records:
        period = _row_lookup(record, ("period", "year", "quarter", "fiscal_period", "date", "日期"))
        normalized_period = normalize_period(period) or extract_report_date(period)
        if not normalized_period:
            continue
        unit = _row_lookup(record, ("unit", "單位")) or "million"
        for metric, names in metric_columns.items():
            value = _row_lookup(record, names)
            if value is None:
                continue
            metric_unit = "TWD/share" if metric == "eps" else unit
            row = normalize_financial_row(
                {"item": metric, "dataName": metric, "period": normalized_period, "value": value, "unit": metric_unit, "confidence": 0.98, "source": "vdf"},
                file_id=file_id,
                file_name=file_name,
                default_source="vdf",
            )
            if row["value"] is not None:
                output.append(row)
    return deduplicate_financial_rows(output)[0]


def cross_validate_financial_sources(rows: Sequence[Mapping[str, Any]], tolerance: float = 0.02) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        value = row.get("value")
        if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            continue
        key = (normalize_text(row.get("dataName")), normalize_text(row.get("period")))
        grouped.setdefault(key, []).append({"source": normalize_text(row.get("source")) or "unknown", "value": float(value)})
    checks: list[dict[str, Any]] = []
    for (data_name, period), observations in sorted(grouped.items()):
        distinct_sources = sorted({item["source"] for item in observations})
        if len(distinct_sources) < 2:
            continue
        values = [item["value"] for item in observations]
        denominator = max(abs(value) for value in values) or 1.0
        relative_difference = (max(values) - min(values)) / denominator
        checks.append(
            {
                "dataName": data_name,
                "period": period,
                "sources": distinct_sources,
                "observations": observations,
                "relativeDifference": round(relative_difference, 8),
                "tolerance": tolerance,
                "status": "PASS" if relative_difference <= tolerance else "REVIEW_REQUIRED",
            }
        )
    return checks


def load_vdf_evidence(
    source: str | os.PathLike[str] | None,
    *,
    ticker: str = "",
    report_date: str = "",
    company_name: str = "",
    max_files: int = DEFAULT_VDF_MAX_FILES,
    max_rows: int = DEFAULT_VDF_MAX_ROWS,
) -> dict[str, Any]:
    if source is None:
        return {"status": "NOT_CONFIGURED", "official": {}, "records": [], "financialRows": [], "sources": [], "errors": []}
    files = discover_vdf_sources(source, max_files=max_files)
    normalized_ticker = normalize_text(ticker).upper()
    matched: list[dict[str, Any]] = []
    source_records: list[dict[str, Any]] = []
    errors: list[str] = []
    remaining = max(1, int(max_rows))
    for path in files:
        if remaining <= 0:
            break
        try:
            records = load_structured_records(path, max_rows=remaining)
        except Exception as error:
            errors.append(f"{path}:{type(error).__name__}:{error}")
            continue
        source_records.append({"path": str(path), "rows": len(records), "sha256": sha256_file(path)})
        for row in records:
            row_ticker = _normalized_record_ticker(row)
            row_name = normalize_text(_row_lookup(row, ("name", "companyName", "stock_name", "證券名稱")))
            if normalized_ticker and row_ticker == normalized_ticker:
                matched.append(dict(row))
            elif company_name and row_name and company_name in row_name:
                matched.append(dict(row))
        remaining -= len(records)
    matched.sort(
        key=lambda row: normalize_text(_row_lookup(row, ("date", "reportDate", "period", "日期"))),
        reverse=True,
    )
    latest = matched[0] if matched else {}
    official_ticker = _normalized_record_ticker(latest) or normalized_ticker
    official_name = normalize_text(_row_lookup(latest, ("name", "companyName", "stock_name", "證券名稱"))) or company_name
    official_market = normalize_text(_row_lookup(latest, ("market", "exchange", "市場")))
    official_date = extract_report_date(_row_lookup(latest, ("date", "reportDate", "日期"))) or report_date
    official = {
        "source": "official",
        "ticker": official_ticker,
        "companyName": official_name,
        "market": official_market,
        "reportDate": official_date,
    }
    official = {key: value for key, value in official.items() if not is_missing(value)}
    return {
        "status": "MATCHED" if matched else "NO_MATCH",
        "official": official,
        "records": matched[:1000],
        "financialRows": vdf_records_to_financial_rows(matched),
        "sources": source_records,
        "errors": errors,
    }


def process_pdf_report(
    pdf_path: str | os.PathLike[str],
    *,
    vdf_source: str | os.PathLike[str] | None = None,
    company_dict_path: str | os.PathLike[str] | None = None,
    market_hint: str = "",
    max_pages: int = DEFAULT_PDF_MAX_PAGES,
    file_id: str = "",
) -> dict[str, Any]:
    path = Path(pdf_path).expanduser().resolve()
    document = extract_pdf_document(path, max_pages=max_pages)
    company_dict = load_company_dictionary(company_dict_path)
    filename_evidence = parse_filename(path.name, market_hint=market_hint, company_dict=company_dict)
    first_page_text = normalize_text(document.get("pages", [{}])[0].get("text", "")) if document.get("pages") else ""
    first_page_evidence = parse_first_page(first_page_text, market_hint=market_hint, company_dict=company_dict)
    ticker = normalize_text(first_page_evidence.get("ticker") or filename_evidence.get("ticker"))
    company_name = normalize_text(first_page_evidence.get("companyName") or filename_evidence.get("companyName"))
    report_date = normalize_text(first_page_evidence.get("reportDate") or filename_evidence.get("reportDate"))
    vdf = load_vdf_evidence(vdf_source, ticker=ticker, report_date=report_date, company_name=company_name)
    resolved_file_id = normalize_text(file_id) or stable_digest({"path": str(path), "sha256": sha256_file(path)})[:16]
    annual = extract_annual_financial_rows(path, document=document, file_id=resolved_file_id, file_name=path.name)
    vdf_financial_rows = []
    for row in vdf.get("financialRows", []):
        if isinstance(row, Mapping):
            item = dict(row)
            item["fileId"] = resolved_file_id
            item["fileName"] = path.name
            vdf_financial_rows.append(item)
    financial_rows = list(annual["rows"]) + vdf_financial_rows
    financial_cross_validation = cross_validate_financial_sources(financial_rows)
    result = process_report(
        {
            "fileId": resolved_file_id,
            "filename": path.name,
            "fileSize": path.stat().st_size,
            "firstPageText": first_page_text,
            "market": market_hint,
            "official": vdf.get("official", {}),
            "companyDict": company_dict,
            "pages": document.get("pageCount", len(document.get("pages", []))),
            "financialRows": financial_rows,
        }
    )
    result["pdf"] = {
        "path": str(path),
        "sha256": sha256_file(path),
        "engine": document.get("engine"),
        "pageCount": document.get("pageCount"),
        "pageEvidence": [
            {"page": page.get("page"), "textLength": len(normalize_text(page.get("text", ""))), "textSHA256": stable_digest(page.get("text", ""))}
            for page in document.get("pages", [])
            if isinstance(page, Mapping)
        ],
    }
    result["annual_financial"] = {
        "status": annual["status"],
        "selectedPages": annual["selectedPages"],
        "classifications": annual["classifications"],
        "tableAudits": [table["audit"] | {"tableId": table["tableId"]} for table in annual["tables"]],
        "duplicatesRemoved": annual["duplicatesRemoved"],
    }
    result["vdf"] = vdf
    result["financial_cross_validation"] = financial_cross_validation
    result["digest"] = stable_digest({key: value for key, value in result.items() if key != "digest"})
    return result


# =============================================================================
# def 06 REGISTRY / COMPATIBILITY
# =============================================================================

def get_registry() -> dict[str, Any]:
    return json.loads(stable_json(REGISTRY))


def resolve_alias(name: str) -> Any:
    canonical = ALIASES.get(name, name)
    value = globals().get(canonical)
    if not callable(value):
        raise KeyError(f"unknown vrn_logic function: {name}")
    return value


def inspect_python_contract(path: str | os.PathLike[str]) -> dict[str, Any]:
    source_path = Path(path)
    source = source_path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(source_path))
    functions = sorted(node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"))
    classes = sorted(node.name for node in tree.body if isinstance(node, ast.ClassDef) and not node.name.startswith("_"))
    constants = sorted(
        target.id
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in ((node.targets if isinstance(node, ast.Assign) else [node.target]))
        if isinstance(target, ast.Name) and target.id.isupper() and not target.id.startswith("_")
    )
    return {"path": str(source_path), "sha256": sha256_file(source_path), "functions": functions, "classes": classes, "constants": constants}


def compare_contracts(original: Mapping[str, Any], candidate: Mapping[str, Any]) -> dict[str, Any]:
    missing_functions = sorted(set(original.get("functions", ())) - set(candidate.get("functions", ())))
    missing_classes = sorted(set(original.get("classes", ())) - set(candidate.get("classes", ())))
    missing_constants = sorted(set(original.get("constants", ())) - set(candidate.get("constants", ())))
    return {
        "compatible": not missing_functions and not missing_classes,
        "missing_functions": missing_functions,
        "missing_classes": missing_classes,
        "missing_constants": missing_constants,
        "candidate_superset_functions": sorted(set(candidate.get("functions", ())) - set(original.get("functions", ()))),
    }


# Complete callable compatibility aliases.
parse_report_filename = parse_filename
extract_filename_entities = parse_filename
extract_report_metadata = parse_filename
parse_ticker = extract_ticker
resolve_ticker = extract_ticker
parse_report_date = extract_report_date
normalize_temporal = normalize_period
normalize_financial_value = parse_financial_value
reconcile = reconcile_evidence
validate_report = reconcile_evidence
run_vrn_logic = process_report
run = process_report


# =============================================================================
# def 09 DATABASE / OUTPUT
# =============================================================================

def _write_sqlite_database_once(result: Mapping[str, Any], path: str | os.PathLike[str]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    if target.is_file():
        shutil.copy2(target, temporary)
    connection = sqlite3.connect(temporary)
    try:
        connection.execute(f"PRAGMA busy_timeout={DEFAULT_SQLITE_BUSY_TIMEOUT_MS}")
        connection.execute("PRAGMA journal_mode=DELETE")
        connection.execute("PRAGMA foreign_keys=ON")
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS stock_report_basic_info (
                file_id TEXT PRIMARY KEY,
                file_name TEXT NOT NULL,
                ticker TEXT,
                yfinance_ticker TEXT,
                bloomberg_ticker TEXT,
                company_name TEXT,
                rating TEXT,
                target_price REAL,
                broker TEXT,
                broker_key TEXT,
                report_date TEXT,
                market TEXT,
                validation_status TEXT,
                identity_digest TEXT,
                payload_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS stock_report_financial_data (
                file_id TEXT NOT NULL,
                data_name TEXT NOT NULL,
                period TEXT NOT NULL,
                source TEXT NOT NULL,
                statement TEXT,
                item TEXT,
                value REAL,
                unit TEXT,
                confidence REAL,
                grade TEXT,
                status TEXT,
                payload_json TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                PRIMARY KEY (file_id, data_name, period, source)
            );
            CREATE TABLE IF NOT EXISTS vrn_evidence (
                file_id TEXT PRIMARY KEY,
                schema_version TEXT NOT NULL,
                digest TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_vrn_basic_ticker_date ON stock_report_basic_info(ticker, report_date);
            CREATE INDEX IF NOT EXISTS idx_vrn_financial_ticker_period ON stock_report_financial_data(file_id, period);
            """
        )
        basic = dict(result.get("basic_info", {}))
        file_id = normalize_text(basic.get("fileId")) or stable_digest(result)[:16]
        now = datetime.now().astimezone().isoformat()
        connection.execute(
            """
            INSERT INTO stock_report_basic_info VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(file_id) DO UPDATE SET
                file_name=excluded.file_name, ticker=excluded.ticker,
                yfinance_ticker=excluded.yfinance_ticker, bloomberg_ticker=excluded.bloomberg_ticker,
                company_name=excluded.company_name, rating=excluded.rating,
                target_price=excluded.target_price, broker=excluded.broker,
                broker_key=excluded.broker_key, report_date=excluded.report_date,
                market=excluded.market, validation_status=excluded.validation_status,
                identity_digest=excluded.identity_digest, payload_json=excluded.payload_json,
                updated_at=excluded.updated_at
            """,
            (
                file_id, normalize_text(basic.get("fileName")), normalize_text(basic.get("ticker")),
                normalize_text(basic.get("yfinanceTicker")), normalize_text(basic.get("bloombergTicker")),
                normalize_text(basic.get("companyName")), normalize_text(basic.get("rating")), basic.get("targetPrice"),
                normalize_text(basic.get("broker")), normalize_text(basic.get("brokerAbbr")),
                normalize_text(basic.get("reportDate")), normalize_text(basic.get("market")),
                normalize_text(basic.get("validationStatus")), normalize_text(basic.get("identityDigest")),
                stable_json(basic), now,
            ),
        )
        for row in result.get("financial_data", []):
            if not isinstance(row, Mapping):
                continue
            row_file_id = normalize_text(row.get("fileId")) or file_id
            connection.execute(
                """
                INSERT INTO stock_report_financial_data VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(file_id,data_name,period,source) DO UPDATE SET
                    statement=excluded.statement, item=excluded.item, value=excluded.value,
                    unit=excluded.unit, confidence=excluded.confidence, grade=excluded.grade,
                    status=excluded.status, payload_json=excluded.payload_json, updated_at=excluded.updated_at
                """,
                (
                    row_file_id, normalize_text(row.get("dataName")), normalize_text(row.get("period")),
                    normalize_text(row.get("source")) or "unknown", normalize_text(row.get("statement")),
                    normalize_text(row.get("item")), row.get("value"), normalize_text(row.get("unit")),
                    row.get("confidence"), normalize_text(row.get("grade")), normalize_text(row.get("status")),
                    stable_json(row), now,
                ),
            )
        connection.execute(
            """
            INSERT INTO vrn_evidence VALUES (?,?,?,?,?)
            ON CONFLICT(file_id) DO UPDATE SET schema_version=excluded.schema_version,
                digest=excluded.digest, payload_json=excluded.payload_json, updated_at=excluded.updated_at
            """,
            (file_id, normalize_text(result.get("schema")), normalize_text(result.get("digest")), stable_json(result), now),
        )
        connection.commit()
        integrity = connection.execute("PRAGMA integrity_check").fetchone()
        if not integrity or normalize_text(integrity[0]).lower() != "ok":
            raise RuntimeError(f"SQLITE_INTEGRITY_FAILED：{integrity}")
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
    os.replace(temporary, target)
    return target


def write_sqlite_database(
    result: Mapping[str, Any],
    path: str | os.PathLike[str],
    *,
    retry_attempts: int = DEFAULT_SQLITE_RETRY_ATTEMPTS,
) -> Path:
    """Atomically upsert one report, retrying transient SQLite/I/O failures."""
    target = Path(path)
    attempts = max(1, int(retry_attempts or 1))
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return _write_sqlite_database_once(result, target)
        except (OSError, sqlite3.Error) as error:
            last_error = error
            target.with_name(f".{target.name}.{os.getpid()}.tmp").unlink(missing_ok=True)
            if attempt < attempts:
                time.sleep(min(0.25 * attempt, 1.0))
    assert last_error is not None
    raise RuntimeError(f"SQLITE_WRITE_FAILED_AFTER_{attempts}_ATTEMPTS：{last_error}") from last_error


def backup_sqlite_database(
    path: str | os.PathLike[str],
    backup_directory: str | os.PathLike[str],
) -> dict[str, Any] | None:
    """Create a content-addressed, non-destructive backup of an existing database."""
    source = Path(path)
    if not source.is_file():
        return None
    connection = sqlite3.connect(f"file:{source.resolve().as_posix()}?mode=ro", uri=True)
    try:
        integrity = normalize_text(connection.execute("PRAGMA integrity_check").fetchone()[0]).lower()
    finally:
        connection.close()
    if integrity != "ok":
        raise RuntimeError(f"SQLITE_BACKUP_SOURCE_INTEGRITY_FAILED：{integrity}")
    digest = sha256_file(source)
    destination = Path(backup_directory) / f"{source.name}.{digest[:16]}.bak"
    if not destination.is_file():
        destination.parent.mkdir(parents=True, exist_ok=True)
        staged = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
        shutil.copy2(source, staged)
        if sha256_file(staged) != digest:
            staged.unlink(missing_ok=True)
            raise RuntimeError("SQLITE_BACKUP_HASH_MISMATCH")
        os.replace(staged, destination)
    if sha256_file(destination) != digest:
        raise RuntimeError("SQLITE_EXISTING_BACKUP_HASH_MISMATCH")
    return {"path": str(destination), "sha256": digest, "bytes": destination.stat().st_size}


def write_duckdb_database(result: Mapping[str, Any], path: str | os.PathLike[str]) -> Path:
    if importlib.util.find_spec("duckdb") is None:
        raise RuntimeError("duckdb requested but duckdb is not installed in the selected VRN environment")
    import duckdb  # type: ignore

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    if target.is_file():
        shutil.copy2(target, temporary)
    connection = duckdb.connect(str(temporary))
    basic = dict(result.get("basic_info", {}))
    file_id = normalize_text(basic.get("fileId")) or stable_digest(result)[:16]
    now = datetime.now().astimezone().isoformat()
    try:
        connection.execute("BEGIN TRANSACTION")
        connection.execute("CREATE TABLE IF NOT EXISTS stock_report_basic_info (file_id VARCHAR PRIMARY KEY, ticker VARCHAR, report_date VARCHAR, payload_json VARCHAR, updated_at VARCHAR)")
        connection.execute("CREATE TABLE IF NOT EXISTS stock_report_financial_data (file_id VARCHAR, data_name VARCHAR, period VARCHAR, source VARCHAR, payload_json VARCHAR, updated_at VARCHAR, PRIMARY KEY(file_id,data_name,period,source))")
        connection.execute("CREATE TABLE IF NOT EXISTS vrn_evidence (file_id VARCHAR PRIMARY KEY, schema_version VARCHAR, digest VARCHAR, payload_json VARCHAR, updated_at VARCHAR)")
        connection.execute("DELETE FROM stock_report_basic_info WHERE file_id=?", [file_id])
        connection.execute("INSERT INTO stock_report_basic_info VALUES (?,?,?,?,?)", [file_id, basic.get("ticker"), basic.get("reportDate"), stable_json(basic), now])
        connection.execute("DELETE FROM stock_report_financial_data WHERE file_id=?", [file_id])
        for row in result.get("financial_data", []):
            if isinstance(row, Mapping):
                connection.execute(
                    "INSERT INTO stock_report_financial_data VALUES (?,?,?,?,?,?)",
                    [file_id, row.get("dataName"), row.get("period"), row.get("source"), stable_json(row), now],
                )
        connection.execute("DELETE FROM vrn_evidence WHERE file_id=?", [file_id])
        connection.execute("INSERT INTO vrn_evidence VALUES (?,?,?,?,?)", [file_id, result.get("schema"), result.get("digest"), stable_json(result), now])
        connection.execute("COMMIT")
    except Exception:
        connection.execute("ROLLBACK")
        raise
    finally:
        connection.close()
    os.replace(temporary, target)
    return target

def write_outputs(result: Mapping[str, Any], output_dir: str | os.PathLike[str], formats: Sequence[str] = DEFAULT_FORMATS) -> list[dict[str, Any]]:
    directory = Path(output_dir)
    selected_formats = tuple(dict.fromkeys(normalize_text(item).lower() for item in formats if normalize_text(item)))
    artifacts: list[dict[str, Any]] = []
    if "json" in selected_formats:
        path = atomic_write_text(directory / f"{DEFAULT_OUTPUT_STEM_EVIDENCE}.json", stable_json(result, pretty=True) + "\n")
        artifacts.append({"path": str(path), "sha256": sha256_file(path), "format": "json"})
    if "csv" in selected_formats:
        basic = result.get("basic_info", {})
        basic_path = atomic_write_csv(directory / f"{DEFAULT_OUTPUT_STEM_BASIC}.csv", [basic], REGISTRY["schemas"]["basic_info"])
        artifacts.append({"path": str(basic_path), "sha256": sha256_file(basic_path), "format": "csv"})
        financial = result.get("financial_data", [])
        financial_path = atomic_write_csv(directory / f"{DEFAULT_OUTPUT_STEM_FINANCIAL}.csv", financial, REGISTRY["schemas"]["financial_data"])
        artifacts.append({"path": str(financial_path), "sha256": sha256_file(financial_path), "format": "csv"})
    if "parquet" in selected_formats:
        try:
            import pyarrow as pa  # type: ignore
            import pyarrow.parquet as pq  # type: ignore
        except ImportError as exc:
            raise RuntimeError("parquet requested but pyarrow is not installed in the selected VRN environment") from exc
        for stem, rows in (
            (DEFAULT_OUTPUT_STEM_BASIC, [result.get("basic_info", {})]),
            (DEFAULT_OUTPUT_STEM_FINANCIAL, result.get("financial_data", [])),
        ):
            path = directory / f"{stem}.parquet"
            path.parent.mkdir(parents=True, exist_ok=True)
            temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
            pq.write_table(pa.Table.from_pylist(list(rows)), temp)
            os.replace(temp, path)
            artifacts.append({"path": str(path), "sha256": sha256_file(path), "format": "parquet"})
    if "sqlite" in selected_formats:
        path = write_sqlite_database(result, directory / DEFAULT_SQLITE_NAME)
        artifacts.append({"path": str(path), "sha256": sha256_file(path), "format": "sqlite"})
    if "duckdb" in selected_formats:
        path = write_duckdb_database(result, directory / DEFAULT_DUCKDB_NAME)
        artifacts.append({"path": str(path), "sha256": sha256_file(path), "format": "duckdb"})
    return artifacts


# =============================================================================
# def 10 RESUMABLE BATCH AUDIT / STAGING
# =============================================================================

def discover_pdf_reports(
    root: str | os.PathLike[str],
    *,
    recursive: bool = True,
    max_files: int = DEFAULT_BATCH_MAX_FILES,
) -> list[Path]:
    source_root = Path(root).expanduser().resolve()
    if not source_root.is_dir():
        raise NotADirectoryError(f"BATCH_ROOT_NOT_FOUND：{source_root}")
    iterator = source_root.rglob("*.pdf") if recursive else source_root.glob("*.pdf")
    files = sorted(
        (path.resolve() for path in iterator if path.is_file() and not path.is_symlink()),
        key=lambda path: path.relative_to(source_root).as_posix().casefold(),
    )
    limit = max(1, int(max_files or DEFAULT_BATCH_MAX_FILES))
    if len(files) > limit:
        raise RuntimeError(f"BATCH_FILE_LIMIT_EXCEEDED：FOUND={len(files)} LIMIT={limit}")
    return files


def inventory_batch_reports(
    root: str | os.PathLike[str],
    *,
    recursive: bool = True,
    max_files: int = DEFAULT_BATCH_MAX_FILES,
) -> list[dict[str, Any]]:
    source_root = Path(root).expanduser().resolve()
    seen_hashes: dict[str, str] = {}
    records: list[dict[str, Any]] = []
    for path in discover_pdf_reports(source_root, recursive=recursive, max_files=max_files):
        relative = path.relative_to(source_root).as_posix()
        digest = sha256_file(path)
        duplicate_of = seen_hashes.get(digest, "")
        if not duplicate_of:
            seen_hashes[digest] = relative
        records.append(
            {
                "relativePath": relative,
                "sourcePath": str(path),
                "sourceSHA256": digest,
                "bytes": path.stat().st_size,
                "duplicateOf": duplicate_of,
                "status": "DUPLICATE_SKIPPED" if duplicate_of else "DISCOVERED",
                "lastAction": "INVENTORIED",
            }
        )
    return records


def load_batch_checkpoint(path: str | os.PathLike[str]) -> dict[str, Any]:
    checkpoint_path = Path(path)
    if not checkpoint_path.is_file():
        return {"schema": BATCH_CHECKPOINT_SCHEMA, "root": "", "items": {}}
    payload = json.loads(checkpoint_path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, Mapping) or payload.get("schema") != BATCH_CHECKPOINT_SCHEMA:
        raise ValueError(f"BATCH_CHECKPOINT_SCHEMA_MISMATCH：{checkpoint_path}")
    if not isinstance(payload.get("items"), Mapping):
        raise ValueError(f"BATCH_CHECKPOINT_ITEMS_INVALID：{checkpoint_path}")
    return dict(payload)


def save_batch_checkpoint(path: str | os.PathLike[str], checkpoint: Mapping[str, Any]) -> Path:
    payload = dict(checkpoint)
    payload["schema"] = BATCH_CHECKPOINT_SCHEMA
    payload["updatedAt"] = datetime.now().astimezone().isoformat()
    payload["digest"] = stable_digest({key: value for key, value in payload.items() if key not in {"digest", "updatedAt"}})
    return atomic_write_text(path, stable_json(payload, pretty=True) + "\n")


def _read_batch_database(database_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    if not database_path.is_file():
        return [], [], []
    connection = sqlite3.connect(f"file:{database_path.resolve().as_posix()}?mode=ro", uri=True)
    try:
        integrity = normalize_text(connection.execute("PRAGMA integrity_check").fetchone()[0]).lower()
        if integrity != "ok":
            raise RuntimeError(f"BATCH_DATABASE_INTEGRITY_FAILED：{integrity}")
        basic = [json.loads(row[0]) for row in connection.execute("SELECT payload_json FROM stock_report_basic_info ORDER BY file_id")]
        financial = [json.loads(row[0]) for row in connection.execute("SELECT payload_json FROM stock_report_financial_data ORDER BY file_id,data_name,period,source")]
        evidence = [json.loads(row[0]) for row in connection.execute("SELECT payload_json FROM vrn_evidence ORDER BY file_id")]
    finally:
        connection.close()
    return basic, financial, evidence


def export_batch_database(
    database_path: str | os.PathLike[str],
    output_directory: str | os.PathLike[str],
    formats: Sequence[str] = DEFAULT_FORMATS,
) -> list[dict[str, Any]]:
    database = Path(database_path)
    directory = Path(output_directory)
    selected = tuple(dict.fromkeys(normalize_text(item).lower() for item in formats if normalize_text(item)))
    basic, financial, evidence = _read_batch_database(database)
    artifacts: list[dict[str, Any]] = []
    if database.is_file() and "sqlite" in selected:
        artifacts.append({"path": str(database), "sha256": sha256_file(database), "format": "sqlite"})
    if "json" in selected:
        path = atomic_write_text(directory / DEFAULT_BATCH_EVIDENCE_NAME, "".join(stable_json(row) + "\n" for row in evidence))
        artifacts.append({"path": str(path), "sha256": sha256_file(path), "format": "jsonl"})
    if "csv" in selected:
        for name, rows, columns in (
            (DEFAULT_OUTPUT_STEM_BASIC, basic, REGISTRY["schemas"]["basic_info"]),
            (DEFAULT_OUTPUT_STEM_FINANCIAL, financial, REGISTRY["schemas"]["financial_data"]),
        ):
            path = atomic_write_csv(directory / f"{name}.csv", rows, columns)
            artifacts.append({"path": str(path), "sha256": sha256_file(path), "format": "csv"})
    if "parquet" in selected:
        try:
            import pyarrow as pa  # type: ignore
            import pyarrow.parquet as pq  # type: ignore
        except ImportError as exc:
            raise RuntimeError("parquet requested but pyarrow is not installed in the selected VRN environment") from exc
        for name, rows in ((DEFAULT_OUTPUT_STEM_BASIC, basic), (DEFAULT_OUTPUT_STEM_FINANCIAL, financial)):
            path = directory / f"{name}.parquet"
            path.parent.mkdir(parents=True, exist_ok=True)
            staged = path.with_name(f".{path.name}.{os.getpid()}.tmp")
            pq.write_table(pa.Table.from_pylist(rows), staged)
            os.replace(staged, path)
            artifacts.append({"path": str(path), "sha256": sha256_file(path), "format": "parquet"})
    return artifacts


def write_batch_governance_outputs(
    summary: Mapping[str, Any],
    records: Sequence[Mapping[str, Any]],
    output_directory: str | os.PathLike[str],
) -> list[dict[str, Any]]:
    directory = Path(output_directory)
    columns = REGISTRY["schemas"]["batch_matrix"]
    summary_path = atomic_write_text(directory / DEFAULT_BATCH_SUMMARY_NAME, stable_json(summary, pretty=True) + "\n")
    matrix_path = atomic_write_csv(directory / DEFAULT_BATCH_MATRIX_NAME, records, columns)
    body = "\n".join(
        "<tr>"
        f"<td>{html_escape(normalize_text(row.get('relativePath')))}</td>"
        f"<td>{html_escape(normalize_text(row.get('status')))}</td>"
        f"<td>{html_escape(normalize_text(row.get('validation')))}</td>"
        f"<td>{html_escape(normalize_text(row.get('ticker')))}</td>"
        f"<td>{html_escape(normalize_text(row.get('name')))}</td>"
        f"<td>{html_escape(normalize_text(row.get('financialRows')))}</td>"
        f"<td>{html_escape(normalize_text(row.get('errorMessage')))}</td>"
        "</tr>"
        for row in records
    )
    html = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<title>VIA VRN Batch</title><style>body{{font-family:Segoe UI,Arial,sans-serif;margin:28px;background:#0b1220;color:#e5e7eb}}table{{width:100%;border-collapse:collapse;background:#111827}}th,td{{border:1px solid #334155;padding:8px;vertical-align:top;font-size:12px;overflow-wrap:anywhere}}th{{background:#1e293b}}</style></head>
<body><h1>VIA · VRN Batch v{MODULE_VERSION}</h1><p>{html_escape(normalize_text(summary.get('gate')))}</p>
<table><thead><tr><th>File</th><th>Status</th><th>Validation</th><th>Ticker</th><th>Name</th><th>Rows</th><th>Error</th></tr></thead><tbody>{body}</tbody></table></body></html>"""
    report_path = atomic_write_text(directory / DEFAULT_BATCH_REPORT_NAME, html)
    return [
        {"path": str(summary_path), "sha256": sha256_file(summary_path), "format": "json"},
        {"path": str(matrix_path), "sha256": sha256_file(matrix_path), "format": "csv"},
        {"path": str(report_path), "sha256": sha256_file(report_path), "format": "html"},
    ]


def _csv_contract_state(path: Path) -> dict[str, Any]:
    with path.open("r", encoding=DEFAULT_ENCODING, newline="") as handle:
        reader = csv.DictReader(handle)
        count = sum(1 for _ in reader)
        return {"records": count, "columns": tuple(reader.fieldnames or ())}


def _sqlite_contract_state(path: Path) -> dict[str, Any]:
    connection = sqlite3.connect(f"file:{path.resolve().as_posix()}?mode=ro", uri=True)
    try:
        integrity = normalize_text(connection.execute("PRAGMA integrity_check").fetchone()[0]).lower()
        counts = {
            "basic_info": connection.execute("SELECT COUNT(*) FROM stock_report_basic_info").fetchone()[0],
            "financial_data": connection.execute("SELECT COUNT(*) FROM stock_report_financial_data").fetchone()[0],
            "evidence": connection.execute("SELECT COUNT(*) FROM vrn_evidence").fetchone()[0],
        }
    finally:
        connection.close()
    return {"integrity": integrity, "counts": counts}


def validate_batch_output_contract(output_directory: str | os.PathLike[str]) -> dict[str, Any]:
    """Validate the nine governed STAGE outputs without mutating them."""
    output = Path(output_directory).expanduser().resolve()
    rows: list[dict[str, Any]] = []
    parsed: dict[str, Any] = {}
    by_key: dict[str, dict[str, Any]] = {}

    for key, relative, kind in STAGE_OUTPUT_CONTRACT:
        matches = sorted(output.glob(relative)) if "*" in relative else [output / relative]
        matches = [path for path in matches if path.is_file()]
        row: dict[str, Any] = {
            "artifact": key,
            "relativePath": relative,
            "kind": kind,
            "exists": bool(matches),
            "fileCount": len(matches),
            "bytes": sum(path.stat().st_size for path in matches),
            "sha256": "SELF_EXCLUDED" if kind == "json_self" else stable_digest([sha256_file(path) for path in matches]) if len(matches) > 1 else sha256_file(matches[0]) if matches else "",
            "records": 0,
            "decision": "PASS" if matches else "BLOCK",
            "detail": "" if matches else "MISSING_REQUIRED_ARTIFACT",
            "files": [{"path": str(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)} for path in matches],
        }
        if kind == "json_self":
            row["bytes"] = "SELF_EXCLUDED"
            row["files"] = []
        try:
            if not matches:
                pass
            elif kind in {"json", "json_self"}:
                payload = json.loads(matches[0].read_text(encoding="utf-8-sig"))
                parsed[key] = payload
                if not isinstance(payload, Mapping):
                    raise ValueError("JSON_ROOT_NOT_OBJECT")
                expected_schema = BATCH_CHECKPOINT_SCHEMA if key == "checkpoint" else BATCH_SUMMARY_SCHEMA
                if payload.get("schema") != expected_schema:
                    raise ValueError(f"SCHEMA_MISMATCH：{payload.get('schema')}")
                if key == "checkpoint":
                    expected_digest = stable_digest({name: value for name, value in payload.items() if name not in {"digest", "updatedAt"}})
                    if payload.get("digest") != expected_digest:
                        raise ValueError("CHECKPOINT_DIGEST_MISMATCH")
                row["records"] = len(payload.get("items", {})) if key == "checkpoint" else 1
            elif kind.startswith("csv_"):
                csv_state = _csv_contract_state(matches[0])
                row["records"] = csv_state["records"]
                required_columns = {
                    "csv_matrix": REGISTRY["schemas"]["batch_matrix"],
                    "csv_basic": REGISTRY["schemas"]["basic_info"],
                    "csv_financial": REGISTRY["schemas"]["financial_data"],
                }[kind]
                missing_columns = sorted(set(required_columns) - set(csv_state["columns"]))
                if missing_columns:
                    raise ValueError(f"CSV_COLUMNS_MISSING：{','.join(missing_columns)}")
            elif kind == "jsonl_evidence":
                evidence = []
                for line_number, line in enumerate(matches[0].read_text(encoding="utf-8-sig").splitlines(), start=1):
                    if line.strip():
                        value = json.loads(line)
                        if not isinstance(value, Mapping):
                            raise ValueError(f"JSONL_ROW_NOT_OBJECT：{line_number}")
                        evidence.append(value)
                row["records"] = len(evidence)
            elif kind == "html":
                content = matches[0].read_text(encoding="utf-8-sig")
                if "<html" not in content.casefold() or "VIA · VRN Batch" not in content:
                    raise ValueError("HTML_SIGNATURE_MISSING")
                row["records"] = content.count("<tr>") - 1
            elif kind == "sqlite":
                state = _sqlite_contract_state(matches[0])
                parsed["database_state"] = state
                row["records"] = sum(state["counts"].values())
                row["tableCounts"] = state["counts"]
                if state["integrity"] != "ok":
                    raise ValueError(f"SQLITE_INTEGRITY_{state['integrity']}")
            elif kind == "sqlite_backup":
                for path in matches:
                    state = _sqlite_contract_state(path)
                    if state["integrity"] != "ok":
                        raise ValueError(f"BACKUP_INTEGRITY_{state['integrity']}")
                    match = re.search(r"\.([A-F0-9]{16})\.bak$", path.name, re.I)
                    if not match or not sha256_file(path).startswith(match.group(1).upper()):
                        raise ValueError(f"BACKUP_NAME_HASH_MISMATCH：{path.name}")
                row["records"] = len(matches)
        except Exception as error:
            row["decision"] = "BLOCK"
            row["detail"] = f"{type(error).__name__}:{normalize_text(error)}"
        rows.append(row)
        by_key[key] = row

    database_state = parsed.get("database_state", {"counts": {}})
    database_counts = dict(database_state.get("counts", {}))
    cross_checks = (
        ("basic_info", database_counts.get("basic_info")),
        ("financial_data", database_counts.get("financial_data")),
        ("evidence", database_counts.get("evidence")),
    )
    for key, expected in cross_checks:
        row = by_key[key]
        if expected is not None and row["records"] != expected:
            row["decision"] = "BLOCK"
            mismatch = f"ROW_COUNT_MISMATCH：FILE={row['records']} DB={expected}"
            row["detail"] = f"{row['detail']};{mismatch}" if row["detail"] else mismatch
    summary_payload = parsed.get("summary", {})
    expected_matrix_rows = summary_payload.get("counts", {}).get("discovered") if isinstance(summary_payload, Mapping) else None
    if expected_matrix_rows is not None and by_key["matrix"]["records"] != expected_matrix_rows:
        by_key["matrix"]["decision"] = "BLOCK"
        by_key["matrix"]["detail"] = f"MATRIX_COUNT_MISMATCH：CSV={by_key['matrix']['records']} SUMMARY={expected_matrix_rows}"
    failed = sum(1 for row in rows if row["decision"] != "PASS")
    result = {
        "status": "PASS" if failed == 0 else "BLOCK",
        "expected": len(STAGE_OUTPUT_CONTRACT),
        "passed": len(rows) - failed,
        "failed": failed,
        "databaseCounts": database_counts,
        "rows": rows,
    }
    result["digest"] = stable_digest(result)
    return result


def collect_batch_artifacts(output_directory: str | os.PathLike[str]) -> list[dict[str, Any]]:
    output = Path(output_directory).expanduser().resolve()
    paths: set[Path] = set()
    for _, relative, _ in STAGE_OUTPUT_CONTRACT:
        matches = output.glob(relative) if "*" in relative else (output / relative,)
        paths.update(path for path in matches if path.is_file())
    for pattern in ("*.parquet", "*.duckdb"):
        paths.update(path for path in output.glob(pattern) if path.is_file())
    return [
        {"path": str(path), "sha256": sha256_file(path), "bytes": path.stat().st_size, "format": path.suffix.lower().lstrip(".")}
        for path in sorted(paths, key=lambda item: item.as_posix().casefold())
    ]


def process_batch_reports(
    batch_root: str | os.PathLike[str],
    *,
    output_directory: str | os.PathLike[str],
    mode: str = "audit",
    vdf_source: str | os.PathLike[str] | None = None,
    company_dict_path: str | os.PathLike[str] | None = None,
    market_hint: str = "",
    max_pages: int = DEFAULT_PDF_MAX_PAGES,
    formats: Sequence[str] = DEFAULT_FORMATS,
    recursive: bool = True,
    resume: bool = True,
    retry_failed: bool = False,
    fail_fast: bool = False,
    max_files: int = DEFAULT_BATCH_MAX_FILES,
    checkpoint_path: str | os.PathLike[str] | None = None,
) -> dict[str, Any]:
    selected_mode = normalize_text(mode).lower()
    if selected_mode not in {"audit", "stage"}:
        raise ValueError("batch mode must be audit or stage")
    source_root = Path(batch_root).expanduser().resolve()
    output = Path(output_directory).expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    checkpoint_file = Path(checkpoint_path).expanduser().resolve() if checkpoint_path else output / DEFAULT_BATCH_CHECKPOINT_NAME
    checkpoint = load_batch_checkpoint(checkpoint_file)
    checkpoint_root = normalize_text(checkpoint.get("root"))
    if checkpoint_root and Path(checkpoint_root).resolve() != source_root:
        raise RuntimeError(f"BATCH_CHECKPOINT_ROOT_MISMATCH：EXPECTED={source_root} ACTUAL={checkpoint_root}")
    checkpoint["root"] = str(source_root)
    items = dict(checkpoint.get("items", {}))
    inventory = inventory_batch_reports(source_root, recursive=recursive, max_files=max_files)
    started_at = datetime.now().astimezone().isoformat()
    selected_formats = parse_formats(",".join(formats)) if not isinstance(formats, str) else parse_formats(formats)
    if selected_mode == "stage" and "sqlite" not in selected_formats:
        selected_formats = (*selected_formats, "sqlite")
    database = output / DEFAULT_SQLITE_NAME
    duckdb_path = output / DEFAULT_DUCKDB_NAME
    backup = None

    for discovered in inventory:
        relative = discovered["relativePath"]
        previous = dict(items.get(relative, {})) if isinstance(items.get(relative), Mapping) else {}
        same_source = previous.get("sourceSHA256") == discovered["sourceSHA256"]
        record = previous if same_source else {}
        record.update({key: value for key, value in discovered.items() if key not in {"status", "lastAction"}})
        prior_status = normalize_text(previous.get("status")).upper()
        if discovered["duplicateOf"]:
            record.update({"status": "DUPLICATE_SKIPPED", "lastAction": "AUDITED_DUPLICATE"})
        elif same_source and prior_status:
            record["status"] = prior_status
            record["lastAction"] = "AUDITED_UNCHANGED"
        else:
            record.update({"status": "DISCOVERED", "lastAction": "AUDITED"})
        items[relative] = record

    checkpoint["items"] = items
    checkpoint["lastMode"] = selected_mode.upper()
    checkpoint["inventoryDigest"] = stable_digest(
        [{"relativePath": row["relativePath"], "sourceSHA256": row["sourceSHA256"], "bytes": row["bytes"]} for row in inventory]
    )
    save_batch_checkpoint(checkpoint_file, checkpoint)

    if selected_mode == "stage" and database.is_file():
        backup = backup_sqlite_database(database, output / "backups")

    stop_after_failure = False
    if selected_mode == "stage":
        for discovered in inventory:
            relative = discovered["relativePath"]
            record = dict(items[relative])
            if discovered["duplicateOf"]:
                items[relative] = record
                continue
            if stop_after_failure:
                record.update({"status": "PENDING", "lastAction": "PENDING_AFTER_FAIL_FAST"})
                items[relative] = record
                continue
            same_source = record.get("sourceSHA256") == discovered["sourceSHA256"]
            prior_status = normalize_text(record.get("status")).upper()
            if resume and same_source and prior_status in {"SUCCEEDED", "STAGED_REVIEW"}:
                record["lastAction"] = "SKIPPED_UNCHANGED"
                items[relative] = record
                continue
            if resume and same_source and prior_status in {"FAILED", "QUARANTINED"} and not retry_failed:
                record["lastAction"] = "SKIPPED_FAILED_EXPLICIT_RETRY_REQUIRED"
                items[relative] = record
                continue
            record["attempts"] = int(record.get("attempts", 0) or 0) + 1
            record["lastAction"] = "STAGE_STARTED"
            record["errorType"] = ""
            record["errorMessage"] = ""
            try:
                result = process_pdf_report(
                    discovered["sourcePath"],
                    vdf_source=vdf_source,
                    company_dict_path=company_dict_path,
                    market_hint=market_hint,
                    max_pages=max_pages,
                    file_id=discovered["sourceSHA256"][:16],
                )
                validation = normalize_text(result.get("validation", {}).get("status")).upper()
                basic = result.get("basic_info", {})
                record.update(
                    {
                        "validation": validation,
                        "ticker": basic.get("ticker", ""),
                        "yfinanceTicker": basic.get("yfinanceTicker", ""),
                        "bloombergTicker": basic.get("bloombergTicker", ""),
                        "name": basic.get("companyName", ""),
                        "rating": basic.get("rating", ""),
                        "targetPrice": basic.get("targetPrice"),
                        "broker": basic.get("broker", ""),
                        "financialRows": len(result.get("financial_data", [])),
                        "vdfRows": len(result.get("vdf", {}).get("financialRows", [])),
                        "resultDigest": result.get("digest", ""),
                        "fileId": basic.get("fileId", ""),
                    }
                )
                if validation == "RED":
                    record.update({"status": "QUARANTINED", "lastAction": "VALIDATION_RED_NOT_WRITTEN"})
                else:
                    write_sqlite_database(result, database)
                    if "duckdb" in selected_formats:
                        write_duckdb_database(result, duckdb_path)
                    record.update(
                        {
                            "status": "STAGED_REVIEW" if validation == "YELLOW" else "SUCCEEDED",
                            "lastAction": "STAGED_DATABASE_UPSERT",
                        }
                    )
            except Exception as error:
                record.update(
                    {
                        "status": "FAILED",
                        "lastAction": "FAILED_ISOLATED",
                        "errorType": type(error).__name__,
                        "errorMessage": normalize_text(error),
                        "tracebackTail": traceback.format_exc().splitlines()[-8:],
                    }
                )
                stop_after_failure = bool(fail_fast)
            items[relative] = record
            checkpoint["items"] = items
            save_batch_checkpoint(checkpoint_file, checkpoint)

    active_records = [dict(items[row["relativePath"]]) for row in inventory]
    counts = {
        "discovered": len(inventory),
        "unique": sum(1 for row in inventory if not row["duplicateOf"]),
        "duplicates": sum(1 for row in inventory if row["duplicateOf"]),
        "succeeded": sum(1 for row in active_records if row.get("status") == "SUCCEEDED"),
        "review": sum(1 for row in active_records if row.get("status") == "STAGED_REVIEW"),
        "failed": sum(1 for row in active_records if row.get("status") == "FAILED"),
        "quarantined": sum(1 for row in active_records if row.get("status") == "QUARANTINED"),
        "pending": sum(1 for row in active_records if row.get("status") in {"DISCOVERED", "PENDING"}),
        "skippedUnchanged": sum(1 for row in active_records if row.get("lastAction") == "SKIPPED_UNCHANGED"),
        "skippedFailed": sum(1 for row in active_records if row.get("lastAction") == "SKIPPED_FAILED_EXPLICIT_RETRY_REQUIRED"),
    }
    if selected_mode == "audit":
        status, gate = "YELLOW", "YELLOW / VRN_BATCH_AUDIT_COMPLETE_STAGE_REQUIRED"
    elif counts["failed"] or counts["quarantined"] or counts["pending"] or counts["skippedFailed"]:
        status, gate = "RED", "RED / VRN_BATCH_STAGE_INCOMPLETE_OR_QUARANTINED"
    elif counts["review"]:
        status, gate = "YELLOW", "YELLOW / VRN_BATCH_STAGED_REVIEW_REQUIRED"
    else:
        status, gate = "GREEN", "GREEN / VRN_BATCH_STAGE_COMPLETE_NO_PROMOTION"
    if selected_mode == "stage" and database.is_file():
        export_batch_database(database, output, selected_formats)
        if backup is None:
            backup = backup_sqlite_database(database, output / "backups")

    summary = {
        "schema": BATCH_SUMMARY_SCHEMA,
        "moduleVersion": MODULE_VERSION,
        "mode": selected_mode.upper(),
        "status": status,
        "gate": gate,
        "batchRoot": str(source_root),
        "outputDirectory": str(output),
        "checkpoint": str(checkpoint_file),
        "database": str(database) if database.is_file() else "",
        "backup": backup or {},
        "counts": counts,
        "inventoryDigest": checkpoint["inventoryDigest"],
        "startedAt": started_at,
        "finishedAt": datetime.now().astimezone().isoformat(),
        "networkCalls": 0,
        "canonicalMutation": 0,
        "promotion": 0,
    }
    checkpoint["items"] = items
    checkpoint["lastGate"] = gate
    save_batch_checkpoint(checkpoint_file, checkpoint)
    write_batch_governance_outputs(summary, active_records, output)

    if selected_mode == "stage":
        output_contract = validate_batch_output_contract(output)
        if output_contract["status"] != "PASS":
            status = "RED"
            gate = "RED / VRN_BATCH_STAGE_OUTPUT_CONTRACT_BLOCKED"
            summary["status"] = status
            summary["gate"] = gate
            checkpoint["lastGate"] = gate
            save_batch_checkpoint(checkpoint_file, checkpoint)
            write_batch_governance_outputs(summary, active_records, output)
            output_contract = validate_batch_output_contract(output)
        summary["outputContract"] = output_contract
        atomic_write_text(output / DEFAULT_BATCH_SUMMARY_NAME, stable_json(summary, pretty=True) + "\n")

    returned = dict(summary)
    returned["artifacts"] = collect_batch_artifacts(output)
    return returned


# =============================================================================
# def 08 SIXTEEN-CHECK SELFTEST
# =============================================================================

def selftest(verbose: bool = True) -> int:
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, condition: Any, detail: str = "") -> None:
        checks.append((name, bool(condition), detail))

    check("import_vrn_logic", MODULE_NAME == "vrn_logic" and callable(process_report))
    check(
        "module_meta_and_ssot_contract",
        MODULE_META["writer"] is False
        and MODULE_META["network_default"] is False
        and SSOT_CONTRACT["single_writer"] == "CGC-PROMOTE-WORKER-001"
        and tuple(SSOT_CONTRACT["lifecycle"]) == ("AUDIT", "STAGE", "APPROVE", "PROMOTE"),
    )
    check(
        "registry_contract_and_aliases",
        set(("basic_info", "financial_data", "identity")).issubset(REGISTRY["schemas"])
        and all(resolve_alias(alias) is globals()[canonical] for alias, canonical in ALIASES.items()),
    )
    tokens = tokenize_filename("CTBC-2330台積電_20260914.pdf")
    parsed_filename = parse_filename("CTBC-2330台積電-買進-TP1500-20260914.pdf", market_hint="TWSE")
    check(
        "filename_tokenization",
        "CTBC" in tokens
        and "2330" in tokens
        and "台積電" in tokens
        and "20260914" in tokens
        and parsed_filename["TICKER"] == "2330"
        and parsed_filename["YFINANCE_TICKER"] == "2330.TW"
        and parsed_filename["BLOOMBERG_TICKER"] == "2330 TT"
        and parsed_filename["NAME"] == "台積電"
        and parsed_filename["TARGET_PRICE"] == 1500.0,
        str(tokens),
    )
    check(
        "ticker_market_contract",
        extract_ticker("2330.TW") == "2330"
        and extract_ticker("3324.TWO") == "3324"
        and infer_market("3324.TWO", "3324") == "TPEX"
        and extract_active_etf_ticker("00980A") == "00980A",
    )
    check(
        "date_gregorian_roc_short",
        extract_report_date("report_20260914.pdf") == "2026-09-14"
        and extract_report_date("民國115年09月14日") == "2026-09-14"
        and extract_report_date("CTBC260914") == "2026-09-14",
    )
    check(
        "broker_rating_report_type",
        canonicalize_broker("中信投顧")["key"] == "CTBC"
        and canonicalize_rating("Overweight") == "BUY"
        and "STRONG_BUY" in RATING_LIST
        and BRIKER_DICT is BROKER_DICT
        and detect_report_type("半導體產業報告.pdf") == "INDUSTRY_REPORT",
    )
    value, unit = parse_financial_value("(1,234.50) 百萬元")
    check(
        "period_and_value_normalization",
        normalize_period("1Q25E") == "2025-Q1E"
        and normalize_period("2024F") == "2024F"
        and value == -1234.5
        and unit == "million",
    )
    filename_evidence = parse_filename("CTBC-2330-台積電-20260914-買進.pdf")
    filename_evidence["source"] = "filename"
    first_evidence = parse_first_page("台積電 2330 TT 中信投顧 買進 目標價: 1,500 2026/09/14")
    consensus = reconcile_evidence(filename_evidence, first_evidence)
    check(
        "filename_first_page_consensus",
        consensus["fields"]["ticker"]["status"] == "MATCH"
        and first_evidence["NAME"] == "台積電"
        and first_evidence["TARGET_PRICE"] == 1500.0
        and consensus["status"] in {"GREEN", "YELLOW"},
    )
    conflict_first = dict(first_evidence)
    conflict_first["ticker"] = "2317"
    conflict = reconcile_evidence(filename_evidence, conflict_first)
    check("ticker_conflict_fail_closed", conflict["status"] == "RED" and conflict["blocking"] == ["ticker"])
    rows = [
        normalize_financial_row({"item": "營收", "period": "2024", "value": "1,000", "unit": "百萬元", "confidence": 0.80, "source": "first_page"}, file_id="F1"),
        normalize_financial_row({"item": "Revenue", "period": "2024", "value": "1,000", "unit": "million", "confidence": 0.95, "source": "financial_page"}, file_id="F1"),
    ]
    deduped, duplicate_count = deduplicate_financial_rows(rows)
    restored = restore_financial_table(
        {"page": 3, "tableIndex": 1, "engine": "fixture", "rows": [["項目", "2023A", "2024E"], ["營收", "1,000", "1,200"], ["EPS", "10.5", "12.0"]]},
        file_id="F1",
        file_name="fixture.pdf",
    )
    check(
        "financial_atomicity_and_dedup",
        duplicate_count == 1
        and len(deduped) == 1
        and deduped[0]["grade"] == "V"
        and restored["audit"]["decision"] == "PASS"
        and len(restored["rows"]) == 4,
    )
    formula_rows = [
        normalize_financial_row({"item": "營收", "period": "2024", "value": 1000, "unit": "million"}, file_id="F1"),
        normalize_financial_row({"item": "毛利", "period": "2024", "value": 400, "unit": "million"}, file_id="F1"),
        normalize_financial_row({"item": "營業利益", "period": "2024", "value": 200, "unit": "million"}, file_id="F1"),
    ]
    formula_checks = validate_financial_formulas(formula_rows)
    check("financial_formula_validation", len(formula_checks) == 2 and all(item["status"] == "PASS" for item in formula_checks))
    fixture = {
        "fileId": "DOC001",
        "filename": "CTBC-2330-台積電-20260914-買進.pdf",
        "firstPageText": "台積電 2330 TT 中信投顧 買進 目標價: 1,500 2026/09/14",
        "official": {"companyName": "台積電", "ticker": "2330", "source": "official"},
        "financialRows": [
            {"item": "營收", "period": "2024", "value": 1000, "unit": "million"},
            {"item": "毛利", "period": "2024", "value": 400, "unit": "million"},
        ],
    }
    result = process_report(fixture)
    basic_columns = set(REGISTRY["schemas"]["basic_info"])
    check(
        "full_pipeline_basic_info_contract",
        basic_columns.issubset(result["basic_info"])
        and result["basic_info"]["TICKER"] == "2330"
        and result["basic_info"]["NAME"] == "台積電"
        and result["basic_info"]["TARGET_PRICE"] == 1500.0,
    )
    financial_columns = set(REGISTRY["schemas"]["financial_data"])
    vdf_rows = vdf_records_to_financial_rows([{"ticker": "2330.TW", "period": "2024", "revenue": "2,000", "eps": "20", "unit": "million"}], file_id="F1")
    check(
        "full_pipeline_financial_data_contract",
        len(result["financial_data"]) == 2
        and all(financial_columns.issubset(row) for row in result["financial_data"])
        and {row["dataName"] for row in vdf_rows} == {"revenue", "eps"},
    )
    repeated = process_report(fixture)
    check("deterministic_result_digest", result["digest"] == repeated["digest"] and stable_json(result) == stable_json(repeated))
    source_path = Path(__file__).resolve()
    before = sha256_file(source_path)
    with tempfile.TemporaryDirectory(prefix="via_vrn_logic_selftest_") as temporary_dir:
        artifacts = write_outputs(result, temporary_dir, formats=("json", "csv", "sqlite"))
        expected_names = {f"{DEFAULT_OUTPUT_STEM_EVIDENCE}.json", f"{DEFAULT_OUTPUT_STEM_BASIC}.csv", f"{DEFAULT_OUTPUT_STEM_FINANCIAL}.csv", DEFAULT_SQLITE_NAME}
        observed_names = {Path(item["path"]).name for item in artifacts}
        connection = sqlite3.connect(Path(temporary_dir) / DEFAULT_SQLITE_NAME)
        try:
            db_counts = (
                connection.execute("SELECT COUNT(*) FROM stock_report_basic_info").fetchone()[0],
                connection.execute("SELECT COUNT(*) FROM stock_report_financial_data").fetchone()[0],
            )
        finally:
            connection.close()
        batch_root = Path(temporary_dir) / "batch-input"
        batch_root.mkdir()
        (batch_root / "A.pdf").write_bytes(b"%PDF-1.4\nfixture\n")
        (batch_root / "B.pdf").write_bytes(b"%PDF-1.4\nfixture\n")
        batch_summary = process_batch_reports(
            batch_root,
            output_directory=Path(temporary_dir) / "batch-output",
            mode="audit",
            formats=("json", "csv", "sqlite"),
        )
        batch_ok = (
            batch_summary["status"] == "YELLOW"
            and batch_summary["counts"]["discovered"] == 2
            and batch_summary["counts"]["unique"] == 1
            and batch_summary["counts"]["duplicates"] == 1
            and (Path(temporary_dir) / "batch-output" / DEFAULT_BATCH_CHECKPOINT_NAME).is_file()
        )
    after = sha256_file(source_path)
    imports = {node.names[0].name.split(".")[0] for node in ast.walk(ast.parse(source_path.read_text(encoding="utf-8"))) if isinstance(node, ast.Import) and node.names}
    imports |= {node.module.split(".")[0] for node in ast.walk(ast.parse(source_path.read_text(encoding="utf-8"))) if isinstance(node, ast.ImportFrom) and node.module}
    forbidden_imports = imports.intersection({"requests", "httpx", "aiohttp", "urllib3", "socket"})
    check("output_atomicity_batch_resume_and_offline_safety", observed_names == expected_names and db_counts == (1, 2) and batch_ok and before == after and not forbidden_imports)

    passed = sum(1 for _, ok, _ in checks if ok)
    failed = len(checks) - passed
    if verbose:
        print(f"[VIA][VRN][十六檢] START path={Path(__file__).resolve()}")
        for index, (name, ok, detail) in enumerate(checks, start=1):
            marker = "OK" if ok else "FAIL"
            suffix = f" · {detail}" if detail else ""
            print(f"[VIA][VRN][十六檢] {marker} {index}/16 — {name}{suffix}")
        print(f"[計] 十六檢 OK {passed} · FAIL {failed}")
    return 0 if failed == 0 and len(checks) == 16 else 1


run_selftest = selftest


# =============================================================================
# def 09 IN-FILE INDEPENDENT ACCEPTANCE MATRIX
# =============================================================================

def run_acceptance_tests(verbose: bool = True) -> int:
    """Run a second 16-check matrix independent from ``selftest`` reporting."""
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, condition: Any, detail: str = "") -> None:
        checks.append((name, bool(condition), detail))

    source_path = Path(__file__).resolve()
    before = sha256_file(source_path)
    check("source_readable_and_stable", source_path.is_file() and before == sha256_file(source_path))
    check("version_and_worldline", MODULE_VERSION == "3.2.0" and WORLDLINE == "WL-MAIN")
    check("offline_and_explicit_writer", MODULE_META["network_default"] is False and MODULE_META["installer_writer"] == "explicit_apply_only")
    check("schema_registry", set(("basic_info", "financial_data", "identity", "batch_matrix")).issubset(REGISTRY["schemas"]) and len(REGISTRY["schemas"]["basic_info"]) >= 35)
    identity = parse_filename("CTBC-2330台積電-買進-TP1500-20260914.pdf", market_hint="TWSE")
    check(
        "filename_segmentation",
        tokenize_filename("CTBC-2330台積電_20260914.pdf") == ["CTBC", "2330", "台積電", "20260914"]
        and identity["TICKER"] == "2330"
        and identity["YFINANCE_TICKER"] == "2330.TW"
        and identity["BLOOMBERG_TICKER"] == "2330 TT"
        and identity["NAME"] == "台積電",
    )
    check("twse_tpex_ticker", extract_ticker("2330.TW") == "2330" and infer_market("3324.TWO", "3324") == "TPEX")
    check("active_etf_ticker", extract_active_etf_ticker("00980A") == "00980A" and resolve_company_name("2330") == "台積電")
    check("date_variants", extract_report_date("民國115年09月14日") == "2026-09-14" and extract_report_date("CTBC260914") == "2026-09-14")
    check(
        "broker_rating_target",
        canonicalize_broker("中信投顧")["key"] == "CTBC"
        and canonicalize_rating("Overweight") == "BUY"
        and extract_target_price("目標價 1,500") == 1500.0
        and BRIKER_DICT is BROKER_DICT
        and set(RATING_LIST) == set(RATING_DICT),
    )
    conflict = reconcile_evidence({"source": "filename", "ticker": "2330"}, {"source": "first_page", "ticker": "2317"})
    check("conflict_fail_closed", conflict["status"] == "RED" and "ticker" in conflict["blocking"])
    check("accounting_negative_and_unit", parse_financial_value("(1,234.50) 百萬元") == (-1234.5, "million"))
    restored = restore_financial_table(
        {"page": 5, "tableIndex": 2, "engine": "fixture", "rows": [["項目", "2023A", "2024E"], ["營收", "1,000", "1,200"], ["EPS", "10.5", "12.0"]]},
        file_id="F1",
    )
    check("atomic_row_and_dedup", restored["audit"]["decision"] == "PASS" and len(restored["rows"]) == 4 and all(row["tableId"] for row in restored["rows"]))
    formula_rows = [
        normalize_financial_row({"item": "營收", "period": "2024", "value": 1000, "unit": "million"}),
        normalize_financial_row({"item": "毛利", "period": "2024", "value": 400, "unit": "million"}),
        normalize_financial_row({"item": "營業利益", "period": "2024", "value": 200, "unit": "million"}),
    ]
    formula_result = validate_financial_formulas(formula_rows)
    vdf_fixture = vdf_records_to_financial_rows([{"ticker": "2330.TW", "period": "2024", "revenue": "2,000", "eps": "20", "unit": "million"}], file_id="F1")
    check("formula_consistency", len(formula_result) == 2 and all(item["status"] == "PASS" for item in formula_result) and {row["dataName"] for row in vdf_fixture} == {"revenue", "eps"})
    fixture = {
        "fileId": "DOC001",
        "filename": "CTBC-2330-台積電-20260914-買進.pdf",
        "firstPageText": "台積電 2330 TT 中信投顧 買進 目標價: 1,500 2026/09/14",
        "official": {"companyName": "台積電", "ticker": "2330", "source": "official"},
        "financialRows": [{"item": "營收", "period": "1Q25E", "value": "(1,234.50) 百萬元", "unit": "百萬元"}],
    }
    first_result = process_report(fixture)
    basic_required = set(REGISTRY["schemas"]["basic_info"])
    financial_required = set(REGISTRY["schemas"]["financial_data"])
    check(
        "pipeline_schema",
        basic_required.issubset(first_result["basic_info"])
        and all(financial_required.issubset(row) for row in first_result["financial_data"])
        and first_result["basic_info"]["NAME"] == "台積電"
        and first_result["basic_info"]["TARGET_PRICE"] == 1500.0,
    )
    second_result = process_report(json.loads(stable_json(fixture)))
    check("pipeline_determinism", first_result["digest"] == second_result["digest"] and stable_json(first_result) == stable_json(second_result))
    tree = ast.parse(source_path.read_text(encoding="utf-8-sig"), filename=str(source_path))
    imports = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imports |= {
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    forbidden = imports.intersection({"requests", "httpx", "aiohttp", "urllib3", "socket"})
    with tempfile.TemporaryDirectory(prefix="via_vrn_acceptance_") as root:
        database = write_sqlite_database(first_result, Path(root) / DEFAULT_SQLITE_NAME)
        connection = sqlite3.connect(database)
        try:
            database_ok = connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok" and connection.execute("SELECT COUNT(*) FROM stock_report_basic_info").fetchone()[0] == 1
        finally:
            connection.close()
    check("deployment_and_offline_boundary", callable(deploy_self) and callable(process_pdf_report) and callable(process_batch_reports) and callable(validate_batch_output_contract) and database_ok and not forbidden and before == sha256_file(source_path))

    passed = sum(1 for _, ok, _ in checks if ok)
    failed = len(checks) - passed
    if verbose:
        print(f"[VIA][VRN][外部契約十六檢] START path={source_path}")
        for index, (name, ok, detail) in enumerate(checks, start=1):
            suffix = f" · {detail}" if detail else ""
            print(f"[VIA][VRN][外部契約十六檢] {'OK' if ok else 'FAIL'} {index}/16 — {name}{suffix}")
        print(f"[計] 外部契約十六檢 OK {passed} · FAIL {failed}")
    return 0 if len(checks) == DEFAULT_REQUIRED_CHECKS and failed == 0 else 1


# =============================================================================
# def 10 GUARDED AUDIT / ATOMIC INSTALL / ROLLBACK
# =============================================================================

def _deployment_row(section: str, check_name: str, decision: str, detail: Any = "") -> dict[str, str]:
    return {
        "section": normalize_text(section),
        "check": normalize_text(check_name),
        "decision": normalize_text(decision).upper(),
        "detail": normalize_text(detail),
    }


def _run_python_check(script: Path, flag: str, working_directory: Path, timeout_seconds: int) -> dict[str, Any]:
    working_directory.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"
    try:
        completed = subprocess.run(
            [sys.executable, str(script), flag],
            cwd=str(working_directory),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
            env=environment,
        )
        return {
            "exit_code": completed.returncode,
            "timed_out": False,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "combined": (completed.stdout + "\n" + completed.stderr).strip(),
        }
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout.decode("utf-8", "replace") if isinstance(error.stdout, bytes) else error.stdout or ""
        stderr = error.stderr.decode("utf-8", "replace") if isinstance(error.stderr, bytes) else error.stderr or ""
        return {"exit_code": 124, "timed_out": True, "stdout": stdout, "stderr": stderr, "combined": (stdout + "\n" + stderr).strip()}


def _run_pair(script: Path, flag: str, root: Path, timeout_seconds: int) -> tuple[dict[str, Any], dict[str, Any], bool]:
    trial_1 = root / "trial_1"
    trial_2 = root / "trial_2"
    trial_1.mkdir(parents=True, exist_ok=True)
    trial_2.mkdir(parents=True, exist_ok=True)
    first = _run_python_check(script, flag, trial_1, timeout_seconds)
    second = _run_python_check(script, flag, trial_2, timeout_seconds)
    deterministic = first["stdout"].strip() == second["stdout"].strip()
    return first, second, deterministic


def _selftest_pass(run: Mapping[str, Any]) -> bool:
    expected = f"[計] 十六檢 OK {DEFAULT_REQUIRED_CHECKS} · FAIL 0"
    return run.get("exit_code") == 0 and run.get("timed_out") is False and expected in str(run.get("stdout", ""))


def _acceptance_pass(run: Mapping[str, Any]) -> bool:
    expected = f"[計] 外部契約十六檢 OK {DEFAULT_REQUIRED_CHECKS} · FAIL 0"
    return run.get("exit_code") == 0 and run.get("timed_out") is False and expected in str(run.get("stdout", ""))


def _copy_atomic(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    staged = destination.with_name(f".{destination.name}.{os.getpid()}.{stable_digest(str(source))[:12]}.tmp")
    shutil.copy2(source, staged)
    if sha256_file(staged) != sha256_file(source):
        raise RuntimeError("ATOMIC_STAGE_HASH_MISMATCH")
    os.replace(staged, destination)


def _write_deployment_reports(report_directory: Path, gate: str, context: Mapping[str, Any], rows: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    report_directory.mkdir(parents=True, exist_ok=True)
    summary_path = report_directory / "VRN_LOGIC_ALLINONE_SUMMARY.json"
    matrix_path = report_directory / "VRN_LOGIC_ALLINONE_MATRIX.csv"
    html_path = report_directory / "VRN_LOGIC_ALLINONE_REPORT.html"
    summary = {
        "schema": INSTALL_REPORT_SCHEMA,
        "gate": gate,
        "context": dict(context),
        "matrix": list(rows),
    }
    atomic_write_text(summary_path, stable_json(summary, pretty=True) + "\n")
    atomic_write_csv(matrix_path, rows, ("section", "check", "decision", "detail"))
    body = "\n".join(
        "<tr>"
        f"<td>{html_escape(str(row.get('section', '')))}</td>"
        f"<td>{html_escape(str(row.get('check', '')))}</td>"
        f"<td class=\"{html_escape(str(row.get('decision', '')).lower())}\">{html_escape(str(row.get('decision', '')))}</td>"
        f"<td>{html_escape(str(row.get('detail', '')))}</td>"
        "</tr>"
        for row in rows
    )
    html = f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><title>VIA VRN Logic All-in-One</title>
<style>body{{font-family:Segoe UI,Arial,sans-serif;margin:28px;background:#0b1220;color:#e5e7eb}}table{{width:100%;border-collapse:collapse;background:#111827}}th,td{{border:1px solid #334155;padding:8px;vertical-align:top;font-size:12px;overflow-wrap:anywhere}}th{{background:#1e293b}}.pass{{color:#34d399}}.warn,.info{{color:#fbbf24}}.block{{color:#f87171}}</style></head>
<body><h1>VIA · VRN Logic All-in-One v{MODULE_VERSION}</h1><p>{html_escape(gate)}</p><table><thead><tr><th>Section</th><th>Check</th><th>Decision</th><th>Detail</th></tr></thead><tbody>{body}</tbody></table></body></html>"""
    atomic_write_text(html_path, html)
    return [
        {"path": str(summary_path), "sha256": sha256_file(summary_path)},
        {"path": str(matrix_path), "sha256": sha256_file(matrix_path)},
        {"path": str(html_path), "sha256": sha256_file(html_path)},
    ]


def deploy_self(
    mode: str = DEFAULT_INSTALL_MODE,
    *,
    repo_root: str | os.PathLike[str] | None = None,
    project_relative: str = DEFAULT_PROJECT_RELATIVE,
    target_relative: str = DEFAULT_TARGET_RELATIVE,
    report_root: str | os.PathLike[str] | None = None,
    timeout_seconds: int = DEFAULT_INSTALL_TIMEOUT_SECONDS,
) -> int:
    """Audit or atomically install this file as the canonical ``vrn_logic.py``."""
    previous_directory = Path.cwd()
    selected_mode = normalize_text(mode).lower()
    if selected_mode not in {"audit", "apply"}:
        raise ValueError("mode must be audit or apply")
    source = Path(__file__).resolve()
    resolved_repo = Path(repo_root).expanduser().resolve() if repo_root else (Path.home() / DEFAULT_REPO_RELATIVE).resolve()
    project_root = (resolved_repo / project_relative).resolve()
    target = (project_root / target_relative).resolve()
    resolved_report_root = Path(report_root).expanduser().resolve() if report_root else (Path.home() / DEFAULT_REPORT_RELATIVE).resolve()
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    report_directory = resolved_report_root / f"VRN_LOGIC_ALLINONE_{run_id}"
    backup = report_directory / "backup" / "vrn_logic.py"
    rows: list[dict[str, str]] = []
    gate = "RED / VRN_LOGIC_ALLINONE_UNINITIALIZED"
    exit_code = 1
    mutation = False
    target_preexisted = target.is_file()
    original_hash = sha256_file(target) if target_preexisted else ""
    context: dict[str, Any] = {
        "module_version": MODULE_VERSION,
        "mode": selected_mode,
        "source": str(source),
        "source_sha256": sha256_file(source),
        "repo_root": str(resolved_repo),
        "project_root": str(project_root),
        "target": str(target),
        "target_preexisted": target_preexisted,
        "original_sha256": original_hash,
        "installed_sha256": "",
        "python": sys.executable,
        "mutation": 0,
        "rollback": 0,
        "network": 0,
        "db_ssot_write": 0,
        "promotion": 0,
    }

    def add(section: str, name: str, decision: str, detail: Any = "") -> None:
        rows.append(_deployment_row(section, name, decision, detail))

    try:
        if not project_root.is_dir():
            raise FileNotFoundError(f"PROJECT_ROOT_NOT_FOUND：{project_root}")
        os.chdir(project_root)
        add("MODULE", "Target environment", "PASS", project_root)
        add("MODULE", "Source SHA256 lock", "PASS", context["source_sha256"])

        candidate_first, candidate_second, candidate_equal = _run_pair(source, "--selftest", report_directory / "sandbox" / "candidate", timeout_seconds)
        for index, run in enumerate((candidate_first, candidate_second), start=1):
            passed = _selftest_pass(run)
            add("ENGINE", f"Candidate selftest trial {index}", "PASS" if passed else "BLOCK", f"Exit={run['exit_code']};TimedOut={run['timed_out']};16of16={passed}")
            if not passed:
                raise RuntimeError(f"CANDIDATE_SELFTEST_TRIAL_{index}_FAILED\n{run['combined']}")
        add("ENGINE", "Candidate deterministic output", "PASS" if candidate_equal else "BLOCK", f"Equal={candidate_equal}")
        if not candidate_equal:
            raise RuntimeError("CANDIDATE_SELFTEST_NONDETERMINISTIC")

        candidate_acceptance = _run_python_check(source, "--acceptance-test", report_directory / "sandbox" / "candidate" / "acceptance", timeout_seconds)
        acceptance_ok = _acceptance_pass(candidate_acceptance)
        add("FUNCTION-LIB", "In-file independent sixteen checks", "PASS" if acceptance_ok else "BLOCK", f"Exit={candidate_acceptance['exit_code']};16of16={acceptance_ok}")
        if not acceptance_ok:
            raise RuntimeError(f"CANDIDATE_ACCEPTANCE_FAILED\n{candidate_acceptance['combined']}")

        if target_preexisted:
            original_contract = inspect_python_contract(target)
            candidate_contract = inspect_python_contract(source)
            comparison = compare_contracts(original_contract, candidate_contract)
            missing_functions = ",".join(comparison["missing_functions"])
            missing_classes = ",".join(comparison["missing_classes"])
            add("FUNCTION-LIB", "Existing public API compatibility", "PASS" if comparison["compatible"] else "BLOCK", f"MissingFunctions=[{missing_functions}];MissingClasses=[{missing_classes}]")
            if not comparison["compatible"]:
                raise RuntimeError(f"PUBLIC_API_COMPATIBILITY_BLOCKED：FUNCTIONS=[{missing_functions}] CLASSES=[{missing_classes}]")
        else:
            add("MODULE", "Existing target", "INFO", "Target absent; Apply may create only the declared vrn_logic.py path.")

        if selected_mode == "audit":
            gate = "YELLOW / VRN_LOGIC_ALLINONE_16_OF_16_AUDIT_ONLY"
            exit_code = 0
            add("OTHERS", "Mutation", "INFO", "0; audit mode")
        else:
            if target_preexisted and source != target:
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, backup)
                backup_ok = sha256_file(backup) == original_hash
                add("OTHERS", "Hash-locked backup", "PASS" if backup_ok else "BLOCK", backup)
                if not backup_ok:
                    raise RuntimeError("BACKUP_HASH_MISMATCH")

            if not (target_preexisted and sha256_file(target) == context["source_sha256"]):
                _copy_atomic(source, target)
                mutation = True
                context["mutation"] = 1
            installed_hash = sha256_file(target)
            context["installed_sha256"] = installed_hash
            installed_hash_ok = installed_hash == context["source_sha256"]
            add("MODULE", "Installed SHA256", "PASS" if installed_hash_ok else "BLOCK", installed_hash)
            if not installed_hash_ok:
                raise RuntimeError("INSTALLED_HASH_MISMATCH")

            installed_first, installed_second, installed_equal = _run_pair(target, "--selftest", report_directory / "sandbox" / "installed", timeout_seconds)
            for index, run in enumerate((installed_first, installed_second), start=1):
                passed = _selftest_pass(run)
                add("ENGINE", f"Installed selftest trial {index}", "PASS" if passed else "BLOCK", f"Exit={run['exit_code']};TimedOut={run['timed_out']};16of16={passed}")
                if not passed:
                    raise RuntimeError(f"INSTALLED_SELFTEST_TRIAL_{index}_FAILED\n{run['combined']}")
            add("ENGINE", "Installed deterministic output", "PASS" if installed_equal else "BLOCK", f"Equal={installed_equal}")
            if not installed_equal:
                raise RuntimeError("INSTALLED_SELFTEST_NONDETERMINISTIC")
            installed_acceptance = _run_python_check(target, "--acceptance-test", report_directory / "sandbox" / "installed" / "acceptance", timeout_seconds)
            installed_acceptance_ok = _acceptance_pass(installed_acceptance)
            add("FUNCTION-LIB", "Installed independent sixteen checks", "PASS" if installed_acceptance_ok else "BLOCK", f"Exit={installed_acceptance['exit_code']};16of16={installed_acceptance_ok}")
            if not installed_acceptance_ok:
                raise RuntimeError(f"INSTALLED_ACCEPTANCE_FAILED\n{installed_acceptance['combined']}")
            gate = "GREEN / VRN_LOGIC_ALLINONE_16_OF_16_APPLIED"
            exit_code = 0
            add("OTHERS", "Final health", "PASS", "Internal 16/16 x4; independent 16/16 x2; deterministic; API-compatible")
    except Exception as error:
        add("OTHERS", "Blocking condition", "BLOCK", f"{type(error).__name__}: {error}")
        if mutation:
            try:
                if target_preexisted and backup.is_file():
                    _copy_atomic(backup, target)
                    rollback_ok = sha256_file(target) == original_hash
                elif not target_preexisted and target.is_file():
                    target.unlink()
                    rollback_ok = not target.exists()
                else:
                    rollback_ok = False
                context["rollback"] = 1 if rollback_ok else 0
                add("OTHERS", "Automatic rollback", "PASS" if rollback_ok else "BLOCK", f"Restored={rollback_ok}")
                gate = "RED / VRN_LOGIC_ALLINONE_APPLY_BLOCKED_ROLLED_BACK" if rollback_ok else "RED / VRN_LOGIC_ALLINONE_ROLLBACK_FAILED"
            except Exception as rollback_error:
                add("OTHERS", "Automatic rollback", "BLOCK", f"{type(rollback_error).__name__}: {rollback_error}")
                gate = "RED / VRN_LOGIC_ALLINONE_ROLLBACK_FAILED"
        else:
            gate = "RED / VRN_LOGIC_ALLINONE_BLOCKED_NO_MUTATION"
        context["traceback_tail"] = traceback.format_exc().splitlines()[-8:]
        exit_code = 1

    context["gate"] = gate
    context["finished_at"] = datetime.now().astimezone().isoformat()
    try:
        artifacts = _write_deployment_reports(report_directory, gate, context, rows)
        context["report_artifacts"] = artifacts
    except Exception as report_error:
        os.chdir(previous_directory)
        print(f"RED / VRN_LOGIC_REPORT_WRITE_FAILED · {type(report_error).__name__}: {report_error}", file=sys.stderr)
        return 1
    os.chdir(previous_directory)
    print(gate)
    print(f"Output: {report_directory}")
    return exit_code


# =============================================================================
# def 11 CLI
# =============================================================================

def parse_formats(value: str) -> tuple[str, ...]:
    selected = tuple(dict.fromkeys(part.strip().lower() for part in value.split(",") if part.strip()))
    unsupported = sorted(set(selected) - {"json", "csv", "parquet", "sqlite", "duckdb"})
    if unsupported:
        raise ValueError(f"unsupported formats: {','.join(unsupported)}")
    return selected or DEFAULT_FORMATS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VIA VRN unified report logic engine")
    parser.add_argument("--selftest", action="store_true", help="run the deterministic sixteen-check suite")
    parser.add_argument("--acceptance-test", action="store_true", help="run the independent in-file sixteen-check suite")
    parser.add_argument("--install", choices=("audit", "apply"), help="audit or atomically install this file as vrn_logic.py")
    parser.add_argument("--repo-root", type=Path, help="repository root; default is USERPROFILE/movies-dataset")
    parser.add_argument("--project-relative", default=DEFAULT_PROJECT_RELATIVE, help="project path below repository root")
    parser.add_argument("--target-relative", default=DEFAULT_TARGET_RELATIVE, help="target path below project root")
    parser.add_argument("--report-root", type=Path, help="report directory; default is USERPROFILE/VIA_Reports")
    parser.add_argument("--timeout", type=int, default=DEFAULT_INSTALL_TIMEOUT_SECONDS, help="seconds allowed per isolated test")
    parser.add_argument("--input", type=Path, help="input JSON payload")
    parser.add_argument("--pdf", type=Path, help="PDF report for filename, first-page and annual-table extraction")
    parser.add_argument("--batch-root", type=Path, help="directory of PDF reports for resumable audit/staging")
    parser.add_argument("--batch-mode", choices=("audit", "stage"), default="audit", help="audit hashes only or stage parsed results")
    parser.add_argument("--checkpoint", type=Path, help="optional batch checkpoint path")
    parser.add_argument("--batch-max-files", type=int, default=DEFAULT_BATCH_MAX_FILES, help="fail closed above this PDF count")
    parser.add_argument("--non-recursive", action="store_true", help="scan only the batch root")
    parser.add_argument("--fresh", action="store_true", help="reprocess unchanged successful reports")
    parser.add_argument("--retry-failed", action="store_true", help="retry unchanged failed or quarantined reports")
    parser.add_argument("--fail-fast", action="store_true", help="stop staging after the first isolated failure")
    parser.add_argument("--vdf-source", type=Path, help="local VDF file or database/output directory used as external evidence")
    parser.add_argument("--company-dict", type=Path, help="optional ticker/name SSOT JSON or CSV")
    parser.add_argument("--market-hint", default="", help="TWSE/TPEX hint when suffix evidence is unavailable")
    parser.add_argument("--max-pages", type=int, default=DEFAULT_PDF_MAX_PAGES, help="0 means every PDF page")
    parser.add_argument("--output-dir", type=Path, help="output directory; omitted means stdout only")
    parser.add_argument("--verify-output-dir", type=Path, help="read-only validation of the nine governed STAGE outputs")
    parser.add_argument("--formats", default=",".join(DEFAULT_FORMATS), help="json,csv,parquet,sqlite,duckdb")
    parser.add_argument("--inspect-contract", type=Path, help="inspect a Python module's public AST contract")
    parser.add_argument("--compare-contract", type=Path, help="compare this candidate with an existing module")
    parser.add_argument("--pretty", action="store_true", help="pretty JSON output")
    parser.add_argument("--version", action="store_true", help="print module version")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.version:
        print(f"{MODULE_ID} {MODULE_VERSION}")
        return 0
    if args.selftest:
        return selftest(verbose=True)
    if args.acceptance_test:
        return run_acceptance_tests(verbose=True)
    if args.install:
        return deploy_self(
            args.install,
            repo_root=args.repo_root,
            project_relative=args.project_relative,
            target_relative=args.target_relative,
            report_root=args.report_root,
            timeout_seconds=args.timeout,
        )
    if args.inspect_contract:
        print(stable_json(inspect_python_contract(args.inspect_contract), pretty=True))
        return 0
    if args.compare_contract:
        original = inspect_python_contract(args.compare_contract)
        candidate = inspect_python_contract(Path(__file__).resolve())
        comparison = compare_contracts(original, candidate)
        print(stable_json({"original": original, "candidate": candidate, "comparison": comparison}, pretty=True))
        return 0 if comparison["compatible"] else 3
    if args.verify_output_dir:
        result = validate_batch_output_contract(args.verify_output_dir)
        print(stable_json(result, pretty=args.pretty))
        return 0 if result["status"] == "PASS" else 6
    if args.batch_root:
        if not args.output_dir:
            raise ValueError("--output-dir is required with --batch-root")
        result = process_batch_reports(
            args.batch_root,
            output_directory=args.output_dir,
            mode=args.batch_mode,
            vdf_source=args.vdf_source,
            company_dict_path=args.company_dict,
            market_hint=args.market_hint,
            max_pages=args.max_pages,
            formats=parse_formats(args.formats),
            recursive=not args.non_recursive,
            resume=not args.fresh,
            retry_failed=args.retry_failed,
            fail_fast=args.fail_fast,
            max_files=args.batch_max_files,
            checkpoint_path=args.checkpoint,
        )
        print(stable_json(result, pretty=args.pretty))
        return 0 if result["status"] != "RED" else 5
    if args.pdf:
        result = process_pdf_report(
            args.pdf,
            vdf_source=args.vdf_source,
            company_dict_path=args.company_dict,
            market_hint=args.market_hint,
            max_pages=args.max_pages,
        )
        if args.output_dir:
            result = dict(result)
            result["artifacts"] = write_outputs(result, args.output_dir, formats=parse_formats(args.formats))
        print(stable_json(result, pretty=args.pretty))
        return 0 if result["validation"]["status"] != "RED" else 4
    if not args.input:
        build_parser().print_help()
        return 2
    payload = json.loads(args.input.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, Mapping):
        raise TypeError("input JSON root must be an object")
    result = process_report(payload)
    if args.output_dir:
        artifacts = write_outputs(result, args.output_dir, formats=parse_formats(args.formats))
        result = dict(result)
        result["artifacts"] = artifacts
    print(stable_json(result, pretty=args.pretty))
    return 0 if result["validation"]["status"] != "RED" else 4


if __name__ == "__main__":
    raise SystemExit(main())
