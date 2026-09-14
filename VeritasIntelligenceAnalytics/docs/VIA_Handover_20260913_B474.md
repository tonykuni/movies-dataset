# VIA 交接紀錄 · 批474(2026-09-13)

> 立案:操作員令「**卡斷了 不卡斷 PS20個加速器 上傳GITHUB附上交接紀錄 B C**」。
> 這份檔的目的只有一個:**下一個接手的人(或下一個工作階段)不必看對話紀錄就能接上**。
> 對話會卡斷,檔案不會。所以凡是「只有我知道」的東西,一律寫進這裡。

---

## 〇-1 · 新律(批475 起,凡事先想這條)

> **凡是流程皆要想一個節省 TOKEN 的方式,想好才進行;通盤畫子系統,思考更省的方法。**

具體做法(本批已照做):
- 不重讀大檔,只 `grep -n` 要改的那一段,前後各看幾行。
- 操作員貼回來的實測輸出**直接當量測結果**,不自己再跑一次。
- 一個問題一個小版本檔;一版一 push;不順手擴大範圍。
- 輸出只印判定行與 `[計]`,不印整篇。

## 〇-1b · 新令六條(批475 收到,批476 起執行;原文照錄,免得卡斷丟失)

1. **所有 PY 檔案都要加上加速器**
2. **VDF 全部還要加入網路工具**
3. **所有紀錄、工具、模組、引擎及功能註冊,除非過時,只增不減**
4. **引擎功能化;子系統指揮化**
5. **必要時,同功能以最小代價整合(功能工具不便時)**
6. **VDF 若實測成功,則測試修正修 VERT**

省 token 的執行方針(先想好才動):
- 第 1、2 條**不逐檔改**(幾百個 .py 逐檔加一行=尾版律要幾百個新版本檔,且正本零觸碰)。
  改在**啟動層**做:匯流排/家族啟動器起子行程時注入加速器(SUP_MDL737)與網路正典件(SUP_MDL740),
  同一處維護、每一支引擎都吃得到、零檔案改動。哪一支沒吃到,census 式的量測會亮出來。
- 第 6 條先量:VERT 在樹上是什麼,量完再說。

## 〇-2 · 你現在最該先做的一件事(操作員工作副本卡住了)

實錄:
```
PS> git pull origin claude/via-envmanager-governance-7cls8h
CONFLICT (content): Merge conflict in
  VeritasIntelligenceAnalytics/supportive modules/registry/VIA_AutoCode_Registry_v0100.json
Automatic merge failed; fix conflicts and then commit the result.
```
**這就是「卡斷」的真身**:工作副本停在未完成合併,在解掉之前,
之後所有 `git pull` 都不會動,新短令永遠到不了那台機器。

台帳(`VIA_AutoCode_Registry_v0100.json`)是 **append-only** 的檔,
兩邊各自加了自己那幾筆,所以每次雙向都動就必衝突。
**律:台帳取聯集,絕不取單邊**(取單邊=另一邊的紀錄靜靜消失)。
`via-unstick` 就是為這件事寫的(委派 MDL143 拉齊醫生的 `ledger_union`;零 force 零刪除)。

一貼即用:
```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
via-unstick            # 先看它怎麼判(它會迴圈解到 UP_TO_DATE 才停)
```

---

## 一 · 批474 這一批做了什麼(四件)

| # | 事 | 檔 | 怎麼驗的 |
|---|----|----|---------|
| ① | 匯流排三修 | `CGC_MDL148_EngineBus_v0107.py` | 二十四檢 24/24 |
| ② | **B**:一頁式紅黃綠燈矩陣,跑完自己跳出來 | `via-ryg`(Register v0183) | 真產 32KB 頁 · 五矩陣皆在 · 零外連 |
| ③ | **C**:庫況普查(回答「VDF 到底能不能跑」) | `via-census` / 矩陣五 | 真讀 6 本庫 35 張表 |
| ④ | 本交接紀錄 | 本檔 | — |

### ① 匯流排三修(工作站實錄照出來的)

實錄逐字:
```
PS> via-bus --matrix
…SyntaxWarning: invalid escape sequence '\s'
(然後吐出兩百行 docstring,什麼都沒跑)
```

三件事,**都是我的**:

1. **我給錯指令**。冊上的動詞是 `matrix`,我上一則訊息叫操作員打的是 `--matrix`。
   但這不只是打錯字——`--matrix` 是任何人都會自然打出來的形狀,
   而 v0106 對它的回應是「印兩百行說明,然後**回 rc=0 說成功**」。
   兩個獨立缺陷,分開修:
   - `_verb()` 正規化:`--matrix/--catalog/--call/--census` 都收。
     **只脫頭部連字號,不猜別的**(`matrixx` 照樣不收——猜錯的體貼比不體貼更難救)。
   - 不認得的動詞改回 **rc=2**,印**六行用法**。
     rc=0 是**假綠**:自動化鏈路看 rc,會把「什麼都沒跑」讀成「跑完了」。
2. **SyntaxWarning**:docstring 裡拿正則當範例,而 docstring 不是 raw 字串。
   諷刺的是那段文字**正在講**「同一個判準寫兩個地方只改一邊」,結果它自己又生一個缺陷。
   改 `r"""`。
3. **矩陣五 · 庫況**(見下)。

### ② B —— `via-ryg`(別名 `紅黃綠` / `燈板`)

```powershell
via-ryg              # 真跑 vrn+vap,其餘家族只解析;產五矩陣頁;**自動開**
via-ryg vrn          # 只真跑 vrn
via-ryg -NoOpen      # 不開(給自動化鏈路)
via-ryg -DryAll      # 一支都不真跑(只要那張圖)
```
**為什麼這裡可以自動跳出,而零彈窗律沒有被違反**:
零彈窗律(批378)管的是「**沒人要求就別跳**」。`via-ryg` 是操作員親手打的,
打了就該跳。兩條律的分界線是「**誰要求的**」,不是「跳不跳」。

### ③ C —— 庫況:`via-census`(別名 `庫況`)+ 矩陣五

