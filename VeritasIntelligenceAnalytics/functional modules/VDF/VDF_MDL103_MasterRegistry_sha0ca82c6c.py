#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
================================================================================
  VDF_MDL103_MasterRegistry.py
================================================================================
  VERITAS DATA FRAMEWORK · MASTER MODULE REGISTRY
  Version    : 1.0.0   |   Module ID : VDF-MASTER-REG-001
  Asset ID   : VDF-MASTER-REG-CLS-001
  Policy     : 全生態模組註冊中樞 · append-only · SSOT

ROLE
================================================================================
  集中註冊「所有資料擷取模組」, 涵蓋:
    [VDF Active]    本期 session 新建 6 個 (MDL001/002/003/005/006 + Verify)
    [VDF Legacy]    過去 session 累積 11 個 (D2/E0-E4/Master 等)
    [VRN Active]    VRN 子系統 6 個 (MDL004/010-014)
    [Supportive]    3 個 (SSOT/Aegis/Celeritas) + super_engine
    [Control UI]    3 個 (SupportBridge/ControlServer/ControlCenter)

  總計 29 個資料擷取/支援/控制模組, 全部登錄.
  輸出 Parquet (必選) + DuckDB + CSV (utf-8-sig) + JSON + GSheet (stub).

  Rich Summary Matrix:
    - 模組總覽 (29 項分類)
    - 輸出格式相容性矩陣
    - registry 項目數
    - 依賴關係圖
    - 健康狀態 (檔案存在/路徑可達)

USAGE
================================================================================
  python VDF_MDL103_MasterRegistry.py                    # 完整註冊 + 輸出
  python VDF_MDL103_MasterRegistry.py --check            # 只檢查路徑健康, 不寫
  python VDF_MDL103_MasterRegistry.py --filter VDF       # 篩 VDF 系列
  python VDF_MDL103_MasterRegistry.py --no-pause         # CI 模式
