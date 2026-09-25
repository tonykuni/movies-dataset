# VIA handover 2026-09-26 · restore drill

Door: `via-envgov`. No install was run.

## What the drill showed

- LKGC latest `20260919_034027_2360` is RED. 43 envs. 30 history files.
- Candidate `20260922_220607_7600` was not promoted: 146 conflicts (7 accepted residuals do not count). Base holds 70 blocked-family packages, including accelerate, albucore, albumentations, blis, camelot-py.
- `via-envgov resume --no-tools` read that candidate and wrote `VIA_Reports/env_governance/RESUME_latest.ps1`. State OK means the plan was written. It does not mean the machine is green.
- 43 records are READY to fill. A full-environment success record has never existed.
- Stale this run, old record kept: `via_vap_312` (2 conflicts), `via_vdf_312` (2 conflicts).
- The plan also lists retired and rollback copies (`via_core.retired-20260914_111946`, `via_core_312__rb20260813_011954`, `via_extract_312__rb20260813_011954`) and unprefixed names (`camelot_311`, `paddle_311`, `vmt_pm`). Do not fill those.

## Not done

- `resume --approve`
- `rollback --execute`
- `recover --execute`
- `--approve-remove`
- pasting `RESUME_latest.ps1`

`uv pip sync` inside that file stays commented. A line without `#` is a failed drill.

## Next

Fix or leave the two stale family envs before any install. Do not stack packages on this base. Code restore remains Git, not this lock.
