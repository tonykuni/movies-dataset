# 台股個股清單 / 主動式台股 ETF 清單 —— 能不能生成,現況判決(操作員 2026-11-08 令)

操作員問:「是否有[辦法]可以生成台股個股清單 / 生成驗證主動式台股ETF清[單]」,
U/I 以 `VRN-RECONCILE · 20261108_080735 · READ-ONLY · 零落庫 / OCR EXTRACTION × SSOT v2 /
CONTENT RECONCILE MATRIX / 覆蓋層+內容層對帳(鍵=pdf_name↔source_document)· 記錄 64 ·
分佈 {"FIRSTPAGE": 64}` 為視覺鎖定。本文是那次全查的收據。

視覺鎖定頁:`claude.ai/artifact/5jrCmWEQb42dsKAqS2pqGW`(Atlas `--vl-*` 唯一正本,色值字級照抄)。

## ⓿ 一句話答案(不對稱)

| 問 | 答 | 根據 |
|---|---|---|
| 主動式台股 ETF 清單能生成並驗證嗎? | **已經做完了、已驗證、已進版控** | `TW_Active_ETF_Registry_v0100.json` 38 筆 · as_of 2026-10-03 16:18 · VERIFIED_OPENAPI 30 |
| 台股個股清單能生成嗎? | **車道在、指令在、桌機跑過 1,981;但冊沒刷、輸出不進倉** | `TW_Equity_Registry_v0100.json` 只有 6 檔種子 · as_of 空 · history 0 |

兩邊卡的是同一件事:`VIA_NET_CONSENT` + `VIA_SCRAPE_CONSENT`。**那兩個我不代設**(操作員政策),
所以本輪只驗引擎、不產清單。

## ① 主動式 ETF 冊:38 筆的組成

正本 `supportive modules/VIA_FlowSystem/FlowSystem_v2/config/TW_Active_ETF_Registry_v0100.json`
(`schema tw-active-etf-registry-v1` · `verify_required true` ·
端點 `openapi.twse.com.tw/v1/opendata/t187ap47_L` 與 `/v1/fund/T86`)。

* **A 尾 31 檔**(主動股票型):00400A–00410A(11)+ 00980A–00999A(20)
* **D 尾 7 檔**(主動債券):00980D–00986D —— IN-02 明文排除
* 狀態:`VERIFIED_OPENAPI` 30 · `PENDING_VERIFY` 5 · `NAME_MISMATCH_OPENAPI` 3
* 驗證者 `FLOW_ENG023_FlowTwActiveEtf_v0101`,真的連過官方名錄:
  `openapi: twse_etf_list 271 · twse_day_all 1380 · official_codes 1411`
* history 三筆:批104 SYNC(2026-08-23,+34 · conflicts 3)→ refresh-resolve(2026-10-03 05:02,
  解掉 00980A/00981A/00982A 名碼衝突)→ refresh-resolve(2026-10-03 16:18)

A 尾 31 檔逐列(代號 · 名稱 · 投信 · 狀態):

