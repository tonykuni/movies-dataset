#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  VDF_MDL003_SentimentMacroEngine.py
================================================================================
  VERITAS DATA FRAMEWORK - MDL003  Sentiment + Macro Integration Engine
  Version    : 1.0.0   |   Module ID : VDF-MDL003-SME-001
  Asset ID   : VDF-MDL003-CLS-001
  Policy     : 功能只增不減 · append-only · SSOT · LL-compliant
  Lineage    : VRN_MDL013_AKShareFetcher v1.0 + VRN_MDL014_MacroFetcher v1.0
             + VDF_D2_FREDEngine v2 + AAII + CNN Fear&Greed integration

ROLE (高度整合的市場情緒 + 宏觀數據引擎)
================================================================================
  4 條獨立資料管道, 整合成單一統一介面:

    [API-1] AAII Sentiment   (American Association of Individual Investors)
            - 每週發布散戶 Bullish / Bearish / Neutral 三方比例
            - 用途: 散戶情緒指標 (反向指標, 極端值出現時常見市場反轉)
            - 來源: aaii.com/sentimentsurvey + 內建快取 CSV
            - 欄位: date, bullish, neutral, bearish, bull_bear_spread, 8w_ma

    [API-2] CNN Fear & Greed Index
            - 每日 0-100 綜合恐慌貪婪指數 + 7 個子指標
            - 子指標: stock_price_strength, market_momentum, stock_price_breadth,
                      put_call_options, junk_bond_demand, market_volatility,
                      safe_haven_demand
            - 用途: 大盤情緒水溫計 (0=極度恐慌, 100=極度貪婪)
            - 來源: production.dataviz.cnn.io/index/fearandgreed/graphdata

    [API-3] FRED (Federal Reserve Economic Data) - 50+ key series
            - 利率/通膨/就業/GDP/信用/外匯/PMI 等聖經級宏觀指標
            - API Key: 2d5ae8dfe834ffc409bf98d51f539c17 (內建)
            - 用途: 宏觀基本面 + 利率/通膨/景氣循環判定
            - 來源: api.stlouisfed.org/fred/series/observations

    [API-4] AKShare CN Futures + Macro
            - 中國期貨連續合約 (滬銅 CU0, 螺紋鋼 RB0, 鐵礦石 I0 等)
            - 中國 PMI / M2 / 工業增加值
            - BDI 散裝航運指數
            - 用途: 中國需求側驗證 (台股鋼鐵/航運/原物料前瞻)
            - 來源: akshare Python lib

ARCHITECTURE (與 MDL001/MDL002 同架構)
================================================================================
  [1] ALL PARAMETERS ON THE TOP
  [2] 4 個獨立 Fetcher 類別 (AAIIFetcher, CNNFearGreedFetcher, FREDFetcher, AKShareFetcher)
  [3] 統一 OutputManager (Parquet 必選 + DuckDB + CSV + JSON + Google Sheet)
  [4] SSOT registry (FRED_REGISTRY / AKSHARE_REGISTRY 內嵌)
  [5] ThreadPoolExecutor 並發抓 (4 條管道並行)
  [6] Rich Summary Matrix (8+ 表 + Panel)
  [7] CLI flags: --aaii / --cnn / --fred / --akshare / --all (default)
                 --no-parquet / --no-duckdb / --no-csv / --no-json / --gsheet
  [8] 互動式選單 (--menu)

USAGE
================================================================================
  python VDF_MDL003_SentimentMacroEngine.py                  # 4 條都跑
  python VDF_MDL003_SentimentMacroEngine.py --aaii --cnn     # 只跑情緒
  python VDF_MDL003_SentimentMacroEngine.py --fred           # 只跑 FRED
  python VDF_MDL003_SentimentMacroEngine.py --menu           # 互動式
  python VDF_MDL003_SentimentMacroEngine.py --no-pause       # 不暫停 (CI/批次)
