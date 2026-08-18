# [VIA:SAFE_BRIDGE:START]
# -*- coding: utf-8 -*-
from __future__ import annotations

# ╔══════════════════════════════════════════════════════════════════════════════════════════╗
# ║  VRN_MDL001_StockReportPipeline.py                                                      ║
# ║  VeritasReportNova · M01 + M02 + M03 全整合 · VRN Output Spec v6.0  v2.0.0             ║
# ╠══════════════════════════════════════════════════════════════════════════════════════════╣
# ║  v2.0.0  Standalone-First + Opt-In Integration                                           ║
# ║   FIX#11  ROOT CAUSE: v1.1 _via_try_init() 在 module-level 仍觸發 chain-load            ║
# ║           因為 getattr(proxy, attr, None) 會喚起 __getattr__                            ║
# ║   FIX#12  Module-level NEVER load Aegis/Celeritas/SuperAccel (預設 standalone)         ║
# ║   FIX#13  Opt-in via env VRN_INTEGRATE=1 / CLI --integrate full|aegis|celer|none        ║
# ║   FIX#14  整合層延後到 main() 才執行 + try/except 完整防護                              ║
# ║   FIX#15  支援 14 支 supportive_module 工具掃描 + health check                         ║
# ║   FIX#16  新增 VRN_PIPELINE_LAUNCHER.ps1 統一啟動器 (paste-and-run)                    ║
# ╠══════════════════════════════════════════════════════════════════════════════════════════╣
# ║  使用情境:                                                                                ║
# ║   1. 獨立執行 (預設):     python VRN_MDL001_StockReportPipeline.py                      ║
# ║   2. 統一啟動 (整合):     PS> .\VRN_PIPELINE_LAUNCHER.ps1                              ║
# ║   3. 環境變數整合:        $env:VRN_INTEGRATE='full'; python VRN_MDL001_*.py            ║
# ║   4. CLI flag 整合:       python VRN_MDL001_*.py --integrate full                       ║
# ║   5. Self-Test:           python VRN_MDL001_*.py --selftest                              ║
# ╚══════════════════════════════════════════════════════════════════════════════════════════╝

# ════════════════════════════════════════════════════════════════════════════
# Phase 0  最早期靜默 (在任何 import 之前)
# ════════════════════════════════════════════════════════════════════════════
import warnings as _w
_w.filterwarnings("ignore", message=".*FontBBox.*")
_w.filterwarnings("ignore", message=".*possibly delisted.*")
_w.filterwarnings("ignore", category=FutureWarning)
_w.filterwarnings("ignore", category=DeprecationWarning)
_w.filterwarnings("ignore", message=".*RequestsDependencyWarning.*")
_w.filterwarnings("ignore", message=".*urllib3.*")

import os as _os
_os.environ.setdefault("PYTHONWARNINGS", "ignore")
_os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
_os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-A  PARAMS  ★★★ ALL PARAMETERS ON THE TOP ★★★
# [VIA:ANCHOR:ANC-A:PARAMS]
# ════════════════════════════════════════════════════════════════════════════

__version__        = "2.0.0"
__module_id__      = "VRN-MDL001-STOCK-PIPELINE"
__spec_version__   = "v6.0"
__rule_version__   = "1.0"

# ──────────────────────────────────────────────────────────────────────────
# §P0  整合控制 (FIX#12 + FIX#13) — 核心控制位
# ──────────────────────────────────────────────────────────────────────────
# Module-level 預設 OFF: 不在 import 階段載入任何外部 supportive 模組
# 整合可由以下三種方式啟用 (優先順序由高至低):
#    1) CLI flag      --integrate full|aegis|celer|supportive|none
#    2) 環境變數      VRN_INTEGRATE=full|aegis|celer|supportive|none
#    3) 程式內預設    P_INTEGRATE_DEFAULT (本檔最頂部)
P_INTEGRATE_DEFAULT       = "none"        # 預設 standalone
P_SUPPORTIVE_MODULE_DIR   = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module"
P_VRN_DESKTOP_DIR         = r"C:\Users\tonyk\OneDrive\Desktop\新增資料夾 (4)\VRN"
P_VRN_MODULE_DIR          = r"C:\VeritasIntelligenceAnalytics\VeritasReportNova\module"
P_VPS_DIR                 = r"C:\VeritasIntelligenceAnalytics\VeritasPraesidium"
P_INTEGRATE_TIMEOUT       = 30            # 整合載入逾時 (秒)
P_INTEGRATE_VERBOSE       = True          # 是否輸出整合日誌

# 14 支 supportive 工具清單 (依依賴順序)
P_SUPPORTIVE_MODULES = [
    # Tier 1: 基礎工具 (無外部依賴)
    "VIA_SSOT_Unified",
    "VIA_RegistryCore_v1",
    "VIS_InstallHealthRegistry",
    "VIA_EnvManager",
    # Tier 2: 加速 / 網路 (heavy import — 整合模式才載)
    "VIA_Runtime_Bridge_All_in_One",
    "VIA_Supportive_Runtime_HardGate_Bridge",
    "VeritasCeleritas",
    "VeritasAegisNexus",
    # Tier 3: AST / 注入器
    "VIA_Panorama_AST_RuntimeInjector",
]
P_SUPPORTIVE_PS_TOOLS = [
    # PowerShell 配套工具(用於 PS1 啟動器引用)
    "Invoke-VIA-FinishProject-SafeFast.ps1",
    "Invoke-VIA-PanoramaHardGateSafeFix.ps1",
    "Invoke-VIA-SupportiveHardGate.ps1",
    "VIA_Supportive_HardGate_Seal.ps1",
    "VIA_Supportive_HardGate_Seal.json",
]

# ──────────────────────────────────────────────────────────────────────────
# §P1  路徑
# ──────────────────────────────────────────────────────────────────────────
VRN_ROOT       = r"C:\VeritasIntelligenceAnalytics\VeritasReportNova"
P_IN_DIR       = rf"{VRN_ROOT}\input"
P_PDF_TEMP     = rf"{VRN_ROOT}\temp\pdf_temp"
P_M01_TEMP     = rf"{VRN_ROOT}\temp\m01_temp"
P_M02_TEMP     = rf"{VRN_ROOT}\temp\m02_temp"
P_M03_TEMP     = rf"{VRN_ROOT}\temp\m03_temp"
P_DB_PATH      = rf"{VRN_ROOT}\database\vrn_integrated.db"
P_OUTPUT_DIR   = rf"{VRN_ROOT}\output"
P_LOG_DIR      = rf"{VRN_ROOT}\logs"

# ──────────────────────────────────────────────────────────────────────────
# §P2  PDF 擷取
# ──────────────────────────────────────────────────────────────────────────
P_DPI          = 300
P_JPEG_QUALITY = 92
P_INPUT_IMAGE_EXT = (".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp")
P_INPUT_WORD_EXT  = (".doc", ".docx")

# ──────────────────────────────────────────────────────────────────────────
# §P3  分類門檻
# ──────────────────────────────────────────────────────────────────────────
P_CLASSIFY_THRESHOLD  = 15
P_MAX_SCAN_PAGES      = 30
P_MAX_FIN_PAGES       = 10
P_FIN_HIT_THRESHOLD   = 1
P_FIN_SCORE_THRESHOLD = 8
P_MIN_DIGIT_DENSITY   = 0.25
P_ALLOW_NO_FIN_PAGES  = True

