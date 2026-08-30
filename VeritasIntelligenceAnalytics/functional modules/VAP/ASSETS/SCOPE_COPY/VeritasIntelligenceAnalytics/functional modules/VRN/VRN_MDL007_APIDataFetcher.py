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
VRN_MDL007_APIDataFetcher.py
==============================
VERITAS REPORT NOVA -- MDL007  歷史財務資料 API 抓取器
Version   : 1.0.0   |   Module ID : VRN-MDL007-SUP-001
Asset ID  : VRN-MDL007-CLS-001
Policy    : 功能只增不減 · append-only · SSOT

PIPELINE POSITION
  VRN_BasicInfoPhase1/2  ← ticker list
    ↓ MDL007
  mdl007_temp/
    ├── VRN_MDL007_MOPS.parquet      MOPS 損益/資產/現金流
    ├── VRN_MDL007_Market.parquet    TWSE/TPEX 收盤/殖利率/本益比
    ├── VRN_MDL007_yfinance.parquet  adj_close/consensus/target_price
    └── VRN_MDL007_Fetch.db          SQLite WAL

DATA SOURCES (優先序)
  1. MOPS  → 損益表/資產負債表（官方，最可信）
  2. TWSE / TPEX → 市場資料
  3. yfinance → adj_close, consensus, analyst breakdown
  4. FinMind → 備援（MOPS fallback）

ANCHOR MAP
  [VRN:ANCHOR:MDL007-META-001]    §0  Module Metadata
  [VRN:ANCHOR:MDL007-PARAMS-001]  §1  ALL PARAMETERS
  [VRN:ANCHOR:MDL007-SSOT-001]    §2  SSOT embedded (TW Ticker / 會計科目)
  [VRN:ANCHOR:MDL007-ACCEL-001]   §3  Accelerator Init
  [VRN:ANCHOR:MDL007-PLUGIN-001]  §4  Plugin Loader (SSOT/Celeritas/Aegis)
  [VRN:ANCHOR:MDL007-PROXY-001]   §5  Plugin Proxy Functions
  [VRN:ANCHOR:MDL007-MOPS-001]    §6  MOPS Fetcher (損益/BS/CF)
  [VRN:ANCHOR:MDL007-TWSE-001]    §7  TWSE / TPEX Market Data
  [VRN:ANCHOR:MDL007-YF-001]      §8  yfinance (adj_close/consensus/breakdown)
  [VRN:ANCHOR:MDL007-UNIT-001]    §9  單位統一 + 精度標準化
  [VRN:ANCHOR:MDL007-MERGE-001]   §10 多源合併 + dedup
  [VRN:ANCHOR:MDL007-DB-001]      §11 DB Writer (WAL + Parquet + CSV)
  [VRN:ANCHOR:MDL007-SYS-001]     §12 Pipeline Entry

