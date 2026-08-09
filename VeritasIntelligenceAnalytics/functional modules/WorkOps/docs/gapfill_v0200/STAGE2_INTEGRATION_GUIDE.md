# Stage-2 Integration Guide

## Safe order
1. Run `Invoke-VIA-WorkOps-GapFill-ReviewOnly-v0200.ps1` without switches.
2. Review `MISSING` vs `EXISTS`.
3. Run with `-StageToOut` to copy candidates only into `WorkOps/out/_gapfill_staging/RUN_*`.
4. Compile staged Python candidates.
5. Run synthetic fixtures and then workstation fixtures.
6. Only after review, version-forward `via-workops.cmd` and `Invoke-VIA-WorkOps-All-v0105.ps1`; never edit frozen versions in place.
7. Register candidate engines in the append-only engine registry using new engine IDs assigned by the existing registry process.

## Suggested activation order
A. Unified Search (read-only)
B. Onboarding state generator (read-only)
C. Milestone Manager (append-only)
D. Timeline / Dependency (append-only links)
E. Closure Intelligence (candidate + explicit confirm)
F. Lesson Learned (candidate + explicit confirm)
G. Retention Manager (plan first; apply only after backup + explicit confirmation)

## Do not merge blindly
- Do not import the RC `PRJ-` ID family.
- Do not replace WOP/THR/DEC/MTG.
- Do not force Graph/FastAPI/DuckDB into the run-local canonical; keep them optional until an explicit product-line promotion.
