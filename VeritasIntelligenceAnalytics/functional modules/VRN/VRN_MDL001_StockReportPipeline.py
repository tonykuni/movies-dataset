# [VIA:SAFE_BRIDGE:START]
# -*- coding: utf-8 -*-
from __future__ import annotations

# ╔══════════════════════════════════════════════════════════════════════════════════════════╗
# ║  VRN_MDL001_StockReportPipeline.py                                                      ║
# ║  VeritasReportNova · M01 + M02 + M03 全整合主流水線 · VRN Output Spec v6.0  v1         ║
# ╠══════════════════════════════════════════════════════════════════════════════════════════╣
# ║  架構錨點:                                                                               ║
# ║    ANC-A  PARAMS         所有可調參數 (All at Top)                                       ║
# ║    ANC-B  BOOTSTRAP      路徑引導 + 輔助工具橋接                                        ║
# ║    ANC-C  STDLIB_IMPORTS 標準套件匯入                                                   ║
# ║    ANC-D  REGEX_LOCK     🔒 三條鎖定 TW Ticker Regex                                   ║
# ║    ANC-E  BROKER_RATING  券商清單 + 評等對照表                                          ║
# ║    ANC-F  ACCEL_M03      M03 加速引擎 (L1~L6 + GCTuner + MemoryPool)                  ║
# ║    ANC-G  INFRA          Loguru / DuckDB / Cache / Governor                             ║
# ║    ANC-H  M01_DETECTORS  Ticker/Broker/Rating/Date/TP/Company 偵測器                   ║
# ║    ANC-I  M01_VDF        TWSE/TPEX/MOPS/yfinance 查詢 (Legacy + Panoramic)             ║
# ║    ANC-J  M01_PRICE      價格 + 潛在漲幅 (get_price_metrics)                            ║
# ║    ANC-K  M01_CONSENSUS  YFinance 共識擷取 (v6.0 新增)                                  ║
# ║    ANC-L  M01_REPAIR     SentenceRepairEngine (typed output)                            ║
# ║    ANC-M  M01_CLASSIFY   文件/頁面分類引擎                                              ║
# ║    ANC-N  M01_EXTRACT    PyMuPDF HQ PDF 擷取                                            ║
# ║    ANC-O  M01_OUTPUT     JSON / CSV / TXT 結構化輸出 (v6.0 schema)                     ║
# ║    ANC-P  M02_REPAIR     TextRepairEngine R1-R9                                         ║
# ║    ANC-Q  M02_CANONICAL  同義詞映射 + FinancialRow                                     ║
# ║    ANC-R  M02_VERIFY     交叉驗證 C01~C05                                               ║
# ║    ANC-S  M02_DB         SQLite WAL + Parquet 輸出                                      ║
# ║    ANC-T  CROSS_VALID    v6.0 五條交叉驗證規則 CV-01~CV-05                              ║
# ║    ANC-U  PIPELINE       主流水線 VRNIntegratedPipeline                                 ║
# ║    ANC-V  CLI            argparse 命令列                                                 ║
# ║    ANC-W  MAIN           主入口                                                          ║
# ╠══════════════════════════════════════════════════════════════════════════════════════════╣
# ║  輸出規格: VRN Output Specification v6.0 (2026-02-06)                                   ║
# ║  功能只增不減 · LEGO M-C-F · Append-Only Registry                                      ║
# ╚══════════════════════════════════════════════════════════════════════════════════════════╝

# [VIA:SUPREME_BRIDGE_V3:START]
try:
    import sys as _via_sys
    _via_search_dirs = [
        r"C:\Users\tonyk\OneDrive\Desktop\新增資料夾 (4)\VRN",
        r"C:\VeritasIntelligenceAnalytics\VeritasReportNova\module",
        r"C:\VeritasIntelligenceAnalytics\VeritasPraesidium",
    ]
    for _via_dir in _via_search_dirs:
        if _via_dir and _via_dir not in _via_sys.path:
            _via_sys.path.insert(0, _via_dir)
except Exception as _via_boot_err:
    print(f"[VIA][WARN] path bootstrap: {_via_boot_err}")

try:
    from VeritasAegisNexus import *
except Exception as _via_net_err:
    print(f"[VIA][WARN] VeritasAegisNexus: {_via_net_err}")

try:
    from VeritasCeleritas import *
except Exception as _via_cel_err:
    print(f"[VIA][WARN] VeritasCeleritas: {_via_cel_err}")

try:
    for _via_fn in ("cross_init", "configure_ultra_acceleration", "configure_acceleration"):
        _via_fn_obj = globals().get(_via_fn)
        if callable(_via_fn_obj):
            _via_fn_obj(silent=True) if _via_fn == "cross_init" else _via_fn_obj()
            break
except Exception as _via_init_err:
    print(f"[VIA][WARN] accel bootstrap: {_via_init_err}")
# [VIA:SUPREME_BRIDGE_V3:END]

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-A  PARAMS     所有可調參數集中於此 不散落程式碼
# [VIA:ANCHOR:ANC-A:PARAMS]
# ════════════════════════════════════════════════════════════════════════════

__version__        = "1.1.0"
__module_id__      = "VRN-MDL001-STOCK-PIPELINE"
__spec_version__   = "v6.0"
__rule_version__   = "1.0"

# §P1  路徑
VRN_ROOT       = r"C:\VeritasIntelligenceAnalytics\VeritasReportNova"
P_IN_DIR       = rf"{VRN_ROOT}\input"
P_PDF_TEMP     = rf"{VRN_ROOT}\temp\pdf_temp"
P_M01_TEMP     = rf"{VRN_ROOT}\temp\m01_temp"
P_M02_TEMP     = rf"{VRN_ROOT}\temp\m02_temp"
P_M03_TEMP     = rf"{VRN_ROOT}\temp\m03_temp"
P_DB_PATH      = rf"{VRN_ROOT}\database\vrn_integrated.db"
P_OUTPUT_DIR   = rf"{VRN_ROOT}\output"

# §P2  PDF 擷取
P_DPI          = 300
P_JPEG_QUALITY = 92
P_INPUT_IMAGE_EXT = (".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp")
P_INPUT_WORD_EXT  = (".doc", ".docx")

# §P3  分類門檻
P_CLASSIFY_THRESHOLD  = 15
P_MAX_SCAN_PAGES      = 30
P_MAX_FIN_PAGES       = 10
P_FIN_HIT_THRESHOLD   = 1
P_FIN_SCORE_THRESHOLD = 8
P_MIN_DIGIT_DENSITY   = 0.25
P_ALLOW_NO_FIN_PAGES  = True

# §P4  加速器
P_WORKERS        = 0         # 0=auto (cpu-1)
P_BATCH_SIZE     = 24
P_PRIORITY_BOOST = True
P_GC_OPTIMIZE    = True
P_ENV_BIND       = True
P_ENABLE_CACHE   = True
P_SKIP_IF_EXISTS = False
# Governor
P_GOV_ENABLED        = True
P_GOV_CPU_TEMP_MAX   = 82.0
P_GOV_DRAM_MAX_PCT   = 85.0
P_GOV_MIN_AVAIL_GB   = 1.0
P_GOV_SAFE_AVAIL_GB  = 2.0

# §P5  VDF / yfinance
P_ENABLE_NAME_LOOKUP    = True
P_NAME_LOOKUP_TIMEOUT   = 3
P_VDF_PANORAMIC_ENABLED = True
P_VDF_PANORAMIC_TIMEOUT = 5
P_VDF_RETRY_COUNT       = 2
P_VDF_RETRY_DELAY       = 0.5

# §P6  HTML + 啟動
P_CLEAN_TEMP_ON_START = True
P_HTML_REPORT         = True
P_HTML_AUTO_OPEN      = False      # LL#12

# §P7  文字清洗
P_MIN_LINE_LEN   = 2
P_MAX_LINE_LEN   = 800
P_DEDUP_WINDOW   = 50

# §P8  年份排除 (避免 OCR 抓到年份誤判為 ticker)
P_YEAR_EXCLUSION = list(range(2021, 2031))

# §P9  交叉驗證門檻 (VRN v6.0 CV-01~CV-05)
CV01_TP_DIFF_WARN_PCT  = 20.0    # CV-01: 報告TP vs 共識均值差異 > 20% 發警告
CV02_RATING_MISMATCH   = True    # CV-02: 研報評等 vs 共識評等不一致標記 MISMATCH
CV03_MIN_ANALYST_COUNT = 3       # CV-03: 分析師人數不足
CV04_TP_RANGE_CHECK    = True    # CV-04: TP 超出分析師區間警告
CV05_MEAN_SELL_THRESH  = 3.5     # CV-05: 量化均值 > 3.5 但報告為 buy 標記

# §P10 M02 驗證 (C01~C05)
M02_ZERO_ERROR       = False     # False = 驗證失敗記錄 warning 不中斷流水線
M02_EPS_RANGE        = (-500.0, 500.0)
M02_GROSS_DIFF_MAX   = 0.02      # C02: 毛利誤差容許 2%

# §P11  Lesson Learned
P_LL_CONFIDENCE_THRESHOLD = 0.85

# §P12  M03 加速模式
VIA_ACCEL_DEFAULT_MODE = "maxsafe"
VRN_MODE_MAP = {
    "performance": "maxsafe",
    "safe":        "safe",
    "balanced":    "balanced",
    "max":         "aggressive",
    "ultra":       "aggressive",
}
_CROSS_THREAD_MULTIPLIER = 1.6
_CROSS_THREAD_MIN_BUMP   = 2
_CROSS_THREAD_HARD_CAP   = 64

# ── v1.1.0 NEW (append-only): 6-項優化開關 ──────────────────────────────────
P_USE_DOC_CACHE  = True   # P1 每 PDF 開一次 fitz + pdfplumber
P_PAGE_PARALLEL  = True   # P2 page-level 平行 (within _typed_to_tables 等)
P_PAGE_WORKERS   = 0      # 0 = auto
P_USE_DUCKDB_V11 = True   # P3 DuckDB primary, sqlite fallback
P_BATCH_SIZE     = 5000   # P3
P_POLARS_FIRST   = True   # P5 polars exports
P_SELF_VERIFY    = True   # P6 4-phase HTML

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-B  BOOTSTRAP  (已於頂部完成)
# ⚓ ANC-C  STDLIB_IMPORTS
# [VIA:ANCHOR:ANC-C:IMPORTS]
# ════════════════════════════════════════════════════════════════════════════

import os, gc, re, sys, json, csv, time, copy, math, shutil, hashlib
import sqlite3, platform, threading, importlib, traceback, subprocess
import multiprocessing, collections, contextlib, urllib.request, urllib.parse
import warnings
from pathlib import Path

# ── 靜默非關鍵警告 (yfinance 404 / pdfplumber FontBBox) ─────────────────────
warnings.filterwarnings("ignore", message=".*FontBBox.*")
warnings.filterwarnings("ignore", message=".*possibly delisted.*")
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*RequestsDependencyWarning.*")
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import OrderedDict

# ── 可選加速套件 (safe import) ──────────────────────────────────────────────

def _safe_import(name: str):
    try:
        return importlib.import_module(name)
    except ImportError:
        return None

def _safe_import_sub(name: str):
    try:
        parts = name.rsplit(".", 1)
        mod = importlib.import_module(parts[0])
        return getattr(mod, parts[1], None) if len(parts) > 1 else mod
    except Exception:
        return None

fitz         = _safe_import("fitz")
pdfplumber   = _safe_import("pdfplumber")
yfinance     = _safe_import("yfinance")
# yfinance: suppress 404 / delisted stderr noise
if yfinance:
    try:
        import logging as _yf_logging
        _yf_logging.getLogger("yfinance").setLevel(_yf_logging.CRITICAL)
        _yf_logging.getLogger("peewee").setLevel(_yf_logging.CRITICAL)
    except Exception:
        pass
psutil       = _safe_import("psutil")
loguru_mod   = _safe_import("loguru")
duckdb_mod   = _safe_import("duckdb")
polars_mod   = _safe_import("polars")
pandas_mod   = _safe_import("pandas")
pyarrow_mod  = _safe_import("pyarrow")
numba_mod    = _safe_import("numba")
numexpr_mod  = _safe_import("numexpr")
xxhash_mod   = _safe_import("xxhash")
orjson_mod   = _safe_import("orjson")
rich_mod     = _safe_import("rich")
rich_console = _safe_import("rich.console")
tqdm_mod     = _safe_import("tqdm")

# v1.1.0 alias (統一命名跟其他模組一致)
duckdb_lib   = duckdb_mod
pl           = polars_mod
DUCKDB_OK_v110 = duckdb_lib is not None
POLARS_OK_v110 = pl is not None


# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-C-EXT  v1.1.0 DOCCACHE  (NEW — append-only)
# [VIA:ANCHOR:ANC-C-EXT:DOCCACHE]
# ════════════════════════════════════════════════════════════════════════════

class MDL001SPDocCache:
    """VRN-MDL001SP-CLS-001  (NEW v1.1.0)
    Open fitz + pdfplumber ONCE per PDF, share for cover/typed/fin-page/typed_to_tables.
    Replaces 4× repeated pdfplumber.open() in _process_one.
    """
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self._fitz: Any = None
        self._pp:   Any = None
        self.n_pages: int = 0

    def __enter__(self):
        if fitz is not None:
            try:
                self._fitz = fitz.open(self.pdf_path)
                self.n_pages = len(self._fitz)
            except Exception as e:
                try: log.debug(f"[MDL001SP] DocCache fitz open fail: {e}")
                except: pass
                self._fitz = None
        if pdfplumber is not None:
            try:
                self._pp = pdfplumber.open(self.pdf_path)
                if self.n_pages == 0:
                    self.n_pages = len(self._pp.pages)
            except Exception as e:
                try: log.debug(f"[MDL001SP] DocCache pdfplumber open fail: {e}")
                except: pass
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

    def fitz_page(self, page_no_1based: int):
        if self._fitz is None or page_no_1based - 1 >= len(self._fitz): return None
        return self._fitz[page_no_1based - 1]

    def pdfplumber_page(self, page_no_1based: int):
        if self._pp is None or page_no_1based - 1 >= len(self._pp.pages): return None
        return self._pp.pages[page_no_1based - 1]


# ── Logger ──────────────────────────────────────────────────────────────────

def _build_logger():
    if loguru_mod:
        lg = loguru_mod.logger
        try:
            lg.remove()
            lg.add(sys.stderr, level="DEBUG",
                   format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <white>{message}</white>",
                   colorize=True)
            _log_dir = Path(P_M01_TEMP).parent.parent / "logs"
            _log_dir.mkdir(parents=True, exist_ok=True)
            lg.add(str(_log_dir / "vrn_{time:YYYYMMDD}.log"),
                   level="DEBUG", rotation="10 MB", retention="30 days",
                   encoding="utf-8", enqueue=True)
        except Exception:
            pass
        return lg
    else:
        import logging as _lg
        logging = _lg.getLogger("VRN")
        logging.setLevel(_lg.DEBUG)
        if not logging.handlers:
            _h = _lg.StreamHandler()
            _h.setFormatter(_lg.Formatter("%(asctime)s | %(levelname)-8s | %(message)s",
                                          datefmt="%H:%M:%S"))
            logging.addHandler(_h)
        return logging

log = _build_logger()

# ── Utility helpers ─────────────────────────────────────────────────────────

def _hash8(s: str) -> str:
    if xxhash_mod:
        return xxhash_mod.xxh64(s.encode()).hexdigest()[:8].upper()
    return hashlib.sha256(s.encode("utf-8", errors="replace")).hexdigest()[:8].upper()

def _jload(p: str, default=None) -> Any:
    try:
        txt = Path(p).read_text(encoding="utf-8")
        if orjson_mod:
            return orjson_mod.loads(txt)
        return json.loads(txt)
    except Exception:
        return default

