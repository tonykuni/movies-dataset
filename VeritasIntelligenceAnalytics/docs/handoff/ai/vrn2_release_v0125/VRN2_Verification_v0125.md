# VRN-2 v0125 驗證紀錄(2026-10-18 · Claude Code 雲端容器)

發行檔:`ActivateVRN-2_v0125.zip`(SHA-256 見 `VRN2_Release_v0125.json`)· 一鍵 PS:`VRN2_OneClick_v0125.md` · 交接報告:`../VRN2_Handover_v0125.md` · 日誌:`logs_v0125.zip`。

## 這一輪從哪來

使用者機器第 38 輪(v0124 · 52 份)貼回:⑧ 完成 紅 0 黃 5 · ⑨ 推送被拒(本機領先 131 個提交 · 遠端較新)· 獨立驗證 v1:基本資料 FAIL 10 · 一標題四重點 FAIL 8 · 年度數據 FAIL 69 / BADITEM 29 / SUBFAIL 218 · 驗證約 26 分。
省 Token 分診(只看貼包判決行 · 不重讀程式):能從貼包確定根因的直接修(⑨ · 分析師 · 驗證器 OCR / 日期);明細在使用者機器的(年度數據 FAIL / SUBFAIL)→ 加第三讀法閘把對不上的移剔除冊 + 驗證器出 ≤150 行摘要,下一輪依摘要修。

## 情境實測(模擬使用者機器:先跑 v0124 並上船 → 另一台機器推了新提交 → 本機有別的系統的提交未推 → Downloads 裡是 v0124)

| 步驟 | 結果 | 證據 |
|---|---|---|
| 啟動器 v0125 自測 | 16/16(含 ⑨ 遠端較新 + 本機別的提交 → 只送船包 · 再跑已是最新) | `logs/launcher_selftest.log` |
| 管理器 v0231~v0235 自測 | 33/33 · 11/11 · 6/6 · 14/14 · 7/7 | `logs/oneclick_ps_run1.log` |
| 一鍵 PS 第 1 次 | ③ 備份 v0124 → 換 v0125(雜湊對)→ 只落 v0235 → ⑧ 完成 紅 0 → ⑨ **只送 VRN-2 船包**(疊在遠端最新 · fast-forward · `VCGC_local_only.md` 沒被推)→ 獨立驗證錯值 0 + 摘要 · 約 1 分 40 秒 | `logs/oneclick_ps_run1.log` · `logs/ship_commit_remote_run1.log` · `logs/ship_commit_local.log` |
| 一鍵 PS 第 2 次 | ③ 已是 v0125 → ⑨ GitHub 已是最新(不重推)· 約 1 分 10 秒 | `logs/oneclick_ps_run2.log` |
| 新電腦(clone) | ② 船包補回 13/13 → ⑧ 完成 → ⑨ 只送船包 · 四本輸出冊與原機逐位元相同 | `logs/run_new_machine_clone.log` |
| 使用者自己 git pull(遠端有較新的船包) | 船包 zip + json 整檔衝突(不混兩邊)→ `git checkout --theirs -- docs/handoff/ai/vrn2_ship` → 船包 = 遠端版本 | `logs/user_pull_merge_test.log` |

## 輸出值驗證(獨立驗證器 v2 · 不 import VRN-2 · 子欄用 PyMuPDF · 3 路平行)

| 冊 | 結果 |
|---|---|
| 基本資料(14 份) | 194/194 |
| 一標題四重點 | 63/63 |
| 年度數據 | 4,411 筆:ALIGNED 3,949 · SUBALIGNED 452 · PRESENT 10(pypdfium2 已對欄 · 驗證器對不到 · 不算錯)· **FAIL / BADITEM / SUBFAIL 0** |
| 第三讀法閘(v0235) | 子欄 452 過 / 0 剔除 · 欄位未定位 20 → 補對欄 6 / 剔除 14 · 剔除冊 74 → 88 |
| 驗證器反向測試 | 7/7(子欄 4 種錯 · 分析師帳號名 FAIL / EST · 日期寫法 · 影像頁 OCR) |
| U/I 真瀏覽器 | 21/21 |

報告:`verify_report.json` · `logs/verify_digest.txt`(就是一鍵 PS 印出、要貼回的那份)。

全景卡(VCGC 省 Token `read` · 只讀):管理器 v0235 問題 0 · 啟動器 v0125 9 項 SWALLOW(與 v0124 相同 · 量測 / 視窗關閉的退路 · 本輪沒新增)· 驗證器 3 項(讀取器 / psutil 缺時的退路)。

## 沒驗到的(不寫成綠)

使用者機器 52 份(v0235 閘的剔除數 · 分析師改寫 · 驗證摘要)· Windows PowerShell 5.1 · CPU / RAM 量測與優先權 · ③ 補裝(容器 `--no-install`)。
