# VeritasAutoPlot™ v4.1 — 完整系統報告

> **VDF 資料連結整合版**
> 生成時間：2026-03-20
> 系統：VeritasAutoPlot™ v4.1 (VDF Connector Edition)

---

## 一、系統概述

VeritasAutoPlot™ v4.1 是 Veritas Intelligence Analytics 生態系統中的**自主視覺化引擎**，本次升級的核心目標是建立 **VDF（VeritasDataForge）資料庫擷取維護系統**與 AutoPlot 之間的完整資料連結管線，使 VDF 產出的 Parquet 檔案與 Google Sheet 成為 AutoPlot 的直接資料來源。

### 核心能力

| 能力 | 說明 |
|---|---|
| **VDF 目錄自動掃描** | 遞迴掃描 VDF 輸出目錄，自動辨識 M01/LEGO v6/M02 檔案 |
| **VDF 檔名解析** | 解析 VDF 命名規則（`{table}__{CAT}__{start}__{end}__{ts}.parquet`） |
| **多 DuckDB 跨庫查詢** | 支援 intl_v6.duckdb / batch_download.duckdb / akshare_fred_macro.duckdb |
| **Google Sheet 讀取** | 直接從公開/共享 Google Sheet URL 讀取資料 |
| **Parquet/CSV/JSON 自動載入** | 支援 VDF 所有匯出格式，含 utf-8-sig 編碼 |
| **多 Ticker 比較** | 從 VDF 載入多檔並生成正規化比較與相關性矩陣 |
| **ETF 資金流分析** | dvol_ratio / INFLOW / OUTFLOW 視覺化 |
| **宏觀經濟儀表板** | M02 AKShare/FRED 5 區域宏觀指標視覺化 |
| **DataFrame 直接輸入** | 程式化整合，直接傳入 pandas DataFrame |

---

## 二、模組架構

### 引擎模組清單（14 個模組，5,317 行 Python）

| 模組 | 行數 | 功能 | VDF 整合 |
|---|---|---|---|
| `autoplot.py` | 1,131 | 主控管線（8 種 run 方法） | 核心 |
| `vdf_connector.py` | 1,042 | VDF 資料連結引擎（**新增**） | 核心 |
| `chart_engine.py` | 502 | Plotly 圖表生成器（14 種圖表） | — |
| `vdf_bridge.py` | 503 | VDF Schema 橋接（7 CAT + DuckDB） | 核心 |
| `via_integration.py` | 458 | VIA 生態系統整合（AST/SSOT/VPN） | 輔助 |
| `html_renderer.py` | 451 | HTML 儀表板渲染器 | — |
| `design_system.py` | 259 | 視覺設計常數（VIA FusionDashboard 鎖死） | — |
| `chart_flow.py` | 258 | ETF 資金流圖表 | 核心 |
| `event_matrix.py` | 207 | 歷史金融危機事件庫 | — |
| `data_loader.py` | 205 | Universal Data Loader | 基礎 |
| `ta_engine.py` | 182 | 技術指標引擎 | — |
| `bubble_valuation.py` | 92 | 泡沫偵測與估值引擎 | — |
| `__init__.py` | 27 | 模組匯出 | — |

---

## 三、VDF 資料連結架構

### 資料流向

```
VDF VeritasDataForge
├── M01 BatchDownloader TURBO v4
│   ├── ohlcv_{ts}.parquet ──────────────┐
│   ├── ohlcv_{ts}.csv ─────────────────┤
│   └── batch_download.duckdb ──────────┤
│                                        │
├── CentralHub LEGO v6                   │    VDFConnector
│   ├── {table}__{CAT}__{s}__{e}__{ts}  ├──→ (自動掃描)
│   │   .parquet / .csv                  │    ├── VDFNamingParser
│   ├── intl_v6.duckdb ────────────────┤    ├── VDFOutputScanner
│   └── etf_flow_daily ────────────────┤    ├── MultiDBLoader
│                                        │    └── GSheetConnector
├── M02 AKShare/FRED Sentiment DB v5     │         │
│   ├── akshare_fred_{region}_{ts}      ├──→      │
│   │   .parquet / .csv                  │         │
│   └── akshare_fred_macro.duckdb ──────┤         │
│                                        │         ▼
└── Google Sheet (CentralHub 設定)       │    VeritasAutoPlot
    └── https://docs.google.com/...  ───┘    ├── run_vdf()
                                              ├── run_vdf_file()
                                              ├── run_vdf_compare()
                                              ├── run_gsheet()
                                              ├── run_macro()
                                              ├── run_etf_flow()
                                              ├── run_df()
                                              └── run() (classic)
                                                   │
                                                   ▼
                                              HTML Dashboard
                                              (VIA FusionDashboard 視覺風格)
```

