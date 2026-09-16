# External and Attachment Notes

## Polars API sources

- https://docs.pola.rs/api/python/stable/reference/expressions/api/polars.rolling_cov.html — `rolling_cov(a, b, window_size, min_samples, ddof)`; current stable documentation states the rolling window includes the current row and prior `window_size - 1` rows, and `min_periods` was renamed to `min_samples` in Polars 1.21.0. Default `ddof=1` is sample covariance.
- https://docs.pola.rs/api/python/stable/reference/expressions/api/polars.Expr.ewm_mean.html — EWM supports `com`, `span`, `half_life`, `alpha`, `adjust`, `min_samples`, and `ignore_nulls`; the same documentation defines the difference between adjusted and recursive EWM and how missing-value weighting works.
- https://docs.pola.rs/api/python/stable/reference/expressions/functions.html — stable expression function index lists `polars.rolling_corr` and `polars.rolling_cov`.
- https://docs.pola.rs/api/python/stable/reference/expressions/api/polars.Expr.rolling_quantile.html — rolling quantile uses trailing windows, supports `min_samples`, and supports interpolation methods including linear.

## Official Taiwan-data source notes

- https://www.twse.com.tw/en/trading/historical/stock-day.html — TWSE historical daily trading value/volume page; page states data is available since 2010-01-04 and can be downloaded as CSV.
- https://www.twse.com.tw/en/trading/day-trading.html — TWSE day-trading page; page states day-trading volume/value figures can be adjusted on T, T+1, and finalized on T+2. This supports point-in-time lag/revision handling for turnover features.
- https://www.twse.com.tw/en/trading/margin/mi-margn.html — TWSE daily margin transaction page; page describes nightly publication and balance revisions.
- https://ranaroussi.github.io/yfinance/ — yfinance documentation; states the package is an open-source research/educational tool, not affiliated with Yahoo, and supports history/download access. It is treated as a price-boundary fallback only, not the official TWSE/TPEX turnover source.

## User attachment SSOT notes

- `VIA_CapitalFlow_Group_Integration_ALL_Manifest_v0100_20260911.md`: attachment state is `STAGING_VALIDATED / PRODUCTION_BLOCKED`; reported synthetic/unit totals are 52/52 pass; production blockers include missing real TWSE+TPEx/VDF connection, unverified PIT membership, missing broker/SBL/passive ETF integration, missing dynamic walk-forward, unavailable Parquet engine, and incomplete end-to-end reconciliation.
- `VIA_TW_Group_CapitalFlow_Integrated_SSOT_v0210.json`: fixed governance includes adjusted price, no zero-fill for missing flow, PIT membership with effective/available timestamps, signal T and execution T+1, FDR, negative controls, costs, and dynamic nested walk-forward parameters frozen until refit. Candidate windows include 20/60/120/240 days and beta 60 days.
- `VIA_Taiwan_Group_Validation_SSOT_v0200.json`: metric families include attention, price-volume, flow, statistical validation, and size/liquidity; includes relative strength, PCA/RMT, CCF/FDR, flow proxies, and effective coverage.
- `VIA_TW_Group_CapitalFlow_Reconciliation_v0100.md`: distinguishes non-day-trade turnover as activity rather than net cash flow; institutional net shares times adjusted close is a NetValueProxy; margin/short balance deltas times adjusted close are credit cash-flow proxies; ETF holdings changes are snapshot-implied flow.
- `VIA_Global_SpotFlow_Quantification_Backtest_Contract_v1_5.md`: recommends four price regimes, volume-price confirmation, RVOL, CLV, A/D, OBV, CMF, relative strength, and walk-forward validation; warns that stage labels are descriptive and not forecasts.

The current MVP uses these notes to implement stable parameter codes, Chinese display text, Benchmark pros/cons/remedies/alternatives, and rolling correlation indicators while preserving the attachment's production-blocked status for data integrations not yet connected.
