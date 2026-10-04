# VCGC 單一 Layout 引擎 v0104

本包包含可執行 Python 原始碼、必要相依程式、功能 SSOT、中央註冊快照、回歸測試及檢核資料。範圍為 VCGC 的 Layout 功能；整套 VDF、VRN 資料庫與其他 VCGC 管理命令仍使用既有 VIA 主系統。

## 整合方式

公開入口維持 `via-vcgc layout`，有效引擎為 `SUP_MDL743_GenericLayoutHub_v0104.py`。內部使用 15 個已列冊模組，共用一份能力 SSOT。Hub v0101 保留成功擷取，v0100 保留 GLE 掛載；兩者仍是必要依賴。被取代的 Hub v0102/v0103 與舊表格修復實作不放入執行包。

新載入器依模組名稱、來源路徑及來源雜湊重用實例；來源變更才重新載入，失敗不留污染快取。System Manager 與使用者頁共用同一個功能呈現函式。清冊附模組分工、有效 API 歸屬、所有 class/def 的行號與雜湊，後續先讀索引，再讀需要的函式，避免反覆讀整份程式。

原生內文、FINANCIAL DATA、首頁任意位置資訊表、年度財報表、左右及上下分表、圖區與可用 OCR、檔名及實體頁排序、快取與 HTML/JSON/CSV/Markdown 輸出，均沿用同一流程。11 個已驗證擷取來源與原始擷取政策保持原位元；修復另存，不推測財務值，不寫正式財務資料庫。

## 解壓後執行

從 ZIP 根目錄執行。使用已具備 PyMuPDF、pdfplumber、pdfminer.six、Pillow、pandas、numpy 的 Python；實測版本見 `VALIDATION.json`。本包不包含 Python 環境、OCR 執行檔或大型模型，也不自動安裝。

```text
python "VeritasIntelligenceAnalytics/supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v0148.py" layout --selftest
python "VeritasIntelligenceAnalytics/supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v0148.py" layout --manifest
python "VeritasIntelligenceAnalytics/supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v0148.py" layout --dir "輸入PDF資料夾" --out "核對輸出資料夾"
```

自測成功回傳 0。文件輸出成功但需核對時維持 `REVIEW`，命令回傳 2；應同時看 `errors`，不可把 REVIEW 誤判為程式例外或正式入庫成功。既有三道治理檢查保留；本環境的 VIA 環境根未設定，治理報告如實顯示 NODATA。

`--evidence` 可重用同一組檔案、同版鎖定來源及同版 PDF 相依套件產生的原始證據；需連同 `documents/<signature>/layout_review.json` 與圖片存在。跨機器缺少圖片或版本不同時，應從原始 PDF 產生證據，不可強行忽略核對。

## 檢核內容

`BUNDLE_MANIFEST.json` 記錄每個執行檔的 SHA-256；私有 `LayoutBundle` 模組負責複製、驗證與打包。`ENGINE_CATALOG.json` 是由 SSOT 即時導出的索引，並非第二份設定。`VALIDATION.json` 記錄本次測試結果。

本次完成 46 項能力、564 個 class/def 定義與 37 個有效 API 歸屬核對；正典新增 238 筆註冊，原有 10,708 個編號保留，範圍外紀錄不變。

整合自測涵蓋 45 項，包括真實財報 360 格、左右欄及不等高上下表、內文接續、原值保存、快取拒絕污染、功能註冊、有效 API 唯一歸屬、完整函式索引，以及封裝的雜湊、路徑與重複檔案核對。另以兩份 23 頁既有證據核對整合輸出，並以一頁財報驗證封裝內原生擷取相依路徑。測試在解壓後的新 Python 程序進行，禁止讀取原工作副本。

繁中圖區 OCR 的 `chi_tra` 在本次環境仍為 UNAVAILABLE；已註冊後端介面不代表模型已安裝。其他 PDF 仍需逐份核對，不能把本次樣本通過等同所有版型都已驗證。

## 併入既有 VIA

先在副本檢查 `CHANGES_FROM_BASE.patch`，其基準 commit 見 `VALIDATION.json`。此 patch 不包含全域中央註冊檔及 AutoCode 歷程冊，避免直接覆蓋主系統的新登錄。本包附的全域中央註冊檔用於獨立驗證；不可直接覆蓋已新增其他登錄的主系統。合併程式與能力 SSOT 後，由目標系統既有正典寫入器執行：

```text
via-vcgc registry-sync --layout-only
via-vcgc registry-sync --layout-only --apply
via-vcgc layout --selftest
via-vcgc layout --manifest
```

先核對 dry run 範圍，再套用；沿用既有編號，範圍外紀錄保持原狀。不須新增 PowerShell 啟動器。本次交付未推送 GitHub、未部署或修改 Windows 主系統。