### VDF 檔名解析規則

| 來源 | 命名格式 | 範例 |
|---|---|---|
| M01 | `ohlcv_{ts}.{ext}` | `ohlcv_20260319_151527.parquet` |
| LEGO v6 | `{table}__{CAT}__{start}__{end}__{ts}.{ext}` | `etf_daily__DEFAULT__2025-01-01__latest__20260319.parquet` |
| M02 | `akshare_fred_{region}_{ts}.{ext}` | `akshare_fred_us_20260319.csv` |
| DuckDB | `*.duckdb` | `intl_v6.duckdb` |

### VDF Schema 支援（8 表）

| 表名 | 說明 | Ticker 欄位 |
|---|---|---|
| `index_intl` | 國際指數 | `ticker` |
| `stock_intl` | 國際股票 | `ticker` |
| `etf_daily` | ETF 日線 | `ticker` |
| `fx_daily` | 外匯日線 | `pair` |
| `commodity_daily` | 商品日線 | `ticker` |
| `rate_daily` | 利率日線 | `ticker` |
| `crypto_daily` | 加密貨幣日線 | `symbol` |
| `etf_flow_daily` | ETF 資金流 | `ticker` |

---

## 四、API 使用指南

### 4.1 VDF 目錄掃描 → 單一 Ticker

```python
from engine.autoplot import VeritasAutoPlot

engine = VeritasAutoPlot()
engine.run_vdf(
    vdf_base=r"C:\VeritasIntelligenceAnalytics\VeritasDataForge",
    ticker="NVDA",
    table="stock_intl",       # 可選：指定表
    start_date="2020-01-01",  # 可選：起始日
    end_date="2025-12-31",    # 可選：結束日
)
path = engine.save()
print(f"Dashboard saved: {path}")
```

### 4.2 VDF Parquet 檔案直接載入

```python
engine = VeritasAutoPlot()
engine.run_vdf_file(
    filepath=r"C:\...\output\parquet\ohlcv_20260319.parquet",
    ticker="AMD",
)
engine.save("AMD_report.html")
```

### 4.3 Google Sheet 讀取

```python
engine = VeritasAutoPlot()
engine.run_gsheet(
    url="https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms/edit#gid=0",
    asset_name="My Portfolio",
)
engine.save("portfolio.html")
```

### 4.4 多 Ticker 比較

```python
engine = VeritasAutoPlot()
engine.run_vdf_compare(
    vdf_base=r"C:\VeritasIntelligenceAnalytics\VeritasDataForge",
    tickers=["NVDA", "AMD", "TSM", "INTC"],
    table="stock_intl",
)
engine.save("semiconductor_compare.html")
```

### 4.5 宏觀經濟儀表板

```python
engine = VeritasAutoPlot()
engine.run_macro(
    vdf_base=r"C:\VeritasIntelligenceAnalytics\VeritasDataForge",
    regions=["US", "EU", "CN", "JP", "TW"],
)
engine.save("global_macro.html")
```

### 4.6 ETF 資金流監控

```python
engine = VeritasAutoPlot()
engine.run_etf_flow(
    vdf_base=r"C:\VeritasIntelligenceAnalytics\VeritasDataForge",
    tickers=["SMH", "QQQ", "SPY", "IWM"],
)
engine.save("etf_flow_monitor.html")
```

### 4.7 DataFrame 直接輸入（程式化整合）

```python
import pandas as pd

# 從任何來源取得 DataFrame
df = pd.read_parquet("my_data.parquet")

engine = VeritasAutoPlot()
engine.run_df(df, asset_name="Custom Data")
engine.save("custom_report.html")
```

### 4.8 取得 VDF 掃描結果

```python
engine = VeritasAutoPlot()
engine.run_vdf(vdf_base=r"C:\...\VeritasDataForge", ticker="NVDA")

# 取得完整檔案目錄
catalog = engine.get_vdf_catalog()
for item in catalog:
    print(f"{item['source']}: {item['filepath']}")

# 取得掃描摘要
summary = engine.get_vdf_summary()
print(f"Total files: {summary['total_files']}")
print(f"By source: {summary['by_source']}")
```

---

## 五、測試結果

