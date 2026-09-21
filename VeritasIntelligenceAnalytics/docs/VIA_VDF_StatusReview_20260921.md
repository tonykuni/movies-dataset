# VDF 邏輯參數與現況審視 · 2026-09-21(自 VIA 中央口切入;側線審視,不占批號)

> 操作員令:「將 VDF 專案從 session_01RLMQGZLcigd5Bt5aN6J4Ck 了解;VIA 管理一切包含 VRN、VDF;從 VIA 入手查 VDF 的邏輯參數及現況」。
> 本文是**唯讀審視**:零引擎改動、零冊改動、零台帳追記。所有數字都標明出處與量測地點(**容器** = 本審視的沙盒,沒有操作員的資料家與家族境;**工作站** = 操作員貼回的實錄或冊上快照)。
> 分支:`claude/busy-bell-97sa4f`(自 main 8e8e766f = 批662 分出)。**遠端 `claude/via-envmanager-governance-7cls8h` 已推進到批674(12 個 commit 尚未併入 main)**,本文一併讀了那 12 批的 docs。

---

## 〇 · 一句話

VDF(Veritas Data Forge,資料鍛造子系統)**引擎面已可獨立跑通**:批667 的 `via-vdfchain` 七站全綠(容器 13 秒),批610 審計閘 GREEN 49 · NODATA 9 · RED 0,45 支尾版引擎對兄弟家族真依賴 0。**卡住的不是程式,是料與閘**:所有觸網擷取站在同意閘未開時一律 GATED(批599 實跑 33 項 vdf 中 GATED 15),而打包就緒閘(批673/674)三專案合計離就緒 9/21,VDF 的三個缺列是自測門覆蓋 62.4%、家族境量不到、落頁規格 0/2。

---

## 一 · VIA 怎麼管 VDF(從中央口往下看)

| 層 | 冊 / 件 | VDF 在裡面的樣子 |
|---|---|---|
| 唯一對接口(L20) | `CGC_MDL149_VeritasCentralGovernanceConsole_v0117`(`via-vcgc`) | status 八行:政策庫 99 律 · 305 lessons · Deck 89 任務 · 規格 63 項 · 格子 264 站 · Register 159 指令 · 中央冊 5643/5642(容器,批662 樹) |
| 政策庫 | `VIA_Policy_Laws_SSOT_v0100.json` | VDF 專屬律見第三節 |
| 規格冊(輸入主控台) | `VIA_InputConsole_Spec_v0100.json` → `families.vdf` | 六群 **33 項**:tw_equity 11 · macro 3 · financials 6 · etf 4 · intl 2 · db 7;`python: vdf`(家族境) |
| 工作流冊 | `VIA_Workflow_SSOT_v0100.json` | `vdf_daily_update`(tw_prices_inc→tw_chips→tw_trading_value→tw_align→db_arch)· `vdf_db_governance` · `vdf_quantguard_features` · `vdf_daytrade_file_chain` · `vdf_market_lists_acceptance` · `vatetf_pipeline` · `vtmra_family` |
| 庫表冊 | `VIA_DB_Table_SSOT_v0100.json` | 54 表:`vdf_tw_market.duckdb` 37 表 · `vdf_global_market.duckdb` 11 表 · `ActiveTWETF.duckdb` 6 表 |
| 短令冊 | `Register-VIA-Commands-v0232.ps1`(main)/ **v0239**(遠端分支) | `via-price`(ENG054)· `via-chip`(056)· `via-tval`(057)· `via-align`(081)· `via-vdfdb`(079)· `via-vdfinc`(089)· `via-vdfcov`(090)· `via-consensus`(088)· `via-vetf`(085)· `via-quantguard`(086)· `via-market-lists`(087)· `via-finstat`(082)· `via-fred`(074)· `via-revfill`(075)· `via-etfuniv/etfhist/etfrev`(077/078/076)· `via-vdfarch`(073)· `via-vdf-extra5` · `via-daytrade`(055 L15)· **`via-vdfchain`(CGC_MDL170,批667,只在遠端分支)** |
| 能力卡書(Essentia) | `VIA_Essentia_CardBook_VDF_v0100.json`(批588) | 45 支引擎一張卡;原始碼 519,902 token → 8,392 token(省 98.4%);AI 讀卡不讀原始碼(L65) |
| 參數/邏輯/因子正典 | `VIA_Central_Params_SSOT`(66 冊索引)· `VIA_Logic_Registry`(批597,15 條正典路由,12 支 VDF 引擎綁 `num/argval/newest`)· `VIA_Feature_Catalog` | 邏輯庫舊本 `VIA_Lib_Registry` 名實不符(其實是 pip 安裝台帳)→ 待操作員改名(批597 PENDING_OPERATOR) |
| 架構冊(工作站快照) | `VIA_VDFArchitecture_v0100.json`(ENG073 build,2026-09-15) | 61 表 · 15,148,690 列 · 12 SSOT 類 · 305 parquet;資料家 `C:\Users\tonyk\VIA System\via_database` linked |

