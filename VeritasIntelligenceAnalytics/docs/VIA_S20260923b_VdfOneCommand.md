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
| VCGC · 契約 · SSOT 驗收 | 36/36 · 19/19 · PASS(正則清冊 1282 條,交正主 CGC_MDL115 重建) |

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

## 七 · 還原

刪掉 `Open-VIA-VDF-v0100.ps1`、`Open-VIA-VDF-v0101.ps1`、`Invoke-VIA-VdfFetch-v0106.ps1`(短令冊自動退回 v0105)、`Open-VIA-VDF.cmd`、`functional modules/VDF/VDF_ENG093_LaunchConsole_v0100.py`。既有檔一支都沒動。
