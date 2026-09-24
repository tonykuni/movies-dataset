# VIA 側線 2026-09-24 第四段 · 擷取紀律五條 · 交易所為主(操作員令「自動進行實測自修正直到全部成功」)

> 主線批號由併線的手指定(L25)。上一段 = `docs/VIA_S20260924c_CanonMigrationPass3.md`(已由 PR #103 併進 main 9bae6d3b)。
> 本段只做**不需要操作員許可、也不需要操作員裁定**的部分;要你做的、要你裁的,寫在第六、七節。

## 零 · 本段收到的三道令(原話)

1. 「自動進行實測自修正直到全部成功」
2. 「擷取資料前要先檢查資料庫缺啥,確定擷取範圍去擷取,BATCH FETCHING 固定時間先暫存 避免重複擷取 整合資料庫去重補不足 確保完整性 VDF加速器跟網路工具都要導入並覆蓋深入所有指令細節動作」
3. 「所有數據都以交易所為主 但只有YFINANCE抓得到ADJ CLOSE所以可用他抓CLOSE ADJ CLOSE重複CLOSE是為了核對 成交量 成交值 市值都以交易所為主 可以跟其他看盤網站核對正確性」

第二道令我拆成五條,逐支引擎照這五條量、照這五條改:

| # | 紀律 | 落在哪 |
|---|---|---|
| ① | 擷取前先查庫缺啥 | ENG057 `db_done_lanes`:庫裡已有 (日, 市場) 且開高低齊的,算已完成;換機器、整併來的日子不重抓 |
| ② | 只抓確定的範圍 | 已完成 = checkpoint ∪ 庫內已有;待抓清單只剩缺的 |
| ③ | 批次、定量暫存、可續 | 正典 `batch_fetch`:每 N 件落庫 + checkpoint;Ctrl+C 先落盤再停(rc 130),下次從斷點續 |
| ④ | 去重、補不足、報完整性 | ENG057 `upsert`:鍵已在的列只補空欄(COALESCE,不覆蓋);鍵不在才插;跑完印逐市場「有料日 / 日曆日」與缺的日 |
| ⑤ | 加速器與網路工具覆蓋每一個動作 | 網路一律走統包 SUP_MDL740(新 `curl_bytes` 位元組車道);ENG055/056/057 **自己開 curl 的後備全拿掉**;平行走加速器 `accel_map` |

## 一 · 一句話

五條紀律做成**一份正典**(`SUP_MDL753` 的 `batch_fetch` / `BatchProgress` / `fmt_eta`),籌碼 ENG056、成交值 ENG057 都改呼叫它;
成交值 ENG057 升成**交易所的日行情表**(開高低收量值筆數,交易所為主),並多一個唯讀 `verify`:交易所收盤 × Yahoo 收盤逐列核對。
順帶把一個**跟著機器走的假紅**修掉(VRN 鏈跑器把「庫不在」的存證報成 ok)。

## 二 · 量到的(全部是實量,附量法)

| # | 量到什麼 | 怎麼量 | 修在哪 |
|---|---|---|---|
| 1 | ENG055 L10(央行利率)· L11(恐懼貪婪)、ENG056、ENG057 都有**自己開 `curl` 的後備**——不經同意閘、不經網路工具的法遵層 | 逐支 grep `subprocess` / `curl` | 統包新增 `curl_bytes`;三支改走它,統包缺這條車道就誠實停(rc1 / FAIL),不再退回生 curl |
| 2 | ENG056 v0102 的批次迴圈用 `range(0, n, chunk)` 步進,**自癒把工數減半之後 chunk 變小,步進還是舊的** → 中間一段項目被跳過、而且不記 done | 正典 ㊵ 同一個情境(14 件、前 8 件傳輸敗觸發自癒 4 工 → 2 工)拿舊寫法重跑:只處理 12 件、**最後 2 件整個沒碰**,done 4 / 應 6 | 正典 `batch_fetch` 改 while 迴圈 `i += len(part)`;㊵ 驗 14 件一件不漏 |
| 3 | 成交值 ENG057 只收收盤,**開高低沒收**——同一個回包裡明明就有(操作員令「所有數據以交易所為主」) | 容器直接打一次真端點(不經引擎、不落庫):TWSE MI_INDEX 表頭有 開盤價/最高價/最低價;TPEX dailyQuotes 有 開盤/最高/最低 | v0102 同一回包一次收齊;真回包餵解析器:TWSE 1,093 檔 · TPEX 890 檔 · 開高低收順序 0 違規 · 沒成交的 25 檔四價皆空 |
| 4 | 交易所收盤 × Yahoo 收盤(容器庫副本,480,660 對列):一樣 86.0% · 配股段 13.4%(Yahoo 事後按配股回調,正常)· **當天跳開、前後一致 3,063 列(0.6%)**=Z175 那種陳價 | ENG057 v0102 `verify`(容差 0.5%;前後一致才判 STALE_1D) | 只報不改(資料面在 Z175);例:4154 2024-08-16 比值 1.0、前後 1.4484 |
| 5 | 兩邊各缺:只在交易所 335,307 列、只在 Yahoo 94,273 列;**Yahoo 表整個沒有上市(TWSE)**;Yahoo 上櫃薄日 2025-08-01;交易所上櫃薄日 77 天 | 同上 `verify` | 補的是 ENG057 `run`(要同意閘)→ Z178 |
| 6 | **成交量 Yahoo 一律 ≤ 交易所**:2026-09-23 上櫃 868 檔,收盤與開高低 868/868 一樣,量只有 325 檔在 1% 以內,中位 98.4%、沒有一檔 Yahoo 比較多 | 真端點回包 × 容器庫 Yahoo 同日列 | 證實「成交量以交易所為主」是對的;量的口徑另見 #7 |
| 7 | **交易所自己的表,量的口徑也不一樣**:5483 在 2026-09-23,TPEX dailyQuotes 41,907,426(不是整千)· otc「不含定價」41,028,000(整千)· Yahoo 41,111,613。ENG057 啟動時探第一個會答的 TPEX 變體,跨次執行有可能混到不同口徑 | 三個 TPEX 變體同日各打一次 | 本段只記(Z180);下一段逐列記來源表 |
| 8 | 市值:交易所不直接給。發行股數交易所給了三處——TPEX openapi 公司基本資料 `IssueShares`(出表 1150924)· TPEX openapi 每日收盤 `Capitals`(每天)· TPEX rwd `otc?…&type=EW`「發行股數」(5483 皆 641,221,651);TWSE 公司基本資料 t187ap03_L「已發行普通股數或TDR原股發行股數」(樹上 2026-08-05 快照;openapi.twse 容器被擋)。**ENG055 L1 本來就在抓 t187ap03_L/_O,卻把這一欄丟了**;主線 ENG092 冊寫「發行股數來自 Yahoo」 | 真端點 + 樹上快照 | 本段只記(Z179);下一段:L1 同一回包收股數(零額外請求),市值不在 ENG057 另寫一份(ENG092 已宣告這一欄,Zero-Hydra) |
| 9 | 調整後價格層的因子是 Yahoo adj ÷ Yahoo close,**配股不在因子裡**(Z173);VATETF 橋拿 adj ÷ factor 還原收盤 | 合成配股例:只乘因子 110×f ≠ adj,再乘配股段才等於 adj | ENG060 欄上具名 `factor_basis`;ENG085 收盤改取交易所 |
| 10 | VRN 鏈跑器 ⑪ 在側線樹上紅、在 main 乾淨樹上綠——**同一份碼**。容器上那張矩陣存證是 ENG083 自己寫的 `{"state":"ABSENT","why":"庫不在…"}`,`data_evidence()` 只問檔在不在,檔在就 ok=True,研報 0 份還掛 ok | 兩棵樹對照 + 讀存證 | CGC_MDL172 v0105:存證自己的態算數;㉖ 四份合成存證,不看本機 |
| 11 | 自測格子站名的檢數又過時七站(VATETF 橋寫八檢,v0104 已十一) | 逐支 `--selftest` 實數 | 格子 v0481 |
| 12 | 交易所端點容器可達性變了:`www.twse.com.tw/rwd`(MI_INDEX)與 `www.tpex.org.tw/www`、TPEX openapi **可達、真料**;openapi.twse 仍回 800B 安全頁 | 各打一次 | 記進 Z170 |
| 13 | **推之前抓到一個本段自己造成的跨引擎回歸**:`tw_trading_daily` 是兩支共用的表(ENG055 L2 寫最新一天、ENG057 寫歷史)。ENG057 v0102 替它加了開高低三欄;ENG055 的 `upsert` 是 `INSERT INTO t SELECT * FROM df`(照欄位次序),表一多欄,L2 **每一次都炸** `BinderException: table tw_trading_daily has 10 columns but 7 values were supplied` | 暫存庫兩種先後各跑一次,兩次都炸 | ENG055 v0114 `upsert` 改照欄名插入、這批多的欄照型別補;L2 同一回包收開高低;+⑬ |
| 14 | 上櫃兩條交易所來源是同一口徑:TPEX rwd dailyQuotes 與 TPEX openapi 每日收盤 2026-09-24 四碼 890 檔,成交股數 **890/890 完全一樣**(ENG055 L2 與 ENG057 寫進同一張表不會混口徑);上市的 openapi STOCK_DAY_ALL 容器被擋,對不了 | 兩個端點同日各打一次 | 記進 Z180 |

## 三 · 改了什麼(全是新版檔;舊版零觸碰,留作版史 L04)

| 檔 | 版 | 為什麼 | 自測 |
|---|---|---|---|
| `supportive modules/SUP_MDL753_VIACommonUtils_v0108.py` | v0107→v0108 | +`batch_fetch`(批次擷取正典:加速器平行 · 定量落盤 · checkpoint · 自癒減工不跳項 · Ctrl+C 安全)· +`BatchProgress`(進度列 + JSON 心跳,原 ENG056 那一份搬進來)· +`fmt_eta` | 40/40(+㊵) |
| `supportive modules/network/SUP_MDL740_NetUnified_v0114.py` | v0113→v0114 | +`curl_bytes`(位元組車道:二進位檔、要逐位元組保留原文的回包;同樣過雙閘) | 22/22(+㉒) |
| `functional modules/VDF/engine/VDF_ENG055_OmniFetch_v0114.py` | v0113→v0114 | L10 央行利率(xls)· L11 恐懼貪婪改走 `curl_bytes`;統包缺這條車道=FAIL 講明要 v0114+,不自己開 curl;L11 原文逐位元組保留;`upsert` 照欄名插入(#13);L2 收開高低 | 13/13(+⑫⑬) |
| `functional modules/VDF/engine/VDF_ENG056_ChipBackfill_v0103.py` | v0102→v0103 | 批次迴圈改呼叫正典 `batch_fetch`(修掉 #2 的跳項);進度列綁正典;生 curl 後備拿掉;沒有網路工具 = rc1 | 10/10(+⑩) |
| `functional modules/VDF/engine/VDF_ENG057_TradingValueBackfill_v0102.py` | v0101→v0102 | 交易所開高低一併收;先查庫缺啥(`db_done_lanes`)→ 只抓缺的 → `batch_fetch`(加速器 · 每 40 件落庫)→ 完整度報告;`upsert` 補空欄不覆蓋;+`verify`(唯讀核對);生 curl 後備拿掉 | 11/11 |
| `functional modules/VDF/engine/VDF_ENG060_AdjPriceLayer_v0107.py` | v0106→v0107 | +`factor_basis` 欄(因子基準具名);自測改建在暫存庫(真庫唯讀掛上,L17);⑨ 配股段例 | 9/9(+⑨) |
| `functional modules/VDF/engine/VDF_ENG085_VatetfBridge_v0105.py` | v0104→v0105 | 收盤取交易所 `tw_trading_daily`(同日同檔、>0),沒有才退 adj ÷ factor;逐類計數 `close_basis` | 12/12(+⑫) |
| `supportive modules/registry/CGC_MDL172_VRNChainRunner_v0105.py` | v0104→v0105 | 存證自己寫 ABSENT/NODATA/FAIL、或 0 份研報,就不准報 ok(why 照轉存證的);舊版無 state 的存證照舊 | 廿六檢(28 檢)28/28 |
| `supportive modules/registry/CGC_MDL064_SelftestGrid_v0481.py` | v0480→v0481 | 只改七站站名的檢數(總擷取 十一→十三 · 籌碼 九→十 · 成交值 六→十一 · 調整後價格層 八→九 · VATETF 橋 八→十二 · VRN 鏈 廿五→廿六 · 共用小工具正典 三十九→四十);別的尺拿站名當鑰匙的字一個不動 | 相關八站 OK 8 |
| 冊(就地) | — | 元件冊(registry-sync 兩回:新 31 · 變更 278 · 退役 10,退役的 10 件全是 ENG056 搬進正典的進度列與 ETA〔Zero-Hydra〕;ENG055 修正後再同步 新 2 · 變更 83 · 退役 0)· 正則清冊(CGC_MDL115 重建,樣式 1372 · 共用 726)· 自動編號帳一筆 · 掉球 | — |

## 四 · 怎麼證明(每一檢都有負控或改壞版)

改壞測試:每一支都拿「把修正拿掉」或「改回舊寫法」的改壞版餵自測,檢要紅。

| 檔 | 改壞版(全抓) |
|---|---|
| 正典 v0108 | 5:**原本 ENG056 的 range 步進跳項** · 傳輸敗(None)記成 done · 不定量落盤 · 不走加速器 · 中斷不落盤 |
| 網路工具 v0114 | 3:不過閘 · 回包被解成文字(不是位元組)· 失敗還帶 data |
| ENG055 v0114 | 9:拿掉統包檢查 · 原文改成重新序列化(fixture 刻意不是 `json.dumps` 的輸出,否則抓不到)· follow 反了 · 退回 subprocess · **改回照次序插入** · 不補新欄 · 新欄一律加成 DOUBLE · L2 上市不收開高低 · L2 上櫃不收開高低 |
| ENG056 v0103 | 4:生 curl 後備回來 · 不檢工具 · 進度標籤掉了 · 不落 checkpoint |
| ENG057 v0102 | 9:不從庫重建 done · 不要求開高低 · 覆蓋已有值 · 不補空欄 · 生 curl 回來 · SAME 判在 STALE 之前 · 不解析開盤 · 不報薄日 · 整市場缺席當成薄日 |
| ENG060 v0107 | 4:view 掉了 `factor_basis` · 基準字寫錯 · 自測寫真庫 · 因子被改 |
| ENG085 v0105 | 3:不取交易所 · 暫欄 `close_basis` 留在表上 · 先退 adj ÷ factor(次序反了);另有負控:沒有交易所表時照舊 adj ÷ factor |
| MDL172 v0105 | 5:不看存證態 · 0 份算 ok · 忽略路徑參數 · 拿掉非物件防護 · 只擋 NODATA |

另外量了:
- **真端點**(不經引擎、不落庫、不開同意閘):ENG057 的兩個解析器吃真回包,結果見第二節 #3、#6。
- **VCGC 三十七檢** 37/37(registry-sync 之後)· `ssot verify` rc0(黃燈五盞都是既有的操作員裁定項)· 本機照 CI(契約 OK · UAT rc0)。
- **全格 v0481**:見第五節。

## 五 · 全格實跑(容器,v0481)

**OK 334 · FAIL 7 · SKIP 14 · TIMEOUT 0**(1063 秒)。本段開工前同一棵樹用 v0480 跑是 OK 332 · FAIL 9 · SKIP 14——轉綠的兩站:
VRN 六層鏈(CGC_MDL172 v0105 修掉存證假 ok)、Veritas 中央控管台(新檔同步進元件冊)。全格重寫的 37 個已追蹤產出檔(報表頁、UI 頁、四本自動冊)全部還原,**不提交**。

剩下的紅燈 **main 乾淨樹同樣紅**,全是環境或他線,逐站記在 Z181:
工具升階梯(OCR/TA 階梯態隨裝件而變)· 治理台 UI Matrix(綠燈率 = 全格實跑,其餘紅燈的連帶)· 首頁文字擷取 ⑪ 與 VRN 統一報告引擎(容器沒有 pdfplumber)·
VRN 六層鏈實跑(ENG072/ENG073 要 pydantic)· VRN 第二血統總驗(容器沒有 python-docx,而那支測試的跳過條件漏看 docx → Z182 交 VRN 線)·
CGC_MDL120 ⑥(產生頁 `VIA_UI_ETFConsensusAnalysis_v0100.html` 在 gitignore、容器沒產)。**本段沒有造成任何一盞新紅**。

## 六 · 沒做的,為什麼

- **市值(Z179)**:交易所給發行股數、不給市值;主線 ENG092 已宣告市值這一欄(冊寫發行股數來自 Yahoo,跟 09-24 令不合)。在 ENG057 另寫一份市值就是第二顆頭,所以下一段做:發行股數表(交易所來源、asof、具名)+ 市值 = 交易所收盤 × 交易所股數;ENG092 冊的規則要改指向它——那一行由併線的手裁。
- **成交量口徑(Z180)**:下一段 ENG057 逐列記來源表,`verify` 報口徑分布。
- **跟其他看盤網站核對**:本段核的是 Yahoo(收盤、開高低、量)與交易所自己的不同表;別的網站要先定哪幾家、用哪個端點,不猜。
- **其他引擎的擷取紀律**:VDF_ENG089 `audit` 另外報 ENG047/050/058/072 有重抓風險,排在後面逐支做。
- **仍在等你的**:Z161 · Z164 · Z165 · Z168 · Z170 · Z171 · Z177 · **Z178**(本段新增)。

## 七 · 工作站要做的(依序;掉球 Z178)

1. 本段併進 main 之後,拉到最新 main。
2. 開兩道同意閘:`$env:VIA_NET_CONSENT='YES'; $env:VIA_SCRAPE_CONSENT='YES'`
3. 在 `VeritasIntelligenceAnalytics` 夾下:
   `via-py vdf "functional modules\VDF\engine\VDF_ENG057_TradingValueBackfill_v0102.py" run`
   ——它會先印「庫裡已有 N 件、待抓 M 件」,只抓缺的(舊列沒有開高低的日子會重抓一次補開高低,已有的值不動);中途可 Ctrl+C,下次從斷點續。
4. 跑完再一次(唯讀、不觸網):`via-py vdf "functional modules\VDF\engine\VDF_ENG057_TradingValueBackfill_v0102.py" verify`
5. 兩段輸出貼回。Z177 那七行唯讀指令如果還沒貼,一起貼。

## 八 · 還原

程式檔全是新版:刪掉新版檔(或 `git revert` 本段提交),尾版就回到上一版。冊(元件冊 · 正則清冊 · 帳 · 掉球)是就地改的,`git revert` 即回。
本段沒有動任何 `.ps1`、沒有改任何 intake 正本、沒有設任何同意閘或金鑰環境變數、沒有裝任何套件;真端點只各打一次做量測,沒有經過引擎、沒有寫進任何庫。
