# VIA v0.4.0 validation report

## Decision

`ROTATION_T2_T3_REVIEW_CANDIDATE_49_BLOCKED_FIXTURE_REGRESSION_PASS`

The five-state historical rotation snapshot, 29/31/49 version isolation, candidate ingestion, evidence gates, Attention Share math, statistical primitives, walk-forward guards and offline dashboard pass automated validation. T1/M3 rotation truthing, candidate index generation and real-data activation remain blocked by design.

## Contract counts

| Check | Result |
|---|---:|
| Historical snapshot date | 2026-07-18 |
| Registry groups declared / materialized | 29 / not attached |
| Tracked rotation groups | 18 |
| Ignite / Diffuse / Overheat / Ebb / Dormant | 4 / 2 / 4 / 5 / 3 |
| Rotation T1 / index eligible | 0 / 0 |
| Controlled regression groups / membership | 31 / 149 |
| Candidate groups / membership / distinct tickers | 49 / 252 / 241 |
| Candidate index eligible | 0 / 49 |
| Market intelligence categories / items | 14 / 77 |
| VDF fetcher / network executions | 0 / 0 |
| Canonical mutations | 0 |

## Validation rounds

1. Full engine run: pass with the expected fail-closed/review Gate.
2. Rotation source contract: all 18 runtime rows match `VIA_Rotation_Snapshot_20260718_v0400.json`.
3. Append-only rerun: 18 persisted rows, second run appended 0; conflicting same-date rewrite is rejected.
4. Python compile and JSON parse: pass.
5. Unit, integration, leakage and contract suite: 30/30 pass.
6. Inline JavaScript syntax: pass.
7. Offline dependency scan: pass; no external script, stylesheet or Google Fonts dependency.
8. Browser smoke: `SKIP_NO_CHROMIUM` in this environment; the UAT script validates five state cards, 18 rows, 49 candidates, 31 classification cards, 149 members, human × append-only decisions and 390px overflow when Chromium is available.

## Evidence-honesty checks

- The five-state table is `SOURCE_REPORTED_T2_T3_UNVERIFIED`; no row is promoted to T1 or used by INDEX.
- The date 2026-07-18 is explicitly historical, not current.
- `tw_group_registry.json` and the claimed schema cross-check were not attached; only the declared count 29 is preserved.
- Hierarchical L1/L2/L3 values remain DEMO and ONE/FIS console values remain synthetic, estimated or NeedsFetch.
- The VDF attachment is treated as a U/I contract, not proof that a fetcher ran.
- Missing `pyarrow` in the release environment is recorded as `REVIEW_OPTIONAL_DEPENDENCY`; CSV outputs pass, while Parquet is produced after installing `requirements.txt`.

## Activation blockers

- VDF/M3 truthing has not converted the 18 rotation rows from T2/T3 to T1.
- No candidate group has complete threshold plus PCA/CCF/permutation evidence.
- Four candidate groups have no VDF metrics.
- `面板 / 6116` has conflicting name and role rows.
- `石英/頻率元件` has no exact 49-group taxonomy target.
- Candidate size buckets and capital-control styles require real market-cap and flow sources.
- The 31-group market, flow and backtest values are controlled fixtures.
- Chromium visual QA and Parquet emission were not executable in this environment.
