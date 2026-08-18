# VIA v0140B OneDrive Hydration — Manual Decision

## Purpose

Use this procedure only after v0140B returns `HOLD_IMPLICIT_HYDRATION_RISK_NO_SYSTEM_MUTATION`. The validation package deliberately does not hydrate, pin, copy, hash, or open a recall-on-access candidate.

## What the HOLD means

`OFFLINE`, `RECALL_ON_OPEN`, or `RECALL_ON_DATA_ACCESS` indicates that a content read may change local OneDrive state. The guard therefore authorizes metadata inspection only and skips H02–H06. A HOLD is a successful enforcement of the read-only boundary.

## Required human decision

Choose exactly one disposition outside the validator:

1. **Keep cloud-only and stop.** Preserve the current OneDrive state. Do not rerun content-handle probes against this candidate.
2. **Make locally available by explicit user action.** In File Explorer, the user may deliberately choose the appropriate OneDrive availability action and wait for sync to settle. This is a user-owned state mutation and must not be automated or attributed to v0140B.
3. **Select an already-local alternate source.** Point a new run at a distinct file whose Windows attributes do not contain any blocking recall flag. Do not copy the held candidate as part of the validation run.

## Before rerun

- Record which disposition was chosen and who authorized it.
- Confirm OneDrive has no pending sync/error indication for the selected source.
- Rerun v0140B from a fresh run directory with the same read-only approval token.
- Let H01 re-evaluate attributes; do not bypass or override the guard.
- Treat `reparse_tag = 0` as informational only. A blocking recall attribute remains sufficient for HOLD.

## Promotion boundary

Only `PASS_HANDLE_EVIDENCE_READY_NO_SYSTEM_MUTATION` may support a later proposal for sequential reader-path patch validation. It does not itself authorize a patch, production ingestion, canonical runtime execution, or candidate promotion.

## Audit note template

```text
Decision UTC:
Decision owner:
Disposition: KEEP_CLOUD_ONLY | USER_MADE_LOCAL | ALREADY_LOCAL_ALTERNATE
Candidate label (no absolute path):
OneDrive state reviewed: YES/NO
Fresh v0140B run ID:
Resulting gate:
```
