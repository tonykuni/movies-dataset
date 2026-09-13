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
| **F** | 正本頁再生閘 | 在無資料環境跑 `via-famui`,會把操作員的正本 UI 頁改寫成「缺(誠實)」。本工作階段手動 `git checkout --` 復原 **5** 次。MDL138 應該自己擋住這件事,現在沒擋。 |
| **G** | VRN_MDL 數量 | 操作員總表寫 300,實掃 **294**。差 6 支,還沒逐支列出是哪 6 支。 |
| **I** | VDF SSOT 化:庫冊(哪本庫/哪張表/誰寫/最少幾列/正本是哪本) | 第二節四件事是輸入。下一批。 |
| **J** | `vrn_digest` 取價失敗未進計數行 | 待改;不是假綠但不夠誠實。 |
| **K** | 樞紐 `_launch_locked` 對 net 項目**覆寫式**設 `VIA_NET_CONSENT/VIA_SCRAPE_CONSENT="YES"` | 批408 從六個短令拔掉的那種代設;且 "YES" 過不了閘二 token 檢查。本批只記不動,等明令。 |
| **L** | 「VERT」是哪個子系統 | 樹上不存在(命中全是 `Converter` 子字串)。**要問操作員。** |
| **M** | 7 支直呼網路的 VDF 引擎改走 `via_net` | 逐支新版本檔;bootstrap 已把 `via_net` 送到門口。 |
| **H** | 11 支引擎仍綁舊 `tw_listings`(891) | 而 `tw_listings_industry` 有 1,978。**`VDF_ENG052`/`ENG081` 是寫入端,不可一律轉換。** |

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

via-census                        # ② C:你那台機器的庫況真相(唯讀)
via-ryg -Timeout 300              # ③ B:五矩陣紅黃綠燈,有心跳不白畫面,跑完自己跳出來
via-boot                          # ④ 啟動層實證:每支引擎起跑是否綁上加速器/網路件(同意閘不碰)
```
