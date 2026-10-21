# VRN-1 / VRN-2 操作員一鍵 v0102 · 容器實測紀錄(2026-10-21)

操作員令:「ONE CODE TO HANDLE ALL.」(v0136 合併 MAIN 之後)。
一鍵程式碼 SHA-256 `e8f121d5cfb39f3108abf52398c3878b28e4fe4a345da71f37701d7d02804ce9`(`VRN1_VRN2_OneClick_v0102.md` 的 powershell 區塊)· 內含 VRN-2 一鍵 v0136 程式碼雜湊 `eebbd1755d50…`(啟動器 v0136 `cb6bf142a0e3…` · 驗證器 v0105)。

v0102 = v0101 + ② 改指 VRN-2 一鍵 v0136(驗證器 v0105:DUPKEY 看位置證據 · 對調診斷 · EPS 格 · 貼給 AI 每類錯值都出現;啟動器 ⑫a 自己把 VRN-1 倉 fast-forward 到 main)。
一段貼上去:① VRN-1 倉(不在 → 從 GitHub 複製 · 在 → stash 保存 · 切 main · 只快轉)→ ② VRN-2 v0136 全流程(U/I 自己跳出)→ ③ VRN-1 MAIN(check → run · 沒有 pwsh 就 winget 裝)→ ④ 總結 + 要人判 + GitHub Actions。
只呼叫兩邊自己的入口,不改任何一邊的程式 / 冊 / 號;VCGC / VDF 不碰(四系統各自獨立)。v0101 的開關全部照舊。

## Codex #564(PR 上的四條 · 都在本段程式碼裡 · 都修)

| 等級 | 指出 | 修法 | 單元 |
|---|---|---|---|
| P1 | ① 切不到 main(main 在別的 worktree / 未追蹤檔擋住)仍 `git pull --ff-only` → 別的分支被快轉到 main、或分岔的分支被當最新 | 切完後核對 HEAD 真的是 main 才拉;否則黃「切不到 main → 不拉 · 照現狀 <分支>@<sha> 跑」,理由(第一次失敗的 git 訊息)印出 | A:main 佔在別的 worktree → 黃、HEAD 不變 |
| P2 | `--untracked-files=no` 看不到未追蹤的檔 → 可能擋住切換 | 未追蹤的檔另外數、留著不動(不用 `stash -u` 動操作員的檔);真擋到時切換會失敗 → 走上面那條黃、不拉 | B:未追蹤 1 個 → 說明裡寫出來 |
| P2 | `VRN_PAIR_SKIP` 跳過一邊 → 總結仍 GREEN「兩個系統都跑完」 | 跳過一邊 → 最多 YELLOW:「這次只跑了 VRN-x(VRN_PAIR_SKIP=…)· 不算兩邊都完成」 | B |
| P2 | 一行的 boot 紅燈只 `return`、最後沒 `exit` → cmd `%ERRORLEVEL%` 永遠 0 | boot 紅燈 `exit 1` · 執行包 try/catch · 最後 `exit` 最終燈(GREEN 0 / YELLOW 2 / RED 1) | C1 exit 2 · C2(程式碼被改)exit 1 · C3(不是 git 倉)exit 1 |