**VDF 自己的冊**(`functional modules/VDF/`):`VDF_Unified_Params_v0100.json`(全引擎統一參數 SSOT)· `VDF_Param_Registry_v0100.json`(收割 678 個參數,append-only)· `VDF_Param_Engine_Map_v0100.json`(ENG053:57 引擎 × 317 參數 × 14 車道)· `VDF_Input_Interface_Matrix_v0100.json`(批88 輸入介面矩陣)· `VDF_Fetch_Orders_v0100.json`(批114 擷取單制)· `VDF_Architecture_Clarification_v0100.md`(五層架構釐清書)· `registry/VIA_VDF_Fetch_Contract.json`(VDF-FETCH/1.0,277 項)。

---

## 二 · VDF 是什麼(結構)

- **定位**:全系統唯一允許對外抓取的取數層;上游=官方/公開源(TWSE/TPEX/MOPS/FRED/Yahoo/AKShare),下游=VRN 研報、VAP 繪圖、VATETF 應用端、QuantGuard 因子。
- **五層**(釐清書 v0100):L0 啟動/介面(`Invoke-VDF.ps1`、`via-vdf`、MDL501 UI)→ L1 擷取引擎(MDL001–007)→ L2 共用庫(MDL101–105)→ L3 工具/測試(MDL201/301–303)→ L4 Registry(MDL401–404)→ L5 資料面。
- **活樹引擎**:`engine/` 尾版 **45 支 ENG/MDL 家族**(ENG046–ENG091 + MDL002/003/007),其中 40 支有 `--selftest`;5 支沒有(ENG051 v0102、MDL002、MDL003、MDL007、candidates/sector_rotation)。批610 又替 10 支活樹檔補了 `--selftest` 等價動詞。
- **三本正典庫**:`vdf_tw_market.duckdb`(台股價/量/值/當沖/籌碼/名冊/共識/月營收 + VRN 七張 `vrn_*` 正典表,L90)· `vdf_global_market.duckdb` · `ActiveTWETF.duckdb`。家在資料家(`VIA_DATA_HOME`),倉內 `output_hub/` 已接點(批490/523)。
- **獨立性(批667 量的)**:45 家族對 VRN/VAP **真依賴 0**;唯一一處 `ENG088` 讀 VRN 收容夾的外來件,是路徑不是依賴。

---

## 三 · VDF 的邏輯參數(律 → 冊 → 引擎常數)

### 3.1 政策庫裡直接管 VDF 的律

| 律 | 內容(縮) |
|---|---|
| L21 | 所有 VDF 價格資料皆 adj(除權息調整後);報告上是報告日原始價;兩者不可直接比 |
| L34 | VATETF(舊名 VETF)是應用端,零自抓,只讀 VDF 落的庫 |
| L35 | VDF 基金只抓**主動式台股 ETF**(ENG077 宇宙 + ENG078 持股);被動 ETF 只到價格;其他基金不抓不建表 |
| L37 | 擷取範圍律:抓前先查庫 MAX(date)/checkpoint → 缺口=範圍(增量自 MAX(date)−3 日重疊)→ 批次落盤+checkpoint anti-join → 永不重抓;短缺口該走「逐日全市場」道(候建 Z35) |
| L41/L42 | 指標只用 ADJ 價;量值四欄(raw/ex_daytrade)並存,指標一律用扣當沖量;輸入只從 VDF 庫 → 特徵表 → VAP(TA-Lib 段已被 L50 退役) |
| L43 | Forward P/E 的共識 EPS 只取 FactSet 稀釋 EPS;其他源只給目標價 |
| L44 | VATETF 每跑一夾 RUN_<ts>,只認本跑 audit |
| L45 | 個股當沖量值三態:openapi TWTB4U=標的冊;rwd/TPEX 被 WAF 擋;量值走檔案收容道 `via-daytrade --from-file` |
| L50 | QuantGuard 是唯一活動技術分析路徑;TA-Lib 永久禁裝禁 import |
| L69 | VDF 每支活件尾版都要帶 `[VIA:NET-BRIDGE]`(批670 量:VDF 195/195 ACCEL,NET 尾版 45 缺 0) |
| L78 | 空表守衛同構律(ENG070 v0112 的根因) |
| L83 | 只走一半的路不算跑過(ENG090 漏 import os 的教訓;自測要合成缺席側) |
| L87 | 豁免必附理由(ENG091 審計豁免冊 7 筆) |
| L90 | 正典儲存層=DuckDB;Parquet/CSV/JSON 是派生層,單向不回灌 |
| L98 | 三座庫依序完工 **VRN → VDF → VIA**;VIA 手下引擎存在理由是支援這三座 |
| L99 | 目標價跨過除權息一律改 ADJ CLOSE 基準:因子=`adj_close/close`,`tp_adj = tp × (報告日因子 ÷ 最新日因子)`,上漲空間對「目前」adj_close 算;永不拿 close 頂替 adj_close |
| L07/L08 | 同意閘 `VIA_NET_CONSENT` / `VIA_SCRAPE_CONSENT` 與金鑰(`FRED_API_KEY`)**永遠操作員自設**;裝套件、改 `.ps1`(L70)=操作員的手 |

