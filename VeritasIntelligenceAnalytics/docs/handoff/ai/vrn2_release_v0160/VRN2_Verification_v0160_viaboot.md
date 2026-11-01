# VRN-2 v0160 驗證補記(2026-10-31 · 桌機 VIA 設定檔的 Set-VIABoot 情境)

桌機的 VIA PowerShell 設定檔(`Register-VIA-Commands` v0243 那一代)會定義 `Set-VIABoot`:`Invoke-VIAPython` 每次起 python 前呼叫它 →
`PYTHONPATH` 帶 `supportive modules\bootstrap`(VIA 的 `sitecustomize.py` · 啟動層加速器快取 · 中央入口身分)。v0160 的 e2e 用 `-NoProfile`,沒有這一層。
補跑:同一個沙盒(t160a)· 沙盒分支還原成沒被改的開機檔 · 定義跟 v0243 同形的 `Set-VIABoot`(只設 `VIA_ROOT` 與 `PYTHONPATH`)· auto(repair)。

```text
[GREEN] boot: Handle-All v0108 SHA-256 OK (claude/optimistic-goodall-yhalc5)
[GREEN] ⓪ VIA 加速器進度模板 <sbx>/VIA/supportive modules/VIA_PS_PyProgress_Module.ps1(Invoke-VIAPython · 25 加速器 · 真百分比 · 經過 / 剩約 · 心跳 · 逾時不卡)
[進度] 0/19 ① 取套件
[GREEN] ①b VIA 加速器 · VeritasCeleritas_v1141.py · 鎖冊 accelerator=EXACT · network=EXACT · 執行緒 3 · 子行程照繼承
[進度] 19/19 完成 · 收尾 BLOCKED
===== 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 5 項等 VCGC 決定 / 安裝
[計] Handle-All 結束 · RoundAll 結束碼 2 · 3 秒(視窗不會關)
PYPROG={"n":19,"d":19,"pct":100,"secs":2.152,"name":"VRN2_RoundAll_v0116.py"}
PYTHONPATH=<sbx>/VIA/supportive modules/bootstrap
```

結果:RoundAll v0116 在 VIA `sitecustomize` 底下照跑(沒有例外)· ①b 照點 · `[進度]` 0 → 19/19 · 收尾頁照寫。燈號跟前一次 auto 不同的列,
是沙盒狀態(中間跑過整輪,收據換成啟動器 v0158),不是 `sitecustomize` 造成。倉:沒寫任何檔。
