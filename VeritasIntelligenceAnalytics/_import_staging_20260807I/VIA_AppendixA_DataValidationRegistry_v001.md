# VIA Appendix A Data Validation Registry v001

Generated: 2026-07-05

## def Summary

- Appendix A 事件數據大方向可用，但需要把 Verified / Corrected / Pending / Reject 分流。
- 全球 PMI dashboard 目前應標為 UI demo / mock data；多數 headline 與最新公開資料不一致。
- VDF v003 第一優先仍是資料衛生：禁止 self-ingestion、官方資料 raw audit、本機 reader fallback。

## def Registry

| ID | Group | Status | Confidence | Claim | Verified Value | Action |
|---|---|---|---|---|---|---|
| A001 | Micron / Memory | Verified | 90 | 美光 2026-06-23 大跌約 13.3%、收約 $1,051.77；南韓 FSS 槓桿 ETF 警告觸發記憶體股賣壓。 | 可保留；Forbes 確認跌逾 13%、FSS 警告與 memory ETF / Samsung / SK Hynix 相關。 | Keep with source |
| A002 | Micron / Earnings | Verified - Price Needs Market Source | 85 | 美光 2026-06-24 盤後財報，FY3Q26 營收 $41.46B；6/25 大漲 15.7% 收 $1,213.56。 | Micron IR 確認 FY3Q26 revenue $41.46B vs $9.30B prior year；股價漲幅/收盤價需價格源二次核對。 | Keep but add price verification |
| A003 | Micron / Post-earnings | Pending | 55 | 美光財報後 8 日由 $1,213.56 跌約 19.6% 至 ~$975；Burry 空單。 | 方向可列為待查；Burry 空單需標為 reports / 據報導。 | Fetch price series and verify |
| A004 | Taiwan Equity | Verified - Official Series Needed | 80 | 台股 2026-06-23 盤中 48,218.87 新高。 | 媒體盤勢資料可用；仍建議 TWSE 指數日內/歷史資料作 final source。 | Fetch official index series |
| A005 | TSMC / Taiwan Equity | Correct / Pending Official | 55 | 台積電 2026-06-23 盤中 2,525。 | 公開盤勢資料見到「突破 2,500」與部分 2,535；2,525 尚待 TWSE 個股日內資料確認。 | Do not hardcode 2,525 yet |
| A006 | Taiwan Equity / Institutional Flow | Verified | 95 | 2026-06-24 台股跌 1,057.05 點收 46,043.60；外資 −1,774.18 億；三大法人 −2,102.38 億。 | 經濟日報/中央社資料相符。 | Keep and fetch official |
| A007 | Taiwan Futures | Pending Official Series | 70 | 2026-06-24 外資台指期未平倉淨空單 83,605 口。 | 媒體報導可用，但正式數值需 TAIFEX 大額交易人/法人資料補抓。 | Fetch TAIFEX official |
| A008 | Taiwan Equity / Crash Extension | Verified | 95 | 2026-06-26 台股再崩 1,683.5 點收 44,571.76，外資賣超 1,431.89 億。 | 經濟日報確認，創史上第 3 大收盤跌點，外資賣超史上第 2 大。 | Add to Appendix A and narrative |
| A009 | US Labor / BLS | Verified | 100 | 2026 年 6 月非農 +57k、失業率 4.2%、勞參率 61.5%、E/P 59.0%、前兩月合計下修 74k。 | BLS 官方就業報告確認。 | Keep |
| A010 | US Labor / Household Survey | Verified - Table Pull Needed | 85 | 家庭調查就業 −507k、勞動力 −720k；失業率下降主要因分母收縮。 | Reuters 報導提到 720k 退出勞動力；家庭調查需從 BLS A-table 抽數。 | Fetch BLS table A values |
| A011 | Fed / FOMC | Verified | 100 | 2026-06-17 FOMC 維持聯邦基金利率 3.50%–3.75%。 | Fed 官方聲明確認。 | Keep |
| A012 | Fed / Market Pricing | Corrected | 85 | Fed 因果鏈應改為 higher-for-longer / 年底前升息風險，而不是 12 月降息機率大減。 | Reuters 指弱非農後 July hike odds below 20%, September around 60% vs 75% before report；Fed 目標區間仍 3.50%–3.75%。 | Rewrite narrative |
| A013 | Fed / Dot Plot | Corrected / Split Required | 70 | 點陣圖 9/18 位升息、CPI 4.2%、2Y 4.21%。 | Fed SEP 官方可驗證；媒體解讀顯示 9 位官員預期年底利率更高、8 位不變、1 位下降。CPI/2Y 需分別用 BLS/FRED 驗證。 | Split into separate claims |
| A014 | Taiwan Margin / Retail | Media Verified / Official Pending | 75 | 集中市場融資 6,050.4 億、櫃買 2,084.4 億、兩市 8,134.8 億；零股 710.7 億。 | 媒體報導已見相同數字；官方 TWSE/TPEx 數列仍需 VDF 補抓。 | Fetch official series before scoring |
| A015 | Taiwan Momentum / Top Winners | Corrected | 65 | 前 20 強勢股 +31%~60%。 | 需拆時點：6/19 週排行約 32.5%~46.1%；7/3 盤中週排行可見 60%+，不能混用。 | Recompute from official price data |
| A016 | US Labor / Response Rates | Corrected / Exact Value Pending | 60 | CES/CPS 收件率近月值；60% 掉到 40 幾%。 | BLS response rate page可用；CPS 回覆率長期下降方向成立，但精確『60 到 40 幾』尚未驗證。 | Fetch BLS response-rate tables |
| A017 | Global Macro / PMI Dashboard | Reject / Rebuild | 95 | 全球 PMI dashboard 九區並列數字可正式使用。 | 多數 headline 與最新公開資料不一致；目前應標為 UI demo / mock data，不可入正式報告。 | Re-fetch all PMI rows |
| A018 | Global Macro / US PMI | Reject / Replace | 100 | 美國製造業 PMI = 48.7，收縮。 | ISM 2026-06 Manufacturing PMI = 53.3，擴張；New Orders 56.0, Production 52.2, Employment 49.7, Prices 73.0。 | Replace in dashboard |
| A019 | Global Macro / Eurozone PMI | Reject / Replace | 95 | 歐洲製造業 PMI = 45.8，收縮。 | S&P Global Eurozone Manufacturing PMI = 51.4，連續第 5 個月擴張。 | Replace in dashboard |
| A020 | Global Macro / China PMI | Corrected | 90 | 中國官方製造業 PMI = 50.8。 | NBS / Reuters 顯示 2026-06 官方製造業 PMI = 50.3。 | Replace value |
| A021 | Global Macro / Taiwan PMI | Reject / Replace | 95 | 台灣 S&P Global 製造業 PMI = 48.3，收縮。 | S&P Global Taiwan Manufacturing PMI = 55.2，強擴張。 | Replace value and state |
| A022 | Global Macro / Japan PMI | Reject / Replace | 90 | 日本製造業 PMI = 50.1。 | S&P Global Japan Manufacturing PMI final = 54.8；Reuters/TE 也一致。 | Replace value |
| A023 | Global Macro / South Asia PMI | Pending Definition / Likely Replace | 70 | 南亞製造業 PMI = 57.5。 | S&P Global release page 顯示 India Manufacturing PMI Jun = 54.5；若用南亞代表需明確定義。 | Define region proxy and replace |
| A024 | Global Macro / Middle East PMI | Pending Latest Release | 60 | 中東 PMI = 54.2。 | 若以沙烏地為代表，最新可得 S&P Global/Riyad Bank May 2026 = 52.8；June value需再抓。 | Fetch June release or latest available |
| A025 | Global Macro / ASEAN PMI | Pending Definition | 50 | 東南亞 PMI = 51.2，印尼代表。 | 目前缺少明確來源與 proxy 定義；需確認是 ASEAN aggregate、Indonesia、Thailand 或其他。 | Define region proxy |