| 代號 | 名稱 | 投信 | 狀態 |
|---|---|---|---|
| 00400A | 主動國泰動能高息 | 國泰投信 | VERIFIED_OPENAPI |
| 00401A | 主動摩根台灣鑫收 | 摩根投信 | VERIFIED_OPENAPI |
| 00402A | 主動安聯美國科技 | 安聯投信 | VERIFIED_OPENAPI |
| 00403A | 主動統一升級50 | 統一投信 | VERIFIED_OPENAPI |
| 00404A | 主動聯博動能50 | 聯博投信 | VERIFIED_OPENAPI |
| 00405A | 主動富邦台灣龍耀 | 富邦投信 | VERIFIED_OPENAPI |
| 00406A | 主動中信台灣收益 | 中國信託投信 | VERIFIED_OPENAPI |
| 00407A | 主動凱基台灣 | 凱基投信 | VERIFIED_OPENAPI |
| 00408A | 主動第一金優股息 | 第一金投信 | VERIFIED_OPENAPI |
| 00409A | 主動復華全球50 | (冊內空白) | VERIFIED_OPENAPI |
| 00410A | 主動永豐科技趨勢 | 永豐投信 | VERIFIED_OPENAPI |
| 00980A | 主動野村臺灣優選 | 野村投信 | VERIFIED_OPENAPI(首檔) |
| 00981A | 主動統一台股增長 | 統一投信 | VERIFIED_OPENAPI |
| 00982A | 主動群益台灣強棒 | 群益投信 | VERIFIED_OPENAPI |
| 00983A | 主動中信ARK創新 | 中國信託投信 | VERIFIED_OPENAPI |
| 00984A | 主動安聯台灣高息 | 安聯投信 | VERIFIED_OPENAPI |
| 00985A | 主動野村台灣50 | 野村投信 | VERIFIED_OPENAPI |
| 00986A | 主動台新龍頭成長 | 台新投信 | VERIFIED_OPENAPI |
| 00987A | 主動台新優勢成長 | 台新投信 | VERIFIED_OPENAPI |
| 00988A | 主動統一全球創新 | 統一投信 | VERIFIED_OPENAPI |
| 00989A | 主動摩根美國科技 | 摩根投信 | VERIFIED_OPENAPI |
| 00990A | 主動元大AI新經濟 | 元大投信 | VERIFIED_OPENAPI |
| 00991A | 主動復華未來50 | 復華投信 | VERIFIED_OPENAPI |
| 00992A | 主動群益科技創新 | 群益投信 | VERIFIED_OPENAPI |
| 00993A | 主動安聯台灣 | 安聯投信 | VERIFIED_OPENAPI |
| 00994A | 主動第一金台股優 | 第一金投信 | VERIFIED_OPENAPI |
| 00995A | 主動中信台灣卓越 | 中國信託投信 | VERIFIED_OPENAPI |
| 00996A | 主動兆豐台灣豐收 | 兆豐投信 | VERIFIED_OPENAPI |
| 00997A | 主動群益美國增長 | 群益投信 | VERIFIED_OPENAPI |
| 00998A | 主動復華金融股息 | 復華投信 | **PENDING_VERIFY**(同時在 VDF 退役冊) |
| 00999A | 主動野村臺灣高息 | 野村投信 | VERIFIED_OPENAPI |

D 尾 7 檔(IN-02 排除,僅記錄):00980D 主動野村優選非投等債 · 00981D 主動統一美債 ·
00982D 主動群益優選非投等債 · 00983D 主動中信優選投等債 · 00984D 主動安聯美元債 ·
00985D 主動野村全球債 · 00986D 主動第一金優選債。

## ② 38 / 31 / 30 / 25 / 22 的對帳(為什麼數字不一樣)

| 數 | 它是什麼 | 出處 | 比上一行少掉誰 |
|---|---|---|---|
| 38 | 主動式 ETF 全冊(含債券) | TW_Active_ETF_Registry_v0100 | — |
| 31 | A 尾 = 主動股票型 | 尺 `^00[0-9]{3}A$` | 扣 D 尾主動債券 7 檔 |
| 30 | A 尾且官方名錄驗過 | status = VERIFIED_OPENAPI | 扣 00998A(PENDING_VERIFY) |
| 25 | 再扣海外成分 | **我依名稱的判讀,非冊上欄位** | 扣美國科技 / 全球 / ARK 等 6 檔 |
| 22 | 「主動式台股 ETF 全驗證」 | 桌機實錄 2026-09-28 12:16:08 | 再扣持股未驗證者(IN-02 要 `verified==True`) |

**22 就是操作員問的「生成並驗證」的那份清單。** 它比 31 少不是漏抓,是 IN-02 三道排除:
D 尾債券 · 國外成分 · 無持股揭露。

另:`VDF_ActiveETF_Retired_SSOT_v0100.json` 記 00998A 由操作員 2026-10-13 裁定退役,
根因正是「TWSE t187ap47_L A 碼 31 · 既有快照 32 → ENG077 報官方冊消失 1 → rc 2」。
**Registry 的 PENDING_VERIFY 與 VDF 的退役冊,對同一檔的自報是一致的。**

