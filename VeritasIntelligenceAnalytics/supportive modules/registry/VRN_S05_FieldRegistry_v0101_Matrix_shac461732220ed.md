# VRN S05 Field Registry v01.01 — 完整 106 欄位矩陣

**Schema:** VRN_S05_FieldRegistry | **Version:** v01.01 | **Generated:** 2026-05-31T15:30:00+08:00

**Only-Add Compliance:** True ✅

## 統計

- BasicInfo: **30** (V31 LOCKED schema)
- FinancialData: **76** = v0608 (61) + v06126 新增 (15)
- **總計: 106 fields**

## 依賴 SSoT 版本

- `VRN_BASIC_INFO_SCHEMA_LOCK_V31` = 3.1.0
- `VRN_FINANCIAL_ACCOUNT_SSOT_v0608` = 0608
- `VIS_VRN_FinancialRescueRules_v06126` = 06.12.6
- `VIS_VRN_BrokerAlias_Compatibility_v0222` = 0.2.2.2
- `VIS_VRN_BrokerAlias_Extension_v0224` = 0.2.2.4
- `VIS_VRN_BrokerAnalystAdapters_v06146` = 0.6.14.6
- `VIS_VRN_BasicInfoFinancialQualityRules_v0100` = 0.1.0.0
- `VIS_VRN_TickerFilenameSSOT_v0100` = 0.1.0.0
- `VIS_VRN_HistoricalValidationPolicy_v0100` = 0.1.0.0
- `VIS_VRN_EligibleRed_SourceAliasMap_v0102` = 0.1.0.2
- `VIS_VRN_EligibleYellow_TableSplitQueue_v0100` = 0.1.0.0

## A. BasicInfo (V31, 30 fields)

| Field ID | Ordinal | Name | Category | 觀點? | 衍生? | SSoT P1 | 容忍度 |
|---|---|---|---|---|---|---|---|
| BAS_01 | 1 | `report_date` | SourceMetadata | — | 源 | `broker_report` | ±1d (YELLOW) |
| BAS_02 | 2 | `report_code` | Derived | — | ✅ | `computed` | exact match |
| BAS_03 | 3 | `filename` | SourceMetadata | — | 源 | `filesystem` | exact match |
| BAS_04 | 4 | `broker` | BrokerOpinion | ✅ | — | `broker_report` | preserved (no validation) |
| BAS_05 | 5 | `analyst` | BrokerOpinion | ✅ | — | `broker_report` | preserved (no validation) |
| BAS_06 | 6 | `ticker` | Verifiable | — | — | `tickerfilename_ssot_v0100` | exact match |
| BAS_07 | 7 | `yfinance_ticker` | Verifiable | — | — | `computed` | exact match |
| BAS_08 | 8 | `bloomberg_ticker` | Verifiable | — | — | `computed` | exact match |
| BAS_09 | 9 | `name` | Verifiable | — | — | `official_twse` | exact match |
| BAS_10 | 10 | `name_en` | Verifiable | — | — | `official_twse` | exact match |
| BAS_11 | 11 | `rating` | BrokerOpinion | ✅ | — | `broker_report` | preserved (no validation) |
| BAS_12 | 12 | `rating_cat` | BrokerOpinion | ✅ | — | `broker_report` | preserved (no validation) |
| BAS_13 | 13 | `target_price` | BrokerOpinion | ✅ | — | `broker_report` | preserved (no validation) |
| BAS_14 | 14 | `consensus_target_high` | BrokerOpinion | ✅ | — | `broker_report` | preserved (no validation) |
| BAS_15 | 15 | `consensus_target_low` | BrokerOpinion | ✅ | — | `broker_report` | preserved (no validation) |
| BAS_16 | 16 | `consensus_target_mean` | BrokerOpinion | ✅ | — | `broker_report` | preserved (no validation) |
| BAS_17 | 17 | `consensus_target_median` | BrokerOpinion | ✅ | — | `broker_report` | preserved (no validation) |
| BAS_18 | 18 | `consensus_rating` | BrokerOpinion | ✅ | — | `broker_report` | preserved (no validation) |
| BAS_19 | 19 | `consensus_rating_mean` | BrokerOpinion | ✅ | — | `broker_report` | preserved (no validation) |
| BAS_20 | 20 | `analyst_count` | BrokerOpinion | ✅ | — | `broker_report` | preserved (no validation) |
| BAS_21 | 21 | `analyst_strong_buy` | BrokerOpinion | ✅ | — | `broker_report` | preserved (no validation) |
| BAS_22 | 22 | `analyst_buy` | BrokerOpinion | ✅ | — | `broker_report` | preserved (no validation) |
| BAS_23 | 23 | `analyst_hold` | BrokerOpinion | ✅ | — | `broker_report` | preserved (no validation) |
| BAS_24 | 24 | `analyst_sell` | BrokerOpinion | ✅ | — | `broker_report` | preserved (no validation) |
| BAS_25 | 25 | `analyst_strong_sell` | BrokerOpinion | ✅ | — | `broker_report` | preserved (no validation) |
| BAS_26 | 26 | `adj_close` | Verifiable | — | — | `vdf_duckdb` | G≤0.1% / Y≤1.0% |
| BAS_27 | 27 | `adj_close_date` | Verifiable | — | — | `vdf_duckdb` | ±1d (YELLOW) |
| BAS_28 | 28 | `upside_pct` | Derived | — | ✅ | `computed` | exact match |
| BAS_29 | 29 | `upside_source` | Derived | — | ✅ | `computed` | exact match |
| BAS_30 | 30 | `summary` | BrokerOpinion | ✅ | — | `broker_report` | preserved (no validation) |

