# IT Inputs Required for LiveRead

For the default Offline acceptance: **none**.

For `LiveRead`:
- Microsoft Entra application/client ID
- Tenant ID or approved authority
- delegated signed-in-user mail read permission
- IT ticket/change/reference
- company policy approval for desktop/public-client authentication

WorkOps default live-read scope:
- `Mail.Read`
- `User.Read`

For optional Draft-only validation:
- delegated `Mail.ReadWrite`
- a test recipient address
- no `Mail.Send` is requested by WorkOps
- no send endpoint is called

The application remains bound to `127.0.0.1`.
