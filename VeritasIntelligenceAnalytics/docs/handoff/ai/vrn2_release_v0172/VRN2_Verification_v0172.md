# VRN-2 v0172 驗證紀錄(2026-11-03 · VRN P0 三項:Parquet 型別 · UPSIDE_ADJ 小數欄 · Basic Info 合併檢視 · 套件 v0172 · RoundAll v0128 · Handle-All v0120)

操作員 2026-11-03:「新增小數欄,舊欄保留並標註,三項一起修 · 授權給你依照你建議最佳化完成」+ 睡前授權「自動解決完善三個獨立系統一切問題 · 完成既有範圍不可擴張」。

## 1. 三項修正(只增新版 · 前版一字不改)

| # | 桌機 15:18 真資料 | 本輪 | 沙盒實證 |
|---|---|---|---|
| F1 | FinancialAligned 11,905 列 JSON / CSV 在 · Parquet「(沒寫:ArrowInvalid)」| **HistoryAlign v0103**:前版照寫;只有沒寫成時依欄位型別重寫(數字欄空值 null · 真混型整欄轉字串 · 讀回比對才換上)| auto1 (sandbox venv: pyarrow cannot load) → receipt honestly '(沒寫:ImportError) · 型別版也沒寫成:ImportError' → auto2 repair with a pyarrow Python: the prior write hit ArrowInvalid (mixed column) → v0103 typed rewrite · FinancialAligned 5232 rows · num 6 · str 16 · mixed→str ['VALUE_FINAL'] |
| F2 | `UPSIDE_PCT(ADJ)` 存百分數(46.0)· 增量庫已有舊列 → 不能改語意 | **ConsensusJoin v0107**:新增 `UPSIDE_ADJ`(純小數 9 位)緊接舊欄 · 舊欄保留 · `output/VRN2_Combined_columns_latest.json` 標註 | Combined UPSIDE_ADJ right after UPSIDE_PCT(ADJ) · filled 11 = old 11 · cross-check mismatches 0 · column notes file written · DuckDB book_combined 多 UPSIDE_ADJ 欄(31 列 · 新輪 17 列有值 · 舊列 NULL) |
| F3 | Basic Info NAME 23/52 · ADJ_CLOSE 0/52(原文冊)vs Combined 51/52 | **Workbench v0107**:Basic Info · 合併檢視(原 / 合標來源 · 兩冊不改)· 上漲空間用小數欄 × 100 · 驗證燈 +3 · 自包含(跳過 v0105 / 桌機 accelfix v0106)· 第 3 行加速器標記 | Workbench v0107 over v0102 (repo runtime) · marks {"id=\"wb107-css\"": 1, "id=\"wb107\"": 1, "id=\"wb107b\"": 1, "id=\"wb107-js\"": 1, "id=\"wb105\"": 0} · lamps {"Basic Info · 合併檢視": "YELLOW", "上漲空間 新欄 × 舊欄": "GREEN", "歷史對齊 Parquet": "GREEN"} · browser 1920/1366/390: card rows 17, nothing overflows outside the table container; the 390-px page scroll is the prior page header (unchanged when the v0107 blocks are removed) |

## 2. ⑤ 自動修(收據 ≥ v0170 → repair · 幾分鐘 · 不用整輪)

RoundAll v0128 新觸發:歷史對齊 Parquet「(沒寫…」→ ⑬b(先只增不覆寫補放 HistoryAlign v0103 鏈)· Combined 沒有 UPSIDE_ADJ → 重組(ConsensusJoin v0107)·
頁不是 v0107 → 重渲染(補放 Workbench v0107)· 增量庫照舊跟著補寫(OutputStore v0102 的 ALTER TABLE 加欄 · 舊列 NULL)。
沙盒 auto2 的計畫實錄:`歷史對齊 FinancialAligned,Deleted 的 Parquet 沒寫(ImportError(這支 Python 的 pyarrow 載不起來))→ HistoryAlign v0103 依欄位型別重寫(JSON / CSV 照舊) · TARGET_PRICE(ADJ) 同步還原 + 共識照 TWSE / TPEX 格式合併(ConsensusJoin v0105)→ 重組 Combined · ⑬ 增量庫補寫(本輪有修正) · Workbench 重渲染(最新收據)`

## 3. 測試

| 項目 | 結果 |
|---|---|
| RoundAll v0128 自測 | [PASS] VRN2_RoundAll v0128 --selftest · 98 項 · 不過 0 |
| 啟動器 v0172 自測 | 全過 · [PASS] v0172: HistoryAlign v0103 (typed Parquet rewrite · JSON / CSV unchanged) · ConsensusJoin v0107 (UPSIDE_ADJ ratio  |
| 模組自測 | HistoryAlign v0103(pyarrow) 全過(6 項) · ConsensusJoin v0107 全過(9 項) · Workbench v0107 全過(15 項) · ConsensusJoin v0106 回歸 全過(11 項) · Workbench v0105 回歸 全過(10 項) |
| PowerShell 剖析 | pwsh 剖析錯 [0, 0, 0, 0, 0] · Handle-All 一行 = 可讀版 True · 開機行 = 可讀版 True |
| e2e(最短一行 · 沙盒)| auto1 rc 0 · confirm list rc 0 · auto2 rc 0 · tamper rc 0 · auto1 整輪(啟動器 v0172)→ 模擬桌機 v0170 狀態 → auto2 repair → 竄改開機檔不執行 |
| 收尾狀態 | {"auto1": {"state": "OPEN", "per_owner": {"VCGC": 8, "VRN-2": 3, "人工": 8}}, "auto2": {"state": "OPEN", "per_owner": {"VCGC": 6, "VRN-2": 3, "人工": 8}}} · VRN-2 項與 v0171 基準相同(沙盒限定:沒有真 OCR 環境的驗收紅 · 已記錄在前版驗證)· 綠 32 → 36 |

## 4. 沒做 / 待辦(不擴張)

- 桌機實跑(一行 · auto = repair · 幾分鐘)· 操作員 `--confirm H-fd2ea35f`(只有操作員打才算)· 同意閘不代設。
- 桌機真的 11,905 列 ArrowInvalid 在沙盒以同形狀資料重現(單元 + 沙盒 auto2);桌機那本要等 repair 跑過才看到 `parquet_typed`。
- 下一階段(VRN P1 · 已列在 VIA_Ultimate_Requirements_v0100.md):F4 拖曳 / 刪除勾選接後端 · F5 匯出 Parquet 檔 · 內建預覽 · checkpoint · 壓測。
