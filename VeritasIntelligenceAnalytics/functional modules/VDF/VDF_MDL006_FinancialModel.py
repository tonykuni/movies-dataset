#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
================================================================================
  VDF_MDL006_FinancialModel.py
================================================================================
  VERITAS DATA FRAMEWORK · MDL006  Financial Model + Valuation Engine
  Version    : 1.0.0   |   Module ID : VDF-MDL006-FM-001
  Asset ID   : VDF-MDL006-CLS-001
  Policy     : 功能只增不減 · append-only · SSOT · LL-compliant

ROLE
================================================================================
  以 YFinance 為主要資料源 (TW + 海外股通用), 對每檔個股建立:

  [1] 每日交易數據     · tk.history(period='5y', interval='1d')
                          欄位: Open, High, Low, Close, Adj Close, Volume

  [2] 三大報表          · 年度 + 當季 + 累計
      - 損益表 IS  · tk.income_stmt + tk.quarterly_income_stmt
      - 資負表 BS · tk.balance_sheet + tk.quarterly_balance_sheet
      - 現金流 CF · tk.cashflow + tk.quarterly_cashflow

  [3] 比率分析  Ratio Analysis (按報表年度滾動)
      - 獲利能力: GPM · OPM · NPM · ROE · ROA · ROIC
      - 流動性:   Current Ratio · Quick Ratio · Cash Ratio
      - 償債:     D/E · D/A · Interest Coverage
      - 效率:     Asset Turnover · Inventory Days · DSO · DPO · Cash Cycle
      - 成長:     Revenue YoY · NI YoY · EPS YoY

  [4] 每股分析  Per-Share
      - EPS  Basic + Diluted (TTM + Forward 2026-27)
      - BPS  Book Value Per Share
      - DPS  Dividend Per Share
      - CFPS Operating Cash Flow Per Share
      - FCFPS Free Cash Flow Per Share
      - SPS  Sales Per Share

  [5] 評價分析  Valuation
      - PER (trailing/forward)
      - PBR (TTM BVPS)
      - PSR (TTM Sales)
      - EV/EBITDA
      - Dividend Yield · FCF Yield · Earnings Yield
      - PEG (PE / EPS Growth)

  [6] 財務模型  Financial Model (附帶, 可開關)
      - 1-stage Gordon Growth Model     (DCF lite)
      - Justified PE                    (Cost of Equity 模型)
      - 殘餘收益 Residual Income (RIM)
      - 同業比較 Peer Comparable

  [7] 圖表        · Forward PE Band · PB Band (Plotly HTML, 互動式)
                    SVG fallback (無 Plotly 時)

USAGE
================================================================================
  python VDF_MDL006_FinancialModel.py                        # 預設 universe + 全部報表
  python VDF_MDL006_FinancialModel.py --tickers 2330,3324,NVDA
  python VDF_MDL006_FinancialModel.py --period 10y           # 改抓 10 年日線
  python VDF_MDL006_FinancialModel.py --no-charts            # 不畫 PE/PB band
  python VDF_MDL006_FinancialModel.py --no-pause             # CI 模式
