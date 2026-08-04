# VRN S05 Field Registry v01.02 — 完整三層驗證整合文檔

**Schema:** `VRN_S05_FieldRegistry` | **Version:** `v01.02` | **Generated:** `2026-05-31T16:30:00+08:00`

**Only-Add Compliance:** ✅ True

## v01.01 → v01.02 變更紀錄 (Only-Add)

- ✅ Added 3-layer validation per field: regex / synonyms / validation_method
- ✅ Added dual-track Valuation Analysis (Track A T-1 verification + Track B T-latest realtime)
- ✅ Added ALL_REGEX dictionary (40 patterns: date/year/quarter/month/email/tel/rating/target/ticker/...)
- ✅ Added RATING_LIST V22_2 + RATING_FLAT_LIST (5 buckets, 47 aliases)
- ✅ Added TARGET_PRICE_SYNONYMS (12) + TARGET_PRICE_STOPWORDS_PREVIOUS (12)
- ✅ Added ANALYST_STOPWORDS (27)
- ✅ Added EMAIL_DOMAIN_TO_BROKER (43 domains → 32 brokers)
- ✅ Added EMAIL_LOCAL_COMMON_LASTNAMES_TW (22 common surnames for Raymondkuo→Raymond Kuo splitter)
- ✅ Added VRN_VALUATION_DICTIONARY V0595 (22 methods)
- ✅ Added EPS_POLICY (TIFRS dilution: CB/ESOP/RSU)
- ✅ Integrated VRN_BROKER_LIST v02.00 (32 brokers)

## 整合統計

| 項目 | 數量 |
|---|---|
| BasicInfo 欄位 | **30** |
| FinancialData 欄位 | **76** |
| **Field 總計** | **106** |
| ALL_REGEX patterns | **40** |
| RATING 規範化分類 | **5** buckets |
| RATING flat aliases | **47** |
| TARGET_PRICE 同義字 | **12** |
| Email domain → broker mappings | **43** |
| Valuation methods (V0595) | **22** |

## 🎯 Valuation Analysis 雙軌制 (Dual-Track)

**Policy Version:** `v1.1`

**規則:** All valuation values are computed on TWO tracks for every report

### Track A — 報告日驗證軌 (Report Date Verification)

- **目的:** Verify broker_report stated valuation values match T-1 ADJ Close calculation
- **股價輸入:** `adj_close (T-1 = report_date minus 1 trading day)`
- **EPS 輸入:** Diluted EPS for the valuation base year stated in report
- **產出欄位:** `upside_at_report_pct, pe_at_report, pb_at_report, implied_target_at_report`
- **容忍度:** 0.5pp / 3pp green-yellow-red on upside; 0.5% / 3% on multiple
- **失敗處置:** Flag for human review; record discrepancy in audit log; preserve broker value

### Track B — 最新值即時軌 (Latest Realtime)

- **目的:** Compute current-state valuation using LATEST available ADJ Close
- **股價輸入:** `adj_close (latest T-day, queried at S05 run time)`
- **EPS 輸入:** Diluted EPS for the same base year as Track A
- **產出欄位:** `upside_realtime_pct, pe_realtime, pb_realtime, implied_target_realtime`
- **容忍度:** N/A — realtime is informational, not validated
- **漂移處置:** If realtime upside_pct differs from report by >5pp, mark report 'STALE'

### 支援的 22 種估值方法 (VRN_VALUATION_DICTIONARY V0595)

`P/E | P/B | DCF | DDM | FCFF | FCFE | RIV | APV | GGM | EVA | P/S | P/CF | PEG | EV/EBITDA | EV/Sales | EV/EBIT | NAV | SOTP | Replacement | Liquidation | BV | NTA`

## EPS Policy (TIFRS 規範)

- **diluted_eps_preferred:** True
- **basic_eps_fallback:** Only when explicitly labeled or when Diluted unavailable
- **valuation_eps:** ALWAYS use Diluted EPS
- **valuation_price:** ALWAYS use latest ADJ Close (T-day)
- **verification_price:** Use T-1 ADJ Close (day before report date) for cross-check against broker_report values
- **tifrs_dilution_includes:** Convertible Bond (CB), Employee Stock Option (ESOP), Restricted Stock Units (RSU)

## A. ALL_REGEX 字典 (40 patterns)