### 3.2 冊上的參數(現值)

| 冊 | 參數 | 現值 |
|---|---|---|
| InputConsole Spec `defaults` | `start` | **2023-07-01**(批600 操作員令;批392 的 2023-01-01 退場) |
| InputConsole Spec `user.group_starts` | tw_equity / macro / financials / etf / intl | 全部 **2023-07-01**(批599 `via-console set group-start`,changelog 五筆) |
| InputConsole Spec `param_kinds` | range / start / since / since_ym / days(1~3650)/ codes / lanes / cats / from-file … | 各引擎 CLI 旗標的統一語意;ENG064 的 range 有「<2022-01-01 抬升」律 |
| `VDF_Unified_Params` | time.start_date=2018-01-01 · end=TODAY;fetch batch_size 5 / max_retries 3 / retry_delay 2s / timeout 30s;output formats parquet/csv/duckdb/sqlite/sql,csv utf-8-sig;`honesty.simulation_data`=模擬值必帶 `_SIM` 後綴 | 舊世代(批88 前)的種子冊;新引擎的起始日已由 Spec 接管 |
| `VDF_Input_Interface_Matrix` | INTL_DAILY 10 檔指數/匯率(含 ^NDX/^RUT)· INTL_FIN 11 項 · TW_FIN period_mode=年度 · start_date=2023-07-01 | 活冊,零刪除(removed_* 軟移除) |
| VATETF / QuantGuard | `vdf_quantguard_run` 需明確 `--in` Parquet(NEED_INPUT,不補值);輸入契約=adj_close + 調整後 OHLC + non_day_trade_volume | |

### 3.3 引擎裡的關鍵常數(尾版原始碼)

