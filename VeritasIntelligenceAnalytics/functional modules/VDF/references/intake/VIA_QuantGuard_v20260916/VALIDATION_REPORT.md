# VIA QuantGuard™｜Quant Engine PIT Replay Validation Report

## Result

The integrated Point-in-Time replay module and anti-lookahead test matrix passed:

```text
37 passed, 1 skipped locally (PostgreSQL service is CI-only unless `TEST_POSTGRES_DSN` is set)
```

The code also passed Python compilation and SSOT JSON validation through `scripts/verify_engine.sh`.

## Consolidated implementation

The replay orchestration is concentrated in `quant_engine/replay.py`. The module contains `PointInTimeStore`, `DuckDBPointInTimeStore`, `PostgresPointInTimeStore`, `DeterministicReplay`, `ReplayConfig`, `ReplaySession`, `ReplayManifest`, stable frame hashing, future-row guards, future-append invariance checks, and calendar-to-session conversion. VIA QuantGuard numerical regression is concentrated in `tests/test_quantguard_regression.py` with a versioned fixture: risk and stress values come from independent reference calculations, while factor values are reviewed golden baselines. Indicator mathematics remains in the existing core, risk, and statistics modules; the replay module is responsible for deciding which rows those modules are allowed to see.

## Test matrix

| Test group | Assertions |
|---|---|
| Revision visibility | A T+2 correction is hidden before its `available_at` and `confirmed_at`, then becomes visible afterward. |
| Release policy | `confirmed_only` excludes provisional data; `initial_release` can expose it after initial availability. |
| Future-row guard | Any row with `available_at > cutoff` raises an assertion. |
| Future append invariance | Appending a future observation does not change the historical snapshot hash. |
| Stable hashing | Reordering rows does not change the canonical frame hash. |
| Late US close | A US close after the Taiwan cutoff is excluded from the same Taiwan session. |
| Calendar replay | Next-session execution uses `open_utc` when present; final session has no execution row. |
| Deterministic replay | Replay emits only the requested current session, one manifest per session, and stable audit fields. |
| Manifest persistence | Replay manifests write valid JSON with policy and hash metadata. |
| DuckDB persistence | DuckDB adapter returns the same as-of rows as the memory store. |
| PostgreSQL persistence | CI service job runs the same adapter contract with `TEST_POSTGRES_DSN`. |
| Revision integrity | Duplicate global revision IDs and duplicate observation-version keys are rejected. |
| Data contract | Missing `confirmed_at` fails closed rather than silently assuming confirmation. |
| Existing engine regression | Technical indicators, risk metrics, cross-market example, governance, and feature matrix tests remain green. |
| VIA QuantGuard numerical regression | Independent golden values protect Sharpe, Max Drawdown, SMA, EMA, multi-factor composites, and stress scenarios with field-level tolerances. |
| DuckDB backtest CLI | A deterministic smoke test runs revision loading, PIT replay, Factor Composite, next-bar returns, risk metrics, manifests, and summary output. |

## Commands used

```bash
cd /home/ubuntu/quant_engine_mvp
PYTHONPATH=. pytest -q
python3 -m compileall -q quant_engine tests examples scripts
./scripts/verify_engine.sh
```

## User-test entry points

The focused replay suite is:

```bash
PYTHONPATH=. pytest -q tests/test_replay.py
PYTHONPATH=. pytest -q --strict-markers tests/test_quantguard_regression.py -m regression
PYTHONPATH=. pytest -q tests/test_replay.py -m anti_lookahead
PYTHONPATH=. pytest -q tests/test_replay.py -m postgres
```

The full suite is:

```bash
PYTHONPATH=. pytest -q
```

The implementation is designed to fail closed. A missing confirmation field, an unavailable future row, an invalid revision, or a future close in a Taiwan signal row is rejected rather than silently repaired.

The CI workflow is `.github/workflows/ci.yml`. It blocks a merge when the full suite, focused anti-lookahead suite, compilation, SSOT validation, or the PostgreSQL backend contract fails.
The commercial test-gate name is **VIA QuantGuard™**. Its tolerance policy is exact equality for categorical outputs, `1e-12` for deterministic cumulative values, and `1e-10` for rolling floating-point statistics unless a reviewed fixture version says otherwise.
