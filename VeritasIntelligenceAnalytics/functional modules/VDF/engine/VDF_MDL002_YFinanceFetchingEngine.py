#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
  VDF_MDL002_YFinanceFetchingEngine.py
================================================================================
  VERITAS DATA FRAMEWORK - MDL002  yfinance Universal Fetching Engine (Full)
  Version    : 17.0.0   |   Module ID : VDF-MDL002-YFE-001
  Asset ID   : VDF-MDL002-CLS-001
  Policy     : 功能只增不減 · append-only · SSOT · LL-compliant
  Lineage    : yfinance_universal_engine_v5 (1242 lines) → MDL002 v17 (全宇宙)

ARCHITECTURE (架構不改)
================================================================================
  v5 全部架構 100% 保留:
    [1] ALL PARAMETERS ON THE TOP (基本設定 / 時間 / 數據 / I/O / 處理 / MARKETS)
    [2] SSOT regex 雙保險治理 (VIA_SSOT_Unified 主來源 + 內嵌 regex fallback)
    [3] MARKETS_REGEX_MAP / ASSET_CLASS_RULES routing
    [4] FileManager (CSV/Parquet + backup + incremental)
    [5] DataValidator (清理 + 去重 + 驗證)
    [6] FinancialDataFetcher (依資產類別 routing + Adj Close 正規化)
    [7] YFinanceUniverseTool (主程式)
    [8] 互動式選單 (--menu)

v17 新增 (only-additive)
================================================================================
  CAT-03 ETF 完整補齊 (依 VDF ETF 宇宙矩陣 圖2):
    ETF_REGION_GLOBAL (A)   — 全球 / 區域股票指數 ETF (14 檔)
    ETF_SECTOR_US     (B)   — 美國產業 / 板塊 ETF (16 檔, SPDR Select Sectors)
    ETF_BONDS         (C)   — 債券 ETF (11 檔, 期限 × 信評)
    ETF_THEMATIC      (D)   — 主題 / 因子 / 商品 / 槓桿反向 (12 檔)
    ETF_HELPER        (E)   — 輔助指標 (美元 / 波動率 / 現金 等價) (5 檔)
    ETF_TW_PASSIVE    (F)   — 台股本土被動式 ETF (9 檔)
    ETF_TW_ACTIVE     (G)   — 台股主動式 ETF (25 檔, 依 ActiveETF Matrix v8)

  資金流計算 (依 圖3 TIER-2 + TIER-4):
    TIER-2: dollar_vol / dvol_ma5 / dvol_ma20 / dvol_ratio
           ret_1d / ret_5d / ret_20d / pv_signal (INFLOW/OUTFLOW)
           rs_vs_spy / rs_ma10 / rs_trend
    TIER-4: risk_on_off / hy_spread_proxy / growth_vs_value
           em_rotation / semicon_momentum / cash_parking / hedge_panic

  加速 (功能只增不減):
    yf.download batch (一次抓多個 ticker)
    ThreadPoolExecutor 並發 (多 batch 同時抓)
    Session pool (HTTPAdapter retries)

  Rich Summary Matrix (詳細彙總):
    8 張表 + Panel + Final banner

USAGE
================================================================================
  python VDF_MDL002_YFinanceFetchingEngine.py
  python VDF_MDL002_YFinanceFetchingEngine.py --menu
  python VDF_MDL002_YFinanceFetchingEngine.py --etf-only      # 只抓 ETF
  python VDF_MDL002_YFinanceFetchingEngine.py --non-etf-only  # v5 等價 (跳過 ETF)
  python VDF_MDL002_YFinanceFetchingEngine.py --no-flows      # 關閉 ETF 資金流計算
  python VDF_MDL002_YFinanceFetchingEngine.py --no-pause
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

# =====================================================================================
# 📋 ALL PARAMETERS CONFIGURATION SECTION (v5 全保留 + v17 新增)
# =====================================================================================

# 🔧 [PARAM-1/9] 基本設定 (v5 原樣)
PROJECT_NAME       = "1-2YFinanceData"
BASE_DIR           = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VDF\dict"
OUTPUT_DIR         = "1-3-YFinanceUniverse"
ENABLE_INCREMENTAL = True

# 📅 [PARAM-2/9] 時間設定 (v5 原樣)
START_DATE              = "2018-01-01"
END_DATE                = "2025-06-18"
USE_CURRENT_DATE_AS_END = True

# 📊 [PARAM-3/9] 數據設定 (v5 保留 + v17 加速擴充)
BATCH_SIZE          = 5
MAX_RETRIES         = 3
RETRY_DELAY         = 2
REQUEST_TIMEOUT     = 30

# v17 加速: yf.download batch + ThreadPool
ENABLE_BATCH_DOWNLOAD = True   # yf.download 一次抓多個 ticker
YF_BATCH_SIZE         = 20     # 每批最多多少個 ticker (Yahoo 限制建議 <50)
ENABLE_THREADPOOL     = True   # 並發批次抓取
THREADPOOL_WORKERS    = 4      # 並發批次數 (避免被 ban)
ENABLE_YF_THREADS     = True   # yf.download 內部 threads=True 加速

# 📁 [PARAM-4/9] 檔案設定 (v5 原樣)
OUTPUT_FORMATS    = ["csv", "parquet"]
CSV_ENCODING      = "utf-8-sig"
ENABLE_BACKUP     = True
MAX_BACKUP_FILES  = 5

# 🎛️ [PARAM-5/9] 處理設定 (v5 原樣 + v17 新增資金流開關)
AUTO_DEDUPLICATE     = True
VALIDATE_DATA        = True
ENABLE_PROGRESS_BAR  = True
LOG_LEVEL            = "INFO"

# v17 ETF 資金流計算開關 (依 圖3 TIER-2/TIER-4)
ENABLE_ETF_FLOW_CALC   = True   # 主開關
FLOW_DVOL_MA5_WINDOW   = 5
FLOW_DVOL_MA20_WINDOW  = 20
FLOW_RS_MA10_WINDOW    = 10
FLOW_RS_TREND_LAG      = 5
FLOW_PV_VOL_THRESHOLD  = 0.20   # vol_chg > 0.20 才標 INFLOW/OUTFLOW
FLOW_SPY_BENCHMARK     = "SPY"  # 相對強度基準

# v17 複合信號計算開關 (TIER-4)
ENABLE_COMPOSITE_SIGNALS = True

