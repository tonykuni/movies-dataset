# VRN-2 v0161 驗證紀錄(2026-10-31 · RoundAll v0117 · Handle-All v0109 · 套件 v0158 不動)

## 1. 起因(桌機 14:33 貼回 · `VRN2_PasteBack_20261031_143304.zip`)

RoundAll v0116 repair → 收尾 **OPEN · VRN-2 2 項**,兩項都是 ⑥e。`market\vdf\last_error.txt` 的錯誤是
`RuntimeError: Another writer may be active. Inspect …\VIA_Reports\vrn2\market\vdf\RUNNING.lock; remove only after confirming the old process has stopped.`
上午整輪(啟動器 v0158 · 3802 秒)⑥e 跑 5 次全被這個鎖擋住:09-18 ~ 10-04 日線(2 檔 · 就是 3706 / 6669 回補)rc1 致命錯 · 財報 2020~2023 / 2022~2025 / 2023~2025 / latest 都 rc1。
不是網路工具 DENY(上一輪那句 `Existing VIA network bridge denied` 不在)→ RoundAll 認不出來 → 照保守規則算 VRN-2;收尾頁那列又先放了 43 檔代號的 CMD,錯誤被截掉。

根因:VDF 引擎 `VDF_TW_AllInOne_v039` 的 `def_run_lock` 在輸出夾用 O_EXCL 建 `RUNNING.lock`,只在 `finally` 刪 → 引擎被強制結束(逾時殺掉 / 關視窗)就留下,
之後每次 ⑥e 都停。輸出夾是 VRN-2 自己的(`VIA_Reports\vrn2\market\vdf`);引擎與共用 MarketFetch 是借用的(只讀不改)。

## 2. 修法(RoundAll v0117 · SHA-256 `9136cc21a230`)

| 項目 | 內容 |
|---|---|
| 擷取鎖過期判斷 | PID 已不在 / 號碼現在不是 python(被重用)/ 那個行程比鎖晚起(重用)→ 過期;讀不到 = 當它還在跑 |
| 處理 | 過期 → 移到 `RUNNING.lock.stale_<時間>`(不刪 · 內容照留)· 還在跑 → 不動(收尾頁「人工」)|
| ④ / ⑤ | ④ 跑啟動器前先看一次 · ⑤ 鎖過期就移開 · 上一輪 ⑥e 被鎖擋住就重抓(repair 自己找共用 MarketFetch 最高版號)|
| last_error.txt | ④ 前 / ⑤ 重抓前把上一輪的移到 `last_error.before_<時間>.txt`(MarketFetch 只在失敗時寫 · 不移的話抓成功了舊錯誤還在)|
| 收尾頁 | 「⑥e 擷取錯誤」錯誤在前 · CMD 在後(代號縮成「N 檔」)· 新列「⑥e 擷取鎖擋住」· 三列合一列 · 貼回包帶 `RUNNING.lock` |

Handle-All v0109 = v0108 指向 RoundAll v0117(一行 `1d0c8a92b7b6` · 開機檔 `348a293e60db` · 最短一行 443 字元 · cmd 一行 1240 字元)。套件 `vrn2_release_v0158/VRN2_Closeout_v0158.zip` 不動。

## 3. 測試

```text
[PASS] 65 ⑥e 擷取鎖過期判斷:沒有鎖 · PID 已不在 = 過期 · 還在跑的 python 比鎖早起 = 不動 · 號碼現在是別的程式 / 比鎖晚起 = 過期(重用)· 讀不到程式名 = 不動 · 鎖讀不到 PID = 過期
[PASS] 66 過期擷取鎖移到 RUNNING.lock.stale_<時間>(不刪 · 內容照留)· 原位置空出來 · 貼回包帶 market/vdf/RUNNING.lock
[PASS] 67 ⑤ 自動修:上一輪 ⑥e 被擷取鎖擋住 + 鎖過期 → 先移鎖再重抓 ⑥e(順序)· 鎖還在跑 → 都不做 · 鎖已不在 → 只重抓 · VIA_VRN2_NO_MARKET=1 → 不重抓
[PASS] 68 「⑥e 擷取錯誤」錯誤訊息在前 · CMD 在後(43 檔代號縮成「43 檔」)· 收尾頁:擷取鎖還在跑 = 人工 · 鎖過期 / 已不在 = VRN-2(跑 repair 自己修)· 同一件事三列合一列
[PASS] 69 上一輪的 last_error.txt 在 ④ 跑啟動器前 / ⑤ 重抓 ⑥e 前移到 last_error.before_<時間>.txt(不刪)· MarketFetch 只在失敗時寫 → 這輪抓成功就不會留著舊錯誤 · 沒有檔 = 不動
[PASS] VRN2_RoundAll v0117 --selftest · 69 項 · 不過 0
venv(有 PyMuPDF):[PASS] VRN2_RoundAll v0117 --selftest · 71 項 · 不過 0
pwsh 7.4.6 剖析錯 [0, 0, 0, 0, 0] · Handle-All 一行 = 可讀版 True · 開機行 = 可讀版 True
e2e 結束碼:stale rc 0 · live rc 0 · full rc 0 · tamper rc 0
```

VCGC 全景骨架卡(`CGC_MDL158 … read`):RoundAll v0117 報 10 項 SWALLOW,跟 v0115 / v0116 一樣多。

## 4. 用桌機貼回包重播(只讀 · 容器 · report 模式 · 放一個 PID 已不在的鎖)

