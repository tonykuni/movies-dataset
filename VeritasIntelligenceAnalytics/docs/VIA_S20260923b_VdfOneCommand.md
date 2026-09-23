# 側線 2026-09-23 b — 一個指令開 VDF:先問參數,再看資料庫

側線 2026-09-23;主線批號由併線的手指定 L25。

操作員令:「給我一個指令含進入環境一件開啟 VDF 的 POWERSHELL CODE 實測 · 應先跳出 HTML U/I 問我要不要改參數啟動 · 然後看到資料庫狀況」。

---

## 一 · 指令

**第一次**(先把這條分支拉進工作站那棵樹,再開;整行貼進任何 pwsh 7 視窗):

```powershell
$VIA = "C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics"; git -C $VIA pull --no-edit https://github.com/tonykuni/movies-dataset claude/busy-bell-97sa4f; . (Get-ChildItem "$VIA\Open-VIA-VDF-v*.ps1" | Sort-Object Name | Select-Object -Last 1).FullName
```

**之後每次**(任何 pwsh 7 視窗、任何資料夾):

```powershell
. (Get-ChildItem "$VIA\Open-VIA-VDF-v*.ps1" | Sort-Object Name | Select-Object -Last 1).FullName
```

- 這一行永遠開最新一版(今天是 `Open-VIA-VDF-v0101.ps1`;寫死版號也行,只是出新版要跟著改)。
- 最前面是**一個點、一個空白**(點源)。這樣短令冊才會留在這個視窗,跑完 `via-*` 照常能打。
  用 `&` 也能跑完四步,只是冊只活在腳本裡;沒有 `$PROFILE` 載冊的視窗,跑完會提醒你改用點源。
- 新開的視窗還沒有 `$VIA`:把 `$VIA` 換成完整路徑(上面第一次那一行已經設好)。
- 不想打字:在檔案總管雙擊 VIA 根的 `Open-VIA-VDF.cmd`。它開一個 pwsh 7 視窗點源同一支,跑完視窗留著。

---

## 二 · 會發生什麼

1. **進環境**:點源旁邊的 `Register-VIA-Commands` 尾版,`$VIA`、`via-*`、家族境 python 在這個視窗生效。
2. **跳出「VDF 一鍵啟動」頁**:
   - 參數:起始年、每道上限檔數(0 = 全市場)、只看計畫、不做倉庫自癒。預設值讀自啟動器本身,不另寫一份。
   - 啟動就緒:家族境 python、兩道同意閘(只讀)、視窗限量、下一步。
   - 啟動前的資料庫狀況:目錄時間、分類燈、增量缺口。
   - 三個按鈕:「用預設參數啟動」「用上面的參數啟動」「不啟動」。
3. **跑**:照你按的呼叫 `Invoke-VIA-VdfFetch` 尾版,進度印在 PowerShell 視窗。
4. **跳出「VDF 資料庫狀況」頁**:先重點資料庫目錄,再排出分類燈、增量缺口與逐表清單。

兩頁都由短令冊的 `via-open` 開:它直接叫瀏覽器 exe(Edge / Chrome / Firefox),不經 `.html` 預設程式(你的機器上是 VS Code)。

加 `-NoUi` 就不開問參數頁,直接用預設跑(給排程);第 ④ 步照做,但頁只落檔不跳。加 `-NoStatus` 跑完不做第 ④ 步。

---

## 三 · 安全與界線

- 問參數頁只綁 `127.0.0.1`,每次一把一次性權杖;只收同一頁送出的決定,每一欄都驗證,不認得的欄位直接拒絕。
- **同意閘本指令不碰**。擷取車道(CGC_MDL134)在自己的子行程開閘,所以不用你先開;直呼 `via-price` / `via-chip` 才要你在視窗開閘二。
- **零跳出律照舊**:短令冊載入就設 `VIA_NO_OPEN=1`,Python 的 `webbrowser` 一律不開。這一令是你親手打的,打了就該跳(批474 B:分界線是誰要求的),所以由 `via-open` 開,不繞過閘也不改閘。
- 頁面零 CDN、零外部資源,淺色深色都能看。
- 分類燈與門檻、缺口與哨兵、目錄新鮮度,各由 CGC_MDL153、VDF_ENG089、CGC_MDL123 算,本頁只排版。

---

## 四 · 實測