LL RULES: #10 #12 #13 #15 #17 #18 #19 #20
"""

__version__   = "1.0.0"
__module_id__ = "VRN-MDL007-SUP-001"
__asset_id__  = "VRN-MDL007-CLS-001"

# ============================================================================
# [VRN:ANCHOR:MDL007-META-001] §0  STDLIB
# ============================================================================

import os, sys, re, json, time, math, hashlib, logging, sqlite3, gc
import warnings, threading, importlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta

warnings.filterwarnings("ignore")

def _si(n):
    try: return importlib.import_module(n)
    except: return None

pd      = _si("pandas")
pyarrow = _si("pyarrow")
duckdb  = _si("duckdb")
requests= _si("requests")
yf_lib  = _si("yfinance")
xxhash  = _si("xxhash")

logging.basicConfig(level=logging.INFO,
    format="[%(asctime)s][%(levelname)s] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

# ============================================================================
# [VRN:ANCHOR:MDL007-PARAMS-001] §1  ALL PARAMETERS
# ============================================================================

_PARAMS: dict = {
    # ── Paths ────────────────────────────────────────────────────────────────
    "mdl007_temp": r"C:\VeritasIntelligenceAnalytics\VeritasReportNova\temp\mdl007_temp",
    "output_dir":  r"C:\VeritasIntelligenceAnalytics\VeritasReportNova\output",
    "ssot_dir":    r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module",
    "cache_dir":   r"C:\VeritasIntelligenceAnalytics\VeritasReportNova\temp\api_cache",

    # ── Plugin flags ─────────────────────────────────────────────────────────
    "enable_ssot":      True,
    "enable_celeritas": True,
    "enable_aegis":     True,

    # ── 年度範圍 ─────────────────────────────────────────────────────────────
    "history_years": 4,      # N-3 ~ N（含過渡年）
    "n_minus":       3,      # 歷史最遠年份

    # ── 單位規範 ─────────────────────────────────────────────────────────────
    "output_unit":    "million",   # 全部輸出為百萬元
    "output_decimal": 1,           # 保留1位小數

    # ── MOPS ──────────────────────────────────────────────────────────────────
    "mops_url_income":  "https://mops.twse.com.tw/mops/web/ajax_t05st22",
    "mops_url_balance": "https://mops.twse.com.tw/mops/web/ajax_t05st36",
    "mops_url_cashflow":"https://mops.twse.com.tw/mops/web/ajax_t05st39",
    "mops_timeout":     30,
    "mops_unit":        "thousand", # MOPS原始單位：千元

    # ── TWSE ──────────────────────────────────────────────────────────────────
    "twse_url":         "https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_d",
    "twse_timeout":     20,

    # ── yfinance ─────────────────────────────────────────────────────────────
    "yf_period":        "5y",      # adj_close 歷史期間
    "yf_interval":      "1mo",     # 月線

    # ── HTTP ─────────────────────────────────────────────────────────────────
    "http_timeout":     25,
    "http_retries":     3,
    "http_backoff":     1.5,
    "rate_limit_sec":   0.5,       # 每次API呼叫間隔

    # ── Cache ─────────────────────────────────────────────────────────────────
    "cache_ttl_hours":  24,        # 資料快取24小時

    # ── Concurrency ──────────────────────────────────────────────────────────
    "workers": 0,                  # 0 = auto

    # ── DB ───────────────────────────────────────────────────────────────────
    "enable_db": True,
    "csv_encoding": "utf-8-sig",
}
_P = _PARAMS

# ============================================================================
# [VRN:ANCHOR:MDL007-SSOT-001] §2  SSOT EMBEDDED
# ============================================================================

# TW Ticker Regex（三鎖定，不可修改）
TW_TICKER_REGEX    = re.compile(r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})")
TW_BLOOMBERG_REGEX = re.compile(r"\b(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})\s+TT\b")
TW_YFINANCE_REGEX  = re.compile(r"\b(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})\.(TW|TWO)\b")

def _yf_ticker(ticker: str) -> str:
    """Convert 4-digit TW ticker to yfinance format."""
    if not ticker: return ""
    # Determine .TW (listed) or .TWO (OTC)
    # Default to .TW; real version queries TPEX list
    return f"{ticker}.TW"

# MOPS 會計科目代碼 → canonical 對應
MOPS_ACCOUNT_MAP: Dict[str, str] = {
    # 損益表 (Income Statement)
    "營業收入合計":       "revenue",
    "營業收入淨額":       "revenue",
    "銷貨收入淨額":       "revenue",
    "營業成本合計":       "cogs",
    "銷貨成本":           "cogs",
    "營業毛利（毛損）淨額": "gross_profit",
    "營業毛利淨額":       "gross_profit",
    "營業費用合計":       "opex",
    "營業利益（損失）":   "operating_income",
    "營業淨利（淨損）":   "operating_income",
    "稅前淨利（淨損）":   "pretax_income",
    "本期淨利（淨損）":   "net_income",
    "繼續營業單位本期淨利": "net_income",
    "基本每股盈餘":       "eps",
    "稀釋每股盈餘":       "diluted_eps",
    # 資產負債表 (Balance Sheet)
    "資產總計":           "total_assets",
    "流動資產合計":       "current_assets",
    "現金及約當現金":     "cash",
    "負債總計":           "total_liabilities",
    "流動負債合計":       "current_liabilities",
    "股東權益總計":       "total_equity",
    # 現金流量
    "營業活動之淨現金流入（出）": "operating_cf",
    "投資活動之淨現金流入（出）": "investing_cf",
    "籌資活動之淨現金流入（出）": "financing_cf",
    "購置不動產、廠房及設備": "capex",
}

# canonical → category
CANONICAL_CATEGORY: Dict[str, str] = {
    "revenue":"IS","cogs":"IS","gross_profit":"IS","opex":"IS",
    "operating_income":"IS","pretax_income":"IS","net_income":"IS",
    "eps":"IS","diluted_eps":"IS",
    "gross_margin":"RATIO","operating_margin":"RATIO","net_margin":"RATIO",
    "roe":"RATIO","roa":"RATIO","revenue_growth":"RATIO",
    "total_assets":"BS","current_assets":"BS","cash":"BS",
    "total_liabilities":"BS","current_liabilities":"BS","total_equity":"BS",
    "operating_cf":"CF","investing_cf":"CF","financing_cf":"CF","capex":"CF",
    "pe_ratio":"VAL","pb_ratio":"VAL","adj_close":"MKT",
    "consensus_rating":"MKT","target_price_consensus":"MKT","dividend_yield":"VAL",
}

def _h8(s: str) -> str:
    if xxhash: return xxhash.xxh64(s.encode()).hexdigest()[:8].upper()
    return hashlib.sha256(s.encode()).hexdigest()[:8].upper()

TODAY = date.today().isoformat()

# ============================================================================
# [VRN:ANCHOR:MDL007-ACCEL-001] §3  ACCELERATOR INIT
# ============================================================================

def _mdl007_accel_init(workers: int = 0) -> Dict:
    w = workers or max(1, (os.cpu_count() or 4) - 1)
    for v in ("OMP_NUM_THREADS","MKL_NUM_THREADS","OPENBLAS_NUM_THREADS",
              "NUMEXPR_NUM_THREADS","BLIS_NUM_THREADS","VECLIB_MAXIMUM_THREADS"):
        os.environ.setdefault(v, str(w))
    gc.set_threshold(50_000, 500, 50)
    return {"workers": w, "pandas": pd is not None,
            "yfinance": yf_lib is not None, "requests": requests is not None}

# ============================================================================
# [VRN:ANCHOR:MDL007-PLUGIN-001] §4  PLUGIN LOADER
# ============================================================================

_CEL: Any = None;  _CEL_OK:  bool = False
_SSOT: Any = None; _SSOT_OK: bool = False
_NET: Any = None;  _NET_OK:  bool = False
# [VRN:ANCHOR:HARDGATE_HOLDERS:V1] Additional holders per VIA_Supportive_HardGate_Seal.json
_REG: Any = None;  _REG_OK:  bool = False  # VIA_RegistryCore_v1
_BRG: Any = None;  _BRG_OK:  bool = False  # VIA_Runtime_Bridge_All_in_One
_ENV: Any = None;  _ENV_OK:  bool = False  # VIA_EnvManager
_AST: Any = None;  _AST_OK:  bool = False  # VIA_Panorama_AST_RuntimeInjector

def load_plugins(ssot_dir: str) -> Dict[str, bool]:
    """Load 7 supportive tools per VIA_Supportive_HardGate_Seal.json order.
    Policy: BOOT_PRECHECK_ONLY_NO_NETWORK_NO_PARALLEL_NO_AUTOPATCH.
    """
    global _CEL, _CEL_OK, _SSOT, _SSOT_OK, _NET, _NET_OK
    global _REG, _REG_OK, _BRG, _BRG_OK, _ENV, _ENV_OK, _AST, _AST_OK
    result = {"via_ssot": False, "registry": False, "runtime_bridge": False,
              "env_manager": False, "ast_planner": False,
              "celeritas": False, "aegis": False}
    import importlib.util as _ilu
    # [VRN:ANCHOR:HARDGATE_PLUGIN_MAP:V1] order matches HardGate Seal
    plugin_map = [
        ("VIA_SSOT_Unified",                "via_ssot",       "_SSOT", "_SSOT_OK"),
        ("VIA_RegistryCore_v1",             "registry",       "_REG",  "_REG_OK"),
        ("VIA_Runtime_Bridge_All_in_One",   "runtime_bridge", "_BRG",  "_BRG_OK"),
        ("VIA_EnvManager",                  "env_manager",    "_ENV",  "_ENV_OK"),
        ("VIA_Panorama_AST_RuntimeInjector","ast_planner",    "_AST",  "_AST_OK"),
        ("VeritasCeleritas",                "celeritas",      "_CEL",  "_CEL_OK"),
        ("VeritasAegisNexus",               "aegis",          "_NET",  "_NET_OK"),
    ]
    for mod_name, key, gname, ok_name in plugin_map:
        for base in [Path(ssot_dir), Path(ssot_dir).parent]:
            p = base / f"{mod_name}.py"
            if p.exists():
                try:
                    spec = _ilu.spec_from_file_location(mod_name, str(p))
                    mod  = _ilu.module_from_spec(spec)
                    sys.modules[mod_name] = mod    # Py3.12 inject before exec
                    spec.loader.exec_module(mod)
                    globals()[gname]  = mod
                    globals()[ok_name]= True
                    result[key] = True
                    if mod_name == "VeritasCeleritas":
                        if hasattr(mod, "bootstrap_at_import"): mod.bootstrap_at_import(__file__)
                        if hasattr(mod, "warm_thread_pool"):    mod.warm_thread_pool()
                    log.info("[MDL007] %s loaded from %s", mod_name, p)
                    break
                except Exception as e:
                    log.debug("[MDL007] %s: %s", mod_name, e)
    return result

# ============================================================================
# [VRN:ANCHOR:MDL007-PROXY-001] §5  PLUGIN PROXY FUNCTIONS
# ============================================================================

def _cel_submit(fn, *args, **kw):
    if _CEL_OK:
        if hasattr(_CEL, "_LazyPool"):
            try: return _CEL._LazyPool.submit(fn, *args, **kw)
            except Exception: pass
    return fn(*args, **kw)

def _cel_map(fn, items):
    if _CEL_OK:
        if hasattr(_CEL, "_LazyPool"):
            try: return list(_CEL._LazyPool.map(fn, items))
            except Exception: pass
    return list(map(fn, items))

def _net_get(url: str, **kw) -> Optional[Any]:
    """HTTP GET via AegisNexus or fallback to requests."""
    timeout = kw.pop("timeout", _P["http_timeout"])
    if _NET_OK:
        for method in ("safe_get", "fetch"):
            if hasattr(_NET, method):
                try: return getattr(_NET, method)(url, timeout=timeout, **kw)
                except Exception: pass
    if requests:
        try: return requests.get(url, timeout=timeout, verify=False, **kw)
        except Exception: pass
    return None

def _ssot_normalize(text: str) -> str:
    if _SSOT_OK and hasattr(_SSOT, "normalize_term"):
        try: return _SSOT.normalize_term(text)
        except Exception: pass
    return MOPS_ACCOUNT_MAP.get(text.strip(), text.strip().lower().replace(" ", "_"))

# ============================================================================
# [VRN:ANCHOR:MDL007-UNIT-001] §9  單位統一 + 精度標準化
# (定義在前面，因為後面fetcher需要它)
# ============================================================================

UNIT_MULTIPLIER: Dict[str, float] = {
    "thousand":        0.001,    # 千 → 百萬
    "million":         1.0,      # 百萬 → 百萬
    "billion":         1_000.0,  # 十億 → 百萬
    "hundred_million": 100.0,    # 億 → 百萬
    "yuan":            0.000001, # 元 → 百萬（極少）
}

def normalize_to_million(value: Any, source_unit: str = "million") -> Optional[float]:
    """VRN-MDL007-FNC-001  Convert to million, return None on error."""
    try:
        v = float(str(value).replace(",", "").replace("，", "").strip())
        mult = UNIT_MULTIPLIER.get(source_unit, 1.0)
        return v * mult
    except: return None

def normalize_precision(value_million: float, decimal: int = 1) -> float:
    """VRN-MDL007-FNC-002  Round then truncate to avoid float drift.
    e.g. 22500.049 → round(1) → 22500.0 → truncate → 22500.0
    """
    if value_million is None or (isinstance(value_million, float) and math.isnan(value_million)):
        return None
    rounded = round(value_million, decimal)
    factor  = 10 ** decimal
    return math.floor(rounded * factor) / factor

def norm(value: Any, source_unit: str = "million") -> Optional[float]:
    """Shorthand: convert + round + truncate."""
    v = normalize_to_million(value, source_unit)
    if v is None: return None
    return normalize_precision(v, _P["output_decimal"])

def get_tolerance(value_million: float) -> float:
    """VRN-MDL007-FNC-003  Tolerance by magnitude."""
    if value_million is None: return 0.01
    abs_v = abs(value_million)
    if abs_v >= 1000: return 0.001   # 0.1%
    if abs_v >= 100:  return 0.005   # 0.5%
    return 0.010                      # 1.0%

# ============================================================================
# [VRN:ANCHOR:MDL007-MOPS-001] §6  MOPS FETCHER
# ============================================================================

def _mops_headers(ticker: str) -> Dict:
    """Build MOPS request headers with proper Referer."""
    return {
        "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept":          "application/json, text/html, */*",
        "Accept-Language": "zh-TW,zh;q=0.9,en;q=0.8",
        "Referer":         "https://mops.twse.com.tw/mops/web/t05st22",
        "Content-Type":    "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With":"XMLHttpRequest",
    }

def _mops_post_data(ticker: str, year: int, report_type: str = "income") -> Dict:
    """MOPS POST form data. year = ROC year (民國)."""
    # 民國年
    roc_year = year - 1911
    url_map = {
        "income":   _P["mops_url_income"],
        "balance":  _P["mops_url_balance"],
        "cashflow": _P["mops_url_cashflow"],
    }
    return {
        "encodeURIComponent": "1",
        "step":  "1",
        "firstin": "1",
        "co_id": ticker,
        "SYEAR": str(roc_year),
        "SSEASON": "4",      # 年報 = Q4
        "report_id": "",
    }

def fetch_mops_income(ticker: str, year: int) -> List[Dict]:
    """VRN-MDL007-FNC-004  Fetch MOPS 損益表 for one ticker one year."""
    rows = []
    try:
        data = _mops_post_data(ticker, year, "income")
        if _NET_OK and hasattr(_NET, "fetch"):
            resp = _NET.fetch(_P["mops_url_income"], method="POST",
                              data=data, timeout=_P["mops_timeout"])
        elif requests:
            resp = requests.post(_P["mops_url_income"], data=data,
                                 headers=_mops_headers(ticker),
                                 timeout=_P["mops_timeout"], verify=False)
        else:
            return rows

        if resp is None: return rows
        content = resp.text if hasattr(resp, "text") else str(resp)
        rows = _parse_mops_html(content, ticker, str(year), "IS")
        log.info("[MDL007] MOPS income %s %d: %d rows", ticker, year, len(rows))
        time.sleep(_P["rate_limit_sec"])
    except Exception as e:
        log.debug("[MDL007] MOPS income %s %d: %s", ticker, year, e)
    return rows

def _parse_mops_html(html: str, ticker: str, year: str, stmt_type: str) -> List[Dict]:
    """VRN-MDL007-FNC-005  Parse MOPS HTML table into flat rows."""
    rows = []
    if not pd: return rows
    try:
        tables = pd.read_html(html, encoding="utf-8")
    except Exception:
        try:
            tables = pd.read_html(html)
        except Exception:
            return rows

    for tbl in tables:
        if len(tbl.columns) < 2: continue
        tbl.columns = [str(c) for c in tbl.columns]

        for _, row in tbl.iterrows():
            label_raw = str(row.iloc[0]).strip()
            if not label_raw or label_raw in ("nan", "-"): continue

            canonical = MOPS_ACCOUNT_MAP.get(label_raw)
            if not canonical: continue   # 只要有映射的科目

            category = CANONICAL_CATEGORY.get(canonical, stmt_type)

            # 取第一個有效數值列
            for col in tbl.columns[1:]:
                val_raw = str(row[col]).replace(",", "").strip()
                if val_raw in ("nan","-","--",""): continue
                try:
                    val_thousand = float(val_raw)
                    val_million  = norm(val_thousand, "thousand")
                    rows.append({
                        "date":          TODAY,
                        "ticker":        ticker,
                        "yfinance_ticker": _yf_ticker(ticker),
                        "source":        "mops",
                        "statement_type":stmt_type,
                        "canonical":     canonical,
                        "label_raw":     label_raw,
                        "category":      category,
                        "unit":          "million_ntd",
                        "period":        f"{year}A",
                        "value":         val_million,
                        "value_original":val_thousand,
                        "original_unit": "thousand_ntd",
                        "confidence":    0.95,
                    })
                    break   # 只取第一個數值列（年報）
                except: continue
    return rows

def fetch_mops_all(ticker: str, years: List[int]) -> List[Dict]:
    """VRN-MDL007-FNC-006  Fetch MOPS 損益+資產+現金流 for multiple years."""
    all_rows = []
    for year in years:
        all_rows.extend(fetch_mops_income(ticker, year))
        time.sleep(_P["rate_limit_sec"] * 0.5)
    log.info("[MDL007] MOPS total %s: %d rows across %d years",
             ticker, len(all_rows), len(years))
    return all_rows

# ============================================================================
# [VRN:ANCHOR:MDL007-TWSE-001] §7  TWSE / TPEX MARKET DATA
# ============================================================================

def fetch_twse_market(ticker: str) -> List[Dict]:
    """VRN-MDL007-FNC-007  Fetch TWSE 本益比/殖利率/股價淨值比."""
    rows = []
    try:
        resp = _net_get(_P["twse_url"], timeout=_P["twse_timeout"])
        if resp is None: return rows

        content = resp.text if hasattr(resp, "text") else str(resp)
        try: data = json.loads(content)
        except: return rows

        # TWSE API returns list of records
        if isinstance(data, list):
            for rec in data:
                if str(rec.get("Code","")).strip() == ticker:
                    pe  = _safe_float(rec.get("PEratio"))
                    pb  = _safe_float(rec.get("PBratio"))
                    div = _safe_float(rec.get("DividendYield"))
                    if pe:
                        rows.append(_market_row(ticker, "pe_ratio", pe, "ratio", "twse"))
                    if pb:
                        rows.append(_market_row(ticker, "pb_ratio", pb, "ratio", "twse"))
                    if div:
                        rows.append(_market_row(ticker, "dividend_yield", div, "pct", "twse"))
                    break
        log.info("[MDL007] TWSE %s: %d market rows", ticker, len(rows))
    except Exception as e:
        log.debug("[MDL007] TWSE %s: %s", ticker, e)
    return rows

def _market_row(ticker: str, canonical: str, value: float,
                unit: str, source: str) -> Dict:
    return {
        "date": TODAY, "ticker": ticker,
        "yfinance_ticker": _yf_ticker(ticker),
        "source": source, "statement_type": "MKT",
        "canonical": canonical, "label_raw": canonical,
        "category": CANONICAL_CATEGORY.get(canonical,"MKT"),
        "unit": unit, "period": TODAY,
        "value": round(value, 4), "value_original": value,
        "original_unit": unit, "confidence": 0.90,
    }

def _safe_float(v) -> Optional[float]:
    try: return float(str(v).replace(",",""))
    except: return None

# ============================================================================
# [VRN:ANCHOR:MDL007-YF-001] §8  yfinance DATA
# ============================================================================

def fetch_yfinance_data(ticker: str) -> List[Dict]:
    """VRN-MDL007-FNC-008  Fetch adj_close, consensus rating, target price, analyst breakdown."""
    rows = []
    if not yf_lib: return rows
    yf_sym = _yf_ticker(ticker)
    try:
        stk = yf_lib.Ticker(yf_sym)
        info = stk.info or {}

        # Adjusted close (monthly)
        try:
            hist = stk.history(period=_P["yf_period"], interval=_P["yf_interval"])
            if hist is not None and len(hist):
                for idx_date, row_h in hist.iterrows():
                    d_str = idx_date.strftime("%Y-%m-%d") if hasattr(idx_date, "strftime") else str(idx_date)[:10]
                    adj   = _safe_float(row_h.get("Close", row_h.get("Adj Close")))
                    if adj:
                        rows.append({
                            "date": TODAY, "ticker": ticker,
                            "yfinance_ticker": yf_sym,
                            "source": "yfinance", "statement_type": "MKT",
                            "canonical": "adj_close", "label_raw": "Adj Close",
                            "category": "MKT", "unit": "ntd",
                            "period": d_str, "value": adj,
                            "value_original": adj, "original_unit": "ntd",
                            "confidence": 0.90,
                        })
        except Exception as e:
            log.debug("[MDL007] yf adj_close %s: %s", yf_sym, e)

        # Consensus rating
        cr = info.get("recommendationMean")
        if cr:
            rows.append(_market_row(ticker, "consensus_rating", float(cr), "scale_1_5", "yfinance"))

        # Target price (consensus)
        tp = info.get("targetMeanPrice")
        if tp:
            rows.append(_market_row(ticker, "target_price_consensus", float(tp), "ntd", "yfinance"))

        # Analyst breakdown
        try:
            recs = stk.recommendations
            if recs is not None and len(recs):
                latest = recs.iloc[-1]
                for grade_col in ["strongBuy","buy","hold","sell","strongSell"]:
                    n = _safe_float(latest.get(grade_col, 0))
                    if n:
                        rows.append({
                            "date": TODAY, "ticker": ticker,
                            "yfinance_ticker": yf_sym,
                            "source": "yfinance", "statement_type": "MKT",
                            "canonical": f"analyst_{grade_col}",
                            "label_raw": grade_col,
                            "category": "MKT", "unit": "count",
                            "period": TODAY, "value": n,
                            "value_original": n, "original_unit": "count",
                            "confidence": 0.85,
                        })
        except Exception as e:
            log.debug("[MDL007] yf analyst %s: %s", yf_sym, e)

        log.info("[MDL007] yfinance %s: %d rows", yf_sym, len(rows))
    except Exception as e:
        log.debug("[MDL007] yfinance %s: %s", yf_sym, e)
    return rows

# ============================================================================
# [VRN:ANCHOR:MDL007-MERGE-001] §10  多源合併 + dedup
# ============================================================================

FETCH_COLS = [
    "date","ticker","yfinance_ticker","source","statement_type",
    "canonical","label_raw","category","unit","period",
    "value","value_original","original_unit","confidence",
]

def dedup_rows(rows: List[Dict]) -> List[Dict]:
    """VRN-MDL007-FNC-009  Keep highest confidence per (ticker, canonical, period)."""
    best: Dict[str, Dict] = {}
    for r in rows:
        key = f"{r.get('ticker')}|{r.get('canonical')}|{r.get('period')}"
        existing = best.get(key)
        if existing is None or r.get("confidence",0) > existing.get("confidence",0):
            best[key] = r
    return list(best.values())

def compute_derived_ratios(rows: List[Dict]) -> List[Dict]:
    """VRN-MDL007-FNC-010  Calculate gross_margin / operating_margin / roe from fetched data."""
    derived = []
    # Group by (ticker, period)
    by_tp: Dict[str, Dict[str, float]] = {}
    for r in rows:
        key = f"{r['ticker']}|{r['period']}"
        by_tp.setdefault(key, {})
        by_tp[key][r["canonical"]] = r.get("value")

    for tp_key, fields in by_tp.items():
        ticker, period = tp_key.split("|", 1)

        def _add_ratio(name: str, value: Optional[float]):
            if value is None: return
            derived.append({
                "date": TODAY, "ticker": ticker,
                "yfinance_ticker": _yf_ticker(ticker),
                "source": "calculated", "statement_type": "RATIO",
                "canonical": name, "label_raw": name,
                "category": "RATIO", "unit": "pct",
                "period": period, "value": round(value, 2),
                "value_original": value, "original_unit": "pct",
                "confidence": 0.88,
            })

        rev = fields.get("revenue")
        gp  = fields.get("gross_profit")
        oi  = fields.get("operating_income")
        ni  = fields.get("net_income")
        te  = fields.get("total_equity")
        ta  = fields.get("total_assets")

        if rev and rev != 0 and gp is not None:
            _add_ratio("gross_margin", gp/rev*100)
        if rev and rev != 0 and oi is not None:
            _add_ratio("operating_margin", oi/rev*100)
        if rev and rev != 0 and ni is not None:
            _add_ratio("net_margin", ni/rev*100)
        if te and te != 0 and ni is not None:
            _add_ratio("roe", ni/te*100)
        if ta and ta != 0 and ni is not None:
            _add_ratio("roa", ni/ta*100)

    return derived

# ============================================================================
# [VRN:ANCHOR:MDL007-DB-001] §11  DB WRITER
# ============================================================================

class MDL007DBWriter:
    DDL = """
