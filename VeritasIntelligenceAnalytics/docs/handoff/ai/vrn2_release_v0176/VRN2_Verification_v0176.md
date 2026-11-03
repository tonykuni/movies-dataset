# VRN-2 v0176 驗證紀錄(2026-11-03 · 四點去開頭符號 · 主題與摘要 Name(YFinance Ticker, 評等) - 原文標題 · 評價點用調整後目標價 ÷ 調整後收盤 · 套件 v0176 · RoundAll v0132 · Handle-All v0124)

## 1. 操作員要求 → 做法

| 要求 | 做法 |
|---|---|
| 四點摘要前面出現任何標點符號(如 ➢)則刪除 | ⑬a `VRN2_BookSource_v0101`:Summary 冊 TITLE / POINT_1 ~ POINT_4 開頭的項目符號 · 標點 · 編號 · 空白刪掉 · 內文一字不改(原文核對照樣找得到)· 1.5 倍 / 2026 年 / 25Q3 / 「引言」 這類開頭不動 |
| 第一點通常為評價 · 用每日更新後的 ADJ 目標價 · ADJ CLOSE 算上漲空間 | Combined 主題與摘要:評價點排第一 · 上漲空間 = TARGET_PRICE(ADJ) ÷ ADJ_CLOSE − 1(與 Combined 的 UPSIDE_PCT(ADJ) 同一公式)· 句尾接算法 · 沒有評價句 → 補一句(仍是四點)· 調整後價缺 → 數字不動 |
| 標題格式 Name(YFinance Ticker, 評等) - 原文標題 | 主題與摘要開頭 = Name(YFinance Ticker, 評等) - 原文標題(Name:Combined → 基本資料 → 英文名 → 代號)|
| 增量庫不重複 | `VRN2_OutputStore_v0104`:Summary 去符號後再算雜湊 · Combined 主題與摘要不算 · 舊列就地整理(先備份 · restore-fill)· 調整後收盤變了照樣追加(每日歷史)|

## 2. 測試

| 項目 | 結果 |
|---|---|
| 模組自測 | BookSource v0101(含 v0100 自測):2_BookSource v0101 --selftest · 不過 0 · OutputStore v0104(含 v0103 → v0100 自測):-selftest · 引擎 duckdb+pyarrow · 不過 0 |
| 啟動器 v0176 自測 | 全過 · [PASS] v0176: ⑬a BookSource v0101 (Summary 四點 / 標題去開頭符號 · Combined 主題與摘要 = 示例公司(9999.TW, 買進) - 標題甲 · 評價點第一 · 上漲空間 118 ÷  |
| RoundAll v0132 自測 | [PASS] VRN2_RoundAll v0132 --selftest · 103 項 · 不過 0 |
| PowerShell 剖析 | pwsh 剖析錯 [0, 0, 0, 0, 0] · Handle-All 一行 = 可讀版 True · 開機行 = 可讀版 True |
| 桌機形狀(操作員 10/28 上傳的 Summary 冊 CSV · 只在暫存夾 · 11/03 桌機貼回另見 ➢ 7 · • 6 · ⚫ 2 · 標題 - 3 · 同一套規則)| 52 份 · 開頭符號 2 → 0 · 去掉後都是原文的尾段 · 其他欄逐一相同 · 非空點數 201 → 201(一點都沒少)· 再跑不變 |
| 桌機形狀(02 頁基本資料 52 列 + 上傳 Summary 組 Combined · 調整後價用合成數字)| 主題與摘要 52 列全部重組 · 有目標價 43 列 → 改算上漲空間 43 列 · YFinance 代號進標題 27(=有代號的全部)· 評等進標題 46(=有評等的全部)· 標題 + 至多四點 52 / 52 · 再跑主題與摘要 0 列 |
| e2e(最短一行 · 沙盒)| auto1 rc 0 · confirm list rc 0 · auto2 rc 0 · tamper rc 0 · auto1 整輪(啟動器 v0176)→ 模擬桌機 v0175 狀態(四點帶 ➢ / • · 主題與摘要舊格式 · 收據沒有 summary_cleanup / summary_tidy)→ auto2 repair:歷史對齊 FinancialAligned,Deleted 的 Parquet 沒寫(ImportError(這支 Python 的 pyarrow 載不起來))→ HistoryAlign v0103 依欄位型別重寫(JSON / CSV 照舊) · TARGET_PRICE(ADJ) 同步還原 + 共識照 TWSE / TPEX 格式合併(ConsensusJoin v0105)→ 重組 Combined · ⑬a 輸出冊 SOUR → 竄改開機檔不執行 |
| e2e 結果 | Summary 17 份 · 開頭符號剩 0 格 · Combined 17 列 · 新格式 17 列 · 有調整後價 11 列 · 改算上漲空間 11 列 · 除錯列:[GREEN] ⑥ 四點 / 主題與摘要 · Summary 17 份 · 開頭還有符號 0 格 · Combined 17 列 · 主題與摘要不是 Name(YFinance Ticker, 評等) - 原文標題 開頭 0 列 · 評價點用調整後目標價 ÷ 調整後收盤 11 列 |
| 增量庫 | auto2 追加 {"BasicInfo": 0, "FinancialData": 0, "Summary": 0, "Combined": 0, "Rejected": 0, "FinancialAligned": 0, "Deleted": 0} · 整理 {"Summary": 0, "Combined": 0} · 累計 {"BasicInfo": 17, "FinancialData": 5232, "Summary": 17, "Rejected": 834,  |
| 收尾負責方 | VRN-2 項與 v0175 基準相同(沙盒限定 · 沒有真 OCR 環境)|

## 3. 桌機下一步

1. 貼 `vrn2_release_v0176/VRN2_HandleAll_v0124.md` 的最短一行(收據 ≥ v0170 → repair · ⑬a v0101 → ⑬ v0104 整理 → Workbench)。
2. MQ-1560 看過原圖:`python "%USERPROFILE%\\Downloads\\VRN2_RoundAll_v0132.py" --confirm H-fd2ea35f --note "…"`(只有操作員打才算)。
