# VIA Toolchain Bundle — 2026-08-30

Nine tools built across this session, all updated to the same standard and
re-checked by the PowerShell repair engine that is itself part of the bundle.

Self-scan result: **0 parse errors, 0 parallel-fixable findings, 2 remaining
MEDIUM notes** (both are `Start-Process` calls used only to open an HTML
report, which is the permitted pattern).

---

## What changed in this update

Every earlier deliverable was scanned by `Invoke-VIA-PSRepair-Accel20-v0101`
and the violations it found in my own code were fixed:

| Fix | Files touched |
|---|---|
| `New-Object System.Collections.Generic.List[T]` → `[...]::new()` | 43 sites across 5 scripts |
| Sequential `ReadToEnd()` on two redirected pipes → concurrent async reads | 3 scripts |
| Added `Get-CleanPath` so stray quotes in a parameter cannot poison a path | 4 scripts |

The `GENERIC_LIST` pattern throws "Argument types do not match" when the list
is later converted with `@()`. The sequential `ReadToEnd()` pattern deadlocks
once a child fills one pipe buffer while the parent is blocked reading the
other. Both were on the accumulated-lessons list and both were still present
in my own scripts until this pass.

---

## Contents

### Governance and repair

**`Invoke-VIA-PSRepair-Accel20-v0101.ps1`**
PowerShell multi-round AST repair engine, 20 accelerators. Pure PowerShell,
so no Python environment can block it. Parallel runspaces in chunks of 25 with
progress refreshed at every chunk boundary. Only `Parallel-Fixable` findings
are auto-applied; every edit is anchored to an exact AST extent offset and the
file is re-parsed in memory before it reaches disk. A fix that would introduce
a parse error is rejected and the original left untouched.

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\Invoke-VIA-PSRepair-Accel20-v0101.ps1 `
  -Root '<tree>' -OutRoot 'C:\VIA\VIA_PSRepair'
# add -GoToken GO_v1 to apply, -IncludeSnapshots to scan rollback copies too
```

**`Invoke-VIA-PostRepairVerify-Accel20-v0101.ps1`**
Read-only verification: did the woken tests pass, did line endings flip, are
the rollback snapshots redundant, which scripts still fail to parse. Runs a
harness self-check first — a throwaway trivial test — so a broken runner is
reported as `HARNESS_SUSPECT` instead of silently printing zeros.

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\Invoke-VIA-PostRepairVerify-Accel20-v0101.ps1 `
  -Root '<tree>' -PythonExe 'C:\Users\tonyk\envs\via_vrn4\Scripts\python.exe' `
  -OutRoot 'C:\VIA\VIA_PostRepairVerify' -SkipHash
```

**`VIA_DefTestAudit_v0100.py`**
Finds and repairs `def def_test_x()` functions, which pytest can never collect.
Nested ones are reported as unfixable rather than renamed pointlessly. Every
edited file keeps a `.predeftest.bak` sibling.

```powershell
& python VIA_DefTestAudit_v0100.py --root '<tree>' --out 'C:\VIA\VIA_DefTestAudit'
# add --apply --go-token GO_v1 to apply
```

### Import

**`Invoke-VIA-MotherImport-Accel20-v0101.ps1`** + **`VIA_Accel20_Analyzer_v0100.py`**
Stage-2 placement engine, 20 accelerators, three panoramic rounds. Dry-run by
default; `-GoToken GO_v1` applies. Placement never overwrites — a name clash
with different content becomes a `__vN` sibling. The two files must sit in the
same folder.

**`IMPORT_20260830N.json`** — batch N manifest in the existing
`import_manifests/` schema, for `Invoke-VIA-ImportStaging.ps1` stage 1.

**Known limitation:** routing is per-file, so a Python package with a
`pyproject.toml` gets scattered across subsystem folders. Move packages by hand
until `-PackageMode` exists.

### Documents

**`Invoke-VIA-VRN-FourEngineBatch-v0101.ps1`** + **`VRN_BatchFourEngine_v0100.py`**
Batch driver for VRNFourEngineSuite. Adds what the suite lacks: a batch layer
(the orchestrator takes one file per run) and a markitdown bridge for `.docx`,
which the suite rejects outright. Reconciles freshly extracted figures against
a prior text-corpus extraction so disagreements surface instead of hiding.
Same folder for both files.

**`Invoke-VIA-MarkItDown-v0101.ps1`**
Self-extracting markitdown engine, all optional extras probed and reported as
ACTIVE or DORMANT. Cloud tiers stay dormant until an endpoint is configured.
Outputs are append-only and carry an evidence tag.

### VDF

**`test_VDF_TW_AllStock_Excellence_BacktestReportEngine_v035_FIXED.py`**
The v035 test with its function renamed from `def_test_cny_rule` to
`test_cny_rule`. Verified: **1 passed**, all seven checks green. The lunar-new-
year combined YoY and low-base gate logic is correct — it had simply never been
executed, because pytest could not collect a function named `def_test_*`.

---

## Verified on the target machine

- def_test repair applied: 52 files with the defect, 47 repaired, 5 nested and
  left alone
- `VIA_EnvManager.py` → 10 passed, `VIA_RegistryCore_v1.py` → 4 passed
  (both had reported "no tests ran" before the rename)
- PS repair applied: 89 files edited, 89 verified by re-parse, 0 rejected
- Line endings safe: `core.autocrlf=true`, diffs are localised, not whole-file
- Rollback snapshots: **715 unique, 17 redundant, 13.3 MB** — they are not
  spare copies and should not be deleted

## Outstanding

- **7 PowerShell scripts do not parse.** Purely mechanical, no judgement needed.
  One of them, `Install-GenericLayoutEngine-All.ps1` line 67, ships inside the
  GenericLayoutEngine package itself.
- **Woken tests are failing.** In sandbox: 35 failures and 8 collection errors
  across 25 files, concentrated in `SectorFlow` and `GroupingIndexRotation`.
  These were invisible before the rename. Failures here are expected and are
  the point of the exercise.
- **24 environments report unhealthy** and `NO_HEALTHY_MANAGED_ENV_AVAILABLE`
  blocks installs through EnvManager. The four timeouts look like scan-duration
  limits rather than broken environments, so the gate is likely fail-closed on
  bad input. Separate track.

## Governance

Every tool is dry-run by default and needs an explicit `GO_v1` token to write.
Nothing deletes. Edits keep `.bak` siblings. Accelerators are labelled EXACT
when they report a measurement and HEURISTIC when they report a proxy — hydra
risk is import fan-in and fan-out, not a proof of blast radius, and subsystem
routing is keyword matching that should be confirmed before it is trusted.
