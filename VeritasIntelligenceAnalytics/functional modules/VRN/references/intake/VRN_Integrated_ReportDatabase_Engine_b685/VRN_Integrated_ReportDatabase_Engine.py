# -*- coding: utf-8 -*-
"""
VRN Integrated Report Database Engine
=====================================
單檔整合版：Filename 擷取 + First Page Anchor + TWSE/TPEX Name 驗證 + BasicInfo/FinancialData 入庫。

核心輸出：
    - StockReportBasicInfo.parquet           必選，累積式更新
    - StockReportFinancialData.parquet       必選，累積式更新

可選輸出：
    - CSV：UTF-8 BOM，供 Excel 人工檢查
    - JSON：UTF-8，供 UI / Evidence / SSOT
    - DuckDB：供 SQL / Dashboard
    - Google Sheet：保留接口，需自行提供 gspread 憑證

設計原則：
    1. Parquet 是唯一主資料庫。
    2. CSV / JSON / DuckDB / Google Sheet 全部從 Parquet 派生。
    3. Filename 粗抓候選；首頁資訊區精抓；TWSE/TPEX/SSOT 回填正式 Name。
    4. 4 碼數字優先作 TW_TICKER；6 碼以上優先判斷日期。
    5. 支援 (20)260131、260131、20260131、1140822、114/08/22 等日期。
    6. StockReportBasicInfo 一份報告一列；StockReportFinancialData 一份報告多列 long format。

建議執行：
    python VRN_Integrated_ReportDatabase_Engine.py --input "C:/Reports/incoming" --output "C:/VRN_DB" --csv --json --duckdb
    python VRN_Integrated_ReportDatabase_Engine.py --self-test
"""

# ============================================================
# def 00_GLOBAL_PARAMETERS：所有參數集中於此區
# ============================================================

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import math
import os
import re
import sys
import time
import traceback
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.request import Request, urlopen

SCHEMA_VERSION = "VRN_SCHEMA_20260921_001"
DEFAULT_RUN_ID_PREFIX = "VRN_RUN"
DEFAULT_OUTPUT_DIR = "./vrn_output"
DEFAULT_INPUT_DIR = "./incoming"

BASICINFO_PARQUET_NAME = "StockReportBasicInfo.parquet"
FINANCIALDATA_PARQUET_NAME = "StockReportFinancialData.parquet"
BASICINFO_CSV_NAME = "StockReportBasicInfo.csv"
FINANCIALDATA_CSV_NAME = "StockReportFinancialData.csv"
BASICINFO_JSON_NAME = "StockReportBasicInfo.json"
FINANCIALDATA_JSON_NAME = "StockReportFinancialData.json"
DUCKDB_NAME = "StockReport.duckdb"
HTML_MATRIX_NAME = "VRN_BatchReport.html"
BATCH_SUMMARY_JSON_NAME = "VRN_BatchSummary.json"
BATCH_MATRIX_CSV_NAME = "VRN_BatchMatrix.csv"
BATCH_CHECKPOINT_JSON_NAME = "VRN_BatchCheckpoint.json"

# TWSE/TPEX 公司基本資料 OpenAPI。若未連網或端點變更，仍可使用本地 SSOT CSV。
TWSE_PROFILE_API_URL = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"
TPEX_PROFILE_API_URL = "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O"
HTTP_TIMEOUT_SECONDS = 30
HTTP_USER_AGENT = "Mozilla/5.0 VRN-Integrated-Engine/1.0"
ENABLE_ONLINE_NAME_TABLE_BY_DEFAULT = False

# 使用者常用本地 SSOT 路徑，可在 CLI 覆蓋。
DEFAULT_TICKER_SSOT_CSV = ""
DEFAULT_BROKER_SSOT_CSV = ""
DEFAULT_RATING_SSOT_CSV = ""

# Filename 與文字切割符號。
TOKEN_SEPARATOR_REGEX = re.compile(
    r"[\s\t\r\n\-_–—+,.，。、:：;；/\\|()（）\[\]【】{}<>《》〈〉\"'`~!！?？@#$%^&*=]+"
)
MIXED_TOKEN_REGEX = re.compile(r"\d+|[A-Za-z]+|[\u3400-\u4DBF\u4E00-\u9FFF]+")
CHINESE_REGEX = re.compile(r"^[\u3400-\u4DBF\u4E00-\u9FFF]+$")
ENGLISH_REGEX = re.compile(r"^[A-Za-z]+$")
NUMBER_REGEX = re.compile(r"^\d+$")

# Ticker Regex：一般公司 / yfinance / Bloomberg / 報告文字。
TW_STOCK_TICKER_REGEX = re.compile(r"^([1-9]\d{3})$")
TW_YFINANCE_TICKER_REGEX = re.compile(r"\b([1-9]\d{3})\.(TW|TWO)\b", re.IGNORECASE)
TW_BBG_TICKER_REGEX = re.compile(r"\b([1-9]\d{3})\s*(TT)\b", re.IGNORECASE)
TW_TEXT_TICKER_REGEX = re.compile(r"(?:代號|股票代號|Ticker|Code|Stock\s*Code)?\s*[:：]?\s*\b([1-9]\d{3})\b", re.IGNORECASE)

# 日期 Regex。
DATE_YYYYMMDD_REGEX = re.compile(r"(?<!\d)((?:19|20)\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])(?!\d)")
DATE_YYMMDD_REGEX = re.compile(r"(?<!\d)(\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])(?!\d)")
DATE_ROC_YYYMMDD_REGEX = re.compile(r"(?<!\d)(1\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])(?!\d)")
DATE_SPLIT_REGEX = re.compile(
    r"((?:19|20)\d{2}|1\d{2})[./\-年](0?[1-9]|1[0-2])[./\-月](0?[1-9]|[12]\d|3[01])日?"
)
DATE_SENTENCE_END_REGEX = re.compile(r"[。．\.！!？?]$")

# 首頁區域切割比例。
FIRST_PAGE_TOP_RATIO = 0.42
FIRST_PAGE_LEFT_RATIO = 0.45
FIRST_PAGE_RIGHT_RATIO = 0.55
FIRST_PAGE_MAX_PAGES_FOR_TEXT = 3
PDF_TABLE_MAX_PAGES = 80

# BasicInfo 欄位。
BASICINFO_COLUMNS = [
    "FileID",
    "ReportID",
    "SourceFileName",
    "SourcePath",
    "FileHash",
    "TW_TICKER",
    "YF_TICKER",
    "Market",
    "Name",
    "CompanyNameCandidate",
    "Broker",
    "BrokerCandidate",
    "ReportDate",
    "ReportTitle",
    "ReportType",
    "Language",
    "Analyst",
    "Department",
    "Rating",
    "RatingChange",
    "TargetPrice",
    "CurrentPrice",
    "UpsideDownsidePct",
    "InvestmentThesis",
    "Industry",
    "SubIndustry",
    "MarketCap",
    "ShareCapital",
    "Chairman",
    "GeneralManager",
    "Spokesperson",
    "ConfidenceScore",
    "ValidationStatus",
    "ValidationIssues",
    "EvidenceJson",
    "CreatedAt",
    "UpdatedAt",
    "RunID",
    "SchemaVersion",
]

# FinancialData 欄位，採 long format。
FINANCIALDATA_COLUMNS = [
    "FinancialRowID",
    "FileID",
    "ReportID",
    "TW_TICKER",
    "YF_TICKER",
    "Name",
    "ReportDate",
    "Broker",
    "PeriodType",
    "FiscalYear",
    "FiscalQuarter",
    "PeriodLabelRaw",
    "EstimateFlag",
    "MetricCategory",
    "MetricName",
    "MetricNameRaw",
    "Value",
    "ValueRaw",
    "Unit",
    "Currency",
    "Scale",
    "YoY",
    "QoQ",
    "PER",
    "PBR",
    "EV_EBITDA",
    "DividendYield",
    "ROE",
    "ROA",
    "Revenue",
    "GrossProfit",
    "GrossMargin",
    "OperatingProfit",
    "OperatingMargin",
    "NetIncome",
    "EPS",
    "TotalAssets",
    "TotalLiabilities",
    "Equity",
    "BookValuePerShare",
    "OperatingCashFlow",
    "Capex",
    "FreeCashFlow",
    "PageNumber",
    "TableID",
    "RowIndex",
    "ColumnIndex",
    "SourceText",
    "ConfidenceScore",
    "ValidationStatus",
    "ValidationIssues",
    "CreatedAt",
    "UpdatedAt",
    "RunID",
    "SchemaVersion",
]

# 去重鍵。
BASICINFO_UPSERT_KEYS = ["ReportID"]
FINANCIALDATA_UPSERT_KEYS = ["FinancialRowID"]

# 評等同義字，可再由 SSOT CSV 擴充。
DEFAULT_RATING_ALIASES = {
    "BUY": ["BUY", "買進", "買入", "強力買進", "OUTPERFORM", "增持", "ADD", "OVERWEIGHT", "OW", "買進評等"],
    "HOLD": ["HOLD", "中立", "持有", "NEUTRAL", "EQUALWEIGHT", "EW", "MARKET PERFORM", "觀望"],
    "SELL": ["SELL", "賣出", "減持", "UNDERPERFORM", "UNDERWEIGHT", "UW", "降低持股"],
    "NOT_RATED": ["未評等", "NOT RATED", "NR"],
}

# 報告類型同義字。
REPORT_TYPE_ALIASES = {
    "INITIATION": ["初次評等", "初評", "Initiation", "Initiating Coverage"],
    "UPDATE": ["更新", "Update", "Company Update", "研究報告"],
    "FLASH": ["速報", "Flash", "快報", "訪談", "法說", "Earnings Flash"],
    "INDUSTRY": ["產業", "Industry", "Sector"],
}

