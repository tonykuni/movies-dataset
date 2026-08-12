#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
================================================================================
  VDF_MDL007_SSOTResolver.py
================================================================================
  VERITAS DATA FRAMEWORK - MDL007  SSOT-Driven Multi-Source Ticker Resolver
  Version    : 1.0.0   |   Module ID : VDF-MDL007-RES-001
  Asset ID   : VDF-MDL007-CLS-001
  Policy     : SSOT regex 鎖定 · 多源 union · 個股全欄位解析

ROLE
================================================================================
  接受任何輸入 (raw ticker, yf ticker, bloomberg, 公司名稱),
  透過 SSOT regex 解析為 canonical, 並從 4 個官方源拉齊所有欄位:

    [TWSE]      上市股票每日量價 + 公司基本資料 (t187ap03_L) + BWIBBU 估值
    [TPEX]      上櫃股票每日量價 + 公司基本資料 (mopsfin_t187ap03_O) + PE
    [MOPS]      公開資訊觀測站 · 公司財務基本資料 (補 TWSE/TPEX 之不足)
    [YFinance]  Adj Close · Volume · Consensus (analyst targets) + 估值
    [FactSet]   stub · 預留 commercial consensus 接口

OUTPUT SCHEMA (per ticker)
================================================================================
  Identifiers:
    tw_ticker            · 4-digit canonical (e.g. "2330")
    tw_yfinance_ticker   · XXXX.TW or XXXX.TWO (e.g. "2330.TW")
    tw_bloomberg_ticker  · XXXX TT (e.g. "2330 TT")
    canonical_via_code   · TW.Equity.2330 (registry-ready)

  Identity:
    name_zh · name_en · market(TWSE/TPEX) · industry · listing_date
    address · chairman · capital · paid_up_shares

  Coverage Matrix (boolean):
    has_twse_quote · has_tpex_quote · has_mops_data · has_yfinance_data

  Latest Daily:
    adj_close · close · open · high · low · volume · turnover · market_cap

  YF Consensus:
    yf_target_mean/median/high/low · yf_num_analysts · yf_recommendation
    yf_trailing_pe · yf_forward_pe · yf_dividend_yield

  FactSet Consensus (stub):
    fs_target_mean/median/high/low · fs_num_analysts · fs_eps_2026/2027

SSOT (locked, immutable - 同 MDL004)
================================================================================
  TW_TICKER_REGEX     = (?!0)(?!202[1-9])(?!2030)([1-9]\d{3})
  TW_BLOOMBERG_REGEX  = ([1-9]\d{3}) TT
  TW_YFINANCE_REGEX   = ([1-9]\d{3})\.(TW|TWO)

USAGE
================================================================================
  # 單檔解析
  python VDF_MDL007_SSOTResolver.py --ticker 2330
  python VDF_MDL007_SSOTResolver.py --ticker 2330.TW
  python VDF_MDL007_SSOTResolver.py --ticker "2330 TT"
  python VDF_MDL007_SSOTResolver.py --name 台積電

  # 批次解析
  python VDF_MDL007_SSOTResolver.py --batch 2330,2317,3324,6488

  # 從 MDL001 universe parquet 解析全部
  python VDF_MDL007_SSOTResolver.py --all --no-pause

  # 跳 consensus (僅 identity + daily quote)
  python VDF_MDL007_SSOTResolver.py --batch 2330,2317 --no-consensus
