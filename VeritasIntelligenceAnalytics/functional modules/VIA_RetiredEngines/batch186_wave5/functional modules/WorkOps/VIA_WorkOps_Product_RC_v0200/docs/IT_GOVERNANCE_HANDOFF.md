# Veritas WorkOps — IT / Security Handoff

## Default architecture
- Local application server: `127.0.0.1:8775`
- Microsoft Graph delegated access as the signed-in user.
- Default mail permission target: `Mail.Read` + `User.Read`.
- Optional draft creation: `Mail.ReadWrite`; still no send endpoint in WorkOps.
- No application secret is stored by WorkOps for the desktop public-client flow.
- MSAL token cache is local and excluded from WorkOps backups.
- Outlook mailbox move/delete is disabled in this release.
- Critical actions (project confirmation, escalation, committed date changes, closure, draft creation) are explicit human-confirmation gates.

## IT onboarding
1. Review requested delegated permissions.
2. Register/approve a Microsoft Entra public client / desktop application according to company policy.
3. Provide Client ID and tenant identifier to the user.
4. User enters the values in WorkOps Setup.
5. User acknowledges the IT ticket/reference before enabling sync.
6. First authentication uses Microsoft identity UI / device code flow.
7. WorkOps stores normalized local work events only within the configured local profile.

## Data boundaries
- Raw email event cache: local.
- SSOT: local DuckDB/Parquet when available.
- Draft creation, if enabled, creates an Outlook draft only.
- Automatic sending is disabled.
- Restore is staged into a new folder and never overwrites canonical data automatically.

## Evidence for review
- `out/diagnostics.json`
- `out/diagnostics.html`
- `config/privacy_policy.json`
- `config/outlook_graph.json`
- `registry/VIA_Module_Registry.json`
- `out/module_registry_snapshot.json`
