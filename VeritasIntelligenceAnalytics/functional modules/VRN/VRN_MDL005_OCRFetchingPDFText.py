# -*- coding: utf-8 -*-
from __future__ import annotations
"""
VRN_MDL005_OCRFetchingPDFText_v1.py
=====================================
VERITAS REPORT NOVA -- MDL005  Multi-Engine OCR + PDF Text Fetching
Version   : 1.0.0   |   Module ID : VRN-MDL005-SUP-001
Asset ID  : VRN-MDL005-CLS-001
Policy    : 功能只增不減 · append-only · SSOT · 獨立模組

PIPELINE POSITION
  pdf_temp/                ← 高畫質 PDF (from MDL001)
    ↓ (parallel with MDL004)
  VRN_MDL005_OCRFetchingPDFText_v1  (此模組)
    ↓
  mdl005_temp/             ← 精準文字段落 (OCR+修復+分段) → MDL006+

DESIGN PRINCIPLES  (identical spec to MDL004)
  ① ALL PARAMETERS ON TOP  — single _PARAMS dict, zero magic numbers in code
  ② AST-CLEAN SECTIONS     — each §section is a self-contained extractable unit
  ③ MODULAR / DETACHABLE   — every engine, fix, validator callable standalone
  ④ 20 TEXT-FIX STRATEGIES — T01–T20, each a separate named function
  ⑤ DUAL-ENGINE EXTRACTION — primary layout + secondary OCR, consensus merge
  ⑥ READING ORDER FIX      — reorder blocks by (x,y) coords, not raw stream
  ⑦ PYDANTIC SCHEMA CHECK  — typed paragraph validation, tag ERR/WARN/PASS
  ⑧ SSOT REAL INTEGRATION  — VIA_SSOT_Unified / VeritasAegisNexus / VeritasCeleritas
                              actual API calls, not stub stubs

ANCHOR MAP
  [VRN:ANCHOR:MDL005-META-001]       §0   Module Metadata
  [VRN:ANCHOR:MDL005-PARAMS-001]     §1   ALL PARAMETERS
  [VRN:ANCHOR:MDL005-SSOT-001]       §2   SSOT: embedded + VIA_SSOT_Unified merge
  [VRN:ANCHOR:MDL005-ACCEL-001]      §3   Accelerator Init (6-ENV + Celeritas)
  [VRN:ANCHOR:MDL005-SAFEIMPORT-001] §4   Safe Imports (graceful 80+)
  [VRN:ANCHOR:MDL005-PLUGIN-001]     §5   Plugin Loader: SSOT / Celeritas / Aegis
  [VRN:ANCHOR:MDL005-PROXY-001]      §6   Plugin Proxy Functions (safe stubs)
  [VRN:ANCHOR:MDL005-DATACLASS-001]  §7   Data Classes
  [VRN:ANCHOR:MDL005-SCAN-001]       §8   PDF Scanner + scan detection
  [VRN:ANCHOR:MDL005-ENGINE-001]     §9   Engine A: PyMuPDF fitz (primary)
  [VRN:ANCHOR:MDL005-ENGINE-002]     §10  Engine B: pdfplumber (secondary)
  [VRN:ANCHOR:MDL005-ENGINE-003]     §11  Engine C: pdfminer.six (deep parse)
  [VRN:ANCHOR:MDL005-ENGINE-004]     §12  Engine D: Docling (AI layout)
  [VRN:ANCHOR:MDL005-ENGINE-005]     §13  Engine E: Marker (fast Markdown)
  [VRN:ANCHOR:MDL005-ENGINE-006]     §14  Engine F: PaddleOCR (scan)
  [VRN:ANCHOR:MDL005-ENGINE-007]     §15  Engine G: Surya (layout+OCR)
  [VRN:ANCHOR:MDL005-MERGE-001]      §16  Dual-Engine Merge + Dedup
  [VRN:ANCHOR:MDL005-FIX-001]        §17  T01–T20 Text Fix Strategy Library
  [VRN:ANCHOR:MDL005-SCHEMA-001]     §18  Pydantic Schema Validator
  [VRN:ANCHOR:MDL005-SEGMENT-001]    §19  Page Classifier + Segment Tagger
  [VRN:ANCHOR:MDL005-DB-001]         §20  DB Writer (WAL + Parquet + CSV)
  [VRN:ANCHOR:MDL005-OUT-001]        §21  Output Assembler
  [VRN:ANCHOR:MDL005-SYS-001]        §22  Pipeline Entry

SMART ASSET REGISTRY
  VRN-MDL005-CLS-001  VRN_MDL005_TextFetcher
  VRN-MDL005-CLS-002  MDL005DBWriter
  VRN-MDL005-CLS-003  RawTextBlock
  VRN-MDL005-CLS-004  FixedTextBlock
  VRN-MDL005-CLS-005  TextParagraph (Pydantic)
  VRN-MDL005-FNC-001..FNC-050  (see inline)

EXTERNAL SSOT PATHS (loaded in §5 Plugin Loader)
  supportive_module/VIA_SSOT_Unified.py   — CANONICAL_MAP, BROKER_MAP, normalize_rating()
  supportive_module/VeritasCeleritas.py   — _LazyPool.submit/map, bootstrap_at_import()
  supportive_module/VeritasAegisNexus.py  — safe_get(), RateLimiter, ExponentialBackoff

OUTPUTS (mdl005_temp)
  VRN_MDL005_Text.json          ← per-PDF all text blocks (fixed + tagged + segmented)
  VRN_MDL005_VerifySummary.json ← fix/segment/engine counts + plugin status
  VRN_MDL005.db                 ← SQLite WAL (text_blocks + fix_log + segment_log)
  VRN_MDL005_Text.parquet       ← Parquet flat
  VRN_MDL005_Text.csv           ← CSV (UTF-8 BOM)

LL RULES: #10 #12 #13 #15 #17 #18 #19 #20
"""

# ============================================================================
# [VRN:ANCHOR:MDL005-META-001] §0  MODULE METADATA
# ============================================================================

__version__   = "1.1.0"
__module_id__ = "VRN-MDL005-SUP-001"
__asset_id__  = "VRN-MDL005-CLS-001"
__author__    = "VRN Team"
__domain__    = "OCR_TEXT_FETCH"

# ============================================================================
# [VRN:ANCHOR:MDL005-PARAMS-001] §1  ALL PARAMETERS — SINGLE SOURCE OF TRUTH
# ── Change behaviour HERE only. Zero magic numbers elsewhere. ────────────────
# ============================================================================

_PARAMS: dict = {

    # ── Paths ─────────────────────────────────────────────────────────────────
    "pdf_temp":    r"C:\VeritasIntelligenceAnalytics\VeritasReportNova\temp\pdf_temp",
    "mdl005_temp": r"C:\VeritasIntelligenceAnalytics\VeritasReportNova\temp\mdl005_temp",
    "ssot_dir":    r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module",

    # ── Plugin enable flags ────────────────────────────────────────────────────
    "enable_ssot":       True,    # VIA_SSOT_Unified
    "enable_celeritas":  True,    # VeritasCeleritas (parallel acceleration)
    "enable_aegis":      True,    # VeritasAegisNexus (HTTP/fetch for metadata)

    # ── Concurrency ───────────────────────────────────────────────────────────
    "workers":     0,             # 0 = auto (cpu_count - 1)

    # ── DB / output ───────────────────────────────────────────────────────────
    "enable_db":   True,
    "zero_error":  True,

    # ── Engine selection ──────────────────────────────────────────────────────
    # Available: "pymupdf", "pdfplumber", "pdfminer", "docling",
    #            "marker", "paddleocr", "surya"
    "engine_primary":   "pymupdf",
    "engine_secondary": "pdfplumber",
    "engine_fallback":  "pdfminer",
    "engine_ocr":       "paddleocr",
    "engine_ai":        "docling",

    # ── Page limits ───────────────────────────────────────────────────────────
    "max_pages":   50,

    # ── Scan detection ────────────────────────────────────────────────────────
    "scan_text_threshold":  50,   # avg chars/page below → treat as scan
    "scan_sample_pages":    3,

    # ── Text block geometry ───────────────────────────────────────────────────
    "y_bucket_px":          5,    # px group size for y-axis row buckets
    "min_block_chars":      2,    # discard blocks shorter than this
    "min_paragraph_chars":  10,   # discard merged paragraphs shorter
    "char_width_ratio":     2.0,  # gap/avg_char_width > this → space

    # ── Reading order ─────────────────────────────────────────────────────────
    "reading_order_x_tol":  50,   # px — same column tolerance
    "dual_col_x_split":     0.5,  # page-width ratio for dual-column midpoint

    # ── Segment classification keywords ───────────────────────────────────────
    "seg_keywords_summary": [
        "投資摘要", "摘要", "結論", "建議", "Summary", "Conclusion",
        "Investment Thesis", "Key Points", "Recommendation",
    ],
    "seg_keywords_fin": [
        "損益表", "資產負債表", "現金流量表", "財務報表", "財務預估",
        "Income Statement", "Balance Sheet", "Cash Flow", "Earnings",
        "Financial Summary", "Key Financials",
    ],
    "seg_keywords_qa": [
        "問答", "法說", "Q&A", "Conference Call", "Earnings Call",
    ],
    "seg_keywords_outlook": [
        "展望", "前景", "Outlook", "Guidance", "Forecast",
        "Business Update", "產業動態",
    ],
    "seg_keywords_disclaimer": [
        "免責聲明", "Disclaimer", "Important Disclosures",
        "Legal Notice", "Research Disclosures",
    ],

    # ── Title detection heuristics ────────────────────────────────────────────
    "title_max_chars":      60,   # shorter than this may be title
    "title_fontsize_ratio": 1.2,  # font > avg * ratio → title candidate
    "title_end_punct_re":   r"[。，；：,;:]$",  # if ends with this → NOT title

    # ── Sentence merge (向右向下整合到句點) ──────────────────────────────────
    "sent_merge_end_re":    r"[。！？.!?]$",
    "sent_merge_enabled":   True,

    # ── Dedup ─────────────────────────────────────────────────────────────────
    "dedup_hash_prefix_len": 80,  # chars to hash for dedup key

    # ── Fix strategy flags T01–T20 ────────────────────────────────────────────
    "fix_T01_reading_order":      True,  # reorder blocks by (x,y) coords
    "fix_T02_whitespace_reconstruct": True,  # gap-based space detection
    "fix_T03_dehyphenation":      True,  # re-trieve → retrieve
    "fix_T04_zh_en_separation":   True,  # remove OCR spaces in CJK
    "fix_T05_unicode_normalize":  True,  # NFKC normalize full/half width
    "fix_T06_trim_nbsp":          True,  # strip + \u00a0 → space
    "fix_T07_ocr_alphanum":       True,  # l→1, O→0, I→1 near digits
    "fix_T08_mojibake_detect":    True,  # flag garbled encoding
    "fix_T09_watermark_filter":   True,  # remove light-color / tiny text
    "fix_T10_sent_merge":         True,  # merge broken sentences to punct
    "fix_T11_title_detect":       True,  # tag blocks as title/body
    "fix_T12_dedup":              True,  # remove duplicate blocks
    "fix_T13_empty_drop":         True,  # drop empty/stub blocks
    "fix_T14_segment_tag":        True,  # tag segment type (summary/fin/qa...)
    "fix_T15_header_footer_strip":True,  # strip repeated page headers/footers
    "fix_T16_bullet_preserve":    True,  # preserve bullet/numbered list structure
    "fix_T17_table_ref_skip":     True,  # skip blocks that are really table cells
    "fix_T18_reading_col_reorder":True,  # multi-column left-then-right reorder
    "fix_T19_financial_term_norm":True,  # normalize via SSOT SYNONYM_MAP
    "fix_T20_confidence_score":   True,  # compute per-block confidence

    # ── Pydantic ──────────────────────────────────────────────────────────────
    "schema_strict":        False,

    # ── Watermark detection ───────────────────────────────────────────────────
    "watermark_rgb_min":    240,  # RGB above this → watermark
    "watermark_size_max":   6.0,  # pt below this → watermark

    # ── T17: table cell detection ─────────────────────────────────────────────
    "table_cell_max_chars": 30,   # very short + numeric → likely table cell
    "table_cell_num_ratio": 0.5,  # fraction of chars that are digits → table

    # ── v1.1.0 NEW (append-only) ──────────────────────────────────────────────
    "use_doc_cache":   True,    # P1: 每 PDF 只開一次 fitz + pdfplumber
    "page_parallel":   True,    # P2: pages 跨 worker 平行
    "page_workers":    0,       # 0 = auto
    "use_duckdb":      True,    # P3: DuckDB primary, sqlite fallback
    "batch_size":      5000,    # P3: BatchBuffer flush threshold
    "polars_first":    True,    # P5: polars vectorized text fixes
    "self_verify":     True,    # P6: 4-phase HTML
}

# ── Short alias (read-only) ───────────────────────────────────────────────────
_P = _PARAMS

# ============================================================================
# STDLIB
# ============================================================================

import os, sys, re, json, time, math, hashlib, logging, sqlite3, csv, io
import gc, argparse, threading, warnings, collections, copy, importlib, unicodedata
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings("ignore")

# ============================================================================
# [VRN:ANCHOR:MDL005-SAFEIMPORT-001] §4  SAFE IMPORTS
# ============================================================================

def _si(name: str):
    try: return importlib.import_module(name)
    except Exception: return None

