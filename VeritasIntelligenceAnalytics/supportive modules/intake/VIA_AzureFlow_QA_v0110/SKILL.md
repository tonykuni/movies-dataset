---
name: via-azureflow-qa-plugin
description: Standalone VIA AzureFlow QA plug-in that combines read-only AzureFlow v8 engine/job inspection with VIA ZIP/E2E and standardized-package verification. Use for Windows I/O, drag-and-drop ZIP validation, completed-job artifact inspection, light standalone UI, three one-click actions, or packaging a reusable VIA sub-engine.
---

# VIA 天青智流 AzureFlow QA Plug-in

Use this skill as a small, independent VIA sub-engine for deterministic QA. It combines the existing read-only `via-azureflow-inspection` workflow with the `via-e2e-zip-verifier` ZIP, HTML, E2E, JUnit, industry-profile, standardized-package, and package-integrity checks.

## Operating contract

- Preserve source files and input ZIPs. Never write back to an AzureFlow source, registry, job run, or user-selected archive.
- Never import, execute, or auto-deploy user source. AzureFlow inspection is metadata/API/file inspection only. ZIP E2E execution is opt-in through `--run-extracted-e2e` and runs only after path-safety and CRC checks.
- Keep network disabled by default. The inspect action may issue GET requests only to the explicitly supplied AzureFlow API URL, normally `http://127.0.0.1:8766`.
- Treat `completed` as job completion, not proof that every optional artifact was selected for API download.
- Keep the distinction between local run artifacts and API-selected downloads. A local file may exist while its logical API endpoint is unselected.
- Preserve `NOT_MOUNTED_IN_SANDBOX` for Windows paths that are not visible in the current environment.
- Treat `PROPOSAL_REVIEW_REQUIRED`, `active_review_required`, `PASS_WITH_REVIEW`, and `review_required=true` as review states, not full activation.

## Three simple actions

The bundled `scripts/via_azureflow_qa.py` exposes exactly three user-facing actions:

1. **AzureFlow inspection** (`inspect`): query `/api/health`, `/api/catalog`, `/api/status`, `/api/jobs`, and `/api/dashboard`; merge live data with the v8 SSOT registry; inspect local run directories and selected artifacts; write a Markdown inspection report.
2. **ZIP/package verification** (`verify`): validate SHA-256 when supplied, reject path traversal, run ZIP CRC checks, extract into an isolated directory, and route automatically to either `validate_via_zip.py` for a VIA all-in-one package or `validate_standardized_zip.py` for a standardized package with one `manifest.json` root. Verify required standalone HTML, inline JavaScript, bundled E2E/JUnit reports, industry profiles, copied UI synchronization, and screenshots according to the selected package contract.
3. **Complete QA** (`all`): run actions 1 and 2, then write one machine-readable `VIA_AzureFlow_QA_Run_Summary.json` containing action statuses, report paths, safety flags, package kind, and exit codes.

Use `--package-kind auto|via|standardized` when automatic ZIP classification needs to be overridden.

## Quick start on Windows

From PowerShell in the extracted plug-in directory:

```powershell
.\Invoke-VIA-AzureFlowQA.ps1 -Action All `
  -Root 'C:\VIA\reconstruction' `
  -Zip 'C:\VIA\delivery\VIA-All-Latest.zip' `
  -Output 'C:\VIA\QA-Output'
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

python scripts/via_azureflow_qa.py all \
  --base-url http://127.0.0.1:8766 \
  --root /path/to/reconstruction \
  --zip /path/to/VIA-All-Latest.zip \
  --out-dir ./VIA_AzureFlow_QA_Output