## def Global PMI Audit

| Region | Indicator | User Value | Verified Value | Verdict | Action/Note |
|---|---|---|---|---|---|
| United States | ISM Manufacturing PMI | 48.7 | 53.3 | Reject / Replace | ISM official: PMI 53.3; table says contraction but actual is expansion. |
| Eurozone | S&P Global Manufacturing PMI | 45.8 | 51.4 | Reject / Replace | S&P Global final 51.4, fifth month expansion. |
| Japan | S&P Global Manufacturing PMI | 50.1 | 54.8 | Reject / Replace | Final Japan PMI 54.8. |
| China | NBS Manufacturing PMI | 50.8 | 50.3 | Corrected | NBS/Reuters reported 50.3. |
| Taiwan | S&P Global Manufacturing PMI | 48.3 | 55.2 | Reject / Replace | Taiwan PMI 55.2; table incorrectly says contraction. |
| South Asia / India | India Manufacturing PMI proxy | 57.5 | 54.5 preliminary from release page | Pending Definition / Likely Replace | Need define South Asia proxy; S&P release page shows India Manufacturing Jun 54.5. |
| Middle East / Saudi | Riyad Bank Saudi PMI proxy | 54.2 | May 2026 52.8; June pending | Pending Latest Release | If using Saudi as proxy, latest available in verified source is May 52.8. |
| ASEAN / Southeast Asia | ASEAN/Indonesia proxy | 51.2 | Undefined | Pending Definition | Need decide aggregate vs country proxy before validation. |

## def VDF v003 Tasks

| Priority | Task | Detail | Owner | Note |
|---|---|---|---|---|
| P0 | Exclude self-ingestion | 排除 _runs、_source_backups、standardized_*、price_breadth_*、TTFI_* | VDF v003 | Required before next scoring |
| P0 | TWSE raw audit | 保存 T86 / MI_MARGN / MI_INDEX 原始回應與錯誤碼 | VDF v003 | 官方資料 0 rows 必修 |
| P0 | Local reader fallback | 修 tw_stock CSV / parquet READ_FAIL：encoding、separator、parquet engine、多表 CSV | VDF v003 | 三大法人與融資本機資料可能已存在 |
| P0 | Official 20 trading-day window | 確保最新 20 交易日涵蓋 2026-06-23 / 2026-06-24 / 2026-06-26 | TTFI v003 | 目前停在 2026-06-16 |
| P1 | Split scores | breadth_only_score / verified_score / data_quality_adjusted_score | TTFI v003 | 避免資料不足卻輸出單一分數 |
| P1 | Global PMI rebuild | 保留 UI 規格，重抓 headline + subcomponents | Global Macro v002 | 目前 PMI 表不可正式使用 |