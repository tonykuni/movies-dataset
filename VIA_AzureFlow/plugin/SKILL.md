---
name: via-azureflow-qa-plugin
description: Standalone VIA AzureFlow QA plug-in and complete system facade that combines read-only AzureFlow v8 inspection, VIA ZIP/E2E/standardized-package verification, Windows I/O, Task Scheduler readiness, human-review activation gates, and one-click parent-system handoff. Use for Windows path or drag-and-drop ZIP QA, completed-job inspection, scheduled validation, or packaging a reusable VIA sub-engine.
---

# VIA 天青智流 AzureFlow QA Plug-in

Use this skill as a **single, manifest-driven VIA sub-engine and system facade**. It keeps the original three deterministic actions (`inspect`, `verify`, `all`) backward compatible, then composes them through `complete_system` for one reproducible workflow:

1. Validate the plug-in manifest and all declared entrypoints.
2. Run AzureFlow v8 read-only inspection.
3. Verify the selected VIA or standardized ZIP.
4. Write one combined QA handoff.
5. Check Windows Task Scheduler readiness without registering a task automatically.
6. Stop at the human-review activation gate unless the Windows operator explicitly uses `-ActivateSchedule`.

## Operating contract

- Preserve source files, input ZIPs, AzureFlow runs, registries, and user-selected archives. Never write back to them.
- Never import, execute, or auto-deploy user source. Packaged E2E is opt-in through `--run-extracted-e2e` and runs only after checksum, path-safety, and CRC checks.
- Keep network disabled by default. `inspect` may issue GET requests only to the explicitly supplied AzureFlow API URL, normally `http://127.0.0.1:8766`.
- Treat `completed` as job completion, not proof that every optional artifact was selected for API download.
- Preserve `NOT_MOUNTED_IN_SANDBOX` for Windows paths that are not visible in the current environment.
- Treat `PROPOSAL_REVIEW_REQUIRED`, `active_review_required`, `PASS_WITH_REVIEW`, and `review_required=true` as review states, not full activation.
- Never restart a quiet or unavailable AzureFlow service automatically.

## Three compatible QA actions

The bundled `scripts/via_azureflow_qa.py` exposes exactly three user-facing actions:

1. **AzureFlow inspection** (`inspect`): query `/api/health`, `/api/catalog`, `/api/status`, `/api/jobs`, and `/api/dashboard`; merge live data with the v8 SSOT registry; inspect local run directories and selected artifacts; write a Markdown inspection report.
2. **ZIP/package verification** (`verify`): validate SHA-256 when supplied, reject path traversal, run ZIP CRC checks, extract into an isolated directory, and route automatically to either `validate_via_zip.py` for a VIA all-in-one package or `validate_standardized_zip.py` for a standardized package with one `manifest.json` root.
3. **Complete QA** (`all`): run actions 1 and 2, then write `VIA_AzureFlow_QA_Run_Summary.json` containing action statuses, report paths, safety flags, package kind, and exit codes.

Use `--package-kind auto|via|standardized` when automatic ZIP classification needs to be overridden.

## Unified complete-system mode

Use `scripts/via_azureflow_qa_system.py` or the Windows `Invoke-VIAAzureFlowQASystem.ps1` launcher when the user needs one complete, auditable flow rather than separate actions. It does not replace the three actions; it coordinates them.

```powershell
.\Invoke-VIAAzureFlowQASystem.ps1 `
  -Root 'C:\VIA\work\reconstruction' `
  -Zip 'C:\VIA\delivery\VIA-All-Latest.zip' `
  -ChecksumFile 'C:\VIA\delivery\VIA-All-Latest.zip.sha256' `
  -Output 'C:\VIA\QA\system-run' `
  -NoArtifactProbe
```

The system output is:

- `VIA_AzureFlow_QA_System_Report.json`: machine-readable manifest, QA, scheduling, activation, and safety state.
- `VIA_AzureFlow_QA_System_Report.md`: human-readable matrix and handoff report.
- `qa/`: the existing inspect/verify/all output tree.
- `activation_result.json`: `READY_FOR_WINDOWS_ACTIVATION` unless explicit activation was requested.

The system layer never registers a Windows task by default. On a real Windows host, after reviewing a PASS report, explicitly use:

```powershell
.\Invoke-VIAAzureFlowQASystem.ps1 `
  -Root 'C:\VIA\work\reconstruction' `
  -Zip 'C:\VIA\delivery\VIA-All-Latest.zip' `
  -ChecksumFile 'C:\VIA\delivery\VIA-All-Latest.zip.sha256' `
  -Output 'C:\VIA\QA\system-run' `
  -ActivateSchedule `
  -TaskName 'VIA-AzureFlow-QA-All' `
  -Schedule Daily `
  -At (Get-Date).Date.AddHours(2) `
  -RunOnlyWhenUserIsLoggedOn
```

`-ActivateSchedule` is an explicit Windows-side action. It calls `Register-VIAAzureFlowQATask.ps1` only after QA returns PASS, and records `activation_result.json`. It does not promote SSOT, approve commands, or execute source content.

## Quick start on Windows

From PowerShell in the extracted plug-in directory:

```powershell
.\Invoke-VIA-AzureFlowQA.ps1 -Action All `
  -Root 'C:\VIA\work\reconstruction' `
  -Zip 'C:\VIA\delivery\VIA-All-Latest.zip' `
  -Output 'C:\VIA\QA\qa-run'
