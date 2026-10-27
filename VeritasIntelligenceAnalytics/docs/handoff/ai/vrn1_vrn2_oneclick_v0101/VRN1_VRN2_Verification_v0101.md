# VRN-1 / VRN-2 操作員一鍵 v0101 · 容器實測紀錄(2026-10-20)

操作員令:「INTEGRATED INTO ONE CODE TO HANDLE ALL.」·「授權全自動完成到收尾 實測實際修正自動完成直到輸出結果驗證結果無誤於HTML U/I即收尾完成」。
一鍵程式碼 SHA-256 `b46148b9cf9d207b3e72ad9a7c3fd8e2c317aadc28c10b1818e36b7a5fa1c141`(`VRN1_VRN2_OneClick_v0101.md` 的 powershell 區塊)· 內含 VRN-2 一鍵 v0132 程式碼雜湊 `c68b66b0ddf4…`。

v0101 = v0100 + 該你手動做的也自己處理:VRN-1 倉不在 → 從 GitHub 複製 · 沒有 PowerShell 7 → winget 自動安裝 · 樣本夾自動找(`VRN1_SAMPLES` → `VIA_VRN_INPUT` → `C:\測試樣本報告`,兩邊讀同一批)·
總結多「要人判」(P21 待修的報告 · 待修清單在哪 · 有 `gh` 就加 VRN-1 倉 main 的 GitHub Actions 結果)。只呼叫兩邊自己的入口,不改任何一邊的程式 / 冊 / 號;VCGC / VDF 不碰。

| 情境 | 結果 |
|---|---|
| **VRN-1 倉不在**(只有 VIA 樹 · Downloads 是 v0131)· 貼「一行」(pwsh 7.4.6 · `-EncodedCommand`) | ① 綠「複製好了 · main 7693aee」· ② 綠 結束碼 0(取 v0132 · ⑦ 14 / 14 · ⑪ 錯值 0 · ⑫ 借到 VRN-1 `table.pivot_db` 事實 4,653 / 4,905)· ③ 綠(樣本夾自動用 `VIA_VRN_INPUT` · check 0 · run 0 · G23 借到 2 / 2 · G22 PASS · 收尾 完成)· 要人判:P21 8 / 14 與待修的 6 份 · 待修清單路徑 · VRN-1 倉 main 最近一次 Actions(failure)與去哪看 · NEXT 綠 |
| 再貼一次 | ① 綠 `main 7693aee → 7693aee` · ② 綠(啟動器已是 v0132 · ⑨ 已是最新)· ③ 綠 · VRN-1 倉仍乾淨 |
| 沒有 pwsh、沒有 winget、沒有 git | ① 紅「找不到 git」· ③ 紅「這台沒有 winget … 到 https://aka.ms/powershell 下載安裝」· 結束碼 1 · 不卡住 |
| winget 自動安裝 | **容器測不到**(Linux 沒有 winget / Windows PowerShell)· 程式碼依 winget 官方參數寫:`winget install --id Microsoft.PowerShell --exact --silent --accept-source-agreements --accept-package-agreements`,裝好用 `%ProgramFiles%\PowerShell\7\pwsh.exe` 直接接著跑 |

**收尾判準:輸出驗證無誤於 HTML U/I**(真 Chromium · 最後狀態 = 再貼一次之後):

| 頁 | 實測 |
|---|---|
| VRN-2 U/I `VRN2_UI_latest.html`(第一個分頁「驗證過的輸出」) | 35 / 35 · 獨立驗證寫回 4,905 筆:✓✓ 對位 4,905 · 人工核對 0 · ✗ 0 |
| VRN-2 PIVOT `pivot\VRN_Pivot_v0100.html` | 29 / 29 |
| VRN-1 驗證過的輸出 `VRN_Verified_Output_v0100.html` | 27 / 27 · 年度數據 1,686(逐欄證實 1,679 · 自動修正 7)· 剔除 40 附理由 |
| VRN-1 PIVOT `VRN_Pivot_v0100.html` | 29 / 29 |

實測抓到、改掉的:P21 一開始從 AutoTest 報告找(它在 MAIN 報告裡)→ 改讀 `VRN_Main_Report_v0100.json` · `gh` 的 `--jq` 參數嵌雙引號在 Windows PowerShell 5.1 會被弄壞 → 改成取 JSON 回來解析 ·
沒有 winget 時說明改成照實說(不說「安裝沒成功」)。

日誌:`logs_v0101.zip` · 測試工具:`tools_v0101.zip`(產生器 · 情境腳本 · U/I 實測腳本 · 不含 .ps1)。v0100(`vrn1_vrn2_oneclick_v0100`)照舊留著。