| 引擎 | 常數 | 值 / 意義 |
|---|---|---|
| ENG054 TWDailyBackfill v0105(`via-price`) | `OVERLAP_DAYS=3` · `BATCH=80` · `LOCK_RETRY×LOCK_WAIT=20×6s` · `LISTING_EPS` 雙所(t187ap03_L / mopsfin_t187ap03_O)+ ETF 冊 t187ap47_L(只收四碼被動碼) | 增量律:各票 MAX(date)−3 日起;少一所即 **rc=2 NODATA 且不准自稱雙所**(批645) |
| ENG064 HistoryBackfill v0112 | `TARGET_START=2020-01-01` · `TERMINATION_FLOOR=2022-01-01`(批212 終止 2020/21 段)· 年段倒序 2023→2022 · `BATCH=40` · `PAUSE_S=0.35` · `HIST_WORKERS=4` · `HIST_SUB=10` · `HIST_LANE=yf`(0.54s/檔)· `HIST_BREAKER=3` · `GAP_BATCH_SIZE=20` · `GAP_EMPTY_RETRY_HOURS=24` | 取票=`SELECT DISTINCT ticker FROM tw_daily_prices`(閉環,對的;新票入場是 ENG054 的事);涵蓋率正主=ENG090 roster |
| ENG089 IncrementalFetchGate v0100(`via-vdfinc`) | `DEFAULT_SINCE=2023-01-01`;零網路零寫入;scan / plan [--deep] / audit | 只列缺口;複用 CGC_MDL123 資料家 catalog(容器缺 catalog → ABSENT 是誠實態) |
| ENG060 AdjPriceLayer v0104 | `factor = adj_close / close`;adj_open/high/low = ×factor;`data_class='DERIVED_ADJ_FACTOR'`;正典取數視圖 `prices_canonical`;adj_rows ≥ 95% src_rows | 下游一切以調整層取數 |
| ENG090 DataCoverageGate v0104(`via-vdfcov`) | 名冊正本 `CGC_MDL142_TWNameBook`;`roster` 車道照 market 拆;整所缺席判定;零網路 | |
| ENG091 VdfAuditGate v0100 | `--workers 6` · `--timeout 300`;平行跑 → 序跑複判(鎖撞假紅);rc 0/1/2 | |
| ENG055 OmniFetch v0111 | 車道 L5–L15(etf_stats / global / idx_val / us_macro / cross_macro / tw_rates / sentiment / eurostat / factset / daytrade / daytrade_stock);`--from-file --date --market` | |
| ENG074 FredMacroSSOT v0102 | 需 `FRED_API_KEY`(env 或 `mega/.fred_api_key`);增量=DONE 序列 max_date−45d 修訂窗;FAIL 序列 PARK | |
| ENG085 VatetfBridge v0104 | 持股 asof 前最新日;價 45 日;consensus 依 source 分 FactSet/其他;每跑 RUN_<ts> | |
| CGC_MDL170 VDFChainRunner v0101(`via-vdfchain`,遠端分支) | `DEFAULT_SINCE=2023-07-01`;十站 0a/0b/0c/1/2/3a/3b/4a/4b/4c;`--resume` 只重跑沒過的站;rc 0 GREEN/1 RED/2 NODATA/3 ABSENT/4 GATED | 參數=ENG053 · 邏輯=ENG073 · 因子=ENG061+062 · 引擎=ENG090/089/091 |

---

## 四 · 現況(分清楚容器與工作站)

### 4.1 引擎面(能不能跑)

| 量尺 | 結果 | 出處 |
|---|---|---|
| VDF 鏈 `via-vdfchain run` | 0a 加速器 GREEN · 0b 網路 **GATED**(閘未開)· 0c 獨立性 GREEN(45 家族,真依賴 0)· 1 參數 11/11 · 2 邏輯 9/9 · 3a 因子 9/9 · 3b 族群 8/8 · 4a 涵蓋閘 23/23 · 4b 增量閘 16/16 · 4c 稽核閘 11/11 → **GATED(七站全綠,13s)** | 批667,容器 |
| VDF 審計閘 ENG091 | 活樹 58 支待審 · 豁免 8 · **GREEN 49 · NODATA 9 · RED 0** · 缺動詞 0(NODATA=容器沒裝 rich/akshare/gspread/pandas_datareader/xlrd) | 批610,容器 |
| 卡書 F1 | 45 支尾版:40 支有自測 → GREEN 36 · RED 3(兩支 duckdb 鎖撞假紅;ENG070 真紅已於批596 v0112 修好)· NODATA 1(ENG072 缺籌碼表) | 批588/596 |
| 加速器/網路橋 | ACCEL VDF 195/195;NET 尾版 45 缺 0 | 批670 |
| 全格子 | v0417 OK 262 · FAIL 0 · SKIP 2(批661);遠端分支 v0424 270 站,批668 更正實量 OK 267 · FAIL 1(總控頁契約,已修) | 批661/668 |
| VCGC 自測(本審視在容器實跑) | 二十三檢 OK 22 · FAIL 1:⑬ 元件自動編號冊 ACTIVE 5643/5642(main 樹上有 1 件未同步;遠端分支批664 已是 5685/5685) | 本次,容器 |
| 打包就緒閘 VDF 列 | ① 引擎在位 GREEN 93 支 · ② 自測門覆蓋 **62.4%** · ③ 自測綠 NODATA(存證比樹舊)· ④ 四面登錄 GREEN · ⑤ 家族境 NODATA · ⑥ 落頁規格 NODATA 0/2 · ⑦ 資料證據 GREEN 10 列;三專案合計離就緒 **9/21** | 批673/674,容器 |

### 4.2 資料面(庫裡有什麼)

**工作站**(`VIA_VDFArchitecture` 2026-09-15 快照 + 批559 census 9/17 + 批650/661 實錄):

