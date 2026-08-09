# Board v0127 proposal

Keep Board v0126 VisualLock structure and color tokens. Add data only.

## Surface 00 Today
Add four compact KPI chips:
- Active commitments
- Overdue commitments
- Cross-ledger errors/warnings
- WOP warning-or-worse

## Project rows/cards
Add:
- Progress % (ENG-053)
- Health L1-L5 + explicit top penalty
- Open CMT count
- Consistency finding count

## Search / navigation
Do not create another page if avoidable:
- existing unified search remains canonical search
- add links from health/consistency rows back to native IDs

## Accuracy
Do not mix `source_coverage_pct` with Gold Set accuracy.
Gold Set remains measured accuracy; ENG-053 coverage only describes how many structured dimensions are available.
