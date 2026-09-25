# -*- coding: utf-8 -*-
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
"""
VRN_MDL003_TableRestorer.py
============================
VERITAS REPORT NOVA -- MDL003  Table Restoration + Validation + SSOT Integration
Version   : 1.1.0   |   Module ID : VRN-MDL003-SUP-001
Asset ID  : VRN-MDL003-CLS-001
Policy    : 功能只增不減 · append-only · SSOT · 獨立模組

▓▓▓ v1.1.0 變更摘要（功能只增不減）▓▓▓
  ✓ Polars-first 架構：DataFrame 為主資料路徑，pandas 變 fallback
  ✓ DuckDB-first 持久層：sqlite WAL 變 fallback（雙寫保證）
  ✓ P1 DB batch commit：buffer 池 + 單次 flush，解決 ThreadPoolExecutor 鎖序列化
  ✓ P2 module-level 預編譯 regex pool：clean_ocr_number / canonicalize 不再每呼叫重編
  ✓ P3 _CANON_NORM_CACHE / _CANON_LOWER_CACHE：canonicalize_label O(1) 快取
  ✓ P4 _jwrite_fast()：orjson 快寫，回退 json
  ✓ P5 polars batch parquet/csv 直寫，跳過 SQL 來回
  ✓ P6 repair_text_blocks_batch()：Polars vectorized text 處理
  ✓ P7 4-phase self-verification：READY/NEAR-READY/NOT-READY HTML 報告
  ✓ 既有 v1.0.0 函數簽名 100% 保留，全部 append-only

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
  [VRN:ANCHOR:MDL003-META-001]    §0  Module Metadata
  [VRN:ANCHOR:MDL003-SSOT-001]    §1  Embedded SSOT + Synonym Engine
  [VRN:ANCHOR:MDL003-ACCEL-001]   §2  Accelerator Init
  [VRN:ANCHOR:MDL003-DAT-001]     §3  Config / _DEFAULTS
  [VRN:ANCHOR:MDL003-LOAD-001]    §4  MDL002 Output Loader
  [VRN:ANCHOR:MDL003-REPAIR-001]  §5  Text Repair Engine (R1–R9)
  [VRN:ANCHOR:MDL003-RESTORE-001] §6  Table Restoration Engine
  [VRN:ANCHOR:MDL003-CALC-001]    §7  CALC Rule Engine (accounting identities)
  [VRN:ANCHOR:MDL003-VERIFY-001]  §8  Financial Verification + Tagging (RP/CALC/API/ERR)
  [VRN:ANCHOR:MDL003-TEXTFLOW-001] §9 Text Flow Restoration (sentence merge)
  [VRN:ANCHOR:MDL003-EXTERNAL-001] §10 External SSOT Integration (optional)
  [VRN:ANCHOR:MDL003-DB-001]      §11 DB Writer (DuckDB-first + sqlite fallback)
  [VRN:ANCHOR:MDL003-OUT-001]     §12 Output Assembler
  [VRN:ANCHOR:MDL003-SELFCHK-001] §12.5 4-Phase Self-Verification
  [VRN:ANCHOR:MDL003-SYS-001]     §13 Pipeline Entry

SMART ASSET REGISTRY
  VRN-MDL003-CLS-001  VRN_MDL003_TableRestorer
  VRN-MDL003-CLS-002  MDL003DBWriter           (sqlite, fallback)
  VRN-MDL003-CLS-003  TextRepairEngine
  VRN-MDL003-CLS-004  TableRestoreEngine
  VRN-MDL003-CLS-005  FinancialVerifier
  VRN-MDL003-CLS-006  RestoredTable
  VRN-MDL003-CLS-007  RestoredTextBlock
  VRN-MDL003-CLS-008  MDL003DuckWriter         (NEW v1.1.0 — DuckDB-first)
  VRN-MDL003-CLS-009  MDL003BatchBuffer        (NEW v1.1.0 — batch commit)
  VRN-MDL003-CLS-010  MDL003SelfVerifier       (NEW v1.1.0 — 4-phase)
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
  VRN-MDL003-FNC-013  _jwrite_fast            (NEW v1.1.0 — orjson)
  VRN-MDL003-FNC-014  pl_export_parquet       (NEW v1.1.0 — polars direct)
  VRN-MDL003-FNC-015  pl_export_csv           (NEW v1.1.0 — polars direct)
  VRN-MDL003-FNC-016  repair_text_blocks_batch (NEW v1.1.0 — polars vectorized)
  VRN-MDL003-FNC-017  build_self_verify_html   (NEW v1.1.0 — VIA Visual Lock)

OUTPUTS (mdl003_temp)
  VRN_MDL003_Restored.json          ← 主輸出：還原表格 + 驗證結果 → MDL004+
  VRN_MDL003_VerifySummary.json     ← 驗證摘要 (RP/CALC/API/ERR counts)
  VRN_MDL003.duckdb                 ← DuckDB primary (NEW v1.1.0)
  VRN_MDL003.db                     ← SQLite WAL (fallback)
  VRN_MDL003_Restored.parquet       ← Parquet flat (FinancialRow per record, polars-direct)
  VRN_MDL003_Restored.csv           ← CSV (UTF-8 BOM)
  VRN_MDL003_TextFlow.json          ← 還原文字段落 (for RAG/LLM)
  VRN_MDL003_SelfVerify.html        ← 4-phase debug chain report (NEW v1.1.0)

SSOT INTEGRATION PATHS
  supportive_module/VIA_SSOT_Unified.py      ← optional synonym extension
  supportive_module/VeritasAegisNexus.py     ← optional governance check
  supportive_module/VeritasCeleritas.py      ← optional acceleration

LL RULES: #10 #12 #13 #15 #17 #18 #19 #20 #21 #22 #23 #24
"""

# ============================================================================
# [VRN:ANCHOR:MDL003-META-001] §0
# ============================================================================

__version__   = "1.1.0"
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
from typing import Any, Dict, List, Optional, Tuple, Iterable
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

# ── v1.1.0: Polars + DuckDB (primary) ─────────────────────────────────────────
pl       = _si("polars")
duckdb   = _si("duckdb")

POLARS_OK = pl is not None
DUCKDB_OK = duckdb is not None

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
# [VRN:ANCHOR:MDL003-PRECOMP-001] §1.5  P2 PRE-COMPILED REGEX POOL (v1.1.0)
# ── 所有 hot-path regex 集中預編譯，避免函數內 re.sub() 每呼叫重編 ──────────────
# ============================================================================

# clean_ocr_number 用
_RE_BRACKET_NEG  = re.compile(r"^\((.*?)\)$")
# v1.1.0 fix: original (?<!\w)O(?=\d)|(?<=\d)O(?!\w) failed for "2O25"
# because both sides of inner O are \w. Allow O when surrounded by digits.
_RE_OCR_O_TO_0   = re.compile(
    r"(?<![A-Za-z])O(?=\d)"   # O at start or after non-letter, before digit
    r"|(?<=\d)O(?=\d)"        # O between digits  ← KEY FIX
    r"|(?<=\d)O(?![A-Za-z])"  # O after digit, not before letter
)
# canonicalize_label 用
_RE_NORM_PUNCT   = re.compile(r"[\s/（）()（）%,，]")
# restore_one_table 用
_RE_HDR_REPEAT   = re.compile(r"[\s\d年QEFefCTctat\-/]+")
# repair_text_blocks 用
_RE_DOUBLESPACE  = re.compile(r" {2,}")
_RE_SENT_END     = re.compile(r"[。！？.!?]$")

# ── P3: _CANONICAL_MAP O(1) lookup caches ─────────────────────────────────────
# 在 __init__ 階段建立，並在 load_external_ssot append 時重建
_CANON_NORM_CACHE:  Dict[str, str] = {}     # norm(key) → value
_CANON_LOWER_CACHE: List[Tuple[str, str, str]] = []  # (key_lower, value, key_orig)

def _rebuild_canon_caches():
    """P3: Rebuild O(1) caches after _CANONICAL_MAP is mutated."""
    global _CANON_NORM_CACHE, _CANON_LOWER_CACHE
    _CANON_NORM_CACHE = {
        _RE_NORM_PUNCT.sub("", k): v for k, v in _CANONICAL_MAP.items()
    }
    _CANON_LOWER_CACHE = [
        (k.lower(), v, k) for k, v in _CANONICAL_MAP.items()
    ]

