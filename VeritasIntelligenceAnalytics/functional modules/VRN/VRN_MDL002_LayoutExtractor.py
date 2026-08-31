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
VRN_MDL002_LayoutExtractor.py
==============================
VERITAS REPORT NOVA -- MDL002  Full Layout & Table Region Extractor
Version   : 1.0.0   |   Module ID : VRN-MDL002-SUP-001
Asset ID  : VRN-MDL002-CLS-001
Policy    : 功能只增不減 · append-only · SSOT · 獨立模組

PIPELINE POSITION
  pdf_temp/             ← 統一高畫質 PDF (from MDL001)
    ↓
  VRN_MDL002_LayoutExtractor  (此模組)
    ↓
  mdl002_temp/          ← 全部表格資訊 + layout座標 + 位置編號 → MDL003

DESIGN PHILOSOPHY (from NotebookLM analysis)
  This module implements the "Zonal Cropping + Multi-Engine" strategy:
  ① Page-level: detect 1st-page summary zones (top/left/right sidebar)
  ② Fin-page detection: keyword anchoring (損益表/Income Statement etc.)
  ③ Table region detection: vector lines + text gap + image CV
  ④ Quadrant splitting: dense fin-pages cut into 4 quadrants
  ⑤ Time-header validation: confirm table is financial (year/quarter pattern)
  ⑥ Accounting-subject validation: first-column keyword matching
  ⑦ All tables get: page_no, region_id, bbox, type, source, header_periods

ANCHOR MAP
  [VRN:ANCHOR:MDL002-META-001]    §0  Module Metadata
  [VRN:ANCHOR:MDL002-SSOT-001]    §1  SSOT: keywords + regex (locked TW_TICKER)
  [VRN:ANCHOR:MDL002-ACCEL-001]   §2  Accelerator Init (6-ENV)
  [VRN:ANCHOR:MDL002-DAT-001]     §3  Config / _DEFAULTS
  [VRN:ANCHOR:MDL002-SCAN-001]    §4  pdf_temp Scanner
  [VRN:ANCHOR:MDL002-PAGECLASS-001] §5 Page Classifier (1st-page / fin-page / content)
  [VRN:ANCHOR:MDL002-ZONE-001]    §6  Zonal Cropping: 1st-page sidebar + top zones
  [VRN:ANCHOR:MDL002-REGION-001]  §7  Table Region Detection (vector/text/quadrant)
  [VRN:ANCHOR:MDL002-VALIDATE-001] §8 Table Validation (time-header + subject-col)
  [VRN:ANCHOR:MDL002-EXTRACT-001] §9  Multi-Engine Table Extraction per region
  [VRN:ANCHOR:MDL002-TEXT-001]    §10 Full-text extraction per page (TXT blocks)
  [VRN:ANCHOR:MDL002-NUMBER-001]  §11 Region numbering + layout serialisation
  [VRN:ANCHOR:MDL002-DB-001]      §12 DB Writer (WAL + Parquet + CSV)
  [VRN:ANCHOR:MDL002-OUT-001]     §13 Output Assembler
  [VRN:ANCHOR:MDL002-SYS-001]     §14 Pipeline Entry VRN_MDL002_LayoutExtractor

SMART ASSET REGISTRY
  VRN-MDL002-CLS-001  VRN_MDL002_LayoutExtractor
  VRN-MDL002-CLS-002  MDL002DBWriter
  VRN-MDL002-CLS-003  PageRecord
  VRN-MDL002-CLS-004  TableRecord
  VRN-MDL002-CLS-005  TextBlock
  VRN-MDL002-FNC-001  list_pdfs_in_temp
  VRN-MDL002-FNC-002  classify_page
  VRN-MDL002-FNC-003  extract_zones_first_page
  VRN-MDL002-FNC-004  detect_table_regions
  VRN-MDL002-FNC-005  split_quadrants
  VRN-MDL002-FNC-006  validate_financial_table
  VRN-MDL002-FNC-007  extract_table_from_region
  VRN-MDL002-FNC-008  extract_text_blocks
  VRN-MDL002-FNC-009  extract_spans_metadata
  VRN-MDL002-FNC-010  number_all_regions
  VRN-MDL002-FNC-011  process_one
  VRN-MDL002-FNC-012  assemble_output
  VRN-MDL002-FNC-013  _mdl002_accel_init

OUTPUTS (mdl002_temp)
  VRN_MDL002_Layout.json         ← 主輸出：每份PDF完整layout + 所有表格記錄 → MDL003
  VRN_MDL002_VerifySummary.json  ← 驗證摘要
  VRN_MDL002.db                  ← SQLite WAL (tables + text_blocks + spans)
  VRN_MDL002_Layout.parquet      ← Parquet flat
  VRN_MDL002_Layout.csv          ← CSV (UTF-8 BOM)

