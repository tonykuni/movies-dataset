# Invoke-VIA-WorkOps-All-v0106 proposal

Do not modify v0105 in place. Version-forward to v0106.

Recommended post-analysis order:

```text
GapFill / replies / meeting bridge
        ↓
ENG-051 commitments candidates
        ↓
ENG-050 unified register
        ↓
ENG-052 consistency guard
        ↓
ENG-053 project health
        ↓
ENG-046 daily todo refresh
        ↓
Board v0127 generation
```

Commands:

```text
via-workops commitments candidates
via-workops register
via-workops consistency
via-workops health
via-workops todo
```

Rules:
- Consistency `FAIL` should make the overall run `READY_WITH_WARNINGS` / review-required, not mutate data.
- Commitment candidates never auto-accept.
- Board generation may read all four derived outputs.