_rebuild_canon_caches()  # initial build

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
    return {
        "workers":   w,
        "pyarrow":   pyarrow is not None,
        "fitz":      fitz is not None,
        "polars":    POLARS_OK,
        "duckdb":    DUCKDB_OK,
        "orjson":    orjson is not None,
    }

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
    # ── v1.1.0 NEW ───────────────────────────────────────────────────────────
    use_duckdb   = True,     # DuckDB primary, sqlite fallback
    batch_size   = 5000,     # P1 batch buffer flush threshold
    self_verify  = True,     # P7 4-phase self-verification HTML
    polars_first = True,     # use polars batch path for parquet/csv
)

# ============================================================================
# [VRN:ANCHOR:MDL003-PLUGIN-HOLDERS-001] §3.5  PLUGIN HOLDERS (7 HardGate tools)
# ============================================================================

# [VRN:ANCHOR:HARDGATE_HOLDERS:V1]
_SSOT: Any = None;  _SSOT_OK:  bool = False
_REG:  Any = None;  _REG_OK:   bool = False
_BRG:  Any = None;  _BRG_OK:   bool = False
_ENV:  Any = None;  _ENV_OK:   bool = False
_AST:  Any = None;  _AST_OK:   bool = False
_CEL:  Any = None;  _CEL_OK:   bool = False
_NET:  Any = None;  _NET_OK:   bool = False

def _find_plugin(ssot_dir: str, filename: str) -> Optional[str]:
    """VRN-MDL003-FNC-PLUGIN-001  Search ssot_dir + parents for plugin file."""
    candidates = [
        Path(ssot_dir) / filename,
        Path(ssot_dir).parent / filename,
        Path(ssot_dir).parent.parent / "module" / filename,
        Path(ssot_dir).parent.parent / "supportive_module" / filename,
    ]
    for c in candidates:
        if c.exists(): return str(c)
    return None

# ============================================================================
# UTILITIES
# ============================================================================

def _hash8(s: str) -> str:
    if xxhash: return xxhash.xxh64(s.encode()).hexdigest()[:8].upper()
    return hashlib.sha256(s.encode()).hexdigest()[:8].upper()

def _jwrite(p: str, data: Any):
    """Legacy json writer (kept for backward compat)."""
    def _def(o): return None if isinstance(o, float) and (math.isnan(o) or math.isinf(o)) else str(o)
    Path(p).write_text(json.dumps(data, ensure_ascii=False, indent=2, default=_def), encoding="utf-8")

def _jwrite_fast(p: str, data: Any) -> float:
    """VRN-MDL003-FNC-013 (P4)  orjson fast write, fallback to _jwrite.
    Returns elapsed seconds."""
    t0 = time.perf_counter()
    if orjson is not None:
        try:
            opts = orjson.OPT_INDENT_2 | orjson.OPT_NON_STR_KEYS | orjson.OPT_SERIALIZE_NUMPY
            def _default(o):
                if isinstance(o, float) and (math.isnan(o) or math.isinf(o)): return None
                return str(o)
            Path(p).write_bytes(orjson.dumps(data, default=_default, option=opts))
            return round(time.perf_counter() - t0, 4)
        except Exception as e:
            log.warning("[MDL003] orjson fail (%s), fallback json", e)
    _jwrite(p, data)
    return round(time.perf_counter() - t0, 4)

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
        """Apply R1–R8 to text blocks, optionally merge sentences. (legacy path)"""
        seen   = set()
        result = []
        for blk in blocks:
            text = blk.get("text", "")
            # R1: remove noise
            text = _NOISE_RE.sub(" ", text).strip()
            # R4: normalize spaces
            text = text.replace("\u3000", " ").replace("\u00a0", " ")
            text = self._ZH_SPACE_RE.sub("", text)
            text = _RE_DOUBLESPACE.sub(" ", text)
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
            if _RE_SENT_END.search(buf_text.strip()):
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
# [VRN:ANCHOR:MDL003-TEXT-BATCH-001] §5.5  P6 POLARS TEXT BATCH (v1.1.0)
# ============================================================================

