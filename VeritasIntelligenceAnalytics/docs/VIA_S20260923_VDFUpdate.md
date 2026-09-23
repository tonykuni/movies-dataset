# 側線 2026-09-23 — VDF 更新狀況 · 三支上傳引擎治理版 · VCGC 第四扇門(SSOT 正則·同義字連動)

側線 2026-09-23;主線批號由併線的手指定 L25。基底 main `03b4f256`(PR #91,批725–726)。

操作員令(依序):

1. 「自 session 更新 VDF」「更新狀況」
2. 「自動實測自動修正自動完成」(附 MDL002 / MDL003 / MDL006 三支上傳檔)
3. 「SSOT REGEX 同義字等與 VCGC 相連自動規劃檢查更新 · 實測自測自完工 · 結果驗證」
4. 「善用 VCGC 工具節省 TOKEN」
5. 同日第二段:「許可出 v0105 依你建議執行」(= L70 許可),附工作站實錄(`via-vcgc ssot` 四次都印出 v0125 的整份版史)
6. 「https://github.com/tonykuni/movies-dataset 路徑應改為這個」:貼上區一律從這個倉拉,不依賴視窗所在資料夾或本機 `origin` 指到哪

---

## 一 · 現況

- **VDF 可以啟動**。工作站 09-21 兩次實錄裡「看起來卡住」的地方,五個根因都量到了,四個已由新版處理,一個要操作員裁定(閘二的尺)。
- **三支上傳引擎**已成治理版 v0100:閘沒開回 rc4、零出網零寫檔;沒料回 rc2,不再印「完成」。
- **VCGC 現在看得到、也管得到 SSOT 正則與同義字層**:`via-vcgc ssot` 檢、`ssot plan` 規劃、`ssot plan -Apply` 交正主更新、`ssot verify` 驗收。
  今天實跑:正則清冊落後 7 條樣式,交正主重建後驗收 PASS。
- **啟動器還原版 Invoke v0105 已出貨**(你許可):跑完把 `--limit` 與年份旗標還原;接上 L102 模板章,Celeritas 兩站綠。
- **VCGC v0127**:不認得的動詞只印 22 行用法段,不再印三百多行版史;你貼回的那四次就是這個問題。

---

## 二 · 工作站 09-21 為什麼看起來卡住

| 症狀(工作站實錄) | 根因 | 處理 | 你的手 |
|---|---|---|---|
| `via-vdfinc plan` 兩次都報 56 個缺口,抓完也不變 | 計畫讀的是**快取目錄**,目錄沒重建;而且不說目錄幾分鐘前產的 | ENG089 v0101:先印目錄時間與年齡,過期標 `[過期]` 並回 rc2;紀錄表(`ts` 欄)不算缺口;1900-01-01 哨兵列另列 | 抓完先 `via-datahome catalog` 再 `via-vdfinc plan` |
| 第二次 `via-vdffetch` 仍只抓 100 | Invoke v0104 寫了 `$env:VIA_HIST_LIMIT`,Register v0242 第 363 行在沒給 `--limit` 時讀回 → **黏住** | 對接口 v0104 量出來並印清除那一行;**Invoke v0105 已出貨**:每個出口都還原三個視窗變數 | 已不必手清;Register 第 363 行的讀回仍在,改它要另一次許可(Z127) |
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
| Celeritas 產出契約閘(L102) | 第一段撤回 v0105 時綠;第二段出貨 v0105(接上模板章)後兩站仍綠 |
| Invoke v0105 模板章稽核(正主 `xps_audit`) | joined · restore · requires7 全到 · forbidden 0 · verdict pass |
| VCGC v0127 自測 | 36/36(+㊱ 不認得的動詞只印用法段,22 行) |
| 對接口讀新啟動器 | `launcher_restores` = True;對接口 31/31 · 單元測試 34/34 · 契約 19/19 |
| 格子逐站(新改 16 站) | OK 15 · SKIP 1(啟動就緒要工作站家族境) |
| 全格子 350 站 | OK 325 · FAIL 12 · SKIP 13 · TIMEOUT 0(815 秒;平行段撞到單寫者庫的站,序跑複判過) |
| 12 紅逐站複驗 | **每一站在 main 原碼也紅**(乾淨 main,或 main 原碼跑同一份本地料):工具升階梯 · 治理台 UI Matrix · 首頁文字擷取 · VRN 六層鏈廿五檢與實跑 · VRN 統一報告引擎 · U/I 畫面統一閘 · 研報欄位規格實跑 · CGC_MDL120/143/144 · 系統 API 三態。本側線新增的紅 0 |

---

## 六 · L70:Invoke v0105 已出貨(你 2026-09-23 許可)

- **做什麼**:起跑記下 `VIA_HIST_SINCE` / `VIA_REV_SINCE` / `VIA_HIST_LIMIT`,**每一個出口**都還原(含找不到根、`-Year` 不合格兩個早退)。
- **模板章(L102)接法:不包裹**。正主 `xps_join` 會把整支包進 scriptblock,`-Year` / `-Limit` 綁不上、點源進環境失效(Z136)。所以:
  - 最上面兩行是章頭與 `#Requires -Version 7.0`,`param()` 仍是第一個敘述。
  - 正主 `supportive modules\ps7\VeritasCeleritas.PS7.ps1` 載進動態模組,它檔頭的 `Set-StrictMode` 與變數不外洩到本檔或你的視窗。
  - 每一個出口都呼叫正主 `Restore-CeleritasPS7`,跑完就還原,不等視窗關。
- **跑的時候會變的**:正主只動本行程,優先權 AboveNormal、親和性、GC、執行緒池、本執行緒文化、主控台 UTF-8,跑完全數還原。
  子行程(十道 python)會繼承較高的優先權,跑擷取時電腦可能稍微頓。
- **開跑會多印一行** `[Celeritas] …`:「本行程減壓已套」或「正主在但沒套上,略過」並附正主的第一個錯。
  容器沒有 pwsh,我量不到正主首載是否正常(Z137),這一行就是工作站上的答案。
- **pwsh 7 才能跑**:`via-vdffetch` 在你的 pwsh 視窗裡直接呼叫,PS 測試閘也先找 pwsh,兩條路都不受影響;只有「一貼即用」那一行從 `powershell` 改成 `pwsh`。
- **還原**:刪掉 `Invoke-VIA-VdfFetch-v0105.ps1`,尾版律自動退回 v0104。容器沒有 pwsh,**PowerShell 語法還沒真剖析過**;工作站的 PS 測試閘(CGC_MDL145)會拿 pwsh 對它跑 `-Dry -NoEnter`,那是第一次真剖析。

---

## 七 · 工作站貼上區

你貼回的四次整份版史,原因只有一個:視窗裡 `via-vcgc` 讀的那棵樹還沒拉到這條分支,最新的還是 v0125,它沒有 `ssot` 這個動詞。
`via-*` 讀的是 Register 設的 `$VIA`,**跟視窗現在在哪個資料夾無關**(你那時在 `C:\Users\tonyk\VIA-VDF-VRN`,沒關係)。
所以下面每一行都指明倉庫 `https://github.com/tonykuni/movies-dataset`,並用 `git -C $VIA` 對準 `$VIA` 那棵樹,不管本機 `origin` 指到哪。

```powershell
git -C $VIA remote -v
git -C $VIA pull --no-edit https://github.com/tonykuni/movies-dataset claude/busy-bell-97sa4f
via-reload
via-vcgc status
```

`via-vcgc status` 第一行要是 `[VCGC] v0127`。還是 v0125 的話,先打 `via-pin --show` 看這個視窗用的是哪一份副本,再對那一份重跑上面的 `git -C` 兩行。
第一行 `remote -v` 如果 `origin` 不是 movies-dataset,要改是你的手:

```powershell
git -C $VIA remote set-url origin https://github.com/tonykuni/movies-dataset
```

版本對了之後:

```powershell
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
& "C:\Users\tonyk\envs\via_vdf_312\Scripts\python.exe" "$VIA\functional modules\VDF\VDF_MDL006_FinancialModel_v0100.py" --tickers 2330,3324 --no-charts --no-pause
```

貼回:`via-vcgc status` 第一行、`via-vdffetch` 開跑印的 `[Celeritas]` 那一行、`via-vcgc ssot verify` 第一行、`via-vdfsys launch` 的下一步卡。

---

## 八 · 掉球

新增 Z120–Z137(`docs/VIA_DroppedBalls_B507.md`):閘二三把尺 · 哨兵列 · 車道不建衍生層 · 三支出網走統包 · MDL006 去留 · 重疊與資料缺陷 · 短令與 Deck · 視窗限量 Register 行 · VRN 管理的 SSOT 燈 · MDL176 公開 collect() · MDL176 `apply` 無旗標就寫 · MDL115 沒有乾跑 · 格子重複站 · 逐期 EPS 河流圖 · MDL002 路徑與副本 · 開機鏈掛 `ssot verify` · 啟動器類 .ps1 的模板章接法(v0105 先在本檔做了,正主側仍待)· Celeritas 正主首載在自己的 StrictMode 下可能讀到未設變數(Z137,待工作站那一行)。