# 🌍 [PARAM-6/9] 市場配置 — MARKETS (v5 11 group 全保留 + v17 ETF 7 group 新增)
MARKETS = {
    # ==================================================================================
    # CAT-01 國際股票指數 (Stock Market Indices) — 無 Adj Close, OHLCV only [v5 保留]
    # ==================================================================================
    "INDICES_US": {
        "^GSPC": "S&P 500",
        "^NDX":  "Nasdaq 100",
        "^DJI":  "Dow Jones",
        "^RUT":  "Russell 2000",
        "^VIX":  "VIX",
        "^SOX":  "Philadelphia Semiconductor",
    },
    "INDICES_ASIA": {
        "^N225":     "Nikkei 225",
        "^TOPX":     "Topix",
        "^HSI":      "Hang Seng",
        "^HSCE":     "HSCEI 國企指數",
        "000001.SS": "上證綜指",
        "399001.SZ": "深證成指",
        "^KS11":     "KOSPI",
        "^STI":      "STI 新加坡",
        "^NSEI":     "Nifty 50",
        "^AXJO":     "ASX 200",
    },
    "INDICES_EUROPE": {
        "^GDAXI": "DAX 30",
        "^FTSE":  "FTSE 100",
        "^FCHI":  "CAC 40",
    },

    # ==================================================================================
    # CAT-02 國際個股 + 台股個股 — 有 Adj Close [v5 保留]
    # ==================================================================================
    "EQUITY_US": {
        "AAPL":  "Apple",
        "MSFT":  "Microsoft",
        "NVDA":  "NVIDIA",
        "GOOGL": "Alphabet",
        "AMZN":  "Amazon",
        "META":  "Meta",
        "TSLA":  "Tesla",
        "TSM":   "TSMC ADR",
        "AVGO":  "Broadcom",
        "AMD":   "AMD",
    },
    "EQUITY_TW_LISTED": {
        "2330.TW": "台積電",
        "2317.TW": "鴻海",
        "2454.TW": "聯發科",
        "2308.TW": "台達電",
        "2382.TW": "廣達",
        "2891.TW": "中信金",
        "2412.TW": "中華電",
        "1301.TW": "台塑",
        "2603.TW": "長榮",
        "3008.TW": "大立光",
    },
    "EQUITY_TW_OTC": {
        "6415.TWO": "矽力-KY",
        "3324.TWO": "雙鴻",
        "5483.TWO": "中美晶",
        "6488.TWO": "環球晶",
        "8069.TWO": "元太",
    },
    "EQUITY_ASIA": {
        "0700.HK":   "騰訊控股",
        "9988.HK":   "阿里巴巴",
        "7203.T":    "Toyota",
        "6758.T":    "Sony",
        "005930.KS": "Samsung Electronics",
        "600519.SS": "貴州茅台",
    },
    "EQUITY_EUROPE": {
        "SAP.DE":  "SAP",
        "BMW.DE":  "BMW",
        "BP.L":    "BP",
        "HSBA.L":  "HSBC",
    },

    # ==================================================================================
    # CAT-03 ETF (Exchange Traded Funds) — 有 Adj Close, 含配息還原 [v17 新增 7 大分類]
    # ==================================================================================

    # ── (A) 全球/區域股票指數 ETF — 判斷大資金進出哪個地區 (14 檔) ──
    "ETF_REGION_GLOBAL": {
        "SPY":  "S&P 500 (美國大盤基準)",
        "QQQ":  "Nasdaq 100 (科技板塊代理)",
        "IWM":  "Russell 2000 (美小型股風險偏好)",
        "EFA":  "已開發市場非美 (歐日韓資金輪動)",
        "EEM":  "新興市場 (EM vs DM 輪動)",
        "VWO":  "新興市場 Vanguard (EM 資金另一代理)",
        "FXI":  "中國大型股 (中國資金進出)",
        "MCHI": "MSCI China (A+H+ADR 合計)",
        "EWJ":  "日本 (日圓避險參考)",
        "EWY":  "韓國 (台韓半導體輪動)",
        "EWT":  "台灣 (外資台股持倉代理)",
        "EWZ":  "巴西 (原物料新興市場)",
        "INDA": "印度 (亞洲資金分流)",
        "EWG":  "德國 (歐洲工業代理)",
        "EZU":  "歐元區 (ECB 政策資金反應)",
    },

    # ── (B) 美國產業/板塊 ETF — SPDR Select Sectors 11 大 GICS + 細分 (16 檔) ──
    "ETF_SECTOR_US": {
        "XLK":  "科技 (AAPL MSFT NVDA 主導)",
        "XLF":  "金融 (升息受益/銀行風險)",
        "XLV":  "醫療保健 (防禦性避風港)",
        "XLE":  "能源 (油價連動/通膨預期)",
        "XLI":  "工業 (景氣循環領先)",
        "XLY":  "非必需消費 (消費信心)",
        "XLP":  "必需消費 (防禦/避險訊號)",
        "XLU":  "公用事業 (長債替代/降息受益)",
        "XLRE": "房地產 (利率敏感/REITs)",
        "XLB":  "材料 (商品周期連動)",
        "XLC":  "通訊服務 (GOOG META 主導)",
        "SOXX": "半導體 (台股最相關)",
        "SMH":  "半導體 VanEck (NVDA TSM 權重高)",
        "IBB":  "生技 (風險偏好生技指標)",
        "KRE":  "區域銀行 (銀行危機早期警報)",
        "ARKK": "創新科技主動 (高風險偏好溫度計)",
    },

    # ── (C) 債券 ETF — 期限 × 信評 (11 檔) ──
    "ETF_BONDS": {
        "SHY": "美國短債 1-3Y (Fed 短端利率代理)",
        "IEF": "美國中債 7-10Y (殖利率曲線中段)",
        "TLT": "美國長債 20Y+ (股債翹翹板核心)",
        "IEI": "美國中短債 3-7Y (曲線形狀輔助)",
        "LQD": "投資級公司債 (IG 信用利差)",
        "HYG": "高收益 (垃圾債) (HY 利差)",
        "JNK": "高收益 SPDR (HYG 配對驗證)",
        "TIP": "TIPS 通膨連結債 (Break-even 通膨率)",
        "BND": "全債市 Vanguard (整體債市基準)",
        "EMB": "新興市場主權債 (EM 信用風險溢價)",
        "MUB": "市政債免稅 (美國地方財政壓力)",
    },

    # ── (D) 主題/因子/商品/槓桿反向 ETF (12 檔) ──
    "ETF_THEMATIC": {
        "GLD":  "黃金 (避險/實質利率反向)",
        "IAU":  "黃金 iShares (GLD 配對驗證)",
        "SLV":  "白銀 (工業+避險雙屬性)",
        "USO":  "WTI 原油 (通膨/地緣衝突代理)",
        "DJP":  "商品指數 (大宗商品整體輪動)",
        "VTV":  "價值股因子 (價值 vs 成長輪動)",
        "VUG":  "成長股因子 (利率敏感成長)",
        "QUAL": "品質因子 (資金品質偏好)",
        "MTUM": "動能因子 (趨勢動能強弱)",
        "SQQQ": "Nasdaq 3X 放空 (反轉信號)",
        "TQQQ": "Nasdaq 3X 做多 (資金過度集中警示)",
        "SH":   "S&P 500 反向 1X (機構避險倉位估算)",
    },

    # ── (E) 輔助指標 ETF — 流動性 × 波動率 × 美元 (5 檔) ──
    "ETF_HELPER": {
        "UUP":  "美元指數多頭 (美元強弱→EM 資金方向)",
        "UDN":  "美元指數空頭 (UUP 配對)",
        "VIXY": "VIX 期貨多頭 (避險需求量化)",
        "BIL":  "T-Bill 短債 (現金等價物流量)",
        "SGOV": "0-3M 公債 (資金停泊規模)",
    },

    # ── (F) 台股本土被動式 ETF (9 檔) ──
    "ETF_TW_PASSIVE": {
        "0050.TW":   "元大台灣 50 (最大台股 ETF, 外資持倉代理)",
        "0056.TW":   "元大高股息 (配息型資金, 散戶資金偏好)",
        "00632R.TW": "元大台灣 50 反 1 (本土避險量化)",
        "006208.TW": "富邦台 50 (低費用競爭, 0050 分流監控)",
        "00878.TW":  "國泰永續高股息 (ESG 主題)",
        "00713.TW":  "元大台灣高息低波",
        "00919.TW":  "群益台灣精選高息",
        "00929.TW":  "復華台灣科技優息 (月配息高股息)",
        "00946.TW":  "群益台灣科技高息",
    },

    # ── (G) 台股主動式 ETF — 依 VIA_ActiveETF_Matrix_v8 (25 檔) ──
    "ETF_TW_ACTIVE": {
        # 400 系列
        "00400A.TW": "主動國泰動能高息",
        "00401A.TW": "主動摩根台灣鑫收",
        "00404A.TW": "主動國泰臺灣價值優選",
        "00405A.TW": "主動國泰臺灣科技領袖",
        "00406A.TW": "主動中信臺灣半導體精選",
        "00407A.TW": "主動中信臺灣高息動能",
        "00408A.TW": "主動永豐臺灣均衡成長",
        "00409A.TW": "主動第一金臺灣優選息收",
        "00410A.TW": "主動凱基臺灣價值動能",
        "00420A.TW": "主動安聯臺灣科技創新",
        "00423A.TW": "主動復華臺灣半導體優選",
        # 980 系列 (2025/05 首批)
        "00980A.TW": "主動野村臺灣優選 (台灣首檔, 2025/05/05)",
        "00981A.TW": "主動統一台股增長",
        "00982A.TW": "主動群益台灣強棒",
        "00984A.TW": "主動安聯台灣高息",
        "00985A.TW": "主動野村台灣 50",
        "00987A.TW": "主動台新優勢成長",
        # 990 系列
        "00991A.TW": "主動復華未來 50",
        "00992A.TW": "主動群益科技創新",
        "00993A.TW": "主動安聯台灣",
        "00994A.TW": "主動第一金台股優",
        "00995A.TW": "主動中信台灣卓越",
        "00996A.TW": "主動兆豐台灣豐收",
        "00997A.TW": "主動富邦臺灣 AI 成長",
        "00999A.TW": "主動野村高息成長",
    },

    # ==================================================================================
    # CAT-04 外匯 FX — 無 Adj Close, Close = spot rate [v5 保留]
    # ==================================================================================
    "CURRENCIES": {
        "TWD=X":    "USD/TWD",
        "EURUSD=X": "EUR/USD",
        "JPY=X":    "USD/JPY",
        "GBPUSD=X": "GBP/USD",
        "CNY=X":    "USD/CNY",
        "KRW=X":    "USD/KRW",
        "AUDUSD=X": "AUD/USD",
        "DX-Y.NYB": "DXY 美元指數",
    },

    # ==================================================================================
    # CAT-05 大宗商品期貨 — 無 Adj Close, 需處理換月 [v5 保留]
    # ==================================================================================
    "COMMODITIES": {
        "GC=F": "黃金 Gold",
        "SI=F": "白銀 Silver",
        "CL=F": "WTI 原油",
        "BZ=F": "布蘭特原油",
        "NG=F": "天然氣",
        "HG=F": "銅 Copper",
        "ZS=F": "大豆 Soybean",
        "ZW=F": "小麥 Wheat",
        "ES=F": "S&P 500 Futures",
        "NQ=F": "Nasdaq 100 Futures",
        "YM=F": "Dow Jones Futures",
    },

    # ==================================================================================
    # CAT-06 債券殖利率 — Close = 殖利率%, 無 Volume [v5 保留]
    # ==================================================================================
    "BONDS_YIELDS": {
        "^IRX": "美國 13週 T-Bill",
        "^FVX": "美國 5Y 殖利率",
        "^TNX": "美國 10Y 殖利率",
        "^TYX": "美國 30Y 殖利率",
    },

    # ==================================================================================
    # CAT-07 加密貨幣 — 24/7, Adj Close = Close [v5 保留]
    # ==================================================================================
    "CRYPTO": {
        "BTC-USD": "Bitcoin",
        "ETH-USD": "Ethereum",
        "SOL-USD": "Solana",
        "BNB-USD": "BNB",
        "XRP-USD": "XRP",
    },
}

# 🏷️ [PARAM-7/9] 資產類別 routing — 決定 auto_adjust 與欄位後處理 (v5 保留 + v17 ETF 7 group)
ASSET_CLASS_RULES = {
    # v5 既有
    "INDICES_US":        {"asset_class": "INDEX",     "auto_adjust": False, "has_adj_close": False, "has_volume": True},
    "INDICES_ASIA":      {"asset_class": "INDEX",     "auto_adjust": False, "has_adj_close": False, "has_volume": True},
    "INDICES_EUROPE":    {"asset_class": "INDEX",     "auto_adjust": False, "has_adj_close": False, "has_volume": True},
    "EQUITY_US":         {"asset_class": "EQUITY",    "auto_adjust": False, "has_adj_close": True,  "has_volume": True},
    "EQUITY_TW_LISTED":  {"asset_class": "EQUITY",    "auto_adjust": False, "has_adj_close": True,  "has_volume": True},
    "EQUITY_TW_OTC":     {"asset_class": "EQUITY",    "auto_adjust": False, "has_adj_close": True,  "has_volume": True},
    "EQUITY_ASIA":       {"asset_class": "EQUITY",    "auto_adjust": False, "has_adj_close": True,  "has_volume": True},
    "EQUITY_EUROPE":     {"asset_class": "EQUITY",    "auto_adjust": False, "has_adj_close": True,  "has_volume": True},
    "CURRENCIES":        {"asset_class": "FX",        "auto_adjust": False, "has_adj_close": False, "has_volume": False},
    "COMMODITIES":       {"asset_class": "FUTURES",   "auto_adjust": False, "has_adj_close": False, "has_volume": True},
    "BONDS_YIELDS":      {"asset_class": "YIELD",     "auto_adjust": False, "has_adj_close": False, "has_volume": False},
    "CRYPTO":            {"asset_class": "CRYPTO",    "auto_adjust": False, "has_adj_close": True,  "has_volume": True},
    # v17 ETF (全部有 Adj Close, has_volume = True, 都計算資金流)
    "ETF_REGION_GLOBAL": {"asset_class": "ETF_A",     "auto_adjust": False, "has_adj_close": True,  "has_volume": True},
    "ETF_SECTOR_US":     {"asset_class": "ETF_B",     "auto_adjust": False, "has_adj_close": True,  "has_volume": True},
    "ETF_BONDS":         {"asset_class": "ETF_C",     "auto_adjust": False, "has_adj_close": True,  "has_volume": True},
    "ETF_THEMATIC":      {"asset_class": "ETF_D",     "auto_adjust": False, "has_adj_close": True,  "has_volume": True},
    "ETF_HELPER":        {"asset_class": "ETF_E",     "auto_adjust": False, "has_adj_close": True,  "has_volume": True},
    "ETF_TW_PASSIVE":    {"asset_class": "ETF_F",     "auto_adjust": False, "has_adj_close": True,  "has_volume": True},
    "ETF_TW_ACTIVE":     {"asset_class": "ETF_G",     "auto_adjust": False, "has_adj_close": True,  "has_volume": True},
}

# 🎯 [PARAM-8/9] ETF group 集合 (用於資金流計算範圍判定)
ETF_GROUPS = {"ETF_REGION_GLOBAL", "ETF_SECTOR_US", "ETF_BONDS", "ETF_THEMATIC",
              "ETF_HELPER", "ETF_TW_PASSIVE", "ETF_TW_ACTIVE"}

# 🌐 [PARAM-9/9] HTTP / Session 設定 (v17 加速擴充)
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}


# =====================================================================================
# 📦 簡化依賴管理 / Simplified Dependency Management (v5 保留)
# =====================================================================================

import os
import re
import sys
import json
import time
import warnings
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

warnings.filterwarnings('ignore')

# =====================================================================================
# 🔒 CORE TICKER REGEX DEFINITIONS (EXACT NAMES - DO NOT CHANGE)
# 此區為 SSOT 鎖死區. 透過 YFinance 擷取的代碼統稱為 YFinance Ticker.
#
# 雙保險機制:
#   主來源: VIA_SSOT_Unified (rule_id RGX-FIN-TW-* / RGX-FIN-YF-*)
#   備援:   本檔內嵌 regex (與 SSOT 同步, 在 SSOT 不可載入時自動接手)
#
# v17 擴充: 新增 TW Active ETF regex (5碼 + A + .TW)
# =====================================================================================