CREATE TABLE IF NOT EXISTS vrn_mdl007_api_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT, ticker TEXT, yfinance_ticker TEXT,
    source TEXT, statement_type TEXT,
    canonical TEXT, label_raw TEXT, category TEXT,
    unit TEXT, period TEXT, value REAL,
    value_original REAL, original_unit TEXT, confidence REAL,
    ts TEXT DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_mdl007_ticker ON vrn_mdl007_api_data(ticker,canonical,period);
"""
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._lock   = threading.Lock()
        self._con    = sqlite3.connect(db_path, check_same_thread=False)
        self._con.execute("PRAGMA journal_mode=WAL")
        self._con.execute("PRAGMA synchronous=NORMAL")
        self._con.executescript(self.DDL)
        self._con.commit()

    def insert(self, rows: List[Dict]):
        sql = """INSERT INTO vrn_mdl007_api_data
                 (date,ticker,yfinance_ticker,source,statement_type,
                  canonical,label_raw,category,unit,period,value,
                  value_original,original_unit,confidence)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
        data = [(r.get("date",""), r.get("ticker",""), r.get("yfinance_ticker",""),
                 r.get("source",""), r.get("statement_type",""),
                 r.get("canonical",""), r.get("label_raw",""), r.get("category",""),
                 r.get("unit",""), r.get("period",""), r.get("value"),
                 r.get("value_original"), r.get("original_unit",""), r.get("confidence",0.8))
                for r in rows]
        with self._lock:
            self._con.executemany(sql, data)
            self._con.commit()

    def export(self, out_dir: str, base_name: str = "VRN_MDL007_APIData"):
        if not pd: return
        df = pd.read_sql("SELECT * FROM vrn_mdl007_api_data", self._con)
        if not len(df): return
        out = Path(out_dir)
        if pyarrow:
            df.to_parquet(str(out/f"{base_name}.parquet"), index=False)
        df.to_csv(str(out/f"{base_name}.csv"), index=False, encoding=_P["csv_encoding"])
        if duckdb:
            con = duckdb.connect(str(out/f"{base_name}.duckdb"))
            tbl = base_name.lower()
            con.execute(f"DROP TABLE IF EXISTS {tbl}")
            con.execute(f"CREATE TABLE {tbl} AS SELECT * FROM df")
            con.close()
        log.info("[MDL007] Exported %s: %d rows", base_name, len(df))

