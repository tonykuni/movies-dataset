# VeritasAutoPlot™ v4.0 — 系統全景式架構報告

**Asset ID:** VIA-SA-VIZ-001-AUTOPLOT  
**Version:** 4.0.0  
**Generated:** 2026-03-19  
**Visual Lock:** VIA FusionDashboard × Notion × MUJI × Seaborn  
**Status:** ALL TESTS PASSED (6/6)

---

## 1. 系統概覽

VeritasAutoPlot 是 Veritas Intelligence Analytics 生態系統中的**自主式數據視覺化引擎**，負責將原始金融數據轉化為高品質的視覺智慧（Visual Intelligence）。系統採用模組化架構設計，完全鎖死 VIA FusionDashboard 視覺風格，並與 VDF（VeritasDataForge）、VRN（VeritasRuntimeNetwork）、VPN（VeritasPanoramaNexus）三大子系統無縫整合。

系統的核心理念是「一貼可用、一鍵完成」——輸入任何支援格式的數據檔案，自動完成資料剖析、技術指標計算、泡沫偵測、估值分析、圖表生成與洞察產出，最終輸出為獨立的 HTML 儀表板檔案。

---

## 2. 模組架構矩陣

| 模組檔案 | 行數 | 功能域 | AST 錨點 | 說明 |
|---|---|---|---|---|
| `design_system.py` | 259 | CFG | — | 視覺設計常數鎖死（色彩、字型、間距、陰影） |
| `data_loader.py` | 205 | IO | — | Universal Data Loader（CSV/Excel/Parquet/JSON） |
| `ta_engine.py` | 182 | CORE | — | 技術指標引擎（MA/EMA/BB/MACD/RSI/KD） |
| `event_matrix.py` | 207 | DATA | — | 1995~今歷史金融危機事件庫（17 大危機） |
| `bubble_valuation.py` | 92 | CORE | — | 泡沫偵測（Z-Score）與估值引擎（Log-Linear） |
| `chart_engine.py` | 502 | VIZ | — | Plotly 圖表生成器（10 種圖表類型） |
| `chart_flow.py` | 258 | VIZ | ANCHOR:VAP_CHART_FLOW_ENTRY | ETF 資金流專用圖表引擎 |
| `html_renderer.py` | 451 | IO | — | HTML 儀表板渲染器（FusionDashboard 母版） |
| `autoplot.py` | 535 | CORE | ANCHOR:VAP_PIPELINE_ENTRY/EXIT | 主控管線（一鍵生成完整儀表板） |
| `vdf_bridge.py` | 503 | IO | ANCHOR:VAP_VDF_* (11 個) | VDF 橋接模組（Schema/DuckDB/PANORAMIC） |
| `via_integration.py` | 458 | VIZ | ANCHOR[VIA:ANCHOR:VIZ-001~005] | VIA 生態系統整合（AST/SSOT/VPN） |
| `__init__.py` | 23 | — | — | 模組匯出入口 |
| **合計** | **3,675** | | | |

---

## 3. 生態系統整合矩陣

| 整合目標 | 模組 | 支援格式 | 狀態 |
|---|---|---|---|
| VDF Schema v6 (7 CAT) | `vdf_bridge.py` | DuckDB / CSV / Parquet / JSON | PASS |
| VDF PANORAMIC_DATA | `vdf_bridge.py` | JSON (UTF-8-sig) | PASS |
| VDF ASSET_REGISTRY | `vdf_bridge.py` | AST-SHA1 格式 | PASS |
| VDF ETF Flow | `vdf_bridge.py` + `chart_flow.py` | dvol_ratio / INFLOW / OUTFLOW | PASS |
| VRN Anchor AST | `vdf_bridge.py` | ANCHOR:VAP_* 錨點系統 | PASS |
| VIA AST SmartAsset | `via_integration.py` | VIZ-C/F{SEQ:03d} 格式 | PASS |
| VIA SSOT Engine | `via_integration.py` | SSOT.json 讀寫 | PASS |
| VPN Pipeline (M01~M07) | `via_integration.py` | VPN JSON 手遞格式 | PASS |
| VIA UltimateTemplate v3 | `via_integration.py` | ANCHOR[VIA:ANCHOR:*] 格式 | PASS |