## B. FinancialData (76 fields = v0608 61 + v06126 新增 15)

### B.1 Income Statement

| UID | Official EN | Unit | Aliases ZH | 容忍度 |
|---|---|---|---|---|
| VRN_FIN_0001 | Revenue | mn TWD | 收入, 營收, 營業收入, 銷貨收入 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0002 | Gross Profit | mn TWD | 毛利, 營業毛利 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0003 | Operating Income | mn TWD | 營業利益, 營業淨利, 營業收入淨額 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0004 | Operating Expense | mn TWD | 營業費用 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0005 | Pretax Income | mn TWD | 稅前利益, 稅前淨利, 稅前純益 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0006 | Net Income | mn TWD | 純益, 本期淨利, 稅後淨利 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0008 | EBITDA | mn TWD | 息稅折舊攤銷前盈餘 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0009 | Depreciation And Amortization | mn TWD | 折舊及攤銷, 折舊及攤提, 折舊攤銷 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0068+v06126 | Profit Before Tax | mn TWD | 稅前純益, 稅前淨利, 稅前利益 | G≤0.5% / Y≤3.0% |

### B.2 Balance Sheet

| UID | Official EN | Unit | Aliases ZH | 容忍度 |
|---|---|---|---|---|
| VRN_FIN_0010 | Cash And Cash Equivalents | mn TWD | 現金約當現金, 現金及約當現金 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0011 | Accounts Receivable | mn TWD | 應收帳款, 應收帳款及票據, 應收帳款與票據 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0012 | Inventory | mn TWD | 存貨 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0013 | Current Assets | mn TWD | 流動資產, 流動資產合計 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0014 | Other Current Assets | mn TWD | 其他流動資產, 其它流動資產 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0015 | Property Plant And Equipment | mn TWD | 不動產、廠房設備, 不動產廠房及設備, 不動產、廠房及設備, 固定資產, 固定資產淨額 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0016 | Long Term Investments | mn TWD | 長期投資, 長期投資合計, 採用權益法之投資, 長期股權投資 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0017 | Other Non Current Assets | mn TWD | 其他非流動資產, 其它非流動資產 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0018 | Total Assets | mn TWD | 總資產, 資產總計, 資產總額, 資產合計 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0019 | Accounts Payable | mn TWD | 應付帳款, 應付帳款及票據 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0020 | Short Term Debt | mn TWD | 短期借款, 短期負債 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0021 | Current Liabilities | mn TWD | 流動負債, 流動負債合計 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0022 | Other Current Liabilities | mn TWD | 其他流動負債 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0023 | Non Current Liabilities | mn TWD | 非流動負債, 其他非流動負債, 長期負債合計, 非流動負債合計, 長期負債 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0024 | Total Liabilities | mn TWD | 總負債, 負債總計, 負債總額, 負債總額 分配後 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0025 | Common Stock | mn TWD | 股本, 普通股股本 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0026 | Retained Earnings | mn TWD | 保留盈餘 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0027 | Parent Equity | mn TWD | 母公司業主權益, 歸屬母公司業主權益 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0028 | Total Equity | mn TWD | 總權益, 權益總計, 股東權益, 權益總額, 股東權益總計… | G≤0.5% / Y≤3.0% |
| VRN_FIN_0029 | Total Liabilities And Equity | mn TWD | 負債及權益總計, 負債和權益總計 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0063🆕 | Short Term Borrowings | mn TWD | 短期借款, 短期銀行借款, 短借, 一年內到期借款 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0064🆕 | Capital Surplus | mn TWD | 資本公積, 資本公積合計 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0065🆕 | Other Equity | mn TWD | 其他權益, 其他權益項目 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0066🆕 | Intangible Assets | mn TWD | 無形資產, 無形資產合計 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0067🆕 | Other Assets | mn TWD | 其他資產, 其他非流動資產, 其它非流動資產 | G≤0.5% / Y≤3.0% |

