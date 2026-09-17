# TradingView / Cross-Market Research Notes

## TradingView indicator definitions

The research agents checked TradingView public support/reference pages and identified the following implementation contracts. SMA is a trailing arithmetic mean; EMA uses alpha=2/(n+1) but seed behavior must be fixed and compared bar by bar. MACD is EMA(12)-EMA(26), signal EMA(9), histogram line-signal. True Range is max(high-low, abs(high-prev_close), abs(low-prev_close)); ATR is normally Wilder/RMA smoothing, not a generic rolling mean. Bollinger Bands are SMA plus/minus k times rolling standard deviation, with ddof and source explicitly fixed. Keltner Channels commonly use EMA basis and ATR bands, with basis length, ATR length, multiplier, and range/ATR style kept separate.

RSI uses Wilder RMA of gains and losses; Stochastic uses raw %K followed by separate smoothing and %D; ROC is 100*(close/close[n]-1); Williams %R is -100*(highest_high-close)/(highest_high-lowest_low); CCI uses typical price and mean absolute deviation, not rolling standard deviation. Volume indicators include session-anchored VWAP, cumulative OBV, MFI from positive/negative typical-price money flow, CMF from money-flow multiplier times volume, and ADL from cumulative money-flow volume. Boundary policies for zero denominators, warm-up, nulls, equal high/low, and source columns must be explicit.

Risk and statistics definitions to freeze include rolling Beta=Cov(asset_ret, benchmark_ret)/Var(benchmark_ret), Sharpe=mean(excess_return)/sample_std(excess_return), Sortino=mean(excess_return)/downside_deviation, Calmar=CAGR/abs(max_drawdown), historical VaR as a loss quantile, and CVaR/ES as the average tail loss beyond VaR. Correlation, covariance ddof, autocorrelation lag/window convention, R-squared intercept policy, skewness convention, and kurtosis raw/excess convention must be explicit. Nulls, small samples, zero variance, zero drawdown, and tail-sample insufficiency must remain visible.

## Repainting and lookahead

TradingView's public documentation emphasizes that an unconfirmed higher-timeframe request can repaint. The conservative non-repainting pattern is to use a confirmed prior higher-timeframe expression (for example expression[1]) together with the documented lookahead pattern, or in a local engine to aggregate completed higher-timeframe bars first and join only after confirmation. The local engine must never use centered rolling, negative shift, future-return labels as features, or unconfirmed higher-timeframe closes.

## Cross-market Taiwan/US alignment

Use timezone-aware timestamps with Asia/Taipei and America/New_York IANA zones, never a fixed UTC offset. The US core session is 09:30-16:00 ET and shifts in UTC during DST; Taiwan has fixed UTC+8. Maintain market-local session date, source timestamp, close_utc, available_at, confirmed_at, and data revision fields. Maintain versioned per-market holiday/session calendars with open, closed, settlement-only, and early-close statuses.

For a conservative daily Taiwan/US comparison, calculate each market's adjusted close line independently and align on the intersection of confirmed trading sessions. For a Taiwan signal, a US close that occurs after the Taiwan close must not be used in the same Taiwan trading date; it becomes available at the next Taiwan session. When using as-of joins, only accept right.close_utc <= left.cutoff/available_at. Non-trading dates are not zero-return observations and must not be blindly forward-filled for analysis.

## Sources

TradingView: https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/ ; https://www.tradingview.com/pine-script-docs/concepts/repainting/ ; https://www.tradingview.com/pine-script-docs/concepts/time/ ; https://www.tradingview.com/pine-script-docs/concepts/sessions/ ; https://www.tradingview.com/pine-script-reference/v6/ ; https://www.tradingview.com/support/solutions/43000502338-relative-strength-index-rsi/ ; https://www.tradingview.com/support/solutions/43000502332-stochastic-stoch/ ; https://www.tradingview.com/support/solutions/43000502343-rate-of-change-roc/ ; https://www.tradingview.com/support/solutions/43000501985-williams-r-r/ ; https://www.tradingview.com/support/solutions/43000502001-commodity-channel-index-cci/ ; https://www.tradingview.com/support/solutions/43000501823-average-true-range-atr/ ; https://www.tradingview.com/support/solutions/43000501840-bollinger-bands-bb/ ; https://www.tradingview.com/support/solutions/43000502266-keltner-channels-kc/ ; https://www.tradingview.com/support/solutions/43000502018-volume-weighted-average-price-vwap/ ; https://www.tradingview.com/support/solutions/43000502593-on-balance-volume-obv/ ; https://www.tradingview.com/support/solutions/43000502348-money-flow-mfi/ ; https://www.tradingview.com/support/solutions/43000501974-chaikin-money-flow-cmf/ ; https://www.tradingview.com/support/solutions/43000501770-accumulation-distribution-adl/.

Official calendars: https://www.twse.com.tw/en/trading/holiday.html ; https://www.nyse.com/markets/hours-calendars ; https://www.nyse.com/publicdocs/Trading_Days.pdf.

The sources support definitions and governance, not a claim that the current local implementation is numerically identical to TradingView until fixture-by-fixture validation is completed.
