# VDF 輸入 / 輸出盤點(2026-10-28;只讀盤點,不改程式)

操作員問(2026-10-28):「先給我輸入項目找那些資料透過誰清單 · 輸出也是」。依據:擷取冊 `VDF_FetchSystem_SSOT_v0106`(36 支)、
輸入範圍冊 `VDF_InputUniverse_SSOT_v0103`、族群冊 `VDF_FetchGroups_SSOT_v0102`(14 道)、表冊 `VIA_DB_Table_SSOT_v0102`(63 表)、
各引擎說明字串與原始碼(來源主機 · 表 · 檔)。四系統對等獨立:只盤 VDF。

## 一 · 輸入 → 誰抓 → 從哪裡 → 寫到哪

| 輸入項目 | 引擎(冊號) | 來源 | 輸出 |
|---|---|---|---|
| 台股個股總清單(上市 + 上櫃,開頭五欄 date·ticker·yf·bbg·name) | **009** MDL009_TWStockList v0102 | TWSE OpenAPI `STOCK_DAY_ALL` · `t187ap03_L`;TPEX `tpex_mainboard_daily_close_quotes` · `mopsfin_t187ap03_O` | `0-1-TWStockList/tw_stock_list_latest.parquet/.csv` · `verify_report.json` · `vdf_master_lists.duckdb::tw_stock_list` |
| 台股 universe(雙所分檔 + 拒收表) | **001u** MDL001_TWUniverseVerify | 同上(SSOT 代碼律驗) | `1-0-TWUniverse/{tw_universe_combined,twse_universe,tpex_universe}.parquet` |
| 雙所清單附產業 · 已發行股數 | **e055 L1** OmniFetch | TWSE/TPEX `t187ap03_*` | `vdf_tw_market.duckdb::tw_listings · tw_listings_industry · tw_shares_issued` |
| 清單正主(唯讀載入,給別支用) | ENG087 MarketListGovernance(不在擷取冊) | 本地庫 | 無(讀) |
| 主動式台股 ETF 總清單(代碼 `00xxxA`,揭露律) | **010** MDL010_ActiveETFList v0100 | TWSE OpenAPI `t187ap47_L` | `0-2-ActiveETFList/active_etf_list_latest.parquet/.csv` · `vdf_master_lists.duckdb::tw_active_etf_list` |
| 主動 ETF 名冊 / 須每日揭露者 | **e077** ENG077_ActiveETFUniverse | TWSE `t187ap47_L` | `ActiveTWETF.duckdb::active_tw_etf_universe · active_tw_etf_registry` · `vdf_tw_market.duckdb::etf_book` |
| ETF 冊(全部 ETF,主動旗標) | **e055 L4** | TWSE `t187ap47_L` | `vdf_tw_market.duckdb::etf_book` |
| 加權指數 TAIEX · 櫃買指數 TPEX 官方日資料 | **e232** ENG232_TWIndexOfficial v0101(增量) | TWSE `FMTQIK · BFI82U · MI_MARGN · TWTB4U`;TPEX `dmsRpt · 3itrade · margin_bal · intraday_trading_stat` | `output_hub/tw_index/VDF_TWIndex_Daily.duckdb::tw_index_daily`(三來源對照:官方 vs e055 L2 FMTQIK vs yfinance `^TWII` → `VDF_Universe.duckdb::xcheck`) |
| 美 · 日個股總清單 | **e231** ENG231_GlobalListings | NASDAQ Trader `nasdaqlisted.txt` + `otherlisted.txt`(ETF 另欄標記);JPX `data_j.xls`(只收內國株式,ETF/REIT 不收) | `vdf_global_market.duckdb::us_listings · jp_listings` |
| 台股每日量價(全市場) | **e054** ENG054_TWDailyBackfill;**e064** ENG064_HistoryBackfill(yfinance 同表補洞);**004** MDL004 全市場快照 | TWSE/TPEX 日端點;yfinance `.TW/.TWO` | `vdf_tw_market.duckdb::tw_daily_prices`;`1-4-TWFullMarket/*.parquet` |
| 成交值 · 筆數 · 市場總計 | **e057** ENG057_TradingValueBackfill;**e055 L2** | TWSE/TPEX;`FMTQIK` | `tw_trading_daily`;`tw_market_agg` |
| 籌碼(三大法人 · 融資券) | **e056** ENG056_ChipBackfill | TWSE/TPEX | `tw_chip_inst · tw_chip_margin` |
| 每日估值 PE/PB/殖利率 · 當沖 · 央行利率 | **e055 L3** | TWSE `BWIBBU` / TPEX `peratio`;當沖表;CBC | `tw_valuation_daily · tw_daytrade_* · tw_rates_cbc` |
| 月營收 | **e063** ENG063_MonthlyRevenue;**e075** ENG075 backfill | MOPS `mopsfin` · cnyes;MOPS | `tw_monthly_revenue` |
| 台股財報(MOPS 三表 · 每股淨值) | **e082** ENG082_FinStatements(族群 TW_FIN,預設 2330 · 3324,可增減) | MOPS / TWSE / TPEX | `tw_financial · tw_financial_mops(_log)` |
| 財報 · 估值(yfinance 三表 · PE/PB band) | **006** MDL006_FinancialModel(族群 INTL_FIN,預設 NVDA) | yfinance | `1-6-FinancialModel/{income,balance,cashflow,…}.parquet` |
| 分析師共識 · 目標價 · 殖利率 | **005** MDL005;**e059** ENG059_EstimateBands;**e088** ENG088_ConsensusFusionBridge | FactSet(需鑰)· yfinance | `1-5-TWStockFilter/*.parquet`;`analyst_estimates · consensus_*` |
| 四源個股解析(TWSE/TPEX/MOPS/YF) | **007** MDL007_SSOTResolver | 四源 | `1-7-SSOTResolver/ssot_resolved.parquet` |
| 主動 ETF 每日持股 · 持股異動 · 覆蓋帳 | **e078** ENG078_ActiveETFHoldingsHistory(IPO 起回補);ENG051 ActiveTWETF_Holdings(當日抓取,DDL 正主;不在擷取冊,走啟動鏈) | 投信 PCF 揭露頁(車道冊 `VIA_ActiveETF_HistoryLanes`:16 條 ISSUER_ARCHIVE 多數 PENDING_SOURCE)· MoneyDJ(只給今日)· TWSE | `ActiveTWETF.duckdb::holdings_daily · holdings_changes · active_etf_holdings_coverage` |
| ETF AUM · NAV · PE/PB 日快照(台 + 全球區域 ETF) | **e055 L5** etf_stats | Yahoo `quoteSummary`(統包握手道) | `vdf_global_market.duckdb::etf_stats_daily`;資金流 = **估算**(ΔAUM − 報酬效果,ESTIMATE 旗標,≥2 快照才出值) |
| ETF 量價「流向訊號」 | **002** MDL002(`ETF_FlowSignals`) | yfinance 量價 | `1-3-YFinanceUniverse/ETF_FlowSignals.parquet/.csv`(vol_chg > 0.2 標 INFLOW/OUTFLOW;是代理訊號,不是申贖) |
| 國際指數 · 個股 · ETF · 匯率 · 商品 · 債券殖利率 · 加密(19 組 175 檔日線) | **002** MDL002_YFinanceFetchingEngine | yfinance(INDICES_US/ASIA/EUROPE · EQUITY_US/TW/ASIA/EUROPE · ETF_REGION_GLOBAL/SECTOR_US/BONDS/THEMATIC/HELPER/TW_PASSIVE/TW_ACTIVE · CURRENCIES · COMMODITIES(`=F` 連續期貨)· BONDS_YIELDS · CRYPTO) | `1-3-YFinanceUniverse/YFinanceData.parquet` |
| 國際每日行情(可增減名單) | **e066** ENG066_GlobalUniverse(族群 INTL_DAILY;名單在 `VDF_Input_Interface_Matrix` INTL_DAILY);**e055 L6**(美五大 · 亞洲 · 歐洲 · 南亞 · 區域匯率 · 區域 ETF,2024-01-02 起) | yfinance / Yahoo chart | `vdf_global_market.duckdb::global_daily` |
| 指數估值代理(區域 ETF forward/trailing PE · PB) | **e055 L7** | Yahoo | `index_valuation_proxy` |
| 指數 Forward PER / EPS(S&P 500 · MSCI 8 指數 · 日經) | **e230** ENG230_ForwardValuation | FactSet Insight 文章 · S&P DJI `sp-500-eps-est.xlsx` · MSCI · 日經 | `vdf_global_market.duckdb::fwd_valuation_daily · fwd_valuation_factset_candidates`;`factset_earnings`(e055 L13) |
| 美國總經(CPI · PCE · PPI · 失業 · 非農 · 工業 · 零售 · 房屋 · 密大 · FEDFUNDS · DGS2/10/20 · T10Y2Y …)| **e074** ENG074_FredMacroSSOT;**e113** ENG113_MacroMethod(+ 財政部 DTS TGA);**e055 L8** FRED 細項 | FRED API(需 `FRED_API_KEY`,無鑰誠實 SKIP)· Treasury FiscalData | `macro/us_macro_all.parquet`;`vdf_global_market.duckdb::us_macro · cross_macro · macro_series_registry` |
| 中國經濟 85 支 · 各國經濟 133 支 · 航運 8 支(BDI/BCI/BPI/BCTI/BDTI · Drewry WCI 八航線 · LPI;NBS 目錄樹 月 605 · 季 116 · 年 2188 · 分省 …) | **011d** MDL011_AkshareFetcher deep-macro(選單 `VDF_AkshareSelection_MacroShipping_v0100`,225 支,1990 起全歷史,增量可續跑) | AkShare(轉接國家統計局等政府資料) | VAKE 僅增 parquet 分片 + DuckDB 目錄 / 視圖(`vake_manifest · vake_runs …`) |
| AkShare 全域(AST 盤點 akshare 全部函式 · 參數分類) | **011** MDL011 VAKE | AkShare | 同上 |
| PMI(各經濟體製造 / 服務兩筆) | **e114** ENG114_PmiPair | AkShare(日本 · 英國 · 德國 · 台灣 AkShare 沒有,照實缺) | DuckDB 表(VAKE 同庫) |
| 市場情緒:CNN Fear & Greed(現值 + 全史)· AAII 週調查 | **003** MDL003_SentimentMacroEngine;**e229** CNNFearGreedHistory;**e115** SentimentFetch;**e116** AAIIWorkbook | CNN `dataviz` · AAII 試算表 / 頁 · FRED · AkShare | `1-4-SentimentMacro/cnn_fear_greed.parquet`;`sentiment_daily`;`aaii_sentiment.duckdb::aaii_sentiment` |

