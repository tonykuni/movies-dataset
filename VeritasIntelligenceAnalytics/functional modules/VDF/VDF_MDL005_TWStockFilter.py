#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
================================================================================
  VDF_MDL005_TWStockFilter.py
================================================================================
  VERITAS DATA FRAMEWORK · MDL005  TW Stock Filter + Consensus Aggregator
  Version    : 1.0.0   |   Module ID : VDF-MDL005-FLT-001
  Asset ID   : VDF-MDL005-CLS-001
  Policy     : 功能只增不減 · append-only · SSOT · LL-compliant

ROLE
================================================================================
  1. 接收 universe (TW 全市場 from MDL001_TWUniverse + 海外股 如 NVDA)
  2. 每檔抓 YFinance Consensus + 估值資料 (paid FactSet 可選 stub)
  3. 計算 Upside %, Cash Yield, PER forward
  4. 多格式輸出 + Rich Summary Matrix

OUTPUT SCHEMA (使用者規格)
================================================================================
  date, ticker, yf_ticker, name, market, adj_close, volume,
  yf_target_price_mean, yf_target_price_median,
  yf_target_price_high, yf_target_price_low,
  yf_recommendation, yf_num_analysts,
  fs_target_price_mean, fs_target_price_median,           ← FactSet (stub)
  diluted_eps_2024, diluted_eps_2025,
  diluted_eps_2026, diluted_eps_2027,
  yf_upside_pct_mean, yf_upside_pct_median,
  fs_upside_pct_mean, fs_upside_pct_median,
  per_2026, per_2027,
  yf_dps_2026, yf_dps_2027,
  yf_cash_yield_2026_pct, yf_cash_yield_2027_pct

USAGE
================================================================================
  python VDF_MDL005_TWStockFilter.py                       # 全 universe
  python VDF_MDL005_TWStockFilter.py --tickers 2330,3324,NVDA
  python VDF_MDL005_TWStockFilter.py --universe twse       # 僅 TWSE
  python VDF_MDL005_TWStockFilter.py --max 100             # 限制檔數 (debug)
  python VDF_MDL005_TWStockFilter.py --no-pause            # CI 模式