| 庫 · 表 | 現況 | 燈 / 備註 |
|---|---|---|
| tw_daily_prices / tw_prices_adj / prices_canonical / features_daily | 各 577,733 列 · 892 檔 · 2024-01-02 ~ 2026-09-16(批559);更早的 批522 量測為 2,128,168 列 2020-01-02 起(不同副本庫,見 P) | GREEN;`tw_daily_prices` 有 1900-01-01 哨兵列(Z46,清=操作員的手) |
| roster(名冊×價表) | TPEX 892/892 · **TWSE 1097/1103(缺 6 檔老 ETF:0054/0058/0059/0060/0080/0081)** | NODATA;補價要開閘(批650 更正:整所缺席只是容器的樣子) |
| VRN 對價(批661) | 上漲空間 ADJ 算得出 39 筆;價庫是全的,無料過期 | 目標價年齡 91% 逾 90 天(描述性,不判燈) |
| tw_chip_inst / tw_chip_margin | 1,165,675 / 1,145,409 列(9/15 快照);批559 census 卻列為「冊上宣告、庫裡沒有」 | **兩份量測不一致 → 先 `via-census -Tables` 對一次**(三副本庫病,掉球 P) |
| consensus_daily / consensus_latest | 9/15 快照 597 / 198 列;批559 census 0 列;ENG088 共識融合橋 status 也量到正典 0 列 | 同上,要對副本;FactSet 稀釋 EPS 只 4/40 檔(Z43) |
| tw_daytrade_stock | ABSENT(WAF 擋;檔案收容道 L45) | 量能指標無扣當沖值(Z44) |
| ActiveTWETF holdings_daily | 40 列 1 檔 ETF(9/07);史深缺 1034 日格 | `via-etfhist backfill` 觸網(Z45) |
| tw_monthly_revenue / monthly_revenue_analysis | eng069 v0108 OK;VDF_TW_MonthlyRevenue.duckdb 最新 2025-12-01 | 舊(批559) |
| vdf_global_market | 9 表 192,653 列,最新 2026-09-17;缺 us_macro · macro_series_registry | FRED 鑰=操作員 |
| tw_financial | 派生層;閘未開=空表非缺陷 | `via-finstat` 雙閘 |

**容器**(本審視沙盒):只有上櫃 892 檔、無籌碼表、`tw_trading_daily` 的上市所停在 2025-06-30(批659);資料家 catalog 不在 → ENG089 回 ABSENT 是誠實態,**不能拿容器數字推論工作站**(LL49/LL155)。

### 4.3 閘與手(VDF 現在真正卡的地方)

- 批599 `via-vcgc matrix --family vdf,vrn --apply` 真跑 48 項:GREEN 23 · **GATED 15**(tw_prices_inc · tw_history · tw_chips · tw_trading_value · tw_daytrade_stock · tw_daytrade_files · macro_fred · macro_detail · macro_lanes · fin_statements · tw_revenue_codes · tw_revenue_backfill · estimate_bands · global_universe · global_lanes)· RED 3(tw_align 容器籌碼 0=真缺料;quantguard_run / vrn_unified 缺 `--in`=NEED_INPUT)。
- 這 15 支就是「2023-07-01~今」的答案:起始日已在冊上,**引擎 fail-closed 等閘**。
- 前一個 session 最後一則(批674 之後)停在問操作員:「要我開跑嗎?還是你想先開閘,我一次把 A 也做掉(那 26 格今天就能到手)?」——**沒有回答就沒有下一步**;那則的 A/26 格細節不在倉內任何檔案,只能由操作員或該 session 對話補上。

---

## 五 · VDF 相關還掛著的事(只列,不代裁)

