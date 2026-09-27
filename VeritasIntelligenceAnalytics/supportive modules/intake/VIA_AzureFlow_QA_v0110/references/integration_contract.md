# VIA AzureFlow QA Plug-in Integration Contract

## 1. Plug-in identity

| Field | Value |
|---|---|
| Plug-in name | `VIA 天青智流 AzureFlow QA Plug-in` |
| Package skill ID | `via-azureflow-qa-plugin` |
| Primary role | Read-only AzureFlow v8 inspection plus VIA standalone ZIP/E2E verification |
| Runtime | Python 3.10+; PowerShell 7 launcher; standalone `file://` HTML UI |
| Default API | `http://127.0.0.1:8766` |
| Default network policy | disabled except explicit localhost/API GET for `inspect` |
| Default source policy | no source write, no source delete, no code execution |

## 2. Action matrix

| Action | Inputs | Main subroutine | Outputs | Failure boundary |
|---|---|---|---|---|
| `inspect` | AzureFlow API URL, workspace/root, optional runs directory | `inspect_azureflow.py` | `inspect/VIA_AzureFlow_Engine_Job_Inspection.md` | API unavailable is reported; local fallback is allowed; no restart |
| `verify` | ZIP path, optional SHA-256 file, optional extracted E2E flag | `validate_via_zip.py` | `verify/verification.json`, isolated extraction directory | Stop on checksum, path traversal, or CRC failure |
| `all` | Inputs from both actions | `inspect` then `verify` | `VIA_AzureFlow_QA_Run_Summary.json` plus both subdirectories | Exit nonzero if either action fails |

## 3. Combined summary schema

```json
{
  "schema": "VIA_AZUREFLOW_QA_PLUGIN_RUN/1.0",
  "plugin": "via-azureflow-qa-plugin",
  "action": "all",
  "started_at": "ISO-8601",
  "finished_at": "ISO-8601",
  "inputs": {
    "base_url": "http://127.0.0.1:8766",
    "root": "path or Windows path",
    "zip": "path or null",
    "run_extracted_e2e": false
  },
  "actions": {
    "inspect": {"status": "PASS|FAIL|SKIPPED", "exit_code": 0, "report": "..."},
    "verify": {"status": "PASS|FAIL|SKIPPED", "exit_code": 0, "json": "..."}
  },
  "safety": {
    "source_write": false,
    "source_delete": false,
    "code_execution": false,
    "network": false,
    "human_review_required": true
  },
  "status": "PASS|FAIL|REVIEW_REQUIRED"
}
```

When `--run-extracted-e2e` is used, `code_execution` in the summary still refers to user/source-code execution. The package test runner is an explicit verification action and must remain visible as `run_extracted_e2e=true`.

## 4. Standalone UI contract

The HTML template must remain usable through `file://` and must contain:

- a light compact theme marker `via-azureflow-light-compact`;
- a ZIP file input and drag-and-drop target;
- a Windows path input for the AzureFlow root;
- an API URL input;
- exactly three primary action buttons: `inspect`, `verify`, and `all`;
- a command preview and copy button;
- no `<script src>`, `<link href>`, CDN, image, iframe, fetch, WebSocket, or remote resource dependency;
- no automatic execution of a selected file.

The browser UI is a control surface. The PowerShell launcher and Python CLI are the execution surface.

## 5. Acceptance gates

A complete verification is valid only when:

1. `inspect` reports API health/status or clearly records API unavailability and performs local fallback without restarting a service.
2. `verify` passes SHA-256 when a checksum file is supplied.
3. ZIP path safety and CRC pass before extraction.
4. Required files, HTML body/markers, no external/local script links, inline JavaScript syntax, E2E report, JUnit XML, industry profiles, copied UI synchronization, and screenshots pass according to the package contract.
5. The combined summary records every action, output path, exit code, input path, and safety flag.
6. The skill directory passes `quick_validate.py` before packaging.
7. The extracted skill package passes the same validator and can run the CLI in offline mode.

## 6. Parent-system handoff

A parent VIA system may consume `all/VIA_AzureFlow_QA_Run_Summary.json` as a single job artifact. It may link the two subreports under `inspect/` and `verify/` without copying user source. A `PASS` package result does not activate engines, approve commands, or change SSOT status. Human review remains required for SSOT promotion, command execution, external network providers, and deployment.