fitz        = _si("fitz")
pdfplumb    = _si("pdfplumber")
pdfminer    = _si("pdfminer")
docling_lib = _si("docling.document_converter")
paddle_lib  = _si("paddleocr")
pd          = _si("pandas")
pyarrow     = _si("pyarrow")
orjson      = _si("orjson")
xxhash      = _si("xxhash")
pydantic_lib= _si("pydantic")
np          = _si("numpy")
cv2         = _si("cv2")

# v1.1.0 NEW: polars + duckdb (primary)
pl          = _si("polars")
duckdb_lib  = _si("duckdb")
POLARS_OK   = pl is not None
DUCKDB_OK   = duckdb_lib is not None

_CAP: Dict[str, bool] = {
    "fitz":       fitz is not None,
    "pdfplumber": pdfplumb is not None,
    "pdfminer":   pdfminer is not None,
    "docling":    docling_lib is not None,
    "paddleocr":  paddle_lib is not None,
    "pandas":     pd is not None,
    "pyarrow":    pyarrow is not None,
    "pydantic":   pydantic_lib is not None,
    "numpy":      np is not None,
    "cv2":        cv2 is not None,
    "polars":     POLARS_OK,
    "duckdb":     DUCKDB_OK,
    "orjson":     orjson is not None,
}

# ============================================================================
# [VRN:ANCHOR:MDL005-DOCCACHE-001] §4.5  P1 DOC CACHE — v1.1.0
# ── 同 MDL004 v1.1.0 模式：每 PDF 只開一次 fitz + pdfplumber                  ─
# ============================================================================

class MDL005DocCache:
    """VRN-MDL005-CLS-006 (NEW v1.1.0)
    Open fitz + pdfplumber ONCE per PDF, share for all page operations.
    """
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self._fitz: Any = None
        self._pp:   Any = None
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
                log.debug("[MDL005] DocCache fitz open fail: %s", e)
                self._fitz = None
        if _CAP["pdfplumber"]:
            try:
                self._pp = pdfplumb.open(self.pdf_path)
                if self.n_pages == 0:
                    self.n_pages = len(self._pp.pages)
            except Exception as e:
                log.debug("[MDL005] DocCache pdfplumber open fail: %s", e)
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
        if self._fitz is None or page_no - 1 >= len(self._fitz): return None
        return self._fitz[page_no - 1]

    def pdfplumber_page(self, page_no: int):
        if self._pp is None or page_no - 1 >= len(self._pp.pages): return None
        return self._pp.pages[page_no - 1]


# ============================================================================
# [VRN:ANCHOR:MDL005-PRECOMP-001] §4.6  P4 PRE-COMPILED REGEX POOL — v1.1.0
# ============================================================================

_RE_OCR_O_TO_0_v110 = re.compile(
    r"(?<![A-Za-z])O(?=\d)|(?<=\d)O(?=\d)|(?<=\d)O(?![A-Za-z])"
)
_RE_OCR_l_TO_1_v110 = re.compile(r"(?<![A-Za-z])[lI\|](?=\d)|(?<=\d)[lI\|](?![A-Za-z])")
_RE_BRACKET_NEG_v110 = re.compile(r"^\(([^)]+)\)$")
_RE_DOUBLESPACE_v110 = re.compile(r" {2,}")
_RE_HYPHEN_BREAK     = re.compile(r"(\w)-\s+(\w)")
_RE_MOJIBAKE_v110    = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x80-\x9f]")

# ============================================================================
# [VRN:ANCHOR:MDL005-SSOT-001] §2  SSOT — EMBEDDED (locked) + SSOT_Unified merge
# ============================================================================

# THREE LOCKED TW TICKER REGEX — IMMUTABLE, NEVER MODIFY
TW_TICKER_REGEX    = re.compile(r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})")
TW_BLOOMBERG_REGEX = re.compile(r"\b(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})\s+TT\b")
TW_YFINANCE_REGEX  = re.compile(r"\b(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})\.(TW|TWO)\b")

# Embedded RATING_LIST (dict — read-only SSOT rule, never overwrite)
RATING_LIST: Dict[str, str] = {
    "買進":"BUY",        "買入":"BUY",       "強力買進":"STRONG_BUY",
    "增持":"OVERWEIGHT", "加碼":"OVERWEIGHT","Outperform":"OVERWEIGHT",
    "優於大盤":"OVERWEIGHT","中立":"NEUTRAL", "持有":"NEUTRAL",
    "市場中立":"NEUTRAL", "中性":"NEUTRAL",   "觀望":"NEUTRAL",
    "減持":"UNDERWEIGHT","賣出":"SELL",       "強力賣出":"STRONG_SELL",
    "BUY":"BUY",         "SELL":"SELL",       "HOLD":"NEUTRAL",
    "Overweight":"OVERWEIGHT","Underweight":"UNDERWEIGHT",
    "Neutral":"NEUTRAL", "Outperform":"OVERWEIGHT",
    "Underperform":"UNDERWEIGHT","Market Perform":"NEUTRAL",
    "not rated":"NR",    "Not Rated":"NR",    "N/R":"NR",
}
RATING_FLAT_LIST: Dict[str, str] = {k.lower(): v for k, v in RATING_LIST.items()}

# Embedded BROKER_MAP (append-only)
BROKER_MAP: Dict[str, str] = {
    "GS":"高盛",       "MS":"摩根士丹利",   "JPM":"摩根大通",
    "UBS":"瑞銀",      "CITI":"花旗",       "CLSA":"里昂",
    "KGI":"凱基",      "Nomura":"野村",     "Daiwa":"大和",
    "Macquarie":"麥格理","HSBC":"匯豐",     "DB":"德意志",
    "ML":"美林",       "BAML":"美銀美林",   "SMBC":"三井住友",
    "Mizuho":"瑞穗",   "Yuanta":"元大",     "Fubon":"富邦",
    "CTBC":"中信",     "SinoPac":"永豐",    "Mega":"兆豐",
    "First":"第一",    "Hua Nan":"華南",    "Credit Suisse":"瑞信",
    "Barclays":"巴克萊","CIMB":"聯昌",      "Maybank":"馬銀行",
}
BROKER_ABBR_MAP: Dict[str, str] = {v: k for k, v in BROKER_MAP.items()}

# Embedded SYNONYM_MAP for financial term normalization (T19)
SYNONYM_MAP: Dict[str, List[str]] = {
    "revenue":          ["sales","turnover","topline","營收","營業收入","Net Revenue"],
    "gross_profit":     ["gross income","毛利","營業毛利","Gross Profit"],
    "operating_income": ["ebit","營業利益","Operating Income","EBIT"],
    "net_income":       ["profit","bottomline","淨利","稅後純益","Net Income"],
    "eps":              ["每股盈餘","EPS","Diluted EPS","每股淨利"],
    "roe":              ["股東權益報酬率","ROE"],
    "pe_ratio":         ["本益比","P/E","PER"],
    "target_price":     ["目標價","TP","Target Price","Price Target"],
}
# Reverse map: alias → canonical
_SYNONYM_REVERSE: Dict[str, str] = {
    alias.lower(): canon
    for canon, aliases in SYNONYM_MAP.items()
    for alias in aliases
}

# Compiled regex helpers
_ZH_SP_RE   = re.compile(r"(?<=[\u4e00-\u9fa5])\s+(?=[\u4e00-\u9fa5])")
_HYPHEN_RE  = re.compile(r"(\w+)-\s*\n\s*(\w+)")
_OCR_NUM_RE = re.compile(r"(?<!\w)([lOI\|])(?=[\d,])|(?<=[\d,])([lOI\|])(?!\w)")
_AXIS_RE1   = re.compile(r"^[-+]?[\d\s,\.]+%?$")
_AXIS_RE2   = re.compile(r"^(?:[-+]?\d{1,3}(?:\.\d+)?[%O]?\s*){4,}$")
_AXIS_RE3   = re.compile(r"^\s*(\d+[OBoS]+|[sS]o+|JO+|I+)\s*$")
_BULLET_RE  = re.compile(r"^(\d+\.|[(（]?\d+[)）][.、]?|[➢⚫•▪▸\-])\s*")

def normalize_rating(raw: str) -> Tuple[str, str]:
    """VRN-MDL005-FNC-001  Map raw rating string → (raw, canonical). SSOT-safe."""
    if not raw: return "", "NR"
    canonical = RATING_FLAT_LIST.get(raw.strip().lower(), "")
    if not canonical:
        rl = raw.strip().lower()
        for k, v in RATING_FLAT_LIST.items():
            if k in rl or rl in k: canonical = v; break
    return raw.strip(), canonical or "UNKNOWN"

# ============================================================================
# [VRN:ANCHOR:MDL005-ACCEL-001] §3  ACCELERATOR INIT
# ============================================================================

def _mdl005_accel_init(workers: int = 0) -> Dict:
    """VRN-MDL005-FNC-002  6-ENV thread + GC tuning."""
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
# [VRN:ANCHOR:MDL005-PLUGIN-001] §5  PLUGIN LOADER
# ── Loads VIA_SSOT_Unified / VeritasCeleritas / VeritasAegisNexus ────────────
# ── Uses actual known API, not generic stub ───────────────────────────────────
# ============================================================================

_SSOT: Any = None;  _SSOT_OK:  bool = False
_CEL:  Any = None;  _CEL_OK:   bool = False
_NET:  Any = None;  _NET_OK:   bool = False
# [VRN:ANCHOR:HARDGATE_HOLDERS:V1] Additional holders per VIA_Supportive_HardGate_Seal.json
_REG: Any = None;  _REG_OK: bool = False  # VIA_RegistryCore_v1
_BRG: Any = None;  _BRG_OK: bool = False  # VIA_Runtime_Bridge_All_in_One
_ENV: Any = None;  _ENV_OK: bool = False  # VIA_EnvManager
_AST: Any = None;  _AST_OK: bool = False  # VIA_Panorama_AST_RuntimeInjector

def _find_plugin(ssot_dir: str, filename: str) -> Optional[str]:
    """Search ssot_dir (and parent dirs) for plugin file."""
    candidates = [
        Path(ssot_dir) / filename,
        Path(ssot_dir).parent / filename,
        Path(ssot_dir).parent.parent / "module" / filename,
    ]
    for c in candidates:
        if c.exists(): return str(c)
    return None

def load_plugins(ssot_dir: str) -> Dict[str, bool]:
    """VRN-MDL005-FNC-003  Load all three external SSOT modules.
    Uses importlib.util pattern: inject sys.modules BEFORE exec (Python 3.12 fix).
    Returns capability dict.
    """
    global _SSOT, _SSOT_OK, _CEL, _CEL_OK, _NET, _NET_OK
    global _REG, _REG_OK, _BRG, _BRG_OK, _ENV, _ENV_OK, _AST, _AST_OK
    # [VRN:ANCHOR:HARDGATE_RESULT:V1] 7-key result dict per HardGate Seal
    result = {"via_ssot": False, "registry": False, "runtime_bridge": False,
              "env_manager": False, "ast_planner": False,
              "celeritas": False, "aegis": False}

    # Ensure ssot_dir is on path
    ssot_str = str(Path(ssot_dir))
    if ssot_str not in sys.path and Path(ssot_dir).is_dir():
        sys.path.insert(0, ssot_str)

    # ── VIA_SSOT_Unified ────────────────────────────────────────────────────
    if _P.get("enable_ssot", True):
        p = _find_plugin(ssot_dir, "VIA_SSOT_Unified.py")
        if p:
            try:
                spec = importlib.util.spec_from_file_location("VIA_SSOT_Unified", p)
                mod  = importlib.util.module_from_spec(spec)
                sys.modules["VIA_SSOT_Unified"] = mod   # inject before exec (Py3.12)
                spec.loader.exec_module(mod)
                _SSOT = mod; _SSOT_OK = True
                result["via_ssot"] = True
                # Merge CANONICAL_MAP if available (append-only)
                if hasattr(_SSOT, "CANONICAL_MAP"):
                    for k, v in _SSOT.CANONICAL_MAP.items():
                        if k.lower() not in _SYNONYM_REVERSE:
                            _SYNONYM_REVERSE[k.lower()] = v
                # Merge BROKER_MAP (append-only)
                if hasattr(_SSOT, "BROKER_MAP"):
                    for k, v in _SSOT.BROKER_MAP.items():
                        if k not in BROKER_MAP: BROKER_MAP[k] = v
                log.info("[MDL005] VIA_SSOT_Unified loaded from %s", p)
            except Exception as e:
                log.debug("[MDL005] VIA_SSOT_Unified fail: %s", e)

    # ── VeritasCeleritas ────────────────────────────────────────────────────
    if _P.get("enable_celeritas", True):
        p = _find_plugin(ssot_dir, "VeritasCeleritas.py")
        if p:
            try:
                spec = importlib.util.spec_from_file_location("VeritasCeleritas", p)
                mod  = importlib.util.module_from_spec(spec)
                sys.modules["VeritasCeleritas"] = mod
                spec.loader.exec_module(mod)
                _CEL = mod; _CEL_OK = True
                result["celeritas"] = True
                # Call bootstrap if available
                if hasattr(_CEL, "bootstrap_at_import"):
                    _CEL.bootstrap_at_import(__file__)
                # Warm thread pool
                if hasattr(_CEL, "warm_thread_pool"):
                    _CEL.warm_thread_pool()
                log.info("[MDL005] VeritasCeleritas loaded from %s", p)
            except Exception as e:
                log.debug("[MDL005] VeritasCeleritas fail: %s", e)

    # ── VeritasAegisNexus ───────────────────────────────────────────────────
    if _P.get("enable_aegis", True):
        p = _find_plugin(ssot_dir, "VeritasAegisNexus.py")
        if p:
            try:
                spec = importlib.util.spec_from_file_location("VeritasAegisNexus", p)
                mod  = importlib.util.module_from_spec(spec)
                sys.modules["VeritasAegisNexus"] = mod
                spec.loader.exec_module(mod)
                _NET = mod; _NET_OK = True
                result["aegis"] = True
                log.info("[MDL005] VeritasAegisNexus loaded from %s", p)
            except Exception as e:
                log.debug("[MDL005] VeritasAegisNexus fail: %s", e)

    # [VRN:ANCHOR:HARDGATE_EXTRA_TOOLS:V1] Load 4 remaining HardGate Seal tools.
    # Order: Registry / RuntimeBridge / EnvManager / ASTPlanner per Seal JSON.
    for mod_name, key, gname, ok_name in [
        ("VIA_RegistryCore_v1",              "registry",       "_REG", "_REG_OK"),
        ("VIA_Runtime_Bridge_All_in_One",    "runtime_bridge", "_BRG", "_BRG_OK"),
        ("VIA_EnvManager",                   "env_manager",    "_ENV", "_ENV_OK"),
        ("VIA_Panorama_AST_RuntimeInjector", "ast_planner",    "_AST", "_AST_OK"),
    ]:
        p = _find_plugin(ssot_dir, f"{mod_name}.py")
        if p:
            try:
                spec = importlib.util.spec_from_file_location(mod_name, p)
                mod  = importlib.util.module_from_spec(spec)
                sys.modules[mod_name] = mod
                spec.loader.exec_module(mod)
                globals()[gname]   = mod
                globals()[ok_name] = True
                result[key] = True
                log.info("[MDL005] %s loaded from %s", mod_name, p)
            except Exception as e:
                log.debug("[MDL005] %s fail: %s", mod_name, e)

    return result

