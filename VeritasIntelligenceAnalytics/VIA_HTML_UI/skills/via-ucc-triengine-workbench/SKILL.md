---
name: via-ucc-triengine-workbench
description: Build, extend, test, and document a local-only VIA Universal Control Console with SYNCHRONIZER, industry module templates, Plotly/Seaborn-inspired light dashboards, and E1/E2/E3 TriEngine handoffs. Use for VIA HTML UI work, serverless localStorage/BroadcastChannel synchronization, custom industry management modules, CSV/Excel SpreadsheetML analytics export, or repeatable VIA specification-to-standardization workflows.
---

# VIA UCC / TriEngine Workbench

Use this skill to keep VIA work **local-only, one-click usable, schema-stable, and testable**.

## Core workflow

1. Inspect the existing HTML, current v2 state schema, attached specifications, and any engine scripts before editing.
2. Preserve the standalone constraint: do not introduce a server, fetch, WebSocket, CDN, or remote package. Use inline HTML/CSS/JavaScript, `localStorage`, `BroadcastChannel`, Blob downloads, and SpreadsheetML `.xls`.
3. Model the system as a left control surface plus a right result surface:
   - LP-01 Input Matrix
   - LP-02 Auto-Run
   - LP-03 Subsystem Links
   - LP-04 Live Log Stream
   - TAB-1 input validation / deduplication / auto-test / detailed summary
   - TAB-2+ category result pages
   - final tab for engines, parameters, decision path, and SSOT snapshot
4. For the current VIA pair, keep state compatible with `version: 2` and preserve unknown fields when the UI bridge normalizes state. Read [state-and-module-schema.md](references/state-and-module-schema.md) before adding fields.
5. Build or extend an industry profile through the SYNCHRONIZER, choosing **replace** or **merge** explicitly. Keep system modules intact when replacing custom modules.
6. Keep chart definitions and history rows in the same state envelope as modules. Use the built-in pivot configuration to generate `PivotSummary` during Excel export.
7. Use the light dashboard palette in [palette.md](references/palette.md). Keep the left sidebar light, use compact typography, equal-height panels where requested, and expose layout controls rather than hard-coding one viewport.
8. Run browser UAT for: initial render, responsive layout, search/filter, settings drawer, connection modal, module template application, custom chart creation, pivot selection, state persistence, and Excel export.
9. Generate industry-specific validation assets from VSX IR when a module profile changes:
   ```bash
   python /home/ubuntu/skills/via-ucc-triengine-workbench/scripts/generate_module_validation.py \
     --ir <vsx-dir>/via_spec_ir.json --html <target.html> \
     --profile <industry-profile.json> --industry <profile-key> --out <validation-dir>
   ```
   Run the generated Python validator in CI and use the generated browser script for `file://` smoke testing.
10. Run the bundled validator against any exported JSON bundle before delivery:
   ```bash
   python /home/ubuntu/skills/via-ucc-triengine-workbench/scripts/validate_via_bundle.py <state-or-template.json>
   ```
11. Integrate the complete quality gate with [ci-cd-integration.md](references/ci-cd-integration.md) or run it locally:
    ```bash
    python /home/ubuntu/skills/via-ucc-triengine-workbench/scripts/run_via_ci.py \
      --extractor <via_spec_extractor.py> --hub <via_triengine_hub.py> \
      --html <target.html> --profile <industry-profile.json> \
      --industry <profile-key> --source <inputs...> --out artifacts/via-ci --root .
    ```
12. If engine files are present, follow [tri-engine-handoff.md](references/tri-engine-handoff.md) for E1 → E2 → E3 routing, mount validation, and append-only logs. Do not install or execute untrusted source files merely to inspect them.
13. If a Python data-app companion is requested, keep it optional and isolated under a companion/reference path. Streamlit, Mermaid, Graphviz, and Agraph must not become runtime dependencies of the canonical standalone HTML files; document prepared offline dependencies and provide fallback text/data views when optional packages are absent.

## Custom industry module recipe

1. Define a stable module ID, display name, type, note, enabled flag, pinned flag, and order.
2. Define chart IDs separately from module IDs. Use `line`, `bar`, `area`, or `kpi`; point each chart at a metric key and grouping field.
3. Define history rows with `date,moduleId,metric,value,category`. Keep values numeric and dates sortable.
4. Define a pivot as `rowField`, `columnField`, `valueField`, and `aggregation` (`sum`, `average`, `min`, or `max`).
5. Add the profile to the SYNCHRONIZER template library and render a summary showing module, chart, and history counts.
6. Export JSON for a portable template; export CSV for modules, charts, or history; export SpreadsheetML `.xls` for the full workbook.
7. Re-open the central UI and verify that custom modules appear in navigation and that analytics fields survive the UI bridge.

## Safety and delivery rules

- Treat `file://` as a first-class target; do not require an HTTP server.
- Preserve user data on merge and preserve system modules on replace.
- Escape XML and CSV cells before export.
- Keep test data out of the delivered browser state; clear localStorage after UAT.
- Prefer deterministic validators and browser console assertions over visual guesswork.
- Deliver the updated standalone HTML files and the validated `SKILL.md` path.

## References

- State and module fields: [state-and-module-schema.md](references/state-and-module-schema.md)
- E1/E2/E3 routing and mounts: [tri-engine-handoff.md](references/tri-engine-handoff.md)
- VSX-generated validation and CI/CD integration: [ci-cd-integration.md](references/ci-cd-integration.md)
- Light Plotly/Seaborn palette: [palette.md](references/palette.md)
- Starter industry profiles: [industry-profile.json](templates/industry-profile.json)
- Optional Python companion boundary: `docs/references/streamlit_companion/README.md` in the standardized template
