# Chart review notes

The CI duration chart clearly shows the investment-research pipeline at 7.53 seconds, below smart healthcare at 7.81 seconds, finance cyber at 7.73 seconds, and smart manufacturing at 8.37 seconds. The Hub pipeline stage dominates elapsed time in every industry.

The browser runtime chart clearly distinguishes the two file:// surfaces. The central UI shows approximately 957 ms DOMContentLoaded, 1000 ms First Contentful Paint, and 958 ms load event. The SYNCHRONIZER shows approximately 31 ms DOMContentLoaded, 108 ms First Contentful Paint, and 64 ms load event. The chart uses a common millisecond scale and labels each bar directly.

The capacity chart correctly highlights 6 watchlist rows, 10 modules, 4 charts, 28 history records, and 2 pivot dimensions. The history record count is the largest capacity value and is visually distinct in yellow.

The responsive chart confirms four tested viewports: Central UI and SYNCHRONIZER at 1440×1000 PC horizontal and 390×844 mobile vertical. All four are marked PASS with no horizontal overflow. The annotation area is crowded near the legend and should be adjusted before final delivery for cleaner presentation.

The regenerated responsive chart uses a separate dimension chart and results table, eliminating annotation overlap. All four rows show PASS and no horizontal overflow.

The regenerated quality-gate heatmap uses an explicit 0–1 color range. All 24 cells render in Seaborn teal, matching the observed all-pass result across four industries and six CI steps.

The generated HTML report renders cleanly at 1440×1000 and 390×844. Desktop shows the compact Muji-like header, hero summary, four metric cards, and first chart panel. Mobile wraps navigation, stacks the hero content, keeps four metric cards in a two-column grid, and preserves readable CJK typography without visible clipping in the first viewport.