def _jwrite(p: str, data: Any) -> bool:
    try:
        Path(p).parent.mkdir(parents=True, exist_ok=True)
        Path(p).write_text(
            json.dumps(data, ensure_ascii=False, indent=2,
                       default=lambda o: None if isinstance(o, float) and (math.isnan(o) or math.isinf(o)) else str(o)),
            encoding="utf-8")
        return True
    except Exception as e:
        log.warning(f"[JWRITE] {e}")
        return False

def mkdir(p: str) -> None:
    Path(p).mkdir(parents=True, exist_ok=True)

def trim(s: str) -> str:
    if not s:
        return ""
    s = re.sub(r"[\u0000-\u0008\u000b\u000e-\u001f]", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def san(n: str) -> str:
    return re.sub(r'[\\/:*?"<>|]+', "_", n).strip().strip(".")[:180]

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-D  REGEX_LOCK  🔒 三條鎖定 Ticker Regex (不可修改)
# [VIA:ANCHOR:ANC-D:REGEX_LOCK]
# ════════════════════════════════════════════════════════════════════════════

_TW_TICKER_BASE   = r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})"
TW_MOTHER_REGEX   = re.compile(rf"^{_TW_TICKER_BASE}$")
TW_BLOOMBERG_REGEX = re.compile(rf"\b{_TW_TICKER_BASE}\s+TT\b")
TW_YFINANCE_REGEX  = re.compile(rf"\b{_TW_TICKER_BASE}\.(TW|TWO)\b")
TW_CODE_EXTRACT    = re.compile(r"\b([1-9]\d{3})(?=\s+TT|\.TWO?|$)")
TW_TICKER_SCAN     = re.compile(rf"\b{_TW_TICKER_BASE}\b")

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-E  BROKER_RATING  券商清單 + RATING_LIST
# [VIA:ANCHOR:ANC-E:BROKER_RATING]
# ════════════════════════════════════════════════════════════════════════════

P_KNOWN_BROKERS: List[Dict] = [
    {"full": "元大證券",   "abbr": "YTA",     "p": ["元大",  "Yuanta"]},
    {"full": "凱基證券",   "abbr": "KGI",     "p": ["凱基",  "KGI"]},
    {"full": "富邦證券",   "abbr": "FBN",     "p": ["富邦",  "Fubon"]},
    {"full": "國泰證券",   "abbr": "CTY",     "p": ["國泰",  "Cathay"]},
    {"full": "永豐金證券", "abbr": "SNP",     "p": ["永豐",  "SinoPac"]},
    {"full": "群益金鼎",   "abbr": "CYS",     "p": ["群益"]},
    {"full": "統一投顧",   "abbr": "PSC",     "p": ["統一投顧", "統一證"]},
    {"full": "兆豐金控",   "abbr": "MBK",     "p": ["兆豐",  "Mega"]},
    {"full": "台新證券",   "abbr": "TSB",     "p": ["台新",  "Taishin"]},
    {"full": "中信證券",   "abbr": "CTBC",    "p": ["CTBC",  "中信"]},
    {"full": "華南永昌",   "abbr": "HNC",     "p": ["華南永昌", "華南"]},
    {"full": "第一金證券", "abbr": "FSC",     "p": ["第一金"]},
    {"full": "元富證券",   "abbr": "MFH",     "p": ["元富",  "MasterLink"]},
    {"full": "野村證券",   "abbr": "NMR",     "p": ["野村",  "Nomura"]},
    {"full": "摩根士丹利", "abbr": "MS",      "p": ["MS",    "Morgan Stanley", "摩根士丹利"]},
    {"full": "高盛",       "abbr": "GS",      "p": ["GS",    "Goldman", "高盛"]},
    {"full": "摩根大通",   "abbr": "JPM",     "p": ["JPM",   "摩根大通"]},
    {"full": "瑞銀",       "abbr": "UBS",     "p": ["UBS",   "瑞銀"]},
    {"full": "花旗",       "abbr": "CITI",    "p": ["花旗",  "Citi"]},
    {"full": "麥格理",     "abbr": "MQG",     "p": ["麥格理", "Macquarie"]},
    {"full": "日盛證券",   "abbr": "JSC",     "p": ["日盛"]},
    {"full": "玉山證券",   "abbr": "ESB",     "p": ["玉山"]},
    {"full": "宏遠證券",   "abbr": "HYS",     "p": ["宏遠"]},
    {"full": "康和證券",   "abbr": "CHS",     "p": ["康和"]},
    {"full": "BAML",       "abbr": "BAML",    "p": ["BAML", "Merrill", "美林"]},
    {"full": "Deutsche Bank", "abbr": "DB",   "p": ["Deutsche", "德銀"]},
    {"full": "HSBC",       "abbr": "HSBC",    "p": ["HSBC", "匯豐"]},
    {"full": "Barclays",   "abbr": "BARCLAYS","p": ["Barclays", "巴克萊"]},
    {"full": "Mizuho",     "abbr": "MIZUHO",  "p": ["Mizuho", "瑞穗"]},
]

RATING_LIST: Dict[str, Dict] = {
    "buy":      {"zh": ["買進","買入","增持","強力買進","推薦","加碼","積極買進"],
                 "en": ["Buy","Strong Buy","Outperform","Overweight","Accumulate","Add"]},
    "hold":     {"zh": ["持有","中立","觀望","平衡","續抱"],
                 "en": ["Hold","Neutral","Market Perform","Equal Weight"]},
    "sell":     {"zh": ["賣出","減持","下調","減碼","避險","轉弱"],
                 "en": ["Sell","Reduce","Underperform","Underweight","Strong Sell"]},
    "not_rated":{"zh": ["未評等","未評級","無評等","暫無評等"],
                 "en": ["N/A","Not Rated","NR","Not Covered"]},
}
P_RATING_PATTERNS = {k: (v.get("zh", []) + v.get("en", [])) for k, v in RATING_LIST.items()}

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-F  ACCEL_M03  M03 加速引擎 (精簡整合版)
# [VIA:ANCHOR:ANC-F:ACCEL_M03]
# ════════════════════════════════════════════════════════════════════════════

# [VIA:AST-PY-000001:ANCHOR] _mem_pressure_scale
def _mem_pressure_scale() -> float:
    try:
        if not psutil:
            return 1.0
        vm = psutil.virtual_memory()
        r = float(vm.available) / float(vm.total)
        if r < 0.12: return 0.45
        if r < 0.18: return 0.55
        if r < 0.28: return 0.72
        if r < 0.38: return 0.88
        return 1.0
    except Exception:
        return 1.0

# [VIA:AST-PY-000002:ANCHOR] _cpu_count
def _cpu_count(logical: bool = True) -> int:
    try:
        if not logical and psutil:
            n = psutil.cpu_count(logical=False)
            return max(1, int(n)) if n else _cpu_count(logical=True)
    except Exception:
        pass
    return max(1, int(os.cpu_count() or multiprocessing.cpu_count() or 4))