## ③ 個股清單:兩條路都在,兩條都沒落到倉裡

### 3-1 FlowSystem 路(冊沒刷)

`TW_Equity_Registry_v0100.json`:`policy` 寫明「官方普通股名單 SSOT;`--refresh-equity`
經同意閘自 OpenAPI 併冊(append-only);種子候校驗」。現況 **6 筆**:
2330 台積電 · 2317 鴻海 · 6488 環球晶(TPEX)· 3665 貿聯-KY · 1305 華夏(以上 SEED_KNOWN)·
1815 富喬(SEED_NAME_ONLY,市場別候官方冊校驗,誠實不臆填)。`as_of` 空 · `history` 0 筆。

刷的實作在 `FLOW_ENG024_FlowRegistryOps.py` L102 `cmd_refresh_equity()`:
TWSE `t187ap03_L` + TPEX `mopsfin_t187ap03_O`,逐列取 `公司代號 / 公司簡稱`,
新碼標 `VERIFIED_OPENAPI`,append-only;`VIA_ACCEL` 未載或 fetch 失敗一律印 `[SKIP] …(誠實)`
並保持既有態 —— 沒有假填。

### 3-2 VDF 路(桌機跑過,輸出不進版控)

冊 `functional modules/VDF/VDF_InputUniverse_SSOT_v0104.json`,`/source` 就是操作員自己的
R49 令(2026-10-02):「只有台灣個股全部及主動式台股ETF…加權 櫃買資訊跟上面全抓當輸入
VDF SYSTEM MANAGER管理」。

* IN-01 台灣全部個股 `^[1-9][0-9]{3}$`(正例 2330/1101/9958 · 反例 0050/91234/2330.TW/２３３０)
  · 下限 TWSE 900 / TPEX 700 家(任一所 0 = RED · 低於 = AMBER)
* IN-02 主動式台股 ETF `^00[0-9]{3}A$` · 要 `ACTIVE_DOMESTIC` + holdings_daily 有持股列
* IN-03 TAIEX / TPEX 指數(官方 > yfinance 代理)
* 引擎 E-01…E-12,15 步 loop;`/loop/rule` 明寫「觸網站要操作員自己開同意閘
  (VIA_NET_CONSENT / VIA_SCRAPE_CONSENT),本冊與管理員不代設」
* OUT-01 落點 `(再生件)VIA_Reports/vdf/universe/VDF_UNIVERSE_latest.csv / .json`
  欄位 Seq · Group · Code · Name · Market · YF Ticker · BB Ticker · Industry · Issuer · 持股已驗證

桌機實錄:
* 2026-09-28 12:16:08(R15 首跑 R14 面板):**台股 1,981(加權 1,089 · 櫃買 892)· 清單 GREEN**
  · 主動式台股 ETF 22 全驗證
* 2026-10-13 20:3x:`VDF_MDL009_TWStockList v0102 run OK · 1,985 筆 · 12.4s`
* `docs/VIA_VDF_StatusReview_20260921.md`:roster TPEX 892/892 · TWSE 1097/1103

**`VIA_Reports/**` 與 `output_hub/**` 都不進版控(政策),所以雲端容器看不到那 1,981。
照政策,不是壞掉。**

## ④ 操作員貼回的「流VIA · 資金流總覽 整合 Console」(2026-11-08)⇄ 本倉

貼回那頁自稱「收斂 indices_flow · flow_monitor · global_map_sim 三支為單頁 · 同一 FIS 引擎
(有機流→穩健z→tanh)三視角 · 財務/流量一律標證據狀態,不捏造 · in-memory 無 localStorage ·
只增不減 · EVIDENCE-HONEST · 非投資建議 · 20260704 10:43」,七段:
①指數資金流 ②族群&宇宙 ③全球模擬 ④擷取擴充 ⑤資金品質儀表 ⑥全球商品流 ⑦ETF分類。