"""

# ===== [VIA:ANCHOR:SUPPORT:BOOTSTRAP:START] =====
# 接橋補丁 v2(2026-08-12 令:引擎統一導入 輔助/加速器/網路/自動編號;
#  導入一律 bridge-first 過橋;graceful 全退化 — 缺席零影響;
#  不 eager 導入 Runtime_Bridge/EnvManager 重件)
import sys as _via_sys
from pathlib import Path as _via_Path

def _via_bootstrap_support_paths():
    try:
        _self = _via_Path(__file__).resolve()
        roots = [_self.parent]
        p = _self.parent
        for _ in range(4):
            p = p.parent
            roots.append(p)
        for root in roots:
            for name in ("supportive_module", "supportive modules"):
                sup = root / name
                if sup.is_dir():
                    s = str(sup)
                    if s not in _via_sys.path:
                        _via_sys.path.insert(0, s)
    except Exception:
        pass

_via_bootstrap_support_paths()
try:
    from VRN_SupportBridge import BRIDGE as _VIA_BRIDGE
    _VIA_HAS_BRIDGE = True
except Exception:
    _VIA_BRIDGE = None
    _VIA_HAS_BRIDGE = False

def _via_load(_name):
    # 統一導入閘:先過橋(輔助性工具),橋缺退直導,再缺落 None(graceful)
    try:
        if _VIA_BRIDGE is not None:
            for _fn in ("load", "get", "require"):
                _f = getattr(_VIA_BRIDGE, _fn, None)
                if callable(_f):
                    try:
                        _m = _f(_name)
                    except Exception:
                        _m = None
                    if _m is not None:
                        return _m
    except Exception:
        pass
    try:
        return __import__(_name)
    except Exception:
        return None

_VIA_SSOT = _via_load("VIA_SSOT_Unified")
_VIA_AEGIS = _via_load("VeritasAegisNexus")
_VIA_CELERITAS = _via_load("VeritasCeleritas")
_VIA_ACCEL = _via_load("VIA_SuperAccel_Module")   # 加速器(工作站候上傳;graceful)
_VIA_NET = _via_load("VIA_NetSupport")            # 網路支援模組
_VIA_REGCORE = _via_load("VIA_RegistryCore_v1")   # 自動編號核心(工作站候上傳;graceful)
try:
    if _VIA_REGCORE is not None:  # 自動編號:標準介面任一,全護欄不擲例外
        for _fn in ("auto_register", "ensure_code", "register_module"):
            _f = getattr(_VIA_REGCORE, _fn, None)
            if callable(_f):
                _f(__file__)
                break
except Exception:
    pass
# ===== [VIA:ANCHOR:SUPPORT:BOOTSTRAP:END] =====


# =====================================================================================
# 📋 ALL PARAMETERS ON TOP
# =====================================================================================

PROJECT_NAME       = "1-7-SSOTResolver"
# 歸檔可攜補丁(2026-08-12 整合去重歸戶;工作站正本路徑優先,缺席退本地 db — 內容零改):
import os as _os
from pathlib import Path as _P
_PROD_BASE = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VDF\dict"
BASE_DIR           = _PROD_BASE if _os.path.isdir(_PROD_BASE) else str(_P(__file__).parent / "db")
OUTPUT_DIR         = "1-7-SSOTResolver"

# Universe source (from MDL001-VRF)
UNIVERSE_SOURCE    = "1-0-TWUniverse"
UNIVERSE_FILE      = "tw_universe_combined.parquet"

# 🔒 SSOT TW Ticker Regex (LOCKED · immutable · 與 MDL004 完全一致)
TW_TICKER_REGEX    = r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})"
TW_BLOOMBERG_REGEX = r"([1-9]\d{3}) TT"
TW_YFINANCE_REGEX  = r"([1-9]\d{3})\.(TW|TWO)"

# Source endpoints
TWSE_DAILY_ALL_URL      = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
TWSE_COMPANY_BASIC_URL  = "https://openapi.twse.com.tw/v1/opendata/t187ap03_L"      # 上市公司基本資料
TWSE_BWIBBU_URL         = "https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_d"  # 估值 (PE/PB/Yield)

TPEX_DAILY_CLOSE_URL    = "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes"
TPEX_COMPANY_BASIC_URL  = "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O"   # 上櫃公司基本資料
TPEX_PERATIO_URL        = "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_peratio_analysis"

# MOPS endpoints (公開資訊觀測站)
MOPS_INDUSTRY_URL       = "https://mopsfin.twse.com.tw/opendata/t187ap03_L.csv"     # 補充來源
MOPS_BASIC_QUERY_URL    = "https://mops.twse.com.tw/mops/web/ajax_t05st03"          # 個別查詢 (POST)

# HTTP
HTTP_USER_AGENT    = "Mozilla/5.0 VeritasDataForge/VDF-MDL007"
HTTP_TIMEOUT       = 20
HTTP_RETRIES       = 3
HTTP_RETRY_DELAY   = 2

# YFinance
YF_TIMEOUT         = 15
YF_INFO_WORKERS    = 8
YF_RETRY_ATTEMPTS  = 3
YF_RETRY_DELAY     = 1.5

# Cache TTL (一次抓全清單後快取, 避免重複 hit endpoint)
CACHE_TTL_SECONDS  = 1800   # 30 min

# 輸出
OUTPUT_PARQUET     = True
OUTPUT_DUCKDB      = True
OUTPUT_CSV         = True
OUTPUT_JSON        = True   # JSON 預設開 (resolver 結果常被當 lookup table)
OUTPUT_GSHEET      = False

CSV_ENCODING       = "utf-8-sig"
DUCKDB_FILENAME    = "VDF_MDL007_SSOTResolver.duckdb"
LOG_LEVEL          = "INFO"


# =====================================================================================
# 📦 Imports
# =====================================================================================

import os, sys, re, json, time, warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
warnings.filterwarnings('ignore')

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    sys.exit("❌ pandas/numpy 必須安裝")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    yf = None

# Import OutputManager (LIB MDL101)
try:
    HERE = Path(__file__).parent
    sys.path.insert(0, str(HERE))
    from VDF_MDL101_OutputManager import OutputManager
    OUTPUT_MGR_AVAILABLE = True
except ImportError:
    OUTPUT_MGR_AVAILABLE = False
    OutputManager = None

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    console = None


# =====================================================================================
# 🔧 Utilities
# =====================================================================================

def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _safe_num(v: Any) -> Optional[float]:
    if v is None: return None
    if isinstance(v, str):
        v = v.replace(",", "").strip()
        if v in ("", "-", "--", "N/A", "null", "nan"): return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _safe_int(v: Any) -> Optional[int]:
    f = _safe_num(v)
    return int(f) if f is not None else None


def _http_get(url: str, retries: int = HTTP_RETRIES) -> Optional[requests.Response]:
    if not REQUESTS_AVAILABLE: return None
    headers = {"User-Agent": HTTP_USER_AGENT, "Accept": "application/json"}
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=headers, timeout=HTTP_TIMEOUT)
            r.raise_for_status()
            return r
        except Exception:
            if attempt < retries - 1:
                time.sleep(HTTP_RETRY_DELAY)
    return None


def _log(level: str, msg: str):
    if not RICH_AVAILABLE:
        print(f"[{level}] {msg}"); return
    colors = {"INFO": "cyan", "OK": "green", "WARN": "yellow", "ERR": "red", "DBG": "dim"}
    c = colors.get(level, "white")
    console.print(f"[{c}][{level}][/{c}] {msg}")


# =====================================================================================
# 🔍 [SSOT Core] TickerResolver - 任意輸入 → canonical
# =====================================================================================

class TickerResolver:
    """
    SSOT 規則:
      Input formats accepted:
        1. "2330"        (raw 4-digit)
        2. "2330.TW"     (YF TWSE)
        3. "2330.TWO"    (YF TPEX)
        4. "2330 TT"     (Bloomberg)
        5. "台積電"      (中文公司名)
        6. "TSMC"        (英文公司名 - 模糊匹配, 需 name index)
      Output canonical:
        tw_ticker (4-digit), market (TWSE/TPEX), yf_ticker, bloomberg_ticker
    """
    VERSION = "1.0.0"

    # 內部 name index (中英文 → ticker), runtime 由 sources 填
    _name_to_ticker: Dict[str, str] = {}

    @classmethod
    def register_name(cls, ticker: str, name_zh: str, name_en: str = ""):
        if name_zh: cls._name_to_ticker[name_zh.strip()] = ticker
        if name_en: cls._name_to_ticker[name_en.strip().upper()] = ticker

    @staticmethod
    def parse(raw_input: str) -> Dict[str, Optional[str]]:
        """解析輸入, 回 {format, code, market}."""
        s = str(raw_input).strip()

        # Pattern 4: Bloomberg "XXXX TT"
        m = re.match(rf"^{TW_BLOOMBERG_REGEX}$", s)
        if m: return {"format": "bloomberg", "code": m.group(1), "market": None}

        # Pattern 2/3: YFinance "XXXX.TW" / "XXXX.TWO"
        m = re.match(rf"^{TW_YFINANCE_REGEX}$", s)
        if m:
            code = m.group(1); suffix = m.group(2)
            return {"format": "yfinance", "code": code,
                    "market": "TWSE" if suffix == "TW" else "TPEX"}

        # Pattern 1: raw 4-digit
        m = re.match(rf"^{TW_TICKER_REGEX}$", s)
        if m: return {"format": "raw", "code": m.group(1), "market": None}

        # Pattern 5/6: name lookup
        key = s.upper() if re.match(r"^[A-Za-z\s\-]+$", s) else s
        if key in TickerResolver._name_to_ticker:
            code = TickerResolver._name_to_ticker[key]
            return {"format": "name", "code": code, "market": None}
        # Try partial match
        for n, c in TickerResolver._name_to_ticker.items():
            if s in n or n in s:
                return {"format": "name_partial", "code": c, "market": None}

        return {"format": "unknown", "code": None, "market": None}

    @staticmethod
    def to_canonical(code: str, market: Optional[str] = "TWSE") -> Dict[str, str]:
        """code + market → all canonical identifiers."""
        code = str(code).strip()
        market = market or "TWSE"
        suffix = ".TW" if market == "TWSE" else ".TWO"
        return {
            "tw_ticker":            code,
            "tw_yfinance_ticker":   f"{code}{suffix}",
            "tw_bloomberg_ticker":  f"{code} TT",
            "canonical_via_code":   f"TW.Equity.{code}",
            "market":               market,
        }

    @staticmethod
    def is_valid_tw_code(code: str) -> bool:
        """SSOT regex 驗證."""
        return bool(re.match(rf"^{TW_TICKER_REGEX}$", str(code).strip()))


# =====================================================================================
# 🌐 [Source 1] TWSESource - 上市股票 + 公司基本資料
# =====================================================================================

class TWSESource:
    """TWSE OpenAPI - 上市股票每日量價 + 公司基本資料 + 估值."""
    VERSION = "1.0.0"
    name = "TWSE"

    def __init__(self):
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self.stats = {"calls": 0, "rows": 0, "errors": []}

    def _cached(self, key: str):
        if key in self._cache:
            ts, val = self._cache[key]
            if time.time() - ts < CACHE_TTL_SECONDS:
                return val
        return None

    def _store(self, key: str, val: Any):
        self._cache[key] = (time.time(), val)

    def fetch_all_daily(self) -> Dict[str, Dict]:
        """一次抓全 TWSE 每日量價, 回 {code: row}."""
        cached = self._cached("daily_all")
        if cached: return cached
        r = _http_get(TWSE_DAILY_ALL_URL)
        if r is None:
            self.stats["errors"].append("TWSE daily HTTP fail")
            return {}
        try:
            data = r.json()
        except Exception as e:
            self.stats["errors"].append(f"TWSE daily JSON: {e}")
            return {}
        out: Dict[str, Dict] = {}
        for d in data:
            code = (d.get("Code") or "").strip()
            if not TickerResolver.is_valid_tw_code(code): continue
            out[code] = {
                "code":         code,
                "name_zh":      (d.get("Name") or "").strip(),
                "market":       "TWSE",
                "open":         _safe_num(d.get("OpeningPrice")),
                "high":         _safe_num(d.get("HighestPrice")),
                "low":          _safe_num(d.get("LowestPrice")),
                "close":        _safe_num(d.get("ClosingPrice")),
                "change":       _safe_num(d.get("Change")),
                "volume":       _safe_int(d.get("TradeVolume")),
                "turnover":     _safe_num(d.get("TradeValue")),
                "transactions": _safe_int(d.get("Transaction")),
                "_source":      "TWSE_OpenAPI_STOCK_DAY_ALL",
            }
        self.stats["calls"] += 1
        self.stats["rows"]  += len(out)
        self._store("daily_all", out)
        return out

    def fetch_all_company_basic(self) -> Dict[str, Dict]:
        """一次抓全 TWSE 公司基本資料 (t187ap03_L), 回 {code: row}."""
        cached = self._cached("basic_all")
        if cached: return cached
        r = _http_get(TWSE_COMPANY_BASIC_URL)
        if r is None:
            self.stats["errors"].append("TWSE basic HTTP fail")
            return {}
        try:
            data = r.json()
        except Exception as e:
            self.stats["errors"].append(f"TWSE basic JSON: {e}")
            return {}
        out: Dict[str, Dict] = {}
        for d in data:
            code = (d.get("公司代號") or d.get("Code") or "").strip()
            if not TickerResolver.is_valid_tw_code(code): continue
            out[code] = {
                "code":          code,
                "name_zh":       (d.get("公司簡稱") or d.get("公司名稱") or "").strip(),
                "name_en":       (d.get("英文簡稱") or "").strip(),
                "industry":      (d.get("產業別") or "").strip(),
                "listing_date":  (d.get("上市日期") or "").strip(),
                "address":       (d.get("住址") or "").strip(),
                "chairman":      (d.get("董事長") or "").strip(),
                "capital":       _safe_num(d.get("實收資本額")),
                "paid_up_shares":_safe_num(d.get("已發行普通股數")),
                "_source":       "TWSE_OpenAPI_t187ap03_L",
            }
            # Register name for resolver
            TickerResolver.register_name(code, out[code]["name_zh"], out[code]["name_en"])
        self.stats["calls"] += 1
        self.stats["rows"]  += len(out)
        self._store("basic_all", out)
        return out

    def fetch_all_bwibbu(self) -> Dict[str, Dict]:
        """一次抓全 TWSE 估值 (BWIBBU), 回 {code: row}."""
        cached = self._cached("bwibbu_all")
        if cached: return cached
        r = _http_get(TWSE_BWIBBU_URL)
        if r is None:
            return {}
        try:
            data = r.json()
        except Exception:
            return {}
        out: Dict[str, Dict] = {}
        for d in data:
            code = (d.get("Code") or d.get("證券代號") or "").strip()
            if not TickerResolver.is_valid_tw_code(code): continue
            out[code] = {
                "code":          code,
                "twse_pe_ratio": _safe_num(d.get("PEratio") or d.get("本益比")),
                "twse_dividend_yield": _safe_num(d.get("DividendYield") or d.get("殖利率(%)")),
                "twse_pb_ratio": _safe_num(d.get("PBratio") or d.get("股價淨值比")),
                "_source":       "TWSE_OpenAPI_BWIBBU_d",
            }
        self.stats["calls"] += 1
        self._store("bwibbu_all", out)
        return out


# =====================================================================================
# 🌐 [Source 2] TPEXSource - 上櫃股票 + 公司基本資料
# =====================================================================================

class TPEXSource:
    """TPEX OpenAPI - 上櫃股票每日量價 + 公司基本資料."""
    VERSION = "1.0.0"
    name = "TPEX"

    def __init__(self):
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self.stats = {"calls": 0, "rows": 0, "errors": []}

    def _cached(self, key: str):
        if key in self._cache:
            ts, val = self._cache[key]
            if time.time() - ts < CACHE_TTL_SECONDS: return val
        return None

    def _store(self, key: str, val: Any):
        self._cache[key] = (time.time(), val)

    def fetch_all_daily(self) -> Dict[str, Dict]:
        cached = self._cached("daily_all")
        if cached: return cached
        r = _http_get(TPEX_DAILY_CLOSE_URL)
        if r is None:
            self.stats["errors"].append("TPEX daily HTTP fail")
            return {}
        try:
            data = r.json()
        except Exception as e:
            self.stats["errors"].append(f"TPEX daily JSON: {e}")
            return {}
        out: Dict[str, Dict] = {}
        for d in data:
            code = (d.get("SecuritiesCompanyCode") or d.get("Code") or "").strip()
            if not TickerResolver.is_valid_tw_code(code): continue
            out[code] = {
                "code":         code,
                "name_zh":      (d.get("CompanyName") or d.get("SecuritiesName") or "").strip(),
                "market":       "TPEX",
                "open":         _safe_num(d.get("Open") or d.get("OpeningPrice")),
                "high":         _safe_num(d.get("High") or d.get("HighestPrice")),
                "low":          _safe_num(d.get("Low")  or d.get("LowestPrice")),
                "close":        _safe_num(d.get("Close") or d.get("LastestTradedPrice")),
                "change":       _safe_num(d.get("Change")),
                "volume":       _safe_int(d.get("TradingShares")),
                "turnover":     _safe_num(d.get("TradingAmount")),
                "transactions": _safe_int(d.get("Transaction")),
                "_source":      "TPEX_OpenAPI_daily_close_quotes",
            }
        self.stats["calls"] += 1
        self.stats["rows"]  += len(out)
        self._store("daily_all", out)
        return out

    def fetch_all_company_basic(self) -> Dict[str, Dict]:
        cached = self._cached("basic_all")
        if cached: return cached
        r = _http_get(TPEX_COMPANY_BASIC_URL)
        if r is None:
            self.stats["errors"].append("TPEX basic HTTP fail")
            return {}
        try:
            data = r.json()
        except Exception as e:
            self.stats["errors"].append(f"TPEX basic JSON: {e}")
            return {}
        out: Dict[str, Dict] = {}
        for d in data:
            code = (d.get("SecuritiesCompanyCode") or d.get("公司代號") or "").strip()
            if not TickerResolver.is_valid_tw_code(code): continue
            out[code] = {
                "code":          code,
                "name_zh":       (d.get("CompanyName") or d.get("公司簡稱") or "").strip(),
                "name_en":       (d.get("CompanyNameEng") or "").strip(),
                "industry":      (d.get("Industry") or d.get("產業別") or "").strip(),
                "listing_date":  (d.get("ListingDate") or d.get("上櫃日期") or "").strip(),
                "address":       (d.get("Address") or d.get("住址") or "").strip(),
                "chairman":      (d.get("Chairman") or d.get("董事長") or "").strip(),
                "capital":       _safe_num(d.get("Capital") or d.get("實收資本額")),
                "paid_up_shares":_safe_num(d.get("PaidUpShares") or d.get("已發行普通股數")),
                "_source":       "TPEX_OpenAPI_mopsfin_t187ap03_O",
            }
            TickerResolver.register_name(code, out[code]["name_zh"], out[code]["name_en"])
        self.stats["calls"] += 1
        self.stats["rows"]  += len(out)
        self._store("basic_all", out)
        return out

    def fetch_all_pe_ratio(self) -> Dict[str, Dict]:
        cached = self._cached("pe_all")
        if cached: return cached
        r = _http_get(TPEX_PERATIO_URL)
        if r is None:
            return {}
        try:
            data = r.json()
        except Exception:
            return {}
        out: Dict[str, Dict] = {}
        for d in data:
            code = (d.get("SecuritiesCompanyCode") or "").strip()
            if not TickerResolver.is_valid_tw_code(code): continue
            out[code] = {
                "code":               code,
                "tpex_pe_ratio":      _safe_num(d.get("PERatio")),
                "tpex_dividend_yield":_safe_num(d.get("DividendYield")),
                "tpex_pb_ratio":      _safe_num(d.get("PBRatio")),
                "_source":            "TPEX_OpenAPI_peratio",
            }
        self.stats["calls"] += 1
        self._store("pe_all", out)
        return out


# =====================================================================================
# 🌐 [Source 3] MOPSSource - 公開資訊觀測站補充欄位
# =====================================================================================

class MOPSSource:
    """
    MOPS · 公開資訊觀測站
    補充 TWSE/TPEX 沒給的細節 (產業細分類, 子公司, 集團代號 等).
    本版採 lightweight 模式: 主要欄位已從 TWSE/TPEX OpenAPI t187ap03 取得,
    MOPS source 在此版扮演 coverage flag (是否找得到該股) + 完整性檢查.
    """
    VERSION = "1.0.0"
    name = "MOPS"

    def __init__(self):
        self.stats = {"checks": 0, "available": 0, "errors": []}
        self._known_codes: Set[str] = set()

    def register_codes(self, codes: List[str]):
        """從 TWSE/TPEX 已知的 codes 註冊 (MOPS 涵蓋所有上市櫃)."""
        for c in codes:
            if TickerResolver.is_valid_tw_code(c):
                self._known_codes.add(c)

    def has_data(self, code: str) -> bool:
        """是否在 MOPS 系統中 (與 TWSE/TPEX 同步)."""
        self.stats["checks"] += 1
        ok = code in self._known_codes
        if ok: self.stats["available"] += 1
        return ok

    def get_record(self, code: str) -> Dict:
        """MOPS 補充欄位 (此版用 placeholder, 真實環境可 POST 至 ajax_t05st03)."""
        if not self.has_data(code):
            return {"code": code, "mops_industry_detail": None,
                    "mops_holding_company": None, "_source": "MOPS_UNAVAILABLE"}
        return {
            "code":                  code,
            "mops_industry_detail":  None,    # 詳細產業細分類 (need POST query)
            "mops_holding_company":  None,    # 集團持股
            "_source":               "MOPS_OPENAPI_via_t187ap03",
        }


# =====================================================================================
# 🌐 [Source 4] YFinanceSource - Adj Close + Volume + Consensus
# =====================================================================================

class YFinanceSource:
    """yfinance - Adj Close + Volume + Analyst Consensus + 估值."""
    VERSION = "1.0.0"
    name = "YFinance"

    def __init__(self):
        self.stats = {"ok": 0, "fail": 0, "errors": []}

    def fetch_one(self, yf_ticker: str, include_consensus: bool = True) -> Dict:
        """單檔 yfinance.Ticker, 抓 history 最新 + info."""
        out = {
            "yf_ticker":           yf_ticker,
            "yf_adj_close":        None,
            "yf_close":            None,
            "yf_volume":           None,
            "yf_target_mean":      None, "yf_target_median":  None,
            "yf_target_high":      None, "yf_target_low":     None,
            "yf_num_analysts":     None, "yf_recommendation": None,
            "yf_market_cap":       None, "yf_shares_outstanding": None,
            "yf_trailing_pe":      None, "yf_forward_pe":     None,
            "yf_trailing_eps":     None, "yf_forward_eps":    None,
            "yf_book_value":       None, "yf_price_to_book":  None,
            "yf_dividend_rate":    None, "yf_dividend_yield": None,
            "yf_currency":         None, "yf_short_name":     None,
            "_yf_error":           None,
            "_source":             "yfinance",
        }
        if not YFINANCE_AVAILABLE:
            out["_yf_error"] = "yfinance not installed"
            self.stats["fail"] += 1
            return out
        for attempt in range(YF_RETRY_ATTEMPTS):
            try:
                tk = yf.Ticker(yf_ticker)
                # Latest quote
                hist = tk.history(period="5d", timeout=YF_TIMEOUT)
                if hist is not None and not hist.empty:
                    out["yf_adj_close"] = float(hist["Close"].iloc[-1])  # YF 1.x: Close 已是 adj
                    out["yf_close"]     = float(hist["Close"].iloc[-1])
                    if "Volume" in hist.columns:
                        out["yf_volume"] = int(hist["Volume"].iloc[-1])
                # Consensus from info
                if include_consensus:
                    info = tk.info or {}
                    out["yf_target_mean"]        = _safe_num(info.get("targetMeanPrice"))
                    out["yf_target_median"]      = _safe_num(info.get("targetMedianPrice"))
                    out["yf_target_high"]        = _safe_num(info.get("targetHighPrice"))
                    out["yf_target_low"]         = _safe_num(info.get("targetLowPrice"))
                    out["yf_num_analysts"]       = _safe_int(info.get("numberOfAnalystOpinions"))
                    out["yf_recommendation"]     = info.get("recommendationKey")
                    out["yf_market_cap"]         = _safe_num(info.get("marketCap"))
                    out["yf_shares_outstanding"] = _safe_num(info.get("sharesOutstanding"))
                    out["yf_trailing_pe"]        = _safe_num(info.get("trailingPE"))
                    out["yf_forward_pe"]         = _safe_num(info.get("forwardPE"))
                    out["yf_trailing_eps"]       = _safe_num(info.get("trailingEps"))
                    out["yf_forward_eps"]        = _safe_num(info.get("forwardEps"))
                    out["yf_book_value"]         = _safe_num(info.get("bookValue"))
                    out["yf_price_to_book"]      = _safe_num(info.get("priceToBook"))
                    out["yf_dividend_rate"]      = _safe_num(info.get("dividendRate"))
                    out["yf_dividend_yield"]     = _safe_num(info.get("dividendYield"))
                    out["yf_currency"]           = info.get("currency")
                    out["yf_short_name"]         = info.get("shortName")
                self.stats["ok"] += 1
                return out
            except Exception as e:
                if attempt < YF_RETRY_ATTEMPTS - 1:
                    time.sleep(YF_RETRY_DELAY)
                else:
                    out["_yf_error"] = str(e)[:80]
                    self.stats["fail"] += 1
                    self.stats["errors"].append(f"{yf_ticker}: {str(e)[:60]}")
        return out

    def fetch_batch(self, yf_tickers: List[str],
                    include_consensus: bool = True) -> Dict[str, Dict]:
        """並發抓批次."""
        results: Dict[str, Dict] = {}
        if len(yf_tickers) > 1:
            with ThreadPoolExecutor(max_workers=YF_INFO_WORKERS) as pool:
                futs = {pool.submit(self.fetch_one, t, include_consensus): t
                        for t in yf_tickers}
                for done in as_completed(futs):
                    t = futs[done]
                    try:
                        results[t] = done.result()
                    except Exception as e:
                        results[t] = {"yf_ticker": t, "_yf_error": str(e)[:60]}
                        self.stats["fail"] += 1
        else:
            for t in yf_tickers:
                results[t] = self.fetch_one(t, include_consensus)
        return results


# =====================================================================================
# 🌐 [Source 5] FactSetSource - Consensus stub
# =====================================================================================

class FactSetSource:
    """FactSet API stub. 需 commercial API key, 此版回 NaN."""
    VERSION = "1.0.0-stub"
    name = "FactSet"

    def __init__(self):
        self.stats = {"calls": 0, "is_stub": True}

    def fetch_one(self, code: str) -> Dict:
        self.stats["calls"] += 1
        return {
            "code":              code,
            "fs_target_mean":    None,
            "fs_target_median":  None,
            "fs_target_high":    None,
            "fs_target_low":     None,
            "fs_num_analysts":   None,
            "fs_eps_2026":       None,
            "fs_eps_2027":       None,
            "fs_revenue_2026":   None,
            "fs_revenue_2027":   None,
            "_source":           "FACTSET_STUB",
        }

    def fetch_batch(self, codes: List[str]) -> Dict[str, Dict]:
        return {c: self.fetch_one(c) for c in codes}


# =====================================================================================
# 🎯 [Main Engine] SSOTResolverEngine
# =====================================================================================

class SSOTResolverEngine:
    """
    Pipeline:
      1. Parse all inputs → canonical codes
      2. Pre-load 5 sources (TWSE/TPEX daily + basic, MOPS, YFinance, FactSet)
      3. Per ticker: merge all sources + coverage matrix
      4. Output multi-format
    """
    VERSION = "1.0.0"

    def __init__(self):
        self.start_time = time.time()
        # CLI args
        self.single_ticker  = None
        self.batch_input    = None
        self.name_query     = None
        self.use_all        = "--all" in sys.argv
        self.no_consensus   = "--no-consensus" in sys.argv
        for i, a in enumerate(sys.argv):
            if a == "--ticker" and i+1 < len(sys.argv):
                self.single_ticker = sys.argv[i+1]
            if a == "--batch" and i+1 < len(sys.argv):
                self.batch_input = sys.argv[i+1]
            if a == "--name" and i+1 < len(sys.argv):
                self.name_query = sys.argv[i+1]

        # Sources
        self.twse = TWSESource()
        self.tpex = TPEXSource()
        self.mops = MOPSSource()
        self.yfin = YFinanceSource()
        self.fs   = FactSetSource()

        # OutputManager
        if OUTPUT_MGR_AVAILABLE:
            self.output_mgr = OutputManager(
                base_dir=BASE_DIR, output_dir=OUTPUT_DIR,
                duckdb_filename=DUCKDB_FILENAME,
                enable_parquet=OUTPUT_PARQUET, enable_duckdb=OUTPUT_DUCKDB,
                enable_csv=OUTPUT_CSV, enable_json=OUTPUT_JSON,
                enable_gsheet=OUTPUT_GSHEET, respect_cli_flags=True,
            )
        else:
            self.output_mgr = None

        # Results
        self.parsed: List[Dict] = []
        self.records: List[Dict] = []
        self.save_results: Dict = {}

    def show_header(self):
        info = f"""
