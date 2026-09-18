# VIA AI continuation contract

This directory is an overlay for the existing VIA SSOT and Registry. Never create a competing mother system, registry, allocator, runtime bridge, or database.

## Required execution order

1. Read `config/SYSTEM_CAPSULE.v0100.json`.
2. Read exactly one task context pack.
3. Resolve module IDs through `registry/ai_module_registry.v0100.json`.
4. Load only the files and symbols listed in the task pack.
5. Run AST and contract checks before edits.
6. Modify only owned paths/symbols.
7. Run the declared gates.
8. Write a handoff packet and Promote Plan.

## Hard gates

- Append-only identity and event history.
- No rename or deletion of existing physical engines.
- No direct promotion to canonical status.
- No automatic regrouping or deletion of accepted SSOT classifications.
- No database, Parquet, PDF, model, secret, full log, or full backtest upload.
- No two agents may edit the same path or symbol concurrently.
- A failed, missing, or unverifiable gate blocks activation.
- Preserve Adj price usage and existing VIA data semantics when financial modules are involved.

## Output contract

Every completed task must identify: task ID, module ID, base SHA, head SHA, changed paths, changed symbols, validations, unresolved risks, rollback instructions, next action, and expected hashes.

