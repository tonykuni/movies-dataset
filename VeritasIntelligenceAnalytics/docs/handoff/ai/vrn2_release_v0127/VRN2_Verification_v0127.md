# VRN-2 v0127 驗證紀錄(2026-10-19 · Claude Code 雲端容器)

發行檔:`ActivateVRN-2_v0127.zip`(內含 `ActivateVRN-2.py` · SHA-256 `333e906e78e7…` · 全碼見 `VRN2_Release_v0127.json`)。交接報告:`../VRN2_Handover_v0127.md`。一鍵 PS:`VRN2_OneClick_v0127.md`。日誌(`logs/*.log`)在 `logs_v0127.zip`(repo 的 .gitignore 不收 *.log)。

## U/I 上的驗證過的輸出(本輪重點)

| 項目 | 結果 | 證據 |
|---|---|---|
| U/I 第一個分頁「驗證過的輸出」 | 全部檔案總表 → 選一份 → 基本資料 / 一標題四重點 / 年度數據格子 · 每格值 + 徽章(✓✓ 兩層都對位)· 滑鼠提示 · 搜尋 · 只看待核對 · 下載 CSV | `shots/ui_verified.png` · `ui_verified_basic.png` · `ui_verified_grid.png` |
| 頁面上的值 = 輸出冊 | 4,916 格逐筆與 `VRN2_FinancialData_latest.json` 相同(值 · 科目 · 期間) | `logs/ui_test.log` |
| 獨立驗證寫回 | 啟動器 ⑪ 背景跑完 → 判決依冊內序號寫回 · 冊指紋 `68489c72479b1faa` 與本頁相同 → 套用;改一碼指紋 → 狀態列寫「別一輪」· 格子不套用 | `logs/ui_test.log` |
| U/I 真瀏覽器(Chromium) | **35/35**(原 21 項 + 本輪 14 項) | `logs/ui_test.log` |

## 輸出值驗證(獨立驗證器 v0100 · 不 import VRN-2 程式)

| 冊 | v0126 輸出(v3 判) | v0126 輸出(v0100 判) | **v0127 輸出(v0100 判)** |
|---|---|---|---|
| 基本資料(14 份) | 194 過 | 194 過(目標價 / 股價 / 上漲空間改成「標籤旁」才算) | **194 過 · 0 錯** |
| 一標題四重點 | 63 過 | 63 過(組句數字對基本資料 / 年度數據) | **63 過 · 0 錯** |
| 年度數據 | 4,860 筆 · ALIGNED 4,323 · PRESENT 10 | **DUPROW 18**(9 對完全重複)· 其餘全對位 | **4,916 筆 · ALIGNED 4,389 · SUBALIGNED 452 · TRANSALIGNED 75 · 不過 0 · PRESENT 0** |

- v0127 年度數據 = v0126 4,860 + 一格整列拆開 65(凱基慧洋財務比率表 13 列 × 5 期)− 完全重複 9。剔除冊 719 → 733(+ 貿聯 2 列散文誤成整列 5 · + 重複 9)。
- **驗證器反向測試總表**(`tools/verify_mutation_suite.py` · `logs/verifier_mutation_suite.log`):把真的會發生的錯放回輸出,驗證器一定要抓到。

| 放回的錯 | v3 漏抓 | **v0100 漏抓** |
|---|---|---|
| 年度數據換成下一列的值(3,000 筆) | 2,917 | **0** |
| 換成上一列的值(3,000 筆) | 131 | **0** |
| 換成同列鄰欄的值(2,978 筆) | 20 | **0** |
| 季度值標成年度期間(貿聯 Dec-26F / Dec-27F) | 4 / 4 | **0** |
| 子欄換成別列的值(40 組 × 2) | 29 · 31 | **0 · 0** |
| 轉置表換成別年的值(59 筆) | 0 | **0** |
| 基本資料 目標價 ↔ 股價 · 目標價換成首頁別的數 · 評等換成定義頁才有的 | v3 只查「原文有這個數 / 前 8 頁有這個字」→ 依構造會過(沒另跑 v3) | **0** |
| 重點 目標價換股價 · 原目標價 / 倍數換成原文別的數 · EPS 兩年對調 · 跨檔對調 · 標題剩一個字 | v3 數字只查「原文有」→ 前四類依構造會過 · 跨檔對調 v3 也抓得到(沒另跑 v3) | **0** |
| 原本的 ①~⑩(子欄 4 種 · 分析師 · 日期 · 影像頁 · DUPKEY · 轉置 · 值列錯開) | — | **10/10** |

## 自測 / 實測