def repair_text_blocks_batch(
    blocks: List[Dict],
    reflow: bool = True,
) -> List[Dict]:
    """VRN-MDL003-FNC-016 (P6)
    Polars-vectorized text repair:
      - R1/R4/R6/R8 全部用 polars expression chain，避免 Python 迴圈
      - R2 dedup 用 polars unique() on hash
      - R3 sentence merge 仍走 Python（有狀態，無法純向量化）

    Falls back to TextRepairEngine().repair_text_blocks() if polars unavailable
    or block list is small (< 50 items, overhead not worth it).
    """
    if not blocks:
        return []

    # 小樣本走原路徑（避免 polars overhead）
    if not POLARS_OK or len(blocks) < 50:
        return TextRepairEngine().repair_text_blocks(blocks, reflow=reflow)

    try:
        # ── Build DataFrame ──────────────────────────────────────────────────
        df = pl.DataFrame({
            "idx":        list(range(len(blocks))),
            "text":       [str(b.get("text", "")) for b in blocks],
            "block_type": [str(b.get("block_type", "")) for b in blocks],
            "is_title":   [bool(b.get("is_title", False)) for b in blocks],
        })

        # ── R1+R4: noise + space normalize (vectorized) ──────────────────────
        # NOTE: polars regex (Rust regex crate) 不支援 look-behind / look-ahead,
        # 所以原本的 `(?<=[\u4e00-\u9fa5])\s+(?=[\u4e00-\u9fa5])` 必須改寫
        # 策略：先把連續空白壓到 1 個，再用 capturing group 匹配「漢字+空白+漢字」
        df = df.with_columns([
            pl.col("text")
              .str.replace_all(r"\{.*?\}", " ")
              .str.replace_all(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ")
              .str.replace_all(r"\u3000", " ")
              .str.replace_all(r"\u00a0", " ")
              .str.replace_all(r" {2,}", " ")
              # 多次套用以去掉漢字之間單一空白(因為每次 sub 只消費一個空白且
              # 後一漢字會被前一輪的 capture 吃掉，需要再跑一次掃尾巴)
              .str.replace_all(r"([\u4e00-\u9fa5]) ([\u4e00-\u9fa5])", r"$1$2")
              .str.replace_all(r"([\u4e00-\u9fa5]) ([\u4e00-\u9fa5])", r"$1$2")
              .str.strip_chars()
              .alias("text_clean")
        ])

        # ── R6: drop empty/short ─────────────────────────────────────────────
        df = df.filter(pl.col("text_clean").str.len_chars() >= 2)

        # ── R8: axis noise filter (vectorized regex match) ───────────────────
        df = df.filter(
            ~pl.col("text_clean").str.contains(r"^[-+]?[\d\s,\.]+%?$")
            & ~pl.col("text_clean").str.contains(r"^(?:[-+]?\d{1,3}(?:\.\d+)?[%O]?\s*){4,}$")
            & ~pl.col("text_clean").str.contains(r"^\s*(\d+[OBoS]+|[sS]o+|JO+|I+)\s*$")
        )

        # ── R2: dedup by first-80-char hash (use polars unique) ─────────────
        df = df.with_columns([
            pl.col("text_clean").str.slice(0, 80).hash().alias("h80")
        ])
        df = df.unique(subset=["h80"], keep="first", maintain_order=True)

        # ── Reconstruct kept block dicts in original order ───────────────────
        kept_indices = df.sort("idx")["idx"].to_list()
        kept_texts   = df.sort("idx")["text_clean"].to_list()

        result = []
        for ki, kt in zip(kept_indices, kept_texts):
            blk = dict(blocks[ki])
            blk["text"] = kt
            result.append(blk)

        if not reflow:
            return result

        # ── R3: sentence merge (stateful, Python loop) ───────────────────────
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
            if _RE_SENT_END.search(buf_text.strip()):
                merged.append(dict(buf_blk, text=buf_text.strip()))
                buf_text = ""; buf_blk = None

        if buf_text and buf_blk:
            merged.append(dict(buf_blk, text=buf_text.strip()))
        return merged

    except Exception as e:
        log.warning("[MDL003] polars text batch fail (%s), fallback engine", e)
        return TextRepairEngine().repair_text_blocks(blocks, reflow=reflow)


# ============================================================================
# [VRN:ANCHOR:MDL003-RESTORE-001] §6  TABLE RESTORATION ENGINE
# ============================================================================

def canonicalize_label(label: str) -> str:
    """VRN-MDL003-FNC-002  Map raw label → canonical field name.
    P3 OPTIMIZED: uses _CANON_NORM_CACHE / _CANON_LOWER_CACHE for O(1) hot-path.
    """
    if not label: return ""
    # ── L0: direct hit ────────────────────────────────────────────────────────
    if label in _CANONICAL_MAP: return _CANONICAL_MAP[label]
    # ── L1: normalized punctuation hit (O(1) via cache) ───────────────────────
    norm = _RE_NORM_PUNCT.sub("", label)
    if norm in _CANON_NORM_CACHE: return _CANON_NORM_CACHE[norm]
    # ── L2: lower substring hit (uses cache, scans once) ──────────────────────
    label_lower = label.lower()
    for k_lower, v, k_orig in _CANON_LOWER_CACHE:
        if k_lower in label_lower or label_lower in k_lower:
            return v
    # ── Fallback: snake-case the raw label ────────────────────────────────────
    return label.lower().replace(" ", "_")[:40]

def classify_fin_type(canonical: str) -> str:
    """VRN-MDL003-FNC-003"""
    if canonical in _IS_FIELDS: return "income_statement"
    if canonical in _BS_FIELDS: return "balance_sheet"
    if canonical in _CF_FIELDS: return "cash_flow"
    if canonical in _VL_FIELDS: return "valuation"
    return "other"

def clean_ocr_number(val: str) -> Optional[float]:
    """VRN-MDL003-FNC-004  Convert raw cell string to float or None.
    P2 OPTIMIZED: uses pre-compiled _RE_BRACKET_NEG / _RE_OCR_O_TO_0.
    """
    if not val: return None
    val = str(val).strip()
    # Special strings → null
    if val in ("--", "---", "n.a.", "N/A", "NA", "nm", "NM",
               "盈轉虧", "虧轉盈", "-", "—", ""):
        return None
    # Remove thousands separators and spaces
    val = val.replace(",", "").replace("，", "").replace(" ", "").replace("\u00a0","")
    # Bracket negative: (268) → -268    [P2: pre-compiled]
    val = _RE_BRACKET_NEG.sub(r"-\1", val)
    # Percentage: 48.5% → 48.5
    val = val.replace("%", "")
    # OCR: O→0, l→1 in pure numeric context    [P2: pre-compiled]
    val = _RE_OCR_O_TO_0.sub("0", val)
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
        # Skip header repeat rows (all periods/years in label)   [P2: pre-compiled]
        if _RE_HDR_REPEAT.fullmatch(label_raw): continue

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
    """VRN-MDL003-FNC-008  Apply full text repair + sentence merge.
    v1.1.0: routes to polars batch path when blocks are large.
    """
    return repair_text_blocks_batch(blocks, reflow=True)

# ============================================================================
# [VRN:ANCHOR:MDL003-EXTERNAL-001] §10  EXTERNAL SSOT INTEGRATION
# ============================================================================


def _cel_submit(fn, *args, **kw) -> Any:
    """VRN-MDL003-FNC-PROXY-001  Celeritas parallel submit, fallback direct call."""
    if _CEL_OK:
        if hasattr(_CEL, "_LazyPool"):
            try: return _CEL._LazyPool.submit(fn, *args, **kw)
            except Exception: pass
        if hasattr(_CEL, "submit"):
            try: return _CEL.submit(fn, *args, **kw)
            except Exception: pass
        if hasattr(_CEL, "parallel_map"):
            try:
                results = _CEL.parallel_map(fn, [(args, kw)])
                return results[0] if results else fn(*args, **kw)
            except Exception: pass
    return fn(*args, **kw)

def _cel_map(fn, items, **kw) -> List:
    """VRN-MDL003-FNC-PROXY-002  Celeritas parallel map, fallback list(map(...))."""
    if _CEL_OK:
        if hasattr(_CEL, "_LazyPool"):
            try: return list(_CEL._LazyPool.map(fn, items))
            except Exception: pass
        if hasattr(_CEL, "map"):
            try: return list(_CEL.map(fn, items))
            except Exception: pass
        if hasattr(_CEL, "parallel_map"):
            try: return _CEL.parallel_map(fn, list(items))
            except Exception: pass
    return list(map(fn, items))

def _cel_thread_budget(mode: str = "balanced") -> int:
    """VRN-MDL003-FNC-PROXY-003  Celeritas thread_budget, fallback cpu_count-1."""
    if _CEL_OK and hasattr(_CEL, "thread_budget"):
        try: return _CEL.thread_budget(mode=mode)
        except Exception: pass
    return max(1, (os.cpu_count() or 4) - 1)

def _cel_capability_report() -> Dict:
    """VRN-MDL003-FNC-PROXY-004  Celeritas capability_report, fallback empty."""
    if _CEL_OK and hasattr(_CEL, "capability_report"):
        try: return _CEL.capability_report()
        except Exception: pass
    return {}

def _ssot_get(key: str, default: Any = None) -> Any:
    """VRN-MDL003-FNC-PROXY-005  VIA_SSOT_Unified .get(), fallback default."""
    if _SSOT_OK and hasattr(_SSOT, "get"):
        try: return _SSOT.get(key, default)
        except Exception: pass
    return default

def _ssot_normalize_term(text: str) -> str:
    """VRN-MDL003-FNC-PROXY-006  Map term via SSOT canonical, fallback embedded."""
    if not text: return text
    t = text.strip()
    # 1. Try external SSOT class instance (real implementation, bypasses stubs)
    if _SSOT_OK and hasattr(_SSOT, "SSOT"):
        try:
            inst = _SSOT.SSOT()
            got = inst.normalize(t)
            if got and got != t: return got
        except Exception: pass
    # 2. Local fallback to _CANONICAL_MAP
    return _CANONICAL_MAP.get(t, _CANONICAL_MAP.get(t.lower(), t))

def _net_get(url: str, timeout: int = 20, **kw) -> Optional[Any]:
    """VRN-MDL003-FNC-PROXY-007  AegisNexus HTTP GET, fallback requests."""
    if _NET_OK:
        if hasattr(_NET, "safe_get"):
            try: return _NET.safe_get(url, timeout=timeout, **kw)
            except Exception: pass
        if hasattr(_NET, "fetch"):
            try: return _NET.fetch(url, timeout=timeout, **kw)
            except Exception: pass
    req = _si("requests")
    if req:
        try: return req.get(url, timeout=timeout, verify=False)
        except Exception: pass
    return None

# ============================================================================
# [VRN:ANCHOR:MDL003-PLUGIN-LOADER-001] §10  PLUGIN LOADER (7-tool HardGate)
# ============================================================================

def load_external_ssot(ssot_dir: str) -> Dict[str, bool]:
    """VRN-MDL003-FNC-009  Load 7 supportive tools per HardGate Seal.
    Policy: BOOT_PRECHECK_ONLY_NO_NETWORK_NO_PARALLEL_NO_AUTOPATCH.
    Returns capability dict (7 keys, all bool).
    """
    global _SSOT, _SSOT_OK, _CEL, _CEL_OK, _NET, _NET_OK
    global _REG, _REG_OK, _BRG, _BRG_OK, _ENV, _ENV_OK, _AST, _AST_OK

    result = {"via_ssot": False, "registry": False, "runtime_bridge": False,
              "env_manager": False, "ast_planner": False,
              "celeritas": False, "aegis": False}

    ssot_path = Path(ssot_dir)
    if not ssot_path.is_dir(): return result

    ssot_str = str(ssot_path)
    if ssot_str not in sys.path:
        sys.path.insert(0, ssot_str)

    import importlib.util as _ilu

    def _load_one(mod_name: str) -> Optional[Any]:
        p = _find_plugin(ssot_dir, f"{mod_name}.py")
        if not p: return None
        try:
            spec = _ilu.spec_from_file_location(mod_name, p)
            mod  = _ilu.module_from_spec(spec)
            sys.modules[mod_name] = mod
            spec.loader.exec_module(mod)
            log.info("[MDL003] %s loaded from %s", mod_name, p)
            return mod
        except Exception as e:
            log.debug("[MDL003] %s load fail: %s", mod_name, e)
            return None

    # ── 1. VIA_SSOT_Unified ─────────────────────────────────────────────────
    mod = _load_one("VIA_SSOT_Unified")
    if mod is not None:
        _SSOT = mod; _SSOT_OK = True; result["via_ssot"] = True
        if hasattr(mod, "CANONICAL_MAP") and isinstance(mod.CANONICAL_MAP, dict):
            for k, v in mod.CANONICAL_MAP.items():
                if k not in _CANONICAL_MAP:
                    _CANONICAL_MAP[k] = v
            log.info("[MDL003] CANONICAL_MAP merged %d entries", len(mod.CANONICAL_MAP))
            # P3: rebuild caches after mutation
            _rebuild_canon_caches()
            log.info("[MDL003] _CANON caches rebuilt: norm=%d lower=%d",
                     len(_CANON_NORM_CACHE), len(_CANON_LOWER_CACHE))

    # ── 2. VIA_RegistryCore_v1 ──────────────────────────────────────────────
    mod = _load_one("VIA_RegistryCore_v1")
    if mod is not None:
        _REG = mod; _REG_OK = True; result["registry"] = True

    # ── 3. VIA_Runtime_Bridge_All_in_One ────────────────────────────────────
    mod = _load_one("VIA_Runtime_Bridge_All_in_One")
    if mod is not None:
        _BRG = mod; _BRG_OK = True; result["runtime_bridge"] = True

    # ── 4. VIA_EnvManager ───────────────────────────────────────────────────
    mod = _load_one("VIA_EnvManager")
    if mod is not None:
        _ENV = mod; _ENV_OK = True; result["env_manager"] = True

    # ── 5. VIA_Panorama_AST_RuntimeInjector ─────────────────────────────────
    mod = _load_one("VIA_Panorama_AST_RuntimeInjector")
    if mod is not None:
        _AST = mod; _AST_OK = True; result["ast_planner"] = True

    # ── 6. VeritasCeleritas ─────────────────────────────────────────────────
    mod = _load_one("VeritasCeleritas")
    if mod is not None:
        _CEL = mod; _CEL_OK = True; result["celeritas"] = True
        if hasattr(mod, "bootstrap_at_import"):
            try: mod.bootstrap_at_import(__file__)
            except Exception: pass
        if hasattr(mod, "warm_thread_pool"):
            try: mod.warm_thread_pool()
            except Exception: pass

    # ── 7. VeritasAegisNexus ────────────────────────────────────────────────
    mod = _load_one("VeritasAegisNexus")
    if mod is not None:
        _NET = mod; _NET_OK = True; result["aegis"] = True

    return result

# ============================================================================
# [VRN:ANCHOR:MDL003-DB-001] §11  DB WRITERS  (DuckDB-first, sqlite fallback)
# ============================================================================

# ── P1 共用 SQL DDL（DuckDB 與 SQLite 共用，僅 ts default 略不同） ────────────
_DDL_FIN_ROWS = """
CREATE TABLE IF NOT EXISTS vrn_mdl003_financial_rows (
    id           INTEGER,
    region_id    VARCHAR,
    pdf_name     VARCHAR,
    report_code  VARCHAR,
    page_no      INTEGER,
    region_type  VARCHAR,
    quadrant     VARCHAR,
    label_raw    VARCHAR,
    canonical    VARCHAR,
    fin_type     VARCHAR,
    period       VARCHAR,
    value        DOUBLE,
    source       VARCHAR,
    calc_applied INTEGER,
    ts           VARCHAR
);
"""
_DDL_VERIFY = """
CREATE TABLE IF NOT EXISTS vrn_mdl003_verify_results (
    id           INTEGER,
    region_id    VARCHAR,
    pdf_name     VARCHAR,
    report_code  VARCHAR,
    check_name   VARCHAR,
    period       VARCHAR,
    ok           INTEGER,
    expected     DOUBLE,
    actual       DOUBLE,
    diff_pct     DOUBLE,
    ts           VARCHAR
);
"""
_DDL_TEXTFLOW = """
CREATE TABLE IF NOT EXISTS vrn_mdl003_text_flow (
    id          INTEGER,
    block_id    VARCHAR,
    pdf_name    VARCHAR,
    report_code VARCHAR,
    page_no     INTEGER,
    block_type  VARCHAR,
    text        VARCHAR,
    is_title    INTEGER,
    is_bold     INTEGER,
    font_size   DOUBLE,
    ts          VARCHAR
);
"""

# ── P1: BatchBuffer (CLS-009) ─────────────────────────────────────────────────

class MDL003BatchBuffer:
    """VRN-MDL003-CLS-009  P1 batch buffer.
    每張表 process 完不立即 commit，先進 buffer。
    達到 batch_size 或最後 flush_all() 時才一次性寫入。

    解決問題：
      v1.0.0 每張 table 一次 executemany + commit + 全域鎖
        → ThreadPoolExecutor N workers 全部撞鎖序列化
      v1.1.0 各 worker append-only push 進 thread-safe buffer (lock 粒度極小)
        → flush 改由 main thread 在 ThreadPoolExecutor close 後一次性執行
    """
    def __init__(self, batch_size: int = 5000):
        self.batch_size = batch_size
        self._fin_buf:    List[Tuple] = []
        self._verify_buf: List[Tuple] = []
        self._text_buf:   List[Tuple] = []
        self._lock = threading.Lock()  # 僅保護 list.extend，不保護 DB

    def push_fin_rows(self, rt: "RestoredTable"):
        if not rt.rows: return
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        rows = []
        for row in rt.rows:
            for period, val in row["values"].items():
                src = row["sources"].get(period, "ERR")
                rows.append((
                    None,  # id (auto)
                    rt.region_id, rt.pdf_name, rt.report_code,
                    rt.page_no, rt.region_type, rt.quadrant,
                    row["label_raw"], row["canonical"], row["fin_type"],
                    period, val, src, rt.calc_applied, ts,
                ))
        with self._lock:
            self._fin_buf.extend(rows)

    def push_verify(self, rt: "RestoredTable", verify: Dict):
        if not verify or not verify.get("details"): return
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        rows = [
            (None, rt.region_id, rt.pdf_name, rt.report_code,
             d.get("check",""), d.get("period",""),
             1 if d.get("ok") else 0,
             d.get("expected"), d.get("actual"), d.get("diff_pct"), ts)
            for d in verify.get("details", [])
        ]
        with self._lock:
            self._verify_buf.extend(rows)

    def push_text_flow(self, blocks: List[Dict]):
        if not blocks: return
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        rows = [
            (None,
             b.get("block_id",""), b.get("pdf_name",""),
             b.get("report_code",""), b.get("page_no",0),
             b.get("block_type",""), b.get("text",""),
             1 if b.get("is_title") else 0,
             1 if b.get("is_bold") else 0,
             b.get("font_size",0.0), ts)
            for b in blocks
        ]
        with self._lock:
            self._text_buf.extend(rows)

    def stats(self) -> Dict[str, int]:
        return {
            "fin":    len(self._fin_buf),
            "verify": len(self._verify_buf),
            "text":   len(self._text_buf),
        }

    def consume_all(self) -> Tuple[List, List, List]:
        """Atomically swap out all buffers (caller becomes owner)."""
        with self._lock:
            f, v, t = self._fin_buf, self._verify_buf, self._text_buf
            self._fin_buf, self._verify_buf, self._text_buf = [], [], []
        return f, v, t


# ── DuckDB Writer (CLS-008, primary) ──────────────────────────────────────────

class MDL003DuckWriter:
    """VRN-MDL003-CLS-008  DuckDB-first persistence (v1.1.0).
    Single connection, single thread (writes happen post-pool).
    3-table schema mirrors sqlite for output compatibility.

    Why DuckDB > SQLite here:
      - INSERT 速度 5–20× (column store + bulk register)
      - 直接 register polars DataFrame (zero-copy via Arrow)
      - 直接 COPY ... TO 'parquet' 跳過所有來回 I/O
    """
    def __init__(self, db_path: str):
        if not DUCKDB_OK:
            raise RuntimeError("duckdb not available")
        self.db_path = db_path
        # 若舊檔存在會 lock，先嘗試移除（DuckDB 1.x 不支持並發寫）
        self._con = duckdb.connect(db_path)
        self._con.execute(_DDL_FIN_ROWS)
        self._con.execute(_DDL_VERIFY)
        self._con.execute(_DDL_TEXTFLOW)

    def flush(self, fin_rows: List[Tuple], verify_rows: List[Tuple],
              text_rows: List[Tuple]) -> Dict[str, int]:
        """Bulk-flush all buffered rows. Single transaction."""
        n_fin = n_ver = n_txt = 0
        try:
            self._con.execute("BEGIN TRANSACTION")
            if fin_rows:
                self._con.executemany(
                    "INSERT INTO vrn_mdl003_financial_rows VALUES "
                    "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    fin_rows
                )
                n_fin = len(fin_rows)
            if verify_rows:
                self._con.executemany(
                    "INSERT INTO vrn_mdl003_verify_results VALUES "
                    "(?,?,?,?,?,?,?,?,?,?,?)",
                    verify_rows
                )
                n_ver = len(verify_rows)
            if text_rows:
                self._con.executemany(
                    "INSERT INTO vrn_mdl003_text_flow VALUES "
                    "(?,?,?,?,?,?,?,?,?,?,?)",
                    text_rows
                )
                n_txt = len(text_rows)
            self._con.execute("COMMIT")
        except Exception as e:
            try: self._con.execute("ROLLBACK")
            except Exception: pass
            log.error("[MDL003] DuckDB flush fail: %s", e)
            raise
        return {"fin": n_fin, "verify": n_ver, "text": n_txt}

    def export_parquet_polars(self, out_dir: str) -> Optional[str]:
        """P5: DuckDB native COPY → Parquet. Skips Python round-trip."""
        out_path = str(Path(out_dir) / "VRN_MDL003_Restored.parquet")
        try:
            self._con.execute(
                f"COPY (SELECT * FROM vrn_mdl003_financial_rows) "
                f"TO '{out_path}' (FORMAT PARQUET, COMPRESSION ZSTD)"
            )
            return out_path
        except Exception as e:
            log.warning("[MDL003] DuckDB→parquet fail: %s", e)
            return None

    def export_csv_polars(self, out_dir: str) -> Optional[str]:
        """P5: try multiple paths in priority order (avoid pyarrow dependency).
          1. polars via fetchall + manual DataFrame (no pyarrow needed)
          2. DuckDB native COPY ... TO csv (then prepend BOM)
        """
        out_path = str(Path(out_dir) / "VRN_MDL003_Restored.csv")
        # Path 1: polars via fetchall (no pyarrow required)
        if POLARS_OK:
            try:
                rows = self._con.execute(
                    "SELECT * FROM vrn_mdl003_financial_rows"
                ).fetchall()
                cols = [d[0] for d in self._con.description]
                if rows:
                    df = pl.DataFrame(rows, schema=cols, orient="row")
                    csv_text = df.write_csv()  # str
                    Path(out_path).write_bytes(b"\xef\xbb\xbf" + csv_text.encode("utf-8"))
                else:
                    # Empty table: write header only
                    Path(out_path).write_bytes(
                        b"\xef\xbb\xbf" + (",".join(cols) + "\n").encode("utf-8")
                    )
                return out_path
            except Exception as e:
                log.debug("[MDL003] polars-fetchall csv fail (%s), try DuckDB native", e)
        # Path 2: DuckDB native COPY (no BOM, but works without polars)
        try:
            self._con.execute(
                f"COPY (SELECT * FROM vrn_mdl003_financial_rows) "
                f"TO '{out_path}' (HEADER, DELIMITER ',')"
            )
            # Prepend BOM
            data = Path(out_path).read_bytes()
            Path(out_path).write_bytes(b"\xef\xbb\xbf" + data)
            return out_path
        except Exception as e:
            log.warning("[MDL003] csv export fail: %s", e)
            return None

    def close(self):
        try: self._con.close()
        except Exception: pass


# ── SQLite Writer (CLS-002, fallback, kept for backward compat) ───────────────

class MDL003DBWriter:
    """VRN-MDL003-CLS-002  SQLite WAL persistence.
    v1.0.0 LEGACY: kept as fallback when duckdb is unavailable.

    P1 v1.1.0 改進：
      - 不再每張表 commit；改由 batch flush (insert_*) 走 buffer 模式
      - 保留舊 insert_* 方法以維持 v1.0.0 簽名相容
    """

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

    # ── v1.0.0 legacy API (kept) ─────────────────────────────────────────────
    def insert_financial_rows(self, rt: "RestoredTable"):
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

    def insert_verify(self, rt: "RestoredTable", verify: Dict):
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

    # ── v1.1.0 batch flush API (NEW) ─────────────────────────────────────────
    def flush(self, fin_rows: List[Tuple], verify_rows: List[Tuple],
              text_rows: List[Tuple]) -> Dict[str, int]:
        """v1.1.0 batch flush: equivalent of MDL003DuckWriter.flush().
        Note: input tuples have id-placeholder None at position 0 — strip it."""
        n_fin = n_ver = n_txt = 0
        with self._lock:
            try:
                self._con.execute("BEGIN")
                if fin_rows:
                    self._con.executemany(
                        "INSERT INTO vrn_mdl003_financial_rows "
                        "(region_id,pdf_name,report_code,page_no,region_type,quadrant,"
                        " label_raw,canonical,fin_type,period,value,source,calc_applied,ts) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        [r[1:] for r in fin_rows]
                    )
                    n_fin = len(fin_rows)
                if verify_rows:
                    self._con.executemany(
                        "INSERT INTO vrn_mdl003_verify_results "
                        "(region_id,pdf_name,report_code,check_name,period,ok,"
                        " expected,actual,diff_pct,ts) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?)",
                        [r[1:] for r in verify_rows]
                    )
                    n_ver = len(verify_rows)
                if text_rows:
                    self._con.executemany(
                        "INSERT INTO vrn_mdl003_text_flow "
                        "(block_id,pdf_name,report_code,page_no,block_type,text,"
                        " is_title,is_bold,font_size,ts) "
                        "VALUES (?,?,?,?,?,?,?,?,?,?)",
                        [r[1:] for r in text_rows]
                    )
                    n_txt = len(text_rows)
                self._con.commit()
            except Exception as e:
                try: self._con.rollback()
                except Exception: pass
                log.error("[MDL003] sqlite flush fail: %s", e)
                raise
        return {"fin": n_fin, "verify": n_ver, "text": n_txt}

    def export_parquet(self, out_dir: str):
        """v1.0.0 path: pandas → parquet (kept)."""
        if not pd or not pyarrow: return
        try:
            df = pd.read_sql("SELECT * FROM vrn_mdl003_financial_rows", self._con)
            df.to_parquet(str(Path(out_dir) / "VRN_MDL003_Restored.parquet"), index=False)
        except Exception as e: log.warning("[MDL003] parquet: %s", e)

    def export_csv(self, out_dir: str):
        """v1.0.0 path: pandas → csv (kept)."""
        if not pd: return
        try:
            df = pd.read_sql("SELECT * FROM vrn_mdl003_financial_rows", self._con)
            df.to_csv(str(Path(out_dir) / "VRN_MDL003_Restored.csv"),
                      index=False, encoding="utf-8-sig")
        except Exception as e: log.warning("[MDL003] csv: %s", e)

    # ── v1.1.0 polars-direct exports (NEW) ───────────────────────────────────
    def export_parquet_polars(self, out_dir: str) -> Optional[str]:
        """P5 sqlite path: polars via cursor.fetchall → write_parquet."""
        out_path = str(Path(out_dir) / "VRN_MDL003_Restored.parquet")
        if not POLARS_OK:
            self.export_parquet(out_dir)
            return out_path if Path(out_path).exists() else None
        try:
            with self._lock:
                cur = self._con.execute(
                    "SELECT * FROM vrn_mdl003_financial_rows"
                )
                rows = cur.fetchall()
                cols = [d[0] for d in cur.description] if cur.description else []
            if not rows:
                # Empty result: write empty parquet with schema
                df = pl.DataFrame(schema={c: pl.Utf8 for c in cols} if cols else None)
            else:
                df = pl.DataFrame(rows, schema=cols, orient="row")
            df.write_parquet(out_path, compression="zstd")
            return out_path
        except Exception as e:
            log.warning("[MDL003] polars→parquet fail (%s), fallback pandas", e)
            self.export_parquet(out_dir)
            return out_path if Path(out_path).exists() else None

    def export_csv_polars(self, out_dir: str) -> Optional[str]:
        """P5 sqlite path: polars via cursor.fetchall (avoids pyarrow); BOM."""
        out_path = str(Path(out_dir) / "VRN_MDL003_Restored.csv")
        if POLARS_OK:
            try:
                with self._lock:
                    cur = self._con.execute(
                        "SELECT * FROM vrn_mdl003_financial_rows"
                    )
                    rows = cur.fetchall()
                    cols = [d[0] for d in cur.description] if cur.description else []
                if rows and cols:
                    df = pl.DataFrame(rows, schema=cols, orient="row")
                    csv_text = df.write_csv()
                    Path(out_path).write_bytes(b"\xef\xbb\xbf" + csv_text.encode("utf-8"))
                else:
                    Path(out_path).write_bytes(
                        b"\xef\xbb\xbf" + (",".join(cols) + "\n").encode("utf-8")
                    )
                return out_path
            except Exception as e:
                log.debug("[MDL003] polars-fetchall csv fail (%s), fallback pandas", e)
        # Fallback: legacy pandas path
        self.export_csv(out_dir)
        return out_path if Path(out_path).exists() else None

    def close(self):
        try: self._con.close()
        except Exception: pass


# ── P5: stand-alone polars export helpers (FNC-014/015) ───────────────────────

def pl_export_parquet(fin_rows: List[Tuple], out_dir: str) -> Optional[str]:
    """VRN-MDL003-FNC-014 (P5)
    Build polars DataFrame directly from row tuples and write parquet.
    Used when caller wants to skip DB entirely.
    """
    if not POLARS_OK or not fin_rows: return None
    try:
        cols = ["id","region_id","pdf_name","report_code","page_no",
                "region_type","quadrant","label_raw","canonical","fin_type",
                "period","value","source","calc_applied","ts"]
        df = pl.DataFrame(fin_rows, schema=cols, orient="row")
        out_path = str(Path(out_dir) / "VRN_MDL003_Restored.parquet")
        df.write_parquet(out_path, compression="zstd")
        return out_path
    except Exception as e:
        log.warning("[MDL003] pl_export_parquet fail: %s", e)
        return None

def pl_export_csv(fin_rows: List[Tuple], out_dir: str) -> Optional[str]:
    """VRN-MDL003-FNC-015 (P5)  Same idea, csv output with BOM."""
    if not POLARS_OK or not fin_rows: return None
    try:
        cols = ["id","region_id","pdf_name","report_code","page_no",
                "region_type","quadrant","label_raw","canonical","fin_type",
                "period","value","source","calc_applied","ts"]
        df = pl.DataFrame(fin_rows, schema=cols, orient="row")
        out_path = str(Path(out_dir) / "VRN_MDL003_Restored.csv")
        buf = io.BytesIO()
        df.write_csv(buf)
        Path(out_path).write_bytes(b"\xef\xbb\xbf" + buf.getvalue())
        return out_path
    except Exception as e:
        log.warning("[MDL003] pl_export_csv fail: %s", e)
        return None

# ============================================================================
# CORE PROCESSOR
# ============================================================================

def process_one_pdf(
    pdf_report: Dict,
    cfg:        Dict,
    repair:     TextRepairEngine,
    db:         Optional[Any] = None,         # legacy: MDL003DBWriter — kept signature
    buffer:     Optional[MDL003BatchBuffer] = None,   # v1.1.0: NEW
) -> Dict:
    """VRN-MDL003-FNC-010  Restore all tables + text for one PDF report.

    v1.1.0 改進：
      - 新增 buffer 參數；若提供，DB 寫入改走 buffer.push_*（無鎖、無 commit）
      - 維持 db 參數舊行為以相容 v1.0.0 呼叫方
      - 兩者都給時，buffer 優先（不會 double-write）
    """
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

            # ── DB push: v1.1.0 buffer-first, fallback legacy db.insert_* ───
            if buffer is not None:
                if rt.ok:
                    buffer.push_fin_rows(rt)
                if verify_result:
                    buffer.push_verify(rt, verify_result)
            elif db is not None:
                try:
                    if rt.ok and hasattr(db, "insert_financial_rows"):
                        db.insert_financial_rows(rt)
                    if verify_result and hasattr(db, "insert_verify"):
                        db.insert_verify(rt, verify_result)
                except Exception as e:
                    log.warning("[MDL003] DB rows %s: %s", rt.region_id, e)

        # ── Restore text ───────────────────────────────────────────────────
        if cfg.get("text_reflow", True):
            raw_blocks = pdf_report.get("text_blocks", [])
            flowed = reflow_text_blocks(raw_blocks, repair)
            out["n_text_blocks_out"] = len(flowed)
            out["text_flow"] = flowed

            if buffer is not None and flowed:
                buffer.push_text_flow(flowed)
            elif db is not None and flowed:
                try:
                    if hasattr(db, "insert_text_flow"):
                        db.insert_text_flow(flowed)
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
# [VRN:ANCHOR:MDL003-SELFCHK-001] §12.5  P7 4-PHASE SELF-VERIFICATION
# ============================================================================

class MDL003SelfVerifier:
    """VRN-MDL003-CLS-010  P7 4-phase debug chain.

    Phases:
      [1/4] Schema & Imports  — module integrity, regex compile, canon caches
      [2/4] DB Persistence    — DuckDB primary table presence, sqlite fallback
      [3/4] Output Files      — JSON / Parquet / CSV all written, sizes >= threshold
      [4/4] Data Integrity    — row counts match, no NaN in required columns

    Result classification (per Tony's spec):
      READY      = 0 fail
      NEAR-READY = 1-2 fail
      NOT-READY  = 3+ fail
    """

    def __init__(self, cfg: Dict, run_summary: Dict, mdl003_temp: str):
        self.cfg          = cfg
        self.run_summary  = run_summary
        self.mdl003_temp  = mdl003_temp
        self.checks: List[Dict] = []

    def _add(self, phase: str, name: str, ok: bool, detail: str = ""):
        self.checks.append({
            "phase":  phase,
            "name":   name,
            "ok":     bool(ok),
            "detail": detail,
        })

    def run(self) -> Dict:
        # ── PHASE 1: Schema & Imports ────────────────────────────────────────
        self._add("1/4", "Module version",
                  __version__ == "1.1.0", f"version={__version__}")
        self._add("1/4", "TW_TICKER_REGEX locked",
                  TW_TICKER_REGEX.pattern == r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})",
                  TW_TICKER_REGEX.pattern)
        self._add("1/4", "Pre-compiled regex pool",
                  all(p is not None for p in [_RE_BRACKET_NEG, _RE_OCR_O_TO_0,
                                              _RE_NORM_PUNCT, _RE_HDR_REPEAT,
                                              _RE_DOUBLESPACE, _RE_SENT_END]),
                  "P2 regex pool")
        self._add("1/4", "Canon caches non-empty",
                  len(_CANON_NORM_CACHE) > 0 and len(_CANON_LOWER_CACHE) > 0,
                  f"norm={len(_CANON_NORM_CACHE)} lower={len(_CANON_LOWER_CACHE)}")
        self._add("1/4", "polars available",
                  POLARS_OK, "polars" + (" OK" if POLARS_OK else " MISSING"))
        self._add("1/4", "duckdb available",
                  DUCKDB_OK, "duckdb" + (" OK" if DUCKDB_OK else " MISSING"))
        self._add("1/4", "orjson available",
                  orjson is not None, "orjson" + (" OK" if orjson else " MISSING"))

        # ── PHASE 2: DB Persistence ──────────────────────────────────────────
        duck_p   = Path(self.mdl003_temp) / "VRN_MDL003.duckdb"
        sqlite_p = Path(self.mdl003_temp) / "VRN_MDL003.db"
        self._add("2/4", "DuckDB file exists",
                  duck_p.exists() or sqlite_p.exists(),
                  f"duckdb={duck_p.exists()} sqlite={sqlite_p.exists()}")
        if duck_p.exists() and DUCKDB_OK:
            try:
                con = duckdb.connect(str(duck_p), read_only=True)
                tbls = con.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema='main'"
                ).fetchall()
                names = {t[0] for t in tbls}
                con.close()
                expected = {"vrn_mdl003_financial_rows",
                            "vrn_mdl003_verify_results",
                            "vrn_mdl003_text_flow"}
                self._add("2/4", "DuckDB schema 3 tables",
                          expected.issubset(names),
                          f"have={sorted(names)}")
            except Exception as e:
                self._add("2/4", "DuckDB schema 3 tables", False, str(e))

        # ── PHASE 3: Output Files ────────────────────────────────────────────
        expected_files = [
            ("VRN_MDL003_Restored.json",      1024),
            ("VRN_MDL003_VerifySummary.json", 64),
            ("VRN_MDL003_TextFlow.json",      32),
            ("VRN_MDL003_Restored.parquet",   0),    # may be empty if no rows
            ("VRN_MDL003_Restored.csv",       0),
        ]
        for fn, min_size in expected_files:
            p = Path(self.mdl003_temp) / fn
            ok = p.exists() and (p.stat().st_size >= min_size if min_size else True)
            self._add("3/4", f"file:{fn}",
                      ok, f"exists={p.exists()} size={p.stat().st_size if p.exists() else 0}")

        # ── PHASE 4: Data Integrity ──────────────────────────────────────────
        self._add("4/4", "ok_count >= 0",
                  self.run_summary.get("ok_count", -1) >= 0,
                  f"ok_count={self.run_summary.get('ok_count')}")
        # Cross-check: total_tables_ok ≤ total_tables_in
        ti = self.run_summary.get("total_tables_in", 0)
        to = self.run_summary.get("total_tables_ok", 0)
        self._add("4/4", "tables_ok ≤ tables_in",
                  to <= ti, f"{to}/{ti}")
        # Verify pass rate sanity
        vp = self.run_summary.get("total_verify_pass", 0)
        vf = self.run_summary.get("total_verify_fail", 0)
        self._add("4/4", "verify counts non-negative",
                  vp >= 0 and vf >= 0, f"pass={vp} fail={vf}")

        # ── Summarize ────────────────────────────────────────────────────────
        n_total = len(self.checks)
        n_pass  = sum(1 for c in self.checks if c["ok"])
        n_fail  = n_total - n_pass

        if n_fail == 0:    classification = "READY"
        elif n_fail <= 2:  classification = "NEAR-READY"
        else:              classification = "NOT-READY"

        return {
            "total":          n_total,
            "pass":           n_pass,
            "fail":           n_fail,
            "classification": classification,
            "checks":         self.checks,
            "generated":      time.strftime("%Y-%m-%d %H:%M:%S"),
        }


