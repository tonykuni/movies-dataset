# 側線 2026-09-23 — VDF 更新狀況 · 三支上傳引擎治理版 · VCGC 第四扇門(SSOT 正則·同義字連動)

側線 2026-09-23;主線批號由併線的手指定 L25。基底 main `03b4f256`(PR #91,批725–726)。

操作員令(依序):

1. 「自 session 更新 VDF」「更新狀況」
2. 「自動實測自動修正自動完成」(附 MDL002 / MDL003 / MDL006 三支上傳檔)
3. 「SSOT REGEX 同義字等與 VCGC 相連自動規劃檢查更新 · 實測自測自完工 · 結果驗證」
4. 「善用 VCGC 工具節省 TOKEN」

---

## 一 · 現況

- **VDF 可以啟動**。工作站 09-21 兩次實錄裡「看起來卡住」的地方,五個根因都量到了,四個已由新版處理,一個要操作員裁定(閘二的尺)。
- **三支上傳引擎**已成治理版 v0100:閘沒開回 rc4、零出網零寫檔;沒料回 rc2,不再印「完成」。
- **VCGC 現在看得到、也管得到 SSOT 正則與同義字層**:`via-vcgc ssot` 檢、`ssot plan` 規劃、`ssot plan -Apply` 交正主更新、`ssot verify` 驗收。
  今天實跑:正則清冊落後 7 條樣式,交正主重建後驗收 PASS。

---

## 二 · 工作站 09-21 為什麼看起來卡住

| 症狀(工作站實錄) | 根因 | 處理 | 你的手 |
|---|---|---|---|
| `via-vdfinc plan` 兩次都報 56 個缺口,抓完也不變 | 計畫讀的是**快取目錄**,目錄沒重建;而且不說目錄幾分鐘前產的 | ENG089 v0101:先印目錄時間與年齡,過期標 `[過期]` 並回 rc2;紀錄表(`ts` 欄)不算缺口;1900-01-01 哨兵列另列 | 抓完先 `via-datahome catalog` 再 `via-vdfinc plan` |
| 第二次 `via-vdffetch` 仍只抓 100 | Invoke v0104 寫了 `$env:VIA_HIST_LIMIT`,Register v0242 第 363 行在沒給 `--limit` 時讀回 → **黏住** | 對接口 v0104 量出來並印清除那一行;每個出口都還原的 Invoke v0105 **只做成提案**(見第六段,未出貨) | 本視窗 `$env:VIA_HIST_LIMIT=''`;許可後才出 v0105 與改 Register 那一行(Z127) |
| `via-price ; via-chip` → `[FAIL-CLOSED] 同意閘未開` | 閘二有三把尺:13 支引擎認字面 `YES`;統包把 Register 預設的 `OFF` 算「已設」;車道在子行程強設 YES,直呼不會 | 對接口 v0104 `launch` 逐把量,印直呼前要打的那一行 | 直呼前本視窗 `$env:VIA_SCRAPE_CONSENT='YES'`;長期要裁一把尺(掉球 Z120) |
| `launch.ps1` 不認得 | PowerShell 執行目前資料夾的腳本要帶 `.\` | 對接口下一步卡改印 `.\launch.ps1` | 打 `.\launch.ps1` |
| 調整後價格層/因子庫沒跟著更新 | 車道不建 ENG060/ENG061,只有開機鏈 ②b ②c 建 | 下一步卡印明 | 需要時跑開機鏈(掉球 Z122) |

---

## 三 · 三支上傳引擎:實測 → 修 → 驗

上傳檔與主線批716 收容件**逐位元相同**(sha256 前八碼 e5dbb168 / cb9c413e / 3da0113e);樹上副本是超集,上傳獨有定義 0。要做的不是併,是讓它們真的能跑、而且講真話。

| 引擎 | 原件實測(容器斷網、閘未設) | v0100 修了什麼 | 驗 |
|---|---|---|---|
| VDF_MDL002 yfinance 全宇宙 | 不看同意閘就出網;沒料回 rc1;缺件會 `pip install` | 閘關 rc4 · **逐代號增量**(原件逐日判缺:台股先落地的那天,美股晚收盤的列永遠存不進來)· 零新列 rc2 且不重存舊料 · 失敗代號記名 · 不代裝套件 rc3 · `--help`/未知旗標不觸網 · 結尾等 Enter 只在互動終端 · `pct_change` 明寫前補(pandas 3 行為變了)· 6415 改 `6415.TW`(樹上台股名冊記 TWSE) | 自測 ⑦–⑩;假 yfinance 端到端三跑:首抓 rc0 → 晚收盤那一天補回 rc0 → 零新列 rc2 且檔未改寫 |
| VDF_MDL003 情緒總經 | 不看閘就出網;FRED 鑰整串印出;季資料 YoY 期數錯 | 閘關 rc4 · 鑰只印末四碼 · YoY 依頻率取期數 · CNN 帶 Referer · AAII `.xls` 引擎 | 自測 ⑦;合成季資料 YoY=4.0、月資料有缺 YoY=10.0 |
| VDF_MDL006 財務模型(批182 封存那支復役) | 沒有 `--selftest`,旗標被略過整條真跑;斷網時報 ok=3、七張表 0 列、rc0 | 閘關 rc4 · 有料才算 ok · 三表依期末日對期 · 季表真年增 + 另給季增 · 殖利率單位(Yahoo 已回百分數,原件再 ×100)· 報表幣別≠報價幣別時跨幣欄留空 · `--tickers` 依台股名冊定 `.TW`/`.TWO` · 補 L53 自測 | 自測 ⑦–⑭ 13/13(選配套件缺=NODATA);假 yfinance 端到端:3324→`3324.TWO`、ROE 缺表那年留空、季年增 100% 季增 53.8%、殖利率 1.25% 不是 125%、TSM 跨幣欄留空 |

三支的出網仍是閘後直呼(同 MDL004 v0100 先例),改走統包是掉球 Z123。與現役引擎的重疊(FRED→ENG074、CNN→ENG055、三表→ENG082 等)記在 Z124/Z125,裁定權在操作員。

---

## 四 · VCGC 第四扇門:SSOT 正則 · 同義字連動

**之前**:VCGC 只看得到一盞 SSOT 燈,而且那盞燈是經 VRN 系統管理轉來的「聯集冊在不在」——冊在就綠,從來不跑缺項、漂移或衝突檢。VCGC 沒有任何動詞能檢查或更新這一層。

**之後(VCGC v0126)**:逐格委派正主,本台不編一條正則、不併一個同義字。

| 格 | 正主 | 今天實量 |
|---|---|---|
| 規則樞紐狀態 / 跨冊衝突 | SUP_MDL749 | 綠;衝突紅 0 |
| 下游落差 | SUP_MDL749 drift | 黃:2 支(TW02 報告解析器、首頁全能引擎) |
| 同詞多義 | SUP_MDL749 additive | 黃:10 條,按來源可判,**你裁** |
| 增補橋 | VRN_ENG088 | 綠;收容件漂移 8 列(黃,只攤開) |
| 同義聯集冊 | CGC_MDL176 | 綠:缺 0 條 |
| 拒絕閘覆蓋 | CGC_MDL176 | 黃:讀券商冊還沒過閘 27 支(舊債 Z101) |
| 全冊編譯 | CGC_MDL169 | 綠:9 本冊 regex 全編得過 |
| 正則清冊(深檢) | CGC_MDL115 | 實跑前 **STALE**(1269 → 1276 樣式);交正主重建後綠 |
| 陸券清除驗收(深檢) | CGC_MDL177 | 綠:殘留 0 |

跑法(`via-vcgc` 參數原樣轉交,不用改 Register):

```powershell
via-vcgc ssot                 # 檢:只讀零寫;黃=待你裁定
via-vcgc ssot plan            # 規劃:哪幾步能交正主自動做、哪幾條要你裁;零寫
via-vcgc ssot plan -Apply     # 只把能自動的那幾步交正主做,做完自動重量
via-vcgc ssot verify          # 驗收(含深檢):自動那一半到位 = rc0;黃不擋
```

「自動」落在三處:`via-vcgc status` 每跑一次就帶一行 SSOT 連動;一頁交接第十五段;格子三站實跑(`ssot`、`ssot plan`、`ssot verify`)。
格子**不掛** `-Apply`:寫冊是正主的事,由你下令。

正則清冊只升不降:較新 python 產的冊讀得動 3.12 語法的檔,本境較舊就不比、不重建,容器(3.11)與工作站(3.13)不會來回覆寫。

---

## 五 · 驗證(容器;網路命名空間隔離、同意閘未設)

| 項 | 結果 |
|---|---|
| VCGC v0126 自測 | 35/35 |
| VDF 子系統管理對接口 v0104 自測 | 31/31 |
| 增量擷取閘 ENG089 v0101 自測 | 19/19 |
| MDL002 / 003 / 006 自測 | 3.11 rc2(選配套件缺,不是紅)· 3.12 與 3.13 rc0 |
| 單元測試 test_vdf_system_manager_v0103 | 34/34 |
| SSOT 增補單元測試 | 20/20 |
| MasterControl 契約測試 | 19/19 |
| 治理完整度自指閘(CGC_MDL164 selfref) | 基線外 0 |
| `via-vcgc ssot verify` | PASS(綠 7 · 黃 4 待裁定) |
| Celeritas 產出契約閘(L102) | 撤回 v0105 後基線外新缺 0(見第六段) |
| 格子逐站(新改 16 站) | OK 15 · SKIP 1(啟動就緒要工作站家族境) |
| 全格子 350 站 | OK 325 · FAIL 12 · SKIP 13 · TIMEOUT 0(815 秒;平行段撞到單寫者庫的站,序跑複判過) |
| 12 紅逐站複驗 | **每一站在 main 原碼也紅**(乾淨 main,或 main 原碼跑同一份本地料):工具升階梯 · 治理台 UI Matrix · 首頁文字擷取 · VRN 六層鏈廿五檢與實跑 · VRN 統一報告引擎 · U/I 畫面統一閘 · 研報欄位規格實跑 · CGC_MDL120/143/144 · 系統 API 三態。本側線新增的紅 0 |

---

## 六 · L70 旗標:只有提案,沒有出貨的 .ps1

本側線**沒有新增或修改任何 .ps1**。啟動器還原版 v0105 原本做好了,格子的 Celeritas 產出契約閘(L102,批715)當場點名它沒接模板章;
用正主 `xps_join` 接上又會把整支包進一個 scriptblock:`param()` 不再是腳本參數(`-Year` / `-Limit` 綁不上)、點源進環境的函式被關在裡面。
兩件事都指向同一個結論:新 .ps1 是你的手(L70),而且接模板章要先有適合啟動器的接法(Z136)。所以撤回,改成下面這份提案。

許可後的做法:照這份差異出 `Invoke-VIA-VdfFetch-v0105.ps1`(舊版 v0104 零觸碰),接上模板章後,格子的 Celeritas 兩站要轉綠;還原=刪掉 v0105,尾版律退回 v0104。

```diff
--- Invoke-VIA-VdfFetch-v0104.ps1
+++ Invoke-VIA-VdfFetch-v0105.ps1
@@ -1,5 +1,11 @@
 # =====================================================================
-# Invoke-VIA-VdfFetch-v0104.ps1 — 單一 PowerShell 啟動 VDF 擷取(含進入環境+倉庫自癒)
+# Invoke-VIA-VdfFetch-v0105.ps1 — 單一 PowerShell 啟動 VDF 擷取(含進入環境+倉庫自癒)
+# v0104→v0105(側線 2026-09-23;主線批號由併線的手指定 L25;操作員「更新 VDF」):工作站 09-21 實錄——
+#   先打 `via-vdffetch 2023 --limit 100`,再打 `via-vdffetch 2023` 想抓全市場,第二跑 hist_2023 仍 43 秒、庫只多幾百列:**還是 100 檔**。
+#   根因:⑤ 把 $env:VIA_HIST_LIMIT 寫進本進程(視窗)後沒有還原;短令冊 via-vdffetch 沒打 --limit 時又會讀回它 → 探測上限黏在視窗裡。
+#   修法只在本檔:起跑先記下 VIA_HIST_SINCE / VIA_REV_SINCE / VIA_HIST_LIMIT 三個的原值,每一個出口都還原(Restore-VIAFetchEnv);
+#   你自己事先設的值照樣尊重(還原成你設的那個)。視窗原本就帶著 VIA_HIST_LIMIT 時 ⑤ 印黃字講明它從哪來、怎麼清。其餘一字不動(v0104 留作版史 L04)。
+#   還原本版:刪掉本檔,短令冊 newest glob 自動退回 v0104。
 # 批383 操作員令「用一個 powershell 啟動 vdf 包含進入環境」
 # =====================================================================
 # 一貼即用(新視窗、任何目錄皆可;不需先載短令冊):
@@ -43,6 +49,16 @@
 $ErrorActionPreference = "Continue"
 # 點源道安全退出:. 本檔 時 exit 會關掉操作員視窗→改 return(僅結束本腳本);-File 道維持 exit <rc>
 $script:Dotted = ($MyInvocation.InvocationName -eq ".")
+# v0105:本跑前的視窗環境——跑完逐一還原(不讓 --limit / 年份旗標黏在操作員的視窗裡)
+$script:VIAFetchEnvBefore = [ordered]@{}
+foreach ($k in @("VIA_HIST_SINCE", "VIA_REV_SINCE", "VIA_HIST_LIMIT")) {
+    $script:VIAFetchEnvBefore[$k] = [Environment]::GetEnvironmentVariable($k, "Process")
+}
+function Restore-VIAFetchEnv {
+    foreach ($k in @($script:VIAFetchEnvBefore.Keys)) {
+        [Environment]::SetEnvironmentVariable($k, $script:VIAFetchEnvBefore[$k], "Process")
+    }
+}
 
 
 function Write-Step([string]$Text) { Write-Host ("--- " + $Text) -ForegroundColor Cyan }
@@ -192,6 +208,10 @@
 
 # ---------------------------------------------------------------- ⑤ 年份旗標
 if (-not ($Year -match "^\d{4}$")) { Write-Host ("  [FAIL] -Year 需四位數年份,收到:" + $Year) -ForegroundColor Red; if ($script:Dotted) { $global:LASTEXITCODE = 2; return } else { exit 2 } }
+$limWas = "" + $script:VIAFetchEnvBefore["VIA_HIST_LIMIT"]
+if ($limWas -match "^\d+$") {
+    Write-Host ("  [注意] 本視窗原本就帶著 VIA_HIST_LIMIT=" + $limWas + "(上一次 --limit 留下的,或你自己設的);短令冊沒打 --limit 時會沿用它。要全市場:`$env:VIA_HIST_LIMIT='' 後再跑") -ForegroundColor Yellow
+}
 $env:VIA_HIST_SINCE = $Year + "-01-01"
 $env:VIA_REV_SINCE = $Year + "-01"
 if ($Limit -gt 0) { $env:VIA_HIST_LIMIT = "" + $Limit } else { $env:VIA_HIST_LIMIT = "" }
@@ -204,11 +224,12 @@
 if ($accel) { Invoke-VIAPython -Python $PY $accel --activate } else { Write-Host "  [加速器] 模組缺=略(graceful)" -ForegroundColor Yellow }
 
 $lanes = Get-Tail (Join-Path $VIA "supportive modules\registry") "CGC_MDL134_ParallelLanes_v*.py"
-if (-not $lanes) { Write-Host "  [FAIL] 十道並行編排引擎缺(CGC_MDL134_ParallelLanes_v*.py)" -ForegroundColor Red; if ($script:Dotted) { $global:LASTEXITCODE = 2; return } else { exit 2 } }
+if (-not $lanes) { Restore-VIAFetchEnv; Write-Host "  [FAIL] 十道並行編排引擎缺(CGC_MDL134_ParallelLanes_v*.py)" -ForegroundColor Red; if ($script:Dotted) { $global:LASTEXITCODE = 2; return } else { exit 2 } }
 Write-Step "⑥ 九頭龍哨兵 H1-H6(唯讀;H3 進程雙頭/H5 尾版律 FAIL=誠實停)"
 $plan = (Invoke-VIAPython -Python $PY $lanes plan 2>&1 | Out-String)
 Write-Host $plan
 if ($plan -match "H3 FAIL|H5 FAIL") {
+    Restore-VIAFetchEnv
     Write-Host "=== [via-vdffetch] 九頭龍風險(見上 H3/H5)=誠實停;關閉另一條在跑的鏈或修尾版後重試 ===" -ForegroundColor Red
     if ($script:Dotted) { $global:LASTEXITCODE = 3; return } else { exit 3 }
 }
@@ -226,5 +247,6 @@
 $proj = Get-Tail (Join-Path $VIA "supportive modules\registry") "CGC_MDL131_ProjectCompletion_v*.py"
 if ($proj) { Invoke-VIAPython -Python $PY $proj digest }
 
-Write-Host ("=== [via-vdffetch] 畢 rc=" + $rc + ";看頁:via-open 架構 / via-open 竣工(零跳出律:頁只落檔)===") -ForegroundColor Cyan
+Restore-VIAFetchEnv
+Write-Host ("=== [via-vdffetch] 畢 rc=" + $rc + " · " + $limTxt + "(視窗的 VIA_HIST_SINCE/VIA_REV_SINCE/VIA_HIST_LIMIT 已還原成本跑前的值);看頁:via-open 架構 / via-open 竣工(零跳出律:頁只落檔)===") -ForegroundColor Cyan
 if ($script:Dotted) { $global:LASTEXITCODE = $rc } else { exit $rc }
```

---

## 七 · 工作站貼上區

```powershell
git fetch origin
git merge --no-edit origin/main
git merge --no-edit origin/claude/busy-bell-97sa4f
. .\Register-VIA-Commands-v0242.ps1
$env:VIA_HIST_LIMIT=''
via-vcgc ssot verify
via-vcgc ssot plan
via-vdfsys launch
.\launch.ps1
via-datahome catalog
via-vdfinc plan
```

直呼 `via-price` / `via-chip` 之前,在同一個視窗先打(這是你的手,AI 不代設):

```powershell
$env:VIA_SCRAPE_CONSENT='YES'
```

要真跑三支治理版引擎(會觸網),同樣先開閘一:

```powershell
$env:VIA_NET_CONSENT='YES'
& "C:\Users\tonyk\envs\via_vdf_312\Scripts\python.exe" "functional modules\VDF\VDF_MDL006_FinancialModel_v0100.py" --tickers 2330,3324 --no-charts --no-pause
```

貼回:`via-vcgc ssot verify` 第一行、`via-vdfsys launch` 的下一步卡、`via-vdfinc plan` 的目錄時間那一行。

---

## 八 · 掉球

新增 Z120–Z136(`docs/VIA_DroppedBalls_B507.md`):閘二三把尺 · 哨兵列 · 車道不建衍生層 · 三支出網走統包 · MDL006 去留 · 重疊與資料缺陷 · 短令與 Deck · 視窗限量 Register 行 · VRN 管理的 SSOT 燈 · MDL176 公開 collect() · MDL176 `apply` 無旗標就寫 · MDL115 沒有乾跑 · 格子重複站 · 逐期 EPS 河流圖 · MDL002 路徑與副本 · 開機鏈掛 `ssot verify` · 啟動器類 .ps1 的模板章接法。