"""

# =====================================================================================
# 📋 ALL PARAMETERS ON TOP
# =====================================================================================

PROJECT_NAME       = "0-0-MasterRegistry"
BASE_DIR           = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VDF\dict"
OUTPUT_DIR         = "0-0-MasterRegistry"

# 模組根目錄
VDF_MODULES_ROOT   = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VDF"
VRN_MODULES_ROOT   = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN"
SUPPORTIVE_ROOT    = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module"

# 輸出格式
OUTPUT_PARQUET     = True   # 必選
OUTPUT_DUCKDB      = True
OUTPUT_CSV         = True
OUTPUT_JSON        = True
OUTPUT_GSHEET      = False
CSV_ENCODING       = "utf-8-sig"
DUCKDB_FILENAME    = "VDF_MDL103_MasterRegistry.duckdb"
LOG_LEVEL          = "INFO"


# =====================================================================================
# 📚 MODULE REGISTRY (源真理表 - 29 個資料擷取/支援模組)
# =====================================================================================

# Schema: (mdl_id, category, name, file, version, status, role,
#          registry_items, output_formats, dependencies, last_updated)

MODULE_REGISTRY = [
    # ─────────────────────────────────────────────────────────────────────
    # [VDF Active - 本期 session 新建]
    # ─────────────────────────────────────────────────────────────────────
    {"mdl_id": "VDF-MDL001",     "category": "VDF Active",  "subcategory": "Equity",
     "name": "TW Equity Engine",  "file": "VDF_MDL001_TWEquityEngine.py",
     "version": "1.0.0",          "status": "Production",
     "role": "台股 TWSE/TPEX 全市場個股引擎",
     "registry_items": "Universe (動態載入)",
     "output_formats": "Parquet+CSV (升級中可加 DuckDB+JSON+GSheet)",
     "dependencies": "yfinance, pandas, requests, rich, pyarrow",
     "lines": 2263, "last_updated": "2026-06-01"},

    {"mdl_id": "VDF-MDL001-VRF", "category": "VDF Active",  "subcategory": "Equity",
     "name": "TW Universe Verifier","file": "VDF_MDL001_TWUniverseVerify.py",
     "version": "1.0.0",            "status": "Production",
     "role": "SSOT regex 驗證 TWSE/TPEX OpenAPI universe",
     "registry_items": "SSOT regex locked: (?!0)(?!202[1-9])(?!2030)([1-9]\\d{3})",
     "output_formats": "Parquet · CSV · JSON",
     "dependencies": "pandas, requests, rich, pyarrow",
     "lines": 585, "last_updated": "2026-06-01"},

    {"mdl_id": "VDF-MDL002",     "category": "VDF Active",  "subcategory": "Universe",
     "name": "YFinance Universe",   "file": "VDF_MDL002_YFinanceFetchingEngine.py",
     "version": "1.0.0",            "status": "Production",
     "role": "全宇宙 yfinance (175 檔 · 19 群組 · 8 asset class)",
     "registry_items": "175 (Indices+Equity+ETF×7+FX+Commodity+Bond+Crypto)",
     "output_formats": "Parquet+CSV (升級中可加 DuckDB+JSON+GSheet)",
     "dependencies": "yfinance, pandas, rich, pyarrow",
     "lines": 1802, "last_updated": "2026-06-01"},

    {"mdl_id": "VDF-MDL003",     "category": "VDF Active",  "subcategory": "Sentiment+Macro",
     "name": "Sentiment + Macro Engine", "file": "VDF_MDL003_SentimentMacroEngine.py",
     "version": "1.0.0",                "status": "Production",
     "role": "AAII + CNN F&G + FRED + AKShare 高度整合",
     "registry_items": "FRED 47 series · AKShare 13 codes · AAII + CNN endpoints",
     "output_formats": "Parquet · DuckDB · CSV · JSON · GSheet",
     "dependencies": "yfinance, requests, akshare, pandas_datareader",
     "lines": 1466, "last_updated": "2026-06-01"},

    {"mdl_id": "VDF-MDL004",     "category": "VDF Active",  "subcategory": "FullMarket",
     "name": "TW Full Market Engine",   "file": "VDF_MDL004_TWFullMarketEngine.py",
     "version": "2.0.0",                "status": "Production",
     "role": "TW 全市場 ~1,900 檔 · Daily Quote + SMA + AvgVol + MCap + Consensus",
     "registry_items": "TWSE/TPEX OpenAPI + YF bulk + YF consensus + FactSet stub",
     "output_formats": "Parquet · DuckDB · CSV · JSON · GSheet",
     "dependencies": "yfinance, requests, pandas, pyarrow, duckdb",
     "lines": 1071, "last_updated": "2026-06-04"},

    {"mdl_id": "VDF-MDL007",     "category": "VDF Active",  "subcategory": "Resolver",
     "name": "SSOT Multi-Source Resolver","file": "VDF_MDL007_SSOTResolver.py",
     "version": "1.0.0",                  "status": "Production",
     "role": "個股全欄位解析 · SSOT regex + TWSE/TPEX/MOPS/YFinance 4 源 union",
     "registry_items": "Any input → canonical + 4-source coverage matrix",
     "output_formats": "Parquet · DuckDB · CSV · JSON · GSheet",
     "dependencies": "yfinance, requests, pandas, pyarrow, duckdb",
     "lines": 1221, "last_updated": "2026-06-04"},

    {"mdl_id": "VDF-MDL005",     "category": "VDF Active",  "subcategory": "Filter",
     "name": "TW Stock Filter + Consensus","file": "VDF_MDL005_TWStockFilter.py",
     "version": "1.0.0",                  "status": "Production",
     "role": "Consensus (YF+FactSet stub) + Upside + PER + DPS Yield",
     "registry_items": "讀 MDL001 universe + EXTRA_TICKERS",
     "output_formats": "Parquet · DuckDB · CSV · JSON · GSheet",
     "dependencies": "yfinance, pandas, requests",
     "lines": 1003, "last_updated": "2026-06-01"},

    {"mdl_id": "VDF-MDL006",     "category": "VDF Active",  "subcategory": "Financials",
     "name": "Financial Model + PE/PB Band","file": "VDF_MDL006_FinancialModel.py",
     "version": "1.0.0",                   "status": "Production",
     "role": "5y daily + 三大報表 + 比率 + 評價 + PE/PB Band Charts",
     "registry_items": "讀 MDL001 universe (+ EXTRA: NVDA, TSM, AAPL)",
     "output_formats": "Parquet · DuckDB · CSV · JSON · Plotly HTML Charts",
     "dependencies": "yfinance, pandas, plotly, pyarrow",
     "lines": 1385, "last_updated": "2026-06-01"},

    # ─────────────────────────────────────────────────────────────────────
    # [VDF Legacy - 過去累積 D2 / E0-E4 / Master]
    # ─────────────────────────────────────────────────────────────────────
    {"mdl_id": "VDF-D2-FRED",    "category": "VDF Legacy",  "subcategory": "Macro",
     "name": "FRED Engine v2",      "file": "VDF_D2_FREDEngine_v2.py",
     "version": "2.0",              "status": "Stable",
     "role": "FRED 300+ series registry + transform",
     "registry_items": "_FRED_REGISTRY (300+ series, theme/sub_theme/freq)",
     "output_formats": "CSV+Parquet (legacy)",
     "dependencies": "requests, pandas_datareader, pandas",
     "lines": None, "last_updated": "Earlier"},

    {"mdl_id": "VDF-D2-YF",      "category": "VDF Legacy",  "subcategory": "Universe",
     "name": "YFinance Engine v2",  "file": "VDF_D2_YFinanceEngine_v2.py",
     "version": "2.0",              "status": "Stable",
     "role": "YFinance 通用抓取 (price/financials)",
     "registry_items": "—",
     "output_formats": "CSV+Parquet",
     "dependencies": "yfinance, pandas",
     "lines": None, "last_updated": "Earlier"},

    {"mdl_id": "VDF-D2-DATA",    "category": "VDF Legacy",  "subcategory": "TW",
     "name": "TW Data Engines v1",  "file": "VDF_D2_DataEngines_v1.py",
     "version": "1.0",              "status": "Stable",
     "role": "TWSE / TPEX / MOPS 直連",
     "registry_items": "MOPS 財報函式 + TWSE 月營收",
     "output_formats": "CSV+Parquet",
     "dependencies": "requests, pandas",
     "lines": None, "last_updated": "Earlier"},

    {"mdl_id": "VDF-D2-GLOBAL",  "category": "VDF Legacy",  "subcategory": "Global",
     "name": "Global Universe Engine v2", "file": "VDF_D2_GlobalUniverseEngine_v2.py",
     "version": "2.0",                   "status": "Stable",
     "role": "全球指數 + 商品 + AKShare 內嵌 (BDI 395×5)",
     "registry_items": "Global indices + commodities",
     "output_formats": "CSV+Parquet",
     "dependencies": "yfinance, akshare, requests",
     "lines": None, "last_updated": "Earlier"},

    {"mdl_id": "VDF-D2-INTG",    "category": "VDF Legacy",  "subcategory": "TW",
     "name": "Integrated Engine v21","file": "VDF_D2_IntegratedEngine_v21.py",
     "version": "21.0",             "status": "Stable",
     "role": "TW 籌碼 / 三大法人 / 股票列表整合",
     "registry_items": "—",
     "output_formats": "CSV+Parquet",
     "dependencies": "requests, pandas",
     "lines": None, "last_updated": "Earlier"},

    {"mdl_id": "VDF-E0",         "category": "VDF Legacy",  "subcategory": "Registry",
     "name": "E0 Code Registry v1", "file": "VDF_E0_Registry_v1.py",
     "version": "1.0",              "status": "Stable",
     "role": "代號↔全名解析中樞 (9 類 default universe)",
     "registry_items": "TW股/指數/全球指數/FX/大宗/加密/ETF/FRED/AKShare",
     "output_formats": "JSON",
     "dependencies": "VIA_SSOT_Unified",
     "lines": None, "last_updated": "Earlier"},

    {"mdl_id": "VDF-E1",         "category": "VDF Legacy",  "subcategory": "Daily",
     "name": "E1 Daily Fetcher v1", "file": "VDF_E1_DailyFetcher_v1.py",
     "version": "1.0",              "status": "Stable",
     "role": "每日資訊一體 (價格+籌碼單日抓齊)",
     "registry_items": "—",
     "output_formats": "CSV+JSON",
     "dependencies": "yfinance, requests",
     "lines": None, "last_updated": "Earlier"},

    {"mdl_id": "VDF-E2",         "category": "VDF Legacy",  "subcategory": "Verify",
     "name": "E2 Quarterly Verifier v1", "file": "VDF_E2_QuarterlyVerifyFetcher_v1.py",
     "version": "1.0",                  "status": "Stable",
     "role": "單季/累計/年度交互驗證 (5 條對賬規則)",
     "registry_items": "CUM3Q-CUM2Q=Q3 等 5 規則",
     "output_formats": "CSV+JSON",
     "dependencies": "requests, pandas",
     "lines": None, "last_updated": "Earlier"},

    {"mdl_id": "VDF-E3",         "category": "VDF Legacy",  "subcategory": "AKShare",
     "name": "E3 AKShare Fetcher v1","file": "VDF_E3_AKShareFetcher_v1.py",
     "version": "1.0",              "status": "Stable",
     "role": "AKShare 獨立抓取 (CN 期貨/PMI/M2/BDI)",
     "registry_items": "13 codes (與 MDL003 同步)",
     "output_formats": "CSV+JSON",
     "dependencies": "akshare, pandas",
     "lines": None, "last_updated": "Earlier"},

    {"mdl_id": "VDF-E4",         "category": "VDF Legacy",  "subcategory": "Macro",
     "name": "E4 Macro Fetcher v1", "file": "VDF_E4_MacroFetcher_v1.py",
     "version": "1.0",              "status": "Stable",
     "role": "FRED + 其他宏觀 (用 D2 FRED 300+ registry)",
     "registry_items": "300+ FRED series",
     "output_formats": "CSV+JSON",
     "dependencies": "VDF_D2_FREDEngine_v2, pandas_datareader",
     "lines": None, "last_updated": "Earlier"},

    {"mdl_id": "VDF-MASTER",     "category": "VDF Legacy",  "subcategory": "Orchestrator",
     "name": "MASTER Orchestrator v1","file": "VDF_MASTER_Orchestrator_v1.py",
     "version": "1.0",               "status": "Stable",
     "role": "10-stage 循環 (TEST→DEBUG→OPTIMIZE→CONSOLIDATE→USER_TEST→FINAL)",
     "registry_items": "—",
     "output_formats": "HTML Dashboard",
     "dependencies": "All VDF E0-E4",
     "lines": None, "last_updated": "Earlier"},

    # ─────────────────────────────────────────────────────────────────────
    # [VRN Active - VRN 子系統 (VeritasReportNova)]
    # ─────────────────────────────────────────────────────────────────────
    {"mdl_id": "VRN-MDL004",     "category": "VRN Active",  "subcategory": "Crawler",
     "name": "TW Stock Crawler",    "file": "VRN_MDL004_TWStockCrawler_v1.py",
     "version": "1.0.0",            "status": "Stable",
     "role": "TW 全清單 + Cnyes Playwright + yfinance fallback",
     "registry_items": "TWSE/TPEX OpenAPI listings (~2,000 檔)",
     "output_formats": "CSV+JSON+Parquet",
     "dependencies": "requests, playwright, yfinance",
     "lines": 1125, "last_updated": "Earlier"},

    {"mdl_id": "VRN-MDL010",     "category": "VRN Active",  "subcategory": "Registry",
     "name": "Code Registry",       "file": "VRN_MDL010_CodeRegistry.py",
     "version": "1.0.0",            "status": "Stable",
     "role": "VRN 統一代號中樞 (73 項 universe)",
     "registry_items": "TW股/指數/全球/FX/大宗/加密/ETF/FRED/AKShare",
     "output_formats": "CSV+JSON",
     "dependencies": "VRN_SupportBridge",
     "lines": 471, "last_updated": "Earlier"},

    {"mdl_id": "VRN-MDL011",     "category": "VRN Active",  "subcategory": "Daily",
     "name": "Daily Fetcher",       "file": "VRN_MDL011_DailyFetcher.py",
     "version": "1.0.0",            "status": "Stable",
     "role": "BRIDGE.aegis_* + Celeritas parallel + yfinance fallback",
     "registry_items": "—",
     "output_formats": "CSV+JSON",
     "dependencies": "VRN_SupportBridge, yfinance",
     "lines": None, "last_updated": "Earlier"},

    {"mdl_id": "VRN-MDL012",     "category": "VRN Active",  "subcategory": "Verify",
     "name": "Quarterly Verifier",  "file": "VRN_MDL012_QuarterlyVerifier.py",
     "version": "1.0.0",            "status": "Stable",
     "role": "單季/累計/年度對賬",
     "registry_items": "—",
     "output_formats": "CSV+JSON",
     "dependencies": "VRN_SupportBridge",
     "lines": None, "last_updated": "Earlier"},

    {"mdl_id": "VRN-MDL013",     "category": "VRN Active",  "subcategory": "AKShare",
     "name": "AKShare Fetcher",     "file": "VRN_MDL013_AKShareFetcher.py",
     "version": "1.0.0",            "status": "Stable",
     "role": "AKShare CN 期貨/宏觀",
     "registry_items": "與 VDF MDL003 共用 13 codes",
     "output_formats": "CSV+JSON",
     "dependencies": "akshare, VRN_MDL010",
     "lines": 313, "last_updated": "Earlier"},

    {"mdl_id": "VRN-MDL014",     "category": "VRN Active",  "subcategory": "Macro",
     "name": "Macro Fetcher",       "file": "VRN_MDL014_MacroFetcher.py",
     "version": "1.0.0",            "status": "Stable",
     "role": "FRED + 其他宏觀 (用 D2 FRED 300+)",
     "registry_items": "300+ FRED series",
     "output_formats": "CSV+JSON",
     "dependencies": "VDF_D2_FREDEngine_v2, pandas_datareader",
     "lines": 358, "last_updated": "Earlier"},

    # ─────────────────────────────────────────────────────────────────────
    # [Supportive - 3 工具 + super_engine]
    # ─────────────────────────────────────────────────────────────────────
    {"mdl_id": "SUP-SSOT",       "category": "Supportive",  "subcategory": "Normalize",
     "name": "VIA SSOT Unified",    "file": "VIA_SSOT_Unified.py",
     "version": "—",                "status": "Locked SSOT",
     "role": "代號/欄位 normalize · 鎖定 TW_TICKER_REGEX",
     "registry_items": "TW_TICKER_REGEX · TW_BLOOMBERG_REGEX · TW_YFINANCE_REGEX",
     "output_formats": "Python module",
     "dependencies": "(none)",
     "lines": None, "last_updated": "Stable"},

    {"mdl_id": "SUP-AEGIS",      "category": "Supportive",  "subcategory": "Network",
     "name": "Veritas Aegis Nexus", "file": "VeritasAegisNexus.py",
     "version": "1.1",              "status": "Stable",
     "role": "UA 輪替 · rate-limit · robots 合規",
     "registry_items": "—",
     "output_formats": "Python module",
     "dependencies": "requests",
     "lines": 1811, "last_updated": "Earlier"},

    {"mdl_id": "SUP-CELERITAS",  "category": "Supportive",  "subcategory": "Accelerator",
     "name": "Veritas Celeritas",   "file": "VeritasCeleritas.py",
     "version": "1.1",              "status": "Stable",
     "role": "並行/JIT · joblib (import 538ms · xmap 1125×)",
     "registry_items": "—",
     "output_formats": "Python module",
     "dependencies": "joblib, numba (optional)",
     "lines": None, "last_updated": "Earlier"},

    {"mdl_id": "SUP-SUPER",      "category": "Supportive",  "subcategory": "Engine",
     "name": "super_engine",        "file": "super_engine.py",
     "version": "—",                "status": "Stable",
     "role": "環境 probe (available/installed mapping)",
     "registry_items": "—",
     "output_formats": "Python module",
     "dependencies": "(none)",
     "lines": None, "last_updated": "Earlier"},

    # ─────────────────────────────────────────────────────────────────────
    # [Control UI]
    # ─────────────────────────────────────────────────────────────────────
    {"mdl_id": "CTL-BRIDGE",     "category": "Control UI",  "subcategory": "Bridge",
     "name": "VRN Support Bridge",  "file": "VRN_SupportBridge.py",
     "version": "1.0.0",            "status": "Stable",
     "role": "4-level 上溯找 supportive_module / BRIDGE 單例",
     "registry_items": "aegis_*/ celeritas_parallel_map / ssot_normalize / probe_all",
     "output_formats": "Python module",
     "dependencies": "VIA_SSOT_Unified, VeritasAegisNexus, VeritasCeleritas",
     "lines": None, "last_updated": "Earlier"},

    {"mdl_id": "CTL-SERVER",     "category": "Control UI",  "subcategory": "Server",
     "name": "VRN Control Server",  "file": "VRN_ControlServer.py",
     "version": "1.0.0",            "status": "Stable",
     "role": "port 7788 ThreadingHTTPServer (健康+engine+probe+run)",
     "registry_items": "9 VDF engines + 5 VRN MDLs (14 engines schema)",
     "output_formats": "REST API JSON",
     "dependencies": "(stdlib)",
     "lines": None, "last_updated": "Earlier"},

    {"mdl_id": "CTL-CENTER",     "category": "Control UI",  "subcategory": "Frontend",
     "name": "VRN Control Center", "file": "VRN_ControlCenter.html",
     "version": "1.0.0",          "status": "Stable",
     "role": "3-col UI (BASE+Bridge+Batch | tabs | timeline)",
     "registry_items": "All/D2/D3/D5/VRN tabs",
     "output_formats": "HTML",
     "dependencies": "VRN_ControlServer:7788",
     "lines": None, "last_updated": "Earlier"},

    {"mdl_id": "CTL-DATAMOD",    "category": "Control UI",  "subcategory": "DataModule",
     "name": "VIA DataModule Controller","file": "VIA_DataModule_Controller.html",
     "version": "1.0.1",            "status": "Production",
     "role": "5-tab UI: MDL001/002/003-A/B/C 增刪查 + 執行",
     "registry_items": "5 tabs · 280+ items 預設 · localStorage 持久化",
     "output_formats": "HTML standalone",
     "dependencies": "(none, pure HTML+JS)",
     "lines": 728, "last_updated": "2026-06-01"},
]


# =====================================================================================
# 📦 Imports
# =====================================================================================

import os, sys, json, time, warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
warnings.filterwarnings('ignore')

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

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
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.tree import Tree
    from rich import box
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    console = None


# =====================================================================================
# 🎯 MasterRegistryEngine
# =====================================================================================

class MasterRegistryEngine:
    """29 個模組全生態註冊中樞."""
    VERSION = "1.0.0"

    def __init__(self):
        self.output_dir   = Path(BASE_DIR) / OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.duckdb_path  = self.output_dir / DUCKDB_FILENAME
        self.start_time   = time.time()
        # CLI args
        self.check_only   = "--check" in sys.argv
        self.filter_cat   = None
        for i, a in enumerate(sys.argv):
            if a == "--filter" and i+1 < len(sys.argv):
                self.filter_cat = sys.argv[i+1]
        self.df_registry  = None
        self.df_health    = None
        self.save_results = {}

    def show_header(self):
        if RICH_AVAILABLE:
            console.print(Panel(
                f"[bold]VDF MASTER MODULE REGISTRY · v{self.VERSION}[/bold]\n\n"
                f"📚 Total modules : {len(MODULE_REGISTRY)}\n"
                f"📁 Output dir    : {self.output_dir}\n"
                f"🎯 Mode          : {'CHECK ONLY' if self.check_only else 'FULL REGISTRATION'}\n"
                f"🔍 Filter        : {self.filter_cat or 'ALL categories'}",
                title="[bold blue]🏛️ VDF Master Registry[/bold blue]", border_style="blue"))
        else:
            print(f"=== MASTER REGISTRY · {len(MODULE_REGISTRY)} modules ===")

    def build_registry_df(self) -> "pd.DataFrame":
        """主註冊表."""
        if pd is None: return None
        df = pd.DataFrame(MODULE_REGISTRY)
        if self.filter_cat:
            df = df[df["category"].str.contains(self.filter_cat, case=False, na=False)]
        df["registered_at"] = datetime.now().isoformat(timespec='seconds')
        return df.reset_index(drop=True)

    def health_check(self) -> "pd.DataFrame":
        """檢查每個模組檔案是否實際存在 (在 Windows 真機上)."""
        if pd is None: return None
        rows = []
        for m in MODULE_REGISTRY:
            cat = m["category"]
            fn = m["file"]
            # 推定路徑
            if cat == "VDF Active" or cat == "VDF Legacy":
                base = Path(VDF_MODULES_ROOT)
            elif cat == "VRN Active":
                base = Path(VRN_MODULES_ROOT)
            elif cat == "Supportive":
                base = Path(SUPPORTIVE_ROOT)
            else:
                base = Path(VDF_MODULES_ROOT)
            full_path = base / fn

            # 沙盒環境路徑不存在是正常的
            exists = full_path.exists() if base.exists() else None  # None = 無法判定

            rows.append({
                "mdl_id":         m["mdl_id"],
                "name":           m["name"],
                "file":           fn,
                "expected_path":  str(full_path),
                "exists":         exists,
                "size_kb":        (full_path.stat().st_size // 1024) if (exists is True) else None,
                "category":       cat,
            })
        return pd.DataFrame(rows)

    def save_output(self, name: str, df: "pd.DataFrame") -> Dict:
        if pd is None or df is None or df.empty:
            self.save_results[name] = {"rows": 0, "outputs": []}
            return self.save_results[name]
        outputs = []
        # Parquet (必選)
        if OUTPUT_PARQUET and PYARROW_AVAILABLE:
            p = self.output_dir / f"{name}.parquet"
            try:
                df.to_parquet(p, index=False)
                outputs.append({"format": "parquet", "path": str(p),
                                "size_kb": p.stat().st_size // 1024})
            except Exception as e:
                outputs.append({"format": "parquet", "error": str(e)[:80]})
        # CSV (utf-8-sig)
        if OUTPUT_CSV:
            p = self.output_dir / f"{name}.csv"
            try:
                df.to_csv(p, index=False, encoding=CSV_ENCODING)
                outputs.append({"format": "csv", "path": str(p),
                                "size_kb": p.stat().st_size // 1024})
            except Exception as e:
                outputs.append({"format": "csv", "error": str(e)[:80]})
        # JSON
        if OUTPUT_JSON:
            p = self.output_dir / f"{name}.json"
            try:
                d = df.copy()
                for c in d.columns:
                    if pd.api.types.is_datetime64_any_dtype(d[c]):
                        d[c] = d[c].dt.strftime('%Y-%m-%d %H:%M:%S')
                d.to_json(p, orient="records", indent=2, force_ascii=False)
                outputs.append({"format": "json", "path": str(p),
                                "size_kb": p.stat().st_size // 1024})
            except Exception as e:
                outputs.append({"format": "json", "error": str(e)[:80]})
        # DuckDB
        if OUTPUT_DUCKDB and DUCKDB_AVAILABLE:
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
        self.save_results[name] = {"rows": len(df), "outputs": outputs}
        return self.save_results[name]

    def run(self) -> int:
        try:
            self.show_header()
            # 1. Build registry
            print("\n🔍 步驟 1/3: 建模組註冊表")
            self.df_registry = self.build_registry_df()
            print(f"   ✓ 共 {len(self.df_registry)} 個模組已登錄")

            # 2. Health check (檔案存在性)
            print("\n🩺 步驟 2/3: 健康檢查 (檔案存在性)")
            self.df_health = self.health_check()
            n_exist = (self.df_health["exists"] == True).sum() if pd is not None else 0
            n_miss  = (self.df_health["exists"] == False).sum() if pd is not None else 0
            n_unk   = self.df_health["exists"].isna().sum() if pd is not None else 0
            print(f"   ✓ 存在: {n_exist} · 缺失: {n_miss} · 未判定: {n_unk} (沙盒環境)")

            # 3. Save (除非 --check)
            if not self.check_only:
                print("\n💾 步驟 3/3: 多格式輸出")
                self.save_output("module_registry", self.df_registry)
                self.save_output("module_health",   self.df_health)
                for tbl, info in self.save_results.items():
                    fmts = [o.get("format") for o in info.get("outputs", []) if "error" not in o]
                    print(f"   ✓ {tbl:<24} → {info['rows']:>4} 列  [{' · '.join(fmts)}]")
            else:
                print("\n⏭️  步驟 3/3: --check 模式, 不寫檔")

            # 4. Rich Summary Matrix
            self._print_rich_summary()
            return 0
        except Exception as e:
            print(f"\n❌ 錯誤: {e}")
            if LOG_LEVEL == "DEBUG":
                import traceback; traceback.print_exc()
            return 1

    def _print_rich_summary(self):
        if not RICH_AVAILABLE: return
        elapsed = round(time.time() - self.start_time, 2)
        console.rule("[bold cyan]🏛️ VDF MASTER REGISTRY · Full Ecosystem Matrix[/bold cyan]")

        # ── Table 1: 分類分布 ──
        t = Table(title="📚 [bold]模組分類分布 (29 個)[/bold]",
                  box=box.ROUNDED, header_style="bold magenta")
        t.add_column("分類",          style="cyan", width=18)
        t.add_column("數量",          style="green", width=8, justify="right")
        t.add_column("狀態",          style="yellow", width=14)
        t.add_column("代表模組",      style="yellow", width=60)
        if pd is not None and self.df_registry is not None:
            for cat in self.df_registry["category"].unique():
                sub = self.df_registry[self.df_registry["category"] == cat]
                # 狀態統計
                status_dist = sub["status"].value_counts().to_dict()
                status_str = " · ".join(f"{s}: {c}" for s, c in status_dist.items())
                # 代表
                repr_names = ", ".join(sub["name"].head(3).tolist())
                if len(sub) > 3: repr_names += f" ... (+{len(sub)-3})"
                t.add_row(cat, str(len(sub)), status_str, repr_names)
        console.print(t)

        # ── Table 2: 全模組明細 ──
        t = Table(title=f"📋 [bold]全模組明細 ({len(self.df_registry) if self.df_registry is not None else 0} 個)[/bold]",
                  box=box.ROUNDED, header_style="bold magenta")
        t.add_column("MDL ID",        style="cyan",   width=16)
        t.add_column("Category",      style="yellow", width=12)
        t.add_column("Name",          style="green",  width=30)
        t.add_column("Output 格式",   style="yellow", width=36)
        t.add_column("Lines",         style="green",  width=8, justify="right")
        t.add_column("Status",        style="yellow", width=12)
        if pd is not None and self.df_registry is not None:
            for _, r in self.df_registry.iterrows():
                lines_str = f"{int(r['lines']):,}" if pd.notna(r.get('lines')) else "—"
                t.add_row(r["mdl_id"], r["category"], r["name"][:28],
                          r["output_formats"][:34], lines_str, r["status"])
        console.print(t)

        # ── Table 3: 輸出格式相容性矩陣 ──
        t = Table(title="💾 [bold]輸出格式相容性 (Parquet 必選 · 其他可選)[/bold]",
                  box=box.ROUNDED, header_style="bold magenta")
        t.add_column("MDL ID",      style="cyan",   width=16)
        t.add_column("Parquet",     style="green",  width=10, justify="center")
        t.add_column("DuckDB",      style="yellow", width=10, justify="center")
        t.add_column("CSV(utf8sig)",style="yellow", width=12, justify="center")
        t.add_column("JSON",        style="yellow", width=8,  justify="center")
        t.add_column("GSheet",      style="yellow", width=10, justify="center")
        t.add_column("HTML/Chart",  style="yellow", width=12, justify="center")
        if pd is not None and self.df_registry is not None:
            # 只顯示 VDF Active 系列 (本期 session)
            sub = self.df_registry[self.df_registry["category"] == "VDF Active"]
            for _, r in sub.iterrows():
                fmt = str(r["output_formats"]).lower()
                t.add_row(
                    r["mdl_id"],
                    "✅" if "parquet" in fmt else "—",
                    "✅" if "duckdb"  in fmt else ("⚠️" if "可加" in r["output_formats"] else "—"),
                    "✅" if "csv"     in fmt else "—",
                    "✅" if "json"    in fmt else ("⚠️" if "可加" in r["output_formats"] else "—"),
                    "✅" if "gsheet"  in fmt else ("⚠️" if "可加" in r["output_formats"] else "—"),
                    "✅" if ("html" in fmt or "chart" in fmt) else "—",
                )
        console.print(t)

        # ── Table 4: 健康檢查 (路徑可達性) ──
        if pd is not None and self.df_health is not None:
            t = Table(title="🩺 [bold]檔案健康檢查 (Windows 真機路徑)[/bold]",
                      box=box.ROUNDED, header_style="bold magenta")
            t.add_column("Category",  style="cyan",   width=15)
            t.add_column("存在 ✅",   style="green",  width=10, justify="right")
            t.add_column("缺失 ❌",   style="red",    width=10, justify="right")
            t.add_column("未判定 ⚠️", style="yellow", width=12, justify="right")
            t.add_column("總計",      style="yellow", width=8,  justify="right")
            for cat in self.df_health["category"].unique():
                sub = self.df_health[self.df_health["category"] == cat]
                ex = (sub["exists"] == True).sum()
                ms = (sub["exists"] == False).sum()
                un = sub["exists"].isna().sum()
                t.add_row(cat, str(ex), str(ms), str(un), str(len(sub)))
            console.print(t)

        # ── Table 5: Registry 項目摘要 ──
        t = Table(title="📊 [bold]Registry 項目摘要 (擷取目標數量)[/bold]",
                  box=box.ROUNDED, header_style="bold magenta")
        t.add_column("MDL ID",         style="cyan",   width=18)
        t.add_column("Registry Items", style="yellow", width=64)
        items_summary = {
            "VDF-MDL001-VRF":  "SSOT TW_TICKER_REGEX 鎖定: (?!0)(?!202[1-9])(?!2030)([1-9]\\d{3})",
            "VDF-MDL002":      "175 yf tickers (Indices 6 · Equity 7 · ETF×7類 86 · FX 8 · Commodity 9 · Bond 17 · Crypto 5)",
            "VDF-MDL003":      "FRED 47 series + AKShare 13 codes + AAII Excel + CNN dataviz API",
            "VDF-MDL005":      "讀 MDL001 universe + EXTRA: NVDA, TSM, AAPL",
            "VDF-MDL006":      "讀 MDL001 universe (5y daily × 三大報表 × annual+quarterly)",
            "VDF-D2-FRED":     "300+ FRED series (與 MDL003 互補)",
            "VRN-MDL010":      "73 項 universe (TW/Index/Global/FX/Comm/Crypto/ETF/FRED/AKShare)",
            "SUP-SSOT":        "TW_TICKER_REGEX · BLOOMBERG_REGEX · YFINANCE_REGEX (locked)",
        }
        for mdl, items in items_summary.items():
            t.add_row(mdl, items)
        console.print(t)

        # ── Final panel ──
        n_act_vdf   = len([m for m in MODULE_REGISTRY if m['category'] == 'VDF Active'])
        n_leg_vdf   = len([m for m in MODULE_REGISTRY if m['category'] == 'VDF Legacy'])
        n_vrn       = len([m for m in MODULE_REGISTRY if m['category'] == 'VRN Active'])
        n_sup       = len([m for m in MODULE_REGISTRY if m['category'] == 'Supportive'])
        n_ctl       = len([m for m in MODULE_REGISTRY if m['category'] == 'Control UI'])
        n_total     = len(MODULE_REGISTRY)
        n_parquet   = sum(1 for m in MODULE_REGISTRY if 'Parquet' in m.get('output_formats', ''))
        summary = (
            f"[bold]生態總覽[/bold]\n"
            f"  · VDF Active (本期)  : [green]{n_act_vdf}[/green] 個\n"
            f"  · VDF Legacy         : [yellow]{n_leg_vdf}[/yellow] 個\n"
            f"  · VRN Active         : [yellow]{n_vrn}[/yellow] 個\n"
            f"  · Supportive         : [cyan]{n_sup}[/cyan] 個\n"
            f"  · Control UI         : [cyan]{n_ctl}[/cyan] 個\n"
            f"  · [bold]TOTAL[/bold]              : [bold green]{n_total}[/bold green] 個\n\n"
            f"[bold]輸出格式相容[/bold]\n"
            f"  · 支援 Parquet      : {n_parquet} 個\n"
            f"  · DuckDB 單檔合併    : VDF MDL003/005/006 + MasterRegistry (4 個 .duckdb)\n"
            f"  · CSV (utf-8-sig)   : 全部 (解決中文 BOM)\n"
            f"  · JSON (indent=2)   : 全部本期 VDF Active\n"
            f"  · GSheet (stub)     : MDL003/005 需填 credential\n\n"
            f"[bold]耗時[/bold]              : {elapsed} 秒\n\n"
            f"[bold green]✅ 全生態模組註冊完成, 無遺漏項目[/bold green]"
        )
        console.print(Panel.fit(summary, title="[bold cyan]🎯 整體狀態[/bold cyan]",
                                border_style="cyan"))


# =====================================================================================
# 🎯 Entry
# =====================================================================================

def main():
    eng = MasterRegistryEngine()
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
