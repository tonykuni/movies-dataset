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
VRN_MDL004_OCR_FetchingPDFTable.py
=======================================
VERITAS REPORT NOVA -- MDL004  Multi-Engine OCR + PDF Table Fetching
Version   : 1.0.0   |   Module ID : VRN-MDL004-SUP-001
Asset ID  : VRN-MDL004-CLS-001
Policy    : 功能只增不減 · append-only · SSOT · 獨立模組

PIPELINE POSITION
  pdf_temp/                ← 高畫質 PDF (from MDL001)
    ↓ (parallel with MDL002/MDL003)
  VRN_MDL004_OCR_FetchingPDFTable_v1  (此模組)
    ↓
  mdl004_temp/             ← 精準表格數據 (OCR+修復) → MDL005+

DESIGN PRINCIPLES
  ① ALL PARAMETERS ON TOP  — single _PARAMS dict, zero magic numbers buried in code
  ② AST-CLEAN SECTIONS     — each §section is a self-contained extractable unit
  ③ MODULAR / DETACHABLE   — every engine, fix, validator callable standalone
  ④ 20 FIX STRATEGIES BUILT-IN — F01–F20 each a separate named function
  ⑤ DUAL-ENGINE VOTING     — primary + secondary engine, consensus merge
  ⑥ CONTEXT-AWARE HEADER   — look 3 rows UP for real header detection
  ⑦ PYDANTIC SCHEMA CHECK  — typed row validation, auto-tag ERR/WARN/PASS

ANCHOR MAP
  [VRN:ANCHOR:MDL004-META-001]     §0   Module Metadata
  [VRN:ANCHOR:MDL004-PARAMS-001]   §1   ALL PARAMETERS (single source of truth)
  [VRN:ANCHOR:MDL004-SSOT-001]     §2   SSOT + TW Regex (locked)
  [VRN:ANCHOR:MDL004-ACCEL-001]    §3   Accelerator Init
  [VRN:ANCHOR:MDL004-SAFEIMPORT-001] §4 Safe Imports (80+ graceful)
  [VRN:ANCHOR:MDL004-DATACLASS-001]  §5 Data Classes
  [VRN:ANCHOR:MDL004-SCAN-001]     §6   PDF Scanner
  [VRN:ANCHOR:MDL004-CONTEXT-001]  §7   Context-Aware Header (look-up 3 rows)
  [VRN:ANCHOR:MDL004-ENGINE-001]   §8   Engine A: pdfplumber (primary)
  [VRN:ANCHOR:MDL004-ENGINE-002]   §9   Engine B: PyMuPDF / fitz (secondary)
  [VRN:ANCHOR:MDL004-ENGINE-003]   §10  Engine C: Camelot (lattice/stream)
  [VRN:ANCHOR:MDL004-ENGINE-004]   §11  Engine D: Tabula-py
  [VRN:ANCHOR:MDL004-ENGINE-005]   §12  Engine E: PaddleOCR (scan fallback)
  [VRN:ANCHOR:MDL004-ENGINE-006]   §13  Engine F: Docling (AI layout)
  [VRN:ANCHOR:MDL004-VOTE-001]     §14  Dual-Engine Voting + Consensus Merge
  [VRN:ANCHOR:MDL004-FIX-001]      §15  F01–F20 Fix Strategy Library
  [VRN:ANCHOR:MDL004-SCHEMA-001]   §16  Pydantic Schema Validator
  [VRN:ANCHOR:MDL004-EXTERNAL-001] §17  External SSOT Integration
  [VRN:ANCHOR:MDL004-DB-001]       §18  DB Writer (WAL + Parquet + CSV)
  [VRN:ANCHOR:MDL004-OUT-001]      §19  Output Assembler
  [VRN:ANCHOR:MDL004-SYS-001]      §20  Pipeline Entry

SMART ASSET REGISTRY
  VRN-MDL004-CLS-001  VRN_MDL004_OCRFetcher
  VRN-MDL004-CLS-002  MDL004DBWriter
  VRN-MDL004-CLS-003  RawTableResult
  VRN-MDL004-CLS-004  FixedTable
  VRN-MDL004-CLS-005  TableRow (Pydantic)
  VRN-MDL004-FNC-001..FNC-040  (see inline AST comments)

OUTPUTS (mdl004_temp)
  VRN_MDL004_Tables.json        ← per-PDF all tables (fixed + validated)
  VRN_MDL004_VerifySummary.json ← fix/error/warn counts per engine
  VRN_MDL004.db                 ← SQLite WAL (tables + fix_log + schema_log)
  VRN_MDL004_Tables.parquet     ← Parquet flat
  VRN_MDL004_Tables.csv         ← CSV (UTF-8 BOM)

EXTERNAL SSOT PATHS
  supportive_module/VIA_SSOT_Unified.py
  supportive_module/VeritasAegisNexus.py
  supportive_module/VeritasCeleritas.py

