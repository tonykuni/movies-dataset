# VCGC 輸出表頭普查:SSOT 碼 + 欄位 + 來源(2026-10-05)

依 **L111 ⑦ 編號流程**(政策冊 v0104):子系統的 SSOT 編號格留白;母系統偵測衝突,資訊交給操作員與 AI 協調;協調完子系統更新 SSOT,號碼仍留空;母系統偵測無誤後發號;子系統依鍵自動擷取。**不同來源 = 不同輸出號**(L108 ②),即使同一份資料。

- 完整明細(每張表的欄位 `name:type`、來源、現有號碼、表頭冊比對):`VCGC_OutputHeaderCensus_20261005.json`。
- 唯讀:只讀庫(`READ_ONLY ATTACH`)、parquet schema 與冊,不寫子系統檔。

## 範圍與總數

| | 數量 |
|---|---|
| 輸出(表 / parquet 函式) | **260**(VDF 255 · VRN 5) |
| DuckDB 庫 | 12 |
| VAKE store(AkShare 每支函式 = 一個來源) | 218 |
| 已有號碼 | **7**(只有中央 IDX 冊的核心表) |
| 沒號碼(待母系統發號) | **253** |
| 來源未登 | **30** |
| 一號多源(L108 要分號) | **5** |

> 容器只有前幾輪實抓留下的庫(台股 / 國際 / VAKE / MDL003–007 / VRN 研報);工作站資料家的完整普查要在工作站跑同一套(資料不進 git)。

## 衝突旗標(母系統偵測 → 給子系統協調)

### 1. 一號多源:同一張表、多個來源、一個號(違 L108)

| 表 | 現有號 | 來源 | 表內來源欄 |
|---|---|---|---|
| `vdf_tw_market.tw_daily_prices` | VIA-CORE-IDX001 | e054 TWSE/TPEX · e064 YFINANCE | **無** |
| `vdf_global_market.cross_macro` | VIA-CORE-IDX038 | e055 四變體:FED · OTHERS · TWSE/TPEX · YFINANCE | **無** |
| `vdf_global_market.sentiment_daily` | VIA-CORE-IDX039 | e055 四變體 | **無** |
| `vdf_global_market.factset_earnings` | VIA-CORE-IDX041 | e055 四變體 | 有 |
| `vdf_tw_market.tw_trading_daily` | VIA-CORE-IDX005 | e055 四變體 · e057 TWSE/TPEX | 有(`src`) |

- 現行中央 IDX 號以**表名**為鍵,不分來源。
- 依 ⑦:每個來源要各自一個輸出號。
- 做法二選一(VDF 決定):**拆表**,或**表內帶來源欄並以來源分號**。
- 前三張沒有來源欄,目前無法分辨每一列是哪個來源。

### 2. 來源未登(30 張):冊上找不到「哪支引擎 / 哪個來源」產的

- **VDF(25)**
  - `fg_groups` / `fg_members` / `fg_runs` / `fg_status`:族群目錄,屬 VCGC / VDF 治理表,不是資料。
  - `tw_active_etf_list` · `tw_stock_list` · `aaii_sentiment` · `akshare_futures` · `akshare_macro` · `cnn_fear_greed` · `cnn_subindicators` · `fred_macro` · `stock_filter_consensus`。
  - MDL006 財報 10 張:`balance_sheet_*` · `cashflow_*` · `income_statement_*` · `ratios_*` · `daily_history` · `valuation_snapshot`。
  - MDL007:`parse_log` · `ssot_resolved`。
- **VRN(5)**:`vrn_report_basic`(54 欄)· `vrn_report_analyst` · `vrn_report_metrics` · `vrn_nlp_text_summary` · `vrn_pipeline_runs`。

### 3. 沒號碼(253 張)

除上面 7 張核心表外,其餘(含 218 支 AkShare 函式輸出)都還沒有輸出號。照 ⑦:先補來源、過偵測,再由母系統發號。

## 建議的發號鍵與流程(待操作員點頭再建)

1. **鍵** = `子系統 | 來源 | 表`,例:
   - `VDF | e054:TWSE/TPEX | tw_daily_prices`
   - `VDF | e064:YFINANCE | tw_daily_prices`
   - `VDF | akshare:macro_china_cpi | macro_china_cpi`
2. **子系統**:在自己的 SSOT(fetch 冊 / 表頭冊)填表名 · 欄位 · 來源,號碼格留白。
3. **母系統**:跑普查做偵測(同名異頭 · 一號多源 · 重號 · 來源未登),紅就出資訊卡、不發號;無誤才由中央編號(CGC_MDL237)發 OUT 號,寫進中央號碼冊。
4. **子系統自動擷取**:執行時依鍵讀中央號碼冊取號。不手抄;冊上沒號就照實寫 NODATA。

## 交接工作項(VCGC-REQ158)

| 工作項 | 負責 | 內容 |
|---|---|---|
| `vdf-multisource` | VDF_SystemManager | 一號多源 5 張 |
| `vdf-nosource` | VDF_SystemManager | 來源未登 25 張 |
| `vrn-nosource` | VRN_SystemManager | 來源未登 5 張 |
| `vcgc-assign-fetch` | VCGC | 普查動詞正式化 + 無誤發號 + 子系統讀號介面 |
