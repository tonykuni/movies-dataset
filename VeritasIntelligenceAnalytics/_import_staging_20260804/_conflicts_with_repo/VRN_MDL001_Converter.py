# -*- coding: utf-8 -*-
from __future__ import annotations
"""
VRN_MDL001_Converter.py
=======================
VERITAS REPORT NOVA -- MDL001  Universal Document → High-Quality PDF Converter
Version   : 1.0.0   |   Module ID : VRN-MDL001-SUP-001
Asset ID  : VRN-MDL001-CLS-001
Policy    : 功能只增不減 · append-only · SSOT · 獨立模組

PIPELINE POSITION
  input/           ← PDF / Word / Image / HTML 原始輸入
    ↓
  VRN_MDL001_Converter   (此模組)
    ↓
  pdf_temp/        ← 統一高畫質 PDF (DPI 300/400 可選)  ← 所有後續模組的統一輸入

ANCHOR MAP
  [VRN:ANCHOR:MDL001-META-001]    §0  Module Metadata
  [VRN:ANCHOR:MDL001-SSOT-001]    §1  SSOT + TW Regex (locked)
  [VRN:ANCHOR:MDL001-ACCEL-001]   §2  Accelerator Init (6-ENV)
  [VRN:ANCHOR:MDL001-DAT-001]     §3  Config / _DEFAULTS
  [VRN:ANCHOR:MDL001-DETECT-001]  §4  Input Type Detector
  [VRN:ANCHOR:MDL001-PDF-001]     §5  PDF → High-Quality PDF (DPI warp + re-render)
  [VRN:ANCHOR:MDL001-WORD-001]    §6  Word (.docx/.doc) → PDF via LibreOffice / win32com
  [VRN:ANCHOR:MDL001-IMG-001]     §7  Image (PNG/JPG/TIFF/BMP/WEBP) → PDF
  [VRN:ANCHOR:MDL001-HTML-001]    §8  HTML → PDF via weasyprint / pdfkit fallback
  [VRN:ANCHOR:MDL001-MERGE-001]   §9  Multi-page merge + dedup SHA256
  [VRN:ANCHOR:MDL001-RENAME-001]  §10 Output Rename: ticker_date_broker_HASH8.pdf
  [VRN:ANCHOR:MDL001-DB-001]      §11 DB Writer (WAL + Parquet + CSV)
  [VRN:ANCHOR:MDL001-OUT-001]     §12 Output Assembler
  [VRN:ANCHOR:MDL001-SYS-001]     §13 Pipeline Entry VRN_MDL001_Converter

SMART ASSET REGISTRY
  VRN-MDL001-CLS-001  VRN_MDL001_Converter
  VRN-MDL001-CLS-002  MDL001DBWriter
  VRN-MDL001-FNC-001  detect_input_type
  VRN-MDL001-FNC-002  convert_pdf_to_hq_pdf
  VRN-MDL001-FNC-003  convert_word_to_pdf
  VRN-MDL001-FNC-004  convert_image_to_pdf
  VRN-MDL001-FNC-005  convert_html_to_pdf
  VRN-MDL001-FNC-006  merge_pages_to_pdf
  VRN-MDL001-FNC-007  rename_output_pdf
  VRN-MDL001-FNC-008  file_sha256
  VRN-MDL001-FNC-009  parse_filename_meta
  VRN-MDL001-FNC-010  process_one
  VRN-MDL001-FNC-011  assemble_output
  VRN-MDL001-FNC-012  _mdl001_accel_init
  VRN-MDL001-FNC-013  list_input_files
  VRN-MDL001-FNC-014  validate_pdf_output

OUTPUTS (pdf_temp)
  {ticker}_{date}_{broker}_{HASH8}.pdf    ← 高畫質 PDF 統一命名
  VRN_MDL001_ConvertLog.json              ← 轉換結果 (每檔狀態/SHA256/來源)
  VRN_MDL001_ConvertLog.parquet           ← Parquet flat
  VRN_MDL001_ConvertLog.csv               ← CSV (UTF-8 BOM)
  VRN_MDL001.db                           ← SQLite WAL

LL RULES APPLIED: #10 #12 #13 #15 #17 #18 #19 #20
"""

# ============================================================================
# [VRN:ANCHOR:MDL001-META-001] §0  MODULE METADATA
# ============================================================================

__version__   = "1.1.0"
__module_id__ = "VRN-MDL001-SUP-001"
__asset_id__  = "VRN-MDL001-CLS-001"
__author__    = "VRN Team"
__domain__    = "CONVERT"

# ============================================================================
# STDLIB
# ============================================================================

import os, sys, re, json, time, math, hashlib, logging, sqlite3, csv, io
import gc, argparse, threading, warnings, shutil, subprocess, copy
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings("ignore")

# ── safe import ──────────────────────────────────────────────────────────────
def _si(n):
    try: import importlib; return importlib.import_module(n)
    except: return None

fitz       = _si("fitz")        # PyMuPDF
pdfplumb   = _si("pdfplumber")
PIL        = _si("PIL")
Image      = None
if PIL:
    try: from PIL import Image as _Img; Image = _Img
    except: pass
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
_SSOT: object = None; _SSOT_OK: bool = False  # VIA_SSOT_Unified
_REG: object = None;  _REG_OK: bool = False   # VIA_RegistryCore_v1
_BRG: object = None;  _BRG_OK: bool = False   # VIA_Runtime_Bridge_All_in_One
_ENV: object = None;  _ENV_OK: bool = False   # VIA_EnvManager
_AST: object = None;  _AST_OK: bool = False   # VIA_Panorama_AST_RuntimeInjector
_NET: object = None;  _NET_OK: bool = False   # VeritasAegisNexus

def _load_celeritas(ssot_dir: str) -> bool:
    """VRN-MDL001: Load 7 supportive tools per VIA_Supportive_HardGate_Seal.json.
    Backward-compat: returns True if Celeritas loaded (preserves old caller contract).
    Policy: BOOT_PRECHECK_ONLY_NO_NETWORK_NO_PARALLEL_NO_AUTOPATCH. Py3.12 inject.
    """
    global _CEL, _CEL_OK
    global _SSOT, _SSOT_OK, _REG, _REG_OK, _BRG, _BRG_OK
    global _ENV, _ENV_OK, _AST, _AST_OK, _NET, _NET_OK
    import importlib.util as _ilu
    # [VRN:ANCHOR:HARDGATE_PLUGIN_MAP:V1] order matches HardGate Seal
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
                    sys.modules[mod_name] = mod    # inject before exec (Py3.12)
                    spec.loader.exec_module(mod)
                    globals()[gname]   = mod
                    globals()[ok_name] = True
                    if mod_name == "VeritasCeleritas":
                        if hasattr(mod, "bootstrap_at_import"): mod.bootstrap_at_import(__file__)
                        if hasattr(mod, "warm_thread_pool"):    mod.warm_thread_pool()
                    log.info("[MDL001] %s loaded from %s", mod_name, p)
                    break
                except Exception as e:
                    log.debug("[MDL001] %s: %s", mod_name, e)
    return _CEL_OK

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
weasyprint = _si("weasyprint")  # HTML→PDF
img2pdf    = _si("img2pdf")     # Image→PDF (lossless)

# ============================================================================
# [VRN:ANCHOR:MDL001-SSOT-001] §1  SSOT — TW Regex (LOCKED — NEVER MODIFY)
# ============================================================================