LL RULES: #10 #12 #13 #15 #17 #18 #19 #20
"""

# ============================================================================
# [VRN:ANCHOR:MDL004-META-001] §0  MODULE METADATA
# ============================================================================

__version__   = "1.1.0"
__module_id__ = "VRN-MDL004-SUP-001"
__asset_id__  = "VRN-MDL004-CLS-001"
__author__    = "VRN Team"
__domain__    = "OCR_TABLE_FETCH"

# ============================================================================
# [VRN:ANCHOR:MDL004-PARAMS-001] §1  ALL PARAMETERS — SINGLE SOURCE OF TRUTH
# ── Change behaviour HERE only. Zero magic numbers elsewhere in code. ────────
# ============================================================================

_PARAMS: dict = {

    # ── Paths ─────────────────────────────────────────────────────────────────
    "pdf_temp":    r"C:\VeritasIntelligenceAnalytics\VeritasReportNova\temp\pdf_temp",
    "mdl004_temp": r"C:\VeritasIntelligenceAnalytics\VeritasReportNova\temp\mdl004_temp",
    "ssot_dir":    r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module",

    # ── Concurrency ───────────────────────────────────────────────────────────
    "workers":     0,           # 0 = auto (cpu_count - 1)

    # ── DB / output ───────────────────────────────────────────────────────────
    "enable_db":   True,
    "zero_error":  True,        # raise on unhandled exception in process_one

    # ── Engine selection (order = priority) ───────────────────────────────────
    # Available: "pdfplumber", "pymupdf", "camelot_lattice", "camelot_stream",
    #            "tabula", "paddleocr", "docling"
    "engine_primary":   "pdfplumber",
    "engine_secondary": "pymupdf",
    "engine_fallback":  "camelot_lattice",
    "engine_ocr":       "paddleocr",        # used only when PDF is scan-based

    # ── Context-aware header ──────────────────────────────────────────────────
    "header_look_up_px":    80,     # pixels above table bbox to search for header
    "header_look_up_rows":  3,      # max rows to inspect for real header
    "header_min_cols":      2,      # min columns to accept a row as header

    # ── Table geometry ────────────────────────────────────────────────────────
    "snap_tolerance":       3,      # px tolerance for line snapping
    "join_tolerance":       3,      # px tolerance for cell joining
    "edge_tolerance":       2,      # px tolerance for edge detection
    "min_table_rows":       2,      # discard tables with fewer rows
    "min_table_cols":       2,      # discard tables with fewer cols

    # ── Quadrant split for dense fin-pages ───────────────────────────────────
    "quadrant_split":       True,

    # ── OCR (PaddleOCR) ───────────────────────────────────────────────────────
    "ocr_lang":             "ch",   # ch / en / japan
    "ocr_use_gpu":          False,
    "ocr_det_db_thresh":    0.3,

    # ── Scan detection ────────────────────────────────────────────────────────
    "scan_text_threshold":  50,     # avg chars/page below this → treat as scan
    "scan_sample_pages":    3,

    # ── Fix strategy flags (F01–F20) — set False to disable individual fix ──
    "fix_F01_header_context":       True,   # look-up 3 rows above
    "fix_F02_cross_page_concat":    True,   # merge split tables across pages
    "fix_F03_borderless_explicit":  True,   # explicit vertical lines for stream
    "fix_F04_dual_column_split":    True,   # split dual-column pages
    "fix_F05_nested_table":         True,   # snap_tolerance adjustment
    "fix_F06_rowspan_ffill":        True,   # forward fill vertical merged cells
    "fix_F07_colspan_ffill":        True,   # forward fill horizontal merged cells
    "fix_F08_text_wrap_merge":      True,   # merge wrapped continuation lines
    "fix_F09_text_center_align":    True,   # use text center for alignment
    "fix_F10_empty_row_drop":       True,   # drop all-None rows
    "fix_F11_zh_space":             True,   # remove spaces between CJK chars
    "fix_F12_ocr_alphanum":         True,   # O→0, I→1 in numeric context
    "fix_F13_trim_nbsp":            True,   # strip + replace \u00a0
    "fix_F14_currency_bracket":     True,   # (1,000) → -1000
    "fix_F15_mojibake_ocr":         True,   # fallback OCR for encoding failures
    "fix_F16_header_shift":         True,   # auto re-detect header row
    "fix_F17_sum_verify":           True,   # total == sum of sub-items check
    "fix_F18_dtype_note_spill":     True,   # detect notes bleeding into data col
    "fix_F19_watermark_filter":     True,   # filter light-color / tiny text
    "fix_F20_col_shift_repair":     True,   # repair column count mismatch

    # ── Validation thresholds ─────────────────────────────────────────────────
    "sum_verify_tolerance":         0.02,   # 2% for total vs sub-items
    "confidence_high":              0.90,
    "confidence_mid":               0.70,
    "watermark_rgb_min":            240,    # RGB value above this = watermark
    "watermark_fontsize_max":       6.0,    # pt below this = watermark

    # ── Pydantic strict mode ──────────────────────────────────────────────────
    "schema_strict":                False,  # False = coerce, True = reject on fail

    # ── Period regex (time-axis detection) ───────────────────────────────────
    "period_regex": (
        r"(20\d{2}[AEFaefCTct]?|\d{1,2}Q\d{2}|[Ff][Yy]\d{2}[AEae]?|"
        r"\d{4}[Qq]\d|2[0-9][A-Z]{1,2})"
    ),

    # ── Accounting subjects (first-column keywords) ───────────────────────────
    "acct_subjects": [
        "Revenue","Sales","Gross Profit","Operating","EBIT","EBITDA",
        "Net Income","淨利","EPS","每股盈餘","ROE","ROA","毛利","毛利率",
        "Total Assets","總資產","Equity","股東權益","Cash Flow","Dividend",
        "BPS","BVPS","P/E","P/B","CapEx","FCF","DPS",
        "營業收入","營業成本","稅後淨利","每股淨值","股利殖利率",
    ],

    # ── Financial page keywords ───────────────────────────────────────────────
    "fin_keywords": [
        "損益表","資產負債表","現金流量表","財務報表","比率分析",
        "每股分析","Income Statement","Balance Sheet","Cash Flow",
        "Profit & Loss","Financial Summary","Key Financials","Ratio",
    ],

    # ── Required header keywords (for F16 header re-detection) ───────────────
    "header_required_keywords": ["年", "Q", "FY", "20", "E", "F", "A"],

    # ── v1.1.0 NEW (append-only) ──────────────────────────────────────────────
    "use_doc_cache":   True,    # P1 每 PDF 只開一次 fitz + pdfplumber
    "page_parallel":   True,    # P2 page-level 跨 worker 平行
    "page_workers":    0,       # 0 = auto (= workers)
    "use_duckdb":      True,    # P3 DuckDB primary, sqlite fallback
    "batch_size":      5000,    # P3 BatchBuffer flush threshold
    "polars_first":    True,    # P5 polars vectorized cell fixes
    "self_verify":     True,    # P6 4-phase HTML report
}

# ── Convenience short-circuit aliases (read-only) ────────────────────────────
_P = _PARAMS   # use _P["key"] everywhere inside functions

# ============================================================================
# STDLIB
# ============================================================================

import os, sys, re, json, time, math, hashlib, logging, sqlite3, csv, io
import gc, argparse, threading, warnings, collections, copy, importlib
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings("ignore")

# ============================================================================
# [VRN:ANCHOR:MDL004-SAFEIMPORT-001] §4  SAFE IMPORTS
# ============================================================================

def _si(name: str):
    """Safe import — returns module or None."""
    try: return importlib.import_module(name)
    except Exception: return None

# Core PDF
fitz        = _si("fitz")         # PyMuPDF
pdfplumb    = _si("pdfplumber")
# Table engines
camelot_lib = _si("camelot")
tabula_lib  = _si("tabula")
# OCR
paddle_lib  = _si("paddleocr")
# AI layout
docling_lib = _si("docling.document_converter")
# Data
pd          = _si("pandas")
pyarrow     = _si("pyarrow")
orjson      = _si("orjson")
xxhash      = _si("xxhash")
# Validation
pydantic_lib= _si("pydantic")
# Image
cv2         = _si("cv2")
np          = _si("numpy")
PIL_Image   = None
_pil        = _si("PIL")
if _pil:
    try:
        from PIL import Image as _PILImage
        PIL_Image = _PILImage
    except Exception: pass

# v1.1.0 NEW: polars + duckdb (primary) + orjson (fast)
pl          = _si("polars")
duckdb_lib  = _si("duckdb")
POLARS_OK   = pl is not None
DUCKDB_OK   = duckdb_lib is not None

# ── capability map ────────────────────────────────────────────────────────────
_CAP: Dict[str, bool] = {
    "fitz":       fitz is not None,
    "pdfplumber": pdfplumb is not None,
    "camelot":    camelot_lib is not None,
    "tabula":     tabula_lib is not None,
    "paddleocr":  paddle_lib is not None,
    "docling":    docling_lib is not None,
    "pandas":     pd is not None,
    "pyarrow":    pyarrow is not None,
    "pydantic":   pydantic_lib is not None,
    "cv2":        cv2 is not None,
    "numpy":      np is not None,
    "polars":     POLARS_OK,
    "duckdb":     DUCKDB_OK,
    "orjson":     orjson is not None,
}

# ============================================================================
# [VRN:ANCHOR:MDL004-DOCCACHE-001] §4.5  P1 DOC CACHE — v1.1.0
# ── 解 v1.0.0 最大殺手：每頁重開 fitz/pdfplumber                              ─
# ── 一個 PDF 的所有頁、所有 quadrant、所有 fix re-extract 共用同一份 doc handle ─
# ── 用法：                                                                    ─
# ──   with MDL004DocCache(pdf_path) as cache:                                 ─
# ──       fz_doc  = cache.fitz_doc                                            ─
# ──       pp_pdf  = cache.pdfplumber_pdf                                      ─
# ── thread-safe：handle 是 read-only，並行 page extract OK                    ─
# ============================================================================

class MDL004DocCache:
    """VRN-MDL004-CLS-006 (NEW v1.1.0)
    Open fitz + pdfplumber ONCE per PDF, share handles for all page operations.
    A4 50頁原本 ~150 次 open() → 只 2 次。

    Note: pdfplumber is NOT 100% thread-safe for concurrent extract on shared
    Page objects, but DocCache itself just owns the handle; per-page parallel
    workers should call .get_pdfplumber_page(n) which returns a fresh page slice.
    """
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self._fitz: Any = None
        self._pp:   Any = None
        self._lock = threading.Lock()
        self.n_pages: int = 0
        self.page_widths:  List[float] = []
        self.page_heights: List[float] = []

    def __enter__(self):
        if _CAP["fitz"]:
            try:
                self._fitz = fitz.open(self.pdf_path)
                self.n_pages = len(self._fitz)
                for pg in self._fitz:
                    self.page_widths.append(float(pg.rect.width))
                    self.page_heights.append(float(pg.rect.height))
            except Exception as e:
                log.debug("[MDL004] DocCache fitz open fail: %s", e)
                self._fitz = None
        if _CAP["pdfplumber"]:
            try:
                self._pp = pdfplumb.open(self.pdf_path)
                if self.n_pages == 0:
                    self.n_pages = len(self._pp.pages)
            except Exception as e:
                log.debug("[MDL004] DocCache pdfplumber open fail: %s", e)
                self._pp = None
        return self

    def __exit__(self, *exc):
        if self._fitz is not None:
            try: self._fitz.close()
            except: pass
        if self._pp is not None:
            try: self._pp.close()
            except: pass

    @property
    def fitz_doc(self): return self._fitz
    @property
    def pdfplumber_pdf(self): return self._pp

    def fitz_page(self, page_no: int):
        """1-based; return None if out of range/unavailable."""
        if self._fitz is None or page_no - 1 >= len(self._fitz): return None
        return self._fitz[page_no - 1]

    def pdfplumber_page(self, page_no: int):
        """1-based."""
        if self._pp is None or page_no - 1 >= len(self._pp.pages): return None
        return self._pp.pages[page_no - 1]


# ============================================================================
# [VRN:ANCHOR:MDL004-PRECOMP-001] §4.6  P4 PRE-COMPILED REGEX POOL — v1.1.0
# ============================================================================

_RE_BRACKET_NEG = re.compile(r"^\((.*?)\)$")
# v1.1.0 fix: same bug as MDL003 had -- "2O25" failed because both sides of inner O are \w
_RE_OCR_O_TO_0  = re.compile(
    r"(?<![A-Za-z])O(?=\d)|(?<=\d)O(?=\d)|(?<=\d)O(?![A-Za-z])"
)
_RE_OCR_l_TO_1  = re.compile(r"(?<![A-Za-z])[lI\|](?=\d)|(?<=\d)[lI\|](?![A-Za-z])")
_RE_NORM_PUNCT  = re.compile(r"[\s/（）()（）%,，]")
_RE_DOUBLESPACE = re.compile(r" {2,}")
# Pre-compile MOJIBAKE detect range
_RE_MOJIBAKE    = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x80-\x9f]")

# ============================================================================
# [VRN:ANCHOR:MDL004-SSOT-001] §2  SSOT — LOCKED TW REGEX
# ============================================================================

# THREE LOCKED TAIWAN TICKER REGEX — IMMUTABLE, NEVER MODIFY
TW_TICKER_REGEX    = re.compile(r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})")
TW_BLOOMBERG_REGEX = re.compile(r"\b(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})\s+TT\b")
TW_YFINANCE_REGEX  = re.compile(r"\b(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})\.(TW|TWO)\b")

_PERIOD_RE  = re.compile(_P["period_regex"])
_ZH_SP_RE   = re.compile(r"(?<=[\u4e00-\u9fa5])\s+(?=[\u4e00-\u9fa5])")
_OCR_NUM_RE = re.compile(r"(?<!\w)([lOI\|])(?=[\d,])|(?<=[\d,])([lOI\|])(?!\w)")
_BRACKET_RE = re.compile(r"^\(([^)]+)\)$")
_AXIS_RE1   = re.compile(r"^[-+]?[\d\s,\.]+%?$")
_AXIS_RE2   = re.compile(r"^(?:[-+]?\d{1,3}(?:\.\d+)?[%O]?\s*){4,}$")
_AXIS_RE3   = re.compile(r"^\s*(\d+[OBoS]+|[sS]o+|JO+|I+)\s*$")

# ============================================================================
# [VRN:ANCHOR:MDL004-ACCEL-001] §3  ACCELERATOR INIT
# ============================================================================

def _mdl004_accel_init(workers: int = 0) -> Dict:
    """VRN-MDL004-FNC-001  6-ENV thread init + GC tuning."""
    w = workers or max(1, (os.cpu_count() or 4) - 1)
    for v in ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS",
              "NUMEXPR_NUM_THREADS","BLIS_NUM_THREADS","VECLIB_MAXIMUM_THREADS"):
        os.environ.setdefault(v, str(w))
    gc.set_threshold(50_000, 500, 50)
    return {"workers": w, **_CAP}

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s][%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ============================================================================
# [VRN:ANCHOR:MDL004-PLUGIN-HOLDERS-001] §3.5  7-TOOL HARDGATE PLUGIN HOLDERS
# ── Module-level holders so any function in this file can call into the     ─
# ── 7 supportive tools without re-importing. Set during load_external_ssot()─
# ── Order per VIA_Supportive_HardGate_Seal.json:                            ─
# ──   1) VIA_SSOT_Unified                                                    ─
# ──   2) VIA_RegistryCore_v1                                                 ─
# ──   3) VIA_Runtime_Bridge_All_in_One                                       ─
# ──   4) VIA_EnvManager                                                      ─
# ──   5) VIA_Panorama_AST_RuntimeInjector                                    ─
# ──   6) VeritasCeleritas                                                    ─
# ──   7) VeritasAegisNexus                                                   ─
# ── Policy: BOOT_PRECHECK_ONLY_NO_NETWORK_NO_PARALLEL_NO_AUTOPATCH           ─
# ============================================================================

# [VRN:ANCHOR:HARDGATE_HOLDERS:V1]
_SSOT: Any = None;  _SSOT_OK:  bool = False
_REG:  Any = None;  _REG_OK:   bool = False
_BRG:  Any = None;  _BRG_OK:   bool = False
_ENV:  Any = None;  _ENV_OK:   bool = False
_AST:  Any = None;  _AST_OK:   bool = False
_CEL:  Any = None;  _CEL_OK:   bool = False
_NET:  Any = None;  _NET_OK:   bool = False

# OCR_Plugins (companion module — same D4 zone, ADAPTER role)
_OCR_PLUGINS:    Any  = None
_OCR_PLUGINS_OK: bool = False

def _find_plugin(ssot_dir: str, filename: str) -> Optional[str]:
    """VRN-MDL004-FNC-PLUGIN-001  Search ssot_dir + parents for plugin file."""
    candidates = [
        Path(ssot_dir) / filename,
        Path(ssot_dir).parent / filename,
        Path(ssot_dir).parent.parent / "module" / filename,
        Path(ssot_dir).parent.parent / "supportive_module" / filename,
    ]
    for c in candidates:
        if c.exists(): return str(c)
    return None

def _find_companion(filename: str) -> Optional[str]:
    """VRN-MDL004-FNC-PLUGIN-002  Search MDL004 directory + parents for companion module
    (e.g. VRN_MDL004_OCR_Plugins_v1.py). Different search path than _find_plugin."""
    here = Path(__file__).resolve().parent
    candidates = [
        here / filename,
        here.parent / filename,
        here.parent / "VRN" / filename,
        here.parent.parent / "module" / "VRN" / filename,
    ]
    for c in candidates:
        if c.exists(): return str(c)
    return None

# ============================================================================
# [VRN:ANCHOR:MDL004-DATACLASS-001] §5  DATA CLASSES
# ── All data structures live here — import / detach freely ──────────────────
# ============================================================================

@dataclass
class RawTableResult:
    """VRN-MDL004-CLS-003  Raw output from one engine on one region."""
    engine:       str = ""
    page_no:      int = 0
    region_id:    str = ""          # P{page:03d}TBL{seq:03d}
    region_type:  str = ""          # 1st_page | fin_page | content
    quadrant:     str = "full"      # TL | TR | BL | BR | full
    bbox:         List[float] = field(default_factory=list)
    raw_data:     List[List[str]] = field(default_factory=list)
    header_context: str = ""        # text above table (F01)
    n_rows:       int = 0
    n_cols:       int = 0
    ok:           bool = False
    error:        Optional[str] = None

@dataclass
class FixedTable:
    """VRN-MDL004-CLS-004  Table after all 20 fix strategies applied."""
    region_id:      str = ""
    pdf_name:       str = ""
    report_code:    str = ""
    page_no:        int = 0
    region_type:    str = ""
    quadrant:       str = "full"
    engine_primary: str = ""
    engine_used:    str = ""        # final engine that produced accepted data
    header_row:     List[str] = field(default_factory=list)
    periods:        List[str] = field(default_factory=list)
    rows:           List[Dict] = field(default_factory=list)
    # row format: {label_raw, cells: [str], values: {col_idx: str}}
    fixes_applied:  List[str] = field(default_factory=list)  # ["F01","F06",...]
    n_err_cells:    int = 0
    n_warn_cells:   int = 0
    schema_pass:    bool = False
    confidence:     float = 0.0     # 0.0–1.0
    header_context: str = ""
    ok:             bool = False
    error:          Optional[str] = None

# ── Pydantic TableRow (optional, graceful if pydantic not installed) ──────────

def _build_pydantic_model():
    """VRN-MDL004-FNC-002  Build Pydantic TableRow if available, else stub."""
    if not _CAP["pydantic"]: return None
    try:
        from pydantic import BaseModel, field_validator, model_validator
        import re as _re

        class TableRow(BaseModel):
            model_config = {"arbitrary_types_allowed": True, "str_strip_whitespace": True}
            label:  str  = ""
            values: Dict[str, Optional[float]] = {}
            status: str  = "PASS"   # PASS | WARN | ERR

            @field_validator("label", mode="before")
            @classmethod
            def clean_label(cls, v):
                v = str(v or "").strip()
                v = _ZH_SP_RE.sub("", v)
                return v

            @field_validator("values", mode="before")
            @classmethod
            def coerce_values(cls, raw):
                if not isinstance(raw, dict): return {}
                return {str(k): _clean_number(str(v)) for k, v in raw.items()}

        return TableRow
    except Exception as e:
        log.debug("[MDL004] Pydantic model build failed: %s", e)
        return None

_TableRow = _build_pydantic_model()

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
        return orjson.loads(txt) if orjson else json.loads(txt)
    except Exception as e: log.warning("[MDL004] jload %s: %s", p, e); return None

def _parse_meta(pdf_path: str) -> Dict:
    stem = Path(pdf_path).stem
    meta = {"ticker":"","report_date":"","broker_abbr":"","report_code":_hash8(stem)}
    dm = re.search(r"(20\d{2})[_\-]?(\d{2})[_\-]?(\d{2})", stem)
    if dm: meta["report_date"] = "{}-{}-{}".format(dm.group(1),dm.group(2),dm.group(3))
    bm = re.search(r"(GS|MS|JPM|CITI|UBS|兆豐|國泰|中信|元大|富邦|凱基)", stem, re.I)
    if bm: meta["broker_abbr"] = bm.group(1).upper()
    for tok in re.split(r"[_\-\s]", stem):
        m = re.fullmatch(r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})", tok.strip())
        if m: meta["ticker"] = m.group(1); break
    return meta

# ============================================================================
# [VRN:ANCHOR:MDL004-SCAN-001] §6  PDF SCANNER
# ============================================================================

def list_pdfs(pdf_temp: str) -> List[str]:
    """VRN-MDL004-FNC-003"""
    if not os.path.isdir(pdf_temp): return []
    return sorted(os.path.join(pdf_temp, f) for f in os.listdir(pdf_temp)
                  if f.lower().endswith(".pdf"))

def is_scan_pdf(pdf_path: str) -> bool:
    """VRN-MDL004-FNC-004  Detect if PDF is image-based (scanned)."""
    if not _CAP["fitz"]: return False
    try:
        doc = fitz.open(pdf_path)
        n   = min(len(doc), _P["scan_sample_pages"])
        chars = sum(len(doc[i].get_text().strip()) for i in range(n))
        doc.close()
        return (chars / max(n, 1)) < _P["scan_text_threshold"]
    except Exception: return False

# ============================================================================
# [VRN:ANCHOR:MDL004-CONTEXT-001] §7  CONTEXT-AWARE HEADER (F01)
# ── Standalone: call get_header_context(page, table_bbox) anywhere ───────────
# ============================================================================

def get_header_context(page: Any, table_bbox: List[float]) -> str:
    """VRN-MDL004-FNC-005
    Look up to _P['header_look_up_px'] pixels ABOVE table top edge.
    Returns concatenated text of that zone.
    """
    if page is None or not table_bbox: return ""
    try:
        x0, y0, x1, _ = table_bbox
        up_y0 = max(0.0, y0 - _P["header_look_up_px"])
        ctx_bbox = (x0, up_y0, x1, y0)
        txt = page.within_bbox(ctx_bbox).extract_text() or ""
        return txt.strip()
    except Exception as e:
        log.debug("[MDL004] header_context: %s", e); return ""

def find_real_header_row(raw_data: List[List[str]]) -> int:
    """VRN-MDL004-FNC-006
    Among first _P['header_look_up_rows'] rows, find the one with
    the most period-pattern hits (year/quarter). Returns row index (0-based).
    """
    best_idx, best_hits = 0, 0
    for idx in range(min(_P["header_look_up_rows"], len(raw_data))):
        row_text = " ".join(str(c or "") for c in raw_data[idx])
        hits = len(_PERIOD_RE.findall(row_text))
        kw_hits = sum(1 for kw in _P["header_required_keywords"] if kw in row_text)
        score = hits + kw_hits
        if score > best_hits:
            best_hits = score
            best_idx  = idx
    return best_idx

# ============================================================================
# [VRN:ANCHOR:MDL004-ENGINE-001] §8  ENGINE A: pdfplumber (PRIMARY)
# ── Standalone: call engine_pdfplumber(pdf_path, page_no, cfg) anywhere ─────
# ============================================================================

def engine_pdfplumber(
    pdf_path: str,
    page_no:  int,
    quadrant: Optional[Tuple[float, float, float, float]] = None,
    doc_cache: Optional["MDL004DocCache"] = None,    # v1.1.0 NEW
) -> List[RawTableResult]:
    """VRN-MDL004-FNC-007  pdfplumber table extraction with optional bbox crop.
    v1.1.0: if doc_cache provided, reuse open pdfplumber handle (no re-open).
    """
    results: List[RawTableResult] = []
    if not _CAP["pdfplumber"]: return results
    try:
        settings = {
            "vertical_strategy":   "lines",
            "horizontal_strategy": "lines",
            "snap_tolerance":      _P["snap_tolerance"],
            "join_tolerance":      _P["join_tolerance"],
            "edge_tolerance":      _P["edge_tolerance"],
        }

        # v1.1.0 fast path: cached handle
        if doc_cache is not None and doc_cache.pdfplumber_pdf is not None:
            pg = doc_cache.pdfplumber_page(page_no)
            if pg is None: return results
            ctx_page = pg.within_bbox(quadrant) if quadrant else pg
            for strategy in (settings, {**settings,
                             "vertical_strategy":"text","horizontal_strategy":"text"}):
                tbls = ctx_page.extract_tables(strategy) or []
                if tbls: break
            seq = 1
            for tbl in tbls:
                if not tbl or len(tbl) < _P["min_table_rows"]: continue
                n_cols = max(len(r) for r in tbl) if tbl else 0
                if n_cols < _P["min_table_cols"]: continue
                region_id = "P{:03d}TBL{:03d}".format(page_no, seq)
                ctx_text  = (get_header_context(pg, [0, 0, pg.width, pg.height])
                             if quadrant is None else "")
                results.append(RawTableResult(
                    engine="pdfplumber", page_no=page_no,
                    region_id=region_id, raw_data=tbl,
                    header_context=ctx_text, n_rows=len(tbl),
                    n_cols=n_cols, ok=True,
                ))
                seq += 1
            return results

        # Legacy path: open the PDF (v1.0.0 fallback)
        with pdfplumb.open(pdf_path) as pdf:
            if page_no - 1 >= len(pdf.pages): return results
            pg = pdf.pages[page_no - 1]
            ctx_page = pg.within_bbox(quadrant) if quadrant else pg
            # Try lines strategy first, fall back to text strategy
            for strategy in (settings, {**settings,
                             "vertical_strategy":"text","horizontal_strategy":"text"}):
                tbls = ctx_page.extract_tables(strategy) or []
                if tbls: break
            seq = 1
            for tbl in tbls:
                if not tbl or len(tbl) < _P["min_table_rows"]: continue
                n_cols = max(len(r) for r in tbl) if tbl else 0
                if n_cols < _P["min_table_cols"]: continue
                region_id = "P{:03d}TBL{:03d}".format(page_no, seq)
                ctx_text  = get_header_context(pg, [0, 0, pg.width, pg.height]) if quadrant is None else ""
                results.append(RawTableResult(
                    engine  = "pdfplumber",
                    page_no = page_no,
                    region_id   = region_id,
                    raw_data    = tbl,
                    header_context = ctx_text,
                    n_rows  = len(tbl),
                    n_cols  = n_cols,
                    ok      = True,
                ))
                seq += 1
    except Exception as e:
        log.debug("[MDL004] pdfplumber page %d: %s", page_no, e)
    return results

# ============================================================================
# [VRN:ANCHOR:MDL004-ENGINE-002] §9  ENGINE B: PyMuPDF / fitz (SECONDARY)
# ============================================================================

def engine_pymupdf(pdf_path: str, page_no: int,
                   doc_cache: Optional["MDL004DocCache"] = None) -> List[RawTableResult]:
    """VRN-MDL004-FNC-008  PyMuPDF text-line extraction → pseudo table rows.
    v1.1.0: if doc_cache provided, reuse open fitz handle.
    """
    results: List[RawTableResult] = []
    if not _CAP["fitz"]: return results
    try:
        # v1.1.0 fast path: cached handle
        if doc_cache is not None and doc_cache.fitz_doc is not None:
            pg = doc_cache.fitz_page(page_no)
            if pg is None: return results
            data = pg.get_text("dict")
        else:
            doc = fitz.open(pdf_path)
            if page_no - 1 >= len(doc): doc.close(); return results
            pg   = doc[page_no - 1]
            data = pg.get_text("dict")
            doc.close()

        # Group spans into rows by y-coordinate proximity
        rows_by_y: Dict[int, List[str]] = {}
        for block in data.get("blocks", []):
            for line in block.get("lines", []):
                y_key = round(line["bbox"][1] / 5) * 5   # bucket to 5px
                spans = [sp["text"].strip() for sp in line.get("spans",[]) if sp.get("text","").strip()]
                if spans:
                    rows_by_y.setdefault(y_key, []).extend(spans)

        table = [row for _, row in sorted(rows_by_y.items()) if row]
        if len(table) < _P["min_table_rows"]: return results

        results.append(RawTableResult(
            engine="pymupdf", page_no=page_no,
            region_id="P{:03d}TBL001".format(page_no),
            raw_data=table, n_rows=len(table),
            n_cols=max(len(r) for r in table), ok=True,
        ))
    except Exception as e:
        log.debug("[MDL004] pymupdf page %d: %s", page_no, e)
    return results

# ============================================================================
# [VRN:ANCHOR:MDL004-ENGINE-003] §10  ENGINE C: Camelot
# ============================================================================

def engine_camelot(
    pdf_path: str,
    page_no:  int,
    flavor:   str = "lattice",
) -> List[RawTableResult]:
    """VRN-MDL004-FNC-009  Camelot lattice or stream extraction."""
    results: List[RawTableResult] = []
    if not _CAP["camelot"]: return results
    try:
        tables = camelot_lib.read_pdf(
            pdf_path, pages=str(page_no), flavor=flavor,
            suppress_stdout=True,
        )
        for idx, tbl in enumerate(tables, start=1):
            df = tbl.df
            raw = [df.columns.tolist()] + df.values.tolist()
            raw = [[str(c) for c in row] for row in raw]
            if len(raw) < _P["min_table_rows"]: continue
            results.append(RawTableResult(
                engine="camelot_" + flavor, page_no=page_no,
                region_id="P{:03d}TBL{:03d}".format(page_no, idx),
                raw_data=raw, n_rows=len(raw),
                n_cols=max(len(r) for r in raw), ok=True,
            ))
    except Exception as e:
        log.debug("[MDL004] camelot %s page %d: %s", flavor, page_no, e)
    return results

# ============================================================================
# [VRN:ANCHOR:MDL004-ENGINE-004] §11  ENGINE D: Tabula-py
# ============================================================================

def engine_tabula(pdf_path: str, page_no: int) -> List[RawTableResult]:
    """VRN-MDL004-FNC-010  Tabula-py extraction."""
    results: List[RawTableResult] = []
    if not _CAP["tabula"]: return results
    try:
        import tabula as _tabula
        dfs = _tabula.read_pdf(
            pdf_path, pages=page_no, multiple_tables=True, silent=True,
        )
        for idx, df in enumerate(dfs, start=1):
            if df is None or df.empty: continue
            raw = [list(df.columns)] + df.fillna("").values.tolist()
            raw = [[str(c) for c in row] for row in raw]
            if len(raw) < _P["min_table_rows"]: continue
            results.append(RawTableResult(
                engine="tabula", page_no=page_no,
                region_id="P{:03d}TBL{:03d}".format(page_no, idx),
                raw_data=raw, n_rows=len(raw),
                n_cols=max(len(r) for r in raw), ok=True,
            ))
    except Exception as e:
        log.debug("[MDL004] tabula page %d: %s", page_no, e)
    return results

# ============================================================================
# [VRN:ANCHOR:MDL004-ENGINE-005] §12  ENGINE E: PaddleOCR (scan fallback)
# ============================================================================

def engine_paddleocr(pdf_path: str, page_no: int) -> List[RawTableResult]:
    """VRN-MDL004-FNC-011  PaddleOCR for scanned PDF pages."""
    results: List[RawTableResult] = []
    if not _CAP["paddleocr"] or not _CAP["fitz"]: return results
    try:
        from paddleocr import PaddleOCR  # type: ignore
        ocr = PaddleOCR(
            use_angle_cls=True,
            lang=_P["ocr_lang"],
            use_gpu=_P["ocr_use_gpu"],
            show_log=False,
        )
        doc = fitz.open(pdf_path)
        if page_no - 1 >= len(doc): doc.close(); return results
        pg  = doc[page_no - 1]
        # Render page at high DPI for OCR
        mat = fitz.Matrix(300 / 72.0, 300 / 72.0)
        pix = pg.get_pixmap(matrix=mat, alpha=False)
        doc.close()
        img_arr = None
        if _CAP["numpy"]:
            import numpy as _np
            img_arr = _np.frombuffer(pix.tobytes("png"), dtype=_np.uint8)
            img_arr = __import__("cv2").imdecode(img_arr, 1) if _CAP["cv2"] else img_arr

        if img_arr is None: return results
        ocr_result = ocr.ocr(img_arr, cls=True)
        if not ocr_result or not ocr_result[0]: return results

        # Convert OCR result to rows (group by y-coordinate)
        rows_by_y: Dict[int, List[str]] = {}
        for line in ocr_result[0]:
            bbox_pts, (text, conf) = line
            y_center = int((bbox_pts[0][1] + bbox_pts[2][1]) / 2)
            y_bucket = round(y_center / 15) * 15
            if conf >= 0.5:
                rows_by_y.setdefault(y_bucket, []).append(text.strip())

        table = [row for _, row in sorted(rows_by_y.items()) if row]
        if len(table) < _P["min_table_rows"]: return results

        results.append(RawTableResult(
            engine="paddleocr", page_no=page_no,
            region_id="P{:03d}TBL001".format(page_no),
            raw_data=table, n_rows=len(table),
            n_cols=max(len(r) for r in table), ok=True,
        ))
    except Exception as e:
        log.debug("[MDL004] paddleocr page %d: %s", page_no, e)
    return results

# ============================================================================
# [VRN:ANCHOR:MDL004-ENGINE-006] §13  ENGINE F: Docling (AI layout)
# ============================================================================

def engine_docling(pdf_path: str) -> List[RawTableResult]:
    """VRN-MDL004-FNC-012  Docling AI document parsing (whole document)."""
    results: List[RawTableResult] = []
    if not _CAP["docling"]: return results
    try:
        from docling.document_converter import DocumentConverter  # type: ignore
        conv  = DocumentConverter()
        doc   = conv.convert(pdf_path).document
        seq   = 1
        for tbl in getattr(doc, "tables", []):
            raw = [[str(c) for c in row] for row in tbl.data]
            if len(raw) < _P["min_table_rows"]: continue
            results.append(RawTableResult(
                engine="docling", page_no=0,
                region_id="PDOC_TBL{:03d}".format(seq),
                raw_data=raw, n_rows=len(raw),
                n_cols=max(len(r) for r in raw), ok=True,
            ))
            seq += 1
    except Exception as e:
        log.debug("[MDL004] docling %s: %s", pdf_path, e)
    return results

# ============================================================================
# [VRN:ANCHOR:MDL004-VOTE-001] §14  DUAL-ENGINE VOTING + CONSENSUS MERGE
# ============================================================================

def vote_and_merge(
    primary_results:   List[RawTableResult],
    secondary_results: List[RawTableResult],
) -> List[RawTableResult]:
    """VRN-MDL004-FNC-013
    Pair primary and secondary results by page_no + region_id index.
    Prefer primary if row/col counts match within 20%; else use whichever has more cells.
    Returns accepted results tagged with engine_used.
    """
    accepted: List[RawTableResult] = []
    primary_by_page: Dict[int, List[RawTableResult]] = {}
    for r in primary_results:
        primary_by_page.setdefault(r.page_no, []).append(r)
    sec_by_page: Dict[int, List[RawTableResult]] = {}
    for r in secondary_results:
        sec_by_page.setdefault(r.page_no, []).append(r)

    all_pages = sorted(set(list(primary_by_page) + list(sec_by_page)))
    for pg in all_pages:
        p_list = primary_by_page.get(pg, [])
        s_list = sec_by_page.get(pg,    [])
        # Pair by index
        max_len = max(len(p_list), len(s_list))
        for i in range(max_len):
            p = p_list[i] if i < len(p_list) else None
            s = s_list[i] if i < len(s_list) else None
            if p and not s:
                p.engine = p.engine + "+solo"
                accepted.append(p)
            elif s and not p:
                s.engine = s.engine + "+solo"
                accepted.append(s)
            else:
                p_cells = p.n_rows * p.n_cols
                s_cells = s.n_rows * s.n_cols
                ratio   = max(p_cells, s_cells) / max(min(p_cells, s_cells), 1)
                # If within 20% → primary wins; else pick larger
                if ratio <= 1.20:
                    p.engine = p.engine + "+confirmed"
                    accepted.append(p)
                else:
                    winner = p if p_cells >= s_cells else s
                    winner.engine = winner.engine + "+larger"
                    accepted.append(winner)
    return accepted

# ============================================================================
# [VRN:ANCHOR:MDL004-FIX-001] §15  F01–F20 FIX STRATEGY LIBRARY
# ── Each fix is a STANDALONE function. Call individually or via apply_fixes() ─
# ============================================================================

# ── Helper ────────────────────────────────────────────────────────────────────

def _clean_number(val: str) -> Optional[float]:
    """Shared numeric cleaner used by F12, F14 and Pydantic."""
    if not val: return None
    v = str(val).strip()
    if v in ("--","---","n.a.","N/A","NA","nm","NM","-","—","",
             "盈轉虧","虧轉盈"): return None
    v = v.replace(",","").replace("，","").replace(" ","").replace("\u00a0","")
    m = _BRACKET_RE.match(v)
    if m: v = "-" + m.group(1)
    v = v.replace("%","")
    v = re.sub(r"(?<!\w)O(?=\d)|(?<=\d)O(?!\w)", "0", v)
    try: return float(v)
    except ValueError: return None

def _is_axis_noise(text: str) -> bool:
    t = text.strip()
    if _AXIS_RE1.match(t): return True
    if _AXIS_RE2.match(t): return True
    if _AXIS_RE3.match(t): return True
    return False

# ── F01 — Header Context Look-up (implemented in §7, called here) ─────────────

def fix_F01_header_context(
    raw: RawTableResult,
    pdf_path: str,
) -> Tuple[RawTableResult, bool]:
    """F01: Enrich RawTableResult with text above table. Returns (result, applied)."""
    if not _P["fix_F01_header_context"] or raw.header_context: return raw, False
    if not _CAP["pdfplumber"]: return raw, False
    try:
        with pdfplumb.open(pdf_path) as pdf:
            if raw.page_no - 1 >= len(pdf.pages): return raw, False
            pg = pdf.pages[raw.page_no - 1]
            raw.header_context = get_header_context(pg, raw.bbox or [0,0,pg.width,pg.height])
        return raw, bool(raw.header_context)
    except Exception: return raw, False

# ── F02 — Cross-page Table Concat ─────────────────────────────────────────────

def fix_F02_cross_page_concat(
    tables: List[List[List[str]]],
) -> List[List[List[str]]]:
    """F02: Merge continuation tables across pages (same col count, no period header)."""
    if not _P["fix_F02_cross_page_concat"] or len(tables) < 2: return tables
    merged: List[List[List[str]]] = [tables[0]]
    for tbl in tables[1:]:
        prev = merged[-1]
        if not prev or not tbl: merged.append(tbl); continue
        prev_ncols = max(len(r) for r in prev)
        this_ncols = max(len(r) for r in tbl)
        # Same column count and first row of this table has no period patterns
        first_row_text = " ".join(str(c) for c in tbl[0])
        if prev_ncols == this_ncols and not _PERIOD_RE.search(first_row_text):
            merged[-1] = prev + tbl
        else:
            merged.append(tbl)
    return merged

# ── F03 — Borderless Explicit Vertical Lines ──────────────────────────────────

def fix_F03_borderless_explicit(
    pdf_path: str,
    page_no:  int,
    explicit_x: List[float],
) -> List[RawTableResult]:
    """F03: pdfplumber with explicit_vertical_lines for borderless tables."""
    results: List[RawTableResult] = []
    if not _P["fix_F03_borderless_explicit"] or not _CAP["pdfplumber"]: return results
    if not explicit_x: return results
    try:
        settings = {
            "explicit_vertical_lines": explicit_x,
            "horizontal_strategy": "text",
            "vertical_strategy":   "explicit",
            "snap_tolerance": _P["snap_tolerance"],
        }
        with pdfplumb.open(pdf_path) as pdf:
            if page_no - 1 >= len(pdf.pages): return results
            pg   = pdf.pages[page_no - 1]
            tbls = pg.extract_tables(settings) or []
            for idx, tbl in enumerate(tbls, 1):
                if not tbl or len(tbl) < _P["min_table_rows"]: continue
                results.append(RawTableResult(
                    engine="pdfplumber_F03", page_no=page_no,
                    region_id="P{:03d}TBL{:03d}".format(page_no, idx),
                    raw_data=tbl, n_rows=len(tbl),
                    n_cols=max(len(r) for r in tbl), ok=True,
                ))
    except Exception as e:
        log.debug("[MDL004] F03 page %d: %s", page_no, e)
    return results

# ── F04 — Dual-Column Page Split ──────────────────────────────────────────────

def fix_F04_dual_column_split(
    pdf_path: str,
    page_no:  int,
) -> Tuple[List[RawTableResult], List[RawTableResult]]:
    """F04: Split page at midpoint and extract left + right columns separately."""
    left_r: List[RawTableResult] = []
    right_r: List[RawTableResult] = []
    if not _P["fix_F04_dual_column_split"] or not _CAP["pdfplumber"]: return left_r, right_r
    try:
        with pdfplumb.open(pdf_path) as pdf:
            if page_no - 1 >= len(pdf.pages): return left_r, right_r
            pg = pdf.pages[page_no - 1]
            W, H = float(pg.width), float(pg.height)
            mid  = W / 2.0
            for side, bbox in [("L",(0,0,mid,H)), ("R",(mid,0,W,H))]:
                crop = pg.within_bbox(bbox)
                tbls = crop.extract_tables() or []
                for idx, tbl in enumerate(tbls, 1):
                    if not tbl or len(tbl) < _P["min_table_rows"]: continue
                    r = RawTableResult(
                        engine="pdfplumber_F04_" + side, page_no=page_no,
                        region_id="P{:03d}TBL{}_{}".format(page_no, side, idx),
                        raw_data=tbl, n_rows=len(tbl),
                        n_cols=max(len(r) for r in tbl), ok=True,
                    )
                    (left_r if side == "L" else right_r).append(r)
    except Exception as e:
        log.debug("[MDL004] F04 page %d: %s", page_no, e)
    return left_r, right_r

# ── F05 — Nested Table snap_tolerance ─────────────────────────────────────────

def fix_F05_nested_table(raw_data: List[List[str]], snap: int = 1) -> List[List[str]]:
    """F05: Re-run with tighter snap_tolerance for nested sub-tables (stub — triggers re-extract)."""
    # Actual re-extract done in caller with snap_tolerance=snap
    return raw_data   # pass-through; real effect is in engine call

# ── F06 — Row-span Forward Fill ───────────────────────────────────────────────

def fix_F06_rowspan_ffill(raw_data: List[List[str]]) -> Tuple[List[List[str]], bool]:
    """F06: Replace None / empty cells with value from cell above (vertical merge fix)."""
    if not _P["fix_F06_rowspan_ffill"]: return raw_data, False
    if not _CAP["pandas"]: return raw_data, False
    try:
        df = pd.DataFrame(raw_data).replace("", None).ffill(axis=0)
        result = df.fillna("").values.tolist()
        result = [[str(c) for c in row] for row in result]
        return result, True
    except Exception: return raw_data, False

# ── F07 — Col-span Forward Fill ───────────────────────────────────────────────

def fix_F07_colspan_ffill(raw_data: List[List[str]]) -> Tuple[List[List[str]], bool]:
    """F07: Replace None / empty cells with value from cell to the left (horizontal merge)."""
    if not _P["fix_F07_colspan_ffill"]: return raw_data, False
    if not _CAP["pandas"]: return raw_data, False
    try:
        df = pd.DataFrame(raw_data).replace("", None).ffill(axis=1)
        result = df.fillna("").values.tolist()
        result = [[str(c) for c in row] for row in result]
        return result, True
    except Exception: return raw_data, False

# ── F08 — Text-wrap Continuation Merge ────────────────────────────────────────

def fix_F08_text_wrap_merge(raw_data: List[List[str]]) -> Tuple[List[List[str]], bool]:
    """F08: Merge rows where continuation line has far fewer non-empty cells than header."""
    if not _P["fix_F08_text_wrap_merge"] or len(raw_data) < 2: return raw_data, False
    if not raw_data[0]: return raw_data, False
    header_ncols = sum(1 for c in raw_data[0] if str(c).strip())
    threshold    = max(1, header_ncols // 2)
    merged = [raw_data[0]]
    applied = False
    for row in raw_data[1:]:
        non_empty = sum(1 for c in row if str(c or "").strip())
        if non_empty <= threshold and merged:
            # Append text to last row's first cell
            merged[-1] = list(merged[-1])
            merged[-1][0] = str(merged[-1][0] or "").strip() + " " + str(row[0] or "").strip()
            applied = True
        else:
            merged.append(row)
    return merged, applied

# ── F09 — Text-center Alignment ───────────────────────────────────────────────

def fix_F09_text_center_align(raw_data: List[List[str]]) -> List[List[str]]:
    """F09: Normalize alignment by stripping and trimming each cell.
    Real re-alignment handled by pdfplumber with horizontal_strategy='text' in engine call."""
    return [[str(c or "").strip() for c in row] for row in raw_data]

# ── F10 — Empty Row Drop ──────────────────────────────────────────────────────

def fix_F10_empty_row_drop(raw_data: List[List[str]]) -> Tuple[List[List[str]], bool]:
    """F10: Remove rows that are entirely empty or None."""
    if not _P["fix_F10_empty_row_drop"]: return raw_data, False
    cleaned = [row for row in raw_data if any(str(c or "").strip() for c in row)]
    return cleaned, len(cleaned) < len(raw_data)

# ── F11 — CJK Space Remove ────────────────────────────────────────────────────

def fix_F11_zh_space(text: str) -> str:
    """F11: Remove improper spaces between CJK characters."""
    if not _P["fix_F11_zh_space"]: return text
    return _ZH_SP_RE.sub("", text.strip())

# ── F12 — OCR Alpha-Numeric Fix ───────────────────────────────────────────────

def fix_F12_ocr_alphanum(text: str) -> str:
    """F12: l→1, O→0, I→1 when adjacent to digits."""
    if not _P["fix_F12_ocr_alphanum"]: return text
    def _repl(m):
        ch = (m.group(1) or m.group(2) or "")
        return "1" if ch in ("l","I","|") else "0"
    return _OCR_NUM_RE.sub(_repl, text)

# ── F13 — Trim + NBSP ─────────────────────────────────────────────────────────

def fix_F13_trim_nbsp(text: str) -> str:
    """F13: Strip whitespace + replace non-breaking spaces."""
    if not _P["fix_F13_trim_nbsp"]: return text
    return text.replace("\u00a0"," ").replace("\u3000"," ").replace("\n"," ").strip()

# ── F14 — Currency Bracket to Negative ────────────────────────────────────────

def fix_F14_currency_bracket(text: str) -> str:
    """F14: (1,234) → -1234; $1,000 → 1000."""
    if not _P["fix_F14_currency_bracket"]: return text
    t = text.strip().replace("$","").replace("NT$","").replace("，",",")
    m = _BRACKET_RE.match(t)
    if m: t = "-" + m.group(1)
    return t

# ── F15 — Mojibake OCR Fallback ───────────────────────────────────────────────

def fix_F15_mojibake_ocr(text: str) -> str:
    """F15: Detect encoding failure patterns and flag for OCR re-read."""
    # If text is mostly non-printable or looks like mojibake → mark
    junk_ratio = sum(1 for c in text if ord(c) < 32 or (0x80 <= ord(c) <= 0x9F)) / max(len(text),1)
    if junk_ratio > 0.3: return "[OCR_RETRY]"
    return text

# ── F16 — Header Shift Re-detection ──────────────────────────────────────────

def fix_F16_header_shift(raw_data: List[List[str]]) -> Tuple[List[List[str]], int, bool]:
    """F16: Find real header row (first row with period patterns), drop rows before it.
    Returns (fixed_data, new_header_idx, applied)."""
    if not _P["fix_F16_header_shift"]: return raw_data, 0, False
    real_idx = find_real_header_row(raw_data)
    if real_idx == 0: return raw_data, 0, False
    return raw_data[real_idx:], real_idx, True

# ── F17 — Sum Verification ────────────────────────────────────────────────────

def fix_F17_sum_verify(
    rows:  List[Dict],
    total_label_hint: str = "total",
) -> Dict:
    """F17: Verify that sub-rows sum to total row within tolerance.
    Returns {pass: bool, mismatches: list}."""
    if not _P["fix_F17_sum_verify"]: return {"pass": True, "mismatches": []}
    # Find rows that look like totals
    total_rows = [r for r in rows if total_label_hint.lower() in str(r.get("label_raw","")).lower()]
    if not total_rows: return {"pass": True, "mismatches": []}
    mismatches = []
    tol = _P["sum_verify_tolerance"]
    for tr in total_rows:
        for period, total_val in (tr.get("values") or {}).items():
            if total_val is None: continue
            sub_sum = sum(
                (r.get("values") or {}).get(period, 0) or 0
                for r in rows
                if r is not tr and (r.get("values") or {}).get(period) is not None
            )
            if sub_sum > 0:
                diff = abs(total_val - sub_sum) / max(abs(sub_sum), 1)
                if diff > tol:
                    mismatches.append({"period":period,"total":total_val,"sub_sum":round(sub_sum,2),"diff_pct":round(diff*100,2)})
    return {"pass": len(mismatches)==0, "mismatches": mismatches}

# ── F18 — Dtype Note Spill Detection ─────────────────────────────────────────

def fix_F18_dtype_note_spill(cells: List[str], expected_type: str = "numeric") -> List[str]:
    """F18: Detect non-numeric text spilling into numeric columns; replace with empty."""
    if not _P["fix_F18_dtype_note_spill"]: return cells
    if expected_type != "numeric": return cells
    fixed = []
    for c in cells:
        v = str(c or "").strip()
        # If it looks like a note / text, not a number
        if v and _clean_number(v) is None and not v.startswith("["):
            # Check if it's clearly textual (has CJK or long alphabetic)
            if re.search(r"[\u4e00-\u9fa5]{2,}|[A-Za-z]{4,}", v):
                fixed.append("[NOTE]")
                continue
        fixed.append(c)
    return fixed

# ── F19 — Watermark / Light-color Filter ─────────────────────────────────────

def fix_F19_watermark_filter(
    page_obj: Any,
    char_dicts: List[Dict],
) -> List[Dict]:
    """F19: Remove characters with very light RGB or very small fontsize (watermarks)."""
    if not _P["fix_F19_watermark_filter"]: return char_dicts
    clean = []
    rgb_min  = _P["watermark_rgb_min"]
    size_max = _P["watermark_fontsize_max"]
    for ch in char_dicts:
        size  = ch.get("size", 99.0)
        color = ch.get("non_stroking_color", None)
        if size <= size_max: continue
        if color and isinstance(color, (list, tuple)) and len(color) == 3:
            if all(c >= rgb_min for c in color): continue
        clean.append(ch)
    return clean

# ── F20 — Column Shift Repair ─────────────────────────────────────────────────

def fix_F20_col_shift_repair(
    raw_data: List[List[str]],
    expected_ncols: Optional[int] = None,
) -> Tuple[List[List[str]], bool]:
    """F20: If a row has more cells than expected, try merging extra cells back into previous cell."""
    if not _P["fix_F20_col_shift_repair"]: return raw_data, False
    if not raw_data: return raw_data, False
    n_cols = expected_ncols or max(len(r) for r in raw_data[:3])
    fixed = []
    applied = False
    for row in raw_data:
        if len(row) > n_cols:
            # Merge overflow cells into last expected cell
            base  = list(row[:n_cols])
            extra = " ".join(str(c) for c in row[n_cols:] if str(c or "").strip())
            if extra:
                base[-1] = str(base[-1] or "") + " " + extra
            fixed.append(base)
            applied = True
        elif len(row) < n_cols:
            # Pad with empty strings
            fixed.append(list(row) + [""] * (n_cols - len(row)))
        else:
            fixed.append(list(row))
    return fixed, applied

# ============================================================================
# APPLY ALL FIXES — orchestrator
# ============================================================================

def apply_fixes(
    raw: RawTableResult,
    pdf_path: str,
) -> Tuple[List[List[str]], List[str]]:
    """VRN-MDL004-FNC-014
    Apply F01–F20 in sequence to raw_data.
    Returns (fixed_data, [list of applied fix codes]).
    """
    data     = raw.raw_data
    applied  = []

    # F01 context (already done at engine call — mark if present)
    if raw.header_context:
        applied.append("F01")

    # F10 — empty rows first (reduces noise before other fixes)
    data, ok = fix_F10_empty_row_drop(data)
    if ok: applied.append("F10")

    # F16 — header re-detection
    data, shift_idx, ok = fix_F16_header_shift(data)
    if ok: applied.append("F16")

    # F06 — rowspan (vertical merge)
    data, ok = fix_F06_rowspan_ffill(data)
    if ok: applied.append("F06")

    # F07 — colspan (horizontal merge)
    data, ok = fix_F07_colspan_ffill(data)
    if ok: applied.append("F07")

    # F08 — text-wrap continuation
    data, ok = fix_F08_text_wrap_merge(data)
    if ok: applied.append("F08")

    # F20 — col shift
    data, ok = fix_F20_col_shift_repair(data)
    if ok: applied.append("F20")

    # F09 — alignment
    data = fix_F09_text_center_align(data)

    # Per-cell text fixes (F11/F12/F13/F14/F15/F19)
    def _fix_cell(c: str) -> str:
        c = fix_F13_trim_nbsp(str(c or ""))
        c = fix_F11_zh_space(c)
        c = fix_F14_currency_bracket(c)
        c = fix_F12_ocr_alphanum(c)
        c = fix_F15_mojibake_ocr(c)
        return c

    data = [[_fix_cell(c) for c in row] for row in data]
    for code in ("F11","F12","F13","F14","F15"):
        if _P.get("fix_" + code): applied.append(code)

    return data, applied

# ============================================================================
# [VRN:ANCHOR:MDL004-SCHEMA-001] §16  PYDANTIC SCHEMA VALIDATOR
# ── Standalone: call validate_table_rows(rows) anywhere ─────────────────────
# ============================================================================

def validate_table_rows(
    rows:    List[Dict],
    strict:  bool = False,
) -> Tuple[List[Dict], int, int]:
    """VRN-MDL004-FNC-015
    Validate each row dict {label, values} through Pydantic TableRow.
    Tags each row with status: PASS | WARN | ERR.
    Returns (validated_rows, n_pass, n_err).
    """
    if _TableRow is None:
        # No pydantic — basic fallback
        for r in rows: r["status"] = "PASS"
        return rows, len(rows), 0

    validated = []
    n_pass = n_err = 0
    for r in rows:
        try:
            vr = _TableRow(label=r.get("label_raw",""), values=r.get("values",{}))
            r  = dict(r, label_validated=vr.label, values_validated=vr.values, status="PASS")
            n_pass += 1
        except Exception as e:
            r = dict(r, status="ERR", validation_error=str(e)[:120])
            n_err += 1
            if strict: log.debug("[MDL004] schema ERR: %s", e)
        validated.append(r)
    return validated, n_pass, n_err

# ============================================================================
# [VRN:ANCHOR:MDL004-EXTERNAL-001] §17  EXTERNAL SSOT INTEGRATION
# ============================================================================


def _cel_submit(fn: Callable, *args, **kw) -> Any:
    """VRN-MDL004-FNC-PROXY-001  Celeritas parallel submit, fallback direct call.
    Used everywhere we want to push work onto Celeritas warm thread pool."""
    if _CEL_OK:
        if hasattr(_CEL, "_LazyPool"):
            try: return _CEL._LazyPool.submit(fn, *args, **kw)
            except Exception: pass
        if hasattr(_CEL, "submit"):
            try: return _CEL.submit(fn, *args, **kw)
            except Exception: pass
    return fn(*args, **kw)

def _cel_map(fn: Callable, items: Iterable, **kw) -> List:
    """VRN-MDL004-FNC-PROXY-002  Celeritas parallel map, fallback list(map(...))."""
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
    """VRN-MDL004-FNC-PROXY-003  Celeritas thread_budget, fallback cpu_count-1."""
    if _CEL_OK and hasattr(_CEL, "thread_budget"):
        try: return _CEL.thread_budget(mode=mode)
        except Exception: pass
    return max(1, (os.cpu_count() or 4) - 1)

def _cel_capability_report() -> Dict:
    """VRN-MDL004-FNC-PROXY-004  Celeritas capability_report, fallback empty."""
    if _CEL_OK and hasattr(_CEL, "capability_report"):
        try: return _CEL.capability_report()
        except Exception: pass
    return {}

def _cel_accelerated_concat(frames, prefer="polars"):
    """VRN-MDL004-FNC-PROXY-005  Celeritas accelerated_concat, fallback pandas concat."""
    if _CEL_OK and hasattr(_CEL, "accelerated_concat"):
        try: return _CEL.accelerated_concat(frames, prefer=prefer)
        except Exception: pass
    if pd is not None:
        try: return pd.concat(frames, ignore_index=True)
        except Exception: pass
    return frames[0] if frames else None

def _ssot_get(key: str, default: Any = None) -> Any:
    """VRN-MDL004-FNC-PROXY-006  VIA_SSOT_Unified .get(), fallback default."""
    if _SSOT_OK and hasattr(_SSOT, "get"):
        try: return _SSOT.get(key, default)
        except Exception: pass
    return default

def _ssot_normalize_term(text: str) -> str:
    """VRN-MDL004-FNC-PROXY-007  Map term via SSOT canonical, fallback identity.
    Bypasses module-level normalize() stub by using SSOT() class instance directly."""
    if not text: return text
    t = text.strip()
    if _SSOT_OK and hasattr(_SSOT, "SSOT"):
        try:
            inst = _SSOT.SSOT()
            got = inst.normalize(t)
            if got and got != t: return got
        except Exception: pass
    return t

def _net_get(url: str, timeout: int = 20, **kw) -> Optional[Any]:
    """VRN-MDL004-FNC-PROXY-008  AegisNexus HTTP GET, fallback requests."""
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
# [VRN:ANCHOR:MDL004-OCRPLUGINS-PROXY-001]  OCR_Plugins (D4 ADAPTER) PROXIES
# ── These are the ONLY entry points to the OCR_Plugins companion module.    ─
# ── If OCR_Plugins not loaded, returns empty/safe-default per its own       ─
# ── ERROR_POLICY: RETURN_SAFE_DEFAULT.                                       ─
# ============================================================================

def _ocr_plugins_route(pdf_path: str,
                       pdf_type:     str  = "auto",
                       content_hint: str  = "mixed",
                       lang:         str  = "auto",
                       config:       Optional[Dict] = None) -> Dict:
    """VRN-MDL004-FNC-PROXY-009  Call OCR_Plugins.route_ocr_engine() via Celeritas.
    Returns standardized layout blocks (see OCR_Plugins OUTPUT_SCHEMA)."""
    if not _OCR_PLUGINS_OK or not hasattr(_OCR_PLUGINS, "route_ocr_engine"):
        return {"ok": False, "engine_used": "none", "pages": [],
                "error": "OCR_Plugins not loaded"}
    try:
        # Push OCR routing onto Celeritas warm pool when available
        fut = _cel_submit(_OCR_PLUGINS.route_ocr_engine,
                          pdf_path, pdf_type, content_hint, lang, config)
        return fut.result() if hasattr(fut, "result") else fut
    except Exception as e:
        log.debug("[MDL004] _ocr_plugins_route fail: %s", e)
        return {"ok": False, "engine_used": "error", "pages": [], "error": str(e)}

def _ocr_plugins_extract_tables(pdf_path:   str,
                                pdf_type:   str = "auto",
                                output_dir: Optional[str] = None,
                                config:     Optional[Dict] = None) -> Dict:
    """VRN-MDL004-FNC-PROXY-010  Call OCR_Plugins.extract_tables_from_pdf() via Celeritas.
    Returns standardized table_records (see OCR_Plugins OUTPUT_SCHEMA)."""
    if not _OCR_PLUGINS_OK or not hasattr(_OCR_PLUGINS, "extract_tables_from_pdf"):
        return {"ok": False, "engine_used": "none", "table_records": [],
                "total_tables": 0, "error": "OCR_Plugins not loaded"}
    try:
        fut = _cel_submit(_OCR_PLUGINS.extract_tables_from_pdf,
                          pdf_path, pdf_type, output_dir, config)
        return fut.result() if hasattr(fut, "result") else fut
    except Exception as e:
        log.debug("[MDL004] _ocr_plugins_extract_tables fail: %s", e)
        return {"ok": False, "engine_used": "error", "table_records": [],
                "total_tables": 0, "error": str(e)}

def _ocr_plugins_table_records_to_raw(rec_list: List[Dict], page_no_default: int = 0) -> List[RawTableResult]:
    """VRN-MDL004-FNC-PROXY-011  Convert OCR_Plugins table_records → RawTableResult list.
    Bridge function so OCR_Plugins output flows into the standard MDL004 vote/fix pipeline.

    OCR_Plugins table_record keys (per OUTPUT_SCHEMA):
        table_id, page_no, bbox, html, csv_rows, csv_path, crop_path
    """
    out: List[RawTableResult] = []
    for rec in rec_list or []:
        if not isinstance(rec, dict): continue
        rows: List[List[str]] = rec.get("csv_rows") or []
        if not rows or len(rows) < _P["min_table_rows"]: continue
        n_cols = max((len(r) for r in rows), default=0)
        if n_cols < _P["min_table_cols"]: continue
        page_no = int(rec.get("page_no") or page_no_default or 0)
        out.append(RawTableResult(
            engine     = "ocr_plugins:" + str(rec.get("engine_used", "auto")),
            page_no    = page_no,
            region_id  = str(rec.get("table_id") or
                              "P{:03d}TBL_OCRP_{}".format(page_no, len(out)+1)),
            bbox       = list(rec.get("bbox") or []),
            raw_data   = [[str(c) for c in row] for row in rows],
            n_rows     = len(rows),
            n_cols     = n_cols,
            ok         = True,
        ))
    return out

# ============================================================================
# [VRN:ANCHOR:MDL004-PLUGIN-LOADER-001] §17.6  7-TOOL PLUGIN LOADER + OCR_PLUGINS
# ── Loads all 7 supportive tools per VIA_Supportive_HardGate_Seal.json,      ─
# ── plus the D4 OCR_Plugins companion module (separate path search).         ─
# ── Pattern matches MDL005 / MDL007 / MDL008 (canonical reference style).   ─
# ── Uses spec_from_file_location + sys.modules-inject-before-exec for Py3.12 ─
# ============================================================================

def load_external_ssot(ssot_dir: str) -> Dict[str, bool]:
    """VRN-MDL004-FNC-016  Load 7 supportive tools per HardGate Seal + OCR_Plugins.
    Policy: BOOT_PRECHECK_ONLY_NO_NETWORK_NO_PARALLEL_NO_AUTOPATCH.
    Returns capability dict (8 keys: 7 supportive + ocr_plugins).
    """
    global _SSOT, _SSOT_OK, _CEL, _CEL_OK, _NET, _NET_OK
    global _REG, _REG_OK, _BRG, _BRG_OK, _ENV, _ENV_OK, _AST, _AST_OK
    global _OCR_PLUGINS, _OCR_PLUGINS_OK

    # [VRN:ANCHOR:HARDGATE_RESULT:V1] 7-key result dict per HardGate Seal + ocr_plugins
    result = {"via_ssot": False, "registry": False, "runtime_bridge": False,
              "env_manager": False, "ast_planner": False,
              "celeritas": False, "aegis": False,
              "ocr_plugins": False}

    ssot_path = Path(ssot_dir)
    if ssot_path.is_dir():
        ssot_str = str(ssot_path)
        if ssot_str not in sys.path:
            sys.path.insert(0, ssot_str)

    import importlib.util as _ilu

    def _load_one(mod_name: str, finder=_find_plugin) -> Optional[Any]:
        """Load one module by spec_from_file_location, inject sys.modules first.
        finder defaults to _find_plugin (supportive_module dir search), but
        OCR_Plugins uses _find_companion (MDL004 sibling dir search)."""
        p = finder(ssot_dir, f"{mod_name}.py") if finder is _find_plugin else finder(f"{mod_name}.py")
        if not p: return None
        try:
            spec = _ilu.spec_from_file_location(mod_name, p)
            mod  = _ilu.module_from_spec(spec)
            sys.modules[mod_name] = mod   # inject BEFORE exec (Python 3.12 dataclass fix)
            spec.loader.exec_module(mod)
            log.info("[MDL004] %s loaded from %s", mod_name, p)
            return mod
        except Exception as e:
            log.debug("[MDL004] %s load fail: %s", mod_name, e)
            return None

    # ── 1. VIA_SSOT_Unified ─────────────────────────────────────────────────
    mod = _load_one("VIA_SSOT_Unified")
    if mod is not None:
        _SSOT = mod; _SSOT_OK = True; result["via_ssot"] = True

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

    # ── 8. VRN_MDL004_OCR_Plugins_v1 (D4 ADAPTER companion, NOT supportive) ─
    # Append-only protected (VIA_AI_APPEND_ONLY_POLICY_V3) — load only, don't modify.
    mod = _load_one("VRN_MDL004_OCR_Plugins_v1", finder=_find_companion)
    if mod is not None:
        _OCR_PLUGINS = mod; _OCR_PLUGINS_OK = True; result["ocr_plugins"] = True

    return result

# ============================================================================
# [VRN:ANCHOR:MDL004-DB-001] §18  DB WRITER
# ============================================================================

class MDL004DBWriter:
    """VRN-MDL004-CLS-002  SQLite WAL writer."""

    DDL = """
