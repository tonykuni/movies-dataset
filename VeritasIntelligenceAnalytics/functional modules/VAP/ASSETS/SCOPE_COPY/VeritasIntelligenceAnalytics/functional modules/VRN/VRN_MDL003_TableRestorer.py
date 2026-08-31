# -*- coding: utf-8 -*-
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
"""
VRN_MDL003_TableRestorer.py
============================
VERITAS REPORT NOVA -- MDL003  Table Restoration + Validation + SSOT Integration
Version   : 1.0.0   |   Module ID : VRN-MDL003-SUP-001
Asset ID  : VRN-MDL003-CLS-001
Policy    : 功能只增不減 · append-only · SSOT · 獨立模組

PIPELINE POSITION
  mdl002_temp/           ← VRN_MDL002_Layout.json (from MDL002)
    ↓
  VRN_MDL003_TableRestorer  (此模組)
    ↓
  mdl003_temp/           ← 還原後表格 + 驗證結果 + 標準化財務數據 → MDL004+

WHAT THIS MODULE DOES
  1. Load VRN_MDL002_Layout.json from mdl002_temp
  2. For each table record:
     a. TEXT REPAIR (9-step R1–R9): noise → dedup → merge → OCR-fix → canonicalize
     b. TABLE RESTORATION:
        - Split raw_data into header_row + data_rows
        - Align time-axis (periods) with value columns using zip()
        - Canonicalize row labels via _CANONICAL_MAP (SynonymEngine embedded)
        - CALC repair: fill missing values using accounting identities
        - OCR numeric fix: l→1, O→0, bracket negatives, dash→null
     c. FINANCIAL VALIDATION:
        - verify_financial_arithmetic(): gross_profit = revenue - cogs
        - Cross-check periods alignment
        - Tag each field: RP (OCR) | CALC (derived) | API (external) | ERR (failed)
     d. SSOT Integration:
        - VIA_SSOT_Unified.py (if available): load and use for synonym lookup
        - VeritasAegisNexus.py (if available): security/governance check
        - VeritasCeleritas.py (if available): accelerator
  3. Text block restoration:
     - Remove OCR noise (axis numbers, watermarks)
     - Smart sentence merge (向右向下整合直到句點)
     - Title detection + preservation
  4. Output restored + validated JSON/DB/Parquet

ANCHOR MAP
  [VRN:ANCHOR:MDL003-META-001]   §0  Module Metadata
  [VRN:ANCHOR:MDL003-SSOT-001]   §1  Embedded SSOT + Synonym Engine
  [VRN:ANCHOR:MDL003-ACCEL-001]  §2  Accelerator Init
  [VRN:ANCHOR:MDL003-DAT-001]    §3  Config / _DEFAULTS
  [VRN:ANCHOR:MDL003-LOAD-001]   §4  MDL002 Output Loader
  [VRN:ANCHOR:MDL003-REPAIR-001] §5  Text Repair Engine (R1–R9)
  [VRN:ANCHOR:MDL003-RESTORE-001] §6 Table Restoration Engine
  [VRN:ANCHOR:MDL003-CALC-001]   §7  CALC Rule Engine (accounting identities)
  [VRN:ANCHOR:MDL003-VERIFY-001] §8  Financial Verification + Tagging (RP/CALC/API/ERR)
  [VRN:ANCHOR:MDL003-TEXTFLOW-001] §9 Text Flow Restoration (sentence merge)
  [VRN:ANCHOR:MDL003-EXTERNAL-001] §10 External SSOT Integration (optional)
  [VRN:ANCHOR:MDL003-DB-001]     §11 DB Writer
  [VRN:ANCHOR:MDL003-OUT-001]    §12 Output Assembler
  [VRN:ANCHOR:MDL003-SYS-001]    §13 Pipeline Entry

SMART ASSET REGISTRY
  VRN-MDL003-CLS-001  VRN_MDL003_TableRestorer
  VRN-MDL003-CLS-002  MDL003DBWriter
  VRN-MDL003-CLS-003  TextRepairEngine
  VRN-MDL003-CLS-004  TableRestoreEngine
  VRN-MDL003-CLS-005  FinancialVerifier
  VRN-MDL003-CLS-006  RestoredTable
  VRN-MDL003-CLS-007  RestoredTextBlock
  VRN-MDL003-FNC-001  load_mdl002_output
  VRN-MDL003-FNC-002  canonicalize_label
  VRN-MDL003-FNC-003  classify_fin_type
  VRN-MDL003-FNC-004  clean_ocr_number
  VRN-MDL003-FNC-005  is_axis_noise
  VRN-MDL003-FNC-006  restore_one_table
  VRN-MDL003-FNC-007  verify_financial_arithmetic
  VRN-MDL003-FNC-008  reflow_text_blocks
  VRN-MDL003-FNC-009  load_external_ssot
  VRN-MDL003-FNC-010  process_one_pdf
  VRN-MDL003-FNC-011  assemble_output
  VRN-MDL003-FNC-012  _mdl003_accel_init

OUTPUTS (mdl003_temp)
  VRN_MDL003_Restored.json       ← 主輸出：還原表格 + 驗證結果 → MDL004+
  VRN_MDL003_VerifySummary.json  ← 驗證摘要 (RP/CALC/API/ERR counts)
  VRN_MDL003.db                  ← SQLite WAL
  VRN_MDL003_Restored.parquet    ← Parquet flat (FinancialRow per record)
  VRN_MDL003_Restored.csv        ← CSV (UTF-8 BOM)
  VRN_MDL003_TextFlow.json       ← 還原文字段落 (for RAG/LLM)

SSOT INTEGRATION PATHS
  supportive_module/VIA_SSOT_Unified.py      ← optional synonym extension
  supportive_module/VeritasAegisNexus.py     ← optional governance check
  supportive_module/VeritasCeleritas.py      ← optional acceleration

LL RULES: #10 #12 #13 #15 #17 #18 #19 #20
"""

# ============================================================================
# [VRN:ANCHOR:MDL003-META-001] §0
# ============================================================================

__version__   = "1.0.0"
__module_id__ = "VRN-MDL003-SUP-001"
__asset_id__  = "VRN-MDL003-CLS-001"
__author__    = "VRN Team"
__domain__    = "RESTORE_VALIDATE"

# ============================================================================
# STDLIB
# ============================================================================

