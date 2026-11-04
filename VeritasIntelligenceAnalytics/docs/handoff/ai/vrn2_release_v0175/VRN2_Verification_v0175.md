# VRN-2 v0175 驗證紀錄(2026-11-03 · ⑬a 輸出冊實體 SOURCE / BROKER_EN · 增量庫 OutputStore v0103 · Workbench v0109 · 套件 v0175 · RoundAll v0131 · Handle-All v0123)

## 1. 操作員要求 → 做法

| 要求 | 做法 |
|---|---|
| BROKER 一律英文縮寫 | 輸出冊每列多 `BROKER_EN`(候選對照表 · 等 VCGC 核發 · 對不到留空列收據)· 畫面券商欄顯示縮寫 · `BROKER` 原文不改 |
| 輸出冊和增量庫也實體加 Source 欄 | ⑬a `VRN2_BookSource_v0100`(⑬b 之後 · ⑬ 之前):七本報告冊最後兩欄 `BROKER_EN` · `SOURCE`;JSON 保留縮排 · CSV 保留 BOM / CRLF · Parquet 保留欄型別 · 其他值逐位元組不變 · MarketConsensus 自己的 SOURCE 不動 · 增量庫 `VRN2_OutputStore_v0103`:列雜湊不算兩欄(不重複追加)· 舊列就地補欄(先備份 · restore-fill)|
| 細節 / Detail 字型字級為主 · 整字小一點 | Consolas + 微軟正黑體 10.45px(內文)· 11(區段標題)· 9(表頭 / 標籤)· 8(標記)· 19(品牌 / 大標 / 統計)· 模板 15 色 · CSS SHA-256 `739a2a9d9319` |
| 資料驗證狀況 → 系統摘要 · 矩陣化燈號化 | 00 頁改名「系統摘要」· 驗證矩陣(燈號 · 項目 · 細節)+ 共識矩陣(FactSet 目標價中位數 · Yahoo 目標價中位數 · FactSet 分析師人數 · Yahoo 分析師人數 · 兩源檢核)|
| 尚未跨越的驗收條件特別亂 | 04 頁「待驗收項目」矩陣(燈號 · 類別 · 項目 · 細節 · 次數 · 同項合併 · 紅先)|
| 括號說明 / 備註 / 全形 / 表頭 | 表頭英文一行 + 中文一行 · 標題括號說明移到卡片底下的註 · 中文旁括號冒號逗號改全形(檔名 / 路徑 / 資料值不動)|
| 資料不可超過卡片及格子 | 自動換行 · 瀏覽器實測溢出格 0 |
| 左面板步驟 | 1 選擇報告來源 · 2 確認輸入 · 3 啟動處理 · 4 輸出位置 · 5 開啟資料夾 · 6 其他系統(完成的步驟綠框)· 說明移到底下 |
| Word / 影像 · STOCK / NON-STOCK / NEWS | 01 頁輸入分類矩陣(檔名初判 · 候選)· 本版主體只擷取 PDF;Word 需轉 PDF、影像需 OCR |

## 2. 測試

| 項目 | 結果 |
|---|---|
| 模組自測 | BookSource v0100: VRN2_BookSource v0100 --selftest · 不過 0 · OutputStore v0103:03 --selftest · 引擎 duckdb+pyarrow · 不過 0 · Workbench v0109:[GREEN] VRN2_Workbench v0109 自測 全過(12 項) · Workbench v0108 回歸:[GREEN] VRN2_Workbench v0108 自測 全過(12 項) · OutputStore v0102 回歸:02 --selftest · 引擎 duckdb+pyarrow · 不過 0 |
| 啟動器 v0175 自測 | 全過 · [PASS] v0175: ⑬a BookSource v0100 (no books → GRAY · BROKER_EN KGI + SOURCE 報告預估 as the last two columns · BRO |
| RoundAll v0131 自測 | [PASS] VRN2_RoundAll v0131 --selftest · 101 項 · 不過 0 |
| PowerShell 剖析 | pwsh 剖析錯 [0, 0, 0, 0, 0] · Handle-All 一行 = 可讀版 True · 開機行 = 可讀版 True |
| 桌機形狀資料(操作員上傳的 FinancialData 匯出 · 只在沙盒)| 11,905 列 · 最後兩欄 BROKER_EN / SOURCE · 其他值逐一相同 · SOURCE 與 v0108 匯出一致 11905 / 11905 · 13 家券商全有縮寫 |
| 瀏覽器(Chromium · 另一線 v0104 鏈 + v0109)| JS 錯 0 · 溢出格 0 · 內文 Consolas, "Microsoft JhengHei", "Segoe U 10.45px · 表頭雙行 · SOURCE 只一欄 · BROKER_EN 不另列 · 整冊 CSV SOURCE 1 次 |
| e2e(最短一行 · 沙盒)| auto1 rc 0 · confirm list rc 0 · auto2 rc 0 · tamper rc 0 · auto1 整輪(啟動器 v0175:⑬a → ⑬ v0103 → Workbench v0109)→ 模擬桌機 v0174 狀態(冊沒有兩欄 · 頁是 v0108)→ auto2 repair:年度數據比歷史對齊新 → 重跑 ⑬b · FinancialAligned,Deleted 的 Parquet 沒寫 → HistoryAlign v0103 依欄位型別重寫 · TARGET_PRICE(ADJ) 同步還原 + 共識照 TWSE / TPEX 格式合併(ConsensusJoin v0105)→ 重組 Combined · ⑬a 輸出冊 SOURCE / BROKER_EN 欄: → 竄改開機檔不執行 |
| 增量庫 | auto2 追加 {"BasicInfo": 0, "FinancialData": 0, "Summary": 0, "Combined": 0, "Rejected": 0, "FinancialAligned": 0, "Deleted": 0} · 補欄 {} · 累計 {"BasicInfo": 17, "FinancialData": 5232, "Summary": 17, "Rejected": 834, "Combin |
| 收尾負責方 | VRN-2 項與 v0174 基準相同(沙盒限定 · 沒有真 OCR 環境)|

## 3. 桌機下一步

1. 貼 `vrn2_release_v0175/VRN2_HandleAll_v0123.md` 的最短一行(收據 ≥ v0170 → repair · ⑬a 寫兩欄 → ⑬ 舊列補欄 → Workbench v0109)。
2. MQ-1560 看過原圖:`python "%USERPROFILE%\\Downloads\\VRN2_RoundAll_v0131.py" --confirm H-fd2ea35f --note "…"`(只有操作員打才算)。
3. 券商縮寫表要成為正式同義字 → 交 VCGC 核。Word / 影像要擷取 → 下一步(Word 轉 PDF · 影像 OCR · 環境交 VCGC)。