CREATE TABLE IF NOT EXISTS vrn_mdl004_tables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    region_id TEXT, pdf_name TEXT, report_code TEXT,
    page_no INTEGER, region_type TEXT, quadrant TEXT,
    engine_used TEXT, label_raw TEXT, canonical TEXT,
    period TEXT, value REAL, status TEXT,
    fixes_applied TEXT, confidence REAL,
    ts TEXT DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS vrn_mdl004_fix_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    region_id TEXT, pdf_name TEXT, fix_code TEXT, detail TEXT,
    ts TEXT DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS vrn_mdl004_schema_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    region_id TEXT, pdf_name TEXT, row_label TEXT,
    status TEXT, error TEXT,
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

    def insert_table_rows(self, ft: FixedTable):
        sql = """INSERT INTO vrn_mdl004_tables
                 (region_id,pdf_name,report_code,page_no,region_type,quadrant,
                  engine_used,label_raw,canonical,period,value,status,fixes_applied,confidence)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
        fixes_str = ",".join(ft.fixes_applied)
        rows_flat = []
        for row in ft.rows:
            for period, val in (row.get("values") or {}).items():
                rows_flat.append((
                    ft.region_id, ft.pdf_name, ft.report_code,
                    ft.page_no, ft.region_type, ft.quadrant,
                    ft.engine_used,
                    row.get("label_raw",""), row.get("canonical",""),
                    period, val if isinstance(val, float) else None,
                    row.get("status","PASS"), fixes_str, ft.confidence,
                ))
        with self._lock:
            self._con.executemany(sql, rows_flat)
            self._con.commit()

    def insert_fix_log(self, region_id: str, pdf_name: str, fix_code: str, detail: str = ""):
        with self._lock:
            self._con.execute(
                "INSERT INTO vrn_mdl004_fix_log (region_id,pdf_name,fix_code,detail) VALUES (?,?,?,?)",
                (region_id, pdf_name, fix_code, detail[:500])
            )
            self._con.commit()

    def insert_schema_log(self, region_id: str, pdf_name: str, label: str, status: str, error: str=""):
        with self._lock:
            self._con.execute(
                "INSERT INTO vrn_mdl004_schema_log (region_id,pdf_name,row_label,status,error) VALUES (?,?,?,?,?)",
                (region_id, pdf_name, label, status, error[:300])
            )
            self._con.commit()

    def export_parquet(self, out_dir: str):
        if not _CAP["pandas"] or not _CAP["pyarrow"]: return
        try:
            df = pd.read_sql("SELECT * FROM vrn_mdl004_tables", self._con)
            df.to_parquet(str(Path(out_dir) / "VRN_MDL004_Tables.parquet"), index=False)
        except Exception as e: log.warning("[MDL004] parquet: %s", e)

    def export_csv(self, out_dir: str):
        if not _CAP["pandas"]: return
        try:
            df = pd.read_sql("SELECT * FROM vrn_mdl004_tables", self._con)
            df.to_csv(str(Path(out_dir) / "VRN_MDL004_Tables.csv"), index=False, encoding="utf-8-sig")
        except Exception as e: log.warning("[MDL004] csv: %s", e)

# ============================================================================
# [VRN:ANCHOR:MDL004-BATCH-001] §18.5  P3 BATCH BUFFER + DUCK WRITER (v1.1.0)
# ── 同 MDL003 v1.1.0 模式：worker push (低鎖)，主執行緒一次 flush      ────
# ============================================================================

class MDL004BatchBuffer:
    """VRN-MDL004-CLS-007  P3 batch buffer (NEW v1.1.0).
    Workers push into 3 lists; lock granularity = list.extend.
    Main thread calls consume_all() + DuckWriter.flush() AFTER pool closes.
    """
    def __init__(self, batch_size: int = 5000):
        self.batch_size = batch_size
        self._tbl_buf:    List[Tuple] = []
        self._fix_buf:    List[Tuple] = []
        self._schema_buf: List[Tuple] = []
        self._lock = threading.Lock()

    def push_table(self, ft: "FixedTable"):
        if not ft.rows: return
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        fixes_str = ",".join(ft.fixes_applied)
        rows = []
        for row in ft.rows:
            for period, val in (row.get("values") or {}).items():
                rows.append((
                    None,  # id auto
                    ft.region_id, ft.pdf_name, ft.report_code,
                    ft.page_no, ft.region_type, ft.quadrant,
                    ft.engine_used,
                    row.get("label_raw",""), row.get("canonical",""),
                    period,
                    val if isinstance(val,(int,float)) else None,
                    row.get("status","PASS"), fixes_str, ft.confidence, ts,
                ))
        with self._lock:
            self._tbl_buf.extend(rows)

    def push_fix_log(self, region_id: str, pdf_name: str, fix_code: str, detail: str = ""):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            self._fix_buf.append((None, region_id, pdf_name, fix_code, detail[:500], ts))

    def push_schema_log(self, region_id: str, pdf_name: str, label: str,
                        status: str, error: str = ""):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        with self._lock:
            self._schema_buf.append((None, region_id, pdf_name, label,
                                     status, error[:300], ts))

    def stats(self) -> Dict[str, int]:
        return {"tbl": len(self._tbl_buf),
                "fix": len(self._fix_buf),
                "schema": len(self._schema_buf)}

    def consume_all(self) -> Tuple[List, List, List]:
        with self._lock:
            t, f, s = self._tbl_buf, self._fix_buf, self._schema_buf
            self._tbl_buf, self._fix_buf, self._schema_buf = [], [], []
        return t, f, s


_DDL_DUCK_TABLES = """
CREATE TABLE IF NOT EXISTS vrn_mdl004_tables (
    id INTEGER, region_id VARCHAR, pdf_name VARCHAR, report_code VARCHAR,
    page_no INTEGER, region_type VARCHAR, quadrant VARCHAR,
    engine_used VARCHAR, label_raw VARCHAR, canonical VARCHAR,
    period VARCHAR, value DOUBLE, status VARCHAR,
    fixes_applied VARCHAR, confidence DOUBLE, ts VARCHAR
);
"""
_DDL_DUCK_FIX = """
CREATE TABLE IF NOT EXISTS vrn_mdl004_fix_log (
    id INTEGER, region_id VARCHAR, pdf_name VARCHAR,
    fix_code VARCHAR, detail VARCHAR, ts VARCHAR
);
"""
_DDL_DUCK_SCHEMA = """
CREATE TABLE IF NOT EXISTS vrn_mdl004_schema_log (
    id INTEGER, region_id VARCHAR, pdf_name VARCHAR,
    row_label VARCHAR, status VARCHAR, error VARCHAR, ts VARCHAR
);
"""


class MDL004DuckWriter:
    """VRN-MDL004-CLS-008  DuckDB primary writer (NEW v1.1.0)."""
    def __init__(self, db_path: str):
        if not DUCKDB_OK:
            raise RuntimeError("duckdb not available")
        self.db_path = db_path
        self._con = duckdb_lib.connect(db_path)
        self._con.execute(_DDL_DUCK_TABLES)
        self._con.execute(_DDL_DUCK_FIX)
        self._con.execute(_DDL_DUCK_SCHEMA)

    def flush(self, tbl_rows: List, fix_rows: List, schema_rows: List) -> Dict[str, int]:
        n_t = n_f = n_s = 0
        try:
            self._con.execute("BEGIN TRANSACTION")
            if tbl_rows:
                self._con.executemany(
                    "INSERT INTO vrn_mdl004_tables VALUES "
                    "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    tbl_rows)
                n_t = len(tbl_rows)
            if fix_rows:
                self._con.executemany(
                    "INSERT INTO vrn_mdl004_fix_log VALUES (?,?,?,?,?,?)",
                    fix_rows)
                n_f = len(fix_rows)
            if schema_rows:
                self._con.executemany(
                    "INSERT INTO vrn_mdl004_schema_log VALUES (?,?,?,?,?,?,?)",
                    schema_rows)
                n_s = len(schema_rows)
            self._con.execute("COMMIT")
        except Exception as e:
            try: self._con.execute("ROLLBACK")
            except: pass
            log.error("[MDL004] DuckDB flush fail: %s", e); raise
        return {"tbl": n_t, "fix": n_f, "schema": n_s}

    def export_parquet_polars(self, out_dir: str) -> Optional[str]:
        out_path = str(Path(out_dir) / "VRN_MDL004_Tables.parquet")
        try:
            self._con.execute(
                f"COPY (SELECT * FROM vrn_mdl004_tables) "
                f"TO '{out_path}' (FORMAT PARQUET, COMPRESSION ZSTD)"
            )
            return out_path
        except Exception as e:
            log.warning("[MDL004] DuckDB→parquet fail: %s", e); return None

    def export_csv_polars(self, out_dir: str) -> Optional[str]:
        """v1.1.0 fix learnt from MDL003: avoid pyarrow dependency."""
        out_path = str(Path(out_dir) / "VRN_MDL004_Tables.csv")
        if POLARS_OK:
            try:
                rows = self._con.execute("SELECT * FROM vrn_mdl004_tables").fetchall()
                cols = [d[0] for d in self._con.description]
                if rows:
                    df = pl.DataFrame(rows, schema=cols, orient="row")
                    csv_text = df.write_csv()
                    Path(out_path).write_bytes(b"\xef\xbb\xbf" + csv_text.encode("utf-8"))
                else:
                    Path(out_path).write_bytes(
                        b"\xef\xbb\xbf" + (",".join(cols) + "\n").encode("utf-8"))
                return out_path
            except Exception as e:
                log.debug("[MDL004] polars-fetchall csv fail (%s), try DuckDB native", e)
        try:
            self._con.execute(
                f"COPY (SELECT * FROM vrn_mdl004_tables) "
                f"TO '{out_path}' (HEADER, DELIMITER ',')")
            data = Path(out_path).read_bytes()
            Path(out_path).write_bytes(b"\xef\xbb\xbf" + data)
            return out_path
        except Exception as e:
            log.warning("[MDL004] csv export fail: %s", e); return None

    def close(self):
        try: self._con.close()
        except: pass


# ── Add v1.1.0 batch flush to legacy DBWriter for sqlite fallback ───────────
def _mdl004_dbwriter_flush(self,
                           tbl_rows: List, fix_rows: List, schema_rows: List
                           ) -> Dict[str, int]:
    """SQLite batch flush — same shape as DuckWriter.flush()."""
    n_t = n_f = n_s = 0
    with self._lock:
        try:
            self._con.execute("BEGIN")
            if tbl_rows:
                # Strip id placeholder + ts (sqlite has DEFAULT for ts)
                self._con.executemany(
                    "INSERT INTO vrn_mdl004_tables "
                    "(region_id,pdf_name,report_code,page_no,region_type,quadrant,"
                    " engine_used,label_raw,canonical,period,value,status,"
                    " fixes_applied,confidence) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    [r[1:-1] for r in tbl_rows]   # drop id (front) + ts (back)
                ); n_t = len(tbl_rows)
            if fix_rows:
                self._con.executemany(
                    "INSERT INTO vrn_mdl004_fix_log (region_id,pdf_name,fix_code,detail) "
                    "VALUES (?,?,?,?)",
                    [r[1:-1] for r in fix_rows])
                n_f = len(fix_rows)
            if schema_rows:
                self._con.executemany(
                    "INSERT INTO vrn_mdl004_schema_log (region_id,pdf_name,row_label,status,error) "
                    "VALUES (?,?,?,?,?)",
                    [r[1:-1] for r in schema_rows])
                n_s = len(schema_rows)
            self._con.commit()
        except Exception as e:
            try: self._con.rollback()
            except: pass
            log.error("[MDL004] sqlite flush fail: %s", e); raise
    return {"tbl": n_t, "fix": n_f, "schema": n_s}

# Monkey-patch: attach flush method to the existing class (append-only)
MDL004DBWriter.flush = _mdl004_dbwriter_flush


def _mdl004_dbwriter_export_parquet_polars(self, out_dir: str) -> Optional[str]:
    out_path = str(Path(out_dir) / "VRN_MDL004_Tables.parquet")
    if not POLARS_OK:
        self.export_parquet(out_dir)
        return out_path if Path(out_path).exists() else None
    try:
        with self._lock:
            cur = self._con.execute("SELECT * FROM vrn_mdl004_tables")
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description] if cur.description else []
        if not rows:
            df = pl.DataFrame(schema={c: pl.Utf8 for c in cols} if cols else None)
        else:
            df = pl.DataFrame(rows, schema=cols, orient="row")
        df.write_parquet(out_path, compression="zstd")
        return out_path
    except Exception as e:
        log.warning("[MDL004] polars→parquet fail (%s), fallback pandas", e)
        self.export_parquet(out_dir)
        return out_path if Path(out_path).exists() else None

def _mdl004_dbwriter_export_csv_polars(self, out_dir: str) -> Optional[str]:
    out_path = str(Path(out_dir) / "VRN_MDL004_Tables.csv")
    if not POLARS_OK:
        self.export_csv(out_dir)
        return out_path if Path(out_path).exists() else None
    try:
        with self._lock:
            cur = self._con.execute("SELECT * FROM vrn_mdl004_tables")
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description] if cur.description else []
        if rows and cols:
            df = pl.DataFrame(rows, schema=cols, orient="row")
            csv_text = df.write_csv()
            Path(out_path).write_bytes(b"\xef\xbb\xbf" + csv_text.encode("utf-8"))
        else:
            Path(out_path).write_bytes(
                b"\xef\xbb\xbf" + (",".join(cols) + "\n").encode("utf-8"))
        return out_path
    except Exception as e:
        log.debug("[MDL004] polars-fetchall csv fail (%s), fallback pandas", e)
        self.export_csv(out_dir)
        return out_path if Path(out_path).exists() else None

MDL004DBWriter.export_parquet_polars = _mdl004_dbwriter_export_parquet_polars
MDL004DBWriter.export_csv_polars     = _mdl004_dbwriter_export_csv_polars


# ============================================================================
# [VRN:ANCHOR:MDL004-SELFCHK-001] §18.7  P6 4-PHASE SELF-VERIFICATION (v1.1.0)
# ============================================================================

class MDL004SelfVerifier:
    """VRN-MDL004-CLS-009  P6 4-phase debug chain (NEW v1.1.0).
    Phase 1: Schema & Imports / Phase 2: DocCache wiring /
    Phase 3: DB Persistence    / Phase 4: Output Files + Data Integrity
    READY = 0 fail / NEAR-READY = 1-2 / NOT-READY = 3+
    """
    def __init__(self, cfg: Dict, run_summary: Dict, mdl004_temp: str):
        self.cfg = cfg; self.run_summary = run_summary
        self.mdl004_temp = mdl004_temp
        self.checks: List[Dict] = []

    def _add(self, phase: str, name: str, ok: bool, detail: str = ""):
        self.checks.append({"phase":phase,"name":name,"ok":bool(ok),"detail":detail})

    def run(self) -> Dict:
        # Phase 1
        self._add("1/4", "Module version 1.1.0", __version__ == "1.1.0", __version__)
        self._add("1/4", "TW_TICKER_REGEX locked",
                  TW_TICKER_REGEX.pattern == r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})",
                  TW_TICKER_REGEX.pattern[:40])
        self._add("1/4", "Pre-compiled regex pool",
                  all(p is not None for p in [_RE_BRACKET_NEG, _RE_OCR_O_TO_0,
                                              _RE_OCR_l_TO_1, _RE_NORM_PUNCT,
                                              _RE_DOUBLESPACE, _RE_MOJIBAKE]),
                  "P4 regex pool")
        self._add("1/4", "polars available", POLARS_OK, str(POLARS_OK))
        self._add("1/4", "duckdb available", DUCKDB_OK, str(DUCKDB_OK))

        # Phase 2: DocCache wiring
        self._add("2/4", "MDL004DocCache class exists",
                  "MDL004DocCache" in globals(), "")
        self._add("2/4", "MDL004BatchBuffer class exists",
                  "MDL004BatchBuffer" in globals(), "")
        self._add("2/4", "MDL004DuckWriter class exists",
                  "MDL004DuckWriter" in globals(), "")
        self._add("2/4", "engine_pdfplumber accepts doc_cache",
                  "doc_cache" in engine_pdfplumber.__code__.co_varnames, "")
        self._add("2/4", "engine_pymupdf accepts doc_cache",
                  "doc_cache" in engine_pymupdf.__code__.co_varnames, "")

        # Phase 3: DB
        duck_p = Path(self.mdl004_temp) / "VRN_MDL004.duckdb"
        sqlite_p = Path(self.mdl004_temp) / "VRN_MDL004.db"
        self._add("3/4", "DB file exists",
                  duck_p.exists() or sqlite_p.exists(),
                  f"duck={duck_p.exists()} sqlite={sqlite_p.exists()}")
        if duck_p.exists() and DUCKDB_OK:
            try:
                con = duckdb_lib.connect(str(duck_p), read_only=True)
                tbls = {t[0] for t in con.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema='main'").fetchall()}
                con.close()
                expected = {"vrn_mdl004_tables","vrn_mdl004_fix_log","vrn_mdl004_schema_log"}
                self._add("3/4", "DuckDB schema 3 tables",
                          expected.issubset(tbls), str(sorted(tbls)))
            except Exception as e:
                self._add("3/4", "DuckDB schema 3 tables", False, str(e))

        # Phase 4
        for fn in ("VRN_MDL004_Tables.json", "VRN_MDL004_VerifySummary.json",
                   "VRN_MDL004_Tables.parquet", "VRN_MDL004_Tables.csv"):
            p = Path(self.mdl004_temp) / fn
            self._add("4/4", f"file:{fn}", p.exists(),
                      f"size={p.stat().st_size if p.exists() else 0}")
        ti = self.run_summary.get("total_tables", 0)
        self._add("4/4", "total_tables non-negative", ti >= 0, str(ti))

        n_total = len(self.checks); n_pass = sum(1 for c in self.checks if c["ok"])
        n_fail = n_total - n_pass
        cls = "READY" if n_fail == 0 else ("NEAR-READY" if n_fail <= 2 else "NOT-READY")
        return {"total":n_total,"pass":n_pass,"fail":n_fail,
                "classification":cls,"checks":self.checks,
                "generated":time.strftime("%Y-%m-%d %H:%M:%S")}


def build_self_verify_html_mdl004(verify_result: Dict, run_summary: Dict) -> str:
    """VRN-MDL004-FNC-021  VIA Visual Lock self-verify HTML (NEW v1.1.0)."""
    cls = verify_result.get("classification","?")
    cls_color = {"READY":"#439a9a","NEAR-READY":"#e0b020",
                 "NOT-READY":"#c83030"}.get(cls,"#666")
    cls_emoji = {"READY":"✓","NEAR-READY":"⚠","NOT-READY":"✗"}.get(cls,"?")

    by_phase: Dict[str,List[Dict]] = collections.OrderedDict()
    for c in verify_result.get("checks",[]):
        by_phase.setdefault(c["phase"], []).append(c)

    phase_html = []
    for phase, items in by_phase.items():
        rows = "".join(
            f'<tr><td class="ck-name">{c["name"]}</td>'
            f'<td class="ck-{"ok" if c["ok"] else "fail"}">'
            f'{"✓" if c["ok"] else "✗"} {"PASS" if c["ok"] else "FAIL"}</td>'
            f'<td class="ck-detail">{str(c["detail"])[:120]}</td></tr>'
            for c in items)
        n_pass = sum(1 for c in items if c["ok"])
        phase_html.append(f"""
        <div class="cd"><div class="cd-h">PHASE {phase} ({n_pass}/{len(items)} pass)</div>
        <div class="cd-b"><table class="ck-tbl">
        <thead><tr><th>Check</th><th>Result</th><th>Detail</th></tr></thead>
        <tbody>{rows}</tbody></table></div></div>""")

    sum_lines = [
        f"$ VRN_MDL004 v{__version__} self-verification",
        f"  generated      : {verify_result.get('generated','-')}",
        f"  classification : {cls} {cls_emoji}",
        f"  checks         : {verify_result.get('pass',0)}/{verify_result.get('total',0)} pass",
        "",
        "$ pipeline summary",
        f"  total reports  : {run_summary.get('total','-')}",
        f"  ok / fail      : {run_summary.get('ok_count','-')} / {run_summary.get('fail_count','-')}",
        f"  total pages    : {run_summary.get('total_pages','-')}",
        f"  total tables   : {run_summary.get('total_tables','-')}",
        f"  err cells      : {run_summary.get('total_err_cells','-')}",
    ]
    term_html = "\n".join(sum_lines)

    html = f"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="UTF-8">
<title>VRN MDL004 v{__version__} · Self-Verification · {cls}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#f5f4f0;color:#1a1a1a;font-family:'DM Sans',-apple-system,sans-serif;font-size:11px;line-height:1.6;padding:24px}}
.hdr{{border-top:4px solid;border-image:linear-gradient(90deg,#ff5e5e,#ffae5e,#ffe55e,#5eff8c,#5ec8ff,#8c5eff,#ff5ec8) 1;padding-top:16px;margin-bottom:24px}}
h1{{font-family:'Syne',sans-serif;font-size:20px;font-weight:800;letter-spacing:-0.02em}}
.sub{{font-family:'DM Mono',monospace;font-size:10px;color:#666;margin-top:4px}}
.cls-badge{{display:inline-block;padding:4px 12px;background:{cls_color};color:white;font-family:'Syne',sans-serif;font-weight:700;font-size:11px;margin-left:12px;letter-spacing:0.05em}}
.cd{{background:white;border:1px solid #e0ddd5;margin-bottom:16px}}
.cd-h{{background:#4c78a8;color:white;padding:8px 16px;font-family:'Syne',sans-serif;font-weight:600;font-size:11px;letter-spacing:0.03em}}
.cd-b{{padding:12px 16px}}
.tm{{background:#1a1a1a;color:#c8e0c8;font-family:'DM Mono',monospace;font-size:10px;padding:32px 16px 16px 16px;position:relative;white-space:pre;line-height:1.5}}
.tm::before{{content:"● ● ●";position:absolute;top:8px;left:12px;color:#ff5e5e;letter-spacing:4px;font-size:10px}}
.ck-tbl{{width:100%;border-collapse:collapse}}
.ck-tbl th{{background:#f5f4f0;color:#4c78a8;text-align:left;padding:6px 8px;font-weight:600;border-bottom:2px solid #4c78a8;font-size:10px;letter-spacing:0.05em}}
.ck-tbl td{{padding:6px 8px;border-bottom:1px solid #f0ede5;vertical-align:top}}
.ck-name{{font-weight:500;min-width:200px}}
.ck-ok{{color:#439a9a;font-weight:600;min-width:80px}}
.ck-fail{{color:#c83030;font-weight:700;min-width:80px}}
.ck-detail{{color:#666;font-family:'DM Mono',monospace;font-size:10px}}
.foot{{margin-top:24px;color:#999;font-family:'DM Mono',monospace;font-size:9px;text-align:right}}
</style></head><body>
<div class="hdr"><h1>VRN MDL004 · OCRFetcher v{__version__}<span class="cls-badge">{cls}</span></h1>
<div class="sub">VeritasReportNova · 4-Phase Self-Verification · {time.strftime("%Y-%m-%d %H:%M:%S")}</div></div>
<div class="cd"><div class="cd-h">RUN SUMMARY</div><div class="cd-b"><div class="tm">{term_html}</div></div></div>
{"".join(phase_html)}
<div class="foot">Module: {__module_id__} · Asset: {__asset_id__} · v{__version__}</div>
</body></html>"""
    return html