### B.3 Cash Flow Statement

| UID | Official EN | Unit | Aliases ZH | 容忍度 |
|---|---|---|---|---|
| VRN_FIN_0030 | Operating Cash Flow | mn TWD | 營運現金流, 營業活動現金, 營業活動現金流量, 營業活動之淨現金流入出 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0031 | Investing Cash Flow | mn TWD | 投資活動現金, 投資活動現金流量, 長期投資變動 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0032 | Financing Cash Flow | mn TWD | 籌資活動現金, 籌資活動現金流量, 融資活動之淨現金流入出, 融資活動之淨現金流入(出), 其他籌資活動現金流量 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0033 | Capital Expenditure | mn TWD | 資本支出, 資本支出淨額 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0034 | Free Cash Flow | mn TWD | 自由現金流 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0035 | Net Change In Cash | mn TWD | 淨現金流量, 現金淨增加, 本期現金與約當現金增加數, 現金增加數 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0036 | Beginning Cash | mn TWD | 期初現金, 期初現金與約當現金餘額 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0037 | Ending Cash | mn TWD | 期末現金, 期末現金與約當現金餘額 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0038 | Working Capital Change | mn TWD | 營運資金變動 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0039 | Long Term Investment Change | mn TWD | 長期投資變動 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0040 | Debt Change | mn TWD | 長借公司債變動, 長借/公司債變動 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0041 | Cash Dividend Paid | mn TWD | 發放現金股利 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0042 | Cash Capital Increase | mn TWD | 現金增資 | G≤0.5% / Y≤3.0% |

### B.4 Ratio Analysis

| UID | Official EN | Unit | Aliases ZH | 容忍度 |
|---|---|---|---|---|
| VRN_FIN_0043 | Gross Margin | % | 毛利率 | G≤0.3pp / Y≤1.0pp |
| VRN_FIN_0044 | Operating Margin | % | 營益率, 營業利益率 | G≤0.3pp / Y≤1.0pp |
| VRN_FIN_0045 | Net Margin | % | 淨利率 | G≤0.3pp / Y≤1.0pp |
| VRN_FIN_0046 | ROE | % | 股東權益報酬率 | G≤0.3pp / Y≤1.0pp |
| VRN_FIN_0047 | ROA | % | 資產報酬率 | G≤0.3pp / Y≤1.0pp |
| VRN_FIN_0048 | Current Ratio | ratio | 流動比率 | G≤0.5% / Y≤5.0% |
| VRN_FIN_0049 | Debt Ratio | ratio | 負債比率 | G≤0.5% / Y≤5.0% |
| VRN_FIN_0050 | Inventory Turnover | x | 存貨週轉率 | G≤0.5% / Y≤5.0% |
| VRN_FIN_0051 | Receivable Turnover | x | 應收帳款週轉率 | G≤0.5% / Y≤5.0% |
| VRN_FIN_0052 | Asset Turnover | x | 資產週轉率 | G≤0.5% / Y≤5.0% |
| VRN_FIN_0053 | P/E | x | 本益比 | G≤0.5% / Y≤5.0% |
| VRN_FIN_0054 | P/B | x | 股價淨值比 | G≤0.5% / Y≤5.0% |
| VRN_FIN_0069🆕 | Debt To Asset Ratio | % | 負債占資產比率, 負債比率, 負債資產比 | G≤0.3pp / Y≤1.0pp |
| VRN_FIN_0070🆕 | Quick Ratio | % | 速動比率, 速動比率% | G≤0.3pp / Y≤1.0pp |
| VRN_FIN_0071🆕 | Interest Coverage Ratio | x | 利息保障倍數 | G≤0.5% / Y≤5.0% |
| VRN_FIN_0072🆕 | Accounts Receivable Turnover | x | 應收款項週轉率, 應收帳款週轉率 | G≤0.5% / Y≤5.0% |
| VRN_FIN_0073🆕 | Days Sales Outstanding | days | 平均收現日數, 應收帳款收現日數 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0074🆕 | Accounts Payable Turnover | x | 應付款項週轉率, 應付帳款週轉率 | G≤0.5% / Y≤5.0% |
| VRN_FIN_0075🆕 | Days Inventory Outstanding | days | 平均銷貨日數, 存貨銷售日數 | G≤0.5% / Y≤3.0% |
| VRN_FIN_0076🆕 | Fixed Asset Turnover | x | 不動產廠房及設備週轉率, 不動產、廠房及設備週轉率, 固定資產週轉率 | G≤0.5% / Y≤5.0% |
| VRN_FIN_0077🆕 | Total Asset Turnover | x | 總資產週轉率 | G≤0.5% / Y≤5.0% |

