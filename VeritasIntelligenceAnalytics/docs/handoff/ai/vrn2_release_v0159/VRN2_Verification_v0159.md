# VRN-2 v0159 驗證紀錄(2026-10-31 · RoundAll v0115 · Handle-All v0107 · 套件 v0158 不動)

## 1. 起因

桌機 05:30(Handle-All v0106 repair · 同意閘兩道都開)第一次經 VIA 網路工具真抓共識成功(⑥f GREEN · 收尾 BLOCKED · VRN-2 0 · 人工 2)。
同一輪 ⑥e 用 `C:\Python313`(合 VDF 版本界線 · MarketFetchRun 挑的),⑥f 卻用 `envs\via_core_312`(RoundAll ② 只看套件匯得進來就選 · 舊 pandas)→
引擎 `Raw Parquet: WARN_PARQUET_ENGINE_UNAVAILABLE`。操作員:「繼續下一步,依照你的建議進行」→ ⑥e / ⑥f 用同一個擷取 Python。

## 2. 修法(RoundAll v0115 · SHA-256 `92ea3b3e4b1f`)

`bounds_fetch_python()`:給啟動器(④)與 ⑤ 重跑 ⑥f 的 `VIA_FETCH_PY` →
① ② 挑到合 VDF 版本界線的(同 ⑥e)· ② 沒跑(repair)→ 上一輪啟動器 ⑥e 收據記的(還在 · 匯入檢查齊)· ③ 都沒有 → 照舊只看匯入的第一支。④ / ⑤ 印用了哪支、為什麼。
套件 `vrn2_release_v0158/VRN2_Closeout_v0158.zip` 不動(雜湊照釘 `dfca4f6b13fb`)。Handle-All v0107 指向 RoundAll v0115(原始碼從 v0106 md 的可讀版還原 · 重接後跟發行的那一行逐字相同)。

## 3. 測試

```text
[PASS] 59 ⑥e / ⑥f 同一個擷取 Python:合 VDF 版本界線的優先(桌機 ⑥f 用 via_core_312 · Raw Parquet WARN)· repair 沒跑 ② → 上一輪 ⑥e 收據的(匯入齊)· 不齊 / 不在 → 只看匯入的
[PASS] VRN2_RoundAll v0115 --selftest · 59 項 · 不過 0
pwsh 7.4.6 剖析錯 [0, 0, 0, 0, 0] · Handle-All 一行 = 可讀版 True · 開機行 = 可讀版 True
e2e 結束碼:report rc 0 · repair rc 0 · tamper rc 0
```

## 4. 最短一行 e2e(小沙盒 · 沙盒 GitHub 分支 · pwsh 7.4.6 · 同意閘不設)

```text
[report] [GREEN] boot: Handle-All v0107 SHA-256 OK (claude/optimistic-goodall-yhalc5)
[report] [VRN-2] Handle-All v0107 · PowerShell 7.4.6 · 模式 report · VIA <sbx>/VIA
[report] [YELLOW] ④ 模式 report 要上一輪的輸出冊 · 這裡沒有 → 改跑整輪
[report] [GREEN] ⑤ VRN2_RoundAll_v0115.py SHA-256 92ea3b3e4b1f 相符(GitHub claude/optimistic-goodall-yhalc5)→ <sbx>/home/Downloads/VRN2_RoundAll_v0115.py
[report] ══════ VRN2_RoundAll v0115 · 2026-10-31 03:40:36 · Python 3.13.16 · package → preflight → selftest → run → fix → report → closeout → pasteback ══════
[report] [RED] ⓪ VIA 根 · 找不到(查過:--root · <sbx>/VIA · 不是 | VRN2_ROOT · <sbx>/VIA · 不是 | VIA_ROOT · <sbx>/VIA · 不是 | 預設位置 · <sbx>/home/OneDrive/Documents/movies-dataset/VeritasIntelligenceAnalytics · 不是 | 預設位置 ·
[report]   [RED] ⓪ VIA 根 · 找不到(查過:--root · <sbx>/VIA · 不是 | VRN2_ROOT · <sbx>/VIA · 不是 | VIA_ROOT · <sbx>/VIA · 不是 | 預設位置 · /home/user/
[report] [計] Handle-All 結束 · RoundAll 結束碼 1 · 4 秒(視窗不會關)
[repair] [GREEN] boot: Handle-All v0107 SHA-256 OK (claude/optimistic-goodall-yhalc5)
[repair] [VRN-2] Handle-All v0107 · PowerShell 7.4.6 · 模式 repair · VIA <sbx>/VIA
[repair] [GREEN] ⑤ VRN2_RoundAll_v0115.py SHA-256 92ea3b3e4b1f 相符(GitHub claude/optimistic-goodall-yhalc5)→ <sbx>/home/Downloads/VRN2_RoundAll_v0115.py
[repair] ══════ VRN2_RoundAll v0115 · 2026-10-31 03:40:41 · Python 3.13.16 · package → preflight → selftest → run → fix → report → closeout → pasteback ══════
[repair] [RED] ⓪ VIA 根 · 找不到(查過:--root · <sbx>/VIA · 不是 | VRN2_ROOT · <sbx>/VIA · 不是 | VIA_ROOT · <sbx>/VIA · 不是 | 預設位置 · <sbx>/home/OneDrive/Documents/movies-dataset/VeritasIntelligenceAnalytics · 不是 | 預設位置 ·
[repair]   [RED] ⓪ VIA 根 · 找不到(查過:--root · <sbx>/VIA · 不是 | VRN2_ROOT · <sbx>/VIA · 不是 | VIA_ROOT · <sbx>/VIA · 不是 | 預設位置 · /home/user/
[repair] [計] Handle-All 結束 · RoundAll 結束碼 1 · 1 秒(視窗不會關)
[tamper] [RED] boot SHA-256 mismatch - not run
```

沙盒不是 VIA 根(只驗雜湊鏈):最短一行 → 開機行 SHA-256 → Handle-All v0107 → RoundAll v0115 SHA-256 都相符 · 開機檔被改 → 不執行。
**沒跑到的**:桌機狀態的 repair(容器裡原本的桌機狀態沙盒在已失效的 scratchpad · 貼回包只有 CSV 冊)→ 擷取 Python 的選法由自測 59 的三種情況把關。

## 5. 桌機預期

貼 `VRN2_HandleAll_v0107.md` 最上面那行(新視窗先設 `$env:VIA_SCRAPE_CONSENT = 'YES'`):repair → ⑤ 印 `擷取 Python(⑥e / ⑥f)C:\Python313\python.exe · 上一輪 ⑥e 用的(合 VDF 版本界線)`
→ ⑥f 已是今天經網路工具抓的 → 不重抓 → **BLOCKED · VRN-2 0 · VCGC 1 · 人工 2 · 資料源 2**。整輪(`$env:VRN2_MODE = 'full'`)④ 印 `… · 合 VDF 版本界線(② · 同 ⑥e)`,⑥f 引擎不再 WARN Raw Parquet。
