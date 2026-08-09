# Veritas WorkOps ENG-050..053 v0100

Target baseline:
- repository: `tonykuni/movies-dataset`
- branch: `claude/via-system-followup-tz7k9t`
- audited HEAD: `fadbdfdda250156f8172e4737ab7434044869554`
- branch relation at audit: identical to `main`

## Why these four
The prior GapFill functions are already native in the repository as ENG-039..045. Daily To-Do, MeetingLoop bridge, audit/matrix, dedup, and Board v0126 are also present. This package therefore does not recreate those functions.

### ENG-050 Unified Work Register
Derived single view over:
- FOLLOWUP / THREAD
- DECISION
- MILESTONE
- COMMITMENT
- MEETING_ACTION
- CLOSURE_CANDIDATE / CLOSURE

Outputs:
- `out/unified_work_register.json`
- `out/unified_work_register.csv`

It is **not** a new canonical ledger. Original source ledgers remain authoritative.

### ENG-051 Commitment Intelligence
Adds explicit `CMT-####` obligations:
- who promised
- what is promised
- due date
- source reference
- state
- fulfillment evidence

Structured DEC/MLS sources may become **candidates**, never automatic commitments.
Human commands are required for create/accept/reschedule/fulfill.

### ENG-052 Cross-Ledger Consistency Guard
Report-only contradictions such as:
- closed WOP still has open DEC/MLS/CMT
- milestone or commitment points to unknown WOP
- reply thread has no WOP
- stale pending thread already has a parsed reply
- dependency references missing milestone
- dependency cycles
- closure candidate still has blockers

No auto-fix.

### ENG-053 Explainable Project Health & Progress
Progress uses only available evidence dimensions:
- milestones 40%
- commitments 30%
- decisions 20%
- thread completion 10%

Weights are normalized over available dimensions.
Health starts from 100 and subtracts transparent penalties for overdue/block/risk/dependency/consistency signals.

`source_coverage_pct` is data coverage, **not model accuracy**.

## Security / governance
- no Outlook send
- no mailbox move/delete
- no existing WOP/THR/DEC/MLS/CLS/LLN rewrite
- no automatic closure
- no automatic commitment creation from free-form mail
- derived files can be rebuilt
