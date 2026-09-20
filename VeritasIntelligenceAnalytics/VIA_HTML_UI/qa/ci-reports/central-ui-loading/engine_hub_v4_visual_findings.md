# VIA Engine Hub v4 visual UAT

## Desktop 1440 × 1000

The investment workspace now exposes a compact chart-mode control row: line, area, and bars. The chart header explicitly identifies the local `Plotly light · Seaborn semantic` engine. The default line mode keeps the existing dense research layout, while the new point layer adds visible semantic coral points and preserves the light blue Plotly line. Watchlist, risk lens, topology, decision panel, and fixed footer remain aligned.

## Mobile 390 × 844

The investment controls wrap into two short rows without horizontal overflow. Watchlist remains readable, the chart stacks beneath it, and the risk lens follows below. The line chart remains legible at the narrow width; chart modes remain available as compact buttons. No external chart runtime or server is introduced.

## Engine Hub

The UI exposes `window.VIA_ENGINE_HUB` with five local-only engines: `layout`, `visualization`, `interaction`, `state`, and `addon`. Visualization state supports range (`1D`, `1W`, `1M`, `3M`) and mode (`line`, `area`, `bars`); pointer movement updates a crosshair and tooltip.