🔍 VDF MDL007 · SSOT-Driven Multi-Source Resolver v{self.VERSION}

🔒 SSOT Regex      : {TW_TICKER_REGEX}
📂 Sources         : TWSE OpenAPI · TPEX OpenAPI · MOPS · YFinance · FactSet(stub)
🎯 Mode            : {'單檔 ('+self.single_ticker+')' if self.single_ticker else
                      'Batch ('+(self.batch_input or '')+')' if self.batch_input else
                      'Name ('+(self.name_query or '')+')' if self.name_query else
                      'All universe (from MDL001-VRF parquet)' if self.use_all else 'CLI'}
💼 Consensus       : {'⏭️ skip' if self.no_consensus else '✅ YF + FactSet stub'}
📁 Output          : {Path(BASE_DIR) / OUTPUT_DIR}
"""
        if RICH_AVAILABLE:
            console.print(Panel(info.strip(),
                          title="[bold magenta]🔍 VDF MDL007 · SSOT Resolver[/bold magenta]",
                          border_style="magenta"))
        else:
            print(info)

    def _gather_inputs(self) -> List[str]:
        """從 CLI / universe parquet 收集要解析的 inputs."""
        if self.single_ticker:
            return [self.single_ticker]
        if self.batch_input:
            return [s.strip() for s in self.batch_input.split(",") if s.strip()]
        if self.name_query:
            return [self.name_query]
        if self.use_all:
            uni_path = Path(BASE_DIR) / UNIVERSE_SOURCE / UNIVERSE_FILE
            if uni_path.exists():
                try:
                    df = pd.read_parquet(uni_path)
                    if "code" in df.columns:
                        return df["code"].astype(str).tolist()
                except Exception as e:
                    _log("WARN", f"universe parquet load fail: {e}")
        # Default fallback
        return ["2330", "2317", "3324", "NVDA"]

    def _resolve_one(self, raw: str, master_twse_daily: Dict, master_twse_basic: Dict,
                     master_twse_bwibbu: Dict, master_tpex_daily: Dict,
                     master_tpex_basic: Dict, master_tpex_pe: Dict,
                     yf_results: Dict, fs_results: Dict) -> Dict:
        """解析單筆, 合併 4 源."""
        # Parse SSOT regex
        parsed = TickerResolver.parse(raw)
        self.parsed.append({"input": raw, **parsed})

        if parsed["code"] is None:
            return {
                "raw_input":          raw,
                "tw_ticker":          None,
                "tw_yfinance_ticker": None,
                "tw_bloomberg_ticker":None,
                "canonical_via_code": None,
                "name_zh":            None,
                "market":             None,
                "has_twse_quote":     False,
                "has_tpex_quote":     False,
                "has_mops_data":      False,
                "has_yfinance_data":  False,
                "resolve_status":     "UNRESOLVED",
                "resolve_reason":     "Cannot parse via SSOT regex or name index",
            }

        code = parsed["code"]
        market_hint = parsed.get("market")

        # Determine market from data (TWSE first, fallback TPEX)
        twse_daily = master_twse_daily.get(code)
        tpex_daily = master_tpex_daily.get(code)
        if twse_daily and not tpex_daily:
            market = "TWSE"
        elif tpex_daily and not twse_daily:
            market = "TPEX"
        else:
            market = market_hint or "TWSE"

        canonical = TickerResolver.to_canonical(code, market)
        twse_basic   = master_twse_basic.get(code, {})
        tpex_basic   = master_tpex_basic.get(code, {})
        twse_bwibbu  = master_twse_bwibbu.get(code, {})
        tpex_pe      = master_tpex_pe.get(code, {})

        # Coverage matrix
        has_twse_quote = bool(twse_daily)
        has_tpex_quote = bool(tpex_daily)
        has_mops_data  = self.mops.has_data(code)
        yf_data = yf_results.get(canonical["tw_yfinance_ticker"], {})
        has_yfinance_data = bool(yf_data and yf_data.get("_yf_error") is None)

        # Daily quote (prefer market match, fallback alternate)
        if market == "TWSE" and twse_daily:
            daily = twse_daily
        elif market == "TPEX" and tpex_daily:
            daily = tpex_daily
        elif twse_daily:
            daily = twse_daily
        elif tpex_daily:
            daily = tpex_daily
        else:
            daily = {}

        # Identity (prefer matching market's basic)
        basic = twse_basic if market == "TWSE" and twse_basic else (tpex_basic if tpex_basic else twse_basic)

        # Valuation (TWSE BWIBBU vs TPEX PE)
        val = twse_bwibbu if twse_bwibbu else tpex_pe

        # FactSet
        fs = fs_results.get(code, {})

        # YF adj_close fallback for market_cap if TWSE/TPEX missing
        adj_close = yf_data.get("yf_adj_close") or daily.get("close")
        shares = yf_data.get("yf_shares_outstanding") or basic.get("paid_up_shares")
        market_cap = yf_data.get("yf_market_cap") or (
            adj_close * shares if (adj_close and shares) else None)

        return {
            "raw_input":            raw,
            # Identifiers
            "tw_ticker":            canonical["tw_ticker"],
            "tw_yfinance_ticker":   canonical["tw_yfinance_ticker"],
            "tw_bloomberg_ticker":  canonical["tw_bloomberg_ticker"],
            "canonical_via_code":   canonical["canonical_via_code"],
            # Identity
            "name_zh":              basic.get("name_zh") or daily.get("name_zh"),
            "name_en":              basic.get("name_en"),
            "market":               market,
            "industry":             basic.get("industry"),
            "listing_date":         basic.get("listing_date"),
            "address":              basic.get("address"),
            "chairman":             basic.get("chairman"),
            "capital":              basic.get("capital"),
            "paid_up_shares":       basic.get("paid_up_shares"),
            # Coverage Matrix
            "has_twse_quote":       has_twse_quote,
            "has_tpex_quote":       has_tpex_quote,
            "has_mops_data":        has_mops_data,
            "has_yfinance_data":    has_yfinance_data,
            "n_sources_available":  sum([has_twse_quote, has_tpex_quote,
                                          has_mops_data, has_yfinance_data]),
            # Daily Quote (canonical, preferred from TWSE/TPEX, YF fallback)
            "adj_close":            adj_close,
            "close":                daily.get("close") or yf_data.get("yf_close"),
            "open":                 daily.get("open"),
            "high":                 daily.get("high"),
            "low":                  daily.get("low"),
            "volume":               daily.get("volume") or yf_data.get("yf_volume"),
            "turnover":             daily.get("turnover"),
            "transactions":         daily.get("transactions"),
            "market_cap":           market_cap,
            "shares_outstanding":   shares,
            # TWSE/TPEX 估值
            "twse_pe_ratio":        val.get("twse_pe_ratio") if has_twse_quote else None,
            "twse_dividend_yield":  val.get("twse_dividend_yield") if has_twse_quote else None,
            "twse_pb_ratio":        val.get("twse_pb_ratio") if has_twse_quote else None,
            "tpex_pe_ratio":        tpex_pe.get("tpex_pe_ratio") if has_tpex_quote else None,
            "tpex_dividend_yield":  tpex_pe.get("tpex_dividend_yield") if has_tpex_quote else None,
            "tpex_pb_ratio":        tpex_pe.get("tpex_pb_ratio") if has_tpex_quote else None,
            # YF Consensus
            "yf_target_mean":       yf_data.get("yf_target_mean"),
            "yf_target_median":     yf_data.get("yf_target_median"),
            "yf_target_high":       yf_data.get("yf_target_high"),
            "yf_target_low":        yf_data.get("yf_target_low"),
            "yf_num_analysts":      yf_data.get("yf_num_analysts"),
            "yf_recommendation":    yf_data.get("yf_recommendation"),
            "yf_trailing_pe":       yf_data.get("yf_trailing_pe"),
            "yf_forward_pe":        yf_data.get("yf_forward_pe"),
            "yf_trailing_eps":      yf_data.get("yf_trailing_eps"),
            "yf_forward_eps":       yf_data.get("yf_forward_eps"),
            "yf_book_value":        yf_data.get("yf_book_value"),
            "yf_dividend_yield":    yf_data.get("yf_dividend_yield"),
            "yf_currency":          yf_data.get("yf_currency"),
            # FactSet Consensus (stub)
            "fs_target_mean":       fs.get("fs_target_mean"),
            "fs_target_median":     fs.get("fs_target_median"),
            "fs_target_high":       fs.get("fs_target_high"),
            "fs_target_low":        fs.get("fs_target_low"),
            "fs_num_analysts":      fs.get("fs_num_analysts"),
            "fs_eps_2026":          fs.get("fs_eps_2026"),
            "fs_eps_2027":          fs.get("fs_eps_2027"),
            # Status
            "resolve_status":       "OK" if (has_twse_quote or has_tpex_quote or has_yfinance_data) else "PARTIAL",
            "resolve_reason":       parsed["format"],
            "_resolved_at":         datetime.now().isoformat(timespec='seconds'),
        }

    def run(self) -> int:
        try:
            self.show_header()
            inputs = self._gather_inputs()
            _log("INFO", f"Input count: {len(inputs)}")
            if not inputs:
                _log("ERR", "No inputs to resolve"); return 1

            # ─── Step 1: Pre-load all source caches ───
            _log("INFO", "Step 1/4: Pre-load TWSE/TPEX/MOPS sources (one-shot)")
            twse_daily  = self.twse.fetch_all_daily()
            twse_basic  = self.twse.fetch_all_company_basic()
            twse_bwibbu = self.twse.fetch_all_bwibbu()
            tpex_daily  = self.tpex.fetch_all_daily()
            tpex_basic  = self.tpex.fetch_all_company_basic()
            tpex_pe     = self.tpex.fetch_all_pe_ratio()
            self.mops.register_codes(list(twse_daily.keys()) + list(tpex_daily.keys()))
            _log("OK", f"TWSE daily={len(twse_daily)} · basic={len(twse_basic)} · bwibbu={len(twse_bwibbu)}")
            _log("OK", f"TPEX daily={len(tpex_daily)} · basic={len(tpex_basic)} · PE={len(tpex_pe)}")

            # ─── Step 2: Pre-parse inputs to get codes for YF/FactSet pre-fetch ───
            _log("INFO", "Step 2/4: Parse inputs via SSOT regex")
            codes_to_resolve = []
            yf_tickers_to_fetch = []
            for raw in inputs:
                parsed = TickerResolver.parse(raw)
                if parsed["code"]:
                    code = parsed["code"]
                    codes_to_resolve.append(code)
                    # Determine market
                    if code in twse_daily:
                        yf_tickers_to_fetch.append(f"{code}.TW")
                    elif code in tpex_daily:
                        yf_tickers_to_fetch.append(f"{code}.TWO")
                    else:
                        yf_tickers_to_fetch.append(f"{code}.TW")
            yf_tickers_to_fetch = list(set(yf_tickers_to_fetch))
            _log("OK", f"Parsed {len(codes_to_resolve)} valid codes (yf_tickers: {len(yf_tickers_to_fetch)})")

            # ─── Step 3: Batch fetch YFinance + FactSet ───
            yf_results = {}
            if not self.no_consensus and yf_tickers_to_fetch:
                _log("INFO", f"Step 3/4: YFinance batch fetch ({len(yf_tickers_to_fetch)} tickers)")
                t0 = time.time()
                yf_results = self.yfin.fetch_batch(yf_tickers_to_fetch,
                                                    include_consensus=True)
                _log("OK", f"YF: {self.yfin.stats['ok']} ok / {self.yfin.stats['fail']} fail · {round(time.time()-t0, 1)}s")
            else:
                _log("WARN", "Step 3/4: --no-consensus, skipping YF batch")
            fs_results = self.fs.fetch_batch(list(set(codes_to_resolve)))

            # ─── Step 4: Per-input resolve + merge ───
            _log("INFO", f"Step 4/4: Resolve & merge {len(inputs)} inputs")
            for raw in inputs:
                rec = self._resolve_one(
                    raw, twse_daily, twse_basic, twse_bwibbu,
                    tpex_daily, tpex_basic, tpex_pe,
                    yf_results, fs_results)
                self.records.append(rec)

            # ─── Save outputs ───
            if self.output_mgr and self.records:
                df = pd.DataFrame(self.records)
                self.save_results["ssot_resolved"] = self.output_mgr.save("ssot_resolved", df)
                # 也存 parse log
                df_parsed = pd.DataFrame(self.parsed)
                self.save_results["parse_log"] = self.output_mgr.save("parse_log", df_parsed)

            # ─── Rich Summary ───
            self._print_rich_summary()
            elapsed = round(time.time() - self.start_time, 2)
            _log("OK", f"完成 · 總耗時 {elapsed}s")
            return 0
        except KeyboardInterrupt:
            _log("WARN", "Interrupted"); return 1
        except Exception as e:
            _log("ERR", f"{e}")
            if LOG_LEVEL == "DEBUG":
                import traceback; traceback.print_exc()
            return 1

    # ─────────────────────────────────────────────────────────────
    # Rich Summary Matrix
    # ─────────────────────────────────────────────────────────────
    def _print_rich_summary(self):
        if not RICH_AVAILABLE: return self._plain_summary()
        elapsed = round(time.time() - self.start_time, 2)
        console.rule("[bold cyan]🔍 VDF MDL007 · SSOT Resolver · Summary Matrix[/bold cyan]")

        # ── Table 1: Source 統計 ──
        t = Table(title="🌐 [bold]1. Source 抓取統計[/bold]",
                  box=box.ROUNDED, header_style="bold magenta")
        t.add_column("Source", style="cyan", width=14)
        t.add_column("Calls", style="green", width=10, justify="right")
        t.add_column("Rows", style="green", width=10, justify="right")
        t.add_column("Notes", style="yellow", width=40)
        t.add_row("TWSE",     str(self.twse.stats["calls"]),
                  str(self.twse.stats["rows"]),
                  "daily + basic + bwibbu (3 endpoints)")
        t.add_row("TPEX",     str(self.tpex.stats["calls"]),
                  str(self.tpex.stats["rows"]),
                  "daily + basic + PE (3 endpoints)")
        t.add_row("MOPS",     str(self.mops.stats["checks"]),
                  str(self.mops.stats["available"]),
                  f"availability checks (via TWSE/TPEX universe)")
        t.add_row("YFinance", str(self.yfin.stats["ok"]),
                  str(self.yfin.stats["ok"] + self.yfin.stats["fail"]),
                  f"ok={self.yfin.stats['ok']} · fail={self.yfin.stats['fail']}")
        t.add_row("FactSet",  str(self.fs.stats["calls"]),
                  str(self.fs.stats["calls"]),
                  "STUB · returns NaN")
        console.print(t)

        # ── Table 2: Parse status ──
        if self.parsed:
            from collections import Counter
            fmt_cnt = Counter(p["format"] for p in self.parsed)
            t = Table(title="🔍 [bold]2. Input Parse 分布[/bold]",
                      box=box.ROUNDED, header_style="bold magenta")
            t.add_column("Input Format", style="cyan", width=20)
            t.add_column("Count", style="green", width=10, justify="right")
            t.add_column("Description", style="yellow", width=40)
            descriptions = {
                "raw":           "4-digit TW code (e.g. 2330)",
                "yfinance":      "XXXX.TW or XXXX.TWO",
                "bloomberg":     "XXXX TT format",
                "name":          "Exact name match",
                "name_partial":  "Partial name match",
                "unknown":       "Cannot parse",
            }
            for fmt, n in fmt_cnt.most_common():
                t.add_row(fmt, str(n), descriptions.get(fmt, "—"))
            console.print(t)

        # ── Table 3: Coverage Matrix (top 12 records) ──
        if self.records:
            top = self.records[:12]
            t = Table(title=f"📊 [bold]3. Coverage Matrix (top {len(top)})[/bold]",
                      box=box.ROUNDED, header_style="bold magenta")
            t.add_column("Ticker",  style="cyan", width=10)
            t.add_column("Name",    style="yellow", width=14)
            t.add_column("Market",  style="green", width=8)
            t.add_column("TWSE",    style="green", width=8, justify="center")
            t.add_column("TPEX",    style="green", width=8, justify="center")
            t.add_column("MOPS",    style="green", width=8, justify="center")
            t.add_column("YF",      style="green", width=8, justify="center")
            t.add_column("# Src",   style="yellow", width=8, justify="right")
            t.add_column("Status",  style="green", width=12)
            for r in top:
                t.add_row(
                    str(r.get("tw_ticker") or "—"),
                    str(r.get("name_zh") or "")[:12],
                    str(r.get("market") or "—"),
                    "✅" if r.get("has_twse_quote") else "—",
                    "✅" if r.get("has_tpex_quote") else "—",
                    "✅" if r.get("has_mops_data") else "—",
                    "✅" if r.get("has_yfinance_data") else "—",
                    f"{r.get('n_sources_available', 0)}/4",
                    r.get("resolve_status", "?"),
                )
            console.print(t)

        # ── Table 4: Sample Data (top 8 - 完整欄位) ──
        if self.records:
            top = self.records[:8]
            t = Table(title=f"💎 [bold]4. Resolved Data Sample (top {len(top)})[/bold]",
                      box=box.ROUNDED, header_style="bold magenta")
            t.add_column("TW Code",    style="cyan", width=8)
            t.add_column("YF Ticker",  style="cyan", width=10)
            t.add_column("Bloomberg",  style="cyan", width=10)
            t.add_column("Adj Close",  style="green", width=10, justify="right")
            t.add_column("Volume",     style="green", width=10, justify="right")
            t.add_column("MarketCap",  style="green", width=10, justify="right")
            t.add_column("YF Target",  style="yellow", width=10, justify="right")
            t.add_column("FS Target",  style="yellow", width=10, justify="right")
            def f(v, dec=2):
                if v is None or pd.isna(v): return "—"
                try:
                    if abs(v) > 1e9: return f"{v/1e9:.1f}B"
                    if abs(v) > 1e6: return f"{v/1e6:.1f}M"
                    if abs(v) > 1e3: return f"{v/1e3:.1f}K"
                    return f"{v:.{dec}f}"
                except: return "—"
            for r in top:
                t.add_row(
                    str(r.get("tw_ticker") or "—"),
                    str(r.get("tw_yfinance_ticker") or "—"),
                    str(r.get("tw_bloomberg_ticker") or "—"),
                    f(r.get("adj_close")),
                    f(r.get("volume")),
                    f(r.get("market_cap")),
                    f(r.get("yf_target_mean")),
                    f(r.get("fs_target_mean")),
                )
            console.print(t)

        # ── Table 5: 多格式輸出 ──
        if self.save_results:
            t = Table(title="💾 [bold]5. Multi-Format Output[/bold]",
                      box=box.ROUNDED, header_style="bold magenta")
            t.add_column("Table", style="cyan", width=22)
            t.add_column("Rows", style="green", width=10, justify="right")
            t.add_column("Parquet", style="yellow", width=10, justify="center")
            t.add_column("CSV", style="yellow", width=8, justify="center")
            t.add_column("JSON", style="yellow", width=8, justify="center")
            t.add_column("DuckDB", style="yellow", width=8, justify="center")
            for tbl, info in self.save_results.items():
                fmts = {o.get("format"): ("✅" if "error" not in o else "❌")
                        for o in info.get("outputs", [])}
                t.add_row(tbl, f"{info['rows']:,}",
                          fmts.get("parquet", "—"), fmts.get("csv", "—"),
                          fmts.get("json", "—"), fmts.get("duckdb", "—"))
            console.print(t)

        # ── Final Panel ──
        n_resolved = sum(1 for r in self.records if r.get("resolve_status") in ("OK", "PARTIAL"))
        n_unresolved = len(self.records) - n_resolved
        full_coverage = sum(1 for r in self.records if r.get("n_sources_available", 0) >= 4)
        overall = ("[bold green]✅ All resolved[/bold green]"
                   if n_unresolved == 0 and len(self.records) > 0 else
                   "[bold yellow]⚠️ Partial[/bold yellow]")
        summary = (
            f"[bold]Inputs[/bold]              : {len(self.parsed)}\n"
            f"[bold]Resolved[/bold]           : {n_resolved}\n"
            f"[bold]Unresolved[/bold]         : {n_unresolved}\n"
            f"[bold]Full coverage (4/4)[/bold] : {full_coverage}\n"
            f"[bold]Output tables[/bold]      : {len(self.save_results)}\n"
            f"[bold]耗時[/bold]               : {elapsed}s\n\n{overall}"
        )
        console.print(Panel.fit(summary,
                                title="[bold cyan]🎯 SSOT Resolver Result[/bold cyan]",
                                border_style="cyan"))

    def _plain_summary(self):
        print(f"\nMDL007 Resolved: {len(self.records)} records")


# =====================================================================================
# 🎯 Entry
# =====================================================================================

def main():
    eng = SSOTResolverEngine()
    return eng.run()


if __name__ == "__main__":
    try:
        ec = main()
        if "--no-pause" not in sys.argv:
            try: input("\n按 Enter 鍵退出...")
            except (EOFError, KeyboardInterrupt): pass
        sys.exit(ec)
    except KeyboardInterrupt:
        print("\n⚠️ 中斷"); sys.exit(1)
    except Exception as e:
        print(f"\n❌ 未處理: {e}")
        sys.exit(1)
