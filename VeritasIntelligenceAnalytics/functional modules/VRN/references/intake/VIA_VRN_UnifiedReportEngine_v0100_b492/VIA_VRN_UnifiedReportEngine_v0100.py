#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VIA_VRN_UnifiedReportEngine v0100
=================================

單一入口整合三條證據鏈：

1. Filename：代號、日期、券商、公司名稱候選、報告型別。
2. First page：上／左／右資訊區、標題、評等、目標價、現價與本文。
3. Annual financial pages：年度／季度財務表、估值表、期間、單位與數值。

核心治理：

* 台股 canonical ticker 必須通過 TWSE／TPEX 正式名冊；查不到時 TW_TICKER 與
  Name 保持空值，不讓候選值污染正典欄位。
* INDUSTRY／OUTLOOK／OTHER 即使內文提到個股，也不寫入 canonical ticker。
* 三源衝突時保留全部 EvidenceJson；不可硬選的 canonical 欄位保持空值。
* 首頁與財務頁均以 PyMuPDF + pdfplumber 互證；footer、<8pt 小字、附註／附錄
  不進主資料。
* StockReportBasicInfo.parquet 與 StockReportFinancialData.parquet 是必選 SSOT；
  CSV／JSON／DuckDB／HTML 只由本次正典結果派生。
* 寫入採增量、去重、原子替換；低信心新資料不覆蓋既有高信心資料。

相容接軌：若同目錄或 --module-dir 找得到
VIA_VRN_FirstPageEngine_v*.py 與 VRN_ENG072_FirstPageText_v*.py，會優先借用其
公開契約與抽取結果；缺席時走本檔完整退路並把原因寫入 manifest。

用法：

  python VIA_VRN_UnifiedReportEngine_v0100.py --selftest
  python VIA_VRN_UnifiedReportEngine_v0100.py --in report.pdf \
      --official-listings StockTickerListDatabase.csv --out output
  python VIA_VRN_UnifiedReportEngine_v0100.py --in reports --out output \
      --csv --json --duckdb --html
