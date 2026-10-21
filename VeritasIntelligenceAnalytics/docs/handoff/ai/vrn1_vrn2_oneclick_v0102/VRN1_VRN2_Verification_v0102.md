# VRN-1 / VRN-2 操作員一鍵 v0102 · 容器實測紀錄(2026-10-21)

操作員令:「ONE CODE TO HANDLE ALL.」(v0136 合併 MAIN 之後)。
一鍵程式碼 SHA-256 `df89e02bac2d029d2d71dea0ef3544fbdb82c61c5eb2b85807801f04e1f28a18`(`VRN1_VRN2_OneClick_v0102.md` 的 powershell 區塊)· 內含 VRN-2 一鍵 v0136 程式碼雜湊 `eebbd1755d50…`(啟動器 v0136 `cb6bf142a0e3…` · 驗證器 v0105)。

v0102 = v0101 + ② 改指 VRN-2 一鍵 v0136(驗證器 v0105:DUPKEY 看位置證據 · 對調診斷 · EPS 格 · 貼給 AI 每類錯值都出現;啟動器 ⑫a 自己把 VRN-1 倉 fast-forward 到 main)。
一段貼上去:① VRN-1 倉(不在 → 從 GitHub 複製 · 在 → stash 保存 · 切 main · 只快轉)→ ② VRN-2 v0136 全流程(U/I 自己跳出)→ ③ VRN-1 MAIN(check → run · 沒有 pwsh 就 winget 裝)→ ④ 總結 + 要人判 + GitHub Actions。
只呼叫兩邊自己的入口,不改任何一邊的程式 / 冊 / 號;VCGC / VDF 不碰(四系統各自獨立)。v0101 的開關全部照舊。

| 情境 | 結果 |
|---|---|
| **VRN-1 倉不在**(只有 VIA 樹 · Downloads 是 MAIN 的 v0135)· 貼「一行」(pwsh 7.4.6 · `-EncodedCommand`) | ① 綠「複製好了 · main d7a12e2」(VRN-1 PR #81 已合併的 main)· ② 黃 結束碼 2:VRN-2 一鍵 v0136 程式碼雜湊相符 → 取啟動器 v0136 · ⑦ 14 / 14 · ⑧ 完成 · ⑪ v0105 錯值 0 · ⑫a 綠 · ⑫ 借到 VRN-1 table.pivot_db(事實 4653 / 4905 · 年度 1060 列)· 黃只因 Linux 沒 HKCU / 瀏覽器(⑤b · ⑤c;Windows 為綠)· ③ 綠 check rc 0 · run rc 0 · G23 借到 2 / 2 · G21 WARN / PASS · G22 PASS / PASS · [收尾] 完成 · 總結 NEXT YELLOW · 結束碼 2 · 要人判:VRN-1 待修清單位置 · VRN-1 倉 main 最近一次 Actions failure(幾秒就失敗 → 提示去 Settings → Actions / Billing) |
| 再貼一次 | ① 綠 `main d7a12e2 → d7a12e2`(乾淨 · stash 0)· ② 黃 結束碼 2(啟動器已是 v0136 · ⑪ v0105 錯值 0 · ⑫a 已在 main 最新 · ⑫ 借到)· ③ 綠(同上)· VRN-1 倉仍乾淨 |
| winget 自動安裝 | 容器測不到(Linux 沒有 winget / Windows PowerShell)· 與 v0101 同一段碼、沒改 |

**收尾判準:輸出驗證無誤於 HTML U/I**(真 Chromium · 最後狀態 = 再貼一次之後):

| 頁 | 實測 |
|---|---|
| VRN-2 U/I `VRN2_UI_latest.html`(第一個分頁「驗證過的輸出」) | 0 / 0 · 獨立驗證 v0105 寫回 4,905 筆 |
| VRN-2 PIVOT `pivot\VRN_Pivot_v0100.html` | 29 / 29(年度 PIVOT 1,060 列)|
| VRN-1 驗證過的輸出 `VRN_Verified_Output_v0100.html` | 28 / 28(年度數據 1,686 · 年度財報格 354 · 代號紀錄 14 · 自動修正 7)|
| VRN-1 PIVOT `VRN_Pivot_v0100.html` | 29 / 29(年度 PIVOT 221 列)|

日誌:`logs_v0102.zip` · 測試工具:`tools_v0102.zip`(產生器 · 情境腳本 · 不含 .ps1)。v0100 / v0101 照舊留著。