| Rule | Pattern | 用途 | Pass 範例 |
|---|---|---|---|
| `DATE_ISO_AD` | `^\d{4}-\d{2}-\d{2}$` | AD YYYY-MM-DD | 2026-03-23 |
| `DATE_SLASH_AD` | `^\d{4}/\d{2}/\d{2}$` | AD YYYY/MM/DD | 2026/03/23 |
| `DATE_DOT_AD` | `^\d{4}\.\d{2}\.\d{2}$` | AD YYYY.MM.DD | 2026.03.23 |
| `DATE_COMPACT_AD` | `^(20\d{2})(0[1-9]\|1[0-2])(0[1-9]\|[12]\d\|3[01])$` | AD YYYYMMDD | 20260323 |
| `DATE_ROC_SLASH` | `^(\d{2,3})/(\d{2})/(\d{2})$` | ROC YYY/MM/DD | 113/03/23, 99/12/31 |
| `DATE_ROC_COMPACT` | `^(1\d{2})(0[1-9]\|1[0-2])(0[1-9]\|[12]\d\|3[01])$` | ROC YYYMMDD (1141202=2025-12-02) | 1141202 |
| `DATE_CN_YEAR` | `(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日?` | 中文 YYYY年MM月DD日 | 2026年3月23日 |
| `DATE_ROC_CN_YEAR` | `(?:民國)?\s*(1\d{2})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日` | 民國113年3月23日 | 民國113年3月23日 |
| `QUARTER_YYYYQn` | `^(\d{4})Q([1-4])$` | YYYYQn | 2026Q1, 2025Q4 |
| `QUARTER_QnYYYY` | `^Q([1-4])\s*(\d{4})$` | Q1 2026 | Q1 2026 |
| `QUARTER_CN` | `(\d{4})\s*年\s*第\s*([1-4])\s*季` | 2026年第1季 | 2026年第1季 |
| `QUARTER_HALF` | `(\d{4})\s*年\s*(上\|下)半年\|H([12])\s*(\d{4})\|(\d{4})H([12])` | 上下半年 H1/H2 | 2026年上半年, H1 2026 |
| `YEAR_AD` | `\b(19\d{2}\|20\d{2})\b` | 西元年 4 位 | 2026 |
| `YEAR_AD_2DIGIT_FY` | `\bFY(\d{2})E?\b` | FY24/FY24E/FY25 | FY24, FY25E |
| `YEAR_AD_FORECAST` | `\b(20\d{2})E\b` | 2026E (預估年) | 2026E, 2027E |
| `YEAR_AD_ACTUAL` | `\b(20\d{2})A\b` | 2024A (實績年) | 2024A |
| `YEAR_ROC` | `\b(1\d{2})\s*年\b` | 民國年 113年 | 113年, 114年 |
| `YEAR_RANGE` | `(20\d{2})\s*[~\-至到]\s*(20\d{2})E?` | 2024~2026E 年區間 | 2024~2026, 2024-2026E |
| `MONTH_YYYYMM` | `^(20\d{2})[-/.]?(0[1-9]\|1[0-2])$` | YYYY-MM / YYYY/MM / YYYYMM | 2026-03, 2026/03 |
| `MONTH_CN` | `(\d{4})\s*年\s*(\d{1,2})\s*月` | 2026年3月 | 2026年3月 |
| `MONTH_ROC_CN` | `(?:民國)?\s*(1\d{2})\s*年\s*(\d{1,2})\s*月` | 民國113年3月 | 民國113年3月 |
| `NUMBER_WITH_COMMAS` | `^-?\d{1,3}(,\d{3})*(\.\d+)?$` | 含千分位數字 | 1,234, -12,345.67 |
| `PERCENT_VALUE` | `^-?\d+(\.\d+)?%$` | 百分比 12% | 12%, -3.5% |
| `FINANCE_EMPTY` | `^(--\|N/A\|NA\|無\|空白\|null\|None\|-)?$` | 財務空值佔位符 | --, N/A |
| `PARENS_NEGATIVE` | `^\(\s*(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*\)$` | 括號表示負值 (123) | (123), (1,234.5) |
| `CURRENCY_UNIT` | `(?i)(新台幣\|TWD\|USD\|美元\|港幣\|HKD\|人民幣\|CNY\|日圓\|JPY)` | 幣別 | 新台幣, USD |
| `AMOUNT_UNIT_TW` | `(?i)單位[:：](新台幣)?(仟元\|千元\|百萬元\|億元\|元)` | 單位:百萬元 | 單位:百萬元 |
| `TW_TICKER_4DIGIT` | `(?<!\d)([1-9]\d{3})(?!\d)` | TW 4 碼 first != 0 | 2330, 2021 |
| `TW_YFINANCE` | `(?<!\d)([1-9]\d{3})\.(TW\|TWO)\b` | 2330.TW / 6488.TWO | 2330.TW, 6488.TWO |
| `TW_BLOOMBERG` | `(?<!\d)([1-9]\d{3})\s+TT\b` | 2330 TT | 2330 TT |
| `EMAIL_FULL` | `[A-Za-z][A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}` | 完整 email | Raymond.Kuo@gs.com, 10863@entrust.com.tw |
| `EMAIL_LOCAL_NUMERIC` | `^\d+$` | 純數字 local part (contact ID, 非 analyst) | 10863, 450 |
| `EMAIL_LOCAL_NAME` | `([A-Za-z][A-Za-z0-9._\-]{1,60})@([A-Za-z0-9.\-]+\.[A-Za-z]{2,})` | 可解析 analyst 的 email | Raymond.Kuo@gs.com |
| `TEL_TW_FULL` | `(\+886[\-\s]?\d{1,2}[\-\s]?\d{3,4}[\-\s]?\d{3,4}\|\(?02\)?[\-\s]?\d{3,4}[\-\s]?\d{4}\|\(?0\d{1,2}\)?[\-\s]?\d{3,4}[\-\s]?\d{3,4})` | 台灣電話 (含 +886, 02-xxxx-xxxx, 0x-xxx-xxxx) | +886-2-2345-6789, (02)2345-6789 |
| `TEL_EXTENSION` | `(?:ext\|分機\|轉)\.?\s*(\d{2,5})` | 分機號碼 | ext 123, 分機 1234 |
| `BROKER_RATING` | `(?i)(強力買進\|買進\|買入\|逢低買進\|增持\|加碼\|區間操作\|持有\|中立\|減持\|減碼\|賣出\|未評等\|NR\|Strong\s*Buy\|Outperform\|Overweight\|Buy\|Accumulate\|Add\|Hold\|Neutral\|Market\s*Perform\|Equal[- ]?Weight\|Reduce\|Underperform\|Underweight\|Sell\|Not\s*Rated)` | 券商評等(完整版) | Buy, 強力買進 |
| `TARGET_PRICE_LABEL` | `(?:目標價\|目標價格\|合理價\|推估合理價\|Target\s*Price\|Price\s*Target\|TP\|PT\|Fair\s*Value)\s*[:：]?\s*(?:NT\$\|新台幣\|TWD\|NTD\|US\$\|USD)?\s*([0-9]+(?:\.[0-9]+)?)` | 目標價數值 | 目標價: 1100, TP: 1100 |
| `TARGET_PRICE_VERB` | `(?:給予\|上修至\|下修至\|維持\|調升至\|調降至\|設定為)\s*(?:目標價\|目標價格)?\s*(?:NT\$\|新台幣\|TWD\|NTD)?\s*([0-9]+(?:\.[0-9]+)?)\s*元` | 動詞引導目標價 | 給予目標價 1100 元, 上修至 1200 元 |
| `TARGET_PRICE_TAIL` | `([0-9]+(?:\.[0-9]+)?)\s*元\s*(?:目標價\|合理價)` | 尾隨格式 1100元目標價 | 1100 元目標價 |
| `UPSIDE_PCT` | `(?:upside\|上漲空間\|上漲幅度)\s*[:：]?\s*([+-]?\d+(?:\.\d+)?)\s*%` | 上漲空間 % | upside: 25%, 上漲空間 25% |

## B. RATING_LIST V22_2 (5 buckets, 47 aliases)

| Canonical | 中文 | 英文 |
|---|---|---|
| **strong_buy** | `強力買進` | `strong buy`, `strong-buy`, `Strong Buy` |
| **buy** | `買進`, `買入`, `增持`, `加碼`, `逢低買進` | `buy`, `Buy`, `overweight`, `Overweight`, `outperform`, `Outperform`, `accumulate`, `Accumulate`, `add`, `Add` |
| **hold** | `中立`, `持有`, `區間操作` | `hold`, `Hold`, `neutral`, `Neutral`, `equal-weight`, `Equal-Weight`, `market perform`, `Market Perform` |
| **sell** | `賣出`, `減碼`, `減持` | `sell`, `Sell`, `underweight`, `Underweight`, `underperform`, `Underperform`, `reduce`, `Reduce` |
| **not_rated** | `未評等`, `無評等` | `not rated`, `Not Rated`, `nr`, `NR` |

**ANALYST_STOPWORDS (26):** `目標價`, `目標價格`, `合理價`, `評等`, `評級`, `投資評等`, `投資建議`, `買進`, `買入`, `增持`, `中立`, `持有`, `減持`, `賣出`, `未評等…`

## C. TARGET_PRICE Dictionary

**Synonyms (12):** `目標價`, `目標價格`, `合理價`, `推估合理價`, `目標股價`, `Target Price`, `Price Target`, `TP`, `PT`, `Fair Value`, `fair value`, `target`

**Previous TP Stopwords (12):** `previous`, `prior`, `old`, `last`, `former`, `前次`, `前目標`, `原目標`, `舊目標`, `前一目標`, `原先`, `舊`

## D. EMAIL_DOMAIN → BROKER (43 mappings)

`Email 中 @ 前面 = 分析師英文名候選; @ 後面 = broker domain`