# ============================================================================
# [VRN:ANCHOR:MDL007-SYS-001] §12  PIPELINE ENTRY
# ============================================================================

class VRN_MDL007_APIDataFetcher:
    """VRN-MDL007-CLS-001
    For each ticker:
      1. Compute history year range (N-3 ~ N)
      2. Fetch MOPS income/balance/cashflow
      3. Fetch TWSE market data
      4. Fetch yfinance adj_close + consensus + breakdown
      5. Dedup + compute derived ratios
      6. Write DB + Parquet + CSV
    """
    def __init__(self, cfg: Optional[Dict] = None):
        self.cfg     = dict(_PARAMS, **(cfg or {}))
        self.workers = self.cfg.get("workers") or max(1,(os.cpu_count() or 4)-1)
        self.db: Optional[MDL007DBWriter] = None

    def _history_years(self, report_year: Optional[int] = None) -> List[int]:
        n = report_year or date.today().year
        return [n - i for i in range(1, _P["history_years"] + 1)]

    def fetch_one_ticker(self, ticker: str, report_year: Optional[int] = None) -> Dict:
        t0   = time.perf_counter()
        rows = []
        years = self._history_years(report_year)

        # MOPS
        rows.extend(fetch_mops_all(ticker, years))

        # TWSE
        rows.extend(fetch_twse_market(ticker))

        # yfinance
        rows.extend(fetch_yfinance_data(ticker))

        # Dedup
        rows = dedup_rows(rows)

        # Derived ratios
        rows.extend(compute_derived_ratios(rows))
        rows = dedup_rows(rows)

        # DB
        if self.db and rows:
            try: self.db.insert(rows)
            except Exception as e: log.warning("[MDL007] DB insert %s: %s", ticker, e)

        elapsed = round(time.perf_counter()-t0, 2)
        log.info("[MDL007] %s: %d rows in %.2fs", ticker, len(rows), elapsed)
        return {"ticker": ticker, "rows": len(rows),
                "ok": True, "elapsed": elapsed, "data": rows}

    def run(self, tickers: List[str], report_years: Optional[Dict[str, int]] = None) -> Dict:
        t0 = time.perf_counter()
        out_dir = self.cfg.get("mdl007_temp", _P["mdl007_temp"])
        Path(out_dir).mkdir(parents=True, exist_ok=True)

        # Plugin + accel
        plugin_caps = load_plugins(self.cfg.get("ssot_dir", _P["ssot_dir"]))
        cap = _mdl007_accel_init(self.workers)
        log.info("[MDL007] accel=%s plugins=%s", cap, plugin_caps)

        # DB
        if self.cfg.get("enable_db", True):
            self.db = MDL007DBWriter(str(Path(out_dir)/"VRN_MDL007.db"))

        report_years = report_years or {}
        all_results = []

        # Parallel fetch via Celeritas or stdlib
        if _CEL_OK and hasattr(_CEL, "_LazyPool"):
            try:
                futs = {_CEL._LazyPool.submit(
                    self.fetch_one_ticker, t, report_years.get(t)): t
                    for t in tickers}
                for fut in as_completed(futs.values() if hasattr(futs,"values") else futs):
                    try: all_results.append(fut.result())
                    except Exception as e:
                        all_results.append({"ticker":"?","ok":False,"error":str(e)})
            except Exception:
                all_results = []

        if not all_results:  # stdlib fallback
            with ThreadPoolExecutor(max_workers=self.workers) as ex:
                futs = {ex.submit(self.fetch_one_ticker, t,
                                  report_years.get(t)): t for t in tickers}
                for fut in as_completed(futs):
                    try: all_results.append(fut.result())
                    except Exception as e:
                        all_results.append({"ticker":futs[fut],"ok":False,"error":str(e)})

        # Export
        if self.db:
            self.db.export(out_dir)

        total_rows = sum(r.get("rows",0) for r in all_results)
        elapsed    = round(time.perf_counter()-t0, 2)
        summary = {
            "module":    __module_id__, "version": __version__,
            "tickers":   tickers, "n_tickers": len(tickers),
            "total_rows":total_rows, "elapsed": elapsed,
            "ok":        all(r.get("ok") for r in all_results),
            "results":   all_results,
            "plugin_caps": plugin_caps,
        }
        Path(out_dir/"VRN_MDL007_Summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=2, default=str),
            encoding="utf-8")
        log.info("[MDL007] DONE: %d tickers %d rows %.2fs", len(tickers), total_rows, elapsed)
        return summary

