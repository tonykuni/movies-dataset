#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
================================================================================
  VDF_MDL004_TWFullMarketEngine.py
================================================================================
  VERITAS DATA FRAMEWORK - MDL004  TW Full-Market Equity Engine (v2 升級)
  Version    : 2.0.0   |   Module ID : VDF-MDL004-FME-001
  Asset ID   : VDF-MDL004-CLS-001
  Policy     : 功能只增不減 · SSOT TW_TICKER_REGEX 鎖定 · 參考 VRN 多源 fallback

ROLE
================================================================================
  全市場 TW Equity Engine 升級版 (供 MDL005/006 上游使用), 一次抓出每檔個股:
    [1] Identity        ticker · yf_ticker · name · market(TWSE/TPEX)
    [2] Daily Quote     adj_close · volume · turnover · market_cap
    [3] Moving Average  sma_5 · sma_10 · sma_20 · sma_60 · sma_120 · sma_240 · ytd_pct
    [4] Average Volume  avg_vol_60 · avg_vol_120 · avg_vol_240
    [5] YF Consensus    target_mean/median/high/low · num_analysts · recommendation
    [6] FactSet         consensus stub (預留 API 接口)

  資料源優先序 (multi-source fallback, 參考 VRN_MDL004):
    Universe :  TWSE OpenAPI (上市) + TPEX OpenAPI (上櫃)
                fallback → yfinance ticker probe (從前次 universe parquet)
    Quote    :  TWSE STOCK_DAY_ALL + TPEX daily_close_quotes (一次抓全市場)
                fallback → yfinance individual ticker
    History  :  yfinance bulk download (period=1y) 批次 50 檔/次
    Consensus:  yfinance ticker.info (concurrent)
                fallback → FactSet API (stub)

SSOT (locked, immutable)
================================================================================
  TW_TICKER_REGEX     = r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})"
  TW_BLOOMBERG_REGEX  = r"([1-9]\d{3}) TT"
  TW_YFINANCE_REGEX   = r"([1-9]\d{3})\.(TW|TWO)"

DEPENDENCIES (透過 VDF_MDL101_OutputManager 共用)
================================================================================
  pandas · numpy · requests · yfinance · pyarrow · duckdb (optional) · rich (optional)

USAGE
================================================================================
  # 全市場全欄位 (~1900 檔 · 預估 5-10 min)
  python VDF_MDL004_TWFullMarketEngine.py --no-pause

  # 限定樣本 (測試)
  python VDF_MDL004_TWFullMarketEngine.py --max 50 --no-pause

  # 跳 Consensus (快速跑)
  python VDF_MDL004_TWFullMarketEngine.py --no-consensus --no-pause

  # 跳 SMA history (只抓 daily snapshot)
  python VDF_MDL004_TWFullMarketEngine.py --no-history --no-pause

  # 自定 universe (從 MDL001 verify 輸出讀)
  python VDF_MDL004_TWFullMarketEngine.py --universe-source 1-0-TWUniverse --no-pause
