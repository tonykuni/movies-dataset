#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== VDF_MDL006_FinancialModel_v0100(側線 2026-09-23;主線批號由併線的手指定 L25)=====
# 操作員 2026-09-23 上傳本支原件並令「自動實測 · 自動修正 · 自動完成」。
# 先量:上傳檔與主線批716 收容件 supportive modules/references/intake/VIA_VDF_Engines_b716/ 逐位元相同(sha256 3da0113e352dec5c…);
#   樹上副本全是它的超集(多加速器橋/網路橋/L53 自測動詞/可攜路徑),上傳獨有定義 0 —— 沒有可併的內容,要做的是讓它真的能跑。
# 本版以 functional modules/VIA_RetiredEngines/batch182_wave2/functional modules/VDF/VDF_MDL006_FinancialModel.py(37 個定義,樹上最完整的一份)為底,原邏輯只動誠實態那幾個 return,其餘一行未改;加:
#   ① 治理入口 main_governed():閘一委派統包網路工具 gate_state(),閘關 rc4 GATED 零出網零寫檔(同 VDF_MDL004 v0100 先例)
#   ② 誠實多態:零列 rc2 NODATA · 缺必要套件 rc3 ABSENT · 例外 rc1 RED(原件把沒料講成成功或壞掉)
#   ③ 自測 ⑦:閘關回 rc4、零連線(另補整段 L53 自測動詞:原件沒有 --selftest,旗標被略過→整條管線真跑)
# 實測(容器;unshare -n 斷網;同意閘未設):原件沒有 --selftest,旗標被略過→整條管線真跑:對 Yahoo 抓 2330.TW / NVDA 等(全敗),12 張空表落檔、印「🎉 完成」回 rc0(假綠)。
# 出網仍是原件的直呼(閘後才呼,同 VDF_MDL004 v0100 先例);改走統包 yf_history / http_json 是下一步(掉球)。
# 逐行審讀後再修(同日;每一條都有自測):
#   ④ 有料才算 ok:原件每個報表各自吞例外後照樣 ok+=1(斷網實測 ok=3 / fail=0、七張表全 0 列)
#   ⑤ 三表依期末日對期:原件用列序配對,資產負債表少一期時舊的損益期配到別一期(自測 ⑨ 正負控)
#   ⑥ 年增真的是年增:原件取下一列 —— 季表上那是季增;改依日期往回一年,季表另給 qoq(自測 ⑩)
#   ⑦' 殖利率單位:Yahoo 2025 起 dividendYield 已是百分數,原件再 ×100(0.45% → 45%);改用 dividendRate ÷ 現價(自測 ⑪)
#   ⑧' 報表幣別 ≠ 報價幣別(TSM:TWD 報表、USD 報價)→ 跨幣別每股/殖利率欄留空、PB band 不畫(自測 ⑫)
#   ⑨' --tickers 依樹上台股名冊決定 .TW/.TWO(原件一律 .TW,上櫃股抓錯);--help 只印用法、未知旗標 rc1;結尾等 Enter 只在互動終端(自測 ⑬)
#   ⑩' PE/PB band 用的是單一 EPS/BVPS(帶狀線是水平線):這版只在 stats 講明 basis,逐期 EPS 的河流圖是掉球
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
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
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


def _div_yield_pct(info: Dict) -> Optional[float]:
    """v0100:殖利率(%)。Yahoo 2025 起 dividendYield 改回傳百分數(0.45 = 0.45%),原件再 ×100 成 45%。
    先用單位不含糊的 dividendRate ÷ 現價;沒有再用 trailingAnnualDividendYield(仍是小數)×100;最後才用 dividendYield(已是百分數)。"""
    info = info or {}
    rate = _safe_float(info.get("dividendRate"))
    px = _safe_float(info.get("currentPrice")) or _safe_float(info.get("regularMarketPrice"))
    if rate is not None and px:
        return rate / px * 100
    t = _safe_float(info.get("trailingAnnualDividendYield"))
    if t is not None:
        return t * 100
    return _safe_float(info.get("dividendYield"))


def cross_currency(info: Dict):
    """v0100:回 (報表幣別, 報價幣別);缺一回 None。"""
    info = info or {}
    fc = info.get("financialCurrency")
    qc = info.get("currency")
    return (str(fc).upper() if fc else None), (str(qc).upper() if qc else None)