"""

from __future__ import annotations

import argparse
import collections
import contextlib
import csv
import datetime as dt
import difflib
import hashlib
import html
import importlib.util
import io
import json
import math
import os
import re
import statistics
import sys
import tempfile
import traceback
import unicodedata
import uuid
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence
from xml.etree import ElementTree


# ============================================================================
# 0 · PARAMETERS（所有可調參數集中在頂部）
# ============================================================================

ENGINE_NAME = "VIA_VRN_UnifiedReportEngine"
ENGINE_VERSION = "v0100"
SCHEMA_VERSION = "vrn.report.v1.0.0"

DEFAULT_OUTPUT_DIR = Path("VRN_Unified_Output")
DEFAULT_BASIC_PARQUET = "StockReportBasicInfo.parquet"
DEFAULT_FINANCIAL_PARQUET = "StockReportFinancialData.parquet"
DEFAULT_MANIFEST_JSON = "VRN_Unified_RunManifest.json"
DEFAULT_MATRIX_HTML = "VRN_Unified_ValidationMatrix.html"

DEFAULT_FOOTER_RATIO = 0.10
DEFAULT_HEADER_RATIO = 0.20
DEFAULT_RIGHT_COLUMN_X_RATIO = 0.52
DEFAULT_WIDE_BLOCK_RATIO = 0.66
DEFAULT_MIN_FONT_PT = 8.0
DEFAULT_FIRSTPAGE_AGREE = 0.90
DEFAULT_FIRSTPAGE_PARTIAL = 0.60
DEFAULT_BAG_AGREE = 0.98
DEFAULT_FINANCIAL_PAGE_SCORE = 4.50
DEFAULT_MIN_FINANCIAL_METRICS = 2
DEFAULT_MIN_ANNUAL_PERIODS = 2
DEFAULT_REL_TOLERANCE = 0.05
DEFAULT_ABS_TOLERANCE = 0.02
DEFAULT_FORMULA_TOLERANCE = 0.08
DEFAULT_TARGET_PRICE_TOLERANCE = 0.02
DEFAULT_MAX_PAGES = 250
DEFAULT_MAX_TABLES_PER_PAGE = 20
DEFAULT_MAX_TABLE_ROWS = 200
DEFAULT_MAX_EVIDENCE_CHARS = 12000
DEFAULT_PARQUET_COMPRESSION = "zstd"
DEFAULT_CSV_ENCODING = "utf-8-sig"

SUPPORTED_INPUT_EXTENSIONS = (
    ".pdf", ".docx", ".doc", ".png", ".jpg", ".jpeg", ".tif", ".tiff",
    ".bmp", ".webp", ".gif",
)

FIRSTPAGE_ENGINE_PATTERN = "VIA_VRN_FirstPageEngine_v*.py"
FIRSTPAGE_TEXT_PATTERN = "VRN_ENG072_FirstPageText_v*.py"

REPORT_TYPE_STOCK = "STOCK"
REPORT_TYPE_INDUSTRY = "INDUSTRY"
REPORT_TYPE_OUTLOOK = "OUTLOOK"
REPORT_TYPE_OTHER = "OTHER"

REPORT_TYPE_MAP = {
    "個股": REPORT_TYPE_STOCK,
    "stock": REPORT_TYPE_STOCK,
    "產業": REPORT_TYPE_INDUSTRY,
    "industry": REPORT_TYPE_INDUSTRY,
    "sector": REPORT_TYPE_INDUSTRY,
    "大盤晨報": REPORT_TYPE_OUTLOOK,
    "海外": REPORT_TYPE_OUTLOOK,
    "outlook": REPORT_TYPE_OUTLOOK,
    "market": REPORT_TYPE_OUTLOOK,
    "研討會": REPORT_TYPE_OTHER,
    "未分類": REPORT_TYPE_OTHER,
    "other": REPORT_TYPE_OTHER,
}

STRONG_OUTLOOK_KEYWORDS = (
    "晨報", "早報", "晨會", "盤勢", "盤前", "盤後", "盤中", "投資日報",
    "市場展望", "大盤展望", "總體展望", "morning brief", "market outlook",
    "market strategy", "daily wrap", "market wrap",
)
STRONG_INDUSTRY_KEYWORDS = (
    "產業報告", "產業展望", "產業研究", "類股報告", "族群報告", "供應鏈",
    "industry report", "industry outlook", "sector report", "sector outlook",
)
WEAK_INDUSTRY_KEYWORDS = (
    "半導體", "伺服器", "記憶體", "散熱", "pcb", "ccl", "abf", "hbm",
    "semiconductor", "server", "thermal", "hardware", "supply chain",
)
OTHER_REPORT_KEYWORDS = (
    "研討會", "論壇", "峰會", "conference", "summit", "corporate day",
)

FOOTNOTE_PREFIXES = (
    "備註", "註:", "註：", "附註", "footnote", "note:", "notes:",
    "資料來源", "source:", "免責聲明", "disclaimer", "重要聲明",
)
APPENDIX_PREFIXES = ("附錄", "appendix")

FINANCIAL_PAGE_KEYWORDS = (
    "財務預估", "財務摘要", "損益預估", "獲利預估", "財務報表", "估值分析",
    "評價分析", "valuation", "financial summary", "financial forecast",
    "earnings forecast", "income statement", "balance sheet", "cash flow",
)

PERIOD_TOKEN_PATTERN = re.compile(
    r"(?ix)(?:\b(?:FY\s*[-_/]?)?(?:19|20)\d{2}[AEF]?\b|"
    r"\b(?:19|20)?\d{2}[AEF]\b|\b[AEF]\s*[-_/]?\d{2,4}\b|"
    r"\b[1-4]Q\s*\d{2,4}[AEF]?\b|\bQ[1-4]\s*\d{2,4}[AEF]?\b|"
    r"\b\d{2,4}\s*Q[1-4][AEF]?\b|民國\s*\d{2,3}\s*年|"
    r"\b1[01]\d\s*年\b)"
)

METRIC_ALIASES = {
    "Revenue": ("營業收入", "營收", "銷售收入", "淨銷售", "revenue", "net sales", "sales"),
    "RevenueYoY": ("營收年增率", "營收yoy", "revenue yoy", "sales growth"),
    "GrossProfit": ("營業毛利", "毛利", "gross profit"),
    "GrossMargin": ("營業毛利率", "毛利率", "gross margin", "gm%"),
    "OperatingProfit": ("營業利益", "營業利潤", "營業淨利", "operating profit", "operating income", "ebit"),
    "OperatingMargin": ("營業利益率", "營益率", "operating margin", "opm%"),
    "PretaxIncome": ("稅前淨利", "稅前利益", "pretax income", "pre-tax income"),
    "PretaxMargin": ("稅前淨利率", "稅前利益率", "pretax margin"),
    "NetIncome": ("稅後淨利", "歸屬母公司淨利", "本期淨利", "net income", "net profit"),
    "NetMargin": ("稅後淨利率", "淨利率", "net margin"),
    "EPS": ("每股盈餘", "每股稅後盈餘", "eps"),
    "TotalAssets": ("資產總額", "總資產", "total assets"),
    "TotalLiabilities": ("負債總額", "總負債", "total liabilities"),
    "Equity": ("股東權益", "權益總額", "淨值", "shareholders equity", "total equity"),
    "Cash": ("現金及約當現金", "現金", "cash and equivalents", "cash"),
    "Inventory": ("存貨", "inventory"),
    "AccountsReceivable": ("應收帳款", "accounts receivable", "a/r"),
    "Debt": ("有息負債", "借款", "debt"),
    "BookValuePerShare": ("每股淨值", "bvps", "book value per share"),
    "OperatingCashFlow": ("營業現金流", "營運現金流", "operating cash flow", "cash flow from operations"),
    "InvestingCashFlow": ("投資現金流", "investing cash flow"),
    "FinancingCashFlow": ("融資現金流", "financing cash flow"),
    "Capex": ("資本支出", "capex", "capital expenditure"),
    "FreeCashFlow": ("自由現金流", "free cash flow", "fcf"),
    "PER": ("本益比", "price earnings", "p/e", "per"),
    "PBR": ("股價淨值比", "price to book", "p/b", "pbr"),
    "PSR": ("股價營收比", "price to sales", "p/s", "psr"),
    "EV_EBITDA": ("ev/ebitda", "ev ebitda"),
    "DividendYield": ("殖利率", "dividend yield", "yield"),
    "ROE": ("股東權益報酬率", "roe"),
    "ROA": ("資產報酬率", "roa"),
    "ROIC": ("投入資本報酬率", "roic"),
    "DPS": ("每股股利", "每股股息", "dps"),
    "CFPS": ("每股現金流", "cfps"),
    "TargetPrice": ("目標價", "target price", "price target"),
    "CurrentPrice": ("現價", "收盤價", "股價", "current price", "share price", "closing price"),
    "UpsideDownsidePct": ("上漲空間", "下跌空間", "潛在報酬", "upside", "downside"),
}

METRIC_CATEGORY = {
    "Revenue": "Income Statement", "RevenueYoY": "Income Statement",
    "GrossProfit": "Income Statement", "GrossMargin": "Income Statement",
    "OperatingProfit": "Income Statement", "OperatingMargin": "Income Statement",
    "PretaxIncome": "Income Statement", "PretaxMargin": "Income Statement",
    "NetIncome": "Income Statement", "NetMargin": "Income Statement", "EPS": "Income Statement",
    "TotalAssets": "Balance Sheet", "TotalLiabilities": "Balance Sheet", "Equity": "Balance Sheet",
    "Cash": "Balance Sheet", "Inventory": "Balance Sheet", "AccountsReceivable": "Balance Sheet",
    "Debt": "Balance Sheet", "BookValuePerShare": "Balance Sheet",
    "OperatingCashFlow": "Cash Flow", "InvestingCashFlow": "Cash Flow",
    "FinancingCashFlow": "Cash Flow", "Capex": "Cash Flow", "FreeCashFlow": "Cash Flow",
    "PER": "Valuation", "PBR": "Valuation", "PSR": "Valuation", "EV_EBITDA": "Valuation",
    "DividendYield": "Valuation", "ROE": "Valuation", "ROA": "Valuation", "ROIC": "Valuation",
    "DPS": "Per Share", "CFPS": "Per Share", "TargetPrice": "Valuation",
    "CurrentPrice": "Valuation", "UpsideDownsidePct": "Valuation",
}

PERCENT_METRICS = frozenset((
    "RevenueYoY", "GrossMargin", "OperatingMargin", "PretaxMargin", "NetMargin",
    "DividendYield", "ROE", "ROA", "ROIC", "UpsideDownsidePct",
))
MULTIPLE_METRICS = frozenset(("PER", "PBR", "PSR", "EV_EBITDA"))
PER_SHARE_METRICS = frozenset(("EPS", "BookValuePerShare", "DPS", "CFPS", "TargetPrice", "CurrentPrice"))

BROKER_ALIASES = {
    "GOLDMAN": ("goldman sachs", "goldman", "gs"),
    "MORGANSTANLEY": ("morgan stanley", "ms"),
    "JPMORGAN": ("j.p. morgan", "jp morgan", "jpm", "jp"),
    "CITI": ("citigroup", "citi"),
    "CLSA": ("clsa taiwan", "clsa", "clst", "里昂"),
    "UBS": ("ubs", "瑞銀"),
    "DAIWA": ("daiwa", "大和"),
    "NOMURA": ("nomura", "野村"),
    "KGI": ("kgi", "凱基"),
    "MEGA": ("mega", "兆豐"),
    "TAISHIN": ("taishin", "台新"),
    "CTBC": ("ctbc", "中信"),
    "YUANTA": ("yuanta", "元大"),
    "SINO": ("sinopac", "永豐"),
    "HUANAN": ("華南",),
    "FUBON": ("fubon", "富邦"),
    "CAPITAL": ("capital securities", "群益"),
    "IBTS": ("ibts", "統一投顧", "統一證券"),
}

RATING_ALIASES = {
    "BUY": ("strong buy", "outperform", "overweight", "買進", "優於大盤", "加碼"),
    "HOLD": ("neutral", "equalweight", "equal-weight", "hold", "中立", "持有"),
    "SELL": ("underperform", "underweight", "sell", "賣出", "劣於大盤", "減碼"),
    "NOT_RATED": ("not rated", "n.r.", "未評等", "nr"),
}

BASIC_COLUMNS = [
    "FileID", "ReportID", "SourceFileName", "SourcePath", "FileHash",
    "TW_TICKER", "YF_TICKER", "Market", "Name", "CompanyNameCandidate",
    "ReportDate", "ReportTitle", "ReportType", "Language", "Broker",
    "BrokerCandidate", "Analyst", "Department", "Rating", "RatingChange",
    "TargetPrice", "CurrentPrice", "UpsideDownsidePct", "InvestmentThesis",
    "Industry", "SubIndustry", "MarketCap", "ShareCapital", "Chairman",
    "GeneralManager", "Spokesperson", "ConfidenceScore", "ValidationStatus",
    "ValidationIssues", "EvidenceJson", "CreatedAt", "UpdatedAt", "RunID",
    "SchemaVersion",
]

FINANCIAL_COLUMNS = [
    "FinancialRowID", "FileID", "ReportID", "TW_TICKER", "YF_TICKER", "Name",
    "ReportDate", "Broker", "PeriodType", "FiscalYear", "FiscalQuarter",
    "PeriodLabelRaw", "EstimateFlag", "MetricCategory", "MetricName",
    "MetricNameRaw", "Value", "ValueRaw", "Unit", "Currency", "Scale", "YoY",
    "QoQ", "PER", "PBR", "EV_EBITDA", "DividendYield", "ROE", "ROA",
    "Revenue", "GrossProfit", "GrossMargin", "OperatingProfit", "OperatingMargin",
    "NetIncome", "EPS", "TotalAssets", "TotalLiabilities", "Equity",
    "BookValuePerShare", "OperatingCashFlow", "Capex", "FreeCashFlow",
    "PageNumber", "TableID", "RowIndex", "ColumnIndex", "SourceText",
    "ConfidenceScore", "ValidationStatus", "ValidationIssues", "EvidenceJson",
    "CreatedAt", "UpdatedAt", "RunID", "SchemaVersion",
]


@dataclass(frozen=True)
class EngineConfig:
    footer_ratio: float = DEFAULT_FOOTER_RATIO
    header_ratio: float = DEFAULT_HEADER_RATIO
    right_column_x_ratio: float = DEFAULT_RIGHT_COLUMN_X_RATIO
    wide_block_ratio: float = DEFAULT_WIDE_BLOCK_RATIO
    min_font_pt: float = DEFAULT_MIN_FONT_PT
    firstpage_agree: float = DEFAULT_FIRSTPAGE_AGREE
    firstpage_partial: float = DEFAULT_FIRSTPAGE_PARTIAL
    bag_agree: float = DEFAULT_BAG_AGREE
    financial_page_score: float = DEFAULT_FINANCIAL_PAGE_SCORE
    min_financial_metrics: int = DEFAULT_MIN_FINANCIAL_METRICS
    min_annual_periods: int = DEFAULT_MIN_ANNUAL_PERIODS
    rel_tolerance: float = DEFAULT_REL_TOLERANCE
    abs_tolerance: float = DEFAULT_ABS_TOLERANCE
    formula_tolerance: float = DEFAULT_FORMULA_TOLERANCE
    target_price_tolerance: float = DEFAULT_TARGET_PRICE_TOLERANCE
    max_pages: int = DEFAULT_MAX_PAGES
    max_tables_per_page: int = DEFAULT_MAX_TABLES_PER_PAGE
    max_table_rows: int = DEFAULT_MAX_TABLE_ROWS
    allow_web_official: bool = False


@dataclass
class ListingRecord:
    code: str
    name: str
    market: str | None = None
    yf_ticker: str | None = None
    industry: str | None = None
    source: str = ""


@dataclass
class PageEvidence:
    page_number: int
    width: float
    height: float
    header: str = ""
    right: str = ""
    body: str = ""
    footer_char_count: int = 0
    heads: list[dict[str, Any]] = field(default_factory=list)
    fitz_text: str = ""
    plumber_text: str = ""
    compare: dict[str, Any] = field(default_factory=dict)
    fitz_tables: list[list[list[str]]] = field(default_factory=list)
    plumber_tables: list[list[list[str]]] = field(default_factory=list)
    score: float = 0.0
    role: str = "OTHER"
    score_evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class FinancialObservation:
    metric_name: str
    metric_name_raw: str
    metric_category: str
    period_raw: str
    period_type: str | None
    fiscal_year: int | None
    fiscal_quarter: str | None
    estimate_flag: str | None
    value: float | None
    value_raw: str
    unit: str | None
    currency: str | None
    scale: float | None
    page_number: int
    table_id: str
    row_index: int
    column_index: int
    engine: str
    source_text: str


@dataclass
class ReportResult:
    basic: dict[str, Any]
    financial: list[dict[str, Any]]
    evidence: dict[str, Any]


# ============================================================================
# 1 · GENERIC HELPERS
# ============================================================================


def def_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def def_nfkc(value: Any) -> str:
    return unicodedata.normalize("NFKC", str(value or ""))


def def_compact_text(value: Any) -> str:
    return re.sub(r"\s+", " ", def_nfkc(value)).strip()


def def_normalize_compare(value: Any) -> str:
    return re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "", def_nfkc(value)).lower()


def def_json(value: Any, max_chars: int | None = None) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    if max_chars and len(raw) > max_chars:
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        return json.dumps({"truncated": True, "sha256": digest, "preview": raw[:max_chars]},
                          ensure_ascii=False, separators=(",", ":"))
    return raw


def def_stable_id(prefix: str, *parts: Any) -> str:
    payload = "\x1f".join(def_nfkc(x).strip() for x in parts)
    return f"{prefix}_{hashlib.sha256(payload.encode('utf-8')).hexdigest()[:24]}"


def def_file_sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            block = fh.read(chunk_size)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def def_version_key(path: Path) -> tuple[int, str]:
    nums = re.findall(r"v(\d+)", path.stem, re.I)
    return (int(nums[-1]) if nums else -1, path.name.lower())


def def_find_latest_module(explicit: Path | None, module_dir: Path | None,
                           pattern: str) -> tuple[Path | None, str]:
    if explicit:
        p = explicit.expanduser().resolve()
        return (p, "explicit") if p.is_file() else (None, f"explicit missing:{p}")
    roots: list[Path] = []
    for root in (module_dir, Path(__file__).resolve().parent, Path.cwd(), Path.cwd() / "upload"):
        if root:
            q = Path(root).expanduser().resolve()
            if q not in roots:
                roots.append(q)
    hits: list[Path] = []
    for root in roots:
        if root.is_dir():
            hits.extend(x for x in root.glob(pattern) if x.resolve() != Path(__file__).resolve())
    if not hits:
        return None, f"{pattern} not found in " + ";".join(str(x) for x in roots)
    return sorted(set(hits), key=def_version_key)[-1], "auto-latest"


def def_load_module(path: Path | None, logical_name: str) -> tuple[Any | None, str]:
    if path is None:
        return None, "path unavailable"
    try:
        unique = f"{logical_name}_{hashlib.sha1(str(path).encode()).hexdigest()[:8]}"
        spec = importlib.util.spec_from_file_location(unique, path)
        if spec is None or spec.loader is None:
            return None, "import spec unavailable"
        mod = importlib.util.module_from_spec(spec)
        sys.modules[unique] = mod
        spec.loader.exec_module(mod)
        return mod, f"loaded:{path.name}"
    except Exception as exc:
        return None, f"load failed {type(exc).__name__}:{str(exc)[:160]}"


def def_module_doc_version(module: Any | None) -> str | None:
    if module is None:
        return None
    for line in str(getattr(module, "__doc__", "") or "").splitlines():
        text = line.strip()
        if text:
            return text[:200]
    return None


def def_module_version_consistency(path: Path | None, reported: str | None) -> str:
    if path is None or not reported:
        return "N/A"
    file_match = re.search(r"v(\d+)", path.stem, re.I)
    report_match = re.search(r"v(\d+)", str(reported), re.I)
    if not file_match or not report_match:
        return "N/A"
    return "MATCH" if int(file_match.group(1)) == int(report_match.group(1)) else "MISMATCH"


def def_collect_inputs(targets: Sequence[str | Path]) -> tuple[list[Path], list[dict[str, Any]]]:
    files: list[Path] = []
    diagnostics: list[dict[str, Any]] = []
    for target in targets:
        path = Path(target).expanduser()
        if path.is_file():
            if path.suffix.lower() in SUPPORTED_INPUT_EXTENSIONS:
                files.append(path.resolve())
                diagnostics.append({"path": str(path), "state": "ACCEPTED_FILE"})
            else:
                diagnostics.append({"path": str(path), "state": "UNSUPPORTED_EXTENSION"})
        elif path.is_dir():
            found = sorted(x.resolve() for x in path.iterdir()
                           if x.is_file() and x.suffix.lower() in SUPPORTED_INPUT_EXTENSIONS)
            files.extend(found)
            diagnostics.append({"path": str(path), "state": "ACCEPTED_DIR", "count": len(found)})
        else:
            diagnostics.append({"path": str(path), "state": "MISSING"})
    unique = sorted({str(x): x for x in files}.values(), key=lambda x: str(x).lower())
    return unique, diagnostics


def def_similarity(a: str, b: str) -> dict[str, Any]:
    aa = "".join(def_nfkc(a).split())
    bb = "".join(def_nfkc(b).split())
    if not aa and not bb:
        return {"sequence": 1.0, "bag": None, "state": "BOTH_EMPTY"}
    seq = difflib.SequenceMatcher(None, aa, bb).ratio()
    ca, cb = collections.Counter(aa), collections.Counter(bb)
    total = sum(ca.values()) + sum(cb.values())
    bag = (2 * sum((ca & cb).values()) / total) if total else None
    if seq >= DEFAULT_FIRSTPAGE_AGREE:
        state = "AGREE"
    elif bag is not None and bag >= DEFAULT_BAG_AGREE:
        state = "ORDER_ONLY"
    elif seq >= DEFAULT_FIRSTPAGE_PARTIAL:
        state = "PARTIAL"
    else:
        state = "DIVERGE"
    return {"sequence": round(seq, 4), "bag": round(bag, 4) if bag is not None else None,
            "state": state}


def def_safe_float(value: Any) -> float | None:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def def_close(a: float | None, b: float | None, rel: float = DEFAULT_REL_TOLERANCE,
              abs_tol: float = DEFAULT_ABS_TOLERANCE) -> bool | None:
    if a is None or b is None:
        return None
    return math.isclose(a, b, rel_tol=rel, abs_tol=abs_tol)


# ============================================================================
# 2 · DATE / PERIOD / NUMBER / METRIC NORMALIZATION
# ============================================================================


def def_valid_date(year: int, month: int, day: int) -> str | None:
    try:
        return dt.date(year, month, day).isoformat()
    except ValueError:
        return None


def def_parse_numeric_date(token: str) -> str | None:
    raw = re.sub(r"\D", "", def_nfkc(token))
    if len(raw) == 8:
        return def_valid_date(int(raw[:4]), int(raw[4:6]), int(raw[6:8]))
    if len(raw) == 7:
        roc = int(raw[:3])
        if 1 <= roc <= 200:
            return def_valid_date(roc + 1911, int(raw[3:5]), int(raw[5:7]))
    if len(raw) == 6:
        yy = int(raw[:2])
        year = 2000 + yy if yy <= 79 else 1900 + yy
        return def_valid_date(year, int(raw[2:4]), int(raw[4:6]))
    return None


def def_extract_date_candidates(text: str) -> list[dict[str, Any]]:
    normalized = def_nfkc(text)
    normalized = re.sub(r"\(\s*20\s*\)(\d{6})(?!\d)", r"20\1", normalized)
    found: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()

    patterns = (
        re.compile(r"(?<!\d)((?:19|20)\d{2})[年./\-](\d{1,2})[月./\-](\d{1,2})日?(?!\d)"),
        re.compile(r"(?<!\d)(1\d{2})[年./\-](\d{1,2})[月./\-](\d{1,2})日?(?!\d)"),
    )
    for idx, rx in enumerate(patterns):
        for match in rx.finditer(normalized):
            year = int(match.group(1)) + (1911 if idx == 1 else 0)
            value = def_valid_date(year, int(match.group(2)), int(match.group(3)))
            if value and (value, match.start()) not in seen:
                found.append({"value": value, "raw": match.group(0), "span": list(match.span()),
                              "calendar": "ROC" if idx == 1 else "CE"})
                seen.add((value, match.start()))

    for match in re.finditer(r"(?<![A-Za-z0-9])(\d{6,8})(?![A-Za-z0-9])", normalized):
        value = def_parse_numeric_date(match.group(1))
        if value and (value, match.start()) not in seen:
            found.append({"value": value, "raw": match.group(0), "span": list(match.span()),
                          "calendar": "ROC" if len(match.group(1)) == 7 else "CE"})
            seen.add((value, match.start()))
    return sorted(found, key=lambda x: x["span"][0])


def def_expand_two_digit_year(year: int) -> int:
    return 2000 + year if year <= 79 else 1900 + year


def def_parse_period(token: Any) -> dict[str, Any]:
    raw = def_compact_text(token)
    if not raw:
        return {"raw": raw, "kind": None, "period": None, "basis": None,
                "year": None, "quarter": None}
    value = raw.upper().replace("'", "")
    basis_map = {"A": "Actual", "E": "Estimate", "F": "Forecast"}

    date_value = def_parse_numeric_date(value) if value.isdigit() and len(value) in (6, 7, 8) else None
    if date_value:
        return {"raw": raw, "kind": "date", "period": date_value, "basis": None,
                "year": int(date_value[:4]), "quarter": None}

    match = re.fullmatch(r"(?:民國|ROC)?\s*(\d{2,3})\s*年", value, re.I)
    if match and 1 <= int(match.group(1)) <= 200:
        year = int(match.group(1)) + 1911
        return {"raw": raw, "kind": "year", "period": str(year), "basis": None,
                "year": year, "quarter": None}

    quarter_patterns = (
        re.fullmatch(r"([1-4])Q\s*(\d{2,4})([AEF])?", value),
        re.fullmatch(r"Q([1-4])\s*(\d{2,4})([AEF])?", value),
    )
    match = next((x for x in quarter_patterns if x), None)
    if match:
        quarter = int(match.group(1))
        year = int(match.group(2))
        year = year if year >= 1000 else def_expand_two_digit_year(year)
        return {"raw": raw, "kind": "quarter", "period": f"{year}-Q{quarter}",
                "basis": basis_map.get(match.group(3)), "year": year,
                "quarter": f"Q{quarter}"}
    match = re.fullmatch(r"(\d{2,4})\s*Q([1-4])([AEF])?", value)
    if match:
        year = int(match.group(1))
        year = year if year >= 1000 else def_expand_two_digit_year(year)
        quarter = int(match.group(2))
        return {"raw": raw, "kind": "quarter", "period": f"{year}-Q{quarter}",
                "basis": basis_map.get(match.group(3)), "year": year,
                "quarter": f"Q{quarter}"}

    match = re.fullmatch(r"FY[\s_\-/]?(\d{2,4})([AEF])?", value)
    if match:
        year = int(match.group(1))
        year = year if year >= 1000 else def_expand_two_digit_year(year)
        return {"raw": raw, "kind": "year", "period": str(year),
                "basis": basis_map.get(match.group(2)), "year": year, "quarter": None}
    match = re.fullmatch(r"([AEF])[\s_\-/]?(\d{2,4})", value)
    if match:
        year = int(match.group(2))
        year = year if year >= 1000 else def_expand_two_digit_year(year)
        return {"raw": raw, "kind": "year", "period": str(year),
                "basis": basis_map.get(match.group(1)), "year": year, "quarter": None}
    match = re.fullmatch(r"((?:19|20)?\d{2})[\s_\-/]?([AEF])", value)
    if match:
        year = int(match.group(1))
        year = year if year >= 1000 else def_expand_two_digit_year(year)
        return {"raw": raw, "kind": "year", "period": str(year),
                "basis": basis_map.get(match.group(2)), "year": year, "quarter": None}
    match = re.fullmatch(r"((?:19|20)\d{2})", value)
    if match:
        year = int(match.group(1))
        return {"raw": raw, "kind": "year", "period": str(year), "basis": None,
                "year": year, "quarter": None}
    return {"raw": raw, "kind": None, "period": None, "basis": None,
            "year": None, "quarter": None}


def def_period_candidates(text: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    normalized = def_nfkc(text)
    for match in PERIOD_TOKEN_PATTERN.finditer(normalized):
        raw_match = match.group(0).strip()
        # 報告日 2025/12/05 裡的 2025 不是財務期間欄。只有真正獨立的年
        # 才可進 annual-period 證據，避免「一個日期 + 一個預估年」湊成兩年。
        if re.fullmatch(r"(?:19|20)\d{2}", raw_match):
            before = normalized[max(0, match.start() - 2):match.start()]
            after = normalized[match.end():match.end() + 3]
            if re.search(r"[/.-]\s*\d", after) or re.search(r"\d\s*[/.-]$", before):
                continue
        parsed = def_parse_period(match.group(0))
        key = (parsed.get("period"), parsed.get("basis"), parsed.get("kind"))
        if parsed.get("period") and key not in seen:
            out.append(parsed)
            seen.add(key)
    return out


def def_parse_number(raw_value: Any) -> tuple[float | None, str | None]:
    raw = def_nfkc(raw_value).strip()
    if not raw or raw.lower() in {"-", "--", "—", "–", "n.a.", "na", "n/a", "nm", "null"}:
        return None, "EMPTY"
    negative = raw.startswith("(") and raw.endswith(")")
    cleaned = raw.strip("() ").replace(",", "").replace("，", "")
    cleaned = re.sub(r"(?i)(?:nt\$|twd|usd|rmb|cny|jpy|元|百萬元|千元|億元)", "", cleaned)
    cleaned = cleaned.replace("％", "%")
    match = re.search(r"[-+]?\d+(?:\.\d+)?", cleaned)
    if not match:
        return None, "NOT_NUMERIC"
    try:
        value = float(match.group(0))
    except ValueError:
        return None, "NOT_NUMERIC"
    if negative:
        value = -abs(value)
    return (value if math.isfinite(value) else None), None


def def_detect_unit(text: str, metric_name: str | None = None) -> tuple[str | None, str | None, float | None]:
    normalized = def_nfkc(text).lower()
    if metric_name in PERCENT_METRICS or (metric_name is None and ("%" in normalized or "％" in normalized)):
        return "%", None, 1.0
    if metric_name in MULTIPLE_METRICS or (metric_name is None and re.search(r"\b(?:x|倍)\b", normalized)):
        return "x", None, 1.0
    if metric_name in PER_SHARE_METRICS:
        currency = ("USD" if "usd" in normalized else "CNY" if "cny" in normalized or "rmb" in normalized
                    else "JPY" if "jpy" in normalized else "TWD")
        return f"{currency}/share", currency, 1.0
    currency = ("USD" if "usd" in normalized else "CNY" if "cny" in normalized or "rmb" in normalized
                else "JPY" if "jpy" in normalized else "TWD" if re.search(r"nt\$|twd|新台幣|台幣", normalized)
                else None)
    if re.search(r"(?i)(?:\b(?:bn|billion)\b|nt\$\s*bn|twd\s*bn)|十億", normalized):
        return (f"{currency or ''}bn".strip(), currency, 1000.0)
    if "億元" in normalized:
        return (f"{currency or ''}100m".strip(), currency, 100.0)
    if re.search(r"(?i)(?:\b(?:mn|million)\b|nt\$\s*m\b|twd\s*m\b)|百萬元", normalized):
        return (f"{currency or ''}m".strip(), currency, 1.0)
    if re.search(r"(?i)\b(?:000|thousand|k)\b|千元", normalized):
        return (f"{currency or ''}000".strip(), currency, 0.001)
    return None, currency, None


def def_alias_matches(text: Any, alias: str) -> bool:
    source = def_nfkc(text).lower()
    needle = def_nfkc(alias).lower().strip()
    if not source or not needle:
        return False
    if re.fullmatch(r"[a-z0-9 /&.\-]+", needle):
        escaped = re.escape(needle).replace(r"\ ", r"\s+")
        return re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", source) is not None
    return needle in source


def def_metric_name(raw_name: Any) -> str | None:
    text = def_nfkc(raw_name)
    if not def_compact_text(text):
        return None
    ranked: list[tuple[int, str, str]] = []
    for canonical, aliases in METRIC_ALIASES.items():
        for alias in aliases:
            key = def_normalize_compare(alias)
            if key and def_alias_matches(text, alias):
                ranked.append((len(key), canonical, alias))
    if not ranked:
        return None
    ranked.sort(key=lambda x: (-x[0], x[1]))
    return ranked[0][1]


def def_metric_hits(text: str) -> list[str]:
    return sorted({name for name in METRIC_ALIASES if def_metric_name_for(text, name)})


def def_metric_name_for(text: str, canonical: str) -> bool:
    return any(def_alias_matches(text, alias) for alias in METRIC_ALIASES[canonical])


def def_language(text: str) -> str:
    value = def_nfkc(text)
    cjk = len(re.findall(r"[\u4e00-\u9fff]", value))
    latin = len(re.findall(r"[A-Za-z]", value))
    if cjk and latin:
        ratio = cjk / max(1, cjk + latin)
        return "mixed" if 0.15 <= ratio <= 0.85 else ("中文" if ratio > 0.85 else "英文")
    return "中文" if cjk else "英文" if latin else "unknown"


def def_broker_fallback(text: str, strict: bool = False) -> str | None:
    normalized = def_nfkc(text).lower()
    for canonical, aliases in BROKER_ALIASES.items():
        for alias in sorted(aliases, key=len, reverse=True):
            a = alias.lower()
            if a.isascii() and re.fullmatch(r"[a-z]{1,4}", a):
                if re.search(rf"(?<![a-z0-9]){re.escape(a)}(?![a-z0-9])", normalized):
                    return canonical
            elif a in normalized:
                if strict and any(x in a for x in ("中信", "元大", "富邦", "統一")):
                    around = re.search(re.escape(a) + r".{0,8}(?:證券|投顧|研究|capital|securities)", normalized)
                    if not around:
                        continue
                return canonical
    return None


def def_rating_fallback(text: str) -> str | None:
    normalized = def_nfkc(text).lower()
    for canonical, aliases in RATING_ALIASES.items():
        for alias in sorted(aliases, key=len, reverse=True):
            if re.search(rf"(?<![a-z]){re.escape(alias.lower())}(?![a-z])", normalized):
                return canonical
    return None


def def_rating_change(text: str) -> str | None:
    normalized = def_nfkc(text).lower()
    rules = (
        ("INITIATED", ("初次評等", "初評", "首次覆蓋", "initiation", "initiating coverage")),
        ("UPGRADED", ("升評", "調升評等", "upgrade", "upgraded")),
        ("DOWNGRADED", ("降評", "調降評等", "downgrade", "downgraded")),
        ("MAINTAINED", ("維持評等", "重申", "maintain", "reiterate")),
    )
    for canonical, aliases in rules:
        if any(alias in normalized for alias in aliases):
            return canonical
    return None


def def_target_price_fallback(text: str, ticker: str | None = None) -> float | None:
    normalized = def_nfkc(text)
    candidates: list[tuple[int, float]] = []
    trigger = re.compile(r"(?i)(?:目標價|target\s*price|price\s*target|\bPT\b)")
    for match in trigger.finditer(normalized):
        window = normalized[match.end():match.end() + 48]
        if re.match(r"\s*[:：]?\s*(?:n\.?a\.?|not\s+rated)", window, re.I):
            continue
        number = re.search(r"(?:NT\$|TWD|USD|\$)?\s*([0-9][0-9,]*(?:\.\d+)?)", window, re.I)
        if not number:
            continue
        raw = number.group(1).replace(",", "")
        value = def_safe_float(raw)
        if value is None or value <= 0:
            continue
        if ticker and str(int(value)) == ticker and value.is_integer():
            continue
        tail = window[number.end():number.end() + 12]
        between = window[:number.start()]
        if re.match(r"\s*(?:%|％|x\b|倍|mn\b|bn\b)", tail, re.I):
            continue
        if re.search(r"上漲空間|下跌空間|upside|downside|yield", between, re.I):
            continue
        score = 10 - min(number.start(), 10)
        if re.search(r"NT\$|TWD|USD|\$|元", number.group(0), re.I):
            score += 3
        candidates.append((score, value))
    return sorted(candidates, reverse=True)[0][1] if candidates else None


def def_current_price_fallback(text: str, ticker: str | None = None) -> float | None:
    normalized = def_nfkc(text)
    rx = re.compile(r"(?i)(?:現價|收盤價|current\s*price|share\s*price|closing\s*price)"
                    r"[^0-9]{0,20}([0-9][0-9,]*(?:\.\d+)?)")
    for match in rx.finditer(normalized):
        value = def_safe_float(match.group(1).replace(",", ""))
        if value is not None and value > 0 and not (ticker and str(int(value)) == ticker):
            return value
    return None


def def_upside(target: float | None, current: float | None) -> float | None:
    if target is None or current in (None, 0):
        return None
    return round((target / current - 1.0) * 100.0, 2)


# ============================================================================
# 3 · OFFICIAL TWSE/TPEX LISTING RESOLVER
# ============================================================================


class OfficialListingResolver:
    CODE_KEYS = ("code", "ticker", "symbol", "stock_id", "證券代號", "股票代號",
                 "SecuritiesCompanyCode", "TW_TICKER")
    # Name 固定採官方簡稱；只有來源沒有簡稱欄時才退公司全名。
    NAME_KEYS = ("short_name", "stock_name", "證券名稱", "股票名稱", "公司簡稱",
                 "Name", "name", "CompanyName")
    MARKET_KEYS = ("market", "exchange", "上市櫃", "市場別", "Market")
    YF_KEYS = ("yf_ticker", "yfinance_ticker", "symbol_yf", "YF_TICKER")
    INDUSTRY_KEYS = ("industry", "industry_name", "產業別", "Industry")

    def __init__(self, listings_path: Path | None = None, firstpage_engine: Any | None = None,
                 allow_web: bool = False):
        self.records: dict[str, ListingRecord] = {}
        self.listings_path = listings_path.expanduser().resolve() if listings_path else None
        self.firstpage_engine = firstpage_engine
        self.allow_web = allow_web
        self.state: list[str] = []
        if self.listings_path:
            self._load_path(self.listings_path)

    @staticmethod
    def _pick(row: dict[str, Any], keys: Sequence[str]) -> Any:
        lowered = {str(k).lower(): v for k, v in row.items()}
        for key in keys:
            if key in row and row[key] not in (None, ""):
                return row[key]
            if key.lower() in lowered and lowered[key.lower()] not in (None, ""):
                return lowered[key.lower()]
        return None

    @staticmethod
    def _market(value: Any, yf_ticker: Any = None) -> str | None:
        raw = def_nfkc(value).upper()
        yf = def_nfkc(yf_ticker).upper()
        if raw in {"TWSE", "上市", "TSE", "TW"} or yf.endswith(".TW"):
            return "TWSE"
        if raw in {"TPEX", "上櫃", "OTC", "TWO"} or yf.endswith(".TWO"):
            return "TPEX"
        return raw or None

    def _ingest(self, rows: Iterable[dict[str, Any]], source: str) -> None:
        count = 0
        for row in rows:
            code_raw = self._pick(row, self.CODE_KEYS)
            code_match = re.search(r"(?<!\d)([1-9]\d{3})(?!\d)", def_nfkc(code_raw))
            name = def_compact_text(self._pick(row, self.NAME_KEYS))
            if not code_match or not name:
                continue
            code = code_match.group(1)
            yf = def_compact_text(self._pick(row, self.YF_KEYS)) or None
            market = self._market(self._pick(row, self.MARKET_KEYS), yf)
            if not yf and market:
                yf = f"{code}.{'TW' if market == 'TWSE' else 'TWO'}"
            rec = ListingRecord(code=code, name=name, market=market, yf_ticker=yf,
                                industry=def_compact_text(self._pick(row, self.INDUSTRY_KEYS)) or None,
                                source=source)
            if code not in self.records or not self.records[code].market:
                self.records[code] = rec
            count += 1
        self.state.append(f"{source}:{count}")

    def _load_path(self, path: Path) -> None:
        if not path.exists():
            self.state.append(f"missing:{path}")
            return
        try:
            suffix = path.suffix.lower()
            if suffix in {".csv", ".txt", ".tsv"}:
                delimiter = "\t" if suffix == ".tsv" else ","
                with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
                    self._ingest(csv.DictReader(fh, delimiter=delimiter), path.name)
            elif suffix == ".json":
                payload = json.loads(path.read_text(encoding="utf-8-sig"))
                rows: list[dict[str, Any]] = []
                if isinstance(payload, list):
                    rows = [x for x in payload if isinstance(x, dict)]
                elif isinstance(payload, dict):
                    block = payload.get("codes", payload)
                    if isinstance(block, list):
                        rows = [x for x in block if isinstance(x, dict)]
                    elif isinstance(block, dict):
                        for code, item in block.items():
                            if isinstance(item, dict):
                                rows.append({"code": code, **item})
                            else:
                                rows.append({"code": code, "name": item})
                self._ingest(rows, path.name)
            elif suffix in {".parquet", ".pq"}:
                import pandas as pd
                self._ingest(pd.read_parquet(path).to_dict("records"), path.name)
            elif suffix in {".duckdb", ".db"}:
                self._load_duckdb(path)
            else:
                self.state.append(f"unsupported listings:{path.name}")
        except Exception as exc:
            self.state.append(f"load failed:{path.name}:{type(exc).__name__}:{str(exc)[:120]}")

    def _load_duckdb(self, path: Path) -> None:
        try:
            import duckdb
        except Exception:
            self.state.append("duckdb module unavailable")
            return
        con = duckdb.connect(str(path), read_only=True)
        try:
            tables = {x[0] for x in con.execute("SHOW TABLES").fetchall()}
            for table in ("tw_universe", "tw_listings", "tw_listings_industry"):
                if table not in tables:
                    continue
                frame = con.execute(f'SELECT * FROM "{table}"').fetchdf()
                self._ingest(frame.to_dict("records"), f"{path.name}:{table}")
        finally:
            con.close()

    def resolve(self, code: str | None) -> ListingRecord | None:
        if not code or not re.fullmatch(r"[1-9]\d{3}", str(code)):
            return None
        if code in self.records:
            return self.records[code]
        engine = self.firstpage_engine
        nr = getattr(engine, "nr", None) if engine is not None else None
        if nr is None:
            return None
        try:
            name, source, _trail = nr.lookup(code, allow_web=self.allow_web)
        except Exception as exc:
            self.state.append(f"engine lookup {code} failed:{type(exc).__name__}")
            return None
        if not name:
            return None
        market = "TWSE" if "TWSE" in source else "TPEX" if "TPEX" in source else None
        rec = ListingRecord(code=code, name=str(name), market=market,
                            yf_ticker=(f"{code}.{'TW' if market == 'TWSE' else 'TWO'}"
                                       if market else None),
                            industry=getattr(nr, "industry", None), source=source)
        self.records[code] = rec
        return rec

    def roster(self) -> frozenset[str]:
        return frozenset(self.records)

    def diagnostics(self) -> dict[str, Any]:
        return {"records": len(self.records), "sources": list(self.state),
                "allow_web": self.allow_web}


def def_same_company_name(candidate: str | None, official: str | None) -> bool | None:
    a, b = def_normalize_compare(candidate), def_normalize_compare(official)
    if not a or not b:
        return None
    for suffix in ("股份有限公司", "有限公司", "控股公司", "控股", "公司", "ky"):
        a, b = a.replace(def_normalize_compare(suffix), ""), b.replace(def_normalize_compare(suffix), "")
    if a == b:
        return True
    if min(len(a), len(b)) >= 2 and (a in b or b in a):
        return True
    short, long_text = (a, b) if len(a) <= len(b) else (b, a)
    if len(short) >= 2 and len(long_text) >= 4 and short[0] == long_text[0]:
        iterator = iter(long_text)
        return all(ch in iterator for ch in short)
    return False


# ============================================================================
# 4 · FILENAME ENGINE ADAPTER
# ============================================================================


class FilenameEngineAdapter:
    def __init__(self, module: Any | None, module_path: Path | None,
                 resolver: OfficialListingResolver | None = None):
        self.module = module
        self.module_path = module_path
        self.engine: Any | None = None
        self.state = "fallback"
        if module is not None and hasattr(module, "FirstPageEngine"):
            try:
                official = resolver.roster() if resolver else None
                self.engine = module.FirstPageEngine(official_set=official or None,
                                                     auto_hub=False)
                self.state = f"public-contract:{module_path.name if module_path else 'module'}"
            except Exception as exc:
                self.state = f"engine init failed:{type(exc).__name__}:{str(exc)[:100]}"

    def bind_resolver(self, resolver: OfficialListingResolver) -> None:
        if self.engine is not None:
            try:
                self.engine.tf.official_set = set(resolver.roster()) or None
                self.engine.tf.roster = resolver.roster()
                self.engine.tf.roster_state = (f"official listings {len(resolver.roster())}"
                                               if resolver.roster() else "official listings unavailable")
                self.engine.nr.tk2name.update({k: v.name for k, v in resolver.records.items()})
            except Exception:
                pass

    def facts(self, filename: str) -> dict[str, Any]:
        if self.engine is not None and hasattr(self.engine, "filename_facts"):
            try:
                facts = dict(self.engine.filename_facts(filename))
                facts["adapter"] = self.state
                return facts
            except Exception as exc:
                self.state = f"public contract failed:{type(exc).__name__}:{str(exc)[:100]}"
        facts = self._fallback(filename)
        facts["adapter"] = self.state
        return facts

    @staticmethod
    def _strip_upload_prefix(stem: str) -> str:
        return re.sub(r"^(?:[0-9a-f]{8}-){4}[0-9a-f]{8,12}[-_]", "", stem, flags=re.I)

    def _fallback(self, filename: str) -> dict[str, Any]:
        stem = self._strip_upload_prefix(Path(filename).stem)
        normalized = def_nfkc(stem)
        tokens = re.findall(r"[\u4e00-\u9fff]+(?:-KY)?|[A-Za-z]+|\d+", normalized)
        dates = [x["value"] for x in def_extract_date_candidates(normalized)]
        tickers: list[str] = []
        for match in re.finditer(r"(?<![A-Za-z0-9])([1-9]\d{3})(?:(?:TWO|TT|TW|T)(?![A-Za-z0-9])|(?![A-Za-z0-9]))",
                                 normalized, re.I):
            code = match.group(1)
            if code not in tickers:
                tickers.append(code)
        broker = def_broker_fallback(normalized)
        lowered = normalized.lower()
        if any(x.lower() in lowered for x in STRONG_OUTLOOK_KEYWORDS):
            kind, reason = "大盤晨報", "filename outlook marker"
        elif any(x.lower() in lowered for x in STRONG_INDUSTRY_KEYWORDS):
            kind, reason = "產業", "filename industry marker"
        elif any(x.lower() in lowered for x in OTHER_REPORT_KEYWORDS):
            kind, reason = "研討會", "filename other marker"
        elif tickers:
            kind, reason = "個股", "bounded 4-digit candidate"
        elif any(x.lower() in lowered for x in WEAK_INDUSTRY_KEYWORDS):
            kind, reason = "產業", "filename thematic marker"
        else:
            kind, reason = "未分類", "no decisive marker"
        name_hint = self._name_hint(normalized, tickers[0] if tickers else None, broker)
        return {"ticker": tickers[0] if tickers else None, "broker": broker,
                "date": dates[0] if dates else None, "name_hint": name_hint,
                "kind": kind, "kind_reason": reason, "tickers": tickers,
                "dates": dates, "tokens": tokens}

    @staticmethod
    def _name_hint(filename: str, ticker: str | None, broker: str | None) -> str | None:
        if not ticker:
            return None
        lines = re.split(r"[-_+ ,，。、:：;；/\\()[\]{}【】]+", filename)
        generic = ("個股", "報告", "研究", "評等", "目標價", "初評", "更新", "法說",
                   "buy", "hold", "sell", "report", "research", "update")
        try:
            pos = next(i for i, token in enumerate(lines) if ticker in token)
        except StopIteration:
            return None
        candidates = lines[pos:pos + 3] + list(reversed(lines[max(0, pos - 2):pos]))
        for token in candidates:
            text = def_compact_text(token.replace(ticker, ""))
            text = re.sub(r"(?i)\b(?:TT|TW|TWO)\b", "", text).strip()
            if not text or text.isdigit() or any(x.lower() in text.lower() for x in generic):
                continue
            if broker and def_broker_fallback(text) == broker:
                continue
            if re.search(r"[\u4e00-\u9fffA-Za-z]", text):
                return text
        return None

    def broker_from_text(self, text: str, strict: bool = True) -> str | None:
        if self.engine is not None:
            try:
                return self.engine.brd.broker_normalize(text, strict=strict)
            except Exception:
                pass
        return def_broker_fallback(text, strict=strict)

    def rating_from_text(self, text: str) -> str | None:
        if self.engine is not None:
            try:
                result = self.engine.brd.validate_rating(text)
                if isinstance(result, dict):
                    return result.get("canonical")
            except Exception:
                pass
        return def_rating_fallback(text)

    def target_price_from_text(self, text: str, ticker: str | None = None) -> float | None:
        if self.engine is not None:
            try:
                return self.engine.fv.extract_target_price(text, ticker=ticker)
            except Exception:
                pass
        return def_target_price_fallback(text, ticker=ticker)

    def diagnostics(self) -> dict[str, Any]:
        return {"state": self.state,
                "module": str(self.module_path) if self.module_path else None}


# ============================================================================
# 5 · PAGE EXTRACTION（first page 與財務頁共用同一套版面規則）
# ============================================================================


def def_is_excluded_line(text: str) -> bool:
    value = def_compact_text(text).lower()
    return any(value.startswith(x.lower()) for x in FOOTNOTE_PREFIXES + APPENDIX_PREFIXES)


def def_repair_lines(lines: Sequence[str]) -> str:
    output: list[str] = []
    terminators = ("。", ".", "!", "?", "！", "？", ":", "：", "%", "％", "」", ")", "】")
    for raw in lines:
        line = def_compact_text(raw)
        if not line or def_is_excluded_line(line):
            continue
        if output and not output[-1].endswith(terminators):
            previous = output.pop()
            if previous.endswith("-") and line[:1].isascii():
                output.append(previous[:-1] + line)
            elif previous[-1:].isascii() and line[:1].isascii():
                output.append(previous + " " + line)
            else:
                output.append(previous + line)
        else:
            output.append(line)
    return "\n".join(output)


def def_table_clean(table: Any, max_rows: int = DEFAULT_MAX_TABLE_ROWS) -> list[list[str]]:
    rows: list[list[str]] = []
    if table is None:
        return rows
    for raw_row in list(table)[:max_rows]:
        if raw_row is None:
            continue
        row = [def_compact_text(cell) for cell in list(raw_row)]
        if any(row):
            rows.append(row)
    return rows


def def_table_signature(table: Sequence[Sequence[str]]) -> str:
    payload = "\n".join("\x1f".join(def_normalize_compare(cell) for cell in row)
                        for row in table)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def def_extract_fitz_page(page: Any, page_number: int, config: EngineConfig,
                           with_tables: bool = False) -> PageEvidence:
    width, height = float(page.rect.width), float(page.rect.height)
    zones: dict[str, list[dict[str, Any]]] = {"header": [], "right": [], "body": [], "footer": []}
    heads: list[dict[str, Any]] = []
    footer_count = 0
    try:
        block_data = page.get_text("dict").get("blocks", [])
    except Exception:
        block_data = []
    for block in block_data:
        if block.get("type") != 0:
            continue
        lines: list[str] = []
        max_size, bold = 0.0, False
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            text = "".join(str(span.get("text") or "") for span in spans).strip()
            if text:
                lines.append(text)
            for span in spans:
                size = def_safe_float(span.get("size")) or 0.0
                max_size = max(max_size, size)
                font = str(span.get("font") or "")
                flags = int(span.get("flags") or 0)
                if flags & 16 or "bold" in font.lower():
                    bold = True
        if not lines:
            continue
        x0, y0, x1, y1 = [float(x) for x in block.get("bbox", (0, 0, 0, 0))]
        record = {"lines": lines, "x0": x0, "y0": y0, "x1": x1, "y1": y1,
                  "size": max_size, "bold": bold}
        line_text = " ".join(lines)
        in_footer = y1 >= (1.0 - config.footer_ratio) * height
        too_small = max_size and max_size < config.min_font_pt
        excluded = def_is_excluded_line(line_text)
        if in_footer or too_small or excluded:
            zones["footer"].append(record)
            footer_count += len(line_text)
            continue
        wide = (x1 - x0) > config.wide_block_ratio * width
        if wide and y0 < config.header_ratio * height:
            zone = "header"
        elif x0 >= config.right_column_x_ratio * width:
            zone = "right"
        else:
            zone = "body"
        zones[zone].append(record)
        if max_size >= 13.0 or (bold and max_size >= 10.5):
            heads.append({"text": line_text[:300], "size": round(max_size, 2), "bold": bold,
                          "zone": zone, "y": round(y0, 2)})
    for items in zones.values():
        items.sort(key=lambda x: (round(x["y0"], 1), x["x0"]))
    header = "\n".join(line for item in zones["header"] for line in item["lines"])
    right = "\n".join(line for item in zones["right"] for line in item["lines"])
    body = def_repair_lines([line for item in zones["body"] for line in item["lines"]])
    fitz_text = "\n".join(x for x in (header, right, body) if x.strip())
    tables: list[list[list[str]]] = []
    if with_tables:
        try:
            # PyMuPDF 1.26 會主動把 pymupdf_layout 推薦字樣印到 stdout；
            # 若不攔住會污染 --json-stdout 與 PowerShell 管線。
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                finder = page.find_tables()
            for tab in list(getattr(finder, "tables", []))[:config.max_tables_per_page]:
                clean = def_table_clean(tab.extract(), config.max_table_rows)
                if clean:
                    tables.append(clean)
        except Exception:
            pass
    return PageEvidence(page_number=page_number, width=width, height=height,
                        header=header, right=right, body=body,
                        footer_char_count=footer_count, heads=heads,
                        fitz_text=fitz_text, fitz_tables=tables)


def def_extract_plumber_page(page: Any, page_number: int, config: EngineConfig,
                              with_tables: bool = False) -> dict[str, Any]:
    width, height = float(page.width), float(page.height)
    zones: dict[str, list[str]] = {"header": [], "right": [], "body": [], "footer": []}
    try:
        words = page.extract_words(use_text_flow=False, extra_attrs=["size"])
    except Exception:
        try:
            words = page.extract_words(use_text_flow=False)
        except Exception:
            words = []
    line_map: dict[int, list[dict[str, Any]]] = {}
    for word in words:
        key = round(float(word.get("top", 0.0)) / 4.0)
        line_map.setdefault(key, []).append(word)
    for key in sorted(line_map):
        ordered = sorted(line_map[key], key=lambda x: float(x.get("x0", 0.0)))
        if not ordered:
            continue
        parts, current = [], [ordered[0]]
        for word in ordered[1:]:
            gap = float(word.get("x0", 0.0)) - float(current[-1].get("x1", 0.0))
            if gap > 0.15 * width:
                parts.append(current)
                current = [word]
            else:
                current.append(word)
        parts.append(current)
        for segment in parts:
            x0 = min(float(x.get("x0", 0.0)) for x in segment)
            x1 = max(float(x.get("x1", 0.0)) for x in segment)
            top = min(float(x.get("top", 0.0)) for x in segment)
            bottom = max(float(x.get("bottom", 0.0)) for x in segment)
            sizes = [def_safe_float(x.get("size")) for x in segment]
            max_size = max((x for x in sizes if x is not None), default=10.0)
            text = " ".join(str(x.get("text") or "") for x in segment).strip()
            if not text:
                continue
            in_footer = bottom >= (1.0 - config.footer_ratio) * height
            if in_footer or max_size < config.min_font_pt or def_is_excluded_line(text):
                zones["footer"].append(text)
                continue
            wide = (x1 - x0) > config.wide_block_ratio * width
            if wide and top < config.header_ratio * height:
                zone = "header"
            elif x0 >= config.right_column_x_ratio * width:
                zone = "right"
            else:
                zone = "body"
            zones[zone].append(text)
    tables: list[list[list[str]]] = []
    if with_tables:
        try:
            for table in (page.extract_tables() or [])[:config.max_tables_per_page]:
                clean = def_table_clean(table, config.max_table_rows)
                if clean:
                    tables.append(clean)
        except Exception:
            pass
    return {"header": "\n".join(zones["header"]), "right": "\n".join(zones["right"]),
            "body": def_repair_lines(zones["body"]),
            "footer_char_count": sum(len(x) for x in zones["footer"]),
            "tables": tables}


def def_score_financial_page(page: PageEvidence, config: EngineConfig) -> tuple[float, str, dict[str, Any]]:
    text = page.fitz_text
    lowered = def_nfkc(text).lower()
    metric_hits = def_metric_hits(text)
    periods = def_period_candidates(text)
    annual = sorted({x["year"] for x in periods if x.get("kind") == "year" and x.get("year")})
    quarters = sorted({x["period"] for x in periods if x.get("kind") == "quarter"})
    keywords = sorted({x for x in FINANCIAL_PAGE_KEYWORDS if x.lower() in lowered})
    numbers = re.findall(r"(?<![A-Za-z])[-+()]?\d[\d,]*(?:\.\d+)?%?", text)
    appendix = any(lowered.lstrip().startswith(x.lower()) for x in APPENDIX_PREFIXES)
    disclaimer = sum(1 for x in FOOTNOTE_PREFIXES if x.lower() in lowered)
    score = min(len(metric_hits), 8) * 0.65
    score += min(len(annual), 6) * 0.55
    score += min(len(quarters), 6) * 0.30
    score += min(len(keywords), 3) * 1.25
    score += min(len(numbers) / 25.0, 1.5)
    if appendix:
        score -= 6.0
    score -= min(disclaimer * 0.5, 2.0)
    if (len(annual) >= config.min_annual_periods
            and len(metric_hits) >= config.min_financial_metrics):
        role = "ANNUAL_FINANCIAL"
    elif quarters and len(metric_hits) >= config.min_financial_metrics:
        role = "QUARTERLY_FINANCIAL"
    elif any(x in metric_hits for x in ("PER", "PBR", "EV_EBITDA", "TargetPrice")) and periods:
        role = "VALUATION"
    else:
        role = "OTHER"
    evidence = {"metric_hits": metric_hits, "periods": periods, "annual_years": annual,
                "quarters": quarters, "keywords": keywords, "number_count": len(numbers),
                "appendix": appendix, "disclaimer_hits": disclaimer}
    return round(score, 3), role, evidence


class DocumentPageExtractor:
    def __init__(self, config: EngineConfig, eng072_module: Any | None = None,
                 eng072_path: Path | None = None):
        self.config = config
        self.eng072_module = eng072_module
        self.eng072_path = eng072_path
        self.state: list[str] = []

    def extract_pdf(self, path: Path) -> tuple[PageEvidence, list[PageEvidence], dict[str, Any]]:
        try:
            import fitz
        except Exception as exc:
            raise RuntimeError("PyMuPDF(fitz) is required for PDF page extraction") from exc
        with fitz.open(str(path)) as document:
            total_page_count = document.page_count
            page_count = min(total_page_count, self.config.max_pages)
            if page_count < 1:
                raise ValueError("PDF has no pages")
            pages = [def_extract_fitz_page(document[index], index + 1, self.config, with_tables=False)
                     for index in range(page_count)]
        for page in pages:
            page.score, page.role, page.score_evidence = def_score_financial_page(page, self.config)
        financial_indices = {page.page_number - 1 for page in pages
                             if page.score >= self.config.financial_page_score and page.role != "OTHER"}
        candidate_indices = {0} | financial_indices
        plumber_error = ""
        try:
            import pdfplumber
            with pdfplumber.open(str(path)) as pdf:
                for index in sorted(candidate_indices):
                    if index >= len(pdf.pages):
                        continue
                    data = def_extract_plumber_page(pdf.pages[index], index + 1, self.config,
                                                    with_tables=index in financial_indices)
                    page = pages[index]
                    page.plumber_text = "\n".join(x for x in
                                                   (data["header"], data["right"], data["body"])
                                                   if x.strip())
                    page.plumber_tables = data["tables"]
                    page.compare = def_similarity(page.fitz_text, page.plumber_text)
        except Exception as exc:
            plumber_error = f"pdfplumber unavailable/failed:{type(exc).__name__}:{str(exc)[:120]}"
        with fitz.open(str(path)) as document:
            for index in sorted(financial_indices):
                if index < document.page_count:
                    table_page = def_extract_fitz_page(document[index], index + 1, self.config,
                                                        with_tables=True)
                    pages[index].fitz_tables = table_page.fitz_tables
        first = pages[0]
        eng072 = self._eng072_evidence(path)
        annual_pages = [page for page in pages if page.page_number - 1 in financial_indices]
        meta = {"page_count": page_count, "candidate_pages": [x.page_number for x in annual_pages],
                "pdfplumber": plumber_error or "OK", "eng072": eng072,
                "truncated": total_page_count > self.config.max_pages}
        return first, annual_pages, meta

    def _eng072_evidence(self, path: Path) -> dict[str, Any]:
        module = self.eng072_module
        if module is None:
            return {"state": "ABSENT", "module": str(self.eng072_path) if self.eng072_path else None}
        if path.suffix.lower() != ".pdf":
            return {"state": "NOT_PDF"}
        try:
            zones = module.extract_page1_zones(path)
            plumber = module.extract_page1_plumber(path) if zones else None
            if not zones:
                return {"state": "NO_ZONES"}
            comparison = module.compare_zones(zones, plumber) if plumber else {}
            return {"state": "OK", "header": zones.get("header", ""),
                    "right": zones.get("right", ""), "body": zones.get("body", ""),
                    "footer_char_count": len(zones.get("footer", "")),
                    "compare": comparison, "table_count": len((plumber or {}).get("tables", [])),
                    "module": self.eng072_path.name if self.eng072_path else "in-memory"}
        except Exception as exc:
            return {"state": "FAILED", "why": f"{type(exc).__name__}:{str(exc)[:160]}"}

    def extract_non_pdf(self, path: Path) -> tuple[PageEvidence, list[PageEvidence], dict[str, Any]]:
        text, tag = "", "UNSUPPORTED"
        module = self.eng072_module
        try:
            if path.suffix.lower() == ".docx":
                if module is not None and hasattr(module, "extract_docx_head"):
                    text, tag = module.extract_docx_head(path)
                else:
                    text, tag = def_docx_head_fallback(path), "DOCX_ZIP_FALLBACK"
            elif path.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp", ".gif"}:
                if module is not None and hasattr(module, "extract_image_page1"):
                    text, tag = module.extract_image_page1(path)
                else:
                    tag = "IMAGE_NEEDS_OCR"
        except Exception as exc:
            tag = f"EXTRACT_FAILED:{type(exc).__name__}"
        page = PageEvidence(page_number=1, width=0, height=0, body=text, fitz_text=text)
        return page, [], {"page_count": 1, "candidate_pages": [], "tag": tag,
                          "eng072": {"state": "DIRECT_NON_PDF" if module else "ABSENT"}}

    def diagnostics(self) -> dict[str, Any]:
        return {"eng072_module": str(self.eng072_path) if self.eng072_path else None,
                "state": list(self.state)}


def def_docx_head_fallback(path: Path, max_paragraphs: int = 30) -> str:
    with zipfile.ZipFile(path) as archive:
        xml = archive.read("word/document.xml")
    root = ElementTree.fromstring(xml)
    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    paragraphs: list[str] = []
    for paragraph in root.iter(namespace + "p"):
        text = "".join(node.text or "" for node in paragraph.iter(namespace + "t")).strip()
        if text:
            paragraphs.append(text)
        if len(paragraphs) >= max_paragraphs:
            break
    return "\n".join(paragraphs)


# ============================================================================
# 6 · FIRST-PAGE ANCHORS
# ============================================================================


def def_extract_ticker_candidates(text: str) -> list[str]:
    normalized = def_nfkc(text)
    found: list[str] = []
    patterns = (
        re.compile(r"(?<![A-Za-z0-9])([1-9]\d{3})\s*(?:TWO|TT|TW|T)(?![A-Za-z0-9])", re.I),
        re.compile(r"(?i)(?:股票代號|證券代號|stock\s*code|ticker)\s*[:：#]?\s*([1-9]\d{3})(?!\d)"),
        re.compile(r"(?<![A-Za-z0-9])([1-9]\d{3})(?![A-Za-z0-9])"),
    )
    for rx in patterns:
        for match in rx.finditer(normalized):
            code = match.group(1)
            if code not in found:
                found.append(code)
    return found


def def_extract_company_candidates(text: str, tickers: Sequence[str], broker: str | None) -> list[str]:
    lines = [def_compact_text(x) for x in def_nfkc(text).splitlines() if def_compact_text(x)]
    generic = ("report", "research", "target", "price", "rating", "目標價", "評等", "報告",
               "證券", "投顧", "研究部", "股份有限公司", "company update", "initiation")
    candidates: list[str] = []
    for line in lines[:30]:
        if tickers and not any(code in line for code in tickers):
            continue
        fragments = re.findall(r"[\u4e00-\u9fff]{2,12}(?:-KY)?|[A-Za-z][A-Za-z&.\- ]{2,35}", line)
        for fragment in fragments:
            value = def_compact_text(fragment)
            if any(word.lower() in value.lower() for word in generic):
                continue
            if broker and def_broker_fallback(value) == broker:
                continue
            if value not in candidates:
                candidates.append(value)
    return candidates[:8]


def def_extract_title(page: PageEvidence) -> str | None:
    heads = sorted(page.heads, key=lambda x: (-float(x.get("size") or 0), float(x.get("y") or 0)))
    for head in heads:
        text = def_compact_text(head.get("text"))
        if len(text) >= 4 and not def_is_excluded_line(text):
            return text
    for line in (page.header + "\n" + page.body).splitlines():
        text = def_compact_text(line)
        if len(text) >= 4 and not def_is_excluded_line(text):
            return text
    return None


def def_extract_thesis(body: str) -> str | None:
    repaired = def_repair_lines(body.splitlines())
    sentences = re.split(r"(?<=[。.!?！？])\s*", repaired)
    for sentence in sentences:
        text = def_compact_text(sentence)
        if 18 <= len(text) <= 500 and not def_is_excluded_line(text):
            return text
    return None


def def_extract_contacts(text: str) -> tuple[str | None, str | None]:
    email = re.search(r"(?i)\b([A-Za-z][A-Za-z0-9._%+\-]{1,60})@([A-Za-z0-9.\-]+\.[A-Za-z]{2,})\b", text)
    analyst = email.group(1).replace(".", " ").replace("_", " ").title() if email else None
    department_match = re.search(r"(?i)(證券研究部|研究部|equity\s+research|research\s+department)", text)
    department = department_match.group(1) if department_match else None
    return analyst, department


def def_report_type(filename_kind: str | None, title: str | None, anchor_text: str) -> tuple[str, str]:
    combined = def_nfkc(" ".join(x for x in (title, anchor_text[:1200]) if x)).lower()
    if any(x.lower() in combined for x in STRONG_OUTLOOK_KEYWORDS):
        return REPORT_TYPE_OUTLOOK, "first-page outlook marker"
    if any(x.lower() in combined for x in STRONG_INDUSTRY_KEYWORDS):
        return REPORT_TYPE_INDUSTRY, "first-page industry marker"
    if any(x.lower() in combined for x in OTHER_REPORT_KEYWORDS):
        return REPORT_TYPE_OTHER, "first-page conference marker"
    mapped = REPORT_TYPE_MAP.get(def_nfkc(filename_kind).lower())
    if mapped:
        return mapped, "filename engine"
    if any(x.lower() in combined for x in WEAK_INDUSTRY_KEYWORDS):
        return REPORT_TYPE_INDUSTRY, "first-page thematic marker without stock identity"
    return REPORT_TYPE_OTHER, "no decisive report-type marker"


def def_first_page_facts(page: PageEvidence, filename_facts: dict[str, Any],
                         adapter: FilenameEngineAdapter, eng072: dict[str, Any]) -> dict[str, Any]:
    canonical_text = "\n".join(x for x in (page.header, page.right, page.body) if x.strip())
    anchor_text = "\n".join(x for x in (page.header, page.right, page.body[:1800]) if x.strip())
    title = def_extract_title(page)
    report_type, type_reason = def_report_type(filename_facts.get("kind"), title, anchor_text)
    tickers = def_extract_ticker_candidates(anchor_text)
    broker = adapter.broker_from_text(anchor_text, strict=True)
    dates = def_extract_date_candidates(anchor_text)
    rating = adapter.rating_from_text(anchor_text)
    ticker_hint = filename_facts.get("ticker")
    target = adapter.target_price_from_text(anchor_text, ticker=ticker_hint)
    current = def_current_price_fallback(anchor_text, ticker=ticker_hint)
    companies = def_extract_company_candidates(anchor_text, tickers, broker)
    analyst, department = def_extract_contacts(anchor_text)
    source_consensus: dict[str, Any] = {}
    if page.compare:
        source_consensus["pymupdf_vs_pdfplumber"] = dict(page.compare)
    if eng072.get("state") == "OK":
        eng_text = "\n".join(x for x in (eng072.get("header", ""), eng072.get("right", ""),
                                          eng072.get("body", "")) if str(x).strip())
        source_consensus["canonical_vs_eng072"] = def_similarity(canonical_text, eng_text)
    return {
        "report_type": report_type, "report_type_reason": type_reason,
        "title": title, "text": canonical_text, "anchor_text": anchor_text,
        "ticker_candidates": tickers, "date_candidates": dates,
        "broker": broker, "company_candidates": companies, "rating": rating,
        "rating_change": def_rating_change(" ".join(x for x in (title, anchor_text) if x)),
        "target_price": target, "current_price": current,
        "upside_downside_pct": def_upside(target, current),
        "analyst": analyst, "department": department,
        "investment_thesis": def_extract_thesis(page.body),
        "language": def_language(canonical_text), "consensus": source_consensus,
        "footer_excluded_chars": page.footer_char_count + int(eng072.get("footer_char_count") or 0),
    }


# ============================================================================
# 7 · FINANCIAL TABLE RESTORATION AND CONSENSUS
# ============================================================================


def def_rectangular(table: Sequence[Sequence[str]]) -> list[list[str]]:
    width = max((len(row) for row in table), default=0)
    return [list(row) + [""] * (width - len(row)) for row in table]


def def_header_periods(table: Sequence[Sequence[str]]) -> tuple[int | None, dict[int, dict[str, Any]]]:
    rows = def_rectangular(table)
    best_index, best_map, best_score = None, {}, -1
    for index, row in enumerate(rows[:4]):
        merged = list(row)
        if index + 1 < min(len(rows), 4):
            merged = [def_compact_text(f"{a} {b}") for a, b in zip(row, rows[index + 1])]
        period_map: dict[int, dict[str, Any]] = {}
        for column, cell in enumerate(merged):
            parsed = def_parse_period(cell)
            if parsed.get("period"):
                period_map[column] = parsed
            else:
                candidates = def_period_candidates(cell)
                if len(candidates) == 1:
                    period_map[column] = candidates[0]
        score = len(period_map)
        if score > best_score:
            best_index, best_map, best_score = index, period_map, score
    return (best_index, best_map) if best_map else (None, {})


def def_table_context_unit(table: Sequence[Sequence[str]], page_text: str) -> str:
    first = " ".join(" ".join(row) for row in list(table)[:4])
    return f"{first} {page_text[:1200]}"


def def_parse_financial_table(table: Sequence[Sequence[str]], page: PageEvidence,
                              engine: str, table_ordinal: int) -> list[FinancialObservation]:
    rows = def_rectangular(def_table_clean(table))
    header_index, period_map = def_header_periods(rows)
    if header_index is None or not period_map:
        return []
    first_period_column = min(period_map)
    table_id = def_stable_id("TBL", page.page_number, engine, table_ordinal,
                             def_table_signature(rows))
    context = def_table_context_unit(rows, page.fitz_text)
    observations: list[FinancialObservation] = []
    for row_index in range(header_index + 1, len(rows)):
        row = rows[row_index]
        metric_raw = def_compact_text(" ".join(cell for cell in row[:first_period_column] if cell))
        metric = def_metric_name(metric_raw)
        if not metric:
            continue
        unit, currency, scale = def_detect_unit(f"{metric_raw} {context}", metric)
        for column, period in period_map.items():
            if column >= len(row):
                continue
            value_raw = def_compact_text(row[column])
            if not value_raw:
                continue
            value, _error = def_parse_number(value_raw)
            standardized = value
            if value is not None and scale is not None and metric not in PERCENT_METRICS | MULTIPLE_METRICS | PER_SHARE_METRICS:
                standardized = round(value * scale, 6)
            observations.append(FinancialObservation(
                metric_name=metric, metric_name_raw=metric_raw,
                metric_category=METRIC_CATEGORY.get(metric, "Operating Metric"),
                period_raw=str(period.get("raw") or ""), period_type=period.get("kind"),
                fiscal_year=period.get("year"), fiscal_quarter=period.get("quarter"),
                estimate_flag=period.get("basis"), value=standardized, value_raw=value_raw,
                unit=unit, currency=currency, scale=scale, page_number=page.page_number,
                table_id=table_id, row_index=row_index, column_index=column,
                engine=engine, source_text=f"{metric_raw} | {period.get('raw')} | {value_raw}"))
    return observations


def def_extract_financial_observations(pages: Sequence[PageEvidence]) -> list[FinancialObservation]:
    observations: list[FinancialObservation] = []
    for page in pages:
        for ordinal, table in enumerate(page.fitz_tables):
            observations.extend(def_parse_financial_table(table, page, "pymupdf.find_tables", ordinal))
        for ordinal, table in enumerate(page.plumber_tables):
            observations.extend(def_parse_financial_table(table, page, "pdfplumber.extract_tables", ordinal))
    return observations


def def_observation_key(obs: FinancialObservation) -> tuple[str, str, str]:
    period = (f"{obs.fiscal_year}-{obs.fiscal_quarter}" if obs.fiscal_quarter
              else str(obs.fiscal_year or obs.period_raw))
    return obs.metric_category, obs.metric_name, period


def def_numeric_consensus(observations: Sequence[FinancialObservation],
                          config: EngineConfig) -> tuple[float | None, str, float,
                                                         list[str], dict[str, Any]]:
    values = [x.value for x in observations if x.value is not None]
    engines = sorted({x.engine for x in observations if x.value is not None})
    issues: list[str] = []
    evidence = {"engines": engines, "values": [x.value for x in observations],
                "raw": [x.value_raw for x in observations],
                "locations": [{"page": x.page_number, "table": x.table_id,
                               "row": x.row_index, "column": x.column_index,
                               "engine": x.engine} for x in observations]}
    if not values:
        return None, "REVIEW", 0.30, ["VALUE_PARSE_FAILED"], evidence
    representative = statistics.median(values)
    conflicts = [x for x in values if not def_close(x, representative, config.rel_tolerance,
                                                     config.abs_tolerance)]
    if conflicts:
        issues.append("MULTI_ENGINE_VALUE_CONFLICT")
        return None, "FAIL", 0.10, issues, evidence
    if len(engines) >= 2:
        return round(representative, 6), "PASS", 0.96, issues, evidence
    issues.append("SINGLE_TABLE_ENGINE")
    return round(representative, 6), "REVIEW", 0.72, issues, evidence


def def_make_financial_rows(observations: Sequence[FinancialObservation],
                            identity: dict[str, Any], file_id: str, report_id: str,
                            run_id: str, now: str, config: EngineConfig) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[FinancialObservation]] = collections.defaultdict(list)
    for obs in observations:
        groups[def_observation_key(obs)].append(obs)
    rows: list[dict[str, Any]] = []
    for (category, metric, period_key), items in sorted(groups.items()):
        value, status, confidence, issues, evidence = def_numeric_consensus(items, config)
        first = sorted(items, key=lambda x: (x.page_number, x.table_id, x.row_index, x.column_index))[0]
        financial_id = def_stable_id("FIN", report_id, category, metric, period_key)
        row = {column: None for column in FINANCIAL_COLUMNS}
        row.update({
            "FinancialRowID": financial_id, "FileID": file_id, "ReportID": report_id,
            "TW_TICKER": identity.get("ticker"), "YF_TICKER": identity.get("yf_ticker"),
            "Name": identity.get("name"), "ReportDate": identity.get("report_date"),
            "Broker": identity.get("broker"), "PeriodType": first.period_type,
            "FiscalYear": first.fiscal_year, "FiscalQuarter": first.fiscal_quarter,
            "PeriodLabelRaw": first.period_raw, "EstimateFlag": first.estimate_flag,
            "MetricCategory": category, "MetricName": metric,
            "MetricNameRaw": first.metric_name_raw, "Value": value,
            "ValueRaw": " | ".join(dict.fromkeys(x.value_raw for x in items)),
            "Unit": first.unit, "Currency": first.currency, "Scale": first.scale,
            "PageNumber": min(x.page_number for x in items),
            "TableID": ";".join(sorted({x.table_id for x in items})),
            "RowIndex": min(x.row_index for x in items),
            "ColumnIndex": min(x.column_index for x in items),
            "SourceText": " || ".join(dict.fromkeys(x.source_text for x in items))[:2000],
            "ConfidenceScore": confidence, "ValidationStatus": status,
            "ValidationIssues": ";".join(issues),
            "EvidenceJson": def_json(evidence),
            "CreatedAt": now, "UpdatedAt": now, "RunID": run_id,
            "SchemaVersion": SCHEMA_VERSION,
        })
        if metric in row:
            row[metric] = value
        rows.append(row)
    def_apply_growth_rates(rows)
    def_apply_financial_formula_checks(rows, config)
    return rows


def def_apply_growth_rates(rows: list[dict[str, Any]]) -> None:
    groups: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    for row in rows:
        if row.get("FiscalYear") and not row.get("FiscalQuarter") and row.get("Value") is not None:
            groups[str(row.get("MetricName"))].append(row)
    for metric_rows in groups.values():
        metric_rows.sort(key=lambda x: int(x["FiscalYear"]))
        for previous, current in zip(metric_rows, metric_rows[1:]):
            pv, cv = def_safe_float(previous.get("Value")), def_safe_float(current.get("Value"))
            if pv not in (None, 0) and cv is not None:
                current["YoY"] = round((cv / pv - 1.0) * 100.0, 2)


def def_apply_financial_formula_checks(rows: list[dict[str, Any]], config: EngineConfig) -> None:
    by_period: dict[tuple[Any, Any], dict[str, dict[str, Any]]] = collections.defaultdict(dict)
    for row in rows:
        by_period[(row.get("FiscalYear"), row.get("FiscalQuarter"))][str(row.get("MetricName"))] = row
    for period, metrics in by_period.items():
        def check_ratio(numerator: str, denominator: str, margin: str) -> None:
            n = def_safe_float((metrics.get(numerator) or {}).get("Value"))
            d = def_safe_float((metrics.get(denominator) or {}).get("Value"))
            m = def_safe_float((metrics.get(margin) or {}).get("Value"))
            if n is None or d in (None, 0) or m is None:
                return
            expected = n / d * 100.0
            if not def_close(expected, m, config.formula_tolerance, 0.5):
                def_add_row_issue(metrics[margin], f"FORMULA_MISMATCH:{margin}!={numerator}/{denominator}")

        check_ratio("GrossProfit", "Revenue", "GrossMargin")
        check_ratio("OperatingProfit", "Revenue", "OperatingMargin")
        check_ratio("PretaxIncome", "Revenue", "PretaxMargin")
        check_ratio("NetIncome", "Revenue", "NetMargin")

        assets = def_safe_float((metrics.get("TotalAssets") or {}).get("Value"))
        liabilities = def_safe_float((metrics.get("TotalLiabilities") or {}).get("Value"))
        equity = def_safe_float((metrics.get("Equity") or {}).get("Value"))
        if assets is not None and liabilities is not None and equity is not None:
            if not def_close(assets, liabilities + equity, config.formula_tolerance, 0.5):
                for metric in ("TotalAssets", "TotalLiabilities", "Equity"):
                    def_add_row_issue(metrics[metric], "FORMULA_MISMATCH:Assets!=Liabilities+Equity")


def def_add_row_issue(row: dict[str, Any], issue: str) -> None:
    existing = [x for x in str(row.get("ValidationIssues") or "").split(";") if x]
    if issue not in existing:
        existing.append(issue)
    row["ValidationIssues"] = ";".join(existing)
    row["ValidationStatus"] = "FAIL"
    row["ConfidenceScore"] = min(def_safe_float(row.get("ConfidenceScore")) or 0.0, 0.25)


# ============================================================================
# 8 · THREE-SOURCE ARBITRATION
# ============================================================================


def def_first_value(values: Iterable[Any]) -> Any:
    return next((x for x in values if x not in (None, "", [])), None)


def def_source_scalar(values: Sequence[Any]) -> Any:
    present = [x for x in values if x not in (None, "", [])]
    if not present:
        return None
    counts = collections.Counter(str(x) for x in present)
    top, count = counts.most_common(1)[0]
    if list(counts.values()).count(count) > 1:
        return None
    return next(x for x in present if str(x) == top)


def def_page_identity_facts(pages: Sequence[PageEvidence], adapter: FilenameEngineAdapter) -> dict[str, Any]:
    per_page: list[dict[str, Any]] = []
    for page in pages:
        # 窄版頁首常被版面器歸入 body；取 body 的前段只作頁面身分 anchor，
        # 不掃整張財務表，避免同業比較表中的 peer ticker 冒充報告主體。
        header = "\n".join(x for x in (page.header, page.right, page.body[:900]) if x.strip())
        tickers = def_extract_ticker_candidates(header)
        dates = def_extract_date_candidates(header)
        broker = adapter.broker_from_text(header, strict=True)
        companies = def_extract_company_candidates(header, tickers, broker)
        target = adapter.target_price_from_text(page.fitz_text,
                                                ticker=tickers[0] if tickers else None)
        per_page.append({"page": page.page_number, "tickers": tickers,
                         "dates": [x["value"] for x in dates], "broker": broker,
                         "companies": companies, "target_price": target,
                         "score": page.score, "role": page.role})
    ticker_votes = [def_first_value(x["tickers"]) for x in per_page]
    date_votes = [def_first_value(x["dates"]) for x in per_page]
    broker_votes = [x["broker"] for x in per_page]
    target_values = [x["target_price"] for x in per_page if x["target_price"] is not None]
    return {"pages": per_page, "ticker": def_source_scalar(ticker_votes),
            "date": def_source_scalar(date_votes), "broker": def_source_scalar(broker_votes),
            "company_candidates": list(dict.fromkeys(c for x in per_page for c in x["companies"])),
            "target_prices": target_values}


def def_arbitrate_ticker(report_type: str, filename_facts: dict[str, Any],
                         first_page: dict[str, Any], financial_pages: dict[str, Any],
                         resolver: OfficialListingResolver) -> dict[str, Any]:
    sources: dict[str, Any] = {
        "filename": filename_facts.get("ticker"),
        "first_page": def_first_value(first_page.get("ticker_candidates", [])),
        "financial_pages": financial_pages.get("ticker"),
    }
    mentions = sorted({code for value in (
        filename_facts.get("tickers", []), first_page.get("ticker_candidates", []),
        [x for page in financial_pages.get("pages", []) for x in page.get("tickers", [])])
        for code in value if re.fullmatch(r"[1-9]\d{3}", str(code))})
    if report_type != REPORT_TYPE_STOCK:
        return {"ticker": None, "listing": None, "status": "N/A_NON_STOCK",
                "confidence": 1.0, "sources": sources, "mentioned_tickers": mentions,
                "invalid_candidates": [], "reason": "non-stock report: mentions are not identity"}

    official: dict[str, ListingRecord] = {}
    invalid: list[str] = []
    for code in sorted({str(x) for x in sources.values() if x}):
        record = resolver.resolve(code)
        if record:
            official[code] = record
        else:
            invalid.append(code)
    if not official:
        reason = "no candidate" if not any(sources.values()) else "TWSE/TPEX official name unavailable"
        return {"ticker": None, "listing": None,
                "status": "FAIL" if any(sources.values()) else "REVIEW",
                "confidence": 0.0, "sources": sources, "mentioned_tickers": mentions,
                "invalid_candidates": invalid, "reason": reason}

    document_votes = collections.Counter(str(code) for code in sources.values() if code in official)
    if not document_votes:
        return {"ticker": None, "listing": None, "status": "FAIL", "confidence": 0.0,
                "sources": sources, "mentioned_tickers": mentions,
                "invalid_candidates": invalid, "reason": "official candidates not present in document sources"}
    ranking = document_votes.most_common()
    top_code, top_count = ranking[0]
    tied = len(ranking) > 1 and ranking[1][1] == top_count
    if tied:
        return {"ticker": None, "listing": None, "status": "FAIL", "confidence": 0.0,
                "sources": sources, "mentioned_tickers": mentions,
                "invalid_candidates": invalid, "reason": "document sources tie on different official tickers"}
    record = official[top_code]
    if top_count >= 2:
        status, confidence = "PASS", 0.98 if len(document_votes) == 1 else 0.91
        reason = f"{top_count} document sources agree + official listing"
    elif len(official) == 1:
        status, confidence = "PASS", 0.84
        reason = "one document source + TWSE/TPEX official listing"
    else:
        return {"ticker": None, "listing": None, "status": "FAIL", "confidence": 0.0,
                "sources": sources, "mentioned_tickers": mentions,
                "invalid_candidates": invalid, "reason": "single votes for multiple official tickers"}
    return {"ticker": top_code, "listing": asdict(record), "status": status,
            "confidence": confidence, "sources": sources, "mentioned_tickers": mentions,
            "invalid_candidates": invalid, "reason": reason}


def def_arbitrate_text_field(field_name: str, sources: dict[str, Any],
                             prefer: Sequence[str] = ()) -> dict[str, Any]:
    present = {key: value for key, value in sources.items() if value not in (None, "", [])}
    if not present:
        return {"value": None, "status": "N/A", "confidence": 0.0,
                "sources": sources, "reason": f"{field_name}: no evidence"}
    counts = collections.Counter(str(x) for x in present.values())
    top, count = counts.most_common(1)[0]
    if list(counts.values()).count(count) == 1 and count >= 2:
        value = next(x for x in present.values() if str(x) == top)
        return {"value": value, "status": "PASS", "confidence": 0.96,
                "sources": sources, "reason": f"{count} sources agree"}
    if len(counts) == 1:
        value = next(iter(present.values()))
        confidence = 0.84 if len(present) >= 2 else 0.68
        return {"value": value, "status": "PASS" if len(present) >= 2 else "REVIEW",
                "confidence": confidence, "sources": sources,
                "reason": f"{len(present)} source(s), no conflict"}
    if prefer:
        for key in prefer:
            if key in present:
                return {"value": present[key], "status": "REVIEW", "confidence": 0.55,
                        "sources": sources, "reason": f"conflict; selected preferred source {key}"}
    return {"value": None, "status": "FAIL", "confidence": 0.0,
            "sources": sources, "reason": f"{field_name}: unresolved conflict"}


def def_arbitrate_target_price(first_value: float | None, financial_values: Sequence[float],
                               config: EngineConfig) -> dict[str, Any]:
    financial = [def_safe_float(x) for x in financial_values]
    financial = [x for x in financial if x is not None]
    sources = {"first_page": first_value, "financial_pages": financial}
    if first_value is None and not financial:
        return {"value": None, "status": "N/A", "confidence": 0.0,
                "sources": sources, "reason": "no target price evidence"}
    if financial:
        median = statistics.median(financial)
        if any(not def_close(x, median, config.target_price_tolerance, 0.5) for x in financial):
            return {"value": None, "status": "FAIL", "confidence": 0.0,
                    "sources": sources, "reason": "financial pages disagree on target price"}
        if first_value is not None:
            if def_close(first_value, median, config.target_price_tolerance, 0.5):
                return {"value": round(float(statistics.median([first_value, median])), 4),
                        "status": "PASS", "confidence": 0.98, "sources": sources,
                        "reason": "first page and valuation table agree"}
            return {"value": None, "status": "FAIL", "confidence": 0.0,
                    "sources": sources, "reason": "first page and valuation table conflict"}
        return {"value": round(float(median), 4), "status": "REVIEW", "confidence": 0.76,
                "sources": sources, "reason": "valuation table only"}
    return {"value": first_value, "status": "REVIEW", "confidence": 0.72,
            "sources": sources, "reason": "first page only"}


def def_consensus_gate(first_page: dict[str, Any]) -> dict[str, Any]:
    states: list[str] = []
    for item in first_page.get("consensus", {}).values():
        if isinstance(item, dict) and item.get("state"):
            states.append(str(item["state"]))
    if not states:
        return {"status": "REVIEW", "confidence": 0.55, "states": [],
                "reason": "single extractor/no comparable text"}
    if "DIVERGE" in states:
        return {"status": "FAIL", "confidence": 0.10, "states": states,
                "reason": "first-page extractors diverge"}
    if "PARTIAL" in states:
        return {"status": "REVIEW", "confidence": 0.70, "states": states,
                "reason": "first-page extractors partially agree"}
    return {"status": "PASS", "confidence": 0.96, "states": states,
            "reason": "first-page extractors agree/order-only"}


def def_overall_status(gates: dict[str, dict[str, Any]], report_type: str,
                       financial_rows: Sequence[dict[str, Any]]) -> tuple[str, float, list[str]]:
    issues: list[str] = []
    scores: list[float] = []
    hard_fail = False
    review = False
    for name, gate in gates.items():
        status = str(gate.get("status") or "N/A")
        if status == "FAIL":
            hard_fail = True
            issues.append(f"{name}:{gate.get('reason', 'FAIL')}")
        elif status == "REVIEW":
            review = True
            issues.append(f"{name}:{gate.get('reason', 'REVIEW')}")
        if status not in {"N/A", "N/A_NON_STOCK"}:
            scores.append(float(gate.get("confidence") or 0.0))
    financial_fail = sum(1 for row in financial_rows if row.get("ValidationStatus") == "FAIL")
    financial_review = sum(1 for row in financial_rows if row.get("ValidationStatus") == "REVIEW")
    if financial_fail:
        hard_fail = True
        issues.append(f"FinancialData:{financial_fail} conflicting/formula-invalid rows")
    elif financial_review:
        review = True
        issues.append(f"FinancialData:{financial_review} single-engine rows")
    if report_type == REPORT_TYPE_STOCK and gates["ticker"].get("value") is None:
        hard_fail = True
    status = "FAIL" if hard_fail else "REVIEW" if review else "PASS"
    confidence = round(statistics.mean(scores), 4) if scores else 0.0
    return status, confidence, issues


# ============================================================================
# 9 · UNIFIED ORCHESTRATOR
# ============================================================================


class UnifiedReportEngine:
    def __init__(self, config: EngineConfig | None = None, module_dir: Path | None = None,
                 firstpage_engine_path: Path | None = None,
                 firstpage_text_path: Path | None = None,
                 official_listings: Path | None = None):
        self.config = config or EngineConfig()
        fp_path, fp_find = def_find_latest_module(firstpage_engine_path, module_dir,
                                                  FIRSTPAGE_ENGINE_PATTERN)
        fp_module, fp_load = def_load_module(fp_path, "vrn_firstpage_engine")
        text_path, text_find = def_find_latest_module(firstpage_text_path, module_dir,
                                                      FIRSTPAGE_TEXT_PATTERN)
        text_module, text_load = def_load_module(text_path, "vrn_firstpage_text")
        fp_reported = getattr(fp_module, "ENGINE_VERSION", None)
        text_reported = def_module_doc_version(text_module)
        self.module_state = {"firstpage_engine": {"path": str(fp_path) if fp_path else None,
                                                   "find": fp_find, "load": fp_load,
                                                   "reported_name": getattr(fp_module, "ENGINE_NAME", None),
                                                   "reported_version": fp_reported,
                                                   "version_consistency":
                                                       def_module_version_consistency(fp_path, fp_reported)},
                             "firstpage_text": {"path": str(text_path) if text_path else None,
                                                 "find": text_find, "load": text_load,
                                                 "reported_version": text_reported,
                                                 "version_consistency":
                                                     def_module_version_consistency(text_path, text_reported)}}
        provisional = OfficialListingResolver(official_listings, None,
                                              allow_web=self.config.allow_web_official)
        self.filename = FilenameEngineAdapter(fp_module, fp_path, provisional)
        self.resolver = OfficialListingResolver(official_listings, self.filename.engine,
                                                allow_web=self.config.allow_web_official)
        self.filename.bind_resolver(self.resolver)
        self.pages = DocumentPageExtractor(self.config, text_module, text_path)

    def run_file(self, path: Path, run_id: str | None = None) -> ReportResult:
        source = path.expanduser().resolve()
        run_id = run_id or def_stable_id("RUN", def_now_iso(), uuid.uuid4().hex)
        now = def_now_iso()
        file_hash = def_file_sha256(source)
        file_id = def_stable_id("FILE", source.name, file_hash)
        filename_facts = self.filename.facts(source.name)
        if source.suffix.lower() == ".pdf":
            first_page, financial_pages, page_meta = self.pages.extract_pdf(source)
        else:
            first_page, financial_pages, page_meta = self.pages.extract_non_pdf(source)
        first_facts = def_first_page_facts(first_page, filename_facts, self.filename,
                                           page_meta.get("eng072", {}))
        financial_facts = def_page_identity_facts(financial_pages, self.filename)
        ticker_gate = def_arbitrate_ticker(first_facts["report_type"], filename_facts,
                                           first_facts, financial_facts, self.resolver)
        listing = ticker_gate.get("listing") or {}
        name_candidates = list(dict.fromkeys(
            [x for x in [filename_facts.get("name_hint")] + first_facts.get("company_candidates", [])
             + financial_facts.get("company_candidates", []) if x]))
        name_checks = [{"candidate": x, "matches_official": def_same_company_name(x, listing.get("name"))}
                       for x in name_candidates]
        name_status = ("PASS" if listing.get("name") and any(x["matches_official"] for x in name_checks)
                       else "REVIEW" if listing.get("name") else "N/A")
        name_gate = {"value": listing.get("name"), "status": name_status,
                     "confidence": 0.98 if name_status == "PASS" else 0.65 if name_status == "REVIEW" else 0.0,
                     "reason": "official name matched a document candidate" if name_status == "PASS"
                     else "official name has no matching document candidate" if listing.get("name")
                     else "canonical ticker unavailable", "checks": name_checks}
        date_gate = def_arbitrate_text_field("ReportDate", {
            "filename": filename_facts.get("date"),
            "first_page": def_first_value(x.get("value") for x in first_facts.get("date_candidates", [])),
            "financial_pages": financial_facts.get("date")}, prefer=("first_page", "filename"))
        broker_gate = def_arbitrate_text_field("Broker", {
            "filename": filename_facts.get("broker"), "first_page": first_facts.get("broker"),
            "financial_pages": financial_facts.get("broker")}, prefer=("first_page", "filename"))
        ticker_gate_view = {**ticker_gate, "value": ticker_gate.get("ticker")}
        observations = def_extract_financial_observations(financial_pages)
        financial_target_values: list[float] = []
        report_date_hint = (def_first_value(x.get("value") for x in
                                           first_facts.get("date_candidates", []))
                            or filename_facts.get("date"))
        report_year_hint = int(str(report_date_hint)[:4]) if report_date_hint else None
        target_observations = [x for x in observations
                               if x.metric_name == "TargetPrice" and x.value is not None]
        forward_targets = [x for x in target_observations
                           if x.estimate_flag in {"Estimate", "Forecast"}
                           and (report_year_hint is None or x.fiscal_year is None
                                or x.fiscal_year >= report_year_hint)]
        if forward_targets:
            financial_target_values.extend(x.value for x in forward_targets)
        elif target_observations:
            latest_year = max((x.fiscal_year or -1) for x in target_observations)
            financial_target_values.extend(x.value for x in target_observations
                                           if (x.fiscal_year or -1) == latest_year)
        else:
            # 沒有表格期間可用時才退回整頁文字抽值；否則歷史 A 欄的目標價
            # 可能被誤當成本期值，正是三源互證要避免的污染。
            financial_target_values.extend(financial_facts.get("target_prices", []))
        target_gate = def_arbitrate_target_price(first_facts.get("target_price"),
                                                 financial_target_values, self.config)
        first_consensus_gate = def_consensus_gate(first_facts)
        financial_page_gate = {
            "value": [x.page_number for x in financial_pages],
            "status": "PASS" if financial_pages else "REVIEW",
            "confidence": 0.95 if financial_pages else 0.35,
            "reason": f"{len(financial_pages)} annual/financial candidate page(s)"
            if financial_pages else "no annual financial page met the evidence threshold",
        }
        identity = {"ticker": ticker_gate.get("ticker"), "name": listing.get("name"),
                    "market": listing.get("market"), "yf_ticker": listing.get("yf_ticker"),
                    "industry": listing.get("industry"), "report_date": date_gate.get("value"),
                    "broker": broker_gate.get("value")}
        report_id = def_stable_id("REPORT", identity.get("ticker") or first_facts["report_type"],
                                  identity.get("report_date") or "NO_DATE",
                                  identity.get("broker") or "NO_BROKER", source.name, file_hash)
        financial_rows = def_make_financial_rows(observations, identity, file_id, report_id,
                                                 run_id, now, self.config)
        gates = {"ticker": ticker_gate_view, "name": name_gate, "date": date_gate,
                 "broker": broker_gate, "first_page_consensus": first_consensus_gate,
                 "financial_pages": financial_page_gate, "target_price": target_gate}
        status, confidence, issues = def_overall_status(gates, first_facts["report_type"], financial_rows)
        evidence = {
            "filename": filename_facts,
            "first_page": dict(first_facts),
            "financial_pages": {"identity": financial_facts,
                                "candidates": [def_page_public_evidence(x) for x in financial_pages]},
            "gates": gates, "listing_resolver": self.resolver.diagnostics(),
            "module_state": self.module_state, "page_meta": page_meta,
            "raw_capture": {"financial_observation_count": len(observations),
                            "footer_excluded_chars": first_facts.get("footer_excluded_chars")},
        }
        basic = {column: None for column in BASIC_COLUMNS}
        basic.update({
            "FileID": file_id, "ReportID": report_id, "SourceFileName": source.name,
            "SourcePath": str(source), "FileHash": file_hash,
            "TW_TICKER": identity.get("ticker"), "YF_TICKER": identity.get("yf_ticker"),
            "Market": identity.get("market"), "Name": identity.get("name"),
            "CompanyNameCandidate": " | ".join(name_candidates) or None,
            "ReportDate": identity.get("report_date"), "ReportTitle": first_facts.get("title"),
            "ReportType": first_facts.get("report_type"), "Language": first_facts.get("language"),
            "Broker": identity.get("broker"),
            "BrokerCandidate": " | ".join(str(x) for x in broker_gate["sources"].values() if x) or None,
            "Analyst": first_facts.get("analyst"), "Department": first_facts.get("department"),
            "Rating": first_facts.get("rating"), "RatingChange": first_facts.get("rating_change"),
            "TargetPrice": target_gate.get("value"),
            "CurrentPrice": first_facts.get("current_price"),
            "UpsideDownsidePct": def_upside(target_gate.get("value"), first_facts.get("current_price")),
            "InvestmentThesis": first_facts.get("investment_thesis"),
            "Industry": identity.get("industry"), "ConfidenceScore": confidence,
            "ValidationStatus": status, "ValidationIssues": ";".join(issues),
            "EvidenceJson": def_json(evidence),
            "CreatedAt": now, "UpdatedAt": now, "RunID": run_id,
            "SchemaVersion": SCHEMA_VERSION,
        })
        return ReportResult(basic=basic, financial=financial_rows, evidence=evidence)

    def run_many(self, paths: Sequence[Path], run_id: str | None = None) -> tuple[list[ReportResult], list[dict[str, Any]]]:
        run_id = run_id or def_stable_id("RUN", def_now_iso(), uuid.uuid4().hex)
        results: list[ReportResult] = []
        errors: list[dict[str, Any]] = []
        for path in paths:
            try:
                results.append(self.run_file(path, run_id=run_id))
            except Exception as exc:
                errors.append({"path": str(path), "error": f"{type(exc).__name__}:{exc}",
                               "traceback": traceback.format_exc(limit=5)})
        return results, errors

    def diagnostics(self) -> dict[str, Any]:
        return {"modules": self.module_state, "filename": self.filename.diagnostics(),
                "pages": self.pages.diagnostics(), "listings": self.resolver.diagnostics()}


def def_page_public_evidence(page: PageEvidence) -> dict[str, Any]:
    return {"page_number": page.page_number, "score": page.score, "role": page.role,
            "score_evidence": page.score_evidence, "compare": page.compare,
            "fitz_table_count": len(page.fitz_tables),
            "pdfplumber_table_count": len(page.plumber_tables),
            "footer_excluded_chars": page.footer_char_count,
            "fitz_tables_raw": page.fitz_tables,
            "pdfplumber_tables_raw": page.plumber_tables}


# ============================================================================
# 10 · PARQUET SSOT / OPTIONAL DERIVATIVES
# ============================================================================


def def_import_pandas() -> Any:
    try:
        import pandas as pd
        return pd
    except Exception as exc:
        raise RuntimeError("pandas is required for dataset output") from exc


def def_parquet_engine() -> str:
    for engine in ("pyarrow", "fastparquet"):
        if importlib.util.find_spec(engine) is not None:
            return engine
    raise RuntimeError("Parquet is mandatory but neither pyarrow nor fastparquet is installed")


def def_frame(rows: Sequence[dict[str, Any]], columns: Sequence[str]) -> Any:
    pd = def_import_pandas()
    normalized = [{column: row.get(column) for column in columns} for row in rows]
    return pd.DataFrame(normalized, columns=list(columns))


def def_status_rank(value: Any) -> int:
    return {"PASS": 3, "REVIEW": 2, "FAIL": 1}.get(str(value), 0)


def def_merge_records(existing: Any, incoming: Any, key: str) -> Any:
    pd = def_import_pandas()
    if existing is None or existing.empty:
        return incoming.copy()
    if incoming.empty:
        return existing.copy()
    columns = list(dict.fromkeys(list(existing.columns) + list(incoming.columns)))
    old_rows = {str(row.get(key)): row for row in existing.reindex(columns=columns).to_dict("records")}
    for new in incoming.reindex(columns=columns).to_dict("records"):
        identity = str(new.get(key))
        old = old_rows.get(identity)
        if old is None:
            old_rows[identity] = new
            continue
        old_rank, new_rank = def_status_rank(old.get("ValidationStatus")), def_status_rank(new.get("ValidationStatus"))
        old_conf = def_safe_float(old.get("ConfidenceScore")) or 0.0
        new_conf = def_safe_float(new.get("ConfidenceScore")) or 0.0
        if (new_rank, new_conf) >= (old_rank, old_conf):
            created = old.get("CreatedAt")
            old_rows[identity] = new
            if created not in (None, ""):
                old_rows[identity]["CreatedAt"] = created
    result = pd.DataFrame(list(old_rows.values()), columns=columns)
    return result.sort_values(by=[key], kind="stable").reset_index(drop=True)


def def_read_existing_parquet(path: Path, columns: Sequence[str]) -> Any:
    pd = def_import_pandas()
    if not path.exists():
        return pd.DataFrame(columns=list(columns))
    frame = pd.read_parquet(path)
    return frame.reindex(columns=list(columns))


def def_atomic_parquet(frame: Any, path: Path, engine: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp.parquet")
    try:
        frame.to_parquet(temp, index=False, engine=engine,
                         compression=DEFAULT_PARQUET_COMPRESSION)
        check = def_import_pandas().read_parquet(temp, engine=engine)
        if len(check) != len(frame) or list(check.columns) != list(frame.columns):
            raise RuntimeError("Parquet read-back row/column verification failed")
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def def_atomic_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temp.write_text(text, encoding=encoding)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def def_atomic_csv(frame: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        frame.to_csv(temp, index=False, encoding=DEFAULT_CSV_ENCODING)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def def_write_duckdb(basic: Any, financial: Any, path: Path) -> None:
    try:
        import duckdb
    except Exception as exc:
        raise RuntimeError("--duckdb requested but duckdb is not installed") from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp.duckdb")
    con = duckdb.connect(str(temp))
    try:
        con.register("basic_frame", basic)
        con.register("financial_frame", financial)
        con.execute("CREATE TABLE StockReportBasicInfo AS SELECT * FROM basic_frame")
        con.execute("CREATE TABLE StockReportFinancialData AS SELECT * FROM financial_frame")
        con.execute("CREATE UNIQUE INDEX idx_basic_report ON StockReportBasicInfo(ReportID)")
        con.execute("CREATE UNIQUE INDEX idx_financial_row ON StockReportFinancialData(FinancialRowID)")
        con.close()
        con = None
        os.replace(temp, path)
    finally:
        if con is not None:
            con.close()
        if temp.exists():
            temp.unlink()


def def_persist_results(results: Sequence[ReportResult], output_dir: Path,
                        write_csv: bool = False, write_json: bool = False,
                        write_duckdb: bool = False, write_html: bool = True,
                        manifest_extra: dict[str, Any] | None = None) -> dict[str, Any]:
    engine = def_parquet_engine()
    output = output_dir.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    new_basic = def_frame([x.basic for x in results], BASIC_COLUMNS)
    new_financial = def_frame([row for x in results for row in x.financial], FINANCIAL_COLUMNS)
    basic_path = output / DEFAULT_BASIC_PARQUET
    financial_path = output / DEFAULT_FINANCIAL_PARQUET
    old_basic = def_read_existing_parquet(basic_path, BASIC_COLUMNS)
    old_financial = def_read_existing_parquet(financial_path, FINANCIAL_COLUMNS)
    merged_basic = def_merge_records(old_basic, new_basic, "ReportID")
    merged_financial = def_merge_records(old_financial, new_financial, "FinancialRowID")
    def_atomic_parquet(merged_basic, basic_path, engine)
    def_atomic_parquet(merged_financial, financial_path, engine)
    outputs: dict[str, str] = {"basic_parquet": str(basic_path),
                               "financial_parquet": str(financial_path)}
    if write_csv:
        basic_csv = output / "StockReportBasicInfo.csv"
        financial_csv = output / "StockReportFinancialData.csv"
        def_atomic_csv(merged_basic, basic_csv)
        def_atomic_csv(merged_financial, financial_csv)
        outputs.update({"basic_csv": str(basic_csv), "financial_csv": str(financial_csv)})
    if write_json:
        basic_json = output / "StockReportBasicInfo.json"
        financial_json = output / "StockReportFinancialData.json"
        def_atomic_text(basic_json, json.dumps(merged_basic.to_dict("records"), ensure_ascii=False,
                                               indent=2, default=str))
        def_atomic_text(financial_json, json.dumps(merged_financial.to_dict("records"), ensure_ascii=False,
                                                   indent=2, default=str))
        outputs.update({"basic_json": str(basic_json), "financial_json": str(financial_json)})
    if write_duckdb:
        duck = output / "StockReport.duckdb"
        def_write_duckdb(merged_basic, merged_financial, duck)
        outputs["duckdb"] = str(duck)
    if write_html:
        matrix = output / DEFAULT_MATRIX_HTML
        def_atomic_text(matrix, def_render_matrix(results))
        outputs["matrix_html"] = str(matrix)
    manifest = {
        "engine": ENGINE_NAME, "version": ENGINE_VERSION, "schema": SCHEMA_VERSION,
        "generated_at": def_now_iso(), "parquet_engine": engine,
        "new_reports": len(new_basic), "new_financial_rows": len(new_financial),
        "total_reports": len(merged_basic), "total_financial_rows": len(merged_financial),
        "outputs": outputs, **(manifest_extra or {}),
    }
    manifest_path = output / DEFAULT_MANIFEST_JSON
    def_atomic_text(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2, default=str))
    outputs["manifest"] = str(manifest_path)
    return {"outputs": outputs, "manifest": manifest,
            "basic_rows": len(merged_basic), "financial_rows": len(merged_financial)}


# ============================================================================
# 11 · OFFLINE HTML VALIDATION MATRIX
# ============================================================================


def def_html_escape(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def def_lamp(status: Any) -> str:
    value = str(status or "N/A")
    cls = "ok" if value == "PASS" else "no" if value == "FAIL" else "wa" if value == "REVIEW" else "na"
    return f'<span class="lamp {cls}">{def_html_escape(value)}</span>'


def def_render_matrix(results: Sequence[ReportResult]) -> str:
    summary_rows: list[str] = []
    gate_rows: list[str] = []
    financial_rows: list[str] = []
    for result in results:
        basic = result.basic
        evidence = result.evidence
        gates = evidence.get("gates", {})
        summary_rows.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in (
            def_html_escape(basic.get("SourceFileName")), def_html_escape(basic.get("ReportType")),
            def_html_escape(basic.get("TW_TICKER")), def_html_escape(basic.get("Name")),
            def_html_escape(basic.get("ReportDate")), def_html_escape(basic.get("Broker")),
            def_html_escape(basic.get("TargetPrice")), def_lamp(basic.get("ValidationStatus")),
            def_html_escape(basic.get("ConfidenceScore")),
            def_html_escape(basic.get("ValidationIssues")))) + "</tr>")
        for gate_name, gate in gates.items():
            gate_rows.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in (
                def_html_escape(basic.get("SourceFileName")), def_html_escape(gate_name),
                def_lamp(gate.get("status")), def_html_escape(gate.get("value")),
                def_html_escape(gate.get("reason")),
                def_html_escape(def_json(gate.get("sources", gate.get("states", "")))[:1500]))) + "</tr>")
        for row in result.financial:
            financial_rows.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in (
                def_html_escape(basic.get("SourceFileName")), def_html_escape(row.get("PageNumber")),
                def_html_escape(row.get("MetricCategory")), def_html_escape(row.get("MetricName")),
                def_html_escape(row.get("PeriodLabelRaw")), def_html_escape(row.get("Value")),
                def_html_escape(row.get("Unit")), def_lamp(row.get("ValidationStatus")),
                def_html_escape(row.get("ValidationIssues")))) + "</tr>")
    return f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>VRN 三源互證矩陣</title>
<style>
:root{{--bg:#f5f7fb;--card:#fff;--line:#dce3ee;--text:#172033;--muted:#667085;--blue:#2457a7}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font:9.5px/1.45 "Segoe UI","Noto Sans TC",sans-serif}}
header{{position:sticky;top:0;background:#0f2747;color:#fff;padding:10px 16px;z-index:2}}h1{{font-size:13px;margin:0}}header p{{margin:2px 0 0;color:#c7d6eb}}
main{{padding:12px;display:grid;gap:12px}}section{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px;overflow:auto}}
h2{{font-size:11px;margin:0 0 7px;color:var(--blue)}}table{{border-collapse:collapse;width:100%;min-width:900px}}th,td{{border-bottom:1px solid #e8edf4;padding:4px 6px;text-align:left;vertical-align:top;overflow-wrap:anywhere}}
th{{position:sticky;top:0;background:#edf2f8;font-size:8.5px;color:#475467}}.lamp{{display:inline-block;border-radius:999px;padding:1px 6px;font-weight:700}}
.ok{{background:#dcfce7;color:#166534}}.wa{{background:#fef3c7;color:#92400e}}.no{{background:#fee2e2;color:#991b1b}}.na{{background:#e5e7eb;color:#4b5563}}
@media(max-width:720px){{main{{padding:6px}}section{{border-radius:4px}}}}
</style></head><body><header><h1>VRN · Filename × First Page × Annual Financial Pages</h1>
<p>{def_html_escape(ENGINE_VERSION)} · {len(results)} 份 · footer 10%／&lt;8pt／附註附錄已排除</p></header><main>
<section><h2>Basic Info canonical matrix</h2><table><thead><tr><th>檔案</th><th>型別</th><th>Ticker</th><th>Name</th><th>報告日</th><th>券商</th><th>目標價</th><th>狀態</th><th>信心</th><th>問題</th></tr></thead><tbody>{''.join(summary_rows) or '<tr><td colspan="10">無資料</td></tr>'}</tbody></table></section>
<section><h2>Mutual-validation gates</h2><table><thead><tr><th>檔案</th><th>Gate</th><th>狀態</th><th>Canonical</th><th>裁決理由</th><th>來源證據</th></tr></thead><tbody>{''.join(gate_rows) or '<tr><td colspan="6">無資料</td></tr>'}</tbody></table></section>
<section><h2>Financial Data long format</h2><table><thead><tr><th>檔案</th><th>頁</th><th>類別</th><th>指標</th><th>期間</th><th>值</th><th>單位</th><th>狀態</th><th>問題</th></tr></thead><tbody>{''.join(financial_rows) or '<tr><td colspan="9">無財務資料</td></tr>'}</tbody></table></section>
</main></body></html>"""