"""

# =====================================================================================
# 📋 ALL PARAMETERS ON TOP
# =====================================================================================

PROJECT_NAME       = "1-4-TWFullMarket"
BASE_DIR           = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VDF\dict"
OUTPUT_DIR         = "1-4-TWFullMarket"

# Universe source (從 MDL001 verify 讀, 或自抓)
UNIVERSE_SOURCE    = "1-0-TWUniverse"
UNIVERSE_FILE      = "tw_universe_combined.parquet"
USE_LOCAL_UNIVERSE = True   # True: 用 MDL001 verify 輸出 · False: 即時抓 OpenAPI

# 🔒 SSOT TW Ticker Regex (LOCKED, immutable)
TW_TICKER_REGEX    = r"(?!0)(?!202[1-9])(?!2030)([1-9]\d{3})"
TW_BLOOMBERG_REGEX = r"([1-9]\d{3}) TT"
TW_YFINANCE_REGEX  = r"([1-9]\d{3})\.(TW|TWO)"

# TWSE / TPEX OpenAPI endpoints
TWSE_DAILY_ALL_URL      = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
TWSE_LISTING_URL        = "https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL"   # 含市值/本益比
TPEX_DAILY_CLOSE_URL    = "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes"
TPEX_PEER_RATIO_URL     = "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_peratio_analysis"

# HTTP
HTTP_USER_AGENT    = "Mozilla/5.0 VeritasDataForge/VDF-MDL004"
HTTP_TIMEOUT       = 20
HTTP_RETRIES       = 3
HTTP_RETRY_DELAY   = 2

# YFinance settings
YF_HISTORY_PERIOD  = "1y"          # 1 年日線足夠算 240-day SMA
YF_HISTORY_INTERVAL= "1d"
YF_BULK_BATCH_SIZE = 50            # yf.download 批次大小
YF_TIMEOUT         = 15
YF_INFO_WORKERS    = 8             # ticker.info 並發 worker 數
YF_BULK_WORKERS    = 4             # bulk download 並發 worker 數
YF_RETRY_ATTEMPTS  = 3
YF_RETRY_DELAY     = 1.5

# SMA 設定 (鎖定窗格)
SMA_WINDOWS        = [5, 10, 20, 60, 120, 240]
AVG_VOL_WINDOWS    = [60, 120, 240]
COMPUTE_YTD        = True

# 並發
ENABLE_THREADPOOL  = True
MAX_RETRIES        = 3
RETRY_DELAY        = 2

# 輸出格式 (透過 OutputManager)
OUTPUT_PARQUET     = True   # 必選
OUTPUT_DUCKDB      = True
OUTPUT_CSV         = True
OUTPUT_JSON        = False  # 大檔, 預設關
OUTPUT_GSHEET      = False

CSV_ENCODING       = "utf-8-sig"
DUCKDB_FILENAME    = "VDF_MDL004_TWFullMarket.duckdb"
ENABLE_BACKUP      = True
MAX_BACKUP_FILES   = 5
LOG_LEVEL          = "INFO"


# =====================================================================================
# 📦 Imports
# =====================================================================================

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
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
# 批716 自糾:第一版直接把 AegisNexus 掛進來當網路出口 —— 方向對,**門走錯了**。
# 本樹 VDF 的網路出口是**統包工具**(SUP_MDL740,經 via_net_unified_v* 轉接),
# 它身上才有雙閘(VIA_NET_CONSENT / VIA_SCRAPE_TOKEN)、才有 AegisNexus 後端 + stdlib 退路。
# 繞過它直接接 AegisNexus,等於在 VDF 開了第二個網路出口 —— 批115 全導入令的正向尺當場紅。
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import os, sys, re, json, time, warnings
import pathlib
from datetime import datetime, timedelta, date
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

# Import OutputManager (renumbered MDL101)
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
    from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, MofNCompleteColumn
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


def _ytd_start() -> datetime:
    return datetime(datetime.now().year, 1, 1)


def _is_valid_tw_code(code: str) -> bool:
    """SSOT TW_TICKER_REGEX 驗證 (LOCKED)."""
    if not code: return False
    return bool(re.match(r'^' + TW_TICKER_REGEX + r'$', str(code).strip()))


def _to_yf_ticker(code: str, market: str) -> str:
    """code + market → yfinance ticker (SSOT: 1234.TW 或 1234.TWO)."""
    code = str(code).strip()
    if market == "TWSE": return f"{code}.TW"
    if market == "TPEX": return f"{code}.TWO"
    return code


def _safe_num(v: Any) -> Optional[float]:
    """安全 float 轉換, 失敗回 None."""
    if v is None: return None
    if isinstance(v, str):
        v = v.replace(",", "").strip()
        if v in ("", "-", "--", "N/A", "null"): return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _safe_int(v: Any) -> Optional[int]:
    f = _safe_num(v)
    return int(f) if f is not None else None


def _progress(total: int, label: str, every: float = 5.0):
    """批719:操作員實錄「**現在不知道是卡斷還在運作**」。

    用批694 立的那一條約定:印 `[進度] n/N` —— PowerShell 那端的動態進度條
    認這個字樣畫真百分比;沒報進度的就只能脈動,而**脈動跟卡死長得一模一樣**。
    節流 every 秒印一次,並附已跑秒數與估剩秒數:看的人要判斷得出「還在動」。
    """
    st = {"n": 0, "last": time.time(), "t0": time.time()}

    def cb(step: int = 1):
        st["n"] += step
        now = time.time()
        if st["n"] >= total or now - st["last"] >= every:
            st["last"] = now
            done, el = st["n"], now - st["t0"]
            eta = (el / max(done, 1)) * max(total - done, 0)
            print(f"  [進度] {done}/{total} · {done * 100.0 / max(total, 1):.1f}%"
                  f" · 已 {el:.0f}s · 估剩 {eta:.0f}s · {label}", flush=True)

    return cb


def net_consent() -> bool:
    """閘況**問統包工具**(它那邊才是雙閘的正主);問不到才退回只讀環境變數。

    **AI 永不代設** —— 本支只讀,一行都不寫。
    """
    nt = _via_net()
    if nt is not None and hasattr(nt, "gate_state"):
        try:
            return bool((nt.gate_state() or {}).get("open"))
        except Exception:
            pass
    return str(os.environ.get("VIA_NET_CONSENT", "")).strip().upper() in ("YES", "1", "TRUE")


def _net_json(url: str, retries: int = HTTP_RETRIES):
    """走**統包網路工具**取 JSON(批115 全導入令 · L20 後端是 AegisNexus)。

    回 (態, 資料)。態:OK / GATED(雙閘未開)/ ABSENT(工具缺席)/ FAIL:…
    **本支不自己開第二個網路出口** —— 統包缺席就誠實 ABSENT,不偷偷落回直連。
    """
    nt = _via_net()
    if nt is None or not hasattr(nt, "http_json"):
        return "ABSENT", None
    try:
        r = nt.http_json(url, timeout=HTTP_TIMEOUT) or {}
    except Exception as exc:
        return f"FAIL:{type(exc).__name__}", None
    st = str(r.get("state") or "")
    if st == "OK":
        return "OK", r.get("data")
    if st == "DENY":
        return "GATED", None
    return f"FAIL:{(r.get('note') or st)[:60]}", None


def _http_get(url: str, retries: int = HTTP_RETRIES):
    """**保留簽章**(只增不減:上游呼叫端一個字不用改),但內部改走 AegisNexus。

    回一個最小的 response-like 物件(帶 `.json()` / `.text` / `.status_code`),
    讓原本 `r.json()` 的呼叫端照舊跑得動;拿不到就回 None,與上游語意一致。
    """
    state, data = _net_json(url, retries)
    if state != "OK" or data is None:
        _log("WARN" if state != "GATED" else "INFO",
             f"網路未取得({state}):{url[:72]}"
             + ("  ← 同意閘未開,這**不是壞掉**;要開請由操作員設 VIA_NET_CONSENT"
                if state == "GATED" else ""))
        return None

    class _Resp:                                    # 只做相容,不做第二套 HTTP
        status_code = 200

        def __init__(self, payload):
            self._p = payload

        def json(self):
            return self._p

        @property
        def text(self):
            return json.dumps(self._p, ensure_ascii=False)

        def raise_for_status(self):
            return None

    return _Resp(data)


def _log(level: str, msg: str):
    if not RICH_AVAILABLE:
        print(f"[{level}] {msg}"); return
    colors = {"INFO": "cyan", "OK": "green", "WARN": "yellow", "ERR": "red", "DBG": "dim"}
    c = colors.get(level, "white")
    console.print(f"[{c}][{level}][/{c}] {msg}")


# =====================================================================================
# 🌐 [Fetcher 1] TWSE Full-Market Daily Quote
# =====================================================================================

class TWSEFullMarketFetcher:
    """
    TWSE STOCK_DAY_ALL — 一次抓全上市 ~1000 檔當日交易資料.
    Returns DataFrame with columns:
      code, name, market, open, high, low, close, change,
      volume(股), turnover(元), transactions
    """
    VERSION = "2.0.0"

    def __init__(self):
        self.stats = {"rows_raw": 0, "rows_valid": 0, "errors": []}

    def fetch(self) -> "pd.DataFrame":
        r = _http_get(TWSE_DAILY_ALL_URL)
        if r is None:
            self.stats["errors"].append("TWSE STOCK_DAY_ALL HTTP fail")
            return pd.DataFrame()
        try:
            data = r.json()
        except Exception as e:
            self.stats["errors"].append(f"TWSE JSON parse: {str(e)[:80]}")
            return pd.DataFrame()
        if not data:
            return pd.DataFrame()
        rows = []
        for d in data:
            code = (d.get("Code") or d.get("證券代號") or "").strip()
            if not _is_valid_tw_code(code):   # SSOT regex filter
                continue
            rows.append({
                "code":         code,
                "name":         (d.get("Name") or d.get("證券名稱") or "").strip(),
                "market":       "TWSE",
                "open":         _safe_num(d.get("OpeningPrice") or d.get("開盤價")),
                "high":         _safe_num(d.get("HighestPrice") or d.get("最高價")),
                "low":          _safe_num(d.get("LowestPrice")  or d.get("最低價")),
                "close":        _safe_num(d.get("ClosingPrice") or d.get("收盤價")),
                "change":       _safe_num(d.get("Change") or d.get("漲跌價差")),
                "volume":       _safe_int(d.get("TradeVolume") or d.get("成交股數")),
                "turnover":     _safe_num(d.get("TradeValue")  or d.get("成交金額")),
                "transactions": _safe_int(d.get("Transaction") or d.get("成交筆數")),
            })
        self.stats["rows_raw"]   = len(data)
        self.stats["rows_valid"] = len(rows)
        return pd.DataFrame(rows)


# =====================================================================================
# 🌐 [Fetcher 2] TPEX Full-Market Daily Quote
# =====================================================================================

class TPEXFullMarketFetcher:
    """
    TPEX daily_close_quotes — 一次抓全上櫃 ~900 檔當日交易資料.
    Returns DataFrame with same schema as TWSE.
    """
    VERSION = "2.0.0"

    def __init__(self):
        self.stats = {"rows_raw": 0, "rows_valid": 0, "errors": []}

    def fetch(self) -> "pd.DataFrame":
        r = _http_get(TPEX_DAILY_CLOSE_URL)
        if r is None:
            self.stats["errors"].append("TPEX HTTP fail")
            return pd.DataFrame()
        try:
            data = r.json()
        except Exception as e:
            self.stats["errors"].append(f"TPEX JSON parse: {str(e)[:80]}")
            return pd.DataFrame()
        if not data:
            return pd.DataFrame()
        rows = []
        for d in data:
            # TPEX 欄位名與 TWSE 略有差異
            code = (d.get("SecuritiesCompanyCode") or
                    d.get("Code") or d.get("證券代號") or "").strip()
            if not _is_valid_tw_code(code):
                continue
            rows.append({
                "code":         code,
                "name":         (d.get("CompanyName") or d.get("SecuritiesName")
                                  or d.get("證券名稱") or "").strip(),
                "market":       "TPEX",
                "open":         _safe_num(d.get("Open") or d.get("OpeningPrice") or d.get("開盤")),
                "high":         _safe_num(d.get("High") or d.get("HighestPrice") or d.get("最高")),
                "low":          _safe_num(d.get("Low")  or d.get("LowestPrice")  or d.get("最低")),
                "close":        _safe_num(d.get("Close") or d.get("LastestTradedPrice")
                                          or d.get("ClosingPrice") or d.get("收盤")),
                "change":       _safe_num(d.get("Change") or d.get("漲跌")),
                "volume":       _safe_int(d.get("TradingShares") or d.get("成交股數")),
                "turnover":     _safe_num(d.get("TradingAmount") or d.get("成交金額")),
                "transactions": _safe_int(d.get("Transaction") or d.get("成交筆數")),
            })
        self.stats["rows_raw"]   = len(data)
        self.stats["rows_valid"] = len(rows)
        return pd.DataFrame(rows)


# =====================================================================================
# 📈 [Fetcher 3] YFinance Bulk History (for SMA + Avg Vol)
# =====================================================================================

class YFHistoryBulkFetcher:
    """
    批次抓 1y daily history (足夠算 240-day SMA).
    用 yfinance.download (bulk mode) 一次 50 檔, 大幅減少 API call.

    Returns dict {yf_ticker: DataFrame[Date, Open, High, Low, Close, Adj Close, Volume]}
    """
    VERSION = "2.0.0"

    def __init__(self):
        self.stats = {
            "tickers_total":  0,
            "tickers_ok":     0,
            "tickers_fail":   0,
            "batches":        0,
            "errors":         [],
        }

    def _fetch_batch(self, batch: List[str]) -> Dict[str, "pd.DataFrame"]:
        """一個 batch (50 檔) 的 bulk download."""
        results: Dict[str, pd.DataFrame] = {}
        if not YFINANCE_AVAILABLE or not batch:
            return results
        try:
            tickers_str = " ".join(batch)
            df = yf.download(tickers_str, period=YF_HISTORY_PERIOD,
                             interval=YF_HISTORY_INTERVAL, progress=False,
                             threads=False, timeout=YF_TIMEOUT)
            if df is None or df.empty:
                return results
            # yf 多 ticker 結果是 MultiIndex columns
            if isinstance(df.columns, pd.MultiIndex):
                for t in batch:
                    try:
                        # df[('Close', t)] 等
                        cols = {c[0] for c in df.columns if c[1] == t}
                        if not cols: continue
                        d = pd.DataFrame()
                        for col in ["Open","High","Low","Close","Adj Close","Volume"]:
                            if col in cols:
                                d[col] = df[(col, t)]
                        d = d.dropna(how="all")
                        if not d.empty:
                            d.index.name = "date"
                            results[t] = d.reset_index()
                    except Exception:
                        pass
            else:
                # 單一 ticker 結果
                if len(batch) == 1:
                    d = df.copy()
                    d.index.name = "date"
                    results[batch[0]] = d.reset_index()
        except Exception as e:
            self.stats["errors"].append(f"batch[{len(batch)}]: {str(e)[:80]}")
        return results

    def fetch(self, yf_tickers: List[str],
              progress_cb=None) -> Dict[str, "pd.DataFrame"]:
        """抓全清單, 拆 batch 並發."""
        self.stats["tickers_total"] = len(yf_tickers)
        results: Dict[str, pd.DataFrame] = {}
        # 切 batch
        batches = [yf_tickers[i:i + YF_BULK_BATCH_SIZE]
                   for i in range(0, len(yf_tickers), YF_BULK_BATCH_SIZE)]
        self.stats["batches"] = len(batches)
        if ENABLE_THREADPOOL and len(batches) > 1:
            with ThreadPoolExecutor(max_workers=YF_BULK_WORKERS) as pool:
                futs = {pool.submit(self._fetch_batch, b): i
                        for i, b in enumerate(batches)}
                for done in as_completed(futs):
                    try:
                        res = done.result()
                        results.update(res)
                    except Exception as e:
                        self.stats["errors"].append(f"future: {str(e)[:60]}")
                    if progress_cb: progress_cb()
        else:
            for b in batches:
                res = self._fetch_batch(b)
                results.update(res)
                if progress_cb: progress_cb()
        self.stats["tickers_ok"]   = len(results)
        self.stats["tickers_fail"] = self.stats["tickers_total"] - self.stats["tickers_ok"]
        return results


# =====================================================================================
# 💼 [Fetcher 4] YFinance Consensus (analyst targets)
# =====================================================================================

class YFConsensusFetcher:
    """
    用 yfinance.Ticker.info 抓每檔 analyst targets, 並發.
    每檔約 0.3-0.8s, 用 8 worker 並發.

    Returns dict {yf_ticker: {target_mean, target_median, target_high, target_low,
                              num_analysts, recommendation, sharesOutstanding, marketCap}}
    """
    VERSION = "2.0.0"

    def __init__(self):
        self.stats = {"ok": 0, "fail": 0, "errors": []}

    def _fetch_one(self, yf_ticker: str) -> Dict:
        out = {
            "yf_ticker":          yf_ticker,
            "target_mean":        None, "target_median":     None,
            "target_high":        None, "target_low":        None,
            "num_analysts":       None, "recommendation":    None,
            "shares_outstanding": None, "market_cap":        None,
            "trailing_eps":       None, "forward_eps":       None,
            "trailing_pe":        None, "forward_pe":        None,
            "book_value":         None, "price_to_book":     None,
            "dividend_rate":      None, "dividend_yield":    None,
            "_error":             None,
        }
        if not YFINANCE_AVAILABLE:
            out["_error"] = "yfinance not installed"
            return out
        for attempt in range(YF_RETRY_ATTEMPTS):
            try:
                tk = yf.Ticker(yf_ticker)
                info = tk.info or {}
                out["target_mean"]        = _safe_num(info.get("targetMeanPrice"))
                out["target_median"]      = _safe_num(info.get("targetMedianPrice"))
                out["target_high"]        = _safe_num(info.get("targetHighPrice"))
                out["target_low"]         = _safe_num(info.get("targetLowPrice"))
                out["num_analysts"]       = _safe_int(info.get("numberOfAnalystOpinions"))
                out["recommendation"]     = info.get("recommendationKey")
                out["shares_outstanding"] = _safe_num(info.get("sharesOutstanding"))
                out["market_cap"]         = _safe_num(info.get("marketCap"))
                out["trailing_eps"]       = _safe_num(info.get("trailingEps"))
                out["forward_eps"]        = _safe_num(info.get("forwardEps"))
                out["trailing_pe"]        = _safe_num(info.get("trailingPE"))
                out["forward_pe"]         = _safe_num(info.get("forwardPE"))
                out["book_value"]         = _safe_num(info.get("bookValue"))
                out["price_to_book"]      = _safe_num(info.get("priceToBook"))
                out["dividend_rate"]      = _safe_num(info.get("dividendRate"))
                out["dividend_yield"]     = _safe_num(info.get("dividendYield"))
                self.stats["ok"] += 1
                return out
            except Exception as e:
                if attempt < YF_RETRY_ATTEMPTS - 1:
                    time.sleep(YF_RETRY_DELAY)
                else:
                    out["_error"] = str(e)[:80]
                    self.stats["fail"] += 1
                    self.stats["errors"].append(f"{yf_ticker}: {str(e)[:60]}")
        return out

    def _fetch_via_net(self, yf_tickers, progress_cb=None):
        """**先走統包的 quoteSummary raw 道**(SUP_MDL740;cookie+crumb 標準握手)。

        批719 實錄:工作站 Step 3 撞 `HTTP 401 Invalid Crumb` —— 裸 yfinance 沒做
        Yahoo 那套 cookie+crumb 握手就會這樣。統包身上**早就有**這道握手
        (批137/批155),所以這裡只接線不重寫(LL404)。取不到就回 None,
        讓呼叫端誠實落回原路徑**並講明為什麼**。
        """
        nt = _via_net()
        if nt is None or not hasattr(nt, "yahoo_quote_summary_raw"):
            return None
        out = {}
        CH = 40
        for i in range(0, len(yf_tickers), CH):
            chunk = yf_tickers[i:i + CH]
            try:
                r = nt.yahoo_quote_summary_raw(chunk, "financialData") or {}
            except Exception as exc:
                _log("WARN", f"統包 quoteSummary 道例外:{type(exc).__name__}")
                return None
            if str(r.get("state")) == "DENY":
                _log("INFO", "雙閘未開 —— 共識這一步 GATED,**不是壞掉**")
                return None
            for sym, res in (r.get("results") or {}).items():
                fd = (res or {}).get("financialData") or {}

                def _raw(k, _fd=fd):
                    v = _fd.get(k)
                    return v.get("raw") if isinstance(v, dict) else v

                out[sym] = {"yf_ticker": sym,
                            "target_mean_price": _safe_num(_raw("targetMeanPrice")),
                            "target_median_price": _safe_num(_raw("targetMedianPrice")),
                            "target_high_price": _safe_num(_raw("targetHighPrice")),
                            "target_low_price": _safe_num(_raw("targetLowPrice")),
                            "number_of_analysts": _safe_int(_raw("numberOfAnalystOpinions")),
                            "recommendation_mean": _safe_num(_raw("recommendationMean")),
                            "_via": "SUP_MDL740.quoteSummary"}
            for _ in chunk:
                if progress_cb:
                    progress_cb()
        return out or None

    def fetch(self, yf_tickers: List[str],
              progress_cb=None) -> Dict[str, Dict]:
        via = self._fetch_via_net(yf_tickers, progress_cb)
        if via is not None:
            _log("OK", f"共識走統包 quoteSummary 道:{len(via)}/{len(yf_tickers)}")
            return via
        _log("WARN", "統包道取不到 —— 落回裸 yfinance(**可能撞 401 Invalid Crumb**;"
                     "那不是本引擎壞了,是 Yahoo 要 cookie+crumb 握手)")
        results: Dict[str, Dict] = {}
        if ENABLE_THREADPOOL and len(yf_tickers) > 1:
            with ThreadPoolExecutor(max_workers=YF_INFO_WORKERS) as pool:
                futs = {pool.submit(self._fetch_one, t): t for t in yf_tickers}
                for done in as_completed(futs):
                    t = futs[done]
                    try:
                        results[t] = done.result()
                    except Exception as e:
                        results[t] = {"yf_ticker": t, "_error": str(e)[:60]}
                        self.stats["fail"] += 1
                    if progress_cb: progress_cb()
        else:
            for t in yf_tickers:
                results[t] = self._fetch_one(t)
                if progress_cb: progress_cb()
        return results


# =====================================================================================
# 💎 [Fetcher 5] FactSet Consensus (STUB)
# =====================================================================================

class FactSetConsensusFetcher:
    """
    FactSet API stub. 需 commercial API key, 此版本回 NaN.
    保留 schema 欄位以利 MDL005/006 之 consensus 對賬.
    """
    VERSION = "2.0.0-stub"

    def __init__(self):
        self.stats = {"ok": 0, "fail": 0, "is_stub": True}

    def fetch(self, tickers: List[str]) -> Dict[str, Dict]:
        results = {}
        for t in tickers:
            results[t] = {
                "code":            t,
                "fs_target_mean":  None,
                "fs_target_median":None,
                "fs_target_high":  None,
                "fs_target_low":   None,
                "fs_num_analysts": None,
                "fs_eps_2026":     None,
                "fs_eps_2027":     None,
                "_source":         "FACTSET_STUB",
            }
        self.stats["ok"] = len(tickers)
        return results


# =====================================================================================
# 📊 [Calculator] SMA · AvgVolume · MarketCap · YTD
# =====================================================================================

class SMAVolMcapCalculator:
    """
    從 1y daily history 算:
      - SMA 5/10/20/60/120/240 (Adj Close 為主, Close fallback)
      - AvgVolume 60/120/240
      - YTD return %  (today_close / 年初_close - 1) * 100
      - market_cap = current_close × shares_outstanding (from consensus)
    """
    VERSION = "2.0.0"

    @staticmethod
    def _price_series(df: "pd.DataFrame") -> Optional["pd.Series"]:
        """優先 Adj Close, fallback Close."""
        if df is None or df.empty: return None
        for col in ["Adj Close", "adj_close", "Close", "close"]:
            if col in df.columns:
                s = df[col].dropna()
                if not s.empty:
                    return s
        return None

    @staticmethod
    def _vol_series(df: "pd.DataFrame") -> Optional["pd.Series"]:
        if df is None or df.empty: return None
        for col in ["Volume", "volume"]:
            if col in df.columns:
                s = df[col].dropna()
                if not s.empty:
                    return s
        return None

    @classmethod
    def calc_one(cls, yf_ticker: str, hist_df: "pd.DataFrame",
                 shares_outstanding: Optional[float] = None) -> Dict:
        """單檔計算 ALL 指標."""
        out: Dict[str, Any] = {"yf_ticker": yf_ticker}

        if hist_df is None or hist_df.empty:
            # 全部填 None
            for w in SMA_WINDOWS: out[f"sma_{w}"] = None
            for w in AVG_VOL_WINDOWS: out[f"avg_vol_{w}"] = None
            out["ytd_pct"]      = None
            out["adj_close"]    = None
            out["volume"]       = None
            out["market_cap"]   = None
            return out

        # ensure sorted by date
        if "date" in hist_df.columns:
            hist_df = hist_df.sort_values("date").reset_index(drop=True)
        elif "Date" in hist_df.columns:
            hist_df = hist_df.sort_values("Date").reset_index(drop=True)

        price = cls._price_series(hist_df)
        vol   = cls._vol_series(hist_df)

        # SMA
        for w in SMA_WINDOWS:
            if price is not None and len(price) >= w:
                out[f"sma_{w}"] = float(price.iloc[-w:].mean())
            else:
                out[f"sma_{w}"] = None

        # AvgVolume
        for w in AVG_VOL_WINDOWS:
            if vol is not None and len(vol) >= w:
                out[f"avg_vol_{w}"] = float(vol.iloc[-w:].mean())
            else:
                out[f"avg_vol_{w}"] = None

        # YTD return
        if COMPUTE_YTD and price is not None and not price.empty:
            try:
                ytd_start = _ytd_start()
                # 找最接近 ytd_start 的第一筆
                date_col = "date" if "date" in hist_df.columns else ("Date" if "Date" in hist_df.columns else None)
                if date_col:
                    dt_series = pd.to_datetime(hist_df[date_col], errors='coerce')
                    mask = dt_series >= ytd_start
                    if mask.any():
                        ytd_first_idx = mask.idxmax()
                        first_price = price.iloc[ytd_first_idx] if ytd_first_idx < len(price) else None
                        last_price  = price.iloc[-1]
                        if first_price and first_price > 0:
                            out["ytd_pct"] = (last_price / first_price - 1) * 100
                        else:
                            out["ytd_pct"] = None
                    else:
                        out["ytd_pct"] = None
                else:
                    out["ytd_pct"] = None
            except Exception:
                out["ytd_pct"] = None
        else:
            out["ytd_pct"] = None

        # latest
        out["adj_close"] = float(price.iloc[-1]) if price is not None and not price.empty else None
        out["volume"]    = int(vol.iloc[-1])    if vol   is not None and not vol.empty   else None

        # Market Cap = price × shares_outstanding
        if out["adj_close"] and shares_outstanding:
            out["market_cap"] = out["adj_close"] * shares_outstanding
        else:
            out["market_cap"] = None

        return out

    @classmethod
    def calc_batch(cls, hist_by_ticker: Dict[str, "pd.DataFrame"],
                   consensus_by_ticker: Dict[str, Dict]) -> "pd.DataFrame":
        """全部 tickers 批次算."""
        rows = []
        for yf_t, df in hist_by_ticker.items():
            cons = consensus_by_ticker.get(yf_t, {})
            shares = cons.get("shares_outstanding")
            row = cls.calc_one(yf_t, df, shares_outstanding=shares)
            rows.append(row)
        return pd.DataFrame(rows)


# =====================================================================================
# 🎯 [Engine] TWFullMarketEngine 主類
# =====================================================================================

class TWFullMarketEngine:
    """
    Pipeline (5 step):
      1. Load universe (from MDL001 verify parquet OR fresh fetch)
      2. Daily quote (TWSE + TPEX one-shot)
      3. YF bulk history (for SMA + AvgVol)
      4. YF consensus (analyst targets)
      5. SMA/AvgVol/MarketCap calc + merge + output
    """
    VERSION = "2.0.0"

    def __init__(self):
        self.start_time   = time.time()
        # CLI args parse
        self.max_n              = None
        self.no_consensus       = "--no-consensus" in sys.argv
        self.no_history         = "--no-history" in sys.argv
        for i, a in enumerate(sys.argv):
            if a == "--max" and i+1 < len(sys.argv):
                try: self.max_n = int(sys.argv[i+1])
                except: pass
            if a == "--universe-source" and i+1 < len(sys.argv):
                global UNIVERSE_SOURCE
                UNIVERSE_SOURCE = sys.argv[i+1]

        # Fetchers
        self.twse_fetcher = TWSEFullMarketFetcher()
        self.tpex_fetcher = TPEXFullMarketFetcher()
        self.yf_history   = YFHistoryBulkFetcher()
        self.yf_consensus = YFConsensusFetcher()
        self.fs_consensus = FactSetConsensusFetcher()

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

        # State
        self.df_quote         = None    # combined TWSE+TPEX daily
        self.df_history_meta  = None    # how many days per ticker
        self.df_consensus     = None    # YF analyst targets
        self.df_factset       = None    # stub
        self.df_calc          = None    # SMA/AvgVol/MCap calc
        self.df_final         = None    # merged final output
        self.save_results     = {}

    def show_header(self):
        info = f"""
