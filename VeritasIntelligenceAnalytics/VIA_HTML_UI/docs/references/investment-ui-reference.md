# Investment UI research notes

## Sources

1. Seaborn official color palette tutorial: https://seaborn.pydata.org/tutorial/color_palettes.html
   - Use qualitative palettes for categories by varying hue.
   - Use sequential palettes for numeric magnitude, primarily varying luminance.
   - Use diverging palettes when data has a meaningful midpoint.
   - Avoid relying on red/green alone because of color-vision deficiencies; pair color with labels, position, icons, or shape.
   - Relevant named families: muted/deep/colorblind qualitative palettes; crest/flare/viridis for numeric series; vlag/icefire for diverging data.

2. TradingView features: https://www.tradingview.com/features/
   - Investment workspaces emphasize charts, alerts, screeners, financials, calendars, options, macro data, and multi-chart analysis.
   - Their chart patterns include candles, bars, volume candles, area, baseline, line, and high-low.
   - Useful layout pattern: compact analysis controls + chart canvas + supporting panels.

3. TradingView watchlists guide: https://www.tradingview.com/support/solutions/43000745825-mastering-the-tradingview-watchlists/
   - Watchlists expose last price, price change, percent change, volume, and extended-hours change.
   - Users organize assets by asset type, market, sector, or custom sections; rows can be reordered and metrics sorted.
   - Symbol details should provide market summary, news, fundamental and technical stats, risk, earnings, dividends, and notes.

## Implementation direction

- Keep the VIA warm light UCC surface and compact typography.
- Add an investment workspace with a watchlist table, market breadth cards, a lightweight SVG price/relative-performance chart, alert state, and timeframe controls.
- Use Seaborn-inspired semantic tokens: blue/teal for neutral or positive analytics, coral for attention, amber for watch, purple for macro/alternative data; do not encode direction with red/green alone.
- Keep demo values explicitly marked as illustrative/static template data; no external market data dependency is introduced.
- Preserve file:// operation, localStorage/BroadcastChannel sync, export functions, and existing HTML-only deployment model.