# ============================================================================
# 12 · SELFTEST（合成 PDF：檔名／首頁／年度財務頁真正一起跑）
# ============================================================================


def def_make_test_listings(path: Path) -> None:
    path.write_text("code,name,market,yf_ticker,industry\n2330,台積電,TWSE,2330.TW,半導體\n"
                    "2317,鴻海,TWSE,2317.TW,電子\n2308,台達電,TWSE,2308.TW,電子\n",
                    encoding="utf-8-sig")


def def_draw_table(page: Any, x: float, y: float, widths: Sequence[float],
                   rows: Sequence[Sequence[str]], row_height: float = 24.0) -> None:
    import fitz
    total_width = sum(widths)
    for row_index in range(len(rows) + 1):
        yy = y + row_index * row_height
        page.draw_line((x, yy), (x + total_width, yy), color=(0, 0, 0), width=0.8)
    xx = x
    page.draw_line((xx, y), (xx, y + len(rows) * row_height), color=(0, 0, 0), width=0.8)
    for width in widths:
        xx += width
        page.draw_line((xx, y), (xx, y + len(rows) * row_height), color=(0, 0, 0), width=0.8)
    for row_index, row in enumerate(rows):
        xx = x
        for column, cell in enumerate(row):
            rect = fitz.Rect(xx + 3, y + row_index * row_height + 4,
                             xx + widths[column] - 3, y + (row_index + 1) * row_height - 3)
            page.insert_textbox(rect, str(cell), fontsize=9, fontname="helv", align=0)
            xx += widths[column]