**為什麼要新增這張表**:操作員問的 C 是「VDF 到底能不能跑」。
既有的能跑閘(`via-rungate`)、調度矩陣一～四,**全都回答不了那題**——
> 一支引擎可以完美地跑完,然後把資料寫進一張空表。

只報「引擎綠不綠」就是一種假綠。四態:

| 態 | 意思 |
|----|------|
| GREEN | 有列,且(無日期欄 或 日期跨度 ≥ 30 天) |
| AMBER | 有列,但跨度 < 30 天 —— **料在,但薄**(最容易被當成綠的一種) |
| NODATA | 表在、列數 0 —— **表建好了沒料** |
| ABSENT | 碼裡當表在用、庫裡沒有這張表 —— **不是壞掉,是還沒建** |

**ABSENT 收得緊**(這裡犯過一次錯,記在這):
第一版抓所有 `tw_/vrn_/etf_` 開頭的識別字,量出 **74 筆**,一半是 python 變數名,
連庫裡明明有 891 列的 `tw_listings` 都被寫成「缺」。
那是**判錯的紅燈,一次七十四盞**。收緊成只認 SQL 語境
(`FROM/JOIN/INTO/TABLE/UPDATE` 後面那個名字)且 ≥3 個檔在用 → 23 筆,每筆都亮得出引用數。

---

## 一-b · 批476 · 新令 1/2/4/5 的落地:啟動層注入(零引擎改動)

**量到的**:加速器在 VDF 引擎只綁 4/109、VRN 0、VAP 0;VDF 109 支裡 52 支走正典網路件,**7 支活著的直呼網路**
(`ENG047 / ENG049 / ENG050_v0101 / ENG051 / MDL002 / MDL003 / MDL007`)。

**為什麼不逐檔加**:幾百個 .py 逐檔加一行=幾百個新版本檔(尾版律),正本零觸碰守不住,新引擎還得記得加。

**做法(第 5 條「最小代價整合」)**:`supportive modules/bootstrap/sitecustomize.py`。Python 起跑會自動 import 路徑上的
`sitecustomize`;四個啟動器把該目錄**前置**進子行程 `PYTHONPATH`,每一支 .py 起跑就綁上。

| 啟動器 | 版 | 注入點 |
|---|---|---|
| 匯流排 MDL148 | v0109 | `child_env(family)`;新增 `boot` 動詞=每家族真起子行程印它看到的 |
| 能跑閘 MDL137 | v0101 | `run_station` |
| 樞紐 MDL095 | v0135 | `_launch_locked`(家族從引擎路徑推) |
| 短令冊 | v0185 | `Set-VIABoot` 載入即前置;`via-py <family>` 設 `VIA_FAMILY`;`via-boot`(別名 `啟動層`) |

bootstrap 做三件事,全包 try(**絕不能讓引擎起不來**):
① 所有家族:`SUP_MDL737.activate()` → `VIA_ACCEL_BOOT=1:<可用>/<冊>` 或 `ABSENT:<因>`
② 只在 `VIA_FAMILY=vdf`:`SUP_MDL740` 註冊成 `via_net`(引擎 `import via_net` 即可用 `http_json/http_bytes/yf_download`)
③ 預設零輸出;`VIA_BOOT_VERBOSE=1` 才印一行;`VIA_BOOT=0` 整個關

**不做的**:同意閘一個字不碰(fail-closed 照舊);**不 monkeypatch `requests`**——靜靜改別人行為,是這套系統最恨的病。

實證(`via-boot`):vdf → 加速器 `1:11/88` · `via_net` True · 閘態「(未設)」;vrn/vap → 加速器同、不掛網路件。

**排隊(下一批)**:7 支直呼網路的 VDF 引擎逐支改走 `via_net`(各一個新版本檔);Grid 站登錄(格子檔太大,省 token 先延)。


## 一-c · 批477 · VETF 收尾 + TWREV v2.7 + 討論重建包(操作員睡覺期間,核准自主完成)

**「VERT」= VETF**(上傳的封印包名字就是答案)。四包先查再造:VETF 封印包 125/126 已在庫(b242)、NLP v1.8.0 68/68 已在庫(批421)→ **兩包不重收**;TWREV v2.7 對樹上舊版 14 檔全不同=真升版;討論重建包 0/20 在庫。

| 件 | 做了什麼 | 證據 |
|---|---|---|
| VETF | adapter 16 檢通過卻**從沒登錄**(冊 0、短令 0)→ 登 `vdf_vetf_consensus` + `via-vetf`(別名 `共識擴充`) | 合成長表真跑:Forward P/E 2330=1100/55=**20.0** 對;EPS=0 留空=fail-closed;覆蓋 factset_eps_n1 100% |
| TWREV v2.7 | 收容 `VDF/references/intake/TWREV_v2.7_FULL_b477`;登 `vdf_twrev` + `via-twrev`(別名 `月營收`) | selftest 全部通過;demo 真突破 27/候選 468;匯流排 GREEN 2.67s |
| 討論重建包 | ≤1MB 治理件 13 檔入 VRN 收容夾;>1MB 衍生 JSON 7 檔(76.8MB)**只記 sha256 不進 git** | `MANIFEST_intake_b477.json` |
| 匯流排 v0110 | **第十盞判錯的燈**:套件內模組當檔案跑的 ImportError 被判「缺件」→ 冊上 `module`(-m 啟動)+ `cwd: engine`(讀 cwd 的引擎)+ classify_stop 守衛 | 三十一檢 31/31 |

**via-twrev 的工作家**:引擎全靠相對路徑(`data/ output/ logs/`),所以首跑把 `config.yaml + data/` 種進 `VIA_Reports\twrev`,碼仍從收容夾 import(一份碼);`fetch/run` 觸 MOPS **只看同意閘,不代設**。demo 曾覆寫封裝內 3 個資料檔→自 zip 還原後才入庫。


## 一-d · 批478 · VDF SSOT 化第一步:庫冊 + 庫況對冊比 + K 項