## 二 · 輸出在哪(表冊 v0102 的 63 表 + MDL 的 parquet 夾)

| 庫 / 夾 | 表 · 檔 | 誰寫 |
|---|---|---|
| `vdf_tw_market.duckdb`(32 表) | tw_daily_prices · tw_prices_adj · prices_canonical · features_daily · tw_trading_daily · tw_chip_inst/margin/derived · tw_monthly_revenue · tw_universe · tw_listings(_industry) · etf_book · tw_valuation_daily · consensus_* · analyst_estimates · tw_daytrade_* · tw_market_agg · tw_rates_cbc · etf_revenue_* · tw_financial(_mops) · **vrn_report_* 等 VRN-2 的 9 表**(寫入者 = 本倉 `VRN_ENG073_ReportStructuredDB` 系列,即 VRN-2;VRN-1 是另一團隊的倉、只讀、不寫本庫;db check 紅 34 列裡 14 列是 VRN-2 寫進來的,四系統對等:VDF 只攤開不代修) | e054 · e057 · e056 · e063 · e055 · e059 · e082 · e088 · (VRN-2:VRN_ENG073) |
| `vdf_global_market.duckdb`(14 表) | global_daily · gl_prices_adj · prices_canonical · features_daily · us_macro · cross_macro · sentiment_daily · macro_series_registry · factset_earnings · etf_stats_daily · index_valuation_proxy · fwd_valuation_daily(+candidates) · us_listings · jp_listings | e066 · e055 · e074 · e113 · e230 · e231 |
| `ActiveTWETF.duckdb`(6 表) | holdings_daily · holdings_changes · active_tw_etf_universe · active_tw_etf_registry · active_etf_holdings_coverage · fetch_status | ENG051 · e078 · e077 |
| `output_hub/tw_index/VDF_TWIndex_Daily.duckdb` | tw_index_daily(TAIEX · TPEX) | e232 |
| `vdf_master_lists.duckdb` | tw_stock_list · tw_active_etf_list | 009 · 010 |
| `VDF_Universe.duckdb` · `VIA_Reports/vdf/universe/` | xcheck(指數三來源 · 三表代號數)· VDF_UNIVERSE_latest.csv/.json | 管理員 universe 動詞 |
| `aaii_sentiment.duckdb` | aaii_sentiment | e116 |
| VAKE(AkShare)分片 + 目錄 | 每支函式一分片;vake_manifest / vake_runs / vake_fetch_log | 011 · 011d |
| 擷取家 parquet 夾(MDL 系) | `0-1-TWStockList · 0-2-ActiveETFList · 1-0-TWUniverse · 1-3-YFinanceUniverse · 1-4-SentimentMacro · 1-4-TWFullMarket · 1-5-TWStockFilter · 1-6-FinancialModel · 1-7-SSOTResolver · macro/` | 009 · 010 · 001u · 002 · 003 · 004 · 005 · 006 · 007 · e074 |
| 族群目錄 `VDF_FetchGroups.duckdb` | fg_groups · fg_members · fg_runs · fg_status(+latest 視圖) | MDL012 |