| 代號 / 出處 | 事 | 誰 |
|---|---|---|
| Z27 | 五額外雙閘 3 件(macro_fred / fin_statements / global_universe;FRED 另要 API key) | 操作員開閘 |
| Z35 / L37⑤ | 短缺口「逐日全市場」道(ENG054 `--lane bulk-day`)未建;逐檔道 5 日≈16 分 | AI(候令) |
| Z43 | VATETF EPS 覆蓋:FactSet 只 4/40 檔 → forward P/E 上限 10% | 操作員 |
| Z44 / L45 | 當沖量值檔案收容(瀏覽器存 CSV → `via-daytrade --from-file`) | 操作員 |
| Z45 | 主動 ETF 持股史深 1034 日格 | 操作員(`via-etfhist backfill` 觸網) |
| Z46 | tw_daily_prices 1900-01-01 哨兵列 | 操作員(census DELETE 只印不跑) |
| Z50 | QuantGuard 靠 polars;工作站 via_vdf_312 要裝 `polars>=1.21,<2` | 操作員 |
| Z52 | 價格最早 2024-01-02,未達 2023-01-01;補庫按操作員指示停止中 | 操作員(喊停) |
| U | VDF 正境 `via_vdf`(登錄 py3.12)vs `via_vdf_312`(實為 3.13.7 未登錄) | 操作員一句話 |
| P | `vdf_tw_market_repo_*` 副本庫與正庫並存(三副本病;上面 4.2 的量測不一致很可能來自這裡) | 操作員裁刪 |
| 批650 | TWSE 6 檔老 ETF 缺價 | 操作員開閘後 `via-price` |
| 批597 | `VIA_Lib_Registry`(邏輯庫舊本)名實不符要改名 | 操作員 |
| 批610 | ENG072 StoryRotationBridge NODATA(要 tw_chip_inst/margin → `via-chip`) | 操作員(觸網) |
| 批673 | VDF 自測門覆蓋 62.4%(93 支中約 35 支沒門)· 落頁規格 0/2 未接 MDL173 | AI 可續做 |
| 批674 | 磁碟 Register 停在 v0234,遠端 v0239;守門員第三假設已修 | 操作員 `git pull` |

---

## 六 · 版本落差警示(接手者先看)

1. **main(8e8e766f,PR #52)停在批662;遠端 `claude/via-envmanager-governance-7cls8h` 已到批674**(a6c5118b)。`via-vdfchain` · `via-state` · `via-packgate` · `via-deploy` · `via-panoplan` · `via-vrnchain` · `via-matrixspec` 與 Register v0233–v0239、CGC_MDL168–175 都只在那條分支上。要用這些短令必須先 `git pull origin claude/via-envmanager-governance-7cls8h`。
2. 倉根 `VIA_HANDOVER_LATEST.md` 與 `docs/VIA_Handover_ONEPAGE.md` 仍是**批554**快照(VCGC v0111);VCGC v0117 的交接源仍指 B498。最新逐批交接是遠端分支的 `docs/VIA_Handover_20260920_B664.md` + 每批一檔 `VIA_B6xx_*.md`。
3. `.claude/settings.json` 的 SessionStart hook 會在開機跑 `via_boot_update.sh`(每日首開更新檢查)。

---

## 七 · 一貼即用(工作站;閘那兩行是操作員的手,本文不代設)

```powershell
Set-Location 'C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics'
git pull origin claude/via-envmanager-governance-7cls8h
. (Get-ChildItem .\Register-VIA-Commands-v*.ps1 | Sort-Object Name | Select-Object -Last 1).FullName
via-fresh
via-vdfchain
via-vdfchain run
via-vdfcov roster
via-vdfinc plan --since 2023-07-01
via-census -Tables
via-consensus
via-state html
via-packgate
```

要真的補 2023-07-01 起的料(15 個 GATED 站),在同一個視窗自己貼:

```powershell
$env:VIA_NET_CONSENT = 'YES'
$env:VIA_SCRAPE_CONSENT = 'YES'
via-vdfchain run --resume
via-vcgc matrix --family vdf --apply
```

貼回:`via-vdfchain run` 的十站表 · `via-vdfcov roster` 的 market 拆分 · `via-census -Tables` 裡 tw_chip_inst / consensus_daily 的列數(解 4.2 那兩處不一致)· `via-packgate` 的 VDF 七列。

---

## 八 · 本審視的方法與限制

- 讀:倉根一頁交接(批554)· `docs/VIA_B588/596/597/599/610/644–674`(後 12 批自遠端分支 `git show`)· 政策庫 99 律 · 規格冊 · 工作流冊 · 庫表冊 · VDF 卡書 · VDF 四本參數冊 · ENG054/060/064/089/090/091 與 CGC_MDL170 尾版原始碼抬頭。
- 跑(容器,零網路):`via-vcgc status`、`--selftest`(22/23,⑬ 見 4.1)。**沒有跑任何擷取引擎、沒有寫任何庫、沒有設任何閘。**
- 前一個 session 的對話本文讀不到(只能取得其 session 記錄與 post_turn 摘要);本文的「前一 session 現況」全部以它已 commit 的 docs 為準。
