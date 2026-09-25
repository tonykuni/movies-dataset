# VCGC / VRN / VDF 接手驗收（2026-09-25）

狀態：驗收進行中，尚未宣告正式環境啟用完成。

## 授權與基線

- 操作員要求接手全景掃描、修正、測試、真實測試、整併、使用者測試及 GitHub 整合，隨後明示「核准一切動作」。本次必要的 PowerShell 與模板修正已包含於該授權。
- main 基線 `ee99f06cb9086a3f88cfc27d97a7e2dfd9ca3a99`，已含 PR #117 / #121。
- 整合 PR #120 的 `e84df5f64af0677d52a8899e7571f6c58eb9b149`，保留來源歷史，不 rebase / force push。衝突僅元件冊及 MasterControl 再生頁，由正主工具重生。
- 使用倉內 CGC_MDL158 v0106 的 read / slice / scan，並沿用 CGC_MDL149、SelftestGrid、VRN_AutoTestLoop、ENG089 / ENG090 及唯一 VIA_HTML_UI。
- 掃描 main 活樹 1,543 檔，135 筆靜態提示；其中模板豁免 ACCEL 22、VERB 4、HARDIMP 27、PINVER 4。提示不是 135 個已證實執行錯誤。

## 修正與驗證

| 項目 | 變更 | 已量到的驗證 |
|---|---|---|
| Z210 模板通知 | 原中央 UI 的第一個 IIFE 匯出 `__viaToast`，同步 IIFE 明確綁定；manifest 發布 2026-09-25 修正版 | 原頁同步會產生 TypeError；修正版所有 pageerror 都納入失敗，不放行 toast |
| Z214 瀏覽器測試 | v0102 明確測無資料不覆蓋有日期狀態；有資料更新用獨立合成 DuckDB 跑完整流程 | 空資料 20/20；有資料 20/20，兩者不可混稱真市場實測 |
| ENG090 v0102 | 長連結／路徑可換行，避免窄螢幕撐寬 | 原 390px 視窗膨脹為 421px，舊測試比兩個膨脹值而誤過；新斷言釘住 390px；23/23 引擎自測 |
| 日期行情 oracle | 同日獨立交易所價缺席標 NODATA，另列覆蓋率；有值但錯價仍 fail | 4 個回歸案例：全缺、錯價、部分覆蓋、全覆蓋 |
| Z211 PowerShell | Invoke-VIA-VRN v0105 從本輪模板連結冊解析 centralUI；缺頁回原始報告；NoOpen 保留 | PowerShell 7.6.6 語法解析與 3 條入口選擇實測；尚非 Windows 六步正式執行證據 |
| Z213 層級 | via_vrn_logic_book v0110 將 ENG090 掛 L4 產出，VDF 財報來源歸屬不變 | 六層冊 17/17 |
| #120 整合 | ENG089 v0101、VCGC v0130 與自測迴圈 v0107 | ENG089 12/12（含 Chromium）；VCGC 38/38 |

## 誠實限制

- 本容器沒有操作員的正式市場 DuckDB 或 Windows 家族環境，合成財報資料只驗契約及交接。
- 106 份原始報告從授權 OneDrive 取得，逐檔保存大小與 SHA256。一次下載出現截斷，重新取得完整檔後必須重跑，不能將傳輸壞檔當程式缺陷或從分母刪掉。
- CGC_MDL187 v0100 的 KILL-05 無授權輸入，一律禁止 `.ps1`；本次即使已取得操作員明示許可仍會報紅。保留其原判，未改閘或排除檔案換綠。
- 同閘 KILL-07 將 PR #120 的 VCGC 交接說明字串（列供人手貼的 PowerShell）判為代設環境變數。實際沒有執行該字串；完整閘結果保留，不假稱全過。
- 正式同意閘、金鑰與資料庫均不由自測設置或重寫。

## 重現

使用獨立 Python 3.12 環境；Playwright Python / Node 均固定 1.55.0，Chromium 140.0.7339.16，PowerShell 7.6.6。無需另做第二套 UI。

`test_VRN_TakeoverRegression.py --emit-fixture <新的暫存夾>` 產生標示 SYNTHETIC 的財報測試庫，交給 ENG090 `run --db ... --page ... --out ...`。瀏覽器測試 v0102 用 `VIA_VRN_FINSTAT_PAGE`、`VIA_VRN_FINSTAT_OUT`、`VIA_UX_ARTIFACT_DIR` 指向該輪產物。

完整結果、剩餘限制與 GitHub CI 狀態於收尾追加，未量到的項目不列綠。
