# Section E — 台股個股 Consensus SSOT

_Build: 2026-05-26 · Schema: 1.0.0_

**描述:** 台股個股 YFinance + FactSet 分析師預期共識資料 — 包含目標價、評級分布、未來 5 年 EPS 預估。每天執行一次。

**覆蓋:** 全台上市櫃股票 (~1800-2000 檔)  
**頻率:** Daily (post-market, after 16:00 TWT)  
**DuckDB 表:** `tw_consensus_daily`  
**Primary Key:** ['Date', 'tw_ticker']  
**來源:** YFINANCE + FactSet (via Cnyes 鉅亨網 scrape)

---

## E1 · YFinance Quote API (v7)

**Endpoint:** `https://query1.finance.yahoo.com/v7/finance/quote?symbols={ticker}`

| 欄位 | 單位 | 說明 |
|---|---|---|
| `yf_market_cap` | USD/TWD | 市值 |
| `yf_target_mean_price` | Price | 分析師平均目標價 |
| `yf_target_high_price` | Price | 分析師最高目標價 |
| `yf_target_low_price` | Price | 分析師最低目標價 |
| `yf_recommendation_mean` | Score 1-5 | 綜合評級分數 (1=Strong Buy, 5=Sell) |
| `yf_recommendation_key` | String | 評級分類 (buy/hold/sell/etc) |
| `yf_number_of_analyst_opinions` | Count | 分析師人數 |
| `yf_currency` | ISO | 報價幣別 |

## E2 · YFinance Chart API (v8)

**Endpoint:** `https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=5d&interval=1d`

| 欄位 | 單位 | 說明 |
|---|---|---|
| `yf_adj_close` | Price | 最新除權息還原收盤價 |
| `yf_volume` | Shares | 最新成交量 |

## E3 · FactSet Consensus (via 鉅亨網 scrape)

**Endpoint:** `https://www.cnyes.com/twstock/{ticker}/summary/overview`  
**Method:** Playwright headless scrape

### Block 1 — 目標估值

| 欄位 | 格式 | 說明 |
|---|---|---|
| `factset_updated_at` | YYYY-MM-DD | FactSet 資料更新日 |
| `factset_target_analyst_count` | int | 出具目標價的分析師人數 |
| `factset_target_current_price` | float | 目前股價 |
| `factset_target_low` | float | 最低目標估值 |
| `factset_target_median` | float | 中位數目標估值 |
| `factset_target_high` | float | 最高目標估值 |

### Block 2 — 綜合評級分布

| 欄位 | 格式 | 說明 |
|---|---|---|
| `factset_rating_updated_at` | YYYY-MM-DD |  |
| `factset_rating_analyst_count` | int | 提供評級的分析師人數 |
| `factset_rating_optimistic_count` | int | 積極樂觀(Buy) 人數 |
| `factset_rating_neutral_count` | int | 保持中立(Hold) 人數 |
| `factset_rating_pessimistic_count` | int | 保守悲觀(Sell) 人數 |

### Block 3 — 預估 EPS (5 年 × 3 種估值)

**Years:** actuals = [2024, 2025], estimates = [2026, 2027, 2028]  
**Pattern:** `factset_diluted_eps_{type}_{year}` × 16 fields

| Year | Median | High | Low | Type |
|---|---|---|---|---|
| 2024 | `factset_diluted_eps_median_2024` | `factset_diluted_eps_high_2024` | `factset_diluted_eps_low_2024` | actual |
| 2025 | `factset_diluted_eps_median_2025` | `factset_diluted_eps_high_2025` | `factset_diluted_eps_low_2025` | actual |
| 2026 | `factset_diluted_eps_median_2026` | `factset_diluted_eps_high_2026` | `factset_diluted_eps_low_2026` | estimate |
| 2027 | `factset_diluted_eps_median_2027` | `factset_diluted_eps_high_2027` | `factset_diluted_eps_low_2027` | estimate |
| 2028 | `factset_diluted_eps_median_2028` | `factset_diluted_eps_high_2028` | `factset_diluted_eps_low_2028` | estimate |

## Derived Signals (建議實作)

| Signal | Formula | 意義 |
|---|---|---|
| **target_upside_pct** | `(factset_target_median - factset_target_current_price) / factset_target_current_price * 100` | 中位數目標價隱含漲幅 % |
| **target_dispersion** | `(factset_target_high - factset_target_low) / factset_target_median` | 分析師分歧度 — 高=共識弱 |
| **rating_bull_bear_ratio** | `factset_rating_optimistic_count / max(factset_rating_pessimistic_count, 1)` | Buy/Sell 比，>3 強烈看好 |
| **eps_growth_2yr** | `(factset_diluted_eps_median_2027 - factset_diluted_eps_median_2025) / factset_diluted_eps_median_2025` | 2 年期 EPS 成長預期 |
| **eps_estimate_dispersion** | `(factset_diluted_eps_high_{year} - factset_diluted_eps_low_{year}) / factset_diluted_eps_median_{year}` | EPS 預估分歧度 — 高=高度不確定 |
| **implied_forward_pe** | `factset_target_current_price / factset_diluted_eps_median_2026` | 隱含 forward PE |
| **yf_vs_factset_target_gap** | `(yf_target_mean_price - factset_target_median) / factset_target_median` | 外資 (YF) vs 在地 (FactSet) 共識差異 |

## 輸出格式 (multi-format)

| Format | Filename | Encoding/Engine |
|---|---|---|
| CSV | `Consensus.csv` | utf-8-sig |
| Parquet | `Consensus.parquet` | pyarrow |
| DuckDB | `Consensus.duckdb` | consensus |
| Excel | `Consensus.xlsx` | openpyxl |
| HTML | `Consensus_Report.html` | utf-8-sig |