# ── 三種台股代號鎖死規則 (LOCKED, v5 原樣) ───────────────────────────────────
TW_TICKER_REGEX    = re.compile(r"^(?!202[1-9])(?!2030)[1-9]\d{3}$")
TW_BLOOMBERG_REGEX = re.compile(r"\b[1-9]\d{3} TT\b")
TW_YFINANCE_REGEX  = re.compile(r"\b[1-9]\d{3}\.(TW|TWO)\b")
TW_CODE_EXTRACT    = re.compile(r"\b([1-9]\d{3})(?:\s+TT|\.TWO?|\b)")

# ── v17 新增: 台股 ETF regex ────────────────────────────────────────────────
# 被動式: 4-6 碼數字 + .TW (0050.TW, 0056.TW, 00878.TW, 006208.TW)
TW_ETF_PASSIVE_REGEX = re.compile(r"^\d{4,6}\.TW$")
# 主動式: 5 碼數字 + A + .TW (00980A.TW, 00400A.TW) — 主動式統一 5 碼+A
TW_ETF_ACTIVE_REGEX  = re.compile(r"^\d{5}A\.TW$")
# 槓桿反向: 4-6 碼數字 + R/L + 可選數字 + .TW (00632R.TW, 0050R.TW)
TW_ETF_LEVERAGED_REGEX = re.compile(r"^\d{4,6}[RL]\d?\.TW$")
# 統一台股 ETF: 上述三種任一
TW_ETF_REGEX = re.compile(r"^\d{4,6}([A]|[RL]\d?)?\.TW$")

# ── 國際 YFinance Ticker schema (v5 保留) ───────────────────────────────────
YF_INDEX_REGEX     = re.compile(r"^\^[A-Z0-9_]+$|^\d{6}\.S[SZ]$")
YF_EQUITY_US_REGEX = re.compile(r"^[A-Z][A-Z0-9.\-]{0,5}$")
YF_EQUITY_HK_REGEX = re.compile(r"^\d{4,5}\.HK$")
YF_EQUITY_JP_REGEX = re.compile(r"^\d{4}\.T$")
YF_EQUITY_KR_REGEX = re.compile(r"^\d{6}\.K[SQ]$")
YF_EQUITY_CN_REGEX = re.compile(r"^\d{6}\.S[SZ]$")
YF_EQUITY_EU_REGEX = re.compile(r"^[A-Z][A-Z0-9]{0,4}\.(DE|L|PA|MI|AS|MC|SW)$")
YF_EQUITY_AU_REGEX = re.compile(r"^[A-Z]{2,4}\.AX$")
YF_EQUITY_IN_REGEX = re.compile(r"^[A-Z]+\.(NS|BO)$")
YF_EQUITY_CA_REGEX = re.compile(r"^[A-Z]+\.(TO|V)$")
YF_FX_REGEX        = re.compile(r"^[A-Z]{3,6}=X$|^DX-Y\.NYB$")
YF_FUTURES_REGEX   = re.compile(r"^[A-Z0-9]{1,4}=F$")
YF_CRYPTO_REGEX    = re.compile(r"^[A-Z0-9]{2,10}-USD$")

# v17 新增: 美股 ETF regex (與 EQUITY_US 共用, 但放寬限制以容納 SPDR 等)
YF_ETF_US_REGEX = re.compile(r"^[A-Z]{1,5}$")

# ── DEPRECATED 別名 (向後相容, v5 保留) ──────────────────────────────────────
INTL_INDEX_REGEX     = YF_INDEX_REGEX
INTL_EQUITY_US_REGEX = YF_EQUITY_US_REGEX
INTL_EQUITY_HK_REGEX = YF_EQUITY_HK_REGEX
INTL_EQUITY_JP_REGEX = YF_EQUITY_JP_REGEX
INTL_EQUITY_KR_REGEX = YF_EQUITY_KR_REGEX
INTL_EQUITY_CN_REGEX = YF_EQUITY_CN_REGEX
INTL_EQUITY_EU_REGEX = YF_EQUITY_EU_REGEX
INTL_EQUITY_AU_REGEX = YF_EQUITY_AU_REGEX
INTL_EQUITY_IN_REGEX = YF_EQUITY_IN_REGEX
INTL_EQUITY_CA_REGEX = YF_EQUITY_CA_REGEX
INTL_FX_REGEX        = YF_FX_REGEX
INTL_FUTURES_REGEX   = YF_FUTURES_REGEX
INTL_CRYPTO_REGEX    = YF_CRYPTO_REGEX

# 各 MARKETS group 對映的 regex (v5 保留 + v17 ETF 7 group)
MARKETS_REGEX_MAP = {
    # v5 既有
    "INDICES_US":       YF_INDEX_REGEX,
    "INDICES_ASIA":     YF_INDEX_REGEX,
    "INDICES_EUROPE":   YF_INDEX_REGEX,
    "EQUITY_US":        YF_EQUITY_US_REGEX,
    "EQUITY_TW_LISTED": TW_YFINANCE_REGEX,
    "EQUITY_TW_OTC":    TW_YFINANCE_REGEX,
    "EQUITY_ASIA":      None,
    "EQUITY_EUROPE":    YF_EQUITY_EU_REGEX,
    "CURRENCIES":       YF_FX_REGEX,
    "COMMODITIES":      YF_FUTURES_REGEX,
    "BONDS_YIELDS":     YF_INDEX_REGEX,
    "CRYPTO":           YF_CRYPTO_REGEX,
    # v17 ETF
    "ETF_REGION_GLOBAL": YF_ETF_US_REGEX,
    "ETF_SECTOR_US":     YF_ETF_US_REGEX,
    "ETF_BONDS":         YF_ETF_US_REGEX,
    "ETF_THEMATIC":      YF_ETF_US_REGEX,
    "ETF_HELPER":        YF_ETF_US_REGEX,
    "ETF_TW_PASSIVE":    TW_ETF_REGEX,
    "ETF_TW_ACTIVE":     TW_ETF_ACTIVE_REGEX,
}

# EQUITY_ASIA 子 regex (v5 保留)
ASIA_SUFFIX_REGEX_MAP = [
    ('.HK', YF_EQUITY_HK_REGEX),
    ('.T',  YF_EQUITY_JP_REGEX),
    ('.KS', YF_EQUITY_KR_REGEX),
    ('.KQ', YF_EQUITY_KR_REGEX),
    ('.SS', YF_EQUITY_CN_REGEX),
    ('.SZ', YF_EQUITY_CN_REGEX),
]

# ── 雙保險: SSOT 治理 hook (v5 保留) ─────────────────────────────────────────
_SSOT_VALIDATOR = None
_ssot_extract   = None
try:
    from VIA_SSOT_Unified import extract as _ssot_extract  # noqa: F401
    _SSOT_VALIDATOR = "VIA_SSOT_Unified (主來源)"
except Exception:
    _SSOT_VALIDATOR = "內嵌 regex (fallback)"


def _ssot_match(rule_name: str, value: str) -> bool:
    """SSOT 主驗證 (v5 保留)."""
    if _ssot_extract is None:
        return False
    try:
        result = _ssot_extract(rule_name, value)
        return bool(result) and result == value
    except Exception:
        return False


def validate_ticker(ticker: str, market_group: str) -> Tuple[bool, str]:
    """
    驗證單一 ticker 是否符合該 market_group 的 regex schema.
    雙保險邏輯: SSOT 主驗 → 內嵌 regex fallback.
    v17 擴充: 台股 ETF 主動式 / 被動式 / 槓桿反向 三段判定.
    """
    if not ticker or not isinstance(ticker, str):
        return False, "ticker 為空或非字串"

    # ── 台股雙鎖 (TW_LISTED / TW_OTC): 三段式檢查 (v5 保留) ──
    if market_group in ("EQUITY_TW_LISTED", "EQUITY_TW_OTC"):
        ssot_ok  = _ssot_match("TW_YFINANCE_TICKER", ticker)
        regex_ok = bool(TW_YFINANCE_REGEX.fullmatch(ticker))
        if not (ssot_ok or regex_ok):
            return False, "不符合 TW_YFINANCE_REGEX: 必須為 [1-9]\\d{3}\\.(TW|TWO)"
        if market_group == "EQUITY_TW_LISTED" and not ticker.endswith(".TW"):
            return False, f"上市股票 suffix 必須為 .TW, 得到: {ticker}"
        if market_group == "EQUITY_TW_OTC" and not ticker.endswith(".TWO"):
            return False, f"上櫃股票 suffix 必須為 .TWO, 得到: {ticker}"
        m = TW_CODE_EXTRACT.search(ticker)
        if not m:
            return False, "無法提取四碼台股代號"
        code = m.group(1)
        ssot_code_ok  = _ssot_match("TW_STOCK_CODE_4DIGIT", code)
        regex_code_ok = bool(TW_TICKER_REGEX.fullmatch(code))
        if not (ssot_code_ok or regex_code_ok):
            return False, f"四碼代號 {code} 不符合母代號規則 (排除權證等)"
        return True, f"TW ticker OK ({code})"

    # ── v17 新增: 台股 ETF 雙鎖 ──
    if market_group == "ETF_TW_PASSIVE":
        if TW_ETF_REGEX.fullmatch(ticker):
            return True, "TW ETF passive OK"
        return False, f"不符合 TW ETF passive regex: {ticker}"

    if market_group == "ETF_TW_ACTIVE":
        if TW_ETF_ACTIVE_REGEX.fullmatch(ticker):
            return True, "TW ETF active OK (5digits+A+.TW)"
        return False, f"不符合 TW ETF active regex: 必須為 \\d{{5}}A\\.TW, 得到: {ticker}"

    # ── EQUITY_ASIA: 依 suffix 分流 (v5 保留) ──
    if market_group == "EQUITY_ASIA":
        for suffix, regex in ASIA_SUFFIX_REGEX_MAP:
            if ticker.endswith(suffix):
                if regex.fullmatch(ticker):
                    return True, f"Asia YF ticker OK ({suffix})"
                else:
                    return False, f"不符合 {suffix} 市場 regex"
        return False, "未知 Asia suffix"

    # ── 其他 group: 直接用對映表 (v5 保留) ──
    regex = MARKETS_REGEX_MAP.get(market_group)
    if regex is None:
        return True, "no regex defined (skipped)"
    if regex.fullmatch(ticker):
        return True, "OK"
    return False, f"不符合 {market_group} 的 YF regex schema"


def detect_tw_ticker_format(s: str) -> Optional[str]:
    """判斷字串屬於哪種台股代號格式 (v5 保留 + v17 ETF 識別)."""
    if not s or not isinstance(s, str):
        return None
    if TW_ETF_ACTIVE_REGEX.fullmatch(s):
        return "TW_ETF_ACTIVE"
    if TW_ETF_REGEX.fullmatch(s):
        return "TW_ETF_PASSIVE"
    if TW_YFINANCE_REGEX.fullmatch(s):
        return "YFINANCE"
    if TW_BLOOMBERG_REGEX.fullmatch(s):
        return "BLOOMBERG"
    if TW_TICKER_REGEX.fullmatch(s):
        return "BARE"
    return None


# =====================================================================================
# 🔧 核心依賴檢查 (v5 保留)
# =====================================================================================