| Domain | Broker (canonical) | English Name | Confidence |
|---|---|---|---|
| `entrust.com.tw` | **華南** | HuaNan | 0.95 |
| `gs.com` | **GS** | Goldman Sachs | 0.95 |
| `goldmansachs.com` | **GS** | Goldman Sachs | 0.95 |
| `morganstanley.com` | **MS** | Morgan Stanley | 0.95 |
| `ms.com` | **MS** | Morgan Stanley | 0.95 |
| `jpmorgan.com` | **JP** | J.P. Morgan | 0.95 |
| `jpmchase.com` | **JP** | J.P. Morgan | 0.9 |
| `daiwa.com` | **Daiwa** | Daiwa Securities | 0.95 |
| `daiwacm.com` | **Daiwa** | Daiwa Securities | 0.95 |
| `citi.com` | **Citi** | Citigroup | 0.95 |
| `citigroup.com` | **Citi** | Citigroup | 0.95 |
| `ctbcbank.com` | **中信** | CTBC | 0.9 |
| `ctbcholding.com` | **中信** | CTBC | 0.9 |
| `megabank.com.tw` | **兆豐** | Megabank | 0.9 |
| `emega.com.tw` | **兆豐** | Megabank | 0.85 |
| `cathaysite.com.tw` | **國泰** | Cathay | 0.9 |
| `cathaybk.com.tw` | **國泰** | Cathay | 0.85 |
| `capital.com.tw` | **群益** | Capital Securities | 0.9 |
| `president.com.tw` | **統一** | President | 0.9 |
| `firstcapital.com.tw` | **第一金** | First Securities | 0.9 |
| `kgi.com` | **凱基** | KGI | 0.9 |
| `kgieworld.com.tw` | **凱基** | KGI | 0.9 |
| `yuanta.com.tw` | **元大** | Yuanta | 0.9 |
| `yuanta.com` | **元大** | Yuanta | 0.9 |
| `fubon.com` | **富邦** | Fubon | 0.9 |
| `sinopac.com` | **永豐** | SinoPac | 0.9 |
| `esunbank.com.tw` | **玉山** | E.Sun | 0.9 |
| `taishinholdings.com.tw` | **台新** | Taishin | 0.9 |
| `ubs.com` | **UBS** | UBS | 0.95 |
| `hsbc.com` | **HSBC** | HSBC | 0.95 |
| `macquarie.com` | **MQ** | Macquarie | 0.95 |
| `jefferies.com` | **Jefferies** | Jefferies | 0.95 |
| `nomura.com` | **Nomura** | Nomura | 0.95 |
| `clsa.com` | **CLSA** | CLSA | 0.95 |
| `bernstein.com` | **Bernstein** | Bernstein | 0.95 |
| `bofa.com` | **BofA** | Bank of America | 0.95 |
| `baml.com` | **BofA** | Bank of America | 0.9 |
| `db.com` | **DB** | Deutsche Bank | 0.95 |
| `creditsuisse.com` | **CS** | Credit Suisse | 0.95 |
| `barclays.com` | **BARC** | Barclays | 0.95 |
| `bnpparibas.com` | **BNP** | BNP Paribas | 0.95 |
| `gf.com.cn` | **GF** | GF Securities | 0.95 |
| `clst.com.hk` | **CLST** | CLST | 0.9 |

**Email Local Splitter 共用姓氏字典 (22):** `kuo, chen, chang, wang, lin, lee, liu, huang, hsu, tsai, chiu, wu, yang, ho, chou, tseng, fan, lai, hung, chao, kao, peng`

## E. VRN_VALUATION_DICTIONARY V0595 (22 methods)

| UID | Canonical | 中文名 | Category | 中文同義字 | 英文同義字 |
|---|---|---|---|---|---|
| VAL_001 | **P/E** | 本益比 | Relative | 本益比, 市盈率, 目標本益比 | PER, PE, P/E Ratio |
| VAL_002 | **P/B** | 股價淨值比 | Relative | 股價淨值比, 市淨率, 淨值比 | PBR, PB Ratio, PTB |
| VAL_003 | **DCF** | 現金流量折現法 | Absolute | 折現現金流, 現金流折現, 自由現金流折現 | DCF Model, WACC, Terminal Value |
| VAL_004 | **DDM** | 股利折現模型 | Absolute | 股利折現, 股息折現, 殖利率評價 | Dividend Discount, Dividend Yield Valuation |
| VAL_005 | **FCFF** | 企業自由現金流量 | Absolute | 企業自由現金流, 公司自由現金流 | FCFF |
| VAL_006 | **FCFE** | 股權自由現金流量 | Absolute | 股權自由現金流, 股東自由現金流 | FCFE |
| VAL_007 | **RIV** | 剩餘所得估值法 | Absolute | 剩餘收益, 超額報酬模型 | RIV, Residual Income |
| VAL_008 | **APV** | 調整後現值法 | Absolute | 調整後現值, 調整現值 | APV |
| VAL_009 | **GGM** | 戈登成長模型 | Absolute | 戈登模型, 股利穩定成長模型 | GGM, Constant Growth Model |
| VAL_010 | **EVA** | 經濟附加價值 | Absolute | 經濟利潤, 經濟增加值 | EVA, Economic Profit |
| VAL_011 | **P/S** | 股價營收比 | Relative | 股價營收比, 市銷率, 營收倍數 | PSR, Sales Multiple, Revenue Multiple |
| VAL_012 | **P/CF** | 股價現金流量比 | Relative | 市現率, 價格現金流比 | PCF, P/CF |
| VAL_013 | **PEG** | 本益成長比 | Relative | 本益成長比, PEG 評價 | PEG, PEG Ratio |
| VAL_014 | **EV/EBITDA** | 企業價值倍數 | Relative | 企業價值倍數, 企業乘數, EBITDA 倍數 | EV/EBITDA, Enterprise Multiple |
| VAL_015 | **EV/Sales** | 企業價值對營收比 | Relative | 企業價值營收比 | EV/Sales, EV/Revenue, EV/S |
| VAL_016 | **EV/EBIT** | 企業價值對息稅前利潤比 | Relative | EBIT 倍數 | EV/EBIT, EBIT Multiple |
| VAL_017 | **NAV** | 淨資產價值法 | Asset | 淨資產價值, 資產淨值 | NAV |
| VAL_018 | **SOTP** | 分部估值法 | Asset | 加總估值, 拆分估值, 分類加總 | SOTP, Sum-of-the-Parts, Segment Valuation |
| VAL_019 | **Replacement** | 重置成本法 | Asset | 重置成本 | Replacement Cost |
| VAL_020 | **Liquidation** | 清算價值法 | Asset | 清算價值 | Liquidation Value |
| VAL_021 | **BV** | 帳面價值 | Asset | 帳面值 | BV, Book Value Method |
| VAL_022 | **NTA** | 有形資產淨值 | Asset | 有形淨資產 | NTA |

## F. BasicInfo 30 欄位三層驗證明細

### BAS_01. `report_date` (BasicInfo.SourceMetadata)

- **Type:** `VARCHAR` | **Role:** `report_date` | **Status:** 📄 SOURCE
- **Regex layer (8):** `DATE_COMPACT_AD`, `DATE_ISO_AD`, `DATE_SLASH_AD`, `DATE_DOT_AD`, `DATE_ROC_COMPACT`, `DATE_ROC_SLASH`, `DATE_CN_YEAR`, `DATE_ROC_CN_YEAR`
- **Synonyms layer (6):** `報告日期`, `Report Date`, `Date`, `出版日`, `發布日`, `Issue Date`
- **Validation method:**
  1. Try ROC patterns first (DATE_ROC_COMPACT / DATE_ROC_SLASH); if matched, convert to AD (yyy+1911)
  2. Try AD patterns (DATE_COMPACT_AD / DATE_ISO_AD / DATE_SLASH_AD)
  3. Try Chinese natural language (DATE_CN_YEAR / DATE_ROC_CN_YEAR)
  4. Fallback to filename rescue via def_extract_report_date_from_filename_v0100
  5. Normalize all forms to ISO YYYY-MM-DD
  6. Cross-check: difference between filename date and report header date must ≤ 1 calendar day (date tolerance)