# 財務指標標準化。
METRIC_ALIASES = {
    "Revenue": ["Revenue", "Sales", "Net Sales", "營收", "營業收入", "銷貨收入", "合併營收", "Net Revenue"],
    "GrossProfit": ["Gross Profit", "毛利", "營業毛利"],
    "GrossMargin": ["Gross Margin", "GPM", "毛利率"],
    "OperatingProfit": ["Operating Profit", "OP", "Operating Income", "營業利益", "營業淨利"],
    "OperatingMargin": ["Operating Margin", "OPM", "營益率", "營業利益率"],
    "PretaxIncome": ["Pretax Income", "PBT", "稅前淨利", "稅前利益"],
    "NetIncome": ["Net Income", "NI", "PAT", "稅後淨利", "淨利", "歸屬母公司淨利"],
    "EPS": ["EPS", "每股盈餘", "每股稅後盈餘", "每股獲利"],
    "PER": ["PER", "P/E", "PE", "本益比"],
    "PBR": ["PBR", "P/B", "PB", "股價淨值比"],
    "EV_EBITDA": ["EV/EBITDA", "EV EBITDA"],
    "DividendYield": ["Dividend Yield", "殖利率", "股息殖利率"],
    "ROE": ["ROE", "股東權益報酬率"],
    "ROA": ["ROA", "資產報酬率"],
    "TotalAssets": ["Total Assets", "總資產"],
    "TotalLiabilities": ["Total Liabilities", "總負債"],
    "Equity": ["Equity", "Shareholders Equity", "股東權益", "淨值"],
    "BookValuePerShare": ["BVPS", "Book Value Per Share", "每股淨值"],
    "OperatingCashFlow": ["Operating Cash Flow", "CFO", "營業現金流", "營運現金流"],
    "Capex": ["Capex", "Capital Expenditure", "資本支出"],
    "FreeCashFlow": ["Free Cash Flow", "FCF", "自由現金流"],
    "MarketCap": ["Market Cap", "市值"],
    "TargetPrice": ["Target Price", "TP", "目標價"],
    "CurrentPrice": ["Current Price", "現價", "股價"],
}

METRIC_CATEGORY_MAP = {
    "Revenue": "Income Statement",
    "GrossProfit": "Income Statement",
    "GrossMargin": "Income Statement",
    "OperatingProfit": "Income Statement",
    "OperatingMargin": "Income Statement",
    "PretaxIncome": "Income Statement",
    "NetIncome": "Income Statement",
    "EPS": "Income Statement",
    "PER": "Valuation",
    "PBR": "Valuation",
    "EV_EBITDA": "Valuation",
    "DividendYield": "Valuation",
    "ROE": "Valuation",
    "ROA": "Valuation",
    "TotalAssets": "Balance Sheet",
    "TotalLiabilities": "Balance Sheet",
    "Equity": "Balance Sheet",
    "BookValuePerShare": "Balance Sheet",
    "OperatingCashFlow": "Cash Flow",
    "Capex": "Cash Flow",
    "FreeCashFlow": "Cash Flow",
    "MarketCap": "Basic Info",
    "TargetPrice": "Valuation",
    "CurrentPrice": "Valuation",
}

# CSV 編碼。
CSV_ENCODING_FOR_EXCEL = "utf-8-sig"
JSON_ENCODING = "utf-8"

# 信心分數權重。
CONFIDENCE_WEIGHTS = {
    "filename_ticker": 0.18,
    "first_page_ticker": 0.22,
    "exchange_name": 0.24,
    "report_date": 0.12,
    "broker": 0.10,
    "rating_or_target": 0.08,
    "title_or_text": 0.06,
}

# ============================================================
# def 01_OPTIONAL_IMPORTS
# ============================================================

def require_pandas():
    try:
        import pandas as pd  # type: ignore
        return pd
    except Exception as exc:
        raise RuntimeError("缺少 pandas。請先安裝：pip install pandas pyarrow") from exc


def optional_import_pyarrow_available() -> bool:
    try:
        import pyarrow  # noqa: F401
        return True
    except Exception:
        return False


def optional_import_duckdb():
    try:
        import duckdb  # type: ignore
        return duckdb
    except Exception:
        return None


def optional_import_pdfplumber():
    try:
        import pdfplumber  # type: ignore
        return pdfplumber
    except Exception:
        return None


def optional_import_fitz():
    try:
        import fitz  # type: ignore
        return fitz
    except Exception:
        return None

# ============================================================
# def 02_BASIC_UTILS
# ============================================================