_TW_ROSTER_CACHE: Dict[str, Any] = {}


def _tw_roster_yf(code: str) -> Optional[str]:
    """v0100:台股代號 → yfinance 代號,讀樹上台股名冊(functional modules/VRN/VRN_TWRoster_Offline_v*.json 尾版;唯讀)。
    原件 --tickers 一律補 .TW,上櫃股(例 3324 雙鴻)就抓錯。名冊不在或查無 → None(呼叫方退回 .TW 並講明)。"""
    if "codes" not in _TW_ROSTER_CACHE:
        codes = {}
        try:
            hits = sorted((Path(__file__).resolve().parent.parent / "VRN").glob("VRN_TWRoster_Offline_v*.json"))
            if hits:
                import json as _js
                codes = (_js.loads(hits[-1].read_text(encoding="utf-8")) or {}).get("codes") or {}
        except Exception:
            codes = {}
        _TW_ROSTER_CACHE["codes"] = codes
    rec = _TW_ROSTER_CACHE["codes"].get(str(code)) or {}
    yf_t = rec.get("yf") if isinstance(rec, dict) else None
    return str(yf_t) if yf_t else None


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

                # v0100:有料才算 ok —— 原件每個報表各自吞例外後照樣 ok+=1,斷網實測 ok=3 / fail=0、七張表全 0 列
                _got = [k for k in ("history", "is_annual", "is_quarterly", "bs_annual", "bs_quarterly", "cf_annual", "cf_quarterly")
                        if out.get(k) is not None and len(out[k])]
                if _got:
                    self.stats["ok"] += 1
                else:
                    out["_error"] = "無料(價格史與六表皆空)"
                    self.stats["fail"] += 1
                    self.stats["errors"].append(f"{yf_ticker}: 無料")
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

    @staticmethod
    def _match_period_row(df, period, tol_days: int = 20):
        """v0100:依期末日對期(±tol_days),回位置索引或 None。
        原件用列序對期:資產負債表少一期時,舊的損益期會配到別一期的資產負債(且 fallback 取最後一列)。"""
        if pd is None or df is None or df.empty or period is None or "period_end" not in df.columns:
            return None
        try:
            pe = pd.to_datetime(df["period_end"], errors="coerce")
            d = (pe - pd.Timestamp(period)).abs()
            if d.isna().all():
                return None
            j = int(d.values.argmin())
            return j if d.iloc[j] <= pd.Timedelta(days=tol_days) else None
        except Exception:
            return None

    @staticmethod
    def _growth_by_date(df_out, col: str, months: int, tol_days: int = 20):
        """v0100:成長率依期末日往回找 months 個月前那一期(±tol_days);找不到就留空,不拿相鄰列頂替。"""
        pe = pd.to_datetime(df_out["period_end"], errors="coerce")
        vals = []
        for i in range(len(df_out)):
            cur = df_out[col].iloc[i]
            if pd.isna(pe.iloc[i]) or cur is None or pd.isna(cur):
                vals.append(None); continue
            target = pe.iloc[i] - pd.DateOffset(months=months)
            d = (pe - target).abs()
            j = int(d.values.argmin()) if not d.isna().all() else None
            if j is None or j == i or d.iloc[j] > pd.Timedelta(days=tol_days):
                vals.append(None); continue
            prev = df_out[col].iloc[j]
            vals.append(_safe_div(cur, prev, 100) - 100 if (prev not in (None, 0) and not pd.isna(prev)) else None)
        return vals

    @classmethod
    def calc_ratios_per_period(cls, is_df, bs_df, cf_df, freq: Optional[str] = None) -> "pd.DataFrame":
        """對每個 period 算一行比率(v0100:三表依期末日對期;成長率依日期往回找;freq='Quarterly' 另給 qoq)."""
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
                # v0100:依期末日對期(原件用列序 + 取最後一列頂替 —— 配到的常是別一期)
                bs_i = cls._match_period_row(bs_df, period)
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
                cf_i = cls._match_period_row(cf_df, period)   # v0100:依期末日對期
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
        # 成長率 v0100:依期末日往回找一年前那一期(原件取下一列 —— 季表上那是「季增」不是「年增」);季表另給 qoq
        if len(df_out) >= 2 and "period_end" in df_out.columns:
            for c in ["revenue", "operating_income", "net_income"]:
                if c in df_out.columns:
                    df_out[f"{c}_yoy_pct"] = cls._growth_by_date(df_out, c, 12)
                    if freq == "Quarterly":
                        df_out[f"{c}_qoq_pct"] = cls._growth_by_date(df_out, c, 3)
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
            "div_yield_pct":         _div_yield_pct(info),   # v0100:原件把已是百分數的 dividendYield 再 ×100(0.45% → 45%)
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

        # v0100:報表幣別 ≠ 報價幣別(例:TSM 報表 TWD、ADR 報價 USD)→ 報表值 ÷ 股數 ÷ 報價 的欄留空,不直接相除
        fc, qc = cross_currency(info)
        out["financial_currency"] = fc
        out["quote_currency"] = qc
        if fc and qc and fc != qc:
            for k in ("sales_per_share", "cfps", "fcfps", "fcf_yield_pct"):
                if k in out:
                    out[k] = None
            out["currency_note"] = f"報表幣別 {fc} ≠ 報價幣別 {qc}:跨幣別的每股與殖利率欄留空"
        else:
            out["currency_note"] = None
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
            "eps_basis":  "constant(info forwardEps/trailingEps 單一值;帶狀線是水平線,不是逐期本益比)",   # v0100 講明
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
            "bvps_basis": "constant(info bookValue 單一值;帶狀線是水平線,不是逐期淨值比)",   # v0100 講明
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
                    yf_t = _tw_roster_yf(t)   # v0100:依樹上台股名冊決定 .TW / .TWO(原件一律 .TW)
                    if not yf_t:
                        yf_t = f"{t}.TW"
                        print(f"   ⚪ {t} 不在台股名冊,暫以 {yf_t} 抓;上櫃股請直接寫 {t}.TWO")
                    rows.append({"ticker": t, "yf_ticker": yf_t, "name": t,
                                 "market": "TPEX" if yf_t.endswith(".TWO") else "TWSE"})
                elif t.endswith(".TWO") or t.endswith(".TW"):
                    rows.append({"ticker": t.split(".")[0], "yf_ticker": t, "name": t,
                                 "market": "TPEX" if t.endswith(".TWO") else "TWSE"})
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
                print("❌ Universe 空, 中止"); return 2   # v0100:宇宙空=NODATA(上游 MDL005 已退役、宇宙檔不在;原件回 1)

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
                        data.get("is_annual"), data.get("bs_annual"), data.get("cf_annual"), freq="Annual")
                    if df_a is not None and not df_a.empty:
                        df_a["ticker"] = raw_t; df_a["name"] = name; df_a["freq"] = "Annual"
                        ra_rows.append(df_a)
                # Quarterly
                if ENABLE_QUARTERLY:
                    df_q = RatioAnalyzer.calc_ratios_per_period(
                        data.get("is_quarterly"), data.get("bs_quarterly"), data.get("cf_quarterly"), freq="Quarterly")
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

                    # PB Band(v0100:報表幣別 ≠ 報價幣別時 bookValue 與價格不同幣,不畫)
                    _fc, _qc = cross_currency(info)
                    if _fc and _qc and _fc != _qc:
                        print(f"   ⚪ {raw_t} PB band 略過:淨值 {_fc} 與報價 {_qc} 不同幣")
                    elif bvps and bvps > 0:
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