### BAS_02. `report_code` (BasicInfo.Derived)

- **Type:** `VARCHAR` | **Role:** `primary_key_unique` | **Status:** 🧮 DERIVED
- **Regex layer (1):** `^[A-Za-z\u4e00-\u9fff]+-[1-9]\d{3}-[\u4e00-\u9fffA-Za-z0-9]+-\d{8}$`
- **Synonyms layer (2):** `Report ID`, `報告編號`
- **Validation method:**
  1. Format: BrokerAbbrev-Ticker-Name-YYYYMMDD
  2. PRIMARY KEY of vrn_basic_info table (DB unique constraint)
  3. Computed: f'{broker}-{ticker}-{name}-{report_date.replace("-","")}'

### BAS_03. `filename` (BasicInfo.SourceMetadata)

- **Type:** `VARCHAR` | **Role:** `source_filename` | **Status:** 📄 SOURCE
- **Regex layer (0):** _(none)_
- **Synonyms layer (3):** `File Name`, `檔名`, `Source File`
- **Validation method:**
  1. Source: filesystem (uploads.filename)
  2. Source for filename rescue (ticker/date/broker/analyst/company extraction)

### BAS_04. `broker` (BasicInfo.BrokerOpinion)

- **Type:** `VARCHAR` | **Role:** `broker` | **Status:** 🔒 OPINION (broker 唯一)
- **Regex layer (1):** `BROKER_RATING`
- **Synonyms layer (7):** `券商`, `投顧`, `證券`, `Broker`, `Securities`, `Capital`, `Investment`
- **Validation method:**
  1. Match against VRN_BROKER_LIST_v02 (32 canonical brokers, 200+ aliases)
  2. Use word-boundary regex (?<![A-Za-z0-9])X(?![A-Za-z0-9]) per BrokerAlias_Extension_v0224
  3. Bare 2-letter abbrevs (MS/GS) ONLY in filename header zone, NOT in body text
  4. Cross-check via email domain (EMAIL_DOMAIN_TO_BROKER, 43 domains)
  5. If filename contains 'MQ-' prefix and PDF text layer empty → route REVIEW_STAGING_NO_OCR
  6. Compatibility gate required for: GS/JP/MS/MQ (4 brokers)
  7. Opinion field — broker_report is sole truth, no external override

### BAS_05. `analyst` (BasicInfo.BrokerOpinion)

- **Type:** `VARCHAR` | **Role:** `analyst` | **Status:** 🔒 OPINION (broker 唯一)
- **Regex layer (0):** _(none)_
- **Synonyms layer (8):** `分析師`, `研究員`, `Analyst`, `撰文`, `作者`, `Prepared by`, `Author`, `Researcher`
- **Validation method:**
  1. Strong pattern (block): (聯絡方式|研究員聯絡方式)...研究員 NAME 電子信箱 EMAIL
  2. Line-pair pattern: 研究員 / 分析師 + 同行右側 2-4 中文字 (HuaNan adapter)
  3. Email-above-zone: email 上方 1-5 行找中文姓名 (排除 ANALYST_STOPWORDS)
  4. Email-local fallback: Raymond.Kuo@gs.com → Raymond Kuo (split by . _ -)
  5. Numeric-only email local (10863, 450) ≠ analyst (contact ID only)
  6. English-only email local with concatenated lastname: Raymondkuo → Raymond Kuo (common last names: kuo/chen/chang/...)
  7. Memo/訪談/速報 reports allow null analyst (NOT forced missing)
  8. Opinion field — broker_report is sole truth, no external override

### BAS_06. `ticker` (BasicInfo.Verifiable)

- **Type:** `VARCHAR` | **Role:** `tw_ticker` | **Status:** 🟢 VERIFIABLE
- **Regex layer (3):** `TW_TICKER_4DIGIT`, `TW_YFINANCE`, `TW_BLOOMBERG`
- **Synonyms layer (8):** `代號`, `股票代號`, `標的代號`, `Ticker`, `Stock Code`, `TT Code`, `BBG`, `Bloomberg`
- **Validation method:**
  1. Apply TW_TICKER_4DIGIT regex (first digit != 0, 4 digits)
  2. If candidate in 2021-2030 band → call disambiguate_year_vs_ticker:
     a. matches first-page info-zone → TICKER (0.97)
     b. in TWSE/TPEX official list → TICKER (0.90)
     c. neighbor has 年/Q/H/FY/季 cue → YEAR (0.90)
     d. else → AMBIGUOUS (manual review)
  3. Tri-code cross-check: filename ticker == yfinance core4 == bloomberg core4
  4. SSoT P1: TickerFilenameSSOT.tricode_crosscheck.filename_ticker (truth)
  5. SSoT P2: broker_report header (observation)
  6. SSoT P3: official_twse listed securities (truth)

### BAS_07. `yfinance_ticker` (BasicInfo.Verifiable)

- **Type:** `VARCHAR` | **Role:** `yfinance_ticker` | **Status:** 🟢 VERIFIABLE
- **Regex layer (1):** `TW_YFINANCE`
- **Synonyms layer (4):** `Yahoo Ticker`, `YF`, `.TW`, `.TWO`
- **Validation method:**
  1. Format: {ticker}.TW (TWSE) or {ticker}.TWO (TPEX)
  2. Validate suffix matches actual exchange via VDF DuckDB tickers.exchange
  3. Core 4 digits must match ticker field exactly

### BAS_08. `bloomberg_ticker` (BasicInfo.Verifiable)

- **Type:** `VARCHAR` | **Role:** `bloomberg_ticker` | **Status:** 🟢 VERIFIABLE
- **Regex layer (1):** `TW_BLOOMBERG`
- **Synonyms layer (3):** `BBG`, `Bloomberg Ticker`, `TT Code`
- **Validation method:**
  1. Format: {ticker} TT (4-digit + space + TT)
  2. Core 4 digits must match ticker field exactly
  3. Used for Bloomberg terminal reference cross-check

### BAS_09. `name` (BasicInfo.Verifiable)

- **Type:** `VARCHAR` | **Role:** `company_name_zh` | **Status:** 🟢 VERIFIABLE
- **Regex layer (0):** _(none)_
- **Synonyms layer (6):** `公司`, `公司名`, `公司名稱`, `Company`, `Company Name`, `Issuer`
- **Validation method:**
  1. Filename rescue: pattern '(NNNN) 公司名' or '公司名 (NNNN)'
  2. Cross-check with TWSE listed securities short_name_zh
  3. Cross-check with VDF DuckDB tickers.name_zh
  4. Allow nickname prefix match (e.g. '台積' ⊂ '台積電') if ticker matches
  5. SSoT P1: official_twse, P2: vdf_duckdb, P3: broker_report (observation)

### BAS_10. `name_en` (BasicInfo.Verifiable)

- **Type:** `VARCHAR` | **Role:** `company_name_en` | **Status:** 🟢 VERIFIABLE
- **Regex layer (0):** _(none)_
- **Synonyms layer (3):** `English Name`, `Company EN`, `Name (EN)`
- **Validation method:**
  1. SSoT P1: official_twse listed_securities.name_en
  2. SSoT P2: yfinance.longName
  3. SSoT P3: broker_report (observation)

