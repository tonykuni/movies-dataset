# VIA WorkOps Smart Workflow v0105

## Focus
Projectized work management + semi-automated email tracking + intelligent visual status.

## New
- ENG-042 Meeting T-2 Preparation Guard
- ENG-044 Lesson Learned Engine
- ENG-045 Process Mining KPI Bridge
- Project Cockpit UI (zh-TW / zh-CN / en)

## Project Cockpit
One project card summarizes:
- immutable Project ID
- user-owned project name
- Level 1–5 status lamp
- Level 4–5 breathing alert
- progress
- owner
- due date
- waiting age
- missing control fields
- current issue / next action
- follow-up readiness
- meeting readiness

Click the card to expand detail. The default view remains concise.

## Meeting T-2
Within 48 hours of a meeting, the guard checks agenda, owner, missing materials, overdue commitments, high risk and blocked actions.

## Lesson Learned
Closure and broken commitments become lesson candidates. Human confirmation is required before `LLN-...` registration.

## KPI Bridge
Outputs:
- `management_kpi.json`
- `process_event_log.csv`

The CSV uses process-mining-ready fields such as:
- `case:concept:name`
- `concept:name`
- `time:timestamp`
- `org:resource`
- `source_id`
- `evidence_id`

No Outlook source mutation, automatic send, automatic close, or automatic escalation.
