# VRN 單一模組化 Layout 引擎 v0102

2026-09-27。本版接續 v0101；本文件記錄目前的功能、註冊及實測狀態。v0101 文件中的登錄待辦及政策缺件屬前版歷史狀態。

唯一使用入口仍是 `via-vcgc layout`。沿用已驗證的擷取與 GenericLayoutEngine v2.1.0 四件原模組，在擷取後整合文本、表格、圖區與證據修復。沒有重造 PDF 擷取器，也沒有更動 VDF 台股清單更新、既有 basic / financial 擷取或正式資料庫。

## System Manager 與使用者共用說明

`SUP_MDL743_GenericLayoutHub_v0102.py` 頂部有人可讀的完整功能摘要及 AST 可讀的 `ENGINE_MANIFEST`，指向 `VIA_Layout_Capabilities_SSOT_v0100.json`。System Manager v0113 以 AST 讀取，無須執行被檢視引擎。

SSOT 包含 46 項能力、模組與函式綁定、依賴限制、驗證項目、31 段附件函式對照及統一參數。System Manager 及使用者 HTML 顯示相同功能與中央註冊碼，機器目錄另提供每項能力對應的函式編號。實作存在、中央登錄與本次文件品質分別呈現，避免把 IMPLEMENTED 誤當全部資料已驗證。

## 模組與責任

| 元件 | 責任 |
| --- | --- |
| CGC_MDL149 v0147 | 保留三道治理閘門、Layout 唯一入口及限定範圍登錄 |
| SUP_MDL743 Hub v0102 | 來源鎖定、既有擷取委派、階段協調、快取、證據與統一輸出 |
| LayoutCommon v0100 | SSOT、原生文字與行、座標、數值、上下最多五行上下文防撞 |
| LayoutText v0100 | 字型／描邊／疊印粗體證據、七階角色、頁首頁尾及免責子樹、標題及段落、混合欄序 |
| LayoutTables v0100 | 座標投影、年度漏列、跨格表頭、折行、無來源空軸清理、驗算、去重、多表、續表及並排關係 |
| LayoutFigures v0100 | 影像碎片留存、複合子圖、雙 Y 軸防誤切、共用圖例、來源綁定及既有 OCR 委派 |
| CGC_MDL069 v0113 | 靜態讀取引擎描述，核對實作與測試綁定、顯示中央註冊碼及完整功能 |
| 舊 GLE 四模組與 Hub v0101 | 保持原件；native 擷取、adapter SDK、後端及路由器以委派方式重用 |

四個私有階段共用同一個既有加速器 bridge，不安裝依賴、不設定網路同意，也不自動下載模型。32 個既有 adapter 介面不表示 32 个模型均已安裝或驗證。

## 正式登錄

由既有 VCGC `registry_sync` 正典寫入器配號，未手填元件號。`registry-sync --layout-only --apply` 僅同步此整合相關身分；其他元件按既有紀錄保留，不重新宣稱已驗證，也不因精簡工作樹缺檔而退役。

- 全部 46 項功能與其實作綁定已 REGISTERED。
- 新增 355 筆中央元件／類別／函式／功能紀錄，包含舊 GLE 的委派定義。
- 原有 10,350 筆中央編號保持一致；範圍外紀錄完整不變。
- 最後 dry run：new=0、changed=0、stale=0。
- InputConsole Spec 及 AutoCode ledger 已更新。沿用 Deck v0161、既有尾版路由及 SelftestGrid GenericLayoutHub 站；未更動 PowerShell。

完整功能及中央碼以產出的 `ENGINE_CATALOG.json` 為準，文件不另維護第二份清單。

## 實測

37 項針對本次行為及負例的回歸通過，包括來源鎖定、零／空白／負數、粗體證據、標題防併、跨頁、單雙欄、表圖遮罩、投影、跨格、多表與續表、圖區、英文 Tesseract 裁切、缺件狀態、中央編號穩定、靜態目錄、匯出及快取。先前已通過且鎖定的舊引擎測試不反覆執行。

正式 VCGC 路由經省 Token／政策／環境既有步驟後，重用已核對的擷取證據執行新修復。環境根仍回報 NODATA；未把環境還原點或所有環境驗證宣稱 GREEN。路由 rc=2 是文件 REVIEW，輸出 errors=[]。

| 文件 | 頁數 | 原生文字 | 修復表格 | 首頁年度表 |
| --- | ---: | ---: | ---: | --- |
| 晶心科 CTBC | 15 | 1,166 全留 | 4 | 14 列 × 7 欄；2022–2027F |
| 華南裕民 | 8 | 851 全留 | 12 | 8 列 × 9 欄；3 層表頭及 5 個年度 |

晶心科 2025F–2027F 淨利 -237／306／778，裕民稅後 EPS 5.21／3.24／5.54／4.19／5.07 保留。裕民評等表維持「報告日期／評等／目標價」三欄；買進文字未混進日期或數值。5 個無數值單欄文字候選保留證據並回到本文順序，不用表格遮罩吞掉正文。

原 native_geometry、layout 及 financial_tables 與擷取證據逐項相同；HTML 仍含全部原生字項、原頁及 FINANCIAL DATA。11 份擷取來源 SHA-256 不變。依檔名由上而下、每份依實體頁排列。第二次修復快取命中 2 份，未再次執行基礎擷取。

## 能力界線

文件狀態保持 REVIEW，合計吻合不能證明完整還原。沒有推測補值，原始數值與修復結果分開留存。結構化表格仍須對照原頁；保留的候選、圖區及碎片數不代表已完整辨識的財務表或圖表數。

本機 Tesseract 有 eng／osd，缺 chi_tra。正式繁中圖區 OCR 明確 UNAVAILABLE；英文裁切路徑另經實跑驗證。沿用 GLE 的行級 OCR 框，不冒稱字級辨識；座標角色及數列配對屬候選，未知數列不造值。

HTML 完成資料、順序、字項及功能碼檢核；瀏覽器政策阻止本機 file URL，未宣稱完成瀏覽器畫面驗收。沒有 GitHub 推送、合併、Windows 工作站部署或正式庫寫入。

## 使用

```text
via-vcgc layout --manifest
via-vcgc layout --dir <PDF檔案或目錄> --out <核對輸出目錄> --open
via-vcgc layout --dir <相同PDF> --out <輸出目錄> --evidence <已驗證LAYOUT_REVIEW.json>
via-vcgc layout --selftest
```

重用證據必須保留原 documents 斷點目錄，且輸入檔案集合、SHA、原引擎簽章及原始資料一致；少一份輸入即拒用，避免靜默漏檔。新修復快取以來源、SSOT、模組雜湊及 OCR 環境識別，缺損影像或損壞 JSON 不視為成功快取。

輸出：`LAYOUT_REVIEW.html`、`LAYOUT_REVIEW.json`、`LAYOUT_REPAIRED.json`、`LAYOUT_REPAIRED.csv`、`LAYOUT_REPAIRED.md`、`ENGINE_CATALOG.json`。Markdown 用內嵌 HTML 表格保留 rowspan／colspan；JSON 留原值、來源與修復沿革。