# ──────────────────────────────────────────────────────────────────────────
# §P4  加速器
# ──────────────────────────────────────────────────────────────────────────
P_WORKERS        = 0         # 0=auto (cpu-1)
P_BATCH_SIZE     = 24
P_PRIORITY_BOOST = True
P_GC_OPTIMIZE    = True
P_ENV_BIND       = True
P_ENABLE_CACHE   = True
P_SKIP_IF_EXISTS = False
P_GOV_ENABLED        = True
P_GOV_CPU_TEMP_MAX   = 82.0
P_GOV_DRAM_MAX_PCT   = 85.0
P_GOV_MIN_AVAIL_GB   = 1.0
P_GOV_SAFE_AVAIL_GB  = 2.0

# ──────────────────────────────────────────────────────────────────────────
# §P5  VDF / yfinance
# ──────────────────────────────────────────────────────────────────────────
P_ENABLE_NAME_LOOKUP    = True
P_NAME_LOOKUP_TIMEOUT   = 3
P_VDF_PANORAMIC_ENABLED = True
P_VDF_PANORAMIC_TIMEOUT = 5
P_VDF_RETRY_COUNT       = 2
P_VDF_RETRY_DELAY       = 0.5

# ──────────────────────────────────────────────────────────────────────────
# §P6  HTML + 啟動
# ──────────────────────────────────────────────────────────────────────────
P_CLEAN_TEMP_ON_START = True
P_HTML_REPORT         = True
P_HTML_AUTO_OPEN      = False      # LL#12

# ──────────────────────────────────────────────────────────────────────────
# §P7  文字清洗
# ──────────────────────────────────────────────────────────────────────────
P_MIN_LINE_LEN   = 2
P_MAX_LINE_LEN   = 800
P_DEDUP_WINDOW   = 50

# ──────────────────────────────────────────────────────────────────────────
# §P8  年份排除
# ──────────────────────────────────────────────────────────────────────────
P_YEAR_EXCLUSION = list(range(2021, 2031))

# ──────────────────────────────────────────────────────────────────────────
# §P9  CV-01~CV-05
# ──────────────────────────────────────────────────────────────────────────
CV01_TP_DIFF_WARN_PCT  = 20.0
CV02_RATING_MISMATCH   = True
CV03_MIN_ANALYST_COUNT = 3
CV04_TP_RANGE_CHECK    = True
CV05_MEAN_SELL_THRESH  = 3.5

# ──────────────────────────────────────────────────────────────────────────
# §P10 M02 驗證
# ──────────────────────────────────────────────────────────────────────────
M02_ZERO_ERROR       = False
M02_EPS_RANGE        = (-500.0, 500.0)
M02_GROSS_DIFF_MAX   = 0.02

# ──────────────────────────────────────────────────────────────────────────
# §P11 Lesson Learned
# ──────────────────────────────────────────────────────────────────────────
P_LL_CONFIDENCE_THRESHOLD = 0.85

