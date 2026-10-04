# VRN Layout reuse v0101 — 2026-09-27

本次找回其他對話的 `GenericLayoutEngine_AllEngines_v2.1.0.zip`，四個核心檔案與本倉已登錄 intake 完全相同。沿用完整核心、路由器、adapter SDK 與後端實作，不另造擷取引擎。不能據此宣稱全球最強；32 個 adapter 介面也不代表 32 個模型已安裝。

## 改動

- SUP_MDL743 v0101：使用既有 pdfplumber / PyMuPDF / pdfminer.six，保存整頁文字座標、所有頁面、表格候選與既有財務矩陣；不按固定象限裁切。整頁文字還原不是完整表格結構辨識。
- CGC_MDL149 v0146：新增 `via-vcgc layout`，依序執行既有省 Token、政策、環境閘門；其他路由交還 v0144。
- CGC_MDL095 v0161：新增 `vcgc_layout_review`。原有 92 個 task 定義相容。
- HTML：依輸入檔名由上而下排列，每份內依實體頁排列；保留內文、原頁對照及 FINANCIAL DATA。數值零、負數、空白保留來源差異，不補算、不猜年度。
- SSOT：11 份既有擷取來源以 SHA-256 鎖定，執行前後核對。VDF 清單更新、既有 basic / financial 擷取與資料庫寫入均未改動。
- 相同輸入、引擎、套件、政策及 bridge 內容才可用快取；原頁影像缺少時重建。涉及 OCR 或低文字量頁面不重用整份快取。

## 實測證據

| 項目 | 結果 |
| --- | --- |
| 原 GLE 附件測試 | 18 項通過 |
| 既有 Hub 自測 | 通過；報告九檢、無失敗 |
| 新路由／內容／鎖定回歸 | 13 項通過，包括右上與下方座標、後續財報頁、大小寫副檔名、快取及治理閘門 |
| Deck | 舊 92 個 task 不變；新增 1 個 |
| 真實報告 | 晶心科 CTBC 15 頁、華南裕民 8 頁，共 23 頁 |
| 實際後端 | 兩份各 3 個後端 PASS；不表示財報數值已全部通過驗證 |
| 文字座標輸出 | 晶心科 1,166 / 1,166；裕民 851 / 851，共 2,017 項全部存在 HTML |
| 首頁年度資訊 | 晶心科 2025F / 2026F / 2027F；裕民 EPS 5.21 / 3.24 / 5.54 / 4.19 / 5.07 均保留 |
| 結構候選 | GLE 27 個；既有財務讀取器 19 個矩陣，兩者不可相加當獨立表格數 |
| 真實快取 | 裕民報告第二次命中；晶心科有低文字量頁面，不標為整份可快取 |
| 鎖定 | 11 個來源 SHA-256 均未改變 |
| 靜態與登錄差異 | 4 個新 Python 檔解析／編譯通過，均有 accelerator bridge；Spec 僅新增一項、ledger 僅附加一筆 |

部分無框線表格仍只偵測到表頭，尤其晶心科首頁年度表格。下方數字在整頁文字座標還原可見，但不得當作完整結構化矩陣已修復。整體狀態維持 REVIEW。

## 登錄與啟用界線

| 表面 | 狀態 |
| --- | --- |
| VCGC 命令 | 新增 layout wrapper，保留原三道治理閘門 |
| InputConsole Spec | 新增 vcgc_layout_review |
| Deck | 新增同名 task |
| SelftestGrid | 既有 GenericLayoutHub 站以尾版選擇新版 selftest |
| SystemManager | 沿用既有家族盤點；未另建管理器 |
| 短令／PowerShell | 沿用 via-vcgc 尾版選擇；未更改任何 PowerShell |
| AutoCode / Component SSOT | ledger 已附加；沿用既有家族代號，新函式編號尚待完整工作樹以 VCGC registry-sync 產生 |

目前是精簡工作副本。從同一基底補回既有 NLP v0103 後，正式入口的省 Token 閘門已 GREEN；政策步驟仍回傳 rc=2，顯示 accelerator / 環境計畫 / 還原順序資料不齊。未跳過閘門。真實 PDF 實測是隔離呼叫 layout hub，不能當作正式 VCGC 全流程通過。

未對精簡工作樹執行 `registry-sync --apply`，以免把未下載的正式元件誤標退役。未宣稱七冊登錄全數完成。瀏覽器安全政策禁止本機 file URL，故 HTML 已做資料／順序／字項完整性核對，但尚未完成瀏覽器畫面驗收。

## 在完整且治理可用的工作樹執行

```text
via-vcgc layout --dir <PDF檔案或目錄> --out <核對輸出目錄> --open
via-vcgc layout --selftest
```

輸出 `LAYOUT_REVIEW.html` 與 `LAYOUT_REVIEW.json`。回傳 rc=2 表示 REVIEW 或 NODATA；不可當作全綠入庫完成。正式庫不由此入口写入。

本次僅完成本機升級候選與審閱補丁，未推送、合併或部署。先前自動核准審核拒絕 GitHub 推送，理由為遠端尚未核實且發布授權不足，本次未改用其他方式發布。安裝前須核對基底及版本號，完成全工作樹的正式登錄、治理與畫面驗收。