# ===== [VIA:GOVERNED-ENTRY:v0100] 同意閘 · 誠實多態入口(側線 2026-09-23;先例 VDF_MDL004 v0100 main_governed)=====
# 原邏輯一行未改,只加一扇門:閘一(VIA_NET_CONSENT)委派統包網路工具 gate_state()(抄到函式才算出處 LL316;工具缺席=關,fail-closed;永不代設)
#   閘關 → rc4 GATED 零出網零寫檔 · 跑完零列 → rc2 NODATA(0 列不是成功也不是壞掉)· 缺必要套件 → rc3 ABSENT · 例外 → rc1 RED
def _via_gate1(_consent=None):
    """回 (開否, 說明)。_consent 只給自測模擬「閘關」——不讀也不寫任何環境變數。"""
    if _consent is not None:
        return bool(_consent), "自測模擬"
    nt = _via_net()
    if nt is None or not hasattr(nt, "gate_state"):
        return False, "統包網路工具缺席(supportive modules/network/via_net_unified_v*.py → SUP_MDL740)"
    try:
        g = nt.gate_state() or {}
    except Exception as exc:
        return False, "gate_state 例外:" + type(exc).__name__
    return bool(g.get("gate1_net_consent")), "閘一 VIA_NET_CONSENT=" + str(g.get("gate1_raw"))