🎯 VDF MDL004 · TW Full Market Engine v{self.VERSION}

🔒 SSOT Regex      : {TW_TICKER_REGEX}
📁 Output dir      : {Path(BASE_DIR) / OUTPUT_DIR}
🎛️  Max tickers    : {self.max_n or '全市場 ~1,900'}
🌐 YF bulk batch   : {YF_BULK_BATCH_SIZE} 檔/批 · {YF_BULK_WORKERS} workers
💼 YF consensus    : {'⏭️ skip' if self.no_consensus else f'{YF_INFO_WORKERS} workers'}
📊 Compute history : {'⏭️ skip (no SMA/AvgVol)' if self.no_history else f'✅ SMA {SMA_WINDOWS} · AvgVol {AVG_VOL_WINDOWS}'}
💾 Output formats  : Parquet={OUTPUT_PARQUET} · DuckDB={OUTPUT_DUCKDB} · CSV={OUTPUT_CSV} · JSON={OUTPUT_JSON}
"""
        if RICH_AVAILABLE:
            console.print(Panel(info.strip(),
                          title="[bold blue]🇹🇼 VDF MDL004 · TW Full Market[/bold blue]",
                          border_style="blue"))
        else:
            print(info)

    def _load_universe(self) -> "pd.DataFrame":
        """從 MDL001 verify parquet 或 fresh fetch."""
        uni_path = Path(BASE_DIR) / UNIVERSE_SOURCE / UNIVERSE_FILE
        if USE_LOCAL_UNIVERSE and uni_path.exists():
            try:
                df = pd.read_parquet(uni_path)
                _log("OK", f"Universe loaded from MDL001 verify: {len(df)} 檔 from {uni_path.name}")
                # 標準化欄位
                if "code" not in df.columns:
                    raise ValueError("universe parquet missing 'code'")
                if "market" not in df.columns:
                    df["market"] = "TWSE"  # default
                return df[["code", "name", "market"]] if "name" in df.columns else df[["code", "market"]].assign(name="")
            except Exception as e:
                _log("WARN", f"Universe parquet load fail: {e}, falling back to OpenAPI")
        return pd.DataFrame()  # will trigger fresh fetch in step 1

    def run(self) -> int:
        try:
            self.show_header()

            # ─── Step 1: Daily Quote (一次抓全市場) ───
            _log("INFO", "Step 1/5: Daily quote from TWSE + TPEX OpenAPI")
            df_twse = self.twse_fetcher.fetch()
            df_tpex = self.tpex_fetcher.fetch()
            self.df_quote = pd.concat([df_twse, df_tpex], ignore_index=True)
            _log("OK", f"TWSE={len(df_twse)} · TPEX={len(df_tpex)} · Total={len(self.df_quote)}")

            if self.df_quote.empty:
                _log("ERR", "No quote data, abort. Trying universe parquet fallback...")
                df_uni = self._load_universe()
                if df_uni.empty:
                    _log("ERR", "No universe available either, abort")
                    return 1
                # Create empty quote with universe only
                self.df_quote = df_uni.copy()
                for col in ["open","high","low","close","change","volume","turnover","transactions"]:
                    self.df_quote[col] = None

            # 限制 max_n (for testing)
            if self.max_n:
                self.df_quote = self.df_quote.head(self.max_n)
                _log("WARN", f"--max {self.max_n} applied, processing {len(self.df_quote)} only")

            # 加 yf_ticker
            self.df_quote["yf_ticker"] = self.df_quote.apply(
                lambda r: _to_yf_ticker(r["code"], r["market"]), axis=1)

            yf_tickers = self.df_quote["yf_ticker"].tolist()

            # ─── Step 2: YF bulk history (for SMA + AvgVol) ───
            hist_by_ticker = {}
            if not self.no_history:
                _log("INFO", f"Step 2/5: YF bulk history fetch ({len(yf_tickers)} tickers, "
                     f"period={YF_HISTORY_PERIOD}, batch={YF_BULK_BATCH_SIZE})")
                t0 = time.time()
                hist_by_ticker = self.yf_history.fetch(
                    yf_tickers, progress_cb=_progress(len(yf_tickers), "YF 歷史"))
                _log("OK", f"YF history: {self.yf_history.stats['tickers_ok']}/"
                     f"{self.yf_history.stats['tickers_total']} OK · "
                     f"{self.yf_history.stats['batches']} batches · "
                     f"{round(time.time()-t0, 1)}s")
            else:
                _log("WARN", "Step 2/5: --no-history specified, SMA/AvgVol will be NaN")

            # ─── Step 3: YF consensus ───
            consensus_by_ticker = {}
            if not self.no_consensus:
                _log("INFO", f"Step 3/5: YF consensus (info.targetMeanPrice etc, "
                     f"{YF_INFO_WORKERS} workers)")
                t0 = time.time()
                consensus_by_ticker = self.yf_consensus.fetch(
                    yf_tickers, progress_cb=_progress(len(yf_tickers), "YF 共識"))
                _log("OK", f"YF consensus: {self.yf_consensus.stats['ok']}/"
                     f"{self.yf_consensus.stats['ok']+self.yf_consensus.stats['fail']} OK · "
                     f"{round(time.time()-t0, 1)}s")
            else:
                _log("WARN", "Step 3/5: --no-consensus specified, target prices = NaN")

            # ─── Step 4: FactSet stub ───
            _log("INFO", "Step 4/5: FactSet consensus (STUB)")
            fs_data = self.fs_consensus.fetch([t for t in self.df_quote["code"]])
            self.df_factset = pd.DataFrame(list(fs_data.values()))

            # ─── Step 5: SMA + AvgVol + MarketCap calc ───
            _log("INFO", "Step 5/5: Calculate SMA / AvgVol / MarketCap / YTD")
            self.df_calc = SMAVolMcapCalculator.calc_batch(hist_by_ticker, consensus_by_ticker)

            # YF Consensus 轉 DataFrame
            cons_rows = list(consensus_by_ticker.values()) if consensus_by_ticker else \
                        [{"yf_ticker": t} for t in yf_tickers]
            self.df_consensus = pd.DataFrame(cons_rows)

            # ─── Merge all into final ───
            _log("INFO", "Merging quote + consensus + calc into final DataFrame")
            df = self.df_quote.copy()
            # Merge consensus (on yf_ticker)
            if not self.df_consensus.empty:
                df = df.merge(self.df_consensus, on="yf_ticker", how="left",
                              suffixes=("", "_cons"))
            # Merge calc (SMA/AvgVol/MCap on yf_ticker)
            if not self.df_calc.empty:
                # 注意: calc 也有 adj_close/volume, 用 _calc 後綴, 否則衝突
                calc_cols = [c for c in self.df_calc.columns if c != "yf_ticker"]
                df = df.merge(self.df_calc[["yf_ticker"] + calc_cols], on="yf_ticker",
                              how="left", suffixes=("", "_calc"))
            # Merge FactSet stub (on code)
            if not self.df_factset.empty and "code" in self.df_factset.columns:
                df = df.merge(self.df_factset, on="code", how="left", suffixes=("", "_fs"))

            self.df_final = df
            _log("OK", f"Final DataFrame: {len(df)} rows × {len(df.columns)} cols")

            # ─── Save outputs ───
            if self.output_mgr:
                _log("INFO", "Saving multi-format outputs")
                self.save_results["tw_fullmarket_snapshot"] = \
                    self.output_mgr.save("tw_fullmarket_snapshot", self.df_final)
                # 也存 raw quote, history meta, consensus 等 sub-tables
                if not self.df_quote.empty:
                    self.save_results["raw_quote"] = \
                        self.output_mgr.save("raw_quote", self.df_quote)
                if not self.df_consensus.empty:
                    self.save_results["yf_consensus"] = \
                        self.output_mgr.save("yf_consensus", self.df_consensus)
                if not self.df_calc.empty:
                    self.save_results["sma_avgvol_mcap"] = \
                        self.output_mgr.save("sma_avgvol_mcap", self.df_calc)
            else:
                _log("WARN", "OutputManager not available, results in memory only")

            # ─── Rich Summary ───
            self._print_rich_summary()
            elapsed = round(time.time() - self.start_time, 2)
            _log("OK", f"完成 · 總耗時 {elapsed}s")
            return 0

        except KeyboardInterrupt:
            _log("WARN", "Interrupted by user")
            return 1
        except Exception as e:
            _log("ERR", f"{e}")
            if LOG_LEVEL == "DEBUG":
                import traceback; traceback.print_exc()
            return 1

    # ─────────────────────────────────────────────────────────────
    # Rich Summary
    # ─────────────────────────────────────────────────────────────
    def _print_rich_summary(self):
        if not RICH_AVAILABLE: return self._plain_summary()
        elapsed = round(time.time() - self.start_time, 2)
        console.rule("[bold cyan]🎯 VDF MDL004 · TW Full Market · Summary Matrix[/bold cyan]")

        # Table 1: Pipeline 各步驟
        t = Table(title="🚀 [bold]1. Pipeline Steps[/bold]",
                  box=box.ROUNDED, header_style="bold magenta")
        t.add_column("Step", style="cyan", width=24)
        t.add_column("Source", style="yellow", width=16)
        t.add_column("Result", style="green", width=14, justify="right")
        t.add_column("Status", style="green", width=10, justify="center")
        t.add_row("1 · Daily Quote", "TWSE+TPEX",
                  f"{len(self.df_quote) if self.df_quote is not None else 0:,} 檔",
                  "✅" if self.df_quote is not None and not self.df_quote.empty else "❌")
        t.add_row("2 · YF History",  "yfinance bulk",
                  f"{self.yf_history.stats['tickers_ok']:,} OK"
                  if not self.no_history else "⏭️ skipped",
                  "✅" if (not self.no_history and self.yf_history.stats['tickers_ok'] > 0) else "⏭️")
        t.add_row("3 · YF Consensus","yfinance info",
                  f"{self.yf_consensus.stats['ok']:,} OK"
                  if not self.no_consensus else "⏭️ skipped",
                  "✅" if (not self.no_consensus and self.yf_consensus.stats['ok'] > 0) else "⏭️")
        t.add_row("4 · FactSet stub","stub",
                  f"{self.fs_consensus.stats['ok']:,} stub",
                  "⏭️")
        t.add_row("5 · Calc SMA/Vol/MCap","internal",
                  f"{len(self.df_calc) if self.df_calc is not None else 0:,} 行",
                  "✅" if self.df_calc is not None and not self.df_calc.empty else "❌")
        console.print(t)

        # Table 2: Final DataFrame schema
        if self.df_final is not None and not self.df_final.empty:
            t = Table(title=f"📋 [bold]2. Final Schema ({len(self.df_final.columns)} cols)[/bold]",
                      box=box.ROUNDED, header_style="bold magenta")
            t.add_column("Group",   style="cyan", width=14)
            t.add_column("Columns", style="yellow", width=72)
            groups = {
                "Identity":  ["ticker", "code", "yf_ticker", "name", "market"],
                "Daily":     ["open","high","low","close","change","volume","turnover","transactions","adj_close"],
                "SMA":       [f"sma_{w}" for w in SMA_WINDOWS] + ["ytd_pct"],
                "AvgVol":    [f"avg_vol_{w}" for w in AVG_VOL_WINDOWS],
                "MarketCap": ["market_cap","shares_outstanding"],
                "YF Cons":   ["target_mean","target_median","target_high","target_low",
                              "num_analysts","recommendation","trailing_pe","forward_pe",
                              "dividend_rate","dividend_yield"],
                "FactSet":   ["fs_target_mean","fs_target_median","fs_num_analysts"],
            }
            for grp, cols in groups.items():
                present = [c for c in cols if c in self.df_final.columns]
                if present:
                    t.add_row(grp, ", ".join(present)[:70])
            console.print(t)

        # Table 3: Sample data (top 8)
        if self.df_final is not None and not self.df_final.empty:
            top = self.df_final.head(8)
            t = Table(title=f"📊 [bold]3. Sample Snapshot (top {len(top)})[/bold]",
                      box=box.ROUNDED, header_style="bold magenta")
            t.add_column("Code",    style="cyan", width=8)
            t.add_column("Name",    style="yellow", width=14)
            t.add_column("Mkt",     style="green", width=6)
            t.add_column("Close",   style="green", width=10, justify="right")
            t.add_column("Volume",  style="green", width=12, justify="right")
            t.add_column("MCap",    style="green", width=12, justify="right")
            t.add_column("SMA20",   style="yellow", width=10, justify="right")
            t.add_column("SMA60",   style="yellow", width=10, justify="right")
            t.add_column("YTD%",    style="yellow", width=8, justify="right")
            t.add_column("TgtMean", style="yellow", width=10, justify="right")
            def f(v, dec=2):
                if v is None or pd.isna(v): return "—"
                try:
                    if abs(v) > 1e9: return f"{v/1e9:.1f}B"
                    if abs(v) > 1e6: return f"{v/1e6:.1f}M"
                    if abs(v) > 1e3: return f"{v/1e3:.1f}K"
                    return f"{v:.{dec}f}"
                except: return "—"
            for _, r in top.iterrows():
                t.add_row(
                    str(r.get("code", "")),
                    str(r.get("name", ""))[:12],
                    str(r.get("market", "")),
                    f(r.get("close") or r.get("adj_close")),
                    f(r.get("volume")),
                    f(r.get("market_cap")),
                    f(r.get("sma_20")),
                    f(r.get("sma_60")),
                    f(r.get("ytd_pct"), 1),
                    f(r.get("target_mean")),
                )
            console.print(t)

        # Table 4: 多格式輸出
        if self.save_results:
            t = Table(title="💾 [bold]4. Multi-Format Output[/bold]",
                      box=box.ROUNDED, header_style="bold magenta")
            t.add_column("Table",   style="cyan", width=30)
            t.add_column("Rows",    style="green", width=10, justify="right")
            t.add_column("Parquet", style="yellow", width=10, justify="center")
            t.add_column("CSV",     style="yellow", width=8, justify="center")
            t.add_column("JSON",    style="yellow", width=8, justify="center")
            t.add_column("DuckDB",  style="yellow", width=8, justify="center")
            for tbl, info in self.save_results.items():
                fmts = {o.get("format"): ("✅" if "error" not in o else "❌")
                        for o in info.get("outputs", [])}
                t.add_row(tbl, f"{info['rows']:,}",
                          fmts.get("parquet", "—"), fmts.get("csv", "—"),
                          fmts.get("json", "—"), fmts.get("duckdb", "—"))
            console.print(t)

        # Final panel
        n_total = len(self.df_quote) if self.df_quote is not None else 0
        n_hist = self.yf_history.stats.get("tickers_ok", 0)
        n_cons = self.yf_consensus.stats.get("ok", 0)
        n_final_rows = len(self.df_final) if self.df_final is not None else 0
        n_final_cols = len(self.df_final.columns) if self.df_final is not None else 0
        overall = ("[bold green]✅ Pipeline 全綠[/bold green]"
                   if n_total > 0 and n_final_rows > 0
                   else "[bold yellow]⚠️ 部分管道異常[/bold yellow]")
        summary = (
            f"[bold]Universe[/bold]        : {n_total:,} 檔 (TWSE+TPEX)\n"
            f"[bold]YF History[/bold]      : {n_hist:,} 檔 OK\n"
            f"[bold]YF Consensus[/bold]    : {n_cons:,} 檔 OK\n"
            f"[bold]Final shape[/bold]     : {n_final_rows:,} × {n_final_cols} cols\n"
            f"[bold]Output tables[/bold]   : {len(self.save_results)}\n"
            f"[bold]耗時[/bold]            : {elapsed} 秒\n\n{overall}"
        )
        console.print(Panel.fit(summary, title="[bold cyan]🎯 整體狀態[/bold cyan]",
                                border_style="cyan"))

    def _plain_summary(self):
        print(f"\nMDL004 Summary: {len(self.df_final) if self.df_final is not None else 0} rows")


# =====================================================================================
# 🎯 Entry
# =====================================================================================

def main():
    eng = TWFullMarketEngine()
    return eng.run()


def main_governed() -> int:
    """誠實多態的入口:閘沒開回 **rc4 GATED**,不是 rc1 RED。

    批716 實測:原件在閘關著時一路跑到 Step 1,兩所都拿不到料,然後 `abort` 回 rc1 ——
    **把「閘沒開」講成「壞了」**。判錯的紅燈和假綠一樣傷:看的人會去修一支沒有壞的引擎。
    """
    if not net_consent():
        print("  [GATED] 同意閘未開 —— 這**不是壞掉**。本引擎要觸網(TWSE / TPEX OpenAPI + yfinance)。")
        print("  [律] **AI 永不代設同意閘。** 要開請操作員自己貼:")
        print("       $env:VIA_NET_CONSENT='YES'")
        print("  [註] `--offline-probe` 可以在閘關著時跑一次啟動探針(證明它起得來,一個位元組都不出網)。")
        return 4
    return main()


def selftest() -> int:
    """離線自測:**零網路**。證明它接得上加速器與網路工具、而且閘沒開時誠實停。"""
    ran, fails = [], []

    def chk(name, cond, note=""):
        ran.append(name)
        ok = bool(cond)
        if not ok:
            fails.append(name)
        print("  [%s] %s%s" % ("OK" if ok else "FAIL", name, (" (%s)" % note) if note else ""))

    print("=== TW 全市場引擎 v0100(批716)· 自測(沙盒 · 零網路 · 不代設同意閘)===")
    src = pathlib.Path(__file__).read_text(encoding="utf-8", errors="ignore")
    chk("① 加速器橋接得上(缺席也不能炸 —— graceful 零行為變更)",
        "VIA_ACCEL" in globals(), f"(加速器 {'在' if VIA_ACCEL else '缺席(合律)'})")
    nt = _via_net()
    chk("② **VDF 的網路出口只有統包工具**(批115 全導入令 · L20 後端才是 AegisNexus):"
        "檔頭要有 `[VIA:NET-BRIDGE]`,而且 `http_json` 問得到。"
        "**批716 自糾**:第一版直接把 AegisNexus 掛進來當出口 —— 方向對、**門走錯了**;"
        "繞過統包等於在 VDF 開第二個網路出口,批115 的正向尺當場紅。"
        "**負控**:統包缺席要誠實 ABSENT,不偷偷落回直連",
        "[VIA:NET-" + "BRIDGE:" in src and nt is not None and hasattr(nt, "http_json"),
        f"(統包 {'在' if nt else '缺席'} · 橋標記 {'有' if '[VIA:NET-' + 'BRIDGE:' in src else '無'})")
    code = "\n".join(ln for ln in src.splitlines() if not ln.strip().startswith("#"))
    direct = ("requests." + "get") in code or ("urllib.request." + "urlopen") in code
    chk("③ **零直連**:全檔不得再出現直接 HTTP 呼叫(註解不算)—— 有第二個出口,L20 就是空的",
        not direct, f"(直連字樣 {'有' if direct else '無'})")
    st, _ = _net_json("https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL")
    chk("④ **同意閘誠實態**:閘沒開要回 GATED(**不是壞掉、也不是沒資料**);"
        "AI 永不代設 —— 本支只讀環境變數,一行都不寫",
        st in ("GATED", "OK"), f"(閘 {st})")
    pause = "按 Enter " + "鍵退出"
    chk("⑤ **零彈窗**:上游原件結尾停在一行等人敲鍵盤的 `input()`,格子裡會把整跑卡死;已拆除。"
        "(檢的字句本身不可以含它禁的那串字 —— 本週第四次踩 LL384,這次拆寫)",
        pause not in src, f"(彈窗 {'有' if pause in src else '無'})")
    chk("⑦ **閘沒開回 rc4 GATED,不是 rc1 RED**:原件在閘關著時一路跑到 Step 1,"
        "兩所都拿不到料然後 abort 回 1 —— **把『閘沒開』講成『壞了』**。"
        "判錯的紅燈和假綠一樣傷:看的人會去修一支沒有壞的引擎",
        "main_governed" in src and "return 4" in src, "(governed 入口 在)")
    import io as _io, contextlib as _ctx
    _buf = _io.StringIO()
    with _ctx.redirect_stdout(_buf):
        _cb = _progress(3, "自測", every=0.0)
        _cb(); _cb(); _cb()
    _out = _buf.getvalue()
    chk("⑧ **動態進度**(操作員實錄「現在不知道是卡斷還在運作」):長步驟要印 `[進度] n/N · %`"
        "(批694 約定的字樣,PowerShell 那端的動態進度條認它畫真百分比),而且要附**已跑秒數與估剩**。"
        "**負控**:只脈動不報數 = 跟卡死長得一模一樣,看的人分不出來",
        "[進度]" in _out and "3/3" in _out and "100.0%" in _out and "估剩" in _out
        and "progress_cb=_progress(" in src,
        f"(樣本 {_out.strip().splitlines()[-1][:58] if _out.strip() else '無'})")

    chk("⑨ **共識走統包的 cookie+crumb 握手道**:工作站實錄 Step 3 撞 `HTTP 401 Invalid Crumb` —— "
        "裸 yfinance 沒做 Yahoo 那套握手。統包身上早就有(批137/批155),這裡只接線不重寫。"
        "**負控**:取不到要誠實落回並**講明為什麼**,不可以默默回空當成「沒有共識」",
        "yahoo_quote_summary_raw" in src and "_fetch_via_net" in src
        and "Invalid Crumb" in src,
        "(委派 + 誠實落回 皆在)")

    chk("⑥ 兩所都在掃描面(TWSE **與** TPEX):樹上 893 檔全是 `.TWO`,缺的就是上市那一半",
        "TWSEFullMarketFetcher" in src and "TPEXFullMarketFetcher" in src
        and "openapi.twse.com.tw" in src,
        "(TWSE + TPEX 兩個抓取器都在)")
    n = len(ran) - len(fails)
    print(f"  [計] {len(ran)} 檢 OK {n} · FAIL {len(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    import pathlib
    if "--selftest" in sys.argv[1:]:
        sys.exit(selftest())
    if "--offline-probe" in sys.argv[1:]:
        # 啟動探針:閘關著照樣把引擎點起來,證明它起得來;網路一個位元組都不出。
        sys.exit(main())
    try:
        # 批716:**零彈窗律** —— 上游原件在這裡 `input()` 等人按 Enter,格子裡會把整跑卡死。
        sys.exit(main_governed())
    except KeyboardInterrupt:
        print("\n[中斷]")
        sys.exit(130)