# ============================================================================
# CORE TABLE PROCESSOR — integrates engines + fixes + schema
# ============================================================================

def process_one_page(
    pdf_path:    str,
    page_no:     int,
    is_scan:     bool,
    cfg:         Dict,
    db:          Optional[MDL004DBWriter],
    pdf_name:    str,
    report_code: str,
    doc_cache:   Optional["MDL004DocCache"] = None,    # v1.1.0 NEW
    buffer:      Optional["MDL004BatchBuffer"] = None, # v1.1.0 NEW
) -> List[FixedTable]:
    """VRN-MDL004-FNC-017  Process one page: dual-engine → fixes → schema → FixedTable list.
    v1.1.0: doc_cache reuses opened fitz/pdfplumber handles (B1/B2 fix).
            buffer pushes DB rows without lock contention (B4 fix).
    """
    out_tables: List[FixedTable] = []
    fin_pg = page_no > 1  # simplified; real classification in MDL002

    # ── Step 1: Run primary + secondary engines (wrapped via Celeritas) ───
    if is_scan:
        primary_fut = _cel_submit(engine_paddleocr, pdf_path, page_no)
        primary_res = primary_fut.result() if hasattr(primary_fut, "result") else primary_fut
        sec_res     = []
    else:
        eng_a = cfg.get("engine_primary", _P["engine_primary"])
        eng_b = cfg.get("engine_secondary", _P["engine_secondary"])

        # v1.1.0: pass doc_cache through
        primary_fn = engine_pdfplumber if eng_a == "pdfplumber" else engine_pymupdf
        sec_fn     = engine_pymupdf    if eng_b == "pymupdf"    else engine_pdfplumber

        primary_fut = _cel_submit(primary_fn, pdf_path, page_no, doc_cache=doc_cache) \
                      if doc_cache is not None else \
                      _cel_submit(primary_fn, pdf_path, page_no)
        sec_fut     = _cel_submit(sec_fn,     pdf_path, page_no, doc_cache=doc_cache) \
                      if doc_cache is not None else \
                      _cel_submit(sec_fn,     pdf_path, page_no)
        primary_res = primary_fut.result() if hasattr(primary_fut, "result") else primary_fut
        sec_res     = sec_fut.result()     if hasattr(sec_fut, "result")     else sec_fut

    # ── Quadrant split for dense fin-pages ────────────────────────────────
    if fin_pg and cfg.get("quadrant_split", _P["quadrant_split"]) and _CAP["pdfplumber"]:
        try:
            # v1.1.0: prefer doc_cache for quadrants (avoids 4× re-open per page)
            if doc_cache is not None and doc_cache.pdfplumber_pdf is not None:
                pg = doc_cache.pdfplumber_page(page_no)
                if pg is not None:
                    W, H = float(pg.width), float(pg.height)
                    quads = [("TL",(0,0,W/2,H/2)),("TR",(W/2,0,W,H/2)),
                             ("BL",(0,H/2,W/2,H)),("BR",(W/2,H/2,W,H))]
                    for qname, bbox in quads:
                        q_res = engine_pdfplumber(pdf_path, page_no,
                                                  quadrant=bbox, doc_cache=doc_cache)
                        for r in q_res:
                            r.quadrant = qname
                        primary_res.extend(q_res)
            else:
                # Legacy path
                with pdfplumb.open(pdf_path) as pdf:
                    if page_no - 1 < len(pdf.pages):
                        pg = pdf.pages[page_no - 1]
                        W, H = float(pg.width), float(pg.height)
                        quads = [("TL",(0,0,W/2,H/2)),("TR",(W/2,0,W,H/2)),
                                 ("BL",(0,H/2,W/2,H)),("BR",(W/2,H/2,W,H))]
                        for qname, bbox in quads:
                            q_fut = _cel_submit(engine_pdfplumber, pdf_path, page_no, quadrant=bbox)
                            q_res = q_fut.result() if hasattr(q_fut, "result") else q_fut
                            for r in q_res:
                                r.quadrant = qname
                            primary_res.extend(q_res)
        except Exception as e:
            log.debug("[MDL004] quadrant page %d: %s", page_no, e)

    # ── Step 2: Vote & merge ───────────────────────────────────────────────
    accepted = vote_and_merge(primary_res, sec_res)
    if not accepted and not is_scan:
        # Fallback level 1: camelot lattice → stream (also via Celeritas)
        cam_fut = _cel_submit(engine_camelot, pdf_path, page_no, "lattice")
        accepted = cam_fut.result() if hasattr(cam_fut, "result") else cam_fut
        if not accepted:
            cam_fut = _cel_submit(engine_camelot, pdf_path, page_no, "stream")
            accepted = cam_fut.result() if hasattr(cam_fut, "result") else cam_fut

    # ── Fallback level 2: OCR_Plugins.extract_tables_from_pdf (D4 ADAPTER) ──
    # Only invoked when ALL existing engines failed AND OCR_Plugins is loaded.
    # OCR_Plugins routes between camelot/docling/paddleocr based on pdf_type.
    if not accepted and _OCR_PLUGINS_OK:
        log.info("[MDL004] Page %d: all native engines failed → trying OCR_Plugins", page_no)
        plugin_pdf_type = "scanned" if is_scan else "auto"
        plugin_res = _ocr_plugins_extract_tables(
            pdf_path, pdf_type=plugin_pdf_type, output_dir=None,
            config=cfg.get("ocr_plugins_config"),
        )
        if plugin_res.get("ok") and plugin_res.get("table_records"):
            # Filter to current page_no, then bridge to RawTableResult format
            recs_this_page = [r for r in plugin_res["table_records"]
                              if int(r.get("page_no", 0)) == page_no]
            accepted = _ocr_plugins_table_records_to_raw(recs_this_page, page_no_default=page_no)
            if accepted:
                log.info("[MDL004] Page %d: OCR_Plugins recovered %d tables (engine=%s)",
                         page_no, len(accepted), plugin_res.get("engine_used"))

    # ── Step 3: Apply fixes + schema for each accepted table ─────────────
    for raw in accepted:
        if not raw.ok or not raw.raw_data: continue

        fixed_data, fixes = apply_fixes(raw, pdf_path)

        # Build header + periods
        header_idx = find_real_header_row(fixed_data)
        header_row = [str(c or "").strip() for c in fixed_data[header_idx]] if fixed_data else []
        periods    = [p for c in header_row for p in _PERIOD_RE.findall(str(c))]
        periods    = list(dict.fromkeys(periods))  # dedup preserve order

        # Build row dicts
        rows_out: List[Dict] = []
        for row in fixed_data[header_idx + 1:]:
            if not row: continue
            label = str(row[0] or "").strip()
            if not label or _is_axis_noise(label): continue
            values: Dict[str, Optional[float]] = {}
            for ci, cell in enumerate(row[1:]):
                period = periods[ci] if ci < len(periods) else f"col{ci}"
                values[period] = _clean_number(str(cell or ""))
            rows_out.append({"label_raw": label, "canonical": label, "values": values})

        # F17 sum verify
        if _P["fix_F17_sum_verify"]:
            sv = fix_F17_sum_verify(rows_out)
            if not sv["pass"]: fixes.append("F17_WARN")

        # F18 dtype note spill
        if _P["fix_F18_dtype_note_spill"]:
            for rr in rows_out:
                cells = [str(v) for v in (rr.get("values") or {}).values()]
                rr["cells_fixed"] = fix_F18_dtype_note_spill(cells)

        # Pydantic schema
        rows_out, n_pass, n_err = validate_table_rows(rows_out, strict=cfg.get("schema_strict", False))

        # Confidence score
        total_cells = max(1, sum(len((r.get("values") or {})) for r in rows_out))
        good_cells  = sum(1 for r in rows_out
                          for v in (r.get("values") or {}).values() if v is not None)
        confidence  = round(good_cells / total_cells, 3)

        ft = FixedTable(
            region_id      = raw.region_id,
            pdf_name       = pdf_name,
            report_code    = report_code,
            page_no        = page_no,
            region_type    = "fin_page" if fin_pg else "1st_page",
            quadrant       = raw.quadrant,
            engine_primary = cfg.get("engine_primary", _P["engine_primary"]),
            engine_used    = raw.engine,
            header_row     = header_row,
            periods        = periods,
            rows           = rows_out,
            fixes_applied  = fixes,
            n_err_cells    = n_err,
            n_warn_cells   = 0,
            schema_pass    = n_err == 0,
            confidence     = confidence,
            header_context = raw.header_context,
            ok             = True,
        )
        out_tables.append(ft)

        # v1.1.0: prefer buffer (no DB lock contention), fallback to legacy db
        if buffer is not None:
            try:
                buffer.push_table(ft)
                for fix in fixes:
                    buffer.push_fix_log(ft.region_id, pdf_name, fix, "")
                for row in rows_out:
                    if row.get("status") != "PASS":
                        buffer.push_schema_log(ft.region_id, pdf_name,
                                               row.get("label_raw",""),
                                               row.get("status",""),
                                               row.get("validation_error",""))
            except Exception as e:
                log.warning("[MDL004] buffer push %s: %s", ft.region_id, e)
        elif db:
            try:
                db.insert_table_rows(ft)
                for fix in fixes:
                    db.insert_fix_log(ft.region_id, pdf_name, fix)
                for row in rows_out:
                    if row.get("status") != "PASS":
                        db.insert_schema_log(ft.region_id, pdf_name,
                                              row.get("label_raw",""), row.get("status",""),
                                              row.get("validation_error",""))
            except Exception as e:
                log.warning("[MDL004] DB insert %s: %s", ft.region_id, e)

    return out_tables

