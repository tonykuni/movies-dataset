# VRN-2 v0160 驗證紀錄(2026-10-31 · RoundAll v0116 · Handle-All v0108 · 套件 v0158 不動)

## 1. 起因

操作員在 **cmd 視窗**貼了 PowerShell 的行(`$env:VIA_SCRAPE_CONSENT = 'YES'` → `The filename, directory name, or volume label syntax is incorrect.` ·
最短一行 → `'$r' is not recognized`)· 並下令:「所有 PS / PY 檔案都要導入加速器 · VDF 及任何向外擷取資料的工具都要加入網路工具 · 貼到 PowerShell 上的指令也要加裝
相同加速模組及自動更新進度條及百分比 · 模板應該在加速器裡面 · 不卡斷 · 加速完成指令自動跳出 HTML U/I · 人機互動介面現代化專業感要足夠」。

## 2. 修法

| 檔 | 版 | 內容 |
|---|---|---|
| `VRN2_HandleAll_v0108.md` | v0108 | 載入 VIA 自己的 `supportive modules\VIA_PS_PyProgress_Module.ps1`(帶 `VIA_PS_Accel_Module.ps1` · 25 加速器)· RoundAll 經 `Invoke-VIAPython`(真百分比 · 經過 / 剩約 · 心跳 · 逾時保底 整輪 5 h / 其他 2 h · `VRN2_TIMEOUT_SEC`)· 模組不在 → 內建進度條 · Handle-All 步驟進度列(`Write-VIAProgress`)· RoundAll `--no-open` → 跑完這裡開收尾頁(`Microsoft.PowerShell.Management\Start-Process` · 不擋視窗 · `VRN2_NO_UI=1` 不開)· cmd 一行 |
| `VRN2_RoundAll_v0116.py` | v0116 | ①b 本行程點 VIA 加速器(套件的 `VIA_ExecutionBridge_v0103` · 核對工具鎖冊)· `[進度] n/N`(權重 · ④ 啟動器進度條換算 · ⑤ 逐項 · 子行程 `[進度]` 改標 `[子步驟]`)· 收尾頁新版面 · 問句整行先印 · `--launcher-args` 去外圍引號 · 自測 64 |

套件 `vrn2_release_v0158/VRN2_Closeout_v0158.zip` 不動(`dfca4f6b13fb`)。RoundAll v0116 `e518022ba4d0` · Handle-All 一行 `80cac6c34457` · 開機檔 `ae0cff82ebcc` · 最短一行 443 字元 · cmd 一行 1240 字元。

## 3. 測試

```text
[PASS] 60 [進度] n/N:依權重 · 這輪計畫外的步驟不算 · 同一行不重印 · 結束 = N/N · ④ 啟動器進度條(含色碼)換算進總進度 · 別的 n/N 不當進度
[PASS] 61 子行程的 [進度] 行改標 [子步驟] 才轉播(PowerShell 進度模板只認 RoundAll 的總進度)· 原行照收(NEXT / 燈號照判)· on_line 每行都收到
[PASS] 62 ①b 本行程點 VIA 加速器:套件的 ExecutionBridge 點亮 → 綠(加速器 · 鎖冊 · 執行緒)· 沒有橋 / 鎖冊 / 缺套件 / VRN2_NO_ACCEL=1 → 灰照跑 · 鎖冊對不上 → 黃 · 收尾頁 VCGC
[PASS] 63 收尾頁新版面:頂列狀態 + 主題切換(淺 / 深 / 跟系統)· 結案卡 · 燈號環圈(依綠黃紅灰比例)· 負責方堆疊條 · 流程每一步的燈 · 待辦空結果提示 · 檔案卡 · 複製提示框 · 可列印 · 單檔不連外 · 一個 script · 內容跳脫
[PASS] 64 --launcher-args 去外圍引號(PowerShell 傳進來的 "--no-install")· 舊資料庫問句整行先印再等輸入 · 收尾頁 json 帶每一步的燈(流程)
[PASS] VRN2_RoundAll v0116 --selftest · 64 項 · 不過 0
venv(有 PyMuPDF):[PASS] VRN2_RoundAll v0116 --selftest · 66 項 · 不過 0
pwsh 7.4.6 剖析錯 [0, 0, 0, 0, 0] · Handle-All 一行 = 可讀版 True · 開機行 = 可讀版 True
e2e 結束碼:report rc 0 · auto rc 0 · nomod rc 0 · full rc 0 · tmo rc 0 · tamper rc 0 · venv unchanged · 倉:e2e 沒寫任何檔(VCGC 自己的全景監看行程會寫它的冊 · 不提交 · 已還原)
```

