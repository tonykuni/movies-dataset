# VIA 交接紀錄 · 批474(2026-09-13)

> 立案:操作員令「**卡斷了 不卡斷 PS20個加速器 上傳GITHUB附上交接紀錄 B C**」。
> 這份檔的目的只有一個:**下一個接手的人(或下一個工作階段)不必看對話紀錄就能接上**。
> 對話會卡斷,檔案不會。所以凡是「只有我知道」的東西,一律寫進這裡。

---

## 〇 · 你現在最該先做的一件事(操作員工作副本卡住了)

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

## 二 · C 的答案:VDF 現況(**容器內副本實測,不是操作員機器**)

> ⚠️ **這一節的數字來自 GitHub 副本裡的 .duckdb,不是操作員工作站上的庫。**
> 兩者可能差很多。操作員機器上的真相要打 `via-census` 才知道。
> 這條警語是有意寫的:拿容器的數字去說操作員的機器,就是另一種判錯的紅燈。

`vdf_tw_market.duckdb`(容器副本 5.5MB):

| 表 | 列 | 日期跨度 | 判 |
|----|----|---------|-----|
| `tw_listings_industry` | 1,978 | — | GREEN |
| `tw_listings` | 891 | — | GREEN(**但只有 891,見下** ) |
| `tw_rates_cbc` | 308 | 2001-01-01 → 2026-08-01 | GREEN |
| `etf_book` | 271 | — | GREEN |
| `tw_valuation_daily` | 2,656 | 2026-09-08 → 09-11(**4 天**) | AMBER |
| `tw_trading_daily` | 1,773 | 2026-09-08 → 09-11(**4 天**) | AMBER |
| `tw_daytrade_market` | 9 | 2026-09-01 → 09-11 | AMBER |
| `tw_market_agg` | 6 | 2026-09-01 → 09-08 | AMBER |
| `consensus_daily` / `consensus_latest` / `tw_monthly_revenue` / `monthly_revenue_analysis` | **0** | — | **NODATA ×4** |

`vdf_global_market.duckdb`(國際半邊):

| 表 | 列 | 日期跨度 | 判 |
|----|----|---------|-----|
| `global_daily` | **47,973** | 2024-01-02 → 2026-09-11 | **GREEN** |
| `sentiment_daily` | 253 | 2025-09-11 → 2026-09-11 | GREEN |
| `cross_macro` | 103 | 2018-01-01 → 2026-07-01 | GREEN |
| `etf_stats_daily` | 104 | 2026-09-09 → 09-13 | AMBER |
| `index_valuation_proxy` | 78 | 2026-09-11 → 09-13 | AMBER |

### 誠實的結論

- **國際半邊 = 綠**。`global_daily` 47,973 列橫跨兩年半,那是真的在跑。
- **台股半邊 = 黃/紅**。價格與估值只有 **4 天**;四張表 **0 列**。
- **最大的一筆:`tw_daily_prices` 這張表,全樹沒有任何一本庫有它——
  而 121 個檔案在 SQL 語境裡用它。** 另外 `tw_chip_inst`(33 檔)、
  `tw_prices_adj`(30 檔)、`tw_chip_margin`(18 檔)同樣不存在。

  容器副本裡台股價格實際住在 **`tw_trading_daily`**。
  所以這是**名字對不上**,不是「資料抓失敗」——
  批471 那次 `vap_stack` 報 `Table tw_daily_prices does not exist`,
  當時記成「VAP 側缺陷」,**現在看那個判斷是錯的**:
  VAP 沒壞,它要的表本來就不叫那個名字。

  ⚠️ **但在操作員機器上可能相反**(那邊的庫大得多)。
  所以本批**沒有**去改任何一個 `tw_daily_prices` 的引用——
  先量再改;量的地方不對,改下去就是災難。
  **下一步是操作員打 `via-census`,把那台機器的真相貼回來。**

---

## 三 · 還掛著的事(誰都別忘)

| 代號 | 事 | 卡在哪 |
|------|----|-------|
| **A** | 姊妹倉 `tonykuni/VIA-VDF-VRN` 同步 | **工具層權限**。操作員在聊天裡授權過三次,但 `add_repo` 被自動模式的權限分類器擋下。聊天授權 ≠ 工具授權,我繞不過去。 |
| **D** | 批416 F2 逐家投信 PCF 端點查實 | 需網路 + 同意閘。**同意閘一律由操作員自己設,我不代設。** |
| **E** | `tw_daily_prices` 名稱歸位(121 檔) | 等 `via-census` 在操作員機器上的實測結果。**先量再改。** |
| **F** | 正本頁再生閘 | 在無資料環境跑 `via-famui`,會把操作員的正本 UI 頁改寫成「缺(誠實)」。本工作階段手動 `git checkout --` 復原 4 次。MDL138 應該自己擋住這件事,現在沒擋。 |
| **G** | VRN_MDL 數量 | 操作員總表寫 300,實掃 **294**。差 6 支,還沒逐支列出是哪 6 支。 |
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
via-ryg                           # ③ B:五矩陣紅黃綠燈,跑完自己跳出來
```
