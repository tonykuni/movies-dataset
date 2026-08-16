# VIA v0140B Windows Handle HOLD Evidence — Sanitized

This record preserves the safety-relevant result of a real Windows execution while removing the user name, source absolute path, run-root absolute path, and lane-root absolute paths.

## Decision

- Generated UTC: `2026-08-16T17:47:07.952244+00:00`
- Final gate: `VIA_V0140B_WINDOWS_FILE_HANDLE_ACQUISITION_SANDBOX_VALIDATION_HOLD_IMPLICIT_HYDRATION_RISK_NO_SYSTEM_MUTATION`
- Platform: `Windows`
- Candidate: existing regular CSV file; sanitized path `<USERPROFILE>\OneDrive\<REDACTED>\Standardized_Prices.csv`
- Candidate bytes: `170858`
- Windows attributes: `ARCHIVE`, `RECALL_ON_DATA_ACCESS`
- Windows attribute value: `4194336`
- Reparse tag: `0`
- Blocking recall flags: `RECALL_ON_DATA_ACCESS`
- Implicit hydration risk: `true`
- Content read authorized: `false`

## Six-engine result

| Engine | Strategy | Status | Outcome | Open attempts | Open successes | Bytes read |
|---|---|---|---|---:|---:|---:|
| H01 | OneDrive attribute recall preflight | PASS | `PREFLIGHT_BLOCKED_IMPLICIT_HYDRATION_RISK` | 0 | 0 | 0 |
| H02 | Python pathlib binary open | PASS | `SKIPPED_IMPLICIT_HYDRATION_OR_PREFLIGHT_RISK` | 0 | 0 | 0 |
| H03 | Python os.open binary | PASS | `SKIPPED_IMPLICIT_HYDRATION_OR_PREFLIGHT_RISK` | 0 | 0 | 0 |
| H04 | Win32 CreateFileW exact path | PASS | `SKIPPED_IMPLICIT_HYDRATION_OR_PREFLIGHT_RISK` | 0 | 0 | 0 |
| H05 | Win32 CreateFileW extended path | PASS | `SKIPPED_IMPLICIT_HYDRATION_OR_PREFLIGHT_RISK` | 0 | 0 | 0 |
| H06 | .NET FileStream exact path | PASS | `SKIPPED_IMPLICIT_HYDRATION_OR_PREFLIGHT_RISK` | 0 | 0 | 0 |

## Zero-effect boundary

- Source hash/write/copy/content artifact: `0/0/0/0`
- Network requests: `0`
- Canonical runtime executions: `0`
- Registry writes: `0`
- Existing mutations: `0`
- Patch applications: `0`
- Candidate promotions: `0`
- Hydra violations: `0`

## Interpretation

The HOLD is the intended fail-closed outcome, not an engine crash. H01 found `RECALL_ON_DATA_ACCESS` before any content handle was opened. H02 through H06 therefore remained unattempted, preventing a nominal read from implicitly changing the OneDrive hydration state.

