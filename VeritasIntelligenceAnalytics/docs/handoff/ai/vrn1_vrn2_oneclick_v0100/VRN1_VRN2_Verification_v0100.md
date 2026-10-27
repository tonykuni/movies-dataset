# VRN-1 / VRN-2 操作員一鍵 v0100 · 容器實測紀錄(2026-10-20)

操作員令:「INTEGRATE ABOVE INTO ONE CODE TO HANDLE ALL ABOVE. git pull」。一鍵程式碼 SHA-256 `60e5515615e0cb96fa1c532ec280d28a91d8dd61d49f91de203a1b393519134a`(`VRN1_VRN2_OneClick_v0100.md` 的 powershell 區塊)·
內含 VRN-2 一鍵 v0132 程式碼雜湊 `c68b66b0ddf4…`(相符才執行 VRN-2 自己的流程)。

本段只依序呼叫兩邊自己的入口(VRN-1 = `artifacts\VRN-1.ps1`,VRN-2 = 一鍵 v0132 → `ActivateVRN-2.py`),不改任何一邊的程式 / 冊 / 號;VCGC 與 VDF 不碰。

| 情境 | 起始狀態 | 結果 |
|---|---|---|
| 完整(定稿版) | VRN-1 = GitHub 真複製 · 本機 main 退回 62475b0 · 停在別的分支 `work` · 1 個沒提交的改動;VRN-2 = 沙盒樹 · Downloads 是 v0131 · 發行與本一鍵放在假 GitHub 分支 · 貼「一行」(pwsh 7.4.6 · `-EncodedCommand`) | ① 綠 `main 62475b0 → 7693aee` · 改動已暫存(`git stash` · 印出 `stash pop` 指令)· 分支 work → main(原分支還在)· ② 綠 結束碼 0(取 v0132 · 雜湊相符 · ⑦ 14 / 14 · ⑪ 錯值 0)· ⑫ 借到 VRN-1 `table.pivot_db`(sha256 `74b97b8bf02d`)事實 4,653 / 4,905 · 年度 1,060 列 · ③ 綠 check rc 0 · run rc 0 · G23 借到 2 / 2 · G22 PASS · 收尾 完成 · ④ NEXT 綠 |
| 再貼一次 | 同一棵樹(VRN-1 已是最新 · 沒有改動) | ① 綠 `main 7693aee → 7693aee`(沒有東西要暫存)· ② 綠(啟動器已是 v0132 · ⑨ 已是最新)· ③ 綠 · 跑完 VRN-1 倉仍是乾淨的(run 不寫倉 → 下次 git pull 不會卡) |
| VRN-1 倉不在 | `VIA_VRN1_ROOT` 指到不存在的夾 · 跳過 VRN-2 | ① 紅「不是 VRN-1 的 git 倉 · 設 `$env:VIA_VRN1_ROOT`」· ③ 紅(附同一個說明)· NEXT 紅 · 結束碼 1 · 不卡住 |
| VIA 根不在 | `VRN2_ROOT` 指到不存在的夾 · 跳過 VRN-1 | ② 紅「不是 git 倉 · 設 `$env:VRN2_ROOT`」· NEXT 紅 · 結束碼 1 |

實測抓到、改掉的:VRN-1 倉不在時的說明寫成 `"…$V1?)"` —— PowerShell 把 `$V1?` 當成變數名 `V1?`(空的),路徑印不出來 → 改寫法;報告路徑的比對原本是 `\S+`(Windows 路徑有空白就抓不到)→ 改成允許空白。兩處都在定稿版重跑過。

日誌:`logs_v0100.zip`(完整 · 再貼一次 · 兩個出錯情境 · 草稿那一次)· 測試工具:`tools_v0100.zip`(產生器 · 情境腳本 · 不含 .ps1)。
