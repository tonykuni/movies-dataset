# VIA AzureFlow QA Plug-in Integration Contract

## 1. Plug-in identity

| Field | Value |
|---|---|
| Plug-in name | `VIA 天青智流 AzureFlow QA Plug-in` |
| Package skill ID | `via-azureflow-qa-plugin` |
| Version | `1.2.0` |
| Primary role | Manifest-driven AzureFlow v8 inspection plus VIA standalone ZIP/E2E verification and Windows scheduling facade |
| Runtime | Python 3.10+; PowerShell 7 or Windows PowerShell launcher; standalone `file://` HTML UI |
| Default API | `http://127.0.0.1:8766` |
| Default network policy | disabled except explicit localhost/API GET for `inspect` |
| Default source policy | no source write, no source delete, no code execution |

## 2. Backward-compatible action matrix

| Action | Inputs | Main subroutine | Outputs | Failure boundary |
|---|---|---|---|---|
| `inspect` | AzureFlow API URL, workspace/root, optional runs directory | `inspect_azureflow.py` | `inspect/VIA_AzureFlow_Engine_Job_Inspection.md` | API unavailable is reported; local fallback is allowed; no restart |
| `verify` | ZIP path, optional SHA-256 file, optional extracted E2E flag | `validate_via_zip.py` or `validate_standardized_zip.py` | `verify/verification.json`, isolated extraction directory | Stop on checksum, path traversal, or CRC failure |
| `all` | Inputs from both actions | `inspect` then `verify` | `VIA_AzureFlow_QA_Run_Summary.json` plus both subdirectories | Exit nonzero if either action fails |

The three actions remain the only user-facing QA action IDs in `plugin_manifest.json`. The complete system is a facade that composes them and does not fork a second validator implementation.

## 3. Complete-system workflow

`complete_system` is exposed through `scripts/via_azureflow_qa_system.py` and `Invoke-VIAAzureFlowQASystem.ps1`:

1. Read and validate `plugin_manifest.json`.
2. Check all manifest-declared entrypoint files and record bytes/hash.
3. Run compatible `all` using the existing QA CLI.
4. Evaluate scheduled-runner files and Windows runtime readiness.
5. Write one system JSON and one system Markdown report.
6. Stop at `READY_FOR_WINDOWS_ACTIVATION` unless the Windows operator explicitly passes `-ActivateSchedule`.

The Python system layer never registers a Windows task. The PowerShell system launcher may call `Register-VIAAzureFlowQATask.ps1` only after QA status is `PASS` and only when `-ActivateSchedule` is explicitly present.

## 4. Combined QA summary schema

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
    "inspect": {"status": "PASS|FAIL|REVIEW_REQUIRED", "exit_code": 0, "report": "..."},
    "verify": {"status": "PASS|FAIL", "exit_code": 0, "report": "..."}
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

## 5. System report schema

```json
{
  "schema": "VIA_AZUREFLOW_QA_SYSTEM/1.0",
  "plugin": "via-azureflow-qa-plugin",
  "version": "1.2.0",
  "mode": "complete_system",
  "status": "PASS|FAIL|REVIEW_REQUIRED",
  "manifest_summary": {"total": 0, "passed": 0, "failed": 0},
  "manifest_inventory": [],
  "inputs": {"root": {}, "zip": {}, "checksum_file": {}},
  "qa": {"status": "PASS", "exit_code": 0, "summary": "...", "actions": {}},
  "scheduling": {
    "status": "READY|BLOCKED",
    "windows_runtime_available": false,
    "scheduled_runner": "...",
    "registration_script": "...",
    "task_test": "...",
    "cmd_wrapper": "..."
  },
  "activation": {
    "status": "READY_FOR_WINDOWS_ACTIVATION|ACTIVATED|BLOCKED_QA_NOT_PASS|ACTIVATION_FAILED",
    "registered": false,
    "automatic_registration": false,
    "human_review_required": true
  },
  "safety": {
    "source_write": false,
    "source_delete": false,
    "code_execution": false,
    "network": false,
    "automatic_command_activation": false,
    "ssot_promotion": false,
    "human_review_required": true
  }
}
```

## 6. Activation result schema

`activation_result.json` is written by the Windows system launcher:

```json
{
  "schema": "VIA_AZUREFLOW_QA_SYSTEM_ACTIVATION/1.0",
  "plugin": "via-azureflow-qa-plugin",
  "requested": false,
  "status": "READY_FOR_WINDOWS_ACTIVATION",
  "registered": false,
  "task_name": "VIA-AzureFlow-QA-All",
  "qa_exit_code": 0,
  "safety": {
    "source_write": false,
    "source_delete": false,
    "automatic_command_activation": false,
    "ssot_promotion": false,
    "human_review_required": true
  }
}
```

## 7. Standalone UI contract

The HTML template must remain usable through `file://` and must contain:

- a light compact theme marker `via-azureflow-light-compact`;
- a ZIP file input and drag-and-drop target;
- a Windows path input for the AzureFlow root;
- an API URL input;
- exactly three primary QA action buttons: `inspect`, `verify`, and `all`;
- a command preview and copy button;
- an optional complete-system command preview that still requires PowerShell for execution;
- no `<script src>`, `<link href>`, CDN, image, iframe, fetch, WebSocket, or remote resource dependency;
- no automatic execution of a selected file.

The browser UI is a control surface. The PowerShell launchers and Python CLI are the execution surfaces.

## 8. Acceptance gates

A complete verification is valid only when:

1. `inspect` reports API health/status or clearly records API unavailability and performs local fallback without restarting a service.
2. `verify` passes SHA-256 when a checksum file is supplied.
3. ZIP path safety and CRC pass before extraction.
4. Required files, HTML body/markers, no external/local script links, inline JavaScript syntax, E2E report, JUnit XML, industry profiles, copied UI synchronization, and screenshots pass according to the package contract.
5. `complete_system` records manifest checks, every action, output path, exit code, scheduler readiness, activation status, and safety flags.
6. The skill directory passes `quick_validate.py` before packaging.
7. The extracted skill package passes the same validator and can run the CLI in offline mode.
8. Windows task registration is called only by explicit `-ActivateSchedule`; it is never implicit in `All` or Python system mode.

## 9. Parent-system handoff

A parent VIA system may consume `VIA_AzureFlow_QA_System_Report.json` as the preferred system artifact and retain `VIA_AzureFlow_QA_Run_Summary.json` for backward compatibility. It may link the `qa/inspect` and `qa/verify` subreports without copying user source. A `PASS` package result does not activate engines, approve commands, change SSOT status, or register a task. Human review remains required for SSOT promotion, command execution, external network providers, deployment, and Windows task activation.
