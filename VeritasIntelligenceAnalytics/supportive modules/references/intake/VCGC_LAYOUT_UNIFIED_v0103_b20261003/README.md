# VCGC Layout v0103 年度財報分表修正

本機提交：e7a20b9c0140e872811b2533c5295f9645c2fc84

修正年度財報左右黏表、各欄上下黏表與科目數字錯列。HTML、JSON、CSV、Markdown 共用四張獨立表。
晶心科第 5 頁：資產負債表 17×6、損益表 13×6、現金流量表 18×6、比率分析 12×6，含表頭共 360 格逐格核對。
41 項回歸通過。46 項能力仍在同一 SSOT，新增 3 函式正典配號、舊碼保持、退役 0。
既有擷取、原頁與財務矩陣不改；不下載 OCR 模型；正式庫不寫入。文件維持 REVIEW。

## 選擇一份補丁

- 從原 main bfdb7844549530b5895b2a566060b3bdab9a6149 安裝：VCGC_LAYOUT_v0103_from_main.patch（包含前兩版整合）。
- 已有 v0102 提交 bef9204d1dd6c2322e74f4a822bdadb398fb6e65：VCGC_LAYOUT_v0103_from_v0102.patch。

兩份擇一。在相符工作樹先 git apply --check <所選補丁>，成功後 git apply <所選補丁>。
不同基底或中央編號已有變動時先合併核對，不強制覆寫。

## 使用

via-vcgc layout --manifest
via-vcgc layout --dir <PDF路徑> --out <輸出目錄> --open
via-vcgc layout --selftest

完整說明：VRN_LAYOUT_FINANCIAL_GRID_v0103.md。
驗證：VALIDATION.json；功能及編號：ENGINE_CATALOG.json。
本包沒有原始 PDF。修正版 HTML 報告另行提供。
僅本機提交，未推送、合併或部署；繁中圖區 OCR 缺 chi_tra，與本頁原生座標修復無關。
