# VIA B531：2024-01-01 至最新可用日功能測試

## 建議執行方式

在 Windows PowerShell 執行：

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'

# 只在需要同步 GitHub 時使用；若工作樹有變更，會先建立 B531 stash，且不自動 stash pop。
& .\VIA_Reports\handover\VIA_B531_2024_LATEST_FUNCTIONAL_TEST.ps1 -Pull
```

腳本會自動讀取 `MARKET_LISTS_latest.json` 的最新可用日期，將測試範圍設定為：

```text
2024-01-01 .. <資料庫目前最新日期>
```

目前已知資料庫最新日期為 `2026-09-16`，因此本批範圍會是 `2024-01-01..2026-09-16`。若資料庫最新日期改變，腳本不需要修改。

## 完整選項

```powershell
# 離線功能測試；不開網路、不跑當沖抓取、不執行 TA One。
& .\VIA_Reports\handover\VIA_B531_2024_LATEST_FUNCTIONAL_TEST.ps1

# 同步 GitHub 後再測試。
& .\VIA_Reports\handover\VIA_B531_2024_LATEST_FUNCTIONAL_TEST.ps1 -Pull

# 加入指定當沖 CSV；只使用該檔案，不自行找檔或抓網路。
& .\VIA_Reports\handover\VIA_B531_2024_LATEST_FUNCTIONAL_TEST.ps1 `
  -DaytradeFile 'C:\Users\tonyk\Downloads\TWTB4U_20260912.csv'

# 舊版 -RunTAOne 僅保留相容參數；TA-One/TA-Lib 永久禁用，不會執行；技術分析請走 QuantGuard。
& .\VIA_Reports\handover\VIA_B531_2024_LATEST_FUNCTIONAL_TEST.ps1 -RunTAOne

# 只有明確同意外部網路及資料抓取時才使用；這不是一般離線驗收預設值。
& .\VIA_Reports\handover\VIA_B531_2024_LATEST_FUNCTIONAL_TEST.ps1 -EnableNetwork

# 明確要求安裝 OpenCC；必須同時開啟網路。
& .\VIA_Reports\handover\VIA_B531_2024_LATEST_FUNCTIONAL_TEST.ps1 -InstallOpenCC -EnableNetwork

# 明確要求重建 OCR 專屬環境；必須同時開啟網路，預設不重建。
& .\VIA_Reports\handover\VIA_B531_2024_LATEST_FUNCTIONAL_TEST.ps1 -RebuildOCREnvironment -EnableNetwork

# 產生中央頁面並允許 publish；預設只產生，不 publish。
& .\VIA_Reports\handover\VIA_B531_2024_LATEST_FUNCTIONAL_TEST.ps1 -Publish
```

## 對應原始功能

腳本保留原始測試意圖，但將流程固定成 2024 至最新資料範圍：

| 原始功能 | B531 行為 |
|---|---|
| Git status、stash、pull、log | 保留；只有 `-Pull` 才 pull，stash 不自動還原 |
| `via-vetf` | 執行 ETF 驗收 |
| `via-fplogic status/bench/enrich` | 執行首頁邏輯狀態、檔名命中與 enrich |
| OpenCC 安裝 | 預設跳過；`-InstallOpenCC -EnableNetwork` 才執行 |
| `via-rebuild` | 不在一般功能測試中自動重建；`-RebuildOCREnvironment -EnableNetwork` 才執行 |
| `via-vrnlogic reset-backends/sync-db` | 執行 VRN 邏輯庫與政策因子同步 |
| `via-ryg vrn` | 執行 VRN 有界 selftest，固定 `-Timeout 300 -NoOpen` |
| `via-daytrade` | 沒有 `-DaytradeFile` 時跳過；避免無輸入時誤觸發抓取 |
| `via-taone` | 永久封鎖；`-RunTAOne` 僅輸出 BLOCKED，不執行 legacy TA-One/TA-Lib |
| `via-cgfamily` | 執行中央治理家族狀態 |
| `via-census -Tables` | 執行資料庫表與覆蓋盤點 |
| `via-vcgc page --publish` | 預設只產頁；加入 `-Publish` 才傳入 publish |
| DuckDB 日期核驗 | 以唯讀 SQL 檢查 2024、2025、2026 各年度交易日數、標的數與逐標的完整覆蓋 |
| 結果存檔 | 每次落在 `VIA_Reports\\handover\\B531_2024_latest_<timestamp>` |

## 裁決原則

功能自測通過不代表資料庫完整。只要價格資料缺少標的、起始日未達規格、Windows 原始樣本未掛載，或中央站出現 RED、YELLOW、BLOCKED，報告會保留原燈號，不轉成 GREEN。

B531 不會自動設置 `VIA_NET_CONSENT` 或 `VIA_SCRAPE_CONSENT`。只有加入 `-EnableNetwork` 時才明確設定這兩個環境變數；測試完成後應關閉該 PowerShell 視窗，避免同意閘留在後續工作環境。