- **庫冊** `supportive modules/registry/VIA_DB_Table_SSOT_v0100.json`:49 張表(來源=你機器的 census 實測 + 引擎碼寫入者掃描,20 張表有寫入者)。冊上明寫:列數/日期是**觀測值不是保證值**,`min_rows` 才是判準;三本正庫;`_repo_` 是副本;`tw_daily_prices` 標 1900 哨兵列;`known_legacy_absent` 12 張。
- **匯流排 v0111**:census **冊優先**——冊上宣告而庫裡沒有 → `ABSENT(冊上宣告)` 並列寫入者(該有而沒有,最該亮的一種);冊外 SQL 語境 ≥3 檔 → `ABSENT(冊外)`;庫裡有冊上沒有 → 加註「冊外」提醒冊該補。矩陣五多一欄「冊」。三十二檢 32/32。
- **K 項已改**(你核准全線):樞紐 v0136 同意閘由覆寫改 `setdefault`——沒設才補、設了一律尊重;既有流程零行為變更。


## 一-e · 批479 · M 項:VDF 直呼網路的引擎改走正典網路件優先

**先量再改**:七支直呼網路的 VDF 引擎裡,**有人調度的只有兩支**——`ENG047`(冊 `macro_detail`)與 `ENG051`(樞紐任務)。
`ENG049 / ENG050 / MDL002 / MDL003 / MDL007` 被 0 支引擎 import、被 0 處調度=**真孤兒**(先前「被 30 檔引用」全是提及,不是依賴)。孤兒不動刀:只增不減,動了也沒人跑。

| 引擎 | 新版 | 改法 | 驗 |
|---|---|---|---|
| ENG047 | `_v0101` | `_http_get_json` 先走 `via_net.http_json`,不在位才退回 urllib(零回歸);DENY 照停不代設閘 | 八檢 8/8;經啟動層 `--fetch` 閘未開 → FAIL-CLOSED 零外呼 |
| ENG051 | `_v0101` | 本檔唯一對外呼叫點 `def_http_get_text` 先走 `via_net.http_text`,非 OK 丟 `RequestException` 讓既有 except 接手 | 原本就無 selftest → py_compile + 單一 seam |

冊/樞紐的 glob 都是 `*.py` 萬用,尾版律自動解析到 `_v0101`(匯流排 catalog 實證)。VDF 引擎走正典優先數:0 → 2(活著的兩支全部)。


## 一-f · 批480 · F 項:正本頁保護(MDL138 v0101)+ 第五個啟動器接啟動層

無資料環境跑 `via-famui`,產生器會把你的正本 UI 頁改寫成一格格「缺(誠實)」——本工作階段我人工 `git checkout` 還原 **5 次**。守則寫進 `run_item`:只對正本頁,跑前快照;跑後若新頁占位格 ≥3 且比舊頁多=資料缺席的再生 → **還原舊頁,並寫進紀錄 `guard` 欄**(不是靜靜還原),態走 DATA 不假綠。真資料再生照常覆寫。專測兩案皆對;八檢 8/8。同版把 MDL138 接上啟動層(產生器子行程綁加速器)。

## 一-g · 你睡覺期間推了什麼(一眼看完)

| 批 | commit | 一句話 |
|---|---|---|
| 477 | `54ecf4a4` | VETF 登錄+真跑實證;TWREV v2.7 收容+自測綠;討論重建包收容;匯流排第十盞燈(-m 啟動 / cwd) |
| 478 | `37b5b60b` | 庫冊 `VIA_DB_Table_SSOT_v0100`;census 對冊比;樞紐同意閘改 setdefault(K) |
| 479 | `d286f101` | ENG047/ENG051 v0101 走正典網路件優先(M);孤兒五支只記不動 |
| 480 | `d11a0718` | 正本頁保護(F);MDL138 接啟動層 |
| 481 | `1a502f9e` | 兩專案授權使用:ENG051 v0102(v1.1.0 綁上)+ 月營收跨族群相位 v030 收容登冊 |
| 482 | `2525efd0` | 自測格子 v0295 +三站;格子接啟動層;新短令 0 死路 |
| 483 | `4e03010b` | 啟動層接力被遮的 sitecustomize;via-boot 三家族並行+心跳 |
| 484 | `403ad604` | digest v0114 取價缺 n;匯流排 v0113 心跳走 stderr;H 量測結案 |
| 485 | `06736d7a` | `via-census -Hygiene` 唯讀審計;匯流排登進樞紐 v0137/總控 v0122 |
| 486 | `a6327d03` | 所有 py 指令走 `Invoke-VIAPython`:20 加速器 + 動態進度條;短令冊 82 處;VdfFetch v0104 |
| 487 | `06f8987c` | via-boot 卡住根因:啟動層每次載 Celeritas → 改快取優先;PS 點亮不擋 |
| 488 | `4270bda0` | via-ryg 參數三修(貼進來的註解/非數字 timeout/家族驗證)+ 兩枚 v0184 起的舊錯 |
| 489 | (本批) | 實錄四修:啟動層父行程跳過、心跳錯位、+tails、ENG073 樹內尋庫 |

**沒動的**:資料本體一筆都沒動(1900 哨兵列、`_repo_` 副本、六張 0 列表——要你點頭);同意閘一個字沒設;孤兒引擎沒刪。


## 一-h · 批481 · 「另外兩個專案有沒有授權使用?授權使用」

| 專案 | 先查 | 造 |
|---|---|---|
| 主動 ETF 每日持股引擎 v1.1.0 | 早在庫(位元相同),**但活著的 ENG051 是它的舊版**(29 個 def 對 46 個) | `ENG051_v0102` = v1.1.0 + 去硬寫根(`~/Downloads/…` → 自 `VIA_ROOT` 推到 `output_hub/active_tw_etf`)+ `via_net` 優先;27/27;樞紐 glob 尾版律自動接上 |
| 月營收 × 產業 × 族群 相位/領先落後 v030 | **從沒收過**(只在 b305 整理清單出現過);樹上無重複件 | 收容 `…/VDF_TW_MonthlyRevenue_CrossGroupPhase_v030_b481`;8/8;`--self-test` 真跑;冊 `vdf_revphase` 匯流排 GREEN |