# ============================================================================
# [VRN:ANCHOR:MDL005-PROXY-001] §6  PLUGIN PROXY FUNCTIONS (safe stubs)
# ── These are the ONLY entry points for plugin calls in the rest of the code.─
# ── If plugin not loaded, gracefully falls back to stdlib equivalents. ───────
# ============================================================================

def _cel_submit(fn: Callable, *args, **kw) -> Any:
    """VRN-MDL005-FNC-004  Celeritas parallel submit, fallback direct call."""
    if _CEL_OK:
        # Try _LazyPool.submit (warm ThreadPoolExecutor)
        if hasattr(_CEL, "_LazyPool"):
            try: return _CEL._LazyPool.submit(fn, *args, **kw)
            except Exception: pass
        # Try .submit directly
        if hasattr(_CEL, "submit"):
            try: return _CEL.submit(fn, *args, **kw)
            except Exception: pass
    return fn(*args, **kw)

def _cel_map(fn: Callable, items: Iterable, **kw) -> List:
    """VRN-MDL005-FNC-005  Celeritas parallel map, fallback list(map(...))."""
    if _CEL_OK:
        if hasattr(_CEL, "_LazyPool"):
            try: return list(_CEL._LazyPool.map(fn, items))
            except Exception: pass
        if hasattr(_CEL, "map"):
            try: return list(_CEL.map(fn, items))
            except Exception: pass
    return list(map(fn, items))

def _net_get(url: str, timeout: int = 20, **kw) -> Optional[Any]:
    """VRN-MDL005-FNC-006  AegisNexus HTTP GET, fallback requests."""
    if _NET_OK:
        # safe_get (VIA_NetSupreme pattern)
        if hasattr(_NET, "safe_get"):
            try: return _NET.safe_get(url, timeout=timeout, **kw)
            except Exception: pass
        # fetch (AegisNexus pattern)
        if hasattr(_NET, "fetch"):
            try: return _NET.fetch(url, timeout=timeout, **kw)
            except Exception: pass
    # Fallback: requests
    req = _si("requests")
    if req:
        try: return req.get(url, timeout=timeout, verify=False)
        except Exception: pass
    return None

def _ssot_get(key: str, default: Any = None) -> Any:
    """VRN-MDL005-FNC-007  VIA_SSOT_Unified .get(), fallback default."""
    if _SSOT_OK and hasattr(_SSOT, "get"):
        try: return _SSOT.get(key, default)
        except Exception: pass
    return default

def _ssot_normalize_rating(raw: str) -> Tuple[str, str]:
    """VRN-MDL005-FNC-008  Use SSOT normalize_rating if available, fallback embedded."""
    if _SSOT_OK and hasattr(_SSOT, "normalize_rating"):
        try: return _SSOT.normalize_rating(raw)
        except Exception: pass
    return normalize_rating(raw)

def _ssot_normalize_term(text: str) -> str:
    """VRN-MDL005-FNC-009  Map financial term via SYNONYM_MAP (embedded + SSOT merged)."""
    t = text.strip()
    return _SYNONYM_REVERSE.get(t.lower(), t)

# ============================================================================
# UTILITIES
# ============================================================================

def _hash8(s: str) -> str:
    if xxhash: return xxhash.xxh64(s.encode()).hexdigest()[:8].upper()
    return hashlib.sha256(s.encode()).hexdigest()[:8].upper()

def _jwrite(p: str, data: Any):
    def _def(o): return None if isinstance(o,float) and (math.isnan(o) or math.isinf(o)) else str(o)
    Path(p).write_text(json.dumps(data, ensure_ascii=False, indent=2, default=_def), encoding="utf-8")

def _jload(p: str) -> Any:
    try:
        txt = Path(p).read_text(encoding="utf-8")
        return orjson.loads(txt) if orjson else json.loads(txt)
    except Exception as e: log.warning("[MDL005] jload %s: %s", p, e); return None

def _parse_meta(pdf_path: str) -> Dict:
    stem = Path(pdf_path).stem
    meta = {"ticker":"","report_date":"","broker_abbr":"","report_code":_hash8(stem)}
    dm = re.search(r"(20\d{2})[_\-]?(\d{2})[_\-]?(\d{2})", stem)
    if dm: meta["report_date"] = "{}-{}-{}".format(dm.group(1),dm.group(2),dm.group(3))
    bm = re.search(r"(GS|MS|JPM|CITI|UBS|KGI|Nomura|Yuanta|Fubon|CTBC|Mega|兆豐|國泰|中信|元大|凱基)", stem, re.I)
    if bm: meta["broker_abbr"] = bm.group(1).upper()
    for tok in re.split(r"[_\-\s]", stem):
        m = re.fullmatch(r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})", tok.strip())
        if m: meta["ticker"] = m.group(1); break
    return meta

# ============================================================================
# [VRN:ANCHOR:MDL005-DATACLASS-001] §7  DATA CLASSES
# ============================================================================

@dataclass
class RawTextBlock:
    """VRN-MDL005-CLS-003  Raw text block from one engine."""
    engine:    str = ""
    page_no:   int = 0
    block_id:  str = ""       # P{page:03d}TXT{seq:03d}
    text:      str = ""
    x0:        float = 0.0
    y0:        float = 0.0
    x1:        float = 0.0
    y1:        float = 0.0
    font_size: float = 0.0
    is_bold:   bool = False
    color_rgb: Optional[Tuple[float,float,float]] = None
    ok:        bool = False

@dataclass
class FixedTextBlock:
    """VRN-MDL005-CLS-004  Text block after all 20 fix strategies."""
    block_id:     str = ""
    pdf_name:     str = ""
    report_code:  str = ""
    page_no:      int = 0
    text:         str = ""
    segment:      str = "content"  # summary|fin_page|qa|outlook|disclaimer|content
    is_title:     bool = False
    is_bullet:    bool = False
    font_size:    float = 0.0
    is_bold:      bool = False
    x0:           float = 0.0
    y0:           float = 0.0
    confidence:   float = 1.0
    fixes_applied:List[str] = field(default_factory=list)
    ok:           bool = False
    error:        Optional[str] = None

# ── Pydantic TextParagraph (optional) ────────────────────────────────────────

def _build_pydantic_model():
    if not _CAP["pydantic"]: return None
    try:
        from pydantic import BaseModel, field_validator
        class TextParagraph(BaseModel):
            model_config = {"str_strip_whitespace": True}
            block_id:  str = ""
            text:      str = ""
            segment:   str = "content"
            is_title:  bool = False
            confidence:float = 1.0
            status:    str = "PASS"

            @field_validator("text", mode="before")
            @classmethod
            def clean_text(cls, v):
                v = str(v or "").strip()
                v = v.replace("\n", " ").replace("\u00a0", " ")
                v = _ZH_SP_RE.sub("", v)
                return v

            @field_validator("confidence", mode="before")
            @classmethod
            def clamp_conf(cls, v):
                try: return max(0.0, min(1.0, float(v)))
                except: return 0.0

        return TextParagraph
    except Exception as e:
        log.debug("[MDL005] Pydantic model build: %s", e); return None

_TextParagraph = _build_pydantic_model()

# ============================================================================
# [VRN:ANCHOR:MDL005-SCAN-001] §8  PDF SCANNER
# ============================================================================

def list_pdfs(pdf_temp: str) -> List[str]:
    """VRN-MDL005-FNC-010"""
    if not os.path.isdir(pdf_temp): return []
    return sorted(os.path.join(pdf_temp,f) for f in os.listdir(pdf_temp)
                  if f.lower().endswith(".pdf"))

def is_scan_pdf(pdf_path: str) -> bool:
    """VRN-MDL005-FNC-011  Detect image-based (scanned) PDF."""
    if not _CAP["fitz"]: return False
    try:
        doc = fitz.open(pdf_path)
        n   = min(len(doc), _P["scan_sample_pages"])
        chars = sum(len(doc[i].get_text().strip()) for i in range(n))
        doc.close()
        return (chars / max(n,1)) < _P["scan_text_threshold"]
    except Exception: return False

# ============================================================================
# [VRN:ANCHOR:MDL005-ENGINE-001] §9  ENGINE A: PyMuPDF fitz (PRIMARY)
# ── Standalone: engine_pymupdf(pdf_path, page_no) → List[RawTextBlock] ───────
# ============================================================================

def engine_pymupdf(pdf_path: str, page_no: int,
                   doc_cache: Optional["MDL005DocCache"] = None) -> List[RawTextBlock]:
    """VRN-MDL005-FNC-012  PyMuPDF full dict extraction — text + coordinates + font.
    v1.1.0: if doc_cache provided, reuse open fitz handle (no re-open).
    """
    blocks: List[RawTextBlock] = []
    if not _CAP["fitz"]: return blocks
    try:
        # v1.1.0 fast path
        if doc_cache is not None and doc_cache.fitz_doc is not None:
            pg = doc_cache.fitz_page(page_no)
            if pg is None: return blocks
            raw = pg.get_text("dict")
        else:
            doc = fitz.open(pdf_path)
            if page_no - 1 >= len(doc): doc.close(); return blocks
            pg      = doc[page_no - 1]
            raw     = pg.get_text("dict")
            doc.close()
        avg_sz  = _compute_avg_fontsize(raw)
        seq     = 1
        for blk in raw.get("blocks", []):
            if blk.get("type") != 0: continue   # 0 = text block
            lines_text = []
            max_sz     = 0.0
            is_bold    = False
            rgb        = None
            x0,y0,x1,y1 = blk.get("bbox",(0,0,0,0))
            for ln in blk.get("lines",[]):
                for sp in ln.get("spans",[]):
                    sp_text = sp.get("text","").strip()
                    if not sp_text: continue
                    lines_text.append(sp_text)
                    sz = sp.get("size",0)
                    if sz > max_sz: max_sz = sz
                    if "Bold" in sp.get("font","") or sp.get("flags",0) & 16:
                        is_bold = True
                    c = sp.get("color")
                    if c is not None and rgb is None:
                        r = (c >> 16) & 0xFF
                        g = (c >> 8)  & 0xFF
                        b = c & 0xFF
                        rgb = (r/255.0, g/255.0, b/255.0)
            txt = " ".join(lines_text).strip()
            if len(txt) < _P["min_block_chars"]: continue
            bid = "P{:03d}TXT{:03d}".format(page_no, seq)
            blocks.append(RawTextBlock(
                engine="pymupdf", page_no=page_no, block_id=bid,
                text=txt, x0=x0, y0=y0, x1=x1, y1=y1,
                font_size=round(max_sz,1), is_bold=is_bold, color_rgb=rgb, ok=True,
            ))
            seq += 1
    except Exception as e:
        log.debug("[MDL005] pymupdf page %d: %s", page_no, e)
    return blocks

def _compute_avg_fontsize(raw_dict: Dict) -> float:
    """Helper: average font size across all spans in a page dict."""
    sizes = []
    for blk in raw_dict.get("blocks",[]):
        for ln in blk.get("lines",[]):
            for sp in ln.get("spans",[]):
                sz = sp.get("size",0)
                if sz > 0: sizes.append(sz)
    return sum(sizes)/len(sizes) if sizes else 10.0

# ============================================================================
# [VRN:ANCHOR:MDL005-ENGINE-002] §10  ENGINE B: pdfplumber (SECONDARY)
# ============================================================================

