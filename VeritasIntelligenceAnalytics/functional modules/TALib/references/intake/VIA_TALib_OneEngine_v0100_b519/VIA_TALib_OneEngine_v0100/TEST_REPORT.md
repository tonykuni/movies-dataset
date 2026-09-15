# VIA TA-Lib OneEngine v1.0.0 驗收報告

驗收日期：2026-09-09  
結論：整合層 `PASS`；真實 TA-Lib runtime 驗收在本工作環境為 `ENVIRONMENT BLOCKED`。

## 已通過

執行：

```text
python3 -m compileall -q VIA_TALib_OneEngine_v0100
python3 -m unittest discover -s VIA_TALib_OneEngine_v0100/tests -v
```

結果：10 tests，全部通過。

| 驗收項目 | 結果 |
|---|---|
| Python 全檔語法編譯 | PASS |
| Adj Close 必要；不得以 raw Close 靜默替代 | PASS |
| Adj Close factor 還原 Adj O/H/L | PASS |
| VDF `obs_date`／`adj` 欄位識別 | PASS |
| 原始量值／扣當沖量值雙軌 | PASS |
| 一般期間 5/10/20/60/120/240 | PASS |
| RSI、MACD、BBANDS、KD 等特殊 preset | PASS |
| 動態函數目錄及全發現函數調度 | PASS（使用 deterministic Abstract API test double） |
| 量能函數 raw／ex-daytrade 雙算 | PASS |
| BETA 等雙序列 input override | PASS |
| CSV 與唯讀 SQLite 輸入 | PASS |
| SQLite Date+Ticker 增量去重輸出 | PASS |
| Signals 與 VAP activity toggle catalog | PASS |
| CSV、manifest、parameter catalog、registry、signals、VAP catalog 完整輸出 | PASS |
| 外部 JSON 與程式內建 defaults 語意一致 | PASS |

## 環境限制

本工作容器沒有安裝 TA-Lib binary wrapper、pyarrow、DuckDB、SQLAlchemy 或 PowerShell，因此無法在此環境完成以下實體相依驗收：

- 真實 TA-Lib C library 的全部函數涵蓋率。
- Parquet 寫入。
- DuckDB／SQLAlchemy 實體資料庫讀寫。
- PowerShell launcher 實際啟動。

執行 `self-test` 時，引擎依設計回報找不到 TA-Lib 並停止；沒有改用附件舊版 NumPy 公式。部署到 `via_vdf` 環境、安裝 `requirements.txt` 後，請執行：

```powershell
.\Invoke-VIA-TALib-OneEngine.ps1 -Mode self-test -Install
```

合格門檻：`status=PASS` 且 `function_coverage=1.0`。若個別函數失敗，manifest 會記錄 ticker、function、variant、volume basis 與錯誤內容。

## 舊版基準

- 附件來源：`VIA_ENG003_TALibEngine.py v0100`
- SHA-256：`2a86ae2472914c204014cf769d3ccf04d4f1684d29a3b1f9818a88e8a8577b72`
- 舊版內建 self-test：10 PASS、1 SKIP（工作環境缺真實 TA-Lib）、0 FAIL。
- 舊版 runtime 共 64 個硬編碼項目；OneEngine 改由安裝中的 TA-Lib Abstract API 動態發現，不再維護第二份函數清單。