短令:`via-revphase`(別名 `營收相位`;自你的庫匯出 CSV 再餵引擎;`-SelfTest`)、`via-etfhold`(別名 `持股日更`;`-SelfTest` 不碰正庫;日更觸網只看同意閘)。
兩支引擎本體都沒有授權條款檔——「授權」= 你親口,已記台帳 1016。


## 一-i · 批482 · 功能註冊只增不減:自測格子 v0295

**先量再登**:這幾批新版的 MDL148/138/137/095、ENG047/051/078 在格子裡**本來就有站**,且全用 `newest()` 動態解析尾版 → 已自動跑到新版,不重登(重登=九頭龍)。真的沒站的只有三支 → 登了:VETF adapter 16 檢、月營收相位 v030 8 檢、TWREV v2.7 selftest(pycode 站,`-m` 啟動;第十盞燈那一課)。`--only` 重跑 4 站 OK 4。
格子執行器接啟動層(第六個啟動器),且把 ENG051 自測根指到 `VIA_Reports/selftest_grid/`,不寫進原始碼樹。
死路掃描:本工作階段新登的十個短令 **0 死路**;YELLOW 162 條是既有債(多為台帳 JSON 內提及的舊令名),沒動。


## 一-j · 批483 · 自審兩修

- **啟動層接力**:`sitecustomize` 靠 PYTHONPATH 前置生效,會遮住發行版自帶的 sitecustomize(Debian 的 apport 掛鉤就在那)。改成 `_boot()` 之後找 sys.path 上**下一個**同名檔,找到就接力執行、記 `VIA_BOOT_CHAINED`。實證:被遮的也跑了。
- **`via-boot` 不再「還在跑」**:原本三家族逐一探測、各 120 秒、零輸出;v0112 改三家族並行 + 每 20 秒心跳 + 總上限 150 秒,逾時的家族誠實印「探測逾時」。容器 0.3 秒;三十三檢 33/33。


## 一-k · 批484 · J 項結案 + 匯流排 JSON 契約 + H 項量測結案

- **J**:`vrn_report_digest` v0114 計數行亮「**取價缺 n**」(以前取價失敗只把值轉 None,計數行看不出來)。容器真跑:`報告 2 · OK 1 · FAIL 0 · SKIP 1 · 取價缺 1`。
- **匯流排 v0113**:自己踩到——`call` 跑超過 20 秒時心跳印進 stdout,結果 JSON 就炸。人看的字走 stderr,機器讀的字走 stdout;三十四檢 34/34。
- **H**(量測結案,不改碼):`tw_listings` 讀 4 支、寫 ENG081;`tw_listings_industry` 讀 2 支、`engine/` 內無寫入者(1,981 列來自別處,庫冊已標)。你機器上 `tw_listings` 1,996 ≥ 1,981,「綁舊表 891 列」的顧慮不成立(那是容器副本的數字)。
- 輸入主控台(MDL139)讀冊的 groups/items → 本工作階段登冊的四項會在你重建頁時自動出現。


## 一-l · 批485 · I 項準備(唯讀審計)+ 匯流排登進樞紐/總控

- **`via-census -Hygiene`**(別名 `庫衛生`):哨兵列(日期 < 1950)數出來 + 對應 `DELETE` **只寫不跑**;`_repo_` 副本每張表對正庫 MAX 日期,副本較舊=退役候選**不刪**。沒有 `--apply`,永遠不會有——刪資料是你的手。你機器上跑一次,把哨兵那幾行貼回來,我們就有數字可以決定。
- **匯流排登進樞紐/總控**:批471 立的匯流排至今沒有樞紐任務、沒有總控正式名稱——總控頁按不到。樞紐 v0137 `+bus_ryg/+bus_census`(白名單釘數 54→56,兩檢照改,25/25);總控 v0122 +兩個正式名稱。**總控頁沒在雲端再生**——你那邊 `via-manager` 再生一次,按鍵才會出現。


## 一-m · 批486 · 所有 py 指令統一走 `Invoke-VIAPython`(20 加速器 + 動態進度條)

**先查再造**:PS 側 20 加速器實體模組早就在 `supportive modules/VIA_PS_Accel_Module.ps1`(批102):`$VIA_ACCEL20` 冊 + `Write-VIAProgress` + `Invoke-VIAGuarded`。不重造,只接上每一次 python 啟動。

| 件 | 做法 |
|---|---|
| `supportive modules/VIA_PS_PyProgress_Module.ps1`(新) | `Invoke-VIAPython [-Family f] [-Python exe] [-TimeoutSec N] <script> [args]`:一視窗第一次跑 python 真點亮 20 格(SUP_MDL737 `--activate`;缺席誠實說缺);每次子行程邊跑邊轉播(stdout 走 pipeline,上游捕捉照舊)、`Write-VIAProgress` 動態條、逾時 Kill 整樹回 124、`$LASTEXITCODE` 照真回 |
| 短令冊 v0189 | **82 處** python 呼叫規律改寫成 `Invoke-VIAPython`;模組缺=誠實退回直呼 |
| `Invoke-VIA-VdfFetch-v0104` | 點源模組 + 5 處改寫(含 `$plan` 捕捉那處) |
| OneShot | 0 個直呼(委派短令)=自動受惠 |
| 匯流排 v0115 | 自測沙盒的 .duckdb 不再冒充正庫(第一版整夾排除 VIA_Reports 打掉了 VRN 主庫,收窄成沙盒標記) |

自犯錯兩枚記檔:排水把行吞進位置變數(捕捉 0 行);點源行插在 `$VIA` 賦值之前(我的測試預設了 `$VIA` 才沒炸,你機器上 95 個短令會全斷)。兩枚都在推之前實證修掉。

**其餘啟動器**(All/Complete/EnvGovernance/Unstick/FixAll…)還沒接進度條——下一批逐個接;PSRepair/PDFPlumberPlus/AllGreen 本來就有。


## 一-n · 批487 · 「via-boot 為何每次動不了」——根因是我的啟動層