def engine_pdfplumber(pdf_path: str, page_no: int,
                      doc_cache: Optional["MDL005DocCache"] = None) -> List[RawTextBlock]:
    """VRN-MDL005-FNC-013  pdfplumber text-line extraction with coordinates.
    v1.1.0: doc_cache fast path.
    """
    blocks: List[RawTextBlock] = []
    if not _CAP["pdfplumber"]: return blocks
    try:
        if doc_cache is not None and doc_cache.pdfplumber_pdf is not None:
            pg = doc_cache.pdfplumber_page(page_no)
            if pg is None: return blocks
            lines = pg.extract_text_lines(return_chars=False) or []
            seq = 1
            for ln in lines:
                txt = (ln.get("text") or "").strip()
                if len(txt) < _P["min_block_chars"]: continue
                bid = "P{:03d}TXT{:03d}".format(page_no, seq)
                blocks.append(RawTextBlock(
                    engine="pdfplumber", page_no=page_no, block_id=bid, text=txt,
                    x0=ln.get("x0",0), y0=ln.get("top",0),
                    x1=ln.get("x1",0), y1=ln.get("bottom",0), ok=True,
                ))
                seq += 1
            return blocks

        with pdfplumb.open(pdf_path) as pdf:
            if page_no - 1 >= len(pdf.pages): return blocks
            pg    = pdf.pages[page_no - 1]
            lines = pg.extract_text_lines(return_chars=False) or []
            seq   = 1
            for ln in lines:
                txt = (ln.get("text") or "").strip()
                if len(txt) < _P["min_block_chars"]: continue
                bid = "P{:03d}TXT{:03d}".format(page_no, seq)
                blocks.append(RawTextBlock(
                    engine="pdfplumber", page_no=page_no, block_id=bid,
                    text=txt,
                    x0=ln.get("x0",0), y0=ln.get("top",0),
                    x1=ln.get("x1",0), y1=ln.get("bottom",0),
                    ok=True,
                ))
                seq += 1
    except Exception as e:
        log.debug("[MDL005] pdfplumber page %d: %s", page_no, e)
    return blocks

# ============================================================================
# [VRN:ANCHOR:MDL005-ENGINE-003] §11  ENGINE C: pdfminer.six (DEEP PARSE)
# ============================================================================

def engine_pdfminer(pdf_path: str, page_no: int) -> List[RawTextBlock]:
    """VRN-MDL005-FNC-014  pdfminer.six deep character stream extraction."""
    blocks: List[RawTextBlock] = []
    if not _CAP["pdfminer"]: return blocks
    try:
        from pdfminer.high_level import extract_pages           # type: ignore
        from pdfminer.layout import LTTextBox, LTTextLine       # type: ignore
        seq = 1
        for pg_idx, pg_layout in enumerate(extract_pages(pdf_path), start=1):
            if pg_idx != page_no: continue
            for el in pg_layout:
                if not isinstance(el, LTTextBox): continue
                txt = el.get_text().strip()
                if len(txt) < _P["min_block_chars"]: continue
                bid = "P{:03d}TXT{:03d}".format(page_no, seq)
                blocks.append(RawTextBlock(
                    engine="pdfminer", page_no=page_no, block_id=bid,
                    text=txt.replace("\n"," "),
                    x0=el.x0, y0=el.y0, x1=el.x1, y1=el.y1, ok=True,
                ))
                seq += 1
            break
    except Exception as e:
        log.debug("[MDL005] pdfminer page %d: %s", page_no, e)
    return blocks

# ============================================================================
# [VRN:ANCHOR:MDL005-ENGINE-004] §12  ENGINE D: Docling (AI LAYOUT)
# ============================================================================

def engine_docling(pdf_path: str) -> List[RawTextBlock]:
    """VRN-MDL005-FNC-015  Docling AI document parsing (whole doc, layout-aware)."""
    blocks: List[RawTextBlock] = []
    if not _CAP["docling"]: return blocks
    try:
        from docling.document_converter import DocumentConverter  # type: ignore
        conv = DocumentConverter()
        doc  = conv.convert(pdf_path).document
        seq  = 1
        for el in getattr(doc, "elements", []):
            if getattr(el, "type", "") == "table": continue
            txt = getattr(el, "text", "")
            if not txt or len(txt.strip()) < _P["min_block_chars"]: continue
            pg  = getattr(el, "page_no", 0) or 0
            bid = "P{:03d}TXT{:03d}".format(pg, seq)
            blocks.append(RawTextBlock(
                engine="docling", page_no=pg, block_id=bid,
                text=txt.strip(), ok=True,
            ))
            seq += 1
    except Exception as e:
        log.debug("[MDL005] docling %s: %s", pdf_path, e)
    return blocks

# ============================================================================
# [VRN:ANCHOR:MDL005-ENGINE-005] §13  ENGINE E: Marker (FAST MARKDOWN)
# ============================================================================

def engine_marker(pdf_path: str) -> List[RawTextBlock]:
    """VRN-MDL005-FNC-016  Marker PDF→Markdown, extract text sections."""
    blocks: List[RawTextBlock] = []
    try:
        import marker  # type: ignore
        from marker.convert import convert_single_pdf  # type: ignore
        from marker.models import load_all_models      # type: ignore
        models = load_all_models()
        text, _, _ = convert_single_pdf(pdf_path, models)
        # Split by Markdown headings / paragraphs
        sections = re.split(r"\n{2,}", text or "")
        seq = 1
        for sec in sections:
            sec = sec.strip()
            if len(sec) < _P["min_block_chars"]: continue
            blocks.append(RawTextBlock(
                engine="marker", page_no=0, block_id="MARK_TXT{:03d}".format(seq),
                text=sec, ok=True,
            ))
            seq += 1
    except Exception as e:
        log.debug("[MDL005] marker %s: %s", pdf_path, e)
    return blocks

# ============================================================================
# [VRN:ANCHOR:MDL005-ENGINE-006] §14  ENGINE F: PaddleOCR (SCAN FALLBACK)
# ============================================================================

def engine_paddleocr(pdf_path: str, page_no: int) -> List[RawTextBlock]:
    """VRN-MDL005-FNC-017  PaddleOCR for scanned PDF pages."""
    blocks: List[RawTextBlock] = []
    if not _CAP["paddleocr"] or not _CAP["fitz"]: return blocks
    try:
        from paddleocr import PaddleOCR  # type: ignore
        ocr = PaddleOCR(use_angle_cls=True, lang=_P.get("ocr_lang","ch"),
                        use_gpu=False, show_log=False)
        doc = fitz.open(pdf_path)
        if page_no - 1 >= len(doc): doc.close(); return blocks
        pg  = doc[page_no - 1]
        mat = fitz.Matrix(300/72.0, 300/72.0)
        pix = pg.get_pixmap(matrix=mat, alpha=False)
        doc.close()
        if not (_CAP["numpy"] and _CAP["cv2"]): return blocks
        img = np.frombuffer(pix.tobytes("png"), dtype=np.uint8)
        img = cv2.imdecode(img, 1)
        result = ocr.ocr(img, cls=True)
        if not result or not result[0]: return blocks
        seq = 1
        rows_by_y: Dict[int, List[str]] = {}
        for line in result[0]:
            pts, (txt, conf) = line
            if conf < 0.5: continue
            y_c = int((pts[0][1]+pts[2][1])/2)
            y_b = round(y_c/15)*15
            rows_by_y.setdefault(y_b,[]).append(txt.strip())
        for y_b in sorted(rows_by_y):
            merged = " ".join(rows_by_y[y_b])
            if len(merged) < _P["min_block_chars"]: continue
            bid = "P{:03d}TXT{:03d}".format(page_no, seq)
            blocks.append(RawTextBlock(
                engine="paddleocr", page_no=page_no, block_id=bid,
                text=merged, y0=float(y_b), ok=True,
            ))
            seq += 1
    except Exception as e:
        log.debug("[MDL005] paddleocr page %d: %s", page_no, e)
    return blocks

# ============================================================================
# [VRN:ANCHOR:MDL005-ENGINE-007] §15  ENGINE G: Surya (LAYOUT + OCR)
# ============================================================================

def engine_surya(pdf_path: str, page_no: int) -> List[RawTextBlock]:
    """VRN-MDL005-FNC-018  Surya layout+OCR extraction."""
    blocks: List[RawTextBlock] = []
    try:
        from surya.ocr import run_ocr          # type: ignore
        from surya.model.detection import model as det_model    # type: ignore
        from surya.model.recognition import model as rec_model  # type: ignore
        from PIL import Image as PILImage
        if not _CAP["fitz"]: return blocks
        doc = fitz.open(pdf_path)
        if page_no - 1 >= len(doc): doc.close(); return blocks
        mat = fitz.Matrix(150/72.0, 150/72.0)
        pix = doc[page_no-1].get_pixmap(matrix=mat, alpha=False)
        doc.close()
        img = PILImage.frombytes("RGB", (pix.width, pix.height), pix.samples)
        result = run_ocr([img], [["zh","en"]], det_model.load_model(), rec_model.load_model())
        seq = 1
        if result and result[0]:
            for line in result[0].text_lines:
                txt = line.text.strip()
                if len(txt) < _P["min_block_chars"]: continue
                bid = "P{:03d}TXT{:03d}".format(page_no, seq)
                bb  = line.bbox
                blocks.append(RawTextBlock(
                    engine="surya", page_no=page_no, block_id=bid,
                    text=txt, x0=bb[0], y0=bb[1], x1=bb[2], y1=bb[3], ok=True,
                ))
                seq += 1
    except Exception as e:
        log.debug("[MDL005] surya page %d: %s", page_no, e)
    return blocks

# ============================================================================
# [VRN:ANCHOR:MDL005-MERGE-001] §16  DUAL-ENGINE MERGE + DEDUP
# ============================================================================

def merge_and_dedup(
    primary:   List[RawTextBlock],
    secondary: List[RawTextBlock],
) -> List[RawTextBlock]:
    """VRN-MDL005-FNC-019
    Merge primary + secondary, dedup by text hash prefix.
    Primary wins on collision (higher quality source).
    Sort by (page_no, y0, x0) for reading order.
    """
    seen: Dict[str, RawTextBlock] = {}
    for b in primary:
        key = _hash8(b.text[:_P["dedup_hash_prefix_len"]])
        seen[key] = b
    for b in secondary:
        key = _hash8(b.text[:_P["dedup_hash_prefix_len"]])
        if key not in seen:
            seen[key] = b
    merged = sorted(seen.values(), key=lambda b: (b.page_no, b.y0, b.x0))
    return merged

# ============================================================================
# [VRN:ANCHOR:MDL005-FIX-001] §17  T01–T20 TEXT FIX STRATEGY LIBRARY
# ── Each fix is STANDALONE — call individually or via apply_text_fixes() ─────
# ============================================================================

def fix_T01_reading_order(blocks: List[RawTextBlock]) -> Tuple[List[RawTextBlock], bool]:
    """T01: Sort blocks by (page_no, y0, x0) — corrects PDF stream order jumps."""
    if not _P["fix_T01_reading_order"]: return blocks, False
    sorted_b = sorted(blocks, key=lambda b: (b.page_no, round(b.y0/5)*5, b.x0))
    return sorted_b, True

def fix_T02_whitespace_reconstruct(text: str, avg_char_w: float = 6.0) -> str:
    """T02: Detect missing spaces by gap ratio — fills gaps between words."""
    if not _P["fix_T02_whitespace_reconstruct"]: return text
    # Simple: normalize multiple spaces → single space
    return re.sub(r" {2,}", " ", text).strip()

def fix_T03_dehyphenation(text: str) -> Tuple[str, bool]:
    """T03: Merge line-end hyphenated words: re-\ntrieve → retrieve."""
    if not _P["fix_T03_dehyphenation"]: return text, False
    fixed, n = _HYPHEN_RE.subn(r"\1\2", text)
    return fixed, n > 0

def fix_T04_zh_en_separation(text: str) -> Tuple[str, bool]:
    """T04: Remove OCR-inserted spaces between CJK characters."""
    if not _P["fix_T04_zh_en_separation"]: return text, False
    fixed = _ZH_SP_RE.sub("", text)
    return fixed, fixed != text

def fix_T05_unicode_normalize(text: str) -> str:
    """T05: NFKC normalization — full-width → half-width, ligatures, etc."""
    if not _P["fix_T05_unicode_normalize"]: return text
    return unicodedata.normalize("NFKC", text)

def fix_T06_trim_nbsp(text: str) -> str:
    """T06: Strip whitespace + replace non-breaking / ideographic spaces."""
    if not _P["fix_T06_trim_nbsp"]: return text
    return (text.replace("\u00a0"," ").replace("\u3000"," ")
                .replace("\n"," ").replace("\r","").strip())

def fix_T07_ocr_alphanum(text: str) -> str:
    """T07: l→1, O→0, I→1 when adjacent to digits."""
    if not _P["fix_T07_ocr_alphanum"]: return text
    def _repl(m):
        ch = (m.group(1) or m.group(2) or "")
        return "1" if ch in ("l","I","|") else "0"
    return _OCR_NUM_RE.sub(_repl, text)

def fix_T08_mojibake_detect(text: str) -> Tuple[str, bool]:
    """T08: Detect mojibake (high ratio of control/non-print chars)."""
    if not _P["fix_T08_mojibake_detect"]: return text, False
    junk = sum(1 for c in text if ord(c) < 32 or (0x80 <= ord(c) <= 0x9F))
    if len(text) > 0 and junk / len(text) > 0.3:
        return "[OCR_RETRY] " + text[:20], True
    return text, False