# THREE LOCKED TAIWAN TICKER REGEX — IMMUTABLE
TW_TICKER_REGEX    = re.compile(r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})")
TW_BLOOMBERG_REGEX = re.compile(r"\b(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})\s+TT\b")
TW_YFINANCE_REGEX  = re.compile(r"\b(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})\.(TW|TWO)\b")

# Broker filename map
_BROKER_FN_MAP: Dict[str, str] = {
    "GS": "Goldman Sachs",   "MS": "Morgan Stanley",  "JPM": "JPMorgan",
    "CITI": "Citigroup",     "UBS": "UBS",             "DB": "Deutsche Bank",
    "CS": "Credit Suisse",   "BAML": "BofA Merrill",  "NOMURA": "Nomura",
    "DAIWA": "Daiwa",        "CLSA": "CLSA",           "MACQ": "Macquarie",
    "兆豐": "兆豐金控",       "國泰": "國泰證券",        "中信": "中信證券",
    "元大": "元大證券",        "富邦": "富邦證券",        "凱基": "凱基證券",
    "永豐金": "永豐金證券",    "華南永昌": "華南永昌",    "玉山": "玉山證券",
}

# ============================================================================
# [VRN:ANCHOR:MDL001-ACCEL-001] §2  ACCELERATOR INIT
# ============================================================================

def _mdl001_accel_init(workers: int = 0) -> Dict:
    """VRN-MDL001-FNC-012  6-ENV thread init + GC tuning."""
    w = workers or max(1, (os.cpu_count() or 4) - 1)
    for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                "NUMEXPR_NUM_THREADS", "BLIS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ.setdefault(var, str(w))
    gc.set_threshold(50_000, 500, 50)
    return {
        "workers":    w,
        "fitz":       fitz is not None,
        "pdfplumber": pdfplumb is not None,
        "PIL":        Image is not None,
        "img2pdf":    img2pdf is not None,
        "weasyprint": weasyprint is not None,
        "pyarrow":    pyarrow is not None,
    }

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s][%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger(__name__)

# ============================================================================
# [VRN:ANCHOR:MDL001-DAT-001] §3  CONFIG / _DEFAULTS
# ============================================================================

_DEFAULTS = dict(
    input_dir   = r"C:\VeritasIntelligenceAnalytics\VeritasReportNova\input",
    pdf_temp    = r"C:\VeritasIntelligenceAnalytics\VeritasReportNova\temp\pdf_temp",
    mdl001_temp = r"C:\VeritasIntelligenceAnalytics\VeritasReportNova\temp\mdl001_temp",
    ssot_dir    = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module",
    dpi         = 300,           # 300 or 400
    jpeg_quality= 90,            # JPEG quality for image-based PDFs
    max_pages   = 50,            # max pages per doc
    workers     = 0,             # 0 = auto (cpu-1)
    enable_db   = True,
    zero_error  = True,
    dedup       = True,          # skip SHA256 duplicates in pdf_temp
    overwrite   = False,         # overwrite existing output PDF
    rename_mode = "auto",        # auto = ticker_date_broker_HASH8 | preserve = keep original name
    # ── v1.1.0 NEW (append-only) ─────────────────────────────────────────────
    use_duckdb     = True,    # P3 DuckDB primary, sqlite fallback
    batch_size     = 5000,    # P3 buffer flush threshold
    polars_first   = True,    # P5 polars vectorized exports
    self_verify    = True,    # P6 4-phase HTML
    fitz_reuse     = True,    # P1.5 在 convert_pdf_to_hq_pdf 中重用 doc handle
)

# Supported input extensions
_PDF_EXT  = {".pdf"}
_WORD_EXT = {".docx", ".doc", ".rtf"}
_IMG_EXT  = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp", ".heic", ".avif"}
_HTML_EXT = {".html", ".htm"}
_ALL_EXT  = _PDF_EXT | _WORD_EXT | _IMG_EXT | _HTML_EXT

# ── Filename patterns ─────────────────────────────────────────────────────────
_FN_DATE_RE   = re.compile(r"(20\d{2})[_\-]?(\d{2})[_\-]?(\d{2})")
_FN_BROKER_RE = re.compile(
    r"(%s)" % "|".join(re.escape(k) for k in sorted(_BROKER_FN_MAP, key=len, reverse=True)),
    re.IGNORECASE,
)

# ============================================================================
# UTILITIES
# ============================================================================

def _hash8(s: str) -> str:
    if xxhash:
        return xxhash.xxh64(s.encode()).hexdigest()[:8].upper()
    return hashlib.sha256(s.encode()).hexdigest()[:8].upper()

def file_sha256(path: str) -> Optional[str]:
    """VRN-MDL001-FNC-008"""
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""): h.update(chunk)
        return h.hexdigest()
    except Exception: return None

def _jwrite(p: str, data: Any):
    def _def(o): return None if isinstance(o, float) and (math.isnan(o) or math.isinf(o)) else str(o)
    Path(p).write_text(json.dumps(data, ensure_ascii=False, indent=2, default=_def), encoding="utf-8")

def _jload(p: str) -> Any:
    try:
        txt = Path(p).read_text(encoding="utf-8")
        if orjson: return orjson.loads(txt)
        return json.loads(txt)
    except Exception as e: log.warning("[MDL001] jload failed %s: %s", p, e); return None

# ============================================================================
# [VRN:ANCHOR:MDL001-DETECT-001] §4  INPUT TYPE DETECTOR
# ============================================================================

def detect_input_type(path: str) -> str:
    """VRN-MDL001-FNC-001  Returns: 'pdf'|'word'|'image'|'html'|'unknown'"""
    ext = Path(path).suffix.lower()
    if ext in _PDF_EXT:  return "pdf"
    if ext in _WORD_EXT: return "word"
    if ext in _IMG_EXT:  return "image"
    if ext in _HTML_EXT: return "html"
    return "unknown"

def list_input_files(input_dir: str) -> List[str]:
    """VRN-MDL001-FNC-013  List all supported input files, sorted."""
    if not os.path.isdir(input_dir): return []
    files = []
    for f in sorted(os.listdir(input_dir)):
        if Path(f).suffix.lower() in _ALL_EXT:
            files.append(os.path.join(input_dir, f))
    return files

def parse_filename_meta(filename: str) -> Dict:
    """VRN-MDL001-FNC-009  Extract ticker / date / broker from filename."""
    stem   = Path(filename).stem
    result = {"ticker": "", "report_date": "", "broker_abbr": "", "broker": ""}
    # Date
    dm = _FN_DATE_RE.search(stem)
    if dm:
        result["report_date"] = "{}-{}-{}".format(dm.group(1), dm.group(2), dm.group(3))
    # Broker
    bm = _FN_BROKER_RE.search(stem)
    if bm:
        abbr = bm.group(1).upper()
        result["broker_abbr"] = abbr
        result["broker"]      = _BROKER_FN_MAP.get(abbr, abbr)
    # Ticker — 4-digit, not year
    for tok in re.split(r"[_\-\s]", stem):
        m = re.fullmatch(r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})", tok.strip())
        if m: result["ticker"] = m.group(1); break
    return result

# ============================================================================
# [VRN:ANCHOR:MDL001-PDF-001] §5  PDF → HIGH-QUALITY PDF
# ============================================================================

