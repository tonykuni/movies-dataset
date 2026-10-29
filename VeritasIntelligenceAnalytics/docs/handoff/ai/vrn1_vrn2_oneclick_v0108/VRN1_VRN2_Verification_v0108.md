# VRN-1 / VRN-2 操作員一鍵 v0108 · 容器驗證(2026-10-29)

v0108 = v0107 的程式碼只改三處:② 發行夾 `vrn2_release_v0146` → `vrn2_release_v0147`、`$H2` → VRN-2 一鍵 v0147 程式碼 SHA-256(`5358a2715209`)、橫幅「操作員一鍵 v0107」→「v0108」;歷史子句(v0107 · ② 改指 VRN-2 一鍵 v0146 …)照舊。

| 檢查 | 結果 |
|---|---|
| pwsh 7.4.6 語法剖析(Run-VRN1-VRN2-v0108.ps1 · boot_pair108.ps1)| 見 `vrn2_release_v0147/logs_v0147.zip` 的 `pscheck147.log` |
| 本段程式碼 SHA-256 = boot 裡的 `$H` | 同上 |
| 一行(-EncodedCommand)解碼 = boot | 同上 |
| `$H2` = `VRN2_OneClick_v0147.md` 程式碼 SHA-256 | 同上 |
| 橫幅版號 | `操作員一鍵 v0108` |
| 本地實測一輪 v0100 的 `$H_OP` = 本段程式碼 SHA-256 | 同上 |

沒有 .ps1 進倉:一鍵程式碼只在本夾的 md 裡,`tools_v0108.zip` 是容器測試用副本。