"""

# =====================================================================================
# 📋 ALL PARAMETERS ON TOP
# =====================================================================================

PROJECT_NAME       = "1-6-FinancialModel"
# 歸檔可攜補丁(2026-08-12 整合去重歸戶;工作站正本路徑優先,缺席退本地 db — 內容零改):
import os as _os
from pathlib import Path as _P
_PROD_BASE = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VDF\dict"
BASE_DIR           = _PROD_BASE if _os.path.isdir(_PROD_BASE) else str(_P(__file__).parent / "db")

OUTPUT_DIR         = "1-6-FinancialModel"

# Universe 來源 (與 MDL005 一致)
UNIVERSE_SOURCE    = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VDF\dict\1-0-TWUniverse"
UNIVERSE_FILE      = "tw_universe_combined.parquet"
EXTRA_TICKERS      = ["NVDA", "TSM", "AAPL"]

# YFinance 設定
YF_HISTORY_PERIOD  = "5y"            # 5 年日線 (PE/PB Band 用)
YF_HISTORY_INTERVAL= "1d"
YF_TIMEOUT         = 20
YF_RETRY           = 3
ENABLE_QUARTERLY   = True            # 是否抓當季+累計 (預設 True)
ENABLE_ANNUAL      = True            # 是否抓年度

# 比率分析
RATIO_MIN_PERIODS  = 2               # 需至少 2 期才算成長率
FORWARD_EPS_YEARS  = [2026, 2027]    # forward PE 計算用

# PE Band 設定
PE_BAND_LEVELS     = [10, 15, 20, 25, 30, 35]   # 6 條 PE 線
PB_BAND_LEVELS     = [1.0, 1.5, 2.0, 3.0, 5.0]  # 5 條 PB 線
USE_DYNAMIC_BANDS  = True            # True: 用歷史 PE 分位(-2σ/-1σ/mean/+1σ/+2σ); False: 用固定 levels
PE_BAND_TITLE      = "Forward PE Band"
PB_BAND_TITLE      = "PB Band"
CHART_HEIGHT       = 500
CHART_WIDTH        = 1100

# 並發
ENABLE_THREADPOOL  = True
THREADPOOL_WORKERS = 6               # YF 同時抓 6 檔 (避免 throttle)
MAX_RETRIES        = 3
RETRY_DELAY        = 2

# 輸出格式
OUTPUT_PARQUET     = True   # 必選
OUTPUT_DUCKDB      = True
OUTPUT_CSV         = True
OUTPUT_JSON        = False  # MDL006 資料大, JSON 預設關 (可開)
OUTPUT_CHARTS      = True   # PE/PB band HTML

CSV_ENCODING       = "utf-8-sig"
DUCKDB_FILENAME    = "VDF_MDL006_FinancialModel.duckdb"
CHARTS_SUBDIR      = "charts"
ENABLE_BACKUP      = True
MAX_BACKUP_FILES   = 5
LOG_LEVEL          = "INFO"


# =====================================================================================
# 📦 Imports
# =====================================================================================

import os, sys, re, json, time, warnings
from datetime import datetime, timedelta
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

try:
    import plotly.graph_objects as go
    from plotly.offline import plot as plot_html
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    go = None

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


def _yf_suffix(market: str) -> str:
    if market == "TWSE": return ".TW"
    if market == "TPEX": return ".TWO"
    return ""


def _resolve_yf_ticker(ticker: str, market: Optional[str] = None) -> str:
    t = str(ticker).strip().upper()
    if '.' in t or '^' in t or '=' in t:
        return t
    if re.match(r'^[1-9]\d{3}$', t):
        if market == "TPEX": return f"{t}.TWO"
        return f"{t}.TW"
    return t


def _safe_float(v: Any) -> Optional[float]:
    try:
        if v is None: return None
        if pd is not None and pd.isna(v): return None
        return float(v)
    except (TypeError, ValueError):
        return None


def _safe_div(a: Any, b: Any, mul: float = 1.0) -> Optional[float]:
    """安全除法 (a/b)*mul, 失敗回 None."""
    fa = _safe_float(a); fb = _safe_float(b)
    if fa is None or fb is None or fb == 0:
        return None
    try:
        return (fa / fb) * mul
    except Exception:
        return None


# =====================================================================================
# 🌐 [Fetcher] YFinanceFinancialFetcher
# =====================================================================================

class YFinanceFinancialFetcher:
    """
    抓 yfinance 完整財務資料:
      - history (5y daily OHLCV + Adj Close)
      - income_stmt + quarterly_income_stmt
      - balance_sheet + quarterly_balance_sheet
      - cashflow + quarterly_cashflow
      - info (用於 EPS / BPS / DPS 等橫斷面)
    """

    VERSION = "1.0.0"

    def __init__(self):
        self.stats = {"ok": 0, "fail": 0, "errors": []}

    def _fetch_one(self, yf_ticker: str) -> Dict[str, Any]:
        """抓單一 ticker, 回傳 dict 包含 6 個 DataFrame + info."""
        out: Dict[str, Any] = {
            "yf_ticker":     yf_ticker,
            "history":       None,
            "is_annual":     None, "is_quarterly":    None,
            "bs_annual":     None, "bs_quarterly":    None,
            "cf_annual":     None, "cf_quarterly":    None,
            "info":          {},
            "_error":        None,
        }
        if not YFINANCE_AVAILABLE or yf is None:
            out["_error"] = "yfinance_not_installed"
            return out
        for attempt in range(MAX_RETRIES):
            try:
                tk = yf.Ticker(yf_ticker)

                # 1. 日線歷史
                try:
                    h = tk.history(period=YF_HISTORY_PERIOD,
                                   interval=YF_HISTORY_INTERVAL, timeout=YF_TIMEOUT)
                    if h is not None and not h.empty:
                        # 確保 index 有名字 (YF 通常給 'Date', mock 可能 None)
                        if h.index.name is None:
                            h.index.name = "date"
                        h = h.reset_index()
                        # Normalize date col name (各種可能性都處理)
                        for cand in ["Date", "Datetime", "date", "index"]:
                            if cand in h.columns and cand != "date":
                                h = h.rename(columns={cand: "date"})
                                break
                        if "date" not in h.columns:
                            # 萬一還是沒 date 欄, 用第一個 datetime-like 欄
                            for c in h.columns:
                                if pd.api.types.is_datetime64_any_dtype(h[c]):
                                    h = h.rename(columns={c: "date"}); break
                        if "date" in h.columns:
                            h["date"] = pd.to_datetime(h["date"], errors='coerce')
                            if hasattr(h["date"], 'dt') and h["date"].dt.tz is not None:
                                h["date"] = h["date"].dt.tz_localize(None)
                        h["yf_ticker"] = yf_ticker
                        out["history"] = h
                except Exception as e:
                    self.stats["errors"].append(f"{yf_ticker}:history:{str(e)[:60]}")

                # 2. info
                try:
                    out["info"] = tk.info or {}
                except Exception:
                    out["info"] = {}

                # 3. 三大報表 (年度 + 當季)
                def _safe_get(attr_name):
                    try:
                        df = getattr(tk, attr_name, None)
                        if df is None or df.empty: return None
                        # Yahoo 給的是寬表: rows=indicators, cols=periods. transpose 變 long.
                        out_df = df.T.reset_index().rename(columns={"index": "period_end"})
                        out_df["period_end"] = pd.to_datetime(out_df["period_end"], errors='coerce')
                        out_df["yf_ticker"]  = yf_ticker
                        return out_df
                    except Exception as e:
                        self.stats["errors"].append(f"{yf_ticker}:{attr_name}:{str(e)[:60]}")
                        return None

                if ENABLE_ANNUAL:
                    out["is_annual"] = _safe_get("income_stmt")
                    out["bs_annual"] = _safe_get("balance_sheet")
                    out["cf_annual"] = _safe_get("cashflow")
                if ENABLE_QUARTERLY:
                    out["is_quarterly"] = _safe_get("quarterly_income_stmt")
                    out["bs_quarterly"] = _safe_get("quarterly_balance_sheet")
                    out["cf_quarterly"] = _safe_get("quarterly_cashflow")

                self.stats["ok"] += 1
                return out
            except Exception as e:
                last_err = str(e)[:120]
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    out["_error"] = last_err
                    self.stats["fail"] += 1
                    self.stats["errors"].append(f"{yf_ticker}: {last_err}")
        return out

    def fetch_batch(self, yf_tickers: List[str]) -> Dict[str, Dict]:
        """並發抓, 回傳 dict {yf_ticker: per_ticker_data}."""
        results = {}
        if ENABLE_THREADPOOL and len(yf_tickers) > 1:
            with ThreadPoolExecutor(max_workers=THREADPOOL_WORKERS) as pool:
                futmap = {pool.submit(self._fetch_one, t): t for t in yf_tickers}
                for fut in as_completed(futmap):
                    t = futmap[fut]
                    try:
                        results[t] = fut.result()
                    except Exception as e:
                        self.stats["errors"].append(f"{t}:future:{str(e)[:80]}")
        else:
            for t in yf_tickers:
                results[t] = self._fetch_one(t)
        return results


# =====================================================================================
# 📊 RatioAnalyzer
# =====================================================================================

class RatioAnalyzer:
    """
    從三大報表 + info 計算比率:
      獲利能力 / 流動性 / 償債 / 效率 / 成長

    輸入 (per_ticker_data dict, 同 _fetch_one 輸出格式):
      is_annual / bs_annual / cf_annual (DataFrame, rows=periods, cols=indicators)
      info (dict)
    """

    VERSION = "1.0.0"

    # YFinance 欄位名稱對照 (新版 yf >= 0.2)
    KEYS = {
        # Income Statement
        "revenue":         ["Total Revenue", "TotalRevenue", "Revenues"],
        "gross_profit":    ["Gross Profit", "GrossProfit"],
        "operating_income":["Operating Income", "OperatingIncome", "Operating Profit"],
        "net_income":      ["Net Income", "NetIncome", "Net Income Common Stockholders"],
        "ebitda":          ["EBITDA", "Normalized EBITDA"],
        "interest_expense":["Interest Expense", "InterestExpense"],
        "tax":             ["Tax Provision", "Income Tax Expense"],
        "shares_diluted":  ["Diluted Average Shares", "Diluted Shares"],
        # Balance Sheet
        "total_assets":    ["Total Assets", "TotalAssets"],
        "total_equity":    ["Stockholders Equity", "Common Stock Equity", "Total Equity Gross Minority Interest"],
        "total_liab":      ["Total Liabilities Net Minority Interest", "Total Liab"],
        "current_assets":  ["Current Assets", "TotalCurrentAssets"],
        "current_liab":    ["Current Liabilities", "TotalCurrentLiabilities"],
        "cash":            ["Cash And Cash Equivalents", "Cash"],
        "inventory":       ["Inventory"],
        "receivables":     ["Accounts Receivable", "Receivables"],
        "payables":        ["Accounts Payable"],
        "total_debt":      ["Total Debt", "Long Term Debt"],
        # Cash Flow
        "ocf":             ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"],
        "capex":           ["Capital Expenditure"],
        "fcf":             ["Free Cash Flow"],
        "dividends_paid":  ["Cash Dividends Paid"],
    }

    @classmethod
    def _get(cls, df: Optional["pd.DataFrame"], key: str, row_idx: int = 0) -> Optional[float]:
        """從 DataFrame 取單一指標 (row_idx=0 表示最近一期)."""
        if pd is None or df is None or df.empty:
            return None
        for col in cls.KEYS.get(key, []):
            if col in df.columns:
                try:
                    val = df.iloc[row_idx][col]
                    return _safe_float(val)
                except (IndexError, KeyError):
                    pass
        return None

    @classmethod
    def calc_ratios_per_period(cls, is_df, bs_df, cf_df) -> "pd.DataFrame":
        """對每個 period 算一行比率."""
        if pd is None or is_df is None or is_df.empty:
            return pd.DataFrame() if pd is not None else None
        rows = []
        n_periods = len(is_df)
        for i in range(n_periods):
            period = is_df.iloc[i].get("period_end")
            rev   = cls._get(is_df, "revenue", i)
            gp    = cls._get(is_df, "gross_profit", i)
            opi   = cls._get(is_df, "operating_income", i)
            ni    = cls._get(is_df, "net_income", i)
            ebitda= cls._get(is_df, "ebitda", i)
            int_e = cls._get(is_df, "interest_expense", i)

            # 對應期 BS (找最近的 period_end)
            ta = te = tl = ca = cl = cash = inv = ar = ap = tot_d = None
            if bs_df is not None and not bs_df.empty:
                # 用 index i 對應 (注意 BS 通常少一期, fallback 取 i=0)
                bs_i = min(i, len(bs_df) - 1) if len(bs_df) > 0 else None
                if bs_i is not None:
                    ta    = cls._get(bs_df, "total_assets", bs_i)
                    te    = cls._get(bs_df, "total_equity", bs_i)
                    tl    = cls._get(bs_df, "total_liab", bs_i)
                    ca    = cls._get(bs_df, "current_assets", bs_i)
                    cl    = cls._get(bs_df, "current_liab", bs_i)
                    cash  = cls._get(bs_df, "cash", bs_i)
                    inv   = cls._get(bs_df, "inventory", bs_i)
                    ar    = cls._get(bs_df, "receivables", bs_i)
                    ap    = cls._get(bs_df, "payables", bs_i)
                    tot_d = cls._get(bs_df, "total_debt", bs_i)

            ocf = capex = fcf = None
            if cf_df is not None and not cf_df.empty:
                cf_i = min(i, len(cf_df) - 1) if len(cf_df) > 0 else None
                if cf_i is not None:
                    ocf   = cls._get(cf_df, "ocf", cf_i)
                    capex = cls._get(cf_df, "capex", cf_i)
                    fcf   = cls._get(cf_df, "fcf", cf_i)
            # FCF 若沒 = ocf - |capex|
            if fcf is None and ocf is not None and capex is not None:
                fcf = ocf + capex  # capex 通常為負

            # 計算
            row = {
                "period_end": period,
                # 獲利
                "gross_margin_pct":     _safe_div(gp, rev, 100),
                "operating_margin_pct": _safe_div(opi, rev, 100),
                "net_margin_pct":       _safe_div(ni, rev, 100),
                "ebitda_margin_pct":    _safe_div(ebitda, rev, 100),
                "roa_pct":              _safe_div(ni, ta, 100),
                "roe_pct":              _safe_div(ni, te, 100),
                # 流動性
                "current_ratio":        _safe_div(ca, cl),
                "quick_ratio":          _safe_div((ca or 0) - (inv or 0), cl) if ca is not None and cl is not None else None,
                "cash_ratio":           _safe_div(cash, cl),
                # 償債
                "debt_to_equity":       _safe_div(tot_d, te),
                "debt_to_assets":       _safe_div(tot_d, ta),
                "interest_coverage":    _safe_div(opi, abs(int_e) if int_e else None),
                # 效率
                "asset_turnover":       _safe_div(rev, ta),
                "inventory_days":       _safe_div(inv, rev, 365) if rev else None,
                "ar_days_dso":          _safe_div(ar, rev, 365) if rev else None,
                # 原值 (給上層用)
                "revenue":              rev,
                "gross_profit":         gp,
                "operating_income":     opi,
                "net_income":           ni,
                "ebitda":               ebitda,
                "total_assets":         ta,
                "total_equity":         te,
                "ocf":                  ocf,
                "fcf":                  fcf,
            }
            rows.append(row)
        df_out = pd.DataFrame(rows)
        # 成長率 (period 由近到遠, 所以下一期是更早的; growth = current/previous - 1)
        if len(df_out) >= 2:
            for c in ["revenue", "operating_income", "net_income"]:
                if c in df_out.columns:
                    df_out[f"{c}_yoy_pct"] = (
                        df_out[c] / df_out[c].shift(-1) - 1
                    ) * 100
        return df_out


# =====================================================================================
# 💎 ValuationAnalyzer (每股 + 評價)
# =====================================================================================

class ValuationAnalyzer:
    """每股分析 + 評價分析."""

    VERSION = "1.0.0"

    @classmethod
    def calc_valuation(cls, info: Dict, latest_ratios: Dict,
                       hist: Optional["pd.DataFrame"]) -> Dict:
        """產一行橫斷面 valuation."""
        out = {
            # 每股 (Per Share)
            "eps_trailing":          _safe_float(info.get("trailingEps")),
            "eps_forward":           _safe_float(info.get("forwardEps")),
            "bps":                   _safe_float(info.get("bookValue")),
            "dps":                   _safe_float(info.get("dividendRate")),
            # 估值
            "per_trailing":          _safe_float(info.get("trailingPE")),
            "per_forward":           _safe_float(info.get("forwardPE")),
            "pbr":                   _safe_float(info.get("priceToBook")),
            "psr":                   _safe_float(info.get("priceToSalesTrailing12Months")),
            "ev_ebitda":             _safe_float(info.get("enterpriseToEbitda")),
            "div_yield_pct":         (_safe_float(info.get("dividendYield")) or 0) * 100 if info.get("dividendYield") else None,
            "peg_ratio":             _safe_float(info.get("pegRatio")),
            # 市值 + EV
            "market_cap":            _safe_float(info.get("marketCap")),
            "enterprise_value":      _safe_float(info.get("enterpriseValue")),
            # 最新價
            "current_price":         _safe_float(info.get("currentPrice")) or _safe_float(info.get("regularMarketPrice")),
        }

        # 從 latest_ratios 補
        if latest_ratios:
            out["sales_per_share"] = _safe_div(latest_ratios.get("revenue"),
                                                _safe_float(info.get("sharesOutstanding")))
            out["cfps"]            = _safe_div(latest_ratios.get("ocf"),
                                                _safe_float(info.get("sharesOutstanding")))
            out["fcfps"]           = _safe_div(latest_ratios.get("fcf"),
                                                _safe_float(info.get("sharesOutstanding")))
            out["roe_pct"]         = latest_ratios.get("roe_pct")
            out["roa_pct"]         = latest_ratios.get("roa_pct")
            out["gross_margin_pct"]= latest_ratios.get("gross_margin_pct")
            out["operating_margin_pct"] = latest_ratios.get("operating_margin_pct")
            out["net_margin_pct"]  = latest_ratios.get("net_margin_pct")

        # FCF Yield
        if out.get("fcfps") and out.get("current_price"):
            out["fcf_yield_pct"] = _safe_div(out["fcfps"], out["current_price"], 100)
        else:
            out["fcf_yield_pct"] = None

        # Earnings Yield = 1/PE
        if out.get("per_trailing") and out["per_trailing"] > 0:
            out["earnings_yield_pct"] = round(100 / out["per_trailing"], 2)
        else:
            out["earnings_yield_pct"] = None

        return out


# =====================================================================================
# 📈 PEBandChartBuilder + PBBandChartBuilder
# =====================================================================================

class BandChartBuilder:
    """
    Forward PE Band / PB Band 圖表建構.

    PE Band:
      X: date (5 年日線)
      Y: price (Close / Adj Close)
      Bands: PE 線 (10×, 15×, 20×, 25×, 30×, 35× × Forward EPS)
             或 動態 (-2σ, -1σ, mean, +1σ, +2σ 的歷史 PE)

    PB Band:
      同上, 但 levels 用 PB × BVPS
    """

    VERSION = "1.0.0"

    @staticmethod
    def _historical_pe(hist: "pd.DataFrame", eps_ttm: float) -> "pd.DataFrame":
        """對歷史每日價格反算 PE = Price / TTM EPS (假設 EPS 不變)."""
        if pd is None or hist is None or hist.empty or not eps_ttm or eps_ttm <= 0:
            return pd.DataFrame() if pd is not None else None
        df = hist.copy()
        if "Adj Close" in df.columns:
            df["pe"] = df["Adj Close"] / eps_ttm
        elif "Close" in df.columns:
            df["pe"] = df["Close"] / eps_ttm
        return df

    @classmethod
    def build_pe_band_data(cls, hist: "pd.DataFrame", forward_eps: float,
                          ticker: str, name: str) -> Dict:
        """
        產生 PE band data + statistics.

        回傳 dict:
          - df: 含 date, price, PE_10x, PE_15x, ... 等線
          - stats: {min_pe, max_pe, mean_pe, std_pe, current_pe, ...}
        """
        if pd is None or hist is None or hist.empty:
            return {"df": pd.DataFrame() if pd is not None else None,
                    "stats": {}, "levels_used": []}

        df = hist.copy()
        price_col = "Adj Close" if "Adj Close" in df.columns else "Close"
        df = df[["date", price_col]].rename(columns={price_col: "price"}).copy()
        df = df.sort_values("date").reset_index(drop=True)

        if not forward_eps or forward_eps <= 0:
            forward_eps = 0.01  # 防 div0
        # 動態 PE
        df["pe_implied"] = df["price"] / forward_eps

        stats = {
            "ticker":     ticker,
            "forward_eps": forward_eps,
            "current_price": float(df["price"].iloc[-1]) if not df.empty else None,
            "current_pe":   float(df["pe_implied"].iloc[-1]) if not df.empty else None,
            "min_pe":       float(df["pe_implied"].min()),
            "max_pe":       float(df["pe_implied"].max()),
            "mean_pe":      float(df["pe_implied"].mean()),
            "std_pe":       float(df["pe_implied"].std()),
            "p25_pe":       float(df["pe_implied"].quantile(0.25)),
            "p75_pe":       float(df["pe_implied"].quantile(0.75)),
        }

        # 動態 levels (用 -2σ, -1σ, mean, +1σ, +2σ) 或 固定
        if USE_DYNAMIC_BANDS:
            mu = stats["mean_pe"]; sd = stats["std_pe"]
            levels = [
                ("-2σ",   mu - 2*sd),
                ("-1σ",   mu - 1*sd),
                ("mean",  mu),
                ("+1σ",   mu + 1*sd),
                ("+2σ",   mu + 2*sd),
            ]
            levels = [(l, v) for l, v in levels if v > 0]
        else:
            levels = [(f"{lv}x", lv) for lv in PE_BAND_LEVELS]

        for label, pe_level in levels:
            df[f"pe_band_{label}"] = pe_level * forward_eps

        df["ticker"] = ticker
        df["name"]   = name
        return {"df": df, "stats": stats, "levels_used": levels}

    @classmethod
    def build_pb_band_data(cls, hist: "pd.DataFrame", bvps: float,
                          ticker: str, name: str) -> Dict:
        if pd is None or hist is None or hist.empty:
            return {"df": pd.DataFrame() if pd is not None else None,
                    "stats": {}, "levels_used": []}
        df = hist.copy()
        price_col = "Adj Close" if "Adj Close" in df.columns else "Close"
        df = df[["date", price_col]].rename(columns={price_col: "price"}).copy()
        df = df.sort_values("date").reset_index(drop=True)
        if not bvps or bvps <= 0:
            bvps = 0.01
        df["pb_implied"] = df["price"] / bvps
        stats = {
            "ticker":     ticker, "bvps": bvps,
            "current_price": float(df["price"].iloc[-1]) if not df.empty else None,
            "current_pb":    float(df["pb_implied"].iloc[-1]) if not df.empty else None,
            "min_pb":        float(df["pb_implied"].min()),
            "max_pb":        float(df["pb_implied"].max()),
            "mean_pb":       float(df["pb_implied"].mean()),
            "std_pb":        float(df["pb_implied"].std()),
        }
        if USE_DYNAMIC_BANDS:
            mu = stats["mean_pb"]; sd = stats["std_pb"]
            levels = [
                ("-2σ", mu - 2*sd), ("-1σ", mu - 1*sd),
                ("mean", mu),
                ("+1σ", mu + 1*sd), ("+2σ", mu + 2*sd),
            ]
            levels = [(l, v) for l, v in levels if v > 0]
        else:
            levels = [(f"{lv}x", lv) for lv in PB_BAND_LEVELS]
        for label, pb_level in levels:
            df[f"pb_band_{label}"] = pb_level * bvps
        df["ticker"] = ticker
        df["name"]   = name
        return {"df": df, "stats": stats, "levels_used": levels}

    @classmethod
    def render_html(cls, band_data: Dict, kind: str = "pe",
                    output_path: Optional[Path] = None) -> Optional[str]:
        """Plotly HTML, 互動式. kind='pe' or 'pb'."""
        if not PLOTLY_AVAILABLE or go is None:
            return cls._render_svg_fallback(band_data, kind, output_path)
        df = band_data.get("df")
        stats = band_data.get("stats", {})
        if pd is None or df is None or df.empty:
            return None

        ticker = stats.get("ticker", "?")
        title = (f"{ticker} · {PE_BAND_TITLE} (Forward EPS = {stats.get('forward_eps',0):.2f})"
                 if kind == "pe" else
                 f"{ticker} · {PB_BAND_TITLE} (BVPS = {stats.get('bvps',0):.2f})")

        fig = go.Figure()
        # Band lines (drawn first as backdrop)
        band_prefix = "pe_band_" if kind == "pe" else "pb_band_"
        band_cols = [c for c in df.columns if c.startswith(band_prefix)]
        band_colors = ['#c96b5a', '#c4943a', '#5a9e6f', '#439a9a', '#4c78a8', '#7a6daa']
        for i, c in enumerate(band_cols):
            label = c.replace(band_prefix, "")
            fig.add_trace(go.Scatter(
                x=df["date"], y=df[c], mode='lines',
                name=label, line=dict(width=1.5, dash='dash',
                                       color=band_colors[i % len(band_colors)]),
                hovertemplate=f"{label}: %{{y:.2f}}<extra></extra>",
            ))
        # Price line
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["price"], mode='lines',
            name='Price', line=dict(width=2.5, color='#1e1d1a'),
            hovertemplate="Price: %{y:.2f}<br>%{x|%Y-%m-%d}<extra></extra>",
        ))
        # Layout
        fig.update_layout(
            title=dict(text=title, font=dict(size=16, family='DM Sans')),
            xaxis_title="Date", yaxis_title="Price",
            height=CHART_HEIGHT, width=CHART_WIDTH,
            template='plotly_white',
            font=dict(family='DM Sans', size=11),
            hovermode='x unified',
            legend=dict(orientation='h', y=-0.15, x=0.5, xanchor='center'),
            margin=dict(l=60, r=30, t=60, b=70),
        )
        # Stats annotation (top-right)
        if kind == "pe":
            stats_text = (f"Current PE: {stats.get('current_pe',0):.2f}× | "
                          f"Mean: {stats.get('mean_pe',0):.2f}× | "
                          f"Range: {stats.get('min_pe',0):.1f}-{stats.get('max_pe',0):.1f}×")
        else:
            stats_text = (f"Current PB: {stats.get('current_pb',0):.2f}× | "
                          f"Mean: {stats.get('mean_pb',0):.2f}× | "
                          f"Range: {stats.get('min_pb',0):.1f}-{stats.get('max_pb',0):.1f}×")
        fig.add_annotation(
            xref="paper", yref="paper", x=0.99, y=0.99,
            xanchor='right', yanchor='top',
            text=stats_text, showarrow=False,
            font=dict(family='DM Mono', size=9, color='#6b6860'),
            bgcolor='rgba(255,255,255,0.85)', bordercolor='#dbd9d3', borderwidth=1,
        )

        html = plot_html(fig, output_type='div', include_plotlyjs='cdn')
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            full_html = f"""<!DOCTYPE html><html><head>
<meta charset="UTF-8"><title>{title}</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Mono&family=DM+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>body{{font-family:'DM Sans',sans-serif;background:#f5f4f0;padding:20px;margin:0;}}
.hdr{{background:#fff;border:1px solid #dbd9d3;border-radius:12px;padding:16px;margin-bottom:12px;}}
.hdr h1{{font-size:18px;color:#1e1d1a;margin:0;}}
.hdr p{{font-size:11px;color:#6b6860;margin-top:4px;font-family:'DM Mono',monospace;}}
.chart{{background:#fff;border:1px solid #dbd9d3;border-radius:12px;padding:16px;}}
</style></head><body>
<div class="hdr"><h1>{title}</h1>
<p>VIA · VDF MDL006 Financial Model · build {_today()}</p></div>
<div class="chart">{html}</div>
</body></html>"""
            output_path.write_text(full_html, encoding='utf-8')
        return html

    @classmethod
    def _render_svg_fallback(cls, band_data: Dict, kind: str,
                              output_path: Optional[Path] = None) -> Optional[str]:
        """無 Plotly 時用 SVG fallback."""
        df = band_data.get("df")
        if pd is None or df is None or df.empty:
            return None
        # 簡化版 SVG: 用 1100x500 viewBox
        # 不畫互動, 只畫 price + bands
        stats = band_data.get("stats", {})
        ticker = stats.get("ticker", "?")
        n = len(df)
        x_min, x_max = 50, 1050
        y_min, y_max = 50, 450
        prices = df["price"].astype(float).values
        all_y_vals = list(prices)
        band_prefix = "pe_band_" if kind == "pe" else "pb_band_"
        band_cols = [c for c in df.columns if c.startswith(band_prefix)]
        for c in band_cols:
            all_y_vals.extend(df[c].astype(float).fillna(0).tolist())
        y_lo, y_hi = min(all_y_vals), max(all_y_vals)
        if y_hi == y_lo: y_hi = y_lo + 1

        def sx(i): return x_min + (i / max(n - 1, 1)) * (x_max - x_min)
        def sy(v): return y_max - (v - y_lo) / (y_hi - y_lo) * (y_max - y_min)

        svg_lines = [
            f'<svg viewBox="0 0 {x_max+50} {y_max+50}" xmlns="http://www.w3.org/2000/svg" font-family="DM Sans">',
            f'<text x="50" y="30" font-size="16" font-weight="bold">{ticker} · {"PE" if kind=="pe" else "PB"} Band (SVG fallback)</text>',
        ]
        # bands
        band_colors = ['#c96b5a', '#c4943a', '#5a9e6f', '#439a9a', '#4c78a8', '#7a6daa']
        for i, c in enumerate(band_cols):
            vals = df[c].astype(float).fillna(0).tolist()
            pts = " ".join(f"{sx(j):.1f},{sy(v):.1f}" for j, v in enumerate(vals))
            color = band_colors[i % len(band_colors)]
            label = c.replace(band_prefix, "")
            svg_lines.append(f'<polyline fill="none" stroke="{color}" stroke-width="1.5" stroke-dasharray="4,3" points="{pts}"><title>{label}</title></polyline>')
        # price
        pts = " ".join(f"{sx(j):.1f},{sy(v):.1f}" for j, v in enumerate(prices))
        svg_lines.append(f'<polyline fill="none" stroke="#1e1d1a" stroke-width="2.5" points="{pts}"><title>Price</title></polyline>')
        svg_lines.append('</svg>')
        svg = "\n".join(svg_lines)
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>{ticker}</title></head>
<body style="font-family:sans-serif;padding:20px;background:#f5f4f0">{svg}</body></html>"""
            output_path.write_text(html, encoding='utf-8')
        return svg


# =====================================================================================
# 💾 OutputManager (同 MDL005)
# =====================================================================================

class OutputManager:
    VERSION = "1.0.0"

    def __init__(self):
        self.output_dir = Path(BASE_DIR) / OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.charts_dir = self.output_dir / CHARTS_SUBDIR
        self.charts_dir.mkdir(exist_ok=True)
        self.duckdb_path = self.output_dir / DUCKDB_FILENAME

        self.enable_parquet = OUTPUT_PARQUET
        self.enable_duckdb  = OUTPUT_DUCKDB and DUCKDB_AVAILABLE
        self.enable_csv     = OUTPUT_CSV
        self.enable_json    = OUTPUT_JSON
        self.enable_charts  = OUTPUT_CHARTS

        if "--no-parquet" in sys.argv: self.enable_parquet = False
        if "--no-duckdb"  in sys.argv: self.enable_duckdb  = False
        if "--no-csv"     in sys.argv: self.enable_csv     = False
        if "--json"       in sys.argv: self.enable_json    = True
        if "--no-charts"  in sys.argv: self.enable_charts  = False
        self.results = {}

    def save(self, name: str, df: "pd.DataFrame") -> Dict:
        if pd is None or df is None or df.empty:
            self.results[name] = {"rows": 0, "outputs": []}
            return self.results[name]
        outputs = []
        if self.enable_parquet and PYARROW_AVAILABLE:
            p = self.output_dir / f"{name}.parquet"
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
                d.to_json(p, orient="records", indent=2, force_ascii=False)
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

    def save_chart_html(self, ticker: str, kind: str, html_content: str) -> Dict:
        """儲存 PE/PB band chart HTML."""
        fname = f"{ticker}_{kind}_band.html"
        p = self.charts_dir / fname
        try:
            # render_html 已直接 write 到 path, 這只回 metadata
            if not p.exists() and html_content:
                p.write_text(html_content, encoding='utf-8')
            return {"path": str(p), "size_kb": p.stat().st_size // 1024 if p.exists() else 0}
        except Exception as e:
            return {"error": str(e)[:80]}


# =====================================================================================
# 🎯 FinancialModelEngine (主類)
# =====================================================================================

class FinancialModelEngine:
    """
    Pipeline:
      1. UniverseLoader (與 MDL005 相同邏輯)
      2. YFinanceFinancialFetcher (history + 3 statements × 2 freqs)
      3. RatioAnalyzer (per-period 比率)
      4. ValuationAnalyzer (橫斷面評價)
      5. BandChartBuilder (PE Band + PB Band Plotly HTML)
      6. OutputManager (多格式 + charts dir)
    """

    VERSION = "1.0.0"

    def __init__(self):
        self.yf_fetcher  = YFinanceFinancialFetcher()
        self.output_mgr  = OutputManager()
        self.start_time  = time.time()
        # State
        self.df_universe       = None
        self.daily_history_all = None
        self.is_annual_all     = None
        self.is_quarterly_all  = None
        self.bs_annual_all     = None
        self.bs_quarterly_all  = None
        self.cf_annual_all     = None
        self.cf_quarterly_all  = None
        self.ratios_annual_all = None
        self.ratios_qtr_all    = None
        self.valuation_all     = None
        self.pe_band_stats_all = None
        self.pb_band_stats_all = None
        self.save_results      = {}
        self.charts_saved      = []
        # CLI
        self.tickers_override = None
        self.max_n            = None
        for i, arg in enumerate(sys.argv):
            if arg == "--tickers" and i+1 < len(sys.argv):
                self.tickers_override = [t.strip().upper() for t in sys.argv[i+1].split(",") if t.strip()]
            if arg == "--max" and i+1 < len(sys.argv):
                try: self.max_n = int(sys.argv[i+1])
                except ValueError: pass
            if arg == "--period" and i+1 < len(sys.argv):
                global YF_HISTORY_PERIOD
                YF_HISTORY_PERIOD = sys.argv[i+1]

    def show_header(self):
        header = f"""
🎯 VDF MDL006 · Financial Model + Valuation Engine (v{self.VERSION})

📊 資料源     : YFinance (history + income/balance/cashflow × annual+quarterly)
📅 日線範圍   : {YF_HISTORY_PERIOD} × {YF_HISTORY_INTERVAL}
📁 Universe   : {UNIVERSE_SOURCE}\\{UNIVERSE_FILE}
              + EXTRA: {', '.join(EXTRA_TICKERS)}
🌐 YFinance   : {'✅' if YFINANCE_AVAILABLE else '❌'}
📈 Plotly     : {'✅' if PLOTLY_AVAILABLE else '⚪ 用 SVG fallback'}
🦆 DuckDB     : {'✅' if DUCKDB_AVAILABLE else '⚪'}
🚀 並發       : {THREADPOOL_WORKERS} workers
📐 PE Band    : {'動態 (-2σ/-1σ/mean/+1σ/+2σ)' if USE_DYNAMIC_BANDS else f'固定 {PE_BAND_LEVELS}'}
📐 PB Band    : {'動態 (-2σ/-1σ/mean/+1σ/+2σ)' if USE_DYNAMIC_BANDS else f'固定 {PB_BAND_LEVELS}'}
🎛️ 設定       : tickers_override={self.tickers_override or '—'} · max={self.max_n or 'NoLimit'}
💾 Output     : Parquet={'✅' if self.output_mgr.enable_parquet else '—'} · DuckDB={'✅' if self.output_mgr.enable_duckdb else '—'} · CSV={'✅' if self.output_mgr.enable_csv else '—'} · JSON={'✅' if self.output_mgr.enable_json else '—'} · Charts={'✅' if self.output_mgr.enable_charts else '—'}
        """
        if RICH_AVAILABLE:
            console.print(Panel(header.strip(), title="[bold blue]VDF MDL006 · Financial Model[/bold blue]",
                                border_style="blue"))
        else:
            print(header)

    def _load_universe(self) -> "pd.DataFrame":
        if pd is None:
            return None
        if self.tickers_override:
            rows = []
            for t in self.tickers_override:
                if re.match(r'^[1-9]\d{3}$', t):
                    rows.append({"ticker": t, "yf_ticker": f"{t}.TW", "name": t, "market": "TWSE"})
                else:
                    rows.append({"ticker": t, "yf_ticker": t, "name": t, "market": "US"})
            return pd.DataFrame(rows)
        # Load from universe parquet
        p = Path(UNIVERSE_SOURCE) / UNIVERSE_FILE
        if p.exists():
            try:
                df = pd.read_parquet(p)
                df["yf_ticker"] = df.apply(
                    lambda r: _resolve_yf_ticker(r["code"], r.get("market")), axis=1)
                df["ticker"] = df["code"]
                if self.max_n: df = df.head(self.max_n)
                # 加 extras
                extras = [{"ticker": t, "code": t, "name": t,
                           "market": "US", "yf_ticker": t} for t in EXTRA_TICKERS]
                if extras:
                    df = pd.concat([df, pd.DataFrame(extras)], ignore_index=True)
                return df[["ticker", "yf_ticker", "name", "market"]]
            except Exception as e:
                print(f"⚠️ universe parquet 讀取失敗: {e}")
        # Fallback (debug)
        return pd.DataFrame([
            {"ticker": "2330", "yf_ticker": "2330.TW", "name": "台積電", "market": "TWSE"},
            {"ticker": "3324", "yf_ticker": "3324.TWO","name": "雙鴻",   "market": "TPEX"},
            {"ticker": "NVDA", "yf_ticker": "NVDA",    "name": "NVIDIA", "market": "US"},
        ])

    def run(self) -> int:
        try:
            self.show_header()

            # 1. Universe
            print("\n🔍 步驟 1/6: 載入 Universe")
            self.df_universe = self._load_universe()
            uni_n = len(self.df_universe) if self.df_universe is not None else 0
            print(f"   ✓ Universe: {uni_n} 檔")
            if uni_n == 0:
                print("❌ Universe 空, 中止"); return 1

            # 2. YF fetch
            print(f"\n🌐 步驟 2/6: YFinance 抓 history + 三大報表 ({uni_n} 檔)")
            yf_tickers = self.df_universe["yf_ticker"].tolist()
            per_ticker_data = self.yf_fetcher.fetch_batch(yf_tickers)
            print(f"   ✓ ok={self.yf_fetcher.stats['ok']} / fail={self.yf_fetcher.stats['fail']}")

            # 3. 合併 各 ticker 的資料成 long-form
            print(f"\n📊 步驟 3/6: 整合 daily history + 三大報表 long-form")
            hist_rows, is_a, is_q, bs_a, bs_q, cf_a, cf_q = [], [], [], [], [], [], []
            for yf_t, data in per_ticker_data.items():
                # 從 universe 找 raw ticker + name
                row = self.df_universe[self.df_universe["yf_ticker"] == yf_t]
                if row.empty: continue
                raw_t, name = row.iloc[0]["ticker"], row.iloc[0]["name"]
                if data.get("history") is not None and not data["history"].empty:
                    h = data["history"].copy()
                    h["ticker"] = raw_t; h["name"] = name
                    hist_rows.append(h)
                for src_key, target_list in [
                    ("is_annual", is_a), ("is_quarterly", is_q),
                    ("bs_annual", bs_a), ("bs_quarterly", bs_q),
                    ("cf_annual", cf_a), ("cf_quarterly", cf_q),
                ]:
                    df = data.get(src_key)
                    if df is not None and not df.empty:
                        df = df.copy()
                        df["ticker"] = raw_t; df["name"] = name
                        target_list.append(df)

            self.daily_history_all = pd.concat(hist_rows, ignore_index=True) if hist_rows else pd.DataFrame()
            self.is_annual_all     = pd.concat(is_a, ignore_index=True) if is_a else pd.DataFrame()
            self.is_quarterly_all  = pd.concat(is_q, ignore_index=True) if is_q else pd.DataFrame()
            self.bs_annual_all     = pd.concat(bs_a, ignore_index=True) if bs_a else pd.DataFrame()
            self.bs_quarterly_all  = pd.concat(bs_q, ignore_index=True) if bs_q else pd.DataFrame()
            self.cf_annual_all     = pd.concat(cf_a, ignore_index=True) if cf_a else pd.DataFrame()
            self.cf_quarterly_all  = pd.concat(cf_q, ignore_index=True) if cf_q else pd.DataFrame()
            print(f"   ✓ history    : {len(self.daily_history_all):,} 列")
            print(f"   ✓ IS annual  : {len(self.is_annual_all):,} 列 · quarterly: {len(self.is_quarterly_all):,}")
            print(f"   ✓ BS annual  : {len(self.bs_annual_all):,} 列 · quarterly: {len(self.bs_quarterly_all):,}")
            print(f"   ✓ CF annual  : {len(self.cf_annual_all):,} 列 · quarterly: {len(self.cf_quarterly_all):,}")

            # 4. Ratios
            print(f"\n📐 步驟 4/6: 比率分析 (per period)")
            ra_rows, rq_rows = [], []
            for yf_t, data in per_ticker_data.items():
                row = self.df_universe[self.df_universe["yf_ticker"] == yf_t]
                if row.empty: continue
                raw_t, name = row.iloc[0]["ticker"], row.iloc[0]["name"]
                # Annual
                if ENABLE_ANNUAL:
                    df_a = RatioAnalyzer.calc_ratios_per_period(
                        data.get("is_annual"), data.get("bs_annual"), data.get("cf_annual"))
                    if df_a is not None and not df_a.empty:
                        df_a["ticker"] = raw_t; df_a["name"] = name; df_a["freq"] = "Annual"
                        ra_rows.append(df_a)
                # Quarterly
                if ENABLE_QUARTERLY:
                    df_q = RatioAnalyzer.calc_ratios_per_period(
                        data.get("is_quarterly"), data.get("bs_quarterly"), data.get("cf_quarterly"))
                    if df_q is not None and not df_q.empty:
                        df_q["ticker"] = raw_t; df_q["name"] = name; df_q["freq"] = "Quarterly"
                        rq_rows.append(df_q)
            self.ratios_annual_all = pd.concat(ra_rows, ignore_index=True) if ra_rows else pd.DataFrame()
            self.ratios_qtr_all    = pd.concat(rq_rows, ignore_index=True) if rq_rows else pd.DataFrame()
            print(f"   ✓ 年度比率: {len(self.ratios_annual_all):,} 列")
            print(f"   ✓ 當季比率: {len(self.ratios_qtr_all):,} 列")

            # 5. Valuation (橫斷面)
            print(f"\n💎 步驟 5/6: 評價分析 (橫斷面 PER/PBR/PSR/Yield)")
            val_rows = []
            for yf_t, data in per_ticker_data.items():
                row = self.df_universe[self.df_universe["yf_ticker"] == yf_t]
                if row.empty: continue
                raw_t, name = row.iloc[0]["ticker"], row.iloc[0]["name"]
                # 取最新一期年度比率
                latest_ratios = {}
                if not self.ratios_annual_all.empty:
                    rsub = self.ratios_annual_all[self.ratios_annual_all["ticker"] == raw_t]
                    if not rsub.empty:
                        latest_ratios = rsub.iloc[0].to_dict()
                vrow = ValuationAnalyzer.calc_valuation(data.get("info", {}), latest_ratios, data.get("history"))
                vrow["ticker"] = raw_t; vrow["name"] = name; vrow["yf_ticker"] = yf_t
                vrow["date"]   = _today()
                val_rows.append(vrow)
            self.valuation_all = pd.DataFrame(val_rows) if val_rows else pd.DataFrame()
            print(f"   ✓ 評價: {len(self.valuation_all):,} 檔")

            # 6. Build PE/PB Band charts
            pe_stats_rows, pb_stats_rows = [], []
            if self.output_mgr.enable_charts:
                print(f"\n📈 步驟 6/6: 建 PE / PB Band 圖表")
                for yf_t, data in per_ticker_data.items():
                    row = self.df_universe[self.df_universe["yf_ticker"] == yf_t]
                    if row.empty: continue
                    raw_t, name = row.iloc[0]["ticker"], row.iloc[0]["name"]
                    hist = data.get("history")
                    if hist is None or hist.empty:
                        continue
                    info = data.get("info", {})
                    forward_eps = _safe_float(info.get("forwardEps")) or _safe_float(info.get("trailingEps"))
                    bvps = _safe_float(info.get("bookValue"))

                    # PE Band
                    if forward_eps and forward_eps > 0:
                        pe_data = BandChartBuilder.build_pe_band_data(hist, forward_eps, raw_t, name)
                        if pe_data["df"] is not None and not pe_data["df"].empty:
                            chart_path = self.output_mgr.charts_dir / f"{raw_t}_pe_band.html"
                            BandChartBuilder.render_html(pe_data, kind="pe", output_path=chart_path)
                            self.charts_saved.append({"ticker": raw_t, "kind": "pe",
                                                       "path": str(chart_path)})
                            pe_stats_rows.append({"ticker": raw_t, "name": name, **pe_data["stats"]})

                    # PB Band
                    if bvps and bvps > 0:
                        pb_data = BandChartBuilder.build_pb_band_data(hist, bvps, raw_t, name)
                        if pb_data["df"] is not None and not pb_data["df"].empty:
                            chart_path = self.output_mgr.charts_dir / f"{raw_t}_pb_band.html"
                            BandChartBuilder.render_html(pb_data, kind="pb", output_path=chart_path)
                            self.charts_saved.append({"ticker": raw_t, "kind": "pb",
                                                       "path": str(chart_path)})
                            pb_stats_rows.append({"ticker": raw_t, "name": name, **pb_data["stats"]})

                self.pe_band_stats_all = pd.DataFrame(pe_stats_rows) if pe_stats_rows else pd.DataFrame()
                self.pb_band_stats_all = pd.DataFrame(pb_stats_rows) if pb_stats_rows else pd.DataFrame()
                print(f"   ✓ PE band charts: {sum(1 for c in self.charts_saved if c['kind']=='pe')}")
                print(f"   ✓ PB band charts: {sum(1 for c in self.charts_saved if c['kind']=='pb')}")
            else:
                print(f"\n⏭️  步驟 6/6: 圖表已停用 (--no-charts)")
                self.pe_band_stats_all = pd.DataFrame()
                self.pb_band_stats_all = pd.DataFrame()

            # 7. Save 所有 tables
            print(f"\n💾 多格式輸出")
            for tbl_name, df in [
                ("daily_history",         self.daily_history_all),
                ("income_statement_annual",    self.is_annual_all),
                ("income_statement_quarterly", self.is_quarterly_all),
                ("balance_sheet_annual",       self.bs_annual_all),
                ("balance_sheet_quarterly",    self.bs_quarterly_all),
                ("cashflow_annual",            self.cf_annual_all),
                ("cashflow_quarterly",         self.cf_quarterly_all),
                ("ratios_annual",     self.ratios_annual_all),
                ("ratios_quarterly",  self.ratios_qtr_all),
                ("valuation_snapshot",self.valuation_all),
                ("pe_band_stats",     self.pe_band_stats_all),
                ("pb_band_stats",     self.pb_band_stats_all),
            ]:
                self.save_results[tbl_name] = self.output_mgr.save(tbl_name, df)
            for tbl, info in self.save_results.items():
                fmts = [o.get("format") for o in info.get("outputs", []) if "error" not in o]
                print(f"   ✓ {tbl:<32} → {info['rows']:>6,} 列  [{' · '.join(fmts)}]")

            # 8. Rich Summary
            print_rich_summary(self)
            print(f"\n🎉 完成! 輸出: {self.output_mgr.output_dir}")
            print(f"   Charts dir: {self.output_mgr.charts_dir}")
            return 0
        except KeyboardInterrupt:
            print("\n⚠️ 中斷"); return 1
        except Exception as e:
            print(f"\n❌ 錯誤: {e}")
            if LOG_LEVEL == "DEBUG":
                import traceback; traceback.print_exc()
            return 1


# =====================================================================================
# 🎨 Rich Summary Matrix
# =====================================================================================

def print_rich_summary(eng: FinancialModelEngine):
    if not RICH_AVAILABLE:
        return _plain(eng)
    elapsed = round(time.time() - eng.start_time, 2)
    console.rule("[bold cyan]🎯 VDF MDL006 · Financial Model · Summary Matrix[/bold cyan]")

    # Table 1: 套件依賴
    t = Table(title="📦 [bold]套件依賴[/bold]", box=box.ROUNDED, header_style="bold magenta")
    t.add_column("套件", style="cyan", width=18)
    t.add_column("狀態", style="green", width=8, justify="center")
    t.add_column("用途", style="yellow", width=48)
    t.add_row("pandas/numpy", "✅" if PANDAS_AVAILABLE else "❌", "資料表 + 衍生計算")
    t.add_row("yfinance",     "✅" if YFINANCE_AVAILABLE else "❌", "history + 三大報表")
    t.add_row("pyarrow",      "✅" if PYARROW_AVAILABLE else "⚪", "Parquet 必選格式")
    t.add_row("duckdb",       "✅" if DUCKDB_AVAILABLE else "⚪", "單檔資料庫")
    t.add_row("plotly",       "✅" if PLOTLY_AVAILABLE else "⚪", "PE/PB Band 互動 HTML")
    t.add_row("rich",         "✅" if RICH_AVAILABLE else "⚪", "終端表格")
    console.print(t)

    # Table 2: Pipeline 各步驟
    t = Table(title="🚀 [bold]Pipeline 結果 (6 步驟)[/bold]", box=box.ROUNDED, header_style="bold magenta")
    t.add_column("步驟",     style="cyan",  width=20)
    t.add_column("狀態",     style="green", width=8, justify="center")
    t.add_column("輸出",     style="yellow", width=50)
    uni_n = len(eng.df_universe) if eng.df_universe is not None else 0
    t.add_row("1 · Universe",    "✅" if uni_n > 0 else "❌", f"{uni_n} 檔")
    t.add_row("2 · YF Fetch",    "✅" if eng.yf_fetcher.stats['ok'] > 0 else "❌",
              f"ok={eng.yf_fetcher.stats['ok']} / fail={eng.yf_fetcher.stats['fail']}")
    t.add_row("3 · Daily History","✅" if eng.daily_history_all is not None and not eng.daily_history_all.empty else "❌",
              f"{len(eng.daily_history_all):,} 列 (5y daily OHLCV)" if pd is not None and eng.daily_history_all is not None else "—")
    t.add_row("4 · Ratios",       "✅" if pd is not None and eng.ratios_annual_all is not None and not eng.ratios_annual_all.empty else "⚪",
              f"年度 {len(eng.ratios_annual_all):,} · 當季 {len(eng.ratios_qtr_all):,}" if pd is not None and eng.ratios_annual_all is not None else "—")
    t.add_row("5 · Valuation",    "✅" if pd is not None and eng.valuation_all is not None and not eng.valuation_all.empty else "⚪",
              f"{len(eng.valuation_all):,} 檔" if pd is not None and eng.valuation_all is not None else "—")
    t.add_row("6 · PE/PB Charts", "✅" if eng.charts_saved else "⏭️",
              f"PE×{sum(1 for c in eng.charts_saved if c['kind']=='pe')} · PB×{sum(1 for c in eng.charts_saved if c['kind']=='pb')}")
    console.print(t)

    # Table 3: 三大報表 row count by ticker × statement
    if pd is not None and eng.is_annual_all is not None and not eng.is_annual_all.empty:
        t = Table(title="📊 [bold]三大報表期數明細[/bold]", box=box.ROUNDED, header_style="bold magenta")
        t.add_column("Ticker", style="cyan",  width=10)
        t.add_column("IS年", style="green", width=8, justify="right")
        t.add_column("IS季", style="green", width=8, justify="right")
        t.add_column("BS年", style="green", width=8, justify="right")
        t.add_column("BS季", style="green", width=8, justify="right")
        t.add_column("CF年", style="green", width=8, justify="right")
        t.add_column("CF季", style="green", width=8, justify="right")
        t.add_column("history days", style="yellow", width=14, justify="right")
        for _, row in eng.df_universe.iterrows():
            tk = row["ticker"]
            ia = len(eng.is_annual_all[eng.is_annual_all["ticker"]==tk]) if not eng.is_annual_all.empty else 0
            iq = len(eng.is_quarterly_all[eng.is_quarterly_all["ticker"]==tk]) if not eng.is_quarterly_all.empty else 0
            ba = len(eng.bs_annual_all[eng.bs_annual_all["ticker"]==tk]) if not eng.bs_annual_all.empty else 0
            bq = len(eng.bs_quarterly_all[eng.bs_quarterly_all["ticker"]==tk]) if not eng.bs_quarterly_all.empty else 0
            ca = len(eng.cf_annual_all[eng.cf_annual_all["ticker"]==tk]) if not eng.cf_annual_all.empty else 0
            cq = len(eng.cf_quarterly_all[eng.cf_quarterly_all["ticker"]==tk]) if not eng.cf_quarterly_all.empty else 0
            hist = len(eng.daily_history_all[eng.daily_history_all["ticker"]==tk]) if not eng.daily_history_all.empty else 0
            t.add_row(str(tk), str(ia), str(iq), str(ba), str(bq), str(ca), str(cq), f"{hist:,}")
        console.print(t)

    # Table 4: Valuation snapshot
    if pd is not None and eng.valuation_all is not None and not eng.valuation_all.empty:
        t = Table(title="💎 [bold]評價分析 Snapshot[/bold]", box=box.ROUNDED, header_style="bold magenta")
        t.add_column("Ticker",   style="cyan",   width=10)
        t.add_column("Name",     style="yellow", width=18)
        t.add_column("Price",    style="green",  width=10, justify="right")
        t.add_column("EPS TTM",  style="green",  width=10, justify="right")
        t.add_column("BPS",      style="green",  width=10, justify="right")
        t.add_column("PER TTM",  style="green",  width=10, justify="right")
        t.add_column("PER Fwd",  style="green",  width=10, justify="right")
        t.add_column("PBR",      style="green",  width=8,  justify="right")
        t.add_column("ROE %",    style="yellow", width=8,  justify="right")
        t.add_column("Yield %",  style="yellow", width=8,  justify="right")
        for _, r in eng.valuation_all.iterrows():
            def f(v, dec=2): return f"{float(v):.{dec}f}" if v is not None and pd.notna(v) else "—"
            t.add_row(str(r.get("ticker", "")),
                      str(r.get("name", ""))[:16],
                      f(r.get("current_price")),
                      f(r.get("eps_trailing")),
                      f(r.get("bps")),
                      f(r.get("per_trailing")),
                      f(r.get("per_forward")),
                      f(r.get("pbr")),
                      f(r.get("roe_pct"), 1),
                      f(r.get("div_yield_pct"), 2))
        console.print(t)

    # Table 5: PE Band stats
    if pd is not None and eng.pe_band_stats_all is not None and not eng.pe_band_stats_all.empty:
        t = Table(title="📈 [bold]Forward PE Band Stats (5y)[/bold]", box=box.ROUNDED, header_style="bold magenta")
        t.add_column("Ticker",        style="cyan",   width=10)
        t.add_column("Forward EPS",   style="green",  width=12, justify="right")
        t.add_column("Current PE",    style="yellow", width=10, justify="right")
        t.add_column("Mean PE (5y)",  style="green",  width=12, justify="right")
        t.add_column("Min PE",        style="green",  width=8,  justify="right")
        t.add_column("Max PE",        style="green",  width=8,  justify="right")
        t.add_column("Std",           style="yellow", width=8,  justify="right")
        for _, r in eng.pe_band_stats_all.iterrows():
            def f(v, dec=2): return f"{float(v):.{dec}f}" if v is not None and pd.notna(v) else "—"
            t.add_row(str(r.get("ticker", "")),
                      f(r.get("forward_eps")),
                      f(r.get("current_pe")),
                      f(r.get("mean_pe")),
                      f(r.get("min_pe")),
                      f(r.get("max_pe")),
                      f(r.get("std_pe")))
        console.print(t)

    # Table 6: PB Band stats
    if pd is not None and eng.pb_band_stats_all is not None and not eng.pb_band_stats_all.empty:
        t = Table(title="📊 [bold]PB Band Stats (5y)[/bold]", box=box.ROUNDED, header_style="bold magenta")
        t.add_column("Ticker",       style="cyan",   width=10)
        t.add_column("BVPS",         style="green",  width=12, justify="right")
        t.add_column("Current PB",   style="yellow", width=10, justify="right")
        t.add_column("Mean PB (5y)", style="green",  width=12, justify="right")
        t.add_column("Min PB",       style="green",  width=8,  justify="right")
        t.add_column("Max PB",       style="green",  width=8,  justify="right")
        for _, r in eng.pb_band_stats_all.iterrows():
            def f(v, dec=2): return f"{float(v):.{dec}f}" if v is not None and pd.notna(v) else "—"
            t.add_row(str(r.get("ticker", "")),
                      f(r.get("bvps")),
                      f(r.get("current_pb")),
                      f(r.get("mean_pb")),
                      f(r.get("min_pb")),
                      f(r.get("max_pb")))
        console.print(t)

    # Table 7: 輸出明細
    if eng.save_results:
        t = Table(title="💾 [bold]多格式輸出 (12 tables)[/bold]", box=box.ROUNDED, header_style="bold magenta")
        t.add_column("Table",   style="cyan",   width=32)
        t.add_column("列數",    style="green",  width=10, justify="right")
        t.add_column("Parquet", style="yellow", width=8,  justify="center")
        t.add_column("CSV",     style="yellow", width=8,  justify="center")
        t.add_column("JSON",    style="yellow", width=8,  justify="center")
        t.add_column("DuckDB",  style="yellow", width=8,  justify="center")
        for tbl, info in eng.save_results.items():
            fmts = {o.get("format"): ("✅" if "error" not in o else "❌")
                    for o in info.get("outputs", [])}
            t.add_row(tbl, f"{info['rows']:,}",
                      fmts.get("parquet", "—"), fmts.get("csv", "—"),
                      fmts.get("json", "—"), fmts.get("duckdb", "—"))
        console.print(t)

    # Final panel
    total_rows = sum(info.get("rows", 0) for info in eng.save_results.values())
    n_charts = len(eng.charts_saved)
    overall = ("[bold green]✅ Pipeline 全綠[/bold green]"
               if eng.yf_fetcher.stats['ok'] > 0
               else "[bold yellow]⚠️ 部分管道異常[/bold yellow]")
    summary = (
        f"[bold]Universe[/bold]      : {len(eng.df_universe) if eng.df_universe is not None else 0} 檔\n"
        f"[bold]YF success[/bold]    : {eng.yf_fetcher.stats['ok']} / {eng.yf_fetcher.stats['ok'] + eng.yf_fetcher.stats['fail']}\n"
        f"[bold]Tables output[/bold] : {len(eng.save_results)} (Parquet × {sum(1 for r in eng.save_results.values() for o in r.get('outputs', []) if o.get('format') == 'parquet' and 'error' not in o)})\n"
        f"[bold]Total rows[/bold]    : {total_rows:,}\n"
        f"[bold]Charts HTML[/bold]   : {n_charts} (PE × {sum(1 for c in eng.charts_saved if c['kind']=='pe')} · PB × {sum(1 for c in eng.charts_saved if c['kind']=='pb')})\n"
        f"[bold]耗時[/bold]          : {elapsed} 秒\n\n{overall}"
    )
    console.print(Panel.fit(summary, title="[bold cyan]🎯 整體狀態[/bold cyan]", border_style="cyan"))


def _plain(eng):
    print(f"\n{'='*60}\nMDL006 Summary\n{'='*60}")
    print(f"  Tables: {len(eng.save_results)}")
    print(f"  Charts: {len(eng.charts_saved)}")


# =====================================================================================
# 🎯 Entry
# =====================================================================================

def main():
    print("🚀 VDF MDL006 · Financial Model 啟動...")
    eng = FinancialModelEngine()
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