LL RULES: #10 #12 #13 #15 #17 #18 #19 #20
"""

# ============================================================================
# [VRN:ANCHOR:MDL002-META-001] §0
# ============================================================================

__version__   = "1.1.0"
__module_id__ = "VRN-MDL002-SUP-001"
__asset_id__  = "VRN-MDL002-CLS-001"
__author__    = "VRN Team"
__domain__    = "LAYOUT_EXTRACT"

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

fitz       = _si("fitz")
pdfplumb   = _si("pdfplumber")
pd         = _si("pandas")
pyarrow    = _si("pyarrow")
orjson     = _si("orjson")
xxhash     = _si("xxhash")

# v1.1.0 NEW: polars + duckdb (primary)
pl         = _si("polars")
duckdb_lib = _si("duckdb")
POLARS_OK  = pl is not None
DUCKDB_OK  = duckdb_lib is not None

# ── Celeritas plugin globals ───────────────────────────────────────────────────
_CEL: object = None;  _CEL_OK: bool = False
# [VRN:ANCHOR:HARDGATE_HOLDERS:V1] 7-tool support per VIA_Supportive_HardGate_Seal.json
_SSOT: object = None; _SSOT_OK: bool = False
_REG: object = None;  _REG_OK: bool = False
_BRG: object = None;  _BRG_OK: bool = False
_ENV: object = None;  _ENV_OK: bool = False
_AST: object = None;  _AST_OK: bool = False
_NET: object = None;  _NET_OK: bool = False

def _load_celeritas(ssot_dir: str) -> bool:
    """VRN-MDL002: Load 7 supportive tools per VIA_Supportive_HardGate_Seal.json.
    Backward-compat: returns _CEL_OK. Policy: BOOT_PRECHECK_ONLY_NO_NETWORK_NO_PARALLEL_NO_AUTOPATCH.
    """
    global _CEL, _CEL_OK, _SSOT, _SSOT_OK, _REG, _REG_OK, _BRG, _BRG_OK
    global _ENV, _ENV_OK, _AST, _AST_OK, _NET, _NET_OK
    import importlib.util as _ilu
    plugin_map = [
        ("VIA_SSOT_Unified",                 "_SSOT", "_SSOT_OK"),
        ("VIA_RegistryCore_v1",              "_REG",  "_REG_OK"),
        ("VIA_Runtime_Bridge_All_in_One",    "_BRG",  "_BRG_OK"),
        ("VIA_EnvManager",                   "_ENV",  "_ENV_OK"),
        ("VIA_Panorama_AST_RuntimeInjector", "_AST",  "_AST_OK"),
        ("VeritasCeleritas",                 "_CEL",  "_CEL_OK"),
        ("VeritasAegisNexus",                "_NET",  "_NET_OK"),
    ]
    for mod_name, gname, ok_name in plugin_map:
        for p in [Path(ssot_dir)/f"{mod_name}.py",
                  Path(ssot_dir).parent/f"{mod_name}.py"]:
            if p.exists():
                try:
                    spec = _ilu.spec_from_file_location(mod_name, str(p))
                    mod  = _ilu.module_from_spec(spec)
                    sys.modules[mod_name] = mod
                    spec.loader.exec_module(mod)
                    globals()[gname]   = mod
                    globals()[ok_name] = True
                    if mod_name == "VeritasCeleritas":
                        if hasattr(mod, "bootstrap_at_import"): mod.bootstrap_at_import(__file__)
                        if hasattr(mod, "warm_thread_pool"):    mod.warm_thread_pool()
                    log.info("[MDL002] %s loaded", mod_name)
                    break
                except Exception as e:
                    log.debug("[MDL002] %s: %s", mod_name, e)
    return _CEL_OK

def _cel_submit(fn, *args, **kw):
    if _CEL_OK:
        if hasattr(_CEL, "_LazyPool"):
            try: return _CEL._LazyPool.submit(fn, *args, **kw)
            except Exception: pass
    return fn(*args, **kw)
camelot    = _si("camelot")
tabula     = _si("tabula")

# ============================================================================
# [VRN:ANCHOR:MDL002-SSOT-001] §1  SSOT (LOCKED)
# ============================================================================

# THREE LOCKED TW TICKER REGEX — NEVER MODIFY
TW_TICKER_REGEX    = re.compile(r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})")
TW_BLOOMBERG_REGEX = re.compile(r"\b(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})\s+TT\b")
TW_YFINANCE_REGEX  = re.compile(r"\b(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})\.(TW|TWO)\b")

# Financial page keywords (for fin-page detection)
FIN_KEYWORDS_ZH = [
    "損益表", "資產負債表", "現金流量表", "財務報表", "比率分析",
    "每股分析", "每股盈餘", "財務預估", "財務摘要", "關鍵財務",
    "Income Statement", "Balance Sheet", "Cash Flow", "Profit",
    "Financial Summary", "Key Financials", "Earnings", "Valuation",
    "P&L", "Ratio Analysis", "Per Share",
]

# Accounting subject keywords (for table validation — first column)
ACCT_SUBJECTS = [
    "營業收入", "Revenue", "Sales", "Gross Profit", "毛利", "Operating",
    "EBIT", "EBITDA", "Net Income", "淨利", "EPS", "每股盈餘",
    "ROE", "ROA", "毛利率", "Gross Margin", "Total Assets", "總資產",
    "Current Assets", "流動資產", "Equity", "股東權益", "Cash Flow",
    "Operating Income", "營業利益", "Cost of", "營業成本",
    "Dividend", "股利", "BPS", "BVPS", "DPS", "P/E", "P/B",
]

# Time-header regex: matches year/quarter patterns
TIME_HEADER_RE = re.compile(
    r"(20\d{2}[AEFaefCTct]?|\d{1,2}Q\d{2}|[Ff][Yy]\d{2}[AEae]?|"
    r"\d{4}[Qq]\d|2[0-9][A-Z]{1,2})"
)

# 1st page summary keywords (for sidebar/top zone detection)
SUMMARY_KEYWORDS = [
    "目標價", "Target Price", "Rating", "評等", "投資建議",
    "PER", "P/E", "PBR", "P/B", "市值", "收盤價", "Close",
    "Outperform", "Buy", "Hold", "Sell", "買進", "持有",
    "EPS", "每股盈餘", "股息", "Dividend", "殖利率", "Yield",
]

# ============================================================================
# [VRN:ANCHOR:MDL002-ACCEL-001] §2
# ============================================================================

def _mdl002_accel_init(workers: int = 0) -> Dict:
    """VRN-MDL002-FNC-013"""
    w = workers or max(1, (os.cpu_count() or 4) - 1)
    for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                "NUMEXPR_NUM_THREADS", "BLIS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ.setdefault(var, str(w))
    gc.set_threshold(50_000, 500, 50)
    return {
        "workers":    w,
        "fitz":       fitz is not None,
        "pdfplumber": pdfplumb is not None,
        "camelot":    camelot is not None,
        "tabula":     tabula is not None,
        "pyarrow":    pyarrow is not None,
    }

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s][%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

# ============================================================================
# [VRN:ANCHOR:MDL002-DAT-001] §3
# ============================================================================

_DEFAULTS = dict(
    pdf_temp    = r"C:\VeritasIntelligenceAnalytics\VeritasReportNova\temp\pdf_temp",
    ssot_dir    = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module",
    mdl002_temp = r"C:\VeritasIntelligenceAnalytics\VeritasReportNova\temp\mdl002_temp",
    workers     = 0,
    max_pages   = 50,
    enable_db   = True,
    zero_error  = True,
    # Zonal cropping ratios for 1st-page extraction
    top_ratio      = 0.25,    # top 25% = header zone
    sidebar_ratio  = 0.35,    # left/right 35% = sidebar zones
    # Quadrant split for dense fin-pages
    quadrant_split = True,
    # Min time-columns to confirm financial table
    min_time_cols  = 2,
    # Min accounting subjects in first col
    min_acct_hits  = 1,
    # Table extraction engine priority
    engine_order   = "pdfplumber,camelot,tabula,fitz",
    # ── v1.1.0 NEW (append-only) ─────────────────────────────────────────────
    use_doc_cache  = True,    # P1 每 PDF 開一次 fitz + pdfplumber
    page_parallel  = True,    # P2 page-level 平行
    page_workers   = 0,       # 0 = auto
    use_duckdb     = True,    # P3 DuckDB primary, sqlite fallback
    batch_size     = 5000,    # P3 buffer flush threshold
    polars_first   = True,    # P5 polars vectorized exports
    self_verify    = True,    # P6 4-phase HTML
)

# ── Filename date pattern ────────────────────────────────────────────────────
_FN_DATE_RE   = re.compile(r"(20\d{2})[_\-]?(\d{2})[_\-]?(\d{2})")
_FN_BROKER_RE = re.compile(
    r"(GS|MS|JPM|CITI|UBS|DB|CS|BAML|NOMURA|DAIWA|CLSA|MACQ|"
    r"兆豐|國泰|中信|元大|富邦|凱基|永豐金|華南永昌|玉山)",
    re.IGNORECASE,
)

# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class TableRecord:
    """One extracted table from a PDF."""
    pdf_name:     str = ""
    report_code:  str = ""
    page_no:      int = 0
    region_id:    str = ""          # e.g. P001TBL001
    region_type:  str = ""          # "1st_page_top"|"1st_page_sidebar"|"fin_page"|"content"
    quadrant:     str = ""          # "TL"|"TR"|"BL"|"BR"|"full"
    bbox:         List[float] = field(default_factory=list)   # [x0,y0,x1,y1] points
    engine_used:  str = ""
    is_financial: bool = False
    header_periods: List[str] = field(default_factory=list)   # detected time columns
    n_rows:       int = 0
    n_cols:       int = 0
    raw_data:     List[List[str]] = field(default_factory=list)  # table cells as strings
    first_col_subjects: List[str] = field(default_factory=list)
    caption:      str = ""
    error:        Optional[str] = None

@dataclass
class TextBlock:
    """One text block from a page."""
    pdf_name:   str = ""
    report_code:str = ""
    page_no:    int = 0
    block_id:   str = ""    # e.g. P001TXT001
    block_type: str = ""    # "1st_page"|"fin_page"|"content"
    text:       str = ""
    bbox:       List[float] = field(default_factory=list)
    is_title:   bool = False
    is_bold:    bool = False
    font_size:  float = 0.0

# ============================================================================
# [VRN:ANCHOR:MDL002-DOCCACHE-001] §3.5  P1 DOC CACHE — v1.1.0
# ── 解 v1.0.0 最大殺手：每函數內各自開 fitz/pdfplumber                       ─
# ── A4 50頁原本 ~500 次 open() → 只 2 次                                     ─
# ============================================================================

class MDL002DocCache:
    """VRN-MDL002-CLS-006  (NEW v1.1.0)
    Open fitz + pdfplumber ONCE per PDF, share for all page operations.
    Used by detect_table_regions / split_quadrants / extract_table_from_region /
    extract_text_blocks / classify_page / _detect_vector_regions.
    """
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self._fitz: Any = None
        self._pp:   Any = None
        self.n_pages: int = 0
        self.page_widths:  List[float] = []
        self.page_heights: List[float] = []

    def __enter__(self):
        if fitz is not None:
            try:
                self._fitz = fitz.open(self.pdf_path)
                self.n_pages = len(self._fitz)
                for pg in self._fitz:
                    self.page_widths.append(float(pg.rect.width))
                    self.page_heights.append(float(pg.rect.height))
            except Exception as e:
                log.debug("[MDL002] DocCache fitz open fail: %s", e)
                self._fitz = None
        if pdfplumb is not None:
            try:
                self._pp = pdfplumb.open(self.pdf_path)
                if self.n_pages == 0:
                    self.n_pages = len(self._pp.pages)
            except Exception as e:
                log.debug("[MDL002] DocCache pdfplumber open fail: %s", e)
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
# [VRN:ANCHOR:MDL002-PRECOMP-001] §3.6  P4 PRE-COMPILED REGEX POOL — v1.1.0
# ============================================================================

# Year/Quarter recognition (was inline in validate_financial_table)
_RE_YEAR4_v110     = re.compile(r"20\d{2}")
_RE_QUARTER_v110   = re.compile(r"Q[1-4]|[1-4]Q|第[一二三四1234]季")
_RE_YEAR_BARE_v110 = re.compile(r"^(FY|20)?\d{2,4}[AEF]?$")
_RE_DOUBLESPACE_v110 = re.compile(r" {2,}")
_RE_MOJIBAKE_v110    = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x80-\x9f]")

# ============================================================================
# [VRN:ANCHOR:MDL002-SCAN-001] §4
# ============================================================================

def list_pdfs_in_temp(pdf_temp: str) -> List[str]:
    """VRN-MDL002-FNC-001"""
    if not os.path.isdir(pdf_temp): return []
    return sorted(
        os.path.join(pdf_temp, f)
        for f in os.listdir(pdf_temp)
        if f.lower().endswith(".pdf")
    )

def _parse_pdf_meta(pdf_path: str) -> Dict:
    stem   = Path(pdf_path).stem
    meta   = {"ticker": "", "report_date": "", "broker_abbr": "",
              "report_code": _hash8(stem)}
    dm = _FN_DATE_RE.search(stem)
    if dm: meta["report_date"] = "{}-{}-{}".format(dm.group(1), dm.group(2), dm.group(3))
    bm = _FN_BROKER_RE.search(stem)
    if bm: meta["broker_abbr"] = bm.group(1).upper()
    for tok in re.split(r"[_\-\s]", stem):
        m = re.fullmatch(r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})", tok.strip())
        if m: meta["ticker"] = m.group(1); break
    return meta

def _hash8(s: str) -> str:
    if xxhash: return xxhash.xxh64(s.encode()).hexdigest()[:8].upper()
    return hashlib.sha256(s.encode()).hexdigest()[:8].upper()

def _jwrite(p: str, data: Any):
    def _def(o): return None if isinstance(o, float) and (math.isnan(o) or math.isinf(o)) else str(o)
    Path(p).write_text(json.dumps(data, ensure_ascii=False, indent=2, default=_def), encoding="utf-8")

# ============================================================================
# [VRN:ANCHOR:MDL002-PAGECLASS-001] §5  PAGE CLASSIFIER
# ============================================================================

def classify_page(page_text: str, page_no: int) -> str:
    """VRN-MDL002-FNC-002
    Returns: '1st_page' | 'fin_page' | 'content'
    """
    if page_no == 1: return "1st_page"
    for kw in FIN_KEYWORDS_ZH:
        if kw in page_text:
            return "fin_page"
    return "content"

# ============================================================================
# [VRN:ANCHOR:MDL002-ZONE-001] §6  ZONAL CROPPING — 1ST PAGE
# ============================================================================

def extract_zones_first_page(
    pdf_path: str,
    page,               # pdfplumber page object
    cfg:    Dict,
) -> List[Dict]:
    """VRN-MDL002-FNC-003
    Extract tables from specific zones of 1st page:
    - top header (top 25%)
    - left sidebar (left 35%)
    - right sidebar (right 35%)
    Returns list of raw table dicts with zone info.
    """
    if pdfplumb is None: return []
    results = []
    try:
        W = float(page.width)
        H = float(page.height)
        top_r     = cfg.get("top_ratio",     0.25)
        sidebar_r = cfg.get("sidebar_ratio",  0.35)

        zones = {
            "top":    (0, 0, W, H * top_r),
            "left":   (0, 0, W * sidebar_r, H),
            "right":  (W * (1 - sidebar_r), 0, W, H),
        }

        seen_bboxes = set()
        for zone_name, bbox in zones.items():
            try:
                crop = page.within_bbox(bbox)
                tables = crop.extract_tables() or []
                for tbl in tables:
                    if not tbl or not tbl[0]: continue
                    # Dedup by first-row text
                    key = str(tbl[0])
                    if key in seen_bboxes: continue
                    seen_bboxes.add(key)
                    results.append({
                        "zone":       zone_name,
                        "bbox":       list(bbox),
                        "raw_data":   tbl,
                        "n_rows":     len(tbl),
                        "n_cols":     max(len(r) for r in tbl) if tbl else 0,
                    })
            except Exception as e:
                log.debug("[MDL002] 1st-page zone %s: %s", zone_name, e)
    except Exception as e:
        log.debug("[MDL002] extract_zones_first_page: %s", e)
    return results

# ============================================================================
# [VRN:ANCHOR:MDL002-REGION-001] §7  TABLE REGION DETECTION
# ============================================================================

def detect_table_regions(
    pdf_path: str,
    page_no:  int,
    page_text:str,
    page_cls: str,
    cfg:      Dict,
    doc_cache: Optional["MDL002DocCache"] = None,    # v1.1.0 NEW
) -> List[Dict]:
    """VRN-MDL002-FNC-004
    Detects table regions on a given page using:
    A. pdfplumber.extract_tables() (whole page or quadrant)
    B. PyMuPDF vector line detection
    C. Quadrant split for dense fin-pages
    Returns: list of region dicts {bbox, source, page_no, quadrant}
    v1.1.0: doc_cache reuses opened pdfplumber/fitz handles.
    """
    regions = []
    if pdfplumb is None and fitz is None: return regions

    # For dense fin-pages: split into quadrants
    if page_cls == "fin_page" and cfg.get("quadrant_split", True):
        quad_regions = split_quadrants(pdf_path, page_no, cfg, doc_cache=doc_cache)
        regions.extend(quad_regions)
    else:
        # Whole-page extraction
        # v1.1.0 fast path
        if doc_cache is not None and doc_cache.pdfplumber_pdf is not None:
            try:
                pg = doc_cache.pdfplumber_page(page_no)
                if pg is not None:
                    tbls = pg.extract_tables() or []
                    for tbl in tbls:
                        if tbl and len(tbl) >= 2:
                            regions.append({
                                "bbox":    [0, 0, float(pg.width), float(pg.height)],
                                "source":  "pdfplumber_full",
                                "page_no": page_no,
                                "quadrant":"full",
                                "raw_data":tbl,
                            })
            except Exception as e:
                log.debug("[MDL002] pdfplumber full (cache) page %d: %s", page_no, e)
        else:
            try:
                with pdfplumb.open(pdf_path) as pdf:
                    if page_no - 1 < len(pdf.pages):
                        pg    = pdf.pages[page_no - 1]
                        tbls  = pg.extract_tables() or []
                        for tbl in tbls:
                            if tbl and len(tbl) >= 2:
                                regions.append({
                                    "bbox":    [0, 0, float(pg.width), float(pg.height)],
                                    "source":  "pdfplumber_full",
                                    "page_no": page_no,
                                    "quadrant":"full",
                                    "raw_data":tbl,
                                })
            except Exception as e:
                log.debug("[MDL002] pdfplumber full page %d: %s", page_no, e)

    # Supplement with PyMuPDF vector detection if fitz available
    if fitz:
        try:
            vec_regions = _detect_vector_regions(pdf_path, page_no, doc_cache=doc_cache)
            regions.extend(vec_regions)
        except Exception as e:
            log.debug("[MDL002] vector detect page %d: %s", page_no, e)

    return regions

def split_quadrants(pdf_path: str, page_no: int, cfg: Dict,
                    doc_cache: Optional["MDL002DocCache"] = None) -> List[Dict]:
    """VRN-MDL002-FNC-005
    Split a dense financial page into 4 quadrants and extract tables from each.
    TL=Top-Left(Income Stmt), TR=Top-Right(CashFlow),
    BL=Bottom-Left(Balance Sheet), BR=Bottom-Right(Ratio Analysis)
    v1.1.0: doc_cache fast path (1 open() vs 4 opens for the 4 quadrants).
    """
    results = []
    if pdfplumb is None: return results

    def _do_quadrants(pg) -> List[Dict]:
        out = []
        W = float(pg.width); H = float(pg.height)
        qs = [
            ("TL", (0,   0,   W/2, H/2)),
            ("TR", (W/2, 0,   W,   H/2)),
            ("BL", (0,   H/2, W/2, H)),
            ("BR", (W/2, H/2, W,   H)),
        ]
        seen = set()
        for qname, bbox in qs:
            try:
                crop = pg.within_bbox(bbox)
                tbls = crop.extract_tables() or []
                for tbl in tbls:
                    if not tbl or len(tbl) < 2: continue
                    key = str(tbl[0])
                    if key in seen: continue
                    seen.add(key)
                    out.append({
                        "bbox":    list(bbox),
                        "source":  "quadrant",
                        "page_no": page_no,
                        "quadrant":qname,
                        "raw_data":tbl,
                    })
            except Exception as e:
                log.debug("[MDL002] quadrant %s page %d: %s", qname, page_no, e)
        return out

    try:
        # v1.1.0 fast path
        if doc_cache is not None and doc_cache.pdfplumber_pdf is not None:
            pg = doc_cache.pdfplumber_page(page_no)
            if pg is not None:
                results.extend(_do_quadrants(pg))
            return results
        # Legacy path
        with pdfplumb.open(pdf_path) as pdf:
            if page_no - 1 >= len(pdf.pages): return results
            pg = pdf.pages[page_no - 1]
            results.extend(_do_quadrants(pg))
    except Exception as e:
        log.debug("[MDL002] split_quadrants page %d: %s", page_no, e)
    return results

def _detect_vector_regions(pdf_path: str, page_no: int,
                            doc_cache: Optional["MDL002DocCache"] = None) -> List[Dict]:
    """VRN-MDL002 vector line detection — v1.1.0 doc_cache fast path."""
    regions = []
    if fitz is None: return regions
    try:
        # v1.1.0 fast path
        if doc_cache is not None and doc_cache.fitz_doc is not None:
            pg = doc_cache.fitz_page(page_no)
            if pg is None: return regions
            paths = pg.get_drawings()
        else:
            doc  = fitz.open(pdf_path)
            if page_no - 1 >= len(doc): doc.close(); return regions
            pg   = doc[page_no - 1]
            paths = pg.get_drawings()
            doc.close()

        h_lines = [p for p in paths if abs(p["rect"].y1 - p["rect"].y0) < 3]
        v_lines = [p for p in paths if abs(p["rect"].x1 - p["rect"].x0) < 3]
        if len(h_lines) >= 3 and len(v_lines) >= 2:
            all_rects = [p["rect"] for p in h_lines + v_lines]
            x0 = min(r.x0 for r in all_rects)
            y0 = min(r.y0 for r in all_rects)
            x1 = max(r.x1 for r in all_rects)
            y1 = max(r.y1 for r in all_rects)
            regions.append({
                "bbox":    [x0, y0, x1, y1],
                "source":  "vector_lines",
                "page_no": page_no,
                "quadrant":"full",
                "raw_data":[],
            })
    except Exception as e:
        log.debug("[MDL002] vector detect: %s", e)
    return regions

# ============================================================================
# [VRN:ANCHOR:MDL002-VALIDATE-001] §8  TABLE VALIDATION
# ============================================================================

def validate_financial_table(
    raw_data: List[List[str]],
    cfg: Dict,
) -> Tuple[bool, List[str], List[str]]:
    """VRN-MDL002-FNC-006
    Returns (is_financial, header_periods, first_col_subjects)
    Validation rules:
    ① Header row contains >= min_time_cols time patterns (year/quarter)
    ② First column contains >= min_acct_hits accounting subject keywords
    """
    if not raw_data or len(raw_data) < 2:
        return False, [], []

    min_t = cfg.get("min_time_cols", 2)
    min_a = cfg.get("min_acct_hits", 1)

    # Check header row (first 1-2 rows) for time patterns
    header_periods: List[str] = []
    for row_idx in range(min(2, len(raw_data))):
        row = raw_data[row_idx] or []
        for cell in row:
            cell_s = str(cell or "").strip()
            m = TIME_HEADER_RE.findall(cell_s)
            header_periods.extend(m)
    header_periods = list(dict.fromkeys(header_periods))  # dedup preserve order

    # Check first column for accounting subjects
    first_col: List[str] = []
    for row in raw_data[1:]:  # skip header
        if row and row[0]:
            first_col.append(str(row[0]).strip())

    acct_hits = [s for s in first_col
                 if any(kw.lower() in s.lower() for kw in ACCT_SUBJECTS)]

    is_fin = len(header_periods) >= min_t and len(acct_hits) >= min_a
    return is_fin, header_periods, acct_hits

# ============================================================================
# [VRN:ANCHOR:MDL002-EXTRACT-001] §9  MULTI-ENGINE TABLE EXTRACTION
# ============================================================================

def extract_table_from_region(
    pdf_path: str,
    page_no:  int,
    region:   Dict,
    cfg:      Dict,
    doc_cache: Optional["MDL002DocCache"] = None,    # v1.1.0 NEW
) -> Tuple[List[List[str]], str]:
    """VRN-MDL002-FNC-007
    If region already has raw_data → use it.
    Otherwise try engines in priority order within bbox.
    Returns (raw_data, engine_used)
    v1.1.0: doc_cache fast path for pdfplumber + fitz engines.
    """
    # If already extracted (from pdfplumber quadrant split)
    if region.get("raw_data"):
        return region["raw_data"], region.get("source", "cached")

    bbox   = region.get("bbox", [])
    order  = cfg.get("engine_order", "pdfplumber,camelot,tabula,fitz").split(",")

    for engine in order:
        engine = engine.strip()
        try:
            if engine == "pdfplumber" and pdfplumb and bbox:
                # v1.1.0 fast path
                if doc_cache is not None and doc_cache.pdfplumber_pdf is not None:
                    pg = doc_cache.pdfplumber_page(page_no)
                    if pg is not None:
                        crop = pg.within_bbox(tuple(bbox))
                        tbls = crop.extract_tables() or []
                        if tbls and tbls[0]:
                            return tbls[0], "pdfplumber_crop"
                else:
                    with pdfplumb.open(pdf_path) as pdf:
                        if page_no - 1 < len(pdf.pages):
                            pg   = pdf.pages[page_no - 1]
                            crop = pg.within_bbox(tuple(bbox))
                            tbls = crop.extract_tables() or []
                            if tbls and tbls[0]:
                                return tbls[0], "pdfplumber_crop"

            elif engine == "camelot" and camelot:
                tables = camelot.read_pdf(pdf_path, pages=str(page_no), flavor="lattice")
                if len(tables) > 0:
                    return tables[0].data.values.tolist(), "camelot_lattice"

            elif engine == "tabula" and tabula:
                import tabula as tab
                dfs = tab.read_pdf(pdf_path, pages=page_no, multiple_tables=True,
                                   silent=True)
                if dfs and len(dfs) > 0:
                    return [dfs[0].columns.tolist()] + dfs[0].fillna("").values.tolist(), "tabula"

            elif engine == "fitz" and fitz:
                # v1.1.0 fast path
                if doc_cache is not None and doc_cache.fitz_doc is not None:
                    pg_fz = doc_cache.fitz_page(page_no)
                    if pg_fz is not None:
                        text = pg_fz.get_text("dict")
                        lines = []
                        for block in text.get("blocks", []):
                            for line in block.get("lines", []):
                                cells = [span["text"].strip()
                                         for span in line.get("spans", [])
                                         if span.get("text", "").strip()]
                                if cells: lines.append(cells)
                        if lines: return lines, "fitz_lines"
                    continue
                doc = fitz.open(pdf_path)
                if page_no - 1 < len(doc):
                    pg   = doc[page_no - 1]
                    text = pg.get_text("dict")
                    doc.close()
                    # Extract text lines as minimal table
                    lines = []
                    for block in text.get("blocks", []):
                        for line in block.get("lines", []):
                            cells = [span["text"].strip()
                                     for span in line.get("spans", [])
                                     if span.get("text","").strip()]
                            if cells: lines.append(cells)
                    if lines: return lines, "fitz_text"

        except Exception as e:
            log.debug("[MDL002] engine %s page %d: %s", engine, page_no, e)

    return [], "failed"

# ============================================================================
# [VRN:ANCHOR:MDL002-TEXT-001] §10  FULL-TEXT EXTRACTION
# ============================================================================

def extract_text_blocks(
    pdf_path: str,
    page_no:  int,
    page_cls: str,
    report_code: str,
    doc_cache: Optional["MDL002DocCache"] = None,    # v1.1.0 NEW
) -> List[TextBlock]:
    """VRN-MDL002-FNC-008  Extract text blocks with position for MDL003 text repair.
    v1.1.0: doc_cache fast path."""
    blocks: List[TextBlock] = []
    block_counter = 1

    if fitz:
        # v1.1.0 fast path
        if doc_cache is not None and doc_cache.fitz_doc is not None:
            try:
                pg = doc_cache.fitz_page(page_no)
                if pg is not None:
                    raw = pg.get_text("dict")
                    for blk in raw.get("blocks", []):
                        if blk.get("type") != 0: continue
                        lines_text = []; max_size = 0.0; is_bold = False
                        for ln in blk.get("lines", []):
                            ln_text = " ".join(sp["text"] for sp in ln.get("spans", []))
                            lines_text.append(ln_text)
                            for sp in ln.get("spans", []):
                                sz = sp.get("size", 0)
                                if sz > max_size: max_size = sz
                                if "Bold" in sp.get("font", ""): is_bold = True
                        txt = " ".join(lines_text).strip()
                        if not txt: continue
                        rect = blk.get("bbox", [0, 0, 0, 0])
                        bid  = "P{:03d}TXT{:03d}".format(page_no, block_counter)
                        is_t = len(txt) < 40 and not re.search(r"[\u3002\uff0c\uff1b]$", txt)
                        blocks.append(TextBlock(
                            pdf_name=Path(pdf_path).name, report_code=report_code,
                            page_no=page_no, block_id=bid, block_type=page_cls,
                            text=txt, bbox=list(rect), is_title=is_t,
                            is_bold=is_bold, font_size=round(max_size, 1),
                        ))
                        block_counter += 1
                return blocks
            except Exception as e:
                log.debug("[MDL002] text blocks fitz cache page %d: %s", page_no, e)
        try:
            doc = fitz.open(pdf_path)
            if page_no - 1 < len(doc):
                pg   = doc[page_no - 1]
                raw  = pg.get_text("dict")
                for blk in raw.get("blocks", []):
                    if blk.get("type") != 0: continue   # 0=text
                    lines_text = []
                    max_size   = 0.0
                    is_bold    = False
                    for ln in blk.get("lines", []):
                        ln_text = " ".join(sp["text"] for sp in ln.get("spans", []))
                        lines_text.append(ln_text)
                        for sp in ln.get("spans", []):
                            sz = sp.get("size", 0)
                            if sz > max_size: max_size = sz
                            if "Bold" in sp.get("font", ""):
                                is_bold = True
                    txt = " ".join(lines_text).strip()
                    if not txt: continue
                    rect  = blk.get("bbox", [0, 0, 0, 0])
                    bid   = "P{:03d}TXT{:03d}".format(page_no, block_counter)
                    is_t  = len(txt) < 40 and not re.search(r"[。，；]$", txt)
                    blocks.append(TextBlock(
                        pdf_name    = Path(pdf_path).name,
                        report_code = report_code,
                        page_no     = page_no,
                        block_id    = bid,
                        block_type  = page_cls,
                        text        = txt,
                        bbox        = list(rect),
                        is_title    = is_t,
                        is_bold     = is_bold,
                        font_size   = round(max_size, 1),
                    ))
                    block_counter += 1
            doc.close()
        except Exception as e:
            log.debug("[MDL002] text blocks fitz page %d: %s", page_no, e)

    elif pdfplumb:
        # v1.1.0 fast path
        if doc_cache is not None and doc_cache.pdfplumber_pdf is not None:
            try:
                pg = doc_cache.pdfplumber_page(page_no)
                if pg is not None:
                    lines = pg.extract_text_lines() or []
                    for ln in lines:
                        txt = (ln.get("text") or "").strip()
                        if not txt: continue
                        bid  = "P{:03d}TXT{:03d}".format(page_no, block_counter)
                        bbox = [ln.get("x0",0), ln.get("top",0),
                                ln.get("x1",0), ln.get("bottom",0)]
                        blocks.append(TextBlock(
                            pdf_name=Path(pdf_path).name, report_code=report_code,
                            page_no=page_no, block_id=bid, block_type=page_cls,
                            text=txt, bbox=bbox))
                        block_counter += 1
                return blocks
            except Exception as e:
                log.debug("[MDL002] text blocks pdfplumber cache page %d: %s", page_no, e)
        try:
            with pdfplumb.open(pdf_path) as pdf:
                if page_no - 1 < len(pdf.pages):
                    pg    = pdf.pages[page_no - 1]
                    lines = pg.extract_text_lines() or []
                    for ln in lines:
                        txt = (ln.get("text") or "").strip()
                        if not txt: continue
                        bid  = "P{:03d}TXT{:03d}".format(page_no, block_counter)
                        bbox = [ln.get("x0",0), ln.get("top",0),
                                ln.get("x1",0), ln.get("bottom",0)]
                        blocks.append(TextBlock(
                            pdf_name    = Path(pdf_path).name,
                            report_code = report_code,
                            page_no     = page_no,
                            block_id    = bid,
                            block_type  = page_cls,
                            text        = txt,
                            bbox        = bbox,
                        ))
                        block_counter += 1
        except Exception as e:
            log.debug("[MDL002] text blocks pdfplumber page %d: %s", page_no, e)

    return blocks

# ============================================================================
# [VRN:ANCHOR:MDL002-NUMBER-001] §11  REGION NUMBERING
# ============================================================================

def number_all_regions(
    tables:      List[TableRecord],
    text_blocks: List[TextBlock],
    pdf_name:    str,
    report_code: str,
) -> Tuple[List[Dict], List[Dict]]:
    """VRN-MDL002-FNC-010
    Assign sequential IDs: P{page:03d}TBL{seq:03d} and P{page:03d}TXT{seq:03d}
    Returns serialisable dicts.
    """
    # Group tables by page
    tbl_by_page: Dict[int, List[TableRecord]] = collections.defaultdict(list)
    for t in tables: tbl_by_page[t.page_no].append(t)

    tbl_dicts = []
    for pg_no in sorted(tbl_by_page):
        for seq, t in enumerate(tbl_by_page[pg_no], start=1):
            t.region_id = "P{:03d}TBL{:03d}".format(pg_no, seq)
            tbl_dicts.append({
                "region_id":           t.region_id,
                "pdf_name":            pdf_name,
                "report_code":         report_code,
                "page_no":             t.page_no,
                "region_type":         t.region_type,
                "quadrant":            t.quadrant,
                "bbox":                t.bbox,
                "engine_used":         t.engine_used,
                "is_financial":        t.is_financial,
                "header_periods":      t.header_periods,
                "n_rows":              t.n_rows,
                "n_cols":              t.n_cols,
                "raw_data":            t.raw_data,
                "first_col_subjects":  t.first_col_subjects,
                "caption":             t.caption,
                "error":               t.error,
            })

    # Text blocks already have IDs
    txt_dicts = [{
        "block_id":   b.block_id,
        "pdf_name":   b.pdf_name,
        "report_code":b.report_code,
        "page_no":    b.page_no,
        "block_type": b.block_type,
        "text":       b.text,
        "bbox":       b.bbox,
        "is_title":   b.is_title,
        "is_bold":    b.is_bold,
        "font_size":  b.font_size,
    } for b in text_blocks]

    return tbl_dicts, txt_dicts

# ============================================================================
# [VRN:ANCHOR:MDL002-DB-001] §12  DB WRITER
# ============================================================================

class MDL002DBWriter:
    """VRN-MDL002-CLS-002"""

    DDL = """