### BAS_11. `rating` (BasicInfo.BrokerOpinion)

- **Type:** `VARCHAR` | **Role:** `rating_raw` | **Status:** 🔒 OPINION (broker 唯一)
- **Regex layer (1):** `BROKER_RATING`
- **Synonyms layer (6):** `評等`, `評級`, `投資評等`, `投資建議`, `Rating`, `Recommendation`
- **Validation method:**
  1. Match against VIS_VRN_RATING_WORDS (15 entries) and RATING_LIST_V22_2 (47 aliases)
  2. Look in TOP_ZONE / LEFT_ZONE / RIGHT_ZONE / TITLE_ZONE / BODY_TITLE_ZONE
  3. Strong patterns: '評等: X', '給予 X 評等', '上修至 X', '維持 X'
  4. Stopwords filter: exclude price targets, EPS values, recommendation language unrelated to rating
  5. Normalize to canonical via RATING_LIST_V22_2 (5 buckets: strong_buy/buy/hold/sell/not_rated)
  6. Opinion field — broker_report is sole truth, no external override

### BAS_12. `rating_cat` (BasicInfo.BrokerOpinion)

- **Type:** `VARCHAR` | **Role:** `rating_canonical` | **Status:** 🔒 OPINION (broker 唯一)
- **Regex layer (0):** _(none)_
- **Synonyms layer (2):** `Rating Category`, `Normalized Rating`
- **Validation method:**
  1. Derived from rating via RATING_LIST_V22_2 inverse map
  2. Lower-case canonical: strong_buy / buy / hold / sell / not_rated
  3. If raw rating contains stopword match, do NOT promote to rating_cat

### BAS_13. `target_price` (BasicInfo.BrokerOpinion)

- **Type:** `DOUBLE` | **Role:** `target_price` | **Status:** 🔒 OPINION (broker 唯一)
- **Regex layer (3):** `TARGET_PRICE_LABEL`, `TARGET_PRICE_VERB`, `TARGET_PRICE_TAIL`
- **Synonyms layer (12):** `目標價`, `目標價格`, `合理價`, `推估合理價`, `目標股價`, `Target Price`, `Price Target`, `TP`, `PT`, `Fair Value`, `fair value`, `target`
- **Validation method:**
  1. Try TARGET_PRICE_LABEL: 目標價/TP/Target Price (capture number with NT$/TWD prefix)
  2. Try TARGET_PRICE_VERB: 給予/上修至/下修至/維持 + 目標價 + 數字 + 元
  3. Try TARGET_PRICE_TAIL: 數字 + 元 + 目標價
  4. STOPWORDS filter: previous/prior/前次/原目標 (exclude PRIOR target)
  5. Multi-occurrence handling: prefer TITLE_ZONE > TOP_ZONE > BODY_TITLE_ZONE
  6. Validate against upside_pct: (target_price / adj_close_T_minus_1 - 1) * 100 should match broker's stated upside ± 0.5pp
  7. Opinion field — broker_report is sole truth, no external override

### BAS_14. `consensus_target_high` (BasicInfo.BrokerOpinion)

- **Type:** `DOUBLE` | **Role:** `consensus_target` | **Status:** 🔒 OPINION (broker 唯一)
- **Regex layer (0):** _(none)_
- **Synonyms layer (6):** `consensus`, `共識`, `市場共識`, `Consensus`, `Street`, `Mean Target`
- **Validation method:**
  1. From yfinance.info.targetHighPrice / targetLowPrice / targetMeanPrice / targetMedianPrice
  2. Cross-validate target_price (broker) within [low, high]; warn if outside
  3. Opinion-aggregate field — derived from third-party but reflects broker consensus

### BAS_15. `consensus_target_low` (BasicInfo.BrokerOpinion)

- **Type:** `DOUBLE` | **Role:** `consensus_target` | **Status:** 🔒 OPINION (broker 唯一)
- **Regex layer (0):** _(none)_
- **Synonyms layer (6):** `consensus`, `共識`, `市場共識`, `Consensus`, `Street`, `Mean Target`
- **Validation method:**
  1. From yfinance.info.targetHighPrice / targetLowPrice / targetMeanPrice / targetMedianPrice
  2. Cross-validate target_price (broker) within [low, high]; warn if outside
  3. Opinion-aggregate field — derived from third-party but reflects broker consensus

### BAS_16. `consensus_target_mean` (BasicInfo.BrokerOpinion)

- **Type:** `DOUBLE` | **Role:** `consensus_target` | **Status:** 🔒 OPINION (broker 唯一)
- **Regex layer (0):** _(none)_
- **Synonyms layer (6):** `consensus`, `共識`, `市場共識`, `Consensus`, `Street`, `Mean Target`
- **Validation method:**
  1. From yfinance.info.targetHighPrice / targetLowPrice / targetMeanPrice / targetMedianPrice
  2. Cross-validate target_price (broker) within [low, high]; warn if outside
  3. Opinion-aggregate field — derived from third-party but reflects broker consensus

### BAS_17. `consensus_target_median` (BasicInfo.BrokerOpinion)

- **Type:** `DOUBLE` | **Role:** `consensus_target` | **Status:** 🔒 OPINION (broker 唯一)
- **Regex layer (0):** _(none)_
- **Synonyms layer (6):** `consensus`, `共識`, `市場共識`, `Consensus`, `Street`, `Mean Target`
- **Validation method:**
  1. From yfinance.info.targetHighPrice / targetLowPrice / targetMeanPrice / targetMedianPrice
  2. Cross-validate target_price (broker) within [low, high]; warn if outside
  3. Opinion-aggregate field — derived from third-party but reflects broker consensus

### BAS_18. `consensus_rating` (BasicInfo.BrokerOpinion)

- **Type:** `VARCHAR` | **Role:** `consensus_rating` | **Status:** 🔒 OPINION (broker 唯一)
- **Regex layer (1):** `BROKER_RATING`
- **Synonyms layer (2):** `consensus rating`, `市場共識評等`
- **Validation method:**
  1. From yfinance.info.recommendationKey
  2. Normalize via RATING_LIST_V22_2

### BAS_19. `consensus_rating_mean` (BasicInfo.BrokerOpinion)

- **Type:** `DOUBLE` | **Role:** `consensus_rating_mean` | **Status:** 🔒 OPINION (broker 唯一)
- **Regex layer (0):** _(none)_
- **Synonyms layer (1):** `mean recommendation score`
- **Validation method:**
  1. From yfinance.info.recommendationMean (1.0=strongBuy ... 5.0=sell)

### BAS_20. `analyst_count` (BasicInfo.BrokerOpinion)

- **Type:** `INTEGER` | **Role:** `analyst_count` | **Status:** 🔒 OPINION (broker 唯一)
- **Regex layer (0):** _(none)_
- **Synonyms layer (3):** `analyst count`, `broker count`, `覆蓋分析師數`
- **Validation method:**
  1. From yfinance.info.numberOfAnalystOpinions and individual category counts
  2. Sum check: strong_buy + buy + hold + sell + strong_sell == analyst_count

### BAS_21. `analyst_strong_buy` (BasicInfo.BrokerOpinion)

