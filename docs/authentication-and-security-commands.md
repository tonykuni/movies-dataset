# Authentication and security commands (main branch)

The root movie demo has no application login. `streamlit_app.py` reads a local CSV,
filters it using Streamlit widgets, and displays charts. The separate VIA control
plane under `VeritasIntelligenceAnalytics/` has a local HTTP bridge; its CSRF
mechanism is request protection, **not** user authentication or licensing.

## VIA request flow

1. `CGC_MDL095_DeckServer` binds `127.0.0.1:8765` and creates a random
   `CSRF_TOKEN` for that server process. A served HTML response receives the
   token in a `via-csrf` meta tag; the checked-in UI file is not rewritten.
2. The page sends a JSON `POST` to an allowlisted mutation path such as `/run`,
   with `X-VIA-CSRF`. The server rejects an untrusted Host, a wrong `Origin`,
   a `Sec-Fetch-Site` other than `same-origin`, and a missing/wrong token.
   It compares token strings with `hmac.compare_digest`, checks the body size
   and type, validates task inputs, and starts a selected subprocess.
3. Read-only GET endpoints such as `/status` and `/api/*` do not use this POST
   check. Mutation GET endpoints are rejected. The `/probe` endpoint is an
   intentionally minimal, cross-origin-readable liveness probe. The bridge
   has no user accounts, session cookies, password exchange, or bearer login.
4. Network workers separately inspect `VIA_NET_CONSENT` and
   `VIA_SCRAPE_CONSENT`. These are operator consent switches, not credentials.
   `via-gates` shows their state without displaying their current values.

## API credentials and audit

`VDF_ENG074_FredMacroSSOT` checks `FRED_API_KEY`, then the ignored local
`output_hub/mega/.fred_api_key`, then prompts on an interactive terminal.
It can write the key in that local plaintext file; `--fred-key` also places a
key in the command line. FRED API requests put the key in a query parameter.
Keep full URLs and command lines out of diagnostic output. The product gate's
G6 scanner detects known key fingerprints in repository text. It is an audit,
not an access grant or proof that no other secret can appear.

## One read-only command

From the repository root:

```powershell
python scripts/via_auth_audit.py
python scripts/via_auth_audit.py --json
```

This combines the inspection formerly spread across `via-gates`,
`via-productgate` G6, the bridge source and the FRED worker into one short
report. It selects the highest numbered active source for each family, never
executes them, never touches consent settings, and never reads the key file.
`PRESENT` means the expected source markers were found; `REVIEW` means the
source or a marker is missing, with exit code 2. Static inspection does not
replace the bridge's own HTTP selftest or the product gate's full audit.

## Source pointers

- `streamlit_app.py`; root `README.md` (movie demo and local UI).
- `VeritasIntelligenceAnalytics/supportive modules/registry/CGC_MDL095_DeckServer_v0159.py` (local request flow and selftest).
- `VeritasIntelligenceAnalytics/Register-VIA-Commands-v0242.ps1` (`via-gates`, `via-productgate`, `via-netbench`).
- `VeritasIntelligenceAnalytics/supportive modules/network/SUP_MDL740_NetUnified_v0113.py` (network consent checks).
- `VeritasIntelligenceAnalytics/functional modules/VDF/engine/VDF_ENG074_FredMacroSSOT_v0102.py` (key sources and FRED calls).
- `VeritasIntelligenceAnalytics/supportive modules/registry/CGC_MDL133_ProductGate_v0101.py` (G6 key fingerprint check).
