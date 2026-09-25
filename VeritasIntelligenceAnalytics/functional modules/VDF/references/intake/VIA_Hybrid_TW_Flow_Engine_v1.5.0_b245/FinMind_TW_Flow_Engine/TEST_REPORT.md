# 測試報告

- 擷取引擎：VIA Hybrid Official + FinMind TW Flow Engine 1.5.0
- 官方介面：TWSE／TPEX／TDCC Adapter 1.0
- 分析引擎：VIA TW Branch Capital Circle Engine 1.0.0
- 測試日期：2026-08-30
- Python：3.12.13
- 本輪結果：33 / 33 PASS；Python 編譯 PASS；TPEX 官方即時唯讀煙霧測試 PASS

## 自動測試結果

| 類別 | 數量 | 結果 | 驗證內容 |
|---|---:|---:|---|
| 混合來源／DuckDB／Checkpoint／匯出 | 23 | PASS | 官方優先順序、FinMind 缺口接手、coverage 切洞、自然鍵去重、來源欄位、CSV BOM、Parquet、Ctrl+C 固定保存 |
| 官方資料 Adapter | 5 | PASS | ROC／西元日期、TDCC 分級、TWSE 鉅額 CSV、TPEX 鉅額 JSON、TPEX 價量與融資融券欄位映射 |
| 資金圈與大戶行為純函式 | 5 | PASS | 分點成圈、法人對齊、橫盤吸籌、拆單、定量建倉、換手及日資料限制 |

完整測試指令：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s .\tests -v
```

## 混合來源失敗安全測試

| 情境 | 預期結果 | 結果 |
|---|---|---:|
| 官方最新快照成功 | 先寫資料及單日 coverage；FinMind 只抓之前的歷史缺口 | PASS |
| 官方任一市場失敗 | 不寫部分結果、不建立 coverage；FinMind 保留完整接手機會 | PASS |
| TDCC 回傳日期早於最新交易日 | 使用資料列實際日期建立週資料 coverage | PASS |
| 舊 v1.4 DuckDB | 原地新增 `source_provider`、`source_mode`、`source_dataset`，舊資料標記為 FinMind | PASS |
| 同一日期重跑 | 依自然鍵 `INSERT OR REPLACE`，不增加重複列 | PASS |
| 執行中 Ctrl+C | DuckDB CHECKPOINT 與 JSON 狀態固定保存 | PASS |

## 官方端點即時煙霧測試

在不使用 FinMind Token 的情況下，對 TPEX OpenAPI 執行唯讀測試：

| 資料集 | 官方日期 | 命中測試股票 | 結果 |
|---|---|---|---:|
| `tpex_mainboard_daily_close_quotes` | 2026-08-28 | 3324、8069 | PASS |
| `tpex_mainboard_margin_balance` | 2026-08-28 | 3324、8069 | PASS |

TWSE 與 TDCC 的欄位解析以官方格式合成樣本完成單元測試；完整雙市場連線仍會在使用者 Windows 實際執行時由 fail-closed 路由驗證。任何官方來源逾時、日期不符或欄位異常，都不會被標記為已覆蓋，而會保留給 FinMind 補足。

## 安全與治理

- FinMind Token 僅由 `getpass` 於啟動時輸入，未寫入設定、DuckDB、輸出或稽核報告。
- 官方 Session 不帶 FinMind Authorization Header。
- 券商分點驗證碼頁不自動破解，不使用代理、Token 或 IP 輪替規避限制。
- `VeritasCeleritas.py` 與 `VeritasAegisNexus.py` 已成功載入；缺少可選 `VIA_SuperAccel_Module` 時只產生 WARN，不影響本引擎安全節流與斷點續傳。