def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def make_run_id(prefix: str = DEFAULT_RUN_ID_PREFIX) -> str:
    return f"{prefix}_{datetime.now().strftime('%Y%m%dT%H%M%S')}_{os.getpid()}"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def normalize_unicode_text(text: Any) -> str:
    if text is None:
        return ""
    value = str(text)
    value = unicodedata.normalize("NFKC", value)
    value = value.replace("\u3000", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def file_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def stable_hash(parts: Sequence[Any], size: int = 16) -> str:
    raw = "||".join(normalize_unicode_text(p) for p in parts)
    return hashlib.sha256(raw.encode("utf-8", errors="ignore")).hexdigest()[:size]


def safe_json_dumps(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, sort_keys=True, default=str)
    except Exception:
        return json.dumps({"error": "json_dump_failed", "repr": repr(obj)}, ensure_ascii=False)


def read_json_file(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json_file(path: Path, data: Any) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    text = normalize_unicode_text(value)
    if text == "" or text in {"-", "--", "NA", "N/A", "nan", "None"}:
        return None
    text = text.replace(",", "")
    negative = False
    if text.startswith("(") and text.endswith(")"):
        negative = True
        text = text[1:-1]
    text = text.replace("%", "").replace("x", "").replace("X", "")
    m = re.search(r"[-+]?\d+(?:\.\d+)?", text)
    if not m:
        return None
    try:
        num = float(m.group(0))
        return -num if negative else num
    except Exception:
        return None


def safe_int(value: Any) -> Optional[int]:
    num = safe_float(value)
    if num is None or math.isnan(num):
        return None
    return int(num)


def first_non_empty(values: Iterable[Any]) -> str:
    for value in values:
        text = normalize_unicode_text(value)
        if text:
            return text
    return ""


def scan_input_files(input_dir: Path) -> List[Path]:
    if input_dir.is_file():
        return [input_dir]
    patterns = ["**/*.pdf", "**/*.PDF"]
    files: List[Path] = []
    for pattern in patterns:
        files.extend(input_dir.glob(pattern))
    unique = sorted(set(files), key=lambda p: str(p).lower())
    return unique

# ============================================================
# def 03_FILENAME_TOKENIZATION_AND_DATE
# ============================================================

def split_mixed_token(token: str) -> List[str]:
    token = normalize_unicode_text(token)
    if not token:
        return []
    return [x for x in MIXED_TOKEN_REGEX.findall(token) if x]


def tokenize_filename(filename: str) -> Dict[str, Any]:
    stem = Path(filename).stem
    normalized = normalize_unicode_text(stem)
    rough = TOKEN_SEPARATOR_REGEX.split(normalized)
    tokens: List[str] = []
    for item in rough:
        item = normalize_unicode_text(item)
        if not item:
            continue
        parts = split_mixed_token(item)
        if parts:
            tokens.extend(parts)
        else:
            tokens.append(item)
    tokens = [normalize_unicode_text(x) for x in tokens if normalize_unicode_text(x)]
    number_tokens = [x for x in tokens if NUMBER_REGEX.match(x)]
    chinese_tokens = [x for x in tokens if CHINESE_REGEX.match(x)]
    english_tokens = [x for x in tokens if ENGLISH_REGEX.match(x)]
    mixed_tokens = [x for x in tokens if x not in number_tokens and x not in chinese_tokens and x not in english_tokens]
    return {
        "source_stem": stem,
        "normalized": normalized,
        "tokens": tokens,
        "number_tokens": number_tokens,
        "chinese_tokens": chinese_tokens,
        "english_tokens": english_tokens,
        "mixed_tokens": mixed_tokens,
    }


def parse_date_from_yyyymmdd(raw: str) -> Optional[str]:
    text = normalize_unicode_text(raw)
    m = DATE_YYYYMMDD_REGEX.search(text)
    if not m:
        return None
    year = int(m.group(1))
    month = int(m.group(2))
    day = int(m.group(3))
    return validate_date_parts(year, month, day)


def parse_date_from_yymmdd(raw: str) -> Optional[str]:
    text = normalize_unicode_text(raw)
    m = DATE_YYMMDD_REGEX.search(text)
    if not m:
        return None
    yy = int(m.group(1))
    year = 2000 + yy
    month = int(m.group(2))
    day = int(m.group(3))
    return validate_date_parts(year, month, day)


def parse_date_from_roc_yyyymmdd(raw: str) -> Optional[str]:
    text = normalize_unicode_text(raw)
    m = DATE_ROC_YYYMMDD_REGEX.search(text)
    if not m:
        return None
    roc_year = int(m.group(1))
    if not (80 <= roc_year <= 150):
        return None
    year = roc_year + 1911
    month = int(m.group(2))
    day = int(m.group(3))
    return validate_date_parts(year, month, day)


def parse_date_from_split_text(raw: str) -> Optional[str]:
    text = normalize_unicode_text(raw)
    m = DATE_SPLIT_REGEX.search(text)
    if not m:
        return None
    year_value = int(m.group(1))
    if 80 <= year_value <= 150:
        year = year_value + 1911
    else:
        year = year_value
    month = int(m.group(2))
    day = int(m.group(3))
    return validate_date_parts(year, month, day)


def validate_date_parts(year: int, month: int, day: int) -> Optional[str]:
    try:
        dt = datetime(year, month, day)
        if not (1990 <= dt.year <= 2099):
            return None
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return None


def parse_date_any(raw: str) -> Optional[str]:
    text = normalize_unicode_text(raw)
    if not text:
        return None
    for parser in [parse_date_from_split_text, parse_date_from_yyyymmdd, parse_date_from_roc_yyyymmdd, parse_date_from_yymmdd]:
        parsed = parser(text)
        if parsed:
            return parsed
    return None


def parse_date_candidates_from_number_tokens(number_tokens: Sequence[str]) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    for idx, token in enumerate(number_tokens):
        token = normalize_unicode_text(token)
        parsed = None
        kind = ""
        if len(token) == 8:
            parsed = parse_date_from_yyyymmdd(token)
            kind = "YYYYMMDD"
        elif len(token) == 7:
            parsed = parse_date_from_roc_yyyymmdd(token)
            kind = "ROC_YYYMMDD"
        elif len(token) == 6:
            parsed = parse_date_from_yymmdd(token)
            kind = "YYMMDD"
        if parsed:
            candidates.append({"raw": token, "date": parsed, "kind": kind, "index": idx})

    # 支援 (20)260131 被切成 20 + 260131 的情況。
    for idx in range(len(number_tokens) - 1):
        left = normalize_unicode_text(number_tokens[idx])
        right = normalize_unicode_text(number_tokens[idx + 1])
        if left in {"19", "20"} and len(right) == 6:
            merged = left + right
            parsed = parse_date_from_yyyymmdd(merged)
            if parsed:
                candidates.append({"raw": f"{left}+{right}", "date": parsed, "kind": "PREFIX_YYYYMMDD", "index": idx})
    return candidates


def choose_best_report_date(filename_candidates: List[Dict[str, Any]], first_page_text: str) -> Tuple[str, List[Dict[str, Any]]]:
    all_candidates = list(filename_candidates)
    for m in DATE_SPLIT_REGEX.finditer(first_page_text or ""):
        parsed = parse_date_any(m.group(0))
        if parsed:
            all_candidates.append({"raw": m.group(0), "date": parsed, "kind": "FIRST_PAGE_SPLIT", "index": -1})
    for m in DATE_YYYYMMDD_REGEX.finditer(first_page_text or ""):
        parsed = parse_date_any(m.group(0))
        if parsed:
            all_candidates.append({"raw": m.group(0), "date": parsed, "kind": "FIRST_PAGE_YYYYMMDD", "index": -1})
    # filename 優先，其次 first page；取第一個合理值。
    return (all_candidates[0]["date"] if all_candidates else "", all_candidates)

# ============================================================
# def 04_SSOT_LOADERS_AND_NAME_TABLE
# ============================================================

def read_csv_rows_flexible(path: Path) -> List[Dict[str, str]]:
    if not path or not path.exists():
        return []
    encodings = ["utf-8-sig", "utf-8", "big5", "cp950"]
    last_exc: Optional[Exception] = None
    for enc in encodings:
        try:
            with path.open("r", encoding=enc, newline="") as f:
                reader = csv.DictReader(f)
                return [{normalize_unicode_text(k): normalize_unicode_text(v) for k, v in row.items()} for row in reader]
        except Exception as exc:
            last_exc = exc
            continue
    raise RuntimeError(f"CSV 讀取失敗：{path}，最後錯誤：{last_exc}")


def pick_row_value(row: Dict[str, Any], candidates: Sequence[str]) -> str:
    lowered = {normalize_unicode_text(k).lower(): v for k, v in row.items()}
    for key in candidates:
        if key in row and normalize_unicode_text(row.get(key)):
            return normalize_unicode_text(row.get(key))
        lk = key.lower()
        if lk in lowered and normalize_unicode_text(lowered.get(lk)):
            return normalize_unicode_text(lowered.get(lk))
    return ""


def load_local_ticker_ssot(path: Optional[Path]) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}
    if not path or not path.exists():
        return lookup
    rows = read_csv_rows_flexible(path)
    for row in rows:
        code = pick_row_value(row, ["TW_TICKER", "Ticker", "Code", "證券代號", "股票代號", "公司代號", "代號"])
        code_match = re.search(r"([1-9]\d{3})", code)
        if not code_match:
            continue
        ticker = code_match.group(1)
        name = pick_row_value(row, ["Name", "證券名稱", "公司名稱", "公司簡稱", "簡稱", "中文簡稱"])
        market = pick_row_value(row, ["Market", "市場", "上市櫃", "Exchange"])
        yf = pick_row_value(row, ["YF_TICKER", "YFinance", "Yahoo", "yfinance"])
        english = pick_row_value(row, ["EnglishName", "English", "英文名稱", "英文簡稱"])
        industry = pick_row_value(row, ["Industry", "產業", "產業別"])
        if not yf and market.upper() in {"TWSE", "上市"}:
            yf = f"{ticker}.TW"
        if not yf and market.upper() in {"TPEX", "OTC", "上櫃"}:
            yf = f"{ticker}.TWO"
        lookup[ticker] = {
            "TW_TICKER": ticker,
            "YF_TICKER": yf,
            "Market": normalize_market_name(market),
            "Name": name,
            "EnglishName": english,
            "Industry": industry,
            "source": str(path),
        }
    return lookup


def normalize_market_name(value: str) -> str:
    text = normalize_unicode_text(value).upper()
    if text in {"TWSE", "上市", "上市公司", "TSE"}:
        return "TWSE"
    if text in {"TPEX", "OTC", "上櫃", "櫃買", "上櫃公司"}:
        return "TPEX"
    return normalize_unicode_text(value)


def http_get_json(url: str, timeout: int = HTTP_TIMEOUT_SECONDS) -> Any:
    req = Request(url, headers={"User-Agent": HTTP_USER_AGENT, "Accept": "application/json,text/plain,*/*"})
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    text = raw.decode("utf-8", errors="replace")
    return json.loads(text)


def normalize_exchange_profile_row(row: Dict[str, Any], market: str, source_url: str) -> Optional[Dict[str, Any]]:
    code = pick_row_value(row, ["公司代號", "Code", "code", "SecuritiesCode", "股票代號", "有價證券代號"])
    m = re.search(r"([1-9]\d{3})", code)
    if not m:
        return None
    ticker = m.group(1)
    name = pick_row_value(row, ["公司簡稱", "公司名稱", "證券名稱", "Name", "CompanyName", "簡稱"])
    full_name = pick_row_value(row, ["公司名稱", "FullName", "Full Name", "發行公司名稱"])
    english = pick_row_value(row, ["英文簡稱", "英文名稱", "EnglishName", "English Abbreviation"])
    industry = pick_row_value(row, ["產業別", "Industry", "IndustryCode"])
    chairman = pick_row_value(row, ["董事長", "Chairman"])
    general_manager = pick_row_value(row, ["總經理", "General Manager", "GeneralManager"])
    spokesperson = pick_row_value(row, ["發言人", "Spokesperson"])
    yf = f"{ticker}.TW" if market == "TWSE" else f"{ticker}.TWO"
    return {
        "TW_TICKER": ticker,
        "YF_TICKER": yf,
        "Market": market,
        "Name": name or full_name,
        "FullName": full_name,
        "EnglishName": english,
        "Industry": industry,
        "Chairman": chairman,
        "GeneralManager": general_manager,
        "Spokesperson": spokesperson,
        "source": source_url,
    }


def fetch_exchange_name_table(enable_online: bool) -> Dict[str, Dict[str, Any]]:
    if not enable_online:
        return {}
    lookup: Dict[str, Dict[str, Any]] = {}
    endpoints = [(TWSE_PROFILE_API_URL, "TWSE"), (TPEX_PROFILE_API_URL, "TPEX")]
    for url, market in endpoints:
        try:
            data = http_get_json(url)
            if isinstance(data, dict):
                rows = data.get("data") or data.get("items") or data.get("result") or []
            else:
                rows = data
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                item = normalize_exchange_profile_row(row, market, url)
                if item:
                    lookup[item["TW_TICKER"]] = item
        except Exception as exc:
            print(f"[WARN] 線上名稱表抓取失敗：{market} {url} -> {exc}", file=sys.stderr)
    return lookup


def merge_ticker_lookups(*lookups: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    for lookup in lookups:
        for ticker, row in lookup.items():
            if ticker not in merged:
                merged[ticker] = dict(row)
            else:
                for key, value in row.items():
                    if normalize_unicode_text(value):
                        merged[ticker][key] = value
    return merged


def load_broker_alias_ssot(path: Optional[Path]) -> Dict[str, List[str]]:
    alias: Dict[str, List[str]] = {}
    if path and path.exists():
        rows = read_csv_rows_flexible(path)
        for row in rows:
            broker = pick_row_value(row, ["Broker", "broker", "券商", "標準券商", "Canonical"])
            names = pick_row_value(row, ["Alias", "alias", "同義字", "別名", "Aliases"])
            if not broker:
                continue
            parts = [broker] + [normalize_unicode_text(x) for x in re.split(r"[|,，;；/]+", names) if normalize_unicode_text(x)]
            alias[broker] = sorted(set(parts), key=len, reverse=True)
    if not alias:
        alias = default_broker_aliases()
    return alias


def default_broker_aliases() -> Dict[str, List[str]]:
    return {
        "KGI": ["KGI", "凱基", "凱基證券", "凱基投顧"],
        "Yuanta": ["Yuanta", "元大", "元大投顧", "元大證券"],
        "Fubon": ["Fubon", "富邦", "富邦投顧", "富邦證券"],
        "Cathay": ["Cathay", "國泰", "國泰證券", "國泰投顧"],
        "SinoPac": ["SinoPac", "永豐", "永豐金", "永豐投顧", "永豐金證券"],
        "Capital": ["Capital", "群益", "群益投顧", "群益證券"],
        "MasterLink": ["MasterLink", "元富", "元富投顧", "元富證券"],
        "Jih Sun": ["Jih Sun", "日盛", "日盛投顧", "日盛證券"],
        "Mega": ["Mega", "兆豐", "兆豐投顧", "兆豐證券"],
        "CTBC": ["CTBC", "中信", "中信投顧", "中國信託", "中信證券"],
        "Nomura": ["Nomura", "野村"],
        "Morgan Stanley": ["Morgan Stanley", "MS", "摩根士丹利"],
        "JPMorgan": ["JPMorgan", "J.P. Morgan", "JP Morgan", "摩根大通"],
        "Goldman Sachs": ["Goldman Sachs", "GS", "高盛"],
        "Citi": ["Citi", "Citigroup", "花旗"],
        "UBS": ["UBS", "瑞銀"],
        "CLSA": ["CLSA", "里昂"],
        "Macquarie": ["Macquarie", "麥格理"],
        "HSBC": ["HSBC", "匯豐"],
    }


def load_rating_alias_ssot(path: Optional[Path]) -> Dict[str, List[str]]:
    alias = {k: list(v) for k, v in DEFAULT_RATING_ALIASES.items()}
    if path and path.exists():
        rows = read_csv_rows_flexible(path)
        for row in rows:
            canonical = pick_row_value(row, ["Rating", "Canonical", "標準評等"])
            names = pick_row_value(row, ["Alias", "Aliases", "同義字", "別名"])
            if not canonical:
                continue
            parts = [canonical] + [normalize_unicode_text(x) for x in re.split(r"[|,，;；/]+", names) if normalize_unicode_text(x)]
            alias[canonical] = sorted(set(alias.get(canonical, []) + parts), key=len, reverse=True)
    return alias

# ============================================================
# def 05_PDF_FIRST_PAGE_AND_LAYOUT
# ============================================================

def extract_pdf_text_and_first_page_zones(pdf_path: Path) -> Dict[str, Any]:
    result = {
        "full_text": "",
        "first_page_text": "",
        "top_left_text": "",
        "top_center_text": "",
        "top_right_text": "",
        "first_page_repaired_sentences": [],
        "engine": "",
        "issues": [],
    }
    fitz = optional_import_fitz()
    if fitz is not None:
        try:
            doc = fitz.open(str(pdf_path))
            texts = []
            for page_idx in range(min(len(doc), FIRST_PAGE_MAX_PAGES_FOR_TEXT)):
                texts.append(doc[page_idx].get_text("text") or "")
            result["full_text"] = "\n".join(texts)
            if len(doc) > 0:
                page = doc[0]
                result["first_page_text"] = page.get_text("text") or ""
                blocks = page.get_text("blocks") or []
                width = float(page.rect.width)
                height = float(page.rect.height)
                zones = split_blocks_into_top_zones(blocks, width, height)
                result.update(zones)
                zone_lines = []
                for key in ["top_left_text", "top_center_text", "top_right_text"]:
                    zone_lines.extend(text_to_lines(result.get(key, "")))
                result["first_page_repaired_sentences"] = repair_sentences_until_period(zone_lines)
            result["engine"] = "PyMuPDF"
            doc.close()
            return result
        except Exception as exc:
            result["issues"].append(f"PyMuPDF failed: {exc}")

    pdfplumber = optional_import_pdfplumber()
    if pdfplumber is not None:
        try:
            with pdfplumber.open(str(pdf_path)) as pdf:
                texts = []
                for page_idx, page in enumerate(pdf.pages[:FIRST_PAGE_MAX_PAGES_FOR_TEXT]):
                    texts.append(page.extract_text() or "")
                    if page_idx == 0:
                        first_text = page.extract_text() or ""
                        result["first_page_text"] = first_text
                        result["top_left_text"] = first_text
                result["full_text"] = "\n".join(texts)
                result["first_page_repaired_sentences"] = repair_sentences_until_period(text_to_lines(result["first_page_text"]))
            result["engine"] = "pdfplumber"
            return result
        except Exception as exc:
            result["issues"].append(f"pdfplumber failed: {exc}")

    result["issues"].append("No PDF extraction engine available. Install PyMuPDF or pdfplumber.")
    return result


def split_blocks_into_top_zones(blocks: Sequence[Any], width: float, height: float) -> Dict[str, str]:
    left: List[Tuple[float, float, str]] = []
    center: List[Tuple[float, float, str]] = []
    right: List[Tuple[float, float, str]] = []
    top_limit = height * FIRST_PAGE_TOP_RATIO
    for block in blocks:
        try:
            x0, y0, x1, y1, text = float(block[0]), float(block[1]), float(block[2]), float(block[3]), str(block[4])
        except Exception:
            continue
        if y0 > top_limit:
            continue
        cleaned = normalize_unicode_text(text)
        if not cleaned:
            continue
        mid = (x0 + x1) / 2.0
        item = (y0, x0, cleaned)
        if mid <= width * FIRST_PAGE_LEFT_RATIO:
            left.append(item)
        elif mid >= width * FIRST_PAGE_RIGHT_RATIO:
            right.append(item)
        else:
            center.append(item)
    def join(items: List[Tuple[float, float, str]]) -> str:
        items = sorted(items, key=lambda x: (x[0], x[1]))
        return "\n".join(x[2] for x in items)
    return {
        "top_left_text": join(left),
        "top_center_text": join(center),
        "top_right_text": join(right),
    }


def text_to_lines(text: str) -> List[str]:
    raw_lines = str(text or "").splitlines()
    return [normalize_unicode_text(line) for line in raw_lines if normalize_unicode_text(line)]


def repair_sentences_until_period(lines: Sequence[str]) -> List[str]:
    repaired: List[str] = []
    buffer = ""
    for line in lines:
        line = normalize_unicode_text(line)
        if not line:
            continue
        if buffer:
            if should_join_without_space(buffer, line):
                buffer += line
            else:
                buffer += " " + line
        else:
            buffer = line
        if DATE_SENTENCE_END_REGEX.search(buffer) or len(buffer) >= 240:
            repaired.append(buffer.strip())
            buffer = ""
    if buffer:
        repaired.append(buffer.strip())
    return repaired


def should_join_without_space(left: str, right: str) -> bool:
    if not left or not right:
        return False
    return bool(CHINESE_REGEX.search(left[-1]) and CHINESE_REGEX.search(right[0]))

# ============================================================
# def 06_TICKER_BROKER_COMPANY_EXTRACTION
# ============================================================

def extract_filename_ticker_candidates(token_info: Dict[str, Any], ticker_lookup: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    for token in token_info.get("number_tokens", []):
        if TW_STOCK_TICKER_REGEX.match(token):
            exists = token in ticker_lookup if ticker_lookup else True
            candidates.append({"ticker": token, "raw": token, "source": "filename", "exists_in_ssot": exists})
    return candidates


def extract_text_ticker_candidates(text: str, source: str, ticker_lookup: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    seen = set()
    text = normalize_unicode_text(text)
    for regex, kind in [(TW_YFINANCE_TICKER_REGEX, "yfinance"), (TW_BBG_TICKER_REGEX, "bloomberg"), (TW_TEXT_TICKER_REGEX, "text")]:
        for m in regex.finditer(text):
            ticker = m.group(1)
            key = (ticker, kind, m.group(0))
            if key in seen:
                continue
            seen.add(key)
            exists = ticker in ticker_lookup if ticker_lookup else True
            candidates.append({
                "ticker": ticker,
                "raw": m.group(0),
                "source": source,
                "kind": kind,
                "exists_in_ssot": exists,
            })
    return candidates


def choose_canonical_ticker(filename_candidates: List[Dict[str, Any]], page_candidates: List[Dict[str, Any]], ticker_lookup: Dict[str, Dict[str, Any]]) -> Tuple[str, str, List[str]]:
    issues: List[str] = []
    score: Dict[str, float] = {}
    for c in filename_candidates:
        ticker = c.get("ticker", "")
        if not ticker:
            continue
        score[ticker] = score.get(ticker, 0) + 2.0
        if c.get("exists_in_ssot"):
            score[ticker] += 1.0
    for c in page_candidates:
        ticker = c.get("ticker", "")
        if not ticker:
            continue
        score[ticker] = score.get(ticker, 0) + 2.3
        if c.get("kind") in {"yfinance", "bloomberg"}:
            score[ticker] += 0.4
        if c.get("exists_in_ssot"):
            score[ticker] += 1.0
    if not score:
        return "", "", ["NO_TICKER_CANDIDATE"]
    sorted_scores = sorted(score.items(), key=lambda x: (-x[1], x[0]))
    ticker = sorted_scores[0][0]
    if len(sorted_scores) > 1 and sorted_scores[0][1] - sorted_scores[1][1] < 0.5:
        issues.append(f"TICKER_AMBIGUOUS:{sorted_scores[:3]}")
    if ticker_lookup and ticker not in ticker_lookup:
        issues.append(f"TICKER_NOT_IN_SSOT:{ticker}")
    row = ticker_lookup.get(ticker, {})
    yf = normalize_unicode_text(row.get("YF_TICKER", ""))
    if not yf:
        market = normalize_unicode_text(row.get("Market", ""))
        if market == "TWSE":
            yf = f"{ticker}.TW"
        elif market == "TPEX":
            yf = f"{ticker}.TWO"
    return ticker, yf, issues


def match_broker_from_tokens_and_text(chinese_tokens: Sequence[str], english_tokens: Sequence[str], text: str, broker_alias: Dict[str, List[str]]) -> Tuple[str, List[str], List[Dict[str, str]]]:
    haystacks = [normalize_unicode_text(x) for x in list(chinese_tokens) + list(english_tokens)]
    long_text = normalize_unicode_text(text)
    matches: List[Dict[str, str]] = []
    for broker, aliases in broker_alias.items():
        for a in aliases:
            alias = normalize_unicode_text(a)
            if not alias:
                continue
            token_hit = any(alias.lower() == h.lower() or alias.lower() in h.lower() for h in haystacks)
            text_hit = alias.lower() in long_text.lower()
            if token_hit or text_hit:
                matches.append({"broker": broker, "alias": alias, "hit": "token" if token_hit else "text"})
                break
    if not matches:
        return "", [], []
    # 優先 alias 長、token hit。
    matches = sorted(matches, key=lambda x: (x["hit"] != "token", -len(x["alias"]), x["broker"]))
    broker = matches[0]["broker"]
    candidates = [m["broker"] for m in matches]
    return broker, sorted(set(candidates)), matches


def find_company_name_candidates(token_info: Dict[str, Any], ticker_row: Dict[str, Any], broker_candidates: Sequence[str]) -> List[str]:
    official_names = [
        normalize_unicode_text(ticker_row.get("Name", "")),
        normalize_unicode_text(ticker_row.get("FullName", "")),
        normalize_unicode_text(ticker_row.get("EnglishName", "")),
    ]
    broker_set = {normalize_unicode_text(x).lower() for x in broker_candidates}
    candidates: List[str] = []
    for token in token_info.get("chinese_tokens", []) + token_info.get("english_tokens", []):
        token_clean = normalize_unicode_text(token)
        if not token_clean:
            continue
        if token_clean.lower() in broker_set:
            continue
        if any(token_clean and (token_clean in n or n in token_clean) for n in official_names if n):
            candidates.append(token_clean)
        elif len(token_clean) >= 2:
            candidates.append(token_clean)
    return sorted(set(candidates), key=lambda x: (-len(x), x))[:8]


def extract_report_title(first_page_text: str, repaired_sentences: Sequence[str]) -> str:
    lines = text_to_lines(first_page_text)
    # 優先取有中文/英文且不是純日期/頁碼的前幾行。
    for line in lines[:12]:
        if len(line) < 4:
            continue
        if re.fullmatch(r"[\d./\- ]+", line):
            continue
        if "http" in line.lower():
            continue
        return line[:240]
    return first_non_empty(repaired_sentences)[:240]


def detect_report_type(filename_text: str, page_text: str) -> str:
    joined = f"{filename_text} {page_text}"
    for canonical, aliases in REPORT_TYPE_ALIASES.items():
        for alias in aliases:
            if normalize_unicode_text(alias).lower() in joined.lower():
                return canonical
    return ""


def detect_language(text: str) -> str:
    text = normalize_unicode_text(text)
    cn = len(re.findall(r"[\u3400-\u4DBF\u4E00-\u9FFF]", text))
    en = len(re.findall(r"[A-Za-z]", text))
    if cn > 0 and en > 0:
        return "mixed"
    if cn > 0:
        return "zh"
    if en > 0:
        return "en"
    return "unknown"

# ============================================================
# def 07_RATING_TARGET_PRICE_EXTRACTION
# ============================================================

def extract_rating(text: str, rating_alias: Dict[str, List[str]]) -> Tuple[str, List[Dict[str, str]]]:
    hay = normalize_unicode_text(text)
    matches: List[Dict[str, str]] = []
    for canonical, aliases in rating_alias.items():
        for alias in aliases:
            a = normalize_unicode_text(alias)
            if not a:
                continue
            pattern = re.escape(a)
            if re.search(pattern, hay, re.IGNORECASE):
                matches.append({"rating": canonical, "alias": a})
                break
    if not matches:
        return "", []
    matches = sorted(matches, key=lambda x: (-len(x["alias"]), x["rating"]))
    return matches[0]["rating"], matches


def extract_rating_change(text: str) -> str:
    hay = normalize_unicode_text(text)
    patterns = {
        "UPGRADE": ["升評", "調升", "Upgrade", "Upgraded"],
        "DOWNGRADE": ["降評", "調降", "Downgrade", "Downgraded"],
        "MAINTAIN": ["維持", "Maintain", "Maintained", "重申", "Reiterate"],
        "INITIATE": ["初評", "初次", "Initiate", "Initiating"],
    }
    for canonical, aliases in patterns.items():
        for alias in aliases:
            if alias.lower() in hay.lower():
                return canonical
    return ""


def extract_target_price(text: str) -> Optional[float]:
    hay = normalize_unicode_text(text)
    patterns = [
        r"(?:目標價|目標價格|Target\s*Price|TP)\s*[:：]?\s*(?:NT\$|新台幣|TWD|NTD)?\s*([0-9][0-9,]*(?:\.\d+)?)",
        r"(?:TP)\s*([0-9][0-9,]*(?:\.\d+)?)",
    ]
    for pat in patterns:
        m = re.search(pat, hay, re.IGNORECASE)
        if m:
            return safe_float(m.group(1))
    return None


def extract_current_price(text: str) -> Optional[float]:
    hay = normalize_unicode_text(text)
    patterns = [
        r"(?:收盤價|股價|現價|Current\s*Price|Price)\s*[:：]?\s*(?:NT\$|新台幣|TWD|NTD)?\s*([0-9][0-9,]*(?:\.\d+)?)",
    ]
    for pat in patterns:
        m = re.search(pat, hay, re.IGNORECASE)
        if m:
            return safe_float(m.group(1))
    return None


def calculate_upside_downside(target: Optional[float], current: Optional[float]) -> Optional[float]:
    if target is None or current is None or current == 0:
        return None
    return round((target / current - 1.0) * 100.0, 4)

# ============================================================
# def 08_FINANCIAL_TABLE_EXTRACTION
# ============================================================

def extract_pdf_tables(pdf_path: Path, max_pages: int = PDF_TABLE_MAX_PAGES) -> List[Dict[str, Any]]:
    tables: List[Dict[str, Any]] = []
    pdfplumber = optional_import_pdfplumber()
    if pdfplumber is None:
        return tables
    try:
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page_idx, page in enumerate(pdf.pages[:max_pages], start=1):
                try:
                    page_tables = page.extract_tables() or []
                except Exception:
                    page_tables = []
                for table_idx, table in enumerate(page_tables, start=1):
                    cleaned = clean_raw_table(table)
                    if cleaned:
                        tables.append({
                            "PageNumber": page_idx,
                            "TableID": f"P{page_idx:03d}_T{table_idx:03d}",
                            "Rows": cleaned,
                        })
    except Exception as exc:
        print(f"[WARN] 表格抽取失敗：{pdf_path} -> {exc}", file=sys.stderr)
    return tables


def clean_raw_table(table: Any) -> List[List[str]]:
    if not table:
        return []
    rows: List[List[str]] = []
    for row in table:
        if row is None:
            continue
        cleaned = [normalize_unicode_text(cell) for cell in row]
        if any(cell for cell in cleaned):
            rows.append(cleaned)
    return rows


def normalize_metric_name(raw: str) -> str:
    raw_clean = normalize_unicode_text(raw)
    if not raw_clean:
        return ""
    raw_lower = raw_clean.lower().replace(" ", "")
    best = ""
    best_len = 0
    for metric, aliases in METRIC_ALIASES.items():
        for alias in aliases:
            alias_clean = normalize_unicode_text(alias)
            alias_lower = alias_clean.lower().replace(" ", "")
            if alias_lower and alias_lower in raw_lower and len(alias_lower) > best_len:
                best = metric
                best_len = len(alias_lower)
    return best


def infer_unit_and_scale(metric_raw: str, table_context: str) -> Tuple[str, str, float]:
    context = normalize_unicode_text(f"{metric_raw} {table_context}")
    unit = ""
    currency = "TWD"
    scale = 1.0
    if "%" in context or any(x in context for x in ["率", "Margin", "Yield", "ROE", "ROA"]):
        unit = "%"
    elif re.search(r"\b(x|X|倍)\b", context):
        unit = "x"
    elif any(x in context for x in ["百萬", "NT$m", "NTD m", "新台幣百萬元", "台幣百萬元"]):
        unit = "NT$m"
        scale = 1_000_000.0
    elif any(x in context for x in ["十億", "bn", "billion", "NT$bn"]):
        unit = "NT$bn"
        scale = 1_000_000_000.0
    elif any(x in context for x in ["千元", "仟元"]):
        unit = "NT$000"
        scale = 1_000.0
    elif any(x in context for x in ["美元", "USD", "US$"]):
        currency = "USD"
    if not unit:
        unit = "raw"
    return unit, currency, scale


def parse_period_label(label: str) -> Dict[str, Any]:
    raw = normalize_unicode_text(label)
    result = {"PeriodType": "", "FiscalYear": None, "FiscalQuarter": "", "EstimateFlag": "", "PeriodLabelRaw": raw}
    if not raw:
        return result
    upper = raw.upper()
    if re.search(r"\b(TTM|LTM)\b", upper):
        result["PeriodType"] = "TTM"
    if "E" in upper or "F" in upper or "預估" in raw or "估" in raw:
        result["EstimateFlag"] = "Estimate"
    elif "A" in upper or "實際" in raw:
        result["EstimateFlag"] = "Actual"
    else:
        result["EstimateFlag"] = ""
    q_match = re.search(r"(?:([1-4])Q|Q([1-4])|([1-4])季)", upper)
    if q_match:
        q = first_non_empty([q_match.group(1), q_match.group(2), q_match.group(3)])
        result["FiscalQuarter"] = f"Q{q}"
        result["PeriodType"] = "FQ"
    year_match = re.search(r"((?:19|20)\d{2}|\d{2})", upper)
    if year_match:
        year_raw = year_match.group(1)
        year = int(year_raw)
        if year < 100:
            year += 2000
        result["FiscalYear"] = year
        if not result["PeriodType"]:
            result["PeriodType"] = "FY"
    return result


def parse_financial_tables_to_records(tables: List[Dict[str, Any]], basic_row: Dict[str, Any], run_id: str) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for table in tables:
        rows = table.get("Rows") or []
        if len(rows) < 2:
            continue
        header_idx = find_best_header_row(rows)
        if header_idx is None:
            continue
        header = rows[header_idx]
        data_rows = rows[header_idx + 1:]
        table_context = " ".join(" ".join(r) for r in rows[: min(len(rows), 3)])
        for r_idx, row in enumerate(data_rows, start=header_idx + 1):
            if not row:
                continue
            metric_raw = normalize_unicode_text(row[0] if len(row) > 0 else "")
            metric = normalize_metric_name(metric_raw)
            if not metric:
                continue
            category = METRIC_CATEGORY_MAP.get(metric, "Other")
            unit, currency, scale = infer_unit_and_scale(metric_raw, table_context)
            max_cols = max(len(row), len(header))
            for c_idx in range(1, max_cols):
                value_raw = normalize_unicode_text(row[c_idx] if c_idx < len(row) else "")
                if not value_raw:
                    continue
                value = safe_float(value_raw)
                if value is None:
                    continue
                period_label = normalize_unicode_text(header[c_idx] if c_idx < len(header) else "")
                period = parse_period_label(period_label)
                source_text = f"{metric_raw} | {period_label} | {value_raw}"
                fin_id = stable_hash([
                    basic_row.get("ReportID", ""),
                    table.get("TableID", ""),
                    r_idx,
                    c_idx,
                    metric,
                    period_label,
                    value_raw,
                ], size=24)
                record = empty_financial_row()
                record.update({
                    "FinancialRowID": fin_id,
                    "FileID": basic_row.get("FileID", ""),
                    "ReportID": basic_row.get("ReportID", ""),
                    "TW_TICKER": basic_row.get("TW_TICKER", ""),
                    "YF_TICKER": basic_row.get("YF_TICKER", ""),
                    "Name": basic_row.get("Name", ""),
                    "ReportDate": basic_row.get("ReportDate", ""),
                    "Broker": basic_row.get("Broker", ""),
                    "PeriodType": period.get("PeriodType", ""),
                    "FiscalYear": period.get("FiscalYear"),
                    "FiscalQuarter": period.get("FiscalQuarter", ""),
                    "PeriodLabelRaw": period.get("PeriodLabelRaw", ""),
                    "EstimateFlag": period.get("EstimateFlag", ""),
                    "MetricCategory": category,
                    "MetricName": metric,
                    "MetricNameRaw": metric_raw,
                    "Value": value,
                    "ValueRaw": value_raw,
                    "Unit": unit,
                    "Currency": currency,
                    "Scale": scale,
                    "PageNumber": table.get("PageNumber", ""),
                    "TableID": table.get("TableID", ""),
                    "RowIndex": r_idx,
                    "ColumnIndex": c_idx,
                    "SourceText": source_text,
                    "ConfidenceScore": 0.72 if period.get("FiscalYear") else 0.62,
                    "ValidationStatus": "PASS" if period.get("FiscalYear") else "REVIEW",
                    "ValidationIssues": "" if period.get("FiscalYear") else "PERIOD_UNCLEAR",
                    "CreatedAt": now_iso(),
                    "UpdatedAt": now_iso(),
                    "RunID": run_id,
                    "SchemaVersion": SCHEMA_VERSION,
                })
                # 對常用寬欄也同步寫值，方便 dashboard 使用；long 欄仍以 MetricName/Value 為主。
                if metric in record:
                    record[metric] = value
                records.append(record)
    return records


def find_best_header_row(rows: List[List[str]]) -> Optional[int]:
    best_idx = None
    best_score = -1
    for idx, row in enumerate(rows[:6]):
        score = 0
        joined = " ".join(row)
        if re.search(r"(?:19|20)\d{2}|\d{2}[EF]?|Q[1-4]|[1-4]Q", joined, re.IGNORECASE):
            score += 2
        score += sum(1 for cell in row if parse_period_label(cell).get("FiscalYear"))
        score += sum(1 for cell in row if normalize_unicode_text(cell))
        if score > best_score:
            best_score = score
            best_idx = idx
    if best_score <= 1:
        return None
    return best_idx

# ============================================================
# def 09_BASICINFO_RECORD_BUILDER
# ============================================================

def empty_basic_row() -> Dict[str, Any]:
    return {col: "" for col in BASICINFO_COLUMNS}


def empty_financial_row() -> Dict[str, Any]:
    return {col: "" for col in FINANCIALDATA_COLUMNS}


def build_basicinfo_record(pdf_path: Path, ticker_lookup: Dict[str, Dict[str, Any]], broker_alias: Dict[str, List[str]], rating_alias: Dict[str, List[str]], run_id: str) -> Dict[str, Any]:
    source_filename = pdf_path.name
    source_path = str(pdf_path)
    file_hash = file_sha256(pdf_path)
    file_id = stable_hash([source_filename, file_hash], size=24)
    token_info = tokenize_filename(source_filename)
    pdf_info = extract_pdf_text_and_first_page_zones(pdf_path)
    first_page_text = normalize_unicode_text(pdf_info.get("first_page_text", ""))
    top_zone_text = "\n".join([
        pdf_info.get("top_left_text", ""),
        pdf_info.get("top_center_text", ""),
        pdf_info.get("top_right_text", ""),
    ])
    filename_ticker_candidates = extract_filename_ticker_candidates(token_info, ticker_lookup)
    page_ticker_candidates = extract_text_ticker_candidates(first_page_text + "\n" + top_zone_text, "first_page", ticker_lookup)
    tw_ticker, yf_ticker, ticker_issues = choose_canonical_ticker(filename_ticker_candidates, page_ticker_candidates, ticker_lookup)
    ticker_row = ticker_lookup.get(tw_ticker, {}) if tw_ticker else {}
    filename_date_candidates = parse_date_candidates_from_number_tokens(token_info.get("number_tokens", []))
    report_date, all_date_candidates = choose_best_report_date(filename_date_candidates, first_page_text)
    broker, broker_candidates, broker_matches = match_broker_from_tokens_and_text(
        token_info.get("chinese_tokens", []),
        token_info.get("english_tokens", []),
        top_zone_text + "\n" + first_page_text,
        broker_alias,
    )
    company_candidates = find_company_name_candidates(token_info, ticker_row, broker_candidates)
    repaired_sentences = pdf_info.get("first_page_repaired_sentences", []) or []
    report_title = extract_report_title(first_page_text, repaired_sentences)
    report_type = detect_report_type(token_info.get("normalized", ""), first_page_text)
    language = detect_language(first_page_text or token_info.get("normalized", ""))
    rating, rating_matches = extract_rating(first_page_text + "\n" + top_zone_text, rating_alias)
    rating_change = extract_rating_change(first_page_text + "\n" + token_info.get("normalized", ""))
    target_price = extract_target_price(first_page_text + "\n" + top_zone_text)
    current_price = extract_current_price(first_page_text + "\n" + top_zone_text)
    upside = calculate_upside_downside(target_price, current_price)
    confidence, status, validation_issues = score_basicinfo_confidence(
        filename_ticker_candidates,
        page_ticker_candidates,
        ticker_row,
        report_date,
        broker,
        rating,
        target_price,
        report_title,
        ticker_issues,
        pdf_info.get("issues", []),
    )
    report_id = stable_hash([
        tw_ticker,
        report_date,
        broker,
        source_filename,
        file_hash[:16],
    ], size=24)
    evidence = {
        "filename_tokens": token_info,
        "filename_ticker_candidates": filename_ticker_candidates,
        "first_page_ticker_candidates": page_ticker_candidates,
        "date_candidates": all_date_candidates,
        "broker_matches": broker_matches,
        "rating_matches": rating_matches,
        "company_candidates": company_candidates,
        "first_page_left_block": pdf_info.get("top_left_text", ""),
        "first_page_center_block": pdf_info.get("top_center_text", ""),
        "first_page_right_block": pdf_info.get("top_right_text", ""),
        "first_page_repaired_sentences": repaired_sentences,
        "twse_tpex_match": ticker_row,
        "pdf_engine": pdf_info.get("engine", ""),
        "pdf_issues": pdf_info.get("issues", []),
    }
    row = empty_basic_row()
    row.update({
        "FileID": file_id,
        "ReportID": report_id,
        "SourceFileName": source_filename,
        "SourcePath": source_path,
        "FileHash": file_hash,
        "TW_TICKER": tw_ticker,
        "YF_TICKER": yf_ticker or ticker_row.get("YF_TICKER", ""),
        "Market": ticker_row.get("Market", ""),
        "Name": ticker_row.get("Name", ""),
        "CompanyNameCandidate": " | ".join(company_candidates),
        "Broker": broker,
        "BrokerCandidate": " | ".join(broker_candidates),
        "ReportDate": report_date,
        "ReportTitle": report_title,
        "ReportType": report_type,
        "Language": language,
        "Rating": rating,
        "RatingChange": rating_change,
        "TargetPrice": target_price if target_price is not None else "",
        "CurrentPrice": current_price if current_price is not None else "",
        "UpsideDownsidePct": upside if upside is not None else "",
        "InvestmentThesis": first_non_empty(repaired_sentences[:2])[:800],
        "Industry": ticker_row.get("Industry", ""),
        "Chairman": ticker_row.get("Chairman", ""),
        "GeneralManager": ticker_row.get("GeneralManager", ""),
        "Spokesperson": ticker_row.get("Spokesperson", ""),
        "ConfidenceScore": confidence,
        "ValidationStatus": status,
        "ValidationIssues": " | ".join(validation_issues),
        "EvidenceJson": safe_json_dumps(evidence),
        "CreatedAt": now_iso(),
        "UpdatedAt": now_iso(),
        "RunID": run_id,
        "SchemaVersion": SCHEMA_VERSION,
    })
    return row


def score_basicinfo_confidence(filename_tickers: List[Dict[str, Any]], page_tickers: List[Dict[str, Any]], ticker_row: Dict[str, Any], report_date: str, broker: str, rating: str, target_price: Optional[float], report_title: str, ticker_issues: Sequence[str], pdf_issues: Sequence[str]) -> Tuple[float, str, List[str]]:
    score = 0.0
    issues: List[str] = []
    if filename_tickers:
        score += CONFIDENCE_WEIGHTS["filename_ticker"]
    else:
        issues.append("NO_FILENAME_TICKER")
    if page_tickers:
        score += CONFIDENCE_WEIGHTS["first_page_ticker"]
    else:
        issues.append("NO_FIRST_PAGE_TICKER")
    if ticker_row and ticker_row.get("Name"):
        score += CONFIDENCE_WEIGHTS["exchange_name"]
    else:
        issues.append("NO_EXCHANGE_NAME_MATCH")
    if report_date:
        score += CONFIDENCE_WEIGHTS["report_date"]
    else:
        issues.append("NO_REPORT_DATE")
    if broker:
        score += CONFIDENCE_WEIGHTS["broker"]
    else:
        issues.append("NO_BROKER")
    if rating or target_price is not None:
        score += CONFIDENCE_WEIGHTS["rating_or_target"]
    else:
        issues.append("NO_RATING_OR_TARGET_PRICE")
    if report_title:
        score += CONFIDENCE_WEIGHTS["title_or_text"]
    else:
        issues.append("NO_REPORT_TITLE")
    issues.extend(ticker_issues)
    issues.extend(str(x) for x in pdf_issues)
    score = round(min(score, 1.0), 4)
    if score >= 0.78 and not any(x.startswith("TICKER_AMBIGUOUS") for x in issues):
        status = "PASS"
    elif score >= 0.45:
        status = "REVIEW"
    else:
        status = "FAIL"
    return score, status, issues

# ============================================================
# def 10_DATAFRAME_SCHEMA_AND_UPSERT
# ============================================================

def make_dataframe(rows: List[Dict[str, Any]], columns: Sequence[str]):
    pd = require_pandas()
    if not rows:
        return pd.DataFrame(columns=list(columns))
    df = pd.DataFrame(rows)
    for col in columns:
        if col not in df.columns:
            df[col] = ""
    return df[list(columns)]


def enforce_basicinfo_schema(df):
    pd = require_pandas()
    if df is None:
        return pd.DataFrame(columns=BASICINFO_COLUMNS)
    for col in BASICINFO_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[BASICINFO_COLUMNS]


def enforce_financialdata_schema(df):
    pd = require_pandas()
    if df is None:
        return pd.DataFrame(columns=FINANCIALDATA_COLUMNS)
    for col in FINANCIALDATA_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[FINANCIALDATA_COLUMNS]


def read_existing_parquet(path: Path, columns: Sequence[str]):
    pd = require_pandas()
    if not path.exists():
        return pd.DataFrame(columns=list(columns))
    try:
        df = pd.read_parquet(path)
        for col in columns:
            if col not in df.columns:
                df[col] = ""
        return df[list(columns)]
    except Exception as exc:
        backup_path = path.with_suffix(path.suffix + f".read_failed.{int(time.time())}.bak")
        try:
            path.rename(backup_path)
        except Exception:
            pass
        print(f"[WARN] 舊 Parquet 讀取失敗，已嘗試備份：{path} -> {backup_path}，錯誤：{exc}", file=sys.stderr)
        return pd.DataFrame(columns=list(columns))


def cumulative_upsert(existing_df, new_df, key_columns: Sequence[str], columns: Sequence[str]):
    pd = require_pandas()
    existing_df = existing_df.copy() if existing_df is not None else pd.DataFrame(columns=list(columns))
    new_df = new_df.copy() if new_df is not None else pd.DataFrame(columns=list(columns))
    for col in columns:
        if col not in existing_df.columns:
            existing_df[col] = ""
        if col not in new_df.columns:
            new_df[col] = ""
    if new_df.empty:
        return existing_df[list(columns)]
    combined = pd.concat([existing_df[list(columns)], new_df[list(columns)]], ignore_index=True)
    for key in key_columns:
        if key not in combined.columns:
            combined[key] = ""
    # 保留最後一次抽取結果，但不覆蓋不同 ReportID。
    combined = combined.drop_duplicates(subset=list(key_columns), keep="last")
    return combined[list(columns)]


def write_parquet_mandatory(df, path: Path) -> None:
    if not optional_import_pyarrow_available():
        raise RuntimeError("Parquet 是必選輸出，但缺少 pyarrow。請先安裝：pip install pyarrow")
    df.to_parquet(path, index=False)

# ============================================================
# def 11_OPTIONAL_OUTPUTS
# ============================================================

def write_csv_optional(df, path: Path) -> None:
    df.to_csv(path, index=False, encoding=CSV_ENCODING_FOR_EXCEL)


def write_json_optional(df, path: Path) -> None:
    records = df.to_dict(orient="records")
    with path.open("w", encoding=JSON_ENCODING) as f:
        json.dump(records, f, ensure_ascii=False, indent=2, default=str)


def write_duckdb_optional(output_dir: Path, basic_parquet: Path, financial_parquet: Path) -> Optional[Path]:
    duckdb = optional_import_duckdb()
    if duckdb is None:
        print("[WARN] 未安裝 duckdb，略過 DuckDB 輸出。pip install duckdb", file=sys.stderr)
        return None
    db_path = output_dir / DUCKDB_NAME
    con = duckdb.connect(str(db_path))
    con.execute("CREATE OR REPLACE TABLE StockReportBasicInfo AS SELECT * FROM read_parquet(?)", [str(basic_parquet)])
    con.execute("CREATE OR REPLACE TABLE StockReportFinancialData AS SELECT * FROM read_parquet(?)", [str(financial_parquet)])
    con.execute("CREATE OR REPLACE VIEW v_report_financial AS SELECT b.*, f.MetricName, f.Value, f.ValueRaw, f.PeriodType, f.FiscalYear, f.FiscalQuarter, f.EstimateFlag, f.PageNumber, f.TableID FROM StockReportBasicInfo b LEFT JOIN StockReportFinancialData f USING (ReportID)")
    con.close()
    return db_path


def write_google_sheet_optional(basic_df, financial_df, spreadsheet_name: str, credentials_json: str) -> bool:
    if not spreadsheet_name or not credentials_json:
        return False
    try:
        import gspread  # type: ignore
        from gspread_dataframe import set_with_dataframe  # type: ignore
        gc = gspread.service_account(filename=credentials_json)
        try:
            sh = gc.open(spreadsheet_name)
        except Exception:
            sh = gc.create(spreadsheet_name)
        def upsert_ws(title: str, df):
            try:
                ws = sh.worksheet(title)
                ws.clear()
            except Exception:
                ws = sh.add_worksheet(title=title, rows=max(len(df) + 10, 100), cols=max(len(df.columns) + 5, 20))
            set_with_dataframe(ws, df)
        upsert_ws("StockReportBasicInfo", basic_df)
        upsert_ws("StockReportFinancialData", financial_df)
        return True
    except Exception as exc:
        print(f"[WARN] Google Sheet 輸出失敗：{exc}", file=sys.stderr)
        return False

# ============================================================
# def 12_HTML_MATRIX_AND_SUMMARY
# ============================================================

def write_batch_matrix_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    fieldnames = [
        "SourceFileName", "TW_TICKER", "Name", "Broker", "ReportDate", "Rating", "TargetPrice",
        "ConfidenceScore", "ValidationStatus", "ValidationIssues", "FinancialRows",
    ]
    with path.open("w", encoding=CSV_ENCODING_FOR_EXCEL, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def write_html_matrix(path: Path, basic_rows: List[Dict[str, Any]], financial_counts: Dict[str, int], summary: Dict[str, Any]) -> None:
    status_counts: Dict[str, int] = {}
    for row in basic_rows:
        status = normalize_unicode_text(row.get("ValidationStatus", "UNKNOWN")) or "UNKNOWN"
        status_counts[status] = status_counts.get(status, 0) + 1
    body_rows = []
    for row in basic_rows:
        report_id = row.get("ReportID", "")
        fin_count = financial_counts.get(report_id, 0)
        status = row.get("ValidationStatus", "")
        cls = "pass" if status == "PASS" else "review" if status == "REVIEW" else "fail"
        body_rows.append(
            "<tr class='{cls}'>".format(cls=cls)
            + f"<td>{html.escape(str(row.get('SourceFileName', '')))}</td>"
            + f"<td>{html.escape(str(row.get('TW_TICKER', '')))}</td>"
            + f"<td>{html.escape(str(row.get('Name', '')))}</td>"
            + f"<td>{html.escape(str(row.get('Broker', '')))}</td>"
            + f"<td>{html.escape(str(row.get('ReportDate', '')))}</td>"
            + f"<td>{html.escape(str(row.get('Rating', '')))}</td>"
            + f"<td>{html.escape(str(row.get('TargetPrice', '')))}</td>"
            + f"<td>{html.escape(str(row.get('ConfidenceScore', '')))}</td>"
            + f"<td>{html.escape(str(status))}</td>"
            + f"<td>{fin_count}</td>"
            + f"<td>{html.escape(str(row.get('ValidationIssues', ''))[:400])}</td>"
            + "</tr>"
        )
    doc = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8" />
<title>VRN Batch Report</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background:#fbfaf7; color:#1f2937; margin:24px; font-size:13px; }}
h1 {{ margin:0 0 4px 0; font-size:22px; }}
.sub {{ color:#6b7280; margin-bottom:18px; }}
.cards {{ display:grid; grid-template-columns: repeat(5, minmax(120px,1fr)); gap:10px; margin-bottom:16px; }}
.card {{ background:#fff; border:1px solid #e5e7eb; border-radius:12px; padding:12px; }}
.card b {{ display:block; font-size:20px; margin-top:4px; }}
table {{ width:100%; border-collapse:collapse; background:#fff; border:1px solid #e5e7eb; }}
th, td {{ border-bottom:1px solid #e5e7eb; padding:8px; text-align:left; vertical-align:top; }}
th {{ background:#f3f4f6; position:sticky; top:0; }}
tr.pass td:first-child {{ border-left:5px solid #dc2626; }}
tr.review td:first-child {{ border-left:5px solid #f59e0b; }}
tr.fail td:first-child {{ border-left:5px solid #16a34a; }}
.small {{ font-size:12px; color:#6b7280; }}
</style>
</head>
<body>
<h1>VERITAS INTELLIGENCE ANALYTICS</h1>
<div class="sub">VeritasReportNova · Stock Report Database Matrix · {html.escape(str(summary.get('RunID','')))}</div>
<div class="cards">
  <div class="card">PDF processed<b>{summary.get('ProcessedFiles', 0)}</b></div>
  <div class="card">Basic rows<b>{summary.get('BasicRows', 0)}</b></div>
  <div class="card">Financial rows<b>{summary.get('FinancialRows', 0)}</b></div>
  <div class="card">PASS<b>{status_counts.get('PASS', 0)}</b></div>
  <div class="card">REVIEW/FAIL<b>{status_counts.get('REVIEW', 0) + status_counts.get('FAIL', 0)}</b></div>
</div>
<table>
<thead><tr><th>File</th><th>Ticker</th><th>Name</th><th>Broker</th><th>Date</th><th>Rating</th><th>Target</th><th>Score</th><th>Status</th><th>FinRows</th><th>Issues</th></tr></thead>
<tbody>
{''.join(body_rows)}
</tbody>
</table>
<p class="small">Parquet is the mandatory source of truth. CSV / JSON / DuckDB / Google Sheet are optional derived outputs.</p>
</body>
</html>"""
    path.write_text(doc, encoding="utf-8")

# ============================================================
# def 13_PROCESSING_PIPELINE
# ============================================================

def process_one_pdf(pdf_path: Path, ticker_lookup: Dict[str, Dict[str, Any]], broker_alias: Dict[str, List[str]], rating_alias: Dict[str, List[str]], run_id: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    basic = build_basicinfo_record(pdf_path, ticker_lookup, broker_alias, rating_alias, run_id)
    tables = extract_pdf_tables(pdf_path)
    financial = parse_financial_tables_to_records(tables, basic, run_id)
    return basic, financial


def process_batch(args: argparse.Namespace) -> Dict[str, Any]:
    output_dir = ensure_dir(Path(args.output).expanduser().resolve())
    input_path = Path(args.input).expanduser().resolve()
    run_id = args.run_id or make_run_id()

    ticker_ssot_path = Path(args.ticker_ssot).expanduser().resolve() if args.ticker_ssot else None
    broker_ssot_path = Path(args.broker_ssot).expanduser().resolve() if args.broker_ssot else None
    rating_ssot_path = Path(args.rating_ssot).expanduser().resolve() if args.rating_ssot else None

    local_lookup = load_local_ticker_ssot(ticker_ssot_path)
    online_lookup = fetch_exchange_name_table(bool(args.online_name_update))
    ticker_lookup = merge_ticker_lookups(local_lookup, online_lookup)
    broker_alias = load_broker_alias_ssot(broker_ssot_path)
    rating_alias = load_rating_alias_ssot(rating_ssot_path)

    files = scan_input_files(input_path)
    basic_rows: List[Dict[str, Any]] = []
    financial_rows: List[Dict[str, Any]] = []
    checkpoint = {
        "RunID": run_id,
        "StartedAt": now_iso(),
        "Input": str(input_path),
        "Output": str(output_dir),
        "Files": [],
        "SchemaVersion": SCHEMA_VERSION,
    }

    for idx, pdf_path in enumerate(files, start=1):
        print(f"[{idx}/{len(files)}] VRN processing: {pdf_path.name}")
        item = {"path": str(pdf_path), "status": "", "error": ""}
        try:
            basic, financial = process_one_pdf(pdf_path, ticker_lookup, broker_alias, rating_alias, run_id)
            basic_rows.append(basic)
            financial_rows.extend(financial)
            item["status"] = "OK"
            item["ReportID"] = basic.get("ReportID", "")
            item["FinancialRows"] = len(financial)
        except Exception as exc:
            item["status"] = "FAIL"
            item["error"] = f"{exc}\n{traceback.format_exc()}"
            print(f"[ERROR] {pdf_path}: {exc}", file=sys.stderr)
        checkpoint["Files"].append(item)
        write_json_file(output_dir / BATCH_CHECKPOINT_JSON_NAME, checkpoint)

    basic_new = make_dataframe(basic_rows, BASICINFO_COLUMNS)
    financial_new = make_dataframe(financial_rows, FINANCIALDATA_COLUMNS)

    basic_path = output_dir / BASICINFO_PARQUET_NAME
    financial_path = output_dir / FINANCIALDATA_PARQUET_NAME
    basic_existing = read_existing_parquet(basic_path, BASICINFO_COLUMNS)
    financial_existing = read_existing_parquet(financial_path, FINANCIALDATA_COLUMNS)
    basic_final = cumulative_upsert(basic_existing, basic_new, BASICINFO_UPSERT_KEYS, BASICINFO_COLUMNS)
    financial_final = cumulative_upsert(financial_existing, financial_new, FINANCIALDATA_UPSERT_KEYS, FINANCIALDATA_COLUMNS)

    write_parquet_mandatory(basic_final, basic_path)
    write_parquet_mandatory(financial_final, financial_path)

    if args.csv:
        write_csv_optional(basic_final, output_dir / BASICINFO_CSV_NAME)
        write_csv_optional(financial_final, output_dir / FINANCIALDATA_CSV_NAME)
    if args.json:
        write_json_optional(basic_final, output_dir / BASICINFO_JSON_NAME)
        write_json_optional(financial_final, output_dir / FINANCIALDATA_JSON_NAME)
    duckdb_path = None
    if args.duckdb:
        duckdb_path = write_duckdb_optional(output_dir, basic_path, financial_path)
    google_sheet_ok = False
    if args.google_sheet:
        google_sheet_ok = write_google_sheet_optional(basic_final, financial_final, args.google_sheet, args.google_credentials)

    financial_counts: Dict[str, int] = {}
    for row in financial_rows:
        rid = normalize_unicode_text(row.get("ReportID", ""))
        if rid:
            financial_counts[rid] = financial_counts.get(rid, 0) + 1

    matrix_rows = []
    for row in basic_rows:
        rid = normalize_unicode_text(row.get("ReportID", ""))
        copy = dict(row)
        copy["FinancialRows"] = financial_counts.get(rid, 0)
        matrix_rows.append(copy)
    write_batch_matrix_csv(output_dir / BATCH_MATRIX_CSV_NAME, matrix_rows)

    summary = {
        "RunID": run_id,
        "StartedAt": checkpoint.get("StartedAt"),
        "FinishedAt": now_iso(),
        "Input": str(input_path),
        "Output": str(output_dir),
        "ProcessedFiles": len(files),
        "BasicRowsNew": len(basic_rows),
        "FinancialRowsNew": len(financial_rows),
        "BasicRows": int(len(basic_final)),
        "FinancialRows": int(len(financial_final)),
        "TickerLookupRows": len(ticker_lookup),
        "OutputFiles": {
            "BasicInfoParquet": str(basic_path),
            "FinancialDataParquet": str(financial_path),
            "BasicInfoCSV": str(output_dir / BASICINFO_CSV_NAME) if args.csv else "",
            "FinancialDataCSV": str(output_dir / FINANCIALDATA_CSV_NAME) if args.csv else "",
            "BasicInfoJSON": str(output_dir / BASICINFO_JSON_NAME) if args.json else "",
            "FinancialDataJSON": str(output_dir / FINANCIALDATA_JSON_NAME) if args.json else "",
            "DuckDB": str(duckdb_path) if duckdb_path else "",
            "GoogleSheet": args.google_sheet if google_sheet_ok else "",
            "HTML": str(output_dir / HTML_MATRIX_NAME),
        },
        "SchemaVersion": SCHEMA_VERSION,
    }
    write_json_file(output_dir / BATCH_SUMMARY_JSON_NAME, summary)
    write_html_matrix(output_dir / HTML_MATRIX_NAME, basic_rows, financial_counts, summary)
    print(safe_json_dumps(summary))
    return summary

# ============================================================
# def 14_SELF_TEST
# ============================================================

def run_self_test() -> None:
    print("[SELF-TEST] Start")
    sample = "凱基_神達3706 TT_初次評等_(20)260131_TargetPrice 168.pdf"
    token_info = tokenize_filename(sample)
    assert "3706" in token_info["number_tokens"], token_info
    assert "20" in token_info["number_tokens"] and "260131" in token_info["number_tokens"], token_info
    dates = parse_date_candidates_from_number_tokens(token_info["number_tokens"])
    assert any(d["date"] == "2026-01-31" for d in dates), dates
    local_lookup = {
        "3706": {"TW_TICKER": "3706", "YF_TICKER": "3706.TW", "Market": "TWSE", "Name": "神達", "Industry": "電腦及週邊"}
    }
    ft = extract_filename_ticker_candidates(token_info, local_lookup)
    pt = extract_text_ticker_candidates("神達 3706 TT Target Price 168 Buy", "first_page", local_lookup)
    ticker, yf, issues = choose_canonical_ticker(ft, pt, local_lookup)
    assert ticker == "3706" and yf == "3706.TW", (ticker, yf, issues)
    broker_alias = default_broker_aliases()
    broker, broker_candidates, _ = match_broker_from_tokens_and_text(token_info["chinese_tokens"], token_info["english_tokens"], "凱基證券", broker_alias)
    assert broker == "KGI", broker
    rating, _ = extract_rating("本報告維持買進評等，目標價168元", DEFAULT_RATING_ALIASES)
    assert rating == "BUY", rating
    tp = extract_target_price("目標價: NT$168")
    assert tp == 168.0, tp
    print("[SELF-TEST] PASS")

# ============================================================
# def 15_CLI
# ============================================================

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VRN Integrated Report Database Engine")
    parser.add_argument("--input", default=DEFAULT_INPUT_DIR, help="PDF 檔案或資料夾")
    parser.add_argument("--output", default=DEFAULT_OUTPUT_DIR, help="輸出資料夾")
    parser.add_argument("--ticker-ssot", default=DEFAULT_TICKER_SSOT_CSV, help="Ticker / Name SSOT CSV，本地優先")
    parser.add_argument("--broker-ssot", default=DEFAULT_BROKER_SSOT_CSV, help="Broker alias SSOT CSV")
    parser.add_argument("--rating-ssot", default=DEFAULT_RATING_SSOT_CSV, help="Rating alias SSOT CSV")
    parser.add_argument("--online-name-update", action="store_true", default=ENABLE_ONLINE_NAME_TABLE_BY_DEFAULT, help="啟用 TWSE/TPEX 線上名稱表更新")
    parser.add_argument("--csv", action="store_true", help="輸出 UTF-8 BOM CSV")
    parser.add_argument("--json", action="store_true", help="輸出 UTF-8 JSON")
    parser.add_argument("--duckdb", action="store_true", help="輸出 DuckDB")
    parser.add_argument("--google-sheet", default="", help="Google Sheet 名稱，可選")
    parser.add_argument("--google-credentials", default="", help="gspread service account json path")
    parser.add_argument("--run-id", default="", help="指定 RunID")
    parser.add_argument("--self-test", action="store_true", help="只跑內建測試")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if args.self_test:
        run_self_test()
        return 0
    process_batch(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
