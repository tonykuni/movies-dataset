# VIA AzureFlow System Report Review API Reference

## Contents

1. [Inputs](#inputs)
2. [Extracted metrics](#extracted-metrics)
3. [Verdict rules](#verdict-rules)
4. [Evidence and limitations](#evidence-and-limitations)

## Inputs

The review accepts a Markdown system report and resolves a JSON companion by replacing the `.md` suffix with `.json` unless `--json` is supplied. Optional inputs are:

| Input | Purpose |
|---|---|
| `--cases` | Read a tab-separated full-validation matrix. Each row is `case`, `exit_code`, and stdout evidence path. |
| `--validation-report` | Compare the full-validation report's documented version and ZIP checksum with the selected system report or current ZIP. |
| `--plugin-root` | Check current plugin entrypoint existence, size, and SHA-256 against `manifest_inventory`. |
| `--zip` | Check current ZIP existence, size, and SHA-256. |
| `--out-dir` | Write the generated JSON and Markdown review without touching source evidence. |

## Extracted metrics

The script extracts these groups:

| Group | Fields |
|---|---|
| Identity | `schema`, `plugin`, `version`, `mode`, `started_at`, `finished_at`, `status` |
| Manifest | every check, `manifest_summary`, `manifest_inventory`, entrypoint hashes and sizes |
| Inputs | root and ZIP preflight, base URL, checksum file, extracted E2E flag |
| QA | overall status, exit code, inspect record, verify record, validator totals, summary/stdout/stderr paths |
| Scheduling | readiness, Windows runtime availability, runner, registration script, task test, CMD wrapper |
| Activation | status, registered, automatic registration, human review, activation command |
| Safety | source write/delete, code execution, network, localhost-only inspection, command activation, SSOT promotion |
| Cases | total rows, exit-code-zero rows, nonzero rows, per-case evidence path |
| Drift | Markdown/JSON mismatches, validation-version mismatch, ZIP hash mismatch, missing current paths |

## Verdict rules

The top-level `verdict` is deterministic:

1. Return `FAIL` when the JSON companion is missing or invalid, the report status is not `PASS` or `REVIEW_REQUIRED` in a usable state, `qa.status` is not `PASS`, `qa.exit_code` is nonzero for a purported PASS run, manifest failures exist, required evidence is missing, or a prohibited safety flag is true.
2. Return `PASS_WITH_REVIEW` when technical QA is PASS but any review condition exists. Typical conditions are `windows_runtime_available=false`, `registered=false`, `human_review_required=true`, `READY_FOR_WINDOWS_ACTIVATION`, `NOT_MOUNTED_IN_SANDBOX`, or documentation/package drift.
3. Return `PASS` only when technical QA is PASS and no review condition or material discrepancy remains. This is uncommon for a report generated outside the target Windows environment.

`activation.status=READY_FOR_WINDOWS_ACTIVATION` is not activation. `activation.status=ACTIVATED` requires a separate Windows registration result with `registered=true`; the review skill never creates that result.

## Path status semantics

- `EXISTS_FILE`: selected path exists as a file and its size is recorded.
- `EXISTS_DIR`: selected path exists as a directory.
- `MISSING`: selected path was expected in the current environment but is absent.
- `NOT_MOUNTED_OR_UNAVAILABLE`: the report explicitly describes a path as unavailable or the caller did not provide a matching local root.
- `NOT_CHECKED`: no local path was supplied for comparison.

A missing path in a report copied from another host is not automatically a source failure. The review must preserve the environment boundary.

## Safety interpretation

The following values must normally be false: `source_write`, `source_delete`, `automatic_command_activation`, `ssot_promotion`, `network`, and default `code_execution`. `localhost_get_only` may be true for inspect. `human_review_required=true` is a safety control and should be reported as a review condition, not a failure.

## Output schema

The generated JSON uses:

```json
{
  "schema": "VIA_AZUREFLOW_QA_SYSTEM_REVIEW/1.0",
  "source": {"markdown": "...", "json": "..."},
  "summary": {"report_status": "PASS", "qa_status": "PASS", "manifest": {"total": 7, "passed": 7, "failed": 0}},
  "metrics": {},
  "cases": {"total": 0, "zero_exit": 0, "nonzero_exit": 0, "items": []},
  "path_checks": [],
  "comparisons": [],
  "warnings": [],
  "issues": [],
  "verdict": "PASS_WITH_REVIEW"
}
```

The script may add fields without breaking consumers. Treat `issues` as blocking findings and `warnings` as human-review findings.
