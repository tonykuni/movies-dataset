# VIA TA-Lib OneEngine 整合矩陣

| 舊版能力 | 舊版狀況 | OneEngine v1.0.0 | 決策 |
|---|---|---|---|
| 指標範圍 | 64 型，僅 10 種 K 線型態 | 由 `talib.get_functions()` 動態發現安裝版本全部函數 | 取代硬編碼清單 |
| 計算後端 | TA-Lib 失敗時靜默退回自寫 NumPy | 僅 TA-Lib；缺套件或函數失敗即誠實記錄 | 防止公式與暖機期漂移 |
| 期間參數 | 每個指標一個 period，或命令列全域覆寫 | 一般 `timeperiod` 同時計算 5/10/20/60/120/240；特殊指標獨立 preset | 參數完整展開 |
| RSI/MACD/BB/ATR | 14、12/26/9、20/2、14 | 保留，且全部放在 JSON SSOT 可修改 | 保留 |
| 價格 | Adj Close 在位則還原；缺席可 raw fallback | Adj Open/High/Low/Close 直讀優先；僅有 Adj Close 時可用同列 factor 還原；股票無 Adj Close 直接拒絕 | 口徑收緊 |
| 成交量 | 以 split factor 調整單一 volume | 保留交易所原始量；另建扣當沖量，不互相冒充 | 配合台股分析 |
| 成交值 | 無 | 原始成交值與扣當沖成交值雙欄 | 新增 |
| 量能指標 | 單一 volume | OBV/AD/ADOSC/MFI 等分 raw/ex-daytrade 各算一套 | 新增 |
| 資料來源 | CSV/TSV/JSON/SQLite/DuckDB | 再加 Parquet、Feather、JSONL、目錄批次、SQLAlchemy | 擴充 |
| VDF 價格湖欄位 | 無固定對接 | 直接識別 `obs_date` 與 `adj`，並正規化為 Date 與 Adj Close | 新增 |
| 資料庫安全 | SQLite 非明確唯讀 | DuckDB/SQLite 唯讀；SQL 僅允許 SELECT/WITH | 強化 |
| 雙序列輸入 | `--map b=` 個別處理 | `input_overrides` 可將 BETA/CORREL 的 price0/price1 指到任意數值欄位 | 整合 |
| 訊號 | 固定主要指標與 K 線型態 | 保留門檻，從 feature registry 對應實際欄名 | 整合 |
| VAP | 直接找特定繪圖檔 | 輸出 `VIA-VDF-VAP-CONNECTION-MANIFEST/1.0` Catalog | 解耦 |
| 輸出 | CSV/JSON | Parquet 與 CSV 雙輸出、manifest、參數 catalog、feature registry、signals、VAP catalog | 擴充 |
| 增量 | 無 | 檔案及資料庫皆可 Date+Ticker 去重合併，當次結果優先 | 新增 |

舊版附件保留為稽核來源，不再是 runtime 計算入口；VAP 只讀 OneEngine 產生的 Catalog 與 feature lake。