VCGC 全景骨架卡(`CGC_MDL158 … read`):RoundAll v0116 報 10 項 SWALLOW,跟 v0115 一樣多(進度掛勾出錯改成「不再換算」,不是吞掉)。

## 4. 最短一行 e2e(桌機 v0153 狀態沙盒 · 倉的 VIA 網路工具 + VIA PS 加速器進度模組 · 沙盒 GitHub 分支 · pwsh 7.4.6 · 同意閘不設)

```text
[report] [GREEN] boot: Handle-All v0108 SHA-256 OK (claude/optimistic-goodall-yhalc5)
[report] [GREEN] ⓪ VIA 加速器進度模板 <sbx>/VIA/supportive modules/VIA_PS_PyProgress_Module.ps1(Invoke-VIAPython · 25 加速器 · 真百分比 · 經過 / 剩約 · 心跳 · 逾時不卡)
[report] [GRAY] ①b VIA 加速器 · 沒有套件裡的 VIA_ExecutionBridge_v0103.py(這輪沒取套件)· 不點 · 照跑(啟動器自己會點)
[report] [進度] 0/6 ⑥ 除錯報告
[report] [進度] 3/6 ⑧ 收尾頁
[report] [進度] 5/6 ⑦ 貼回包
[report] [進度] 6/6 完成 · 收尾 BLOCKED
[report] ===== 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 5 項等 VCGC 決定 / 安裝
[report]   [計] ⑧ 不是 Windows · 收尾頁自己開(上面那個檔)
[report] [計] Handle-All 結束 · RoundAll 結束碼 1 · 2 秒(視窗不會關)
[report] PYPROG={"name":"VRN2_RoundAll_v0116.py","d":6,"secs":0.39,"pct":100,"n":6}
[auto] [GREEN] boot: Handle-All v0108 SHA-256 OK (claude/optimistic-goodall-yhalc5)
[auto] [GREEN] ⓪ VIA 加速器進度模板 <sbx>/VIA/supportive modules/VIA_PS_PyProgress_Module.ps1(Invoke-VIAPython · 25 加速器 · 真百分比 · 經過 / 剩約 · 心跳 · 逾時不卡)
[auto] [進度] 0/19 ① 取套件
[auto] [GREEN] ①b VIA 加速器 · VeritasCeleritas_v1141.py · 鎖冊 accelerator=EXACT · network=EXACT · 執行緒 3 · 子行程照繼承
[auto] [進度] 3/19 ⑤ 自動修
[auto] [進度] 3/19 ⑤ 自動修 1/4 · 市場資料比歷史對齊新 / 歷史對齊沒跑 → 重跑 ⑬b
[auto] [進度] 5/19 ⑤ 自動修 2/4 · Combined 比市場 / 共識舊(或不在)→ 重組
[auto] [進度] 8/19 ⑤ 自動修 3/4 · ⑬ 增量庫補寫(本輪有修正)
[auto] [進度] 10/19 ⑤ 自動修 4/4 · Workbench 重渲染(最新收據)
[auto] [進度] 13/19 ⑥ 除錯報告
[auto] [進度] 16/19 ⑧ 收尾頁
[auto] [進度] 18/19 ⑦ 貼回包
[auto] [進度] 19/19 完成 · 收尾 BLOCKED
[auto] ===== 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 3 項等 VCGC 決定 / 安裝
[auto]   [計] ⑧ 不是 Windows · 收尾頁自己開(上面那個檔)
[auto] [計] Handle-All 結束 · RoundAll 結束碼 1 · 4 秒(視窗不會關)
[auto] PYPROG={"name":"VRN2_RoundAll_v0116.py","n":19,"d":19,"secs":3.678,"pct":100}
[nomod] [GREEN] boot: Handle-All v0108 SHA-256 OK (claude/optimistic-goodall-yhalc5)
[nomod] [YELLOW] ⓪ 找不到 VIA 加速器進度模板(<sbx>/VIA/supportive modules/VIA_PS_PyProgress_Module.ps1)· 改用內建進度條(一樣照 RoundAll 的 [進度] n/N 畫真百分比)
[nomod] [GREEN] ①b VIA 加速器 · VeritasCeleritas_v1141.py · 鎖冊 accelerator=EXACT · network=EXACT · 執行緒 3 · 子行程照繼承
[nomod] [進度] 0/6 ⑥ 除錯報告
[nomod] [進度] 3/6 ⑧ 收尾頁
[nomod] [進度] 5/6 ⑦ 貼回包
[nomod] [進度] 6/6 完成 · 收尾 BLOCKED
[nomod] ===== 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 3 項等 VCGC 決定 / 安裝
[nomod]   [計] ⑧ 不是 Windows · 收尾頁自己開(上面那個檔)
[nomod] [計] Handle-All 結束 · RoundAll 結束碼 1 · 1 秒(視窗不會關)
[nomod] PYPROG=null
[full] [GREEN] boot: Handle-All v0108 SHA-256 OK (claude/optimistic-goodall-yhalc5)
[full] [GREEN] ⓪ VIA 加速器進度模板 <sbx>/VIA/supportive modules/VIA_PS_PyProgress_Module.ps1(Invoke-VIAPython · 25 加速器 · 真百分比 · 經過 / 剩約 · 心跳 · 逾時不卡)
[full] [進度] 0/94 ① 取套件
[full] [GREEN] ①b VIA 加速器 · VeritasCeleritas_v1141.py · 鎖冊 accelerator=EXACT · network=EXACT · 執行緒 3 · 子行程照繼承
[full] [進度] 3/94 ② 診斷
[full] [進度] 8/94 ③ 全部自測
[full] [進度] 18/94 ④ 跑啟動器
[full] [進度] 18/94 ④ 啟動器 0% · ① CPU / DRAM 優化(第一步)
[full] [進度] 23/94 ④ 啟動器 9% · ② 定位 VRN-2 · 落地 VRN-2 SystemManager
[full] [進度] 28/94 ④ 啟動器 18% · ③ 環境檢查與補裝(序跑:補裝會動到套件 · 先做完別的步驟才匯入)
[full] [進度] 34/94 ④ 啟動器 27% · ④ 加速器覆蓋 100%(序跑:會出 v+1 檔 · 做完才掃描 / 編譯)
[full] [進度] 39/94 ④ 啟動器 36% · ④b 平行段(六個互不相連的步驟同時跑 · 動態排序)
[full] [進度] 45/94 ④ 啟動器 45% · ⑤ 元件登記(序跑:平行段寫完設定冊才掃)
[full] [進度] 51/94 ④ 啟動器 55% · ⑥ 啟動前快速測試(彙整平行段)
[full] [進度] 56/94 ④ 啟動器 64% · ⑦ 啟動 VRN-2 實測 → U/I
[full] [進度] 61/94 ④ 啟動器 73% · ⑧ 完成判定
[full] [進度] 67/94 ④ 啟動器 82% · ⑪ 獨立驗證(背景)· 寫回 U/I · 開 U/I
[full] [進度] 72/94 ④ 啟動器 91% · ⑫ PIVOT 資料庫(借用 VRN-1 的工具 · sha256 核對 · 只收 ⑪ 判對位的格)
[full] [進度] 78/94 ④ 啟動器 100% · 完成
[full] [進度] 78/94 ⑤ 自動修
[full] [進度] 88/94 ⑥ 除錯報告
[full] [進度] 91/94 ⑧ 收尾頁
[full] [進度] 93/94 ⑦ 貼回包
[full] [進度] 94/94 完成 · 收尾 BLOCKED
[full] ===== 收尾 · BLOCKED · 等 VCGC · VRN-2 側沒有待修 · 7 項等 VCGC 決定 / 安裝
[full]   [計] ⑧ 不是 Windows · 收尾頁自己開(上面那個檔)
[full] [計] Handle-All 結束 · RoundAll 結束碼 2 · 129 秒(視窗不會關)
[full] PYPROG={"secs":128.329,"name":"VRN2_RoundAll_v0116.py","n":94,"pct":100,"d":94}
[tmo] [GREEN] boot: Handle-All v0108 SHA-256 OK (claude/optimistic-goodall-yhalc5)
[tmo] [GREEN] ⓪ VIA 加速器進度模板 <sbx>/VIA/supportive modules/VIA_PS_PyProgress_Module.ps1(Invoke-VIAPython · 25 加速器 · 真百分比 · 經過 / 剩約 · 心跳 · 逾時不卡)
[tmo] [進度] 0/94 ① 取套件
[tmo] [GREEN] ①b VIA 加速器 · VeritasCeleritas_v1141.py · 鎖冊 accelerator=EXACT · network=EXACT · 執行緒 3 · 子行程照繼承
[tmo] [進度] 3/94 ② 診斷
[tmo] [進度] 8/94 ③ 全部自測
[tmo] [YELLOW] ⑥ RoundAll 逾 5 秒被停(不卡斷保底 · 只停它自己那棵行程樹)· 真的要更久:先貼 $env:VRN2_TIMEOUT_SEC = '28800' 再貼那一行
[tmo] [YELLOW] ⑦ 這輪沒有寫出收尾頁(<sbx>/VIA/VIA_Reports/vrn2/VRN2_CloseoutUI_latest.json)· 看上面 RoundAll 的最後幾行
[tmo] [計] Handle-All 結束 · RoundAll 結束碼 124 · 5 秒(視窗不會關)
[tmo] PYPROG={"pct":9,"name":"VRN2_RoundAll_v0116.py","d":94,"secs":4.692,"n":8}
[tamper] [RED] boot SHA-256 mismatch - not run
[tamper] PYPROG=null
```