def def_make_test_pdf(path: Path) -> None:
    import fitz
    document = fitz.open()
    first = document.new_page(width=595, height=842)
    first.insert_text((40, 55), "TSMC (2330 TT) Company Update", fontsize=18, fontname="hebo")
    first.insert_text((40, 88), "Report Date: 2025/12/05", fontsize=11)
    first.insert_text((335, 88), "Goldman Sachs Equity Research", fontsize=10)
    first.insert_text((335, 112), "BUY  Target Price NT$1,250", fontsize=11)
    first.insert_text((335, 134), "Current Price NT$1,000", fontsize=11)
    first.insert_text((40, 175), "Demand remains resilient. Advanced-node mix supports earnings growth.", fontsize=11)
    first.insert_text((40, 800), "Confidential footer 9999 Appendix", fontsize=7)

    second = document.new_page(width=595, height=842)
    second.insert_text((40, 48), "TSMC 2330 TT | Goldman Sachs | 2025/12/05", fontsize=10)
    second.insert_text((40, 78), "Financial Summary and Valuation (NT$m)", fontsize=16, fontname="hebo")
    table = [
        ["Metric", "2024A", "2025E", "2026F"],
        ["Revenue", "100000", "120000", "144000"],
        ["Gross Profit", "50000", "60000", "72000"],
        ["Gross Margin %", "50.0", "50.0", "50.0"],
        ["Operating Profit", "40000", "48000", "57600"],
        ["Operating Margin %", "40.0", "40.0", "40.0"],
        ["Net Income", "30000", "36000", "43200"],
        ["EPS", "40.0", "48.0", "57.6"],
        ["PER x", "25.0", "26.0", "21.7"],
        ["Target Price", "1000", "1250", "1250"],
    ]
    def_draw_table(second, 40, 110, [190, 105, 105, 105], table)
    second.insert_text((40, 800), "Source: broker estimates; disclaimer", fontsize=7)

    third = document.new_page(width=595, height=842)
    third.insert_text((40, 60), "Important disclaimer and legal notices", fontsize=16)
    third.insert_text((40, 800), "Mentioned peer 6669; not report identity", fontsize=7)
    document.save(str(path))
    document.close()