"""

# ===== [VIA:ANCHOR:SUPPORT:BOOTSTRAP:START] =====
# 接橋補丁(2026-08-13 稽核令 TOOL-009 後續:功能引擎統一導入支援模組;
#  graceful 全退化 — 橋/核心缺席零影響;不 eager 導入 Runtime_Bridge/EnvManager 重件)
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
try:
    import VIA_SSOT_Unified as _VIA_SSOT
except Exception:
    _VIA_SSOT = None
try:
    import VeritasAegisNexus as _VIA_AEGIS
except Exception:
    _VIA_AEGIS = None
try:
    import VeritasCeleritas as _VIA_CELERITAS
except Exception:
    _VIA_CELERITAS = None
# ===== [VIA:ANCHOR:SUPPORT:BOOTSTRAP:END] =====


# =====================================================================================
# 📋 ALL PARAMETERS ON TOP
# =====================================================================================

PROJECT_NAME       = "1-5-TWStockFilter"
# 歸檔可攜補丁(2026-08-12 整合去重歸戶;工作站正本路徑優先,缺席退本地 db — 內容零改):
import os as _os
from pathlib import Path as _P
_PROD_BASE = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VDF\dict"
BASE_DIR           = _PROD_BASE if _os.path.isdir(_PROD_BASE) else str(_P(__file__).parent / "db")

OUTPUT_DIR         = "1-5-TWStockFilter"

# Universe 來源
UNIVERSE_SOURCE    = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VDF\dict\1-0-TWUniverse"
UNIVERSE_FILE      = "tw_universe_combined.parquet"   # 由 MDL001_TWUniverse_Verify 產
EXTRA_TICKERS      = ["NVDA", "TSM", "AAPL"]          # 額外加入的海外股

# YFinance 設定
YF_BATCH_SIZE      = 50
YF_PERIOD_HIST     = "5d"     # 抓最近 5 天日線取最新收盤
YF_TIMEOUT         = 15
YF_RETRY           = 3

# FactSet (paid API · stub for integration)
FACTSET_API_KEY    = ""        # 留空 = 跳過
FACTSET_USERNAME   = ""
FACTSET_BASE_URL   = "https://api.factset.com/content/factset-estimates/v2"

# Forward EPS 年度 (使用者要 2024~2027)
EPS_FISCAL_YEARS   = [2024, 2025, 2026, 2027]

# 加速 + 容錯
ENABLE_THREADPOOL  = True
THREADPOOL_WORKERS = 8
MAX_RETRIES        = 3
RETRY_DELAY        = 1.5

# 輸出格式 (Parquet 必選)
OUTPUT_PARQUET     = True
OUTPUT_DUCKDB      = True
OUTPUT_CSV         = True
OUTPUT_JSON        = True
OUTPUT_GSHEET      = False
CSV_ENCODING       = "utf-8-sig"
JSON_INDENT        = 2
DUCKDB_FILENAME    = "VDF_MDL005_TWStockFilter.duckdb"

# Backup
ENABLE_BACKUP      = True
MAX_BACKUP_FILES   = 5
LOG_LEVEL          = "INFO"


# =====================================================================================
# 📦 Imports
# =====================================================================================

import os, sys, re, json, time, warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
warnings.filterwarnings('ignore')

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    import pyarrow as pa
    PYARROW_AVAILABLE = True
except ImportError:
    PYARROW_AVAILABLE = False

try:
    import duckdb
    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    yf = None

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich import box
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    console = None


# =====================================================================================
# 🔧 Utilities
# =====================================================================================

def _now_iso() -> str:
    return datetime.now().isoformat(timespec='seconds')


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _yf_suffix(market: str) -> str:
    """TWSE → .TW, TPEX → .TWO, 其他 → ''."""
    if market == "TWSE": return ".TW"
    if market == "TPEX": return ".TWO"
    return ""


def _resolve_yf_ticker(ticker: str, market: Optional[str] = None) -> str:
    """
    將 TW 4 碼 → yfinance 格式.
      2330 + TWSE → 2330.TW
      3324 + TPEX → 3324.TWO
      NVDA → NVDA (海外股)
    """
    t = str(ticker).strip().upper()
    if '.' in t or '^' in t or '=' in t:
        return t  # 已是 yf 格式
    if re.match(r'^[1-9]\d{3}$', t):
        # TW 4 碼, 需 suffix
        if market == "TPEX": return f"{t}.TWO"
        return f"{t}.TW"  # default TWSE
    return t  # 海外股原樣


# =====================================================================================
# 📡 [Fetcher-1] YFinanceConsensusFetcher
# =====================================================================================

class YFinanceConsensusFetcher:
    """
    抓 yfinance 公開 consensus:
      - tk.info: targetMeanPrice / targetMedianPrice / targetHighPrice / targetLowPrice
                 recommendationKey / numberOfAnalystOpinions
                 trailingEps / forwardEps / trailingPE / forwardPE
                 dividendRate / dividendYield
      - tk.earnings_estimate (per fiscal year EPS forecast)
      - tk.history (Adj Close, Volume)
    """

    VERSION = "1.0.0"

    def __init__(self):
        self.stats = {"ok": 0, "fail": 0, "errors": []}

    def _fetch_one(self, yf_ticker: str) -> Dict[str, Any]:
        """單一 ticker 抓全資料."""
        result = {
            "yf_ticker": yf_ticker,
            "adj_close": None, "volume": None,
            "yf_target_price_mean":   None, "yf_target_price_median": None,
            "yf_target_price_high":   None, "yf_target_price_low":    None,
            "yf_recommendation":      None, "yf_num_analysts":        None,
            "yf_trailing_eps":        None, "yf_forward_eps":         None,
            "yf_trailing_pe":         None, "yf_forward_pe":          None,
            "yf_dividend_rate":       None, "yf_dividend_yield":      None,
            "yf_name":                None, "yf_currency":            None,
            "diluted_eps_2024":       None, "diluted_eps_2025":       None,
            "diluted_eps_2026":       None, "diluted_eps_2027":       None,
            "yf_eps_growth_estimate": None,
            "_yf_fetch_error":        None,
        }
        if not YFINANCE_AVAILABLE or yf is None:
            result["_yf_fetch_error"] = "yfinance_not_installed"
            return result

        for attempt in range(MAX_RETRIES):
            try:
                tk = yf.Ticker(yf_ticker)

                # ── Price + Volume ──
                hist = tk.history(period=YF_PERIOD_HIST, timeout=YF_TIMEOUT)
                if hist is not None and not hist.empty:
                    last = hist.iloc[-1]
                    result["adj_close"] = float(last.get("Close", float('nan')))
                    result["volume"]    = int(last.get("Volume", 0) or 0)

                # ── Info dict ──
                try:
                    info = tk.info or {}
                except Exception:
                    info = {}
                result["yf_name"]                = info.get("shortName") or info.get("longName")
                result["yf_currency"]            = info.get("currency")
                result["yf_target_price_mean"]   = info.get("targetMeanPrice")
                result["yf_target_price_median"] = info.get("targetMedianPrice")
                result["yf_target_price_high"]   = info.get("targetHighPrice")
                result["yf_target_price_low"]    = info.get("targetLowPrice")
                result["yf_recommendation"]      = info.get("recommendationKey")
                result["yf_num_analysts"]        = info.get("numberOfAnalystOpinions")
                result["yf_trailing_eps"]        = info.get("trailingEps")
                result["yf_forward_eps"]         = info.get("forwardEps")
                result["yf_trailing_pe"]         = info.get("trailingPE")
                result["yf_forward_pe"]          = info.get("forwardPE")
                result["yf_dividend_rate"]       = info.get("dividendRate")
                result["yf_dividend_yield"]      = info.get("dividendYield")

                # ── Earnings estimates per year (2024~2027) ──
                # yfinance 提供 tk.earnings_estimate (newer) 或 tk.earnings_forecasts
                try:
                    est = None
                    if hasattr(tk, 'earnings_estimate'):
                        est = tk.earnings_estimate
                    if est is None and hasattr(tk, 'earnings_forecasts'):
                        est = tk.earnings_forecasts
                    if est is not None and hasattr(est, 'index'):
                        # est 的 index 通常 ['0q','+1q','0y','+1y'] 對應當/下季/當/下年
                        # avg column 是 mean EPS estimate
                        for idx_key in est.index:
                            avg_val = None
                            try:
                                avg_val = est.loc[idx_key].get('avg')
                            except Exception:
                                pass
                            # +1y EPS → forward year
                            # 暫存到 result, 後面用 fiscal year 推斷對應到 2024-2027
                except Exception as e:
                    pass

                # 用 trailingEps + forwardEps 推估 2024-2027 (yfinance 公開 API 只給 2 年)
                # 實務上專業數據需 FactSet/Bloomberg
                trailing = result["yf_trailing_eps"]
                forward  = result["yf_forward_eps"]
                if trailing is not None and forward is not None:
                    # 估計成長率
                    try:
                        growth = (forward - trailing) / abs(trailing) if trailing != 0 else 0
                        result["yf_eps_growth_estimate"] = round(growth * 100, 2)
                    except Exception:
                        pass
                # 2024 = trailing, 2025 = forward, 2026/2027 = forward * (1+growth)^n
                # 註: 這只是 best-effort, 實務應接 FactSet
                if trailing is not None: result["diluted_eps_2024"] = trailing
                if forward is not None:  result["diluted_eps_2025"] = forward
                if trailing is not None and forward is not None and trailing != 0:
                    growth_factor = forward / trailing
                    if 0.5 < growth_factor < 3.0:  # sanity check
                        result["diluted_eps_2026"] = round(forward * growth_factor, 4)
                        result["diluted_eps_2027"] = round(forward * growth_factor * growth_factor, 4)

                self.stats["ok"] += 1
                return result
            except Exception as e:
                last_err = str(e)[:120]
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    result["_yf_fetch_error"] = last_err
                    self.stats["fail"] += 1
                    self.stats["errors"].append(f"{yf_ticker}: {last_err}")
        return result

    def fetch_batch(self, tickers: List[Tuple[str, str]]) -> "pd.DataFrame":
        """
        並發抓 batch.
        tickers: list of (yf_ticker, raw_ticker) tuples
        """
        if pd is None:
            return pd.DataFrame() if pd is not None else None
        results = []
        if ENABLE_THREADPOOL and len(tickers) > 1:
            with ThreadPoolExecutor(max_workers=THREADPOOL_WORKERS) as pool:
                futmap = {pool.submit(self._fetch_one, yf_t): (yf_t, raw_t)
                          for yf_t, raw_t in tickers}
                for fut in as_completed(futmap):
                    yf_t, raw_t = futmap[fut]
                    try:
                        r = fut.result()
                        r["ticker"] = raw_t
                        results.append(r)
                    except Exception as e:
                        self.stats["errors"].append(f"{yf_t}: future_fail: {str(e)[:80]}")
        else:
            for yf_t, raw_t in tickers:
                r = self._fetch_one(yf_t)
                r["ticker"] = raw_t
                results.append(r)
        return pd.DataFrame(results)


# =====================================================================================
# 💰 [Fetcher-2] FactSetConsensusFetcher (STUB · paid API)
# =====================================================================================

class FactSetConsensusFetcher:
    """
    FactSet Estimates API 整合點 (需付費憑證).
    若 FACTSET_API_KEY 為空, 直接 return None 並標 _factset_skipped.
    保留完整介面供使用者填入憑證後啟用.
    """

    VERSION = "1.0.0"

    def __init__(self, api_key: str = FACTSET_API_KEY, username: str = FACTSET_USERNAME):
        self.api_key  = api_key
        self.username = username
        self.enabled  = bool(api_key) and bool(username)
        self.stats    = {"ok": 0, "fail": 0, "skipped": 0, "errors": []}

    def _fetch_one(self, ticker: str) -> Dict[str, Any]:
        result = {
            "ticker":                  ticker,
            "fs_target_price_mean":    None,
            "fs_target_price_median":  None,
            "fs_target_price_high":    None,
            "fs_target_price_low":     None,
            "fs_recommendation":       None,
            "fs_num_analysts":         None,
            "fs_eps_estimate_2026":    None,
            "fs_eps_estimate_2027":    None,
            "_fs_status":              "SKIPPED",
        }
        if not self.enabled:
            self.stats["skipped"] += 1
            return result

        if not REQUESTS_AVAILABLE:
            result["_fs_status"] = "NO_REQUESTS"
            self.stats["skipped"] += 1
            return result

        try:
            # FactSet Estimates API 範例端點 (參考 docs.factset.com)
            #   GET /content/factset-estimates/v2/consensus
            #   params: ids=<TICKER>, metric=PRICE_TGT
            #   auth: HTTPBasicAuth(username, api_key)
            url = f"{FACTSET_BASE_URL}/consensus"
            params = {"ids": ticker, "metrics": "PRICE_TGT,EPS"}
            from requests.auth import HTTPBasicAuth
            r = requests.get(url, params=params, timeout=YF_TIMEOUT,
                             auth=HTTPBasicAuth(self.username, self.api_key))
            if r.ok:
                data = r.json()
                # 解析 FactSet response 結構
                # 此為 stub, 實際 schema 依 FactSet API 文件
                rows = data.get("data", [])
                for row in rows:
                    metric = row.get("metric")
                    if metric == "PRICE_TGT":
                        result["fs_target_price_mean"]   = row.get("mean")
                        result["fs_target_price_median"] = row.get("median")
                        result["fs_target_price_high"]   = row.get("high")
                        result["fs_target_price_low"]    = row.get("low")
                        result["fs_num_analysts"]        = row.get("count")
                self.stats["ok"] += 1
                result["_fs_status"] = "OK"
            else:
                result["_fs_status"] = f"HTTP_{r.status_code}"
                self.stats["fail"] += 1
        except Exception as e:
            result["_fs_status"] = f"ERROR_{str(e)[:60]}"
            self.stats["fail"] += 1
            self.stats["errors"].append(f"{ticker}: {str(e)[:120]}")
        return result

    def fetch_batch(self, tickers: List[str]) -> "pd.DataFrame":
        if pd is None or not self.enabled:
            # 回傳 stub DataFrame
            if pd is not None and tickers:
                return pd.DataFrame([self._fetch_one(t) for t in tickers])
            return pd.DataFrame() if pd is not None else None
        results = []
        if ENABLE_THREADPOOL and len(tickers) > 1:
            with ThreadPoolExecutor(max_workers=THREADPOOL_WORKERS) as pool:
                futmap = {pool.submit(self._fetch_one, t): t for t in tickers}
                for fut in as_completed(futmap):
                    try:
                        results.append(fut.result())
                    except Exception as e:
                        pass
        else:
            for t in tickers:
                results.append(self._fetch_one(t))
        return pd.DataFrame(results)


# =====================================================================================
# 🧮 UpsideCalculator + 衍生欄位
# =====================================================================================

class UpsideCalculator:
    """
    計算:
      yf_upside_pct_mean / median   = (target_price - adj_close) / adj_close * 100
      fs_upside_pct_mean / median   = 同上 (FactSet)
      per_2026 / per_2027           = adj_close / diluted_eps_YYYY
      yf_dps_2026 / 2027            = dividend_rate (best-effort, yf 只給當前)
      yf_cash_yield_2026_pct        = dps / adj_close * 100
    """

    VERSION = "1.0.0"

    @staticmethod
    def calc_upside(target: Any, price: Any) -> Optional[float]:
        if pd is None: return None
        try:
            tp = float(target); p = float(price)
            if p <= 0: return None
            return round((tp - p) / p * 100, 2)
        except Exception:
            return None

    @staticmethod
    def calc_per(price: Any, eps: Any) -> Optional[float]:
        if pd is None: return None
        try:
            p = float(price); e = float(eps)
            if abs(e) < 0.01: return None
            return round(p / e, 2)
        except Exception:
            return None

    @staticmethod
    def calc_cash_yield(dps: Any, price: Any) -> Optional[float]:
        if pd is None: return None
        try:
            d = float(dps); p = float(price)
            if p <= 0: return None
            return round(d / p * 100, 2)
        except Exception:
            return None

    @classmethod
    def apply(cls, df: "pd.DataFrame") -> "pd.DataFrame":
        """對整張 DataFrame 套用衍生欄位."""
        if pd is None or df is None or df.empty:
            return df
        df = df.copy()
        # Upside %
        df["yf_upside_pct_mean"]   = df.apply(
            lambda r: cls.calc_upside(r.get("yf_target_price_mean"),   r.get("adj_close")), axis=1)
        df["yf_upside_pct_median"] = df.apply(
            lambda r: cls.calc_upside(r.get("yf_target_price_median"), r.get("adj_close")), axis=1)
        # FactSet Upside
        df["fs_upside_pct_mean"]   = df.apply(
            lambda r: cls.calc_upside(r.get("fs_target_price_mean"),   r.get("adj_close")), axis=1)
        df["fs_upside_pct_median"] = df.apply(
            lambda r: cls.calc_upside(r.get("fs_target_price_median"), r.get("adj_close")), axis=1)
        # PER 2026 / 2027
        df["per_2026"] = df.apply(
            lambda r: cls.calc_per(r.get("adj_close"), r.get("diluted_eps_2026")), axis=1)
        df["per_2027"] = df.apply(
            lambda r: cls.calc_per(r.get("adj_close"), r.get("diluted_eps_2027")), axis=1)
        # DPS 2026 / 2027 (yf 只給當前 dividendRate, 推估)
        df["yf_dps_2026"] = df["yf_dividend_rate"]
        # 假設 +5% 成長 (best-effort, 實務應用 FactSet/分析師估計)
        df["yf_dps_2027"] = df["yf_dividend_rate"].apply(
            lambda d: round(float(d) * 1.05, 4) if d is not None and pd.notna(d) else None)
        # Cash Yield
        df["yf_cash_yield_2026_pct"] = df.apply(
            lambda r: cls.calc_cash_yield(r.get("yf_dps_2026"), r.get("adj_close")), axis=1)
        df["yf_cash_yield_2027_pct"] = df.apply(
            lambda r: cls.calc_cash_yield(r.get("yf_dps_2027"), r.get("adj_close")), axis=1)
        return df


# =====================================================================================
# 📥 UniverseLoader (從 MDL001 verify 輸出 + EXTRA_TICKERS)
# =====================================================================================

class UniverseLoader:
    """讀 MDL001 verify 輸出的 tw_universe_combined.parquet."""

    def __init__(self):
        self.stats = {"tw_loaded": 0, "extra_loaded": 0, "fallback_used": False}

    def load(self, universe_filter: Optional[str] = None,
             max_n: Optional[int] = None) -> "pd.DataFrame":
        """
        universe_filter: 'twse' | 'tpex' | None (all)
        max_n: 限制檔數 (debug)
        """
        if pd is None:
            return pd.DataFrame()

        p = Path(UNIVERSE_SOURCE) / UNIVERSE_FILE
        df_tw = None
        if p.exists():
            try:
                df_tw = pd.read_parquet(p)
                self.stats["tw_loaded"] = len(df_tw)
            except Exception as e:
                print(f"⚠️ universe parquet 讀取失敗: {e}")
                df_tw = None

        if df_tw is None or df_tw.empty:
            # Fallback: hardcoded 主流 TW 個股 (debug 用)
            self.stats["fallback_used"] = True
            df_tw = pd.DataFrame([
                {"code": "2330", "name": "台積電",   "market": "TWSE"},
                {"code": "2317", "name": "鴻海",     "market": "TWSE"},
                {"code": "2454", "name": "聯發科",   "market": "TWSE"},
                {"code": "2308", "name": "台達電",   "market": "TWSE"},
                {"code": "2382", "name": "廣達",     "market": "TWSE"},
                {"code": "2891", "name": "中信金",   "market": "TWSE"},
                {"code": "2412", "name": "中華電",   "market": "TWSE"},
                {"code": "3008", "name": "大立光",   "market": "TWSE"},
                {"code": "6505", "name": "台塑化",   "market": "TWSE"},
                {"code": "2603", "name": "長榮",     "market": "TWSE"},
                {"code": "3324", "name": "雙鴻",     "market": "TPEX"},
                {"code": "6415", "name": "矽力-KY", "market": "TPEX"},
                {"code": "5483", "name": "中美晶",   "market": "TPEX"},
                {"code": "6488", "name": "環球晶",   "market": "TPEX"},
                {"code": "8069", "name": "元太",     "market": "TPEX"},
            ])
            self.stats["tw_loaded"] = len(df_tw)

        # Filter market
        if universe_filter:
            uf = universe_filter.upper()
            df_tw = df_tw[df_tw["market"] == uf].reset_index(drop=True)

        # 加 yf_ticker 欄
        df_tw = df_tw.copy()
        df_tw["yf_ticker"] = df_tw.apply(
            lambda r: _resolve_yf_ticker(r["code"], r.get("market")), axis=1)
        df_tw["ticker"] = df_tw["code"]

        # 加 EXTRA_TICKERS (海外股)
        extras = []
        for t in EXTRA_TICKERS:
            extras.append({"ticker": t, "code": t, "name": t,
                           "market": "US", "yf_ticker": t})
        if extras:
            df_extra = pd.DataFrame(extras)
            df_tw = pd.concat([df_tw, df_extra], ignore_index=True)
            self.stats["extra_loaded"] = len(extras)

        # Max limit
        if max_n is not None and max_n > 0:
            df_tw = df_tw.head(max_n).reset_index(drop=True)

        return df_tw[["ticker", "yf_ticker", "name", "market"]]


# =====================================================================================
# 💾 OutputManager (Parquet 必選 + DuckDB + CSV + JSON + GSheet stub)
# =====================================================================================

class OutputManager:
    VERSION = "1.0.0"

    def __init__(self):
        self.output_dir = Path(BASE_DIR) / OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir = self.output_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        self.duckdb_path = self.output_dir / DUCKDB_FILENAME

        self.enable_parquet = OUTPUT_PARQUET
        self.enable_duckdb  = OUTPUT_DUCKDB and DUCKDB_AVAILABLE
        self.enable_csv     = OUTPUT_CSV
        self.enable_json    = OUTPUT_JSON
        self.enable_gsheet  = OUTPUT_GSHEET

        if "--no-parquet" in sys.argv: self.enable_parquet = False
        if "--no-duckdb"  in sys.argv: self.enable_duckdb  = False
        if "--no-csv"     in sys.argv: self.enable_csv     = False
        if "--no-json"    in sys.argv: self.enable_json    = False
        if "--gsheet"     in sys.argv: self.enable_gsheet  = True
        self.results = {}

    def _backup(self, path: Path):
        if not ENABLE_BACKUP or not path.exists(): return
        try:
            import shutil
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            shutil.copy2(path, self.backup_dir / f"{ts}_{path.name}")
        except Exception:
            pass

    def save(self, name: str, df: "pd.DataFrame") -> Dict:
        if pd is None or df is None or df.empty:
            self.results[name] = {"rows": 0, "outputs": []}
            return self.results[name]
        outputs = []
        if self.enable_parquet and PYARROW_AVAILABLE:
            p = self.output_dir / f"{name}.parquet"
            self._backup(p)
            try:
                df.to_parquet(p, index=False)
                outputs.append({"format": "parquet", "path": str(p),
                                "size_kb": p.stat().st_size // 1024})
            except Exception as e:
                outputs.append({"format": "parquet", "error": str(e)[:80]})
        if self.enable_csv:
            p = self.output_dir / f"{name}.csv"
            try:
                df.to_csv(p, index=False, encoding=CSV_ENCODING)
                outputs.append({"format": "csv", "path": str(p),
                                "size_kb": p.stat().st_size // 1024})
            except Exception as e:
                outputs.append({"format": "csv", "error": str(e)[:80]})
        if self.enable_json:
            p = self.output_dir / f"{name}.json"
            try:
                d = df.copy()
                for c in d.columns:
                    if pd.api.types.is_datetime64_any_dtype(d[c]):
                        d[c] = d[c].dt.strftime('%Y-%m-%d')
                d.to_json(p, orient="records", indent=JSON_INDENT, force_ascii=False)
                outputs.append({"format": "json", "path": str(p),
                                "size_kb": p.stat().st_size // 1024})
            except Exception as e:
                outputs.append({"format": "json", "error": str(e)[:80]})
        if self.enable_duckdb and DUCKDB_AVAILABLE:
            try:
                conn = duckdb.connect(str(self.duckdb_path))
                conn.register("__tmp__", df)
                conn.execute(f"DROP TABLE IF EXISTS \"{name}\"")
                conn.execute(f"CREATE TABLE \"{name}\" AS SELECT * FROM __tmp__")
                conn.close()
                outputs.append({"format": "duckdb", "path": str(self.duckdb_path),
                                "table": name})
            except Exception as e:
                outputs.append({"format": "duckdb", "error": str(e)[:80]})
        self.results[name] = {"rows": len(df), "outputs": outputs}
        return self.results[name]


# =====================================================================================
# 🎯 StockFilterEngine (主類)
# =====================================================================================

class StockFilterEngine:
    """
    Pipeline:
      1. UniverseLoader  → 載入 TW universe + EXTRA tickers
      2. YFinanceConsensusFetcher → 抓 consensus, EPS, target price, DPS
      3. FactSetConsensusFetcher  → 抓 FactSet (paid stub)
      4. UpsideCalculator → 計算 Upside%, PER, Cash Yield
      5. OutputManager   → Parquet/DuckDB/CSV/JSON/GSheet
    """

    VERSION = "1.0.0"

    # User-spec final schema (display order)
    OUTPUT_SCHEMA = [
        "date", "ticker", "yf_ticker", "name", "market",
        "adj_close", "volume",
        "yf_target_price_mean", "yf_target_price_median",
        "yf_target_price_high", "yf_target_price_low",
        "yf_recommendation", "yf_num_analysts",
        "fs_target_price_mean", "fs_target_price_median",
        "fs_target_price_high", "fs_target_price_low",
        "fs_num_analysts",
        "diluted_eps_2024", "diluted_eps_2025",
        "diluted_eps_2026", "diluted_eps_2027",
        "yf_upside_pct_mean", "yf_upside_pct_median",
        "fs_upside_pct_mean", "fs_upside_pct_median",
        "per_2026", "per_2027",
        "yf_dps_2026", "yf_dps_2027",
        "yf_cash_yield_2026_pct", "yf_cash_yield_2027_pct",
        "yf_trailing_eps", "yf_forward_eps",
        "yf_trailing_pe",  "yf_forward_pe",
        "yf_dividend_rate","yf_dividend_yield",
    ]

    def __init__(self):
        self.loader        = UniverseLoader()
        self.yf_fetcher    = YFinanceConsensusFetcher()
        self.fs_fetcher    = FactSetConsensusFetcher()
        self.output_mgr    = OutputManager()
        self.start_time    = time.time()
        self.df_universe   = None
        self.df_final      = None
        self.save_results  = {}
        # CLI args
        self.tickers_override = None
        self.universe_filter  = None
        self.max_n            = None
        for i, arg in enumerate(sys.argv):
            if arg == "--tickers" and i+1 < len(sys.argv):
                self.tickers_override = [t.strip().upper() for t in sys.argv[i+1].split(",") if t.strip()]
            if arg == "--universe" and i+1 < len(sys.argv):
                self.universe_filter = sys.argv[i+1]
            if arg == "--max" and i+1 < len(sys.argv):
                try: self.max_n = int(sys.argv[i+1])
                except ValueError: pass

    def show_header(self):
        header = f"""