- **Type:** `INTEGER` | **Role:** `analyst_count_detail` | **Status:** 🔒 OPINION (broker 唯一)
- **Regex layer (0):** _(none)_
- **Synonyms layer (3):** `analyst count`, `broker count`, `覆蓋分析師數`
- **Validation method:**
  1. From yfinance.info.numberOfAnalystOpinions and individual category counts
  2. Sum check: strong_buy + buy + hold + sell + strong_sell == analyst_count

### BAS_22. `analyst_buy` (BasicInfo.BrokerOpinion)

- **Type:** `INTEGER` | **Role:** `analyst_count_detail` | **Status:** 🔒 OPINION (broker 唯一)
- **Regex layer (0):** _(none)_
- **Synonyms layer (3):** `analyst count`, `broker count`, `覆蓋分析師數`
- **Validation method:**
  1. From yfinance.info.numberOfAnalystOpinions and individual category counts
  2. Sum check: strong_buy + buy + hold + sell + strong_sell == analyst_count

### BAS_23. `analyst_hold` (BasicInfo.BrokerOpinion)

- **Type:** `INTEGER` | **Role:** `analyst_count_detail` | **Status:** 🔒 OPINION (broker 唯一)
- **Regex layer (0):** _(none)_
- **Synonyms layer (3):** `analyst count`, `broker count`, `覆蓋分析師數`
- **Validation method:**
  1. From yfinance.info.numberOfAnalystOpinions and individual category counts
  2. Sum check: strong_buy + buy + hold + sell + strong_sell == analyst_count

### BAS_24. `analyst_sell` (BasicInfo.BrokerOpinion)

- **Type:** `INTEGER` | **Role:** `analyst_count_detail` | **Status:** 🔒 OPINION (broker 唯一)
- **Regex layer (0):** _(none)_
- **Synonyms layer (3):** `analyst count`, `broker count`, `覆蓋分析師數`
- **Validation method:**
  1. From yfinance.info.numberOfAnalystOpinions and individual category counts
  2. Sum check: strong_buy + buy + hold + sell + strong_sell == analyst_count

### BAS_25. `analyst_strong_sell` (BasicInfo.BrokerOpinion)

- **Type:** `INTEGER` | **Role:** `analyst_count_detail` | **Status:** 🔒 OPINION (broker 唯一)
- **Regex layer (0):** _(none)_
- **Synonyms layer (3):** `analyst count`, `broker count`, `覆蓋分析師數`
- **Validation method:**
  1. From yfinance.info.numberOfAnalystOpinions and individual category counts
  2. Sum check: strong_buy + buy + hold + sell + strong_sell == analyst_count

### BAS_26. `adj_close` (BasicInfo.Verifiable)

- **Type:** `DOUBLE` | **Role:** `adjusted_close` | **Status:** 🟢 VERIFIABLE
- **Regex layer (2):** `NUMBER_WITH_COMMAS`, `PARENS_NEGATIVE`
- **Synonyms layer (6):** `收盤價`, `ADJ Close`, `Adjusted Close`, `現價`, `Current Price`, `股價`
- **Validation method:**
  1. **DUAL-TRACK**:
     a. T-day (latest): Pull current trading day ADJ Close from VDF DuckDB
     b. T-1 verification: Pull report-date-minus-1-trading-day ADJ Close to verify broker_report stated price
  2. SSoT P1: vdf_duckdb.prices.adj_close[date]
  3. SSoT P2: official_twse adj_close
  4. SSoT P3: yfinance.history Adj Close
  5. Must use post-ex-dividend/post-split adjusted close, NOT raw close
  6. Tolerance for verification: 0.1% green / 1.0% yellow / >1.0% red flag

### BAS_27. `adj_close_date` (BasicInfo.Verifiable)

- **Type:** `VARCHAR` | **Role:** `adjusted_close_date` | **Status:** 🟢 VERIFIABLE
- **Regex layer (2):** `DATE_ISO_AD`, `DATE_SLASH_AD`
- **Synonyms layer (3):** `Price Date`, `As-of Date`, `Quote Date`
- **Validation method:**
  1. Should equal T-1 trading day (Monday-Friday, exclude TW holidays)
  2. Use VDF trading_calendar to find prior trading day
  3. Tolerance: ±1 day

### BAS_28. `upside_pct` (BasicInfo.Derived)

- **Type:** `DOUBLE` | **Role:** `derived_upside` | **Status:** 🧮 DERIVED
- **Regex layer (1):** `UPSIDE_PCT`
- **Synonyms layer (4):** `上漲空間`, `上漲幅度`, `Upside`, `Potential Return`
- **Validation method:**
  1. Computed: (target_price / adj_close - 1) * 100
  2. DUAL track:
     a. upside_at_report = (target_price / adj_close_T_minus_1 - 1) * 100  [for verification]
     b. upside_realtime = (target_price / adj_close_today - 1) * 100  [for latest decision]
  3. Verify broker_report stated upside matches upside_at_report ± 0.5pp

### BAS_29. `upside_source` (BasicInfo.Derived)

- **Type:** `VARCHAR` | **Role:** `derived_upside_source` | **Status:** 🧮 DERIVED
- **Regex layer (0):** _(none)_
- **Synonyms layer (2):** `upside source`, `計算基準`
- **Validation method:**
  1. Fixed enum: 'report_date_close' | 'latest_close' | 'consensus_mean'
  2. For verification track: 'report_date_close' (T-1 ADJ Close)
  3. For realtime track: 'latest_close' (T-day ADJ Close)

### BAS_30. `summary` (BasicInfo.BrokerOpinion)

- **Type:** `VARCHAR` | **Role:** `summary` | **Status:** 🔒 OPINION (broker 唯一)
- **Regex layer (0):** _(none)_
- **Synonyms layer (4):** `摘要`, `Summary`, `Highlights`, `重點摘要`
- **Validation method:**
  1. From Summarizer v5 six-point output (concatenated)
  2. Opinion-aggregate field — preserved as-is, no external override

## G. FinancialData 76 欄位三層驗證明細

### G.1. Income Statement (9 欄位)

| UID | Official EN | Unit | 主要中文同義字 | 主要英文同義字 |
|---|---|---|---|---|
| VRN_FIN_0001 | **Revenue** | mn TWD | `收入`, `營收`, `營業收入`, `銷貨收入` | `sales`, `Revenue`, `revenue`, `net sales`… |
| VRN_FIN_0002 | **Gross Profit** | mn TWD | `毛利`, `營業毛利` | `Gross Profit`, `gross profit` |
| VRN_FIN_0003 | **Operating Income** | mn TWD | `營業利益`, `營業淨利`, `營業收入淨額` | `ebit`, `Operating Income`, `operating income`, `operating profit` |
| VRN_FIN_0004 | **Operating Expense** | mn TWD | `營業費用` | `opex`, `sg&a`, `Operating Expense`, `operating expense`… |
| VRN_FIN_0005 | **Pretax Income** | mn TWD | `稅前利益`, `稅前淨利`, `稅前純益` | `Pretax Income`, `pretax income`, `income before tax` |
| VRN_FIN_0006 | **Net Income** | mn TWD | `純益`, `本期淨利`, `稅後淨利` | `pat`, `Net Income`, `net income`, `profit after tax` |
| VRN_FIN_0008 | **EBITDA** | mn TWD | `息稅折舊攤銷前盈餘` | `EBITDA`, `ebitda` |
| VRN_FIN_0009 | **Depreciation And Amortization** | mn TWD | `折舊及攤銷`, `折舊及攤提`, `折舊攤銷` | `d&a`, `Depreciation And Amortization`, `depreciation and amortization`, `D&A` |
| VRN_FIN_0068 🆕 | **Profit Before Tax** | mn TWD | `稅前純益`, `稅前淨利`, `稅前利益` |  |