# ──────────────────────────────────────────────────────────────────────────
# §P12 加速模式
# ──────────────────────────────────────────────────────────────────────────
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

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-B  BOOTSTRAP (FIX#12 — module-level 完全不載入外部模組)
# [VIA:ANCHOR:ANC-B:BOOTSTRAP]
# ════════════════════════════════════════════════════════════════════════════
import sys as _via_sys

# 僅將路徑加入 sys.path,**不** import 任何模組
_via_search_dirs = [
    P_VRN_DESKTOP_DIR,
    P_VRN_MODULE_DIR,
    P_VPS_DIR,
    P_SUPPORTIVE_MODULE_DIR,   # 新增 supportive_module 路徑
]
for _via_dir in _via_search_dirs:
    if _via_dir and _via_dir not in _via_sys.path:
        try:
            _via_sys.path.insert(0, _via_dir)
        except Exception:
            pass

# 整合狀態追蹤 (由 main() 階段填寫)
_INTEGRATE_STATE = {
    "mode":          "none",
    "loaded":        [],
    "failed":        [],
    "skipped":       [],
    "elapsed_ms":    0,
    "ll_threshold":  P_LL_CONFIDENCE_THRESHOLD,
}

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-C  STDLIB_IMPORTS
# [VIA:ANCHOR:ANC-C:IMPORTS]
# ════════════════════════════════════════════════════════════════════════════

import os, gc, re, sys, json, csv, time, copy, math, shutil, hashlib
import sqlite3, platform, threading, importlib, importlib.util, traceback, subprocess
import multiprocessing, collections, contextlib, urllib.request, urllib.parse
import warnings
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union, Set
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import OrderedDict


# ── Lazy heavy module wrapper ────────────────────────────────────────────────
class _LazyModule:
    """Heavy module proxy — 宣告 0ms,首次屬性存取才 import."""
    __slots__ = ("_name", "_mod", "_failed", "_lock")

    def __init__(self, name: str):
        self._name = name
        self._mod = None
        self._failed = False
        self._lock = threading.Lock()

    def _load(self):
        if self._mod is not None or self._failed:
            return self._mod
        with self._lock:
            if self._mod is not None or self._failed:
                return self._mod
            try:
                self._mod = importlib.import_module(self._name)
            except Exception:
                self._failed = True
        return self._mod

    def __getattr__(self, key):
        # SLOTS 屬性會走標準路徑;其他屬性才觸發 _load
        if key.startswith("_") and key in ("_name", "_mod", "_failed", "_lock"):
            raise AttributeError(key)
        m = self._load()
        if m is None:
            raise AttributeError(f"{self._name} not available (.{key})")
        return getattr(m, key)

    def __bool__(self):
        if self._failed:
            return False
        if self._mod is not None:
            return True
        try:
            return importlib.util.find_spec(self._name) is not None
        except Exception:
            return False


def _safe_import(name: str):
    """Light modules — direct import OK (cost < 50ms)."""
    try:
        return importlib.import_module(name)
    except Exception:
        return None


# Light modules
psutil       = _safe_import("psutil")
loguru_mod   = _safe_import("loguru")
xxhash_mod   = _safe_import("xxhash")
orjson_mod   = _safe_import("orjson")

# Heavy modules — lazy
fitz         = _LazyModule("fitz")
pdfplumber   = _LazyModule("pdfplumber")
yfinance     = _LazyModule("yfinance")
duckdb_mod   = _LazyModule("duckdb")
polars_mod   = _LazyModule("polars")
pandas_mod   = _LazyModule("pandas")
pyarrow_mod  = _LazyModule("pyarrow")
numba_mod    = _LazyModule("numba")
numexpr_mod  = _LazyModule("numexpr")


# ── Logger (lazy build) ──────────────────────────────────────────────────────
_log_lock = threading.Lock()
_log_inst = None


def _get_log():
    global _log_inst
    if _log_inst is not None:
        return _log_inst
    with _log_lock:
        if _log_inst is not None:
            return _log_inst
        if loguru_mod:
            lg = loguru_mod.logger
            try:
                lg.remove()
                lg.add(sys.stderr, level="DEBUG",
                       format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <white>{message}</white>",
                       colorize=True)
                Path(P_LOG_DIR).mkdir(parents=True, exist_ok=True)
                lg.add(str(Path(P_LOG_DIR) / "vrn_{time:YYYYMMDD}.log"),
                       level="DEBUG", rotation="10 MB", retention="30 days",
                       encoding="utf-8", enqueue=True)
            except Exception:
                pass
            _log_inst = lg
        else:
            import logging as _lg
            logging = _lg.getLogger("VRN")
            logging.setLevel(_lg.DEBUG)
            if not logging.handlers:
                _h = _lg.StreamHandler()
                _h.setFormatter(_lg.Formatter("%(asctime)s | %(levelname)-8s | %(message)s",
                                              datefmt="%H:%M:%S"))
                logging.addHandler(_h)
            _log_inst = logging
        return _log_inst


class _LogProxy:
    def __getattr__(self, k):
        return getattr(_get_log(), k)


log = _LogProxy()


def _suppress_yf_logging():
    try:
        import logging as _yfl
        _yfl.getLogger("yfinance").setLevel(_yfl.CRITICAL)
        _yfl.getLogger("peewee").setLevel(_yfl.CRITICAL)
        _yfl.getLogger("urllib3").setLevel(_yfl.CRITICAL)
    except Exception:
        pass


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
# ⚓ ANC-B2  INTEGRATION  Opt-In supportive modules (FIX#13 + FIX#14 + FIX#15)
# [VIA:ANCHOR:ANC-B2:INTEGRATION]
# ════════════════════════════════════════════════════════════════════════════

def _resolve_integrate_mode(cli_arg: Optional[str] = None) -> str:
    """Resolve integration mode.
    Priority: CLI arg > env var > default.
    Valid: 'full' | 'aegis' | 'celer' | 'supportive' | 'none'
    """
    raw = (cli_arg or os.environ.get("VRN_INTEGRATE") or P_INTEGRATE_DEFAULT or "none").strip().lower()
    if raw in ("1", "true", "yes", "on"):
        raw = "full"
    if raw in ("0", "false", "no", "off"):
        raw = "none"
    return raw if raw in ("full", "aegis", "celer", "supportive", "none") else "none"


def _probe_supportive_modules() -> Dict[str, bool]:
    """Probe which supportive modules are present (no-load, find_spec only)."""
    result = {}
    for name in P_SUPPORTIVE_MODULES:
        try:
            result[name] = importlib.util.find_spec(name) is not None
        except Exception:
            result[name] = False
    return result


def _load_supportive_module(name: str, timeout: int = P_INTEGRATE_TIMEOUT) -> Tuple[bool, str, float]:
    """Try to import a supportive module with timeout protection.
    Returns: (ok, message, elapsed_ms)
    """
    t0 = time.time()
    try:
        spec = importlib.util.find_spec(name)
        if spec is None:
            return False, "not_found", 0.0
        # 直接 import — timeout 由整體 main() 控制
        mod = importlib.import_module(name)
        elapsed = (time.time() - t0) * 1000
        # 嘗試呼叫常見初始化函式
        for fn_name in ("cross_init", "configure_ultra_acceleration",
                         "configure_acceleration", "init", "bootstrap"):
            fn = getattr(mod, fn_name, None)
            if callable(fn):
                try:
                    try:
                        fn(silent=True)
                    except TypeError:
                        fn()
                    return True, f"ok ({fn_name} called)", elapsed
                except Exception as e:
                    return True, f"ok (init {fn_name} failed: {e})", elapsed
        return True, "ok (no init fn)", elapsed
    except KeyboardInterrupt:
        return False, "interrupted", (time.time() - t0) * 1000
    except Exception as e:
        return False, f"error: {type(e).__name__}: {str(e)[:100]}", (time.time() - t0) * 1000


def integrate_supportive(mode: str = "none", verbose: bool = True) -> Dict[str, Any]:
    """Activate supportive modules per integration mode.

    mode:
      'none'       — 不載任何 supportive 模組 (預設)
      'aegis'      — 只載 VeritasAegisNexus
      'celer'      — 只載 VeritasCeleritas
      'supportive' — Tier 1 工具 (SSOT/Registry/EnvManager 等輕量)
      'full'       — 全部 9 支 Python supportive 模組
    """
    state = {
        "mode": mode, "loaded": [], "failed": [], "skipped": [],
        "elapsed_ms": 0.0, "started_at": datetime.now().isoformat(),
    }
    if mode == "none":
        if verbose:
            print("[INTEGRATE] mode=none — running standalone (no supportive modules)")
        _INTEGRATE_STATE.update(state)
        return state

    targets: List[str] = []
    if mode == "aegis":
        targets = ["VeritasAegisNexus"]
    elif mode == "celer":
        targets = ["VeritasCeleritas"]
    elif mode == "supportive":
        # Tier 1: lightweight only
        targets = ["VIA_SSOT_Unified", "VIA_RegistryCore_v1",
                   "VIS_InstallHealthRegistry", "VIA_EnvManager"]
    elif mode == "full":
        targets = list(P_SUPPORTIVE_MODULES)

    t0 = time.time()
    for name in targets:
        if verbose:
            print(f"[INTEGRATE] loading {name} ...", flush=True, end=" ")
        ok, msg, ms = _load_supportive_module(name)
        if ok:
            state["loaded"].append({"name": name, "msg": msg, "ms": round(ms, 1)})
            if verbose:
                print(f"✅ {ms:.0f}ms  {msg}")
        else:
            if msg == "not_found":
                state["skipped"].append({"name": name, "msg": msg})
                if verbose:
                    print(f"⬜ skipped (not found)")
            else:
                state["failed"].append({"name": name, "msg": msg, "ms": round(ms, 1)})
                if verbose:
                    print(f"❌ {msg}")

    state["elapsed_ms"] = round((time.time() - t0) * 1000, 1)
    _INTEGRATE_STATE.update(state)

    if verbose:
        print(f"[INTEGRATE] done  loaded={len(state['loaded'])}  "
              f"failed={len(state['failed'])}  skipped={len(state['skipped'])}  "
              f"total={state['elapsed_ms']}ms")
    return state


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
# ⚓ ANC-E  BROKER_RATING
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
# ⚓ ANC-F  ACCEL_M03
# [VIA:ANCHOR:ANC-F:ACCEL_M03]
# ════════════════════════════════════════════════════════════════════════════

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


def _cpu_count(logical: bool = True) -> int:
    try:
        if not logical and psutil:
            n = psutil.cpu_count(logical=False)
            return max(1, int(n)) if n else _cpu_count(logical=True)
    except Exception:
        pass
    return max(1, int(os.cpu_count() or multiprocessing.cpu_count() or 4))


def _available_ram_mb() -> int:
    try:
        if psutil:
            return max(256, int(psutil.virtual_memory().available // (1024 * 1024)))
    except Exception:
        pass
    return 2048


def _resolve_mode(mode=None) -> str:
    raw = (mode or os.environ.get("VIA_ACCEL_MODE") or VIA_ACCEL_DEFAULT_MODE).strip().lower()
    raw = VRN_MODE_MAP.get(raw, raw)
    return raw if raw in ("safe", "balanced", "maxsafe", "aggressive") else "maxsafe"


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


class GCTuner:
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


class MemoryPool:
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


def accel_init_full(cfg: Dict) -> int:
    if cfg.get("PRIORITY_BOOST", P_PRIORITY_BOOST):
        try:
            if platform.system() == "Windows":
                import ctypes
                ctypes.windll.kernel32.SetPriorityClass(
                    ctypes.windll.kernel32.GetCurrentProcess(), 0x00008000)
        except Exception:
            pass
    if cfg.get("GC_OPTIMIZE", P_GC_OPTIMIZE):
        GCTuner.optimize()
    apply_vrn_vds_max_accel()
    w = cfg.get("WORKERS", P_WORKERS)
    return int(w) if w and w > 0 else max(1, _cpu_count(logical=False) - 1)


class HardwareGovernor:
    def status(self, cfg: Dict) -> Dict:
        if not P_GOV_ENABLED or not psutil:
            return {"level": 0, "name": "SAFE", "adj_workers": accel_init_full(cfg)}
        vm    = psutil.virtual_memory()
        avail = vm.available / (1024 ** 3)
        pct   = vm.percent
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


class VIACache:
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
# ⚓ ANC-G  INFRA  Lesson Learned
# [VIA:ANCHOR:ANC-G:INFRA]
# ════════════════════════════════════════════════════════════════════════════

class LessonLearnedDB:
    def __init__(self, db_path: str):
        self._path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
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
                with sqlite3.connect(self._path) as con:
                    con.execute(
                        "INSERT INTO lesson_learned (error_type,report_code,content,cpu_temp,confidence) VALUES (?,?,?,?,?)",
                        (error_type, report_code, content[:500], cpu_temp, confidence))
            except Exception as e:
                log.warning(f"[LL] log_lesson failed: {e}")

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-H  M01_DETECTORS
# [VIA:ANCHOR:ANC-H:M01_DETECTORS]
# ════════════════════════════════════════════════════════════════════════════

def vtk(t: str, cfg: Optional[Dict] = None) -> bool:
    if not t or len(t) != 4 or t[0] == "0":
        return False
    try:
        return int(t) not in (cfg or {}).get("YEAR_EXCLUSION", P_YEAR_EXCLUSION)
    except Exception:
        return False


def detect_tw_ticker(s: str) -> Optional[Dict[str, str]]:
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


def detect_ticker(text: str, cfg: Optional[Dict] = None) -> str:
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


def detect_broker(text: str) -> Dict[str, str]:
    for b in P_KNOWN_BROKERS:
        for p in b["p"]:
            if re.search(re.escape(p), text, re.I):
                return {"full": b["full"], "abbr": b["abbr"]}
    return {"full": "", "abbr": ""}


def detect_rating(text: str) -> Dict[str, str]:
    for cat, pats in P_RATING_PATTERNS.items():
        for p in pats:
            if re.search(re.escape(p), text, re.I):
                return {"rating": p, "category": cat}
    return {"rating": "", "category": ""}


def detect_date(text: str) -> str:
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


def detect_tp(text: str) -> str:
    for kw in ["目標價", "合理價", "Target Price", "Price Target", "Fair Value", "TP"]:
        m = re.search(re.escape(kw) + r'[:\s ]*(?:NT\$?|TWD)?\s*([\d,]+(?:\.\d+)?)', text, re.I)
        if m:
            return m.group(1).replace(",", "")
    return ""


def detect_company(text: str, ticker: str) -> str:
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
# ⚓ ANC-I  M01_VDF
# [VIA:ANCHOR:ANC-I:M01_VDF]
# ════════════════════════════════════════════════════════════════════════════

_NAME_CACHE: Dict[str, Dict] = {}
_NAME_CACHE_LOCK = threading.Lock()


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


def _vdf_json_request(url: str, timeout: int) -> Optional[Dict]:
    raw = _vdf_request(url, timeout)
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            pass
    return None


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


def vdf_lookup_yfinance(ticker: str, timeout: int = P_NAME_LOOKUP_TIMEOUT) -> Dict:
    result = {"name": "", "name_en": "", "source": ""}
    if not yfinance:
        return result
    _suppress_yf_logging()
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


def resolve_company_name(ticker: str, cover_text: str, fn: str) -> Dict:
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
# ⚓ ANC-J  M01_PRICE
# [VIA:ANCHOR:ANC-J:M01_PRICE]
# ════════════════════════════════════════════════════════════════════════════

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


def get_price_metrics(ticker: str, report_date: str, target_price: str) -> Dict[str, Any]:
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
    _suppress_yf_logging()
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
# ⚓ ANC-K  M01_CONSENSUS
# [VIA:ANCHOR:ANC-K:M01_CONSENSUS]
# ════════════════════════════════════════════════════════════════════════════

def fetch_yfinance_info(ticker: str, yfinance_ticker: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {v: None for _, v in YF_INFO_KEY_MAP}
    if not yfinance:
        return out
    _suppress_yf_logging()
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


def fetch_analyst_distribution(yfinance_ticker: str) -> Dict[str, Optional[int]]:
    keys = ["analyst_strong_buy", "analyst_buy", "analyst_hold",
            "analyst_sell", "analyst_strong_sell"]
    result: Dict[str, Optional[int]] = {k: None for k in keys}
    if not yfinance or not yfinance_ticker:
        return result
    _suppress_yf_logging()
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


def build_consensus_block(ticker: str, yfinance_ticker: str) -> Dict[str, Any]:
    info_data = fetch_yfinance_info(ticker, yfinance_ticker)
    dist_data = fetch_analyst_distribution(yfinance_ticker)
    return {
        "consensus_target_high":   info_data.get("consensus_target_high"),
        "consensus_target_low":    info_data.get("consensus_target_low"),
        "consensus_target_mean":   info_data.get("consensus_target_mean"),
        "consensus_target_median": info_data.get("consensus_target_median"),
        "consensus_rating":        info_data.get("consensus_rating", ""),
        "consensus_rating_mean":   info_data.get("consensus_rating_mean"),
        "analyst_count":           info_data.get("analyst_count"),
        "analyst_strong_buy":      dist_data.get("analyst_strong_buy"),
        "analyst_buy":             dist_data.get("analyst_buy"),
        "analyst_hold":            dist_data.get("analyst_hold"),
        "analyst_sell":            dist_data.get("analyst_sell"),
        "analyst_strong_sell":     dist_data.get("analyst_strong_sell"),
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
# ⚓ ANC-L  M01_REPAIR
# [VIA:ANCHOR:ANC-L:M01_REPAIR]
# ════════════════════════════════════════════════════════════════════════════

class SentenceRepairEngine:
    CN_END   = set("。!?;… 》〉")
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
# ⚓ ANC-M  M01_CLASSIFY
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


def is_stock_report(fn: str, cover_text: str, ticker: str) -> Tuple[bool, int, List[str]]:
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


def detect_fin_pages_from_pdf(pdf_obj) -> List[Dict]:
    result = []
    try:
        for i, page in enumerate(pdf_obj.pages[:P_MAX_SCAN_PAGES]):
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
            tot  = len(text.replace(" ", ""))
            digs = len(re.findall(r"[\d,.%\-]", text))
            if tot > 20 and digs / tot >= P_MIN_DIGIT_DENSITY:
                score += 2
                reasons.append("digit_density")
            if hits >= P_FIN_HIT_THRESHOLD or score >= P_FIN_SCORE_THRESHOLD:
                result.append({"page": i + 1, "page_idx": i, "score": score,
                               "hits": hits, "reasons": reasons})
    except Exception as e:
        log.warning(f"[CLASSIFY] {e}")
    return result


def detect_fin_pages(pdf_path: str) -> List[Dict]:
    if not pdfplumber:
        return []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            return detect_fin_pages_from_pdf(pdf)
    except Exception as e:
        log.warning(f"[CLASSIFY] open: {e}")
        return []

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-N  M01_EXTRACT
# [VIA:ANCHOR:ANC-N:M01_EXTRACT]
# ════════════════════════════════════════════════════════════════════════════

def extract_pages_pdf(src: str, dst: str, page_indices: List[int],
                      dpi: int = P_DPI, quality: int = P_JPEG_QUALITY) -> str:
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
# ⚓ ANC-O  M01_OUTPUT
# [VIA:ANCHOR:ANC-O:M01_OUTPUT]
# ════════════════════════════════════════════════════════════════════════════

def build_report_metadata(
        fn: str, ticker: str, report_date: str,
        broker_info: Dict, rating_info: Dict, target_price: str,
        company_info: Dict, price_metrics: Dict,
        consensus: Dict) -> Dict[str, Any]:
    yft = price_metrics.get("yfinance_ticker", f"{ticker}.TW")
    report_code = (
        f"{broker_info.get('abbr', 'UNK')}-"
        f"{ticker}-"
        f"{company_info.get('name', '')}-"
        f"{report_date.replace('-', '')}"
    )
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
        "report_code":   report_code,
        "report_date":   report_date,
        "filename":      fn,
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
        "rating":        rating_info.get("rating", ""),
        "rating_cat":    rating_info.get("category", ""),
        "target_price":  float(target_price.replace(",", "")) if target_price else None,
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
        "adj_close":               price_metrics.get("adj_close"),
        "adj_close_date":          price_metrics.get("adj_close_date", ""),
        "upside_pct":              upside_pct,
        "upside_target_source":    upside_source,
        "performance_pct_since_report": price_metrics.get("performance_pct_since_report"),
    }

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-P  M02_REPAIR
# [VIA:ANCHOR:ANC-P:M02_REPAIR]
# ════════════════════════════════════════════════════════════════════════════

_NOISE_RE          = re.compile(r"[\u0000-\u0008\u000b\u000e-\u001f]|[^\S\n]{3,}", re.UNICODE)
_BROKEN_SENT_RE    = re.compile(r"([^\u3002\uff01\uff1f\.!?;;])\n([^\s])")


class TextRepairEngine:
    _OCR_NUM_RE = re.compile(r"(?<!\w)([lO\|])(?=[\d,])|(?<=[\d,])([lO\|])(?!\w)")

    def repair_text_records(self, records: List[Dict]) -> List[Dict]:
        seen, result = set(), []
        for rec in records:
            text = rec.get("text", "")
            text = _NOISE_RE.sub(" ", text).strip()
            text = text.replace("\u3000", " ").replace("\u00a0", " ")
            text = re.sub(r" {2,}", " ", text)
            if not text or len(text) < 2:
                continue
            key = _hash8(text)
            if key in seen:
                continue
            seen.add(key)
            rec = dict(rec)
            rec["text"] = text
            result.append(rec)
        merged, buf = [], None
        for rec in result:
            if buf is None:
                buf = copy.copy(rec)
                continue
            if (buf.get("type") in ("TXT", "KV") and rec.get("type") == "TXT"
                    and not re.search(r"[。!?;.!?]$", buf["text"])):
                buf["text"] = buf["text"].rstrip() + " " + rec["text"].lstrip()
            else:
                merged.append(buf)
                buf = copy.copy(rec)
        if buf:
            merged.append(buf)
        return merged

    def repair_table_rows(self, rows: List[Dict]) -> List[Dict]:
        fixed = []
        for row in rows:
            label = row.get("label", "")
            label = self._OCR_NUM_RE.sub(
                lambda m: "1" if (m.group(1) or m.group(2)) in "lL|" else "0", label)
            if re.fullmatch(r"[\s\d年QEFe\-/]+", label):
                continue
            fixed.append(dict(row, label=label.strip()))
        return fixed

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-Q  M02_CANONICAL
# [VIA:ANCHOR:ANC-Q:M02_CANONICAL]
# ════════════════════════════════════════════════════════════════════════════

_CANONICAL_MAP: Dict[str, str] = {
    "營業收入淨額":"revenue", "營業收入":"revenue", "收入":"revenue",
    "Revenue":"revenue", "Net Revenue":"revenue", "营收":"revenue",
    "營業成本":"cogs", "Cost of Revenue":"cogs", "COGS":"cogs",
    "營業毛利淨額":"gross_profit", "毛利":"gross_profit", "Gross Profit":"gross_profit",
    "營業費用":"opex", "Operating Expense":"opex", "OpEx":"opex",
    "營業淨利/損":"operating_income", "營業利益":"operating_income",
    "Operating Income":"operating_income", "EBIT":"operating_income",
    "稅前淨利":"pretax_income", "Pretax Income":"pretax_income",
    "稅後淨利":"net_income", "Net Income":"net_income",
    "歸屬母公司淨利":"net_income_parent",
    "每股盈餘(元)":"eps", "每股盈餘":"eps", "EPS":"eps",
    "毛利率":"gross_margin", "Gross Margin":"gross_margin",
    "營業利益率":"operating_margin", "Operating Margin":"operating_margin",
    "淨利率":"net_margin", "Net Margin":"net_margin",
    "本益比(P/E)":"pe_ratio", "P/E":"pe_ratio", "本益比":"pe_ratio",
    "總資產":"total_assets", "Total Assets":"total_assets",
    "總負債":"total_liabilities", "Total Liabilities":"total_liabilities",
    "股東權益":"shareholders_equity", "Shareholders Equity":"shareholders_equity",
    "稀釋每股盈餘":"diluted_eps", "Diluted EPS":"diluted_eps",
    "每股淨值":"bvps", "Book Value Per Share":"bvps",
    "每股股利":"dps", "DPS":"dps",
}


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


def restructure_tables(report_code: str, ticker: str, report_date: str,
                       broker_abbr: str, tables: List[Dict],
                       repair: TextRepairEngine) -> List[FinancialRow]:
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
# ⚓ ANC-R  M02_VERIFY
# [VIA:ANCHOR:ANC-R:M02_VERIFY]
# ════════════════════════════════════════════════════════════════════════════

def verify_financial_rows(rows: List[FinancialRow], zero_error: bool = M02_ZERO_ERROR) -> Dict:
    errors, warnings_l, passes = [], [], []

    def fail(code, detail):
        msg = f"{code}: {detail}"
        errors.append(msg)
        log.error(f"[M02 VERIFY] {msg}")
        if zero_error:
            raise RuntimeError(msg)

    def warn(code, detail):
        warnings_l.append(f"{code}: {detail}")

    def ok(code, detail=""):
        passes.append(f"{code}" + (f": {detail}" if detail else ""))

    if not rows:
        ok("C00", "no rows - skipped")
        return {"ok": True, "passes": passes, "errors": errors, "warnings": warnings_l,
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
        "passes":  passes, "errors": errors, "warnings": warnings_l,
        "n_pass":  len(passes), "n_error": len(errors), "n_warn": len(warnings_l),
    }

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-S  M02_DB
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
CREATE TABLE IF NOT EXISTS vrn_integrate_state (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT DEFAULT (datetime('now')),
    mode        TEXT, loaded_count INTEGER, failed_count INTEGER,
    skipped_count INTEGER, elapsed_ms REAL, state_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_fin_ticker  ON vrn_financial(ticker);
CREATE INDEX IF NOT EXISTS idx_fin_canon   ON vrn_financial(canonical);
CREATE INDEX IF NOT EXISTS idx_fin_period  ON vrn_financial(period);
CREATE INDEX IF NOT EXISTS idx_fin_report  ON vrn_financial(report_code);
CREATE INDEX IF NOT EXISTS idx_meta_ticker ON vrn_metadata(ticker);
"""


class VRNDBWriter:
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

    def insert_integrate_state(self, state: Dict) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO vrn_integrate_state (mode,loaded_count,failed_count,skipped_count,elapsed_ms,state_json) VALUES (?,?,?,?,?,?)",
                (state.get("mode",""), len(state.get("loaded",[])),
                 len(state.get("failed",[])), len(state.get("skipped",[])),
                 state.get("elapsed_ms",0.0),
                 json.dumps(state, ensure_ascii=False)[:5000]))

    def export_parquet(self, out_dir: str) -> bool:
        if not pandas_mod:
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
# ⚓ ANC-T  CROSS_VALID
# [VIA:ANCHOR:ANC-T:CROSS_VALID]
# ════════════════════════════════════════════════════════════════════════════

def run_cross_validation(report_code: str, meta: Dict[str, Any],
                         db_writer: Optional[VRNDBWriter] = None) -> Dict[str, Any]:
    score_holder = [100]
    results: List[Dict] = []
    warnings_l: List[str] = []
    errors:   List[str] = []

    def _add(rule: str, outcome: str, detail: str):
        results.append({"rule": rule, "outcome": outcome, "detail": detail})
        if db_writer:
            try:
                db_writer.insert_cv_result(report_code, rule, outcome, detail)
            except Exception:
                pass
        if outcome == "WARN":
            warnings_l.append(f"{rule}: {detail}")
            score_holder[0] -= 5
        elif outcome == "MISMATCH":
            warnings_l.append(f"{rule}: {detail}")
            score_holder[0] -= 8
        elif outcome == "FLAG":
            warnings_l.append(f"{rule}: {detail}")
            score_holder[0] -= 6
        elif outcome == "LOW_COVERAGE":
            warnings_l.append(f"{rule}: {detail}")
            score_holder[0] -= 3

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
            crec_norm = crec.replace("-", "").replace(" ", "")
            match = any(crec_norm == e.replace("-", "").replace(" ", "") for e in equiv)
            if not match:
                _add("CV-02", "MISMATCH", f"Report={rcat} vs Consensus={crec}")
            else:
                _add("CV-02", "OK", f"Report={rcat} ~ Consensus={crec}")
        else:
            _add("CV-02", "SKIP", "rating data unavailable")

    ac = meta.get("analyst_count")
    if ac is not None:
        if int(ac) < CV03_MIN_ANALYST_COUNT:
            _add("CV-03", "LOW_COVERAGE", f"analyst_count={ac}")
        else:
            _add("CV-03", "OK", f"analyst_count={ac}")
    else:
        _add("CV-03", "SKIP", "analyst_count not available")

    if CV04_TP_RANGE_CHECK:
        cth = meta.get("consensus_target_high")
        ctl = meta.get("consensus_target_low")
        if tp and cth and ctl:
            try:
                tp_f  = float(tp)
                hi, lo = float(cth), float(ctl)
                if tp_f > hi:
                    _add("CV-04", "WARN", f"TP({tp_f}) > analyst high({hi})")
                elif tp_f < lo:
                    _add("CV-04", "WARN", f"TP({tp_f}) < analyst low({lo})")
                else:
                    _add("CV-04", "OK", f"TP({tp_f}) within [{lo}, {hi}]")
            except Exception:
                pass
        else:
            _add("CV-04", "SKIP", "insufficient range data")

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
        "score":    max(0, score_holder[0]),
        "warnings": warnings_l,
        "errors":   errors,
        "results":  results,
    }

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-U  PIPELINE
# [VIA:ANCHOR:ANC-U:PIPELINE]
# ════════════════════════════════════════════════════════════════════════════

class VRNIntegratedPipeline:
    def __init__(self, cfg: Optional[Dict] = None):
        self.cfg        = cfg or {}
        self.repair_m01 = SentenceRepairEngine()
        self.repair_m02 = TextRepairEngine()
        self.cache      = VIACache(enabled=self.cfg.get("ENABLE_CACHE", P_ENABLE_CACHE))
        self.governor   = HardwareGovernor()
        self.db         = VRNDBWriter(self.cfg.get("DB_PATH", P_DB_PATH))
        self.ll_db      = LessonLearnedDB(
            self.cfg.get("DB_PATH", P_DB_PATH).replace(".db", "_ll.db"))
        self.all_results: List[Dict] = []
        self.errors:      List[Dict] = []

    def _open_and_extract(self, pdf_path: str) -> Dict[str, Any]:
        out = {
            "cover_text":   "",
            "fin_pages":    [],
            "cover_typed":  [],
            "fin_typed":    [],
            "direct_tables":[],
        }
        if not pdfplumber:
            return out
        try:
            with pdfplumber.open(pdf_path) as pdf:
                cover_pages = pdf.pages[:3]
                out["cover_text"] = " ".join((p.extract_text() or "") for p in cover_pages)
                out["fin_pages"] = detect_fin_pages_from_pdf(pdf)
                if pdf.pages:
                    typed = self.repair_m01.repair_typed(pdf.pages[0])
                    for item in typed:
                        item["page"] = 1
                    out["cover_typed"] = typed
                fin_typed = []
                for fp in out["fin_pages"]:
                    pi = fp["page_idx"]
                    if pi >= len(pdf.pages):
                        continue
                    typed = self.repair_m01.repair_typed(pdf.pages[pi])
                    for item in typed:
                        item["page"] = pi + 1
                    fin_typed.extend(typed)
                out["fin_typed"] = fin_typed

                direct_tables: List[Dict] = []
                for page in pdf.pages[:P_MAX_FIN_PAGES + 2]:
                    try:
                        tables = page.extract_tables() or []
                    except Exception:
                        tables = []
                    for tbl in tables:
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
                out["direct_tables"] = direct_tables
        except Exception as e:
            log.warning(f"[OPEN_AND_EXTRACT] {e}")
        return out

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

        try:
            fn_stem   = Path(pdf_path).stem
            fn_ticker = detect_ticker(fn_stem, {"YEAR_EXCLUSION": P_YEAR_EXCLUSION})
            fn_broker = detect_broker(fn_stem)
            fn_date   = detect_date(fn_stem)

            extracted = self._open_and_extract(pdf_path)
            cover_text   = extracted["cover_text"]
            fin_pages    = extracted["fin_pages"]
            cover_typed  = extracted["cover_typed"]
            fin_typed    = extracted["fin_typed"]
            direct_tables = extracted["direct_tables"]

            ticker = fn_ticker or detect_ticker(cover_text, {"YEAR_EXCLUSION": P_YEAR_EXCLUSION})
            is_stock, score, reasons = is_stock_report(fn, cover_text, ticker)
            result["score"]    = score
            result["is_stock"] = is_stock

            if not is_stock:
                result["classification"] = {"document_type": "NON_STOCK", "reasons": reasons}
                return result

            broker_info  = fn_broker if fn_broker["abbr"] else detect_broker(cover_text)
            rating_info  = detect_rating(cover_text)
            report_date  = fn_date or detect_date(cover_text)
            target_price = detect_tp(cover_text)
            company_info = resolve_company_name(ticker, cover_text, fn)

            if not fin_pages and not P_ALLOW_NO_FIN_PAGES:
                result["is_stock"] = False
                result["classification"] = {"document_type": "NO_FIN_PAGES"}
                return result

            price_metrics = get_price_metrics(ticker, report_date, target_price)
            yft           = price_metrics.get("yfinance_ticker", f"{ticker}.TW")

            consensus = build_consensus_block(ticker, yft)

            meta = build_report_metadata(
                fn=fn, ticker=ticker, report_date=report_date,
                broker_info=broker_info, rating_info=rating_info,
                target_price=target_price, company_info=company_info,
                price_metrics=price_metrics, consensus=consensus)

            raw_tables = direct_tables if direct_tables else self._typed_to_tables_fallback(
                cover_typed + fin_typed)
            report_code = meta["report_code"]
            fin_rows = restructure_tables(
                report_code=report_code,
                ticker=ticker, report_date=report_date,
                broker_abbr=broker_info.get("abbr", ""),
                tables=raw_tables, repair=self.repair_m02)

            try:
                ver_result = verify_financial_rows(fin_rows, zero_error=False)
            except RuntimeError as ve:
                ver_result = {"ok": False, "passes": [], "errors": [str(ve)],
                              "warnings": [], "n_pass": 0, "n_error": 1, "n_warn": 0}

            cv_result = run_cross_validation(
                report_code=report_code, meta=meta, db_writer=self.db)

            if not ver_result["ok"] or cv_result["score"] < 60:
                self.ll_db.log_lesson(
                    error_type="LOW_QUALITY",
                    report_code=report_code,
                    content=f"ver_ok={ver_result['ok']} cv_score={cv_result['score']}",
                    confidence=cv_result["score"] / 100)

            self.db.insert_metadata(meta)
            self.db.insert_financial(fin_rows)
            self.db.insert_verify(report_code, ver_result)

            fin_data = self._build_financial_data(fin_rows, consensus)

            full_record = {
                "extraction_info": {
                    "extraction_time": datetime.now().isoformat(),
                    "vrn_version":     __spec_version__,
                    "mode":            "equity_report",
                    "module_version":  __version__,
                    "elapsed_sec":     round(time.time() - t0, 2),
                    "integrate_mode":  _INTEGRATE_STATE.get("mode","none"),
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
            try:
                self.ll_db.log_lesson("EXCEPTION", fn, str(e)[:200])
            except Exception:
                pass

        return result

    def _typed_to_tables_fallback(self, typed_items: List[Dict]) -> List[Dict]:
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

    def _build_financial_data(self, fin_rows: List[FinancialRow],
                               consensus: Dict[str, Any]) -> Dict[str, Any]:
        by_canon: Dict[str, Optional[float]] = {}
        by_canon_period: Dict[str, str] = {}
        src_tags: Dict[str, str] = {}

        def _period_rank(p: str) -> Tuple[int, int]:
            is_est = int(bool(re.search(r"[EeFf]$", p)))
            m = re.search(r"(\d{4})", p)
            yr = int(m.group(1)) if m else 0
            return (1 - is_est, yr)

        for row in fin_rows:
            if row.value is None:
                continue
            canon = row.canonical
            period = row.period or ""
            cur_period = by_canon_period.get(canon, "")
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

    def run(self) -> Dict[str, Any]:
        cfg      = self.cfg
        t_start  = time.time()
        in_dir   = cfg.get("IN_DIR",    P_IN_DIR)
        pdf_temp = cfg.get("PDF_TEMP",  P_PDF_TEMP)
        out_dir  = cfg.get("OUTPUT_DIR",P_OUTPUT_DIR)
        for d in (in_dir, pdf_temp, out_dir):
            mkdir(d)

        workers  = accel_init_full(cfg)
        gov      = self.governor.status(cfg)
        adj_w    = min(workers, gov["adj_workers"])

        # Persist integrate state
        try:
            self.db.insert_integrate_state(_INTEGRATE_STATE)
        except Exception:
            pass

        print()
        print("═" * 76)
        print(f"  VRN MDL001 StockReportPipeline v{__version__}  Spec:{__spec_version__}")
        print(f"  M01 Extract + M02 Verify + M03 Accel  Workers:{adj_w}  Gov:{gov['name']}")
        print(f"  Integrate: {_INTEGRATE_STATE.get('mode','none')}  "
              f"loaded={len(_INTEGRATE_STATE.get('loaded',[]))}/"
              f"{len(_INTEGRATE_STATE.get('loaded',[])) + len(_INTEGRATE_STATE.get('failed',[])) + len(_INTEGRATE_STATE.get('skipped',[]))}")
        print(f"  IN  → {in_dir}")
        print(f"  OUT → {out_dir}")
        print("═" * 76)

        pdfs = sorted(str(p) for p in Path(in_dir).glob("*.pdf") if p.is_file())
        if not pdfs:
            log.warning("[RUN] No PDFs found in input dir")
            return {"status": "no_files", "elapsed": 0}
        log.info(f"[RUN] {len(pdfs)} PDFs found")

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
            gov = self.governor.status(cfg)
            if gov["level"] >= 4:
                adj_w = max(1, gov["adj_workers"])
                time.sleep(0.5)

        elapsed = round(time.time() - t_start, 2)
        stock_results = [r for r in self.all_results if r.get("is_stock")]

        consolidated = {
            "meta": {
                "module": __module_id__, "version": __version__,
                "spec": __spec_version__,
                "timestamp": datetime.now().isoformat(),
                "input_dir": in_dir, "output_dir": out_dir,
                "total_pdfs": len(pdfs), "stock_reports": stock_count,
                "elapsed_sec": elapsed,
                "integrate": dict(_INTEGRATE_STATE),
            },
            "reports": [r.get("record", {}) for r in stock_results if r.get("record")],
        }
        json_path = str(Path(out_dir) / "VRN_Integrated_Reports.json")
        _jwrite(json_path, consolidated)
        log.info(f"[OUTPUT] JSON → {json_path}  ({stock_count} reports)")

        csv_path = str(Path(out_dir) / "VRN_Summary.csv")
        self._write_summary_csv(csv_path, stock_results)
        log.info(f"[OUTPUT] CSV  → {csv_path}")

        self.db.export_parquet(out_dir)

        if cfg.get("HTML_REPORT", P_HTML_REPORT):
            html_path = str(Path(out_dir) / "VRN_Report.html")
            self._write_html(html_path, consolidated, elapsed, adj_w, gov)
            log.info(f"[OUTPUT] HTML → {html_path}  (saved, not opened)")

        print()
        print("═" * 76)
        print(f"  ✅ DONE  {stock_count}/{len(pdfs)} stock reports  elapsed={elapsed}s")
        print("═" * 76)

        return {
            "status": "ok", "elapsed": elapsed,
            "total": len(pdfs), "stock": stock_count,
            "errors": len(self.errors),
            "output_dir": out_dir,
            "integrate": dict(_INTEGRATE_STATE),
        }

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

    def _write_html(self, html_path: str, data: Dict,
                    elapsed: float, workers: int, gov: Dict) -> None:
        total    = data["meta"].get("total_pdfs", 0)
        stock    = data["meta"].get("stock_reports", 0)
        ts       = data["meta"].get("timestamp", "")
        intg     = data["meta"].get("integrate", {})
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
        intg_html = (f"Mode={intg.get('mode','none')}  "
                     f"loaded={len(intg.get('loaded',[]))}  "
                     f"failed={len(intg.get('failed',[]))}  "
                     f"skipped={len(intg.get('skipped',[]))}")
        html = f"""<!DOCTYPE html>
<html lang="zh-TW"><head>
<meta charset="UTF-8">
<title>VRN Integrated Report {ts}</title>
<style>
  body{{font-family:'DM Sans','Noto Sans TC',sans-serif;background:#f5f4f0;color:#1a1918;margin:0;padding:20px}}
  h1{{font-size:1.4em;color:#2c5282;margin-bottom:4px}}
  .meta{{font-size:.85em;color:#555;margin-bottom:8px}}
  .intg{{font-size:.8em;color:#439a9a;margin-bottom:16px;font-family:'DM Mono',monospace}}
  table{{border-collapse:collapse;width:100%;font-size:.82em}}
  th{{background:#4c78a8;color:#fff;padding:6px 8px;text-align:left}}
  tr:nth-child(even){{background:#eeecea}}
  td{{padding:5px 8px;border-bottom:1px solid #ddd}}
</style>
</head><body>
<h1>VRN Integrated Pipeline · {__spec_version__} · v{__version__}</h1>
<div class="meta">
  Generated: {ts} ·
  PDFs: {total} · Stock: {stock} ·
  Elapsed: {elapsed}s · Workers: {workers} · Gov: {gov.get('name','')}
</div>
<div class="intg">Integrate: {intg_html}</div>
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
# ⚓ ANC-V  CLI
# [VIA:ANCHOR:ANC-V:CLI]
# ════════════════════════════════════════════════════════════════════════════

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
    ap.add_argument("--integrate", default=None,
                    choices=["none","aegis","celer","supportive","full"],
                    help="Integration mode (overrides VRN_INTEGRATE env)")
    ap.add_argument("--standalone", action="store_true",
                    help="Force standalone (== --integrate none)")
    ap.add_argument("--probe",     action="store_true",
                    help="Probe supportive modules and exit")
    ap.add_argument("--selftest",  action="store_true",
                    help="Run self-test and exit")
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
        "INTEGRATE":    "none" if args.standalone else args.integrate,
        "PROBE":        args.probe,
        "SELFTEST":     args.selftest,
    }


def run_self_test() -> int:
    """4-phase debug chain check."""
    print("═" * 76)
    print(f"  VRN MDL001 SELF-TEST  v{__version__}")
    print("═" * 76)
    fails = 0
    try:
        assert __version__ == "2.0.0"
        assert TW_MOTHER_REGEX.match("2330")
        assert TW_BLOOMBERG_REGEX.search("2330 TT")
        assert TW_YFINANCE_REGEX.search("2330.TW")
        print("  ✅ P1 IMPORTS + REGEX_LOCK")
    except Exception as e:
        print(f"  ❌ P1: {e}"); fails += 1
    try:
        assert detect_ticker("2330_TSMC_Buy_Report") == "2330"
        assert detect_broker("摩根士丹利")["abbr"] == "MS"
        assert detect_rating("給予買進評等")["category"] == "buy"
        assert detect_date("2026-04-15") == "2026-04-15"
        assert detect_tp("目標價: NT$1000") == "1000"
        print("  ✅ P2 DETECTORS")
    except Exception as e:
        print(f"  ❌ P2: {e}"); fails += 1
    try:
        is_s, sc, _ = is_stock_report("2330_MS_Buy.pdf",
            "目標價 NT$1000 給予買進評等 2330", "2330")
        assert is_s and sc >= 15
        meta = build_report_metadata(
            fn="test.pdf", ticker="2330", report_date="2026-04-15",
            broker_info={"full":"MS","abbr":"MS"},
            rating_info={"rating":"買進","category":"buy"},
            target_price="1000", company_info={"name":"台積電","name_en":""},
            price_metrics={"yfinance_ticker":"2330.TW","adj_close":900,"upside_pct":11.1,"upside_target_source":"Report"},
            consensus={"consensus_target_mean":1050,"consensus_rating":"buy","analyst_count":15})
        assert meta["report_code"].startswith("MS-2330-")
        assert meta["upside_pct"] == 11.1
        print("  ✅ P3 CLASSIFY + METADATA")
    except Exception as e:
        print(f"  ❌ P3: {e}"); fails += 1
    try:
        rows = [
            FinancialRow("RC1","2330","2026-04-15","MS",0,"營業收入","revenue","income_statement","2025",1000.0),
            FinancialRow("RC1","2330","2026-04-15","MS",0,"營業成本","cogs","income_statement","2025",400.0),
            FinancialRow("RC1","2330","2026-04-15","MS",0,"毛利","gross_profit","income_statement","2025",600.0),
            FinancialRow("RC1","2330","2026-04-15","MS",0,"EPS","eps","income_statement","2025",30.0),
        ]
        ver = verify_financial_rows(rows, zero_error=False)
        assert ver["ok"], f"verify failed: {ver}"
        cv = run_cross_validation("RC1", {
            "target_price":1000,"consensus_target_mean":1050,
            "rating_cat":"buy","consensus_rating":"buy",
            "analyst_count":15,"consensus_target_high":1100,
            "consensus_target_low":900,"consensus_rating_mean":2.0
        })
        assert cv["score"] >= 90, f"cv score too low: {cv}"
        print(f"  ✅ P4 M02 verify={ver['n_pass']}P/{ver['n_error']}E  CV score={cv['score']}")
    except Exception as e:
        print(f"  ❌ P4: {e}"); fails += 1

    # Phase 5: Integrate probe (no load)
    try:
        probe = _probe_supportive_modules()
        present = sum(1 for v in probe.values() if v)
        absent  = sum(1 for v in probe.values() if not v)
        print(f"  ✅ P5 PROBE  present={present} absent={absent} (no module loaded)")
    except Exception as e:
        print(f"  ❌ P5: {e}"); fails += 1

    print("═" * 76)
    if fails == 0:
        print("  ✅ READY — 0 fail")
        return 0
    elif fails <= 2:
        print(f"  ⚠️  NEAR-READY — {fails} fail")
        return 1
    else:
        print(f"  ❌ NOT-READY — {fails} fail")
        return 2


def run_probe() -> int:
    """Probe supportive modules without loading any of them."""
    print("═" * 76)
    print("  VRN MDL001 SUPPORTIVE PROBE (find_spec only — no load)")
    print("═" * 76)
    print(f"  Search dirs:")
    for d in _via_search_dirs:
        exists = "✅" if Path(d).exists() else "⬜"
        print(f"    {exists} {d}")
    print(f"\n  Python supportive modules:")
    probe = _probe_supportive_modules()
    for name, found in probe.items():
        mark = "✅" if found else "⬜"
        print(f"    {mark} {name}")
    print(f"\n  PowerShell tools (existence only):")
    sup_dir = Path(P_SUPPORTIVE_MODULE_DIR)
    for ps_name in P_SUPPORTIVE_PS_TOOLS:
        ps_path = sup_dir / ps_name
        mark = "✅" if ps_path.exists() else "⬜"
        print(f"    {mark} {ps_name}")
    print("═" * 76)
    return 0

# ════════════════════════════════════════════════════════════════════════════
# ⚓ ANC-W  MAIN
# [VIA:ANCHOR:ANC-W:MAIN]
# ════════════════════════════════════════════════════════════════════════════

def main() -> None:
    cfg = build_cfg_from_args()

    if cfg.get("PROBE"):
        sys.exit(run_probe())

    if cfg.get("SELFTEST"):
        # Self-test 不需要整合外部模組
        sys.exit(run_self_test())

    # Resolve integrate mode (CLI > env > default)
    mode = _resolve_integrate_mode(cfg.get("INTEGRATE"))
    try:
        integrate_supportive(mode, verbose=P_INTEGRATE_VERBOSE)
    except KeyboardInterrupt:
        print("\n[INTEGRATE] interrupted by user — falling back to standalone")
        integrate_supportive("none", verbose=False)
    except Exception as e:
        print(f"\n[INTEGRATE] error ({type(e).__name__}: {e}) — falling back to standalone")
        integrate_supportive("none", verbose=False)

    pipeline = VRNIntegratedPipeline(cfg)
    result   = pipeline.run()
    if result.get("status") == "no_files":
        log.warning("[MAIN] No PDF files found. Check --in_dir.")
        sys.exit(1)


if __name__ == "__main__":
    main()
