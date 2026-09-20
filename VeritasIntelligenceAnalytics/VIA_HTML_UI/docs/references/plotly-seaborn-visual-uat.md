# Plotly Dashboard × Seaborn Light Combo UAT

## Palette

The final light palette uses Plotly blue `#4c78a8` for navigation and analytical chart lines; Plotly teal `#72b7b2` / Seaborn green for positive or healthy states; Plotly coral `#e45756` for actions, alerts, and negative change; Plotly purple `#b279a2` for secondary categorical data; and Plotly yellow `#f2cf5b` for watch or caution states. Backgrounds and panels remain white or cool paper gray so semantic colors are reserved for data meaning.

## Visual results

The central UI renders a light dashboard with blue active navigation, blue relative-performance chart, teal positive indicators, coral primary action, purple secondary instrument badge, and yellow risk/watch accent. The decision panel uses white text on Plotly blue for readable contrast. The SYNCHRONIZER uses the same light paper surface, blue primary action, teal local status, and muted form borders.

Chromium previews were checked at 1440×1000 and 390×844. The mobile central UI remains two-column for KPIs and stacks the investment workspace without horizontal overflow. The SYNCHRONIZER becomes a single-column vertical flow with a compact two-column action matrix.

## Functional UAT

The central UI passed UI Lab opening, 1M range selection, Taiwan market filtering, no-horizontal-overflow, file-only dependency, and add-on availability checks. The SYNCHRONIZER passed the finance-cyber template test with 10 modules, 4 charts, 35 history records, no horizontal overflow, file-only dependency, and add-on API availability. The 35-record count is template-specific; the investment-research template remains 28 records.