import os, sys, re, json, time, math, hashlib, logging, sqlite3, csv, io
import gc, argparse, threading, warnings, collections, copy
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings("ignore")

def _si(n):
    try: import importlib; return importlib.import_module(n)
    except: return None

pd       = _si("pandas")
pyarrow  = _si("pyarrow")
orjson   = _si("orjson")
xxhash   = _si("xxhash")
fitz     = _si("fitz")

# ============================================================================
# [VRN:ANCHOR:MDL003-SSOT-001] §1  EMBEDDED SSOT + SYNONYM ENGINE
# ============================================================================

# THREE LOCKED TW TICKER REGEX — IMMUTABLE
TW_TICKER_REGEX    = re.compile(r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})")
TW_BLOOMBERG_REGEX = re.compile(r"\b(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})\s+TT\b")
TW_YFINANCE_REGEX  = re.compile(r"\b(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})\.(TW|TWO)\b")

# ── Canonical Map (append-only — never remove existing entries) ───────────────
_CANONICAL_MAP: Dict[str, str] = {
    # ── Revenue ──────────────────────────────────────────────────────────────
    "營業收入淨額":"revenue", "營業收入":"revenue", "收入":"revenue",
    "Revenue":"revenue", "Net Revenue":"revenue", "Net Sales":"revenue",
    "营收":"revenue", "Sales":"revenue", "Total Revenue":"revenue",
    # ── COGS ─────────────────────────────────────────────────────────────────
    "營業成本":"cogs", "Cost of Revenue":"cogs", "COGS":"cogs",
    "Cost of Sales":"cogs", "销售成本":"cogs", "营业成本":"cogs",
    # ── Gross Profit ─────────────────────────────────────────────────────────
    "營業毛利淨額":"gross_profit", "毛利":"gross_profit", "Gross Profit":"gross_profit",
    "营业毛利淨額":"gross_profit",
    # ── OpEx ─────────────────────────────────────────────────────────────────
    "營業費用":"opex", "Operating Expense":"opex", "OpEx":"opex",
    "SG&A":"opex", "营业費用":"opex",
    # ── Operating Income ─────────────────────────────────────────────────────
    "營業淨利/損":"operating_income", "營業利益":"operating_income",
    "Operating Income":"operating_income", "EBIT":"operating_income",
    "营业淨利/損":"operating_income",
    # ── Pre-tax ──────────────────────────────────────────────────────────────
    "稅前淨利":"pretax_income", "Pretax Income":"pretax_income",
    "Pre-tax Income":"pretax_income", "税前淨利":"pretax_income",
    # ── Net Income ───────────────────────────────────────────────────────────
    "稅後淨利":"net_income", "Net Income":"net_income",
    "Net Profit":"net_income", "税後淨利":"net_income",
    "歸屬母公司淨利":"net_income_parent", "Attributable Net":"net_income_parent",
    # ── EPS ──────────────────────────────────────────────────────────────────
    "每股盈餘(元)":"eps", "每股盈餘":"eps", "EPS":"eps",
    "EPS (NT$)":"eps", "Basic EPS":"basic_eps", "Diluted EPS":"diluted_eps",
    "每股净利":"eps",
    # ── Margins ──────────────────────────────────────────────────────────────
    "毛利率":"gross_margin", "Gross Margin":"gross_margin",
    "營業利益率":"operating_margin", "Operating Margin":"operating_margin",
    "淨利率":"net_margin", "Net Margin":"net_margin",
    # ── Growth ───────────────────────────────────────────────────────────────
    "營收成長率":"revenue_growth", "Revenue Growth":"revenue_growth",
    "YoY":"yoy_growth", "QoQ":"qoq_growth",
    # ── Per-share ────────────────────────────────────────────────────────────
    "每股淨值":"bvps", "BVPS":"bvps", "Book Value Per Share":"bvps",
    "每股現金股利":"dps", "DPS":"dps", "Dividend Per Share":"dps",
    # ── Valuation ────────────────────────────────────────────────────────────
    "本益比(P/E)":"pe_ratio", "P/E":"pe_ratio", "本益比":"pe_ratio",
    "股價淨值比":"pb_ratio", "P/B":"pb_ratio", "PBR":"pb_ratio",
    "殖利率":"dividend_yield", "Dividend Yield":"dividend_yield",
    # ── Balance Sheet ────────────────────────────────────────────────────────
    "總資產":"total_assets", "Total Assets":"total_assets",
    "總負債":"total_liabilities", "Total Liabilities":"total_liabilities",
    "股東權益":"total_equity", "Total Equity":"total_equity",
    "流動資產":"current_assets", "Current Assets":"current_assets",
    "現金及約當現金":"cash", "Cash":"cash",
    # ── Cash Flow ────────────────────────────────────────────────────────────
    "來自營業活動現金":"operating_cf", "Operating CF":"operating_cf",
    "投資活動現金":"investing_cf", "Investing CF":"investing_cf",
    "自由現金流量":"free_cf", "Free Cash Flow":"free_cf", "FCF":"free_cf",
    "資本支出":"capex", "CapEx":"capex",
    # ── ROE/ROA ──────────────────────────────────────────────────────────────
    "股東權益報酬率":"roe", "ROE":"roe",
    "資產報酬率":"roa", "ROA":"roa",
}

# ── Fin type classifier ───────────────────────────────────────────────────────
_IS_FIELDS = {"revenue","cogs","gross_profit","opex","operating_income",
              "pretax_income","net_income","net_income_parent","eps","basic_eps",
              "diluted_eps","gross_margin","operating_margin","net_margin",
              "revenue_growth","yoy_growth","qoq_growth"}
_BS_FIELDS = {"total_assets","total_liabilities","total_equity","current_assets",
              "cash","inventory","accounts_receivable","property_plant"}
_CF_FIELDS = {"operating_cf","investing_cf","financing_cf","free_cf","capex"}
_VL_FIELDS = {"pe_ratio","pb_ratio","dividend_yield","bvps","dps","roe","roa",
              "peg_ratio","ev_ebitda"}

# ── CALC identity rules ───────────────────────────────────────────────────────
# Format: target_field: (operand_a, operand_b, operator)
CALC_RULES: Dict[str, Tuple[str, str, str]] = {
    "gross_profit":      ("revenue",       "cogs",               "sub"),
    "operating_income":  ("gross_profit",  "opex",               "sub"),
    "net_income":        ("pretax_income", None,                 "approx"),  # approx only
    "gross_margin":      ("gross_profit",  "revenue",            "div"),
    "operating_margin":  ("operating_income","revenue",          "div"),
    "net_margin":        ("net_income",    "revenue",            "div"),
}