def process_one_pdf(
    pdf_path:   str,
    cfg:        Dict,
    db:         Optional[MDL004DBWriter],
    buffer:     Optional["MDL004BatchBuffer"] = None,    # v1.1.0 NEW
) -> Dict:
    """VRN-MDL004-FNC-018  Process all pages of one PDF.
    v1.1.0: open PDF ONCE via DocCache (B1/B2 fix), pages parallel via ThreadPool (B3 fix).
    """
    t0          = time.perf_counter()
    meta        = _parse_meta(pdf_path)
    pdf_name    = Path(pdf_path).name
    report_code = meta["report_code"]
    max_pages   = cfg.get("max_pages", 50)

    out = {
        "pdf_name":    pdf_name,
        "report_code": report_code,
        "ticker":      meta["ticker"],
        "report_date": meta["report_date"],
        "broker_abbr": meta["broker_abbr"],
        "n_pages":     0,
        "n_tables":    0,
        "n_err_cells": 0,
        "tables":      [],
        "ok":          False,
        "error":       None,
        "elapsed":     0.0,
    }

    use_cache    = cfg.get("use_doc_cache", True)
    page_par     = cfg.get("page_parallel", True)
    page_workers = cfg.get("page_workers", 0) or max(2, (os.cpu_count() or 4) - 1)

    try:
        is_scan = is_scan_pdf(pdf_path)

        # v1.1.0: single open via DocCache; all pages share the handles
        cache_ctx = MDL004DocCache(pdf_path) if use_cache else None
        if cache_ctx is not None:
            cache_ctx.__enter__()

        try:
            # Get page count from cache
            if cache_ctx is not None and cache_ctx.n_pages > 0:
                n_pages = min(cache_ctx.n_pages, max_pages)
            elif _CAP["fitz"]:
                doc = fitz.open(pdf_path); n_pages = min(len(doc), max_pages); doc.close()
            elif _CAP["pdfplumber"]:
                with pdfplumb.open(pdf_path) as pdf:
                    n_pages = min(len(pdf.pages), max_pages)
            else:
                n_pages = 0
            out["n_pages"] = n_pages

            all_fixed: List[FixedTable] = []

            if page_par and n_pages > 1:
                # P2: page-level parallel — pages run across workers
                with ThreadPoolExecutor(max_workers=page_workers) as ex:
                    futs = {ex.submit(process_one_page,
                                      pdf_path, pg, is_scan, cfg, db,
                                      pdf_name, report_code,
                                      cache_ctx, buffer): pg
                            for pg in range(1, n_pages + 1)}
                    for fut in as_completed(futs):
                        try:
                            ft_list = fut.result()
                            all_fixed.extend(ft_list)
                        except Exception as e:
                            log.warning("[MDL004] page %d: %s", futs[fut], e)
            else:
                # Sequential (legacy / single-page) — still uses DocCache
                for pg_no in range(1, n_pages + 1):
                    ft_list = process_one_page(pdf_path, pg_no, is_scan, cfg, db,
                                                pdf_name, report_code, cache_ctx, buffer)
                    all_fixed.extend(ft_list)

            # F02: cross-page merge for continuation tables
            if _P["fix_F02_cross_page_concat"] and len(all_fixed) > 1:
                raw_datas = [ft.rows for ft in all_fixed]
                merged_datas = fix_F02_cross_page_concat(raw_datas)
                for i, ft in enumerate(all_fixed):
                    if i < len(merged_datas): ft.rows = merged_datas[i]

            out["n_tables"]    = len(all_fixed)
            out["n_err_cells"] = sum(ft.n_err_cells for ft in all_fixed)
            out["tables"]      = [
                {
                    "region_id":     ft.region_id,
                    "page_no":       ft.page_no,
                    "region_type":   ft.region_type,
                    "quadrant":      ft.quadrant,
                    "engine_used":   ft.engine_used,
                    "header_row":    ft.header_row,
                    "periods":       ft.periods,
                    "rows":          ft.rows,
                    "fixes_applied": ft.fixes_applied,
                    "n_err_cells":   ft.n_err_cells,
                    "schema_pass":   ft.schema_pass,
                    "confidence":    ft.confidence,
                    "header_context":ft.header_context,
                    "ok":            ft.ok,
                }
                for ft in all_fixed
            ]
            out["ok"] = True

        finally:
            if cache_ctx is not None:
                cache_ctx.__exit__(None, None, None)

    except Exception as e:
        out["error"] = str(e)
        log.error("[MDL004] process_one_pdf %s: %s", pdf_name, e)

    out["elapsed"] = round(time.perf_counter() - t0, 2)
    log.info("[MDL004] %s: pages=%d tables=%d err=%d %.2fs",
             pdf_name, out["n_pages"], out["n_tables"], out["n_err_cells"], out["elapsed"])
    return out