逐項對本倉:

| 貼回宣告 | 本倉實況 | 判決 |
|---|---|---|
| 收斂三支為單頁 | 三支原檔都在 `FlowSystem_v2/uploads_original/`:`marketflow_index_v0112.html` · `flow_monitor_original.html` · `world_flow_original.html` | 三支齊備 |
| 70 FIS 宇宙檔 | `config/universe.json` = **70** 檔;T1 9 · T2 15 · T3 22 · T4 24 | 數字對上 |
| 7 情境相位 · 180d · 10區·4層·8類 | `config/sim.json`:keyframes **7** · span_days **180** · steps 84 · regions **10** · tiers **4** · types **8** | 五項全對上 |
| 30 監控族群(chip)vs 33 族群(第二段標題) | 無頭瀏覽器渲染實測:族群表 **30 列**(指數 benchmark 2 · 美股主題ETF 12 · 台股主題族群 5 · GICS 產業 11)· 指數表 15 列 · 0 page error | **chip 30 是對的,標題 33 是真錯 → v0102 改 30** |
| 70 FIS 宇宙檔(chip)vs 69 檔 FIS 宇宙涵蓋(第二段標題) | 冊 `config/universe.json` = **70** 檔;頁內正文也寫「70 檔 ETF 宇宙」 | **chip 70 是對的,標題 69 是第二處真錯 → v0102 改 70** |
| 台股主動式ETF ~28 檔(2026Q1)· 流量 NeedsFetch | 冊 A 碼 31(as_of 2026-10-03);流量確實沒有 | as_of 不同,非矛盾;同一誠實分級 |
| 全球 ETF 宇宙 | `Global_ETF_Universe_v0100.json`:股市各區 8 · 債券 5 · 商品 4 · 比特幣 3 · 房地產 3 | 在倉 |
| FIS 引擎 | 8 支 FLOW_ENG 在位:ENG001 Autotest · ENG009 Manager · ENG019 Attractiveness · ENG020 Leadlag · ENG021 GlobalEtfFlowscope · ENG022 GroupTaxonomy · ENG023 TwActiveEtf · ENG024 RegistryOps | 引擎齊備 |
| 族群流量「synthetic (sandbox demo)」 | 冊同口徑:「hot/lead/chg = v1.0 合成佔位 T4,null = 候 VDF 回填,非實證指標誠實標註」 | 合成值,**不升級成實證** |

### 4-1 貼回的 12 檔 ⇄ 冊:12/12 逐字相同

00980A 主動野村臺灣優選 · 00981A 主動統一台股增長 · 00982A 主動群益台灣強棒 ·
00984A 主動安聯台灣高息 · 00987A 主動台新優勢成長 · 00990A 主動元大AI新經濟 ·
00991A 主動復華未來50 · 00992A 主動群益科技創新 · 00993A 主動安聯台灣 ·
00995A 主動中信台灣卓越 · 00400A 主動國泰動能高息 · 00401A 主動摩根台灣鑫收。

12 檔全部通過兩把尺(SSOT `^00[0-9]{3}A$` · ENG077 執行尺 `^\d{5}A$`),
12 檔也全部已在本倉檔案中出現(16–254 個檔案不等)。
貼回的「元年 2025-05-05 首檔 00980A」與 ENG078「早於主動 ETF 元年不採信」規則一致。

### 4-2 貼回頁其餘各段(只登錄,不改其證據分級)

* ①指數流:15 指數 · 代表 ETF · 隱含總流 = ETF淨流$ / 覆蓋率(自標「放大推估非全市場真值」)·
  T1 真實 11 / T4 合成 4(恒生 · 櫃買 · 道瓊 · 其一)· 真值源 ICI / TWSE T86 / 北向 / EPFR
