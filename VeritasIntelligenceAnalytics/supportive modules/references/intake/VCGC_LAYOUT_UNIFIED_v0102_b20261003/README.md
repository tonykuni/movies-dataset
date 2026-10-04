# VCGC 單一 Layout 引擎 v0102

引擎頂部 ENGINE_MANIFEST → 46 項功能 SSOT → System Manager／使用者同一清單及中央註冊碼。
舊成功擷取與 GLE 原件保持鎖定；新增模組化擷取後修復與完整登錄。

本機提交：bef9204d1dd6c2322e74f4a822bdadb398fb6e65

## 補丁選擇

- 原 main 基底 bfdb7844549530b5895b2a566060b3bdab9a6149：使用 VCGC_LAYOUT_UNIFIED_from_main.patch，含前版 v0101 與本版。
- 已套用前版提交 3b7b6ac3ed0544563434dd7fbb9606e9befacf61：使用 VCGC_LAYOUT_UNIFIED_from_v0101.patch。
- 兩份補丁擇一。若版本或 SSOT 已有其他變更，應先合併核對，不強制覆寫中央編號。

在相符的乾淨工作樹，先執行 git apply --check <所選補丁>，成功後再執行 git apply <所選補丁>。
本包沒有自動安裝、GitHub 推送、合併或部署。

## 開啟與核對

via-vcgc layout --manifest
via-vcgc layout --dir <PDF路徑> --out <輸出目錄> --open
via-vcgc layout --selftest

ENGINE_CATALOG.json 提供 46 項功能、中央號碼、實作與測試綁定；完整說明見 VRN_LAYOUT_UNIFIED_v0102.md。
驗證：37 項回歸、兩份報告共 23 頁／2,017 原生文字全留、11 個鎖定來源不變、兩份修復快取命中。
正式入口已通過原有路由步驟而產生 REVIEW 報告；環境根 NODATA 不表示全面環境通過。

繁中 OCR 缺 chi_tra 時標為 UNAVAILABLE，未下載模型。沿用 GLE 行級 OCR；數值未推測補算。
實檔保持 REVIEW，沒有宣稱百分之百還原或完成瀏覽器畫面驗收。正式財務資料庫不寫入。
本包不含原始 PDF；HTML 核對報告另外提供。