_VIA_FLAGS = ("--no-parquet", "--no-duckdb", "--no-csv", "--no-charts", "--json", "--no-pause", "--selftest", "--self-test")
_VIA_VALUE_FLAGS = ("--tickers", "--max", "--period")
_VIA_USAGE = """用法(v0100):
  python VDF_MDL006_FinancialModel_v0100.py [--tickers 2330,3324,NVDA] [--max N] [--period 5y]
       [--no-parquet] [--no-duckdb] [--no-csv] [--no-charts] [--json] [--no-pause]    要閘一;閘關 rc4 零出網
  ... --selftest      零連線零寫檔結構自測
  ... --help | -h     只印這段
rc:0 有料 · 2 零列 NODATA · 3 缺必要套件 · 4 閘關 GATED · 1 例外或未知旗標"""


def _via_argv_check(argv):
    """v0100:None = 要看用法;[] = 全認得;[...] = 不認得的旗標(原件對任何旗標都當成整條管線真跑)。"""
    argv = list(argv or [])
    if any(a in ("-h", "--help") for a in argv):
        return None
    bad, skip = [], False
    for a in argv:
        if skip:
            skip = False
            continue
        if a in _VIA_VALUE_FLAGS:
            skip = True
            continue
        if a not in _VIA_FLAGS:
            bad.append(a)
    return bad


def _via_interactive() -> bool:
    """v0100:結尾等 Enter 只在互動終端。"""
    try:
        return bool(sys.stdin is not None and sys.stdin.isatty())
    except Exception:
        return False


def main_governed(_consent=None) -> int:
    ok, why = _via_gate1(_consent)
    if not ok:
        print("  [GATED] 同意閘未開 —— 這不是壞掉(" + why + ")。本引擎要觸網(yfinance:三大報表 · 價格史);零出網、零寫檔。")
        print("  開閘是操作員的手(本視窗):$env:VIA_NET_CONSENT='YES'")
        return 4
    print("🚀 VDF MDL006 · Financial Model 啟動...(治理入口 v0100)")
    eng = FinancialModelEngine()
    rc = eng.run()
    # 量列數,不信 fetcher 的 ok:實測斷網時它報 ok=3 / fail=0,七張表卻全是 0 列(原件把「沒例外」算成「抓到」)
    tabs = ("daily_history_all", "is_annual_all", "is_quarterly_all", "bs_annual_all", "bs_quarterly_all", "cf_annual_all", "cf_quarterly_all")
    rows = sum(len(getattr(eng, a)) for a in tabs if getattr(eng, a, None) is not None)
    ok_n = int(((getattr(getattr(eng, "yf_fetcher", None), "stats", None) or {}).get("ok")) or 0)
    if rc == 0 and rows == 0:
        print("  [NODATA] 價格史與三大報表 0 列(fetcher 自報 ok=" + str(ok_n) + ",那是『沒例外』不是『抓到』)—— 不是成功也不是壞掉;表是空殼")
        return 2
    return rc
# ===== [VIA:GOVERNED-ENTRY:END] =====


# ===== [VIA:SELFTEST-VERB:v0100] L53 自測動詞統一律(側線 2026-09-23 補進 MDL006:原件沒有 --selftest,旗標被略過→整條管線真跑)=====
# 本段**零連線、零寫檔、不呼叫 main()**:只驗結構。
# rc 誠實多態:0=GREEN · 1=RED · 2=NODATA(套件缺席不是壞掉) · 3=ABSENT
_VIA_ST_NEED = ['main', 'FinancialModelEngine', 'YFinanceFinancialFetcher', 'RatioAnalyzer', 'ValuationAnalyzer', 'OutputManager', 'main_governed', '_div_yield_pct', 'cross_currency', '_via_argv_check']