* ④擷取擴充:台股主動 ETF 代表 12 檔(流量全 NeedsFetch)· 國際原油 C1 工具 7 項
  (USO/USL/BNO/DBO/UCO/WTI 現貨/Brent 現貨)+ C2 五維真值源(期貨 NYMEX CL / ICE BZ ·
  現貨 FRED DCOILWTICO / DCOILBRENTEU · 供給 EIA 週報 / OPEC MOMR / IEA OMR ·
  庫存 EIA 週報 + Cushing + API · 成本 roll yield / 儲存費 / 邊際成本)·
  SPX 分 11 GICS(重用既有真實 sector FIS)· NDX / DJI 成分級待接
* ⑤品質儀表:T86 買賣超 · MI_MARGN Δ融資餘額 / 使用率 / 券資比 · 當沖比;
  計算規格五步(存量差分去當沖 → 周轉類才扣當沖 → `w_dq = 1 − clip(當沖比,0,cap)` →
  `FIS_adj = FIS × w_dq × f(維持率脆弱度)` → churn vs 真吸籌);
  自標三提醒:買賣超 zero-sum 非總流入 · 外資空走 SBL 不入融券 · 融資維持率是衍生估計非 TWSE 原生欄位
* ⑥全球商品流:17 列(能源 3 · 貴金屬 3 · 工業金屬 4 · 農產 4 · 廣基 3),
  方向×長度(FIS)**全部「待接 FIS」**;positioning 走 CFTC COT(週五發布、資料截至週二)
* ⑦ETF 分類:風險階梯 T0 防禦 → T1 核心 → T2 主題/區域 → T3 商品 → T4 槓桿反向 → T4+ 加密;
  加密段為 web 查證(約 2026-07),現貨 ETF + 2x 上限(SEC 2025/12 禁 3x/5x)

**本倉不改貼回頁自標的 T4 / NeedsFetch / 待接 FIS,也不往上升級。**

## ⑤ 本輪容器實跑的離線自測(唯讀 · 不觸網)

| 引擎 | 系統 | 結果 | 證明了什麼 |
|---|---|---|---|
| `VDF_ENG077_ActiveETFUniverse_v0106` | VDF | **10/10 PASS** | A 碼尺 · 退役冊過濾 · `run --offline` 誠實 rc 2 · 退役冊讀不懂就關門不當空冊 |
| `VDF_ENG078_ActiveETFHoldingsHistory_v0113` | VDF | **30/30 PASS** | 持股回補律 · 負股數整批不寫 · CONFLICTING_DUPLICATE · 元年前不採信 |
| `VDF_ENG087_MarketListGovernance_v0107` | VDF | **15/15 PASS** | 清單抓不到 = HOLD(不寫、不判下市)· 不經 VCGC 就拒跑 |
| `FLOW_ENG023_FlowTwActiveEtf_v0101` | FlowSystem | **10/10 PASS** | 清單 SSOT 種子態誠實 · 申贖流 Δ單位×NAV · 樣本不足誠實不算 · 不代設同意閘 |
| `FLOW_ENG024_FlowRegistryOps` | FlowSystem | **8/8 PASS** | 覆蓋稽核三態實跑:COMPUTABLE 2 · 欄缺 1(誠實不虛算) |

五支全綠 = **車道是好的**。自測綠不等於清單已生成:生成要觸網,觸網要閘。這條界線不跨。

## ⑥ 本倉真有的個股宇宙:47 檔(有券商報告佐證)

`functional modules/VRN/db/vrn_reports.duckdb::vrn_report_basic` 107 列,
`report_kind` 分佈:個股 57 · 產業 19 · 未分類 13 · 大盤晨報 9 · 研討會 6 · 海外 3。
去重後 **47 個真實個股代號**,全合 `^[1-9][0-9]{3}$`,**沒有一檔 `00` 開頭**
(= 這 107 份報告裡一檔 ETF 都沒有,所以 ETF 清單不可能從報告反推)。