**量到的**:容器(只 11 個加速庫)有啟動層的 python 起跑 13→206 ms、拉進 95 個 numpy/pandas/duckdb/pyarrow 模組。批476 我讓每一支 python 起跑都載 Celeritas;你的機器在批384 把 88 件冊全裝進 via_core/via_vdf,所以**每支 python 指令前面都是一大段空白**;批486 的點亮又是**同步**跑完 `--activate` 才畫進度條——所以連條都看不到。兩次卡都是我的啟動層,不是引擎。

**修**:啟動層改**快取優先**——加速的效果其實只是 17 個執行緒預算環境變數,`via-accel --activate` 早就存在 `VIA_Reports/accel_activation/ACCEL_ACTIVATION_*.json`;起跑只套快取(206→59 ms,重套件零載入),永不在啟動層載 Celeritas。PS 點亮:有快取直接畫 20 格零 python;沒快取才**背景**點、最多等 20 秒、逾時誠實說還在背景。

**你現在要做的**(順序重要):
```powershell
# Ctrl+C 掉卡住的 via-boot,然後:
git pull origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
via-accel          # 產快取:這一次會慢(它真的載 88 件冊)——只需一次
via-boot           # 之後每個短令起跑都是毫秒級
```


## 一-o · 批488 · `via-ryg` 參數三修(實錄:`-Timeout 300# 先 Ctrl+C…`)

註解黏在數字後面,PowerShell 把 `300#` 給了 `-Timeout`、把「先」當家族名;包裝一邊丟錯一邊照跑「真跑 先」。修:參數裡出現 `#` → 截掉並提醒「實際採用:…」;`-Timeout` 非正整數誠實停;家族只認 vdf/vrn/vap,亂的只點名亂的那個。
順帶抓到**自 v0184 起就在**的兩枚:沒給 `-Timeout` 時第一個位置參數永遠被跳過(`via-ryg vrn` 其實一直跑 vrn,vap);`vrn,vap` 被 PowerShell 當陣列傳進來變 "vrn vap"(以前傳給匯流排=沒人認得的家族=全 PLAN)。都修了。


## 一-p · 批489 · 你真跑 via-ryg 的實錄,照出四件事

| 實錄 | 真相 | 修 |
|---|---|---|
| `via-boot [vdf] 網路件(不掛)· via_net False` | 啟動層看到父行程已設 `VIA_ACCEL_BOOT` 就整段跳過,連 vdf 該掛的網路件都跳掉 | 每個行程各做各的(批489) |
| `vrn_firstpage TIMEOUT 300s` | 你收件匣 64 份,OCR 起手就 140 秒;**我建議的 300 秒是錯的尺**,預設 900 | 不帶 `-Timeout` 或 `-Timeout 1800`;ENG072 起手靜默另記 R 項 |
| `vap_stack` 底下「⏳ 19s · 引擎最後一行:}」 | 那是上一項 `vrn_pdfplus` 的心跳(20.1s、結尾 `}`),兩條流錯位 | 矩陣模式心跳走 stdout 並帶項目名(v0117) |
| `vrn_structdb 庫缺…確認 clone 根` | ENG073 寫死 `output_hub/mega/` 加兩個寫死替根,你的庫不在那三處(寫死路徑病) | ENG073 v0123 最後一道在樹裡找同名庫並印出用了哪本;`via-census` 先印每本庫的路徑 |

三個 RED(fourpoint／vap_stack／vap_heatmap)雲端看不到尾段 → 新增 `via-bus tails`。`vap_dashboard` ABSENT = via_vap 境沒裝 pandas(你的手:`via-rungate --family vap --approve-install`)。
好消息:加速器真點 54/88;`via-boot` 1.0 秒;`vrn_pdfplus` 在你機器上 GREEN;64 份 digest 68 秒有進度條;頁自動開在 msedge(B 落地)。


## 一-q · 批490 · 你說「庫在 `C:\Users\tonyk\VIA System\via_database`,parquet 存、duckdb 管」——49 張 ABSENT 是我點錯的燈

批489 你貼的 `via-census` 只剩 7 本庫、冊上 49 張全 ABSENT。**不是庫沒了,是庫搬到倉外的家**,而匯流排只掃倉內(`VIA.rglob`)。
我上一則把它歸因到 `/selftest_out/` 沙盒標記,那是判錯:ENG045 的 `vdfout_runs/selftest_out` 真是自測夾,只住 `vdf_hub.duckdb`。

| 事 | 檔 | 怎麼驗的 |
|---|----|---------|
| 資料家冊(家在哪、長什麼樣、省 token 的規矩) | `supportive modules/registry/VIA_DataHome_SSOT_v0100.json` | MDL123 解析序:`--home` > env > VLL local_paths.json > **冊** > 舊指標 `data/WHERE_IS_DATA.md` > 預設 |
| `via-datahome catalog`:家內清點→**一頁目錄** `VIA_Reports/datahome/DATAHOME_CATALOG_latest.json`(庫名→路徑;表/湖→列數·日期範圍);`plan`:倉內散落整併計畫**只列不動** | `CGC_MDL123_DataHome_v0102.py` | 十一檢 11/11(暫存家;真目錄零觸碰) |
| `via-census` 家內也掃(env `VIA_DATA_HOME` > 目錄頁 > MDL123);parquet 湖入普查 `[湖]`;**預設一本庫一行**,`-Tables` 逐表;`[家]`/`[沙盒略]` 明印;沙盒標記錨定擁有者夾;「庫缺」=缺料不是壞掉 | `CGC_MDL148_EngineBus_v0118.py` | 三十九檢 39/39 |
| 啟動層 ③ 資料家:目錄頁→ env `VIA_DATA_HOME` + `VIA_DB_<庫名大寫>`(引擎按名取路徑,不寫死;家不在=誠實不設) | `supportive modules/bootstrap/sitecustomize.py` | 實證兩變數到子行程 |
| ENG073/ENG080 尋庫**家優先**(`VIA_DB_VDF_TW_MARKET` > 家內按名找最新 > 舊路徑鏈) | `VRN_ENG073_…_v0124.py` / `VRN_ENG080_…_v0105.py` | 三十六檢/十六檢皆綠;env 指到暫存家即解到家 |
| `via-datahome catalog [-Tables] | plan | link [-DryRun] [--point 夾]`;`via-census -Tables/-Hygiene`;別名 資料家/庫目錄 | `Register-VIA-Commands-v0191.ps1` | pwsh 解析 0 錯 |

