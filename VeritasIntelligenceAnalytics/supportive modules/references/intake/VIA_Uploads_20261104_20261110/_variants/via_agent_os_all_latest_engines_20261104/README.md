# VIA Agent OS — All Latest Engines (2026-11-04)

**Engine version:** 1.0.2 Hardened  
**Archive scope:** current allowlist only; 26 ZIP members (25 payload files plus `MANIFEST.json`). Superseded Python versions, old dashboards, backups, bytecode and temporary scripts are excluded.

## Contents

- `src/via_agent_os_unified_readonly_hardened.py` — main single-file VIA Agent OS: 8 Skills, Token/context engine, bounded AST review, SDD validation, local MCP stdio adapter, read-only repository/status surfaces.
- `vcgc_remote_preflight.py` — local profile compliance checker; optional explicitly authorized TLS-only probe and local `tools/list` exact-name comparison. It is not an OAuth/MCP client.
- `test_vcgc_remote_preflight.py` — offline/mock tests for the preflight helper.
- `dashboard/` — standalone offline interactive 1.0.2 Dashboard.
- `config/` and `docs/` — credential-free examples and VCGC security/setup guide.
- `reports/` — current test/profile/dependency artifacts plus the new self-contained Skills/Token/Preflight/Performance report, PNG charts, and JSON data.
- `assets/` — current architecture/concurrency diagrams and release preview assets.

## Quick start

Run from the extracted directory:

```bash
python3 -m py_compile src/via_agent_os_unified_readonly_hardened.py vcgc_remote_preflight.py test_vcgc_remote_preflight.py
python3 src/via_agent_os_unified_readonly_hardened.py selftest
python3 src/via_agent_os_unified_readonly_hardened.py skills test
python3 test_vcgc_remote_preflight.py
```

The verified current results are 48/48 selftests, 27/27 acceptance cases across 8 Skills, and 20/20 offline preflight tests. Re-run the commands locally before deployment.

Open `dashboard/via_agent_os_unified_readonly_dashboard.html` or `reports/via_agent_os_v1_0_2_skill_token_preflight_performance_report.html` directly in a browser. Both are local snapshots; no server/CDN is required. The analytics report clearly marks per-Skill provider usage as unavailable and labels shared token fixtures as synthetic only.

## Remote VCGC boundaries

The included `config/VCGC_REMOTE_PROFILE.example.json` intentionally contains invalid placeholders and no credentials. Copy it to a private local file and replace placeholders only with owner-confirmed non-secret values. Keep `enabled=false` and the deny-by-default safety flags. Start with:

```bash
cp config/VCGC_REMOTE_PROFILE.example.json VCGC_REMOTE_PROFILE.json
chmod 600 VCGC_REMOTE_PROFILE.json
python3 vcgc_remote_preflight.py --config VCGC_REMOTE_PROFILE.json
```

This checks local JSON/policy only and makes zero network requests. `--tools-json` reads a sanitized local host-exported `tools/list` document and checks exact names; it does not call tools or prove semantic read-only behavior. `--tls-check` performs DNS/TCP/TLS network activity and must only be used after the endpoint and egress are authorized; it sends no HTTP, OAuth credentials, MCP message or tool call. OAuth and remote MCP authentication remain in the selected Agent host. Do not put access/refresh tokens, cookies, API keys or authorization headers in this archive or profile.

## MCP and concurrency

The local MCP adapter uses stdio and sequential synchronous dispatch with bounded message/tool/runtime/output budgets. The remote VCGC preflight helper is separate and does not connect to a remote MCP service. Per-Agent OAuth credentials must remain separate.

## Token/performance interpretation

The package contains no production provider usage pairs for any of the 8 Skills. Synthetic token fixtures are deterministic tests, not provider billing or actual VCGC savings. `tracemalloc` peaks are not process RSS/PSS; the profile is not a full 1,500-file/128-MiB repository stress test. See the report and dependency review for detailed limits and measurements.

`MANIFEST.json` records size and SHA-256 for every payload file; the manifest does not hash itself.
