#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA / VRN report logic engine — all-in-one edition.

Single-file, standard-library-first implementation for filename, first-page and
financial-page normalization, evidence reconciliation, deterministic output,
sixteen-check acceptance testing and guarded atomic installation.  The module
is intentionally offline and has no import-time writes.
"""
from __future__ import annotations

# =============================================================================
# def 00 PARAMETERS / SSOT BINDINGS
# =============================================================================

MODULE_ID = "VIA-VRN-LOGIC-001"
MODULE_NAME = "vrn_logic"
MODULE_VERSION = "2.1.0"
SCHEMA_VERSION = "VIA.VRN.Logic.v2.1"
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
DEFAULT_FORMATS = ("json", "csv")
DEFAULT_INSTALL_MODE = "audit"
DEFAULT_REPO_RELATIVE = "movies-dataset"
DEFAULT_PROJECT_RELATIVE = "VeritasIntelligenceAnalytics"
DEFAULT_TARGET_RELATIVE = "via/vrn_logic.py"
DEFAULT_REPORT_RELATIVE = "VIA_Reports"
DEFAULT_INSTALL_TIMEOUT_SECONDS = 90
DEFAULT_REQUIRED_CHECKS = 16
INSTALL_REPORT_SCHEMA = "VIA.VRN.Logic.AllInOneInstall.v2.1"
SOURCE_PRIORITY = ("official", "financial_page", "first_page", "filename", "unknown")
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

BROKER_ALIASES = {
    "CTBC": ("CTBC", "中信", "中國信託", "中信投顧", "中信證券"),
    "CATHAY": ("CATHAY", "國泰", "國泰證券", "國泰投顧"),
    "FUBON": ("FUBON", "富邦", "富邦證券", "富邦投顧"),
    "YUANTA": ("YUANTA", "元大", "元大證券", "元大投顧"),
    "MEGA": ("MEGA", "兆豐", "兆豐證券", "兆豐投顧"),
    "KGI": ("KGI", "凱基", "凱基證券", "凱基投顧"),
    "SINO": ("SINO", "永豐", "永豐金", "永豐金證券", "永豐投顧"),
    "TAISHIN": ("TAISHIN", "台新", "台新證券", "台新投顧"),
    "UBS": ("UBS", "瑞銀"),
    "MS": ("MORGAN STANLEY", "MORGANSTANLEY", "大摩", "摩根士丹利"),
    "GS": ("GOLDMAN SACHS", "GOLDMANSACHS", "高盛"),
    "CITI": ("CITI", "CITIGROUP", "花旗"),
    "JPM": ("JPM", "J.P. MORGAN", "JP MORGAN", "摩根大通"),
    "DAIWA": ("DAIWA", "大和"),
    "NOMURA": ("NOMURA", "野村"),
    "MACQUARIE": ("MACQUARIE", "麥格理"),
}

BROKER_NAMES = {
    "CTBC": "中信證券",
    "CATHAY": "國泰證券",
    "FUBON": "富邦證券",
    "YUANTA": "元大證券",
    "MEGA": "兆豐證券",
    "KGI": "凱基證券",
    "SINO": "永豐金證券",
    "TAISHIN": "台新證券",
    "UBS": "瑞銀",
    "MS": "摩根士丹利",
    "GS": "高盛",
    "CITI": "花旗",
    "JPM": "摩根大通",
    "DAIWA": "大和",
    "NOMURA": "野村",
    "MACQUARIE": "麥格理",
}

RATING_ALIASES = {
    "BUY": ("BUY", "STRONG BUY", "OVERWEIGHT", "OUTPERFORM", "買進", "強力買進", "加碼", "優於大盤", "增持"),
    "HOLD": ("HOLD", "NEUTRAL", "MARKET PERFORM", "中立", "持有", "續抱", "與大盤持平"),
    "SELL": ("SELL", "UNDERWEIGHT", "UNDERPERFORM", "賣出", "減碼", "低配", "劣於大盤"),
    "NOT_RATED": ("NOT RATED", "NOT-RATED", "NR", "未評等", "未評級"),
}

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

REGISTRY = {
    "module": MODULE_META,
    "ssot": SSOT_CONTRACT,
    "schemas": {
        "basic_info": (
            "fileId", "fileName", "reportType", "ticker", "market",
            "yfinanceTicker", "bloombergTicker", "tickerKind", "companyName",
            "broker", "brokerAbbr", "reportDate", "reportCode", "language",
            "period", "pages", "issuer", "rating", "ratingCat",
            "validationStatus", "validationRisk", "status",
        ),
        "financial_data": (
            "fileId", "fileName", "category", "statement", "item", "dataName",
            "period", "value", "unit", "confidence", "source", "status",
            "grade", "defects",
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
}


# =============================================================================
# def 01 IMPORTS — stdlib only, kept after parameters by project convention
# =============================================================================

import argparse
import ast
import csv
import hashlib
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
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
    short = re.search(r"(?:CTBC|早報)[-_ ]?(\d{2})(\d{2})(\d{2})(?!\d)", text, re.I)
    if short:
        yy = int(short.group(1))
        year = 2000 + yy if yy <= 50 else 1900 + yy
        return valid_date(year, int(short.group(2)), int(short.group(3)))
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


def parse_filename(filename: Any, market_hint: str = "") -> dict[str, Any]:
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
    return {
        "fileName": Path(text).name,
        "tokens": tokenize_filename(text),
        "ticker": ticker,
        "market": market,
        "yfinanceTicker": forms["yfinance"],
        "bloombergTicker": forms["bloomberg"],
        "tickerKind": "active_etf" if etf_ticker else "tw_equity" if ticker else "",
        "reportDate": report_date,
        "brokerAbbr": broker["key"],
        "broker": broker["name"],
        "rating": rating,
        "reportType": detect_report_type(text),
    }


# =============================================================================
# def 04 FIRST-PAGE / FINANCIAL LOGIC
# =============================================================================

def extract_target_price(value: Any) -> float | None:
    text = normalize_text(value)
    patterns = (
        r"(?:目標價(?:格)?|target\s*price|\bTP\b)\s*[:：=]?[\s]*(?:NT\$?|TWD|新台幣)?\s*([0-9][0-9,]*(?:\.[0-9]+)?)",
        r"(?:NT\$?|TWD)\s*([0-9][0-9,]*(?:\.[0-9]+)?)\s*(?:目標價|target)",
    )
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            number = float(match.group(1).replace(",", ""))
            if MIN_TARGET_PRICE <= number < MAX_TARGET_PRICE:
                return number
    return None


def parse_first_page(text: Any, market_hint: str = "") -> dict[str, Any]:
    normalized = normalize_text(text)
    parsed = parse_filename(normalized, market_hint=market_hint)
    parsed.update(
        {
            "source": "first_page",
            "targetPrice": extract_target_price(normalized),
            "textLength": len(normalized),
            "language": "zh-Hant" if re.search(r"[\u4e00-\u9fff]", normalized) else "en",
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
    multiplier = UNIT_MULTIPLIERS_TO_MILLION.get(detected_unit.casefold(), 1.0)
    return round(number * multiplier, 10), "million" if detected_unit and detected_unit not in {"元", "twd", "ntd"} else detected_unit


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
    fields = {key: reconcile_field(key, sources) for key in ("ticker", "reportDate", "brokerAbbr", "rating", "targetPrice")}
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
    pages: int = 1,
) -> tuple[dict[str, Any], dict[str, Any]]:
    filename_evidence = parse_filename(filename, market_hint=market_hint)
    filename_evidence["source"] = "filename"
    first_page_evidence = parse_first_page(first_page_text, market_hint=market_hint) if first_page_text else None
    validation = reconcile_evidence(filename_evidence, first_page_evidence, official=official)
    values = {key: row["value"] for key, row in validation["fields"].items()}
    ticker = normalize_text(values.get("ticker") or filename_evidence.get("ticker"))
    market = infer_market(filename + " " + first_page_text, ticker, market_hint)
    forms = expand_ticker(ticker, market)
    broker_key = normalize_text(values.get("brokerAbbr") or filename_evidence.get("brokerAbbr"))
    report_date = normalize_text(values.get("reportDate") or filename_evidence.get("reportDate"))
    company = normalize_text((official or {}).get("companyName", ""))
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
        "rating": normalize_text(values.get("rating") or filename_evidence.get("rating")) or "—",
        "ratingCat": normalize_text(values.get("rating") or filename_evidence.get("rating")) or "—",
        "validationStatus": "PHASE2_OK" if risk == "GREEN" else "REVIEW_REQUIRED" if risk == "YELLOW" else "FAIL_CLOSED",
        "validationRisk": risk,
        "status": "ok" if risk == "GREEN" else "warn" if risk == "YELLOW" else "bad",
    }
    basic["reportCode"] = report_code(basic)
    return basic, validation


def process_report(payload: Mapping[str, Any]) -> dict[str, Any]:
    filename = normalize_text(payload.get("filename", payload.get("fileName", "")))
    if not filename:
        raise ValueError("filename is required")
    file_id = normalize_text(payload.get("file_id", payload.get("fileId", "")))
    first_page_text = normalize_text(payload.get("first_page_text", payload.get("firstPageText", "")))
    market_hint = normalize_text(payload.get("market", payload.get("market_hint", "")))
    official = payload.get("official") if isinstance(payload.get("official"), Mapping) else None
    basic, validation = build_basic_info(
        file_id=file_id,
        filename=filename,
        file_size=int(payload.get("file_size", payload.get("fileSize", 1)) or 0),
        first_page_text=first_page_text,
        market_hint=market_hint,
        official=official,
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
# def 07 OUTPUT
# =============================================================================

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
    return artifacts


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
        set(("basic_info", "financial_data")).issubset(REGISTRY["schemas"])
        and all(resolve_alias(alias) is globals()[canonical] for alias, canonical in ALIASES.items()),
    )
    tokens = tokenize_filename("CTBC-2330台積電_20260914.pdf")
    check("filename_tokenization", "CTBC" in tokens and "2330" in tokens and "台積電" in tokens and "20260914" in tokens, str(tokens))
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
    check("filename_first_page_consensus", consensus["fields"]["ticker"]["status"] == "MATCH" and consensus["status"] in {"GREEN", "YELLOW"})
    conflict_first = dict(first_evidence)
    conflict_first["ticker"] = "2317"
    conflict = reconcile_evidence(filename_evidence, conflict_first)
    check("ticker_conflict_fail_closed", conflict["status"] == "RED" and conflict["blocking"] == ["ticker"])
    rows = [
        normalize_financial_row({"item": "營收", "period": "2024", "value": "1,000", "unit": "百萬元", "confidence": 0.80, "source": "first_page"}, file_id="F1"),
        normalize_financial_row({"item": "Revenue", "period": "2024", "value": "1,000", "unit": "million", "confidence": 0.95, "source": "financial_page"}, file_id="F1"),
    ]
    deduped, duplicate_count = deduplicate_financial_rows(rows)
    check("financial_atomicity_and_dedup", duplicate_count == 1 and len(deduped) == 1 and deduped[0]["grade"] == "V")
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
    check("full_pipeline_basic_info_contract", basic_columns.issubset(result["basic_info"]) and result["basic_info"]["ticker"] == "2330")
    financial_columns = set(REGISTRY["schemas"]["financial_data"])
    check("full_pipeline_financial_data_contract", len(result["financial_data"]) == 2 and all(financial_columns.issubset(row) for row in result["financial_data"]))
    repeated = process_report(fixture)
    check("deterministic_result_digest", result["digest"] == repeated["digest"] and stable_json(result) == stable_json(repeated))
    source_path = Path(__file__).resolve()
    before = sha256_file(source_path)
    with tempfile.TemporaryDirectory(prefix="via_vrn_logic_selftest_") as temporary_dir:
        artifacts = write_outputs(result, temporary_dir, formats=("json", "csv"))
        expected_names = {f"{DEFAULT_OUTPUT_STEM_EVIDENCE}.json", f"{DEFAULT_OUTPUT_STEM_BASIC}.csv", f"{DEFAULT_OUTPUT_STEM_FINANCIAL}.csv"}
        observed_names = {Path(item["path"]).name for item in artifacts}
    after = sha256_file(source_path)
    imports = {node.names[0].name.split(".")[0] for node in ast.walk(ast.parse(source_path.read_text(encoding="utf-8"))) if isinstance(node, ast.Import) and node.names}
    imports |= {node.module.split(".")[0] for node in ast.walk(ast.parse(source_path.read_text(encoding="utf-8"))) if isinstance(node, ast.ImportFrom) and node.module}
    forbidden_imports = imports.intersection({"requests", "httpx", "aiohttp", "urllib3", "socket"})
    check("output_atomicity_and_offline_safety", observed_names == expected_names and before == after and not forbidden_imports)

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
    check("version_and_worldline", MODULE_VERSION == "2.1.0" and WORLDLINE == "WL-MAIN")
    check("offline_and_explicit_writer", MODULE_META["network_default"] is False and MODULE_META["installer_writer"] == "explicit_apply_only")
    check("schema_registry", len(REGISTRY["schemas"]["basic_info"]) >= 20 and len(REGISTRY["schemas"]["financial_data"]) >= 14)
    check("filename_segmentation", tokenize_filename("CTBC-2330台積電_20260914.pdf") == ["CTBC", "2330", "台積電", "20260914"])
    check("twse_tpex_ticker", extract_ticker("2330.TW") == "2330" and infer_market("3324.TWO", "3324") == "TPEX")
    check("active_etf_ticker", extract_active_etf_ticker("00980A") == "00980A")
    check("date_variants", extract_report_date("民國115年09月14日") == "2026-09-14" and extract_report_date("CTBC260914") == "2026-09-14")
    check("broker_rating_target", canonicalize_broker("中信投顧")["key"] == "CTBC" and canonicalize_rating("Overweight") == "BUY" and extract_target_price("目標價 1,500") == 1500.0)
    conflict = reconcile_evidence({"source": "filename", "ticker": "2330"}, {"source": "first_page", "ticker": "2317"})
    check("conflict_fail_closed", conflict["status"] == "RED" and "ticker" in conflict["blocking"])
    check("accounting_negative_and_unit", parse_financial_value("(1,234.50) 百萬元") == (-1234.5, "million"))
    duplicate_rows = [
        normalize_financial_row({"item": "營收", "period": "2024", "value": 1000, "unit": "million", "confidence": 0.8}),
        normalize_financial_row({"item": "Revenue", "period": "2024", "value": "1,000", "unit": "百萬元", "confidence": 0.9}),
    ]
    deduped, duplicate_count = deduplicate_financial_rows(duplicate_rows)
    check("atomic_row_and_dedup", duplicate_count == 1 and len(deduped) == 1 and deduped[0]["grade"] == "V")
    formula_rows = [
        normalize_financial_row({"item": "營收", "period": "2024", "value": 1000, "unit": "million"}),
        normalize_financial_row({"item": "毛利", "period": "2024", "value": 400, "unit": "million"}),
        normalize_financial_row({"item": "營業利益", "period": "2024", "value": 200, "unit": "million"}),
    ]
    formula_result = validate_financial_formulas(formula_rows)
    check("formula_consistency", len(formula_result) == 2 and all(item["status"] == "PASS" for item in formula_result))
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
    check("pipeline_schema", basic_required.issubset(first_result["basic_info"]) and all(financial_required.issubset(row) for row in first_result["financial_data"]))
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
    check("deployment_and_offline_boundary", callable(deploy_self) and not forbidden and before == sha256_file(source_path))

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
    unsupported = sorted(set(selected) - {"json", "csv", "parquet"})
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
    parser.add_argument("--output-dir", type=Path, help="output directory; omitted means stdout only")
    parser.add_argument("--formats", default=",".join(DEFAULT_FORMATS), help="json,csv,parquet")
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