---

## 4. VDF Schema 支援（7 大 CAT + Flow）

| CAT | 表名 | Ticker 欄位 | 說明 |
|---|---|---|---|
| CAT-01 | `index_intl` | ticker | 國際指數（auto_adjust=True） |
| CAT-02 | `stock_intl` | ticker | 國際個股 |
| CAT-03 | `etf_daily` | ticker | 國際 ETF |
| CAT-04 | `fx_daily` | pair | 外匯 |
| CAT-05 | `commodity_daily` | ticker | 商品/期貨（has_roll_warn） |
| CAT-06 | `rate_daily` | ticker | 殖利率 |
| CAT-07 | `crypto_daily` | symbol | 加密貨幣 |
| CAT-03-FLOW | `etf_flow_daily` | ticker | ETF 資金流 |

---

## 5. 圖表類型矩陣

| 圖表 | 函式 | Tab Group | 自動觸發條件 |
|---|---|---|---|
| Full Technical Stack | `chart_full_stack()` | Technical Analysis | Main_Price 存在 |
| Price + MA | `chart_price_ma()` | Price & MA | Main_Price 存在 |
| K-Line (Candlestick) | `chart_candlestick()` | Price & MA | OHLC 齊全 |
| MACD Oscillator | `chart_macd()` | Oscillators | MACD 已計算 |
| RSI (14) | `chart_rsi()` | Oscillators | RSI 已計算 |
| KD Stochastic | `chart_kd()` | Oscillators | K/D 已計算 |
| Return Distribution | `chart_distribution()` | Quant Analysis | Daily_Ret 存在 |
| Underwater (Drawdown) | `chart_drawdown()` | Quant Analysis | Drawdown 已計算 |
| Bubble Radar (Z-Score) | `chart_bubble_radar()` | Bubble & Valuation | Z_Score 已計算 |
| Valuation Channel | `chart_valuation()` | Bubble & Valuation | Fair_Value 已計算 |
| DVol Ratio | `chart_dvol_ratio()` | Fund Flow | dvol_ratio 存在 |
| Price + Flow Overlay | `chart_price_flow_overlay()` | Fund Flow | flow_label 存在 |
| RS Flow | `chart_rs_flow()` | Fund Flow | RS_flow 已計算 |
| ETF Category Matrix | `chart_etf_matrix()` | Fund Flow | etf_category 存在 |

---

## 6. VIA Anchor 錨點索引

### VDF Bridge 錨點
```
ANCHOR:VAP_VDF_BRIDGE_ENTRY     — VDF 橋接入口
ANCHOR:VAP_VDF_BRIDGE_CORE      — 橋接核心
ANCHOR:VAP_VDF_DUCKDB_LOAD      — DuckDB 直讀
ANCHOR:VAP_VDF_EXPORT_LOAD      — VDF 匯出檔載入
ANCHOR:VAP_VDF_PANORAMIC_LOAD   — PANORAMIC_DATA 載入
ANCHOR:VAP_VDF_ETF_FLOW_LOAD    — ETF 資金流載入
ANCHOR:VAP_VDF_MULTI_LOAD       — 多 Ticker 批次載入
ANCHOR:VAP_VDF_STANDARDIZE      — VDF 標準化
ANCHOR:VAP_VDF_AST_ID           — AST ID 生成
ANCHOR:VAP_VDF_REGISTRY_EXPORT  — Registry 匯出
ANCHOR:VAP_VDF_ANCHOR_EXPORT    — Anchor 匯出
```

### Pipeline 錨點
```
ANCHOR:VAP_PIPELINE_ENTRY       — 管線入口
ANCHOR:VAP_PIPELINE_EXIT        — 管線出口
ANCHOR:VAP_CHART_FLOW_ENTRY     — 資金流圖表入口
```

### VIA Integration 錨點
```
ANCHOR[VIA:ANCHOR:VIZ-001]      — VIA Integration Entry
ANCHOR[VIA:ANCHOR:VIZ-002]      — AST SmartAsset Bridge
ANCHOR[VIA:ANCHOR:VIZ-003]      — SSOT Compatibility Layer
ANCHOR[VIA:ANCHOR:VIZ-004]      — VPN Pipeline Connector
ANCHOR[VIA:ANCHOR:VIZ-005]      — Export & Registry
```

