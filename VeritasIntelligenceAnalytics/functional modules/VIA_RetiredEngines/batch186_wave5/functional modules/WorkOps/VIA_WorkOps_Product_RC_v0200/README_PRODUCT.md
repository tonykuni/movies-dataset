# Veritas WorkOps v2.0 Release Candidate

Workflow Optimization × Smart Email Tracking Management

This package closes the six productization lanes:

1. Microsoft 365 / Outlook delegated connector
2. Local FastAPI + mouse-first UI actions
3. DuckDB + Parquet SSOT with local degraded fallback
4. Unified Work Register + Timeline + Dependency impact
5. Gold Dataset Accuracy Benchmark + calibration metrics
6. Installer + Diagnostics + Backup + IT Governance + Onboarding

## Start
Development/package mode:
```text
python engines/workops_api_server.py
```
Then open:
`http://127.0.0.1:8775/`

Windows product installation:
```powershell
pwsh -File installer\Install-VeritasWorkOps.ps1
```

## Security defaults
- localhost only
- Outlook read disabled until configured and IT approval is acknowledged
- Mail.Read read scope by default
- optional Mail.ReadWrite only for draft creation
- no auto-send endpoint
- no mailbox delete/move
- token cache excluded from backup
- restore is staging-only
- project classification and close remain human-confirmed