規則(已有冊):`VDF_DataArchitecture_Rule_SSOT` R-DB-01…10 —— parquet 由 DuckDB 管理(hive 分區 ticker=/year=,zstd)· 每子題一庫 · 增量 anti-join 不重複 ·
擷取前看現況(ENG089/090)· TEMP 取代記憶體 · 表頭照 `VDF_InputUniverse_SSOT OUT-xx` · 驗證 CGC_MDL249。族群冊 14 道(TW_PRICE_VOL · TW_CHIP · TW_MONTHLY_REV ·
TW_INDEX · TW_ACTIVE_ETF · TW_FIN · INTL_FIN · INTL_DAILY · CN_MACRO · CN_NBS · GLOBAL_MACRO · SHIPPING · US_MACRO · SENTIMENT)把 36 支分到同一個 as-of 日。

## 三 · 「輸入分類整理好了嗎 · 輸出更亂」—— 誠實判定

**輸入:整理到一半。** 台股三組(IN-01 個股 · IN-02 主動 ETF · IN-03 兩指數)在輸入範圍冊有正本、有驗證、有三來源對照;族群冊把 36 支分成 14 道、四大類。
但國際 · 總經 · 情緒 的「名單」散在三處(MDL002 自己的 19 組、`VDF_Input_Interface_Matrix` INTL_DAILY/INTL_FIN、AkShare 選單),輸入範圍冊只收台股三組。

