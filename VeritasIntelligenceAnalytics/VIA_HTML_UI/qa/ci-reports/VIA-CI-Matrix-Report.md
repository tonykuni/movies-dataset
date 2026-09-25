# VIA Complete CI/CD Test Report

- Generated: 2026-09-15T10:22:23
- Overall status: **PASS**
- Runner: `run_via_ci.py`
- Pipeline: VSX E1 → generated module validation → TriEngine Hub selftest/route/pipeline

## Matrix summary

| Industry | Status | Steps | Failed steps |
|---|---|---:|---|
| smart-manufacturing | **PASS** | 6 | — |
| finance-cyber | **PASS** | 6 | — |
| smart-healthcare | **PASS** | 6 | — |
| investment-research | **PASS** | 6 | — |

## VSX extraction metrics

| Metric | Value |
|---|---:|
| Contract | `VIA_SPEC_IR/1.0` |
| Version | `0100` |
| Items | 441 |
| Gaps | 60 |
| UI items | 152 |
| Tokens | 219 |
| Logic items | 5 |
| API items | 39 |

## Industry profiles

| Industry | Modules | Charts | History schema |
|---|---:|---:|---|
| smart-manufacturing · 智慧製造 | 2 | 2 | `date, module_id, metric, value, category` |
| finance-cyber · 金融資安 | 2 | 2 | `date, module_id, metric, value, category` |

## Step-level timings

### smart-manufacturing

| Step | Return code | Duration (s) |
|---|---:|---:|
| 01_vsx_extract | 0 | 0.177 |
| 02_generate_validators | 0 | 0.046 |
| 03_module_validation | 0 | 0.047 |
| 04_hub_selftest | 0 | 2.176 |
| 05_hub_route | 0 | 0.064 |
| 06_hub_pipeline | 0 | 5.864 |

- Generated validator: `validation/validate_smart-manufacturing.py`
- Browser smoke test: `validation/validate_smart-manufacturing.browser.js`
- Validation result: **PASS**

### finance-cyber

| Step | Return code | Duration (s) |
|---|---:|---:|
| 01_vsx_extract | 0 | 0.168 |
| 02_generate_validators | 0 | 0.045 |
| 03_module_validation | 0 | 0.045 |
| 04_hub_selftest | 0 | 1.781 |
| 05_hub_route | 0 | 0.064 |
| 06_hub_pipeline | 0 | 5.632 |

- Generated validator: `validation/validate_finance-cyber.py`
- Browser smoke test: `validation/validate_finance-cyber.browser.js`
- Validation result: **PASS**

### smart-healthcare

| Step | Return code | Duration (s) |
|---|---:|---:|
| 01_vsx_extract | 0 | 0.208 |
| 02_generate_validators | 0 | 0.048 |
| 03_module_validation | 0 | 0.069 |
| 04_hub_selftest | 0 | 1.745 |
| 05_hub_route | 0 | 0.064 |
| 06_hub_pipeline | 0 | 5.675 |

- Generated validator: `validation/validate_smart-healthcare.py`
- Browser smoke test: `validation/validate_smart-healthcare.browser.js`
- Validation result: **PASS**

### investment-research

| Step | Return code | Duration (s) |
|---|---:|---:|
| 01_vsx_extract | 0 | 0.16 |
| 02_generate_validators | 0 | 0.045 |
| 03_module_validation | 0 | 0.043 |
| 04_hub_selftest | 0 | 1.6 |
| 05_hub_route | 0 | 0.066 |
| 06_hub_pipeline | 0 | 5.619 |

- Generated validator: `validation/validate_investment-research.py`
- Browser smoke test: `validation/validate_investment-research.browser.js`
- Validation result: **PASS**

## Browser UAT result

| Check | Result |
|---|---|
| Central UI investment workspace | PASS |
| Watchlist symbols | 6 |
| Market range controls | 1D / 1W / 1M / 3M |
| Market scope filter | TW / US / ETF |
| Search integration | PASS |
| Horizontal overflow at 390px | None |
| Central add-on API | `VIA_ADDON_API 1.0.0` |
| Investment template application | PASS |
| Investment custom modules | 5 |
| Investment charts | 4 |
| Investment history rows | 28 |
| SYNCHRONIZER add-on API | `VIA_SYNCHRONIZER_ADDON_API 1.0.0` |
| Excel filename | `via-synchronizer-analytics.xls` |
| Excel worksheets | 8 |
| Final browser localStorage | Cleared |

## Artifact layout

```text
reports/
├── matrix-summary.json
├── VIA-CI-Matrix-Report.md
├── smart-manufacturing/ci_report.json
├── finance-cyber/ci_report.json
├── smart-healthcare/ci_report.json
├── investment-research/ci_report.json
├── */vsx/via_spec_ir.json
├── */validation/validate_<industry>.py
├── */validation/validate_<industry>.browser.js
├── */hub-pipeline/pipeline_result.json
└── */logs/*.log
```

## Interpretation

All four profiles passed the same deterministic quality gate. The Hub selftest, route, and pipeline stages are non-blocking with respect to optional engine availability; missing engines are recorded in the Hub artifacts rather than hidden. The generated validators are profile-aware and compare both the target HTML and VSX IR so UI regressions and specification regressions are visible in CI.