def convert_pdf_to_hq_pdf(
    src_path: str,
    dst_path: str,
    dpi: int = 300,
    jpeg_quality: int = 90,
    max_pages: int = 50,
) -> Dict:
    """VRN-MDL001-FNC-002
    Strategy:
      A. If PDF is vector/text-native: re-render at target DPI via PyMuPDF (lossless)
      B. If PDF is scanned/image-based: render each page at DPI, recompose
      C. Fallback: copy as-is with metadata update
    Returns: {ok, method, n_pages, file_size_kb, error}
    """
    result = {"ok": False, "method": "none", "n_pages": 0,
              "file_size_kb": 0, "error": None}
    if fitz is None:
        # Fallback: simple copy
        try:
            shutil.copy2(src_path, dst_path)
            result.update({"ok": True, "method": "copy_fallback",
                           "file_size_kb": round(os.path.getsize(dst_path) / 1024, 1)})
        except Exception as e:
            result["error"] = f"copy_fallback: {e}"
        return result

    try:
        src_doc  = fitz.open(src_path)
        n_pages  = min(len(src_doc), max_pages)
        dst_doc  = fitz.open()  # new empty PDF

        # Detect if vector or image-based
        is_image_based = _detect_image_based_pdf(src_doc)
        method = "render_image" if is_image_based else "rewrite_vector"

        for pg_idx in range(n_pages):
            src_page = src_doc[pg_idx]
            if is_image_based:
                # Render page as image then embed
                mat  = fitz.Matrix(dpi / 72.0, dpi / 72.0)
                pix  = src_page.get_pixmap(matrix=mat, alpha=False)
                # Insert as new page preserving dimensions
                dst_page = dst_doc.new_page(
                    width  = src_page.rect.width,
                    height = src_page.rect.height,
                )
                # Re-embed rendered image
                img_bytes = pix.tobytes("jpeg", jpg_quality=jpeg_quality)
                img_rect  = dst_page.rect
                dst_page.insert_image(img_rect, stream=img_bytes)
            else:
                # Vector: direct page copy preserving all text/fonts
                dst_doc.insert_pdf(src_doc, from_page=pg_idx, to_page=pg_idx)

        # Save with PDF/A compatible settings
        dst_doc.save(
            dst_path,
            garbage=4,
            deflate=True,
            clean=True,
        )
        dst_doc.close()
        src_doc.close()

        sz_kb = round(os.path.getsize(dst_path) / 1024, 1)
        result.update({"ok": True, "method": method,
                       "n_pages": n_pages, "file_size_kb": sz_kb})

    except Exception as e:
        result["error"] = str(e)
        log.debug("[MDL001] PDF->HQ failed %s: %s", src_path, e)
        # Fallback copy
        try:
            shutil.copy2(src_path, dst_path)
            result.update({"ok": True, "method": "copy_fallback",
                           "file_size_kb": round(os.path.getsize(dst_path) / 1024, 1)})
        except Exception as e2:
            result["error"] = str(e2)

    return result

def _detect_image_based_pdf(doc, sample_pages: int = 3) -> bool:
    """Check if PDF is primarily image-based (scanned) vs vector/text."""
    if fitz is None: return False
    n = min(len(doc), sample_pages)
    text_chars = 0
    for i in range(n):
        text = doc[i].get_text()
        text_chars += len(text.strip())
    # If average text chars per page < 50 → image-based
    return (text_chars / max(n, 1)) < 50

# ============================================================================
# [VRN:ANCHOR:MDL001-WORD-001] §6  WORD → PDF
# ============================================================================