CREATE TABLE IF NOT EXISTS vrn_mdl002_tables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    region_id TEXT, pdf_name TEXT, report_code TEXT,
    page_no INTEGER, region_type TEXT, quadrant TEXT,
    bbox TEXT, engine_used TEXT, is_financial INTEGER,
    header_periods TEXT, n_rows INTEGER, n_cols INTEGER,
    first_col_subjects TEXT, caption TEXT, error TEXT,
    ts TEXT DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS vrn_mdl002_text_blocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    block_id TEXT, pdf_name TEXT, report_code TEXT,
    page_no INTEGER, block_type TEXT, text TEXT,
    bbox TEXT, is_title INTEGER, is_bold INTEGER, font_size REAL,
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

    def insert_tables(self, recs: List[Dict]):
        sql = """INSERT INTO vrn_mdl002_tables
                 (region_id,pdf_name,report_code,page_no,region_type,quadrant,
                  bbox,engine_used,is_financial,header_periods,n_rows,n_cols,
                  first_col_subjects,caption,error)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
        with self._lock:
            for r in recs:
                self._con.execute(sql, (
                    r.get("region_id",""), r.get("pdf_name",""),
                    r.get("report_code",""), r.get("page_no",0),
                    r.get("region_type",""), r.get("quadrant",""),
                    json.dumps(r.get("bbox",[])),
                    r.get("engine_used",""),
                    1 if r.get("is_financial") else 0,
                    json.dumps(r.get("header_periods",[])),
                    r.get("n_rows",0), r.get("n_cols",0),
                    json.dumps(r.get("first_col_subjects",[])),
                    r.get("caption",""), r.get("error",""),
                ))
            self._con.commit()

    def insert_text_blocks(self, recs: List[Dict]):
        sql = """INSERT INTO vrn_mdl002_text_blocks
                 (block_id,pdf_name,report_code,page_no,block_type,text,
                  bbox,is_title,is_bold,font_size)
                 VALUES (?,?,?,?,?,?,?,?,?,?)"""
        with self._lock:
            for r in recs:
                self._con.execute(sql, (
                    r.get("block_id",""), r.get("pdf_name",""),
                    r.get("report_code",""), r.get("page_no",0),
                    r.get("block_type",""), r.get("text",""),
                    json.dumps(r.get("bbox",[])),
                    1 if r.get("is_title") else 0,
                    1 if r.get("is_bold") else 0,
                    r.get("font_size",0.0),
                ))
            self._con.commit()

    def export_parquet(self, out_dir: str):
        if not pd or not pyarrow: return
        try:
            df = pd.read_sql("SELECT * FROM vrn_mdl002_tables", self._con)
            df.to_parquet(str(Path(out_dir) / "VRN_MDL002_Layout.parquet"), index=False)
        except Exception as e: log.warning("[MDL002] parquet: %s", e)

    def export_csv(self, out_dir: str):
        if not pd: return
        try:
            df = pd.read_sql("SELECT * FROM vrn_mdl002_tables", self._con)
            df.to_csv(str(Path(out_dir) / "VRN_MDL002_Layout.csv"),
                      index=False, encoding="utf-8-sig")
        except Exception as e: log.warning("[MDL002] csv: %s", e)

# ============================================================================
# [VRN:ANCHOR:MDL002-BATCH-001] §12.5  P3 BATCH BUFFER + DUCK WRITER (v1.1.0)
# ── 同 MDL003/004/005 v1.1.0 模式：worker push (低鎖)，主執行緒一次 flush  ─
# ============================================================================

class MDL002BatchBuffer:
    """VRN-MDL002-CLS-007  P3 batch buffer (NEW v1.1.0)."""
    def __init__(self, batch_size: int = 5000):
        self.batch_size = batch_size
        self._tbl_buf: List[Tuple] = []
        self._txt_buf: List[Tuple] = []
        self._lock = threading.Lock()

    def push_tables(self, tbl_dicts: List[Dict]):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        rows = [
            (None,
             d.get("pdf_name",""), d.get("report_code",""), d.get("page_no",0),
             d.get("region_id",""), d.get("region_type",""), d.get("quadrant",""),
             json.dumps(d.get("bbox",[])),
             d.get("engine_used",""), 1 if d.get("is_financial") else 0,
             json.dumps(d.get("header_periods",[]), ensure_ascii=False),
             d.get("n_rows",0), d.get("n_cols",0),
             json.dumps(d.get("raw_data",[]), ensure_ascii=False),
             json.dumps(d.get("first_col_subjects",[]), ensure_ascii=False),
             ts)
            for d in tbl_dicts
        ]
        with self._lock:
            self._tbl_buf.extend(rows)

    def push_text_blocks(self, txt_dicts: List[Dict]):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        rows = [
            (None,
             d.get("pdf_name",""), d.get("report_code",""), d.get("page_no",0),
             d.get("block_id",""), d.get("block_type",""),
             d.get("text","")[:4000], json.dumps(d.get("bbox",[])),
             1 if d.get("is_title") else 0,
             1 if d.get("is_bold")  else 0,
             d.get("font_size",0.0), ts)
            for d in txt_dicts
        ]
        with self._lock:
            self._txt_buf.extend(rows)

    def stats(self) -> Dict[str, int]:
        return {"tbl": len(self._tbl_buf), "txt": len(self._txt_buf)}

    def consume_all(self) -> Tuple[List, List]:
        with self._lock:
            t, x = self._tbl_buf, self._txt_buf
            self._tbl_buf, self._txt_buf = [], []
        return t, x


_DDL_DUCK_M002_TABLES = """
CREATE TABLE IF NOT EXISTS vrn_mdl002_tables (
    id INTEGER, pdf_name VARCHAR, report_code VARCHAR, page_no INTEGER,
    region_id VARCHAR, region_type VARCHAR, quadrant VARCHAR, bbox VARCHAR,
    engine_used VARCHAR, is_financial INTEGER, header_periods VARCHAR,
    n_rows INTEGER, n_cols INTEGER, raw_data VARCHAR,
    first_col_subjects VARCHAR, ts VARCHAR
);
"""
_DDL_DUCK_M002_TXT = """
CREATE TABLE IF NOT EXISTS vrn_mdl002_text_blocks (
    id INTEGER, pdf_name VARCHAR, report_code VARCHAR, page_no INTEGER,
    block_id VARCHAR, block_type VARCHAR, text VARCHAR, bbox VARCHAR,
    is_title INTEGER, is_bold INTEGER, font_size DOUBLE, ts VARCHAR
);
"""


class MDL002DuckWriter:
    """VRN-MDL002-CLS-008  DuckDB primary writer (NEW v1.1.0)."""
    def __init__(self, db_path: str):
        if not DUCKDB_OK:
            raise RuntimeError("duckdb not available")
        self.db_path = db_path
        self._con = duckdb_lib.connect(db_path)
        self._con.execute(_DDL_DUCK_M002_TABLES)
        self._con.execute(_DDL_DUCK_M002_TXT)

    def flush(self, tbl_rows: List, txt_rows: List) -> Dict[str, int]:
        n_t = n_x = 0
        try:
            self._con.execute("BEGIN TRANSACTION")
            if tbl_rows:
                self._con.executemany(
                    "INSERT INTO vrn_mdl002_tables VALUES "
                    "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", tbl_rows)
                n_t = len(tbl_rows)
            if txt_rows:
                self._con.executemany(
                    "INSERT INTO vrn_mdl002_text_blocks VALUES "
                    "(?,?,?,?,?,?,?,?,?,?,?,?)", txt_rows)
                n_x = len(txt_rows)
            self._con.execute("COMMIT")
        except Exception as e:
            try: self._con.execute("ROLLBACK")
            except: pass
            log.error("[MDL002] DuckDB flush fail: %s", e); raise
        return {"tbl": n_t, "txt": n_x}

    def export_parquet_polars(self, out_dir: str) -> Optional[str]:
        out_path = str(Path(out_dir) / "VRN_MDL002_Layout.parquet")
        try:
            self._con.execute(
                f"COPY (SELECT * FROM vrn_mdl002_tables) "
                f"TO '{out_path}' (FORMAT PARQUET, COMPRESSION ZSTD)")
            return out_path
        except Exception as e:
            log.warning("[MDL002] DuckDB→parquet fail: %s", e); return None

    def export_csv_polars(self, out_dir: str) -> Optional[str]:
        out_path = str(Path(out_dir) / "VRN_MDL002_Layout.csv")
        if POLARS_OK:
            try:
                rows = self._con.execute("SELECT * FROM vrn_mdl002_tables").fetchall()
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
                log.debug("[MDL002] polars-fetchall csv fail (%s), fallback DuckDB", e)
        try:
            self._con.execute(
                f"COPY (SELECT * FROM vrn_mdl002_tables) "
                f"TO '{out_path}' (HEADER, DELIMITER ',')")
            data = Path(out_path).read_bytes()
            Path(out_path).write_bytes(b"\xef\xbb\xbf" + data)
            return out_path
        except Exception as e:
            log.warning("[MDL002] csv export fail: %s", e); return None

    def close(self):
        try: self._con.close()
        except: pass


# ── Append v1.1.0 batch flush + polars exports to legacy DBWriter ─────────

def _mdl002_dbwriter_flush(self, tbl_rows: List, txt_rows: List) -> Dict[str, int]:
    n_t = n_x = 0
    with self._lock:
        try:
            self._con.execute("BEGIN")
            if tbl_rows:
                # Strip id (front) + ts (back)
                self._con.executemany(
                    "INSERT INTO vrn_mdl002_tables "
                    "(pdf_name,report_code,page_no,region_id,region_type,quadrant,"
                    " bbox,engine_used,is_financial,header_periods,n_rows,n_cols,"
                    " raw_data,first_col_subjects) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    [r[1:-1] for r in tbl_rows])
                n_t = len(tbl_rows)
            if txt_rows:
                self._con.executemany(
                    "INSERT INTO vrn_mdl002_text_blocks "
                    "(pdf_name,report_code,page_no,block_id,block_type,text,"
                    " bbox,is_title,is_bold,font_size) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?)",
                    [r[1:-1] for r in txt_rows])
                n_x = len(txt_rows)
            self._con.commit()
        except Exception as e:
            try: self._con.rollback()
            except: pass
            log.error("[MDL002] sqlite flush fail: %s", e); raise
    return {"tbl": n_t, "txt": n_x}

MDL002DBWriter.flush = _mdl002_dbwriter_flush


def _mdl002_dbwriter_export_parquet_polars(self, out_dir: str) -> Optional[str]:
    out_path = str(Path(out_dir) / "VRN_MDL002_Layout.parquet")
    if not POLARS_OK:
        self.export_parquet(out_dir)
        return out_path if Path(out_path).exists() else None
    try:
        with self._lock:
            cur = self._con.execute("SELECT * FROM vrn_mdl002_tables")
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description] if cur.description else []
        if not rows:
            df = pl.DataFrame(schema={c: pl.Utf8 for c in cols} if cols else None)
        else:
            df = pl.DataFrame(rows, schema=cols, orient="row")
        df.write_parquet(out_path, compression="zstd")
        return out_path
    except Exception as e:
        log.warning("[MDL002] polars→parquet fail (%s), fallback pandas", e)
        self.export_parquet(out_dir)
        return out_path if Path(out_path).exists() else None

def _mdl002_dbwriter_export_csv_polars(self, out_dir: str) -> Optional[str]:
    out_path = str(Path(out_dir) / "VRN_MDL002_Layout.csv")
    if not POLARS_OK:
        self.export_csv(out_dir)
        return out_path if Path(out_path).exists() else None
    try:
        with self._lock:
            cur = self._con.execute("SELECT * FROM vrn_mdl002_tables")
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
        log.debug("[MDL002] polars-fetchall csv fail (%s), pandas fallback", e)
        self.export_csv(out_dir)
        return out_path if Path(out_path).exists() else None

MDL002DBWriter.export_parquet_polars = _mdl002_dbwriter_export_parquet_polars
MDL002DBWriter.export_csv_polars     = _mdl002_dbwriter_export_csv_polars


# ============================================================================
# [VRN:ANCHOR:MDL002-SELFCHK-001] §12.7  P6 4-PHASE SELF-VERIFICATION (v1.1.0)
# ============================================================================

class MDL002SelfVerifier:
    """VRN-MDL002-CLS-009  P6 4-phase debug chain (NEW v1.1.0)."""
    def __init__(self, cfg: Dict, run_summary: Dict, mdl002_temp: str):
        self.cfg = cfg; self.run_summary = run_summary
        self.mdl002_temp = mdl002_temp
        self.checks: List[Dict] = []

    def _add(self, phase, name, ok, detail=""):
        self.checks.append({"phase":phase,"name":name,"ok":bool(ok),"detail":detail})

    def run(self) -> Dict:
        # Phase 1
        self._add("1/4", "Module version 1.1.0", __version__ == "1.1.0", __version__)
        self._add("1/4", "TW_TICKER_REGEX locked",
                  TW_TICKER_REGEX.pattern == r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})",
                  "")
        self._add("1/4", "Pre-compiled regex pool",
                  all(p is not None for p in [_RE_YEAR4_v110, _RE_QUARTER_v110,
                                              _RE_YEAR_BARE_v110, _RE_DOUBLESPACE_v110,
                                              _RE_MOJIBAKE_v110]), "")
        self._add("1/4", "polars available", POLARS_OK, "")
        self._add("1/4", "duckdb available", DUCKDB_OK, "")

        # Phase 2: DocCache wiring
        self._add("2/4", "MDL002DocCache exists", "MDL002DocCache" in globals(), "")
        self._add("2/4", "MDL002BatchBuffer exists", "MDL002BatchBuffer" in globals(), "")
        self._add("2/4", "MDL002DuckWriter exists", "MDL002DuckWriter" in globals(), "")
        self._add("2/4", "detect_table_regions accepts doc_cache",
                  "doc_cache" in detect_table_regions.__code__.co_varnames, "")
        self._add("2/4", "split_quadrants accepts doc_cache",
                  "doc_cache" in split_quadrants.__code__.co_varnames, "")
        self._add("2/4", "extract_table_from_region accepts doc_cache",
                  "doc_cache" in extract_table_from_region.__code__.co_varnames, "")
        self._add("2/4", "extract_text_blocks accepts doc_cache",
                  "doc_cache" in extract_text_blocks.__code__.co_varnames, "")
        self._add("2/4", "_detect_vector_regions accepts doc_cache",
                  "doc_cache" in _detect_vector_regions.__code__.co_varnames, "")
        self._add("2/4", "process_one accepts buffer",
                  "buffer" in process_one.__code__.co_varnames, "")

        # Phase 3: DB
        duck_p   = Path(self.mdl002_temp) / "VRN_MDL002.duckdb"
        sqlite_p = Path(self.mdl002_temp) / "VRN_MDL002.db"
        self._add("3/4", "DB file exists", duck_p.exists() or sqlite_p.exists(),
                  f"duck={duck_p.exists()} sqlite={sqlite_p.exists()}")
        if duck_p.exists() and DUCKDB_OK:
            try:
                con = duckdb_lib.connect(str(duck_p), read_only=True)
                tbls = {t[0] for t in con.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema='main'").fetchall()}
                con.close()
                expected = {"vrn_mdl002_tables","vrn_mdl002_text_blocks"}
                self._add("3/4", "DuckDB schema 2 tables",
                          expected.issubset(tbls), str(sorted(tbls)))
            except Exception as e:
                self._add("3/4", "DuckDB schema 2 tables", False, str(e))

        # Phase 4
        for fn in ("VRN_MDL002_Layout.json", "VRN_MDL002_VerifySummary.json",
                   "VRN_MDL002_Layout.parquet", "VRN_MDL002_Layout.csv"):
            p = Path(self.mdl002_temp) / fn
            self._add("4/4", f"file:{fn}", p.exists(),
                      f"size={p.stat().st_size if p.exists() else 0}")
        ti = self.run_summary.get("total_tables", 0)
        self._add("4/4", "total_tables non-negative", ti >= 0, str(ti))

        n_total = len(self.checks); n_pass = sum(1 for c in self.checks if c["ok"])
        n_fail  = n_total - n_pass
        cls = "READY" if n_fail == 0 else ("NEAR-READY" if n_fail <= 2 else "NOT-READY")
        return {"total":n_total,"pass":n_pass,"fail":n_fail,
                "classification":cls,"checks":self.checks,
                "generated":time.strftime("%Y-%m-%d %H:%M:%S")}


def build_self_verify_html_mdl002(verify_result: Dict, run_summary: Dict) -> str:
    """VRN-MDL002-FNC-014  VIA Visual Lock self-verify HTML (NEW v1.1.0)."""
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
        f"$ VRN_MDL002 v{__version__} self-verification",
        f"  generated      : {verify_result.get('generated','-')}",
        f"  classification : {cls} {cls_emoji}",
        f"  checks         : {verify_result.get('pass',0)}/{verify_result.get('total',0)} pass",
        "",
        "$ pipeline summary",
        f"  total reports  : {run_summary.get('total','-')}",
        f"  ok / fail      : {run_summary.get('ok_count','-')} / {run_summary.get('fail_count','-')}",
        f"  total pages    : {run_summary.get('total_pages','-')}",
        f"  total tables   : {run_summary.get('total_tables','-')}",
        f"  fin tables     : {run_summary.get('total_fin_tables','-')}",
        f"  total text blk : {run_summary.get('total_text_blocks','-')}",
    ]
    term_html = "\n".join(sum_lines)

    html = f"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="UTF-8">
<title>VRN MDL002 v{__version__} · Self-Verification · {cls}</title>
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
<div class="hdr"><h1>VRN MDL002 · LayoutExtractor v{__version__}<span class="cls-badge">{cls}</span></h1>
<div class="sub">VeritasReportNova · 4-Phase Self-Verification · {time.strftime("%Y-%m-%d %H:%M:%S")}</div></div>
<div class="cd"><div class="cd-h">RUN SUMMARY</div><div class="cd-b"><div class="tm">{term_html}</div></div></div>
{"".join(phase_html)}
<div class="foot">Module: {__module_id__} · Asset: {__asset_id__} · v{__version__}</div>
</body></html>"""
    return html