整併律(照你一貫的規矩):搬=`link`(hash 定生死、零刪除)、**不複製**(三副本病)、刪副本/暫存=你的手。
「parquet 本體 + duckdb VIEW 管家」的匯出是整併第二步,**等你貼 `via-datahome catalog` 回來我才知道家裡現在長怎樣**(先量再改)。

## 一-r · 批491 · 你貼回來的四份實錄:**接點死了,不是庫沒了**

| 實錄 | 真相 | 修 |
|---|---|---|
| `status`:`LINKED_ELSEWHERE` × 2、三本庫探針 `MISSING` | 你把舊家整夾搬進 `via_database\movies-dataset\data\…`,倉內兩個 `output_hub` 接點還指舊址 | MDL123 v0103:鏡根 `mirror_root()`(家本身/一層/兩層找含 `<倉名>/functional modules` 的那層)、新態 `DEAD_LINK`、`link --relink` **只換接點不動資料**(現址有料=不代決) |
| `catalog`:23 夾,`year=2026` 四個撞名;`fiveday` 整夾 FAIL;`最新 Q3/26Q4` | 分割夾該按母夾命名;20 檔裡一顆壞檔不該整夾判死;Q3 不是日期 | 湖改讀 parquet 中繼資料不掃湖:`px/year=2023`;混裝夾 `mega 252 檔=252 表` 逐檔登目錄;壞檔點名(PART);「最新」只認像日期的 |
| `census`:153 張表、缺 0 張;湖 12 夾 | 49 張 ABSENT 錯燈已熄;12≠23 是撞名去重 | 匯流排 v0119 的湖改向 MDL123 取(單一實作) |
| `tails`:`vap_stack/vap_heatmap` `pyarrow` 沒有 `__version__` | site-packages 的 `pyarrow` 夾缺 `__init__.py`=命名空間包=**套件壞了**,不是引擎壞 | 歸缺件 ABSENT 並指路 `pip install --force-reinstall pyarrow`(你的手) |

`tails` 還是 14:49 那次舊跑(ENG080 v0104);拉齊後 `via-ryg` 重跑才會換。
留給你的手:`via-datahome link -Relink`;兩本 `_repo_` 副本(158.8 MB/14 表至 09-07 vs 正庫至 09-12;0.5 MB/1 列 1900-01-01);`px/year=_raw` 那筆 1900-01-01 哨兵;`fiveday` 壞檔;pyarrow 重裝。

## 一-s · 批492 · 你上傳的兩件

| 件 | 查到什麼 | 做了什麼 |
|---|---|---|
| `TWREV___________v2.7_FULL.zip` | 36 檔逐檔 md5 與 b477 收容包**全同** | 不重複收容(重收=九頭龍);`via-twrev` 照舊 |
| `VIA_VRN_UnifiedReportEngine_v0100.py` | 2760 行;檔名×首頁×財務頁三源互證;兩本 parquet 為必選 SSOT;零寫死路徑;零主動連線(`--allow-web-official` 預設關);借用在庫 FirstPageEngine/ENG072 尾版;容器自測 **23/23** | 收容 `functional modules/VRN/references/intake/VIA_VRN_UnifiedReportEngine_v0100_b492/`;規格項 `vrn_unified`(匯流排 `call` 實證 GREEN);格子 v0296 一站;`via-vrnuni`(Register v0193;別名 統一報告) |

`via-vrnuni -SelfTest` 免料;真跑 `via-vrnuni --in <報告夾> --csv --json --duckdb`(未給 `--out` 落 `VIA_Reports\vrn\unified`)。
它的官方名冊要一份 CSV(`--official-listings`);沒給時台股 canonical ticker 依它自己的律留空,不污染。庫裡的 `tw_listings` 橋成那份 CSV 是 T 項。

## 一-t · 批493 · 你的擷取律 + `vrn_firstpage` 900 秒的根因

律(你 2026-09-14 講的):非 OCR 擷取必用;抓不到才 OCR,從簡單工具組往雙引擎、往 Paddle;成功 = 資料標示還原 + 文字修復;非 OCR 兩引擎互核,再與非 OCR 核對;成功的邏輯存中央邏輯庫。

| 實錄 | 真相 | 修 |
|---|---|---|
| `JP-3653` 一份卡 340 秒,之後多份 `NEEDS_OCR[OCR_EMPTY[五支]]` | 抓不到時整座梯子一次全燒(七支後端逐支載模型),再升高畫質整條重跑;每次 `via-ryg` 從頭燒 | **階梯**:simple(tesseract)→dual(+easyocr)→paddle(三支),每件共用 150 秒預算(`VIA_OCR_BUDGET_SEC`);超了誠實標 `OCR_BUDGET` 不升 |
| `OCR 引擎載入失敗:Unknown argument: show_log` | PPP 收容件拿 PaddleOCR 2.x 的鍵建 3.x | 相容墊片:2.x 鍵自動剔除重試(收容件正本零觸碰);載入失敗的後端記 BROKEN,24 小時內跳過 |
| 每次重跑 64 份都重抽 | 沒有地方記「這份上次怎麼成功的」 | **中央邏輯庫** `VRN_ENG082`:同檔(sha1)上次 SUCCESS 且產物在 = 命中不重抽;FAIL 的 24 小時內不重燒 OCR;`--force` 重抽 |
| 兩法互核、文字修復、標示還原沒有存證 | ENG072 早有 fitz×pdfplumber 雙法,但沒判、沒記 | 每件 sidecar 加 `logic{xcheck, repair, labels_ok, verdict}`;台帳 `VIA_Reports\vrn\extraction_logic\LOGIC_LEDGER.jsonl`(只增)+ `LOGIC_latest.json` |

