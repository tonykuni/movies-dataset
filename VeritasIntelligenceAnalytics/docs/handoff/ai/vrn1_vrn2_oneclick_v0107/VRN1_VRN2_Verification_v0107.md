# VRN-1 / VRN-2 操作員一鍵 v0107 · 容器驗證(2026-10-29)

v0107 = v0106 的程式碼只改三處:② 發行夾 `vrn2_release_v0145` → `vrn2_release_v0146`、`$H2` → VRN-2 一鍵 v0146 程式碼 SHA-256(`9f7490806d18`)、橫幅「操作員一鍵 v0106」→「v0107」;歷史子句(v0106 · ② 改指 VRN-2 一鍵 v0145 …)照舊。

| 檢查 | 結果 |
|---|---|
| pwsh 7.4.6 語法剖析(Run-VRN1-VRN2-v0107.ps1 · boot_pair107.ps1)| 0 錯 |
| 本段程式碼 SHA-256 = boot 裡的 `$H` | 相符 |
| 一行(-EncodedCommand)解碼 = boot | 相符 |
| `$H2` = `VRN2_OneClick_v0146.md` 程式碼 SHA-256 | 相符 |
| 橫幅版號 | `操作員一鍵 v0107` |
| 本地實測一輪 v0100 的 `$H_OP` = 本段程式碼 SHA-256 | 相符 |

證據:`vrn2_release_v0146/logs_v0146.zip` 裡的 `pscheck146.log`(雜湊鏈全 True)。沒有 .ps1 進倉:一鍵程式碼只在本夾的 md 裡,`tools_v0107.zip` 是容器測試用副本。