| 項 | 結果 |
|---|---|
| 引擎自測 VDF_ENG093 v0100 | 9/9;回送介面不在時 6 綠、⑤⑨ 誠實 NODATA |
| 自測 ⑨:照 Invoke-VIAPython 的樣子跑(stdout 導到檔、拿掉 `PYTHONUNBUFFERED`) | 網址行在還沒決定之前就落檔;送「不啟動」→ 200、rc 0、決定檔 cancel |
| 突變測:拿掉那兩個 `flush` | ⑨ 轉紅(網址沒落檔、等到逾時)。證明 ⑨ 抓得到這個錯 |
| 照工作站緩衝跑的真瀏覽器(無頭 Chromium)三條路 | 「用上面的參數啟動」2024 / 100 / 只看計畫 → 決定檔完全相同;「用預設參數啟動」即使頁上亂填 1999 仍回 2023 / 全市場;「不啟動」回 cancel;錯權杖 403;按下後按鈕鎖住 |
| 資料庫狀況頁(合成目錄,10 張表) | 分類燈、增量缺口、逐表都在;零外部資源;rc 2(資料落後,不是壞掉);「頁:」那一行用一鍵腳本同一條正則取得到,路徑存在 |
| 模板章稽核(兩支新 .ps1) | joined · restore · requires7 全到 · verdict pass |
| 格子 | 一鍵啟動台自測 OK;資料庫狀況頁在容器 SKIP(容器沒有目錄,rc 3 = 環境缺件);你的機器上有目錄就會是 OK |
| PowerShell 括號絆線(容器沒有 pwsh 的替代:跳過註解、各種字串、here-string、`$(...)`) | 工作站 pwsh 真跑過的 v0100 · v0105 · 短令冊 v0242 全 OK;兩個負控(少一個 `}`、多一個 `(`)都抓到;v0101 · v0106 OK |
| VCGC · 契約 · SSOT 驗收(第一輪;第七節有最新一輪) | 36/36 · 19/19 · PASS(正則清冊 1282 條,交正主 CGC_MDL115 重建) |

**沒實測到的一件**:容器沒有 pwsh,`Open-VIA-VDF-v0100.ps1` 與 `Open-VIA-VDF.cmd` 在這裡沒真跑過(Z139)。
它們很薄:點源短令冊、呼叫上面測過的引擎、把網址交給 `via-open`、呼叫既有的啟動器。你第一次跑就是它的實測;貼回最後一行 `=== [Open-VIA-VDF] 畢 …`。

---

## 五 · 出貨前自己抓到的四件事(已修,Z140)

1. **網址行沒 flush**:在 Invoke-VIAPython 底下 stdout 導到暫存檔(區塊緩衝),網址要等行程結束才落檔。
   結果是頁不跳、視窗也看不到網址,要等滿 15 分鐘。容器設了 `PYTHONUNBUFFERED=1`,第一輪真瀏覽器測試因此誤綠。
2. **零跳出閘擋掉開頁**:`VIA_NO_OPEN=1` 讓 `webbrowser.open` 對 http 網址也靜默不開;`.html` 交給預設程式又會開成 VS Code。改走 `via-open`。
3. **`&` 跑完短令冊不留**:`via-*` 是 `function global:`,留得下;它們靠的 `Invoke-VIAPython` 是一般 function,跟著腳本消失。
   雙擊 `.cmd`(`-NoProfile`)後 `via-*` 會找不到它。改成點源,`.cmd` 也改點源。
4. **撞族名**:`functional modules/VDF` 已有 `Start-VIA-VDF-v0101`~`v0104`(加速器導入 + 工作台啟動),`Invoke-VIA-TrinityClosure` 用尾版 glob 取它。
   新檔若叫 `Start-VIA-VDF-v0100` 會像那一族的舊版(L04),所以另立一族 `Open-VIA-VDF`。全部遠端分支掃過,沒有同名。

---

## 六 · 工作站第一次實跑(2026-09-23)→ v0101

你貼回的畫面:
- 網址行即時到(flush 修對了),`via-open` 叫起 msedge 開了問參數頁;引擎停在「等你按」(257 秒)。
- **模板章首載就炸**(掉球 Z137 實證):`無法擷取變數 '$script:CeleritasPS7'，因為它尚未設定`。
  正主 `supportive modules/ps7/VeritasCeleritas.PS7.ps1` 第 18 行開 StrictMode,第 24 行就讀還沒設的變數;快照還讀 `$OFS`(預設不存在)與
  `$PSNativeCommandArgumentPassing`(7.3 起才有)。正主自己的 `VeritasCeleritas.PS7.Template.ps1` 走同一條路,同樣會炸。
- 「正主第一個錯」印成了最後一個錯(`$Error[0]`)。