__all__ = [
    "__version__","__module_id__",
    "_PARAMS","_P",
    "TW_TICKER_REGEX","TW_BLOOMBERG_REGEX","TW_YFINANCE_REGEX",
    "MOPS_ACCOUNT_MAP","CANONICAL_CATEGORY",
    "load_plugins","_cel_submit","_cel_map","_net_get","_ssot_normalize",
    "_mdl007_accel_init",
    "normalize_to_million","normalize_precision","norm","get_tolerance",
    "fetch_mops_income","fetch_mops_all",
    "fetch_twse_market","fetch_yfinance_data",
    "dedup_rows","compute_derived_ratios",
    "FETCH_COLS","MDL007DBWriter","VRN_MDL007_APIDataFetcher",
]

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="VRN MDL007 API Data Fetcher")
    p.add_argument("--tickers", nargs="+", required=True)
    p.add_argument("--ssot-dir",    default=_P["ssot_dir"])
    p.add_argument("--mdl007-temp", default=_P["mdl007_temp"])
    p.add_argument("--workers",     type=int, default=0)
    args = p.parse_args()
    cfg  = {"ssot_dir": args.ssot_dir, "mdl007_temp": args.mdl007_temp,
            "workers": args.workers}
    result = VRN_MDL007_APIDataFetcher(cfg).run(args.tickers)
    print(json.dumps({"ok": result["ok"], "total_rows": result["total_rows"],
                      "elapsed": result["elapsed"]}, indent=2))