### 全部 20 項測試通過

| 測試群組 | 測試項目 | 結果 |
|---|---|---|
| VDFNamingParser | Parse LEGO v6 / M01 / M02 / DuckDB / Generic / Unknown | 6/6 PASS |
| GSheetConnector | Parse URL / Build CSV URL | 2/2 PASS |
| VDFOutputScanner | Scan directory / Get latest | 2/2 PASS |
| VDFConnector | Scan / Load ticker / Load file / Export config | 4/4 PASS |
| AutoPlot VDF | run_vdf / run_vdf_file / run_df / run_vdf_compare | 4/4 PASS |
| VDF Catalog | Catalog retrieval / Summary retrieval | 2/2 PASS |

---

## 六、VIA 生態系統整合矩陣

| 系統 | 整合方式 | 狀態 |
|---|---|---|
| **VDF M01 BatchDownloader** | Parquet/CSV/DuckDB 自動掃描 | 完成 |
| **VDF CentralHub LEGO v6** | 8 表 Schema + 檔名解析 | 完成 |
| **VDF M02 AKShare/FRED** | 宏觀資料橋接 + 5 區域 | 完成 |
| **VDF Google Sheet** | URL 解析 + CSV 匯出讀取 | 完成 |
| **VIA SmartAsset AST** | 13 Anchor 錨點 + SHA1 編碼 | 完成 |
| **VIA SSOT Engine** | 模組註冊 + 健康檢查 | 完成 |
| **VPN Pipeline** | M01~M07 全景掃描相容 | 完成 |
| **VRN Anchor AST** | 錨點定位修正系統 | 完成 |

---

## 七、檔案清單

```
VeritasAutoPlot/
├── engine/
│   ├── __init__.py              (27 lines)
│   ├── autoplot.py              (1,131 lines) ← 主控管線 v4.1
│   ├── vdf_connector.py         (1,042 lines) ← VDF 資料連結引擎 [NEW]
│   ├── vdf_bridge.py            (503 lines)   ← VDF Schema 橋接
│   ├── chart_engine.py          (502 lines)   ← Plotly 圖表生成器
│   ├── via_integration.py       (458 lines)   ← VIA 生態系統整合
│   ├── html_renderer.py         (451 lines)   ← HTML 儀表板渲染器
│   ├── design_system.py         (259 lines)   ← 視覺設計常數
│   ├── chart_flow.py            (258 lines)   ← ETF 資金流圖表
│   ├── event_matrix.py          (207 lines)   ← 歷史事件庫
│   ├── data_loader.py           (205 lines)   ← Universal Data Loader
│   ├── ta_engine.py             (182 lines)   ← 技術指標引擎
│   └── bubble_valuation.py      (92 lines)    ← 泡沫偵測引擎
├── output/                      ← 生成的 HTML 儀表板
├── temp/                        ← 測試用模擬 VDF 目錄
├── test_pipeline.py             ← 基礎管線測試
├── test_full_integration.py     ← VDF 整合測試
├── test_vdf_connector.py        ← VDF Connector 完整測試
├── VAP_SYSTEM_REPORT.md         ← v4.0 系統報告
└── VAP_SYSTEM_REPORT_v4.1.md    ← 本文件
```

**總計：14 個引擎模組，5,317 行 Python 程式碼**

---

## 八、部署指南

### 必要依賴

```bash
pip install pandas numpy plotly jinja2 scipy pyarrow
# 可選（DuckDB 支援）
pip install duckdb
```

### 目錄配置

將 `VeritasAutoPlot/` 放置於 VDF 同級目錄：

```
C:\VeritasIntelligenceAnalytics\
├── VeritasDataForge\          ← VDF 資料來源
│   ├── output\
│   │   ├── parquet\
│   │   ├── csv\
│   │   └── VDF_CentralHub_LEGO_v6\
│   └── VDF_M02\
└── VeritasAutoPlot\           ← AutoPlot 引擎
    ├── engine\
    └── output\
```

### 一鍵執行

```python
from engine.autoplot import VeritasAutoPlot

engine = VeritasAutoPlot()
engine.run_vdf(
    vdf_base=r"C:\VeritasIntelligenceAnalytics\VeritasDataForge",
    ticker="NVDA"
)
engine.save()
# → output/VeritasAutoPlot_{timestamp}.html
```

---

> **VeritasAutoPlot™ v4.1** — VDF 資料連結整合版
> 將 VDF 的原始資料自動轉化為視覺智慧
