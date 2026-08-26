# Veritas WorkOps v2.0 — Release Candidate

## Product surfaces
- Today
- Projects
- Classification Review
- Accuracy
- Search
- Setup / IT

## Release status
The standalone local RC closes the planned functional and productization backlog. Local mock/integration acceptance passes with 36 registered modules.

Three target-environment validations remain intentionally external to the build sandbox:
1. company Microsoft 365 delegated authentication,
2. native DuckDB/Parquet runtime after installer dependency installation,
3. Windows PowerShell 7 installer/runtime validation.

These are acceptance gates, not unfinished feature modules. See `docs/TARGET_ACCEPTANCE_CHECKLIST.md`.