# ============================================================================
# [VRN:ANCHOR:MDL004-OUT-001] §19  OUTPUT ASSEMBLER
# ============================================================================

def assemble_output(results: List[Dict]) -> Dict:
    """VRN-MDL004-FNC-019"""
    ok_count = sum(1 for r in results if r.get("ok"))
    return {
        "module":          __module_id__,
        "version":         __version__,
        "generated":       time.strftime("%Y-%m-%d %H:%M:%S"),
        "total":           len(results),
        "ok_count":        ok_count,
        "fail_count":      len(results) - ok_count,
        "total_pages":     sum(r.get("n_pages",0) for r in results),
        "total_tables":    sum(r.get("n_tables",0) for r in results),
        "total_err_cells": sum(r.get("n_err_cells",0) for r in results),
        "reports":         results,
    }

# ============================================================================
# [VRN:ANCHOR:MDL004-SYS-001] §20  PIPELINE ENTRY
# ============================================================================

class VRN_MDL004_OCRFetcher:
    """VRN-MDL004-CLS-001
    run():
      1. Load external SSOT (optional)
      2. Accel init
      3. List PDFs from pdf_temp
      4. Parallel process_one_pdf() — dual-engine OCR + 20 fixes + schema
      5. DB export
      6. VRN_MDL004_Tables.json + VerifySummary.json
    """
    def __init__(self, cfg: Optional[Dict] = None):
        self.cfg     = dict(_PARAMS, **(cfg or {}))
        # Use Celeritas thread budget if loaded, else fallback to cpu_count-1
        workers      = self.cfg.get("workers", 0)
        if not workers:
            workers = _cel_thread_budget(mode="balanced")
        self.workers = workers
        self.db: Optional[MDL004DBWriter] = None

    def run(self) -> Dict:
        run_t0      = time.perf_counter()
        pdf_temp    = self.cfg.get("pdf_temp",    _P["pdf_temp"])
        mdl004_temp = self.cfg.get("mdl004_temp", _P["mdl004_temp"])
        ssot_dir    = self.cfg.get("ssot_dir",    _P["ssot_dir"])
        Path(mdl004_temp).mkdir(parents=True, exist_ok=True)

        # ── 7-tool HardGate load + OCR_Plugins companion ─────────────────────
        ssot_caps = load_external_ssot(ssot_dir)
        log.info("[MDL004] 7-tool SSOT + OCR_Plugins: %s", ssot_caps)

        cap = _mdl004_accel_init(self.workers)
        log.info("[MDL004] accel: %s", cap)

        # Re-budget workers now that Celeritas may be loaded
        if _CEL_OK:
            new_workers = _cel_thread_budget(mode="balanced")
            if new_workers and new_workers != self.workers:
                log.info("[MDL004] worker budget refreshed: %d → %d (Celeritas)",
                         self.workers, new_workers)
                self.workers = new_workers

        # ── v1.1.0: BatchBuffer + DuckDB primary + sqlite fallback ──────────
        self.buffer: Optional[MDL004BatchBuffer] = None
        self.duck:   Optional[MDL004DuckWriter]  = None
        if self.cfg.get("enable_db", True):
            self.buffer = MDL004BatchBuffer(
                batch_size=self.cfg.get("batch_size", 5000))
            if self.cfg.get("use_duckdb", True) and DUCKDB_OK:
                try:
                    self.duck = MDL004DuckWriter(
                        str(Path(mdl004_temp) / "VRN_MDL004.duckdb"))
                    log.info("[MDL004] DuckDB primary writer ready")
                except Exception as e:
                    log.warning("[MDL004] DuckDB init fail (%s), sqlite fallback", e)
                    self.duck = None
            try:
                self.db = MDL004DBWriter(str(Path(mdl004_temp) / "VRN_MDL004.db"))
                log.info("[MDL004] sqlite fallback writer ready")
            except Exception as e:
                log.warning("[MDL004] sqlite init fail: %s", e)
                self.db = None

        pdfs = list_pdfs(pdf_temp)
        if not pdfs:
            log.warning("[MDL004] No PDFs in %s", pdf_temp)
            empty = assemble_output([])
            _jwrite(str(Path(mdl004_temp) / "VRN_MDL004_Tables.json"), empty)
            return {"ok": True, "total": 0, "success": 0, "errors": [], "out_dir": mdl004_temp}

        log.info("[MDL004] Processing %d PDFs, workers=%d  doc_cache=%s page_par=%s",
                 len(pdfs), self.workers,
                 self.cfg.get("use_doc_cache",True),
                 self.cfg.get("page_parallel",True))

        all_results: List[Dict] = []
        fail_count = 0

        # ── PDF-level parallel via Celeritas or stdlib ThreadPoolExecutor ───
        if _CEL_OK and hasattr(_CEL, "_LazyPool"):
            try:
                futs = {_CEL._LazyPool.submit(process_one_pdf, p, self.cfg, self.db,
                                              self.buffer): p
                        for p in pdfs}
                for fut in as_completed(futs):
                    res = fut.result()
                    all_results.append(res)
                    if not res.get("ok"): fail_count += 1
                log.info("[MDL004] Celeritas _LazyPool path completed")
            except Exception as e:
                log.warning("[MDL004] Celeritas pool failed (%s); fallback stdlib", e)
                all_results = []; fail_count = 0
                with ThreadPoolExecutor(max_workers=self.workers) as ex:
                    futs = {ex.submit(process_one_pdf, p, self.cfg, self.db, self.buffer): p
                            for p in pdfs}
                    for fut in as_completed(futs):
                        res = fut.result()
                        all_results.append(res)
                        if not res.get("ok"): fail_count += 1
        else:
            with ThreadPoolExecutor(max_workers=self.workers) as ex:
                futs = {ex.submit(process_one_pdf, p, self.cfg, self.db, self.buffer): p
                        for p in pdfs}
                for fut in as_completed(futs):
                    res = fut.result()
                    all_results.append(res)
                    if not res.get("ok"): fail_count += 1

        # ── v1.1.0: single-thread flush DB after pool closes ────────────────
        flush_stats = {"tbl": 0, "fix": 0, "schema": 0}
        if self.buffer:
            t_rows, f_rows, s_rows = self.buffer.consume_all()
            log.info("[MDL004] Buffer drain: tbl=%d fix=%d schema=%d",
                     len(t_rows), len(f_rows), len(s_rows))
            if self.duck:
                try:
                    flush_stats = self.duck.flush(t_rows, f_rows, s_rows)
                    log.info("[MDL004] DuckDB flush: %s", flush_stats)
                except Exception as e:
                    log.warning("[MDL004] DuckDB flush fail (%s), sqlite fallback", e)
                    if self.db:
                        flush_stats = self.db.flush(t_rows, f_rows, s_rows)
            elif self.db:
                flush_stats = self.db.flush(t_rows, f_rows, s_rows)
                log.info("[MDL004] sqlite flush: %s", flush_stats)

        # ── v1.1.0: polars-direct exports ───────────────────────────────────
        parquet_path = csv_path = None
        if self.duck:
            parquet_path = self.duck.export_parquet_polars(mdl004_temp)
            csv_path     = self.duck.export_csv_polars(mdl004_temp)
        elif self.db:
            parquet_path = self.db.export_parquet_polars(mdl004_temp)
            csv_path     = self.db.export_csv_polars(mdl004_temp)
        log.info("[MDL004] Exports: parquet=%s csv=%s", parquet_path, csv_path)

        out = assemble_output(all_results)
        _jwrite(str(Path(mdl004_temp) / "VRN_MDL004_Tables.json"), out)

        verify = {
            "module":          __module_id__,
            "version":         __version__,
            "generated":       time.strftime("%Y-%m-%d %H:%M:%S"),
            "total":           len(pdfs),
            "ok":              fail_count == 0,
            "ok_count":        len(pdfs) - fail_count,
            "fail_count":      fail_count,
            "total_tables":    out["total_tables"],
            "total_err_cells": out["total_err_cells"],
            "ssot_caps":       ssot_caps,
            "accel_caps":      cap,
            "celeritas_caps":  _cel_capability_report(),
            "ocr_plugins_loaded": _OCR_PLUGINS_OK,
            "engine_primary":  self.cfg.get("engine_primary"),
            "engine_secondary":self.cfg.get("engine_secondary"),
            "fix_flags":       {k:v for k,v in _P.items() if k.startswith("fix_")},
            "flush_stats":     flush_stats,
            "fail_details": [{"pdf_name":r["pdf_name"],"error":r.get("error")}
                             for r in all_results if not r.get("ok")],
        }
        _jwrite(str(Path(mdl004_temp) / "VRN_MDL004_VerifySummary.json"), verify)

        if self.duck: self.duck.close()
        if self.db:   self.db._con.close() if hasattr(self.db, "_con") else None

        # ── v1.1.0: 4-phase self-verify HTML (after DB close to allow read) ─
        sv_html_path = None
        if self.cfg.get("self_verify", True):
            try:
                sv = MDL004SelfVerifier(self.cfg, out, mdl004_temp).run()
                html = build_self_verify_html_mdl004(sv, out)
                sv_html_path = str(Path(mdl004_temp) / "VRN_MDL004_SelfVerify.html")
                Path(sv_html_path).write_text(html, encoding="utf-8")
                log.info("[MDL004] Self-verify: %s (%d/%d) → %s",
                         sv["classification"], sv["pass"], sv["total"], sv_html_path)
            except Exception as e:
                log.warning("[MDL004] self_verify build fail: %s", e)

        elapsed = round(time.perf_counter() - run_t0, 2)
        log.info("[MDL004] Complete: %d/%d OK  tables=%d  err_cells=%d  %.2fs",
                 len(pdfs)-fail_count, len(pdfs), out["total_tables"],
                 out["total_err_cells"], elapsed)
        return {
            "ok":           fail_count == 0,
            "total":        len(pdfs),
            "success":      len(pdfs) - fail_count,
            "total_tables": out["total_tables"],
            "elapsed":      elapsed,
            "flush_stats":  flush_stats,
            "self_verify_html": sv_html_path,
            "errors":       [r.get("error","") for r in all_results if not r.get("ok")],
            "out_dir":      mdl004_temp,
        }

