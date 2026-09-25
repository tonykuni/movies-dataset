# VIA Investment UI Cross-Device E2E Report

- Generated: `2026-09-19T18:27:07.546986+00:00`
- HTML: `/home/ubuntu/via_standardized_template_updated/ui/VIA-UI-Standalone-NoServer.html`
- Overall: **PASS**
- Devices: `desktop-1440, tablet-768, mobile-390`

## Summary

| Device | Checks | Passed | Failed | Console/page errors | Screenshot |
|---|---:|---:|---:|---:|---|
| desktop-1440 | 18 | 18 | 0 | 0 | `screens/desktop-1440.png` |
| tablet-768 | 18 | 18 | 0 | 0 | `screens/tablet-768.png` |
| mobile-390 | 18 | 18 | 0 | 0 | `screens/mobile-390.png` |

## Covered journeys

The suite covers initial render, standalone/no-server dependency checks, responsive overflow and investment-card geometry, chart modes, 1D/1W/1M/3M ranges, tooltip/crosshair, market scope filtering, global search, settings drawer, connection modal, UI Lab, navigation, flow pause/resume, add-on registration, state engine snapshot, mobile menu behavior, accessibility landmarks, and browser console/page errors.

## Result details

- **PASS** `desktop-1440` · `initial_render` (17.44 ms)
- **PASS** `desktop-1440` · `static_standalone_contract` (22.14 ms)
- **PASS** `desktop-1440` · `responsive_no_horizontal_overflow` (3.09 ms)
- **PASS** `desktop-1440` · `responsive_investment_geometry` (29.78 ms)
- **PASS** `desktop-1440` · `chart_modes` (231.22 ms)
- **PASS** `desktop-1440` · `chart_ranges` (347.03 ms)
- **PASS** `desktop-1440` · `chart_tooltip_crosshair` (91.07 ms)
- **PASS** `desktop-1440` · `market_scope_filter` (41.39 ms)
- **PASS** `desktop-1440` · `global_search_filter` (47.28 ms)
- **PASS** `desktop-1440` · `settings_drawer` (129.02 ms)
- **PASS** `desktop-1440` · `connection_modal` (95.86 ms)
- **PASS** `desktop-1440` · `ui_lab_toggle` (94.29 ms)
- **PASS** `desktop-1440` · `navigation_and_flow_controls` (118.56 ms)
- **PASS** `desktop-1440` · `addon_registration` (3.58 ms)
- **PASS** `desktop-1440` · `state_engine_snapshot` (1.5 ms)
- **PASS** `desktop-1440` · `mobile_menu_behavior` (0.01 ms)
- **PASS** `desktop-1440` · `accessibility_landmarks` (4.5 ms)
- **PASS** `desktop-1440` · `browser_console_clean` (0.0 ms)
- **PASS** `tablet-768` · `initial_render` (11.57 ms)
- **PASS** `tablet-768` · `static_standalone_contract` (15.24 ms)
- **PASS** `tablet-768` · `responsive_no_horizontal_overflow` (2.46 ms)
- **PASS** `tablet-768` · `responsive_investment_geometry` (25.96 ms)
- **PASS** `tablet-768` · `chart_modes` (211.91 ms)
- **PASS** `tablet-768` · `chart_ranges` (334.08 ms)
- **PASS** `tablet-768` · `chart_tooltip_crosshair` (91.67 ms)
- **PASS** `tablet-768` · `market_scope_filter` (27.88 ms)
- **PASS** `tablet-768` · `global_search_filter` (85.05 ms)
- **PASS** `tablet-768` · `settings_drawer` (225.81 ms)
- **PASS** `tablet-768` · `connection_modal` (92.19 ms)
- **PASS** `tablet-768` · `ui_lab_toggle` (94.01 ms)
- **PASS** `tablet-768` · `navigation_and_flow_controls` (186.07 ms)
- **PASS** `tablet-768` · `addon_registration` (3.46 ms)
- **PASS** `tablet-768` · `state_engine_snapshot` (4.78 ms)
- **PASS** `tablet-768` · `mobile_menu_behavior` (95.35 ms)
- **PASS** `tablet-768` · `accessibility_landmarks` (2.33 ms)
- **PASS** `tablet-768` · `browser_console_clean` (0.0 ms)
- **PASS** `mobile-390` · `initial_render` (10.23 ms)
- **PASS** `mobile-390` · `static_standalone_contract` (14.86 ms)
- **PASS** `mobile-390` · `responsive_no_horizontal_overflow` (2.88 ms)
- **PASS** `mobile-390` · `responsive_investment_geometry` (19.16 ms)
- **PASS** `mobile-390` · `chart_modes` (214.15 ms)
- **PASS** `mobile-390` · `chart_ranges` (334.48 ms)
- **PASS** `mobile-390` · `chart_tooltip_crosshair` (104.44 ms)
- **PASS** `mobile-390` · `market_scope_filter` (31.73 ms)
- **PASS** `mobile-390` · `global_search_filter` (106.93 ms)
- **PASS** `mobile-390` · `settings_drawer` (250.71 ms)
- **PASS** `mobile-390` · `connection_modal` (109.94 ms)
- **PASS** `mobile-390` · `ui_lab_toggle` (91.74 ms)
- **PASS** `mobile-390` · `navigation_and_flow_controls` (183.78 ms)
- **PASS** `mobile-390` · `addon_registration` (3.41 ms)
- **PASS** `mobile-390` · `state_engine_snapshot` (1.59 ms)
- **PASS** `mobile-390` · `mobile_menu_behavior` (78.8 ms)
- **PASS** `mobile-390` · `accessibility_landmarks` (1.55 ms)
- **PASS** `mobile-390` · `browser_console_clean` (0.0 ms)

## Execution

Run locally with:

```bash
python3 run_via_investment_e2e.py --html /path/to/VIA-UI-Standalone-NoServer.html --out-dir e2e-results
```

The runner uses the installed Chromium executable through Playwright and does not start an HTTP server.
