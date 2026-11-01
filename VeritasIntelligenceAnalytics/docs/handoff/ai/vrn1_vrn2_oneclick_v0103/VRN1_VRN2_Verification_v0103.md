# VRN-1 / VRN-2 操作員一鍵 v0103 · 容器核對紀錄(2026-10-28)

v0103 = v0102 的程式碼只改兩個常數與註解:`$P2` → `vrn2_release_v0142`、`$H2` → VRN-2 一鍵 v0142 程式碼雜湊 `587291dca3c5…`、讀的檔名 → `VRN2_OneClick_v0142.md`;① VRN-1 倉 / ③ VRN-1 MAIN / ④ 總結與 v0102(Codex #564 四條都在)逐字相同。
本段程式碼 SHA-256 `46f47a48a67b…`(`VRN1_VRN2_OneClick_v0103.md` 的 powershell 區塊);一行(boot)核對的就是它。

| 核對(pwsh 7.4.6 · 容器) | 結果 |
|---|---|
| `Run-VRN1-VRN2-v0103.ps1` / `boot_pair103.ps1` PowerShell 語法剖析 | 0 錯誤 |
| md 的 powershell 區塊雜湊 = boot 裡的 `$H` | True |
| 一行(-EncodedCommand)base64 解回 = boot | True |
| 操作員程式裡的 `$H2` = `VRN2_OneClick_v0142.md` powershell 區塊雜湊 | True |
| VRN-2 一鍵 v0142 的 `$Want` = `VRN2_Closeout_v0142.zip` SHA-256 | True |
| VRN-2 一鍵 v0142 本身 | 一鍵情境(pwsh · 第一次從假 GitHub 下載套件 → 再貼 → 竄改啟動器)見 `vrn2_release_v0142/VRN2_Verification_v0142.md` §5 |

沒有宣稱的:本輪沒有在容器重跑整段操作員一鍵(VRN-1 倉複製 + VRN-1 MAIN 那兩段與 v0102 逐字相同,v0102 的容器實測見 `vrn1_vrn2_oneclick_v0102/VRN1_VRN2_Verification_v0102.md`);Windows 桌機實跑由操作員貼回。