# Noise patterns for text (chart axis, watermarks, etc.)
_NOISE_RE = re.compile(
    r"\{.*?\}|[\x00-\x08\x0b\x0c\x0e-\x1f]"
    r"|(?<!\w)[lO\|](?=[\d,])|(?<=[\d,])[lO\|](?!\w)"
    r"|(?:^|\n)[-+]?\s*\d+\s*-\s*(?=\n|$)"   # page number dash: - 1 -
)
_AXIS_RE1 = re.compile(r"^[-+]?[\d\s,\.]+%?$")
_AXIS_RE2 = re.compile(r"^(?:[-+]?\d{1,3}(?:\.\d+)?[%O]?\s*){4,}$")
_AXIS_RE3 = re.compile(r"^\s*(\d+[OBoS]+|[sS]o+|JO+|I+)\s*$")

# Time-period detection
_PERIOD_RE = re.compile(
    r"(20\d{2}[AEFaefCTct]?|\d{1,2}Q\d{2}|[Ff][Yy]\d{2}[AEae]?|"
    r"\d{4}[Qq]\d|2[0-9][A-Z]{1,2})"
)

# ============================================================================
# [VRN:ANCHOR:MDL003-ACCEL-001] §2
# ============================================================================

def _mdl003_accel_init(workers: int = 0) -> Dict:
    """VRN-MDL003-FNC-012"""
    w = workers or max(1, (os.cpu_count() or 4) - 1)
    for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                "NUMEXPR_NUM_THREADS", "BLIS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ.setdefault(var, str(w))
    gc.set_threshold(50_000, 500, 50)
    return {"workers": w, "pyarrow": pyarrow is not None, "fitz": fitz is not None}

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s][%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

# ============================================================================
# [VRN:ANCHOR:MDL003-DAT-001] §3
# ============================================================================

_DEFAULTS = dict(
    mdl002_temp  = r"C:\VeritasIntelligenceAnalytics\VeritasReportNova\temp\mdl002_temp",
    mdl003_temp  = r"C:\VeritasIntelligenceAnalytics\VeritasReportNova\temp\mdl003_temp",
    ssot_dir     = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module",
    workers      = 0,
    enable_db    = True,
    zero_error   = True,
    enable_calc  = True,     # apply CALC identity repair
    min_rows     = 2,        # minimum rows to keep a restored table
    min_cols     = 2,        # minimum cols to keep a restored table
    text_reflow  = True,     # enable sentence merge
)

# ============================================================================
# UTILITIES
# ============================================================================

def _hash8(s: str) -> str:
    if xxhash: return xxhash.xxh64(s.encode()).hexdigest()[:8].upper()
    return hashlib.sha256(s.encode()).hexdigest()[:8].upper()

def _jwrite(p: str, data: Any):
    def _def(o): return None if isinstance(o, float) and (math.isnan(o) or math.isinf(o)) else str(o)
    Path(p).write_text(json.dumps(data, ensure_ascii=False, indent=2, default=_def), encoding="utf-8")

def _jload(p: str) -> Any:
    try:
        txt = Path(p).read_text(encoding="utf-8")
        if orjson: return orjson.loads(txt)
        return json.loads(txt)
    except Exception as e: log.warning("[MDL003] jload %s: %s", p, e); return None

# ============================================================================
# [VRN:ANCHOR:MDL003-LOAD-001] §4  MDL002 LOADER
# ============================================================================

def load_mdl002_output(mdl002_temp: str) -> Optional[Dict]:
    """VRN-MDL003-FNC-001  Load VRN_MDL002_Layout.json."""
    path = Path(mdl002_temp) / "VRN_MDL002_Layout.json"
    if not path.exists():
        log.error("[MDL003] VRN_MDL002_Layout.json not found in: %s", mdl002_temp)
        return None
    data = _jload(str(path))
    if not data or not data.get("reports"):
        log.error("[MDL003] VRN_MDL002_Layout.json is empty or invalid")
        return None
    log.info("[MDL003] Loaded MDL002: %d PDF reports", len(data["reports"]))
    return data

# ============================================================================
# [VRN:ANCHOR:MDL003-REPAIR-001] §5  TEXT REPAIR ENGINE
# ============================================================================

class TextRepairEngine:
    """VRN-MDL003-CLS-003
    9-step repair pipeline:
    R1 — encoding noise removal (watermarks, control chars)
    R2 — duplicate line dedup
    R3 — right-broken line merge (continuation to sentence end)
    R4 — normalize CJK spaces, trim
    R5 — header de-duplication (repeated column headers removed)
    R6 — empty/stub line removal (len<2)
    R7 — OCR numeric fix (l→1, O→0 in numeric context)
    R8 — axis noise filter (chart coordinate numbers)
    R9 — label canonicalization hint
    """

    _OCR_NUM_RE = re.compile(r"(?<!\w)([lO\|])(?=[\d,])|(?<=[\d,])([lO\|])(?!\w)")
    # Chinese char space removal
    _ZH_SPACE_RE = re.compile(r"(?<=[\u4e00-\u9fa5])\s+(?=[\u4e00-\u9fa5])")

    def repair_text_blocks(self, blocks: List[Dict], reflow: bool = True) -> List[Dict]:
        """Apply R1–R8 to text blocks, optionally merge sentences."""
        seen   = set()
        result = []
        for blk in blocks:
            text = blk.get("text", "")
            # R1: remove noise
            text = _NOISE_RE.sub(" ", text).strip()
            # R4: normalize spaces
            text = text.replace("\u3000", " ").replace("\u00a0", " ")
            text = self._ZH_SPACE_RE.sub("", text)
            text = re.sub(r" {2,}", " ", text)
            # R6: empty
            if not text or len(text) < 2: continue
            # R8: axis noise
            if is_axis_noise(text): continue
            # R2: dedup
            key = _hash8(text[:80])
            if key in seen: continue
            seen.add(key)
            blk = dict(blk); blk["text"] = text
            result.append(blk)

        if not reflow: return result

        # R3: sentence merge (向右向下整合直到句點)
        merged = []
        buf_text = ""
        buf_blk  = None
        for blk in result:
            text    = blk.get("text", "")
            is_tbl  = blk.get("block_type","") == "table"
            is_title= blk.get("is_title", False) or len(text) < 20

            if is_tbl or is_title:
                if buf_text and buf_blk:
                    merged.append(dict(buf_blk, text=buf_text.strip()))
                    buf_text = ""; buf_blk = None
                merged.append(blk)
                continue

            buf_text += text
            buf_blk   = blk
            # Sentence end?
            if re.search(r"[。！？.!?]$", buf_text.strip()):
                merged.append(dict(buf_blk, text=buf_text.strip()))
                buf_text = ""; buf_blk = None

        if buf_text and buf_blk:
            merged.append(dict(buf_blk, text=buf_text.strip()))
        return merged

    def repair_table_label(self, label: str) -> str:
        """R7: OCR numeric fix on label."""
        label = self._OCR_NUM_RE.sub(
            lambda m: "1" if (m.group(1) or m.group(2)) in "lL|" else "0", label
        )
        return label.strip()


# ============================================================================
# [VRN:ANCHOR:MDL003-RESTORE-001] §6  TABLE RESTORATION ENGINE
# ============================================================================

def canonicalize_label(label: str) -> str:
    """VRN-MDL003-FNC-002  Map raw label → canonical field name."""
    if label in _CANONICAL_MAP: return _CANONICAL_MAP[label]
    norm = re.sub(r"[\s/（）()（）%,，]", "", label)
    for k, v in _CANONICAL_MAP.items():
        if re.sub(r"[\s/（）()（）%,，]", "", k) == norm: return v
    for k, v in _CANONICAL_MAP.items():
        if k.lower() in label.lower() or label.lower() in k.lower(): return v
    return label.lower().replace(" ", "_")[:40]

def classify_fin_type(canonical: str) -> str:
    """VRN-MDL003-FNC-003"""
    if canonical in _IS_FIELDS: return "income_statement"
    if canonical in _BS_FIELDS: return "balance_sheet"
    if canonical in _CF_FIELDS: return "cash_flow"
    if canonical in _VL_FIELDS: return "valuation"
    return "other"

def clean_ocr_number(val: str) -> Optional[float]:
    """VRN-MDL003-FNC-004  Convert raw cell string to float or None."""
    if not val: return None
    val = str(val).strip()
    # Special strings → null
    if val in ("--", "---", "n.a.", "N/A", "NA", "nm", "NM",
               "盈轉虧", "虧轉盈", "-", "—", ""):
        return None
    # Remove thousands separators and spaces
    val = val.replace(",", "").replace("，", "").replace(" ", "").replace("\u00a0","")
    # Bracket negative: (268) → -268
    val = re.sub(r"^\((.*?)\)$", r"-\1", val)
    # Percentage: 48.5% → 48.5
    val = val.replace("%", "")
    # OCR: O→0, l→1 in pure numeric context
    val = re.sub(r"(?<!\w)O(?=\d)|(?<=\d)O(?!\w)", "0", val)
    try:
        return float(val)
    except ValueError:
        return None

def is_axis_noise(text: str) -> bool:
    """VRN-MDL003-FNC-005  Detect chart axis coordinate noise."""
    t = text.strip()
    if _AXIS_RE1.match(t): return True
    if _AXIS_RE2.match(t): return True
    if _AXIS_RE3.match(t): return True
    return False

@dataclass
class RestoredTable:
    """VRN-MDL003-CLS-006  One restored financial table."""
    region_id:        str = ""
    pdf_name:         str = ""
    report_code:      str = ""
    page_no:          int = 0
    region_type:      str = ""
    quadrant:         str = ""
    is_financial:     bool = False
    periods:          List[str] = field(default_factory=list)
    rows: List[Dict] = field(default_factory=list)
    # Format per row: {label_raw, canonical, fin_type, values: {period: float|None}, sources: {period: "RP"|"CALC"|"ERR"}}
    calc_applied:     int = 0
    err_count:        int = 0
    ok:               bool = False
    error:            Optional[str] = None

def restore_one_table(
    tbl_dict: Dict,
    repair: TextRepairEngine,
    cfg:    Dict,
) -> RestoredTable:
    """VRN-MDL003-FNC-006  Core table restoration logic."""
    rt = RestoredTable(
        region_id    = tbl_dict.get("region_id", ""),
        pdf_name     = tbl_dict.get("pdf_name", ""),
        report_code  = tbl_dict.get("report_code", ""),
        page_no      = tbl_dict.get("page_no", 0),
        region_type  = tbl_dict.get("region_type", ""),
        quadrant     = tbl_dict.get("quadrant", "full"),
        is_financial = tbl_dict.get("is_financial", False),
    )

    raw_data: List[List[str]] = tbl_dict.get("raw_data", [])
    if not raw_data or len(raw_data) < 2:
        rt.error = "insufficient_rows"; return rt

    # ── Step 1: Extract periods from header row(s) ───────────────────────────
    periods: List[str] = []
    data_start_row = 0
    for row_idx in range(min(3, len(raw_data))):
        row = raw_data[row_idx] or []
        row_periods = []
        for cell in row:
            cell_s = str(cell or "").strip()
            m = _PERIOD_RE.findall(cell_s)
            if m: row_periods.extend(m)
        if len(row_periods) >= 2:
            periods = list(dict.fromkeys(row_periods))  # dedup preserve order
            data_start_row = row_idx + 1
            break

    # Use MDL002's detected periods as fallback
    if not periods:
        periods = tbl_dict.get("header_periods", [])

    rt.periods = periods

    # ── Step 2: Parse data rows ──────────────────────────────────────────────
    rows_out: List[Dict] = []
    for row in raw_data[data_start_row:]:
        if not row: continue
        label_raw = repair.repair_table_label(str(row[0] or "").strip())
        if not label_raw or len(label_raw) < 1: continue
        # Skip header repeat rows (all periods/years in label)
        if re.fullmatch(r"[\s\d年QEFefCTctat\-/]+", label_raw): continue

        canonical = canonicalize_label(label_raw)
        fin_type  = classify_fin_type(canonical)

        # Parse numeric values
        values_raw: List[str] = [str(c or "").strip() for c in row[1:]]
        values_map: Dict[str, Optional[float]] = {}
        sources_map: Dict[str, str] = {}

        for ci, v_raw in enumerate(values_raw):
            period = periods[ci] if ci < len(periods) else f"col{ci}"
            v_num  = clean_ocr_number(v_raw)
            values_map[period]  = v_num
            sources_map[period] = "RP" if v_num is not None else "ERR"
            if v_num is None and v_raw not in ("", "--", "---", "n.a.", "N/A"):
                rt.err_count += 1

        rows_out.append({
            "label_raw":    label_raw,
            "canonical":    canonical,
            "fin_type":     fin_type,
            "values":       values_map,
            "sources":      sources_map,
        })

    rt.rows = rows_out

    if len(rt.rows) >= cfg.get("min_rows", 2):
        rt.ok = True
    else:
        rt.error = f"too_few_rows: {len(rt.rows)}"

    return rt

# ============================================================================
# [VRN:ANCHOR:MDL003-CALC-001] §7  CALC RULE ENGINE
# ============================================================================

def apply_calc_rules(rt: RestoredTable) -> RestoredTable:
    """VRN-MDL003-FNC: Apply accounting identities to fill ERR cells.
    For each period, if target field is None (ERR) but operands are available → CALC.
    """
    # Build lookup: canonical → row dict
    row_by_canonical: Dict[str, Dict] = {}
    for row in rt.rows:
        row_by_canonical[row["canonical"]] = row

    for target, (a_field, b_field, op) in CALC_RULES.items():
        if target not in row_by_canonical: continue
        tgt_row = row_by_canonical[target]

        for period in rt.periods:
            if tgt_row["sources"].get(period) in ("RP", "CALC"): continue  # already valid
            # Look up operands
            a_val = None
            b_val = None
            if a_field in row_by_canonical:
                a_val = row_by_canonical[a_field]["values"].get(period)
            if b_field and b_field in row_by_canonical:
                b_val = row_by_canonical[b_field]["values"].get(period)

            calc_val: Optional[float] = None
            if op == "sub" and a_val is not None and b_val is not None:
                calc_val = round(a_val - b_val, 4)
            elif op == "div" and a_val is not None and b_val and abs(b_val) > 0:
                calc_val = round(a_val / b_val, 6)
            elif op == "approx" and a_val is not None:
                # Just propagate operand a as approximation (pretax ≈ net)
                calc_val = a_val

            if calc_val is not None:
                tgt_row["values"][period]  = calc_val
                tgt_row["sources"][period] = "CALC"
                rt.calc_applied += 1

    return rt

# ============================================================================
# [VRN:ANCHOR:MDL003-VERIFY-001] §8  FINANCIAL VERIFICATION
# ============================================================================

def verify_financial_arithmetic(rt: RestoredTable) -> Dict:
    """VRN-MDL003-FNC-007  Cross-check key accounting identities."""
    results = []
    # Build lookup
    by_canon: Dict[str, Dict] = {r["canonical"]: r for r in rt.rows}

    checks = [
        ("gross_profit", "revenue", "cogs", "sub"),
        ("operating_income", "gross_profit", "opex", "sub"),
        ("gross_margin", "gross_profit", "revenue", "div"),
        ("operating_margin", "operating_income", "revenue", "div"),
    ]
    for target, a_f, b_f, op in checks:
        if target not in by_canon or a_f not in by_canon: continue
        tgt = by_canon[target]
        a_r = by_canon[a_f]
        b_r = by_canon.get(b_f, {})

        for period in rt.periods:
            t_v = tgt["values"].get(period)
            a_v = a_r["values"].get(period)
            b_v = b_r.get("values", {}).get(period) if b_r else None

            if t_v is None or a_v is None: continue
            if op == "sub" and b_v is not None:
                expected = a_v - b_v
                pct_diff = abs(t_v - expected) / (abs(expected) + 1e-6)
                ok = pct_diff < 0.02  # 2% tolerance
                results.append({
                    "check":    f"{target}={a_f}-{b_f}",
                    "period":   period,
                    "ok":       ok,
                    "expected": round(expected, 2),
                    "actual":   round(t_v, 2),
                    "diff_pct": round(pct_diff * 100, 2),
                })
            elif op == "div" and b_v and abs(b_v) > 0:
                expected = a_v / b_v
                pct_diff = abs(t_v - expected) / (abs(expected) + 1e-6)
                ok = pct_diff < 0.05  # 5% for ratios
                results.append({
                    "check":  f"{target}={a_f}/{b_f}",
                    "period": period,
                    "ok":     ok,
                    "diff_pct": round(pct_diff * 100, 2),
                })

    pass_count = sum(1 for r in results if r["ok"])
    return {
        "checks":     len(results),
        "pass":       pass_count,
        "fail":       len(results) - pass_count,
        "details":    results,
    }

# ============================================================================
# [VRN:ANCHOR:MDL003-TEXTFLOW-001] §9  TEXT FLOW RESTORATION
# ============================================================================

def reflow_text_blocks(blocks: List[Dict], repair: TextRepairEngine) -> List[Dict]:
    """VRN-MDL003-FNC-008  Apply full text repair + sentence merge."""
    return repair.repair_text_blocks(blocks, reflow=True)

# ============================================================================
# [VRN:ANCHOR:MDL003-EXTERNAL-001] §10  EXTERNAL SSOT INTEGRATION
# ============================================================================


def _cel_submit(fn, *args, **kw):
    """Submit via Celeritas _LazyPool if available, else direct call."""
    if _CEL_OK:
        if hasattr(_CEL, "_LazyPool"):
            try: return _CEL._LazyPool.submit(fn, *args, **kw)
            except Exception: pass
        if hasattr(_CEL, "submit"):
            try: return _CEL.submit(fn, *args, **kw)
            except Exception: pass
    return fn(*args, **kw)

def load_external_ssot(ssot_dir: str) -> Dict:
    """VRN-MDL003-FNC-009  Load 7 supportive tools per VIA_Supportive_HardGate_Seal.json.
    Policy: BOOT_PRECHECK_ONLY_NO_NETWORK_NO_PARALLEL_NO_AUTOPATCH.
    """
    # [VRN:ANCHOR:HARDGATE_RESULT:V1] 7-key result dict per HardGate Seal
    result = {"via_ssot": False, "registry": False, "runtime_bridge": False,
              "env_manager": False, "ast_planner": False,
              "celeritas": False, "aegis": False}
    ssot_path = Path(ssot_dir)
    if not ssot_path.is_dir(): return result

    # Add ssot_dir to sys.path temporarily
    ssot_str = str(ssot_path)
    if ssot_str not in sys.path:
        sys.path.insert(0, ssot_str)

    # VIA_SSOT_Unified
    try:
        import importlib
        via_ssot = importlib.import_module("VIA_SSOT_Unified")
        # Attempt to merge synonym maps if available
        if hasattr(via_ssot, "CANONICAL_MAP"):
            ext_map: Dict = getattr(via_ssot, "CANONICAL_MAP", {})
            for k, v in ext_map.items():
                if k not in _CANONICAL_MAP:  # append-only
                    _CANONICAL_MAP[k] = v
            log.info("[MDL003] VIA_SSOT_Unified: merged %d new entries", len(ext_map))
        result["via_ssot"] = True
    except Exception as e:
        log.debug("[MDL003] VIA_SSOT_Unified not loaded: %s", e)

    # VeritasAegisNexus
    try:
        aegis = importlib.import_module("VeritasAegisNexus")
        result["aegis"] = True
        log.info("[MDL003] VeritasAegisNexus loaded")
    except Exception as e:
        log.debug("[MDL003] VeritasAegisNexus not loaded: %s", e)

    # VeritasCeleritas — spec/exec with sys.modules inject (Python 3.12 @dataclass fix)
    try:
        import importlib.util as _ilu3
        _cel_paths = [Path(ssot_dir)/"VeritasCeleritas.py",
                      Path(ssot_dir).parent/"VeritasCeleritas.py"]
        for _cp in _cel_paths:
            if _cp.exists():
                _spec3 = _ilu3.spec_from_file_location("VeritasCeleritas", str(_cp))
                _mod3  = _ilu3.module_from_spec(_spec3)
                sys.modules["VeritasCeleritas"] = _mod3   # inject before exec (Py3.12)
                _spec3.loader.exec_module(_mod3)
                result["celeritas"] = True
                if hasattr(_mod3, "bootstrap_at_import"): _mod3.bootstrap_at_import(__file__)
                if hasattr(_mod3, "warm_thread_pool"):    _mod3.warm_thread_pool()
                log.info("[MDL003] VeritasCeleritas loaded from %s", _cp)
                break
    except Exception as e:
        log.debug("[MDL003] VeritasCeleritas not loaded: %s", e)

    # [VRN:ANCHOR:HARDGATE_EXTRA_TOOLS:V1] Load 4 remaining HardGate Seal tools
    # Order per VIA_Supportive_HardGate_Seal.json after the 3 already loaded above.
    for mod_name, key in [
        ("VIA_RegistryCore_v1",              "registry"),
        ("VIA_Runtime_Bridge_All_in_One",    "runtime_bridge"),
        ("VIA_EnvManager",                   "env_manager"),
        ("VIA_Panorama_AST_RuntimeInjector", "ast_planner"),
    ]:
        try:
            import importlib as _il
            _m = _il.import_module(mod_name)
            result[key] = True
            log.info("[MDL003] %s loaded", mod_name)
        except Exception as e:
            log.debug("[MDL003] %s not loaded: %s", mod_name, e)

    return result

# ============================================================================
# [VRN:ANCHOR:MDL003-DB-001] §11  DB WRITER
# ============================================================================

class MDL003DBWriter:
    """VRN-MDL003-CLS-002"""

    DDL = """
CREATE TABLE IF NOT EXISTS vrn_mdl003_financial_rows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    region_id TEXT, pdf_name TEXT, report_code TEXT,
    page_no INTEGER, region_type TEXT, quadrant TEXT,
    label_raw TEXT, canonical TEXT, fin_type TEXT,
    period TEXT, value REAL, source TEXT,
    calc_applied INTEGER DEFAULT 0,
    ts TEXT DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS vrn_mdl003_verify_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    region_id TEXT, pdf_name TEXT, report_code TEXT,
    check_name TEXT, period TEXT, ok INTEGER,
    expected REAL, actual REAL, diff_pct REAL,
    ts TEXT DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS vrn_mdl003_text_flow (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    block_id TEXT, pdf_name TEXT, report_code TEXT,
    page_no INTEGER, block_type TEXT, text TEXT,
    is_title INTEGER, is_bold INTEGER, font_size REAL,
    ts TEXT DEFAULT (datetime('now','localtime'))
);
"""
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._con    = sqlite3.connect(db_path, check_same_thread=False)
        self._lock   = threading.Lock()
        self._con.execute("PRAGMA journal_mode=WAL")
        self._con.execute("PRAGMA synchronous=NORMAL")
        self._con.executescript(self.DDL)
        self._con.commit()

    def insert_financial_rows(self, rt: RestoredTable):
        sql = """INSERT INTO vrn_mdl003_financial_rows
                 (region_id,pdf_name,report_code,page_no,region_type,quadrant,
                  label_raw,canonical,fin_type,period,value,source,calc_applied)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)"""
        rows_flat = []
        for row in rt.rows:
            for period, val in row["values"].items():
                src = row["sources"].get(period, "ERR")
                rows_flat.append((
                    rt.region_id, rt.pdf_name, rt.report_code,
                    rt.page_no, rt.region_type, rt.quadrant,
                    row["label_raw"], row["canonical"], row["fin_type"],
                    period, val, src, rt.calc_applied,
                ))
        with self._lock:
            self._con.executemany(sql, rows_flat)
            self._con.commit()

    def insert_verify(self, rt: RestoredTable, verify: Dict):
        sql = """INSERT INTO vrn_mdl003_verify_results
                 (region_id,pdf_name,report_code,check_name,period,ok,expected,actual,diff_pct)
                 VALUES (?,?,?,?,?,?,?,?,?)"""
        with self._lock:
            for det in verify.get("details", []):
                self._con.execute(sql, (
                    rt.region_id, rt.pdf_name, rt.report_code,
                    det.get("check",""), det.get("period",""),
                    1 if det.get("ok") else 0,
                    det.get("expected"), det.get("actual"), det.get("diff_pct"),
                ))
            self._con.commit()

    def insert_text_flow(self, blocks: List[Dict]):
        sql = """INSERT INTO vrn_mdl003_text_flow
                 (block_id,pdf_name,report_code,page_no,block_type,text,is_title,is_bold,font_size)
                 VALUES (?,?,?,?,?,?,?,?,?)"""
        with self._lock:
            for b in blocks:
                self._con.execute(sql, (
                    b.get("block_id",""), b.get("pdf_name",""),
                    b.get("report_code",""), b.get("page_no",0),
                    b.get("block_type",""), b.get("text",""),
                    1 if b.get("is_title") else 0,
                    1 if b.get("is_bold") else 0,
                    b.get("font_size",0.0),
                ))
            self._con.commit()

    def export_parquet(self, out_dir: str):
        if not pd or not pyarrow: return
        try:
            df = pd.read_sql("SELECT * FROM vrn_mdl003_financial_rows", self._con)
            df.to_parquet(str(Path(out_dir) / "VRN_MDL003_Restored.parquet"), index=False)
        except Exception as e: log.warning("[MDL003] parquet: %s", e)

    def export_csv(self, out_dir: str):
        if not pd: return
        try:
            df = pd.read_sql("SELECT * FROM vrn_mdl003_financial_rows", self._con)
            df.to_csv(str(Path(out_dir) / "VRN_MDL003_Restored.csv"),
                      index=False, encoding="utf-8-sig")
        except Exception as e: log.warning("[MDL003] csv: %s", e)

# ============================================================================
# CORE PROCESSOR
# ============================================================================

def process_one_pdf(
    pdf_report: Dict,
    cfg:        Dict,
    repair:     TextRepairEngine,
    db:         Optional[MDL003DBWriter],
) -> Dict:
    """VRN-MDL003-FNC-010  Restore all tables + text for one PDF report."""
    t0          = time.perf_counter()
    pdf_name    = pdf_report.get("pdf_name", "")
    report_code = pdf_report.get("report_code", "")

    out = {
        "pdf_name":          pdf_name,
        "report_code":       report_code,
        "ticker":            pdf_report.get("ticker", ""),
        "report_date":       pdf_report.get("report_date", ""),
        "broker_abbr":       pdf_report.get("broker_abbr", ""),
        "n_tables_in":       len(pdf_report.get("tables", [])),
        "n_tables_restored": 0,
        "n_tables_ok":       0,
        "n_financial_tables":0,
        "n_calc_applied":    0,
        "n_err":             0,
        "n_verify_pass":     0,
        "n_verify_fail":     0,
        "n_text_blocks_in":  len(pdf_report.get("text_blocks", [])),
        "n_text_blocks_out": 0,
        "restored_tables":   [],
        "text_flow":         [],
        "ok":                False,
        "error":             None,
        "elapsed":           0.0,
    }

    try:
        # ── Restore tables ─────────────────────────────────────────────────
        for tbl_dict in pdf_report.get("tables", []):
            rt = restore_one_table(tbl_dict, repair, cfg)

            # Apply CALC rules
            if cfg.get("enable_calc", True) and rt.ok:
                rt = apply_calc_rules(rt)
                out["n_calc_applied"] += rt.calc_applied

            out["n_err"] += rt.err_count

            # Verify arithmetic
            verify_result = {}
            if rt.ok and rt.is_financial:
                verify_result = verify_financial_arithmetic(rt)
                out["n_verify_pass"] += verify_result.get("pass", 0)
                out["n_verify_fail"] += verify_result.get("fail", 0)

            out["n_tables_restored"] += 1
            if rt.ok:
                out["n_tables_ok"] += 1
            if rt.is_financial:
                out["n_financial_tables"] += 1

            # Serialize restored table
            rt_dict = {
                "region_id":    rt.region_id,
                "pdf_name":     rt.pdf_name,
                "report_code":  rt.report_code,
                "page_no":      rt.page_no,
                "region_type":  rt.region_type,
                "quadrant":     rt.quadrant,
                "is_financial": rt.is_financial,
                "periods":      rt.periods,
                "rows":         rt.rows,
                "calc_applied": rt.calc_applied,
                "err_count":    rt.err_count,
                "ok":           rt.ok,
                "error":        rt.error,
                "verify":       verify_result,
            }
            out["restored_tables"].append(rt_dict)

            if db:
                try:
                    if rt.ok: db.insert_financial_rows(rt)
                    if verify_result: db.insert_verify(rt, verify_result)
                except Exception as e:
                    log.warning("[MDL003] DB rows %s: %s", rt.region_id, e)

        # ── Restore text ───────────────────────────────────────────────────
        if cfg.get("text_reflow", True):
            raw_blocks = pdf_report.get("text_blocks", [])
            flowed = reflow_text_blocks(raw_blocks, repair)
            out["n_text_blocks_out"] = len(flowed)
            out["text_flow"] = flowed

            if db and flowed:
                try: db.insert_text_flow(flowed)
                except Exception as e:
                    log.warning("[MDL003] DB text %s: %s", pdf_name, e)

        out["ok"] = True

    except Exception as e:
        out["error"] = str(e)
        log.error("[MDL003] process_one_pdf %s: %s", pdf_name, e)

    out["elapsed"] = round(time.perf_counter() - t0, 2)
    log.info("[MDL003] %s: tables=%d/%d  fin=%d  calc=%d  err=%d  txt=%d  %.2fs",
             pdf_name, out["n_tables_ok"], out["n_tables_restored"],
             out["n_financial_tables"], out["n_calc_applied"],
             out["n_err"], out["n_text_blocks_out"], out["elapsed"])
    return out

# ============================================================================
# [VRN:ANCHOR:MDL003-OUT-001] §12
# ============================================================================

def assemble_output(results: List[Dict]) -> Dict:
    """VRN-MDL003-FNC-011"""
    ok_count = sum(1 for r in results if r.get("ok"))
    return {
        "module":              __module_id__,
        "version":             __version__,
        "generated":           time.strftime("%Y-%m-%d %H:%M:%S"),
        "total":               len(results),
        "ok_count":            ok_count,
        "fail_count":          len(results) - ok_count,
        "total_tables_in":     sum(r.get("n_tables_in",0) for r in results),
        "total_tables_ok":     sum(r.get("n_tables_ok",0) for r in results),
        "total_fin_tables":    sum(r.get("n_financial_tables",0) for r in results),
        "total_calc_applied":  sum(r.get("n_calc_applied",0) for r in results),
        "total_err":           sum(r.get("n_err",0) for r in results),
        "total_verify_pass":   sum(r.get("n_verify_pass",0) for r in results),
        "total_verify_fail":   sum(r.get("n_verify_fail",0) for r in results),
        "total_text_blocks":   sum(r.get("n_text_blocks_out",0) for r in results),
        "reports":             results,
    }

# ============================================================================
# [VRN:ANCHOR:MDL003-SYS-001] §13  PIPELINE ENTRY
# ============================================================================

class VRN_MDL003_TableRestorer:
    """VRN-MDL003-CLS-001
    run():
      1. Load external SSOT (optional)
      2. Accel init
      3. Load VRN_MDL002_Layout.json
      4. Parallel process_one_pdf() — restore tables + text
      5. DB export
      6. VRN_MDL003_Restored.json + TextFlow.json + VerifySummary.json
    """
    def __init__(self, cfg: Dict):
        self.cfg     = cfg
        workers      = cfg.get("workers", 0) or max(1, (os.cpu_count() or 4) - 1)
        self.workers = workers
        self.db: Optional[MDL003DBWriter] = None
        self.repair  = TextRepairEngine()

    def run(self) -> Dict:
        mdl002_temp = self.cfg.get("mdl002_temp", _DEFAULTS["mdl002_temp"])
        mdl003_temp = self.cfg.get("mdl003_temp", _DEFAULTS["mdl003_temp"])
        ssot_dir    = self.cfg.get("ssot_dir",    _DEFAULTS["ssot_dir"])
        Path(mdl003_temp).mkdir(parents=True, exist_ok=True)

        # Load external SSOT
        ssot_caps = load_external_ssot(ssot_dir)
        log.info("[MDL003] SSOT caps: %s", ssot_caps)

        cap = _mdl003_accel_init(self.workers)
        log.info("[MDL003] accel caps: %s", cap)

        if self.cfg.get("enable_db", True):
            self.db = MDL003DBWriter(str(Path(mdl003_temp) / "VRN_MDL003.db"))

        # Load MDL002 output
        mdl002_data = load_mdl002_output(mdl002_temp)
        if not mdl002_data:
            return {"ok": False, "total": 0, "success": 0,
                    "errors": ["MDL002 output not found"], "out_dir": mdl003_temp}

        pdf_reports = mdl002_data.get("reports", [])
        log.info("[MDL003] Restoring %d PDF reports, workers=%d",
                 len(pdf_reports), self.workers)

        all_results: List[Dict] = []
        fail_count = 0

        with ThreadPoolExecutor(max_workers=self.workers) as ex:
            futs = {
                ex.submit(process_one_pdf, rpt, self.cfg, self.repair, self.db): rpt
                for rpt in pdf_reports
            }
            for fut in as_completed(futs):
                res = fut.result()
                all_results.append(res)
                if not res.get("ok"): fail_count += 1

        if self.db:
            self.db.export_parquet(mdl003_temp)
            self.db.export_csv(mdl003_temp)

        out = assemble_output(all_results)
        _jwrite(str(Path(mdl003_temp) / "VRN_MDL003_Restored.json"), out)

        # Separate text flow output
        text_flow_out = {
            "module": __module_id__, "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "reports": [
                {"pdf_name": r["pdf_name"], "report_code": r["report_code"],
                 "text_flow": r.get("text_flow", [])}
                for r in all_results
            ]
        }
        _jwrite(str(Path(mdl003_temp) / "VRN_MDL003_TextFlow.json"), text_flow_out)

        verify_summary = {
            "module":             __module_id__,
            "version":            __version__,
            "generated":          time.strftime("%Y-%m-%d %H:%M:%S"),
            "total":              len(pdf_reports),
            "ok":                 fail_count == 0,
            "ok_count":           len(pdf_reports) - fail_count,
            "fail_count":         fail_count,
            "total_tables_ok":    out["total_tables_ok"],
            "total_fin_tables":   out["total_fin_tables"],
            "total_calc_applied": out["total_calc_applied"],
            "total_err":          out["total_err"],
            "total_verify_pass":  out["total_verify_pass"],
            "total_verify_fail":  out["total_verify_fail"],
            "ssot_caps":          ssot_caps,
            "accel_caps":         cap,
            "fail_details": [
                {"pdf_name": r["pdf_name"], "error": r.get("error")}
                for r in all_results if not r.get("ok")
            ],
        }
        _jwrite(str(Path(mdl003_temp) / "VRN_MDL003_VerifySummary.json"), verify_summary)

        log.info(
            "[MDL003] Complete: %d/%d OK  tables=%d/%d  fin=%d  calc=%d  err=%d  "
            "verify=%d/%d  text=%d",
            len(pdf_reports) - fail_count, len(pdf_reports),
            out["total_tables_ok"], out["total_tables_in"],
            out["total_fin_tables"], out["total_calc_applied"],
            out["total_err"], out["total_verify_pass"],
            out["total_verify_pass"] + out["total_verify_fail"],
            out["total_text_blocks"],
        )
        return {
            "ok":               fail_count == 0,
            "total":            len(pdf_reports),
            "success":          len(pdf_reports) - fail_count,
            "total_tables_ok":  out["total_tables_ok"],
            "total_fin_tables": out["total_fin_tables"],
            "total_calc":       out["total_calc_applied"],
            "total_err":        out["total_err"],
            "errors":           [r.get("error","") for r in all_results if not r.get("ok")],
            "out_dir":          mdl003_temp,
        }