def def_make_industry_test_pdf(path: Path) -> None:
    import fitz
    document = fitz.open()
    page = document.new_page(width=595, height=842)
    page.insert_text((40, 55), "Semiconductor Industry Outlook", fontsize=18, fontname="hebo")
    page.insert_text((40, 90), "Companies mentioned: TSMC 2330 TT and Hon Hai 2317 TT", fontsize=11)
    page.insert_text((40, 125), "Report Date: 2025/12/05", fontsize=11)
    document.save(str(path))
    document.close()


def def_selftest() -> int:
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, condition: bool, note: str = "") -> None:
        checks.append((name, bool(condition), note))
        print(f"  [{'OK' if condition else 'FAIL'}] {name}" + (f" · {note}" if note else ""))

    check("日期：西元/六碼補20/民國/(20)省略", [
        def_parse_numeric_date("20260131"), def_parse_numeric_date("260131"),
        def_parse_numeric_date("1140822"), def_extract_date_candidates("(20)260131")[0]["value"]
    ] == ["2026-01-31", "2026-01-31", "2025-08-22", "2026-01-31"])
    check("期間：2024A/2025E/1Q25", [def_parse_period(x)["period"] for x in
          ("2024A", "2025E", "1Q25")] == ["2024", "2025", "2025-Q1"])
    check("目標價剔除百分比與 ticker echo",
          def_target_price_fallback("2330 TT Target Price NT$1,250 Upside 25%", "2330") == 1250.0)
    check("公司簡稱可對官方長名", def_same_company_name("台積電", "台灣積體電路") is True)
    check("短縮寫用詞界，不把 summary 誤判 A/R 或 P/S",
          "AccountsReceivable" not in def_metric_hits("Financial Summary and Valuation")
          and "PSR" not in def_metric_hits("Financial Summary and Valuation"))
    check("報告日年份不冒充 annual period",
          not def_period_candidates("Report date 2025/12/05"))
    empty_resolver = OfficialListingResolver()
    unresolved = def_arbitrate_ticker("STOCK", {"ticker": "2330", "tickers": ["2330"]},
                                      {"ticker_candidates": []}, {"ticker": None, "pages": []},
                                      empty_resolver)
    check("官方名冊查不到時 ticker/Name 不進 canonical",
          unresolved["ticker"] is None and unresolved["status"] == "FAIL")

    conflict_observations = [
        FinancialObservation("Revenue", "Revenue", "Income Statement", "2025E", "year", 2025,
                             None, "Estimate", 100.0, "100", "TWDm", "TWD", 1.0, 2,
                             "T1", 1, 1, "fitz", "Revenue|2025E|100"),
        FinancialObservation("Revenue", "Revenue", "Income Statement", "2025E", "year", 2025,
                             None, "Estimate", 130.0, "130", "TWDm", "TWD", 1.0, 2,
                             "T2", 1, 1, "pdfplumber", "Revenue|2025E|130"),
    ]
    conflict_value, conflict_status, _, _, _ = def_numeric_consensus(conflict_observations,
                                                                      EngineConfig())
    check("兩種表格引擎數值衝突時不硬選 canonical",
          conflict_value is None and conflict_status == "FAIL")

    with tempfile.TemporaryDirectory() as temp_name:
        temp = Path(temp_name)
        listings = temp / "listings.csv"
        report = temp / "GS-2330-台積電-20251205.pdf"
        industry = temp / "產業報告-2330-2317-20251205.pdf"
        def_make_test_listings(listings)
        def_make_test_pdf(report)
        def_make_industry_test_pdf(industry)
        engine = UnifiedReportEngine(module_dir=Path(__file__).resolve().parent,
                                     official_listings=listings)
        result = engine.run_file(report, run_id="RUN_SELFTEST")
        check("單一入口產生 BasicInfo", result.basic["TW_TICKER"] == "2330"
              and result.basic["Name"] == "台積電" and result.basic["ReportType"] == "STOCK",
              f"ticker={result.basic['TW_TICKER']} name={result.basic['Name']} type={result.basic['ReportType']}")
        check("Filename/首頁/財務頁三源 ticker 互證",
              result.evidence["gates"]["ticker"]["status"] == "PASS",
              def_json(result.evidence["gates"]["ticker"]["sources"]))
        check("首頁 footer 與 7pt 小字排除", "9999" not in result.evidence["first_page"]["anchor_text"]
              and result.evidence["first_page"]["footer_excluded_chars"] > 0)
        candidates = result.evidence["financial_pages"]["candidates"]
        check("年度財務頁自動定位", [x["page_number"] for x in candidates] == [2],
              def_json(candidates))
        check("兩種表格引擎均留下證據", candidates and
              candidates[0]["fitz_table_count"] >= 1 and candidates[0]["pdfplumber_table_count"] >= 1,
              def_json(candidates[0] if candidates else {}))
        metric_periods = {(x["MetricName"], x["FiscalYear"]) for x in result.financial}
        check("FinancialData long format 還原 Revenue/EPS/PER/TargetPrice",
              all((metric, year) in metric_periods for metric in ("Revenue", "EPS", "PER", "TargetPrice")
                  for year in (2024, 2025, 2026)), f"rows={len(result.financial)}")
        check("財務公式 GrossProfit/Revenue=GrossMargin 通過",
              not any("FORMULA_MISMATCH" in str(x.get("ValidationIssues")) for x in result.financial))
        check("首頁目標價與估值表互證", result.evidence["gates"]["target_price"]["status"] == "PASS"
              and result.basic["TargetPrice"] == 1250.0,
              def_json(result.evidence["gates"]["target_price"]))

        fallback_engine = UnifiedReportEngine(
            firstpage_engine_path=Path("/__vrn_missing_firstpage__.py"),
            firstpage_text_path=Path("/__vrn_missing_eng072__.py"), official_listings=listings)
        fallback_result = fallback_engine.run_file(report, run_id="RUN_FALLBACK")
        check("兩份舊引擎缺席時內建退路仍可完整跑",
              fallback_result.basic["TW_TICKER"] == "2330"
              and len(fallback_result.financial) == len(result.financial))

        industry_result = engine.run_file(industry, run_id="RUN_SELFTEST")
        check("產業報告即使提到個股也不寫 canonical ticker",
              industry_result.basic["ReportType"] == "INDUSTRY"
              and industry_result.basic["TW_TICKER"] is None,
              f"type={industry_result.basic['ReportType']} ticker={industry_result.basic['TW_TICKER']}")

        output = temp / "output"
        persisted = def_persist_results([result, industry_result], output, write_csv=True,
                                        write_json=True, write_html=True)
        check("兩個 Parquet 必選 SSOT 可回讀",
              Path(persisted["outputs"]["basic_parquet"]).exists()
              and Path(persisted["outputs"]["financial_parquet"]).exists()
              and persisted["basic_rows"] == 2)
        persisted_again = def_persist_results([result, industry_result], output, write_html=True)
        check("增量重跑依 ReportID/FinancialRowID 去重",
              persisted_again["basic_rows"] == persisted["basic_rows"]
              and persisted_again["financial_rows"] == persisted["financial_rows"])
        pd = def_import_pandas()
        high = pd.DataFrame([{"ReportID": "R1", "ValidationStatus": "PASS",
                              "ConfidenceScore": 0.99, "CreatedAt": "old", "Name": "正典"}])
        low = pd.DataFrame([{"ReportID": "R1", "ValidationStatus": "FAIL",
                             "ConfidenceScore": 0.10, "CreatedAt": "new", "Name": "錯值"}])
        protected = def_merge_records(high, low, "ReportID").iloc[0]
        check("低信心新資料不覆蓋既有高信心列",
              protected["Name"] == "正典" and protected["CreatedAt"] == "old")
        check("CSV 使用 UTF-8 BOM", (output / "StockReportBasicInfo.csv").read_bytes().startswith(b"\xef\xbb\xbf"))
        html_text = (output / DEFAULT_MATRIX_HTML).read_text(encoding="utf-8")
        check("HTML Matrix 零 CDN 且含三源 Gate", "http://" not in html_text
              and "https://" not in html_text and "Mutual-validation gates" in html_text)

    failed = [name for name, ok, _ in checks if not ok]
    print(f"[SELFTEST] {len(checks) - len(failed)}/{len(checks)} PASS")
    if failed:
        print("[FAILED] " + " | ".join(failed))
    return 1 if failed else 0


