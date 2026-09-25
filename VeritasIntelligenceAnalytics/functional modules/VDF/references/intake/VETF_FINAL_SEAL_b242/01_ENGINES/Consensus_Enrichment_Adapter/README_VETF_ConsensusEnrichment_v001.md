# VETF Consensus Enrichment Adapter v001

## 結論

本 Adapter 將既有主動式台股 ETF 最新持股與 Adj Close、FactSet、YFinance 共識資料做時間一致的 as-of join，新增：

- FactSet／YFinance Target Low、Mean、Median、High
- 各目標價相對最新 Adj Close 的 Upside %
- FactSet N、N+1、N+2 EPS Low、Mean、Median、High
- FactSet N、N+1、N+2 Forward P/E（Mean 為主、Median 為輔）
- 分析師數、財政年度、Consensus 日期、資料新鮮度、來源差異與品質旗標

FactSet 與 YFinance 永遠分欄保存，不跨來源平均。

舊矩陣若使用 `EPS 2026 Mean`、`EPS 2027 Mean` 等實際年度欄位，Adapter 會依 Consensus Snapshot 所在年度映射為 N、N+1、N+2，並標記 `INFERRED_FROM_EXPLICIT_FISCAL_YEAR_COLUMNS`；不會把推定結果偽裝成來源原生 N 標記。

## 執行模式

預設為 `candidate`，只寫入新的 sandbox 輸出資料夾，不修改來源資料或正式資料庫。

```powershell
python .\VETF_ConsensusEnrichment_Adapter_v001.py `
  --holdings "D:\VDF\databases\active_etf_holdings.csv" `
  --prices "D:\VDF\databases\tw_stock_price_daily.parquet" `
  --factset "D:\VDF\databases\factset_consensus.parquet" `
  --yfinance "D:\VDF\databases\yfinance_consensus.parquet" `
  --output-dir "D:\VDF\candidate\vetf_consensus" `
  --asof latest `
  --write-mode candidate
```

SQLite／DuckDB 輸入必須使用 `路徑::資料表`：

```powershell
--holdings "D:\VDF\databases\vetf.duckdb::active_etf_holdings_daily"
```

## 相依套件

核心計算與 CSV／JSON／SQLite 只使用 Python 標準函式庫。

選用後端：

- `pyarrow`：讀寫 Parquet
- `duckdb`：讀寫 candidate DuckDB
- `pandas`：DuckDB DataFrame bridge／Parquet fallback
- `polars`：環境偵測預留，後續可作大型資料加速

缺少選用後端時不會生成假 Parquet 或假 DuckDB，而是在 manifest 明確記錄 `SKIPPED_MISSING_BACKEND`。

## 資料時間規則

- 持股：每檔 ETF 取 `holding_date <= analysis_date` 的最新完整快照。
- 價格：每檔股票取 `price_date <= analysis_date` 的最新 Adj Close。
- Consensus：每個來源取 `snapshot_date <= analysis_date` 的最新快照。
- 未來日期資料一律禁止加入，避免 Look-Ahead Bias。

## Forward P/E

```text
fs_forward_pe_n  = price_adj_close / fs_eps_n_mean
fs_forward_pe_n1 = price_adj_close / fs_eps_n1_mean
fs_forward_pe_n2 = price_adj_close / fs_eps_n2_mean
```

同時輸出 Median EPS 版本。EPS 為零、負值或缺失時不輸出具有誤導性的負 P/E，而以狀態欄標記原因。

## 寫入治理

- Append-Only：同分析日、同內容第二次執行為 `SKIPPED_IDENTICAL`。
- 同分析日已有不同內容時為 `APPEND_ONLY_CONFLICT`，拒絕覆寫。
- `canonical_write_enabled` 預設為 `false`。
- 正式寫入還需要 P0/P1 接受、兩個不同授權證明、雙重資料身分與完整 provenance。

## 測試

```powershell
python .\test_vetf_consensus_enrichment_v001.py
```

測試涵蓋 ticker 正規化、每 ETF 最新持股、價格／Consensus as-of、防止前視偏誤、Target Upside、N～N+2 Forward P/E、負／零 EPS、幣別阻擋、來源不混合、雙重身分、來源差異、Append-Only 與 canonical Gate。