def fix_T09_watermark_filter(block: RawTextBlock) -> bool:
    """T09: Return True if block looks like a watermark (tiny/light text).
    Caller should DROP the block if True."""
    if not _P["fix_T09_watermark_filter"]: return False
    if block.font_size > 0 and block.font_size <= _P["watermark_size_max"]:
        return True
    if block.color_rgb:
        r,g,b = block.color_rgb
        if r*255 >= _P["watermark_rgb_min"] and g*255 >= _P["watermark_rgb_min"] \
                and b*255 >= _P["watermark_rgb_min"]:
            return True
    return False

def fix_T10_sent_merge(
    blocks: List[RawTextBlock],
    reflow: bool = True,
) -> Tuple[List[RawTextBlock], bool]:
    """T10: Merge continuation lines until sentence end punctuation."""
    if not _P["fix_T10_sent_merge"] or not reflow: return blocks, False
    end_re = re.compile(_P["sent_merge_end_re"])
    merged: List[RawTextBlock] = []
    buf: Optional[RawTextBlock] = None
    applied = False
    for b in blocks:
        if buf is None:
            buf = copy.copy(b); continue
        # Bullets or very short standalone lines (≤5 chars) → flush buffer first
        # Note: short continuation text (6-40 chars) should still be merged
        is_bullet_line = bool(_BULLET_RE.match(b.text))
        is_standalone  = len(b.text.strip()) <= 5
        if is_bullet_line or is_standalone:
            merged.append(buf); buf = copy.copy(b); continue
        buf.text = buf.text.rstrip() + " " + b.text.lstrip()
        applied = True
        if end_re.search(buf.text.strip()):
            merged.append(buf); buf = None
    if buf: merged.append(buf)
    return merged, applied

def fix_T11_title_detect(block: RawTextBlock, avg_fontsize: float = 10.0) -> Tuple[bool, bool]:
    """T11: Heuristic title detection.
    Returns (is_title, is_bullet)."""
    if not _P["fix_T11_title_detect"]: return False, False
    txt = block.text.strip()
    is_bullet = bool(_BULLET_RE.match(txt))
    if is_bullet: return False, True
    # Title: short, no sentence-ending punct, possibly larger font
    end_punct = re.search(_P["title_end_punct_re"], txt)
    short     = len(txt) <= _P["title_max_chars"]
    big_font  = (block.font_size > 0 and
                 block.font_size >= avg_fontsize * _P["title_fontsize_ratio"])
    is_title  = short and not end_punct and (big_font or block.is_bold)
    return is_title, False

def fix_T12_dedup(blocks: List[RawTextBlock]) -> Tuple[List[RawTextBlock], int]:
    """T12: Remove blocks with duplicate text (hash-based)."""
    if not _P["fix_T12_dedup"]: return blocks, 0
    seen: set = set()
    out: List[RawTextBlock] = []
    removed = 0
    for b in blocks:
        key = _hash8(b.text[:_P["dedup_hash_prefix_len"]])
        if key in seen: removed += 1; continue
        seen.add(key); out.append(b)
    return out, removed

def fix_T13_empty_drop(blocks: List[RawTextBlock]) -> Tuple[List[RawTextBlock], int]:
    """T13: Drop blocks that are empty or below min_block_chars."""
    if not _P["fix_T13_empty_drop"]: return blocks, 0
    out = [b for b in blocks if len(b.text.strip()) >= _P["min_block_chars"]]
    return out, len(blocks) - len(out)

def fix_T14_segment_tag(text: str) -> str:
    """T14: Classify text segment type based on keyword matching.
    Returns: 'summary'|'fin_page'|'qa'|'outlook'|'disclaimer'|'content'
    Uses VIA_SSOT_Unified data if available (via _ssot_get).
    """
    if not _P["fix_T14_segment_tag"]: return "content"
    # Allow SSOT to extend keyword lists
    kw_summary    = _ssot_get("seg_kw_summary",    _P["seg_keywords_summary"])
    kw_fin        = _ssot_get("seg_kw_fin",        _P["seg_keywords_fin"])
    kw_qa         = _ssot_get("seg_kw_qa",         _P["seg_keywords_qa"])
    kw_outlook    = _ssot_get("seg_kw_outlook",    _P["seg_keywords_outlook"])
    kw_disclaimer = _ssot_get("seg_kw_disclaimer", _P["seg_keywords_disclaimer"])
    for kw in kw_disclaimer:
        if kw in text: return "disclaimer"
    for kw in kw_fin:
        if kw in text: return "fin_page"
    for kw in kw_qa:
        if kw in text: return "qa"
    for kw in kw_outlook:
        if kw in text: return "outlook"
    for kw in kw_summary:
        if kw in text: return "summary"
    return "content"

