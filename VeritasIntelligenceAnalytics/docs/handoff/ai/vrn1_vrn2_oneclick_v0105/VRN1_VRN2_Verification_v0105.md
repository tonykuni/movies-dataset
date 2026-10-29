# VRN-1 / VRN-2 操作員一鍵 v0105 · 容器驗證(2026-10-29)

v0105 = v0104 的程式碼只改三處:② 發行夾 `vrn2_release_v0143` → `vrn2_release_v0144`、`$H2` → VRN-2 一鍵 v0144 程式碼 SHA-256(`9adeab66d446`)、橫幅「操作員一鍵 v0104」→「v0105」;其餘(① VRN-1 倉 pull / clone · ③ VRN-1 MAIN · ④ 摘要)一字不改。本段程式碼 SHA-256 `c1dfe6d2f676`。

| 檢查 | 結果 |
|---|---|
| pwsh 7.4.6 語法剖析(Run-VRN1-VRN2-v0105.ps1 · boot_pair105.ps1)| 0 錯 |
| 本段程式碼 SHA-256 = boot 裡的 `$H` | 相符 |
| 一行(-EncodedCommand)解碼 = boot | 相符 |
| `$H2` = `VRN2_OneClick_v0144.md` 程式碼 SHA-256 | 相符 |
| 橫幅版號 | `操作員一鍵 v0105` |
| 本地實測一輪 v0100 的 `$H_OP` = 本段程式碼 SHA-256 | 相符 |
| 歷史子句 | 「v0143 = 啟動器 v0143 + runtime v0142 不動」保留原字(build 腳本對這一句有斷言)|

VRN-2 一鍵 v0144 本身的容器證據(自測 · 沙盒 19 份 · DuckDB 正式路徑 · pwsh 情境 first / again / tamper)在 `vrn2_release_v0144/VRN2_Verification_v0144.md`。
桌機實跑:由本地實測一輪 v0100 的一行帶起(③),本輪的證據在操作員貼回的 `VRN2_PasteBack_<時間>.zip`;桌機還沒跑 v0144。