🎯 VDF MDL005 · TW Stock Filter + Consensus Aggregator (v{self.VERSION})

📁 Universe   : {UNIVERSE_SOURCE}\\{UNIVERSE_FILE}
              + EXTRA: {', '.join(EXTRA_TICKERS)}
🌐 YFinance   : {'✅' if YFINANCE_AVAILABLE else '❌ pip install yfinance'}
💰 FactSet    : {'✅ enabled' if self.fs_fetcher.enabled else '⚪ disabled (set FACTSET_API_KEY)'}
🚀 並發       : {THREADPOOL_WORKERS} workers
📅 EPS Years  : {EPS_FISCAL_YEARS}
🎛️ 設定       : universe={self.universe_filter or 'ALL'} · max={self.max_n or 'NoLimit'} · tickers_override={self.tickers_override or '—'}
💾 Output     : Parquet={'✅' if self.output_mgr.enable_parquet else '—'} · DuckDB={'✅' if self.output_mgr.enable_duckdb else '—'} · CSV={'✅' if self.output_mgr.enable_csv else '—'} · JSON={'✅' if self.output_mgr.enable_json else '—'} · GSheet={'✅' if self.output_mgr.enable_gsheet else '—'}
        """
        if RICH_AVAILABLE:
            console.print(Panel(header.strip(), title="[bold blue]VDF MDL005 · TW Stock Filter[/bold blue]",
                                border_style="blue"))
        else:
            print(header)

    def run(self) -> int:
        try:
            self.show_header()
            # ── 1. Load universe ──
            print("\n🔍 步驟 1/5: 載入 Universe")
            if self.tickers_override:
                # 手動 override: 用 ticker list 直接建 universe
                rows = []
                for t in self.tickers_override:
                    # 判定是否 TW 4 碼
                    if re.match(r'^[1-9]\d{3}$', t):
                        rows.append({"ticker": t, "yf_ticker": f"{t}.TW",
                                     "name": t, "market": "TWSE"})  # 預設 TWSE
                    else:
                        rows.append({"ticker": t, "yf_ticker": t,
                                     "name": t, "market": "US"})
                self.df_universe = pd.DataFrame(rows) if pd is not None else None
            else:
                self.df_universe = self.loader.load(self.universe_filter, self.max_n)
            uni_n = len(self.df_universe) if self.df_universe is not None else 0
            print(f"   ✓ Universe 載入: {uni_n} 檔  (fallback used: {self.loader.stats.get('fallback_used')})")

            if uni_n == 0:
                print("❌ Universe 為空, 中止"); return 1

            # ── 2. YFinance fetch ──
            print(f"\n🌐 步驟 2/5: YFinance Consensus + EPS + DPS 抓取 ({uni_n} 檔)")
            tk_pairs = [(r["yf_ticker"], r["ticker"])
                        for _, r in self.df_universe.iterrows()]
            df_yf = self.yf_fetcher.fetch_batch(tk_pairs)
            print(f"   ✓ YF 完成: ok={self.yf_fetcher.stats['ok']} / fail={self.yf_fetcher.stats['fail']}")

            # ── 3. FactSet fetch (stub) ──
            print(f"\n💰 步驟 3/5: FactSet Consensus (paid API)")
            tickers_only = [r["ticker"] for _, r in self.df_universe.iterrows()]
            df_fs = self.fs_fetcher.fetch_batch(tickers_only)
            print(f"   {'✓' if self.fs_fetcher.enabled else '⏭️'} FS: ok={self.fs_fetcher.stats['ok']} / "
                  f"fail={self.fs_fetcher.stats['fail']} / skipped={self.fs_fetcher.stats['skipped']}")

            # ── 4. Merge + Calculate ──
            print(f"\n🧮 步驟 4/5: 合併 + 計算衍生欄位 (Upside, PER, Cash Yield)")
            df = self.df_universe.merge(df_yf, on=["yf_ticker", "ticker"], how="left") if pd is not None else None
            if df_fs is not None and not df_fs.empty:
                df = df.merge(df_fs, on="ticker", how="left")
            df["date"] = _today()
            df = UpsideCalculator.apply(df)

            # Reorder to OUTPUT_SCHEMA
            cols_present = [c for c in self.OUTPUT_SCHEMA if c in df.columns]
            cols_extra   = [c for c in df.columns if c not in self.OUTPUT_SCHEMA and not c.startswith('_')]
            df_final = df[cols_present + cols_extra]
            self.df_final = df_final
            print(f"   ✓ 合併完成: {len(df_final)} 列 × {len(df_final.columns)} 欄")

            # ── 5. Output ──
            print(f"\n💾 步驟 5/5: 多格式輸出")
            self.save_results["stock_filter_consensus"] = self.output_mgr.save("stock_filter_consensus", df_final)
            for tbl, info in self.save_results.items():
                fmts = [o.get("format") for o in info.get("outputs", []) if "error" not in o]
                print(f"   ✓ {tbl:<28} → {info['rows']:>6,} 列  [{' · '.join(fmts)}]")

            # ── Rich Summary ──
            print_rich_summary(self)
            print(f"\n🎉 完成! 輸出: {self.output_mgr.output_dir}")
            return 0
        except KeyboardInterrupt:
            print("\n⚠️ 用戶中斷"); return 1
        except Exception as e:
            print(f"\n❌ 錯誤: {e}")
            if LOG_LEVEL == "DEBUG":
                import traceback; traceback.print_exc()
            return 1


# =====================================================================================
# 🎨 Rich Summary Matrix
# =====================================================================================

def print_rich_summary(eng: StockFilterEngine):
    if not RICH_AVAILABLE: return _plain(eng)
    elapsed = round(time.time() - eng.start_time, 2)
    console.rule("[bold cyan]🎯 VDF MDL005 · TW Stock Filter · Summary Matrix[/bold cyan]")

    # Table 1: 套件依賴
    t = Table(title="📦 [bold]套件依賴[/bold]", box=box.ROUNDED, header_style="bold magenta")
    t.add_column("套件", style="cyan", width=18)
    t.add_column("狀態", style="green", width=8, justify="center")
    t.add_column("用途", style="yellow", width=48)
    t.add_row("pandas/numpy", "✅" if PANDAS_AVAILABLE else "❌", "資料表 + 衍生計算")
    t.add_row("yfinance",     "✅" if YFINANCE_AVAILABLE else "❌", "YF Consensus + Price")
    t.add_row("requests",     "✅" if REQUESTS_AVAILABLE else "❌", "FactSet (paid) HTTP")
    t.add_row("pyarrow",      "✅" if PYARROW_AVAILABLE else "⚪", "Parquet 輸出")
    t.add_row("duckdb",       "✅" if DUCKDB_AVAILABLE else "⚪", "DuckDB 單檔資料庫")
    t.add_row("rich",         "✅" if RICH_AVAILABLE else "⚪", "終端表格")
    console.print(t)

    # Table 2: Pipeline 狀態
    t = Table(title="🚀 [bold]Pipeline 狀態[/bold]", box=box.ROUNDED, header_style="bold magenta")
    t.add_column("階段", style="cyan", width=18)
    t.add_column("狀態", style="green", width=8, justify="center")
    t.add_column("細節", style="yellow", width=50)
    uni_n = len(eng.df_universe) if eng.df_universe is not None else 0
    t.add_row("Universe Load", "✅" if uni_n > 0 else "❌",
              f"TW={eng.loader.stats['tw_loaded']} + Extra={eng.loader.stats['extra_loaded']}" +
              (" (fallback)" if eng.loader.stats.get('fallback_used') else ""))
    t.add_row("YFinance", "✅" if eng.yf_fetcher.stats['ok'] > 0 else "❌",
              f"ok={eng.yf_fetcher.stats['ok']} · fail={eng.yf_fetcher.stats['fail']} · " +
              f"errors[:3]={eng.yf_fetcher.stats['errors'][:3]}")
    t.add_row("FactSet", "✅" if eng.fs_fetcher.stats['ok'] > 0 else "⏭️",
              f"enabled={eng.fs_fetcher.enabled} · ok={eng.fs_fetcher.stats['ok']} · " +
              f"skipped={eng.fs_fetcher.stats['skipped']}")
    t.add_row("Merge + Calc", "✅" if eng.df_final is not None else "❌",
              f"final shape={eng.df_final.shape if eng.df_final is not None else '—'}")
    console.print(t)

    # Table 3: Universe 市場分布
    if pd is not None and eng.df_universe is not None and not eng.df_universe.empty:
        t = Table(title="🇹🇼 [bold]Universe 市場分布[/bold]", box=box.ROUNDED, header_style="bold magenta")
        t.add_column("Market", style="cyan", width=12)
        t.add_column("檔數",   style="green", width=10, justify="right")
        t.add_column("範例",   style="yellow", width=60)
        for mkt, cnt in eng.df_universe["market"].value_counts().items():
            sample = ", ".join(eng.df_universe[eng.df_universe["market"]==mkt]["ticker"].head(5).tolist())
            t.add_row(str(mkt), str(cnt), sample)
        console.print(t)

    # Table 4: Top tickers preview (Upside ranking)
    if pd is not None and eng.df_final is not None and not eng.df_final.empty:
        df = eng.df_final.copy()
        if "yf_upside_pct_mean" in df.columns:
            df = df.sort_values("yf_upside_pct_mean", ascending=False, na_position='last')
        preview_n = min(10, len(df))
        t = Table(title=f"📊 [bold]Top {preview_n} by YF Upside %[/bold]", box=box.ROUNDED, header_style="bold magenta")
        t.add_column("Ticker",  style="cyan",   width=10)
        t.add_column("Name",    style="yellow", width=18)
        t.add_column("Adj Close", style="green", width=10, justify="right")
        t.add_column("YF TP Mean", style="green", width=10, justify="right")
        t.add_column("Upside %", style="green",  width=10, justify="right")
        t.add_column("Rec",     style="yellow", width=12)
        t.add_column("# Analysts", style="yellow", width=10, justify="right")
        for _, r in df.head(preview_n).iterrows():
            up = r.get("yf_upside_pct_mean")
            up_str = f"{up:+.1f}%" if pd.notna(up) else "—"
            tp = r.get("yf_target_price_mean")
            tp_str = f"{float(tp):.2f}" if pd.notna(tp) else "—"
            ac = r.get("adj_close")
            ac_str = f"{float(ac):.2f}" if pd.notna(ac) else "—"
            na = r.get("yf_num_analysts")
            na_str = str(int(na)) if pd.notna(na) else "—"
            t.add_row(str(r.get("ticker", "—")),
                      str(r.get("name", ""))[:16],
                      ac_str, tp_str, up_str,
                      str(r.get("yf_recommendation", "—"))[:10], na_str)
        console.print(t)

    # Table 5: PER 評價 preview
    if pd is not None and eng.df_final is not None and not eng.df_final.empty:
        df = eng.df_final[eng.df_final["per_2026"].notna()] if "per_2026" in eng.df_final.columns else pd.DataFrame()
        if not df.empty:
            df = df.sort_values("per_2026", ascending=True, na_position='last')
            preview_n = min(8, len(df))
            t = Table(title=f"💰 [bold]Top {preview_n} by Forward PER 2026 (低估值)[/bold]",
                      box=box.ROUNDED, header_style="bold magenta")
            t.add_column("Ticker", style="cyan",   width=10)
            t.add_column("Name",   style="yellow", width=18)
            t.add_column("Price",  style="green",  width=10, justify="right")
            t.add_column("EPS 26", style="green",  width=10, justify="right")
            t.add_column("PER 26", style="green",  width=10, justify="right")
            t.add_column("EPS 27", style="green",  width=10, justify="right")
            t.add_column("PER 27", style="green",  width=10, justify="right")
            t.add_column("Yield %", style="yellow", width=10, justify="right")
            for _, r in df.head(preview_n).iterrows():
                def f(v, dec=2):
                    return f"{float(v):.{dec}f}" if pd.notna(v) else "—"
                t.add_row(str(r.get("ticker", "")),
                          str(r.get("name", ""))[:16],
                          f(r.get("adj_close")),
                          f(r.get("diluted_eps_2026")),
                          f(r.get("per_2026")),
                          f(r.get("diluted_eps_2027")),
                          f(r.get("per_2027")),
                          f(r.get("yf_cash_yield_2026_pct"), 2))
            console.print(t)

    # Table 6: 輸出狀態
    if eng.save_results:
        t = Table(title="💾 [bold]多格式輸出明細[/bold]", box=box.ROUNDED, header_style="bold magenta")
        t.add_column("Table",   style="cyan",   width=28)
        t.add_column("列數",    style="green",  width=10, justify="right")
        t.add_column("Parquet", style="yellow", width=10, justify="center")
        t.add_column("CSV",     style="yellow", width=8,  justify="center")
        t.add_column("JSON",    style="yellow", width=8,  justify="center")
        t.add_column("DuckDB",  style="yellow", width=10, justify="center")
        for tbl, info in eng.save_results.items():
            fmts = {o.get("format"): ("✅" if "error" not in o else "❌")
                    for o in info.get("outputs", [])}
            t.add_row(tbl, f"{info['rows']:,}",
                      fmts.get("parquet", "—"), fmts.get("csv", "—"),
                      fmts.get("json", "—"), fmts.get("duckdb", "—"))
        console.print(t)

    # Final panel
    uni_n = len(eng.df_universe) if eng.df_universe is not None else 0
    final_n = len(eng.df_final) if eng.df_final is not None else 0
    overall = ("[bold green]✅ Pipeline 全綠[/bold green]" if final_n > 0 and eng.yf_fetcher.stats['ok'] > 0
               else "[bold yellow]⚠️ 部分管道異常[/bold yellow]")
    summary = (
        f"[bold]Universe[/bold]      : {uni_n} 檔 (TW + Extra)\n"
        f"[bold]YF success[/bold]    : {eng.yf_fetcher.stats['ok']} / {uni_n}\n"
        f"[bold]FS status[/bold]     : {'enabled' if eng.fs_fetcher.enabled else 'STUB (set FACTSET_API_KEY to activate)'}\n"
        f"[bold]Final rows[/bold]    : {final_n}\n"
        f"[bold]Final cols[/bold]    : {len(eng.df_final.columns) if eng.df_final is not None else 0}\n"
        f"[bold]耗時[/bold]          : {elapsed} 秒\n\n{overall}"
    )
    console.print(Panel.fit(summary, title="[bold cyan]🎯 整體狀態[/bold cyan]", border_style="cyan"))


def _plain(eng):
    print(f"\n{'='*60}\nMDL005 Summary\n{'='*60}")
    print(f"  Final rows: {len(eng.df_final) if eng.df_final is not None else 0}")


# =====================================================================================
# 🎯 Entry
# =====================================================================================

def main():
    print("🚀 VDF MDL005 · TW Stock Filter 啟動...")
    eng = StockFilterEngine()
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
        if LOG_LEVEL == "DEBUG":
            import traceback; traceback.print_exc()
        sys.exit(1)