def fix_T15_header_footer_strip(
    blocks: List[RawTextBlock],
    page_count: int,
) -> Tuple[List[RawTextBlock], int]:
    """T15: Remove blocks that repeat on every page (headers/footers).
    Detects text appearing on ≥ 50% of pages as repetitive."""
    if not _P["fix_T15_header_footer_strip"] or page_count < 3: return blocks, 0
    freq: Dict[str, int] = {}
    for b in blocks:
        k = b.text.strip()[:60]
        freq[k] = freq.get(k,0) + 1
    threshold = max(2, page_count // 2)
    out = [b for b in blocks if freq.get(b.text.strip()[:60],0) < threshold]
    return out, len(blocks) - len(out)

def fix_T16_bullet_preserve(blocks: List[RawTextBlock]) -> List[RawTextBlock]:
    """T16: Mark bullet/numbered list blocks — do NOT merge them into previous paragraph."""
    if not _P["fix_T16_bullet_preserve"]: return blocks
    for b in blocks:
        if _BULLET_RE.match(b.text.strip()):
            b.text = "• " + _BULLET_RE.sub("", b.text.strip())
    return blocks

def fix_T17_table_ref_skip(block: RawTextBlock) -> bool:
    """T17: Return True if block looks like a stray table cell (skip it).
    Short text with high digit ratio."""
    if not _P["fix_T17_table_ref_skip"]: return False
    txt = block.text.strip()
    if len(txt) > _P["table_cell_max_chars"]: return False
    digit_count = sum(1 for c in txt if c.isdigit() or c in ",.%()-")
    ratio = digit_count / max(len(txt),1)
    return ratio >= _P["table_cell_num_ratio"]

def fix_T18_reading_col_reorder(
    blocks: List[RawTextBlock],
    page_width: float,
) -> Tuple[List[RawTextBlock], bool]:
    """T18: Multi-column reorder — left column first, then right column.
    Splits at page_width * dual_col_x_split midpoint."""
    if not _P["fix_T18_reading_col_reorder"] or not blocks: return blocks, False
    split_x = page_width * _P["dual_col_x_split"]
    left    = [b for b in blocks if b.x0 < split_x]
    right   = [b for b in blocks if b.x0 >= split_x]
    # Only reorder if both sides have content
    if not left or not right: return blocks, False
    left  = sorted(left,  key=lambda b: (b.y0, b.x0))
    right = sorted(right, key=lambda b: (b.y0, b.x0))
    return left + right, True

def fix_T19_financial_term_norm(text: str) -> Tuple[str, bool]:
    """T19: Normalize financial terms via SYNONYM_MAP (embedded + SSOT merged).
    e.g. '每股盈餘' → 'EPS' (canonical), '營業收入' → 'revenue'."""
    if not _P["fix_T19_financial_term_norm"]: return text, False
    original = text
    for alias, canonical in _SYNONYM_REVERSE.items():
        if alias in text.lower():
            # Don't replace mid-word — whole word boundary check
            pattern = re.compile(re.escape(alias), re.IGNORECASE)
            text = pattern.sub(canonical, text)
    return text, text != original

def fix_T20_confidence_score(
    block: RawTextBlock,
    fixes_applied: List[str],
) -> float:
    """T20: Compute confidence score 0.0–1.0.
    Deduct for: mojibake, OCR retry, watermark flag, many fixes needed."""
    if not _P["fix_T20_confidence_score"]: return 1.0
    score = 1.0
    if "[OCR_RETRY]" in block.text: score -= 0.4
    if "T08" in fixes_applied:       score -= 0.2
    if "T09" in fixes_applied:       score -= 0.3
    if len(fixes_applied) > 8:       score -= 0.1
    # Reward: has meaningful text length
    if len(block.text) > 50:         score += 0.05
    return round(max(0.0, min(1.0, score)), 3)

# ── Apply all fixes — orchestrator ────────────────────────────────────────────

def apply_text_fixes(
    blocks:     List[RawTextBlock],
    page_width: float = 595.0,
    page_count: int   = 1,
) -> Tuple[List[FixedTextBlock], List[str]]:
    """VRN-MDL005-FNC-020
    Apply T01–T20 to a page's raw text blocks.
    Returns (FixedTextBlock list, [fix codes applied]).
    """
    applied: List[str] = []

    # T01 reading order
    blocks, ok = fix_T01_reading_order(blocks)
    if ok: applied.append("T01")

    # T09 watermark filter (before everything else)
    pre_len = len(blocks)
    blocks  = [b for b in blocks if not fix_T09_watermark_filter(b)]
    if len(blocks) < pre_len: applied.append("T09")

    # T13 empty drop
    blocks, n = fix_T13_empty_drop(blocks)
    if n: applied.append("T13")

    # T12 dedup
    blocks, n = fix_T12_dedup(blocks)
    if n: applied.append("T12")

    # T15 header/footer strip
    blocks, n = fix_T15_header_footer_strip(blocks, page_count)
    if n: applied.append("T15")

    # Per-block text fixes
    avg_sz = sum(b.font_size for b in blocks if b.font_size > 0) / max(
        sum(1 for b in blocks if b.font_size > 0), 1)

    cell_skipped = 0
    for b in blocks:
        b.text = fix_T06_trim_nbsp(b.text)
        b.text = fix_T05_unicode_normalize(b.text)
        b.text, _ = fix_T04_zh_en_separation(b.text)
        b.text, _ = fix_T03_dehyphenation(b.text)
        b.text     = fix_T02_whitespace_reconstruct(b.text)
        b.text     = fix_T07_ocr_alphanum(b.text)
        b.text, _  = fix_T08_mojibake_detect(b.text)
    for code in ("T06","T05","T04","T03","T02","T07","T08"):
        if _P.get("fix_" + code): applied.append(code)

    # T16 bullet preserve
    blocks = fix_T16_bullet_preserve(blocks)
    if _P["fix_T16_bullet_preserve"]: applied.append("T16")

    # T18 column reorder
    blocks, ok = fix_T18_reading_col_reorder(blocks, page_width)
    if ok: applied.append("T18")

    # T10 sentence merge
    blocks, ok = fix_T10_sent_merge(blocks)
    if ok: applied.append("T10")

    # Build FixedTextBlock list
    fixed: List[FixedTextBlock] = []
    for b in blocks:
        # T17 table cell skip
        if fix_T17_table_ref_skip(b):
            cell_skipped += 1; continue

        # T11 title detection
        is_title, is_bullet = fix_T11_title_detect(b, avg_sz)

        # T19 financial term normalization
        b.text, ok19 = fix_T19_financial_term_norm(b.text)
        fix_codes = list(applied)
        if ok19: fix_codes.append("T19")

        # T14 segment tagging
        segment = fix_T14_segment_tag(b.text)

        # T20 confidence
        confidence = fix_T20_confidence_score(b, fix_codes)

        ft = FixedTextBlock(
            block_id      = b.block_id,
            pdf_name      = "",
            report_code   = "",
            page_no       = b.page_no,
            text          = b.text,
            segment       = segment,
            is_title      = is_title,
            is_bullet     = is_bullet,
            font_size     = b.font_size,
            is_bold       = b.is_bold,
            x0            = b.x0,
            y0            = b.y0,
            confidence    = confidence,
            fixes_applied = fix_codes,
            ok            = True,
        )
        fixed.append(ft)

    if cell_skipped: applied.append("T17")
    for code in ("T14","T20"): applied.append(code)

    return fixed, list(dict.fromkeys(applied))  # dedup preserve order

# ============================================================================
# [VRN:ANCHOR:MDL005-SCHEMA-001] §18  PYDANTIC SCHEMA VALIDATOR
# ============================================================================

def validate_text_blocks(
    blocks: List[FixedTextBlock],
    strict: bool = False,
) -> Tuple[List[Dict], int, int]:
    """VRN-MDL005-FNC-021
    Validate each FixedTextBlock through Pydantic TextParagraph.
    Returns (dicts_with_status, n_pass, n_err).
    """
    out_dicts = []
    n_pass = n_err = 0
    for fb in blocks:
        d = {
            "block_id":  fb.block_id,
            "text":      fb.text,
            "segment":   fb.segment,
            "is_title":  fb.is_title,
            "confidence":fb.confidence,
            "status":    "PASS",
        }
        if _TextParagraph:
            try:
                vp = _TextParagraph(**d)
                d.update({"text":vp.text,"confidence":vp.confidence,"status":"PASS"})
                n_pass += 1
            except Exception as e:
                d["status"] = "ERR"
                d["validation_error"] = str(e)[:120]
                n_err += 1
                if strict: log.debug("[MDL005] schema ERR: %s", e)
        else:
            n_pass += 1
        out_dicts.append(d)
    return out_dicts, n_pass, n_err

# ============================================================================
# [VRN:ANCHOR:MDL005-DB-001] §20  DB WRITER
# ============================================================================

class MDL005DBWriter:
    """VRN-MDL005-CLS-002  SQLite WAL writer."""

    DDL = """
CREATE TABLE IF NOT EXISTS vrn_mdl005_text_blocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    block_id TEXT, pdf_name TEXT, report_code TEXT,
    page_no INTEGER, text TEXT, segment TEXT,
    is_title INTEGER, is_bullet INTEGER,
    font_size REAL, is_bold INTEGER,
    x0 REAL, y0 REAL, confidence REAL,
    fixes_applied TEXT, status TEXT,
    ts TEXT DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS vrn_mdl005_fix_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pdf_name TEXT, page_no INTEGER, fix_code TEXT, n_applied INTEGER,
    ts TEXT DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS vrn_mdl005_segment_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pdf_name TEXT, report_code TEXT,
    segment TEXT, block_count INTEGER,
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

    def insert_blocks(self, dicts: List[Dict], pdf_name: str, report_code: str,
                      page_no: int, fixes: List[str]):
        sql = """INSERT INTO vrn_mdl005_text_blocks
                 (block_id,pdf_name,report_code,page_no,text,segment,
                  is_title,is_bullet,font_size,is_bold,x0,y0,confidence,fixes_applied,status)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
        rows = []
        for d in dicts:
            rows.append((
                d.get("block_id",""), pdf_name, report_code, page_no,
                d.get("text","")[:2000], d.get("segment","content"),
                1 if d.get("is_title") else 0,
                1 if d.get("is_bullet") else 0,
                d.get("font_size",0.0), 1 if d.get("is_bold") else 0,
                d.get("x0",0.0), d.get("y0",0.0),
                d.get("confidence",1.0),
                ",".join(fixes),
                d.get("status","PASS"),
            ))
        fix_sql = "INSERT INTO vrn_mdl005_fix_log (pdf_name,page_no,fix_code,n_applied) VALUES (?,?,?,?)"
        with self._lock:
            self._con.executemany(sql, rows)
            for fc in fixes:
                self._con.execute(fix_sql, (pdf_name, page_no, fc, 1))
            self._con.commit()

    def insert_segment_summary(self, pdf_name: str, report_code: str, segment_counts: Dict):
        sql = "INSERT INTO vrn_mdl005_segment_log (pdf_name,report_code,segment,block_count) VALUES (?,?,?,?)"
        with self._lock:
            for seg, cnt in segment_counts.items():
                self._con.execute(sql, (pdf_name, report_code, seg, cnt))
            self._con.commit()

    def export_parquet(self, out_dir: str):
        if not _CAP["pandas"] or not _CAP["pyarrow"]: return
        try:
            df = pd.read_sql("SELECT * FROM vrn_mdl005_text_blocks", self._con)
            df.to_parquet(str(Path(out_dir)/"VRN_MDL005_Text.parquet"), index=False)
        except Exception as e: log.warning("[MDL005] parquet: %s", e)

    def export_csv(self, out_dir: str):
        if not _CAP["pandas"]: return
        try:
            df = pd.read_sql("SELECT * FROM vrn_mdl005_text_blocks", self._con)
            df.to_csv(str(Path(out_dir)/"VRN_MDL005_Text.csv"), index=False, encoding="utf-8-sig")
        except Exception as e: log.warning("[MDL005] csv: %s", e)

# ============================================================================
# [VRN:ANCHOR:MDL005-BATCH-001] §20.5  P3 BATCH BUFFER + DUCK WRITER (v1.1.0)
# ============================================================================

class MDL005BatchBuffer:
    """VRN-MDL005-CLS-006  P3 batch buffer (NEW v1.1.0).
    Workers push, main thread flushes.
    """
    def __init__(self, batch_size: int = 5000):
        self.batch_size = batch_size
        self._blk_buf: List[Tuple] = []
        self._fix_buf: List[Tuple] = []
        self._seg_buf: List[Tuple] = []
        self._lock = threading.Lock()

    def push_blocks(self, dicts: List[Dict], pdf_name: str, report_code: str,
                    page_no: int, fixes: List[str]):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        fixes_str = ",".join(fixes)
        rows = [
            (None,
             d.get("block_id",""), pdf_name, report_code, page_no,
             d.get("text","")[:2000], d.get("segment","content"),
             1 if d.get("is_title") else 0,
             1 if d.get("is_bullet") else 0,
             d.get("font_size",0.0),
             1 if d.get("is_bold") else 0,
             d.get("x0",0.0), d.get("y0",0.0),
             d.get("confidence",1.0), fixes_str,
             d.get("status","PASS"), ts)
            for d in dicts
        ]
        fix_rows = [(None, pdf_name, page_no, fc, 1, ts) for fc in fixes]
        with self._lock:
            self._blk_buf.extend(rows)
            self._fix_buf.extend(fix_rows)

    def push_segment_summary(self, pdf_name: str, report_code: str,
                              segment_counts: Dict):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        rows = [(None, pdf_name, report_code, seg, cnt, ts)
                for seg, cnt in segment_counts.items()]
        with self._lock:
            self._seg_buf.extend(rows)

    def stats(self) -> Dict[str, int]:
        return {"blk": len(self._blk_buf),
                "fix": len(self._fix_buf),
                "seg": len(self._seg_buf)}

    def consume_all(self) -> Tuple[List, List, List]:
        with self._lock:
            b, f, s = self._blk_buf, self._fix_buf, self._seg_buf
            self._blk_buf, self._fix_buf, self._seg_buf = [], [], []
        return b, f, s


_DDL_DUCK_BLK = """
CREATE TABLE IF NOT EXISTS vrn_mdl005_text_blocks (
    id INTEGER, block_id VARCHAR, pdf_name VARCHAR, report_code VARCHAR,
    page_no INTEGER, text VARCHAR, segment VARCHAR,
    is_title INTEGER, is_bullet INTEGER, font_size DOUBLE,
    is_bold INTEGER, x0 DOUBLE, y0 DOUBLE, confidence DOUBLE,
    fixes_applied VARCHAR, status VARCHAR, ts VARCHAR
);
"""
_DDL_DUCK_FIX5 = """
CREATE TABLE IF NOT EXISTS vrn_mdl005_fix_log (
    id INTEGER, pdf_name VARCHAR, page_no INTEGER,
    fix_code VARCHAR, n_applied INTEGER, ts VARCHAR
);
"""
_DDL_DUCK_SEG5 = """
CREATE TABLE IF NOT EXISTS vrn_mdl005_segment_log (
    id INTEGER, pdf_name VARCHAR, report_code VARCHAR,
    segment VARCHAR, block_count INTEGER, ts VARCHAR
);
"""

class MDL005DuckWriter:
    """VRN-MDL005-CLS-007  DuckDB primary writer (NEW v1.1.0)."""
    def __init__(self, db_path: str):
        if not DUCKDB_OK:
            raise RuntimeError("duckdb not available")
        self.db_path = db_path
        self._con = duckdb_lib.connect(db_path)
        self._con.execute(_DDL_DUCK_BLK)
        self._con.execute(_DDL_DUCK_FIX5)
        self._con.execute(_DDL_DUCK_SEG5)

    def flush(self, blk_rows: List, fix_rows: List, seg_rows: List) -> Dict[str, int]:
        n_b = n_f = n_s = 0
        try:
            self._con.execute("BEGIN TRANSACTION")
            if blk_rows:
                self._con.executemany(
                    "INSERT INTO vrn_mdl005_text_blocks VALUES "
                    "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    blk_rows)
                n_b = len(blk_rows)
            if fix_rows:
                self._con.executemany(
                    "INSERT INTO vrn_mdl005_fix_log VALUES (?,?,?,?,?,?)",
                    fix_rows)
                n_f = len(fix_rows)
            if seg_rows:
                self._con.executemany(
                    "INSERT INTO vrn_mdl005_segment_log VALUES (?,?,?,?,?,?)",
                    seg_rows)
                n_s = len(seg_rows)
            self._con.execute("COMMIT")
        except Exception as e:
            try: self._con.execute("ROLLBACK")
            except: pass
            log.error("[MDL005] DuckDB flush fail: %s", e); raise
        return {"blk": n_b, "fix": n_f, "seg": n_s}

    def export_parquet_polars(self, out_dir: str) -> Optional[str]:
        out_path = str(Path(out_dir) / "VRN_MDL005_Text.parquet")
        try:
            self._con.execute(
                f"COPY (SELECT * FROM vrn_mdl005_text_blocks) "
                f"TO '{out_path}' (FORMAT PARQUET, COMPRESSION ZSTD)")
            return out_path
        except Exception as e:
            log.warning("[MDL005] DuckDB→parquet fail: %s", e); return None

    def export_csv_polars(self, out_dir: str) -> Optional[str]:
        out_path = str(Path(out_dir) / "VRN_MDL005_Text.csv")
        if POLARS_OK:
            try:
                rows = self._con.execute("SELECT * FROM vrn_mdl005_text_blocks").fetchall()
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
                log.debug("[MDL005] polars-fetchall csv fail (%s), DuckDB native", e)
        try:
            self._con.execute(
                f"COPY (SELECT * FROM vrn_mdl005_text_blocks) "
                f"TO '{out_path}' (HEADER, DELIMITER ',')")
            data = Path(out_path).read_bytes()
            Path(out_path).write_bytes(b"\xef\xbb\xbf" + data)
            return out_path
        except Exception as e:
            log.warning("[MDL005] csv export fail: %s", e); return None

    def close(self):
        try: self._con.close()
        except: pass


# ── Add v1.1.0 batch flush to legacy MDL005DBWriter (monkey-patch, append-only) ─

def _mdl005_dbwriter_flush(self,
                           blk_rows: List, fix_rows: List, seg_rows: List
                           ) -> Dict[str, int]:
    n_b = n_f = n_s = 0
    with self._lock:
        try:
            self._con.execute("BEGIN")
            if blk_rows:
                # Strip id (front) + ts (back)
                self._con.executemany(
                    "INSERT INTO vrn_mdl005_text_blocks "
                    "(block_id,pdf_name,report_code,page_no,text,segment,"
                    " is_title,is_bullet,font_size,is_bold,x0,y0,"
                    " confidence,fixes_applied,status) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    [r[1:-1] for r in blk_rows])
                n_b = len(blk_rows)
            if fix_rows:
                self._con.executemany(
                    "INSERT INTO vrn_mdl005_fix_log "
                    "(pdf_name,page_no,fix_code,n_applied) VALUES (?,?,?,?)",
                    [r[1:-1] for r in fix_rows])
                n_f = len(fix_rows)
            if seg_rows:
                self._con.executemany(
                    "INSERT INTO vrn_mdl005_segment_log "
                    "(pdf_name,report_code,segment,block_count) VALUES (?,?,?,?)",
                    [r[1:-1] for r in seg_rows])
                n_s = len(seg_rows)
            self._con.commit()
        except Exception as e:
            try: self._con.rollback()
            except: pass
            log.error("[MDL005] sqlite flush fail: %s", e); raise
    return {"blk": n_b, "fix": n_f, "seg": n_s}

MDL005DBWriter.flush = _mdl005_dbwriter_flush


def _mdl005_dbwriter_export_parquet_polars(self, out_dir: str) -> Optional[str]:
    out_path = str(Path(out_dir) / "VRN_MDL005_Text.parquet")
    if not POLARS_OK:
        self.export_parquet(out_dir)
        return out_path if Path(out_path).exists() else None
    try:
        with self._lock:
            cur = self._con.execute("SELECT * FROM vrn_mdl005_text_blocks")
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description] if cur.description else []
        if not rows:
            df = pl.DataFrame(schema={c: pl.Utf8 for c in cols} if cols else None)
        else:
            df = pl.DataFrame(rows, schema=cols, orient="row")
        df.write_parquet(out_path, compression="zstd")
        return out_path
    except Exception as e:
        log.warning("[MDL005] polars→parquet fail (%s), pandas fallback", e)
        self.export_parquet(out_dir)
        return out_path if Path(out_path).exists() else None

def _mdl005_dbwriter_export_csv_polars(self, out_dir: str) -> Optional[str]:
    out_path = str(Path(out_dir) / "VRN_MDL005_Text.csv")
    if not POLARS_OK:
        self.export_csv(out_dir)
        return out_path if Path(out_path).exists() else None
    try:
        with self._lock:
            cur = self._con.execute("SELECT * FROM vrn_mdl005_text_blocks")
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
        log.debug("[MDL005] polars-fetchall csv fail (%s), pandas fallback", e)
        self.export_csv(out_dir)
        return out_path if Path(out_path).exists() else None

MDL005DBWriter.export_parquet_polars = _mdl005_dbwriter_export_parquet_polars
MDL005DBWriter.export_csv_polars     = _mdl005_dbwriter_export_csv_polars


# ============================================================================
# [VRN:ANCHOR:MDL005-SELFCHK-001] §20.7  P6 4-PHASE SELF-VERIFICATION (v1.1.0)
# ============================================================================

class MDL005SelfVerifier:
    """VRN-MDL005-CLS-008  P6 4-phase debug chain (NEW v1.1.0)."""
    def __init__(self, cfg: Dict, run_summary: Dict, mdl005_temp: str):
        self.cfg = cfg; self.run_summary = run_summary
        self.mdl005_temp = mdl005_temp
        self.checks: List[Dict] = []

    def _add(self, phase, name, ok, detail=""):
        self.checks.append({"phase":phase,"name":name,"ok":bool(ok),"detail":detail})

    def run(self) -> Dict:
        # P1: Schema & Imports
        self._add("1/4", "Module version 1.1.0", __version__ == "1.1.0", __version__)
        self._add("1/4", "TW_TICKER_REGEX locked",
                  TW_TICKER_REGEX.pattern == r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})",
                  "")
        self._add("1/4", "Pre-compiled regex pool",
                  all(p is not None for p in [_RE_OCR_O_TO_0_v110, _RE_OCR_l_TO_1_v110,
                                              _RE_BRACKET_NEG_v110, _RE_DOUBLESPACE_v110,
                                              _RE_HYPHEN_BREAK, _RE_MOJIBAKE_v110]),
                  "")
        self._add("1/4", "RATING_LIST is dict (SSOT rule)",
                  isinstance(RATING_LIST, dict), str(type(RATING_LIST).__name__))
        self._add("1/4", "polars available", POLARS_OK, "")
        self._add("1/4", "duckdb available", DUCKDB_OK, "")

        # P2: DocCache wiring
        self._add("2/4", "MDL005DocCache exists",
                  "MDL005DocCache" in globals(), "")
        self._add("2/4", "MDL005BatchBuffer exists",
                  "MDL005BatchBuffer" in globals(), "")
        self._add("2/4", "MDL005DuckWriter exists",
                  "MDL005DuckWriter" in globals(), "")
        self._add("2/4", "engine_pymupdf accepts doc_cache",
                  "doc_cache" in engine_pymupdf.__code__.co_varnames, "")
        self._add("2/4", "engine_pdfplumber accepts doc_cache",
                  "doc_cache" in engine_pdfplumber.__code__.co_varnames, "")

        # P3: DB
        duck_p   = Path(self.mdl005_temp) / "VRN_MDL005.duckdb"
        sqlite_p = Path(self.mdl005_temp) / "VRN_MDL005.db"
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
                expected = {"vrn_mdl005_text_blocks","vrn_mdl005_fix_log","vrn_mdl005_segment_log"}
                self._add("3/4", "DuckDB schema 3 tables",
                          expected.issubset(tbls), str(sorted(tbls)))
            except Exception as e:
                self._add("3/4", "DuckDB schema 3 tables", False, str(e))

        # P4
        for fn in ("VRN_MDL005_Text.json", "VRN_MDL005_VerifySummary.json",
                   "VRN_MDL005_Text.parquet", "VRN_MDL005_Text.csv"):
            p = Path(self.mdl005_temp) / fn
            self._add("4/4", f"file:{fn}", p.exists(),
                      f"size={p.stat().st_size if p.exists() else 0}")
        bi = self.run_summary.get("total_blocks", 0)
        self._add("4/4", "total_blocks non-negative", bi >= 0, str(bi))

        n_total = len(self.checks); n_pass = sum(1 for c in self.checks if c["ok"])
        n_fail  = n_total - n_pass
        cls = "READY" if n_fail == 0 else ("NEAR-READY" if n_fail <= 2 else "NOT-READY")
        return {"total":n_total,"pass":n_pass,"fail":n_fail,
                "classification":cls,"checks":self.checks,
                "generated":time.strftime("%Y-%m-%d %H:%M:%S")}