**輸出:兩層並存,所以亂。** MDL00x 系寫 parquet 夾(擷取家 `0-1 … 1-7`),ENG0xx 系寫 DuckDB(`output_hub` 各庫);同一題材兩邊都有
(量價:tw_daily_prices vs 1-4-TWFullMarket;清單:vdf_master_lists vs tw_listings vs tw_universe;ETF 冊:etf_book 兩處)。表冊 63 表的 `writers` 欄多數空白;
`vdf_tw_market.duckdb` 混進 VRN-2 的 9 張表(`VRN_ENG073_ReportStructuredDB` 寫入;不是 VRN-1,VRN-1 不在本倉)。

## 四 · 缺口(現在沒有任何引擎抓的)

1. **主動 ETF 每日 NAV 日序列 · 受益權單位數 · 真實申購 / 贖回(現金流入流出)**:只有 e055 L5 的 AUM/NAV 快照 + 估算流量(ΔAUM − 報酬)與 MDL002 的量價代理訊號;沒有從投信 PCF / 集保 / TWSE 淨值表抓單位數與申贖的引擎。候選來源:投信每日 PCF(車道冊 16 條待驗)· TWSE/TPEX ETF 淨值 · 集保 e-share 受益人數。
2. **國際 ETF(美 · 日)NAV / AUM / 資金流**:美區域 ETF 只有 e055 L5 快照(ETF_REGION 名單:SPY · DIA · QQQ · IWM · ONEQ · EWJ · EWY · EWT · FXI …);日本 ETF 完全沒有(e231 只收日股個股)。
3. **選擇權**:零引擎(台指選 · 美股選擇權都沒有)。**期貨**:只有 yfinance `=F` 連續合約(COMMODITIES 組);台指期 / TAIFEX 沒有。**現貨商品**:沒有(只有期貨代理)。
4. **台灣 · 日本 · 歐元區官方總經**(主計總處 · 央行 · BoJ · ECB):只靠 AkShare global_macro 轉接(133 支)與 `tw_rates_cbc`;沒有官方 API 直抓引擎。
5. **美日個股的每日行情**:清單有了(e231),行情只抓 Input_Interface_Matrix 裡列的少數代號(e066)與 MDL002 的 175 檔;不是全市場。

## 五 · 建議的整併順序(不動既有,只增)

1. 輸入範圍冊加 IN-04 國際(美 · 日清單 = e231)、IN-05 總經選單(= AkShare 選單 + FRED 系列冊)、IN-06 情緒,讓「名單」只有一本正本。
2. 表冊 63 表補 `writers`(每表唯一寫手),VRN-2 的 9 表移出 `vdf_tw_market.duckdb`(VRN-2 自己決定,VDF 只報;VRN-1 另倉只讀,與此無關)。
3. MDL00x 的 parquet 夾改由 DuckDB 管理(R-DB-01 已規定,尚未落到 002 · 003 · 004 · 005 · 006 · 007)。
4. 缺口 1 立專案:主動 ETF 淨值 · 單位數 · 申贖引擎(先從 TWSE/TPEX 官方表與投信 PCF 驗證車道開始);缺口 3 的台指期 / 選擇權另立。
