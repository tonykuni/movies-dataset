# VIA WorkOps Smart Workflow v0104

## New engines
### ENG-041 Daily Operating Rhythm
Turns project/watchlist/commitment facts into four simple work phases:
1. Morning Risk Control
2. Close Key Gaps Before Noon
3. Afternoon Execution / Recovery
4. End-of-Day Follow-up Preparation

The engine is advisory only. It never sends, escalates or closes.

### ENG-043 Commitment Fulfillment
Lifecycle:
Candidate → Human Confirm → `CMT-YYYYMMDD-NNNNNN` → OPEN/DUE_SOON/OVERDUE → Fulfill or Revise with evidence.

Important commitment facts are not silently promoted. Derived candidates require confirmation.

## UI
`ui/daily_rhythm.html` supports:
- 繁體中文
- 简体中文
- English
- current daypart
- open / due soon / overdue commitment KPIs
- four phase operating rhythm
- commitment control table

## Recommended daily chain
ENG-029 → ENG-030 → ENG-037 → ENG-043 scan/evaluate → ENG-034 → ENG-038 → ENG-035 → ENG-039 → ENG-041 → Human Action.

## Governance
No automatic send, escalation, closure, Outlook move/delete, or commitment registration.