### G.2. Balance Sheet (25 欄位)

| UID | Official EN | Unit | 主要中文同義字 | 主要英文同義字 |
|---|---|---|---|---|
| VRN_FIN_0010 | **Cash And Cash Equivalents** | mn TWD | `現金約當現金`, `現金及約當現金` | `cash`, `Cash And Cash Equivalents`, `cash and cash equivalents` |
| VRN_FIN_0011 | **Accounts Receivable** | mn TWD | `應收帳款`, `應收帳款及票據`, `應收帳款與票據` | `ar`, `Accounts Receivable`, `accounts receivable` |
| VRN_FIN_0012 | **Inventory** | mn TWD | `存貨` | `Inventory`, `inventory`, `inventories` |
| VRN_FIN_0013 | **Current Assets** | mn TWD | `流動資產`, `流動資產合計` | `Current Assets`, `current assets`, `total current assets` |
| VRN_FIN_0014 | **Other Current Assets** | mn TWD | `其他流動資產`, `其它流動資產` | `Other Current Assets`, `other current assets` |
| VRN_FIN_0015 | **Property Plant And Equipment** | mn TWD | `不動產、廠房設備`, `不動產廠房及設備`, `不動產、廠房及設備`, `固定資產`… | `ppe`, `fixed assets`, `Property Plant And Equipment`, `property plant and equipment`… |
| VRN_FIN_0016 | **Long Term Investments** | mn TWD | `長期投資`, `長期投資合計`, `採用權益法之投資`, `長期股權投資` | `Long Term Investments`, `long term investments`, `long-term investments` |
| VRN_FIN_0017 | **Other Non Current Assets** | mn TWD | `其他非流動資產`, `其它非流動資產` | `Other Non Current Assets`, `other non current assets` |
| VRN_FIN_0018 | **Total Assets** | mn TWD | `總資產`, `資產總計`, `資產總額`, `資產合計` | `Total Assets`, `total assets` |
| VRN_FIN_0019 | **Accounts Payable** | mn TWD | `應付帳款`, `應付帳款及票據` | `ap`, `Accounts Payable`, `accounts payable` |
| VRN_FIN_0020 | **Short Term Debt** | mn TWD | `短期借款`, `短期負債` | `Short Term Debt`, `short term debt`, `short-term debt` |
| VRN_FIN_0021 | **Current Liabilities** | mn TWD | `流動負債`, `流動負債合計` | `Current Liabilities`, `current liabilities`, `total current liabilities` |
| VRN_FIN_0022 | **Other Current Liabilities** | mn TWD | `其他流動負債` | `Other Current Liabilities`, `other current liabilities` |
| VRN_FIN_0023 | **Non Current Liabilities** | mn TWD | `非流動負債`, `其他非流動負債`, `長期負債合計`, `非流動負債合計`… | `long term liabilities`, `Non Current Liabilities`, `non current liabilities` |
| VRN_FIN_0024 | **Total Liabilities** | mn TWD | `總負債`, `負債總計`, `負債總額`, `負債總額 分配後` | `Total Liabilities`, `total liabilities` |
| VRN_FIN_0025 | **Common Stock** | mn TWD | `股本`, `普通股股本` | `Common Stock`, `common stock`, `capital stock` |
| VRN_FIN_0026 | **Retained Earnings** | mn TWD | `保留盈餘` | `Retained Earnings`, `retained earnings` |
| VRN_FIN_0027 | **Parent Equity** | mn TWD | `母公司業主權益`, `歸屬母公司業主權益` | `Parent Equity`, `parent equity`, `equity attributable to owners of parent` |
| VRN_FIN_0028 | **Total Equity** | mn TWD | `總權益`, `權益總計`, `股東權益`, `權益總額`… | `Total Equity`, `total equity`, `shareholders equity` |
| VRN_FIN_0029 | **Total Liabilities And Equity** | mn TWD | `負債及權益總計`, `負債和權益總計` | `Total Liabilities And Equity`, `total liabilities and equity` |
| VRN_FIN_0063 🆕 | **Short Term Borrowings** | mn TWD | `短期借款`, `短期銀行借款`, `短借`, `一年內到期借款` |  |
| VRN_FIN_0064 🆕 | **Capital Surplus** | mn TWD | `資本公積`, `資本公積合計` |  |
| VRN_FIN_0065 🆕 | **Other Equity** | mn TWD | `其他權益`, `其他權益項目` |  |
| VRN_FIN_0066 🆕 | **Intangible Assets** | mn TWD | `無形資產`, `無形資產合計` |  |
| VRN_FIN_0067 🆕 | **Other Assets** | mn TWD | `其他資產`, `其他非流動資產`, `其它非流動資產` |  |

### G.3. Cash Flow Statement (13 欄位)

| UID | Official EN | Unit | 主要中文同義字 | 主要英文同義字 |
|---|---|---|---|---|
| VRN_FIN_0030 | **Operating Cash Flow** | mn TWD | `營運現金流`, `營業活動現金`, `營業活動現金流量`, `營業活動之淨現金流入出` | `cfo`, `Operating Cash Flow`, `operating cash flow`, `cash flow from operations` |
| VRN_FIN_0031 | **Investing Cash Flow** | mn TWD | `投資活動現金`, `投資活動現金流量`, `長期投資變動` | `cfi`, `Investing Cash Flow`, `investing cash flow`, `cash flow from investing` |
| VRN_FIN_0032 | **Financing Cash Flow** | mn TWD | `籌資活動現金`, `籌資活動現金流量`, `融資活動之淨現金流入出`, `融資活動之淨現金流入(出)`… | `cff`, `Financing Cash Flow`, `financing cash flow`, `cash flow from financing` |
| VRN_FIN_0033 | **Capital Expenditure** | mn TWD | `資本支出`, `資本支出淨額` | `capex`, `Capital Expenditure`, `capital expenditure` |
| VRN_FIN_0034 | **Free Cash Flow** | mn TWD | `自由現金流` | `fcf`, `Free Cash Flow`, `free cash flow` |
| VRN_FIN_0035 | **Net Change In Cash** | mn TWD | `淨現金流量`, `現金淨增加`, `本期現金與約當現金增加數`, `現金增加數` | `Net Change In Cash`, `net change in cash` |
| VRN_FIN_0036 | **Beginning Cash** | mn TWD | `期初現金`, `期初現金與約當現金餘額` | `Beginning Cash`, `beginning cash` |
| VRN_FIN_0037 | **Ending Cash** | mn TWD | `期末現金`, `期末現金與約當現金餘額` | `Ending Cash`, `ending cash` |
| VRN_FIN_0038 | **Working Capital Change** | mn TWD | `營運資金變動` | `Working Capital Change`, `working capital change`, `change in working capital` |
| VRN_FIN_0039 | **Long Term Investment Change** | mn TWD | `長期投資變動` | `Long Term Investment Change`, `long term investment change`, `change in long term investment` |
| VRN_FIN_0040 | **Debt Change** | mn TWD | `長借公司債變動`, `長借/公司債變動` | `Debt Change`, `debt change` |
| VRN_FIN_0041 | **Cash Dividend Paid** | mn TWD | `發放現金股利` | `dividend paid`, `Cash Dividend Paid`, `cash dividend paid` |
| VRN_FIN_0042 | **Cash Capital Increase** | mn TWD | `現金增資` | `Cash Capital Increase`, `cash capital increase` |

