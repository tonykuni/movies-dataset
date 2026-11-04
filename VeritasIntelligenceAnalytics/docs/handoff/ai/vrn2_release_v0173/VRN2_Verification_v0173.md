# VRN-2 v0173 驗證紀錄(2026-11-03 · 桌機 v0128 實錄補記 · RoundAll v0129:⑬b 只在輸入變了才重跑 · Handle-All v0121 · 套件 v0172 不動)

## 1. 桌機 2026-11-03 05:54(Handle-All v0120 · RoundAll v0128 · repair 55 秒)—— VRN P0 三項上桌

| 項目 | 桌機結果 |
|---|---|
| 套件 | v0172 從 GitHub 取下 · SHA-256 `bd952da149bd` · 11 檔逐檔相符 |
| F1 Parquet | ⑬b「補放 VRN2_HistoryAlign_v0103.py · **Parquet 寫成**」(前版 ArrowInvalid 那本)|
| F2 小數欄 | 計畫「Combined 還沒有 UPSIDE_ADJ → ConsensusJoin v0107 重組」→ Combined 52 列 · FactSet 中位數 49 · Yahoo 48 · 欄序正確(含 UPSIDE_ADJ)· 增量庫:內容有變的 42 列追加(帶 UPSIDE_ADJ)、舊列保留(OutputStore v0101 規則 · 追加 = 補缺同一批 42 列,不是重複)|
| F3 合併檢視 | Workbench **v0107(前版 v0104)** 渲染成功 |
| 收尾 | **REVIEW · VRN-2 0 · VCGC 0** · 人工 1(MQ-1560 四點 `--confirm H-fd2ea35f`)· 資料源 3 |
| 07:59 再跑 | Combined 不再排 · 增量庫追加 0(冪等)· 但 ⑬b + 增量庫 + Workbench 又做了一次 → 本輪修 |

## 2. 本輪修:⑬b 不再每次白做

根因:收據的歷史對齊燈 GRAY「無歷史 47」是**真的沒有歷史財報**(不用 MOPS 之後),v0128 以前的觸發條件只看燈是不是 GRAY → 每次 repair 都成立,
計畫還寫成「市場資料比歷史對齊新 / 歷史對齊沒跑」(兩者都不是)。**RoundAll v0129** 只看輸入:這輪會重抓 / 重填市場資料 · 還沒有歷史對齊收據 ·
市場資料比它新 · 年度數據比它新 · Parquet 沒寫(v0128)—— 計畫照實寫是哪一個;都沒有 → 不重跑(收尾頁照舊列灰 · 不是待修)。

## 3. 測試

| 項目 | 結果 |
|---|---|
| RoundAll v0129 自測 | [PASS] VRN2_RoundAll v0129 --selftest · 99 項 · 不過 0 |
| PowerShell 剖析 | pwsh 剖析錯 [0, 0, 0, 0, 0] · Handle-All 一行 = 可讀版 True · 開機行 = 可讀版 True |
| e2e(最短一行 · 沙盒 · 模擬桌機穩態)| steady rc 0 · fin rc 0 · steady2 rc 0 · tamper rc 0 |
| 穩態 | 計畫:`Combined 比市場 / 共識舊(或不在)→ 重組 · ⑬ 增量庫補寫(本輪有修正) · Workbench 重渲染(最新收據)`(沒有 ⑬b)|
| 年度數據變新 | 計畫:`年度數據比歷史對齊新 → 重跑 ⑬b · TARGET_PRICE(ADJ) 同步還原 + 共識照 TWSE / TPEX 格式合併(ConsensusJoin v0105)→ 重組 Combined · ⑬ 增量庫補寫(本輪有修正) · Workbench 重渲染(最新收據)` |
| 再穩態 | 計畫:`TARGET_PRICE(ADJ) 同步還原 + 共識照 TWSE / TPEX 格式合併(ConsensusJoin v0105)→ 重組 Combined · ⑬ 增量庫補寫(本輪有修正) · Workbench 重渲染(最新收據)`(沒有 ⑬b)|

沙盒的 Combined 重組是沙盒限定(擷取環境缺 requests → 沒有 TARGET_PRICE(ADJ) 同步還原證據);桌機 07:59 沒有這個觸發。

## 4. 桌機下一步

1. 貼 `vrn2_release_v0173/VRN2_HandleAll_v0121.md` 的最短一行 → 應是「⑤ 自動修 · 沒有要修的」· 收尾 REVIEW(VRN-2 0 · VCGC 0)· 幾秒到一分鐘。
2. MQ-1560 看過原圖:`python "%USERPROFILE%\\Downloads\\VRN2_RoundAll_v0129.py" --confirm H-fd2ea35f --note "…"`(只有操作員打才算)→ DATA_GAP = VRN 側終點。
3. Graphify:用 `via_graphify_v0101/VIA_Graphify_v0101.md` 的那一行(桌機這次跑的是 v0100 那行 → 4 系統全灰)。
