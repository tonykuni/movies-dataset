# VRN-2 v0162 驗證紀錄(2026-10-31 · RoundAll v0118 · Handle-All v0110 · 套件 v0158 不動)

## 1. 起因(桌機 16:11 · 主控台文字 · RoundAll v0117 repair · 2518 秒)

- v0117 生效:過期 `RUNNING.lock`(PID 20940 · 2026-10-30T23:09:15Z 留下)移到 `RUNNING.lock.stale_20261031_152959` → ⑥e 開始重抓 · 舊 last_error.txt 改名留著。
- **MOPS 財報這次沒被網路工具擋**(VCGC 0 項):[FIN] 一檔約 30 秒逐檔抓(5 檔 → 19 檔 → 22 檔三組補缺)。
- ⑤ 重抓 ⑥e 的上限寫死 2400 秒 → 第 3 組第 17 檔(4966)被停 · 最後一組 latest(43 檔)沒跑 · 填值照舊(完整 51 · 缺 1)。
- ⑬b 歷史對齊因此不完整(對上 15 · 沒對上 22 · 無歷史 7 · 檢驗 479 不過 10 · 口徑不明 6)。
- 收尾 **OPEN · VRN-2 5 項** = ⑤ 重抓 ⑥e / ⑥ 步驟 ⑥e / ⑤ 重跑 ⑬b / ⑥ 步驟 ⑬b / ⑥ 歷史對齊 —— 其實是同一件事(⑥e 沒抓完)。
- 主控台被進度列文字灌滿:進度列文字含中文 / ⑥ / ·(一個字佔兩格)· 超過視窗寬就折行 → PowerShell 重畫算錯行數 → 舊的那條一直留在畫面上。
- 下一次 repair 也不會自己接著抓:last_error.txt 已改名、收據 ⑥e 寫的是「RoundAll 修正後 · 擷取 RED:逾時 2400 秒」(不是擷取鎖)。

## 2. 修法

| 檔 | 內容 |
|---|---|
| RoundAll v0118(`9a770b113b34`)| ⑤ 重抓 ⑥e 擷取上限 2400 → 5400 秒(`VRN2_MARKET_FETCH_SEC` · 最少 600)· 填值 2400 · 收據 ⑥e「RoundAll 修正後 · 擷取 RED:逾時 N 秒」→ ⑤ 再排重抓(VDF 引擎 MOPS 回應 12 小時快取)· 收尾頁 ⑥e 各列同一項 · ⑥e 沒抓完時 ⑬b 三列併入 · 自測 72 |
| Handle-All v0110(一行 `5fd2053f8ed6` · 開機檔 `aacbdb11c290`)| `$PSStyle.Progress.MaxWidth` = 視窗一半寬(跑完還原)· RoundAll 跑時只留它那一條真百分比 · 進度列標題改英數 · 逾時保底 整輪 8 h / 其他 4 h |

最短一行 443 字元 · cmd 一行 1240 字元 · 套件 `vrn2_release_v0158/VRN2_Closeout_v0158.zip` 不動。

## 3. 測試

```text
[PASS] 70 ⑤ 上一輪 RoundAll 重抓 ⑥e 逾時(收據「RoundAll 修正後 · 擷取 RED:逾時 2400 秒」)→ 接著抓 · ⑥e 綠了 / VIA_VRN2_NO_MARKET=1 → 不抓 · 擷取上限預設 5400 秒(VRN2_MARKET_FETCH_SEC 可調 · 亂填照預設)
[PASS] 71 收尾頁:⑤ 重抓 ⑥e / ⑥ 步驟 ⑥e / ⑬b 三列 = 桌機 16:11 的 VRN-2 5 項 → ⑥e 沒抓完時合成 1 項(說明重抓上限 · 歷史對齊跟著不完整)· ⑥e 完整時 ⑥e / ⑬b 各 1 項
[PASS] 72 ⑤ 重抓 ⑥e 的擷取(--fetch)用 market_fetch_sec() 當上限 · 填值(--fill)照舊 2400 秒
[PASS] VRN2_RoundAll v0118 --selftest · 72 項 · 不過 0
venv(有 PyMuPDF):[PASS] VRN2_RoundAll v0118 --selftest · 74 項 · 不過 0
pwsh 7.4.6 剖析錯 [0, 0, 0, 0, 0] · Handle-All 一行 = 可讀版 True · 開機行 = 可讀版 True
e2e 結束碼:stale rc 0 · live rc 0 · full rc 0 · tamper rc 0
```