1303 · 1319 · 1476 · 1560 · 1590(×3)· 2308 · 2317 · 2330 · 2382 · 2383 · 2606 · 2637(×2)·
2762 · 2891 · 3014 · 3017 · 3038(×2)· 3231 · 3264 · 3605 · 3653(×2)· 3661 · 3665(×2)·
3675(×2)· 3706(×3)· 4142 · 4153 · 4171 · 4442 · 4771 · 4966 · 5904 · 6143 · 6147 · 6278 ·
6285 · 6409 · 6415 · 6526 · 6533 · 6669(×2)· 6768 · 6873 · 6933 · 7728 · 8210 · 8358。

FlowSystem 6 檔種子與這 47 檔交集 = **3 檔**(2330 · 2317 · 3665)。

### 更正我自己上一輪的記錄

空白 ticker 的 50 列,我上一輪記成「資料品質疑點」。**那是記錯的。**
50 列全是非個股報告,`kind_reason` 逐列寫明「無代號、無型別關鍵詞、科技縮寫不足二
(誠實留白)(首頁引擎契約)」—— 它是契約要求的留白,不是缺陷。

## ⑦ 對帳層:頁首那把鍵在本倉對到哪裡

| 頁首宣告 | 本倉實況 | 判決 |
|---|---|---|
| 鍵 = `pdf_name` | 真的存在:`VRN_ENG057_ScanOcrRescue` · `VRN_ENG049_ContentReconcile` · `VRN_ENG055_OfficeMerge` | 對上 |
| 鍵 = `source_document` | 在 `VRN_ENG049/ENG050` 與 SSOT v2 record schema 裡存在;但**不是** `vrn_reports.duckdb` 任何表的欄 —— 落庫側鍵是 `report_file` | 只在契約層 · 未落庫 |
| 記錄 64 · `{"FIRSTPAGE": 64}` | 容器內 `vrn_report_basic` 107 列 · `vrn_report_metrics` 74 列;64 在本倉任何表都對不上 | 那輪是桌機的 · 雲端看不到 |
| READ-ONLY · 零落庫 | 本輪守住:duckdb 全程 `read_only=True` · panorama 只 `ast.parse` · 五支自測只寫暫存夾 | 守住 |

## ⑧ 要操作員做的三件事

| # | 一行指令 | 做完會得到 |
|---|---|---|
| A | `$env:VIA_NET_CONSENT='YES'; $env:VIA_SCRAPE_CONSENT='YES'; via-flowops --refresh-equity` | FlowSystem 個股冊 6 → 台股全集(TWSE + TPEX,append-only),`as_of` / `history` 補上 |
| B | `.\Update-VIA-ETFHoldings.ps1` | `via-etfuniv` 刷主動 ETF 宇宙 → `via-etfhist backfill` 補每日持股 → 22 檔的「持股已驗證」才算活的 |
| C | Remote Control 供出資料夾,或貼回兩個 csv | `VDF_UNIVERSE_latest.csv` + `ActiveTWETF_Latest.csv` 進得了雲端,才能逐檔對帳 |

`list_computer_folders` 仍回空 `folders`;desktop-commander 也跑在這個容器裡
(`platform linux` · `allowedDirectories []`),桌機側一律讀不到 —— 與 2026-11-08
連結全檢那份收據同一結論,沒變。

## ⑨ 族群數修正 —— 照實說:不是 31

**我上一輪寫「冊上是 31 群,該統一照冊寫 31」,那句是錯的。** 用省 Token 工具重查後,
三個數字量的是**三個不同母體**,不能互相覆蓋:

| 數 | 它量什麼 | 實證 | 判決 |
|---|---|---|---|
| **30** | 整合 Console「監控族群」:指數 benchmark 2 · 美股主題ETF 12 · 台股主題族群 5 · GICS 產業 11 | KPI chip 寫 30;無頭瀏覽器渲染後族群表 **實際 30 列**(表頭 族群/分類/方向/強度/走勢%/軌跡/成分)· 0 page error | **對的,就是本頁真值** |
| 33 | 第二段標題「33 族群方向/力道/走勢」 | 對不上 chip、對不上渲染列數、對不上任何冊 | **真錯 → 改 30** |
| 31 | `TW_Group_Classification_v0110.json` 台股族群冊 | 冊卡實證 `len(groups)=31` = `group_count` 31;成員實和 **149** = `member_count` 149;`leader_count` 41 —— **冊自身完全一致** | 是**另一個母體**;本頁台股主題族群只收 5 族,不是這 31 族 |

