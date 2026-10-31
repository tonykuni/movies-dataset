# VRN-2 v0164 驗證紀錄(2026-11-01 · 增量庫清 MOPS 列 · TARGET_PRICE(ADJ) 同步還原 · TWSE / TPEX 格式合併 · 套件 v0164 · RoundAll v0120 · Handle-All v0112)

## 1. 起因

操作員 2026-11-01:「**Yahoo 和共識照用 · 增量庫 MOPS 資料清掉 · Target Price(Adj) 也應該同步還原才有可比較性 · 兩個單位所算的目標價中位數並存方便比較 ·
只要最後把他跟 TWSE / TPEX 輸出個格式依樣在合併即可**」+ 桌機 2026-11-01 03:08 收尾(RoundAll v0119 repair):OPEN · VRN-2 1 =「⑥e 擷取 YELLOW · 跑 10 次 · 失敗 0」·
TARGET_PRICE(ADJ) MISSING 5(3706 / 6669「報告日前沒有日資料 · 需 --start 回補」)· 增量庫 FinancialAligned 16588 / Deleted 38(含 16:11 MOPS 那批)。

## 2. 全景定位(錨點)與分類

| 錨點 | 定位 | 可並行 / 須順序 |
|---|---|---|
| 增量庫 MOPS 列 | `<輸出夾>/VRN2/vrn2_store.duckdb` 的 `book_financialaligned` / `book_deleted`(每列帶 run_id · file_sha · row_sha)+ `parquet/<冊>/run=<id>.parquet` · 認列靠 HistoryAlign 寫的 VALUE_SOURCE / RECON_RATIO / HISTORY_VALUE(不靠時間)| 並行(只動 VRN-2 自己的輸出夾)|
| ⑥e「失敗 0」卻 YELLOW | `VRN2_MarketFetch_v0112.fetch`:`lamp = YELLOW if all(rc in (0, 2))` · 「失敗」只數 rc 不在 (0, 2) · VDF 引擎 rc 2 = `status.json` PARTIAL(issues 或日線品質 REVIEW = Yahoo 收盤 ≠ TWSE 收盤)| 並行(收尾頁判法 · MarketFetch / VDF 不改)|
| 3706 / 6669 MISSING | `MarketFetch.fill`:`before = adj[adj.date < 報告日]`,`adj` 只收 adj_close 非空的列 → VDF `def_adjust_prices` 對 CLOSE_MISMATCH 的日子不給 adj_close → 「沒有日資料」其實可能是「Yahoo 收盤對不上」| 須順序:⑥e 落盤 → ⑥f 同步還原 → Combined → ⑬ |
| 兩家中位數 | `ConsensusJoin_v0100.HEAD`:FACTSET_TARGET_PRICE_MEDIAN · YFINANCE_TARGET_PRICE_MEDIAN 早就並存 | 不用改(保留欄序)|
| TWSE / TPEX 格式 | VDF `IDENTITY_PREFIX` = date · ticker · yfinance_ticker · bloomberg_ticker · name · `DATASET_KEYS` [date, ticker] · `parquet/<ds>/ticker=/year=/data.parquet` + `<ds>.parquet` · CSV 大寫表頭 | 須順序:⑥f 之後 |

順序:runtime v0157(ConsensusJoin v0105 · OutputStore v0102 · SSOTSync v0102 · 提案冊 v0101)→ 啟動器 v0164 → 套件 v0164 → RoundAll v0120(釘套件雜湊)→ Handle-All v0112(釘 RoundAll)→ 開機檔 → 最短一行 / cmd 一行。
九頭龍檢查:VDF 引擎 / 共用 MarketFetch / VCGC 的檔一字不改;MarketFetch 的 `VRN2_Market_latest.json` 不改(v0105 只給 join 一份補過的複本);增量庫清之前整檔備份 · 可 `restore-purge`;
前版模組(ConsensusJoin v0104 ~ v0100 · OutputStore v0101 / v0100 · SSOTSync v0101 / v0100)逐位元組不動。