# ============================================================================
# CORE PROCESSOR
# ============================================================================

def _process_one_page_v110(
    pdf_path: str,
    pg_no:    int,
    pdf_name: str,
    report_code: str,
    cfg:      Dict,
    doc_cache: Optional["MDL002DocCache"],
) -> Tuple[List[TableRecord], List[TextBlock], Optional[str]]:
    """v1.1.0 inner page worker — uses doc_cache, returns (tables, text_blocks, fin_flag)."""
    page_tables: List[TableRecord] = []
    page_text_blocks: List[TextBlock] = []
    fin_flag: Optional[str] = None

    # ── Page text for classification (cache fast path) ──────────────────
    page_text = ""
    if doc_cache is not None and doc_cache.fitz_doc is not None:
        try:
            pg = doc_cache.fitz_page(pg_no)
            if pg is not None: page_text = pg.get_text()
        except Exception: pass
    elif doc_cache is not None and doc_cache.pdfplumber_pdf is not None:
        try:
            pg = doc_cache.pdfplumber_page(pg_no)
            if pg is not None: page_text = pg.extract_text() or ""
        except Exception: pass
    elif fitz:
        try:
            doc = fitz.open(pdf_path)
            if pg_no - 1 < len(doc): page_text = doc[pg_no - 1].get_text()
            doc.close()
        except Exception: pass
    elif pdfplumb:
        try:
            with pdfplumb.open(pdf_path) as pdf:
                if pg_no - 1 < len(pdf.pages):
                    page_text = pdf.pages[pg_no - 1].extract_text() or ""
        except Exception: pass

    pg_cls = classify_page(page_text, pg_no)
    if pg_cls == "fin_page": fin_flag = pg_no

    # ── 1ST PAGE: Zonal extraction ─────────────────────────────────────
    if pg_cls == "1st_page" and pdfplumb:
        try:
            # cache fast path
            if doc_cache is not None and doc_cache.pdfplumber_pdf is not None:
                pg_obj = doc_cache.pdfplumber_page(1)
                if pg_obj is not None:
                    zone_tables = extract_zones_first_page(pdf_path, pg_obj, cfg)
                    for zt in zone_tables:
                        raw = zt.get("raw_data", [])
                        if not raw: continue
                        is_fin, periods, subjects = validate_financial_table(raw, cfg)
                        page_tables.append(TableRecord(
                            pdf_name=pdf_name, report_code=report_code,
                            page_no=pg_no,
                            region_type="1st_page_" + zt.get("zone",""),
                            quadrant="full", bbox=zt.get("bbox",[]),
                            engine_used="pdfplumber_zone",
                            is_financial=is_fin, header_periods=periods,
                            n_rows=zt.get("n_rows",0), n_cols=zt.get("n_cols",0),
                            raw_data=raw, first_col_subjects=subjects,
                        ))
            else:
                with pdfplumb.open(pdf_path) as pdf:
                    pg_obj = pdf.pages[0]
                    zone_tables = extract_zones_first_page(pdf_path, pg_obj, cfg)
                    for zt in zone_tables:
                        raw = zt.get("raw_data", [])
                        if not raw: continue
                        is_fin, periods, subjects = validate_financial_table(raw, cfg)
                        page_tables.append(TableRecord(
                            pdf_name=pdf_name, report_code=report_code,
                            page_no=pg_no,
                            region_type="1st_page_" + zt.get("zone",""),
                            quadrant="full", bbox=zt.get("bbox",[]),
                            engine_used="pdfplumber_zone",
                            is_financial=is_fin, header_periods=periods,
                            n_rows=zt.get("n_rows",0), n_cols=zt.get("n_cols",0),
                            raw_data=raw, first_col_subjects=subjects,
                        ))
        except Exception as e:
            log.debug("[MDL002] 1st-page extract %s: %s", pdf_name, e)
    else:
        regions = detect_table_regions(pdf_path, pg_no, page_text, pg_cls, cfg,
                                        doc_cache=doc_cache)
        for region in regions:
            raw, eng = extract_table_from_region(pdf_path, pg_no, region, cfg,
                                                  doc_cache=doc_cache)
            if not raw or len(raw) < 2: continue
            is_fin, periods, subjects = validate_financial_table(raw, cfg)
            page_tables.append(TableRecord(
                pdf_name=pdf_name, report_code=report_code,
                page_no=pg_no, region_type=pg_cls,
                quadrant=region.get("quadrant","full"),
                bbox=region.get("bbox",[]), engine_used=eng,
                is_financial=is_fin, header_periods=periods,
                n_rows=len(raw),
                n_cols=max(len(r) for r in raw) if raw else 0,
                raw_data=raw, first_col_subjects=subjects,
            ))

    # ── Text blocks ─────────────────────────────────────────────────────
    txt_blocks = extract_text_blocks(pdf_path, pg_no, pg_cls, report_code,
                                      doc_cache=doc_cache)
    page_text_blocks.extend(txt_blocks)

    return page_tables, page_text_blocks, fin_flag