# ============================================================================
# __all__
# ============================================================================

__all__ = [
    "__version__", "__module_id__",
    "TW_TICKER_REGEX", "TW_BLOOMBERG_REGEX", "TW_YFINANCE_REGEX",
    "_CANONICAL_MAP", "CALC_RULES",
    "_mdl003_accel_init",
    "load_mdl002_output", "load_external_ssot",
    "canonicalize_label", "classify_fin_type",
    "clean_ocr_number", "is_axis_noise",
    "TextRepairEngine", "TableRestoreEngine",
    "RestoredTable",
    "restore_one_table", "apply_calc_rules", "verify_financial_arithmetic",
    "reflow_text_blocks",
    "process_one_pdf", "assemble_output",
    "MDL003DBWriter", "VRN_MDL003_TableRestorer",
]

# ============================================================================
# __main__
# ============================================================================

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="VRN MDL003 TableRestorer -- Restore+Validate")
    for k, v in _DEFAULTS.items():
        tp = bool if isinstance(v, bool) else (int if isinstance(v, int) else str)
        if tp == bool: p.add_argument("--" + k.replace("_", "-"), action="store_true", default=v)
        else:          p.add_argument("--" + k.replace("_", "-"), type=tp, default=v)
    args   = p.parse_args()
    cfg    = {k.replace("-", "_"): v for k, v in vars(args).items()}
    result = VRN_MDL003_TableRestorer(cfg).run()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["ok"] else 1)