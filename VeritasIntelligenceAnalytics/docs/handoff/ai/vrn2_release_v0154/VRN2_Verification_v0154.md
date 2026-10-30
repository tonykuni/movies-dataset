# VRN-2 v0154 驗證紀錄(2026-10-30 · ConsensusJoin v0103 · RoundAll v0110 · Handle-All v0102 短開機行)

## 1. 桌機 20:09 整輪(Handle-All v0101 → RoundAll v0109 · 2225 秒)看到的

- ⑪ 獨立驗證 v0114:錯值 0 · 年度 11505 筆 · 沒有 DUPKEY(管理器 v0257 改名 37 · 剔除 8 —— v0153 修的生效)。
- 收尾 **OPEN · VRN-2 2 · VCGC 1 · 人工 2 · 資料源 2**;VRN-2 那兩項都是 ⑥f 共識:
  第一次 43 檔(`Run ID RUN_20261030_120938`)· 6933 / 7728 / 4171 `TARGET_PRICE_STATUS_NOT_200: statusCode=404` → ConsensusJoin v0102「拿掉這三檔、同一個引擎再跑一次(其他代號續跑沿用)」→
  第二次 `Run ID RUN_20261030_121215` · **40 檔全部 `def Fetch`**(一行 `def Resume` 都沒有)→ 8358 / 2891 `ASSIGNED_JSON_NOT_FOUND: __NEXT_DATA__` → gate FAIL_CLOSED · rc 1。
- **根因**:引擎 `def_compute_pipeline_input_hash()` 的雜湊含 `codes`(代號清單)· 日期 · 模式 → 清單一變就不是同一份 checkpoint(`def_initialize_checkpoint` 封存舊的、開新的)→ v0102 說的「續跑沿用」沒有發生。
  同一天 14:36 那輪 7728 有 FactSet 頁、20:09 回 404 → 鉅亨對短時間的第二輪整批請求會回沒有資料的頁 / 404。
- 收尾頁另外把 Combined 6 列算成「鉅亨沒有這檔的 FactSet 頁(404)」:沒有共識的列,v0100 的 join 把**整批**摘要抄進 `CONSENSUS: 缺:`,那串摘要裡有
  「鉅亨沒有 FactSet 頁(404)不納入閘:4171,6933,7728」→ 8358 / 2891 也被算成 404。
- 之後再貼 8.7k 字元的 Handle-All 一行:PSReadLine 2.4.5 在 133 × 33 的視窗裡 `IndexOutOfRangeException`(`ConvertOffsetToPoint`)—— PowerShell 輸入列的毛病,不是 VRN-2 的碼。

## 2. 自測