**把 31 寫到本頁 chip 上,會把一個本來對的 30 改成錯的。** 照冊的正確做法是:
本頁統一寫 **30**,31 留在它該在的地方(台股族群冊)。

同一段還查到**第二處漂移**:chip 寫「70 FIS 宇宙檔」、正文寫「70 檔 ETF 宇宙」,
但第二段標題寫「69 檔 FIS 宇宙涵蓋」。冊 `config/universe.json` = **70** 檔
(T1 9 · T2 15 · T3 22 · T4 24)→ 69 也是錯的。

### 已修(add-only;v0101 不動一字)

`supportive modules/ui_support/VIA_Flow_Overview_Console_v0102.html`
(v0101 已在 main,照版本律不改原地,出新版號):

* 第二段標題 `33 族群方向/力道/走勢 · 69 檔 FIS 宇宙涵蓋` → `30 … · 70 …`
* 標題字樣 `v0101 Porcelain` → `v0102 Porcelain`
* 頁尾依「只增不減」加一行修正紀錄,把 33→30 / 69→70 的理由與冊名寫進頁內

渲染複驗(無頭 Chromium · `file://` 本機 · 不觸網):chip 15 / 30 / 70 / 22 / 7 / 180d ·
第二段標題 30 / 70 · 指數表 15 列 · 族群表 30 列 · 商品表 17 列 · **page error 0**。

### 還沒做、等你一句話

本頁「台股主題族群」只收 5 族(軍工國防 · AI伺服器供應鏈 · 散熱 · 光通訊/CPO · 重電/綠電),
台股族群冊卻有 **31 族 / 149 成員**。若你要的是**把本頁擴成監控全部 31 族**,
那是資料面擴充(不是數字筆誤),我照 add-only 出 v0103 再做。

### 找檔紀錄(你說的備用檔案夾)

* 整合 Console 原來就在倉裡:`supportive modules/ui_support/VIA_Flow_Overview_Console_v0100.html` /
  `_v0101.html` —— 這同時補上了 2026-11-06 那輪列為「未上傳」的 `VIA_Flow_Overview_Console`
* `supportive modules/VIA_FlowSystem/_archive_uploads/VIA_FlowSystem_v1_original_sha6ed157c85d1b.zip`
  (44 檔)= FlowSystem **v1** 舊樹,沒有 monitor 頁、沒有台股族群冊 → 不是這頁的來源
* `FlowSystem_v2/uploads_original/` 10 檔 = 收斂前的三支分頁原版(marketflow_index · flow_monitor ·
  world_flow 等),族群數字不在其中硬寫
* 本倉 `flow_monitor.py` **不含硬寫族群數**:由 `universe.json` 的 `asset_class` 推導(8 桶),
  所以引擎側沒有要改的數字 —— 漂移只在那張手寫的整合 Console 頁上

### 本輪用到的省 Token 工具(照 L65 次序)

`token` 卡 6/6 已啟用 → `read` 骨架卡(flow_monitor.py 省 95.0% · flow_hub.py 省 95.0% ·
flow_ui.py)→ `read --depth 2`(冊 `TW_Group_Classification_v0110.json` 直接看出 `groups[31]`
與每族成員數)→ `slice`(`build_monitor` · `universe.json` 的 `etfs[*].asset_class`)。
整檔一次都沒讀進對話。

---

五系統對等獨立(L120 / L123):個股與 ETF 清單正本歸 **VDF**;FlowSystem 冊與 FIS 引擎在
**VAP** 支援層;報告側 47 檔來自 **VRN-2** 落庫;**VCGC** 只提供省 Token 讀檔與閘。
本文只讀各系統自報值與既有收據,不改他系統正本 / 冊 / 號 / 檔。非投資建議。
