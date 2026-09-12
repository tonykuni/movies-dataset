# VIA AI Workflow v0100 — Test Evidence

Base repository state inspected: `main@fc3f828489d190530e625a69d0df817f6ae578dd` (2026-09-09).

## Local deterministic checks

| Gate | Command | Result |
|---|---|---|
| Python compile | `python -m py_compile src/via_ai_workflow.py src/via_mother_system_bridge.py tests/test_via_ai_workflow.py` | PASS |
| Contract | `python src/via_ai_workflow.py validate` | PASS: 6 modules, 6 events, 30 AST nodes, 51 edges |
| Unit | `python -m unittest discover -s tests -v` | PASS: 10 tests |
| Instruction AST | `python src/via_ai_workflow.py instruction-ast` | PASS |
| Python AST | `python src/via_ai_workflow.py ast-index --root src` | PASS: 1 file, 0 parse errors |
| JSON parse | Parse every package `*.json` with Python `json` | PASS: 18 files |
| Mother-system bridge proposal | `python src/via_mother_system_bridge.py selftest` | PASS |

## Repository regression discovery

The first remote layout placed the candidate bridge in the live registry. The existing MasterControl regression correctly failed because the generated module count changed from 110 to 111 while the tracked HTML remained at 110. The bridge was therefore moved back into the versioned package as `REGISTRATION_PROPOSAL`; no live-registry or tracked MasterControl mutation is part of this architecture-only change.

## Covered behavior

- Six-layer manifest and dependency AST validation.
- Strict unknown-property rejection.
- Real Python AST symbol/call extraction.
- Symbol-only context extraction within a token budget.
- Database and binary artifact rejection from AI context packs.
- Append-only event ledger, monotonic allocation and non-overlapping leased IDs.
- Fail-closed handoff: `ready_for_review` requires every gate to pass.
- Bridge discovery of registry, workflow and database contract.

## Environment note

PowerShell was not installed in the local Linux verification container. The GitHub Actions workflow includes a `pwsh` smoke test on `ubuntu-latest`; its result is the authoritative PowerShell execution evidence for the pull request.
