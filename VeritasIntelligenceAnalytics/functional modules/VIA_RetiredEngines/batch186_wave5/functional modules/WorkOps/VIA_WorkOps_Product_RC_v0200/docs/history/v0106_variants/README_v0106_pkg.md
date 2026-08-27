# VIA WorkOps Follow-up State UI v0100 (ENG-030)

Drop-in extension for `VeritasIntelligenceAnalytics/functional modules/WorkOps/`.

## Architecture
- Parameters: `engines/followup_state_params.json`
- Engine: `engines/workops_followup_state.py`
- UI: `ui/followup/index.html`, `styles.css`, `app.js`

## Existing WorkOps inputs reused
- `out/reply_status.json` (ENG-029)
- `out/reply_events.jsonl` (ENG-029 append-only fact stream)
- `out/wop_registry.json` (ENG-028, when present)

## New derived / append-only outputs
- `out/followup_state.json` — recomputable derived state
- `out/followup_close_events.jsonl` — human-confirmed close events only

## Safety boundary
- This module does not read Outlook directly.
- It does not send, move, delete, mark-read, or modify mail.
- It consumes existing read-only WorkOps exports.
- "Done" from a reply becomes `DONE_CANDIDATE`; it does **not** auto-close.
- Close is mouse-confirmed and appended as an event.

## Install into repo
Copy:
- `engines/followup_state_params.json` -> `.../WorkOps/engines/`
- `engines/workops_followup_state.py` -> `.../WorkOps/engines/`
- `ui/*` -> `.../WorkOps/ui/followup/`

## Run
From WorkOps directory:

```powershell
py .\engines\workops_followup_state.py state
py .\engines\workops_followup_state.py serve
```

Then open `http://127.0.0.1:8775/`.

## Five-level spectrum
1 Stable `#4C72B0`
2 Monitor `#64B5CD`
3 Attention `#E5C849`
4 Warning `#DD8452` — breathing lamp
5 Critical `#C44E52` — breathing lamp

All thresholds and labels are JSON-controlled.