## 3. 修法

| 檔 | 內容 |
|---|---|
| ConsensusJoin v0105 | TARGET_PRICE(ADJ) 同步還原(VDF 已還原 → adj_close ÷ close;CLOSE_MISMATCH 且 Yahoo ÷ TWSE 比值報告日前 10 天內一致(±0.5%)、離 1 超過 1%、報告日後回到 MATCH → Yahoo 還原收盤 ÷ TWSE 收盤;其他 MISSING 寫實原因)· 三格同一個因子 · 證據 `market/VRN2_TPAdjSync_latest.json`(含 VDF status.json · 每檔 MISMATCH 列數)· 共識照 VDF 格式寫 `consensus/dataset`(tw_consensus · tw_consensus_estimate)→ 跟 TWSE / TPEX 日線合併(14 天內最後一個交易日)= tw_market_consensus + `output/VRN2_MarketConsensus_latest` |
| OutputStore v0102 | 認列:Deleted 全部 · FinancialAligned 有歷史記號的 (run_id, file_sha) 整組 · `purge-mops`(預設只算 · `--apply` 先複製 DuckDB 檔 + SHA-256 → removed/<冊>.parquet → 刪 → 受影響 run 分檔搬走再重寫剩的 → PURGE_MANIFEST.json)· `restore-purge` · sync = 先清再收(擋 MOPS 列 · mops_skipped)· 新冊 MarketConsensus |
| SSOTSync v0102 + 提案冊 v0101 | 這輪 8 條新規則(VRN2-PROP-0010 ~ 0017 · ssot_id 空白)· ⑤b 照 v0101 送核號請求 · v0101 的自測隔離跑 |
| 啟動器 v0164(`b28b8c3e0886`)| runtime v0157 · ⑥f 載 v0105 · ⑬ 載 v0102(清 MOPS 列寫在 ⑬ 那行最前面)|
| RoundAll v0120(`860cdd5b5fd4`)| ⑤ combined(沒同步還原過)· store(增量庫沒確認乾淨)· market_fill(市場資料還帶 MOPS 財報 → 只重新填值)· 收尾頁 ⑥e 失敗 0 → 資料源 + 錨點 · 「不用 MOPS」字樣不當 DENY · 自測 78 |
| 套件 v0164(`84834e330fac`)· Handle-All v0112(一行 `cb172a714083` · 開機檔 `d1e0fb0cd8fa`)| 最短一行 443 字元 · cmd 一行 1240 字元 |

## 4. 測試