- auto(repair)/ full:⓪ 綠(VIA 加速器進度模板)· ①b 綠(`VeritasCeleritas_v1141 · accelerator=EXACT · network=EXACT`)· full 的 `[進度]` 跟著啟動器 0 → 100% 走 · `VIA_PYPROG_LAST` = 100%。
- nomod(模組拿掉):⓪ 黃 · 內建進度條照 `[進度]` 畫。 tmo(`VRN2_TIMEOUT_SEC=5`):5 秒停 · 結束碼 124 · 視窗不卡。 tamper:開機檔被改 → 不執行。
- 沙盒收尾是 BLOCKED(沙盒自己的 VCGC 項 · 跟桌機不同)· 收尾頁在 Linux 印「不是 Windows · 自己開」。

## 5. 開頁代理與逾時(pwsh)

```text
[進度] 1/4 a
  [Invoke-VIAPython] 逾 2s 已停(不卡斷;只殺自己生的樹)。這是保底天花板,不是判它壞——
  真的需要更久:$env:VIA_PY_TIMEOUT_SEC=3600 後重跑;要完全不設限用 0(自負卡住風險)
timeout rc=124 secs=2
proxy:
  [VIA_NO_OPEN] 抑制跳出 ./page.html
qualified:
real cmdlet ran /bin/true
Cmdlet
```