def process_one(
    pdf_path: str,
    cfg:      Dict,
    db:       Optional[MDL002DBWriter],
    buffer:   Optional["MDL002BatchBuffer"] = None,    # v1.1.0 NEW
) -> Dict:
    """VRN-MDL002-FNC-011  Process one PDF → extract all layout + tables + text.
    v1.1.0: open PDF ONCE via DocCache (B1/B2 fix), pages parallel (B3 fix),
            buffer pushes DB rows without lock contention (B4 fix).
    """
    t0      = time.perf_counter()
    meta    = _parse_pdf_meta(pdf_path)
    pdf_name   = Path(pdf_path).name
    report_code= meta["report_code"]
    max_pages  = cfg.get("max_pages", 50)

    rec = {
        "pdf_name":     pdf_name,
        "report_code":  report_code,
        "ticker":       meta["ticker"],
        "report_date":  meta["report_date"],
        "broker_abbr":  meta["broker_abbr"],
        "n_pages":      0,
        "n_tables":     0,
        "n_financial_tables": 0,
        "n_text_blocks":0,
        "fin_pages":    [],
        "tables":       [],
        "text_blocks":  [],
        "ok":           False,
        "error":        None,
        "elapsed":      0.0,
    }

    if not os.path.isfile(pdf_path):
        rec["error"] = f"PDF not found: {pdf_path}"; return rec

    use_cache    = cfg.get("use_doc_cache", True)
    page_par     = cfg.get("page_parallel", True)
    page_workers = cfg.get("page_workers", 0) or max(2, (os.cpu_count() or 4) - 1)

    try:
        all_tables:  List[TableRecord]  = []
        all_text:    List[TextBlock]    = []

        # v1.1.0: open via DocCache once
        cache_ctx = MDL002DocCache(pdf_path) if use_cache else None
        if cache_ctx is not None:
            cache_ctx.__enter__()

        try:
            # Page count via cache
            if cache_ctx is not None and cache_ctx.n_pages > 0:
                n_pages = min(cache_ctx.n_pages, max_pages)
            elif fitz:
                doc = fitz.open(pdf_path)
                n_pages = min(len(doc), max_pages); doc.close()
            elif pdfplumb:
                with pdfplumb.open(pdf_path) as pdf:
                    n_pages = min(len(pdf.pages), max_pages)
            else:
                n_pages = 0
            rec["n_pages"] = n_pages

            if page_par and n_pages > 1:
                # P2: page-level parallel
                page_results: Dict[int, Tuple] = {}
                with ThreadPoolExecutor(max_workers=page_workers) as ex:
                    futs = {ex.submit(_process_one_page_v110,
                                      pdf_path, pg, pdf_name, report_code,
                                      cfg, cache_ctx): pg
                            for pg in range(1, n_pages + 1)}
                    for fut in as_completed(futs):
                        try:
                            tbls, txts, fin_pg = fut.result()
                            page_results[futs[fut]] = (tbls, txts, fin_pg)
                        except Exception as e:
                            log.warning("[MDL002] page %d: %s", futs[fut], e)
                # Reorder by page_no
                for pg in sorted(page_results):
                    tbls, txts, fin_pg = page_results[pg]
                    all_tables.extend(tbls)
                    all_text.extend(txts)
                    if fin_pg is not None and fin_pg not in rec["fin_pages"]:
                        rec["fin_pages"].append(fin_pg)
            else:
                for pg_no in range(1, n_pages + 1):
                    tbls, txts, fin_pg = _process_one_page_v110(
                        pdf_path, pg_no, pdf_name, report_code, cfg, cache_ctx)
                    all_tables.extend(tbls)
                    all_text.extend(txts)
                    if fin_pg is not None and fin_pg not in rec["fin_pages"]:
                        rec["fin_pages"].append(fin_pg)

            # Number + serialise
            tbl_dicts, txt_dicts = number_all_regions(all_tables, all_text, pdf_name, report_code)

            rec["n_tables"]           = len(tbl_dicts)
            rec["n_financial_tables"] = sum(1 for t in tbl_dicts if t.get("is_financial"))
            rec["n_text_blocks"]      = len(txt_dicts)
            rec["tables"]             = tbl_dicts
            rec["text_blocks"]        = txt_dicts
            rec["ok"]                 = True

            # v1.1.0: prefer buffer (no DB lock contention), fallback to legacy db
            if buffer is not None:
                try:
                    buffer.push_tables(tbl_dicts)
                    buffer.push_text_blocks(txt_dicts)
                except Exception as e:
                    log.warning("[MDL002] buffer push %s: %s", pdf_name, e)
            elif db:
                try:
                    db.insert_tables(tbl_dicts)
                    db.insert_text_blocks(txt_dicts)
                except Exception as e:
                    log.warning("[MDL002] DB insert %s: %s", pdf_name, e)

        finally:
            if cache_ctx is not None:
                cache_ctx.__exit__(None, None, None)

    except Exception as e:
        rec["error"] = str(e)
        log.error("[MDL002] process_one %s: %s", pdf_name, e)

    rec["elapsed"] = round(time.perf_counter() - t0, 2)
    log.info("[MDL002] %s: pages=%d tables=%d(fin=%d) txt=%d %s %.2fs",
             pdf_name, rec["n_pages"], rec["n_tables"],
             rec["n_financial_tables"], rec["n_text_blocks"],
             "OK" if rec["ok"] else "FAIL", rec["elapsed"])
    return rec