```text
[PASS] 75 ⑥e「擷取 YELLOW · 失敗 0」= VDF rc 2 PARTIAL → 資料源(錨點:status PARTIAL · 3706 MISMATCH 7 列 · 填值缺 = 非台股 · 同步還原 3)· 失敗 2 → VRN-2 · 逾時照舊 VRN-2 · 「不用 MOPS」說明字不算 DENY(真的 DENY 照舊 VCGC)
[PASS] 76 ⑤ 計畫:增量庫沒確認乾淨 → store「清掉 MOPS 算的列(先備份 · 可還原)」· 沒同步還原過 → combined(ConsensusJoin v0105)· 清過且綠 + 同步還原比市場新 → 都不排 · 市場資料還帶 MOPS 財報 → market_fill(只重新填值)→ ⑬b → Combined
[PASS] 77 Combined TARGET_PRICE(ADJ) 缺:同步還原寫的 MISSING(…) 原因 → 資料源 · 日期 / 比值不同不拆類(2 類 · 3 份)
[PASS] 78 套件 v0164(啟動器 v0164 · runtime v0157)· ③ 自測跑 OutputStore v0102 / ConsensusJoin v0105 · 貼回包收清 MOPS 列收據 / 同步還原證據 / VDF status / 合併冊 · ⑤ 補放 v0102 鏈
[PASS] VRN2_RoundAll v0120 --selftest · 78 項 · 不過 0
venv(py3.12 · pandas / pyarrow / duckdb):[PASS] VRN2_RoundAll v0120 --selftest · 80 項 · 不過 0
啟動器 v0164 自測(從套件 zip 解開 · venv):
[PASS] v0164: step 6f loads ConsensusJoin v0105 (TARGET_PRICE(ADJ) synchronous adjustment · consensus in the TWSE / TPEX format · merged) · step 13 loads OutputStore v0102 (MOPS rows purged with a bac
模組自測(系統 py3.13 duckdb · venv py3.12 duckdb + pyarrow · venv pyarrow 只有):
cj105: [PASS] VRN2_ConsensusJoin v0100 --selftest · 7 項 · 不過 0 | [PASS] VRN2_ConsensusJoin v0101 --selftest · 11 項 · 不過 0 | [PASS] VRN2_ConsensusJoin v0102 --selftest · 6 項 · 不過 0 | [PASS] VRN2_ConsensusJoin v0103 --selftest · 13 項 · 不過 0 | [PASS] VRN2_ConsensusJoin v0104 --selftest · 不過 0 | [PASS] VRN2_ConsensusJoin v0105 --selftest · 不過 0 | [PASS] VRN2_ConsensusJoin v0100 --selftest · 7 項 · 不過 0 | [PASS] VRN2_ConsensusJoin v0101 --selftest · 11 項 · 不過 0 | [PASS] VRN2_ConsensusJoin v0102 --selftest · 6 項 · 不過 0 | [PASS] VRN2_ConsensusJoin v0103 --selftest · 13 項 · 不過 0 | [PASS] VRN2_ConsensusJoin v0104 --selftest · 不過 0 | [PASS] VRN2_ConsensusJoin v0105 --selftest · 不過 0 | [PASS] VRN2_ConsensusJoin v0100 --selftest · 7 項 · 不過 0 | [PASS] VRN2_ConsensusJoin v0101 --selftest · 11 項 · 不過 0 | [PASS] VRN2_ConsensusJoin v0102 --selftest · 6 項 · 不過 0 | [PASS] VRN2_ConsensusJoin v0103 --selftest · 13 項 · 不過 0 | [PASS] VRN2_ConsensusJoin v0104 --selftest · 不過 0 | [PASS] VRN2_ConsensusJoin v0105 --selftest · 不過 0
st102: [PASS] VRN2_OutputStore v0102(v0101 / v0100 薄尾) --selftest · 引擎 duckdb · 8 項 · 不過 0 | [PASS] VRN2_OutputStore v0102 --selftest · 引擎 duckdb · 不過 0 | [PASS] VRN2_OutputStore v0102(v0101 / v0100 薄尾) --selftest · 引擎 duckdb · 8 項 · 不過 0 | [PASS] VRN2_OutputStore v0102 --selftest · 引擎 duckdb+pyarrow · 不過 0 | [PASS] VRN2_OutputStore v0102(v0101 / v0100 薄尾) --selftest · 引擎 pyarrow · 8 項 · 不過 0 | [PASS] VRN2_OutputStore v0102 --selftest · 引擎 pyarrow · 不過 0
ss102: [PASS] ① v0101 自測(隔離在只有 v0100 提案冊的夾)照過:[PASS] VRN2_SSOTSync v0101 --selftest · 6 項 · 不過 0 | [PASS] VRN2_SSOTSync v0102 --selftest · 4 項 · 不過 0 | [PASS] ① v0101 自測(隔離在只有 v0100 提案冊的夾)照過:[PASS] VRN2_SSOTSync v0101 --selftest · 6 項 · 不過 0 | [PASS] VRN2_SSOTSync v0102 --selftest · 4 項 · 不過 0 | [PASS] ① v0101 自測(隔離在只有 v0100 提案冊的夾)照過:[PASS] VRN2_SSOTSync v0101 --selftest · 6 項 · 不過 0 | [PASS] VRN2_SSOTSync v0102 --selftest · 4 項 · 不過 0
pwsh 7.4.6 剖析錯 [0, 0, 0, 0, 0] · Handle-All 一行 = 可讀版 True · 開機行 = 可讀版 True
```