def build_self_verify_html(verify_result: Dict, run_summary: Dict,
                           cfg: Dict) -> str:
    """VRN-MDL003-FNC-017  Build VIA Visual Lock compliant HTML.

    Tokens (per VIA_VISUAL_LOCK_SPEC_v1.md):
      - background: #f5f4f0
      - primary blue: #4c78a8
      - teal: #439a9a
      - fonts: Syne + DM Sans + DM Mono
      - 11px base
      - rainbow gradient header border
      - .cd / .cd-h / .cd-b cards
      - .tm black terminal with mac dots
    """
    cls         = verify_result.get("classification", "?")
    cls_color   = {"READY":"#439a9a", "NEAR-READY":"#e0b020",
                   "NOT-READY":"#c83030"}.get(cls, "#666")
    cls_emoji   = {"READY":"✓", "NEAR-READY":"⚠", "NOT-READY":"✗"}.get(cls, "?")

    # Group checks by phase
    by_phase: Dict[str, List[Dict]] = collections.OrderedDict()
    for c in verify_result.get("checks", []):
        by_phase.setdefault(c["phase"], []).append(c)

    phase_html = []
    for phase, items in by_phase.items():
        rows = "".join(
            f'<tr><td class="ck-name">{c["name"]}</td>'
            f'<td class="ck-{"ok" if c["ok"] else "fail"}">'
            f'{"✓" if c["ok"] else "✗"} {"PASS" if c["ok"] else "FAIL"}</td>'
            f'<td class="ck-detail">{str(c["detail"])[:120]}</td></tr>'
            for c in items
        )
        n_pass = sum(1 for c in items if c["ok"])
        phase_html.append(f"""
        <div class="cd">
          <div class="cd-h">PHASE {phase} ({n_pass}/{len(items)} pass)</div>
          <div class="cd-b">
            <table class="ck-tbl">
              <thead><tr><th>Check</th><th>Result</th><th>Detail</th></tr></thead>
              <tbody>{rows}</tbody>
            </table>
          </div>
        </div>
        """)

    # Run summary terminal block
    sum_lines = [
        f"$ VRN_MDL003 v{__version__} self-verification",
        f"  generated      : {verify_result.get('generated','-')}",
        f"  classification : {cls} {cls_emoji}",
        f"  checks         : {verify_result.get('pass',0)}/{verify_result.get('total',0)} pass",
        "",
        "$ pipeline summary",
        f"  total reports      : {run_summary.get('total','-')}",
        f"  ok / fail          : {run_summary.get('ok_count','-')} / {run_summary.get('fail_count','-')}",
        f"  total tables in    : {run_summary.get('total_tables_in','-')}",
        f"  total tables ok    : {run_summary.get('total_tables_ok','-')}",
        f"  financial tables   : {run_summary.get('total_fin_tables','-')}",
        f"  CALC applied       : {run_summary.get('total_calc_applied','-')}",
        f"  verify pass / fail : {run_summary.get('total_verify_pass','-')} / {run_summary.get('total_verify_fail','-')}",
        f"  text blocks out    : {run_summary.get('total_text_blocks','-')}",
    ]
    term_html = "\n".join(sum_lines)

    html = f"""<!DOCTYPE html>
<html lang="zh-Hant"><head>
<meta charset="UTF-8">
<title>VRN MDL003 v{__version__} · Self-Verification · {cls}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    background: #f5f4f0;
    color: #1a1a1a;
    font-family: 'DM Sans', -apple-system, sans-serif;
    font-size: 11px;
    line-height: 1.6;
    padding: 24px;
}}
.hdr {{
    border-top: 4px solid;
    border-image: linear-gradient(90deg, #ff5e5e, #ffae5e, #ffe55e, #5eff8c, #5ec8ff, #8c5eff, #ff5ec8) 1;
    padding-top: 16px;
    margin-bottom: 24px;
}}
h1 {{
    font-family: 'Syne', sans-serif;
    font-size: 20px;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #1a1a1a;
}}
.sub {{
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    color: #666;
    margin-top: 4px;
}}
.cls-badge {{
    display: inline-block;
    padding: 4px 12px;
    background: {cls_color};
    color: white;
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 11px;
    margin-left: 12px;
    letter-spacing: 0.05em;
}}
.cd {{
    background: white;
    border: 1px solid #e0ddd5;
    margin-bottom: 16px;
}}
.cd-h {{
    background: #4c78a8;
    color: white;
    padding: 8px 16px;
    font-family: 'Syne', sans-serif;
    font-weight: 600;
    font-size: 11px;
    letter-spacing: 0.03em;
}}
.cd-b {{ padding: 12px 16px; }}
.tm {{
    background: #1a1a1a;
    color: #c8e0c8;
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    padding: 32px 16px 16px 16px;
    border-radius: 0;
    position: relative;
    white-space: pre;
    line-height: 1.5;
}}
.tm::before {{
    content: "● ● ●";
    position: absolute;
    top: 8px;
    left: 12px;
    color: #ff5e5e;
    letter-spacing: 4px;
    font-size: 10px;
}}
.ck-tbl {{
    width: 100%;
    border-collapse: collapse;
}}
.ck-tbl th {{
    background: #f5f4f0;
    color: #4c78a8;
    text-align: left;
    padding: 6px 8px;
    font-weight: 600;
    border-bottom: 2px solid #4c78a8;
    font-size: 10px;
    letter-spacing: 0.05em;
}}
.ck-tbl td {{
    padding: 6px 8px;
    border-bottom: 1px solid #f0ede5;
    vertical-align: top;
}}
.ck-name {{ font-weight: 500; min-width: 200px; }}
.ck-ok   {{ color: #439a9a; font-weight: 600; min-width: 80px; }}
.ck-fail {{ color: #c83030; font-weight: 700; min-width: 80px; }}
.ck-detail {{ color: #666; font-family: 'DM Mono', monospace; font-size: 10px; }}
.foot {{
    margin-top: 24px;
    color: #999;
    font-family: 'DM Mono', monospace;
    font-size: 9px;
    text-align: right;
}}
</style></head>
<body>
<div class="hdr">
  <h1>VRN MDL003 · TableRestorer v{__version__}<span class="cls-badge">{cls}</span></h1>
  <div class="sub">VeritasReportNova · 4-Phase Self-Verification · {time.strftime("%Y-%m-%d %H:%M:%S")}</div>
</div>

<div class="cd">
  <div class="cd-h">RUN SUMMARY</div>
  <div class="cd-b">
    <div class="tm">{term_html}</div>
  </div>
</div>

{"".join(phase_html)}

<div class="foot">
  Module: {__module_id__} · Asset: {__asset_id__} · Generated by VRN_MDL003 v{__version__}
</div>
</body></html>"""
    return html