def convert_word_to_pdf(src_path: str, dst_path: str) -> Dict:
    """VRN-MDL001-FNC-003
    Strategy A: win32com (Windows, preserves formatting best)
    Strategy B: LibreOffice soffice CLI (cross-platform)
    Strategy C: python-docx → text extraction → minimal PDF
    """
    result = {"ok": False, "method": "none", "n_pages": 0,
              "file_size_kb": 0, "error": None}

    # Strategy A: win32com (Windows only)
    if sys.platform == "win32":
        try:
            import win32com.client  # type: ignore
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            doc = word.Documents.Open(os.path.abspath(src_path))
            doc.SaveAs(os.path.abspath(dst_path), FileFormat=17)  # 17=PDF
            n_pages = doc.ComputeStatistics(2)  # 2=wdStatisticPages
            doc.Close()
            word.Quit()
            sz_kb = round(os.path.getsize(dst_path) / 1024, 1)
            result.update({"ok": True, "method": "win32com",
                           "n_pages": n_pages, "file_size_kb": sz_kb})
            return result
        except Exception as e:
            log.debug("[MDL001] win32com failed: %s", e)

    # Strategy B: LibreOffice
    lo_paths = ["soffice", "libreoffice",
                r"C:\Program Files\LibreOffice\program\soffice.exe",
                r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"]
    for lo in lo_paths:
        if shutil.which(lo) or os.path.isfile(lo):
            try:
                out_dir = str(Path(dst_path).parent)
                cmd = [lo, "--headless", "--convert-to", "pdf",
                       "--outdir", out_dir, os.path.abspath(src_path)]
                proc = subprocess.run(cmd, capture_output=True, timeout=120)
                # LibreOffice outputs to same dir as src with same stem
                lo_out = Path(out_dir) / (Path(src_path).stem + ".pdf")
                if lo_out.exists():
                    shutil.move(str(lo_out), dst_path)
                    sz_kb = round(os.path.getsize(dst_path) / 1024, 1)
                    result.update({"ok": True, "method": "libreoffice",
                                   "file_size_kb": sz_kb})
                    return result
            except Exception as e:
                log.debug("[MDL001] LibreOffice failed: %s", e)

    # Strategy C: python-docx minimal extraction → text PDF via fitz
    try:
        docx = _si("docx")
        if docx and fitz:
            document = docx.Document(src_path)
            text_lines = [p.text for p in document.paragraphs if p.text.strip()]
            if text_lines:
                _text_to_pdf(text_lines, dst_path)
                sz_kb = round(os.path.getsize(dst_path) / 1024, 1)
                result.update({"ok": True, "method": "docx_text_fallback",
                               "file_size_kb": sz_kb})
                return result
    except Exception as e:
        log.debug("[MDL001] docx fallback failed: %s", e)

    result["error"] = "All Word→PDF strategies failed"
    return result

def _text_to_pdf(lines: List[str], dst_path: str):
    """Minimal text → PDF via PyMuPDF."""
    if fitz is None: return
    doc  = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4
    y    = 50
    for line in lines:
        if y > 800:
            page = doc.new_page(width=595, height=842)
            y    = 50
        page.insert_text((50, y), line[:120], fontsize=10)
        y += 14
    doc.save(dst_path, garbage=4, deflate=True)
    doc.close()

# ============================================================================
# [VRN:ANCHOR:MDL001-IMG-001] §7  IMAGE → PDF
# ============================================================================

def convert_image_to_pdf(
    src_path: str,
    dst_path: str,
    dpi: int = 300,
    jpeg_quality: int = 90,
) -> Dict:
    """VRN-MDL001-FNC-004
    Strategy A: img2pdf (lossless, best for archival)
    Strategy B: PIL→PyMuPDF composite
    Strategy C: PyMuPDF direct image insert
    """
    result = {"ok": False, "method": "none", "n_pages": 1,
              "file_size_kb": 0, "error": None}

    # Strategy A: img2pdf (lossless, best quality)
    if img2pdf:
        try:
            with open(dst_path, "wb") as fout:
                fout.write(img2pdf.convert(src_path))
            sz_kb = round(os.path.getsize(dst_path) / 1024, 1)
            result.update({"ok": True, "method": "img2pdf", "file_size_kb": sz_kb})
            return result
        except Exception as e:
            log.debug("[MDL001] img2pdf failed: %s", e)

    # Strategy B: PIL → PyMuPDF
    if Image and fitz:
        try:
            img    = Image.open(src_path).convert("RGB")
            # Target size at DPI
            w_pt   = img.width  * 72.0 / dpi
            h_pt   = img.height * 72.0 / dpi
            buf    = io.BytesIO()
            img.save(buf, format="JPEG", quality=jpeg_quality)
            img_bytes = buf.getvalue()

            doc  = fitz.open()
            page = doc.new_page(width=w_pt, height=h_pt)
            page.insert_image(page.rect, stream=img_bytes)
            doc.save(dst_path, garbage=4, deflate=True)
            doc.close()

            sz_kb = round(os.path.getsize(dst_path) / 1024, 1)
            result.update({"ok": True, "method": "pil_fitz", "file_size_kb": sz_kb})
            return result
        except Exception as e:
            log.debug("[MDL001] pil+fitz failed: %s", e)

    # Strategy C: PyMuPDF direct
    if fitz:
        try:
            src_doc  = fitz.open(src_path)  # fitz can open images
            dst_doc  = fitz.open()
            dst_doc.insert_pdf(src_doc)
            dst_doc.save(dst_path, garbage=4, deflate=True)
            dst_doc.close(); src_doc.close()
            sz_kb = round(os.path.getsize(dst_path) / 1024, 1)
            result.update({"ok": True, "method": "fitz_direct", "file_size_kb": sz_kb})
            return result
        except Exception as e:
            result["error"] = str(e)

    result["error"] = "All Image→PDF strategies failed"
    return result

# ============================================================================
# [VRN:ANCHOR:MDL001-HTML-001] §8  HTML → PDF
# ============================================================================

def convert_html_to_pdf(src_path: str, dst_path: str) -> Dict:
    """VRN-MDL001-FNC-005
    Strategy A: weasyprint
    Strategy B: pdfkit (wkhtmltopdf)
    Strategy C: playwright chromium (headless)
    """
    result = {"ok": False, "method": "none", "n_pages": 0,
              "file_size_kb": 0, "error": None}

    # Strategy A: weasyprint
    if weasyprint:
        try:
            from weasyprint import HTML as WH
            WH(filename=src_path).write_pdf(dst_path)
            sz_kb = round(os.path.getsize(dst_path) / 1024, 1)
            result.update({"ok": True, "method": "weasyprint", "file_size_kb": sz_kb})
            return result
        except Exception as e:
            log.debug("[MDL001] weasyprint failed: %s", e)

    # Strategy B: pdfkit
    pdfkit = _si("pdfkit")
    if pdfkit:
        try:
            pdfkit.from_file(src_path, dst_path)
            sz_kb = round(os.path.getsize(dst_path) / 1024, 1)
            result.update({"ok": True, "method": "pdfkit", "file_size_kb": sz_kb})
            return result
        except Exception as e:
            log.debug("[MDL001] pdfkit failed: %s", e)

    # Strategy C: playwright
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page    = browser.new_page()
            page.goto("file:///" + os.path.abspath(src_path).replace("\\", "/"))
            page.pdf(path=dst_path, format="A4")
            browser.close()
        sz_kb = round(os.path.getsize(dst_path) / 1024, 1)
        result.update({"ok": True, "method": "playwright", "file_size_kb": sz_kb})
        return result
    except Exception as e:
        result["error"] = str(e)

    result["error"] = "All HTML→PDF strategies failed"
    return result

# ============================================================================
# [VRN:ANCHOR:MDL001-RENAME-001] §10  OUTPUT RENAME
# ============================================================================

def rename_output_pdf(
    src_path: str,
    meta: Dict,
    hash8: str,
    rename_mode: str = "auto",
) -> str:
    """VRN-MDL001-FNC-007
    auto mode: {ticker}_{date}_{broker}_{HASH8}.pdf
    preserve mode: keep original stem, append HASH8
    Returns: final filename (stem only, no directory)
    """
    if rename_mode == "preserve":
        return Path(src_path).stem + f"_{hash8}.pdf"

    ticker  = meta.get("ticker", "0000") or "0000"
    date    = (meta.get("report_date", "") or "").replace("-", "")[:8] or "00000000"
    broker  = meta.get("broker_abbr", "UNK") or "UNK"
    return f"{ticker}_{date}_{broker}_{hash8}.pdf"

# ============================================================================
# [VRN:ANCHOR:MDL001-MERGE-001] §9  VALIDATION + POST-PROCESS
# ============================================================================

def validate_pdf_output(dst_path: str) -> Dict:
    """VRN-MDL001-FNC-014  Validate output PDF is readable."""
    result = {"valid": False, "n_pages": 0, "has_text": False, "error": None}
    if not os.path.isfile(dst_path):
        result["error"] = "File not found"
        return result
    if fitz:
        try:
            doc = fitz.open(dst_path)
            result["n_pages"] = len(doc)
            text_sample = ""
            for i in range(min(3, len(doc))):
                text_sample += doc[i].get_text()
            doc.close()
            result["has_text"] = len(text_sample.strip()) > 20
            result["valid"]    = result["n_pages"] > 0
        except Exception as e:
            result["error"] = str(e)
    else:
        # Minimal: check file size > 1KB
        result["valid"] = os.path.getsize(dst_path) > 1024
    return result

# ============================================================================
# [VRN:ANCHOR:MDL001-DB-001] §11  DB WRITER
# ============================================================================

class MDL001DBWriter:
    """VRN-MDL001-CLS-002  SQLite WAL writer for conversion log."""

    DDL = """
CREATE TABLE IF NOT EXISTS vrn_mdl001_convert_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    src_filename    TEXT,
    dst_filename    TEXT,
    input_type      TEXT,
    method          TEXT,
    ticker          TEXT,
    report_date     TEXT,
    broker_abbr     TEXT,
    src_sha256      TEXT,
    dst_sha256      TEXT,
    n_pages         INTEGER,
    file_size_kb    REAL,
    ok              INTEGER,
    error           TEXT,
    dpi             INTEGER,
    ts              TEXT DEFAULT (datetime('now','localtime'))
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

    def insert(self, rec: Dict):
        sql = """INSERT INTO vrn_mdl001_convert_log
                 (src_filename, dst_filename, input_type, method, ticker, report_date,
                  broker_abbr, src_sha256, dst_sha256, n_pages, file_size_kb, ok, error, dpi)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
        with self._lock:
            self._con.execute(sql, (
                rec.get("src_filename",""), rec.get("dst_filename",""),
                rec.get("input_type",""),   rec.get("method",""),
                rec.get("ticker",""),        rec.get("report_date",""),
                rec.get("broker_abbr",""),   rec.get("src_sha256",""),
                rec.get("dst_sha256",""),    rec.get("n_pages",0),
                rec.get("file_size_kb",0),   1 if rec.get("ok") else 0,
                rec.get("error",""),         rec.get("dpi",300),
            ))
            self._con.commit()

    def export_parquet(self, out_dir: str):
        if not pd or not pyarrow: return
        try:
            df = pd.read_sql("SELECT * FROM vrn_mdl001_convert_log", self._con)
            df.to_parquet(str(Path(out_dir) / "VRN_MDL001_ConvertLog.parquet"), index=False)
        except Exception as e: log.warning("[MDL001] parquet export: %s", e)

    def export_csv(self, out_dir: str):
        try:
            df = pd.read_sql("SELECT * FROM vrn_mdl001_convert_log", self._con) if pd else None
            if df is not None:
                df.to_csv(str(Path(out_dir) / "VRN_MDL001_ConvertLog.csv"),
                          index=False, encoding="utf-8-sig")
        except Exception as e: log.warning("[MDL001] csv export: %s", e)

# ============================================================================
# [VRN:ANCHOR:MDL001-BATCH-001] §11.5  P3 BATCH BUFFER + DUCK WRITER (v1.1.0)
# ── 同 MDL002/004/005 v1.1.0 模式：worker push 主執行緒一次 flush          ─
# ============================================================================

class MDL001BatchBuffer:
    """VRN-MDL001-CLS-003  P3 batch buffer (NEW v1.1.0)."""
    def __init__(self, batch_size: int = 5000):
        self.batch_size = batch_size
        self._conv_buf: List[Tuple] = []
        self._lock = threading.Lock()

    def push_conversion(self, rec: Dict):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        # rec is the v1.0.0 schema dict from process_one
        err_val = rec.get("error","") or ""
        row = (
            None,
            rec.get("src_filename",""),
            rec.get("input_type",""),               # src_type column
            rec.get("dst_filename",""),
            rec.get("ticker",""), rec.get("report_date",""),
            rec.get("broker_abbr",""),
            rec.get("src_sha256",""),               # sha256_src
            rec.get("dst_sha256",""),               # sha256_dst
            rec.get("n_pages",0),                   # n_pages_src
            rec.get("n_pages",0),                   # n_pages_dst (same)
            int(rec.get("dpi",0)),
            float(rec.get("file_size_kb",0.0) or 0.0),
            "OK" if rec.get("ok") else "FAIL",      # status
            err_val[:500],
            float(rec.get("elapsed",0.0) or 0.0),
            ts,
        )
        with self._lock:
            self._conv_buf.append(row)

    def stats(self) -> Dict[str, int]:
        return {"conv": len(self._conv_buf)}

    def consume_all(self) -> List:
        with self._lock:
            c = self._conv_buf
            self._conv_buf = []
        return c


_DDL_DUCK_M001_CONV = """
CREATE TABLE IF NOT EXISTS vrn_mdl001_conversions (
    id INTEGER, src_filename VARCHAR, src_type VARCHAR, dst_filename VARCHAR,
    ticker VARCHAR, report_date VARCHAR, broker_abbr VARCHAR,
    sha256_src VARCHAR, sha256_dst VARCHAR,
    n_pages_src INTEGER, n_pages_dst INTEGER,
    dpi INTEGER, file_size_kb DOUBLE,
    status VARCHAR, error VARCHAR, elapsed DOUBLE, ts VARCHAR
);
"""


class MDL001DuckWriter:
    """VRN-MDL001-CLS-004  DuckDB primary writer (NEW v1.1.0)."""
    def __init__(self, db_path: str):
        if not DUCKDB_OK:
            raise RuntimeError("duckdb not available")
        self.db_path = db_path
        self._con = duckdb_lib.connect(db_path)
        self._con.execute(_DDL_DUCK_M001_CONV)

    def flush(self, conv_rows: List) -> Dict[str, int]:
        n_c = 0
        try:
            self._con.execute("BEGIN TRANSACTION")
            if conv_rows:
                self._con.executemany(
                    "INSERT INTO vrn_mdl001_conversions VALUES "
                    "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", conv_rows)
                n_c = len(conv_rows)
            self._con.execute("COMMIT")
        except Exception as e:
            try: self._con.execute("ROLLBACK")
            except: pass
            log.error("[MDL001] DuckDB flush fail: %s", e); raise
        return {"conv": n_c}

    def export_parquet_polars(self, out_dir: str) -> Optional[str]:
        out_path = str(Path(out_dir) / "VRN_MDL001_ConvertLog.parquet")
        try:
            self._con.execute(
                f"COPY (SELECT * FROM vrn_mdl001_conversions) "
                f"TO '{out_path}' (FORMAT PARQUET, COMPRESSION ZSTD)")
            return out_path
        except Exception as e:
            log.warning("[MDL001] DuckDB→parquet fail: %s", e); return None

    def export_csv_polars(self, out_dir: str) -> Optional[str]:
        out_path = str(Path(out_dir) / "VRN_MDL001_ConvertLog.csv")
        if POLARS_OK:
            try:
                rows = self._con.execute("SELECT * FROM vrn_mdl001_conversions").fetchall()
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
                log.debug("[MDL001] polars-fetchall csv fail (%s), fallback DuckDB", e)
        try:
            self._con.execute(
                f"COPY (SELECT * FROM vrn_mdl001_conversions) "
                f"TO '{out_path}' (HEADER, DELIMITER ',')")
            data = Path(out_path).read_bytes()
            Path(out_path).write_bytes(b"\xef\xbb\xbf" + data)
            return out_path
        except Exception as e:
            log.warning("[MDL001] csv export fail: %s", e); return None

    def close(self):
        try: self._con.close()
        except: pass


# ── Append v1.1.0 batch flush + polars exports to legacy DBWriter ─────────
def _mdl001_dbwriter_flush(self, conv_rows: List) -> Dict[str, int]:
    n_c = 0
    with self._lock:
        try:
            self._con.execute("BEGIN")
            if conv_rows:
                self._con.executemany(
                    "INSERT INTO vrn_mdl001_conversions "
                    "(src_filename,src_type,dst_filename,ticker,report_date,"
                    " broker_abbr,sha256_src,sha256_dst,n_pages_src,n_pages_dst,"
                    " dpi,file_size_kb,status,error,elapsed) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    [r[1:-1] for r in conv_rows])
                n_c = len(conv_rows)
            self._con.commit()
        except Exception as e:
            try: self._con.rollback()
            except: pass
            log.error("[MDL001] sqlite flush fail: %s", e); raise
    return {"conv": n_c}

MDL001DBWriter.flush = _mdl001_dbwriter_flush


def _mdl001_dbwriter_export_parquet_polars(self, out_dir: str) -> Optional[str]:
    out_path = str(Path(out_dir) / "VRN_MDL001_ConvertLog.parquet")
    if not POLARS_OK:
        self.export_parquet(out_dir)
        return out_path if Path(out_path).exists() else None
    try:
        with self._lock:
            cur = self._con.execute("SELECT * FROM vrn_mdl001_conversions")
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description] if cur.description else []
        if not rows:
            df = pl.DataFrame(schema={c: pl.Utf8 for c in cols} if cols else None)
        else:
            df = pl.DataFrame(rows, schema=cols, orient="row")
        df.write_parquet(out_path, compression="zstd")
        return out_path
    except Exception as e:
        log.warning("[MDL001] polars→parquet fail (%s), pandas fallback", e)
        self.export_parquet(out_dir)
        return out_path if Path(out_path).exists() else None

def _mdl001_dbwriter_export_csv_polars(self, out_dir: str) -> Optional[str]:
    out_path = str(Path(out_dir) / "VRN_MDL001_ConvertLog.csv")
    if not POLARS_OK:
        self.export_csv(out_dir)
        return out_path if Path(out_path).exists() else None
    try:
        with self._lock:
            cur = self._con.execute("SELECT * FROM vrn_mdl001_conversions")
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
        log.debug("[MDL001] polars-fetchall csv fail (%s), pandas fallback", e)
        self.export_csv(out_dir)
        return out_path if Path(out_path).exists() else None

MDL001DBWriter.export_parquet_polars = _mdl001_dbwriter_export_parquet_polars
MDL001DBWriter.export_csv_polars     = _mdl001_dbwriter_export_csv_polars


# ============================================================================
# [VRN:ANCHOR:MDL001-SELFCHK-001] §11.7  P6 4-PHASE SELF-VERIFICATION (v1.1.0)
# ============================================================================

class MDL001SelfVerifier:
    """VRN-MDL001-CLS-005  P6 4-phase debug chain (NEW v1.1.0)."""
    def __init__(self, cfg: Dict, run_summary: Dict, mdl001_temp: str):
        self.cfg = cfg; self.run_summary = run_summary
        self.mdl001_temp = mdl001_temp
        self.checks: List[Dict] = []

    def _add(self, phase, name, ok, detail=""):
        self.checks.append({"phase":phase,"name":name,"ok":bool(ok),"detail":detail})

    def run(self) -> Dict:
        # P1: imports
        self._add("1/4", "Module version 1.1.0", __version__ == "1.1.0", __version__)
        self._add("1/4", "TW_TICKER_REGEX locked",
                  TW_TICKER_REGEX.pattern == r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})",
                  "")
        self._add("1/4", "polars available", POLARS_OK, "")
        self._add("1/4", "duckdb available", DUCKDB_OK, "")
        self._add("1/4", "fitz available",   fitz is not None, "")

        # P2: new infra
        self._add("2/4", "MDL001BatchBuffer exists",
                  "MDL001BatchBuffer" in globals(), "")
        self._add("2/4", "MDL001DuckWriter exists",
                  "MDL001DuckWriter" in globals(), "")
        self._add("2/4", "DBWriter has flush method",
                  hasattr(MDL001DBWriter, "flush"), "")
        self._add("2/4", "DBWriter has export_parquet_polars",
                  hasattr(MDL001DBWriter, "export_parquet_polars"), "")
        self._add("2/4", "DBWriter has export_csv_polars",
                  hasattr(MDL001DBWriter, "export_csv_polars"), "")

        # P3: DB
        duck_p   = Path(self.mdl001_temp) / "VRN_MDL001.duckdb"
        sqlite_p = Path(self.mdl001_temp) / "VRN_MDL001.db"
        self._add("3/4", "DB file exists", duck_p.exists() or sqlite_p.exists(),
                  f"duck={duck_p.exists()} sqlite={sqlite_p.exists()}")
        if duck_p.exists() and DUCKDB_OK:
            try:
                con = duckdb_lib.connect(str(duck_p), read_only=True)
                tbls = {t[0] for t in con.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema='main'").fetchall()}
                con.close()
                self._add("3/4", "DuckDB schema vrn_mdl001_conversions",
                          "vrn_mdl001_conversions" in tbls, str(sorted(tbls)))
            except Exception as e:
                self._add("3/4", "DuckDB schema vrn_mdl001_conversions",
                          False, str(e))

        # P4: outputs
        for fn in ("VRN_MDL001_ConvertLog.json", "VRN_MDL001_VerifySummary.json",
                   "VRN_MDL001_ConvertLog.parquet", "VRN_MDL001_ConvertLog.csv"):
            p = Path(self.mdl001_temp) / fn
            self._add("4/4", f"file:{fn}", p.exists(),
                      f"size={p.stat().st_size if p.exists() else 0}")
        ti = self.run_summary.get("total", 0)
        self._add("4/4", "total_files non-negative", ti >= 0, str(ti))

        n_total = len(self.checks); n_pass = sum(1 for c in self.checks if c["ok"])
        n_fail  = n_total - n_pass
        cls = "READY" if n_fail == 0 else ("NEAR-READY" if n_fail <= 2 else "NOT-READY")
        return {"total":n_total,"pass":n_pass,"fail":n_fail,
                "classification":cls,"checks":self.checks,
                "generated":time.strftime("%Y-%m-%d %H:%M:%S")}


def build_self_verify_html_mdl001(verify_result: Dict, run_summary: Dict) -> str:
    """VRN-MDL001-FNC-015  VIA Visual Lock self-verify HTML (NEW v1.1.0)."""
    cls = verify_result.get("classification","?")
    cls_color = {"READY":"#439a9a","NEAR-READY":"#e0b020",
                 "NOT-READY":"#c83030"}.get(cls,"#666")
    cls_emoji = {"READY":"✓","NEAR-READY":"⚠","NOT-READY":"✗"}.get(cls,"?")

    by_phase: "Dict[str,List[Dict]]" = {}
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
        f"$ VRN_MDL001_Converter v{__version__} self-verification",
        f"  generated      : {verify_result.get('generated','-')}",
        f"  classification : {cls} {cls_emoji}",
        f"  checks         : {verify_result.get('pass',0)}/{verify_result.get('total',0)} pass",
        "",
        "$ pipeline summary",
        f"  total files    : {run_summary.get('total','-')}",
        f"  ok / fail      : {run_summary.get('ok_count','-')} / {run_summary.get('fail_count','-')}",
        f"  by type        : {dict(list(run_summary.get('by_src_type',{}).items())[:6])}",
    ]
    term_html = "\n".join(sum_lines)

    html = f"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="UTF-8">