def _via_selftest() -> int:
    import os as _o, socket as _sk
    g = globals()
    okn = []; bad = []; nod = []

    def chk(n, c, why=""):
        (okn if c else bad).append(n)
        print(("  \u2713 " + n) if c else "  [FAIL] {} \u2014 {}".format(n, why))

    print("\U0001f9ea {} --selftest(L53 \u52d5\u8a5e\uff1b\u7d50\u69cb\u6aa2\uff0c\u96f6\u9023\u7dda)".format(_o.path.basename(__file__)))
    try:
        src = _o.path.abspath(__file__)
        text = open(src, encoding="utf-8", errors="replace").read()
    except Exception as e:
        print("  [FAIL] \u8b80\u4e0d\u5230\u672c\u6a94\u539f\u59cb\u78bc \u2014 {}".format(e))
        return 1

    # \u2462 \u96f6\u9023\u7dda\u5be6\u8b49:\u6aa2\u671f\u9593\u4efb\u4f55 connect \u90fd\u88ab\u651c\u4e0b\u4f86
    hit = []
    _orig = _sk.socket.connect

    def _blocked(self, *a, **k):
        hit.append(a[0] if a else "?")
        raise OSError("VIA selftest: \u96f6\u9023\u7dda\u95d8\u651c\u622a")

    _sk.socket.connect = _blocked
    try:
        chk("\u2460 \u6a21\u7d44\u8f09\u5165\u7121\u4f8b\u5916", True)
        miss = [n for n in _VIA_ST_NEED if g.get(n) is None]
        chk("\u2461 \u5ba3\u544a\u7b26\u865f\u9f4a\u5099({} \u500b)".format(len(_VIA_ST_NEED)), not miss, "\u7f3a {}".format(miss))
        i_st = text.find("[VIA:SELFTEST-VERB:v0100]")
        i_mn = text.rfind('if __name__ == "__main__":')
        chk("\u2463 \u52d5\u8a5e\u8def\u7531\u5728 main \u4e4b\u524d", 0 <= i_st < i_mn, "selftest \u6bb5 @{} \u4e0d\u5728 main \u5b88\u885b @{} \u4e4b\u524d".format(i_st, i_mn))
        chk("\u2464 \u6a4b\u63a5\u4ef6\u5b8c\u597d(ACCEL/NET)",
            ("[VIA:ACCEL-BRIDGE:" in text) and ("[VIA:NET-BRIDGE:" in text), "\u6a94\u982d\u6a4b\u6a19\u8a18\u4e0d\u5168")
    finally:
        _sk.socket.connect = _orig
    chk("\u2462 \u96f6\u9023\u7dda\u5be6\u8b49", not hit, "\u81ea\u6e2c\u671f\u9593\u5617\u8a66\u9023\u7dda {}".format(hit[:2]))

    # \u2465 \u5957\u4ef6\u65d7\u6a19\u76e4\u9ede:\u7f3a\u4ef6 = NODATA\uff0c\u4e0d\u662f\u7d05\u71c8
    flags = sorted(k for k in g if k.endswith("_AVAILABLE"))
    off = [k for k in flags if not g.get(k)]
    if flags:
        print("  \u25b8 \u5957\u4ef6\u65d7\u6a19 {}/{} \u5230\u4f4d{}".format(len(flags) - len(off), len(flags),
              ("\uff1b\u7f3a " + ", ".join(off)) if off else ""))
    if off:
        nod.append("\u2465")
    print("  \u2465 \u5957\u4ef6\u65d7\u6a19\u76e4\u9ede \u2014 {}".format("NODATA(\u7f3a\u4ef6\u4e0d\u662f\u58de\u6389)" if off else "\u5168\u5230\u4f4d"))

    # ⑦ v0100:同意閘關 → 治理入口回 rc4 GATED(零連線 · 零寫檔 · 不代設;以參數模擬閘關,不讀寫任何環境變數)
    hit7 = []
    _o7 = _sk.socket.connect

    def _b7(self, *a, **k):
        hit7.append(a[0] if a else "?")
        raise OSError("VIA selftest ⑦:零連線閘攔截")

    _sk.socket.connect = _b7
    try:
        import io as _io7, contextlib as _cl7
        with _cl7.redirect_stdout(_io7.StringIO()):
            rc7 = main_governed(_consent=False)
    except Exception as e7:
        rc7 = "例外 " + type(e7).__name__
    finally:
        _sk.socket.connect = _o7
    chk("⑦ 同意閘關 → main_governed 回 rc4 GATED(零連線 · 零寫檔 · 不代設)", rc7 == 4 and not hit7, "rc {} · 連線 {}".format(rc7, hit7[:2]))
    # ⑧ v0100:純函數(零連線;合成數字)——安全除法與安全轉型是比率/估值每一格的地基
    try:
        ok8 = (_safe_div(1, 0) is None and _safe_div(3, 2, 100.0) == 150.0 and _safe_div("x", 2) is None
               and _safe_float("1.5") == 1.5 and _safe_float(None) is None and _safe_float("abc") is None)
    except Exception:
        ok8 = False
    chk("⑧ 純函數:_safe_div 除零/非數回 None、3/2×100=150;_safe_float 非數回 None", ok8)

    if pd is None:
        nod.extend(["⑨", "⑩", "⑭"])
        print("  ⑨ ⑩ ⑭ — NODATA(pandas 不在,無法跑合成報表)")
    else:
        # ⑨ 三表依期末日對期(合成:損益 3 期,資產負債缺中間那期)
        try:
            is9 = pd.DataFrame({"period_end": pd.to_datetime(["2024-12-31", "2023-12-31", "2022-12-31"]),
                                "Total Revenue": [300.0, 200.0, 100.0], "Net Income": [30.0, 20.0, 10.0]})
            bs9 = pd.DataFrame({"period_end": pd.to_datetime(["2024-12-31", "2022-12-31"]),
                                "Stockholders Equity": [150.0, 50.0]})
            r9 = RatioAnalyzer.calc_ratios_per_period(is9, bs9, None, freq="Annual")
            roe = list(r9["roe_pct"])
            # 負控:原件列序配對 —— 2023 期會配到 bs9 第 1 列(2022 的 50)→ ROE 40%,不是「沒有資產負債表」
            legacy_2023 = 20.0 / float(bs9["Stockholders Equity"].iloc[min(1, len(bs9) - 1)]) * 100
            chk("⑨ 三表依期末日對期:2024 ROE 20% · 2023 缺表留空 · 2022 ROE 20%(負控:列序配對給 2023 一個 40%)",
                abs(roe[0] - 20.0) < 1e-9 and (roe[1] is None or pd.isna(roe[1])) and abs(roe[2] - 20.0) < 1e-9 and abs(legacy_2023 - 40.0) < 1e-9,
                "roe {} legacy {}".format(roe, legacy_2023))
        except Exception as e9:
            chk("⑨ 三表依期末日對期", False, "例外 " + type(e9).__name__ + ": " + str(e9)[:80])
        # ⑩ 季表年增 = 四季前那一期;季增另給
        try:
            q10 = pd.DataFrame({"period_end": pd.to_datetime(["2025-03-31", "2024-12-31", "2024-09-30", "2024-06-30", "2024-03-31"]),
                                "Total Revenue": [200.0, 130.0, 120.0, 110.0, 100.0]})
            r10 = RatioAnalyzer.calc_ratios_per_period(q10, None, None, freq="Quarterly")
            y0 = r10["revenue_yoy_pct"].iloc[0]; q0 = r10["revenue_qoq_pct"].iloc[0]; y4 = r10["revenue_yoy_pct"].iloc[4]
            chk("⑩ 季表年增 = 四季前(200/100 → 100%)· 季增另欄(200/130)· 最舊一期沒有一年前 → 留空",
                abs(y0 - 100.0) < 1e-9 and abs(q0 - (200 / 130 - 1) * 100) < 1e-9 and (y4 is None or pd.isna(y4)),
                "yoy0 {} qoq0 {} yoy4 {}".format(y0, q0, y4))
        except Exception as e10:
            chk("⑩ 季表年增", False, "例外 " + type(e10).__name__ + ": " + str(e10)[:80])

    # ⑪ 殖利率單位(純函數)
    d1 = _div_yield_pct({"dividendRate": 2.0, "currentPrice": 100.0, "dividendYield": 2.0})
    d2 = _div_yield_pct({"trailingAnnualDividendYield": 0.02})
    d3 = _div_yield_pct({"dividendYield": 0.45})
    chk("⑪ 殖利率:dividendRate÷現價 2% · 小數欄 ×100 · dividendYield 已是百分數不再 ×100(原件 0.45 → 45)",
        abs(d1 - 2.0) < 1e-9 and abs(d2 - 2.0) < 1e-9 and abs(d3 - 0.45) < 1e-9, "{} {} {}".format(d1, d2, d3))

    # ⑫ 報表幣別 ≠ 報價幣別 → 跨幣別欄留空(正控)· 同幣照算(負控)
    lr = {"revenue": 1000.0, "ocf": 200.0, "fcf": 100.0}
    v_x = ValuationAnalyzer.calc_valuation({"financialCurrency": "TWD", "currency": "USD", "sharesOutstanding": 10.0, "currentPrice": 50.0}, lr, None)
    v_s = ValuationAnalyzer.calc_valuation({"financialCurrency": "USD", "currency": "USD", "sharesOutstanding": 10.0, "currentPrice": 50.0}, lr, None)
    chk("⑫ 幣別不一致 → 每股/FCF 殖利率留空並註明(同幣照算:FCF 殖利率 20%)",
        v_x.get("fcfps") is None and v_x.get("fcf_yield_pct") is None and bool(v_x.get("currency_note"))
        and abs((v_s.get("fcf_yield_pct") or 0) - 20.0) < 1e-9 and v_s.get("currency_note") is None,
        "x {} / s {}".format(v_x.get("fcf_yield_pct"), v_s.get("fcf_yield_pct")))

    # ⑬ 旗標:--help=用法 · 未知旗標點名 · 帶值旗標的值不算未知
    a_h = _via_argv_check(["--help"]); a_b = _via_argv_check(["--ticker", "2330"]); a_o = _via_argv_check(["--tickers", "2330,3324", "--max", "3", "--no-pause"])
    chk("⑬ --help=用法 · 未知旗標點名 · --tickers/--max 的值不算未知", a_h is None and a_b == ["--ticker", "2330"] and a_o == [],
        "help {} bad {} ok {}".format(a_h, a_b, a_o))

    # ⑭ 有料才算 ok:以假 yf(每個報表都空)跑 _fetch_one —— 要記 fail,不是 ok
    if pd is not None:
        class _E:
            def history(self, **k): return pd.DataFrame()
            info = {}
            income_stmt = balance_sheet = cashflow = pd.DataFrame()
            quarterly_income_stmt = quarterly_balance_sheet = quarterly_cashflow = pd.DataFrame()
        class _Y:
            def Ticker(self, t): return _E()
        g_yf, g_av = g.get("yf"), g.get("YFINANCE_AVAILABLE")
        try:
            g["yf"] = _Y(); g["YFINANCE_AVAILABLE"] = True
            f14 = YFinanceFinancialFetcher()
            o14 = f14._fetch_one("ZZZZ")
            chk("⑭ 六表與價格史全空 → fail 1 / ok 0(原件 ok+=1)", f14.stats["ok"] == 0 and f14.stats["fail"] == 1 and bool(o14.get("_error")),
                "stats {}".format({k: f14.stats[k] for k in ("ok", "fail")}))
        except Exception as e14:
            chk("⑭ 有料才算 ok", False, "例外 " + type(e14).__name__ + ": " + str(e14)[:80])
        finally:
            g["yf"] = g_yf; g["YFINANCE_AVAILABLE"] = g_av

    rc = 1 if bad else (2 if nod else 0)
    print("[\u8a08] OK {} \u00b7 FAIL {} \u00b7 NODATA {} \u2192 rc={} ({})".format(
        len(okn), len(bad), len(nod), rc, {0: "GREEN", 1: "RED", 2: "NODATA"}[rc]))
    return rc


if __name__ == "__main__":
    import sys as _via_st_sys
    if ("--selftest" in _via_st_sys.argv) or ("--self-test" in _via_st_sys.argv):
        _via_st_sys.exit(_via_selftest())
# ===== [VIA:SELFTEST-VERB:END] =====

if __name__ == "__main__":
    try:
        _via_bad = _via_argv_check(sys.argv[1:])
        if _via_bad is None:          # v0100:--help 只印用法,不過閘、不觸網
            print(_VIA_USAGE)
            sys.exit(0)
        if _via_bad:                  # v0100:未知旗標不猜
            print("  [ERR] 未知旗標:" + " ".join(_via_bad))
            print(_VIA_USAGE)
            sys.exit(1)
        ec = main_governed()   # v0100:同意閘 · 誠實多態入口
        if "--no-pause" not in sys.argv and _via_interactive():
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