律的資料形在 `VRN_ExtractionLogic_SSOT_v0100.json`(階梯、預算、互核門檻、TTL);執行層 `VRN_ENG082_ExtractionLogic_v0100.py`(十二檢);`VRN_ENG072_FirstPageText_v0117.py` 綁它(三十二檢;容器 30/32:⑤ 空夾 rc2 是 v0116 在此容器本就紅,是夾況不是碼)。
短令:`via-vrnlogic`(status / reset-backends / -SelfTest;別名 邏輯庫)、`via-firstpage [-Force] [-OcrBudget N] [--in …]`(別名 首頁擷取)。
仍是你的手:tesseract 的 `chi_tra` 語言包、easyocr 模型下載(要網路同意)、paddleocr 本體;`via-vrnlogic status` 會列出每支後端的 BROKEN 因由。

## 二 · C 的答案:VDF 現況(**操作員機器實測,批475 他貼回來的**)

> 批474 這一節原本寫的是容器副本的數字,結論是「`tw_daily_prices` 全樹不存在」。
> **對操作員的機器完全不成立。** 幸好那批一個引用都沒改。先量再改——量的地方不對就別改。

`via-census` 於工作站:**132 張表在庫 · GREEN 111 · AMBER 15 · NODATA 6 · ABSENT 12**

| 台股核心表 | 列 | 跨度 | 判 |
|---|---|---|---|
| `tw_daily_prices` | 2,128,169 | **1900-01-01** → 2026-09-11 | GREEN(但有 1900 哨兵列,見下) |
| `tw_prices_adj` / `prices_canonical` / `features_daily` | 2,128,168 | 2020-01-02 → 2026-09-11 | GREEN |
| `tw_trading_daily` | 1,469,025 | 2023-01-03 → 2026-09-11 | GREEN |
| `tw_chip_inst` / `tw_chip_margin` / `tw_chip_derived` | ~1.15M 各 | 2024-01-02 → 2026-09-11 | GREEN |
| `tw_universe` 7,930 · `tw_listings` 1,996 · `tw_listings_industry` 1,981 · `tw_monthly_revenue` 88,275 | | | GREEN |
| `consensus_daily` 597 · `tw_valuation_daily` 13,778 · `analyst_estimates` 585 | | 2026-08-24 起(≤19 天) | AMBER=新管線,料在但薄 |

| 國際 | 列 | 跨度 | 判 |
|---|---|---|---|
| `global_daily` / `gl_prices_adj` / `prices_canonical` | 203,9xx | 2018-01-01 → 2026-09-12 | GREEN |
| `us_macro` | 284,805 | 1990 → 2026-09-13 | GREEN |
| `cross_macro` 6,144 · `sentiment_daily` 264 | | | GREEN |

**結論:VDF 台股半邊與國際半邊在操作員機器上都是綠的。** VDF「能不能跑」這題,答案是能。

### census 照出來、留給「VDF SSOT 化」的四件事

1. **哨兵/垃圾列**:`tw_daily_prices` MIN 日期 `1900-01-01`;`vdf_global_market_repo_ae7…` 的 `global_daily` 只有 1 列、日期 `1900-01-01`。
2. **庫層級的三副本病**:`vdf_tw_market_repo_a7752b3` / `vdf_global_market_repo_ae7…` 兩本 `_repo_` 副本庫與正庫並存(資料止於 2026-08-25,較舊)。哪一本是正本要有冊講。
3. **六張 0 列表**:`VRN_MDL004.duckdb` / `VRN_MDL005.duckdb` 各三張,全空。
4. **ABSENT 12 張**:9 張是 `vrn_mdl00X_*` 舊制表名(疑為 legacy 死路引用);其餘 `vrn_supportbridge`(32 檔在用)、`tw_ticker_regex`(11)、`consensus_current`(3)、`vrn_header_schema_registry_v1`(3)。

「SSOT 化」的第一步就是把這張表**寫成冊**(哪本庫、哪張表、誰寫、該有幾列以上、正本是哪一本),census 改成對冊比對,而不是靠 grep 猜。**冊還沒寫,這是下一批。**

### 批475 · VRN 八項真跑(容器;經 v0108 匯流排)

GREEN 6 · NODATA 1(`vrn_markdown` 無可轉檔=誠實)· ABSENT 1(`vrn_pdfplus` 需 reportlab;操作員機器上 via_vrn_312 已有,故那邊會綠)· **RED 0**。
附記:`vrn_digest` 內含 yfinance 取價,容器內連線失敗仍 `[計] OK 1 · FAIL 0`——取價是選配,按 FAIL 定義不算假綠;但它沒把「取價失敗 n」印進計數行,記為待改。

## 三 · 還掛著的事(誰都別忘)