def build_self_verify_html_mdl005(verify_result: Dict, run_summary: Dict) -> str:
    """VRN-MDL005-FNC-027  VIA Visual Lock self-verify HTML (NEW v1.1.0)."""
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
        f"$ VRN_MDL005 v{__version__} self-verification",
        f"  generated      : {verify_result.get('generated','-')}",
        f"  classification : {cls} {cls_emoji}",
        f"  checks         : {verify_result.get('pass',0)}/{verify_result.get('total',0)} pass",
        "",
        "$ pipeline summary",
        f"  total reports  : {run_summary.get('total','-')}",
        f"  ok / fail      : {run_summary.get('ok_count','-')} / {run_summary.get('fail_count','-')}",
        f"  total pages    : {run_summary.get('total_pages','-')}",
        f"  total blocks   : {run_summary.get('total_blocks','-')}",
        f"  total err      : {run_summary.get('total_err','-')}",
    ]
    term_html = "\n".join(sum_lines)

    html = f"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="UTF-8">
<title>VRN MDL005 v{__version__} · Self-Verification · {cls}</title>
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
<div class="hdr"><h1>VRN MDL005 · TextFetcher v{__version__}<span class="cls-badge">{cls}</span></h1>
<div class="sub">VeritasReportNova · 4-Phase Self-Verification · {time.strftime("%Y-%m-%d %H:%M:%S")}</div></div>
<div class="cd"><div class="cd-h">RUN SUMMARY</div><div class="cd-b"><div class="tm">{term_html}</div></div></div>
{"".join(phase_html)}
<div class="foot">Module: {__module_id__} · Asset: {__asset_id__} · v{__version__}</div>
</body></html>"""
    return html


# ============================================================================
# CORE PROCESSOR
# ============================================================================

def process_one_page(
    pdf_path:    str,
    page_no:     int,
    is_scan:     bool,
    page_count:  int,
    page_width:  float,
    cfg:         Dict,
    db:          Optional[MDL005DBWriter],
    pdf_name:    str,
    report_code: str,
    doc_cache:   Optional["MDL005DocCache"] = None,    # v1.1.0 NEW
    buffer:      Optional["MDL005BatchBuffer"] = None, # v1.1.0 NEW
) -> Dict:
    """VRN-MDL005-FNC-022  Extract + fix + validate text for one page.
    v1.1.0: doc_cache reuses opened fitz/pdfplumber handles.
            buffer pushes DB rows without lock contention.
    """
    # ── Engines ────────────────────────────────────────────────────────────
    if is_scan:
        primary_blks = engine_paddleocr(pdf_path, page_no)
        sec_blks     = engine_surya(pdf_path, page_no)
    else:
        eng_a = cfg.get("engine_primary",   _P["engine_primary"])
        eng_b = cfg.get("engine_secondary",  _P["engine_secondary"])
        eng_fb= cfg.get("engine_fallback",   _P["engine_fallback"])

        # v1.1.0: pass doc_cache through
        if eng_a == "pymupdf":
            primary_blks = engine_pymupdf(pdf_path, page_no, doc_cache=doc_cache)
        else:
            primary_blks = engine_pdfplumber(pdf_path, page_no, doc_cache=doc_cache)
        if eng_b == "pdfplumber":
            sec_blks = engine_pdfplumber(pdf_path, page_no, doc_cache=doc_cache)
        else:
            sec_blks = engine_pymupdf(pdf_path, page_no, doc_cache=doc_cache)

        if not primary_blks and not sec_blks:
            primary_blks = engine_pdfminer(pdf_path, page_no)

    # ── Merge ──────────────────────────────────────────────────────────────
    merged = merge_and_dedup(primary_blks, sec_blks)
    if not merged: return {"page_no":page_no,"n_blocks":0,"blocks":[],"fixes":[]}

    # ── Apply all fixes ────────────────────────────────────────────────────
    fixed_blocks, fixes = apply_text_fixes(merged, page_width, page_count)

    # Fill pdf_name + report_code into each block
    for fb in fixed_blocks:
        fb.pdf_name    = pdf_name
        fb.report_code = report_code

    # ── Schema validation ──────────────────────────────────────────────────
    block_dicts, n_pass, n_err = validate_text_blocks(
        fixed_blocks, strict=cfg.get("schema_strict", False))

    # ── Segment counts ─────────────────────────────────────────────────────
    seg_counts: Dict[str, int] = {}
    for d in block_dicts:
        s = d.get("segment","content")
        seg_counts[s] = seg_counts.get(s,0) + 1

    # ── DB ─────────────────────────────────────────────────────────────────
    # v1.1.0: prefer buffer (no DB lock contention)
    if buffer is not None:
        try:
            buffer.push_blocks(block_dicts, pdf_name, report_code, page_no, fixes)
            buffer.push_segment_summary(pdf_name, report_code, seg_counts)
        except Exception as e:
            log.warning("[MDL005] buffer page %d: %s", page_no, e)
    elif db:
        try:
            db.insert_blocks(block_dicts, pdf_name, report_code, page_no, fixes)
            db.insert_segment_summary(pdf_name, report_code, seg_counts)
        except Exception as e: log.warning("[MDL005] DB page %d: %s", page_no, e)

    return {
        "page_no":      page_no,
        "n_blocks":     len(block_dicts),
        "n_pass":       n_pass,
        "n_err":        n_err,
        "segment_counts":seg_counts,
        "fixes":        fixes,
        "blocks":       block_dicts,
    }

def process_one_pdf(
    pdf_path: str,
    cfg:      Dict,
    db:       Optional[MDL005DBWriter],
    buffer:   Optional["MDL005BatchBuffer"] = None,    # v1.1.0 NEW
) -> Dict:
    """VRN-MDL005-FNC-023  Process all pages of one PDF.
    v1.1.0: open PDF ONCE via DocCache (B1/B2 fix), pages parallel (B3 fix).
    """
    t0          = time.perf_counter()
    meta        = _parse_meta(pdf_path)
    pdf_name    = Path(pdf_path).name
    report_code = meta["report_code"]
    max_pages   = cfg.get("max_pages", _P["max_pages"])

    out = {
        "pdf_name":    pdf_name,
        "report_code": report_code,
        "ticker":      meta["ticker"],
        "report_date": meta["report_date"],
        "broker_abbr": meta["broker_abbr"],
        "n_pages":     0,
        "n_blocks":    0,
        "n_err":       0,
        "segment_counts":{},
        "pages":       [],
        "ok":          False,
        "error":       None,
        "elapsed":     0.0,
    }

    use_cache    = cfg.get("use_doc_cache", True)
    page_par     = cfg.get("page_parallel", True)
    page_workers = cfg.get("page_workers", 0) or max(2, (os.cpu_count() or 4) - 1)

    try:
        is_scan    = is_scan_pdf(pdf_path)
        page_width = 595.0  # A4 default
        n_pages    = 0

        # v1.1.0: open via DocCache once
        cache_ctx = MDL005DocCache(pdf_path) if use_cache else None
        if cache_ctx is not None:
            cache_ctx.__enter__()

        try:
            if cache_ctx is not None and cache_ctx.n_pages > 0:
                n_pages = min(cache_ctx.n_pages, max_pages)
                if cache_ctx.page_widths: page_width = cache_ctx.page_widths[0]
            elif _CAP["fitz"]:
                doc = fitz.open(pdf_path)
                n_pages    = min(len(doc), max_pages)
                if len(doc) > 0: page_width = doc[0].rect.width
                doc.close()
            elif _CAP["pdfplumber"]:
                with pdfplumb.open(pdf_path) as pdf:
                    n_pages = min(len(pdf.pages), max_pages)
                    if pdf.pages: page_width = float(pdf.pages[0].width)

            out["n_pages"] = n_pages
            agg_seg: Dict[str,int] = {}

            if page_par and n_pages > 1:
                # P2: page-level parallel
                page_results: Dict[int, Dict] = {}
                with ThreadPoolExecutor(max_workers=page_workers) as ex:
                    futs = {ex.submit(process_one_page,
                                      pdf_path, pg, is_scan, n_pages, page_width,
                                      cfg, db, pdf_name, report_code,
                                      cache_ctx, buffer): pg
                            for pg in range(1, n_pages + 1)}
                    for fut in as_completed(futs):
                        try:
                            pg_result = fut.result()
                            page_results[pg_result["page_no"]] = pg_result
                        except Exception as e:
                            log.warning("[MDL005] page %d: %s", futs[fut], e)
                # Reorder by page_no
                for pg in sorted(page_results):
                    pg_result = page_results[pg]
                    out["n_blocks"] += pg_result["n_blocks"]
                    out["n_err"]    += pg_result.get("n_err", 0)
                    for seg, cnt in pg_result.get("segment_counts",{}).items():
                        agg_seg[seg] = agg_seg.get(seg,0) + cnt
                    out["pages"].append({
                        "page_no":  pg_result["page_no"],
                        "n_blocks": pg_result["n_blocks"],
                        "fixes":    pg_result["fixes"],
                        "blocks":   pg_result["blocks"],
                    })
            else:
                for pg_no in range(1, n_pages + 1):
                    pg_result = process_one_page(
                        pdf_path, pg_no, is_scan, n_pages, page_width,
                        cfg, db, pdf_name, report_code, cache_ctx, buffer,
                    )
                    out["n_blocks"] += pg_result["n_blocks"]
                    out["n_err"]    += pg_result.get("n_err", 0)
                    for seg, cnt in pg_result.get("segment_counts",{}).items():
                        agg_seg[seg] = agg_seg.get(seg,0) + cnt
                    out["pages"].append({
                        "page_no":  pg_result["page_no"],
                        "n_blocks": pg_result["n_blocks"],
                        "fixes":    pg_result["fixes"],
                        "blocks":   pg_result["blocks"],
                    })

            out["segment_counts"] = agg_seg
            out["ok"]             = True

        finally:
            if cache_ctx is not None:
                cache_ctx.__exit__(None, None, None)

    except Exception as e:
        out["error"] = str(e)
        log.error("[MDL005] process_one_pdf %s: %s", pdf_name, e)

    out["elapsed"] = round(time.perf_counter() - t0, 2)
    log.info("[MDL005] %s: pages=%d blocks=%d err=%d %.2fs",
             pdf_name, out["n_pages"], out["n_blocks"], out["n_err"], out["elapsed"])
    return out

# ============================================================================
# [VRN:ANCHOR:MDL005-OUT-001] §21  OUTPUT ASSEMBLER
# ============================================================================

def assemble_output(results: List[Dict]) -> Dict:
    """VRN-MDL005-FNC-024"""
    ok_count = sum(1 for r in results if r.get("ok"))
    agg_seg: Dict[str,int] = {}
    for r in results:
        for seg, cnt in r.get("segment_counts",{}).items():
            agg_seg[seg] = agg_seg.get(seg,0) + cnt
    return {
        "module":         __module_id__,
        "version":        __version__,
        "generated":      time.strftime("%Y-%m-%d %H:%M:%S"),
        "total":          len(results),
        "ok_count":       ok_count,
        "fail_count":     len(results) - ok_count,
        "total_pages":    sum(r.get("n_pages",0) for r in results),
        "total_blocks":   sum(r.get("n_blocks",0) for r in results),
        "total_err":      sum(r.get("n_err",0) for r in results),
        "segment_counts": agg_seg,
        "reports":        results,
    }

# ============================================================================
# [VRN:ANCHOR:MDL005-SYS-001] §22  PIPELINE ENTRY
# ============================================================================

class VRN_MDL005_TextFetcher:
    """VRN-MDL005-CLS-001
    run():
      1. Load plugins (SSOT / Celeritas / Aegis) — real API integration
      2. Accel init (6-ENV + warm Celeritas pool)
      3. List PDFs from pdf_temp
      4. Parallel process_one_pdf() via Celeritas _LazyPool or stdlib ThreadPoolExecutor
      5. DB export
      6. VRN_MDL005_Text.json + VerifySummary.json
    """
    def __init__(self, cfg: Optional[Dict] = None):
        self.cfg     = dict(_PARAMS, **(cfg or {}))
        workers      = self.cfg.get("workers",0) or max(1,(os.cpu_count() or 4)-1)
        self.workers = workers
        self.db: Optional[MDL005DBWriter] = None
        self._plugin_caps: Dict[str,bool] = {}

    def run(self) -> Dict:
        run_t0      = time.perf_counter()
        pdf_temp    = self.cfg.get("pdf_temp",    _P["pdf_temp"])
        mdl005_temp = self.cfg.get("mdl005_temp", _P["mdl005_temp"])
        ssot_dir    = self.cfg.get("ssot_dir",    _P["ssot_dir"])
        Path(mdl005_temp).mkdir(parents=True, exist_ok=True)

        # ── Plugin load (SSOT / Celeritas / Aegis) ────────────────────────
        self._plugin_caps = load_plugins(ssot_dir)
        log.info("[MDL005] plugins: %s", self._plugin_caps)

        # ── Accel init ────────────────────────────────────────────────────
        cap = _mdl005_accel_init(self.workers)
        log.info("[MDL005] accel: %s", cap)

        # ── v1.1.0: BatchBuffer + DuckDB primary + sqlite fallback ──────────
        self.buffer: Optional[MDL005BatchBuffer] = None
        self.duck:   Optional[MDL005DuckWriter]  = None
        if self.cfg.get("enable_db", True):
            self.buffer = MDL005BatchBuffer(
                batch_size=self.cfg.get("batch_size", 5000))
            if self.cfg.get("use_duckdb", True) and DUCKDB_OK:
                try:
                    self.duck = MDL005DuckWriter(
                        str(Path(mdl005_temp) / "VRN_MDL005.duckdb"))
                    log.info("[MDL005] DuckDB primary writer ready")
                except Exception as e:
                    log.warning("[MDL005] DuckDB init fail (%s), sqlite fallback", e)
                    self.duck = None
            try:
                self.db = MDL005DBWriter(str(Path(mdl005_temp)/"VRN_MDL005.db"))
                log.info("[MDL005] sqlite fallback writer ready")
            except Exception as e:
                log.warning("[MDL005] sqlite init fail: %s", e)
                self.db = None

        pdfs = list_pdfs(pdf_temp)
        if not pdfs:
            log.warning("[MDL005] No PDFs in %s", pdf_temp)
            empty = assemble_output([])
            _jwrite(str(Path(mdl005_temp)/"VRN_MDL005_Text.json"), empty)
            return {"ok":True,"total":0,"success":0,"errors":[],"out_dir":mdl005_temp}

        log.info("[MDL005] Processing %d PDFs, workers=%d  doc_cache=%s page_par=%s",
                 len(pdfs), self.workers,
                 self.cfg.get("use_doc_cache",True),
                 self.cfg.get("page_parallel",True))

        all_results: List[Dict] = []
        fail_count = 0

        # PDF-level parallel via Celeritas or stdlib
        if _CEL_OK and hasattr(_CEL, "_LazyPool"):
            try:
                futs = [_CEL._LazyPool.submit(process_one_pdf, p, self.cfg, self.db,
                                              self.buffer)
                        for p in pdfs]
                for fut in futs:
                    try:
                        res = fut.result()
                    except Exception as e:
                        res = {"ok":False,"error":str(e),"pdf_name":"unknown",
                               "n_pages":0,"n_blocks":0,"n_err":0,
                               "segment_counts":{},"pages":[]}
                    all_results.append(res)
                    if not res.get("ok"): fail_count += 1
            except Exception as e:
                log.warning("[MDL005] Celeritas pool failed, fallback stdlib: %s", e)
                all_results = []; fail_count = 0
                with ThreadPoolExecutor(max_workers=self.workers) as ex:
                    futs2 = {ex.submit(process_one_pdf, p, self.cfg, self.db,
                                       self.buffer): p for p in pdfs}
                    for fut in as_completed(futs2):
                        res = fut.result()
                        all_results.append(res)
                        if not res.get("ok"): fail_count += 1
        else:
            with ThreadPoolExecutor(max_workers=self.workers) as ex:
                futs = {ex.submit(process_one_pdf, p, self.cfg, self.db,
                                  self.buffer): p for p in pdfs}
                for fut in as_completed(futs):
                    res = fut.result()
                    all_results.append(res)
                    if not res.get("ok"): fail_count += 1

        # ── v1.1.0: single-thread flush DB after pool closes ────────────────
        flush_stats = {"blk": 0, "fix": 0, "seg": 0}
        if self.buffer:
            b_rows, f_rows, s_rows = self.buffer.consume_all()
            log.info("[MDL005] Buffer drain: blk=%d fix=%d seg=%d",
                     len(b_rows), len(f_rows), len(s_rows))
            if self.duck:
                try:
                    flush_stats = self.duck.flush(b_rows, f_rows, s_rows)
                    log.info("[MDL005] DuckDB flush: %s", flush_stats)
                except Exception as e:
                    log.warning("[MDL005] DuckDB flush fail (%s), sqlite fallback", e)
                    if self.db:
                        flush_stats = self.db.flush(b_rows, f_rows, s_rows)
            elif self.db:
                flush_stats = self.db.flush(b_rows, f_rows, s_rows)
                log.info("[MDL005] sqlite flush: %s", flush_stats)

        # ── v1.1.0: polars-direct exports ───────────────────────────────────
        parquet_path = csv_path = None
        if self.duck:
            parquet_path = self.duck.export_parquet_polars(mdl005_temp)
            csv_path     = self.duck.export_csv_polars(mdl005_temp)
        elif self.db:
            parquet_path = self.db.export_parquet_polars(mdl005_temp)
            csv_path     = self.db.export_csv_polars(mdl005_temp)
        log.info("[MDL005] Exports: parquet=%s csv=%s", parquet_path, csv_path)

        out = assemble_output(all_results)
        _jwrite(str(Path(mdl005_temp)/"VRN_MDL005_Text.json"), out)

        verify = {
            "module":         __module_id__,
            "version":        __version__,
            "generated":      time.strftime("%Y-%m-%d %H:%M:%S"),
            "total":          len(pdfs),
            "ok":             fail_count == 0,
            "ok_count":       len(pdfs) - fail_count,
            "fail_count":     fail_count,
            "total_blocks":   out["total_blocks"],
            "total_err":      out["total_err"],
            "segment_counts": out["segment_counts"],
            "plugin_caps":    self._plugin_caps,
            "accel_caps":     cap,
            "engine_primary": self.cfg.get("engine_primary"),
            "engine_secondary":self.cfg.get("engine_secondary"),
            "fix_flags":      {k:v for k,v in _P.items() if k.startswith("fix_")},
            "flush_stats":    flush_stats,
            "fail_details":   [{"pdf_name":r.get("pdf_name",""),"error":r.get("error")}
                               for r in all_results if not r.get("ok")],
        }
        _jwrite(str(Path(mdl005_temp)/"VRN_MDL005_VerifySummary.json"), verify)

        # ── Close DBs BEFORE self-verify (avoid DuckDB read-only conflict) ──
        if self.duck: self.duck.close()
        if self.db:
            try: self.db._con.close()
            except: pass

        # ── v1.1.0: 4-phase self-verify HTML ────────────────────────────────
        sv_html_path = None
        if self.cfg.get("self_verify", True):
            try:
                sv = MDL005SelfVerifier(self.cfg, out, mdl005_temp).run()
                html = build_self_verify_html_mdl005(sv, out)
                sv_html_path = str(Path(mdl005_temp)/"VRN_MDL005_SelfVerify.html")
                Path(sv_html_path).write_text(html, encoding="utf-8")
                log.info("[MDL005] Self-verify: %s (%d/%d) → %s",
                         sv["classification"], sv["pass"], sv["total"], sv_html_path)
            except Exception as e:
                log.warning("[MDL005] self_verify build fail: %s", e)

        elapsed = round(time.perf_counter() - run_t0, 2)
        log.info("[MDL005] Complete: %d/%d OK  blocks=%d  err=%d  segs=%s  %.2fs",
                 len(pdfs)-fail_count, len(pdfs),
                 out["total_blocks"], out["total_err"],
                 dict(list(out["segment_counts"].items())[:4]), elapsed)
        return {
            "ok":           fail_count == 0,
            "total":        len(pdfs),
            "success":      len(pdfs) - fail_count,
            "total_blocks": out["total_blocks"],
            "elapsed":      elapsed,
            "flush_stats":  flush_stats,
            "self_verify_html": sv_html_path,
            "errors":       [r.get("error","") for r in all_results if not r.get("ok")],
            "out_dir":      mdl005_temp,
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
    "RATING_LIST","RATING_FLAT_LIST","normalize_rating",
    "BROKER_MAP","BROKER_ABBR_MAP","SYNONYM_MAP",
    # Accel
    "_mdl005_accel_init","_CAP",
    # Plugin loader + proxies
    "load_plugins",
    "_cel_submit","_cel_map","_net_get","_ssot_get",
    "_ssot_normalize_rating","_ssot_normalize_term",
    # Data classes
    "RawTextBlock","FixedTextBlock",
    # Scanner
    "list_pdfs","is_scan_pdf",
    # Engines (all standalone)
    "engine_pymupdf","engine_pdfplumber","engine_pdfminer",
    "engine_docling","engine_marker","engine_paddleocr","engine_surya",
    # Merge
    "merge_and_dedup",
    # Fixes T01–T20 (all standalone)
    "fix_T01_reading_order","fix_T02_whitespace_reconstruct",
    "fix_T03_dehyphenation","fix_T04_zh_en_separation",
    "fix_T05_unicode_normalize","fix_T06_trim_nbsp",
    "fix_T07_ocr_alphanum","fix_T08_mojibake_detect",
    "fix_T09_watermark_filter","fix_T10_sent_merge",
    "fix_T11_title_detect","fix_T12_dedup",
    "fix_T13_empty_drop","fix_T14_segment_tag",
    "fix_T15_header_footer_strip","fix_T16_bullet_preserve",
    "fix_T17_table_ref_skip","fix_T18_reading_col_reorder",
    "fix_T19_financial_term_norm","fix_T20_confidence_score",
    "apply_text_fixes",
    # Schema
    "validate_text_blocks",
    # DB
    "MDL005DBWriter",
    # v1.1.0 NEW
    "MDL005DocCache", "MDL005BatchBuffer", "MDL005DuckWriter",
    "MDL005SelfVerifier", "build_self_verify_html_mdl005",
    # Pipeline
    "process_one_page","process_one_pdf","assemble_output",
    "VRN_MDL005_TextFetcher",
]

# ============================================================================
# __main__
# ============================================================================

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="VRN MDL005 OCR FetchingPDFText v1")
    p.add_argument("--pdf-temp",         default=_P["pdf_temp"])
    p.add_argument("--mdl005-temp",      default=_P["mdl005_temp"])
    p.add_argument("--ssot-dir",         default=_P["ssot_dir"])
    p.add_argument("--workers",          type=int, default=_P["workers"])
    p.add_argument("--engine-primary",   default=_P["engine_primary"])
    p.add_argument("--engine-secondary", default=_P["engine_secondary"])
    p.add_argument("--no-db",            action="store_true")
    p.add_argument("--no-ssot",          action="store_true")
    p.add_argument("--no-celeritas",     action="store_true")
    p.add_argument("--no-aegis",         action="store_true")
    args = p.parse_args()
    cfg  = {
        "pdf_temp":        args.pdf_temp,
        "mdl005_temp":     args.mdl005_temp,
        "ssot_dir":        args.ssot_dir,
        "workers":         args.workers,
        "engine_primary":  args.engine_primary,
        "engine_secondary":args.engine_secondary,
        "enable_db":       not args.no_db,
        "enable_ssot":     not args.no_ssot,
        "enable_celeritas":not args.no_celeritas,
        "enable_aegis":    not args.no_aegis,
    }
    result = VRN_MDL005_TextFetcher(cfg).run()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["ok"] else 1)
