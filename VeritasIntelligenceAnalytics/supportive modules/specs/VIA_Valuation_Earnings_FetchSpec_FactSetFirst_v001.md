# VIA｜估值·盈餘·總經 抓取規格（FactSet-first）v001

Generated: 2026-07-05
工作流（你指定的順序）：**Stage 1 先抓 FactSet 新聞 → Stage 2 再抓每月值**
證據：官方硬數據=**V**（CPI/PPI/NFP/UR/ISM）；forward 估值=**Est**（FactSet 分析師 consensus，**不得標 Confirmed**）
入庫：VIA_TWChip_Warehouse（raw audit、append-only、ledger 去重、provenance 必附）

---

## 0. 兩階段工作流

### Stage 1 — 先抓 FactSet 新聞（指數＋類股 aggregate）
| 來源 | 內容 | 頻率 | 取用 |
|---|---|---|---|
| **FactSet Earnings Insight**（John Butters 週報） | S&P 500 forward 12M P/E（指數＋11 GICS 類股）、bottom-up forward EPS、CY/季 earnings & revenue growth、net margin、EPS surprise、guidance、sector price targets | 週（五） | 免費 PDF：`advantage.factset.com/hubfs/.../EarningsInsight_MMDDYY.pdf`；文章 `insight.factset.com` |
| **FactSet Insight 文章 / StreetAccount** | 類股價格預測、buy/hold/sell、主題（AI/inflation 提及次數） | 週/不定 | `insight.factset.com/topic/earnings` |

**Stage 1 種子值（as of 2026-07-02 FactSet Earnings Insight）**
- S&P 500 forward 12M P/E = **20.4**（>5yr avg、>10yr avg 19.0）
- CY2026 預估 EPS 成長 **24.1%**、營收成長 **10.8%**；Q2 2026 預估 EPS 成長 23.3%
- Trailing 12M P/E ≈ 27.8
- 類股 forward P/E 極值（2026-02 版，**須以最新版更新**）：最高 非核心消費 27.3、最低 金融 15.3
- 分析師預估未來 12 個月 S&P 500 價格 +21%
> ⚠ forward P/E 每週變動（2 月曾 21.6、春季 19.8–21.0、7/2 為 20.4）；每次以最新 Earnings Insight 為準，不寫死。

### Stage 2 — 再抓每月值（macro → 指數量價 → 個股 forward）
順序：FRED/BLS/ISM 月值 → yfinance 指數/個股量價 → FactSet(或替代) 個股 forward estimates。

---

## 1. 總經月值（PMI / CPI / PPI / NFP / 失業率 / 失業期間占比）

| 資料名稱 | 來源 | Series / Endpoint | 頻率 | 證據 | 備註 |
|---|---|---|---|:--:|---|
| PMI 製造/服務 | **ISM** | 官方報告（非 FRED；FRED 已下架） | 月 | V | 含 New Orders/Employment/Prices 細項 |
| CPI 總 / 核心 | FRED/BLS | **CPIAUCSL** / **CPILFESL** | 月 | V | SA |
| PPI 最終需求 | FRED/BLS | **PPIFIS**（最終需求）、**PPIACO**（全商品） | 月 | V | — |
| PPI 核心 | FRED/BLS | 最終需求扣食品能源 **WPSFD49116**（抓前確認 ID） | 月 | V | — |
| 非農新增 | FRED/BLS | **PAYEMS**（+修正） | 月 | V | — |
| 失業率 U-3 | FRED/BLS | **UNRATE** | 月 | V | — |
| 總失業人數 | FRED/BLS | **UNEMPLOY** | 月 | V | 占比分母 |
| 失業期間-各級人數 | FRED/BLS | **UEMPLT5**(<5w) / **UEMP5TO14**(5–14w) / **UEMP15T26**(15–26w) / **UEMP27OV**(27w+) | 月 | V | levels(千人) |
| 失業期間-平均/中位 | FRED/BLS | **UEMPMEAN** / **UEMPMED** | 月 | V | 週數 |
| **失業期間占比** | 計算 | 各級 ÷ UNEMPLOY | 月 | V | BLS Table A-12；占比自算 |

---

## 2. 全球各區指數 量價 ＋ 次產業區間指數