| 代號 | 事 | 卡在哪 |
|------|----|-------|
| **A** | 姊妹倉 `tonykuni/VIA-VDF-VRN` 同步 | **工具層權限**。操作員在聊天裡授權過三次,但 `add_repo` 被自動模式的權限分類器擋下。聊天授權 ≠ 工具授權,我繞不過去。 |
| **D** | 批416 F2 逐家投信 PCF 端點查實 | 需網路 + 同意閘。**同意閘一律由操作員自己設,我不代設。** |
| ~~E~~ | ~~`tw_daily_prices` 名稱歸位~~ | **撤銷**:操作員機器上該表 2,128,169 列,在。批474 從容器副本得出的結論不成立。 |
| ~~F~~ | ~~正本頁再生閘~~ | **已擋**(批480 MDL138 v0101 正本頁保護)。 |
| **G** | VRN_MDL 數量 | 300 vs 294 的差取決於計數範圍(排除 references/_superseded 只數到 20 個唯一編號)——要用同一把尺再量,先記不判。 |
| **I** | VDF SSOT 化 | 庫冊 v0100 + census 對冊比(批478);唯讀審計(批485)。**批489 新知:你的 `vdf_tw_market.duckdb` 不在引擎寫死的 `output_hub/mega/`——冊上該補路徑**,`via-census` 頭幾行會印出來。 |
| **R** | ENG072 起手 140 秒靜默(GLE 探 7 個 OCR 後端) | 該像加速器一樣把探測結果快取;下一批。 |
| **S** | 資料家整併第二步:parquet 本體 + duckdb VIEW 管家的匯出/接點(`link`) | 等操作員貼 `via-datahome catalog` 與 `plan`;搬=link、不複製、刪=他的手(批490)。 |
| **T** | `via-vrnuni` 的官方名冊 CSV:把庫裡 `tw_listings`(MDL142 正典冊)橋成它認的欄名(code/name/yf_ticker/industry) | 小橋;做完 canonical ticker 才會填(批492)。 |
| ~~J~~ | ~~`vrn_digest` 取價失敗未進計數行~~ | **已改**(批484 v0114「取價缺 n」)。 |
| ~~K~~ | ~~樞紐同意閘覆寫式代設~~ | **已改**(批478,v0136 setdefault)。 |
| ~~L~~ | ~~「VERT」是哪個子系統~~ | **已解:VETF**(批477)。 |
| **N** | TWREV `fetch` 直呼 MOPS(requests;無 VIA 同意閘) | `via-twrev` 在外層擋(閘沒開=誠實停);引擎本體改走 `via_net` 是逐支工作,併入 M 佇列。 |
| **O** | VETF React 網站原始碼(63 tsx)未建置 | 需 node/npm;Standalone HTML 已可直接開。非本批範圍。 |
| **P** | `vdf_tw_market_repo_a7752b3` / `vdf_global_market_repo_ae7…` 兩本 `_repo_` 副本庫與正庫並存 | 庫層級三副本病;哪本是正本要有冊講(併入 I)。 |
| ~~M~~ | ~~7 支直呼網路的 VDF 引擎改走 `via_net`~~ | **活著的兩支已改**(批479);其餘五支是孤兒(0 import、0 調度),只記不動。 |
| ~~H~~ | ~~11 支引擎仍綁舊 `tw_listings`(891)~~ **量測結案(批484)**:讀 4 寫 1,你機器上 1,996 列,不成立 | 而 `tw_listings_industry` 有 1,978。**`VDF_ENG052`/`ENG081` 是寫入端,不可一律轉換。** |

---

## 四 · 這套系統的紀律(接手的人請先讀這段)

寫在這裡是因為**每一條都是付過代價換來的**,不是規範文件抄來的。

1. **先查再造 / 先量再改。** 本批光「量」就推翻了兩個既有結論。
2. **判錯的紅燈和假綠一樣傷。** 它讓人去 debug 一支行為完全正確的引擎。
   本工作階段點錯 **九盞**,全是我的。
3. **缺件 ≠ 缺料 ≠ 壞掉。** ABSENT / NODATA / RED 三態,不可混成一盞燈。
4. **FAIL 的定義只有一件事:數字抽出來了而且對不起來。**
5. **同一個判準寫兩個地方、只改一邊,另一邊靜靜走錯。**(批473 我自己又犯一次)
6. **只增不減 · 正本零觸碰 · 尾版律(新版號檔,不改舊檔)· Zero-Hydra(綁既有引擎,不重造)**
7. **零 CDN · 零彈窗(沒人要求就別跳)**
8. **同意閘(`VIA_NET_CONSENT` / `VIA_SCRAPE_CONSENT`)一律由操作員自己設,我不代設。**
9. **零 force push · 不 `Stop-Process` · 不 `Remove-Item` 環境 · `--approve-remove` 只在明令下。**
10. **台帳衝突取聯集,絕不取單邊。**
11. `VIA_Reports/*` 已在 `.gitignore`,產出不入 git。
12. SSOT 正本 `VIA_Financial_Institution_SSOT_v0100.py` 宣告 `canonical_write_mode = READ_ONLY`——**不改**。
13. **所有 VDF 價格資料都是 adj(除權息調整後);報告上寫的是報告日的原始價,兩者不可直接比。**

---

## 五 · 一貼即用(操作員工作站)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName

via-unstick                       # ① 先解開那個未完成合併(台帳取聯集)
git pull origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName

via-datahome status               # ①a 批491:鏡根 + 接點三態(LINKED/DEAD_LINK/LINKED_ELSEWHERE)
via-datahome link -DryRun -Relink # ①a' 只印重接計畫(不動)
via-datahome link -Relink         # ①a'' 重接死接點(只換接點,資料零觸碰;你的手)
via-datahome catalog              # ①b 批490:家內清點(C:\Users\tonyk\VIA System\via_database)→ 一頁目錄;把輸出貼回來
via-datahome plan                 # ①c 倉內散落整併計畫(只列不動)
via-census                        # ② C:庫況(批490 起家內也掃;預設一本庫一行,逐表加 -Tables)
via-vrnuni -SelfTest              # ②b 批492:你上傳的統一報告引擎 23 檢(免料)
via-vrnlogic -SelfTest            # ②c 批493:擷取中央邏輯庫十二檢
via-vrnlogic                      # ②d 邏輯庫現況(件數/法/後端健康)
via-ryg -Timeout 300              # ③ B:五矩陣紅黃綠燈,有心跳不白畫面,跑完自己跳出來
via-boot                          # ④ 啟動層實證:每支引擎起跑是否綁上加速器/網路件(同意閘不碰)
via-vetf                          # ⑤ VETF 持股×Consensus(candidate 沙盒;自動找你的兩本庫)
via-twrev demo                    # ⑥ 月營收 v2.7 免網路跑通;via-twrev fetch 要你自己開閘
via-famui all                     # ⑦ 家族頁再生(現在有正本頁保護,無資料時不會再把正本改成「缺」)
via-revphase -SelfTest            # ⑧ 月營收相位 v030 合成自測;去掉 -SelfTest 就讀你的庫真跑
via-etfhold -SelfTest             # ⑨ 主動 ETF 持股引擎 v1.1.0 27 檢(不碰正庫)
via-census -Hygiene               # ⑩ 庫衛生唯讀審計:哨兵列與副本庫,只數不刪;把輸出貼回來
via-manager                       # ⑪ 總控頁再生,bus_ryg/bus_census 按鍵才會出現
# 批486 起:任何 via-* 跑 python 時,第一次會看到 20 格點亮,之後每支引擎上方有動態進度條(跑了幾秒 · 引擎最後一行)
```
