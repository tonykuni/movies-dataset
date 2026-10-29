# VRN-1 / VRN-2 操作員一鍵 v0109 · 容器驗證(2026-10-29)

v0109 = v0108 的程式碼只改三處:② 發行夾 `vrn2_release_v0147` → `vrn2_release_v0148`、`$H2` → VRN-2 一鍵 v0148 程式碼 SHA-256(`f49cc54d071d`)、橫幅「操作員一鍵 v0108」→「v0109」;歷史子句照舊。md 的歷史段落照 v0107 原文還原(v0108 的 md 把「v0107 = v0106 …」等段落誤寫成「v0108 = …」,v0108 檔不改)。

| 檢查 | 結果 |
|---|---|
| pwsh 7.4.6 語法剖析(Run-VRN1-VRN2-v0109.ps1 · boot_pair109.ps1)| 見 `vrn2_release_v0148/logs_v0148.zip` 的 `pscheck148.log` |
| 本段程式碼 SHA-256 = boot 裡的 `$H` | 同上 |
| 一行(-EncodedCommand)解碼 = boot | 同上 |
| `$H2` = `VRN2_OneClick_v0148.md` 程式碼 SHA-256 | 同上 |
| 橫幅版號 | `操作員一鍵 v0109` |
| 本地實測一輪 v0100 的 `$H_OP` = 本段程式碼 SHA-256 | 同上 |

沒有 .ps1 進倉:一鍵程式碼只在本夾的 md 裡,`tools_v0109.zip` 是容器測試用副本。