"""
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

# =====================================================================================
# 📋 ALL PARAMETERS CONFIGURATION SECTION
# =====================================================================================

# 🔧 [PARAM-1/10] 基本設定
PROJECT_NAME = "1-4-SentimentMacro"
BASE_DIR     = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VDF\dict"
OUTPUT_DIR   = "1-4-SentimentMacro"

# 🔑 [PARAM-2/10] API Keys (FRED 必填)
FRED_API_KEY = "2d5ae8dfe834ffc409bf98d51f539c17"   # 使用者提供
# AAII 不需 key (公開頁面 scrape)
# CNN 不需 key (公開 dataviz API)
# AKShare 不需 key (Python lib 直連)

# 📅 [PARAM-3/10] 時間設定
START_DATE              = "2018-01-01"
END_DATE                = ""    # 空 = today
USE_CURRENT_DATE_AS_END = True
AAII_START_DATE         = "2018-01-01"
CNN_LOOKBACK_DAYS       = 365 * 6   # CNN F&G 只回溯到指定天數 (節點)

# 🌐 [PARAM-4/10] 網路設定 (加速 + 容錯)
HTTP_TIMEOUT      = 30
MAX_RETRIES       = 3
RETRY_DELAY       = 2
ENABLE_THREADPOOL = True
THREADPOOL_WORKERS = 4    # 4 條管道並發
HTTP_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/120.0.0.0 Safari/537.36"),
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "en-US,en;q=0.9,zh-TW;q=0.8",
}

# 📁 [PARAM-5/10] 輸出格式 (Parquet 必選, 其他可選)
OUTPUT_PARQUET   = True   # 必選, 不能關 (Parquet 是主要 SSOT)
OUTPUT_DUCKDB    = True   # 可選 (產生 .duckdb 單一檔案資料庫)
OUTPUT_CSV       = True   # 可選 (utf-8-sig 解決中文 BOM)
OUTPUT_JSON      = True   # 可選 (人類可讀, 適合 debug)
OUTPUT_GSHEET    = False  # 可選 (需 gspread + service account 憑證, 預設關)

CSV_ENCODING     = "utf-8-sig"
JSON_INDENT      = 2
DUCKDB_FILENAME  = "VDF_MDL003_SentimentMacro.duckdb"
GSHEET_CREDENTIAL_PATH = ""   # 留空 = 不嘗試 (要求使用者自填)
GSHEET_SPREADSHEET_ID  = ""

# 🎛️ [PARAM-6/10] 處理設定
ENABLE_BACKUP    = True
MAX_BACKUP_FILES = 5
AUTO_DEDUPLICATE = True
VALIDATE_DATA    = True
LOG_LEVEL        = "INFO"

# 🔌 [PARAM-7/10] API 開關 (CLI flags 可覆蓋)
ENABLE_AAII      = True
ENABLE_CNN       = True
ENABLE_FRED      = True
ENABLE_AKSHARE   = True

# 📊 [PARAM-8/10] FRED Registry (50+ 聖經級宏觀指標)
# 結構: via_code → {fred_id, indicator, theme, sub_theme, unit, freq, transform}
# transform: None / "yoy" / "mom" / "level"
FRED_REGISTRY = {
    # ── (1) 利率政策 / Rates ────────────────────────────────────────
    "US.Rates.Fed.Target_Upper": {"fred_id": "DFEDTARU",  "indicator": "Fed Funds Target Upper",
                                  "theme": "Rates", "sub_theme": "Policy", "unit": "%", "freq": "D"},
    "US.Rates.Fed.Target_Lower": {"fred_id": "DFEDTARL",  "indicator": "Fed Funds Target Lower",
                                  "theme": "Rates", "sub_theme": "Policy", "unit": "%", "freq": "D"},
    "US.Rates.Fed.Effective":    {"fred_id": "DFF",       "indicator": "Effective Fed Funds Rate",
                                  "theme": "Rates", "sub_theme": "Policy", "unit": "%", "freq": "D"},
    "US.Rates.SOFR":             {"fred_id": "SOFR",      "indicator": "SOFR",
                                  "theme": "Rates", "sub_theme": "Money", "unit": "%", "freq": "D"},
    "US.Rates.Treasury.2Y":      {"fred_id": "DGS2",      "indicator": "2Y Treasury",
                                  "theme": "Rates", "sub_theme": "Curve", "unit": "%", "freq": "D"},
    "US.Rates.Treasury.5Y":      {"fred_id": "DGS5",      "indicator": "5Y Treasury",
                                  "theme": "Rates", "sub_theme": "Curve", "unit": "%", "freq": "D"},
    "US.Rates.Treasury.10Y":     {"fred_id": "DGS10",     "indicator": "10Y Treasury",
                                  "theme": "Rates", "sub_theme": "Curve", "unit": "%", "freq": "D"},
    "US.Rates.Treasury.30Y":     {"fred_id": "DGS30",     "indicator": "30Y Treasury",
                                  "theme": "Rates", "sub_theme": "Curve", "unit": "%", "freq": "D"},
    "US.Rates.Spread.2s10s":     {"fred_id": "T10Y2Y",    "indicator": "10Y-2Y Spread",
                                  "theme": "Rates", "sub_theme": "Spread", "unit": "pp", "freq": "D"},
    "US.Rates.Spread.10Y3M":     {"fred_id": "T10Y3M",    "indicator": "10Y-3M Spread (NY Fed recession)",
                                  "theme": "Rates", "sub_theme": "Spread", "unit": "pp", "freq": "D"},
    "US.Rates.RealRate.10Y":     {"fred_id": "DFII10",    "indicator": "10Y TIPS Real Yield",
                                  "theme": "Rates", "sub_theme": "Real", "unit": "%", "freq": "D"},
    "US.Rates.BreakEven.10Y":    {"fred_id": "T10YIE",    "indicator": "10Y Break-even Inflation",
                                  "theme": "Rates", "sub_theme": "Inflation Expectation", "unit": "%", "freq": "D"},
    # ── (2) 通膨 / Inflation ────────────────────────────────────────
    "US.Prices.CPI.Headline":    {"fred_id": "CPIAUCSL",  "indicator": "Headline CPI",
                                  "theme": "Inflation", "sub_theme": "CPI", "unit": "Index", "freq": "M", "transform": "yoy"},
    "US.Prices.CPI.Core":        {"fred_id": "CPILFESL",  "indicator": "Core CPI",
                                  "theme": "Inflation", "sub_theme": "CPI", "unit": "Index", "freq": "M", "transform": "yoy"},
    "US.Prices.PCE.Headline":    {"fred_id": "PCEPI",     "indicator": "Headline PCE",
                                  "theme": "Inflation", "sub_theme": "PCE", "unit": "Index", "freq": "M", "transform": "yoy"},
    "US.Prices.PCE.Core":        {"fred_id": "PCEPILFE",  "indicator": "Core PCE (Fed target)",
                                  "theme": "Inflation", "sub_theme": "PCE", "unit": "Index", "freq": "M", "transform": "yoy"},
    "US.Prices.PPI":             {"fred_id": "PPIACO",    "indicator": "PPI All Commodities",
                                  "theme": "Inflation", "sub_theme": "PPI", "unit": "Index", "freq": "M", "transform": "yoy"},
    "US.Prices.UMich.5Y":        {"fred_id": "MICH",      "indicator": "UMich 5Y Inflation Expectation",
                                  "theme": "Inflation", "sub_theme": "Expectation", "unit": "%", "freq": "M"},
    # ── (3) 就業 / Employment ──────────────────────────────────────
    "US.Employ.Payrolls":        {"fred_id": "PAYEMS",    "indicator": "Nonfarm Payrolls",
                                  "theme": "Employment", "sub_theme": "Payrolls", "unit": "Thousands", "freq": "M", "transform": "mom"},
    "US.Employ.UnemploymentRate":{"fred_id": "UNRATE",    "indicator": "Unemployment Rate",
                                  "theme": "Employment", "sub_theme": "Rate", "unit": "%", "freq": "M"},
    "US.Employ.LFPR":            {"fred_id": "CIVPART",   "indicator": "Labor Force Participation",
                                  "theme": "Employment", "sub_theme": "Rate", "unit": "%", "freq": "M"},
    "US.Employ.AvgHourly":       {"fred_id": "CES0500000003", "indicator": "Avg Hourly Earnings",
                                  "theme": "Employment", "sub_theme": "Wage", "unit": "USD/hr", "freq": "M", "transform": "yoy"},
    "US.Employ.JobOpenings":     {"fred_id": "JTSJOL",    "indicator": "JOLTS Job Openings",
                                  "theme": "Employment", "sub_theme": "Demand", "unit": "Thousands", "freq": "M"},
    "US.Employ.InitialClaims":   {"fred_id": "ICSA",      "indicator": "Initial Jobless Claims",
                                  "theme": "Employment", "sub_theme": "Claims", "unit": "Persons", "freq": "W"},
    # ── (4) 產出 / Growth ──────────────────────────────────────────
    "US.Growth.GDP":             {"fred_id": "GDP",        "indicator": "Nominal GDP",
                                  "theme": "Growth", "sub_theme": "GDP", "unit": "B USD", "freq": "Q"},
    "US.Growth.RealGDP":         {"fred_id": "GDPC1",      "indicator": "Real GDP",
                                  "theme": "Growth", "sub_theme": "GDP", "unit": "B 2017 USD", "freq": "Q", "transform": "yoy"},
    "US.Growth.IndProd":         {"fred_id": "INDPRO",     "indicator": "Industrial Production",
                                  "theme": "Growth", "sub_theme": "Industry", "unit": "Index", "freq": "M", "transform": "yoy"},
    "US.Growth.CapUtil":         {"fred_id": "TCU",        "indicator": "Capacity Utilization",
                                  "theme": "Growth", "sub_theme": "Industry", "unit": "%", "freq": "M"},
    "US.Growth.RetailSales":     {"fred_id": "RSAFS",      "indicator": "Retail Sales",
                                  "theme": "Growth", "sub_theme": "Consumer", "unit": "M USD", "freq": "M", "transform": "yoy"},
    # ── (5) 信用利差 / Credit ───────────────────────────────────────
    "US.Credit.HY.OAS":          {"fred_id": "BAMLH0A0HYM2",  "indicator": "HY OAS Spread",
                                  "theme": "Credit", "sub_theme": "HY", "unit": "%", "freq": "D"},
    "US.Credit.IG.OAS":          {"fred_id": "BAMLC0A0CM",    "indicator": "IG OAS Spread",
                                  "theme": "Credit", "sub_theme": "IG", "unit": "%", "freq": "D"},
    "US.Credit.CCC":             {"fred_id": "BAMLH0A3HYC",   "indicator": "CCC & Lower OAS",
                                  "theme": "Credit", "sub_theme": "HY", "unit": "%", "freq": "D"},
    # ── (6) 央行 / Fed Balance Sheet ────────────────────────────────
    "US.Fed.BalanceSheet":       {"fred_id": "WALCL",      "indicator": "Fed Total Assets (QE/QT)",
                                  "theme": "Fed", "sub_theme": "BalanceSheet", "unit": "M USD", "freq": "W"},
    "US.Fed.ReserveBalance":     {"fred_id": "WRESBAL",    "indicator": "Reserve Balances",
                                  "theme": "Fed", "sub_theme": "Reserve", "unit": "M USD", "freq": "W"},
    # ── (7) 金融狀況 / Financial Conditions ─────────────────────────
    "US.FinCond.ChicagoFCI":     {"fred_id": "NFCI",       "indicator": "Chicago Fed NFCI",
                                  "theme": "FinCond", "sub_theme": "Index", "unit": "Index", "freq": "W"},
    "US.FinCond.STLFSI":         {"fred_id": "STLFSI4",    "indicator": "St. Louis Fed FSI",
                                  "theme": "FinCond", "sub_theme": "Index", "unit": "Index", "freq": "W"},
    "US.FinCond.MoveIndex":      {"fred_id": "BAMLH0A0HYM2",  "indicator": "MOVE Volatility (proxy)",
                                  "theme": "FinCond", "sub_theme": "Volatility", "unit": "Index", "freq": "D"},
    # ── (8) 外匯 / FX ───────────────────────────────────────────────
    "US.Trade.DXY":              {"fred_id": "DTWEXBGS",   "indicator": "USD Broad Index (DXY proxy)",
                                  "theme": "FX", "sub_theme": "USD", "unit": "Index", "freq": "D"},
    # ── (9) 房地產 / Housing ─────────────────────────────────────────
    "US.Housing.CaseShiller":    {"fred_id": "CSUSHPISA",  "indicator": "Case-Shiller National Home Price",
                                  "theme": "Housing", "sub_theme": "Price", "unit": "Index", "freq": "M", "transform": "yoy"},
    "US.Housing.Starts":         {"fred_id": "HOUST",      "indicator": "Housing Starts",
                                  "theme": "Housing", "sub_theme": "Activity", "unit": "Thousands", "freq": "M"},
    "US.Housing.MortgageRate30Y":{"fred_id": "MORTGAGE30US", "indicator": "30Y Mortgage Rate",
                                  "theme": "Housing", "sub_theme": "Rate", "unit": "%", "freq": "W"},
    # ── (10) 商品 / Commodities ─────────────────────────────────────
    "US.Commodity.WTI":          {"fred_id": "DCOILWTICO", "indicator": "WTI Crude Oil Spot",
                                  "theme": "Commodity", "sub_theme": "Energy", "unit": "USD/bbl", "freq": "D"},
    "US.Commodity.Brent":        {"fred_id": "DCOILBRENTEU", "indicator": "Brent Crude Oil",
                                  "theme": "Commodity", "sub_theme": "Energy", "unit": "USD/bbl", "freq": "D"},
    "US.Commodity.NatGas":       {"fred_id": "DHHNGSP",    "indicator": "Henry Hub Natural Gas",
                                  "theme": "Commodity", "sub_theme": "Energy", "unit": "USD/MMBtu", "freq": "D"},
    "US.Commodity.Gold":         {"fred_id": "GOLDAMGBD228NLBM", "indicator": "Gold London AM Fix",
                                  "theme": "Commodity", "sub_theme": "Precious", "unit": "USD/oz", "freq": "D"},
    # ── (11) 中國 / China ────────────────────────────────────────────
    "CN.PMI.Manufacturing":      {"fred_id": "CHNMFGPMI",  "indicator": "China NBS Manufacturing PMI",
                                  "theme": "Global", "sub_theme": "China", "unit": "Index", "freq": "M"},
    "CN.GDP.YoY":                {"fred_id": "MKTGDPCNA646NWDB", "indicator": "China GDP",
                                  "theme": "Global", "sub_theme": "China", "unit": "B USD", "freq": "A"},
}

# 📊 [PARAM-9/10] AKShare Registry (CN 期貨 + 宏觀)
AKSHARE_REGISTRY = {
    # ── CN 期貨連續 ────────────────────────────────────────────────
    "cn_copper_continuous":  {"name": "滬銅連續 CU0",    "func": "futures_main_sina", "sym": "CU0",
                              "theme": "Futures", "sub_theme": "Base Metal"},
    "cn_aluminum":           {"name": "滬鋁連續 AL0",    "func": "futures_main_sina", "sym": "AL0",
                              "theme": "Futures", "sub_theme": "Base Metal"},
    "cn_zinc":               {"name": "滬鋅連續 ZN0",    "func": "futures_main_sina", "sym": "ZN0",
                              "theme": "Futures", "sub_theme": "Base Metal"},
    "cn_rebar_continuous":   {"name": "螺紋鋼連續 RB0",  "func": "futures_main_sina", "sym": "RB0",
                              "theme": "Futures", "sub_theme": "Steel"},
    "cn_iron_ore":           {"name": "鐵礦石連續 I0",   "func": "futures_main_sina", "sym": "I0",
                              "theme": "Futures", "sub_theme": "Iron Ore"},
    "cn_coking_coal":        {"name": "焦煤連續 JM0",    "func": "futures_main_sina", "sym": "JM0",
                              "theme": "Futures", "sub_theme": "Coal"},
    "cn_gold":               {"name": "滬金連續 AU0",    "func": "futures_main_sina", "sym": "AU0",
                              "theme": "Futures", "sub_theme": "Precious"},
    "cn_silver":             {"name": "滬銀連續 AG0",    "func": "futures_main_sina", "sym": "AG0",
                              "theme": "Futures", "sub_theme": "Precious"},
    "cn_crude_oil":          {"name": "上期所原油 SC0",  "func": "futures_main_sina", "sym": "SC0",
                              "theme": "Futures", "sub_theme": "Energy"},
    # ── 航運 ──────────────────────────────────────────────────────
    "cn_bdi":                {"name": "BDI 散裝航運指數", "func": "shipping_bdi",     "sym": None,
                              "theme": "Shipping", "sub_theme": "Dry Bulk"},
    # ── CN 宏觀 ───────────────────────────────────────────────────
    "cn_pmi_mfg":            {"name": "中國製造業 PMI",   "func": "macro_china_pmi", "sym": None,
                              "theme": "Macro", "sub_theme": "PMI"},
    "cn_pmi_svc":            {"name": "中國非製造業 PMI", "func": "macro_china_non_man_pmi", "sym": None,
                              "theme": "Macro", "sub_theme": "PMI"},
    "cn_m2":                 {"name": "中國 M2 貨幣供給",  "func": "macro_china_m2_yearly", "sym": None,
                              "theme": "Macro", "sub_theme": "Money"},
}

# 🎯 [PARAM-10/10] API endpoint URLs
AAII_URL_SENTIMENT  = "https://www.aaii.com/files/surveys/sentiment.xls"  # 官方歷史 Excel
AAII_URL_FALLBACK   = "https://www.aaii.com/sentimentsurvey/sent_results"  # HTML scrape
CNN_URL_FEAR_GREED  = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
FRED_URL_BASE       = "https://api.stlouisfed.org/fred/series/observations"


# =====================================================================================
# 📦 Imports & dependency check
# =====================================================================================

import os
import io
import re
import sys
import json
import time
import warnings
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings('ignore')

# ── 核心套件 ───────────────────────────────────────────────────────────────
try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    print("❌ pandas/numpy 未安裝")
    PANDAS_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    print("❌ requests 未安裝")
    REQUESTS_AVAILABLE = False

# ── 可選套件 ───────────────────────────────────────────────────────────────
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
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False
    ak = None

try:
    import pandas_datareader.data as pdr
    PDR_AVAILABLE = True
except Exception:
    # pandas_datareader has known incompat issues with newer pandas (TypeError, not ImportError)
    PDR_AVAILABLE = False
    pdr = None

try:
    import openpyxl
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

try:
    import xlrd
    XLRD_AVAILABLE = True
except ImportError:
    XLRD_AVAILABLE = False

try:
    import gspread
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich import box
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    print("⚠️ rich 未安裝, 使用簡化顯示")
    RICH_AVAILABLE = False
    console = None


# =====================================================================================
# 🔧 共用 utilities
# =====================================================================================

def _now_iso() -> str:
    return datetime.now().isoformat(timespec='seconds')


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _end_date() -> str:
    if USE_CURRENT_DATE_AS_END or not END_DATE:
        return _today()
    return END_DATE


def _http_get(url: str, params: Optional[Dict] = None,
              timeout: int = HTTP_TIMEOUT, retries: int = MAX_RETRIES) -> Optional[Any]:
    """Robust HTTP GET with retries."""
    if not REQUESTS_AVAILABLE:
        return None
    last_exc = None
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, headers=HTTP_HEADERS, timeout=timeout)
            if r.ok:
                return r
            else:
                last_exc = f"HTTP {r.status_code}"
        except Exception as e:
            last_exc = str(e)[:120]
        if attempt < retries - 1:
            time.sleep(RETRY_DELAY)
    return None


def _apply_transform(series: "pd.Series", transform: Optional[str]) -> "pd.Series":
    """FRED transform: yoy / mom / level."""
    if transform is None or pd is None:
        return series
    s = pd.to_numeric(series, errors='coerce')
    if transform == "yoy":
        return s.pct_change(12) * 100
    if transform == "mom":
        return s.pct_change(1) * 100
    if transform == "level":
        return s
    return s


# =====================================================================================
# 📈 [API-1] AAIIFetcher  -  American Association of Individual Investors
# =====================================================================================

class AAIIFetcher:
    """
    AAII 散戶情緒週度資料抓取.

    策略 (順序嘗試):
      1. 官方 Excel: aaii.com/files/surveys/sentiment.xls (歷史完整)
      2. HTML scrape: aaii.com/sentimentsurvey/sent_results (僅最新 N 週)
      3. 失敗 → 回傳空 DataFrame 並記錄錯誤

    輸出 schema:
      date · bullish · neutral · bearish · bull_bear_spread · ma8_bullish · source
    """

    VERSION = "1.0.0"

    def __init__(self, start_date: str = AAII_START_DATE):
        self.start_date = start_date
        self.stats = {"rows": 0, "method": None, "errors": []}

    def _try_excel(self) -> Optional["pd.DataFrame"]:
        """嘗試 1: 官方 Excel."""
        if pd is None:
            return None
        r = _http_get(AAII_URL_SENTIMENT)
        if r is None:
            self.stats["errors"].append("AAII Excel: HTTP failed")
            return None
        if not (OPENPYXL_AVAILABLE or XLRD_AVAILABLE):
            self.stats["errors"].append("AAII Excel: openpyxl/xlrd not installed")
            return None
        try:
            # AAII Excel 有奇怪 header, 先 read 全部找有效起始列
            buf = io.BytesIO(r.content)
            try:
                df_raw = pd.read_excel(buf, sheet_name=0, header=None, engine='openpyxl')
            except Exception:
                buf.seek(0)
                df_raw = pd.read_excel(buf, sheet_name=0, header=None, engine='xlrd')

            # 找 Date / Bullish / Neutral / Bearish 列 (通常在前 5 行)
            header_row = None
            for i in range(min(10, len(df_raw))):
                row_str = " ".join(str(x) for x in df_raw.iloc[i].tolist()).lower()
                if "bullish" in row_str and "bearish" in row_str:
                    header_row = i
                    break
            if header_row is None:
                self.stats["errors"].append("AAII Excel: header not found")
                return None

            df = pd.read_excel(io.BytesIO(r.content), sheet_name=0,
                               header=header_row,
                               engine='openpyxl' if OPENPYXL_AVAILABLE else 'xlrd')

            # 正規化欄位
            df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]

            # 嘗試識別 Date 欄
            date_col = None
            for c in ['date', 'reported_date', 'survey_date', 'week_ending']:
                if c in df.columns:
                    date_col = c; break
            if date_col is None:
                # 第一欄通常是日期
                date_col = df.columns[0]

            df = df.rename(columns={date_col: 'date'})
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.dropna(subset=['date'])

            # bull/neutral/bear
            for src, dst in [('bullish', 'bullish'), ('neutral', 'neutral'),
                             ('bearish', 'bearish')]:
                if src not in df.columns:
                    # 模糊匹配
                    for c in df.columns:
                        if src in c:
                            df = df.rename(columns={c: dst})
                            break
            for c in ['bullish', 'neutral', 'bearish']:
                if c in df.columns:
                    df[c] = pd.to_numeric(df[c], errors='coerce')

            keep = [c for c in ['date', 'bullish', 'neutral', 'bearish'] if c in df.columns]
            df = df[keep].dropna(subset=['bullish', 'neutral', 'bearish'], how='all')
            df = df.sort_values('date').reset_index(drop=True)

            # 計算衍生欄
            if 'bullish' in df.columns and 'bearish' in df.columns:
                df['bull_bear_spread'] = df['bullish'] - df['bearish']
                df['ma8_bullish'] = df['bullish'].rolling(8, min_periods=1).mean()

            df['source'] = 'AAII_Excel'

            # 篩日期
            df = df[df['date'] >= pd.to_datetime(self.start_date)].reset_index(drop=True)
            self.stats["method"] = "excel"
            return df

        except Exception as e:
            self.stats["errors"].append(f"AAII Excel parse fail: {str(e)[:120]}")
            return None

    def _try_html(self) -> Optional["pd.DataFrame"]:
        """嘗試 2: HTML scrape (僅最新一週)."""
        if pd is None:
            return None
        r = _http_get(AAII_URL_FALLBACK)
        if r is None:
            self.stats["errors"].append("AAII HTML: HTTP failed")
            return None
        # 嘗試 pandas.read_html
        try:
            tables = pd.read_html(io.StringIO(r.text))
            if not tables:
                self.stats["errors"].append("AAII HTML: no tables")
                return None
            for t in tables:
                t_lower = " ".join(str(c).lower() for c in t.columns)
                if "bullish" in t_lower and "bearish" in t_lower:
                    df = t.copy()
                    df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]
                    # 必有 bullish/neutral/bearish 三欄, 日期可能無
                    if 'date' not in df.columns:
                        df['date'] = pd.Timestamp.now().normalize()
                    df['date'] = pd.to_datetime(df['date'], errors='coerce')
                    df = df.dropna(subset=['date'])
                    for c in ['bullish', 'neutral', 'bearish']:
                        if c in df.columns:
                            df[c] = (df[c].astype(str)
                                     .str.replace('%', '').str.replace(',', ''))
                            df[c] = pd.to_numeric(df[c], errors='coerce')
                    if 'bullish' in df.columns and 'bearish' in df.columns:
                        df['bull_bear_spread'] = df['bullish'] - df['bearish']
                        df['ma8_bullish'] = np.nan
                    df['source'] = 'AAII_HTML'
                    self.stats["method"] = "html"
                    return df
            self.stats["errors"].append("AAII HTML: matching table not found")
            return None
        except Exception as e:
            self.stats["errors"].append(f"AAII HTML parse fail: {str(e)[:120]}")
            return None

    def fetch(self) -> "pd.DataFrame":
        """主入口: 嘗試 Excel → HTML → 空."""
        if pd is None:
            return pd.DataFrame()
        df = self._try_excel()
        if df is None or df.empty:
            df = self._try_html()
        if df is None or df.empty:
            return pd.DataFrame()
        self.stats["rows"] = len(df)
        return df


# =====================================================================================
# 😱 [API-2] CNNFearGreedFetcher  -  CNN Fear & Greed Index
# =====================================================================================

class CNNFearGreedFetcher:
    """
    CNN Fear & Greed Index (0-100).
      0-25  Extreme Fear
      25-45 Fear
      45-55 Neutral
      55-75 Greed
      75-100 Extreme Greed

    7 sub-indicators:
      stock_price_strength · market_momentum · stock_price_breadth
      put_call_options · junk_bond_demand · market_volatility · safe_haven_demand

    Endpoint:
      https://production.dataviz.cnn.io/index/fearandgreed/graphdata/<YYYY-MM-DD>
    """

    VERSION = "1.0.0"

    def __init__(self, lookback_days: int = CNN_LOOKBACK_DAYS):
        self.lookback_days = lookback_days
        self.stats = {"rows": 0, "subindicators": 0, "errors": []}

    def fetch(self) -> Dict[str, "pd.DataFrame"]:
        """
        回傳 dict:
          - 'fear_greed': 主指數時間序列
          - 'subindicators': 7 子指標 long-form
        """
        if pd is None:
            return {"fear_greed": pd.DataFrame(), "subindicators": pd.DataFrame()}
        # CNN 預設給最近 ~3 年, 帶日期 hint 可取得對應段
        start = (datetime.now() - timedelta(days=self.lookback_days)).strftime("%Y-%m-%d")
        url = f"{CNN_URL_FEAR_GREED}/{start}"
        r = _http_get(url)
        if r is None:
            # 試無 path 版
            r = _http_get(CNN_URL_FEAR_GREED)
        if r is None:
            self.stats["errors"].append("CNN: HTTP failed for both endpoints")
            return {"fear_greed": pd.DataFrame(), "subindicators": pd.DataFrame()}

        try:
            js = r.json()
        except Exception as e:
            self.stats["errors"].append(f"CNN: JSON parse fail: {str(e)[:120]}")
            return {"fear_greed": pd.DataFrame(), "subindicators": pd.DataFrame()}

        # 主指數
        fg_data = js.get("fear_and_greed_historical", {}).get("data", [])
        fg_rows = []
        for r_ in fg_data:
            ts = r_.get("x")
            if ts is None: continue
            dt = pd.to_datetime(ts, unit='ms') if ts > 1e9 else pd.to_datetime(ts, unit='s')
            fg_rows.append({
                "date": dt.normalize(),
                "fear_greed_index": float(r_.get("y", 0)),
                "rating": r_.get("rating", ""),
            })
        df_main = pd.DataFrame(fg_rows).sort_values('date').reset_index(drop=True) if fg_rows else pd.DataFrame()

        # 7 子指標
        sub_map = {
            "market_momentum_sp500":           "market_momentum",
            "stock_price_strength":            "stock_price_strength",
            "stock_price_breadth":             "stock_price_breadth",
            "put_call_options":                "put_call_options",
            "junk_bond_demand":                "junk_bond_demand",
            "market_volatility_vix":           "market_volatility",
            "safe_haven_demand":               "safe_haven_demand",
        }
        sub_rows = []
        for cnn_key, our_key in sub_map.items():
            block = js.get(cnn_key, {})
            data = block.get("data", [])
            for r_ in data:
                ts = r_.get("x")
                if ts is None: continue
                dt = pd.to_datetime(ts, unit='ms') if ts > 1e9 else pd.to_datetime(ts, unit='s')
                sub_rows.append({
                    "date":      dt.normalize(),
                    "indicator": our_key,
                    "value":     float(r_.get("y", 0)),
                    "rating":    r_.get("rating", ""),
                })

        df_sub = pd.DataFrame(sub_rows).sort_values(['date', 'indicator']).reset_index(drop=True) if sub_rows else pd.DataFrame()

        self.stats["rows"]          = len(df_main)
        self.stats["subindicators"] = df_sub['indicator'].nunique() if not df_sub.empty else 0
        return {"fear_greed": df_main, "subindicators": df_sub}


# =====================================================================================
# 🏦 [API-3] FREDFetcher  -  Federal Reserve Economic Data
# =====================================================================================

class FREDFetcher:
    """
    FRED API fetcher (with internal API key).
    支援 50+ series registry (FRED_REGISTRY).

    策略:
      1. 官方 API: api.stlouisfed.org/fred/series/observations (主要)
      2. pandas_datareader fallback (若 requests 失敗)
    """

    VERSION = "1.0.0"

    def __init__(self, api_key: str = FRED_API_KEY,
                 start_date: str = START_DATE,
                 end_date: Optional[str] = None,
                 series_codes: Optional[List[str]] = None):
        self.api_key    = api_key
        self.start_date = start_date
        self.end_date   = end_date or _end_date()
        # 預設抓全部 50+ series
        self.series_codes = series_codes if series_codes else list(FRED_REGISTRY.keys())
        self.stats = {"ok": 0, "fail": 0, "rows": 0, "errors": [], "method": {}}

    def _fetch_one(self, fred_id: str) -> Optional["pd.DataFrame"]:
        """單一 series 抓取."""
        if pd is None:
            return None

        # ── Path 1: 官方 API ──
        if self.api_key and REQUESTS_AVAILABLE:
            params = {
                "series_id":         fred_id,
                "api_key":           self.api_key,
                "file_type":         "json",
                "observation_start": self.start_date,
                "observation_end":   self.end_date,
            }
            r = _http_get(FRED_URL_BASE, params=params)
            if r is not None:
                try:
                    js = r.json()
                    obs = js.get("observations", [])
                    if obs:
                        df = pd.DataFrame(obs)
                        df["date"]  = pd.to_datetime(df["date"], errors='coerce')
                        df["value"] = pd.to_numeric(df["value"], errors='coerce')
                        df = df[["date", "value"]].dropna(subset=["date"])
                        self.stats["method"][fred_id] = "api"
                        return df
                except Exception as e:
                    self.stats["errors"].append(f"{fred_id}: API parse fail: {str(e)[:80]}")

        # ── Path 2: pandas_datareader ──
        if PDR_AVAILABLE:
            try:
                s = pdr.DataReader(fred_id, "fred", self.start_date, self.end_date)
                if s is not None and not s.empty:
                    df = s.reset_index()
                    df.columns = ["date", "value"]
                    df["date"]  = pd.to_datetime(df["date"], errors='coerce')
                    df["value"] = pd.to_numeric(df["value"], errors='coerce')
                    self.stats["method"][fred_id] = "pdr"
                    return df
            except Exception as e:
                self.stats["errors"].append(f"{fred_id}: pdr fail: {str(e)[:80]}")

        return None

    def fetch(self) -> "pd.DataFrame":
        """並發抓所有 series, long-form output."""
        if pd is None:
            return pd.DataFrame()
        all_rows = []
        # 並發抓
        if ENABLE_THREADPOOL and len(self.series_codes) > 1:
            with ThreadPoolExecutor(max_workers=THREADPOOL_WORKERS) as pool:
                future_to_code = {
                    pool.submit(self._process_one, via_code): via_code
                    for via_code in self.series_codes
                }
                for fut in as_completed(future_to_code):
                    res = fut.result()
                    if res is not None and not res.empty:
                        all_rows.append(res)
        else:
            for via_code in self.series_codes:
                res = self._process_one(via_code)
                if res is not None and not res.empty:
                    all_rows.append(res)

        if not all_rows:
            return pd.DataFrame()
        df = pd.concat(all_rows, ignore_index=True)
        self.stats["rows"] = len(df)
        return df

    def _process_one(self, via_code: str) -> Optional["pd.DataFrame"]:
        """單一 via_code 抓 + 加 metadata + transform."""
        meta = FRED_REGISTRY.get(via_code)
        if not meta:
            return None
        fred_id = meta.get("fred_id")
        if not fred_id:
            return None
        df = self._fetch_one(fred_id)
        if df is None or df.empty:
            self.stats["fail"] += 1
            return None

        # transform
        transform = meta.get("transform")
        if transform:
            try:
                df["value_raw"]    = df["value"]
                df["value"]        = _apply_transform(df["value"], transform)
                df["transform"]    = transform
            except Exception as e:
                self.stats["errors"].append(f"{via_code}: transform fail: {str(e)[:60]}")

        df["via_code"]    = via_code
        df["fred_id"]     = fred_id
        df["indicator"]   = meta.get("indicator", "")
        df["theme"]       = meta.get("theme", "")
        df["sub_theme"]   = meta.get("sub_theme", "")
        df["unit"]        = meta.get("unit", "")
        df["freq"]        = meta.get("freq", "")
        self.stats["ok"] += 1
        return df


# =====================================================================================
# 🏯 [API-4] AKShareFetcher  -  CN Futures + Macro
# =====================================================================================

class AKShareFetcher:
    """
    AKShare CN 期貨 / 宏觀 / 航運抓取.

    內建 13 個 series (AKSHARE_REGISTRY):
      - CN futures: CU0, AL0, ZN0, RB0, I0, JM0, AU0, AG0, SC0
      - Shipping:   BDI
      - CN macro:   PMI / M2

    分流輸出:
      futures_df (期貨)  ·  macro_df (宏觀)  ·  shipping_df (航運)
    """

    VERSION = "1.0.0"

    def __init__(self, codes: Optional[List[str]] = None):
        self.codes = codes if codes else list(AKSHARE_REGISTRY.keys())
        self.stats = {"ok": 0, "fail": 0, "rows": 0, "errors": []}

    def _ak_call(self, func_name: str, **kwargs):
        """安全呼叫 AKShare."""
        if not AKSHARE_AVAILABLE:
            return None
        fn = getattr(ak, func_name, None)
        if fn is None:
            return None
        for attempt in range(MAX_RETRIES):
            try:
                return fn(**{k: v for k, v in kwargs.items() if v is not None})
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    self.stats["errors"].append(f"{func_name}: {str(e)[:80]}")
        return None

    def fetch(self) -> Dict[str, "pd.DataFrame"]:
        """並發抓所有, 分流 futures / shipping / macro."""
        if not AKSHARE_AVAILABLE or pd is None:
            self.stats["errors"].append("akshare not installed (pip install akshare)")
            return {"futures": pd.DataFrame(), "shipping": pd.DataFrame(), "macro": pd.DataFrame()}

        futures_rows  = []
        shipping_rows = []
        macro_rows    = []

        def _one(code: str):
            meta = AKSHARE_REGISTRY.get(code)
            if not meta:
                return None, code
            func = meta.get("func")
            sym  = meta.get("sym")
            kwargs = {"symbol": sym} if sym else {}
            df = self._ak_call(func, **kwargs)
            if df is None or (hasattr(df, 'empty') and df.empty):
                return None, code
            df = df.copy()
            df["code"]      = code
            df["name"]      = meta.get("name", "")
            df["theme"]     = meta.get("theme", "")
            df["sub_theme"] = meta.get("sub_theme", "")
            df["source"]    = "akshare"
            return (meta, df), code

        if ENABLE_THREADPOOL:
            with ThreadPoolExecutor(max_workers=THREADPOOL_WORKERS) as pool:
                futures_map = {pool.submit(_one, c): c for c in self.codes}
                for fut in as_completed(futures_map):
                    res, code = fut.result()
                    if res is None:
                        self.stats["fail"] += 1
                        continue
                    meta, df = res
                    self.stats["ok"] += 1
                    theme = meta.get("theme", "")
                    if theme == "Futures":   futures_rows.append(df)
                    elif theme == "Shipping": shipping_rows.append(df)
                    else:                     macro_rows.append(df)
        else:
            for code in self.codes:
                res, _ = _one(code)
                if res is None:
                    self.stats["fail"] += 1
                    continue
                meta, df = res
                self.stats["ok"] += 1
                theme = meta.get("theme", "")
                if theme == "Futures":   futures_rows.append(df)
                elif theme == "Shipping": shipping_rows.append(df)
                else:                     macro_rows.append(df)

        def _concat(rows):
            if not rows: return pd.DataFrame()
            try:
                return pd.concat(rows, ignore_index=True)
            except Exception as e:
                self.stats["errors"].append(f"concat fail: {str(e)[:80]}")
                return pd.DataFrame()

        futures_df  = _concat(futures_rows)
        shipping_df = _concat(shipping_rows)
        macro_df    = _concat(macro_rows)
        self.stats["rows"] = len(futures_df) + len(shipping_df) + len(macro_df)
        return {"futures": futures_df, "shipping": shipping_df, "macro": macro_df}


# =====================================================================================
# 💾 OutputManager  -  統一輸出管理 (Parquet 必選 + DuckDB + CSV + JSON + GSheet)
# =====================================================================================

class OutputManager:
    """
    多格式輸出管理器.

    支援:
      - Parquet (必選, 主要 SSOT)
      - DuckDB  (可選, 單一檔案資料庫 .duckdb)
      - CSV     (可選, utf-8-sig 避免中文 BOM)
      - JSON    (可選, 人類可讀)
      - GSheet  (可選, 需 gspread + service account)

    每張表存獨立檔案 (Parquet) 或獨立 table (DuckDB):
      - aaii_sentiment
      - cnn_fear_greed
      - cnn_subindicators
      - fred_macro
      - akshare_futures
      - akshare_shipping
      - akshare_macro
    """

    VERSION = "1.0.0"

    def __init__(self):
        self.base_dir   = Path(BASE_DIR)
        self.output_dir = self.base_dir / OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir = self.output_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        self.duckdb_path = self.output_dir / DUCKDB_FILENAME
        # CLI override
        self.enable_parquet = OUTPUT_PARQUET
        self.enable_duckdb  = OUTPUT_DUCKDB  and DUCKDB_AVAILABLE
        self.enable_csv     = OUTPUT_CSV
        self.enable_json    = OUTPUT_JSON
        self.enable_gsheet  = OUTPUT_GSHEET  and GSPREAD_AVAILABLE and GSHEET_CREDENTIAL_PATH

        if "--no-parquet" in sys.argv: self.enable_parquet = False
        if "--no-duckdb"  in sys.argv: self.enable_duckdb  = False
        if "--no-csv"     in sys.argv: self.enable_csv     = False
        if "--no-json"    in sys.argv: self.enable_json    = False
        if "--gsheet"     in sys.argv: self.enable_gsheet  = True

        self.results: Dict[str, Dict[str, Any]] = {}

    def _backup(self, path: Path):
        if not ENABLE_BACKUP or not path.exists(): return
        try:
            import shutil
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            shutil.copy2(path, self.backup_dir / f"{ts}_{path.name}")
            # 清舊備份
            backups = sorted(self.backup_dir.glob(f"*_{path.name}"),
                             key=lambda x: x.stat().st_mtime, reverse=True)
            for bk in backups[MAX_BACKUP_FILES:]:
                try: bk.unlink()
                except Exception: pass
        except Exception:
            pass

    def save(self, table_name: str, df: "pd.DataFrame") -> Dict[str, Any]:
        """單一 table 多格式輸出."""
        if df is None or df.empty or pd is None:
            self.results[table_name] = {"rows": 0, "saved": False, "outputs": []}
            return self.results[table_name]

        rows = len(df)
        outputs = []

        # Parquet
        if self.enable_parquet and PYARROW_AVAILABLE:
            p = self.output_dir / f"{table_name}.parquet"
            self._backup(p)
            try:
                df.to_parquet(p, index=False)
                outputs.append({"format": "parquet", "path": str(p), "size_kb": p.stat().st_size // 1024})
            except Exception as e:
                outputs.append({"format": "parquet", "error": str(e)[:80]})

        # CSV
        if self.enable_csv:
            p = self.output_dir / f"{table_name}.csv"
            self._backup(p)
            try:
                df.to_csv(p, index=False, encoding=CSV_ENCODING)
                outputs.append({"format": "csv", "path": str(p), "size_kb": p.stat().st_size // 1024})
            except Exception as e:
                outputs.append({"format": "csv", "error": str(e)[:80]})

        # JSON
        if self.enable_json:
            p = self.output_dir / f"{table_name}.json"
            self._backup(p)
            try:
                df_for_json = df.copy()
                # Convert datetime to str
                for c in df_for_json.columns:
                    if pd.api.types.is_datetime64_any_dtype(df_for_json[c]):
                        df_for_json[c] = df_for_json[c].dt.strftime('%Y-%m-%d')
                df_for_json.to_json(p, orient="records", indent=JSON_INDENT, force_ascii=False)
                outputs.append({"format": "json", "path": str(p), "size_kb": p.stat().st_size // 1024})
            except Exception as e:
                outputs.append({"format": "json", "error": str(e)[:80]})

        # DuckDB (單一 .duckdb 檔, 多 table)
        if self.enable_duckdb and DUCKDB_AVAILABLE:
            try:
                conn = duckdb.connect(str(self.duckdb_path))
                conn.register("__tmp_df__", df)
                conn.execute(f"DROP TABLE IF EXISTS \"{table_name}\"")
                conn.execute(f"CREATE TABLE \"{table_name}\" AS SELECT * FROM __tmp_df__")
                conn.close()
                outputs.append({"format": "duckdb", "path": str(self.duckdb_path), "table": table_name})
            except Exception as e:
                outputs.append({"format": "duckdb", "error": str(e)[:80]})

        # Google Sheet (僅當有憑證)
        if self.enable_gsheet and GSPREAD_AVAILABLE and GSHEET_CREDENTIAL_PATH and GSHEET_SPREADSHEET_ID:
            try:
                gc = gspread.service_account(filename=GSHEET_CREDENTIAL_PATH)
                sh = gc.open_by_key(GSHEET_SPREADSHEET_ID)
                try:
                    ws = sh.worksheet(table_name)
                    ws.clear()
                except gspread.WorksheetNotFound:
                    ws = sh.add_worksheet(title=table_name, rows=str(rows + 10), cols=str(len(df.columns) + 2))
                data = [df.columns.tolist()] + df.astype(str).values.tolist()
                ws.update(data)
                outputs.append({"format": "gsheet", "spreadsheet_id": GSHEET_SPREADSHEET_ID, "sheet": table_name})
            except Exception as e:
                outputs.append({"format": "gsheet", "error": str(e)[:80]})

        self.results[table_name] = {"rows": rows, "saved": True, "outputs": outputs}
        return self.results[table_name]


# =====================================================================================
# 🎯 SentimentMacroEngine  -  主類 (整合 4 個 fetcher + OutputManager)
# =====================================================================================

class SentimentMacroEngine:
    """
    VDF MDL003 主引擎.

    高度整合 4 個 API:
      [1] AAII Sentiment    (週度)
      [2] CNN Fear & Greed  (日度)
      [3] FRED 50+ macro    (日/週/月度)
      [4] AKShare CN/BDI    (日度)

    並發抓取 (ThreadPoolExecutor) + 統一多格式輸出.
    """

    VERSION = "1.0.0"

    def __init__(self):
        self.output_mgr = OutputManager()
        self.start_time = time.time()
        # CLI flags
        self.run_aaii    = ENABLE_AAII    and "--no-aaii"    not in sys.argv
        self.run_cnn     = ENABLE_CNN     and "--no-cnn"     not in sys.argv
        self.run_fred    = ENABLE_FRED    and "--no-fred"    not in sys.argv
        self.run_akshare = ENABLE_AKSHARE and "--no-akshare" not in sys.argv
        # 反向: 若指定單一 flag, 只跑該 API
        explicit = any(f in sys.argv for f in ["--aaii", "--cnn", "--fred", "--akshare"])
        if explicit:
            self.run_aaii    = "--aaii"    in sys.argv
            self.run_cnn     = "--cnn"     in sys.argv
            self.run_fred    = "--fred"    in sys.argv
            self.run_akshare = "--akshare" in sys.argv

        # Fetchers
        self.aaii_fetcher    = AAIIFetcher()
        self.cnn_fetcher     = CNNFearGreedFetcher()
        self.fred_fetcher    = FREDFetcher()
        self.akshare_fetcher = AKShareFetcher()

        # Result holders
        self.df_aaii         = None
        self.df_cnn_main     = None
        self.df_cnn_sub      = None
        self.df_fred         = None
        self.df_ak_futures   = None
        self.df_ak_shipping  = None
        self.df_ak_macro     = None
        self.save_results    = {}

    def show_header(self):
        """啟動 header."""
        api_status = []
        for label, flag in [("AAII", self.run_aaii), ("CNN F&G", self.run_cnn),
                            ("FRED", self.run_fred), ("AKShare", self.run_akshare)]:
            api_status.append(f"{label}={'✅' if flag else '⏭️'}")
        fmt_status = []
        for label, flag in [("Parquet", self.output_mgr.enable_parquet),
                            ("DuckDB",  self.output_mgr.enable_duckdb),
                            ("CSV",     self.output_mgr.enable_csv),
                            ("JSON",    self.output_mgr.enable_json),
                            ("GSheet",  self.output_mgr.enable_gsheet)]:
            fmt_status.append(f"{label}={'✅' if flag else '—'}")

        header = f"""
