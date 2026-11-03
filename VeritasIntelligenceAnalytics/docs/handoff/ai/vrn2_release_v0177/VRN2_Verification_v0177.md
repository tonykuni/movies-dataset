# VRN-2 v0177 驗證紀錄(2026-11-04 · 頁面分割檔不進範圍 · 千分位兩位小數 · Workbench v0110 · 加速器 100% · 套件 v0177 · RoundAll v0133 · Handle-All v0125)

## 1. 桌機回報 → 根因 → 做法

| 回報 | 根因 / 做法 |
|---|---|
| 整輪 ⑦ 逾時 7200 秒 · ⑧ 沒寫完成判定 · 收尾 VRN-2 2 項 | 來源夾 305 份 = 60 份報告 + 200 份 `page_NNNN[_雜湊].pdf`(11/02 從別的檔切出來的單頁 · 掃描影像 · 頁號 1–63)· 舊範圍規則只排除明確非個股檔名 → 260 份當個股逐份 OCR(擷取 6,798 秒)· **管理器 v0260** 把分割頁加進非個股檔名規則(原檔不動)· **Handle-All v0125** 上一輪 ⑦ 沒跑完 → 自動整輪 · ⑧ 只因資料面紅照舊 repair |
| 數字小數點兩位要有千分位號 | BookSource v0102:主題與摘要 1,234.50 / 23.45%(數值欄不動)· Workbench v0110 顯示兩位小數加千分位(資料不改)|
| 第二圖超出格子 · 左右面板字級 / 按鍵高度 · 矩陣化 · 檢視副本 · 字體偏小 | Workbench v0110(分頁列不動)· 收尾頁字級小一號 |
| ps / py 加速器 100% · 向外擷取加最新網路工具 | 見 §3 |

## 2. 測試

| 項目 | 結果 |
|---|---|
| 模組自測 | 管理器 v0260(含 v0259 鏈):untouched) · 6 checks · failed 0 · BookSource v0102(含 v0101 / v0100):okSource v0102 --selftest · 不過 0 · OutputStore v0105(含 v0104 → v0100):ftest · 引擎 duckdb+pyarrow · 不過 0 · Workbench v0110(含 v0109 鏈): VRN2_Workbench v0110 自測 全過(7 項) · VerbatimVerifier v0106(含 v0105 / v0104):er v0106 --selftest · 3 項 · 不過 0 |
| 啟動器 v0177 自測 | 全過 · [PASS] v0177: manager v0260 (page_NNNN[_hash].pdf out of the stock scope) · BookSource v0102 (1,234.50 / 23.45 |
| RoundAll v0133 自測 | [PASS] VRN2_RoundAll v0133 --selftest · 105 項 · 不過 0 |
| PowerShell | pwsh 剖析錯 [0, 0, 0, 0, 0] · Handle-All 一行 = 可讀版 True · 開機行 = 可讀版 True · 模式規則實跑:bad=full good=repair datared=repair |
| 瀏覽器(Chromium · 1,366 / 1,100 寬)| {"1100": {"buttons_px": [28], "font_left_right": [["10.45px", "9.95px"], ["10.45px"]], "overflow": 0, "card_fit": ["20261103_130820=19px", "3 冊=19px", "VRN2_Closeout_v0176.json=17.5px", "3 份=19px"], "view_copy_rows": 5232, "thousands": ["4,200.00", "2,037.00", "1,249.50"], "header": ["VERITAS INTELLIGENCE ANALYTICS · VRN-2 WORKBENCH", "VeritasReportNova", "Transform investment reports into structured database intelli |
| e2e(最短一行 · 沙盒 · 樣本夾多放 3 份 page_NNNN 分割頁)| auto1 rc 0 · confirm list rc 0 · auto2 rc 0 · tamper rc 0 · 範圍:股報告)· 來源 <sbx>/samples · 檔 25(PDF 25 · 非 PDF 0 不在範圍)· 個股範圍 17 · 排除非個股 8(上輪判定 0 · 檔名 8)· 同步 新增 / 更新 3 · 移除 0 · 耗時 3 秒(平行) · [計] v0260 頁面分割檔(page_NNNN[_雜湊].pdf · 從別的檔切出來的單頁 · 不是整份報告)3 份不進個股範圍(原檔不動 · 輸入矩陣算「頁面影像」) · 範圍夾分割頁 0 份 |
| e2e repair(模擬桌機 v0176:BookSource 收據 v0101)| 歷史對齊 FinancialAligned,Deleted 的 Parquet 沒寫(ImportError(這支 Python 的 pyarrow 載不起來))→ HistoryAlign v0103 依欄位型別重寫(JSON / CSV 照舊) · TARGET_PRICE(ADJ) 同步還原 + 共識照 TWSE · 主題與摘要新寫法 11 / 11 列 · auto2 追加 {"BasicInfo": 0, "FinancialData": 0, "Summary": 0, "Combined": 0, "Rejected": 0, "FinancialAligned": 0, "Deleted": 0} · 整理 {"Summary": 0, "Combined": 0 · 頁面分割檔列:[GREEN] ⑥ 頁面分割檔 · 範圍夾 17 份 · 沒有頁面分割檔(page_NNNN) |
| 收尾負責方 | VRN-2 項與 v0176 基準相同(沙盒限定 · 沒有真 OCR 環境)|

## 3. 加速器 / 網路工具稽核(VRN-2 現役模組鏈)

| 範圍 | 結果 |
|---|---|
| VRN-2 現役模組鏈(啟動器 v0177 常數 → 前版鏈)| 44 支 · 現役尾版加速器標記缺 **0**(v0176 缺 1:VerbatimVerifier v0105 → v0106 補上 · v0105 留作 v0106 的凍結前版 · 由帶標記的 v0106 載入)|
| VRN-2 自己向外擷取 | 共識引擎 v0122 經 VIA 網路工具(SUP_MDL740_NetUnified · 法遵雙閘)+ 加速器 · 現役鏈裡沒有不經網路工具的直接連線 |
| 倉內 functional modules/VRN 的 VRN2_* 尾版 | 5 支全有加速器標記(VCGC 交接檢查點名的 VRN2_UIAction_v0100 是被後版引用的凍結前版 · 不改)|
| ⑥e 價格(借 VDF 的 VDF_TW_AllInOne_v039)| **VDF 的檔 · 只記錄不改**:直接 import urllib.request / yfinance · 只有 DENY 處理的網路橋註記 · VCGC 交接檢查標 ACCEL_BRIDGE_MISSING / MODULE_UNREGISTERED → 交 VDF 那一線改(四系統互不干涉)|

## 4. 桌機下一步

1. 貼 `vrn2_release_v0177/VRN2_HandleAll_v0125.md` 的最短一行 —— 這次會**自動改整輪**(上一輪 ⑦ 逾時);同意閘照舊由你決定(要最新共識才開)。
2. 範圍應回到 60 份上下(52 份個股 + 少數非個股檔名不明的報告)· ⑦ 預期遠低於 7200 秒。
3. MQ-1560:`python "%USERPROFILE%\\Downloads\\VRN2_RoundAll_v0133.py" --confirm H-fd2ea35f --note "你核對的結論"`(只有你打才算 · `--note` 後面不要留「…」)。