---

## 7. 測試結果

| 測試 | 說明 | 狀態 | 輸出 |
|---|---|---|---|
| Test 1 | Standard Pipeline (CSV → HTML) | PASS | 10 plots, 5 insights, 1.6MB HTML |
| Test 2 | VDF Schema Compatible Data | PASS | stock_intl 1200 rows |
| Test 3 | ETF Fund Flow Visualization | PASS | 32 INFLOW + 32 OUTFLOW events |
| Test 4 | VDF PANORAMIC_DATA Visualization | PASS | 6 KPIs, 2 tables |
| Test 5 | VRN Anchor AST Registry Export | PASS | 13 anchor points |
| Test 6 | Multi-Ticker Comparison Dashboard | PASS | 4 tickers, 2 charts |

---

## 8. 使用方式

### 8.1 標準管線（一鍵完成）
```python
from engine import VeritasAutoPlot

engine = VeritasAutoPlot(output_dir="./output")
html = engine.run("data.csv", asset_name="TSMC ADR")
engine.save()
```

### 8.2 VDF 橋接（DuckDB 直讀）
```python
from engine import VDFBridge, VeritasAutoPlot

bridge = VDFBridge()
df = bridge.load_from_duckdb("intl_v6.duckdb", "stock_intl", ticker="TSM")
```

### 8.3 ETF 資金流分析
```python
from engine import VDFFlowEngine, chart_dvol_ratio, chart_price_flow_overlay

flow = VDFFlowEngine()
df = flow.calculate_flow(df)
fig1 = chart_dvol_ratio(df)
fig2 = chart_price_flow_overlay(df)
```

### 8.4 VIA 整合管線
```python
from engine import VeritasAutoPlotVIA

via = VeritasAutoPlotVIA(output_dir="./output")
html = via.run("data.csv")                    # 標準
html = via.run_from_vpn("/path/to/VPN")       # VPN 資料
html = via.run_from_ssot("/path/to/SSOT.json") # SSOT 資料
via.export_via_registry()                      # 匯出 VIA AST Registry
```

---

## 9. 視覺設計鎖定

所有視覺輸出嚴格遵循 VIA FusionDashboard 設計語言：

| 設計元素 | 規格 |
|---|---|
| 背景色 | `#f5f4f0` (light) / `#1a1918` (dark) |
| 卡片面 | `#ffffff` / `#242322` |
| 主字型 | DM Sans + Inter + Noto Sans TC |
| 等寬字型 | DM Mono + JetBrains Mono |
| 資料色板 | Seaborn Deep (10 色) + VIA Fusion (7 色) |
| 漲色 | `#55A868` |
| 跌色 | `#C44E52` |
| 圓角 | 5px / 8px / 12px |
| 陰影 | `0 1px 3px rgba(0,0,0,.06)` |
| 動畫 | fadeIn 0.4s + slideUp 0.3s |

---

## 10. 檔案清單

```
VeritasAutoPlot/
├── engine/
│   ├── __init__.py              (23 lines)
│   ├── design_system.py         (259 lines) — 視覺設計常數
│   ├── data_loader.py           (205 lines) — Universal Data Loader
│   ├── ta_engine.py             (182 lines) — 技術指標引擎
│   ├── event_matrix.py          (207 lines) — 歷史事件庫
│   ├── bubble_valuation.py      (92 lines)  — 泡沫/估值引擎
│   ├── chart_engine.py          (502 lines) — Plotly 圖表生成器
│   ├── chart_flow.py            (258 lines) — ETF 資金流圖表
│   ├── html_renderer.py         (451 lines) — HTML 儀表板渲染器
│   ├── autoplot.py              (535 lines) — 主控管線
│   ├── vdf_bridge.py            (503 lines) — VDF 橋接模組
│   └── via_integration.py       (458 lines) — VIA 生態系統整合
├── output/                      — 生成的 HTML 儀表板
├── sample_data/                 — 測試用範例資料
├── test_pipeline.py             — 基礎測試腳本
├── test_full_integration.py     — 完整整合測試套件
└── VAP_SYSTEM_REPORT.md         — 本文件
```

**Total: 3,675 lines of Python code across 12 engine modules.**