| 項目 | 結果 | 證據 |
|---|---|---|
| 啟動器 v0127 自測 | **20/20**(新增:內嵌獨立驗證器 · ⑦ --no-open / ⑪ 在 ⑩ 之後 / 開 U/I 在 ⑪ 之後 · ⑪ 綠 / 黃 / 超時 / 不驗舊冊 · 內嵌驗證器自測) | `logs/launcher_selftest.log` |
| 管理器鏈自測 | v0231 33/33 · v0232 11/11 · v0233 6/6 · v0234 14/14 · v0235 7/7 · v0236 13/13 · **v0237 12/12** | `logs/manager_selftest_v0237_chain.log` |
| 獨立驗證器 v0100 自測 | **16/16** | `logs/verifier_selftest.log` |
| 新樹實跑 ×2 | 第 1 次 ⑧ 完成 紅 0 · ⑨ 上船 · ⑩ 封存 · **⑪ 綠 錯值 0** · 第 2 次 ⑨ 已是最新 · 四本冊逐位元相同 | `logs/run_fresh_1.log` · `run_fresh_2_no_change.log` |
| 從 v0126 升級(一鍵 PS v0127 · pwsh 7.4)| 情境:先跑過 v0126 並上船 · 遠端被別台推了新提交 · 本機有別的系統的提交(未推)· 遠端放 v0127 發行分支 → 第 1 次 備份 v0126 → 換 v0127(雜湊對)→ 只落 v0237 + 獨立驗證器 → ⑧ 完成 → ⑨ **只送 VRN-2 船包**(疊在遠端最新上 · 本機 VCGC 提交沒推 · 遠端沒有那個檔)→ ⑪ 綠 → PS 摘要「U/I 判決已寫回 · 冊指紋相同」· 第 2 次 本機已是 v0127 · ⑨ 已是最新 | `logs/run_0_v0126_before.log` · `oneclick_ps_run1.log` · `oneclick_ps_run2.log` · `ship_commit_remote_run1.log` |
| **cmd / PowerShell 都能貼的一行**(`-EncodedCommand`) | 情境同上(先跑過 v0126)→ 讀分支上的一鍵程式碼 · SHA-256 `d248eac591b7` 相符 → 執行 → 備份 v0126 → 換 v0127 → ⑧ 完成 · ⑨ 只送 VRN-2 船包 · ⑪ 綠 · 第 2 次 已是 v0127 · ⑨ 已是最新;分支上的程式碼被改一個字 → SHA-256 不對 → **不執行** | `logs/oneclick_cmd_oneliner_run1.log` · `run2.log` · `tamper.log` |
| 新電腦(從遠端 clone) | ② 船包補回 **16/16**(含獨立驗證器)· ⑧ 完成 · ⑪ 綠 · 四本冊與原機逐位元相同 | `logs/run_new_machine_clone.log` |
| v0126 輸出交給新驗證器 | DUPROW 18(v0126 就有的重複列 · 舊驗證器抓不到) | `logs/verifier_v0100_on_v0126_output.log` |

## 重跑方法

`vrn2_test_tools_v0127.zip`:`tools/mktree.sh <樹> <啟動器>` → `PY=<python> tools/runl.sh <樹>` → `tools/verify_outputs.py <output> <scope_in> <報告.json> [--ui <U/I>]`(= `VRN2_IndependentVerifier_v0100.py`)→ `tools/verify_mutation_suite.py <output> <scope_in> 3000` → `node tools/ui_test.js <VRN2_UI_latest.html> <截圖夾> <output>`(`NODE_PATH` 指到 playwright)→ `tools/scen127.sh <樹>` + `PS_FILE=<Run-VRN2-v0127.ps1> tools/run_ps_test.sh <樹>`。
組裝:`tools/make_verifier_v0100.py <verify_outputs_v0126.py> <src/_bridge_block.txt> <輸出>` · `tools/build_v0127.py <v0121 啟動器> <src 夾> <v0121 內嵌原件夾> <輸出>`。
`fixture/TESTSTUB_VRN_SystemManager_v0230.py` 只代表使用者機器上的前版鏈,**不可放進 functional modules/VRN**。

## 沒驗到的(不寫成綠)

`vrn2://` 註冊與 `os.startfile` 自動開 U/I(Windows · 容器只印路徑)· OCR 隔離環境 · ③ 補裝(容器 `--no-install` → ③ 紅 · 不擋 ⑧)· 使用者機器 52 份(新驗證器第一次在使用者機器跑 → 請貼回 ⑪ 那一行與驗證摘要)。