```

For a full extracted-package browser run, add `-RunExtractedE2E`. This is intentionally opt-in because it executes the package's bundled test runner after archive safety checks. For standardized packages, use `-PackageKind Standardized` when auto-detection is not appropriate.

For the UI, open `templates/VIA_AzureFlow_QA_Standalone.html` directly with Edge or Chrome. The UI is standalone `file://` HTML with inline CSS and JavaScript; it has no CDN, server, fetch dependency, or remote resource.

## Core script usage

```bash
python scripts/via_azureflow_qa.py inspect \
  --base-url http://127.0.0.1:8766 \
  --root /path/to/reconstruction \
  --out-dir ./VIA_AzureFlow_QA_Output

python scripts/via_azureflow_qa.py verify \
  --zip /path/to/VIA-All-Latest.zip \
  --checksum-file /path/to/VIA-All-Latest.zip.sha256 \
  --package-kind auto \
  --out-dir ./VIA_AzureFlow_QA_Output

python scripts/via_azureflow_qa_system.py \
  --root /path/to/reconstruction \
  --zip /path/to/VIA-All-Latest.zip \
  --checksum-file /path/to/VIA-All-Latest.zip.sha256 \
  --out-dir ./VIA_AzureFlow_QA_System_Output
```

The CLI exits nonzero if a selected action fails. Missing paths are recorded as failed preflight checks instead of being executed or silently skipped.

## Reusable resources

- `scripts/via_azureflow_qa.py`: three-action orchestrator, path preflight, validator routing, and QA summary writer.
- `scripts/via_azureflow_qa_system.py`: manifest-driven complete-system orchestrator and system report writer.
- `scripts/inspect_azureflow.py`: read-only AzureFlow engine/job/artifact inspector.
- `scripts/validate_via_zip.py`: isolated VIA all-in-one ZIP and extracted-package verifier.
- `scripts/validate_standardized_package.py`: standardized-package directory contract validator.
- `scripts/validate_standardized_zip.py`: standardized ZIP safe extractor and validator wrapper.
- `Invoke-VIA-AzureFlowQA.ps1`: compatible Windows three-action launcher.
- `Invoke-VIAAzureFlowQASystem.ps1`: unified Windows system launcher with explicit activation gate.
- `scripts/Invoke-VIA-AzureFlowQA-Scheduled.ps1`: timestamped scheduled runner.
- `scripts/Register-VIAAzureFlowQATask.ps1`: create, update, or remove a Windows Task Scheduler task.
- `scripts/Test-VIAAzureFlowQATask.ps1`: direct runner and registered-task test harness.
- `templates/VIA_AzureFlow_QA_Standalone.html`: light, compact, mouse-first UI.
- `templates/VIA_AzureFlow_Windows_Deployment_Interactive.html`: local interactive architecture view.
- `references/integration_contract.md`: schemas, outputs, system mode, action matrix, and safety gates.
- `references/windows_installation_deployment_manual.md`: Windows installation, deployment, unified system, launcher, UI, Task Scheduler, and troubleshooting.

## Required verification sequence

1. Run `python -m py_compile` against all bundled Python scripts.
2. Validate `plugin_manifest.json` and every declared entrypoint.
3. Run the CLI `inspect` action against a live API or offline local run root.
4. Run the CLI `verify` action against a known ZIP and deliberately missing or unsafe path fixtures.
5. Run the unified system mode against a known PASS fixture and confirm system JSON/Markdown reports.
6. Open the HTML with a browser or run a static DOM smoke test. Confirm no external resources, file inputs, three action buttons, and command preview.
7. Run the direct scheduled runner simulation and verify `task_result.json`, logs, and exit code.
8. Run `quick_validate.py` against this skill directory.
9. Package the entire skill directory without `__pycache__`, then validate the extracted package again.
10. On Windows only, after human review of a PASS system report, use `-ActivateSchedule` and then run `Test-VIAAzureFlowQATask.ps1 -UseRegisteredTask`.

## Output interpretation

- `inspect/VIA_AzureFlow_Engine_Job_Inspection.md` is the human-readable engine/job report.
- `verify/verification.json` is the structured package verification result.
- `all/VIA_AzureFlow_QA_Run_Summary.json` is the compatible combined handoff record.
- `VIA_AzureFlow_QA_System_Report.json` is the complete-system handoff.
- `VIA_AzureFlow_QA_System_Report.md` is the human-readable system matrix.
- `activation_result.json` records whether Task Scheduler registration was not requested, blocked, failed, or activated.

Do not claim a Windows sample was tested unless the selected path exists on the current host. Do not claim a ZIP is verified if checksum, path safety, CRC, required files, HTML contract, E2E, JUnit, industry profiles, or screenshots fail. Do not call `READY_FOR_WINDOWS_ACTIVATION` the same as an actual registered Windows task.

## References

- Read [integration_contract.md](references/integration_contract.md) when mapping system output to a parent VIA system or deciding whether activation is allowed.
- Read [windows_installation_deployment_manual.md](references/windows_installation_deployment_manual.md) when exporting to Windows, explaining launcher parameters, or documenting Task Scheduler.
- Read [VIA_AzureFlow_Windows_Deployment_Architecture.mmd](references/VIA_AzureFlow_Windows_Deployment_Architecture.mmd) when updating the deployment diagram.
- Use the bundled deterministic subroutines rather than duplicating their parsing logic in an agent response.
- Keep the UI local-only and use the PowerShell launcher for actual Windows filesystem execution.

## Delivery rule

When delivering this skill, attach the `SKILL.md` path so Manus can package it as a `.skill` artifact, and also provide the ZIP package when a portable file is requested.
