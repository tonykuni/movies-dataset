# Target Acceptance Checklist — Windows / Microsoft 365

The package can be fully tested locally without Outlook mutation. The following gates require the target Windows/company environment.

## Gate A — Windows install
- PowerShell 7+
- Python 3.12+
- Local venv creates successfully
- `duckdb`, `pyarrow`, `polars`, `msal` install successfully
- Desktop shortcut launches `127.0.0.1:8775`
- No administrator rights required unless company policy says otherwise

## Gate B — Microsoft Entra / IT
- IT approves delegated signed-in-user mailbox scope
- Client ID / tenant set in Setup UI
- `Mail.Read` authentication succeeds
- Folder discovery is limited to the signed-in user's accessible mailbox scope
- Delta sync returns new/changed messages
- Token cache remains local
- `allow_send` remains false

## Gate C — Native SSOT
`out/ssot_status.json` should report:
`mode = DUCKDB_PARQUET`

SQLite degraded mode is acceptable only when DuckDB/PyArrow are unavailable.

## Gate D — Optional Outlook drafts
Only if IT/user enables draft capability:
- delegated `Mail.ReadWrite`
- WorkOps can create a Draft
- WorkOps does not send it automatically
- User reviews and sends from Outlook

## Gate E — Real accuracy validation
Create a human-reviewed Gold Set from real authorized work mail:
- Project classification
- Topic episode
- Owner
- Status
- ETA
- Commitment
- Risk
- Closure readiness

Run `workops_accuracy_benchmark.py`.
Do not declare production accuracy from confidence scores alone.

## Gate F — Data governance
Review:
- `docs/IT_GOVERNANCE_HANDOFF.md`
- `config/privacy_policy.json`
- `out/diagnostics.html`
- backup/restore staging
- retention plan before any local purge