# [VIA:AST-PY-000003:ANCHOR] _available_ram_mb
def _available_ram_mb() -> int:
    try:
        if psutil:
            return max(256, int(psutil.virtual_memory().available // (1024 * 1024)))
    except Exception:
        pass
    return 2048

# [VIA:AST-PY-000004:ANCHOR] _resolve_mode
def _resolve_mode(mode=None) -> str:
    raw = (mode or os.environ.get("VIA_ACCEL_MODE") or VIA_ACCEL_DEFAULT_MODE).strip().lower()
    raw = VRN_MODE_MAP.get(raw, raw)
    return raw if raw in ("safe", "balanced", "maxsafe", "aggressive") else "maxsafe"

# [VIA:AST-PY-000005:ANCHOR] thread_budget
def thread_budget(mode=None, use_physical: bool = True) -> int:
    eff = _resolve_mode(mode)
    n   = _cpu_count(logical=False) if use_physical else _cpu_count(logical=True)
    logic = _cpu_count(logical=True)
    scale = _mem_pressure_scale()
    if eff == "safe":         t = 1
    elif eff == "balanced":   t = max(1, min(n // 2, 8))
    elif eff == "aggressive": t = max(2, n) if n <= 2 else n
    else:                     t = max(2, min(16, n - 1)) if n > 2 else n
    return max(1, min(logic, int(max(1, t * scale))))

# [VIA:AST-PY-000006:ANCHOR] apply_vrn_vds_max_accel
def apply_vrn_vds_max_accel(mode=None) -> Dict:
    eff = _resolve_mode(mode)
    t   = thread_budget(eff)
    tc  = min(_CROSS_THREAD_HARD_CAP, int(max(t * _CROSS_THREAD_MULTIPLIER, t + _CROSS_THREAD_MIN_BUMP)))
    s, sc = str(t), str(tc)
    env = {
        "OMP_NUM_THREADS": s, "MKL_NUM_THREADS": s, "OPENBLAS_NUM_THREADS": s,
        "NUMEXPR_NUM_THREADS": s, "NUMEXPR_MAX_THREADS": sc, "BLIS_NUM_THREADS": s,
        "VECLIB_MAXIMUM_THREADS": s, "NUMBA_NUM_THREADS": s, "POLARS_MAX_THREADS": s,
        "RAYON_NUM_THREADS": s, "TOKENIZERS_PARALLELISM": "false",
        "VIA_ACCEL_MODE": eff, "VIA_ACCEL_ACTIVE_THREADS": s,
        "VRN_ACCEL_MAX": s, "VRN_CROSS_ACCEL": sc,
        "ACCEL_MASTER_ENABLE_ALL_CPU": "1",
    }
    for k, v in env.items():
        os.environ[k] = v
    if numexpr_mod:
        try:
            numexpr_mod.set_num_threads(t)
        except Exception:
            pass
    return env

# [VIA:AST-PY-000007:ANCHOR] GCTuner
class GCTuner:
    """M03 GC tuner with context managers."""
    _DEFAULT_THRESH = (50_000, 500, 50)

    @classmethod
    def optimize(cls):
        gc.set_threshold(*cls._DEFAULT_THRESH)
        gc.collect(0)

    @classmethod
    @contextlib.contextmanager
    def hot_loop(cls):
        was = gc.isenabled()
        gc.disable()
        try:
            yield
        finally:
            if was:
                gc.enable()
            gc.collect(0)

# [VIA:AST-PY-000008:ANCHOR] MemoryPool
class MemoryPool:
    """M03 RAM-aware byte-buffer pool."""
    def __init__(self, block_mb: int = 0, pool_size: int = 8):
        avail = _available_ram_mb()
        auto  = max(1, min(avail // 8, 64))
        bmb   = int(block_mb) if block_mb > 0 else auto
        self._block = max(1, bmb) * (1024 * 1024)
        self._pool  = [bytearray(self._block) for _ in range(max(1, pool_size))]
        self._lock  = threading.Lock()

    def acquire(self) -> bytearray:
        with self._lock:
            return self._pool.pop() if self._pool else bytearray(self._block)

    def release(self, buf: bytearray) -> None:
        with self._lock:
            if len(self._pool) < 32:
                self._pool.append(buf)

# [VIA:AST-PY-000009:ANCHOR] accel_init_full
def accel_init_full(cfg: Dict) -> int:
    """L1~L4 全速初始化。回傳 worker 數。"""
    # L1: OS priority
    if cfg.get("PRIORITY_BOOST", P_PRIORITY_BOOST):
        try:
            if platform.system() == "Windows":
                import ctypes
                ctypes.windll.kernel32.SetPriorityClass(
                    ctypes.windll.kernel32.GetCurrentProcess(), 0x00008000)
        except Exception:
            pass
    # L2: GC
    if cfg.get("GC_OPTIMIZE", P_GC_OPTIMIZE):
        GCTuner.optimize()
    # L3: ENV
    apply_vrn_vds_max_accel()
    # L4: workers
    w = cfg.get("WORKERS", P_WORKERS)
    return int(w) if w and w > 0 else max(1, _cpu_count(logical=False) - 1)

# [VIA:AST-PY-000010:ANCHOR] HardwareGovernor
class HardwareGovernor:
    """L6 硬體安全監控 防燒毀 / 動態降速。"""
    # [VIA:AST-PY-000011:ANCHOR] HardwareGovernor.status
    def status(self, cfg: Dict) -> Dict:
        if not P_GOV_ENABLED or not psutil:
            return {"level": 0, "name": "SAFE", "adj_workers": accel_init_full(cfg)}
        vm    = psutil.virtual_memory()
        avail = vm.available / (1024 ** 3)
        pct   = vm.percent
        # CPU temp (Windows may not have coretemp)
        temp = 0.0
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                for key in ("coretemp", "cpu_thermal", "k10temp"):
                    if key in temps:
                        temp = temps[key][0].current
                        break
        except Exception:
            pass
        base_w = max(1, _cpu_count(logical=False) - 1)
        if temp > P_GOV_CPU_TEMP_MAX or pct > P_GOV_DRAM_MAX_PCT:
            log.warning(f"[GOV] THROTTLE  temp={temp:.1f}°C  RAM={pct:.0f}%")
            return {"level": 4, "name": "THROTTLE", "adj_workers": max(1, base_w // 2)}
        if avail < P_GOV_MIN_AVAIL_GB:
            return {"level": 3, "name": "PRESSURE", "adj_workers": max(1, base_w // 2)}
        if avail < P_GOV_SAFE_AVAIL_GB:
            return {"level": 2, "name": "CAUTION",  "adj_workers": max(1, base_w - 1)}
        return {"level": 0, "name": "SAFE", "adj_workers": base_w}

# [VIA:AST-PY-000012:ANCHOR] VIACache
class VIACache:
    """L5 Thread-safe 多層快取。"""
    def __init__(self, enabled: bool = True, maxsize: int = 512):
        self._enabled = enabled
        self._cache: Dict[str, Any] = {}
        self._lock   = threading.Lock()
        self._maxsize = maxsize
        self._hits = self._miss = 0

    def get(self, key: str, default=None) -> Any:
        if not self._enabled:
            return default
        with self._lock:
            v = self._cache.get(key)
            if v is not None:
                self._hits += 1
                return v
            self._miss += 1
            return default

    def set(self, key: str, value: Any) -> None:
        if not self._enabled:
            return
        with self._lock:
            if len(self._cache) >= self._maxsize:
                del self._cache[next(iter(self._cache))]
            self._cache[key] = value

    def stats(self) -> Dict:
        return {"hits": self._hits, "miss": self._miss, "size": len(self._cache)}

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-G  INFRA  Loguru / DuckDB Lesson Learned
# [VIA:ANCHOR:ANC-G:INFRA]
# ════════════════════════════════════════════════════════════════════════════

# [VIA:AST-PY-000013:ANCHOR] LessonLearnedDB
class LessonLearnedDB:
    """DuckDB / SQLite Lesson Learned 持久化。"""
    # [VIA:AST-PY-000014:ANCHOR] LessonLearnedDB.__init__
    def __init__(self, db_path: str):
        self._path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._use_duck = duckdb_mod is not None
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        if self._use_duck:
            with duckdb_mod.connect(self._path) as con:
                con.execute("""
                    CREATE TABLE IF NOT EXISTS lesson_learned (
                        ts          TIMESTAMP DEFAULT current_timestamp,
                        error_type  VARCHAR,
                        report_code VARCHAR,
                        content     TEXT,
                        cpu_temp    DOUBLE,
                        confidence  DOUBLE
                    )""")
        else:
            with sqlite3.connect(self._path) as con:
                con.execute("""
                    CREATE TABLE IF NOT EXISTS lesson_learned (
                        id          INTEGER PRIMARY KEY AUTOINCREMENT,
                        ts          TEXT DEFAULT (datetime('now')),
                        error_type  TEXT,
                        report_code TEXT,
                        content     TEXT,
                        cpu_temp    REAL,
                        confidence  REAL
                    )""")

    # [VIA:AST-PY-000015:ANCHOR] LessonLearnedDB.log_lesson
    def log_lesson(self, error_type: str, report_code: str,
                   content: str, confidence: float = 0.0) -> None:
        cpu_temp = 0.0
        try:
            if psutil:
                temps = psutil.sensors_temperatures()
                if temps:
                    for key in ("coretemp", "cpu_thermal", "k10temp"):
                        if key in temps:
                            cpu_temp = temps[key][0].current
                            break
        except Exception:
            pass
        with self._lock:
            try:
                if self._use_duck:
                    with duckdb_mod.connect(self._path) as con:
                        con.execute(
                            "INSERT INTO lesson_learned (error_type,report_code,content,cpu_temp,confidence) VALUES (?,?,?,?,?)",
                            [error_type, report_code, content[:500], cpu_temp, confidence])
                else:
                    with sqlite3.connect(self._path) as con:
                        con.execute(
                            "INSERT INTO lesson_learned (error_type,report_code,content,cpu_temp,confidence) VALUES (?,?,?,?,?)",
                            (error_type, report_code, content[:500], cpu_temp, confidence))
            except Exception as e:
                log.warning(f"[LL] log_lesson failed: {e}")

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-H  M01_DETECTORS  Ticker / Broker / Rating / Date / TP / Company
# [VIA:ANCHOR:ANC-H:M01_DETECTORS]
# ════════════════════════════════════════════════════════════════════════════

# [VIA:AST-PY-000016:ANCHOR] vtk
def vtk(t: str, cfg: Optional[Dict] = None) -> bool:
    """Validate 4-digit TW ticker."""
    if not t or len(t) != 4 or t[0] == "0":
        return False
    try:
        return int(t) not in (cfg or {}).get("YEAR_EXCLUSION", P_YEAR_EXCLUSION)
    except Exception:
        return False

# [VIA:AST-PY-000017:ANCHOR] detect_tw_ticker
def detect_tw_ticker(s: str) -> Optional[Dict[str, str]]:
    """M02-F01: Detect TW ticker in various formats."""
    for system, fmt, regex in [
        ("twse",      "mother",    TW_MOTHER_REGEX),
        ("bloomberg", "bloomberg", TW_BLOOMBERG_REGEX),
        ("yfinance",  "yfinance",  TW_YFINANCE_REGEX),
    ]:
        m = regex.search(s)
        if m:
            return {"category": "ticker", "market": "TW",
                    "system": system, "format": fmt,
                    "code": m.group(1), "raw": s}
    return None

# [VIA:AST-PY-000018:ANCHOR] detect_ticker
def detect_ticker(text: str, cfg: Optional[Dict] = None) -> str:
    """Extract TW ticker (multi-pattern priority)."""
    _cfg = cfg or {}
    for rx in (TW_BLOOMBERG_REGEX, TW_YFINANCE_REGEX):
        m = rx.search(text)
        if m and vtk(m.group(1), _cfg):
            return m.group(1)
    m = re.search(r'[\( ]\s*(\d{4})\s*[\) ]', text)
    if m and vtk(m.group(1), _cfg):
        return m.group(1)
    m = re.match(r'^(\d{4})[_\-\s]', text)
    if m and vtk(m.group(1), _cfg):
        return m.group(1)
    m = re.search(r'[A-Za-z][-_](\d{4})(?:\s|[-_\.]|$)', text)
    if m and vtk(m.group(1), _cfg):
        return m.group(1)
    for m in TW_TICKER_SCAN.finditer(text[:500]):
        if vtk(m.group(1), _cfg):
            return m.group(1)
    return ""

# [VIA:AST-PY-000019:ANCHOR] detect_broker
def detect_broker(text: str) -> Dict[str, str]:
    """Detect broker from text."""
    for b in P_KNOWN_BROKERS:
        for p in b["p"]:
            if re.search(re.escape(p), text, re.I):
                return {"full": b["full"], "abbr": b["abbr"]}
    return {"full": "", "abbr": ""}

# [VIA:AST-PY-000020:ANCHOR] detect_rating
def detect_rating(text: str) -> Dict[str, str]:
    """Detect investment rating → {rating, category}."""
    for cat, pats in P_RATING_PATTERNS.items():
        for p in pats:
            if re.search(re.escape(p), text, re.I):
                return {"rating": p, "category": cat}
    return {"rating": "", "category": ""}

# [VIA:AST-PY-000021:ANCHOR] detect_date
def detect_date(text: str) -> str:
    """Extract report date → ISO YYYY-MM-DD."""
    for pat in [
        r'(20\d{2})[年/\-\.](1[0-2]|0?[1-9])[月/\-\.]([12]\d|3[01]|0?[1-9])',
        r'(20\d{2})(0[1-9]|1[0-2])([12]\d|3[01]|0[1-9])',
        r'民國\s*(\d{2,3})\s*年\s*(1[0-2]|0?[1-9])\s*月\s*([12]\d|3[01]|0?[1-9])\s*日',
    ]:
        m = re.search(pat, text)
        if m:
            y, mo, d = m.group(1), m.group(2), m.group(3)
            if int(y) < 200:
                y = str(int(y) + 1911)
            return f"{y}-{mo.zfill(2)}-{d.zfill(2)}"
    return ""

# [VIA:AST-PY-000022:ANCHOR] detect_tp
def detect_tp(text: str) -> str:
    """Extract target price string."""
    for kw in ["目標價", "合理價", "Target Price", "Price Target", "Fair Value", "TP"]:
        m = re.search(re.escape(kw) + r'[:\s ]*(?:NT\$?|TWD)?\s*([\d,]+(?:\.\d+)?)', text, re.I)
        if m:
            return m.group(1).replace(",", "")
    return ""

# [VIA:AST-PY-000023:ANCHOR] detect_company
def detect_company(text: str, ticker: str) -> str:
    """Detect Chinese company name near ticker."""
    if not ticker:
        return ""
    for pat in [
        re.compile(r'([\u4e00-\u9fff]{2,10})\s*[\( ]\s*' + re.escape(ticker)),
        re.compile(re.escape(ticker) + r'\s*[\) ]?\s*([\u4e00-\u9fff]{2,10})'),
    ]:
        m = pat.search(text)
        if m:
            return m.group(1).strip()
    return ""

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-I  M01_VDF  TWSE / TPEX / MOPS / yfinance 查詢
# [VIA:ANCHOR:ANC-I:M01_VDF]
# ════════════════════════════════════════════════════════════════════════════

_NAME_CACHE: Dict[str, Dict] = {}
_NAME_CACHE_LOCK = threading.Lock()

# [VIA:AST-PY-000024:ANCHOR] _vdf_request
def _vdf_request(url: str, timeout: int, data: Optional[bytes] = None,
                 headers: Optional[Dict] = None) -> Optional[str]:
    hdrs = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    if headers:
        hdrs.update(headers)
    for attempt in range(P_VDF_RETRY_COUNT + 1):
        try:
            req = urllib.request.Request(url, data=data, headers=hdrs)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except Exception:
            if attempt < P_VDF_RETRY_COUNT:
                time.sleep(P_VDF_RETRY_DELAY)
    return None

# [VIA:AST-PY-000025:ANCHOR] _vdf_json_request
def _vdf_json_request(url: str, timeout: int) -> Optional[Dict]:
    raw = _vdf_request(url, timeout)
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            pass
    return None

# [VIA:AST-PY-000026:ANCHOR] vdf_lookup_twse
def vdf_lookup_twse(ticker: str, timeout: int = P_NAME_LOOKUP_TIMEOUT) -> Dict:
    result = {"name": "", "name_en": "", "source": ""}
    url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=tse_{ticker}.tw"
    data = _vdf_json_request(url, timeout)
    if data:
        arr = data.get("msgArray", [])
        if arr:
            info = arr[0]
            name = info.get("n", "")
            if name:
                result.update({"name": name, "name_en": info.get("nf", ""), "source": "twse"})
    return result

# [VIA:AST-PY-000027:ANCHOR] vdf_lookup_tpex
def vdf_lookup_tpex(ticker: str, timeout: int = P_NAME_LOOKUP_TIMEOUT) -> Dict:
    result = {"name": "", "name_en": "", "source": ""}
    url = f"https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=otc_{ticker}.tw"
    data = _vdf_json_request(url, timeout)
    if data:
        arr = data.get("msgArray", [])
        if arr:
            info = arr[0]
            name = info.get("n", "")
            if name:
                result.update({"name": name, "name_en": info.get("nf", ""), "source": "tpex"})
    return result

# [VIA:AST-PY-000028:ANCHOR] vdf_lookup_yfinance
def vdf_lookup_yfinance(ticker: str, timeout: int = P_NAME_LOOKUP_TIMEOUT) -> Dict:
    result = {"name": "", "name_en": "", "source": ""}
    if not yfinance:
        return result
    for suffix in (".TW", ".TWO"):
        try:
            info = yfinance.Ticker(f"{ticker}{suffix}").info
            long_name = info.get("longName", "") or info.get("shortName", "")
            if long_name:
                result["name_en"] = long_name
                result["source"]  = f"yfinance{suffix}"
                return result
        except Exception:
            continue
    return result

# [VIA:AST-PY-000029:ANCHOR] resolve_company_name
def resolve_company_name(ticker: str, cover_text: str, fn: str) -> Dict:
    """多來源公司名稱解析 優先: Local → Cache → TWSE → TPEX → yfinance"""
    result = {"name": "", "name_en": "", "source": "local", "matched_fn": False}
    local_name = detect_company(cover_text, ticker)
    if local_name:
        result["name"] = local_name
    with _NAME_CACHE_LOCK:
        if ticker in _NAME_CACHE:
            cached = _NAME_CACHE[ticker]
            if not result["name"] and cached.get("name"):
                result["name"] = cached["name"]
            if cached.get("name_en"):
                result["name_en"] = cached["name_en"]
            result["source"] = cached.get("source", "cache")
    if P_ENABLE_NAME_LOOKUP and (not result["name"] or not result["name_en"]):
        t = P_NAME_LOOKUP_TIMEOUT
        if not result["name"]:
            for fn_lookup in (vdf_lookup_twse, vdf_lookup_tpex):
                r = fn_lookup(ticker, t)
                if r["name"]:
                    result["name"]   = r["name"]
                    result["source"] = r["source"]
                    if r["name_en"] and not result["name_en"]:
                        result["name_en"] = r["name_en"]
                    break
        if not result["name_en"]:
            yf = vdf_lookup_yfinance(ticker, t)
            if yf["name_en"]:
                result["name_en"] = yf["name_en"]
        if result["name"] or result["name_en"]:
            with _NAME_CACHE_LOCK:
                _NAME_CACHE[ticker] = {
                    "name": result["name"], "name_en": result["name_en"],
                    "source": result["source"]}
    if result["name"] and result["name"] in fn:
        result["matched_fn"] = True
    return result

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-J  M01_PRICE  價格 + 潛在漲幅
# [VIA:ANCHOR:ANC-J:M01_PRICE]
# ════════════════════════════════════════════════════════════════════════════

# yfinance .info 欄位對應
YF_INFO_KEY_MAP: Tuple = (
    ("shortName",           "name_short"),
    ("exchange",            "exchange"),
    ("sector",              "sector"),
    ("industry",            "industry"),
    ("marketCap",           "market_cap"),
    ("beta",                "beta"),
    ("dividendYield",       "dividend_yield"),
    ("payoutRatio",         "payout_ratio"),
    ("trailingPE",          "pe_ratio"),
    ("forwardPE",           "forward_pe"),
    ("priceToBook",         "pb_ratio"),
    ("trailingEps",         "trailing_eps"),
    ("forwardEps",          "forward_eps"),
    ("recommendationMean",  "consensus_rating_mean"),
    ("recommendationKey",   "consensus_rating"),
    ("numberOfAnalystOpinions", "analyst_count"),
    ("targetMeanPrice",     "consensus_target_mean"),
    ("targetHighPrice",     "consensus_target_high"),
    ("targetLowPrice",      "consensus_target_low"),
    ("targetMedianPrice",   "consensus_target_median"),
)

# [VIA:AST-PY-000030:ANCHOR] get_price_metrics
def get_price_metrics(ticker: str, report_date: str, target_price: str) -> Dict[str, Any]:
    """M01 必備 yfinance_ticker / adj_close / upside_pct / performance_pct"""
    res: Dict[str, Any] = {
        "yfinance_ticker": "",
        "adj_close": None,
        "adj_close_date": "",
        "upside_pct": None,
        "upside_target_source": "",
        "performance_pct_since_report": None,
    }
    if not ticker or not yfinance:
        return res
    for suf in (".TW", ".TWO"):
        try:
            yt   = yfinance.Ticker(f"{ticker}{suf}")
            hist = yt.history(period="2y", timeout=P_VDF_PANORAMIC_TIMEOUT)
            if hist is None or len(hist) == 0:
                continue
            res["yfinance_ticker"] = f"{ticker}{suf}"
            last = hist.iloc[-1]
            latest = float(last.get("Close", 0) or last.get("Adj Close", 0))
            res["adj_close"] = round(latest, 2)
            # close on report date
            adj_report = None
            if report_date:
                try:
                    rd = datetime.strptime(report_date[:10].replace("/", "-"), "%Y-%m-%d")
                    idx = hist.index.get_indexer([rd], method="ffill")[0]
                    if 0 <= idx < len(hist):
                        adj_report = float(hist.iloc[idx].get("Close", 0) or hist.iloc[idx].get("Adj Close", 0))
                except Exception:
                    pass
            if adj_report is None:
                adj_report = float(hist.iloc[0].get("Close", 0) or hist.iloc[0].get("Adj Close", 0))
            if adj_report and adj_report > 0:
                res["adj_close_date"] = str(report_date)[:10]
                try:
                    tp_f = float(str(target_price).replace(",", ""))
                    if tp_f > 0:
                        res["upside_pct"]          = round((tp_f - adj_report) / adj_report * 100, 2)
                        res["upside_target_source"] = "Report"
                except Exception:
                    pass
                res["performance_pct_since_report"] = round((latest - adj_report) / adj_report * 100, 2)
            return res
        except Exception:
            continue
    return res

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-K  M01_CONSENSUS  YFinance 共識擷取 (VRN v6.0 新增)
# [VIA:ANCHOR:ANC-K:M01_CONSENSUS]
# ════════════════════════════════════════════════════════════════════════════

# [VIA:AST-PY-000031:ANCHOR] fetch_yfinance_info
def fetch_yfinance_info(ticker: str, yfinance_ticker: str) -> Dict[str, Any]:
    """透過 YF_INFO_KEY_MAP 擷取 .info 欄位 (含共識目標價 / 評等 / 分析師人數)"""
    out: Dict[str, Any] = {v: None for _, v in YF_INFO_KEY_MAP}
    if not yfinance:
        return out
    try_list = [yfinance_ticker] if yfinance_ticker else [f"{ticker}.TW", f"{ticker}.TWO"]
    for yf_t in try_list:
        try:
            info = yfinance.Ticker(yf_t).info
            if not info or not isinstance(info, dict):
                continue
            for yf_key, our_key in YF_INFO_KEY_MAP:
                v = info.get(yf_key)
                if v is not None:
                    out[our_key] = v
            return out
        except Exception:
            continue
    return out

# [VIA:AST-PY-000032:ANCHOR] fetch_analyst_distribution
def fetch_analyst_distribution(yfinance_ticker: str) -> Dict[str, Optional[int]]:
    """透過 .recommendations 取最新一期 strongBuy/buy/hold/sell/strongSell"""
    keys = ["analyst_strong_buy", "analyst_buy", "analyst_hold",
            "analyst_sell", "analyst_strong_sell"]
    result: Dict[str, Optional[int]] = {k: None for k in keys}
    if not yfinance or not yfinance_ticker:
        return result
    try:
        recs = yfinance.Ticker(yfinance_ticker).recommendations
        if recs is not None and not recs.empty:
            latest = recs.iloc[-1]
            result["analyst_strong_buy"]  = int(latest.get("strongBuy",  0))
            result["analyst_buy"]         = int(latest.get("buy",        0))
            result["analyst_hold"]        = int(latest.get("hold",       0))
            result["analyst_sell"]        = int(latest.get("sell",       0))
            result["analyst_strong_sell"] = int(latest.get("strongSell", 0))
    except Exception:
        pass
    return result

# [VIA:AST-PY-000033:ANCHOR] build_consensus_block
def build_consensus_block(ticker: str, yfinance_ticker: str) -> Dict[str, Any]:
    """
    整合 fetch_yfinance_info + fetch_analyst_distribution
    輸出 VRN v6.0 §1D Consensus block (完整)。
    """
    info_data = fetch_yfinance_info(ticker, yfinance_ticker)
    dist_data = fetch_analyst_distribution(yfinance_ticker)
    return {
        # 共識目標價
        "consensus_target_high":   info_data.get("consensus_target_high"),
        "consensus_target_low":    info_data.get("consensus_target_low"),
        "consensus_target_mean":   info_data.get("consensus_target_mean"),
        "consensus_target_median": info_data.get("consensus_target_median"),
        # 共識評等
        "consensus_rating":        info_data.get("consensus_rating", ""),
        "consensus_rating_mean":   info_data.get("consensus_rating_mean"),
        # 分析師覆蓋 (from .info)
        "analyst_count":           info_data.get("analyst_count"),
        # 分析師分佈 (from .recommendations)
        "analyst_strong_buy":      dist_data.get("analyst_strong_buy"),
        "analyst_buy":             dist_data.get("analyst_buy"),
        "analyst_hold":            dist_data.get("analyst_hold"),
        "analyst_sell":            dist_data.get("analyst_sell"),
        "analyst_strong_sell":     dist_data.get("analyst_strong_sell"),
        # 附帶 .info 財務/估值
        "beta":                    info_data.get("beta"),
        "pe_ratio":                info_data.get("pe_ratio"),
        "forward_pe":              info_data.get("forward_pe"),
        "pb_ratio":                info_data.get("pb_ratio"),
        "dividend_yield":          info_data.get("dividend_yield"),
        "trailing_eps":            info_data.get("trailing_eps"),
        "forward_eps":             info_data.get("forward_eps"),
        "name_short":              info_data.get("name_short", ""),
        "sector":                  info_data.get("sector", ""),
        "industry":                info_data.get("industry", ""),
        "market_cap":              info_data.get("market_cap"),
    }

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-L  M01_REPAIR  SentenceRepairEngine
# [VIA:ANCHOR:ANC-L:M01_REPAIR]
# ════════════════════════════════════════════════════════════════════════════

# [VIA:AST-PY-000034:ANCHOR] SentenceRepairEngine
class SentenceRepairEngine:
    """Reconstruct coherent sentences from pdfplumber word-level extraction."""
    CN_END   = set("。！？；…  》〉")
    EN_END   = set(".!?;:)")
    KV_PAT   = re.compile(r'^[\u4e00-\u9fff\w\s]{2,15}\s*[: ]\s*.+')
    TITLE_PATS = [
        re.compile(r'^[\u4e00-\u9fff]{2,10}\s*[\( ]\s*\d{4}\s*[\) ]'),
        re.compile(r'(買進|賣出|中立|持有|Buy|Sell|Hold|Outperform|Neutral)', re.I),
        re.compile(r'目標價|Target\s*Price|Fair\s*Value', re.I),
        re.compile(r'^\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2}$'),
        re.compile(r'^[\u25cf\u25cb■□●○★☆►▶◆◇•·\-– ]\s'),
    ]

    def repair_typed(self, page) -> List[Dict]:
        lines = self._build_lines(page)
        if not lines:
            return self._fallback_typed(page.extract_text() or "")
        return self._merge_typed(self._classify_lines(lines))

    def _build_lines(self, page) -> List[Dict]:
        try:
            words = page.extract_words(keep_blank_chars=True, x_tolerance=3, y_tolerance=3)
        except Exception:
            try:
                words = page.extract_words(x_tolerance=3, y_tolerance=3)
            except Exception:
                words = []
        if not words:
            return []
        groups, cur_y = [[words[0]]], words[0].get("top", 0)
        for w in words[1:]:
            wy = w.get("top", 0)
            if abs(wy - cur_y) <= 3:
                groups[-1].append(w)
            else:
                groups.append([w])
                cur_y = wy
        out = []
        for g in groups:
            g.sort(key=lambda w: w.get("x0", 0))
            txt = " ".join(w.get("text", "") for w in g).strip()
            if not txt:
                continue
            txt = re.sub(r"\s+", " ", txt)
            txt = re.sub(r"([\u4e00-\u9fff])\s+([\u4e00-\u9fff])", r"\1\2", txt)
            sz  = [w.get("size", 10) for w in g if w.get("size")]
            out.append({
                "text": txt.strip(),
                "y":    sum(w.get("top", 0) for w in g) / len(g),
                "sz":   sum(sz) / len(sz) if sz else 10.0,
                "bold": any("Bold" in (w.get("fontname", "") or "") for w in g),
                "n":    len(txt.replace(" ", "")),
            })
        out.sort(key=lambda d: d["y"])
        return out

    def _classify_lines(self, lines: List[Dict]) -> List[Dict]:
        szs = sorted(d["sz"] for d in lines)
        med = szs[len(szs) // 2] if szs else 10
        for d in lines:
            t, s, n = d["text"], d["sz"], d["n"]
            digs = len(re.findall(r'[\d,.%\-]', t))
            tot  = len(t.replace(" ", ""))
            if tot > 3 and digs / tot > 0.6:
                d["tp"] = "table"
                continue
            if self.KV_PAT.match(t) and n < 40:
                d["tp"] = "kv"
                continue
            if re.match(r'^[\u25cf\u25cb■□●○★☆►▶◆◇•·\-– ]\s', t):
                d["tp"] = "bullet"
                continue
            is_title = s > med * 1.3 or (d["bold"] and n < 25) or n <= 8
            if not is_title:
                for p in self.TITLE_PATS:
                    if p.search(t):
                        is_title = True
                        break
            d["tp"] = "title" if is_title else "body"
        return lines

    def _merge_typed(self, lines: List[Dict]) -> List[Dict]:
        raw, buf = [], ""
        for d in lines:
            t = d["text"]
            if d["tp"] in ("title", "kv", "table", "bullet"):
                if buf:
                    raw.append((buf, False))
                    buf = ""
                raw.append((t, d["tp"] == "table"))
            else:
                buf = (buf.rstrip() + t.lstrip()) if buf else t
                if t and t[-1] in self.CN_END | self.EN_END:
                    raw.append((buf, False))
                    buf = ""
        if buf:
            raw.append((buf, False))
        seen, result = set(), []
        for txt, is_tbl in raw:
            txt = txt.strip()
            if txt and txt not in seen:
                seen.add(txt)
                result.append({"text": txt, "line_type": "TBL" if is_tbl else "TXT"})
        return result

    def _fallback_typed(self, raw: str) -> List[Dict]:
        out = []
        for line in raw.split("\n"):
            line = line.strip()
            if not line:
                continue
            tot  = len(line.replace(" ", ""))
            digs = len(re.findall(r'[\d,.%\-]', line))
            is_tbl = tot > 3 and digs / tot > 0.6
            out.append({"text": line, "line_type": "TBL" if is_tbl else "TXT"})
        return out

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-M  M01_CLASSIFY  文件/頁面分類
# [VIA:ANCHOR:ANC-M:M01_CLASSIFY]
# ════════════════════════════════════════════════════════════════════════════

P_FIRSTPAGE_SIGNALS = [
    "投資評等","目標價","評等","買進","中立","賣出",
    "Target Price","Rating","Buy","Hold","Sell",
    "Company Report","Company Update","Earnings Review",
]
P_FIN_KEYWORDS_CORE = [
    "損益表","綜合損益表","合併損益表","資產負債表",
    "Income Statement","Balance Sheet","Cash Flow","P&L",
]
P_FIN_KEYWORDS_GENERAL = [
    "財務摘要","財務預估","Financial Summary","Key Financials",
    "毛利率","營業利益","稅後淨利","EPS","ROE","ROA",
    "Revenue","Gross Margin","Operating Profit","Net Income",
]
P_EXCLUDE_FILENAME_REGEX = re.compile(
    r"(?i)(晨會|早報|盤勢|總經|產業|展望|策略|insights|hardware|"
    r"thermal|宏觀|conference|brief|morning|週報|月報)"
)

# [VIA:AST-PY-000035:ANCHOR] is_stock_report
def is_stock_report(fn: str, cover_text: str, ticker: str) -> Tuple[bool, int, List[str]]:
    """快速判斷是否為個股報告 → (is_stock, score, reasons)"""
    score, reasons = 0, []
    fn_lower = fn.lower()
    if P_EXCLUDE_FILENAME_REGEX.search(fn):
        return False, -1, ["excluded_by_filename"]
    if ticker:
        score += 8
        reasons.append(f"ticker_found:{ticker}")
    for sig in P_FIRSTPAGE_SIGNALS:
        if sig in cover_text or sig.lower() in fn_lower:
            score += 2
            reasons.append(f"signal:{sig}")
            break
    det_broker = detect_broker(fn + " " + cover_text)
    if det_broker["abbr"]:
        score += 3
        reasons.append(f"broker:{det_broker['abbr']}")
    det_rating = detect_rating(cover_text)
    if det_rating["category"]:
        score += 4
        reasons.append(f"rating:{det_rating['category']}")
    tp = detect_tp(cover_text)
    if tp:
        score += 3
        reasons.append(f"tp:{tp}")
    return score >= P_CLASSIFY_THRESHOLD, score, reasons

# [VIA:AST-PY-000036:ANCHOR] detect_fin_pages
def detect_fin_pages(pdf_path: str,
                      doc_cache: Optional["MDL001SPDocCache"] = None) -> List[Dict]:
    """偵測財報頁 → List[{page, score, hits, reasons}]
    v1.1.0: doc_cache fast path."""
    if not pdfplumber:
        return []
    result = []

    def _scan(pdf):
        for i, page in enumerate(pdf.pages[:P_MAX_SCAN_PAGES]):
            text = page.extract_text() or ""
            score, hits, reasons = 0, 0, []
            for kw in P_FIN_KEYWORDS_CORE:
                if kw in text:
                    score += 5
                    hits  += 1
                    reasons.append(f"core:{kw}")
            for kw in P_FIN_KEYWORDS_GENERAL:
                if kw in text:
                    score += 1
                    reasons.append(f"gen:{kw}")
            # digit density check
            tot  = len(text.replace(" ", ""))
            digs = len(re.findall(r"[\d,.%\-]", text))
            if tot > 20 and digs / tot >= P_MIN_DIGIT_DENSITY:
                score += 2
                reasons.append("digit_density")
            if hits >= P_FIN_HIT_THRESHOLD or score >= P_FIN_SCORE_THRESHOLD:
                result.append({"page": i + 1, "page_idx": i, "score": score, "hits": hits, "reasons": reasons})

    try:
        # v1.1.0 fast path
        if doc_cache is not None and doc_cache.pdfplumber_pdf is not None:
            _scan(doc_cache.pdfplumber_pdf)
            return result
        with pdfplumber.open(pdf_path) as pdf:
            _scan(pdf)
    except Exception as e:
        log.warning(f"[CLASSIFY] {e}")
    return result

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-N  M01_EXTRACT  PyMuPDF HQ PDF
# [VIA:ANCHOR:ANC-N:M01_EXTRACT]
# ════════════════════════════════════════════════════════════════════════════

# [VIA:AST-PY-000037:ANCHOR] extract_pages_pdf
def extract_pages_pdf(src: str, dst: str, page_indices: List[int],
                      dpi: int = P_DPI, quality: int = P_JPEG_QUALITY) -> str:
    """M10: Extract pages → HQ PDF."""
    if not fitz:
        raise RuntimeError("PyMuPDF (fitz) not installed")
    doc = fitz.open(src)
    out_doc = fitz.open()
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    for pi in page_indices:
        if pi >= len(doc):
            continue
        pg  = doc[pi]
        pix = pg.get_pixmap(matrix=mat, alpha=False)
        try:
            img_bytes = pix.tobytes("jpeg", quality)
        except Exception:
            img_bytes = pix.tobytes("png")
        np_ = out_doc.new_page(width=pg.rect.width, height=pg.rect.height)
        np_.insert_image(fitz.Rect(0, 0, pg.rect.width, pg.rect.height), stream=img_bytes)
    mkdir(str(Path(dst).parent))
    out_doc.save(dst, deflate=True, garbage=4)
    out_doc.close()
    doc.close()
    return dst

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-O  M01_OUTPUT  JSON / CSV + VRN v6.0 Schema
# [VIA:ANCHOR:ANC-O:M01_OUTPUT]
# ════════════════════════════════════════════════════════════════════════════

# [VIA:AST-PY-000038:ANCHOR] build_report_metadata
def build_report_metadata(
        fn: str, ticker: str, report_date: str,
        broker_info: Dict, rating_info: Dict, target_price: str,
        company_info: Dict, price_metrics: Dict,
        consensus: Dict) -> Dict[str, Any]:
    """
    VRN v6.0 §1 report_metadata 完整組合
    """
    yft = price_metrics.get("yfinance_ticker", f"{ticker}.TW")
    report_code = (
        f"{broker_info.get('abbr', 'UNK')}-"
        f"{ticker}-"
        f"{company_info.get('name', '')}-"
        f"{report_date.replace('-', '')}"
    )
    # Upside: Report TP 優先; 若無則用 consensus_target_mean
    upside_pct    = price_metrics.get("upside_pct")
    upside_source = price_metrics.get("upside_target_source", "")
    if upside_pct is None and consensus.get("consensus_target_mean") and price_metrics.get("adj_close"):
        try:
            ctm = float(consensus["consensus_target_mean"])
            adc = float(price_metrics["adj_close"])
            if ctm > 0 and adc > 0:
                upside_pct    = round((ctm - adc) / adc * 100, 2)
                upside_source = "YFinance"
        except Exception:
            pass

    return {
        # 1A: Report Identification
        "report_code":   report_code,
        "report_date":   report_date,
        "filename":      fn,
        # 1B: Company & Broker
        "ticker":        ticker,
        "tw_ticker":     ticker,
        "yfinance_ticker":    yft,
        "tw_yfinance_ticker": yft,
        "bloomberg_ticker":   f"{ticker} TT" if ticker else "",
        "tw_bloomberg_ticker":f"{ticker} TT" if ticker else "",
        "name":          company_info.get("name", ""),
        "name_en":       company_info.get("name_en", consensus.get("name_short", "")),
        "broker":        broker_info.get("full", ""),
        "broker_abbr":   broker_info.get("abbr", ""),
        # 1C: Rating
        "rating":        rating_info.get("rating", ""),
        "rating_cat":    rating_info.get("category", ""),
        "target_price":  float(target_price.replace(",", "")) if target_price else None,
        # 1D: Consensus (v6.0)
        "consensus_target_high":   consensus.get("consensus_target_high"),
        "consensus_target_low":    consensus.get("consensus_target_low"),
        "consensus_target_mean":   consensus.get("consensus_target_mean"),
        "consensus_target_median": consensus.get("consensus_target_median"),
        "consensus_rating":        consensus.get("consensus_rating", ""),
        "consensus_rating_mean":   consensus.get("consensus_rating_mean"),
        "analyst_count":           consensus.get("analyst_count"),
        "analyst_strong_buy":      consensus.get("analyst_strong_buy"),
        "analyst_buy":             consensus.get("analyst_buy"),
        "analyst_hold":            consensus.get("analyst_hold"),
        "analyst_sell":            consensus.get("analyst_sell"),
        "analyst_strong_sell":     consensus.get("analyst_strong_sell"),
        # 1E: Price & Upside
        "adj_close":               price_metrics.get("adj_close"),
        "adj_close_date":          price_metrics.get("adj_close_date", ""),
        "upside_pct":              upside_pct,
        "upside_target_source":    upside_source,
        "performance_pct_since_report": price_metrics.get("performance_pct_since_report"),
    }

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-P  M02_REPAIR  TextRepairEngine R1-R9
# [VIA:ANCHOR:ANC-P:M02_REPAIR]
# ════════════════════════════════════════════════════════════════════════════

_NOISE_RE          = re.compile(r"[\u0000-\u0008\u000b\u000e-\u001f]|[^\S\n]{3,}", re.UNICODE)
_BROKEN_SENT_RE    = re.compile(r"([^\u3002\uff01\uff1f\.!?；;])\n([^\s])")

# [VIA:AST-PY-000039:ANCHOR] TextRepairEngine
class TextRepairEngine:
    """M02 9-step repair pipeline R1-R9."""
    _OCR_NUM_RE = re.compile(r"(?<!\w)([lO\|])(?=[\d,])|(?<=[\d,])([lO\|])(?!\w)")

    # [VIA:AST-PY-000040:ANCHOR] TextRepairEngine.repair_text_records
    def repair_text_records(self, records: List[Dict]) -> List[Dict]:
        """R1~R7 applied to cover text records."""
        seen, result = set(), []
        for rec in records:
            text = rec.get("text", "")
            text = _NOISE_RE.sub(" ", text).strip()         # R1
            text = text.replace("\u3000", " ").replace("\u00a0", " ")  # R4 normalize
            text = re.sub(r" {2,}", " ", text)
            if not text or len(text) < 2:                   # R6 empty
                continue
            key = _hash8(text)
            if key in seen:                                  # R2 dedup
                continue
            seen.add(key)
            rec = dict(rec)
            rec["text"] = text
            result.append(rec)
        # R3: merge broken continuation lines
        merged, buf = [], None
        for rec in result:
            if buf is None:
                buf = copy.copy(rec)
                continue
            if (buf.get("type") in ("TXT", "KV") and rec.get("type") == "TXT"
                    and not re.search(r"[。！？；.!?]$", buf["text"])):
                buf["text"] = buf["text"].rstrip() + " " + rec["text"].lstrip()
            else:
                merged.append(buf)
                buf = copy.copy(rec)
        if buf:
            merged.append(buf)
        return merged

    # [VIA:AST-PY-000041:ANCHOR] TextRepairEngine.repair_table_rows
    def repair_table_rows(self, rows: List[Dict]) -> List[Dict]:
        """R7 (OCR numeric fix) on table row labels."""
        fixed = []
        for row in rows:
            label = row.get("label", "")
            label = self._OCR_NUM_RE.sub(
                lambda m: "1" if (m.group(1) or m.group(2)) in "lL|" else "0", label)
            if re.fullmatch(r"[\s\d年QEFe\-/]+", label):   # R5: skip pure header repeat
                continue
            fixed.append(dict(row, label=label.strip()))
        return fixed

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-Q  M02_CANONICAL  同義詞映射 + FinancialRow
# [VIA:ANCHOR:ANC-Q:M02_CANONICAL]
# ════════════════════════════════════════════════════════════════════════════

_CANONICAL_MAP: Dict[str, str] = {
    # Revenue
    "營業收入淨額":"revenue", "營業收入":"revenue", "收入":"revenue",
    "Revenue":"revenue", "Net Revenue":"revenue", "营收":"revenue",
    # COGS
    "營業成本":"cogs", "Cost of Revenue":"cogs", "COGS":"cogs",
    # Gross profit
    "營業毛利淨額":"gross_profit", "毛利":"gross_profit", "Gross Profit":"gross_profit",
    # OpEx
    "營業費用":"opex", "Operating Expense":"opex", "OpEx":"opex",
    # Operating income
    "營業淨利/損":"operating_income", "營業利益":"operating_income",
    "Operating Income":"operating_income", "EBIT":"operating_income",
    # Pretax
    "稅前淨利":"pretax_income", "Pretax Income":"pretax_income",
    # Net income
    "稅後淨利":"net_income", "Net Income":"net_income",
    "歸屬母公司淨利":"net_income_parent",
    # EPS
    "每股盈餘(元)":"eps", "每股盈餘":"eps", "EPS":"eps",
    # Margin
    "毛利率":"gross_margin", "Gross Margin":"gross_margin",
    "營業利益率":"operating_margin", "Operating Margin":"operating_margin",
    "淨利率":"net_margin", "Net Margin":"net_margin",
    # Valuation
    "本益比(P/E)":"pe_ratio", "P/E":"pe_ratio", "本益比":"pe_ratio",
    # Balance sheet
    "總資產":"total_assets", "Total Assets":"total_assets",
    "總負債":"total_liabilities", "Total Liabilities":"total_liabilities",
    "股東權益":"shareholders_equity", "Shareholders Equity":"shareholders_equity",
    # Per share
    "稀釋每股盈餘":"diluted_eps", "Diluted EPS":"diluted_eps",
    "每股淨值":"bvps", "Book Value Per Share":"bvps",
    "每股股利":"dps", "DPS":"dps",
}

# [VIA:AST-PY-000042:ANCHOR] canonicalize_label
def canonicalize_label(label: str) -> str:
    if label in _CANONICAL_MAP:
        return _CANONICAL_MAP[label]
    norm = re.sub(r"[\s/  ()  %]", "", label)
    for k, v in _CANONICAL_MAP.items():
        if re.sub(r"[\s/  ()  %]", "", k) == norm:
            return v
    for k, v in _CANONICAL_MAP.items():
        if k in label or label in k:
            return v
    return label.lower().replace(" ", "_")[:40]

# [VIA:AST-PY-000043:ANCHOR] classify_fin_type
def classify_fin_type(canonical: str) -> str:
    _IS = {"revenue","cogs","gross_profit","opex","operating_income",
           "pretax_income","net_income","net_income_parent","eps",
           "gross_margin","operating_margin","net_margin"}
    _BS = {"total_assets","total_liabilities","shareholders_equity",
           "bvps","diluted_eps","dps"}
    _VL = {"pe_ratio","forward_pe","pb_ratio","dividend_yield","beta"}
    if canonical in _IS: return "income_statement"
    if canonical in _BS: return "balance_sheet"
    if canonical in _VL: return "valuation"
    return "other"

@dataclass
# [VIA:AST-PY-000044:ANCHOR] FinancialRow
class FinancialRow:
    report_code: str
    ticker:      str
    report_date: str
    broker_abbr: str
    table_idx:   int
    label_raw:   str
    canonical:   str
    fin_type:    str
    period:      str
    value:       Optional[float]
    unit:        str = "mn_ntd"
    hash8:       str = ""

    def __post_init__(self):
        if not self.hash8:
            self.hash8 = _hash8(f"{self.report_code}:{self.canonical}:{self.period}")

# [VIA:AST-PY-000045:ANCHOR] restructure_tables
def restructure_tables(report_code: str, ticker: str, report_date: str,
                       broker_abbr: str, tables: List[Dict],
                       repair: TextRepairEngine) -> List[FinancialRow]:
    """Convert raw OCR tables → normalised FinancialRow list."""
    rows_out: List[FinancialRow] = []
    for ti, tbl in enumerate(tables):
        header   = tbl.get("header", [])
        raw_rows = repair.repair_table_rows(tbl.get("rows", []))
        periods: List[str] = []
        for h in header:
            p_tokens = re.findall(
                r"(?:20\d{2}[EeFf]?|[1-4]Q\d{2}[EeFf]?|\d{2}Q[1-4][EeFf]?)", h)
            if p_tokens:
                periods.extend(p_tokens)
            elif h.strip():
                periods.append(h.strip())
        for row in raw_rows:
            label  = row.get("label", "").strip()
            values = row.get("values", [])
            if not label or not values:
                continue
            canonical = canonicalize_label(label)
            fin_type  = classify_fin_type(canonical)
            for ci, val in enumerate(values):
                period = periods[ci] if ci < len(periods) else f"col{ci}"
                try:
                    num_val: Optional[float] = float(str(val).replace(",", "")) if val not in ("", None) else None
                except ValueError:
                    num_val = None
                rows_out.append(FinancialRow(
                    report_code=report_code, ticker=ticker,
                    report_date=report_date, broker_abbr=broker_abbr,
                    table_idx=ti, label_raw=label, canonical=canonical,
                    fin_type=fin_type, period=period, value=num_val))
    return rows_out

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-R  M02_VERIFY  交叉驗證 C01~C05
# [VIA:ANCHOR:ANC-R:M02_VERIFY]
# ════════════════════════════════════════════════════════════════════════════

# [VIA:AST-PY-000046:ANCHOR] verify_financial_rows
def verify_financial_rows(rows: List[FinancialRow], zero_error: bool = M02_ZERO_ERROR) -> Dict:
    """
    M02 Cross-Verify:
    C01  Revenue > 0
    C02  Gross profit = Revenue - COGS (within 2%)
    C03  No duplicate (report_code, canonical, period)
    C04  EPS in plausible range
    C05  Period strings valid
    """
    errors, warnings, passes = [], [], []

    def fail(code, detail):
        msg = f"{code}: {detail}"
        errors.append(msg)
        log.error(f"[M02 VERIFY] {msg}")
        if zero_error:
            raise RuntimeError(msg)

    def warn(code, detail):
        warnings.append(f"{code}: {detail}")

    def ok(code, detail=""):
        passes.append(f"{code}" + (f": {detail}" if detail else ""))

    if not rows:
        ok("C00", "no rows - skipped")
        return {"ok": True, "passes": passes, "errors": errors, "warnings": warnings,
                "n_pass": 0, "n_error": 0, "n_warn": 0}

    by_period: Dict[str, Dict[str, Optional[float]]] = collections.defaultdict(dict)
    seen_keys: set = set()

    for row in rows:
        if not re.fullmatch(r"(?:20\d{2}[EeFf]?|[1-4]Q\d{2}[EeFf]?|\d{2}Q[1-4][EeFf]?|col\d+)", row.period):
            warn("C05", f"unusual period={row.period!r}")
        key = (row.report_code, row.canonical, row.period)
        if key in seen_keys:
            warn("C03", f"duplicate {key}")
        seen_keys.add(key)
        if row.canonical == "eps" and row.value is not None:
            eps_lo, eps_hi = M02_EPS_RANGE
            if not (eps_lo <= row.value <= eps_hi):
                fail("C04", f"EPS={row.value} out of range")
        by_period[row.period][row.canonical] = row.value

    ok("C03", f"{len(seen_keys)} unique keys")

    rev_rows = [r for r in rows if r.canonical == "revenue" and r.value is not None]
    if rev_rows:
        neg = [r for r in rev_rows if r.value <= 0]
        if neg:
            fail("C01", f"revenue <= 0 in {[(r.period, r.value) for r in neg[:2]]}")
        else:
            ok("C01", f"all {len(rev_rows)} revenue rows > 0")

    for period, vals in by_period.items():
        rev  = vals.get("revenue")
        cogs = vals.get("cogs")
        gp   = vals.get("gross_profit")
        if rev is not None and cogs is not None and gp is not None:
            calc = rev - cogs
            diff = abs(calc - gp) / (abs(rev) + 1e-9)
            if diff > M02_GROSS_DIFF_MAX:
                fail("C02", f"period={period} gross_profit identity diff={diff:.1%}")
            else:
                ok("C02", f"period={period} gross_profit OK diff={diff:.4f}")

    return {
        "ok":      len(errors) == 0,
        "passes":  passes, "errors": errors, "warnings": warnings,
        "n_pass":  len(passes), "n_error": len(errors), "n_warn": len(warnings),
    }

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-S  M02_DB  SQLite WAL + Parquet
# [VIA:ANCHOR:ANC-S:M02_DB]
# ════════════════════════════════════════════════════════════════════════════

_M02_DDL = """
CREATE TABLE IF NOT EXISTS vrn_financial (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    report_code TEXT NOT NULL,
    ticker      TEXT, report_date TEXT, broker_abbr TEXT,
    table_idx   INTEGER, label_raw TEXT, canonical TEXT,
    fin_type    TEXT, period TEXT, value REAL,
    unit        TEXT DEFAULT 'mn_ntd',
    hash8       TEXT,
    inserted_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS vrn_metadata (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    report_code  TEXT NOT NULL UNIQUE,
    ticker       TEXT, report_date TEXT, broker_abbr TEXT, broker TEXT,
    rating       TEXT, rating_cat TEXT, target_price REAL,
    consensus_target_high   REAL, consensus_target_low    REAL,
    consensus_target_mean   REAL, consensus_target_median REAL,
    consensus_rating        TEXT, consensus_rating_mean   REAL,
    analyst_count           INTEGER,
    analyst_strong_buy      INTEGER, analyst_buy      INTEGER,
    analyst_hold            INTEGER, analyst_sell     INTEGER,
    analyst_strong_sell     INTEGER,
    adj_close REAL, adj_close_date TEXT,
    upside_pct REAL, upside_target_source TEXT,
    name TEXT, name_en TEXT,
    inserted_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS vrn_m02_verify (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    report_code TEXT NOT NULL,
    ok INTEGER, n_pass INTEGER, n_error INTEGER, n_warn INTEGER,
    errors_json TEXT, inserted_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS vrn_cv_results (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    report_code TEXT NOT NULL,
    cv_rule     TEXT, result TEXT, detail TEXT,
    inserted_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_fin_ticker  ON vrn_financial(ticker);
CREATE INDEX IF NOT EXISTS idx_fin_canon   ON vrn_financial(canonical);
CREATE INDEX IF NOT EXISTS idx_fin_period  ON vrn_financial(period);
CREATE INDEX IF NOT EXISTS idx_fin_report  ON vrn_financial(report_code);
CREATE INDEX IF NOT EXISTS idx_meta_ticker ON vrn_metadata(ticker);
"""

# [VIA:AST-PY-000047:ANCHOR] VRNDBWriter
class VRNDBWriter:
    """SQLite WAL-mode DB writer for financial + metadata + verify + CV."""
    def __init__(self, db_path: str):
        self.path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            c.executescript(_M02_DDL)

    def _conn(self):
        con = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA synchronous=NORMAL")
        con.execute("PRAGMA cache_size=-65536")
        con.execute("PRAGMA temp_store=MEMORY")
        return con

    def insert_financial(self, rows: List[FinancialRow]) -> None:
        data = [(r.report_code, r.ticker, r.report_date, r.broker_abbr,
                 r.table_idx, r.label_raw, r.canonical, r.fin_type,
                 r.period, r.value, r.unit, r.hash8)
                for r in rows]
        if data:
            with self._conn() as c:
                c.executemany(
                    "INSERT OR REPLACE INTO vrn_financial "
                    "(report_code,ticker,report_date,broker_abbr,table_idx,label_raw,"
                    "canonical,fin_type,period,value,unit,hash8) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    data)

    def insert_metadata(self, meta: Dict[str, Any]) -> None:
        cols = [
            "report_code","ticker","report_date","broker_abbr","broker",
            "rating","rating_cat","target_price",
            "consensus_target_high","consensus_target_low",
            "consensus_target_mean","consensus_target_median",
            "consensus_rating","consensus_rating_mean","analyst_count",
            "analyst_strong_buy","analyst_buy","analyst_hold",
            "analyst_sell","analyst_strong_sell",
            "adj_close","adj_close_date","upside_pct","upside_target_source",
            "name","name_en",
        ]
        vals = tuple(meta.get(c) for c in cols)
        qs = ",".join(["?"] * len(cols))
        with self._conn() as c:
            c.execute(
                f"INSERT OR REPLACE INTO vrn_metadata ({','.join(cols)}) VALUES ({qs})",
                vals)

    def insert_verify(self, report_code: str, ver: Dict) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO vrn_m02_verify (report_code,ok,n_pass,n_error,n_warn,errors_json) VALUES (?,?,?,?,?,?)",
                (report_code, int(ver["ok"]), ver["n_pass"], ver["n_error"], ver["n_warn"],
                 json.dumps(ver.get("errors", [])[:10])))

    def insert_cv_result(self, report_code: str, cv_rule: str, result: str, detail: str) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO vrn_cv_results (report_code,cv_rule,result,detail) VALUES (?,?,?,?)",
                (report_code, cv_rule, result, detail))

    def export_parquet(self, out_dir: str) -> bool:
        if pandas_mod is None:
            return False
        try:
            with self._conn() as c:
                df = pandas_mod.read_sql("SELECT * FROM vrn_financial", c)
            out = str(Path(out_dir) / "VRN_Financial.parquet")
            if polars_mod:
                polars_mod.from_pandas(df).write_parquet(out)
            elif pyarrow_mod:
                df.to_parquet(out, index=False, engine="pyarrow", compression="snappy")
            else:
                df.to_parquet(out, index=False, compression="snappy")
            log.info(f"[DB] Parquet → {out}")
            return True
        except Exception as e:
            log.warning(f"[DB] export_parquet: {e}")
            return False

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-T  CROSS_VALID  VRN v6.0 五條規則 CV-01~CV-05
# [VIA:ANCHOR:ANC-T:CROSS_VALID]
# ════════════════════════════════════════════════════════════════════════════

# [VIA:AST-PY-000048:ANCHOR] run_cross_validation
def run_cross_validation(report_code: str, meta: Dict[str, Any],
                         db_writer: Optional[VRNDBWriter] = None) -> Dict[str, Any]:
    """
    VRN v6.0 Section 3B Cross Validation Rules:
    CV-01  Report TP vs Consensus Mean  → diff > 20% WARN
    CV-02  Report rating_cat vs consensus_rating → MISMATCH
    CV-03  analyst_count < 3 → LOW_COVERAGE
    CV-04  Report TP 超出分析師區間 WARN
    CV-05  consensus_rating_mean > 3.5 but report = buy → FLAG
    """
    results: List[Dict] = []
    warnings: List[str] = []
    errors:   List[str] = []
    score = 100

    def _add(rule: str, outcome: str, detail: str):
        results.append({"rule": rule, "outcome": outcome, "detail": detail})
        if db_writer:
            try:
                db_writer.insert_cv_result(report_code, rule, outcome, detail)
            except Exception:
                pass
        if outcome == "WARN":
            warnings.append(f"{rule}: {detail}")
            nonlocal score
            score -= 5
        elif outcome == "MISMATCH":
            warnings.append(f"{rule}: {detail}")
            score -= 8
        elif outcome == "FLAG":
            warnings.append(f"{rule}: {detail}")
            score -= 6
        elif outcome == "LOW_COVERAGE":
            warnings.append(f"{rule}: {detail}")
            score -= 3

    # ── CV-01: TP vs consensus_target_mean ──────────────────────────────────
    tp   = meta.get("target_price")
    ctm  = meta.get("consensus_target_mean")
    if tp and ctm:
        try:
            diff_pct = abs(float(tp) - float(ctm)) / (abs(float(ctm)) + 1e-9) * 100
            detail   = f"Report TP({tp}) vs Consensus Mean({ctm}) diff={diff_pct:.1f}%"
            if diff_pct > CV01_TP_DIFF_WARN_PCT:
                _add("CV-01", "WARN", detail)
            else:
                _add("CV-01", "OK", detail)
        except Exception:
            pass
    else:
        _add("CV-01", "SKIP", "insufficient data")

    # ── CV-02: rating_cat vs consensus_rating ───────────────────────────────
    if CV02_RATING_MISMATCH:
        rcat = (meta.get("rating_cat") or "").lower().strip()
        crec = (meta.get("consensus_rating") or "").lower().strip()
        _RATING_EQUIV = {
            "buy":      {"buy", "strong_buy", "strongbuy", "outperform", "overweight"},
            "hold":     {"hold", "neutral", "market perform", "equalweight"},
            "sell":     {"sell", "underperform", "underweight", "strong_sell"},
            "not_rated":{"n/a", "not rated", "nr"},
        }
        if rcat and crec:
            equiv = _RATING_EQUIV.get(rcat, {rcat})
            # normalise consensus key
            crec_norm = crec.replace("-", "").replace(" ", "")
            match = any(crec_norm == e.replace("-", "").replace(" ", "") for e in equiv)
            if not match:
                _add("CV-02", "MISMATCH",
                     f"Report={rcat} vs Consensus={crec}")
            else:
                _add("CV-02", "OK",
                     f"Report={rcat} ~ Consensus={crec}")
        else:
            _add("CV-02", "SKIP", "rating data unavailable")

    # ── CV-03: analyst_count < 3 ────────────────────────────────────────────
    ac = meta.get("analyst_count")
    if ac is not None:
        if int(ac) < CV03_MIN_ANALYST_COUNT:
            _add("CV-03", "LOW_COVERAGE", f"analyst_count={ac}")
        else:
            _add("CV-03", "OK", f"analyst_count={ac}")
    else:
        _add("CV-03", "SKIP", "analyst_count not available")

    # ── CV-04: TP within high/low range ─────────────────────────────────────
    if CV04_TP_RANGE_CHECK:
        cth = meta.get("consensus_target_high")
        ctl = meta.get("consensus_target_low")
        if tp and cth and ctl:
            try:
                tp_f  = float(tp)
                hi, lo = float(cth), float(ctl)
                if tp_f > hi:
                    _add("CV-04", "WARN",
                         f"TP({tp_f}) > analyst high({hi})")
                elif tp_f < lo:
                    _add("CV-04", "WARN",
                         f"TP({tp_f}) < analyst low({lo})")
                else:
                    _add("CV-04", "OK",
                         f"TP({tp_f}) within [{lo}, {hi}]")
            except Exception:
                pass
        else:
            _add("CV-04", "SKIP", "insufficient range data")

    # ── CV-05: consensus_rating_mean > 3.5 but report = buy ─────────────────
    crm  = meta.get("consensus_rating_mean")
    rcat = (meta.get("rating_cat") or "").lower()
    if crm is not None and rcat:
        try:
            if float(crm) > CV05_MEAN_SELL_THRESH and rcat == "buy":
                _add("CV-05", "FLAG",
                     f"consensus_rating_mean={crm} > {CV05_MEAN_SELL_THRESH} but report=buy")
            else:
                _add("CV-05", "OK",
                     f"consensus_rating_mean={crm} consistent with report={rcat}")
        except Exception:
            pass
    else:
        _add("CV-05", "SKIP", "data not available")

    return {
        "score":    max(0, score),
        "warnings": warnings,
        "errors":   errors,
        "results":  results,
    }

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-U-EXT  v1.1.0  BATCH BUFFER + DUCK WRITER + SELF-VERIFY (NEW)
# [VIA:ANCHOR:ANC-U-EXT:V110_INFRA]
# ── 同 MDL002/004/005 v1.1.0 模式：worker push → 主執行緒一次 flush         ─
# ════════════════════════════════════════════════════════════════════════════

class MDL001SPBatchBuffer:
    """VRN-MDL001SP-CLS-002  P3 batch buffer (NEW v1.1.0)."""
    def __init__(self, batch_size: int = P_BATCH_SIZE):
        self.batch_size = batch_size
        self._rec_buf: List[Tuple] = []
        self._lock = threading.Lock()

    def push_result(self, rec: Dict):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        meta = (rec.get("record") or {}).get("report_metadata", {}) or {}
        row = (
            None,
            rec.get("filename","")[:200],
            rec.get("ticker",""),
            rec.get("report_date",""),
            meta.get("broker_abbr","") or "",
            rec.get("company","")[:200],
            rec.get("score",0),
            1 if rec.get("is_stock") else 0,
            rec.get("fin_rows",0),
            float(rec.get("cv_score",0.0) or 0.0),
            1 if rec.get("m02_ok") else 0,
            rec.get("error","")[:500] if rec.get("error") else "",
            ts,
        )
        with self._lock:
            self._rec_buf.append(row)

    def stats(self) -> Dict[str, int]:
        return {"rec": len(self._rec_buf)}

    def consume_all(self) -> List:
        with self._lock:
            r = self._rec_buf
            self._rec_buf = []
        return r


_DDL_DUCK_SP_REC = """
CREATE TABLE IF NOT EXISTS vrn_mdl001sp_results (
    id INTEGER, filename VARCHAR, ticker VARCHAR, report_date VARCHAR,
    broker_abbr VARCHAR, company VARCHAR,
    score INTEGER, is_stock INTEGER, fin_rows INTEGER,
    cv_score DOUBLE, m02_ok INTEGER,
    error VARCHAR, ts VARCHAR
);
"""


class MDL001SPDuckWriter:
    """VRN-MDL001SP-CLS-003  DuckDB primary writer (NEW v1.1.0)."""
    def __init__(self, db_path: str):
        if not DUCKDB_OK_v110:
            raise RuntimeError("duckdb not available")
        self.db_path = db_path
        self._con = duckdb_lib.connect(db_path)
        self._con.execute(_DDL_DUCK_SP_REC)

    def flush(self, rec_rows: List) -> Dict[str, int]:
        n = 0
        try:
            self._con.execute("BEGIN TRANSACTION")
            if rec_rows:
                self._con.executemany(
                    "INSERT INTO vrn_mdl001sp_results VALUES "
                    "(?,?,?,?,?,?,?,?,?,?,?,?,?)", rec_rows)
                n = len(rec_rows)
            self._con.execute("COMMIT")
        except Exception as e:
            try: self._con.execute("ROLLBACK")
            except: pass
            log.error(f"[MDL001SP] DuckDB flush fail: {e}"); raise
        return {"rec": n}

    def export_parquet_polars(self, out_dir: str) -> Optional[str]:
        out_path = str(Path(out_dir) / "VRN_MDL001SP_Results.parquet")
        try:
            self._con.execute(
                f"COPY (SELECT * FROM vrn_mdl001sp_results) "
                f"TO '{out_path}' (FORMAT PARQUET, COMPRESSION ZSTD)")
            return out_path
        except Exception as e:
            log.warning(f"[MDL001SP] DuckDB→parquet fail: {e}"); return None

    def export_csv_polars(self, out_dir: str) -> Optional[str]:
        out_path = str(Path(out_dir) / "VRN_MDL001SP_Results.csv")
        if POLARS_OK_v110:
            try:
                rows = self._con.execute("SELECT * FROM vrn_mdl001sp_results").fetchall()
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
                log.debug(f"[MDL001SP] polars-fetchall csv fail ({e}), DuckDB native")
        try:
            self._con.execute(
                f"COPY (SELECT * FROM vrn_mdl001sp_results) "
                f"TO '{out_path}' (HEADER, DELIMITER ',')")
            data = Path(out_path).read_bytes()
            Path(out_path).write_bytes(b"\xef\xbb\xbf" + data)
            return out_path
        except Exception as e:
            log.warning(f"[MDL001SP] csv export fail: {e}"); return None

    def close(self):
        try: self._con.close()
        except: pass


class MDL001SPSelfVerifier:
    """VRN-MDL001SP-CLS-004  P6 4-phase debug chain (NEW v1.1.0)."""
    def __init__(self, cfg: Dict, run_summary: Dict, out_dir: str):
        self.cfg = cfg; self.run_summary = run_summary; self.out_dir = out_dir
        self.checks: List[Dict] = []

    def _add(self, phase, name, ok, detail=""):
        self.checks.append({"phase":phase,"name":name,"ok":bool(ok),"detail":detail})

    def run(self) -> Dict:
        # P1: imports + locked regex
        self._add("1/4", "Module version 1.1.0", __version__ == "1.1.0", __version__)
        try:
            self._add("1/4", "TW_TICKER_BASE locked",
                      _TW_TICKER_BASE == r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})",
                      _TW_TICKER_BASE[:60])
        except Exception:
            self._add("1/4", "TW_TICKER_BASE locked", False, "_TW_TICKER_BASE not found")
        self._add("1/4", "polars available", POLARS_OK_v110, "")
        self._add("1/4", "duckdb available", DUCKDB_OK_v110, "")
        self._add("1/4", "fitz available",   fitz is not None, "")
        self._add("1/4", "pdfplumber available", pdfplumber is not None, "")

        # P2: new infra wiring
        self._add("2/4", "MDL001SPDocCache exists",
                  "MDL001SPDocCache" in globals(), "")
        self._add("2/4", "MDL001SPBatchBuffer exists",
                  "MDL001SPBatchBuffer" in globals(), "")
        self._add("2/4", "MDL001SPDuckWriter exists",
                  "MDL001SPDuckWriter" in globals(), "")
        self._add("2/4", "detect_fin_pages accepts doc_cache",
                  "doc_cache" in detect_fin_pages.__code__.co_varnames, "")
        try:
            self._add("2/4", "_extract_cover_text accepts doc_cache",
                      "doc_cache" in VRNIntegratedPipeline._extract_cover_text.__code__.co_varnames, "")
            self._add("2/4", "_extract_typed_pages accepts doc_cache",
                      "doc_cache" in VRNIntegratedPipeline._extract_typed_pages.__code__.co_varnames, "")
            self._add("2/4", "_typed_to_tables accepts doc_cache",
                      "doc_cache" in VRNIntegratedPipeline._typed_to_tables.__code__.co_varnames, "")
        except Exception as e:
            self._add("2/4", "method signature check", False, str(e))

        # P3: DB
        duck_p = Path(self.out_dir) / "VRN_MDL001SP.duckdb"
        self._add("3/4", "DuckDB file exists", duck_p.exists(),
                  f"size={duck_p.stat().st_size if duck_p.exists() else 0}")
        if duck_p.exists() and DUCKDB_OK_v110:
            try:
                con = duckdb_lib.connect(str(duck_p), read_only=True)
                tbls = {t[0] for t in con.execute(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema='main'").fetchall()}
                con.close()
                self._add("3/4", "DuckDB schema vrn_mdl001sp_results",
                          "vrn_mdl001sp_results" in tbls, str(sorted(tbls)))
            except Exception as e:
                self._add("3/4", "DuckDB schema vrn_mdl001sp_results", False, str(e))

        # P4: outputs
        for fn in ("VRN_MDL001SP_VerifySummary.json",
                   "VRN_MDL001SP_Results.parquet",
                   "VRN_MDL001SP_Results.csv"):
            p = Path(self.out_dir) / fn
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


def build_self_verify_html_mdl001sp(verify_result: Dict, run_summary: Dict) -> str:
    """VIA Visual Lock self-verify HTML (NEW v1.1.0)."""
    cls = verify_result.get("classification","?")
    cls_color = {"READY":"#439a9a","NEAR-READY":"#e0b020",
                 "NOT-READY":"#c83030"}.get(cls,"#666")
    cls_emoji = {"READY":"✓","NEAR-READY":"⚠","NOT-READY":"✗"}.get(cls,"?")

    by_phase: Dict[str,List[Dict]] = {}
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
        f"$ VRN_MDL001_StockReportPipeline v{__version__} self-verification",
        f"  generated      : {verify_result.get('generated','-')}",
        f"  classification : {cls} {cls_emoji}",
        f"  checks         : {verify_result.get('pass',0)}/{verify_result.get('total',0)} pass",
        "",
        "$ pipeline summary",
        f"  total files    : {run_summary.get('total','-')}",
        f"  stock / non    : {run_summary.get('n_stock','-')} / {run_summary.get('n_non','-')}",
        f"  ok / errors    : {run_summary.get('n_ok','-')} / {run_summary.get('n_err','-')}",
    ]
    term_html = "\n".join(sum_lines)

    html = f"""<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="UTF-8">
<title>VRN MDL001 StockReportPipeline v{__version__} · Self-Verification · {cls}</title>
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
.ck-name{{font-weight:500;min-width:220px}}
.ck-ok{{color:#439a9a;font-weight:600;min-width:80px}}
.ck-fail{{color:#c83030;font-weight:700;min-width:80px}}
.ck-detail{{color:#666;font-family:'DM Mono',monospace;font-size:10px}}
.foot{{margin-top:24px;color:#999;font-family:'DM Mono',monospace;font-size:9px;text-align:right}}
</style></head><body>
<div class="hdr"><h1>VRN MDL001 · StockReportPipeline v{__version__}<span class="cls-badge">{cls}</span></h1>
<div class="sub">VeritasReportNova · 4-Phase Self-Verification · {time.strftime("%Y-%m-%d %H:%M:%S")}</div></div>
<div class="cd"><div class="cd-h">RUN SUMMARY</div><div class="cd-b"><div class="tm">{term_html}</div></div></div>
{"".join(phase_html)}
<div class="foot">Module: {__module_id__} · Spec: {__spec_version__} · v{__version__}</div>
</body></html>"""
    return html


# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-U  PIPELINE  VRNIntegratedPipeline
# [VIA:ANCHOR:ANC-U:PIPELINE]
# ════════════════════════════════════════════════════════════════════════════

# [VIA:AST-PY-000049:ANCHOR] VRNIntegratedPipeline
class VRNIntegratedPipeline:
    """
    M01 + M02 + M03 全整合流水線
    輸出 VRN v6.0 完整 JSON schema (含 report_metadata + financial_data + validation)
    """

    # [VIA:AST-PY-000050:ANCHOR] VRNIntegratedPipeline.__init__
    def __init__(self, cfg: Optional[Dict] = None):
        self.cfg        = cfg or {}
        self.repair_m01 = SentenceRepairEngine()
        self.repair_m02 = TextRepairEngine()
        self.cache      = VIACache(
            enabled=self.cfg.get("ENABLE_CACHE", P_ENABLE_CACHE))
        self.governor   = HardwareGovernor()
        self.db         = VRNDBWriter(self.cfg.get("DB_PATH", P_DB_PATH))
        self.ll_db      = LessonLearnedDB(
            self.cfg.get("DB_PATH", P_DB_PATH).replace(".db", "_ll.db"))
        self.all_results: List[Dict] = []
        self.errors:      List[Dict] = []

        # ── v1.1.0: BatchBuffer + DuckDB primary ───────────────────────────
        self.buffer: Optional[MDL001SPBatchBuffer] = None
        self.duck:   Optional[MDL001SPDuckWriter]  = None
        if self.cfg.get("USE_DUCKDB_V11", P_USE_DUCKDB_V11) and DUCKDB_OK_v110:
            try:
                self.buffer = MDL001SPBatchBuffer(
                    batch_size=self.cfg.get("BATCH_SIZE_V11", P_BATCH_SIZE))
                duck_path = str(Path(self.cfg.get("OUTPUT_DIR", P_OUTPUT_DIR))
                                / "VRN_MDL001SP.duckdb")
                Path(duck_path).parent.mkdir(parents=True, exist_ok=True)
                self.duck = MDL001SPDuckWriter(duck_path)
                log.info(f"[MDL001SP] DuckDB primary writer ready → {duck_path}")
            except Exception as e:
                log.warning(f"[MDL001SP] DuckDB init fail ({e}), buffer disabled")
                self.buffer = None
                self.duck = None

    # ── Phase helper: extract cover text ─────────────────────────────────────
    # [VIA:AST-PY-000051:ANCHOR] VRNIntegratedPipeline._extract_cover_text
    def _extract_cover_text(self, pdf_path: str,
                             doc_cache: Optional["MDL001SPDocCache"] = None) -> str:
        if not pdfplumber:
            return ""
        # v1.1.0 fast path
        if doc_cache is not None and doc_cache.pdfplumber_pdf is not None:
            try:
                pdf = doc_cache.pdfplumber_pdf
                pages = pdf.pages[:3]
                return " ".join((p.extract_text() or "") for p in pages)
            except Exception:
                pass
        try:
            with pdfplumber.open(pdf_path) as pdf:
                pages = pdf.pages[:3]
                return " ".join((p.extract_text() or "") for p in pages)
        except Exception:
            return ""

    # ── Phase helper: extract typed pages ────────────────────────────────────
    # [VIA:AST-PY-000052:ANCHOR] VRNIntegratedPipeline._extract_typed_pages
    def _extract_typed_pages(self, pdf_path: str,
                              page_indices: List[int],
                              doc_cache: Optional["MDL001SPDocCache"] = None) -> List[Dict]:
        if not pdfplumber:
            return []
        results = []
        # v1.1.0 fast path
        if doc_cache is not None and doc_cache.pdfplumber_pdf is not None:
            try:
                pdf = doc_cache.pdfplumber_pdf
                for pi in page_indices:
                    if pi >= len(pdf.pages):
                        continue
                    typed = self.repair_m01.repair_typed(pdf.pages[pi])
                    for item in typed:
                        item["page"] = pi + 1
                    results.extend(typed)
                return results
            except Exception as e:
                log.warning(f"[EXTRACT] typed pages (cache): {e}")
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for pi in page_indices:
                    if pi >= len(pdf.pages):
                        continue
                    typed = self.repair_m01.repair_typed(pdf.pages[pi])
                    for item in typed:
                        item["page"] = pi + 1
                    results.extend(typed)
        except Exception as e:
            log.warning(f"[EXTRACT] typed pages: {e}")
        return results

    # ── Core: process one PDF ─────────────────────────────────────────────────
    # [VIA:AST-PY-000053:ANCHOR] VRNIntegratedPipeline._process_one
    def _process_one(self, pdf_path: str) -> Dict[str, Any]:
        fn          = Path(pdf_path).name
        t0          = time.time()
        result: Dict[str, Any] = {
            "filename":     fn,
            "is_stock":     False,
            "ticker":       "",
            "report_date":  "",
            "score":        0,
            "error":        "",
        }

        # v1.1.0: open PDF ONCE via DocCache, share across all 4 hot extractors
        use_cache = bool(getattr(self.cfg, "use_doc_cache",
                                  self.cfg.get("use_doc_cache", P_USE_DOC_CACHE)
                                  if isinstance(self.cfg, dict) else P_USE_DOC_CACHE))
        cache_ctx = MDL001SPDocCache(pdf_path) if use_cache else None
        if cache_ctx is not None:
            try: cache_ctx.__enter__()
            except Exception: cache_ctx = None

        try:
            # ── Phase 1: Filename pre-parse ──────────────────────────────────
            fn_stem   = Path(pdf_path).stem
            fn_ticker = detect_ticker(fn_stem, {"YEAR_EXCLUSION": P_YEAR_EXCLUSION})
            fn_broker = detect_broker(fn_stem)
            fn_date   = detect_date(fn_stem)

            # ── Phase 2: Cover text extraction (v1.1.0 cache) ────────────────
            cover_text = self._extract_cover_text(pdf_path, doc_cache=cache_ctx)

            # ── Phase 3: Classification ──────────────────────────────────────
            ticker = fn_ticker or detect_ticker(cover_text, {"YEAR_EXCLUSION": P_YEAR_EXCLUSION})
            is_stock, score, reasons = is_stock_report(fn, cover_text, ticker)
            result["score"]    = score
            result["is_stock"] = is_stock

            if not is_stock:
                result["classification"] = {"document_type": "NON_STOCK", "reasons": reasons}
                return result

            # ── Phase 4: M01 detection ───────────────────────────────────────
            broker_info  = fn_broker if fn_broker["abbr"] else detect_broker(cover_text)
            rating_info  = detect_rating(cover_text)
            report_date  = fn_date or detect_date(cover_text)
            target_price = detect_tp(cover_text)
            company_info = resolve_company_name(ticker, cover_text, fn)

            # ── Phase 5: Financial page detection (v1.1.0 cache) ─────────────
            fin_pages    = detect_fin_pages(pdf_path, doc_cache=cache_ctx)
            if not fin_pages and not P_ALLOW_NO_FIN_PAGES:
                result["is_stock"] = False
                result["classification"] = {"document_type": "NO_FIN_PAGES"}
                return result

            # ── Phase 6: PDF extraction (cover + fin pages, v1.1.0 cache) ────
            cover_typed    = self._extract_typed_pages(pdf_path, [0], doc_cache=cache_ctx)
            fin_page_idxs  = [fp["page_idx"] for fp in fin_pages]
            fin_typed_pages = self._extract_typed_pages(pdf_path, fin_page_idxs, doc_cache=cache_ctx)

            # ── Phase 7: Price metrics (yfinance) ────────────────────────────
            price_metrics = get_price_metrics(ticker, report_date, target_price)
            yft           = price_metrics.get("yfinance_ticker", f"{ticker}.TW")

            # ── Phase 8: Consensus block (v6.0) ─────────────────────────────
            consensus = build_consensus_block(ticker, yft)

            # ── Phase 9: build report_metadata (v6.0 §1 full) ───────────────
            meta = build_report_metadata(
                fn=fn, ticker=ticker, report_date=report_date,
                broker_info=broker_info, rating_info=rating_info,
                target_price=target_price, company_info=company_info,
                price_metrics=price_metrics, consensus=consensus)

            # ── Phase 10: M02 table restructure (v1.1.0 cache) ───────────────
            # Stage-1 pdfplumber direct + Stage-2 typed fallback
            raw_tables = self._typed_to_tables(
                cover_typed + fin_typed_pages, pdf_path=pdf_path,
                doc_cache=cache_ctx)
            report_code = meta["report_code"]
            fin_rows = restructure_tables(
                report_code=report_code,
                ticker=ticker, report_date=report_date,
                broker_abbr=broker_info.get("abbr", ""),
                tables=raw_tables, repair=self.repair_m02)

            # ── Phase 11: M02 verify (C01~C05) ───────────────────────────────
            try:
                ver_result = verify_financial_rows(fin_rows, zero_error=False)
            except RuntimeError as ve:
                ver_result = {"ok": False, "passes": [], "errors": [str(ve)],
                              "warnings": [], "n_pass": 0, "n_error": 1, "n_warn": 0}

            # ── Phase 12: CV-01~CV-05 (v6.0) ─────────────────────────────────
            cv_result = run_cross_validation(
                report_code=report_code, meta=meta, db_writer=self.db)

            # ── Phase 13: Lesson Learned ──────────────────────────────────────
            if not ver_result["ok"] or cv_result["score"] < 60:
                self.ll_db.log_lesson(
                    error_type="LOW_QUALITY",
                    report_code=report_code,
                    content=f"ver_ok={ver_result['ok']} cv_score={cv_result['score']}",
                    confidence=cv_result["score"] / 100)

            # ── Phase 14: DB writes ───────────────────────────────────────────
            self.db.insert_metadata(meta)
            self.db.insert_financial(fin_rows)
            self.db.insert_verify(report_code, ver_result)

            # ── Phase 15: build full v6.0 output record ───────────────────────
            # Compute derived financial_data from fin_rows
            fin_data = self._build_financial_data(fin_rows, consensus)

            full_record = {
                "extraction_info": {
                    "extraction_time": datetime.now().isoformat(),
                    "vrn_version":     __spec_version__,
                    "mode":            "equity_report",
                    "module_version":  __version__,
                    "elapsed_sec":     round(time.time() - t0, 2),
                },
                "report_metadata": meta,
                "financial_data":  fin_data,
                "validation": {
                    "score":         cv_result["score"],
                    "m02_verify":    ver_result,
                    "cv_results":    cv_result["results"],
                    "warnings":      cv_result["warnings"] + ver_result.get("warnings", []),
                    "errors":        ver_result.get("errors", []),
                    "n_fin_rows":    len(fin_rows),
                },
            }

            result.update({
                "ticker":       ticker,
                "report_date":  report_date,
                "company":      company_info.get("name", ""),
                "company_en":   company_info.get("name_en", ""),
                "record":       full_record,
                "fin_rows":     len(fin_rows),
                "cv_score":     cv_result["score"],
                "m02_ok":       ver_result["ok"],
                "is_stock":     True,
            })

        except Exception as e:
            result["error"] = str(e)
            log.error(f"[PIPELINE] {fn}: {e}\n{traceback.format_exc()}")
            self.ll_db.log_lesson("EXCEPTION", fn, str(e)[:200])
        finally:
            # v1.1.0: close DocCache regardless of path
            if cache_ctx is not None:
                try: cache_ctx.__exit__(None, None, None)
                except: pass

        return result

    # [VIA:AST-PY-000054:ANCHOR] VRNIntegratedPipeline._typed_to_tables
    def _typed_to_tables(self, typed_items: List[Dict],
                          pdf_path: str = "",
                          doc_cache: Optional["MDL001SPDocCache"] = None) -> List[Dict]:
        """
        Stage-1: pdfplumber direct table extraction (最準確, 有格線時用)
        Stage-2: typed TBL rows grouping fallback (無格線 / 掃描版)
        v1.1.0: doc_cache fast path — reuses opened pdfplumber handle.
        """
        # ── Stage-1: pdfplumber direct extract (高精度路徑) ─────────────────
        if pdf_path and pdfplumber:
            direct_tables: List[Dict] = []

            def _scan_pages(pdf) -> None:
                for page in pdf.pages[:P_MAX_FIN_PAGES + 2]:
                    for tbl in (page.extract_tables() or []):
                        if not tbl or len(tbl) < 2:
                            continue
                        header_row = [str(h or "").strip() for h in tbl[0]]
                        periods    = [h for h in header_row[1:]
                                      if re.search(r"(?:20\d{2}[EeFf]?|[1-4]Q\d{2})", h)]
                        rows: List[Dict] = []
                        for r in tbl[1:]:
                            label = str(r[0] or "").strip() if r else ""
                            if not label:
                                continue
                            vals = [str(v or "").strip() for v in r[1:]]
                            if any(re.search(r"[\d,.\-]", v) for v in vals):
                                rows.append({"label": label, "values": vals})
                        if rows:
                            direct_tables.append({
                                "header": periods if periods else header_row[1:],
                                "rows":   rows,
                            })

            try:
                # v1.1.0 fast path: reuse cached pdfplumber handle
                if doc_cache is not None and doc_cache.pdfplumber_pdf is not None:
                    _scan_pages(doc_cache.pdfplumber_pdf)
                else:
                    with pdfplumber.open(pdf_path) as pdf:
                        _scan_pages(pdf)
                if direct_tables:
                    return direct_tables
            except Exception:
                pass

        # ── Stage-2: typed TBL rows grouping fallback ────────────────────────
        tables: List[Dict] = []
        cur_rows: List[Dict] = []
        for item in typed_items:
            if item.get("line_type") == "TBL":
                txt = item.get("text", "").strip()
                if not txt:
                    continue
                parts = re.split(r"\s{2,}|\t", txt)
                if len(parts) >= 2:
                    cur_rows.append({"label": parts[0], "values": parts[1:]})
                elif len(parts) == 1 and re.search(r"[\d,.\-]{2,}", txt):
                    # 單一數值行: 嘗試空格分割後作為純數值行
                    tokens = txt.split()
                    if len(tokens) >= 2:
                        cur_rows.append({"label": tokens[0], "values": tokens[1:]})
            else:
                if len(cur_rows) >= 2:
                    tables.append({"header": [], "rows": cur_rows})
                cur_rows = []
        if len(cur_rows) >= 2:
            tables.append({"header": [], "rows": cur_rows})
        return tables

    # [VIA:AST-PY-000055:ANCHOR] VRNIntegratedPipeline._build_financial_data
    def _build_financial_data(self, fin_rows: List[FinancialRow],
                               consensus: Dict[str, Any]) -> Dict[str, Any]:
        """Build VRN v6.0 §2 financial_data from fin_rows + consensus.
        Period priority: estimate (E/F suffix) < historical; latest year wins.
        """
        # Collect all values per canonical; prefer historical over estimates,
        # and latest year over earlier years.
        by_canon: Dict[str, Optional[float]] = {}
        by_canon_period: Dict[str, str] = {}
        src_tags: Dict[str, str] = {}

        def _period_rank(p: str) -> Tuple[int, int]:
            """Lower rank = lower priority."""
            is_est = int(bool(re.search(r"[EeFf]$", p)))   # 0=hist, 1=est
            m = re.search(r"(\d{4})", p)
            yr = int(m.group(1)) if m else 0
            return (1 - is_est, yr)  # hist(1) > est(0), later yr > earlier

        for row in fin_rows:
            if row.value is None:
                continue
            canon = row.canonical
            period = row.period or ""
            cur_period = by_canon_period.get(canon, "")
            # Replace if: no existing value, or new period is higher priority
            if canon not in by_canon or _period_rank(period) > _period_rank(cur_period):
                by_canon[canon]        = row.value
                by_canon_period[canon] = period
                src_tags[canon]        = "RP"

        def g(key: str, api_key: Optional[str] = None) -> Optional[float]:
            v = by_canon.get(key)
            if v is not None:
                return v
            if api_key:
                return consensus.get(api_key)
            return None

        rev   = g("revenue")
        cogs  = g("cogs")
        gp    = g("gross_profit")
        if gp is None and rev and cogs:
            gp = rev - cogs
        oi    = g("operating_income")
        ni    = g("net_income")

        def safe_div(a, b) -> Optional[float]:
            try:
                return round(float(a) / float(b), 4) if a and b and float(b) != 0 else None
            except Exception:
                return None

        return {
            "income_statement": {
                "revenue":            rev,
                "cost_of_revenue":    g("cogs"),
                "gross_profit":       gp,
                "operating_expenses": g("opex"),
                "operating_income":   oi,
                "pretax_income":      g("pretax_income"),
                "net_income":         ni,
                "_source": {k: src_tags.get(k, "RP") for k in
                            ["revenue","cost_of_revenue","gross_profit","net_income"]},
            },
            "ratio_analysis": {
                "gross_margin":     safe_div(gp, rev),
                "operating_margin": safe_div(oi, rev),
                "net_margin":       safe_div(ni, rev),
                "roe":  None,
                "roa":  None,
            },
            "balance_sheet": {
                "total_assets":       g("total_assets"),
                "total_liabilities":  g("total_liabilities"),
                "shareholders_equity":g("shareholders_equity"),
            },
            "per_share_analysis": {
                "diluted_eps": g("diluted_eps") or g("eps"),
                "basic_eps":   g("eps"),
                "bvps":        g("bvps"),
                "dps":         g("dps"),
                "_source": {"diluted_eps": src_tags.get("eps", "RP"),
                            "bvps": src_tags.get("bvps", "API")},
            },
            "valuation": {
                "pe_ratio":       g("pe_ratio", "pe_ratio"),
                "forward_pe":     consensus.get("forward_pe"),
                "pb_ratio":       consensus.get("pb_ratio"),
                "dividend_yield": consensus.get("dividend_yield"),
                "beta":           consensus.get("beta"),
            },
        }

    # ── Main run ──────────────────────────────────────────────────────────────
    # [VIA:AST-PY-000056:ANCHOR] VRNIntegratedPipeline.run
    def run(self) -> Dict[str, Any]:
        cfg      = self.cfg
        t_start  = time.time()
        in_dir   = cfg.get("IN_DIR",    P_IN_DIR)
        pdf_temp = cfg.get("PDF_TEMP",  P_PDF_TEMP)
        out_dir  = cfg.get("OUTPUT_DIR",P_OUTPUT_DIR)
        for d in (in_dir, pdf_temp, out_dir):
            mkdir(d)

        # Accelerator init
        workers  = accel_init_full(cfg)
        gov      = self.governor.status(cfg)
        adj_w    = min(workers, gov["adj_workers"])

        # ── Banner ───────────────────────────────────────────────────────────
        print()
        print("═" * 76)
        print(f"  VRN MDL001 StockReportPipeline v{__version__}  Spec:{__spec_version__}")
        print(f"  M01 Extract + M02 Verify + M03 Accel  Workers:{adj_w}  Gov:{gov['name']}")
        print(f"  IN  → {in_dir}")
        print(f"  OUT → {out_dir}")
        print("═" * 76)

        # ── Find PDFs ────────────────────────────────────────────────────────
        pdfs = sorted(str(p) for p in Path(in_dir).glob("*.pdf") if p.is_file())
        if not pdfs:
            log.warning("[RUN] No PDFs found in input dir")
            return {"status": "no_files", "elapsed": 0}
        log.info(f"[RUN] {len(pdfs)} PDFs found")

        # ── Batch process (L6 pipeline) ───────────────────────────────────────
        batch_size = cfg.get("BATCH_SIZE", P_BATCH_SIZE)
        stock_count = 0

        for bi in range(0, len(pdfs), batch_size):
            batch = pdfs[bi: bi + batch_size]
            log.info(f"[BATCH] {bi//batch_size+1}  ({len(batch)} files)  Gov:{gov['name']}")
            with ThreadPoolExecutor(max_workers=adj_w) as ex:
                futs = {ex.submit(self._process_one, fp): fp for fp in batch}
                for fut in as_completed(futs):
                    fp = futs[fut]
                    fn = Path(fp).name
                    try:
                        res = fut.result()
                        self.all_results.append(res)
                        # v1.1.0: push every result to buffer (low-lock)
                        if self.buffer is not None:
                            try: self.buffer.push_result(res)
                            except Exception as e:
                                log.warning(f"[MDL001SP] buffer push: {e}")
                        if res.get("is_stock"):
                            stock_count += 1
                            log.info(
                                f"  ✅ [{res.get('ticker','?')}] "
                                f"{res.get('company','')}  {fn[:35]}  "
                                f"FinRows:{res.get('fin_rows',0)}  "
                                f"CV:{res.get('cv_score','?')}  "
                                f"M02:{'OK' if res.get('m02_ok') else 'ERR'}")
                        else:
                            log.info(f"  ⬜ {fn[:45]}  Score:{res.get('score',0)}")
                    except Exception as e:
                        self.errors.append({"file": fn, "error": str(e)})
                        log.error(f"  ❌ {fn}: {e}")
            # Governor inter-batch
            gov = self.governor.status(cfg)
            if gov["level"] >= 4:
                adj_w = max(1, gov["adj_workers"])
                time.sleep(0.5)

        elapsed = round(time.time() - t_start, 2)

        # ── v1.1.0: single-thread flush DuckDB after all batches done ────────
        flush_stats = {"rec": 0}
        if self.buffer and self.duck:
            r_rows = self.buffer.consume_all()
            log.info(f"[MDL001SP] Buffer drain: rec={len(r_rows)}")
            try:
                flush_stats = self.duck.flush(r_rows)
                log.info(f"[MDL001SP] DuckDB flush: {flush_stats}")
            except Exception as e:
                log.warning(f"[MDL001SP] DuckDB flush fail: {e}")

        # v1.1.0: polars-direct exports
        if self.duck:
            try:
                self.duck.export_parquet_polars(out_dir)
                self.duck.export_csv_polars(out_dir)
            except Exception as e:
                log.warning(f"[MDL001SP] polars export fail: {e}")

        # ── Phase D: Output ───────────────────────────────────────────────────
        stock_results = [r for r in self.all_results if r.get("is_stock")]

        # Consolidated JSON (VRN v6.0 schema)
        consolidated = {
            "meta": {
                "module": __module_id__, "version": __version__,
                "spec": __spec_version__,
                "timestamp": datetime.now().isoformat(),
                "input_dir": in_dir, "output_dir": out_dir,
                "total_pdfs": len(pdfs), "stock_reports": stock_count,
                "elapsed_sec": elapsed,
            },
            "reports": [r.get("record", {}) for r in stock_results if r.get("record")],
        }
        json_path = str(Path(out_dir) / "VRN_Integrated_Reports.json")
        _jwrite(json_path, consolidated)
        log.info(f"[OUTPUT] JSON → {json_path}  ({stock_count} reports)")

        # CSV summary
        csv_path = str(Path(out_dir) / "VRN_Summary.csv")
        self._write_summary_csv(csv_path, stock_results)
        log.info(f"[OUTPUT] CSV  → {csv_path}")

        # Parquet
        self.db.export_parquet(out_dir)

        # HTML report
        if cfg.get("HTML_REPORT", P_HTML_REPORT):
            html_path = str(Path(out_dir) / "VRN_Report.html")
            self._write_html(html_path, consolidated, elapsed, adj_w, gov)
            log.info(f"[OUTPUT] HTML → {html_path}  (saved, not opened)")

        print()
        print("═" * 76)
        print(f"  ✅ DONE  {stock_count}/{len(pdfs)} stock reports  elapsed={elapsed}s")
        print("═" * 76)

        # ── v1.1.0: VerifySummary JSON + 4-phase Self-Verify HTML ────────────
        n_err  = len(self.errors)
        n_ok   = stock_count
        n_non  = len(self.all_results) - stock_count
        verify = {
            "module":        __module_id__,
            "version":       __version__,
            "spec":          __spec_version__,
            "generated":     time.strftime("%Y-%m-%d %H:%M:%S"),
            "total":         len(pdfs),
            "n_stock":       stock_count,
            "n_non":         n_non,
            "n_ok":          n_ok,
            "n_err":         n_err,
            "elapsed_sec":   elapsed,
            "flush_stats":   flush_stats,
            "fail_details":  self.errors,
        }
        _jwrite(str(Path(out_dir) / "VRN_MDL001SP_VerifySummary.json"), verify)

        # Close DuckDB BEFORE self-verify (avoid read-only conflict)
        if self.duck:
            try: self.duck.close()
            except: pass

        sv_html_path = None
        if cfg.get("SELF_VERIFY_V11", P_SELF_VERIFY):
            try:
                sv = MDL001SPSelfVerifier(cfg, verify, out_dir).run()
                html = build_self_verify_html_mdl001sp(sv, verify)
                sv_html_path = str(Path(out_dir) / "VRN_MDL001SP_SelfVerify.html")
                Path(sv_html_path).write_text(html, encoding="utf-8")
                log.info(f"[MDL001SP] Self-verify: {sv['classification']} "
                         f"({sv['pass']}/{sv['total']}) → {sv_html_path}")
            except Exception as e:
                log.warning(f"[MDL001SP] self_verify build fail: {e}")

        return {
            "status": "ok", "elapsed": elapsed,
            "total": len(pdfs), "stock": stock_count,
            "errors": len(self.errors),
            "output_dir": out_dir,
            "flush_stats": flush_stats,
            "self_verify_html": sv_html_path,
        }

    # [VIA:AST-PY-000057:ANCHOR] VRNIntegratedPipeline._write_summary_csv
    def _write_summary_csv(self, csv_path: str, results: List[Dict]) -> None:
        FIELDS = [
            "report_code","ticker","name","name_en","broker_abbr",
            "report_date","rating","rating_cat","target_price",
            "consensus_target_mean","consensus_rating","consensus_rating_mean",
            "analyst_count","adj_close","upside_pct","upside_target_source",
            "cv_score","m02_ok",
        ]
        try:
            with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
                w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
                w.writeheader()
                for r in results:
                    rec = r.get("record", {})
                    meta = rec.get("report_metadata", {})
                    row = {k: meta.get(k, "") for k in FIELDS}
                    row["cv_score"] = r.get("cv_score", "")
                    row["m02_ok"]   = r.get("m02_ok", "")
                    w.writerow(row)
        except Exception as e:
            log.warning(f"[CSV] {e}")

    # [VIA:AST-PY-000058:ANCHOR] VRNIntegratedPipeline._write_html
    def _write_html(self, html_path: str, data: Dict,
                    elapsed: float, workers: int, gov: Dict) -> None:
        total    = data["meta"].get("total_pdfs", 0)
        stock    = data["meta"].get("stock_reports", 0)
        ts       = data["meta"].get("timestamp", "")
        reports  = data.get("reports", [])
        rows_html = ""
        for rpt in reports:
            m   = rpt.get("report_metadata", {})
            val = rpt.get("validation", {})
            cv  = val.get("score", "")
            m2  = "✅" if val.get("m02_verify", {}).get("ok") else "⚠️"
            warns = len(val.get("warnings", []))
            rows_html += (
                f"<tr>"
                f"<td>{m.get('ticker','')}</td>"
                f"<td>{m.get('name','')}</td>"
                f"<td>{m.get('broker_abbr','')}</td>"
                f"<td>{m.get('report_date','')}</td>"
                f"<td>{m.get('rating_cat','')}</td>"
                f"<td>{m.get('target_price','')}</td>"
                f"<td>{m.get('consensus_target_mean','')}</td>"
                f"<td>{m.get('adj_close','')}</td>"
                f"<td>{m.get('upside_pct','')}</td>"
                f"<td>{cv}</td>"
                f"<td>{m2} {warns}W</td>"
                f"</tr>\n"
            )
        html = f"""<!DOCTYPE html>
<html lang="zh-TW"><head>
<meta charset="UTF-8">
<title>VRN Integrated Report {ts}</title>
<style>
  body{{font-family:'DM Sans','Noto Sans TC',sans-serif;background:#f5f4f0;color:#1a1918;margin:0;padding:20px}}
  h1{{font-size:1.4em;color:#2c5282;margin-bottom:4px}}
  .meta{{font-size:.85em;color:#555;margin-bottom:16px}}
  table{{border-collapse:collapse;width:100%;font-size:.82em}}
  th{{background:#2c5282;color:#fff;padding:6px 8px;text-align:left}}
  tr:nth-child(even){{background:#eeecea}}
  td{{padding:5px 8px;border-bottom:1px solid #ddd}}
</style>
</head><body>
<h1>VRN Integrated Pipeline · {__spec_version__}</h1>
<div class="meta">
  Generated: {ts} ·
  PDFs: {total} · Stock: {stock} ·
  Elapsed: {elapsed}s · Workers: {workers} · Gov: {gov.get('name','')}
</div>
<table>
<tr>
  <th>Ticker</th><th>Name</th><th>Broker</th><th>Date</th>
  <th>Rating</th><th>TP</th><th>Consensus Mean</th>
  <th>Adj Close</th><th>Upside%</th><th>CV Score</th><th>M02</th>
</tr>
{rows_html}
</table>
</body></html>"""
        try:
            Path(html_path).write_text(html, encoding="utf-8")
        except Exception as e:
            log.warning(f"[HTML] {e}")

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-V  CLI  argparse
# [VIA:ANCHOR:ANC-V:CLI]
# ════════════════════════════════════════════════════════════════════════════

# [VIA:AST-PY-000059:ANCHOR] build_cfg_from_args
def build_cfg_from_args() -> Dict:
    import argparse
    ap = argparse.ArgumentParser(
        description=f"VRN Integrated Pipeline {__module_id__} v{__version__}",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    ap.add_argument("--in_dir",    default=P_IN_DIR,    help="Input directory (PDFs)")
    ap.add_argument("--pdf_temp",  default=P_PDF_TEMP,  help="PDF temp directory")
    ap.add_argument("--out_dir",   default=P_OUTPUT_DIR,help="Output directory")
    ap.add_argument("--db",        default=P_DB_PATH,   help="SQLite DB path")
    ap.add_argument("--workers",   type=int, default=0, help="ThreadPool workers (0=auto)")
    ap.add_argument("--batch",     type=int, default=P_BATCH_SIZE, help="Batch size")
    ap.add_argument("--dpi",       type=int, default=P_DPI, help="PDF extract DPI")
    ap.add_argument("--no_cache",  action="store_true", help="Disable cache")
    ap.add_argument("--no_gov",    action="store_true", help="Disable Governor")
    ap.add_argument("--accel",     default=VIA_ACCEL_DEFAULT_MODE,
                    choices=["safe","balanced","maxsafe","aggressive"],
                    help="Acceleration mode")
    args = ap.parse_args()
    return {
        "IN_DIR":       args.in_dir,
        "PDF_TEMP":     args.pdf_temp,
        "OUTPUT_DIR":   args.out_dir,
        "DB_PATH":      args.db,
        "WORKERS":      args.workers,
        "BATCH_SIZE":   args.batch,
        "DPI":          args.dpi,
        "ENABLE_CACHE": not args.no_cache,
        "GOV_ENABLED":  not args.no_gov,
        "ACCEL_MODE":   args.accel,
    }

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-W  MAIN  主入口
# [VIA:ANCHOR:ANC-W:MAIN]
# ════════════════════════════════════════════════════════════════════════════

# [VIA:AST-PY-000060:ANCHOR] main
def main() -> None:
    """VRN M01+M02+M03 整合主入口。"""
    cfg = build_cfg_from_args()
    pipeline = VRNIntegratedPipeline(cfg)
    result   = pipeline.run()
    if result.get("status") == "no_files":
        log.warning("[MAIN] No PDF files found. Check --in_dir.")
        sys.exit(1)

if __name__ == "__main__":
    main()