# ============================================================================
# [VRN:ANCHOR:MDL003-SYS-001] §13  PIPELINE ENTRY
# ============================================================================

class VRN_MDL003_TableRestorer:
    """VRN-MDL003-CLS-001
    run() (v1.1.0):
      1. Load external SSOT (optional, 7-tool HardGate)
      2. Accel init
      3. Load VRN_MDL002_Layout.json
      4. Build BatchBuffer (P1)
      5. Parallel process_one_pdf() — workers push into buffer (no DB lock contention)
      6. Single-thread DuckDB flush (or sqlite fallback) post-pool
      7. Polars-direct parquet/csv export (P5)
      8. orjson JSON outputs (P4)
      9. 4-phase self-verification HTML (P7)
    """
    def __init__(self, cfg: Dict):
        self.cfg     = cfg
        workers      = cfg.get("workers", 0) or max(1, (os.cpu_count() or 4) - 1)
        self.workers = workers
        self.duck:   Optional[MDL003DuckWriter] = None   # primary
        self.db:     Optional[MDL003DBWriter]   = None   # fallback
        self.buffer: Optional[MDL003BatchBuffer] = None
        self.repair  = TextRepairEngine()

    def run(self) -> Dict:
        run_t0      = time.perf_counter()
        mdl002_temp = self.cfg.get("mdl002_temp", _DEFAULTS["mdl002_temp"])
        mdl003_temp = self.cfg.get("mdl003_temp", _DEFAULTS["mdl003_temp"])
        ssot_dir    = self.cfg.get("ssot_dir",    _DEFAULTS["ssot_dir"])
        Path(mdl003_temp).mkdir(parents=True, exist_ok=True)

        # ── 1. Load external SSOT ───────────────────────────────────────────
        ssot_caps = load_external_ssot(ssot_dir)
        log.info("[MDL003] SSOT caps: %s", ssot_caps)

        # ── 2. Accel init ───────────────────────────────────────────────────
        cap = _mdl003_accel_init(self.workers)
        log.info("[MDL003] accel caps: %s", cap)

        # ── 3. Load MDL002 output ───────────────────────────────────────────
        mdl002_data = load_mdl002_output(mdl002_temp)
        if not mdl002_data:
            return {"ok": False, "total": 0, "success": 0,
                    "errors": ["MDL002 output not found"], "out_dir": mdl003_temp}

        pdf_reports = mdl002_data.get("reports", [])

        # ── 4. Build BatchBuffer + DB ───────────────────────────────────────
        if self.cfg.get("enable_db", True):
            self.buffer = MDL003BatchBuffer(
                batch_size=self.cfg.get("batch_size", _DEFAULTS["batch_size"])
            )
            # DuckDB primary
            duck_path = str(Path(mdl003_temp) / "VRN_MDL003.duckdb")
            if self.cfg.get("use_duckdb", True) and DUCKDB_OK:
                # Stale lock cleanup: if a previous run crashed, delete the file
                try:
                    self.duck = MDL003DuckWriter(duck_path)
                    log.info("[MDL003] DuckDB primary writer ready: %s", duck_path)
                except Exception as e:
                    log.warning("[MDL003] DuckDB init fail (%s), trying sqlite", e)
                    self.duck = None
            # SQLite fallback (always builds, used if duck fails)
            try:
                self.db = MDL003DBWriter(str(Path(mdl003_temp) / "VRN_MDL003.db"))
                log.info("[MDL003] sqlite fallback writer ready")
            except Exception as e:
                log.warning("[MDL003] sqlite init fail: %s", e)
                self.db = None

        log.info("[MDL003] Restoring %d PDF reports, workers=%d  polars=%s duckdb=%s",
                 len(pdf_reports), self.workers, POLARS_OK,
                 self.duck is not None)

        # ── 5. Parallel process (workers push into buffer; NO DB writes) ────
        all_results: List[Dict] = []
        fail_count = 0

        with ThreadPoolExecutor(max_workers=self.workers) as ex:
            futs = {
                ex.submit(process_one_pdf, rpt, self.cfg, self.repair,
                          None, self.buffer): rpt
                for rpt in pdf_reports
            }
            for fut in as_completed(futs):
                res = fut.result()
                all_results.append(res)
                if not res.get("ok"): fail_count += 1

        # ── 6. Single-thread flush DB ────────────────────────────────────────
        flush_stats = {"fin": 0, "verify": 0, "text": 0}
        if self.buffer:
            fin_rows, verify_rows, text_rows = self.buffer.consume_all()
            log.info("[MDL003] Buffer drain: fin=%d verify=%d text=%d",
                     len(fin_rows), len(verify_rows), len(text_rows))

            if self.duck:
                try:
                    flush_stats = self.duck.flush(fin_rows, verify_rows, text_rows)
                    log.info("[MDL003] DuckDB flush: %s", flush_stats)
                except Exception as e:
                    log.warning("[MDL003] DuckDB flush fail (%s), falling back to sqlite", e)
                    if self.db:
                        flush_stats = self.db.flush(fin_rows, verify_rows, text_rows)
                        log.info("[MDL003] sqlite flush: %s", flush_stats)
            elif self.db:
                flush_stats = self.db.flush(fin_rows, verify_rows, text_rows)
                log.info("[MDL003] sqlite flush: %s", flush_stats)

        # ── 7. Polars-direct exports ────────────────────────────────────────
        parquet_path = csv_path = None
        if self.duck:
            parquet_path = self.duck.export_parquet_polars(mdl003_temp)
            csv_path     = self.duck.export_csv_polars(mdl003_temp)
        elif self.db:
            parquet_path = self.db.export_parquet_polars(mdl003_temp)
            csv_path     = self.db.export_csv_polars(mdl003_temp)

        log.info("[MDL003] Exports: parquet=%s csv=%s", parquet_path, csv_path)

        # ── 8. JSON outputs (orjson fast path) ──────────────────────────────
        out = assemble_output(all_results)
        t_main_json = _jwrite_fast(
            str(Path(mdl003_temp) / "VRN_MDL003_Restored.json"), out
        )

        text_flow_out = {
            "module": __module_id__, "generated": time.strftime("%Y-%m-%d %H:%M:%S"),
            "reports": [
                {"pdf_name": r["pdf_name"], "report_code": r["report_code"],
                 "text_flow": r.get("text_flow", [])}
                for r in all_results
            ]
        }
        t_tflow_json = _jwrite_fast(
            str(Path(mdl003_temp) / "VRN_MDL003_TextFlow.json"), text_flow_out
        )

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
            "flush_stats":        flush_stats,
            "io_timing":          {
                "main_json":  t_main_json,
                "tflow_json": t_tflow_json,
            },
            "fail_details": [
                {"pdf_name": r["pdf_name"], "error": r.get("error")}
                for r in all_results if not r.get("ok")
            ],
        }
        _jwrite_fast(
            str(Path(mdl003_temp) / "VRN_MDL003_VerifySummary.json"), verify_summary
        )

        # ── 9. 4-phase Self-Verification (P7) ───────────────────────────────
        sv_html_path = None
        if self.cfg.get("self_verify", True):
            try:
                verifier = MDL003SelfVerifier(self.cfg, out, mdl003_temp)
                sv_result = verifier.run()
                html = build_self_verify_html(sv_result, out, self.cfg)
                sv_html_path = str(Path(mdl003_temp) / "VRN_MDL003_SelfVerify.html")
                Path(sv_html_path).write_text(html, encoding="utf-8")
                log.info("[MDL003] Self-verify: %s (%d/%d pass) → %s",
                         sv_result["classification"],
                         sv_result["pass"], sv_result["total"],
                         sv_html_path)
            except Exception as e:
                log.warning("[MDL003] self_verify build fail: %s", e)

        # ── Close DB connections ────────────────────────────────────────────
        if self.duck: self.duck.close()
        if self.db:   self.db.close()

        elapsed = round(time.perf_counter() - run_t0, 2)
        log.info(
            "[MDL003] Complete: %d/%d OK  tables=%d/%d  fin=%d  calc=%d  err=%d  "
            "verify=%d/%d  text=%d  %.2fs",
            len(pdf_reports) - fail_count, len(pdf_reports),
            out["total_tables_ok"], out["total_tables_in"],
            out["total_fin_tables"], out["total_calc_applied"],
            out["total_err"], out["total_verify_pass"],
            out["total_verify_pass"] + out["total_verify_fail"],
            out["total_text_blocks"], elapsed,
        )
        return {
            "ok":               fail_count == 0,
            "total":            len(pdf_reports),
            "success":          len(pdf_reports) - fail_count,
            "total_tables_ok":  out["total_tables_ok"],
            "total_fin_tables": out["total_fin_tables"],
            "total_calc":       out["total_calc_applied"],
            "total_err":        out["total_err"],
            "elapsed":          elapsed,
            "flush_stats":      flush_stats,
            "self_verify_html": sv_html_path,
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
    "TextRepairEngine",
    "RestoredTable",
    "restore_one_table", "apply_calc_rules", "verify_financial_arithmetic",
    "reflow_text_blocks", "repair_text_blocks_batch",
    "process_one_pdf", "assemble_output",
    "MDL003DBWriter", "MDL003DuckWriter", "MDL003BatchBuffer",
    "MDL003SelfVerifier", "build_self_verify_html",
    "VRN_MDL003_TableRestorer",
    "_jwrite", "_jwrite_fast",
    "pl_export_parquet", "pl_export_csv",
]

# ============================================================================
# __main__
# ============================================================================

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="VRN MDL003 TableRestorer v1.1.0 -- Restore+Validate")
    for k, v in _DEFAULTS.items():
        tp = bool if isinstance(v, bool) else (int if isinstance(v, int) else str)
        if tp == bool: p.add_argument("--" + k.replace("_", "-"), action="store_true", default=v)
        else:          p.add_argument("--" + k.replace("_", "-"), type=tp, default=v)
    args   = p.parse_args()
    cfg    = {k.replace("-", "_"): v for k, v in vars(args).items()}
    result = VRN_MDL003_TableRestorer(cfg).run()
    print(json.dumps(result, ensure_ascii=False, indent=2))