# ============================================================================
# __all__
# ============================================================================

__all__ = [
    "__version__", "__module_id__",
    # Params
    "_PARAMS", "_P",
    # SSOT
    "TW_TICKER_REGEX","TW_BLOOMBERG_REGEX","TW_YFINANCE_REGEX",
    # Accel
    "_mdl004_accel_init", "_CAP",
    # Data classes
    "RawTableResult","FixedTable",
    # Scan
    "list_pdfs","is_scan_pdf",
    # Context
    "get_header_context","find_real_header_row",
    # Engines (all standalone)
    "engine_pdfplumber","engine_pymupdf","engine_camelot",
    "engine_tabula","engine_paddleocr","engine_docling",
    # Vote
    "vote_and_merge",
    # Fixes (all standalone F01–F20)
    "fix_F01_header_context","fix_F02_cross_page_concat",
    "fix_F03_borderless_explicit","fix_F04_dual_column_split",
    "fix_F05_nested_table","fix_F06_rowspan_ffill",
    "fix_F07_colspan_ffill","fix_F08_text_wrap_merge",
    "fix_F09_text_center_align","fix_F10_empty_row_drop",
    "fix_F11_zh_space","fix_F12_ocr_alphanum",
    "fix_F13_trim_nbsp","fix_F14_currency_bracket",
    "fix_F15_mojibake_ocr","fix_F16_header_shift",
    "fix_F17_sum_verify","fix_F18_dtype_note_spill",
    "fix_F19_watermark_filter","fix_F20_col_shift_repair",
    "apply_fixes",
    # Schema
    "validate_table_rows",
    # SSOT
    "load_external_ssot",
    # DB
    "MDL004DBWriter",
    # v1.1.0 NEW
    "MDL004DocCache", "MDL004BatchBuffer", "MDL004DuckWriter",
    "MDL004SelfVerifier", "build_self_verify_html_mdl004",
    # Pipeline
    "process_one_page","process_one_pdf","assemble_output",
    "VRN_MDL004_OCRFetcher",
]

# ============================================================================
# __main__
# ============================================================================

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="VRN MDL004 OCR FetchingPDFTable v1")
    p.add_argument("--pdf-temp",    default=_P["pdf_temp"])
    p.add_argument("--mdl004-temp", default=_P["mdl004_temp"])
    p.add_argument("--ssot-dir",    default=_P["ssot_dir"])
    p.add_argument("--workers",     type=int, default=_P["workers"])
    p.add_argument("--dpi",         type=int, default=300,
                   help="DPI for scan rendering (informational)")
    p.add_argument("--engine-primary",   default=_P["engine_primary"])
    p.add_argument("--engine-secondary", default=_P["engine_secondary"])
    p.add_argument("--no-db", action="store_true")
    args = p.parse_args()
    cfg  = {
        "pdf_temp":        args.pdf_temp,
        "mdl004_temp":     args.mdl004_temp,
        "ssot_dir":        args.ssot_dir,
        "workers":         args.workers,
        "engine_primary":  args.engine_primary,
        "engine_secondary":args.engine_secondary,
        "enable_db":       not args.no_db,
    }
    result = VRN_MDL004_OCRFetcher(cfg).run()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["ok"] else 1)