桌機規模模擬(容器):16588 FinancialAligned rows (12004 clean + 4584 marked in 44 files) + 38 Deleted → purge plan 0.08 s · apply 2.9 s · 12004 / 0 left · next sync 0 rows (duckdb 2.0 · container)

## 5. e2e(桌機 v0153 狀態沙盒 · 增量庫先用 OutputStore v0101 收一批帶 MOPS 歷史記號的列 · 6669 報告日前 Yahoo 分割 · 沙盒 GitHub 分支 · pwsh 7.4.6)

```text
[repair] [GREEN] boot: Handle-All v0112 SHA-256 OK (claude/optimistic-goodall-yhalc5)
[repair] [計] ⑤ 自動修計畫:市場資料比歷史對齊新 / 歷史對齊沒跑 → 重跑 ⑬b · Combined 比市場 / 共識舊(或不在)→ 重組 · ⑬ 增量庫清掉 MOPS 算的列(先備份 · 可還原)+ 補寫(本輪有修正) · Workbench 重渲染(最新收據)
[repair]     [Combined] [GREEN] 共識合併 v0105 · join · Combined 14 列 · 調整後目標價 11 · FactSet 中位數 14 · YFinance 中位數 14 · EPS 格 42 · 年 2026 ~ 2028 · 同步還原:TARGET_PRICE(ADJ) 補 1 · 仍缺 0(SYNC_YAHOO_RATIO 1) · TWSE / TPEX 格式:tw_consensus 13 · tw_conse
[repair] [GREEN] ⑤ 修 · ⑬ 增量庫清掉 MOPS 算的列(先備份 · 可還原)+ 補寫(本輪有修正) · 清 MOPS 列 {"FinancialAligned": 4935, "Deleted": 13}(備份 _mops_purge_20261031_195741)· duckdb · 追加 {"BasicInfo": 0, "FinancialData": 0, "Summary": 0, "Rejected": 0, "Combined": 1
[repair] [GRAY] ⑥ TARGET_PRICE(ADJ) 同步還原 · ⑥e 錨點 · TARGET_PRICE(ADJ) 補 1 · 仍缺 0(SYNC_YAHOO_RATIO 1) · VDF status PARTIAL · CLOSE_MISMATCH 6669 7 列
[repair] ===== 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 3 項等 VCGC 決定 / 安裝
[repair]   [VCGC] 3 項
[repair]   [人工] 2 項
[full] [GREEN] boot: Handle-All v0112 SHA-256 OK (claude/optimistic-goodall-yhalc5)
[full]   [計] ⑬ 輸出位置 · 增量庫 · GREEN · 擋 MOPS 列 {"FinancialAligned": 4905, "Deleted": 12} · <sbx>/OneDrive/VRN2_out(OneDrive 同步夾)· 鏡像 22 · 引擎 duckdb · 新檔 0 / 已知 14 · 追加 BasicInfo 0 / FinancialData 0 / Summary 0 / Rejected 0 / Combined 14 / 
[full]   NEXT: [YELLOW] VRN-2 v0164 · rc 2 · 跑了 1 輪 · <sbx>/VIA/VIA_Reports/vrn2/VRN2_Closeout_v0164.json
[full] [YELLOW] ④ 跑啟動器 ActivateVRN-2_v0164.py · rc 2 · 103 秒 · NEXT: [YELLOW] VRN-2 v0164 · rc 2 · 跑了 1 輪 · <sbx>/VIA/VIA_Reports/vrn2/VRN2_Closeout_v0164.json
[full] [GRAY] ⑥ TARGET_PRICE(ADJ) 同步還原 · ⑥e 錨點 · TARGET_PRICE(ADJ) 補 1 · 仍缺 0(SYNC_YAHOO_RATIO 1) · VDF status PARTIAL · CLOSE_MISMATCH 6669 7 列
[full] ===== 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 7 項等 VCGC 決定 / 安裝
[full]   [VCGC] 7 項
[full]   [人工] 1 項
[tamper] [RED] boot SHA-256 mismatch - not run
repair rc 0 · full rc 0 · tamper rc 0
```