VIA 的 `VIA_PS_Accel_Module.ps1` 在 `VIA_NO_OPEN=1` 時把 `Start-Process` / `Invoke-Item` 開 .html 的動作擋掉(桌機那行 `[VIA_NO_OPEN] 抑制跳出` 就是它)。
收尾頁是操作員指定要跳出的 VRN-2 自己的頁 → Handle-All 用模組全名呼叫真的 `Start-Process`,同時印出 VIA_NO_OPEN 的說明與 `VRN2_NO_UI=1` 關法(只開這一頁)。

## 6. 收尾頁 U/I

用桌機 05:41 貼回包的收尾資料、沙盒整輪的真收尾頁各渲染一次:Chromium 1440 / 390 寬 · 淺 / 深色 · 主題切換 · 負責方篩選 · 搜尋空結果 · 無主控台錯誤 · 無橫向捲動。

## 7. 桌機預期

PowerShell 7 視窗(`PS C:\…>`):新視窗先貼 `$env:VIA_SCRAPE_CONSENT = 'YES'` 再貼最短一行;cmd 視窗(`C:\…>`):`set VIA_SCRAPE_CONSENT=YES` 再貼 cmd 一行。
auto = repair → ⓪ 綠 · ①b 綠 · 兩條進度列 → **BLOCKED · VRN-2 0 · VCGC 1 · 人工 2 · 資料源 2**(⑥f 今天已經經網路工具抓過 · 不重抓)→ 收尾頁自動跳出(新版面)。