🏛️ VDF MDL003 · Sentiment + Macro Integration Engine (v{self.VERSION})

📅 時間範圍 : {START_DATE} ~ {_end_date()}
📁 輸出目錄 : {BASE_DIR}/{OUTPUT_DIR}
🔑 FRED API : {'✅ Set' if FRED_API_KEY else '❌'} ({FRED_API_KEY[:8]}...{FRED_API_KEY[-4:] if FRED_API_KEY else ''})
🚀 加速     : ThreadPool ({THREADPOOL_WORKERS} workers) · 4 條管道並行

📡 API 開關 : {' · '.join(api_status)}
💾 輸出格式 : {' · '.join(fmt_status)}

🔌 Registry  : FRED {len(FRED_REGISTRY)} series · AKShare {len(AKSHARE_REGISTRY)} codes
        """
        if RICH_AVAILABLE:
            console.print(Panel(header.strip(),
                                title="[bold blue]VDF MDL003 · Sentiment+Macro Engine[/bold blue]",
                                border_style="blue"))
        else:
            print("=" * 80); print(header); print("=" * 80)

    def run(self) -> int:
        """主入口."""
        try:
            self.show_header()
            print("\n🔍 步驟 1/3: 並發抓取 4 條管道")
            # 並發跑 4 條
            tasks = {}
            with ThreadPoolExecutor(max_workers=THREADPOOL_WORKERS) as pool:
                if self.run_aaii:
                    tasks["aaii"]    = pool.submit(self.aaii_fetcher.fetch)
                if self.run_cnn:
                    tasks["cnn"]     = pool.submit(self.cnn_fetcher.fetch)
                if self.run_fred:
                    tasks["fred"]    = pool.submit(self.fred_fetcher.fetch)
                if self.run_akshare:
                    tasks["akshare"] = pool.submit(self.akshare_fetcher.fetch)

                for name, fut in tasks.items():
                    try:
                        result = fut.result(timeout=180)
                        if name == "aaii":
                            self.df_aaii = result
                            print(f"   ✓ AAII:    {len(result) if pd is not None and result is not None else 0:>6} 列  "
                                  f"(method={self.aaii_fetcher.stats.get('method')})")
                        elif name == "cnn":
                            self.df_cnn_main = result.get("fear_greed", pd.DataFrame() if pd is not None else None)
                            self.df_cnn_sub  = result.get("subindicators", pd.DataFrame() if pd is not None else None)
                            print(f"   ✓ CNN F&G: {len(self.df_cnn_main) if pd is not None else 0:>6} 列 主指數 + "
                                  f"{len(self.df_cnn_sub) if pd is not None else 0} 列 子指標")
                        elif name == "fred":
                            self.df_fred = result
                            print(f"   ✓ FRED:    {len(result) if pd is not None and result is not None else 0:>6} 列 "
                                  f"(ok={self.fred_fetcher.stats['ok']}/fail={self.fred_fetcher.stats['fail']})")
                        elif name == "akshare":
                            self.df_ak_futures  = result.get("futures",  pd.DataFrame() if pd is not None else None)
                            self.df_ak_shipping = result.get("shipping", pd.DataFrame() if pd is not None else None)
                            self.df_ak_macro    = result.get("macro",    pd.DataFrame() if pd is not None else None)
                            tot = sum(len(x) for x in [self.df_ak_futures, self.df_ak_shipping, self.df_ak_macro]
                                      if pd is not None and x is not None)
                            print(f"   ✓ AKShare: {tot:>6} 列  "
                                  f"(ok={self.akshare_fetcher.stats['ok']}/fail={self.akshare_fetcher.stats['fail']})")
                    except Exception as e:
                        print(f"   ❌ {name}: {str(e)[:100]}")

            # 儲存
            print("\n💾 步驟 2/3: 多格式輸出")
            saves = {}
            if pd is not None:
                if self.run_aaii and self.df_aaii is not None and not self.df_aaii.empty:
                    saves["aaii_sentiment"]     = self.output_mgr.save("aaii_sentiment", self.df_aaii)
                if self.run_cnn and self.df_cnn_main is not None and not self.df_cnn_main.empty:
                    saves["cnn_fear_greed"]     = self.output_mgr.save("cnn_fear_greed", self.df_cnn_main)
                if self.run_cnn and self.df_cnn_sub is not None and not self.df_cnn_sub.empty:
                    saves["cnn_subindicators"]  = self.output_mgr.save("cnn_subindicators", self.df_cnn_sub)
                if self.run_fred and self.df_fred is not None and not self.df_fred.empty:
                    saves["fred_macro"]         = self.output_mgr.save("fred_macro", self.df_fred)
                if self.run_akshare and self.df_ak_futures is not None and not self.df_ak_futures.empty:
                    saves["akshare_futures"]    = self.output_mgr.save("akshare_futures", self.df_ak_futures)
                if self.run_akshare and self.df_ak_shipping is not None and not self.df_ak_shipping.empty:
                    saves["akshare_shipping"]   = self.output_mgr.save("akshare_shipping", self.df_ak_shipping)
                if self.run_akshare and self.df_ak_macro is not None and not self.df_ak_macro.empty:
                    saves["akshare_macro"]      = self.output_mgr.save("akshare_macro", self.df_ak_macro)
            self.save_results = saves

            for tbl, info in saves.items():
                fmts = [o.get("format") for o in info.get("outputs", []) if "error" not in o]
                print(f"   ✓ {tbl:<22} → {info['rows']:>6,} 列  [{' · '.join(fmts)}]")

            # Rich summary
            print("\n📋 步驟 3/3: Rich Summary Matrix")
            print_rich_summary_matrix(self)
            print(f"\n🎉 處理完成! 輸出: {self.output_mgr.output_dir}")
            return 0

        except KeyboardInterrupt:
            print("\n⚠️ 用戶中斷"); return 1
        except Exception as e:
            print(f"\n❌ 錯誤: {e}")
            if LOG_LEVEL == "DEBUG":
                import traceback; traceback.print_exc()
            return 1


# =====================================================================================
# 🎨 Rich Summary Matrix (8 表 + Panel)
# =====================================================================================

def print_rich_summary_matrix(eng: SentimentMacroEngine):
    """印 detailed and well-organized summary matrix by Rich."""
    if not RICH_AVAILABLE:
        return _print_plain_summary(eng)

    elapsed = round(time.time() - eng.start_time, 2)
    console.rule(f"[bold cyan]🏛️ VDF MDL003 · Sentiment + Macro Engine · 執行彙總矩陣[/bold cyan]")

    # ─ Table 1: 系統環境 ─
    t = Table(title="📦 [bold]系統環境 / 套件依賴[/bold]", box=box.ROUNDED, header_style="bold magenta")
    t.add_column("套件", style="cyan", width=20)
    t.add_column("狀態", style="green", width=8, justify="center")
    t.add_column("作用", style="yellow", width=48)
    t.add_row("pandas/numpy", "✅" if PANDAS_AVAILABLE   else "❌", "資料表處理 + 衍生計算")
    t.add_row("requests",     "✅" if REQUESTS_AVAILABLE else "❌", "HTTP 抓取 (AAII/CNN/FRED)")
    t.add_row("pyarrow",      "✅" if PYARROW_AVAILABLE  else "⚪", "Parquet 輸出 (必選格式)")
    t.add_row("duckdb",       "✅" if DUCKDB_AVAILABLE   else "⚪", "DuckDB 單檔資料庫")
    t.add_row("akshare",      "✅" if AKSHARE_AVAILABLE  else "⚪", "CN 期貨/宏觀")
    t.add_row("openpyxl",     "✅" if OPENPYXL_AVAILABLE else "⚪", "AAII Excel 解析")
    t.add_row("pdr",          "✅" if PDR_AVAILABLE      else "⚪", "FRED fallback (pandas_datareader)")
    t.add_row("gspread",      "✅" if GSPREAD_AVAILABLE  else "⚪", "Google Sheet 輸出")
    t.add_row("rich",         "✅" if RICH_AVAILABLE     else "⚪", "彩色終端表格")
    console.print(t)

    # ─ Table 2: 4 條 API 管道狀態 ─
    t = Table(title="📡 [bold]4 條 API 管道狀態[/bold]", box=box.ROUNDED, header_style="bold magenta")
    t.add_column("管道",    style="cyan", width=14)
    t.add_column("啟用",    style="green", width=8, justify="center")
    t.add_column("抓取結果", style="yellow", width=44)
    t.add_column("錯誤",    style="red",   width=20, justify="right")
    rows_aaii = len(eng.df_aaii) if pd is not None and eng.df_aaii is not None and not eng.df_aaii.empty else 0
    rows_cnn  = len(eng.df_cnn_main) if pd is not None and eng.df_cnn_main is not None and not eng.df_cnn_main.empty else 0
    rows_sub  = len(eng.df_cnn_sub)  if pd is not None and eng.df_cnn_sub  is not None and not eng.df_cnn_sub.empty  else 0
    rows_fred = len(eng.df_fred) if pd is not None and eng.df_fred is not None and not eng.df_fred.empty else 0
    rows_akf  = len(eng.df_ak_futures)  if pd is not None and eng.df_ak_futures  is not None and not eng.df_ak_futures.empty  else 0
    rows_aks  = len(eng.df_ak_shipping) if pd is not None and eng.df_ak_shipping is not None and not eng.df_ak_shipping.empty else 0
    rows_akm  = len(eng.df_ak_macro)    if pd is not None and eng.df_ak_macro    is not None and not eng.df_ak_macro.empty    else 0
    t.add_row("AAII",    "✅" if eng.run_aaii else "⏭️",
              f"{rows_aaii:,} 列 · method={eng.aaii_fetcher.stats.get('method', '—')}",
              str(len(eng.aaii_fetcher.stats.get('errors', []))))
    t.add_row("CNN F&G", "✅" if eng.run_cnn else "⏭️",
              f"{rows_cnn:,} 列 主指數 · {rows_sub:,} 列 子指標 ({eng.cnn_fetcher.stats.get('subindicators', 0)} 種)",
              str(len(eng.cnn_fetcher.stats.get('errors', []))))
    t.add_row("FRED",    "✅" if eng.run_fred else "⏭️",
              f"{rows_fred:,} 列 · ok={eng.fred_fetcher.stats['ok']}/fail={eng.fred_fetcher.stats['fail']} / "
              f"{len(eng.fred_fetcher.series_codes)} series",
              str(len(eng.fred_fetcher.stats.get('errors', []))))
    t.add_row("AKShare", "✅" if eng.run_akshare else "⏭️",
              f"futures={rows_akf:,} · shipping={rows_aks:,} · macro={rows_akm:,} "
              f"(ok={eng.akshare_fetcher.stats['ok']}/fail={eng.akshare_fetcher.stats['fail']})",
              str(len(eng.akshare_fetcher.stats.get('errors', []))))
    console.print(t)

    # ─ Table 3: FRED Registry (theme 分布) ─
    t = Table(title="🏦 [bold]FRED Registry 主題分布 (50+ series)[/bold]", box=box.ROUNDED, header_style="bold magenta")
    t.add_column("主題",    style="cyan", width=14)
    t.add_column("Series 數", style="green", width=12, justify="right")
    t.add_column("代表 ID",  style="yellow", width=48)
    theme_count: Dict[str, List[str]] = {}
    for code, meta in FRED_REGISTRY.items():
        theme = meta.get("theme", "?")
        theme_count.setdefault(theme, []).append(meta.get("fred_id", code))
    for theme, ids in sorted(theme_count.items(), key=lambda x: -len(x[1])):
        sample = ", ".join(ids[:4])
        if len(ids) > 4: sample += f" ... (+{len(ids)-4})"
        t.add_row(theme, str(len(ids)), sample)
    console.print(t)

    # ─ Table 4: AKShare Registry (theme 分布) ─
    t = Table(title="🏯 [bold]AKShare Registry (CN 期貨 + 宏觀)[/bold]", box=box.ROUNDED, header_style="bold magenta")
    t.add_column("Theme",    style="cyan", width=12)
    t.add_column("數量",     style="green", width=8, justify="right")
    t.add_column("代表 code", style="yellow", width=54)
    ak_theme: Dict[str, List[str]] = {}
    for code, meta in AKSHARE_REGISTRY.items():
        ak_theme.setdefault(meta.get("theme", "?"), []).append(code)
    for theme, codes in sorted(ak_theme.items(), key=lambda x: -len(x[1])):
        sample = ", ".join(codes[:5])
        if len(codes) > 5: sample += f" ... (+{len(codes)-5})"
        t.add_row(theme, str(len(codes)), sample)
    console.print(t)

    # ─ Table 5: 輸出格式狀態 ─
    t = Table(title="💾 [bold]多格式輸出狀態[/bold]", box=box.ROUNDED, header_style="bold magenta")
    t.add_column("格式",   style="cyan",   width=12)
    t.add_column("啟用",   style="green",  width=8, justify="center")
    t.add_column("路徑 / 說明", style="yellow", width=56)
    mgr = eng.output_mgr
    t.add_row("Parquet", "✅" if mgr.enable_parquet else "—", "(必選) " + str(mgr.output_dir))
    t.add_row("DuckDB",  "✅" if mgr.enable_duckdb  else "—", str(mgr.duckdb_path))
    t.add_row("CSV",     "✅" if mgr.enable_csv     else "—", f"encoding={CSV_ENCODING}")
    t.add_row("JSON",    "✅" if mgr.enable_json    else "—", f"indent={JSON_INDENT}")
    t.add_row("GSheet",  "✅" if mgr.enable_gsheet  else "—",
              GSHEET_SPREADSHEET_ID if GSHEET_SPREADSHEET_ID else "(需設 GSHEET_CREDENTIAL_PATH + ID)")
    console.print(t)

    # ─ Table 6: 各 table 輸出明細 ─
    if eng.save_results:
        t = Table(title="📁 [bold]各 Table 輸出明細[/bold]", box=box.ROUNDED, header_style="bold magenta")
        t.add_column("Table 名稱", style="cyan",   width=22)
        t.add_column("列數",     style="green",  width=10, justify="right")
        t.add_column("Parquet",  style="yellow", width=10, justify="center")
        t.add_column("CSV",      style="yellow", width=8,  justify="center")
        t.add_column("JSON",     style="yellow", width=8,  justify="center")
        t.add_column("DuckDB",   style="yellow", width=10, justify="center")
        t.add_column("GSheet",   style="yellow", width=8,  justify="center")
        for tbl, info in eng.save_results.items():
            fmts = {o.get("format"): ("✅" if "error" not in o else "❌")
                    for o in info.get("outputs", [])}
            t.add_row(tbl, f"{info['rows']:,}",
                      fmts.get("parquet", "—"), fmts.get("csv", "—"),
                      fmts.get("json", "—"), fmts.get("duckdb", "—"),
                      fmts.get("gsheet", "—"))
        console.print(t)

    # ─ Table 7: 最新值 snapshot (Sentiment) ─
    if pd is not None:
        t = Table(title="📊 [bold]最新情緒 Snapshot[/bold]", box=box.ROUNDED, header_style="bold magenta")
        t.add_column("指標",      style="cyan",   width=24)
        t.add_column("日期",      style="yellow", width=14)
        t.add_column("數值",      style="green",  width=16, justify="right")
        t.add_column("狀態 / 評級", style="yellow", width=22)
        if eng.df_aaii is not None and not eng.df_aaii.empty:
            last = eng.df_aaii.iloc[-1]
            dt = pd.to_datetime(last.get('date'))
            bull = last.get('bullish'); bear = last.get('bearish'); spread = last.get('bull_bear_spread')
            t.add_row("AAII Bullish",     dt.strftime("%Y-%m-%d") if pd.notna(dt) else "—",
                      f"{bull:.1f}%" if pd.notna(bull) else "—",
                      "極端樂觀" if pd.notna(bull) and bull > 50 else
                      ("極端悲觀" if pd.notna(bull) and bull < 20 else "—"))
            t.add_row("AAII Bull-Bear",   dt.strftime("%Y-%m-%d") if pd.notna(dt) else "—",
                      f"{spread:+.1f}" if pd.notna(spread) else "—",
                      "—")
        if eng.df_cnn_main is not None and not eng.df_cnn_main.empty:
            last = eng.df_cnn_main.iloc[-1]
            dt = pd.to_datetime(last.get('date'))
            idx = last.get('fear_greed_index')
            rating = last.get('rating', '')
            t.add_row("CNN Fear & Greed", dt.strftime("%Y-%m-%d") if pd.notna(dt) else "—",
                      f"{idx:.0f}/100" if pd.notna(idx) else "—", str(rating).title())
        console.print(t)

    # ─ Final Panel ─
    total_rows = sum((eng.save_results.get(k, {}).get("rows", 0)) for k in eng.save_results)
    overall_ok = total_rows > 0
    summary_lines = [
        f"  API 管道狀態 : AAII={'✓' if eng.run_aaii else '—'} · CNN={'✓' if eng.run_cnn else '—'} · "
        f"FRED={'✓' if eng.run_fred else '—'} · AKShare={'✓' if eng.run_akshare else '—'}",
        f"  總列數       : {total_rows:,}",
        f"  輸出 tables  : {len(eng.save_results)}",
        f"  執行耗時     : {elapsed} 秒",
    ]
    overall = ("[bold green]✅ 系統運行正常[/bold green]" if overall_ok
               else "[bold yellow]⚠️ 部分管道未取得資料[/bold yellow]")
    console.print(Panel.fit("\n".join(summary_lines) + f"\n\n  {overall}",
                            title="[bold cyan]🎯 整體狀態[/bold cyan]", border_style="cyan"))
    console.rule(f"[dim]VDF MDL003 v{eng.VERSION} · build {_today()} · "
                 f"VERITAS Intelligence System · VDF[/dim]")


def _print_plain_summary(eng: SentimentMacroEngine):
    """Rich 不可用時的純文字 fallback."""
    elapsed = round(time.time() - eng.start_time, 2)
    print(f"\n{'='*80}\n🏛️ VDF MDL003 · 執行彙總\n{'='*80}")
    print(f"  耗時 : {elapsed}s")
    for tbl, info in eng.save_results.items():
        print(f"  {tbl:<22} → {info['rows']:>6,} 列")
    print('=' * 80)


# =====================================================================================
# 🎯 程式入口
# =====================================================================================

def main():
    if sys.version_info < (3, 7):
        print("❌ 需要 Python 3.7+"); return 1
    print("🚀 VDF MDL003 · Sentiment + Macro Integration Engine 啟動...")
    eng = SentimentMacroEngine()
    return eng.run()


def interactive_menu():
    while True:
        print("\n" + "=" * 60)
        print("🔧 VDF MDL003 Sentiment + Macro Engine · 選單")
        print("=" * 60)
        print("1. 🚀 跑全部 4 條 (預設)")
        print("2. 📊 只跑 AAII Sentiment")
        print("3. 😱 只跑 CNN Fear & Greed")
        print("4. 🏦 只跑 FRED (50+ macro)")
        print("5. 🏯 只跑 AKShare (CN 期貨 + 宏觀)")
        print("6. ⚙️ 切換輸出格式 (DuckDB / GSheet)")
        print("7. ❌ 退出")
        print("=" * 60)
        c = input("請選擇 (1-7): ").strip()
        if   c == '1': main()
        elif c == '2': sys.argv.append("--aaii");    main(); sys.argv.remove("--aaii")
        elif c == '3': sys.argv.append("--cnn");     main(); sys.argv.remove("--cnn")
        elif c == '4': sys.argv.append("--fred");    main(); sys.argv.remove("--fred")
        elif c == '5': sys.argv.append("--akshare"); main(); sys.argv.remove("--akshare")
        elif c == '6':
            print("輸出格式切換 (環境變數 sys.argv):")
            print("  目前: --no-parquet={} --no-duckdb={} --no-csv={} --no-json={} --gsheet={}".format(
                  "--no-parquet" in sys.argv, "--no-duckdb" in sys.argv,
                  "--no-csv" in sys.argv, "--no-json" in sys.argv, "--gsheet" in sys.argv))
        elif c == '7': print("👋 再見!"); break


if __name__ == "__main__":
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--menu":
            interactive_menu()
        else:
            exit_code = main()
            if "--no-pause" not in sys.argv:
                try: input("\n按 Enter 鍵退出...")
                except (EOFError, KeyboardInterrupt): pass
            sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ 中斷"); sys.exit(1)
    except Exception as e:
        print(f"\n❌ 未處理錯誤: {e}")
        if LOG_LEVEL == "DEBUG":
            import traceback; traceback.print_exc()
        sys.exit(1)