def check_and_install_dependencies():
    """檢查並安裝核心依賴"""
    required = {
        'pandas':   'pip install pandas',
        'yfinance': 'pip install yfinance',
        'requests': 'pip install requests'
    }
    optional = {
        'rich':    'pip install rich',
        'pyarrow': 'pip install pyarrow',
        'numpy':   'pip install numpy'
    }
    print("🔍 檢查依賴套件...")
    missing = []
    for package in required:
        try:
            __import__(package); print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (必要)"); missing.append(package)
    for package in optional:
        try:
            __import__(package); print(f"✅ {package}")
        except ImportError:
            print(f"⚠️ {package} (可選)")
    if missing:
        install = input(f"\n是否安裝缺失的套件？(y/n): ").lower() == 'y'
        if install:
            for package in missing:
                print(f"📦 安裝 {package}...")
                try:
                    subprocess.run(required[package].split(), check=True)
                    print(f"✅ {package} 安裝成功")
                except Exception:
                    print(f"❌ {package} 安裝失敗")
    return len(missing) == 0


# 導入核心套件 (v5 保留 + v17 numpy 強制)
try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    print("❌ pandas/numpy 未安裝")
    PANDAS_AVAILABLE = False

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    print("❌ yfinance 未安裝")
    YFINANCE_AVAILABLE = False

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
    from rich import box
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    print("⚠️ rich 未安裝，使用簡化顯示")
    RICH_AVAILABLE = False
    console = None

try:
    import pyarrow as pa
    PYARROW_AVAILABLE = True
except ImportError:
    PYARROW_AVAILABLE = False


# =====================================================================================
# 🛠️ 核心工具類 (v5 保留 + v17 ETF 衍生資料支援)
# =====================================================================================

class FileManager:
    """檔案管理器 (v5 原樣 + v17 新增 ETF flow 衍生表)"""

    def __init__(self):
        self.base_dir = Path(BASE_DIR)
        self.output_dir = self.base_dir / OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        # 主價量檔 (v5)
        self.csv_file     = self.output_dir / "YFinanceData.csv"
        self.parquet_file = self.output_dir / "YFinanceData.parquet"
        # 標的清單 (v5)
        self.stock_list_file = self.base_dir / "YFinanceUniverseList.csv"
        # 備份 (v5)
        self.backup_dir = self.output_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        # v17 新增: ETF 衍生表
        self.etf_flow_csv     = self.output_dir / "ETF_FlowSignals.csv"
        self.etf_flow_parquet = self.output_dir / "ETF_FlowSignals.parquet"
        self.composite_csv    = self.output_dir / "ETF_CompositeSignals.csv"

    def create_backup(self, file_path: Path) -> bool:
        """創建備份 (v5 原樣)"""
        if not ENABLE_BACKUP or not file_path.exists():
            return True
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            import shutil
            shutil.copy2(file_path, self.backup_dir / f"{timestamp}_{file_path.name}")
            self.cleanup_old_backups()
            return True
        except Exception as e:
            print(f"⚠️ 備份失敗: {e}")
            return False

    def cleanup_old_backups(self):
        try:
            backups = sorted(self.backup_dir.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)
            for backup in backups[MAX_BACKUP_FILES:]:
                backup.unlink()
        except Exception:
            pass

    def load_existing_data(self) -> Optional["pd.DataFrame"]:
        """v5 原樣"""
        if not ENABLE_INCREMENTAL:
            return None
        try:
            if self.parquet_file.exists() and PYARROW_AVAILABLE:
                print("📂 載入現有 Parquet 數據...")
                return pd.read_parquet(self.parquet_file)
            elif self.csv_file.exists():
                print("📂 載入現有 CSV 數據...")
                return pd.read_csv(self.csv_file, encoding=CSV_ENCODING)
            else:
                print("🆕 未發現現有數據")
                return None
        except Exception as e:
            print(f"⚠️ 載入數據失敗: {e}")
            return None

    def save_data(self, df: "pd.DataFrame") -> Dict[str, bool]:
        """v5 原樣"""
        results = {}
        if df is None or df.empty:
            print("⚠️ 無數據需要保存")
            return {"csv": False, "parquet": False}
        self.create_backup(self.csv_file)
        if PYARROW_AVAILABLE:
            self.create_backup(self.parquet_file)
        try:
            df.to_csv(self.csv_file, index=False, encoding=CSV_ENCODING)
            results["csv"] = True
            print(f"✅ CSV 已保存: {self.csv_file}")
        except Exception as e:
            print(f"❌ CSV 保存失敗: {e}")
            results["csv"] = False
        if PYARROW_AVAILABLE and "parquet" in OUTPUT_FORMATS:
            try:
                df.to_parquet(self.parquet_file, index=False)
                results["parquet"] = True
                print(f"✅ Parquet 已保存: {self.parquet_file}")
            except Exception as e:
                print(f"❌ Parquet 保存失敗: {e}")
                results["parquet"] = False
        else:
            results["parquet"] = False
        return results

    def save_etf_flow(self, df: "pd.DataFrame") -> Dict[str, bool]:
        """v17 新增: 儲存 ETF 資金流衍生表"""
        results = {"csv": False, "parquet": False}
        if df is None or df.empty:
            return results
        try:
            df.to_csv(self.etf_flow_csv, index=False, encoding=CSV_ENCODING)
            results["csv"] = True
            print(f"✅ ETF Flow CSV 已保存: {self.etf_flow_csv.name}")
        except Exception as e:
            print(f"⚠️ ETF Flow CSV 失敗: {e}")
        if PYARROW_AVAILABLE and "parquet" in OUTPUT_FORMATS:
            try:
                df.to_parquet(self.etf_flow_parquet, index=False)
                results["parquet"] = True
                print(f"✅ ETF Flow Parquet 已保存: {self.etf_flow_parquet.name}")
            except Exception as e:
                print(f"⚠️ ETF Flow Parquet 失敗: {e}")
        return results

    def save_composite(self, df: "pd.DataFrame") -> bool:
        """v17 新增: 儲存複合信號表"""
        if df is None or df.empty:
            return False
        try:
            df.to_csv(self.composite_csv, index=False, encoding=CSV_ENCODING)
            print(f"✅ Composite Signals 已保存: {self.composite_csv.name}")
            return True
        except Exception as e:
            print(f"⚠️ Composite Signals 失敗: {e}")
            return False