```text
RoundAll v0116 · OPEN · {"VRN-2": 3, "人工": 2, "資料源": 1} · ⑥e 項 2(VRN-2、VRN-2)· 「擷取錯誤」列開頭:CMD:
RoundAll v0117 · OPEN · {"VRN-2": 2, "人工": 2, "資料源": 1} · ⑥e 項 1(VRN-2(合併 3 列))· 「擷取錯誤」列開頭:(合進 ⑥e 那一項)
```

(只留負責方統計 · 桌機的明細不進倉。貼回包缺 JSON 冊,所以兩版都多一項「Combined 冊」· 桌機沒有這項。)v0116:⑥e 兩項分開算 VRN-2,「擷取錯誤」那列開頭是 CMD(錯誤被截掉);v0117:⑥e 三列合成一項,錯誤排在前面。

## 5. e2e(桌機 v0153 狀態沙盒 · 沙盒 GitHub 分支 · pwsh 7.4.6 · 同意閘不設)

```text
[stale] [GREEN] boot: Handle-All v0109 SHA-256 OK (claude/optimistic-goodall-yhalc5)
[stale] [計] ⑤ 自動修計畫:⑥e 擷取鎖過期(PID 999999 已不在(上一個擷取被強制結束 · 鎖沒清) · 2026-10-31T02:40:00+00:00)→ 移開(不刪) · 市場資料比歷史對齊新 / 歷史對齊沒跑 → 重跑 ⑬b · Combined 比市場 / 共識舊(或不在)→ 重組 · ⑬ 增量庫補寫(本輪有修正) · Workbench 重渲染(最新收據)
[stale] [GREEN] ⑤ 修 · ⑥e 擷取鎖過期(PID 999999 已不在(上一個擷取被強制結束 · 鎖沒清) · 2026-10-31T02:40 · 擷取鎖 PID 999999 已不在(上一個擷取被強制結束 · 鎖沒清) · 鎖時間 2026-10-31T02:40:00+00:00 → 移到 RUNNING.lock.stale_20261031_070748(不刪)
[stale] ===== 收尾 · OPEN · 未結案 · VRN-2 還有 1 項要修
[stale]   [VRN-2] 1 項
[stale]   [VCGC] 2 項
[stale]   [人工] 2 項
[live] [GREEN] boot: Handle-All v0109 SHA-256 OK (claude/optimistic-goodall-yhalc5)
[live] ===== 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 2 項等 VCGC 決定 / 安裝
[live]   [VCGC] 2 項
[live]   [人工] 3 項
[full] [GREEN] boot: Handle-All v0109 SHA-256 OK (claude/optimistic-goodall-yhalc5)
[full] [GREEN] ④ ⑥e 擷取鎖 · 過期 · PID 999998 已不在(上一個擷取被強制結束 · 鎖沒清) · 鎖時間 2026-10-31T03:00:00+00:00 → 移到 RUNNING.lock.stale_20261031_070825(不刪)
[full] [計] ④ 上一輪的 ⑥e last_error.txt 移到 last_error.before_20261031_070825.txt(這輪 ⑥e 失敗才會再寫)
[full] ===== 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 7 項等 VCGC 決定 / 安裝
[full]   [VCGC] 7 項
[full]   [人工] 1 項
[tamper] [RED] boot SHA-256 mismatch - not run
```

- stale(repair):⑤ 把 PID 已不在的鎖移到 `RUNNING.lock.stale_*`;沙盒沒有合 VDF 界線的擷取 Python → ⑥e 這輪沒重抓 → 收尾留 1 項 VRN-2「擷取鎖已不在 · 再跑 repair」(桌機有 `C:\Python313` 會重抓)。
- live(活的 python · 比鎖早起):鎖不動 · 收尾 BLOCKED · 鎖那項算「人工」。
- full:④ 先移開過期鎖 · 舊 last_error.txt 改名留著 · 收尾 BLOCKED · VRN-2 0(沙盒的 VCGC 項是沙盒環境)。 tamper:開機檔被改 → 不執行。
- 輸出夾事後:stale → RUNNING.lock.stale_20261031_070748, last_error.txt · live → RUNNING.lock, RUNNING.lock.stale_20261031_070748, last_error.txt · full → RUNNING.lock.stale_20261031_070748, RUNNING.lock.stale_20261031_070825, last_error.before_20261031_070825.txt

**沒跑到的**:鎖移開之後真的重抓 ⑥e(容器沒有合 VDF 界線的 Python · VRN-2 不裝套件)→ 計畫順序由自測 67 把關,重抓沿用既有 ⑤「market」修法(MarketFetchRun)。

## 6. 桌機預期

repair → ⑤ 計畫第一項「⑥e 擷取鎖過期(PID … 已不在)→ 移開」→「⑥e 上一輪被擷取鎖擋住 → 重抓」→ 日線(含 3706 / 6669 回補)重抓 · 財報打 MOPS 預期照舊被 VIA 網路工具 DENY
→ 收尾回到 **BLOCKED · VRN-2 0 · VCGC 1 · 人工 2 · 資料源 1 ~ 2**。鎖的 PID 還在跑 → 不動 · 收尾頁「人工」。

## 7. 給 VDF(只讀攤開 · 不改)

`VDF_TW_AllInOne_v039.def_run_lock` 只看鎖檔在不在,不檢查鎖裡的 PID 是否還活著 → 引擎被強制結束後,下一次一定被擋(訊息叫人手動刪)。要不要改成「啟動時判 PID 過期」是 VDF 的決定。