修法(只動本側線自己的檔;正主是 Celeritas 線的,留提案):
- `Open-VIA-VDF-v0101.ps1` 與 `Invoke-VIA-VdfFetch-v0106.ps1`(v0100 / v0105 留作版史)換同一段載法:
  1. 先在模組 scope 設好那三個變數。
  2. `-RestoreOnly` 只載函式,不自動起跑。
  3. 先試拍快照,拍不到就不起跑。
  4. 起跑,驗「已套且有快照」;沒套上就依快照還原。
  5. 錯誤不噴紅字,印真正的第一個。
- `Open-VIA-VDF-v0101.ps1` 起跑後整段包 try/finally:按 Ctrl+C 也還原。
- 頁交給瀏覽器之後多印一行:沒跳到最前面就點工作列的瀏覽器。

v0101 起模板章第一次真的套上:跑的時候本行程優先權 AboveNormal、本執行緒文化 Invariant、主控台 UTF-8、進度條 Minimal。
跑完、Ctrl+C、關窗都依快照還原;只動這個行程。

給 Celeritas 線的正主修法(三行;改 .ps1 要 L70 許可):

```powershell
# 第 24 行
if ($null -eq (Get-Variable -Name CeleritasPS7 -Scope Script -ValueOnly -ErrorAction SilentlyContinue)) {
# Get-CeleritasSnapshot 裡的兩個鍵
OFS               = (Get-Variable -Name OFS -ValueOnly -ErrorAction SilentlyContinue)
NativeArgs        = (Get-Variable -Name PSNativeCommandArgumentPassing -ValueOnly -ErrorAction SilentlyContinue)
```

下一次跑請貼回兩行:`[Celeritas] …`(應為「本行程減壓已套」)與最後一行 `=== [Open-VIA-VDF] 畢 …`。

---

## 七 · 問參數頁改版 · 逐一引擎測修 · 最高政策(2026-09-23 晚)

你看過頁之後的令:「每道上限檔數刪除 · 要抓就全抓 · 導入網路工具 · 起始日期 YYYY-MM-DD · 截止日期自動帶入今天 · 方便打勾方格自動 ·
逐一引擎邊測邊修正到成功 · 並將輸入參數(要找的資料)用大矩陣顯示出來完整」「PY 檔都要導入加速器 · VDF 都要導入網路工具 · PS 都要導入模板工具 列為最高政策」「自測自修正再測再修正直到成功」。

**問參數頁(VDF_ENG093 v0101)**
- 檔數上限欄拿掉了:全市場全抓。有人硬送 `limit` 會被拒,並講明「要抓就全抓」。
- 起始日期直接打 `YYYY-MM-DD`,或按右邊日曆挑;截止日期自動帶入今天(各引擎一律抓到最新,不收別的值)。
- **要抓的資料矩陣**:11 步一列一列,打勾方格預設全勾,有「全選 / 全不選」。每一列寫清楚:
  - 要抓的資料、跑哪支引擎尾版、實際帶的參數(藍底隨起始日變);
  - 觸網與否、網路工具橋、加速器橋、在哪條鏈、等哪幾步、逾時秒數。
  - 步冊委派 CGC_MDL125,鏈委派 CGC_MDL134,步清單讀自啟動器;本頁一條規則都不自己寫。
- **逐一引擎自測**:頁上一鍵,背景一支一支跑 `--selftest`,每列填上燈號、rc、秒數、最後一行。
  子行程拿掉同意閘變數,只寫暫存;跑的時候不收「啟動」,跑完才收。
- 按「用下面勾的啟動」→ 決定檔帶 `since · until · steps · dry · noheal`。

**啟動器**
- `Invoke-VIA-VdfFetch-v0107.ps1`:+`-Since YYYY-MM-DD`(蓋過 -Year)、+`-Steps a,b,c`(只跑勾的步,照步清單順序),在 ⑤ 一起驗,錯了什麼都還沒做就停。
- `Open-VIA-VDF-v0102.ps1`:照決定檔送 `-Since -Steps -Dry -NoHeal`,永不送 `-Limit`;狀況頁多帶本次決定。
- 狀況頁多兩張卡:「本次輸入參數」與「各步結果」。
  - 各步結果取 CGC_MDL134 最近一次非 PLAN 報告;紅步附紀錄檔路徑,主控台也逐步印出非綠的步。
  - 報告若比本次決定早,會講明「是上一次的」,不冒充這一次。

**逐一引擎測修(容器,離線)**