class DataValidator:
    """數據驗證器 (v5 原樣)"""

    @staticmethod
    def validate_dataframe(df) -> Dict[str, Any]:
        if df is None or df.empty:
            return {"valid": False, "error": "數據框為空"}
        required_columns = ["Date", "YFinance Ticker", "Close"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return {"valid": False, "error": f"缺少必要欄位: {missing_columns}"}
        issues = []
        try: pd.to_datetime(df["Date"])
        except Exception: issues.append("日期格式錯誤")
        try: pd.to_numeric(df["Close"])
        except Exception: issues.append("價格格式錯誤")
        return {"valid": len(issues) == 0, "issues": issues, "records": len(df),
                "date_range": f"{df['Date'].min()} to {df['Date'].max()}" if not df.empty else "N/A"}

    @staticmethod
    def clean_data(df):
        if df is None or df.empty: return df
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"]).dt.strftime('%Y-%m-%d')
        if AUTO_DEDUPLICATE and "Date" in df.columns and "YFinance Ticker" in df.columns:
            before = len(df)
            df = df.drop_duplicates(subset=["Date", "YFinance Ticker"], keep="last")
            if before != len(df):
                print(f"🔄 去重完成: {before} → {len(df)} 筆")
        if "Date" in df.columns and "YFinance Ticker" in df.columns:
            df = df.sort_values(["Date", "YFinance Ticker"]).reset_index(drop=True)
        return df


# =====================================================================================
# 💰 ETFFundFlowCalculator (v17 新增 — 依 圖3 TIER-2 + TIER-4)
# =====================================================================================

class ETFFundFlowCalculator:
    """
    ETF 資金流計算器.
    TIER-2 (對單一 ETF):
      dollar_vol = close × volume
      dvol_ma5 / dvol_ma20 / dvol_ratio = dvol / dvol_ma20
      ret_1d / ret_5d / ret_20d
      pv_signal: ret > 0 ∧ vol_chg > thr → INFLOW; ret < 0 ∧ vol_chg > thr → OUTFLOW
      rs_vs_spy = etf_ret / spy_ret (rolling)
      rs_ma10, rs_trend = rs_ma10 - rs_ma10.shift(5)
    TIER-4 (跨 ETF 複合信號, 每日一列):
      risk_on_off       = SPY_ret_5d - TLT_ret_5d
      hy_spread_proxy   = HYG_ret_1d - IEF_ret_1d
      growth_vs_value   = VUG_ret_20d - VTV_ret_20d
      em_rotation       = EEM_dvol_ratio / SPY_dvol_ratio
      semicon_momentum  = SMH_ret / QQQ_ret
      cash_parking      = BIL + SGOV dollar_vol (trend)
      hedge_panic       = SQQQ + SH + VIXY dollar_vol (合計)
      tw_foreign_proxy  = EWT_dvol_ratio (台股外資代理)
    """

    def __init__(self, df: "pd.DataFrame"):
        """df: 主價量 DataFrame (含 Date, YFinance Ticker, Close, Volume, Asset_Class)."""
        self.df_main = df
        self.df_etf  = None
        self.df_flow = None
        self.df_composite = None

    def _is_etf_row(self, asset_class: str) -> bool:
        return isinstance(asset_class, str) and asset_class.startswith("ETF_")

    def filter_etf_only(self) -> "pd.DataFrame":
        """從主表抽出 ETF 列."""
        if self.df_main is None or self.df_main.empty:
            return pd.DataFrame()
        if "Asset_Class" not in self.df_main.columns:
            return pd.DataFrame()
        mask = self.df_main["Asset_Class"].apply(self._is_etf_row)
        self.df_etf = self.df_main[mask].copy()
        return self.df_etf

    def calc_tier2_per_etf(self) -> "pd.DataFrame":
        """TIER-2 計算 (每個 ETF 各自一個時間序列)."""
        if self.df_etf is None or self.df_etf.empty:
            self.filter_etf_only()
        if self.df_etf is None or self.df_etf.empty:
            return pd.DataFrame()
        df = self.df_etf.copy()
        df = df.sort_values(["YFinance Ticker", "Date"]).reset_index(drop=True)
        # 強制數值化
        for col in ["Close", "Adj Close", "Volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        price_col = "Adj Close" if "Adj Close" in df.columns and df["Adj Close"].notna().any() else "Close"

        # 1) dollar_vol
        df["dollar_vol"] = df["Close"] * df["Volume"]

        # 2-5) per-ticker rolling (顯式迴圈, 避免 pandas 2+ groupby.apply 欄位消失問題)
        per_ticker_dfs = []
        for tk in df["YFinance Ticker"].unique():
            g = df[df["YFinance Ticker"] == tk].copy().sort_values("Date").reset_index(drop=True)
            g["dvol_ma5"]   = g["dollar_vol"].rolling(FLOW_DVOL_MA5_WINDOW,  min_periods=1).mean()
            g["dvol_ma20"]  = g["dollar_vol"].rolling(FLOW_DVOL_MA20_WINDOW, min_periods=1).mean()
            g["dvol_ratio"] = g["dollar_vol"] / g["dvol_ma20"].replace(0, np.nan)
            g["ret_1d"]  = g[price_col].pct_change(1)
            g["ret_5d"]  = g[price_col].pct_change(5)
            g["ret_20d"] = g[price_col].pct_change(20)
            g["vol_chg"] = g["Volume"].pct_change(1)
            # pv_signal
            g["pv_signal"] = np.where(
                (g["ret_1d"] > 0) & (g["vol_chg"] > FLOW_PV_VOL_THRESHOLD), "INFLOW",
                np.where((g["ret_1d"] < 0) & (g["vol_chg"] > FLOW_PV_VOL_THRESHOLD), "OUTFLOW", "NEUTRAL")
            )
            per_ticker_dfs.append(g)
        df = pd.concat(per_ticker_dfs, ignore_index=True) if per_ticker_dfs else df

        # 6) rs_vs_spy (相對強度)
        spy = df[df["YFinance Ticker"] == FLOW_SPY_BENCHMARK][["Date", "ret_1d"]].rename(
            columns={"ret_1d": "spy_ret_1d"})
        if not spy.empty:
            df = df.merge(spy, on="Date", how="left")
            df["rs_vs_spy"] = df["ret_1d"] / df["spy_ret_1d"].replace(0, np.nan)
            # rs rolling per ticker (顯式迴圈)
            rs_dfs = []
            for tk in df["YFinance Ticker"].unique():
                g = df[df["YFinance Ticker"] == tk].copy().sort_values("Date").reset_index(drop=True)
                g["rs_ma10"]  = g["rs_vs_spy"].rolling(FLOW_RS_MA10_WINDOW, min_periods=1).mean()
                g["rs_trend"] = g["rs_ma10"] - g["rs_ma10"].shift(FLOW_RS_TREND_LAG)
                rs_dfs.append(g)
            df = pd.concat(rs_dfs, ignore_index=True)
        else:
            df["rs_vs_spy"] = np.nan
            df["rs_ma10"]   = np.nan
            df["rs_trend"]  = np.nan

        self.df_flow = df
        return df

    def calc_tier4_composite(self) -> "pd.DataFrame":
        """TIER-4 複合信號 (每日一列, 跨 ETF)."""
        if self.df_flow is None or self.df_flow.empty:
            self.calc_tier2_per_etf()
        if self.df_flow is None or self.df_flow.empty:
            return pd.DataFrame()
        df = self.df_flow

        def _pivot(metric: str, tickers: List[str]) -> "pd.DataFrame":
            sub = df[df["YFinance Ticker"].isin(tickers)][["Date", "YFinance Ticker", metric]]
            if sub.empty:
                return pd.DataFrame()
            return sub.pivot(index="Date", columns="YFinance Ticker", values=metric)

        ret_5d  = _pivot("ret_5d",  ["SPY", "TLT"])
        ret_1d  = _pivot("ret_1d",  ["HYG", "IEF"])
        ret_20d = _pivot("ret_20d", ["VUG", "VTV"])
        dvol_ratio = _pivot("dvol_ratio", ["EEM", "SPY", "SMH", "QQQ", "EWT"])
        dollar_vol = _pivot("dollar_vol", ["BIL", "SGOV", "SQQQ", "SH", "VIXY"])
        smh_qqq_ret = _pivot("ret_5d", ["SMH", "QQQ"])

        composite = pd.DataFrame(index=ret_5d.index if not ret_5d.empty else
                                       (dollar_vol.index if not dollar_vol.empty else pd.Index([])))

        if not ret_5d.empty and "SPY" in ret_5d.columns and "TLT" in ret_5d.columns:
            composite["risk_on_off"] = ret_5d["SPY"] - ret_5d["TLT"]
        if not ret_1d.empty and "HYG" in ret_1d.columns and "IEF" in ret_1d.columns:
            composite["hy_spread_proxy"] = ret_1d["HYG"] - ret_1d["IEF"]
        if not ret_20d.empty and "VUG" in ret_20d.columns and "VTV" in ret_20d.columns:
            composite["growth_vs_value"] = ret_20d["VUG"] - ret_20d["VTV"]
        if not dvol_ratio.empty and "EEM" in dvol_ratio.columns and "SPY" in dvol_ratio.columns:
            composite["em_rotation"] = dvol_ratio["EEM"] / dvol_ratio["SPY"].replace(0, np.nan)
        if not smh_qqq_ret.empty and "SMH" in smh_qqq_ret.columns and "QQQ" in smh_qqq_ret.columns:
            composite["semicon_momentum"] = smh_qqq_ret["SMH"] / smh_qqq_ret["QQQ"].replace(0, np.nan)
        if not dollar_vol.empty:
            cash_cols = [c for c in ["BIL", "SGOV"] if c in dollar_vol.columns]
            if cash_cols:
                composite["cash_parking"] = dollar_vol[cash_cols].sum(axis=1)
            hedge_cols = [c for c in ["SQQQ", "SH", "VIXY"] if c in dollar_vol.columns]
            if hedge_cols:
                composite["hedge_panic"] = dollar_vol[hedge_cols].sum(axis=1)
        if not dvol_ratio.empty and "EWT" in dvol_ratio.columns:
            composite["tw_foreign_proxy"] = dvol_ratio["EWT"]

        composite = composite.reset_index().rename(columns={"index": "Date"})
        # 加入 risk_on_off 文字分類
        if "risk_on_off" in composite.columns:
            composite["risk_regime"] = np.where(composite["risk_on_off"] > 0.005, "RISK_ON",
                                       np.where(composite["risk_on_off"] < -0.005, "RISK_OFF", "NEUTRAL"))
        self.df_composite = composite
        return composite

    def run_all(self) -> Tuple["pd.DataFrame", "pd.DataFrame"]:
        """執行完整資金流計算. 回傳 (flow_df, composite_df)."""
        self.filter_etf_only()
        flow      = self.calc_tier2_per_etf()
        composite = self.calc_tier4_composite() if ENABLE_COMPOSITE_SIGNALS else pd.DataFrame()
        return flow, composite


# =====================================================================================
# 📈 數據獲取器 / Data Fetcher (v5 邏輯 + v17 batch + ThreadPool)
# =====================================================================================

class FinancialDataFetcher:
    """
    金融數據獲取器.
    v5 邏輯 (yf.Ticker().history per symbol) 保留 (fallback path).
    v17 加速: yf.download batch + ThreadPoolExecutor.
    """

    def __init__(self):
        self.file_manager = FileManager()
        self.validator    = DataValidator()
        # v17 stats
        self.stats = {
            "fetched_symbols":   0,
            "failed_symbols":    [],
            "rejected_symbols":  [],
            "batches_used":      0,
            "fallback_used":     0,
            "total_rows":        0,
        }

    def get_missing_dates(self, existing_df) -> List[str]:
        """v5 原樣"""
        end_date = datetime.now() if USE_CURRENT_DATE_AS_END else datetime.strptime(END_DATE, '%Y-%m-%d')
        start_date = datetime.strptime(START_DATE, '%Y-%m-%d')
        all_dates = pd.bdate_range(start=start_date, end=end_date)
        all_dates_str = [d.strftime('%Y-%m-%d') for d in all_dates]
        if existing_df is None or existing_df.empty:
            return all_dates_str
        existing_dates = set(existing_df["Date"].unique())
        missing_dates  = [d for d in all_dates_str if d not in existing_dates]
        print(f"📅 需要更新 {len(missing_dates)} 個交易日")
        return missing_dates

    def get_market_info(self, symbol: str) -> Dict[str, Any]:
        """v5 保留 + v17 ETF group 識別"""
        for market_group, symbols in MARKETS.items():
            if symbol in symbols:
                rules = ASSET_CLASS_RULES.get(market_group, {})
                return {
                    'name': symbols[symbol],
                    'market': market_group,
                    'region': self.get_region_from_market(market_group),
                    'asset_class': rules.get('asset_class', 'UNKNOWN'),
                    'auto_adjust': rules.get('auto_adjust', False),
                    'has_adj_close': rules.get('has_adj_close', False),
                    'has_volume': rules.get('has_volume', True),
                }
        return {'name': symbol, 'market': 'Unknown', 'region': 'Unknown',
                'asset_class': 'UNKNOWN', 'auto_adjust': False,
                'has_adj_close': False, 'has_volume': True}

    def get_region_from_market(self, market: str) -> str:
        """v5 保留 + v17 ETF region"""
        region_map = {
            'INDICES_US':       'US',
            'INDICES_ASIA':     'Asia',
            'INDICES_EUROPE':   'Europe',
            'EQUITY_US':        'US',
            'EQUITY_TW_LISTED': 'Taiwan',
            'EQUITY_TW_OTC':    'Taiwan',
            'EQUITY_ASIA':      'Asia',
            'EQUITY_EUROPE':    'Europe',
            'CURRENCIES':       'Global',
            'COMMODITIES':      'Global',
            'BONDS_YIELDS':     'US',
            'CRYPTO':           'Global',
            'ETF_REGION_GLOBAL':'Global',
            'ETF_SECTOR_US':    'US',
            'ETF_BONDS':        'US',
            'ETF_THEMATIC':     'Global',
            'ETF_HELPER':       'US',
            'ETF_TW_PASSIVE':   'Taiwan',
            'ETF_TW_ACTIVE':    'Taiwan',
        }
        return region_map.get(market, 'Unknown')

    def _post_process_data(self, data: "pd.DataFrame", symbol: str,
                           market_info: Dict[str, Any]) -> "pd.DataFrame":
        """共用後處理 (v5 邏輯重整為獨立方法, 給 batch 與 single 共用)."""
        if data is None or data.empty:
            return pd.DataFrame()
        if not isinstance(data, pd.DataFrame):
            return pd.DataFrame()
        # reset index
        if data.index.name in ('Date', 'Datetime'):
            data = data.reset_index()
        elif 'Date' not in data.columns and data.index.name is None and len(data) > 0:
            data = data.reset_index()

        # 日期格式 (兼容大小寫)
        if 'Date' in data.columns:
            data['Date'] = pd.to_datetime(data['Date']).dt.strftime('%Y-%m-%d')
        elif 'Datetime' in data.columns:
            data['Date'] = pd.to_datetime(data['Datetime']).dt.strftime('%Y-%m-%d')
            data = data.drop(columns=['Datetime'])

        # 標記 ticker / name / market / region / asset_class
        data['YFinance Ticker'] = symbol
        data['Name']        = market_info.get('name', symbol)
        data['Market']      = market_info.get('market', 'Unknown')
        data['Region']      = market_info.get('region', 'Unknown')
        data['Asset_Class'] = market_info.get('asset_class', 'UNKNOWN')

        # Adj Close 正規化 (v5 邏輯)
        has_adj_close = market_info.get('has_adj_close', False)
        if 'Adj Close' in data.columns:
            if not has_adj_close:
                data['Adj Close'] = np.nan
        else:
            data['Adj Close'] = np.nan

        # Volume 正規化
        has_volume = market_info.get('has_volume', True)
        if 'Volume' in data.columns and not has_volume:
            data['Volume'] = np.nan

        # Trading Value
        if 'Close' in data.columns and 'Volume' in data.columns and has_volume:
            data['Trading_Value'] = data['Close'] * data['Volume']
        else:
            data['Trading_Value'] = np.nan

        return data

    def _fetch_single_v5(self, symbol: str, start_date: str, end_date: str,
                         market_info: Dict[str, Any]) -> "pd.DataFrame":
        """v5 原始邏輯: yf.Ticker().history per symbol (fallback path)."""
        for attempt in range(MAX_RETRIES):
            try:
                ticker = yf.Ticker(symbol)
                end_str = (datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
                data = ticker.history(start=start_date, end=end_str, interval='1d',
                                      auto_adjust=market_info.get('auto_adjust', False))
                if data is not None and not data.empty:
                    return self._post_process_data(data, symbol, market_info)
                return pd.DataFrame()
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    self.stats["failed_symbols"].append((symbol, str(e)[:60]))
                    return pd.DataFrame()
        return pd.DataFrame()

    def _fetch_batch_v17(self, symbols: List[str], start_date: str, end_date: str) -> "pd.DataFrame":
        """v17 新增: yf.download batch."""
        if not symbols:
            return pd.DataFrame()
        end_str = (datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
        all_dfs: List[pd.DataFrame] = []
        for attempt in range(MAX_RETRIES):
            try:
                raw = yf.download(
                    tickers=" ".join(symbols),
                    start=start_date,
                    end=end_str,
                    interval='1d',
                    auto_adjust=False,
                    threads=ENABLE_YF_THREADS,
                    progress=False,
                    group_by='ticker',
                )
                if raw is None or raw.empty:
                    return pd.DataFrame()
                # multi-ticker DataFrame: column[0]=ticker, column[1]=field
                # single ticker: flat columns
                if isinstance(raw.columns, pd.MultiIndex):
                    for sym in symbols:
                        if sym not in raw.columns.get_level_values(0):
                            continue
                        sub = raw[sym].copy()
                        if sub.empty: continue
                        sub = sub.dropna(how='all')
                        if sub.empty: continue
                        market_info = self.get_market_info(sym)
                        processed = self._post_process_data(sub, sym, market_info)
                        if not processed.empty:
                            all_dfs.append(processed)
                else:
                    # single ticker case
                    sym = symbols[0]
                    market_info = self.get_market_info(sym)
                    processed = self._post_process_data(raw, sym, market_info)
                    if not processed.empty:
                        all_dfs.append(processed)
                self.stats["batches_used"] += 1
                break
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    print(f"  ❌ batch 失敗: {e}")
                    return pd.DataFrame()
        if all_dfs:
            return pd.concat(all_dfs, ignore_index=True)
        return pd.DataFrame()

    def fetch_yfinance_data(self, symbols: List[str], start_date: str, end_date: str) -> "pd.DataFrame":
        """v5 主入口 + v17 batch 加速."""
        if not YFINANCE_AVAILABLE:
            print("❌ yfinance 不可用"); return pd.DataFrame()

        # ── SSOT 治理檢查 (v5 保留) ──
        validated_symbols, rejected = [], []
        for sym in symbols:
            mkt_info  = self.get_market_info(sym)
            mkt_group = mkt_info.get('market', 'Unknown')
            ok, reason = validate_ticker(sym, mkt_group)
            if ok:
                validated_symbols.append(sym)
            else:
                rejected.append((sym, mkt_group, reason))
        if rejected:
            print(f"\n⚠️ YFinance Ticker 治理檢查: {len(rejected)} 個代碼違規, 已剔除")
            for sym, mkt, reason in rejected[:10]:
                print(f"   ❌ [{mkt}] {sym} → {reason}")
            if len(rejected) > 10:
                print(f"   ... 還有 {len(rejected)-10} 個")
            print()
            self.stats["rejected_symbols"] = rejected

        if not validated_symbols:
            print("❌ 所有 YFinance Ticker 都未通過治理檢查, 中止 fetch")
            return pd.DataFrame()

        print(f"📈 獲取 {len(validated_symbols)} 個金融工具數據 (治理通過 / 共 {len(symbols)} 個)...")
        print(f"   🔒 治理來源: {_SSOT_VALIDATOR}")
        print(f"   🚀 加速: batch={ENABLE_BATCH_DOWNLOAD} (size={YF_BATCH_SIZE}) · "
              f"threadpool={ENABLE_THREADPOOL} (workers={THREADPOOL_WORKERS})")

        all_data: List[pd.DataFrame] = []

        if ENABLE_BATCH_DOWNLOAD:
            # 分批 (每 YF_BATCH_SIZE 個 ticker 一批)
            batches = [validated_symbols[i:i + YF_BATCH_SIZE]
                       for i in range(0, len(validated_symbols), YF_BATCH_SIZE)]
            print(f"   📦 分 {len(batches)} 個 batch (每批最多 {YF_BATCH_SIZE} ticker)")

            if ENABLE_THREADPOOL and len(batches) > 1:
                # 並發批次 (避免被 ban: workers 不超過 4)
                with ThreadPoolExecutor(max_workers=THREADPOOL_WORKERS) as pool:
                    future_to_batch = {
                        pool.submit(self._fetch_batch_v17, batch, start_date, end_date): i
                        for i, batch in enumerate(batches)
                    }
                    for fut in as_completed(future_to_batch):
                        idx = future_to_batch[fut]
                        try:
                            df = fut.result()
                            if df is not None and not df.empty:
                                all_data.append(df)
                                tickers_in = df["YFinance Ticker"].nunique()
                                print(f"   ✓ batch {idx+1}/{len(batches)}: {tickers_in} ticker, {len(df)} 列")
                            else:
                                print(f"   ⚠️ batch {idx+1}/{len(batches)}: 空")
                        except Exception as e:
                            print(f"   ❌ batch {idx+1}/{len(batches)} 例外: {e}")
            else:
                # 順序批次
                for i, batch in enumerate(batches):
                    df = self._fetch_batch_v17(batch, start_date, end_date)
                    if df is not None and not df.empty:
                        all_data.append(df)
                        print(f"   ✓ batch {i+1}/{len(batches)}: {df['YFinance Ticker'].nunique()} ticker, {len(df)} 列")

        else:
            # v5 fallback: 逐個 ticker
            for symbol in validated_symbols:
                market_info = self.get_market_info(symbol)
                df = self._fetch_single_v5(symbol, start_date, end_date, market_info)
                if df is not None and not df.empty:
                    all_data.append(df)
                    self.stats["fallback_used"] += 1

        if all_data:
            result = pd.concat(all_data, ignore_index=True)
            self.stats["fetched_symbols"] = result["YFinance Ticker"].nunique()
            self.stats["total_rows"]      = len(result)
            return result
        return pd.DataFrame()

    def run_fetch(self) -> "pd.DataFrame":
        """執行數據獲取 (v5 邏輯 + v17 stats)."""
        print("🚀 開始 yfinance 全宇宙數據獲取...")
        existing_df = self.file_manager.load_existing_data()
        missing_dates = self.get_missing_dates(existing_df)
        if not missing_dates:
            print("✅ 數據已是最新")
            return existing_df if existing_df is not None else pd.DataFrame()

        # 準備標的 (依 CLI flags 過濾)
        all_symbols: List[str] = []
        for market_group, symbols in MARKETS.items():
            # CLI 過濾
            if "--etf-only" in sys.argv and market_group not in ETF_GROUPS:
                continue
            if "--non-etf-only" in sys.argv and market_group in ETF_GROUPS:
                continue
            all_symbols.extend(symbols.keys())

        start_date = min(missing_dates)
        end_date   = max(missing_dates)
        new_data = self.fetch_yfinance_data(all_symbols, start_date, end_date)

        if not new_data.empty:
            new_data = new_data[new_data['Date'].isin(missing_dates)]
        if existing_df is not None and not existing_df.empty:
            combined_df = pd.concat([existing_df, new_data], ignore_index=True)
        else:
            combined_df = new_data
        combined_df = self.validator.clean_data(combined_df)
        if VALIDATE_DATA:
            validation = self.validator.validate_dataframe(combined_df)
            if not validation['valid']:
                print(f"⚠️ 數據驗證警告: {validation.get('error', '未知錯誤')}")
        print(f"✅ 數據獲取完成: {len(combined_df)} 筆記錄")
        return combined_df


# =====================================================================================
# 🎯 主程式類 / YFinanceUniverseTool (v5 保留 + v17 ETF Flow + Rich Matrix)
# =====================================================================================

class YFinanceUniverseTool:
    """yfinance 全宇宙工具主類 (v5 保留 + v17 ETF 資金流 + Rich Summary Matrix)."""

    def __init__(self):
        self.file_manager = FileManager()
        self.fetcher      = FinancialDataFetcher()
        self.start_time   = time.time()
        self.summary: Dict[str, Any] = {
            "main_rows":         0,
            "main_tickers":      0,
            "etf_rows":          0,
            "etf_tickers":       0,
            "flow_rows":         0,
            "composite_rows":    0,
            "asset_class_dist":  {},
            "etf_group_dist":    {},
            "save_results":      {},
            "etf_save_results":  {},
            "composite_saved":   False,
            "date_range":        "N/A",
            "elapsed_sec":       0.0,
            "modes":             [],
        }

    def show_header(self):
        """顯示啟動標題."""
        counts = {k: len(v) for k, v in MARKETS.items()}
        total = sum(counts.values())
        etf_total    = sum(counts.get(k, 0) for k in ETF_GROUPS)
        nonetf_total = total - etf_total
        header = f"""
🏛️ VDF MDL002 - yfinance Universal Fetching Engine (v17)

📅 時間範圍 : {START_DATE} ~ {'今天' if USE_CURRENT_DATE_AS_END else END_DATE}
📁 輸出目錄 : {BASE_DIR}/{OUTPUT_DIR}
🔄 增量模式 : {'✅ 啟用' if ENABLE_INCREMENTAL else '❌ 停用'}
📊 總標的數 : {total} 檔  ({nonetf_total} 非 ETF + {etf_total} ETF)
🚀 加速     : batch={ENABLE_BATCH_DOWNLOAD} · threadpool={ENABLE_THREADPOOL} (×{THREADPOOL_WORKERS})
💰 資金流   : {'✅ 啟用 TIER-2 + TIER-4' if ENABLE_ETF_FLOW_CALC else '❌ 停用'}

非 ETF (v5):
  US 指數 {counts.get('INDICES_US',0)} · Asia 指數 {counts.get('INDICES_ASIA',0)} · EU 指數 {counts.get('INDICES_EUROPE',0)}
  US 個股 {counts.get('EQUITY_US',0)} · TW 上市 {counts.get('EQUITY_TW_LISTED',0)} · TW 上櫃 {counts.get('EQUITY_TW_OTC',0)}
  Asia 個股 {counts.get('EQUITY_ASIA',0)} · EU 個股 {counts.get('EQUITY_EUROPE',0)}
  FX {counts.get('CURRENCIES',0)} · 期貨 {counts.get('COMMODITIES',0)} · 殖利率 {counts.get('BONDS_YIELDS',0)} · 加密 {counts.get('CRYPTO',0)}

ETF (v17 新增):
  (A) 全球/區域 {counts.get('ETF_REGION_GLOBAL',0)} · (B) 美產業 {counts.get('ETF_SECTOR_US',0)} · (C) 債券 {counts.get('ETF_BONDS',0)}
  (D) 主題/因子 {counts.get('ETF_THEMATIC',0)} · (E) 輔助 {counts.get('ETF_HELPER',0)}
  (F) TW 被動 {counts.get('ETF_TW_PASSIVE',0)} · (G) TW 主動 {counts.get('ETF_TW_ACTIVE',0)}
        """
        if RICH_AVAILABLE:
            console.print(Panel(header.strip(),
                                title="[bold blue]VDF MDL002 · yfinance Universal Fetching Engine[/bold blue]",
                                border_style="blue"))
        else:
            print("=" * 80); print(header); print("=" * 80)

    def save_stock_list(self, df) -> bool:
        """v5 原樣"""
        if df is None or df.empty or 'YFinance Ticker' not in df.columns:
            return False
        try:
            unique_tickers = df['YFinance Ticker'].unique()
            stock_list_data = []
            for ticker in unique_tickers:
                ticker_data = df[df['YFinance Ticker'] == ticker].iloc[0]
                stock_list_data.append({
                    'YFinance Ticker': ticker,
                    'Name':            ticker_data.get('Name', ticker),
                    'Market':          ticker_data.get('Market', 'Unknown'),
                    'Region':          ticker_data.get('Region', 'Unknown'),
                    'Asset_Class':     ticker_data.get('Asset_Class', 'Unknown'),
                    'Update_Time':     datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            stock_df = pd.DataFrame(stock_list_data)
            stock_df.to_csv(self.file_manager.stock_list_file, index=False, encoding=CSV_ENCODING)
            print(f"✅ 標的清單已保存: {self.file_manager.stock_list_file.name}")
            return True
        except Exception as e:
            print(f"⚠️ 保存標的清單失敗: {e}")
            return False

    def _summarize(self, df_main, df_flow, df_composite, save_results, etf_save, composite_saved):
        """彙整 summary dict."""
        s = self.summary
        s["save_results"]     = save_results
        s["etf_save_results"] = etf_save
        s["composite_saved"]  = composite_saved
        s["elapsed_sec"]      = round(time.time() - self.start_time, 2)
        if df_main is not None and not df_main.empty:
            s["main_rows"]    = len(df_main)
            s["main_tickers"] = df_main["YFinance Ticker"].nunique() if "YFinance Ticker" in df_main.columns else 0
            if "Date" in df_main.columns:
                s["date_range"] = f"{df_main['Date'].min()} ~ {df_main['Date'].max()}"
            if "Asset_Class" in df_main.columns:
                s["asset_class_dist"] = df_main["Asset_Class"].value_counts().to_dict()
            if "Market" in df_main.columns:
                etf_mask = df_main["Market"].isin(ETF_GROUPS)
                s["etf_group_dist"] = df_main[etf_mask]["Market"].value_counts().to_dict()
        if df_flow is not None and not df_flow.empty:
            s["flow_rows"]    = len(df_flow)
            s["etf_rows"]     = len(df_flow)
            s["etf_tickers"]  = df_flow["YFinance Ticker"].nunique() if "YFinance Ticker" in df_flow.columns else 0
        if df_composite is not None and not df_composite.empty:
            s["composite_rows"] = len(df_composite)


# =====================================================================================
# 🎨 Rich Summary Matrix (v17 新增 — 詳細彙總 8 表)
# =====================================================================================

def print_rich_summary_matrix(tool: YFinanceUniverseTool, df_main, df_flow, df_composite):
    """印 detailed and well-organized summary matrix by Rich."""
    s = tool.summary
    fetcher_stats = tool.fetcher.stats

    if not RICH_AVAILABLE:
        _print_plain_summary(tool); return

    console.rule(f"[bold cyan]🏛️ VDF MDL002 · YFinance Universal Engine · 執行彙總矩陣[/bold cyan]")

    # ─── Table 1: 系統環境 / 輔助工具 ────────────────────────────────
    t_env = Table(title="📦 [bold]系統環境 / 輔助工具[/bold]", box=box.ROUNDED, header_style="bold magenta")
    t_env.add_column("組件", style="cyan", width=22)
    t_env.add_column("狀態", style="green", width=10, justify="center")
    t_env.add_column("作用", style="yellow", width=50)
    t_env.add_row("pandas/numpy",   "✅" if PANDAS_AVAILABLE   else "❌", "資料表處理 + 衍生計算")
    t_env.add_row("yfinance",       "✅" if YFINANCE_AVAILABLE else "❌", "yfinance API")
    t_env.add_row("pyarrow",        "✅" if PYARROW_AVAILABLE  else "⚪", "Parquet 輸出")
    t_env.add_row("rich",           "✅" if RICH_AVAILABLE     else "⚪", "彩色終端表格")
    t_env.add_row("SSOT validator", "✅" if _ssot_extract is not None else "⚠️",
                  f"{_SSOT_VALIDATOR}")
    console.print(t_env)

    # ─── Table 2: MARKETS 全宇宙統計 (15 group) ─────────────────────
    t_mkt = Table(title="🌍 [bold]MARKETS 全宇宙 (15 group, ETF 7 + 非ETF 8 = 15 group)[/bold]",
                  box=box.ROUNDED, header_style="bold magenta")
    t_mkt.add_column("Group", style="cyan", width=22)
    t_mkt.add_column("類型", style="cyan", width=14)
    t_mkt.add_column("檔數", style="green", width=8, justify="right")
    t_mkt.add_column("Adj Close", style="yellow", width=12, justify="center")
    t_mkt.add_column("代表 ticker", style="yellow", width=30)
    for group_name, group_symbols in MARKETS.items():
        rules = ASSET_CLASS_RULES.get(group_name, {})
        kind  = rules.get("asset_class", "?")
        cnt   = len(group_symbols)
        adj   = "✅" if rules.get("has_adj_close") else "—"
        repr_ticks = ", ".join(list(group_symbols.keys())[:3])
        t_mkt.add_row(group_name, kind, str(cnt), adj, repr_ticks)
    console.print(t_mkt)

    # ─── Table 3: ETF 7 大分類 (v17 新增亮點) ───────────────────────
    t_etf = Table(title="📊 [bold]ETF 宇宙 7 大分類 (v17 新增)[/bold]",
                  box=box.ROUNDED, header_style="bold magenta")
    t_etf.add_column("分類", style="cyan", width=10)
    t_etf.add_column("名稱", style="cyan", width=22)
    t_etf.add_column("檔數", style="green", width=8, justify="right")
    t_etf.add_column("資金流監控用途", style="yellow", width=42)
    t_etf.add_row("(A)", "ETF_REGION_GLOBAL", str(len(MARKETS.get("ETF_REGION_GLOBAL", {}))),  "判斷大資金進出哪個地區")
    t_etf.add_row("(B)", "ETF_SECTOR_US",     str(len(MARKETS.get("ETF_SECTOR_US",     {}))),  "判斷資金在哪個產業集中")
    t_etf.add_row("(C)", "ETF_BONDS",         str(len(MARKETS.get("ETF_BONDS",         {}))),  "判斷資金在股債之間流動")
    t_etf.add_row("(D)", "ETF_THEMATIC",      str(len(MARKETS.get("ETF_THEMATIC",      {}))),  "極端情緒 / 風格輪動偵測")
    t_etf.add_row("(E)", "ETF_HELPER",        str(len(MARKETS.get("ETF_HELPER",        {}))),  "市場環境 context")
    t_etf.add_row("(F)", "ETF_TW_PASSIVE",    str(len(MARKETS.get("ETF_TW_PASSIVE",    {}))),  "與台股籌碼交叉驗證")
    t_etf.add_row("(G)", "ETF_TW_ACTIVE",     str(len(MARKETS.get("ETF_TW_ACTIVE",     {}))),  "主動式 ETF (依 v8 Matrix)")
    console.print(t_etf)

    # ─── Table 4: 抓取結果 ─────────────────────────────────────────
    t_res = Table(title="📈 [bold]抓取結果[/bold]", box=box.ROUNDED, header_style="bold magenta")
    t_res.add_column("指標", style="cyan", width=24)
    t_res.add_column("數值", style="green", width=22, justify="right")
    t_res.add_column("說明", style="yellow", width=32)
    t_res.add_row("總列數",      f"{s['main_rows']:,}",     "Date × Ticker")
    t_res.add_row("Unique tickers", f"{s['main_tickers']:,}", "實際抓到的標的")
    t_res.add_row("日期範圍",    s['date_range'],            "(min ~ max)")
    t_res.add_row("成功 / 拒絕", f"{fetcher_stats['fetched_symbols']} / {len(fetcher_stats['rejected_symbols'])}",
                  "SSOT 治理結果")
    t_res.add_row("失敗 ticker", str(len(fetcher_stats['failed_symbols'])), "yfinance 連線失敗")
    t_res.add_row("Batches",     str(fetcher_stats['batches_used']),       "yf.download 批次數")
    t_res.add_row("執行時間",    f"{s['elapsed_sec']} 秒",   "抓取 + 計算總耗時")
    console.print(t_res)

    # ─── Table 5: Asset Class 分布 ───────────────────────────────
    if s["asset_class_dist"]:
        t_ac = Table(title="🏷️ [bold]Asset Class 分布[/bold]", box=box.ROUNDED, header_style="bold magenta")
        t_ac.add_column("Asset Class", style="magenta", width=22)
        t_ac.add_column("列數", style="green", width=14, justify="right")
        t_ac.add_column("% of total", style="yellow", width=14, justify="right")
        total = s["main_rows"] or 1
        for ac, cnt in sorted(s["asset_class_dist"].items(), key=lambda x: -x[1]):
            pct = cnt / total * 100
            t_ac.add_row(str(ac), f"{cnt:,}", f"{pct:.1f}%")
        console.print(t_ac)

    # ─── Table 6: ETF Fund Flow (TIER-2 + TIER-4) ───────────────
    t_flow = Table(title="💰 [bold]ETF 資金流計算 (圖3 TIER-2 + TIER-4)[/bold]",
                   box=box.ROUNDED, header_style="bold magenta")
    t_flow.add_column("項目", style="cyan", width=22)
    t_flow.add_column("狀態", style="green", width=12, justify="center")
    t_flow.add_column("細節", style="yellow", width=44)
    t_flow.add_row("TIER-2 啟用",   "✅" if ENABLE_ETF_FLOW_CALC else "❌",
                   f"dvol/ret/pv_signal/rs_trend")
    t_flow.add_row("TIER-4 啟用",   "✅" if ENABLE_COMPOSITE_SIGNALS else "❌",
                   "risk_on_off/hy/growth_vs_value/em/semicon/cash/panic")
    t_flow.add_row("Flow 列數",     f"{s['flow_rows']:,}", "Date × ETF Ticker")
    t_flow.add_row("Composite 列數", f"{s['composite_rows']:,}", "每日一列複合信號")
    t_flow.add_row("MA windows",    f"{FLOW_DVOL_MA5_WINDOW} / {FLOW_DVOL_MA20_WINDOW}", "5d/20d 均量")
    t_flow.add_row("RS benchmark",  FLOW_SPY_BENCHMARK, "相對強度基準")
    t_flow.add_row("PV vol 閾值",   f"{FLOW_PV_VOL_THRESHOLD*100:.0f}%", "vol_chg 過閾才標 INFLOW/OUTFLOW")
    console.print(t_flow)

    # ─── Table 7: 加速 / 網路 / 治理 ─────────────────────────────
    t_acc = Table(title="⚡ [bold]加速 / 網路 / 治理 (功能只增不減)[/bold]",
                  box=box.ROUNDED, header_style="bold magenta")
    t_acc.add_column("功能", style="cyan", width=22)
    t_acc.add_column("狀態", style="green", width=12, justify="center")
    t_acc.add_column("參數", style="yellow", width=44)
    t_acc.add_row("yf.download batch", "✅" if ENABLE_BATCH_DOWNLOAD else "❌", f"size={YF_BATCH_SIZE}")
    t_acc.add_row("ThreadPool 並發",   "✅" if ENABLE_THREADPOOL     else "❌", f"workers={THREADPOOL_WORKERS}")
    t_acc.add_row("yf.download threads","✅" if ENABLE_YF_THREADS    else "❌", "yfinance 內部 thread pool")
    t_acc.add_row("增量模式",         "✅" if ENABLE_INCREMENTAL    else "❌", "只抓 missing dates")
    t_acc.add_row("Parquet 雙輸出",   "✅" if PYARROW_AVAILABLE     else "⚪", f"{', '.join(OUTPUT_FORMATS)}")
    t_acc.add_row("自動備份",         "✅" if ENABLE_BACKUP         else "❌", f"max {MAX_BACKUP_FILES} 檔")
    t_acc.add_row("自動去重",         "✅" if AUTO_DEDUPLICATE      else "❌", "(Date, YFinance Ticker)")
    t_acc.add_row("SSOT 治理",        "✅", _SSOT_VALIDATOR)
    t_acc.add_row("Adj Close 正規化", "✅", "indices/FX/futures/yield → NaN")
    console.print(t_acc)

    # ─── Table 8: 輸出檔 ──────────────────────────────────────────
    fm = tool.file_manager
    t_out = Table(title="💾 [bold]輸出檔案[/bold]", box=box.ROUNDED, header_style="bold magenta")
    t_out.add_column("路徑 / 檔名", style="cyan", width=58)
    t_out.add_column("狀態", style="green", width=10, justify="center")
    t_out.add_column("用途", style="yellow", width=24)
    t_out.add_row(str(fm.csv_file),         "✅" if s["save_results"].get("csv") else "—",     "主價量檔 CSV")
    t_out.add_row(str(fm.parquet_file),     "✅" if s["save_results"].get("parquet") else "—", "主價量檔 Parquet")
    t_out.add_row(str(fm.stock_list_file),  "✅", "標的清單 (universe)")
    t_out.add_row(str(fm.etf_flow_csv),     "✅" if s["etf_save_results"].get("csv") else "—",     "ETF 資金流 TIER-2")
    t_out.add_row(str(fm.etf_flow_parquet), "✅" if s["etf_save_results"].get("parquet") else "—", "ETF 資金流 Parquet")
    t_out.add_row(str(fm.composite_csv),    "✅" if s["composite_saved"] else "—",                 "TIER-4 複合信號")
    t_out.add_row(str(fm.backup_dir),       "✅" if ENABLE_BACKUP else "—",                        "備份目錄")
    console.print(t_out)

    # ─── 最終 Panel ────────────────────────────────────────────────
    overall_ok = (s["main_rows"] > 0 and s["save_results"].get("csv"))
    summary_lines = [
        f"  總標的 / 抓取  : {sum(len(v) for v in MARKETS.values())} 檔 / {s['main_tickers']} 成功",
        f"  主價量列數     : {s['main_rows']:,}",
        f"  ETF 資金流列數 : {s['flow_rows']:,}",
        f"  TIER-4 複合信號: {s['composite_rows']:,} 日",
        f"  執行耗時       : {s['elapsed_sec']} 秒",
    ]
    overall = ("[bold green]✅ 系統運行正常[/bold green]" if overall_ok
               else "[bold yellow]⚠️ 部分功能受限[/bold yellow]")
    panel = Panel.fit("\n".join(summary_lines) + f"\n\n  {overall}",
                      title="[bold cyan]🎯 整體狀態[/bold cyan]", border_style="cyan")
    console.print(panel)
    console.rule(f"[dim]VDF MDL002 v17.0 · build {datetime.now().strftime('%Y-%m-%d')} "
                 f"· VERITAS Intelligence System · VDF[/dim]")


def _print_plain_summary(tool: YFinanceUniverseTool):
    """Rich 不可用時的純文字 fallback."""
    s = tool.summary
    bar = "=" * 80
    print(f"\n{bar}\n🏛️ VDF MDL002 - 執行彙總\n{bar}")
    print(f"  主價量    : {s['main_rows']:,} 列 / {s['main_tickers']} ticker")
    print(f"  ETF flow  : {s['flow_rows']:,} 列")
    print(f"  Composite : {s['composite_rows']:,} 列")
    print(f"  日期      : {s['date_range']}")
    print(f"  耗時      : {s['elapsed_sec']}s")
    print(bar)


# =====================================================================================
# 🎯 主程式入口 / Main Entry (v5 邏輯 + v17 ETF Flow + Rich Matrix)
# =====================================================================================

def main():
    """主函數 (v5 保留 + v17 ETF flow + Rich summary)."""
    if sys.version_info < (3, 7):
        print("❌ 需要 Python 3.7 或更高版本")
        return 1
    print("🚀 yfinance 全宇宙數據引擎 (VDF MDL002 v17) 啟動中...")
    tool = YFinanceUniverseTool()
    return tool_run(tool)


def tool_run(tool: YFinanceUniverseTool) -> int:
    """執行主流程 (從 v5 的 YFinanceUniverseTool.run() 拉出, 加 v17 ETF flow)."""
    try:
        tool.show_header()
        print("\n🔍 檢查系統狀態...")
        if not PANDAS_AVAILABLE or not YFINANCE_AVAILABLE:
            print("❌ 缺少必要依賴")
            if "--no-pause" not in sys.argv and input("是否現在檢查依賴？(y/n): ").lower() == 'y':
                check_and_install_dependencies()
            else:
                return 1

        # 1. 抓取主價量
        print("\n📈 步驟 1/4: 數據獲取")
        df_main = tool.fetcher.run_fetch()
        if df_main is None or df_main.empty:
            print("⚠️ 未獲取到任何數據")
            return 1

        # 2. 保存主價量
        print("\n💾 步驟 2/4: 保存主價量")
        save_results = tool.file_manager.save_data(df_main)
        tool.save_stock_list(df_main)

        # 3. ETF 資金流計算 + 儲存
        df_flow      = pd.DataFrame()
        df_composite = pd.DataFrame()
        etf_save     = {}
        composite_saved = False
        if ENABLE_ETF_FLOW_CALC and "--no-flows" not in sys.argv:
            print("\n💰 步驟 3/4: ETF 資金流計算 (TIER-2 + TIER-4)")
            calc = ETFFundFlowCalculator(df_main)
            df_flow, df_composite = calc.run_all()
            if df_flow is not None and not df_flow.empty:
                etf_save = tool.file_manager.save_etf_flow(df_flow)
                print(f"   ✓ TIER-2 flow: {len(df_flow):,} 列")
            if df_composite is not None and not df_composite.empty:
                composite_saved = tool.file_manager.save_composite(df_composite)
                print(f"   ✓ TIER-4 composite: {len(df_composite):,} 列")
        else:
            print("\n⏭️ 步驟 3/4: ETF 資金流計算 (跳過)")

        # 4. Rich Summary Matrix
        print("\n📋 步驟 4/4: Rich Summary Matrix")
        tool._summarize(df_main, df_flow, df_composite, save_results, etf_save, composite_saved)
        print_rich_summary_matrix(tool, df_main, df_flow, df_composite)

        print(f"\n🎉 處理完成! 輸出: {tool.file_manager.output_dir}")
        return 0

    except KeyboardInterrupt:
        print("\n⚠️ 用戶中斷程式")
        return 1
    except Exception as e:
        print(f"\n❌ 程式執行錯誤: {e}")
        if LOG_LEVEL == "DEBUG":
            import traceback; traceback.print_exc()
        return 1


# =====================================================================================
# 互動式選單 (v5 保留)
# =====================================================================================

def interactive_menu():
    """互動式選單"""
    while True:
        print("\n" + "=" * 60)
        print("🔧 VDF MDL002 yfinance Universal Engine v17 - 選單")
        print("=" * 60)
        print("1. 📦 檢查並安裝依賴")
        print("2. 🚀 執行數據獲取 (全宇宙)")
        print("3. 📊 查看現有數據")
        print("4. 🔧 清理備份檔案")
        print("5. 🎯 只抓 ETF")
        print("6. 🌍 只抓非 ETF (v5 等價)")
        print("7. ❌ 退出")
        print("=" * 60)
        choice = input("請選擇 (1-7): ").strip()
        if   choice == '1': check_and_install_dependencies()
        elif choice == '2': main()
        elif choice == '3': view_existing_data()
        elif choice == '4': cleanup_backups()
        elif choice == '5':
            sys.argv.append("--etf-only"); main(); sys.argv.remove("--etf-only")
        elif choice == '6':
            sys.argv.append("--non-etf-only"); main(); sys.argv.remove("--non-etf-only")
        elif choice == '7': print("👋 再見！"); break
        else: print("❌ 無效選擇")


def view_existing_data():
    """查看現有數據 (v5 保留 + v17 ETF flow)"""
    fm = FileManager()
    print("\n📁 查看現有數據...")
    files_to_check = [
        (fm.csv_file,         "📄 主價量 CSV"),
        (fm.parquet_file,     "📦 主價量 Parquet"),
        (fm.stock_list_file,  "📋 標的清單"),
        (fm.etf_flow_csv,     "💰 ETF 資金流 CSV"),
        (fm.etf_flow_parquet, "💰 ETF 資金流 Parquet"),
        (fm.composite_csv,    "🎯 TIER-4 複合信號"),
    ]
    found = False
    for fp, label in files_to_check:
        if fp.exists():
            size = fp.stat().st_size / (1024 * 1024)
            mtime = datetime.fromtimestamp(fp.stat().st_mtime)
            print(f"  {label}: {size:.1f}MB, {mtime.strftime('%Y-%m-%d %H:%M')}")
            found = True
    if not found:
        print("❌ 未找到任何現有檔案")
        return
    try:
        if fm.parquet_file.exists() and PYARROW_AVAILABLE:
            df = pd.read_parquet(fm.parquet_file)
        elif fm.csv_file.exists():
            df = pd.read_csv(fm.csv_file, encoding=CSV_ENCODING)
        else:
            df = pd.DataFrame()
        if not df.empty:
            print(f"\n  📊 總列數    : {len(df):,}")
            if 'Date' in df.columns:           print(f"  📅 日期      : {df['Date'].min()} ~ {df['Date'].max()}")
            if 'YFinance Ticker' in df.columns: print(f"  📈 ticker 數  : {df['YFinance Ticker'].nunique()}")
            if 'Asset_Class' in df.columns:     print(f"  🏷️ asset 類別 : {df['Asset_Class'].nunique()} 種")
    except Exception as e:
        print(f"  ⚠️ 讀取數據失敗: {e}")


def cleanup_backups():
    """v5 保留"""
    fm = FileManager()
    try:
        backups = list(fm.backup_dir.glob("*"))
        if backups:
            print(f"📁 找到 {len(backups)} 個備份檔案")
            if input("是否清理所有備份檔案？(y/n): ").lower() == 'y':
                for backup in backups: backup.unlink()
                print("✅ 備份檔案已清理")
            else: print("❌ 取消清理")
        else: print("📁 未找到備份檔案")
    except Exception as e:
        print(f"❌ 清理失敗: {e}")


# =====================================================================================
# 程式入口
# =====================================================================================

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
        print("\n⚠️ 程式被用戶中斷"); sys.exit(1)
    except Exception as e:
        print(f"\n❌ 未處理的錯誤: {e}")
        if LOG_LEVEL == "DEBUG":
            import traceback; traceback.print_exc()
        sys.exit(1)