### B.5 Per Share Analysis

| UID | Official EN | Unit | Aliases ZH | 容忍度 |
|---|---|---|---|---|
| VRN_FIN_0055 | EPS | TWD | 每股盈餘 | G≤1.0% / Y≤5.0% |
| VRN_FIN_0056 | BVPS | TWD | 每股淨值 | G≤1.0% / Y≤5.0% |
| VRN_FIN_0057 | CFPS | TWD | 每股現金流 | G≤1.0% / Y≤5.0% |
| VRN_FIN_0058 | DPS | TWD | 每股股利 | G≤1.0% / Y≤5.0% |

### B.6 Growth Ratio

| UID | Official EN | Unit | Aliases ZH | 容忍度 |
|---|---|---|---|---|
| VRN_FIN_0059 | Sales YoY | % | 營收年增率 | G≤0.3pp / Y≤1.0pp |
| VRN_FIN_0060 | EPS YoY | % | eps年增率 | G≤0.3pp / Y≤1.0pp |
| VRN_FIN_0061 | Sales QoQ | % | 營收季增率 | G≤0.3pp / Y≤1.0pp |
| VRN_FIN_0062 | EPS QoQ | % | eps季增率 | G≤0.3pp / Y≤1.0pp |

## C. Governance Policy (來自 HistoricalValidationPolicy v0100)

- **broker_report 可作 FinancialData 真理源:** False ❌
- **broker_report 可作 BasicInfo 觀點源:** True ✅
- **BasicInfo 觀點欄位 (18 個,broker_report 為唯一來源):**
  - `analyst`
  - `analyst_buy`
  - `analyst_count`
  - `analyst_hold`
  - `analyst_sell`
  - `analyst_strong_buy`
  - `analyst_strong_sell`
  - `broker`
  - `consensus_rating`
  - `consensus_rating_mean`
  - `consensus_target_high`
  - `consensus_target_low`
  - `consensus_target_mean`
  - `consensus_target_median`
  - `rating`
  - `rating_cat`
  - `summary`
  - `target_price`

- **允許的歷史真理源 (8):**
  - `official_twse`
  - `official_tpex`
  - `mops`
  - `yfinance`
  - `historical_database`
  - `vdf_duckdb`
  - `audited_financial_history`
  - `market_derived_history`

## D. Ticker Regex v2 (修正版)

- **TW_TICKER_REGEX:** `(?<!\d)([1-9]\d{3})(?!\d)` (only first-digit != 0, year band moved out)
- **TW_YFINANCE:** `(?<!\d)([1-9]\d{3})\.(TW|TWO)\b`
- **TW_BLOOMBERG:** `(?<!\d)([1-9]\d{3})\s+TT\b`

### 2021–2030 真實鋼鐵股 (舊 regex 誤殺名單)

- **2021** = 中鋼構
- **2022** = 聚亨
- **2023** = 燁輝
- **2024** = 志聯
- **2025** = 千興
- **2027** = 大成鋼
- **2028** = 威致
- **2029** = 盛餘
- **2030** = 彰源

## E. 容忍度體系

| 類別 | GREEN | YELLOW | 量綱 |
|---|---|---|---|
| price | ≤ 0.1% | ≤ 1.0% | relative |
| eps | ≤ 0.5% | ≤ 3.0% | relative |
| fin_value (mn TWD) | ≤ 0.5% | ≤ 3.0% | relative |
| ratio (x, ratio) | ≤ 0.5% | ≤ 5.0% | relative |
| ratio_pp (% type) | ≤ 0.3pp | ≤ 1.0pp | absolute pp |
| per_share (TWD) | ≤ 1.0% | ≤ 5.0% | relative |
| date | 0d | ±1d | days |
| text_enum | exact match | exact match | exact |
| opinion | preserved | preserved | no validation |