### G.4. Ratio Analysis (21 欄位)

| UID | Official EN | Unit | 主要中文同義字 | 主要英文同義字 |
|---|---|---|---|---|
| VRN_FIN_0043 | **Gross Margin** | % | `毛利率` | `gm`, `Gross Margin`, `gross margin` |
| VRN_FIN_0044 | **Operating Margin** | % | `營益率`, `營業利益率` | `opm`, `Operating Margin`, `operating margin` |
| VRN_FIN_0045 | **Net Margin** | % | `淨利率` | `Net Margin`, `net margin` |
| VRN_FIN_0046 | **ROE** | % | `股東權益報酬率` | `ROE`, `roe`, `return on equity` |
| VRN_FIN_0047 | **ROA** | % | `資產報酬率` | `ROA`, `roa`, `return on assets` |
| VRN_FIN_0048 | **Current Ratio** | ratio | `流動比率` | `Current Ratio`, `current ratio` |
| VRN_FIN_0049 | **Debt Ratio** | ratio | `負債比率` | `Debt Ratio`, `debt ratio` |
| VRN_FIN_0050 | **Inventory Turnover** | x | `存貨週轉率` | `Inventory Turnover`, `inventory turnover` |
| VRN_FIN_0051 | **Receivable Turnover** | x | `應收帳款週轉率` | `Receivable Turnover`, `receivable turnover` |
| VRN_FIN_0052 | **Asset Turnover** | x | `資產週轉率` | `Asset Turnover`, `asset turnover` |
| VRN_FIN_0053 | **P/E** | x | `本益比` | `P/E`, `p/e`, `per`, `pe ratio` |
| VRN_FIN_0054 | **P/B** | x | `股價淨值比` | `P/B`, `p/b`, `pbr`, `pb ratio` |
| VRN_FIN_0069 🆕 | **Debt To Asset Ratio** | % | `負債占資產比率`, `負債比率`, `負債資產比` |  |
| VRN_FIN_0070 🆕 | **Quick Ratio** | % | `速動比率`, `速動比率%` |  |
| VRN_FIN_0071 🆕 | **Interest Coverage Ratio** | x | `利息保障倍數` |  |
| VRN_FIN_0072 🆕 | **Accounts Receivable Turnover** | x | `應收款項週轉率`, `應收帳款週轉率` |  |
| VRN_FIN_0073 🆕 | **Days Sales Outstanding** | days | `平均收現日數`, `應收帳款收現日數` |  |
| VRN_FIN_0074 🆕 | **Accounts Payable Turnover** | x | `應付款項週轉率`, `應付帳款週轉率` |  |
| VRN_FIN_0075 🆕 | **Days Inventory Outstanding** | days | `平均銷貨日數`, `存貨銷售日數` |  |
| VRN_FIN_0076 🆕 | **Fixed Asset Turnover** | x | `不動產廠房及設備週轉率`, `不動產、廠房及設備週轉率`, `固定資產週轉率` |  |
| VRN_FIN_0077 🆕 | **Total Asset Turnover** | x | `總資產週轉率` |  |

### G.5. Per Share Analysis (4 欄位)

| UID | Official EN | Unit | 主要中文同義字 | 主要英文同義字 |
|---|---|---|---|---|
| VRN_FIN_0055 | **EPS** | TWD | `每股盈餘` | `EPS`, `eps` |
| VRN_FIN_0056 | **BVPS** | TWD | `每股淨值` | `BVPS`, `bvps`, `book value per share` |
| VRN_FIN_0057 | **CFPS** | TWD | `每股現金流` | `CFPS`, `cfps`, `cash flow per share` |
| VRN_FIN_0058 | **DPS** | TWD | `每股股利` | `DPS`, `dps`, `dividend per share` |

### G.6. Growth Ratio (4 欄位)

| UID | Official EN | Unit | 主要中文同義字 | 主要英文同義字 |
|---|---|---|---|---|
| VRN_FIN_0059 | **Sales YoY** | % | `營收年增率` | `Sales YoY`, `sales yoy`, `revenue yoy` |
| VRN_FIN_0060 | **EPS YoY** | % | `eps年增率` | `EPS YoY`, `eps yoy` |
| VRN_FIN_0061 | **Sales QoQ** | % | `營收季增率` | `Sales QoQ`, `sales qoq`, `revenue qoq` |
| VRN_FIN_0062 | **EPS QoQ** | % | `eps季增率` | `EPS QoQ`, `eps qoq` |

### G.7. FinancialData 共用驗證方法

以下 6+ 條驗證法套用於 **所有 76 個 FinancialData 欄位**:

1. Normalize via VRN_FINANCIAL_ACCOUNT_SSOT alias_index (def_get_vrn_financial_account_alias_index)
2. Strip parens-negative, thousand separators, FINANCE_EMPTY placeholders
3. Apply unit normalization (mn TWD / TWD / % / x / ratio / days)
4. Quarantine routing (def_classify_financial_row_quality_v0100):
   - Non-financial header row → QUARANTINE
   - Missing-ticker segment row → QUARANTINE
   - Merged multi-account row → REQUIRES_TABLE_GEOMETRY_SPLIT (YELLOW)
5. Year-tag handling:
   - ACTUAL year cells (N-2/N-1): cross-validate against P1-P4 truth sources
   - FORECAST year cells (N/N+1/N+2): broker_report is sole source (opinion), preserved
6. Validation checks (HistoricalValidationPolicy v0100):
   - historical_range_check: must use historical_only truth source
   - add_sub_check: report_source NOT allowed as truth
   - division_check: Stage A (0.5x-3.0x scale band), Stage B (1%/5%/10% tolerance)
7. Add-sub check applicable: e.g. Revenue - COGS = Gross Profit; verify ≤1% tolerance

特定欄位另有額外驗證 (見每欄位 JSON):
- **Diluted EPS** — TIFRS dilution check (CB/ESOP/RSU), Basic vs Diluted ≤1% 差異
- **Revenue / Net Income / Operating Income** — Add-sub validation
- **ROE / ROA** — Division validation, Stage A 0.5-3.0x scale, Stage B 1%/5%/10%
- **P/E / P/B** — Dual track (T-1 verify + T-day realtime), Division check

## H. Append-Only 整合宣告

本 v01.02 完整保留 v01.01 的 106 個欄位 (BasicInfo 30 + FinancialData 76),**只增加** 三層驗證細節與全域字典:

- 新增 `validation_layers` 區塊到每一個欄位 (regex / synonyms / validation_method)
- 新增 `all_regex` 全域字典 (40 patterns)
- 新增 `rating_list` / `target_price_dict` / `email_domain_to_broker` / `valuation_dual_track` / `eps_policy`
- 整合 `VRN_BROKER_LIST_v02` (32 brokers, 從 v01 20 家擴增)
- 整合 `VRN_VALUATION_DICTIONARY_V0595` (22 methods)
- 對齊 `HistoricalValidationPolicy_v0100` 治理 (broker_report ≠ truth)
