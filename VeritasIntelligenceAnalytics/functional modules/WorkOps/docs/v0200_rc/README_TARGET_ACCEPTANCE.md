# Veritas WorkOps Target Acceptance v0201

This is the next stage after `VeritasWorkOps_v0200_RC.zip`.

## What it does
One governed PowerShell runner performs:

1. RC ZIP SHA-256 verification
2. isolated run-local extraction
3. PowerShell AST validation
4. Windows install/upgrade
5. Python compile
6. local RC acceptance
7. **native DuckDB + Parquet gate**
8. LEGO module health
9. diagnostics
10. localhost FastAPI smoke
11. optional explicit Microsoft Graph live-read
12. optional Outlook **Draft-only** validation
13. backup → SHA verify → restore-to-staging
14. HTML / JSON / CSV / transcript report

## Default: Offline

Double-click:

`Run-Offline-Acceptance.cmd`

or:

```powershell
pwsh -File .\Invoke-VeritasWorkOps-TargetAcceptance-v0201.ps1 -Mode Offline
```

This does not access Microsoft 365.

## Live read after IT approval

```powershell
pwsh -File .\Invoke-VeritasWorkOps-TargetAcceptance-v0201.ps1 `
  -Mode LiveRead `
  -ClientId "<IT-PROVIDED-CLIENT-ID>" `
  -TenantId "<TENANT-ID-OR-organizations>" `
  -ItReference "<IT-TICKET>"
```

Microsoft authentication may require Device Code / interactive sign-in.

## Optional Draft-only validation

```powershell
pwsh -File .\Invoke-VeritasWorkOps-TargetAcceptance-v0201.ps1 `
  -Mode LiveReadAndDraft `
  -ClientId "<IT-PROVIDED-CLIENT-ID>" `
  -TenantId "<TENANT-ID>" `
  -ItReference "<IT-TICKET>" `
  -DraftRecipient "your.address@company.com"
```

The runner temporarily enables draft creation, validates `isDraft=true`, and disables draft write again. It never calls a send endpoint.

## Embedded RC payload

`payload\VeritasWorkOps_v0200_RC.zip`

Expected SHA-256:

`2fdc81639d8998ef77dcdee6c46aca009d5b433e6cebb8e8cefe10497553f708`

## Target PASS requirements

- PowerShell AST: PASS
- Python compile: PASS
- Local RC acceptance: PASS
- SSOT mode: **DUCKDB_PARQUET**
- module health: PASS
- localhost API: PASS
- backup verify: PASS
- restore: STAGED_REVIEW_REQUIRED / canonical mutation false
- LiveRead mode only: Graph sync PASS
- LiveReadAndDraft only: draft `isDraft=true`

## Reports

The runner writes an append-only run folder under:

`%USERPROFILE%\Downloads\VeritasWorkOps_TargetAcceptance_Runs\RUN_...`

with:

- `TARGET_ACCEPTANCE_REPORT.html`
- `TARGET_ACCEPTANCE_SUMMARY.json`
- `TARGET_ACCEPTANCE_CHECKS.csv`
- `TARGET_ACCEPTANCE_TRANSCRIPT.txt`
