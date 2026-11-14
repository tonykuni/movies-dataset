# VIA VCGC · AI handover · v0106.4

## Gate / status
- Candidate: v0106.4 CANDIDATE
- Actual system gate: RED / BLOCKED
- Native runtime: NOT_RUN
- Completion: NOT_OBSERVED; no completion is claimed.
- Formal registration: false
- Production: false
- Tony-NB: UNAVAILABLE · original snapshot/source boundary
- Owner action: use the native gate scope below; confirm owner-approved source, connection, and receipt inputs before registration or runtime activation.
- Next gates: resolve each owned RED blocker → owner-approved native install/registration scope → native runtime execution → native test/output receipt → integration/registration evidence. No gate is claimed complete here.

## Exact owned RED blockers

### OBS-0001 · VCGC
- id: OBS-0001
- name: VCGC
- category: systems
- error_detail: No VCGC connector/server or owner registry receipt; TokenEngine add-on tested locally only
- version: v0105
- source_sha256: 802b5ef8ceaf0db54f5b9454453970e98229d8e3ba5cdb0bc2b4b24d81920e00
- next action tied to native gate: obtain owner-approved native scope and receipt for this blocker; do not infer completion from uploaded/static evidence.

### OBS-0186 · VCGC MCP server/connector
- id: OBS-0186
- name: VCGC MCP server/connector
- category: environment
- error_detail: 未提供可核實的VCGC MCP URL/stdio部署指令、憑證與實機root；通用MCP可用不等於VCGC已接通。
- version: v0105
- source_sha256: 802b5ef8ceaf0db54f5b9454453970e98229d8e3ba5cdb0bc2b4b24d81920e00
- next action tied to native gate: obtain owner-approved native scope and receipt for this blocker; do not infer completion from uploaded/static evidence.

### OBS-0194 · Old exclusive-replacement Token policy conflicts with latest additive rule
- id: OBS-0194
- name: Old exclusive-replacement Token policy conflicts with latest additive rule
- category: conflicts
- error_detail: Do not auto-apply uploaded old replacement policy. Keep existing VCGC installer/EnvManager/InstallGate/Token tools unchanged.
- version: v0105
- source_sha256: 1f18899be1bc2253fefe44ada746e200e5099c6c34f625fe6780d4edc8535ffb
- next action tied to native gate: obtain owner-approved native scope and receipt for this blocker; do not infer completion from uploaded/static evidence.

## Current connection observation
- observed_at_utc: 2026-11-06T04:48:52.807717+00:00
- status: PASS
- scope: LOCAL_STDIO_PINNED_CANDIDATE
- receipt: artifacts/mcp_stdio_smoke_v0106_20261106_verified.json
- live_vcgc_connected: false
- receipt hashes observed in pinned attachments:
  - VIA_MatrixGovernance_AllInOne_v0100.py=bb8d5911a0e15765b9a4e0ad9d01a6104a78a044878db71b509b326f1f80b7b0
  - VIA_MatrixGovernance_QA_v0100.html=5d6ff4c59ca2dea122f86839e396d6abca22cfdb9ce8c63c126faf8ba7e7ac8b
  - VIA_MatrixGovernance_README_v0100.md=f1d25131e9b11718e1a453f054c272baf27e37c9cb71894a2089b97e6e2b6338

## Evidence scope and pins
- Owned filter: `r.system == system` exactly
- Owned rows: 22
- Owned tests: 3 · test_status/output_verification/receipt_keys remain source-scoped.
- Categories: systems, io, commands, files, environment, policy, conflicts, requirements, tests
- Model gzip: c3b2b84d16abbe3ae1ab8984dc6fd933b6aceef18372d1fea16d94d694691ff1 · raw: c1e5fe44484b746574704cadc1fff727f1f6166d86880bd50cb9542883d000c4
- Supplemental observations are separate, source-pinned, and never promoted to native/test counts.
- Full JSON/MD exports retain all raw rows; DISPLAY_MATRIX only adds required-field NOT_OBSERVED display values.
- observations: data/subsystem_live_observations_v0106.json · sha256=f7fbee5e7307540d98dece8a43d98d25318e676c48fcd2644e19de3ed5724e70 · bytes=1953
- token_context: artifacts/subsystem_token_context_v0106.json · sha256=7e1f7fa0ec9536d29cc1ec1a43c849db2fe9cfbfb2e6c4939b75a4c8b427e41c · bytes=2533
- token_tools: artifacts/token_tools_v0106_20261106.json · sha256=b57ec28a59e235199cf8d6f7faf2d902cf431ada7229676e55041c86864554be · bytes=23585

## Boundaries
- GitHub actual authenticated read-only health is supplemental only; no Git writes were performed.
- No provider, database, network, fetch, WebSocket, shell, or native engine call is made by this standalone page.
- Uploaded fixtures, static AST, and token observations are not final/live execution.
- Evidence Relationship Map is not a verified runtime flow; only explicit source/target IDs can create DECLARED edges, otherwise OFF.