```

The CLI exits nonzero if a selected action fails. Missing paths are recorded as failed preflight checks instead of being executed or silently skipped.

## Reusable resources

- `scripts/via_azureflow_qa.py`: three-action orchestrator, path preflight, validator routing, and summary writer.
- `scripts/inspect_azureflow.py`: read-only AzureFlow engine/job/artifact inspector.
- `scripts/validate_via_zip.py`: isolated VIA all-in-one ZIP and extracted-package verifier.
- `scripts/validate_standardized_package.py`: standardized-package directory contract validator.
- `scripts/validate_standardized_zip.py`: safe standardized ZIP extractor and validator wrapper.
- `scripts/Invoke-VIA-AzureFlowQA-Scheduled.ps1`: timestamped scheduled runner for Windows Task Scheduler.
- `scripts/Register-VIAAzureFlowQATask.ps1`: register, update, or unregister a Task Scheduler task.
- `scripts/Test-VIAAzureFlowQATask.ps1`: direct runner smoke test or registered-task test harness.
- `Invoke-VIA-AzureFlowQA.ps1`: Windows one-click launcher.
- `Run-VIAAzureFlowQAScheduled.cmd`: editable CMD batch example for Task Scheduler.
- `templates/VIA_AzureFlow_QA_Standalone.html`: light, compact, mouse-first UI.
- `templates/VIA_AzureFlow_Windows_Deployment_Interactive.html`: local interactive installation and architecture diagram.
- `references/integration_contract.md`: schemas, outputs, action matrix, and safety gates.
- `references/windows_installation_deployment_manual.md`: Windows installation, deployment, launcher source walkthrough, UI source walkthrough, and troubleshooting.
- `references/VIA_AzureFlow_Windows_Deployment_Architecture.mmd`: deterministic Mermaid architecture source.
- `references/VIA_AzureFlow_Windows_Deployment_Architecture.png`: rendered static architecture image.

## Required verification sequence

1. Run `python -m py_compile` against all bundled Python scripts.
2. Run the CLI `inspect` action against a live API or an offline local run root.
3. Run the CLI `verify` action against a known ZIP and a deliberately missing or unsafe path fixture. Confirm auto-detection records the selected validator.
4. Open the HTML with a browser or run a static DOM smoke test. Confirm no external resources, file inputs, three action buttons, and command preview.
5. Render the Mermaid architecture source to PNG and check the interactive architecture HTML's inline JavaScript syntax.
6. On Windows, run the scheduled runner smoke test, then optionally register and trigger a real Task Scheduler task.
7. Run `quick_validate.py` against this skill directory.
8. Package the entire skill directory without `__pycache__`, then validate the extracted package again.

## Output interpretation

- `inspect/VIA_AzureFlow_Engine_Job_Inspection.md` is the human-readable engine/job report.
- `verify/verification.json` is the structured package verification result.
- `all/VIA_AzureFlow_QA_Run_Summary.json` is the combined handoff record.
- `all/` may contain reports from both actions; it is append-only and can be copied into a parent VIA system.

Do not claim a Windows sample was tested unless the selected path exists in the current environment. Do not claim a ZIP is verified if checksum, path safety, CRC, required files, HTML contract, E2E, JUnit, industry profiles, or screenshots fail.

## References

- Read [integration_contract.md](references/integration_contract.md) when mapping the combined output to a parent VIA system or when deciding whether an E2E run is allowed.
- Read [windows_installation_deployment_manual.md](references/windows_installation_deployment_manual.md) when exporting the plug-in to Windows, explaining launcher parameters, or documenting the standalone UI.
- Read [VIA_AzureFlow_Windows_Deployment_Architecture.mmd](references/VIA_AzureFlow_Windows_Deployment_Architecture.mmd) and open [VIA_AzureFlow_Windows_Deployment_Interactive.html](templates/VIA_AzureFlow_Windows_Deployment_Interactive.html) when explaining installation flow or Task Scheduler deployment.
- Use the bundled deterministic subroutines rather than duplicating their parsing logic in an agent response.
- Keep the UI local-only and use the PowerShell launcher for actual Windows filesystem execution.

## Delivery rule

When delivering this skill, attach the `SKILL.md` path so Manus can package it as a `.skill` artifact, and also provide the ZIP package when a portable file is requested.