# ============================================================================
# [VRN:ANCHOR:MDL002-OUT-001] §13
# ============================================================================

def assemble_output(results: List[Dict]) -> Dict:
    """VRN-MDL002-FNC-012"""
    ok_count = sum(1 for r in results if r.get("ok"))
    return {
        "module":            __module_id__,
        "version":           __version__,
        "generated":         time.strftime("%Y-%m-%d %H:%M:%S"),
        "total":             len(results),
        "ok_count":          ok_count,
        "fail_count":        len(results) - ok_count,
        "total_pages":       sum(r.get("n_pages",0) for r in results),
        "total_tables":      sum(r.get("n_tables",0) for r in results),
        "total_fin_tables":  sum(r.get("n_financial_tables",0) for r in results),
        "total_text_blocks": sum(r.get("n_text_blocks",0) for r in results),
        "reports":           results,
    }

# ============================================================================
# [VRN:ANCHOR:MDL002-SYS-001] §14  PIPELINE ENTRY
# ============================================================================

class VRN_MDL002_LayoutExtractor:
    """VRN-MDL002-CLS-001
    run():
      1. Accel init
      2. List PDFs from pdf_temp
      3. Parallel process_one() — full layout + table + text extraction
      4. DB export
      5. VRN_MDL002_Layout.json → mdl002_temp
    """
    def __init__(self, cfg: Dict):
        self.cfg     = cfg
        workers      = cfg.get("workers", 0) or max(1, (os.cpu_count() or 4) - 1)
        self.workers = workers
        self.db: Optional[MDL002DBWriter] = None

    def run(self) -> Dict:
        run_t0      = time.perf_counter()
        pdf_temp    = self.cfg.get("pdf_temp",    _DEFAULTS["pdf_temp"])
        mdl002_temp = self.cfg.get("mdl002_temp", _DEFAULTS["mdl002_temp"])
        Path(mdl002_temp).mkdir(parents=True, exist_ok=True)

        _load_celeritas(self.cfg.get("ssot_dir", _DEFAULTS.get("ssot_dir","")))
        cap = _mdl002_accel_init(self.workers)
        log.info("[MDL002] accel caps: %s", cap)

        # ── v1.1.0: BatchBuffer + DuckDB primary + sqlite fallback ──────────
        self.buffer: Optional[MDL002BatchBuffer] = None
        self.duck:   Optional[MDL002DuckWriter]  = None
        if self.cfg.get("enable_db", True):
            self.buffer = MDL002BatchBuffer(
                batch_size=self.cfg.get("batch_size", 5000))
            if self.cfg.get("use_duckdb", True) and DUCKDB_OK:
                try:
                    self.duck = MDL002DuckWriter(
                        str(Path(mdl002_temp) / "VRN_MDL002.duckdb"))
                    log.info("[MDL002] DuckDB primary writer ready")
                except Exception as e:
                    log.warning("[MDL002] DuckDB init fail (%s), sqlite fallback", e)
                    self.duck = None
            try:
                self.db = MDL002DBWriter(str(Path(mdl002_temp) / "VRN_MDL002.db"))
                log.info("[MDL002] sqlite fallback writer ready")
            except Exception as e:
                log.warning("[MDL002] sqlite init fail: %s", e)
                self.db = None

        pdfs = list_pdfs_in_temp(pdf_temp)
        if not pdfs:
            log.warning("[MDL002] No PDFs in: %s", pdf_temp)
            empty = assemble_output([])
            _jwrite(str(Path(mdl002_temp) / "VRN_MDL002_Layout.json"), empty)
            return {"ok": True, "total": 0, "success": 0, "errors": [],
                    "out_dir": mdl002_temp}

        log.info("[MDL002] Processing %d PDFs, workers=%d  doc_cache=%s page_par=%s",
                 len(pdfs), self.workers,
                 self.cfg.get("use_doc_cache",True),
                 self.cfg.get("page_parallel",True))
        all_results: List[Dict] = []
        fail_count = 0

        with ThreadPoolExecutor(max_workers=self.workers) as ex:
            futs = {ex.submit(process_one, p, self.cfg, self.db, self.buffer): p
                    for p in pdfs}
            for fut in as_completed(futs):
                res = fut.result()
                all_results.append(res)
                if not res.get("ok"): fail_count += 1

        # ── v1.1.0: single-thread flush DB after pool closes ────────────────
        flush_stats = {"tbl": 0, "txt": 0}
        if self.buffer:
            t_rows, x_rows = self.buffer.consume_all()
            log.info("[MDL002] Buffer drain: tbl=%d txt=%d",
                     len(t_rows), len(x_rows))
            if self.duck:
                try:
                    flush_stats = self.duck.flush(t_rows, x_rows)
                    log.info("[MDL002] DuckDB flush: %s", flush_stats)
                except Exception as e:
                    log.warning("[MDL002] DuckDB flush fail (%s), sqlite fallback", e)
                    if self.db:
                        flush_stats = self.db.flush(t_rows, x_rows)
            elif self.db:
                flush_stats = self.db.flush(t_rows, x_rows)
                log.info("[MDL002] sqlite flush: %s", flush_stats)

        # ── v1.1.0: polars-direct exports ───────────────────────────────────
        parquet_path = csv_path = None
        if self.duck:
            parquet_path = self.duck.export_parquet_polars(mdl002_temp)
            csv_path     = self.duck.export_csv_polars(mdl002_temp)
        elif self.db:
            parquet_path = self.db.export_parquet_polars(mdl002_temp)
            csv_path     = self.db.export_csv_polars(mdl002_temp)
        log.info("[MDL002] Exports: parquet=%s csv=%s", parquet_path, csv_path)

        out = assemble_output(all_results)
        _jwrite(str(Path(mdl002_temp) / "VRN_MDL002_Layout.json"), out)

        verify = {
            "module":             __module_id__,
            "version":            __version__,
            "generated":          time.strftime("%Y-%m-%d %H:%M:%S"),
            "total":              len(pdfs),
            "ok":                 fail_count == 0,
            "ok_count":           len(pdfs) - fail_count,
            "fail_count":         fail_count,
            "total_tables":       out["total_tables"],
            "total_fin_tables":   out["total_fin_tables"],
            "total_text_blocks":  out["total_text_blocks"],
            "accel_caps":         cap,
            "flush_stats":        flush_stats,
            "fail_details": [{"pdf_name": r["pdf_name"], "error": r.get("error")}
                             for r in all_results if not r.get("ok")],
        }
        _jwrite(str(Path(mdl002_temp) / "VRN_MDL002_VerifySummary.json"), verify)

        # ── Close DBs BEFORE self-verify ────────────────────────────────────
        if self.duck: self.duck.close()
        if self.db:
            try: self.db._con.close()
            except: pass

        # ── v1.1.0: 4-phase self-verify HTML ────────────────────────────────
        sv_html_path = None
        if self.cfg.get("self_verify", True):
            try:
                sv = MDL002SelfVerifier(self.cfg, out, mdl002_temp).run()
                html = build_self_verify_html_mdl002(sv, out)
                sv_html_path = str(Path(mdl002_temp) / "VRN_MDL002_SelfVerify.html")
                Path(sv_html_path).write_text(html, encoding="utf-8")
                log.info("[MDL002] Self-verify: %s (%d/%d) → %s",
                         sv["classification"], sv["pass"], sv["total"], sv_html_path)
            except Exception as e:
                log.warning("[MDL002] self_verify build fail: %s", e)

        elapsed = round(time.perf_counter() - run_t0, 2)
        log.info("[MDL002] Complete: %d/%d OK  tables=%d(fin=%d)  text=%d  %.2fs",
                 len(pdfs) - fail_count, len(pdfs),
                 out["total_tables"], out["total_fin_tables"],
                 out["total_text_blocks"], elapsed)
        return {
            "ok":               fail_count == 0,
            "total":            len(pdfs),
            "success":          len(pdfs) - fail_count,
            "total_tables":     out["total_tables"],
            "total_fin_tables": out["total_fin_tables"],
            "elapsed":          elapsed,
            "flush_stats":      flush_stats,
            "self_verify_html": sv_html_path,
            "errors":           [r.get("error","") for r in all_results if not r.get("ok")],
            "out_dir":          mdl002_temp,
        }