| 步 | 引擎尾版 | 自測 | 加速器橋 | 網路工具橋 | 這次修了什麼 |
|---|---|---|---|---|---|
| datahome | CGC_MDL123_DataHome_v0103 | 13/13 | ✓ | 不觸網(CGC 件,不在 L69 範圍) | — |
| hist_2023 | VDF_ENG064_HistoryBackfill_v0112 | 10/10 | ✓ | ✓ | — |
| global | VDF_ENG066_GlobalUniverse_v0102 | 8/8 | ✓ | ✓ | — |
| fred | VDF_ENG074_FredMacroSSOT_v0102 | 17/17 | ✓ | ✓ | — |
| revenue_backfill | VDF_ENG075_MonthlyRevenueBackfill_v0102 | 10/10 | ✓ | ✓ | — |
| etf_universe | VDF_ENG077_ActiveETFUniverse_v0100 | 8/8 | ✓ | ✓ | — |
| etf_fetch | VDF_ENG051_ActiveTWETF_Holdings_**v0103** | 27/27 | ✓ | ✓ | v0102 只認 `--self-test`,打 `--selftest` 被 argparse 拒 → 加別名(L56 ①) |
| etf_history | VDF_ENG078_ActiveETFHoldingsHistory_v0109 | 29/29 | ✓ | ✓ | — |
| consensus | VRN_ENG071_CnyesFusion_**v0101** | 9/9 | ✓ | ✓ | 網路本來就走統包 SUP_MDL740,只缺標準橋 → 正主 via_bridge_sweeper 掛上 |
| revenue_consensus | VDF_ENG069_RevenueConsensusAnalysis_v0108 | 3/3 | ✓ | ✓ | — |
| etf_revenue | VDF_ENG076_ETFRevenueMomentum_v0101 | 8/8 | ✓ | ✓ | — |

同一張表在問參數頁上按「逐一引擎自測」會再跑一次:容器實跑 11/11 綠。真的觸網抓資料要在你的機器上跑(同意閘是你的手)。

**最高政策(L103,法典 `VIA_Policy_Laws_SSOT_v0100.json`)**
- 三條:PY 導入加速器 · VDF 導入網路工具 · PS 導入模板工具。
- 實量:
  - PY:正主 via_accel_injector 全樹 2607 支補 1 支,就是原掉球 Z138 那支測試檔;格子「Celeritas 產出契約實跑」轉綠。
  - VDF:CGC_MDL156 量到 VDF 活件 72 全掛、生呼叫 0,擷取鏈裡的 VRN_ENG071 也掛上了。
  - PS:新產出全接;既有 838 支升為最高政策的欠帳。改 `.ps1` 仍要你逐批許可(L70),而且要先看到 Z137 的「已套」。
- **排序待你確認**:我照你的原話把 L103 排 rank 1,批618 的 L50「第一條」(TA-Lib)順延 rank 2,L102 順延 rank 3。
  要 L50 仍居首,兩處對調即可,全樹沒有程式依賴 rank 值。

**實測**
- VDF_ENG093 v0101 自測 12/12,突變測(收 limit、拿掉自測鎖)都轉紅。
- 無頭 Chromium 照工作站緩衝跑了三條路:
  - 自訂:改日 2024-03-15、全不選、勾兩步 → 決定檔完全相同。
  - 逐一引擎自測 11/11 綠,跑時啟動鈕鎖住,跑完用預設啟動。
  - 不啟動;錯權杖 403。
- 啟動器:兩支新 `.ps1` 模板章稽核 pass、括號絆線 OK。
  - 審 diff 時抓到一個 pwsh 才會露的錯:PowerShell 變數不分大小寫,步清單叫 `$steps` 會蓋掉新參數 `-Steps`,所以改名 `$stepBook`。
- 其餘:VCGC 36/36 · 門 31/31 · 門單元測 34/34 · 元件冊同步(新 14)· 正則清冊交正主重建 1284 條 · SSOT 驗收 PASS。
  格子一鍵啟動台與 Celeritas 三站都綠;本 PR 的 CI 在容器照步驟全過。

---

## 八 · 還原

刪掉 `Open-VIA-VDF-v0100.ps1`~`v0102.ps1`、`Invoke-VIA-VdfFetch-v0106.ps1` 與 `v0107.ps1`(短令冊自動退回 v0105)、`VDF_ENG093_LaunchConsole_v0101.py`、`VDF_ENG051_ActiveTWETF_Holdings_v0103.py`、`VRN_ENG071_CnyesFusion_v0101.py`、`Open-VIA-VDF.cmd`、`functional modules/VDF/VDF_ENG093_LaunchConsole_v0100.py`。既有檔一支都沒動。