| 區域 | 主要指數（ticker） | 次產業/類股區間指數 來源 |
|---|---|---|
| 美國 | S&P500 `^GSPC`、道瓊 `^DJI`、Nasdaq100 `^NDX`、Russell2000 `^RUT`、費半 `^SOX` | 11 GICS：SPDR 類股 ETF `XLK/XLF/XLE/XLV/XLI/XLY/XLP/XLU/XLB/XLRE/XLC`；或 S&P GICS Industry Group/Industry 指數（FactSet） |
| 歐洲 | STOXX600 `^STOXX`、DAX `^GDAXI`、FTSE100 `^FTSE`、CAC `^FCHI` | STOXX Supersector 指數 |
| 日本 | 日經225 `^N225`、TOPIX（`1306.T` 代理） | TOPIX-17 業種 |
| 韓國 | KOSPI `^KS11` | KRX 業種指數 |
| 中國/港 | 滬深300 `000300.SS`、恒生 `^HSI` | 中證/恒生行業指數（AkShare） |
| 印度 | Nifty50 `^NSEI`、Sensex `^BSESN` | NSE 業種 |
| 台灣 | 加權 `^TWII`、櫃買 `^TWOII` | TWSE/TPEx 類股指數、TSE 產業別 |

- **量價欄位**：OHLCV（yfinance，日）＋ 區域層 forward P/E（FactSet / MSCI）。
- **次產業區間指數走勢**：GICS Industry Group / Industry 層級；FactSet 或 S&P/MSCI；免費替代用類股 ETF 價量近似。

---

## 3. 個股 量價 ＋ Forward PER / EPS / PBR / Book

| 欄位 | 主來源 | 替代/輔助 | 證據 |
|---|---|---|:--:|
| 量價 OHLCV | yfinance（日） | TWSE STOCK_DAY / 各交易所 | V |
| Forward PER | **FactSet consensus** | yfinance `forwardPE`（品質有限） | Est |
| Forward EPS | **FactSet consensus**（bottom-up） | yfinance `forwardEps`、Visible Alpha | Est |
| Forward PBR | **FactSet** | — | Est |
| Book Value / 每股淨值 | FactSet / 財報（MOPS/10-K） | yfinance `bookValue`、`priceToBook`(trailing) | V(財報)/Est(forward) |

> 個股 forward 估值屬**分析師 consensus**，一律標 `Estimated_ThirdParty`，不得入 verified 硬數據、非投資建議。

---

## 4. FactSet 取用現實（先講清楚，免得卡住）

| 層級 | 免費可得？ | 來源 | 備註 |
|---|---|---|---|
| 指數＋11 類股 aggregate forward P/E/EPS/成長/margin | ✅ 免費 | Earnings Insight PDF / insight.factset.com | Stage 1 主力 |
| Forward P/B by sector | △ 不一定每期 | Earnings Insight / FactSet 終端 | 缺期用 MSCI 補 |
| **個股層 forward estimates** | ❌ 付費 | FactSet 終端/API | 替代：LSEG/Refinitiv、Bloomberg、Visible Alpha；粗略用 yfinance |

---

## 5. 頻率 · 證據 · 落地順序

**頻率**：FactSet Earnings Insight＝週（五）；CPI/PPI/NFP/UR/ISM＝月；指數/個股量價＝日。
**證據**：CPI/PPI/NFP/UR/ISM/財報 book＝**V**；所有 forward（P/E、EPS、P/B）＝**Est（FactSet consensus）**。

**落地順序（照你指定）**
1. **Stage 1**：抓最新 FactSet Earnings Insight PDF ＋ insight.factset.com 文章 → 解析指數/11 類股 aggregate forward P/E、EPS、成長、margin、sector price targets。
2. **Stage 2-a**：FRED/BLS/ISM 月值（PMI/CPI/PPI/NFP/UR/失業期間）。
3. **Stage 2-b**：yfinance 全球指數＋類股 ETF＋個股 量價（日）。
4. **Stage 2-c**：FactSet API（或 LSEG/Bloomberg 替代）個股 forward PER/EPS/PBR；Book 取財報。
5. 全程 raw audit ＋ 證據標記；forward 一律 Est、月頻 aggregate 與週頻 FactSet 對帳（as_of 對齊）。

---

## 6. 缺口 / 待確認
1. **PPI 核心 FRED ID**（WPSFD49116）抓取前二次確認。
2. **個股 forward** 需 FactSet 付費層或替代源；免費只到指數/類股 aggregate。
3. Forward P/B by sector 若 Earnings Insight 當期未列 → 用 MSCI/FactSet 終端補。
4. 次產業（GICS Industry 層）區間指數多需 S&P/MSCI/FactSet 授權；免費先用類股 ETF 近似。

---

## 7. 來源（URL）
- FactSet Earnings Insight（最新, forward P/E 20.4）：https://www.factset.com/earningsinsight
- FactSet Earnings Insight PDF 範式：https://advantage.factset.com/hubfs/Website/Resources%20Section/Research%20Desk/Earnings%20Insight/
- FactSet Insight（文章/類股）：https://insight.factset.com/topic/earnings
- FRED（CPI/PPI/PAYEMS/UNRATE/失業期間）：https://fred.stlouisfed.org/
- BLS（PPI/CPI/CES/CPS Table A-12）：https://www.bls.gov/
- ISM（PMI）：https://www.ismworld.org/