# ============================================================================
# __all__
# ============================================================================

__all__ = [
    "__version__", "__module_id__",
    "TW_TICKER_REGEX", "TW_BLOOMBERG_REGEX", "TW_YFINANCE_REGEX",
    "FIN_KEYWORDS_ZH", "ACCT_SUBJECTS", "TIME_HEADER_RE", "SUMMARY_KEYWORDS",
    "_mdl002_accel_init",
    "list_pdfs_in_temp", "classify_page",
    "extract_zones_first_page", "detect_table_regions", "split_quadrants",
    "validate_financial_table", "extract_table_from_region",
    "extract_text_blocks", "number_all_regions",
    "TableRecord", "TextBlock", "MDL002DBWriter",
    # v1.1.0 NEW
    "MDL002DocCache", "MDL002BatchBuffer", "MDL002DuckWriter",
    "MDL002SelfVerifier", "build_self_verify_html_mdl002",
    "process_one", "assemble_output",
    "VRN_MDL002_LayoutExtractor",
]

# ============================================================================
# __main__
# ============================================================================

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="VRN MDL002 LayoutExtractor")
    for k, v in _DEFAULTS.items():
        tp = bool if isinstance(v, bool) else (int if isinstance(v, int) else str)
        if tp == bool: p.add_argument("--" + k.replace("_", "-"), action="store_true", default=v)
        else:          p.add_argument("--" + k.replace("_", "-"), type=tp, default=v)
    args   = p.parse_args()
    cfg    = {k.replace("-", "_"): v for k, v in vars(args).items()}
    result = VRN_MDL002_LayoutExtractor(cfg).run()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["ok"] else 1)