# ============================================================================
# 13 · CLI
# ============================================================================


def def_build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VRN filename/first-page/annual-financial unified engine")
    parser.add_argument("--in", dest="inputs", action="append", default=[],
                        help="PDF/Word/Image file or directory; repeatable")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--official-listings", type=Path,
                        help="TWSE/TPEX official roster: CSV/JSON/Parquet/DuckDB")
    parser.add_argument("--module-dir", type=Path,
                        help="directory containing the two legacy engines")
    parser.add_argument("--firstpage-engine", type=Path)
    parser.add_argument("--firstpage-text", type=Path)
    parser.add_argument("--allow-web-official", action="store_true",
                        help="delegate to existing governed network gate; never opens consent itself")
    parser.add_argument("--csv", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--duckdb", action="store_true")
    parser.add_argument("--html", action="store_true", default=True)
    parser.add_argument("--no-html", action="store_false", dest="html")
    parser.add_argument("--dry-run", action="store_true",
                        help="extract/validate only; do not write Parquet")
    parser.add_argument("--json-stdout", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--financial-page-score", type=float, default=DEFAULT_FINANCIAL_PAGE_SCORE)
    parser.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES)
    return parser


def def_cli(argv: Sequence[str] | None = None) -> int:
    args = def_build_parser().parse_args(list(argv) if argv is not None else None)
    if args.selftest:
        return def_selftest()
    if not args.inputs:
        print("[ERROR] at least one --in file/directory is required", file=sys.stderr)
        return 2
    paths, input_diagnostics = def_collect_inputs(args.inputs)
    if not paths:
        print(json.dumps({"state": "NO_INPUT", "diagnostics": input_diagnostics},
                         ensure_ascii=False, indent=2), file=sys.stderr)
        return 2
    config = EngineConfig(financial_page_score=args.financial_page_score,
                          max_pages=args.max_pages,
                          allow_web_official=args.allow_web_official)
    engine = UnifiedReportEngine(config=config, module_dir=args.module_dir,
                                 firstpage_engine_path=args.firstpage_engine,
                                 firstpage_text_path=args.firstpage_text,
                                 official_listings=args.official_listings)
    run_id = def_stable_id("RUN", def_now_iso(), uuid.uuid4().hex)
    results, errors = engine.run_many(paths, run_id=run_id)
    payload: dict[str, Any] = {
        "run_id": run_id, "inputs": len(paths), "processed": len(results), "errors": errors,
        "diagnostics": engine.diagnostics(),
        "results": [{"basic": x.basic, "financial_rows": len(x.financial)} for x in results],
    }
    if results and not args.dry_run:
        try:
            payload["persistence"] = def_persist_results(
                results, args.out, write_csv=args.csv, write_json=args.json,
                write_duckdb=args.duckdb, write_html=args.html,
                manifest_extra={"run_id": run_id, "input_diagnostics": input_diagnostics,
                                "errors": errors, "engine_diagnostics": engine.diagnostics()})
        except Exception as exc:
            payload["persistence_error"] = f"{type(exc).__name__}:{exc}"
            print(json.dumps(payload, ensure_ascii=False, indent=2, default=str), file=sys.stderr)
            return 3
    if args.json_stdout:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    else:
        print(f"[{ENGINE_NAME} {ENGINE_VERSION}] processed={len(results)}/{len(paths)} errors={len(errors)}")
        for result in results:
            basic = result.basic
            print(f"  [{basic['ValidationStatus']}] {basic['SourceFileName']} · "
                  f"{basic['ReportType']} · {basic['TW_TICKER'] or '-'} "
                  f"{basic['Name'] or '-'} · financial={len(result.financial)}")
        if payload.get("persistence"):
            for name, path in payload["persistence"]["outputs"].items():
                print(f"  {name}: {path}")
        for error in errors:
            print(f"  [ERROR] {error['path']} · {error['error']}")
    return 1 if errors else 0


def main() -> int:
    return def_cli()


if __name__ == "__main__":
    raise SystemExit(main())