自測 71 用的就是桌機 16:11 那 5 列(步驟名 + 內容):⑥e 沒抓完 → 合成 1 項(另見 4 列);⑥e 完整 → ⑥e / ⑬b 各 1 項。VCGC 全景骨架卡:RoundAll v0118 SWALLOW 10 項(同 v0117)。

## 4. e2e(桌機 v0153 狀態沙盒 · 沙盒 GitHub 分支 · pwsh 7.4.6 · 同意閘不設)

```text
[stale] [GREEN] boot: Handle-All v0110 SHA-256 OK (claude/optimistic-goodall-yhalc5)
[stale] [GREEN] ⑤ 修 · ⑥e 擷取鎖過期(PID 999999 已不在(上一個擷取被強制結束 · 鎖沒清) · 2026-10-31T02:40 · 擷取鎖 PID 999999 已不在(上一個擷取被強制結束 · 鎖沒清) · 鎖時間 2026-10-31T02:40:00+00:00 → 移到 RUNNING.lock.stale_20261031_095557(不刪)
[stale] ===== 收尾 · OPEN · 未結案 · VRN-2 還有 1 項要修
[stale]   [VRN-2] 1 項
[stale]   [VCGC] 2 項
[stale]   [人工] 2 項
[stale] PYPROG={"name":"VRN2_RoundAll_v0118.py","pct":100,"n":19,"d":19,"secs":19.247}
[stale] MAXWIDTH=120
[live] [GREEN] boot: Handle-All v0110 SHA-256 OK (claude/optimistic-goodall-yhalc5)
[live] ===== 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 2 項等 VCGC 決定 / 安裝
[live]   [VCGC] 2 項
[live]   [人工] 3 項
[live] PYPROG={"pct":100,"d":6,"name":"VRN2_RoundAll_v0118.py","n":6,"secs":0.882}
[live] MAXWIDTH=120
[full] [GREEN] boot: Handle-All v0110 SHA-256 OK (claude/optimistic-goodall-yhalc5)
[full] [GREEN] ④ ⑥e 擷取鎖 · 過期 · PID 999998 已不在(上一個擷取被強制結束 · 鎖沒清) · 鎖時間 2026-10-31T03:00:00+00:00 → 移到 RUNNING.lock.stale_20261031_095638(不刪)
[full] ===== 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 7 項等 VCGC 決定 / 安裝
[full]   [VCGC] 7 項
[full]   [人工] 1 項
[full] PYPROG={"d":94,"pct":100,"n":94,"name":"VRN2_RoundAll_v0118.py","secs":132.005}
[full] MAXWIDTH=120
[tamper] [RED] boot SHA-256 mismatch - not run
[tamper] PYPROG=null
[tamper] MAXWIDTH=120
```

`MAXWIDTH=120`:Handle-All 跑完把進度列寬度還原(跑的時候是視窗一半寬)。

**沒跑到的**:2400 秒之後真的接著抓(容器沒有合 VDF 界線的 Python)· Windows 主控台的進度列實際長相(容器是 Linux)→ 桌機下一輪確認。

## 5. 桌機預期

repair → ⑤ 計畫有「⑥e 上一輪 RoundAll 重抓到 2400 秒逾時 → 接著抓」→ 日線 / 已抓財報走快取 · 接著抓剩下的財報(含 latest)· 上限 5400 秒 → ⑬b 用完整財報重算 → 收尾:
⑥e 抓完就沒有 ⑥e 那一項;⑬b 若仍黃(沒對上 / 口徑不明)單獨一項 → 看貼回包的 `VRN2_HistoryAlign_latest.json` 再決定(VRN-2 擷取 / 單位口徑 / 報告估計 vs 實際)。
畫面上只剩一條會動的進度列。
