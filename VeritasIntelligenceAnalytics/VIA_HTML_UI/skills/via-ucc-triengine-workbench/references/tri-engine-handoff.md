# VIA TriEngine handoff

## Engine roles

| Engine | Role | Typical inputs | Typical outputs |
|---|---|---|---|
| E1 / VFX | Specification conversion and content extraction | HTML, Markdown, Office, CSV, JSON, PDF | Markdown, Universal Content IR, component specs, topic matrix |
| E2 / VNL | Natural-language normalization, classification, summaries, knowledge handoff | Markdown, text, JSON | refined text, category results, knowledge graph, handoff bundle |
| E3 / VES | Program analysis, standardization, duplication grouping, safe scaffold generation | Python, JavaScript, TypeScript, PowerShell | inventory, standardized scaffold, AI handoff, append-only store |

## Routing

Prefer explicit routing for overlapping formats. Markdown/text/log inputs may be processed by E2 first and E1 second; JSON is extracted by E1 before optional E2 processing; source code is routed to E3. Never infer that a file is safe to execute merely because it is routable.

## Mount contract

Use `mounts/<name>/mount.json` with at least:

```json
{
  "contract": "VIA_MOUNT_MANIFEST/1.0",
  "id": "tool_name",
  "engine": "E1|E2|E3",
  "language": "py|js|ps|exe",
  "free_local": true,
  "entry": {"kind":"...","cmd":["..."]},
  "inputs": [".html"],
  "outputs": ["{out}/{stem}.md"],
  "health": ["..."],
  "license": "MIT"
}
```

The hub should discover, validate, probe, register, and run mounts through declared commands. It should not install packages, download code, or execute untrusted source during inspection. Missing tools should degrade to a visible `MISSING` status.

## Repeatable commands

The supplied Python hub supports `status`, `route`, `run`, `pipeline`, `mount list|probe|run`, `init-mounts`, and `selftest`. The PowerShell wrapper supports the same commands and can pass `-Deep` for engine health checks. Keep outputs in a chosen local directory and record append-only execution envelopes.