| 檔 | 結果 |
|---|---|
| VRN2_ConsensusJoin_v0103(引擎 v0121) | [PASS] VRN2_ConsensusJoin v0103 --selftest · 13 項 · 不過 0 |
| VRN2_ConsensusJoin_v0103(只有 runtime 的引擎 v0120) | [PASS] VRN2_ConsensusJoin v0103 --selftest · 13 項 · 不過 0 |
| VRN2_RoundAll_v0110 | [PASS] VRN2_RoundAll v0110 --selftest · 50 項 · 不過 0 |
| ActivateVRN-2_v0154(套件夾複本) | 12 段 PASS · [PASS] v0154: ConsensusJoin v0103 is the active consensus join (today's payloads resumed on a new code list · 404 / transient retried · still failing  |

ConsensusJoin v0103 的各項:

```text
[PASS] ② 代號來自基本資料冊:2330 · 2454 · 9999(去重 · 4 碼)
[PASS] ③ 引擎離線 fixture 實跑:3 代號 · FactSet 中位數 1450 / 1600 · YFinance 中位數 1500 / 1550 · EPS 2026 60 · 2027 75 · 2028 90 · PER 2026 = 1000 / 60 · 收據在 consensus/
[PASS] ④ join:3 列 · 欄序 = 清單 · 2330 調整後目標價 1470.00 · 上漲 45.5 · 還原收盤 1010.50 · NAME 由 VDF 補 · 主題與摘要 = 標題 + 三點(空點略)
[PASS] ⑤ join 共識欄:2330 FactSet 1450.00 · YFinance 1500.00 · 2026 EPS 60.00 · 2028 EPS 90.00 · 2026 PER 16.67 · 2454 2028 空 · 9999 有共識但沒市場 → 調整後目標價空且說缺 · 綠 / 黃
[PASS] ⑥ 輸出:json / csv(+ parquet 有 pyarrow)· 基本資料冊沒動(3 列 · _STATUS 還在)
[PASS] ⑦ VIA_VRN2_NO_CONSENSUS=1 → 灰不跑 · 收據照寫
[PASS] ⑧ 對應表:市場冊 per_ticker → 5274 → 5274.TWO · 2330 → 2330.TW · 壞值不收
[PASS] ⑨ 引擎原本:鉅亨 TWS:5274 → 5274.TW(桌機 404 的根因)· patch 後 → 5274.TWO · 2330 照舊 .TW
[PASS] ② 只有 404 頁面不存在的列 → 那幾檔不納入(6933 · 4171)
[PASS] ③ 還有別的不過列(2330 HTTP 500)→ 不動(照 FAIL_CLOSED)· 全部代號都 404 → 不動
[PASS] ④ gate FAIL_CLOSED 只因 404 → 拿掉 6933 · 4171 再跑一次 → 第二次 PASS · 收據記 no_coverage / first_gate
[PASS] ⑤ Combined:沒覆蓋的代號 STATUS 加「鉅亨沒有 FactSet 頁(404)」· 其他列不動
[PASS] ⑥ 啟動器叫的 run / join 與 CLI 的 run / join 都是本版(v0101 · v0100 的模組也指過來)
[PASS] ② 分類:6933 404 = 沒有 FactSet 頁 · 8358 沒有 __NEXT_DATA__ / 2891 連線中斷 = 一時抓不到 · 1234 HTTP 404 / 2330 品質列 = 其他
[PASS] ③ 搬 checkpoint:今天的 [2330,6933,8358] → [2330,8358] 搬 2 份 · 引擎自己的 def_initialize_checkpoint 認它可續跑 · 兩份 payload 讀得回 · 舊的封存
[PASS] ④ 不是今天的 checkpoint → 不搬(照引擎一天一抓)
[PASS] ⑤ 桌機 20:09 重演:404 重試 1 次 → 拿掉 6933 / 4171 再跑 → 8358 / 2891 不再上網(沿用第一次)→ PASS · 綠 · no_coverage 2 · source_gap 0
[PASS] ⑥ 同一劇本給 v0102:第二次清單一變 checkpoint 對不上 → 8358 / 2891 重抓 → FAIL_CLOSED(桌機的樣子 · v0103 才修)
[PASS] ⑦ 一時抓不到:8358 第一次沒有 __NEXT_DATA__ · 第二次有 → 重試 1 次就過閘 · 只重抓 8358 · 綠
[PASS] ⑧ 一直抓不到:2891 抓 3 次(重試 2 次)仍沒有 → source_gap · 拿掉再跑不上網 → PASS 但黃(鉅亨這次沒給)
[PASS] ⑨ 別的不過(HTTP 404 網頁本身不在)→ 不重試、不拿掉 · FAIL_CLOSED 原樣(VRN-2 的事)
[PASS] ⑩ join:2891 寫「鉅亨這次沒給資料(抓了 3 次)」· 6933 寫「鉅亨沒有 FactSet 頁(404)」· 不再抄整批摘要 · 2330 不動
[PASS] ⑪ 引擎實跑(不連網:代理指到關著的埠 · yfinance 用空殼):離線抓的 2330 / 5274 搬進即時清單 [2330,5274,6933] → 引擎 Resume 沿用 · 6933 連不上 = 一時抓不到 → 重試 1 次 → 拿掉再跑 → 引擎自己的閘過 · 黃 · source_gap 6933
[PASS] ⑫ 引擎這次沒有產出(rc 1 · 沒有 Gate 行 · NO_PAYLOAD_FETCHED)而矩陣是昨天的 → 不沿用:per_code 清空 · 黃 · engine_no_output · 「共識引擎這次沒有產出」
[PASS] ⑬ 啟動器叫的 run / join 與 CLI 的 run / join 都是本版(v0102 · v0101 · v0100 的模組都指過來)
```

引擎實跑(不連網 · 代理指到關著的埠 · yfinance 空殼):`引擎實跑:離線 gate PASS_WITH_WARNINGS · 即時 gate PASS_WITH_WARNINGS · rc 0 · 引擎輸出 136 行(收起來)· Resume 6 · Fetch 2 · 抓不到 2 · 閘 FAIL_CLOSED / FAIL_CLOSED / PASS_WITH_WARNINGS`

## 3. PowerShell 剖析 + 雜湊鏈(pwsh 7.4.6)

```text
[PASS] 套件 zip = RoundAll 釘的 = 發行清單 · a74f476610b9
[PASS] RoundAll 檔 = Handle-All 一行 / 可讀版 / PS7 一行 / 解開版的 $H = 發行清單 · cc1d4b5d7a04
[PASS] HandleAll md:第 1 段 = 短開機行 · 標記的那段 = Handle-All 一行檔 · 可讀版 × 2 · 一行 SHA-256 標在 md 與發行清單 · a3d4dc8b9f8b
[PASS] 短開機行:只有 ASCII · 1719 字元(133 欄約 13 行)· 釘的是 Handle-All 一行的 SHA-256 · cmd 一行解開 = 短開機行 · 都在 8191 內
[PASS] RoundAll md:PS7 一行 = 檔 · 兩行 -EncodedCommand 解開 = 解開版 · 都在 8191 字元內
[PASS] Handle-All / PS7 一行沒有 exit(視窗不關)· 沒有 # 註解 · 9009 字元
[PASS] PowerShell 剖析(pwsh 7.4.6)0 錯:handleall_line.txt 1243 詞 · handleall_src.ps1 1255 詞 · oneline_roundall_ps7.txt 378 詞 · boot_roundall.ps1 501 詞 · boot_line.txt 284 詞 · boot_src.ps1 288 詞
[PASS] Handle-All 一行版 = 可讀版(去掉換行 / 分號後詞序列相同)
[PASS] 短開機行 = 它的可讀版(詞序列相同)
```

## 4. 桌機 20:09 的 ⑥f 狀態重演(沙盒 13 檔版:第一次 4171 回 404 → v0102 拿掉再跑 → checkpoint 換新 → 2330 / 3661 沒有 __NEXT_DATA__ · 全部用引擎自己的 checkpoint 函式寫)

| 跑的 | 收尾 | 共識收據 |
|---|---|---|
| before RoundAll_v0109 | v0109 before · 收尾 OPEN 未結案 {"VCGC": 4, "VRN-2": 2, "人工": 1, "資料源": 1} | 共識收據: VRN2_ConsensusJoin 共識合併 v0102 · gate FAIL_CLOSED · lamp YELLOW · source_gap [] · no_coverage ['4171'] · retries — · seed [] |
| before RoundAll_v0110 | v0110 before · 收尾 OPEN 未結案 {"VCGC": 4, "VRN-2": 1, "人工": 1} | 共識收據: VRN2_ConsensusJoin 共識合併 v0102 · gate FAIL_CLOSED · lamp YELLOW · source_gap [] · no_coverage ['4171'] · retries — · seed [] |
| repair_v0110 | v0110 repair · 收尾 BLOCKED 等 VCGC {"資料源": 2, "VCGC": 5, "人工": 1} | 共識收據: VRN2_ConsensusJoin 共識合併 v0103 · gate PASS_WITH_WARNINGS · lamp YELLOW · source_gap ['2330', '3661', '4171'] · no_coverage [] · retries 2 · seed [10, 0, 0, 10] |

repair 那一輪 ⑤ 的過程(重演裡鉅亨連不上 → 2330 / 3661 / 4171 都是「一時抓不到」;桌機上 4171 會照樣回 404):

```text
[計] ⑤ 自動修計畫:⑥f 共識閘只因 404 / 一時抓不到(2330,3661) → 用 ConsensusJoin v0103 重跑(沿用今天抓到的 · 重試 · 暫缺不納入閘) · 市場資料比歷史對齊新 / 歷史對齊沒跑 → 重跑 ⑬b · Combined 比市場 / 共識舊(或不在)→ 重組 · ⑬ 增量庫補寫(本輪有修正) · Workbench 重渲染(最新收據)
    [⑥f]     [⑥f] [計] 今天的 checkpoint 是別份代號清單 → 抓到的 10 / 13 份搬進這次的(引擎續跑沿用 · 只抓沒抓過的)
    [⑥f]     [⑥f] [計] 品質閘 FAIL_CLOSED · 一時抓不到:2330,3661,4171(HTTP_GET_FAILED: url=https://www.cnyes.com/twstock/2330/summ) → 等 0 秒 · 同一份清單再跑一次(續跑:抓到的沿用 · 只重抓 2330,3661,4171)· 第 1 次
    [⑥f]     [⑥f] [計] 品質閘 FAIL_CLOSED · 一時抓不到:2330,3661,4171(HTTP_GET_FAILED: url=https://www.cnyes.com/twstock/2330/summ) → 等 0 秒 · 同一份清單再跑一次(續跑:抓到的沿用 · 只重抓 2330,3661,4171)· 第 2 次
    [⑥f]     [⑥f] [計] 品質閘 FAIL_CLOSED 只因 一時抓不到:2330,3661,4171(HTTP_GET_FAILED: url=https://www.cnyes.com/twstock/2330/summ) → 這些代號不納入、同一個引擎再跑一次
    [⑥f]     [⑥f] [計] 今天的 checkpoint 是別份代號清單 → 抓到的 10 / 10 份搬進這次的(引擎續跑沿用 · 只抓沒抓過的)
[YELLOW] ⑤ 修 · ⑥f 共識閘只因 404 / 一時抓不到(2330,3661) · 補放 VRN2_ConsensusJoin_v0103.py · 共識合併 v0103 · run · 共識 10 / 10 代號 · FactSet 中位數 10 · YFinance 中位數 10 · gate PASS_WITH_WARNINGS · rc 0 · 鉅亨這次沒給資料(抓了 3 次)暫不納入閘:2330,3661,4171
[GREEN] ⑤ 修 · 市場資料比歷史對齊新 / 歷史對齊沒跑 · 歷史對齊 v0102 · 對上 11 · 沒對上 0 · 無歷史 0(共 11 份)· 覆蓋 64 格 · 刪除區 12 列 · 檢驗 192(不過 5 · 口徑不明 6)
[GREEN] ⑤ 修 · Combined 比市場 / 共識舊(或不在)→ 重組 · 共識合併 v0103 · join · Combined 14 列 · 調整後目標價 11 · FactSet 中位數 10 · YFinance 中位數 10 · EPS 格 30 · 年 2026 ~ 2028
[YELLOW] ⑤ 修 · ⑬ 增量庫補寫(本輪有修正) · pyarrow · 追加 {"BasicInfo": 0, "FinancialData": 0, "Summary": 0, "Rejected": 0, "Combined": 0, "FinancialAligned": 0, "Deleted": 0} · 補缺 {"BasicInfo": 0, "FinancialData": 0, "Summary": 0, "Rejected": 0, "Combined": 0, "FinancialA
[GREEN] ⑤ 修 · Workbench 重渲染(最新收據) · VRN2_Workbench v0102 · <v154>/t154d/VIA/VIA_Reports/vrn2/VRN2_Workbench_latest.html
```

## 5. Handle-All v0102(短開機行 · 沙盒 GitHub 分支 · pwsh 7.4.6)

| 回合 | 結果 |
|---|---|
| e_report(VRN2_MODE=report · 短開機行) | 收尾 · OPEN · 未結案 · VRN-2 還有 1 項要修 · [VRN-2] 1 項 · [VCGC] 4 項 · [人工] 1 項 |
| e_auto_repair(auto → repair) | 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 5 項等 VCGC 決定 / 安裝 · [VCGC] 5 項 · [人工] 1 項 · [資料源] 2 項 |
| e_auto_again(auto → repair · 再一次) | 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 4 項等 VCGC 決定 / 安裝 · [VCGC] 4 項 · [人工] 1 項 · [資料源] 2 項 |
| e_cmd_report(cmd 一行 · pwsh -EncodedCommand) | 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 4 項等 VCGC 決定 / 安裝 · [VCGC] 4 項 · [人工] 1 項 · [資料源] 2 項 |
| e_tamper(分支上的 md 被改) | [RED] boot: SHA-256 7d203955c9985bae0271dce08599904f7d47b2a5701c700b31355a7ec4a5db3b is not a3d4dc8b9f8bf3d47eff359ad7c56548f5779a80968db6e3ee6178746c37f34b - not run |
| f_full_fixture(整輪 · ⑥f 離線 fixture) | 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 7 項等 VCGC 決定 / 安裝 · [VCGC] 7 項 · [人工] 1 項 |
| g_full_live(整輪 · ⑥f 即時 · 全部連不上) | 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 7 項等 VCGC 決定 / 安裝 · [VCGC] 7 項 · [人工] 1 項 · [資料源] 1 項 |

- auto 選模式:`[計] ④ 自動選模式 repair · 上一輪收據 VRN2_Closeout_v0153.json · 上一輪輸出冊 有(輸出冊是啟動器 v0153 以後做的 · 這版只改 ⑥f 共識 → 不整輪)(整輪:先貼 $env:VRN2_MODE = 'full') / [計] ④ 自動選模式 repair · 上一輪收據 VRN2_Closeout_v0153.json · 上一輪輸出冊 有(輸出冊是啟動器 v0153 以後做的 · 這版只改 ⑥f 共識 → 不整輪)(整輪:先貼 $env:VRN2_MODE = 'full')`
- 第二次 repair:`[GREEN] ⑤ 自動修 · 沒有要修的(能自動修的都已綠 / 灰)`
- 整輪 ⑥f:fixture = `  [計] ⑥f 共識合併 · GREEN · 共識 GREEN:共識 13 / 13 代號 · FactSet 中位數 13 · YFinance 中位數 13 · gate PASS_WITH_WARNINGS · rc 0 · Combined GREEN:Combined 14 列 · 調整後目標價 11 · FactSet 中位數 14 · YFinance 中位數 14 · EPS 格 42 · 年 2026 ~ 2028`;即時(全部連不上)= `  [計] ⑥f 共識合併 · YELLOW · 共識 YELLOW:共識引擎這次沒有產出(rc 1 · RuntimeError: NO_PAYLOAD_FETCHED: [{'code': '6669', 'status': 'FAIL', 'error': 'HTTP_GET_FAILED: url=https://www.cnyes.c)· 上次的矩陣(2026-10-30 11:20)不算這次的 · Combined YELLOW:Combined 14 列(共識欄全空:共識引擎這次沒有產出(rc 1 · RuntimeError: NO_PAYLOAD`
- 整輪 ③ 自測:f_full_fixture 14 支 · 綠 14 · 非綠 0 · g_full_live 14 支 · 綠 14 · 非綠 0
- 結束碼:e_report rc 0 · e_auto_repair rc 0 · e_auto_again rc 0 · e_cmd_report rc 0 · e_tamper rc 0 · done-drive · f_full_fixture rc 0 · g_full_live rc 0

## 6. 限制(誠實寫)

- 容器連不到鉅亨 / Yahoo:即時路徑用「代理指到關著的埠」測(= 一時抓不到);404 的分類用自測的列與桌機的原文字串測。
- 沙盒的 yfinance / duckdb 是空殼,只讓套件檢查過(引擎真的匯入 duckdb 會失敗 → 照引擎沒有 duckdb 的路)· 不在套件裡。
- 沙盒的 VCGC 項(envcheck 缺 · 沒有合 VDF 界線的擷取 Python · 沒有 duckdb)是容器環境的,桌機以桌機收尾頁為準。
- 共識引擎檔(v0120 在 runtime · 桌機用的 v0121 在 functional modules\VRN2)一字不改;v0103 只用它自己的函式搬 checkpoint。

## 7. 桌機下一步

PowerShell 7 貼 `VRN2_HandleAll_v0102.md` 最上面那行短的(1,719 字元 · 全是 ASCII)→ auto 選 **repair**(上一輪收據 v0153 · 輸出冊在)→
⑤ 用 ConsensusJoin v0103 重跑 ⑥f(今天的 checkpoint 才搬 · 明天起照引擎一天一抓)→ 收尾頁 ⑥f 應該是:全部過閘(綠)或「鉅亨這次沒給資料 / 沒有 FactSet 頁」(資料源)· VRN-2 0。
cmd 視窗用同一份 md 的 cmd 那行(不經 PowerShell 輸入列)。