repair 後增量庫:{"lamp": "GREEN", "removed": {"FinancialAligned": 4935, "Deleted": 13}, "removed_total": 4948, "totals_before": {"FinancialAligned": 4935, "Deleted": 13}, "totals_after": {"FinancialAligned": 0, "Deleted": 0}, "backup_sha256": "14e1eabfdc841474031cdf24e6e16aa5edcafb632adf8936c44099d1b18fd7c0", "folder": "_mops_purge_20261031_195741"} · 同步還原:{"mode": "SYNC_YAHOO_RATIO", "before_date": "2025-09-30", "ratio": 0.5, "factor": 0.485, "target_price": 4200.0, "target_price_adj": 2037.0, "match_from": "2026-10-30"} · 增量庫夾:., ./_mops_purge_20261031_195741, ./_mops_purge_20261031_195741/PURGE_MANIFEST.json, ./_mops_purge_20261031_195741/parquet, ./_mops_purge_20261031_195741/removed, ./_mops_purge_20261031_195741/vrn2_store.duckdb.bak, ./integrated, ./integrated/VRN2_Integrated_BasicInfo_20261029_145919.csv, ./integrated/VRN2_Integrated_BasicInfo_20261029_145919.json, ./integrated/VRN2_Integrated_BasicInfo_20261029_145919.parquet, ./integrated/VRN2_Integrated_BasicInfo_latest.csv, ./integrated/VRN2_Integrated_BasicInfo_latest.json, ./integrated/VRN2_Integrated_BasicInfo_latest.parquet, ./latest, ./latest/IDEMPOTENCE_latest.json, ./latest/VRN2_Acceptance_latest.json, ./latest/VRN2_BasicInfo_latest.csv, ./latest/VRN2_BasicInfo_latest.json, ./latest/VRN2_BasicInfo_latest.parquet, ./latest/VRN2_Combined_latest.csv, ./latest/VRN2_Combined_latest.json, ./latest/VRN2_Combined_latest.parquet, ./latest/VRN2_Completion_latest.json, ./latest/VRN2_Deleted_latest.csv, ./latest/VRN2_Deleted_latest.json, ./latest/VRN2_Deleted_latest.parquet, ./latest/VRN2_FinancialAligned_latest.csv, ./latest/VRN2_FinancialAligned_latest.json, ./latest/VRN2_FinancialData_latest.csv, ./latest/VRN2_FinancialData_latest.json, ./latest/VRN2_FinancialData_latest.parquet, ./latest/VRN2_Input_latest.json, ./latest/VRN2_MarketConsensus_latest.csv, ./latest/VRN2_MarketConsensus_latest.json, ./latest/VRN2_Rejected_latest.csv, ./latest/VRN2_Rejected_latest.json, ./latest/VRN2_Rejected_latest.parquet, ./latest/VRN2_Summary_latest.csv, ./latest/VRN2_Summary_latest.json, ./latest/VRN2_Summary_latest.parquet, ./latest/VRN2_VerbatimVerify_latest.json, ./latest/VRN2_Workbench_latest.html, ./parquet, ./parquet/BasicInfo, ./parquet/Combined, ./parquet/Deleted, ./parquet/FinancialAligned, ./parquet/FinancialData, ./parquet/MarketConsensus, ./parquet/Rejected, ./parquet/Summary, ./parquet/catalog.parquet, ./store_pyarrow, ./store_pyarrow/catalog.json, ./vrn2_store.duckdb

**沒跑到的**:the desktop store itself (next repair purges it) · the 3706 / 6669 VDF daily rows on the desktop (the sync evidence file will show which rule applies) · a real consensus fetch (gate closed in the container)。
