# VIA TA-Lib OneEngine v1.0.0

這是附件 `VIA_ENG003_TALibEngine.py v0100` 的整合升級版。Runtime 只有一個計算入口：`VIA_TALib_OneEngine.py`。它以 TA-Lib Abstract API 動態讀取安裝版本的全部函數、輸入、輸出與參數，因此 TA-Lib 新增函數時不用再人工補清單。

## 已整合

- 資料來源：Parquet、CSV/TSV、JSON/JSONL、Feather、資料夾批次、DuckDB、SQLite、SQLAlchemy。
- 可直接識別 VDF 價格湖欄位 `ticker | obs_date | open | high | low | close | adj | volume | year`；其中 `adj` 視為 Adj Close。
- 資料庫輸入採唯讀；查詢只允許 `SELECT`／`WITH`。
- 股票、ETF、指數採 `ADJUSTED_PRICE_ONLY`。Adj O/H/L/C 直讀優先；若只有 Adj Close，可用同列 `Adj Close / raw Close` 還原其餘三價；沒有 Adj Close 不會悄悄改用 raw Close。
- 原始成交量／值與扣除當沖成交量／值同時保留：`volume_raw`、`volume_ex_daytrade`、`turnover_raw`、`turnover_ex_daytrade`。
- 量能指標針對 raw 與 ex-daytrade 各計算一套；扣當沖資料缺席時留空並警告，不拿 raw 冒充。
- 一般 `timeperiod` 預設同時計算 5、10、20、60、120、240。
- 特殊預設：RSI 14、MACD 12/26/9、BBANDS 20/2/2、ATR/ADX/MFI 等 14、KD 9/3/3、ULTOSC 7/14/28、SAR 0.02/0.2；全部都可在 JSON 改。
- 保留附件的主要訊號門檻與 K 線型態事件，輸出最新訊號表。
- 產生 VAP Catalog，沿用 `VIA-VDF-VAP-CONNECTION-MANIFEST/1.0`、Request ID 對應與 `Database + Table + Field + Version` identity。
- Parquet／CSV 採 Date+Ticker 增量去重；輸出 UTF-8-SIG CSV。

## 執行

PowerShell（預設會優先找 `via_vdf` 環境）：

```powershell
.\Invoke-VIA-TALib-OneEngine.ps1 -Mode self-test
.\Invoke-VIA-TALib-OneEngine.ps1 -Mode catalog -CatalogOutput .\output\TALib_All_Parameters.json
.\Invoke-VIA-TALib-OneEngine.ps1 -Mode validate -Source C:\data\StockData.parquet
.\Invoke-VIA-TALib-OneEngine.ps1 -Mode run -Source C:\data\StockData.parquet
.\Invoke-VIA-TALib-OneEngine.ps1 -Mode run -Database C:\data\tw_market.duckdb -Table tw_prices_adj
```

第一次且環境尚未安裝相依套件時才加 `-Install`。引擎不自行下載資料，也不改寫來源資料庫。

Python：

```powershell
python VIA_TALib_OneEngine.py defaults
python VIA_TALib_OneEngine.py catalog --config VIA_TALib_OneEngine.config.json
python VIA_TALib_OneEngine.py run --config VIA_TALib_OneEngine.config.json --source C:\data\StockData.parquet
```

## 參數如何修改

所有 engine/source/data/activity/indicators/signals/quality/output 參數都在 `VIA_TALib_OneEngine.config.json`。最常改的部分：

```json
{
  "activity": {
    "display_mode": "ex_daytrade",
    "indicator_volume_bases": ["raw", "ex_daytrade"]
  },
  "indicators": {
    "generic_periods": [5, 10, 20, 60, 120, 240],
    "function_overrides": {
      "RSI": {"variants": [{"timeperiod": 7}, {"timeperiod": 14}, {"timeperiod": 21}]},
      "SMA": {"variants": [{"timeperiod": 20}, {"timeperiod": 60}]},
      "CDLDOJI": {"enabled": false}
    },
    "single_price_input": "close",
    "input_overrides": {
      "BETA": {"price0": "close", "price1": "benchmark_close"},
      "CORREL": {"price0": "close", "price1": "benchmark_close"}
    }
  }
}
```

`single_price_input` 控制所有 TA-Lib 單價函數使用哪一個正規化價格欄位，預設為調整後 `close`。BETA/CORREL 等雙序列函數可用 `input_overrides` 指到 `benchmark_close`；來源若有同名或設定別名的基準調整後收盤價就會納入計算。`catalog` 會輸出目前已安裝 TA-Lib 的每個函數、原生 default、解析後 variants、實際輸入綁定與輸出，這份就是 UI 參數面板的資料來源。

資料庫輸出可設 `database_if_exists` 為 `replace`、`append` 或 `append_deduplicate`；預設依 Date+Ticker 合併去重後回寫。

## 輸出

- `VIA_TALib_Features_Parquet`：無副檔名 Parquet。
- `VIA_TALib_Features_CSV`：無副檔名 CSV。
- `VIA_TALib_Feature_Manifest.json`：來源口徑、涵蓋率、錯誤、hash。
- `VIA_TALib_Parameter_Catalog.json`：全部函數與可改參數。
- `VIA_TALib_Feature_Registry.csv`：每個輸出欄位的函數、參數、價量基準。
- `VIA_TALib_Latest_Signals.csv`：最新量化狀態。
- `VIA_TALib_VAP_Catalog.json`：VAP 可直接註冊的欄位與切換契約。

## 驗證

```powershell
python -m unittest discover -s tests -v
python VIA_TALib_OneEngine.py self-test --config VIA_TALib_OneEngine.config.json
```

單元測試可在沒有 TA-Lib C library 的環境驗證整合層；`self-test` 必須載入真實 TA-Lib，負責實際函數涵蓋率驗收。

## 治理界線

附件舊版的 NumPy 自寫公式只作歷史稽核參考，不再於 production fallback。這能避免同一欄名在不同機器上由不同公式、暖機期或 NaN 規則產生。VAP 負責顯示與參數編輯，不重算指標；VDF 負責來源資料，OneEngine 負責唯一技術指標計算。
