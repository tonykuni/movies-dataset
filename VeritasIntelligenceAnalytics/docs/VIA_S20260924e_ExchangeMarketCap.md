# VIA 側線 2026-09-24 第五段 · 市值以交易所為主 · 成交量口徑具名(操作員令「成交量 成交值 市值都以交易所為主」)

> 主線批號由併線的手指定(L25)。上一段 = `docs/VIA_S20260924d_FetchDisciplineExchangePrimary.md`(已由 PR #106 併進 main)。
> 本段只做**不需要操作員許可、也不需要操作員裁定**的部分;要你做的、要你裁的,寫在第五、六節。

## 一 · 一句話

交易所不直接給市值,**但給發行股數**——而且總擷取 ENG055 的 L1 本來就在抓那一份公司基本資料,只是把「已發行普通股數」丟掉了。
本段把股數收下來(留史)、在 ENG057 建**全樹唯一一處**市值檢視表(交易所收盤 × 交易所股數),並讓 `tw_trading_daily` 每一列講得出是哪個來源表寫的。

## 二 · 量到的(全部是實量,附量法)

| # | 量到什麼 | 怎麼量 | 修在哪 |
|---|---|---|---|
| 1 | 交易所給發行股數的地方有四處:TWSE 公司基本資料 t187ap03_L「已發行普通股數或TDR原股發行股數」· TPEX 公司基本資料 `IssueShares` · TPEX 每日收盤 `Capitals`(每天)· TPEX rwd `otc?…&type=EW`「發行股數」。5483 在三處 TPEX 來源都是 641,221,651 | TPEX 三處容器直接打;TWSE 用樹上快照(openapi.twse 容器被擋) | ENG055 v0115 收前三處 |
| 2 | **ENG055 L1 抓了 t187ap03_L/_O,卻把股數那一欄丟掉**;L2 抓上櫃每日收盤,也把 `Capitals` 丟掉 | 讀碼 + 真回包 | 同一回包收下,零額外請求 |
| 3 | 股數會跳:同一檔兩份出表(08-05 → 09-24)之間差 ≥20% 的有 **20 檔**(8277 ×0.43 · 5355 ×0.47 · 4747 ×2.0 · 1799 ×2.0 …)。拿之後的股數回推舊日市值會差一倍以上 | ENG057 v0103 `mcap` 的跳動報表,真資料 | 市值分兩欄(嚴格/近似),跳動清單列出 → Z184 |
| 4 | 真資料端到端:L1 解析吃真回包(上市 1,087 檔用樹上快照、上櫃 893 檔用當天 openapi)→ 1,980 檔股數;樹上快照重放 1,977 列;市值檢視表:**上櫃嚴格 864 列**(最新 2026-09-23;前幾大 5274 7,666.4 億 · 6223 5,506.5 億 · 8299 4,897.0 億 · 6488 4,542.1 億 · 6274 4,216.1 億),其餘日子早於第一份股數 → 近似欄;上市在容器庫副本只到 2026-07-01(早於 08-04 出表)→ 全在近似欄 | 容器庫副本(不是真庫)+ 真回包 + 樹上快照 | — |
| 5 | 沒有股數的列(上櫃 4,720 · 上市 4,234)= 代號不在公司基本資料裡(ETF 之類),標 NO_SHARES,不猜 | 同上 | — |
| 6 | ENG057 的 upsert 缺欄**一律用 DOUBLE 補**,`src` 這種字串欄一加就 ConversionException | 自測 ⑫ 實跑當場抓到 | v0103 照 DuckDB 對 df 推得的型別補(同第四段修 ENG055 的做法) |
| 7 | `asof` 是 DuckDB 的保留字(ASOF 聯結),拿來當欄名 SQL 直接語法錯 | 雛型實跑 | 欄名 `asof_date` |
| 8 | 名稱口徑兩所不一:L1 上市取「公司簡稱」、上櫃取 `CompanyName`(全名);TPEX openapi 其實有 `CompanyAbbreviation` | 真回包 | 只記(會牽動名稱正典冊)→ Z183 要你裁 |
| 9 | main 的 PR #105(環境治理八中心 CGC_MDL135)新增 11 件元件沒進元件冊 | registry-sync 計畫 | 一併同步(元件冊唯一寫入口,只增不減) |

## 三 · 改了什麼(全是新版檔;舊版零觸碰,留作版史 L04)

| 檔 | 版 | 為什麼 | 自測 |
|---|---|---|---|
| `functional modules/VDF/engine/VDF_ENG055_OmniFetch_v0115.py` | v0114→v0115 | L1 同一回包收發行股數 → 新表 `tw_shares_issued`(鍵 asof_date · code · market;一份出表日一份,只增不改;出表日認不出=不收);L2 上櫃 `Capitals` 同表;L2 每列記 `src`;`--shares-snapshot` 重放樹上交易所快照(不觸網、不必同意閘、冪等);L1 與重放共用同一個解析 `_shares_rows` | 15/15(+⑭⑮) |
| `functional modules/VDF/engine/VDF_ENG057_TradingValueBackfill_v0103.py` | v0102→v0103 | 每列記 `src`,舊列不補(不冒名);`verify` 報來源分布;`mcap` → 檢視表 `tw_market_cap_daily`:`market_cap`(當天或之前最近一份股數)· `market_cap_later_shares`(第一份之前,用之後第一份近似,另欄)· `basis` 三態 · 股數跳動;`run` 抓完順手刷新;缺欄照型別補 | 13/13(+⑫⑬) |
| `supportive modules/registry/CGC_MDL064_SelftestGrid_v0482.py` | v0481→v0482 | 只改兩站站名的檢數(總擷取 十三→十五 · 成交值 十一→十三) | 相關站 OK(含 ENG092 三站、ENG085) |
| 冊(就地) | — | 主線端點冊 `VIA_VDF_TWMarketEndpoints_SSOT_v0100.json` 的 `market_cap`:規則改成交易所股數、Yahoo sharesOutstanding 只核對;加 `impl`(股數在 ENG055、檢視表在 ENG057)與操作員原話;**舊規則原樣留在 `rule_history`**。ENG092 自測照樣 14/14。元件冊(新 6 + main PR #105 的 11)· 正則清冊重建 · 帳一筆 · 掉球 | — |

## 四 · 怎麼證明

改壞測試(每一個都要紅;這一段起每一檢的例外只紅那一檢,不讓整支自測當掉):

| 檔 | 改壞版(全抓) |
|---|---|
| ENG055 v0115 | 新 7:L1 不收股數 · 出表日不驗 · L2 不記 src · Capitals 不存 · 股數表鍵少了 asof_date · 快照冒充即時來源 · 空快照夾不報 NODATA;另重跑 v0114 的 9 個,全抓 |
| ENG057 v0103 | 新 8:舊列補上 src(冒名)· ASOF 方向反了 · 近似併進嚴格欄 · 抓來的列不記 src · 跳動門檻失效 · 唯讀模式也建檢視表 · 新欄一律 DOUBLE · 日期不用 TRY_CAST;另重跑 v0102 的 9 個,全抓 |

另外量了:VCGC 37/37 · `ssot verify` rc0 · 本機照 CI 綠(契約 OK · UAT rc0)· 格子 v0482 相關站(總擷取 · 成交值 · ENG092 三站 · VATETF 橋)OK。

## 五 · 沒做的,為什麼

- **Z184 股數史**:第一份出表日之前的市值只有近似欄。上櫃有每日股數可回補(一日一請求),上市每日股數交易所沒有已知端點;20 檔股數跳動要逐檔對公開資訊——下一段。
- **Z185 跟其他看盤網站核對**:本段只做了交易所自己兩處互核;Yahoo marketCap 核對要走網路工具握手道 + 同意閘,下一段。
- **Z183 名稱口徑**:會動到名稱正典冊,要你裁。
- **仍在等你的**:Z161 · Z164 · Z165 · Z168 · Z170 · Z171 · Z177 · Z178 · **Z183** · **Z186**。

## 六 · 工作站要做的(依序;掉球 Z186,Z178 若還沒跑一起跑)

1. 本段併進 main 之後,拉到最新 main。
2. 開兩道同意閘:`$env:VIA_NET_CONSENT='YES'; $env:VIA_SCRAPE_CONSENT='YES'`
3. 在 `VeritasIntelligenceAnalytics` 夾下依序:
   - `via-py vdf "functional modules\VDF\engine\VDF_ENG055_OmniFetch_v0115.py" run --lane L1,L2`(抓公司基本資料與當日行情,收股數)
   - `via-py vdf "functional modules\VDF\engine\VDF_ENG055_OmniFetch_v0115.py" --shares-snapshot`(樹上快照重放,不觸網)
   - `via-py vdf "functional modules\VDF\engine\VDF_ENG057_TradingValueBackfill_v0103.py" run`(Z178;只抓缺的)
   - `via-py vdf "functional modules\VDF\engine\VDF_ENG057_TradingValueBackfill_v0103.py" mcap`(建市值檢視表 + 報表,不觸網)
   - `via-py vdf "functional modules\VDF\engine\VDF_ENG057_TradingValueBackfill_v0103.py" verify`(唯讀)
4. 輸出貼回。

## 七 · 還原

程式檔全是新版:刪掉新版檔(或 `git revert` 本段提交),尾版就回到上一版。冊是就地改的(端點冊的舊規則本來就留在 `rule_history`),`git revert` 即回。
本段沒有動任何 `.ps1`、沒有改任何 intake 正本、沒有設任何同意閘或金鑰環境變數、沒有裝任何套件;真端點只各打一次做量測,沒有經過引擎、沒有寫進任何真庫(實測用的是容器庫的副本)。
