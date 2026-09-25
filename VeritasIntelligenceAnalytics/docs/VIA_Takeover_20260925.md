# VCGC / VRN / VDF 接手驗收（2026-09-25）

狀態：PR #122 已合併 main（`2333185c`），最新 head `face9f2a` 的 Windows/Chromium UAT 全過；正式環境全面啟用仍未完成。新增每日資料要求及修正見 `VIA_DailyData_20260925.md`。

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

## 真實報告修正與 CI 接線（第二輪）

- 106 份原件大小全部與 OneDrive 清單相符，總計 104,446,769 bytes。完整重跑：PASS 238 / WARN 13 / FAIL 0，總判 AMBER。未提供人工逐欄答案，不能稱為所有擷取欄位 100% 正確。
- 報告資料庫引擎 v0107 修復真實 Citi 產業報告的修訂表：New / Old 金額與 Chg.% 分開；單位只讀宣告、指標與本格，不拿其他列的百分比決定整表單位。僅明確的年 × New/Old/Chg 合併表頭才展開；多年份歧義保留 REVIEW。
- 百分比保留原文、座標與數值，不填金額寬欄，不參加金額等式。單位不一致的等式另計 skipped_unit_checks；錯誤金額負控仍失敗。每股金額不乘整表百萬倍。已知財務指標列不當表頭。
- 13 個接手回歸全部通過（原行情 4 個＋財報 9 個）。真實 Citi 原 6 條假等式失敗消除，實際金額 12/12；全部報告可驗式由 155/161 變成 154/154，分母改變包含百分比與單位資格，不冒稱舊 161 條全部轉綠。
- 97 份 PDF 中 55 份讀出財務列，共 5,782 列；舊版 5,842 列中含合併欄、多值與誤選表頭，列數不當正確率。複雜跨欄表仍需人工真值與後续版面驗證。
- 本輪 13 警示仍包含影像 OCR 未接線、無文字層與未抽到財務表／未通過無框線表資格；正式市場庫缺席使 40 份有目標價者皆無法完成 ADJ 換算。搜尋可存取 OneDrive 的兩個正式市場庫檔名均無結果。
- 首輪 361 站全格子為 OK 329 / FAIL 21 / SKIP 11 / TIMEOUT 0；正式三庫均缺席，不能把零改動表述為已驗過正式庫。首輪包含我選到舊管理器重生總控頁所造成的契約失敗；已改由尾版 v0148 重生，19/19 通過。
- 本機照新增 Windows CI 步驟跑：ENG089 12/12、ENG090 23/23、接手回歸 13/13；空資料及獨立 SYNTHETIC 庫各 20/20 瀏覽器操作。唯一制式模板零 pageerror，390px 視窗零橫捲。CI 會保存 HTML、截圖、JSON 與合成庫證據。
- 全格子發現取倉時未含根規則檔，已補齊；VRN SSOT 增補單元由 19+1 error 恢復 20/20。沙盒補裝 yfinance 後，五日擷取與 TWREV 的環境失敗已在對照樹轉綠。乾淨 main 的其他紅站同樣逐站比對，最終表待本輪全格子完成補上。

## 全格子收斂與 Windows 路徑覆核

- 第二輪全格子（程式 commit `21168a6e`）：361 站，OK 340 / FAIL 12 / SKIP 9 / TIMEOUT 0，317.4 秒。12 個剩餘紅站在乾淨 main 的同環境對照也都紅；逐站原判與原因存於 `VIA_Takeover_Evidence_20260925.json`。它們包含缺正式三庫、產業／上游輸出、未生成的深頁、既有 NODE_PATH 自測假設，以及讀上一輪未達 95% 的治理台；不把既有失敗寫成已解。
- GitHub Windows 第一次擴充驗收中，總控頁契約與瀏覽器、13 個接手回歸全部過；ENG089 跨輪自測失敗，因 TEMP 短路徑與正規化長路徑比較。v0102 僅正規化自測路徑，不改執行期建構／交接。用路徑別名負控重現：舊版⑪失敗、新版十二檢全過。
- 同時明設測試用 NODE_PATH 指向 CI 已安裝的 node_modules，避免暫存夾中的 ENG089 瀏覽器探針找不到 Playwright 而 SKIP。Windows CI 將在新 head 重新驗證；最終結論須看該 head 的結果。
- 非個股框架見 `VIA_NonStock_Database_Framework_20260925.md`，包含多主體、重點與證據、Evernote 連結、既有表對映及 migration 邊界。106 件中 61 件個股、44 件其他類型、1 件影像待 OCR；不把影像當成已解析文件。

## 同步重送的真實操作修正

Windows head `f5968206` 已通過整條擴充 CI（主控台、ENG089 12/12 且無 SKIP、ENG090 23/23、接手回歸 13/13、兩种財報瀏覽器各 20/20）。追加操作測試仍抓到 SYNCHRONIZER 既有的競態：同一 timestamp / revision 的重複通知會在 250ms 延遲存檔期間抹掉使用者剛切換的勾選。

本輪修正 latest 判法：重複版本不重套，同時間的更高 revision 與更晚時間仍接受。storage 與真正跨頁 BroadcastChannel 兩條路均作負控，原版 2/4（兩個重送情境失敗），修正版 4/4。不是延長等待或忽略錯誤換綠；local / remote / manual 設定保留。唯一模板的 changelog、檔案大小與 sha256 同步更新，新增測試也接入 Windows CI。最後 head 的結果以 PR #122 的 checks 為準。

追加五站中一次 VCGC mtime 保全檢失敗，是我同時還原正則冊時間戳造成，該次保留為失敗；停止所有寫入後獨立重跑 38/38 通過。這次干擾不可算成正式庫或 VCGC 程式缺陷。
