# VRN-1 / VRN-2 操作員一鍵 v0110 · 容器驗證(2026-10-29)

v0110 = v0109 的程式碼只改四處:② 發行夾 `vrn2_release_v0148` → `vrn2_release_v0149`、`$H2` → VRN-2 一鍵 v0149 程式碼 SHA-256(`001d1197308f`)、橫幅「操作員一鍵 v0109」→「v0110」、② 的步驟名 / 檔名 v0148 → v0149;歷史子句與 md 歷史段落照舊。

| 檢查 | 結果 |
|---|---|
| pwsh 7.4.6 語法剖析(Run-VRN1-VRN2-v0110.ps1 · boot_pair110.ps1)| 見 `vrn2_release_v0149/logs_v0149.zip` 的 `pscheck149.log` |
| 本段程式碼 SHA-256 = boot 裡的 `$H` | 同上 |
| 一行(-EncodedCommand)解碼 = boot | 同上 |
| `$H2` = `VRN2_OneClick_v0149.md` 程式碼 SHA-256 | 同上 |
| 橫幅版號 | `操作員一鍵 v0110` |
| 本地實測一輪 v0100 的 `$H_OP` = 本段程式碼 SHA-256 | 同上 |

沒有 .ps1 進倉:一鍵程式碼只在本夾的 md 裡,`tools_v0110.zip` 是容器測試用副本。