<title>VRN MDL001 v{__version__} · Self-Verification · {cls}</title>
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
<div class="hdr"><h1>VRN MDL001 · Converter v{__version__}<span class="cls-badge">{cls}</span></h1>
<div class="sub">VeritasReportNova · 4-Phase Self-Verification · {time.strftime("%Y-%m-%d %H:%M:%S")}</div></div>
<div class="cd"><div class="cd-h">RUN SUMMARY</div><div class="cd-b"><div class="tm">{term_html}</div></div></div>
{"".join(phase_html)}
<div class="foot">Module: {__module_id__} · Asset: {__asset_id__} · v{__version__}</div>
</body></html>"""
    return html


# ============================================================================
# CORE PROCESSOR
# ============================================================================

def process_one(
    src_path: str,
    cfg:      Dict,
    db:       Optional[MDL001DBWriter],
    existing_sha256: set,
    buffer:   Optional["MDL001BatchBuffer"] = None,    # v1.1.0 NEW
) -> Dict:
    """VRN-MDL001-FNC-010  Convert one file → high-quality PDF in pdf_temp.
    v1.1.0: buffer pushes DB rows without lock contention."""
    t0       = time.perf_counter()
    pdf_temp = cfg.get("pdf_temp", _DEFAULTS["pdf_temp"])
    dpi      = cfg.get("dpi", _DEFAULTS["dpi"])
    q        = cfg.get("jpeg_quality", _DEFAULTS["jpeg_quality"])
    max_pg   = cfg.get("max_pages", _DEFAULTS["max_pages"])
    rename   = cfg.get("rename_mode", _DEFAULTS["rename_mode"])
    overwrite= cfg.get("overwrite", _DEFAULTS["overwrite"])

    rec = {
        "src_filename": Path(src_path).name,
        "dst_filename": "",
        "input_type":   "unknown",
        "method":       "none",
        "ticker":       "",
        "report_date":  "",
        "broker_abbr":  "",
        "src_sha256":   "",
        "dst_sha256":   "",
        "n_pages":      0,
        "file_size_kb": 0,
        "dpi":          dpi,
        "ok":           False,
        "error":        None,
        "elapsed":      0.0,
    }

    try:
        # Detect input type
        itype = detect_input_type(src_path)
        rec["input_type"] = itype
        if itype == "unknown":
            rec["error"] = "Unsupported file type"
            return rec

        # SHA256 dedup check
        src_sha = file_sha256(src_path) or ""
        rec["src_sha256"] = src_sha
        if cfg.get("dedup", True) and src_sha and src_sha in existing_sha256:
            rec["ok"]     = True  # treat as success (already converted)
            rec["method"] = "dedup_skip"
            log.info("[MDL001] DEDUP skip: %s", Path(src_path).name)
            return rec

        # Parse filename metadata
        meta = parse_filename_meta(src_path)
        rec.update(meta)

        # Build output filename
        hash8    = _hash8(src_sha or src_path)
        out_name = rename_output_pdf(src_path, meta, hash8, rename)
        dst_path = str(Path(pdf_temp) / out_name)
        rec["dst_filename"] = out_name

        # Skip if exists and not overwrite
        if os.path.isfile(dst_path) and not overwrite:
            val = validate_pdf_output(dst_path)
            if val["valid"]:
                rec.update({"ok": True, "method": "exists_skip",
                            "n_pages": val["n_pages"],
                            "file_size_kb": round(os.path.getsize(dst_path) / 1024, 1),
                            "dst_sha256": file_sha256(dst_path) or ""})
                if src_sha: existing_sha256.add(src_sha)
                return rec

        # Convert
        if itype == "pdf":
            conv = convert_pdf_to_hq_pdf(src_path, dst_path, dpi, q, max_pg)
        elif itype == "word":
            conv = convert_word_to_pdf(src_path, dst_path)
        elif itype == "image":
            conv = convert_image_to_pdf(src_path, dst_path, dpi, q)
        elif itype == "html":
            conv = convert_html_to_pdf(src_path, dst_path)
        else:
            conv = {"ok": False, "error": "Unknown type", "method": "none",
                    "n_pages": 0, "file_size_kb": 0}

        rec.update({
            "ok":           conv.get("ok", False),
            "method":       conv.get("method", "none"),
            "n_pages":      conv.get("n_pages", 0),
            "file_size_kb": conv.get("file_size_kb", 0),
            "error":        conv.get("error"),
        })

        # Post-validate
        if rec["ok"]:
            val = validate_pdf_output(dst_path)
            if not val["valid"]:
                rec["ok"]    = False
                rec["error"] = f"Validation failed: {val.get('error','invalid output')}"
            else:
                rec["n_pages"]   = val["n_pages"]
                rec["dst_sha256"] = file_sha256(dst_path) or ""
                if src_sha: existing_sha256.add(src_sha)

    except Exception as e:
        rec["error"] = str(e)
        log.error("[MDL001] process_one exception %s: %s", src_path, e)

    rec["elapsed"] = round(time.perf_counter() - t0, 2)

    status = "OK" if rec["ok"] else "FAIL"
    log.info("[MDL001] %s → %s [%s] %s pages %.2fs",
             rec["src_filename"], rec["dst_filename"],
             status, rec["n_pages"], rec["elapsed"])

    if buffer is not None:
        try: buffer.push_conversion(rec)
        except Exception as e: log.warning("[MDL001] buffer push: %s", e)
    elif db:
        try: db.insert(rec)
        except Exception as e: log.warning("[MDL001] DB insert: %s", e)

    return rec

# ============================================================================
# [VRN:ANCHOR:MDL001-OUT-001] §12  OUTPUT ASSEMBLER
# ============================================================================

def assemble_output(results: List[Dict]) -> Dict:
    """VRN-MDL001-FNC-011"""
    ok_count  = sum(1 for r in results if r.get("ok"))
    skip_dup  = sum(1 for r in results if r.get("method") in ("dedup_skip", "exists_skip"))
    converted = sum(1 for r in results if r.get("ok") and r.get("method") not in
                    ("dedup_skip", "exists_skip"))
    return {
        "module":        __module_id__,
        "version":       __version__,
        "generated":     time.strftime("%Y-%m-%d %H:%M:%S"),
        "total":         len(results),
        "ok_count":      ok_count,
        "fail_count":    len(results) - ok_count,
        "converted":     converted,
        "skipped_dedup": skip_dup,
        "total_pages":   sum(r.get("n_pages", 0) for r in results),
        "total_size_kb": round(sum(r.get("file_size_kb", 0) for r in results), 1),
        "by_type":       _count_by_key(results, "input_type"),
        "by_method":     _count_by_key(results, "method"),
        "files":         results,
    }

def _count_by_key(results: List[Dict], key: str) -> Dict[str, int]:
    d: Dict[str, int] = {}
    for r in results:
        k = r.get(key, "unknown") or "unknown"
        d[k] = d.get(k, 0) + 1
    return d

# ============================================================================
# [VRN:ANCHOR:MDL001-SYS-001] §13  PIPELINE ENTRY
# ============================================================================

class VRN_MDL001_Converter:
    """VRN-MDL001-CLS-001  MDL001 universal document converter.
    run():
      1. Accel init (6-ENV)
      2. List all supported files in input_dir
      3. Parallel process_one() — convert each to high-quality PDF
      4. DB export (Parquet + CSV)
      5. VRN_MDL001_ConvertLog.json → shared pdf_temp + mdl001_temp
    """

    def __init__(self, cfg: Dict):
        self.cfg     = cfg
        workers      = cfg.get("workers", 0) or max(1, (os.cpu_count() or 4) - 1)
        self.workers = workers
        self.db: Optional[MDL001DBWriter] = None

    def run(self) -> Dict:
        run_t0      = time.perf_counter()
        input_dir   = self.cfg.get("input_dir",   _DEFAULTS["input_dir"])
        pdf_temp    = self.cfg.get("pdf_temp",    _DEFAULTS["pdf_temp"])
        mdl001_temp = self.cfg.get("mdl001_temp", _DEFAULTS["mdl001_temp"])

        Path(pdf_temp).mkdir(parents=True, exist_ok=True)
        Path(mdl001_temp).mkdir(parents=True, exist_ok=True)

        _load_celeritas(self.cfg.get("ssot_dir", _DEFAULTS["ssot_dir"]))
        cap = _mdl001_accel_init(self.workers)
        log.info("[MDL001] accel caps: %s  dpi=%s", cap, self.cfg.get("dpi", 300))

        # ── v1.1.0: BatchBuffer + DuckDB primary + sqlite fallback ──────────
        self.buffer: Optional[MDL001BatchBuffer] = None
        self.duck:   Optional[MDL001DuckWriter]  = None
        if self.cfg.get("enable_db", True):
            self.buffer = MDL001BatchBuffer(
                batch_size=self.cfg.get("batch_size", 5000))
            if self.cfg.get("use_duckdb", True) and DUCKDB_OK:
                try:
                    self.duck = MDL001DuckWriter(
                        str(Path(mdl001_temp) / "VRN_MDL001.duckdb"))
                    log.info("[MDL001] DuckDB primary writer ready")
                except Exception as e:
                    log.warning("[MDL001] DuckDB init fail (%s), sqlite fallback", e)
                    self.duck = None
            try:
                self.db = MDL001DBWriter(str(Path(mdl001_temp) / "VRN_MDL001.db"))
                log.info("[MDL001] sqlite fallback writer ready")
            except Exception as e:
                log.warning("[MDL001] sqlite init fail: %s", e)
                self.db = None

        # Scan existing pdf_temp SHA256 for dedup
        existing_sha256: set = set()
        for f in os.listdir(pdf_temp):
            if f.lower().endswith(".pdf"):
                sha = file_sha256(str(Path(pdf_temp) / f))
                if sha: existing_sha256.add(sha)
        log.info("[MDL001] Existing pdf_temp: %d PDFs (dedup set: %d)",
                 len([f for f in os.listdir(pdf_temp) if f.endswith(".pdf")]),
                 len(existing_sha256))

        # List inputs
        files = list_input_files(input_dir)
        if not files:
            log.warning("[MDL001] No supported files in: %s", input_dir)
            empty = assemble_output([])
            _jwrite(str(Path(mdl001_temp) / "VRN_MDL001_ConvertLog.json"), empty)
            return {"ok": True, "total": 0, "success": 0,
                    "errors": [], "out_dir": pdf_temp}

        log.info("[MDL001] Processing %d files, workers=%d  duck=%s",
                 len(files), self.workers,
                 self.cfg.get("use_duckdb", True))

        all_results: List[Dict] = []
        fail_count = 0

        with ThreadPoolExecutor(max_workers=self.workers) as ex:
            futs = {
                ex.submit(process_one, f, self.cfg, self.db,
                          existing_sha256, self.buffer): f
                for f in files
            }
            for fut in as_completed(futs):
                res = fut.result()
                all_results.append(res)
                if not res.get("ok"): fail_count += 1

        # ── v1.1.0: single-thread flush DB after pool closes ────────────────
        flush_stats = {"conv": 0}
        if self.buffer:
            c_rows = self.buffer.consume_all()
            log.info("[MDL001] Buffer drain: conv=%d", len(c_rows))
            if self.duck:
                try:
                    flush_stats = self.duck.flush(c_rows)
                    log.info("[MDL001] DuckDB flush: %s", flush_stats)
                except Exception as e:
                    log.warning("[MDL001] DuckDB flush fail (%s), sqlite fallback", e)
                    if self.db:
                        flush_stats = self.db.flush(c_rows)
            elif self.db:
                flush_stats = self.db.flush(c_rows)
                log.info("[MDL001] sqlite flush: %s", flush_stats)

        # ── v1.1.0: polars-direct exports ───────────────────────────────────
        parquet_path = csv_path = None
        if self.duck:
            parquet_path = self.duck.export_parquet_polars(mdl001_temp)
            csv_path     = self.duck.export_csv_polars(mdl001_temp)
        elif self.db:
            parquet_path = self.db.export_parquet_polars(mdl001_temp)
            csv_path     = self.db.export_csv_polars(mdl001_temp)
        log.info("[MDL001] Exports: parquet=%s csv=%s", parquet_path, csv_path)

        out = assemble_output(all_results)
        _jwrite(str(Path(mdl001_temp) / "VRN_MDL001_ConvertLog.json"), out)
        # Also copy summary to pdf_temp for downstream modules
        _jwrite(str(Path(pdf_temp) / "VRN_MDL001_ConvertLog.json"), out)

        verify = {
            "module":      __module_id__,
            "version":     __version__,
            "generated":   time.strftime("%Y-%m-%d %H:%M:%S"),
            "total":       len(files),
            "ok":          fail_count == 0,
            "ok_count":    len(files) - fail_count,
            "fail_count":  fail_count,
            "converted":   out["converted"],
            "skipped":     out["skipped_dedup"],
            "total_pages": out["total_pages"],
            "by_src_type": out.get("by_src_type",{}),
            "accel_caps":  cap,
            "flush_stats": flush_stats,
            "fail_details": [{"src": r.get("src_filename",""), "error": r.get("error")}
                             for r in all_results if not r.get("ok")],
        }
        _jwrite(str(Path(mdl001_temp) / "VRN_MDL001_VerifySummary.json"), verify)

        # ── Close DBs BEFORE self-verify ────────────────────────────────────
        if self.duck: self.duck.close()
        if self.db:
            try: self.db._con.close()
            except: pass

        # ── v1.1.0: 4-phase self-verify HTML ────────────────────────────────
        sv_html_path = None
        if self.cfg.get("self_verify", True):
            try:
                sv = MDL001SelfVerifier(self.cfg, out, mdl001_temp).run()
                html = build_self_verify_html_mdl001(sv, out)
                sv_html_path = str(Path(mdl001_temp) / "VRN_MDL001_SelfVerify.html")
                Path(sv_html_path).write_text(html, encoding="utf-8")
                log.info("[MDL001] Self-verify: %s (%d/%d) → %s",
                         sv["classification"], sv["pass"], sv["total"], sv_html_path)
            except Exception as e:
                log.warning("[MDL001] self_verify build fail: %s", e)

        elapsed = round(time.perf_counter() - run_t0, 2)
        log.info(
            "[MDL001] Complete: %d/%d OK  converted=%d  skip=%d  pages=%d  size=%.1fKB  %.2fs",
            len(files) - fail_count, len(files),
            out["converted"], out["skipped_dedup"],
            out["total_pages"], out["total_size_kb"], elapsed,
        )
        return {
            "ok":          fail_count == 0,
            "total":       len(files),
            "success":     len(files) - fail_count,
            "converted":   out["converted"],
            "skipped":     out["skipped_dedup"],
            "total_pages": out["total_pages"],
            "elapsed":     elapsed,
            "flush_stats": flush_stats,
            "self_verify_html": sv_html_path,
            "errors":      [r.get("error", "") for r in all_results if not r.get("ok")],
            "out_dir":     pdf_temp,
            "log_dir":     mdl001_temp,
        }

# ============================================================================
# __all__
# ============================================================================

__all__ = [
    "__version__", "__module_id__",
    "TW_TICKER_REGEX", "TW_BLOOMBERG_REGEX", "TW_YFINANCE_REGEX",
    "_mdl001_accel_init",
    "detect_input_type", "list_input_files", "parse_filename_meta",
    "file_sha256", "rename_output_pdf",
    "convert_pdf_to_hq_pdf", "convert_word_to_pdf",
    "convert_image_to_pdf", "convert_html_to_pdf",
    "validate_pdf_output",
    "process_one", "assemble_output",
    "MDL001DBWriter", "VRN_MDL001_Converter",
    # v1.1.0 NEW
    "MDL001BatchBuffer", "MDL001DuckWriter",
    "MDL001SelfVerifier", "build_self_verify_html_mdl001",
]

# ============================================================================
# __main__
# ============================================================================

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="VRN MDL001 Converter -- Universal→High-Quality PDF")
    for k, v in _DEFAULTS.items():
        tp = bool if isinstance(v, bool) else (int if isinstance(v, int) else str)
        if tp == bool: p.add_argument("--" + k.replace("_", "-"), action="store_true", default=v)
        else:          p.add_argument("--" + k.replace("_", "-"), type=tp, default=v)
    args   = p.parse_args()
    cfg    = {k.replace("-", "_"): v for k, v in vars(args).items()}
    result = VRN_MDL001_Converter(cfg).run()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result["ok"] else 1)