單元(pwsh 7.4.6 · git 夾具):
```
[OK] A ① 切不到 main(main 在別的 worktree · 理由印出)→ 黃、不拉(HEAD 仍 feat@c847dd3)· 總結紅(③ 沒有 VRN-1.ps1)
[YELLOW] ① VRN-1 git pull · 切不到 main → 不拉 · 照現狀 feat@c847dd3 跑 · 切不到 main(fatal: 'main' is already used by worktree at '/tmp/clau
[RED] ③ VRN-1 MAIN · 找不到 /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/pair102/ut/cl/artifacts/VRN-1.ps1 · VRN-1 倉不在
[YELLOW] ① VRN-1 git pull · 切不到 main → 不拉 · 照現狀 feat@c847dd3 跑 · 切不到 main(fatal: 'main' is already used by worktree at '/tmp/clau
[RED] ③ VRN-1 MAIN · 找不到 /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/pair102/ut/cl/artifacts/VRN-1.ps1 · VRN-1 倉不在
[OK] B 跳過 VRN-2 · ① 綠 ③ 綠 → 最終 YELLOW「這次只跑了 VRN-1」(exit 碼由 boot 帶回 · 見 C1)
[GREEN] ① VRN-1 git pull · main 2d3dde9 → 2d3dde9 · 未追蹤的檔 1 個留著不動(擋到切換時下面會說)
[GREEN] ③ VRN-1 MAIN · check rc 0 · run rc 0 · [收尾] 完成
[GREEN] ① VRN-1 git pull · main 2d3dde9 → 2d3dde9 · 未追蹤的檔 1 個留著不動(擋到切換時下面會說)
[GREEN] ③ VRN-1 MAIN · check rc 0 · run rc 0 · [收尾] 完成
[OK] C1 boot 雜湊相符 → 執行 → 最終燈 YELLOW 帶回 exit 2
[OK] C2 boot 程式碼被改 → 雜湊不對 → 不執行 · exit 1
[OK] C3 boot VRN2_ROOT 不是 git 倉 → exit 1
[計] 操作員一鍵 v0102 單元 5/5 · PASS
```

| 情境 | 結果 |
|---|---|
| **VRN-1 倉不在**(只有 VIA 樹 · Downloads 是 MAIN 的 v0135)· 貼「一行」(pwsh 7.4.6 · `-EncodedCommand`)· 結束碼 2 | ① GREEN:複製好了 · main d7a12e2 → /tmp/claude-0/-home-user/a5893bdc-578f-5cd1-ac75-9575fa695b26/scratchpad/pair102/clone_here/VIA-VDF-VRN · ② YELLOW:結束碼 2 · ⑫ PIVOT 借到 VRN-1 table.pivot_db(sha256 adadf2a50d19)· 事實 4653/4905 · 年度 1060 列 · 衝突 18 · ③ GREEN:check rc 0 · run rc 0 · G23 借到 2/2 · G21 WARN/PASS · G22 PASS/PASS · [收尾] 完成 · 輸出驗證無誤才算收尾完成 · NEXT: [YELLOW] 跑完但有黃燈 · 看上面黃的那一步(說明裡有下一步)· 把總結這幾行貼回 |
| 再貼一次 · 結束碼 2 | ① GREEN:CPU 量不到 · 可用 RAM 量不到 · 優先權 Normal → Normal · ② YELLOW:結束碼 2 · ⑫ PIVOT 借到 VRN-1 table.pivot_db(sha256 adadf2a50d19)· 事實 4653/4905 · 年度 1060 列 · 衝突 18 · ③ GREEN:check rc 0 · run rc 0 · G23 借到 2/2 · G21 WARN/PASS · G22 PASS/PASS · [收尾] 完成 · 輸出驗證無誤才算收尾完成 · NEXT: [YELLOW] 跑完但有黃燈 · 看上面黃的那一步(說明裡有下一步)· 把總結這幾行貼回 |
| winget 自動安裝 | 容器測不到(Linux 沒有 winget / Windows PowerShell)· 與 v0101 同一段碼、沒改 |

② 黃與總結黃只因 Linux 沒 HKCU / 瀏覽器(VRN-2 ⑤b · ⑤c);Windows 上為綠。結束碼由 boot 帶回(YELLOW → 2)。

**收尾判準:輸出驗證無誤於 HTML U/I**(真 Chromium · 最後狀態 = 再貼一次之後):

| 頁 | 實測 |
|---|---|
| VRN-2 U/I `VRN2_UI_latest.html` | 35 / 35 |
| VRN-2 PIVOT `pivot\VRN_Pivot_v0100.html` | 29 / 29 |
| VRN-1 驗證過的輸出 `VRN_Verified_Output_v0100.html` | 28 / 28 |
| VRN-1 PIVOT `VRN_Pivot_v0100.html` | 29 / 29 |

日誌:`logs_v0102.zip`(兩次情境 · 單元 A–C3 · 四張 U/I)· 測試工具:`tools_v0102.zip`(產生器 · 情境腳本 · 單元腳本 · 不含 .ps1)。v0100 / v0101 照舊留著。
