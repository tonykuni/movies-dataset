# VRN-2 v0128 驗證紀錄(2026-10-19 · Claude Code 雲端容器)

發行檔:`ActivateVRN-2_v0128.zip`(內含 `ActivateVRN-2.py` · SHA-256 `0048bf332e38…` · 全碼見 `VRN2_Release_v0128.json`)。交接報告:`../VRN2_Handover_v0128.md`。一鍵:`VRN2_OneClick_v0128.md`(**cmd / PowerShell 都能貼的一行** · 程式碼 SHA-256 `32eadc1b5766`)。日誌(`logs/*.log`)在 `logs_v0128.zip`(repo 的 .gitignore 不收 *.log)。

## 本輪兩件事

| 項目 | 結果 | 證據 |
|---|---|---|
| **① 依 MAIN 登記紀錄定位 VRN-2 程式夾**(使用者機器 v0127 第一次跑:② 紅「找不到 functional modules\VRN」) | 啟動器 `locate()`:VIA_ROOT(含其下 VeritasIntelligenceAnalytics)· 交接報告的 VIA 根 · 本支所在夾 · 目前夾 · MAIN 成功紀錄的鎖檔路徑 · git 倉裡找 → 多個候選選本機登記的 MAIN 管理器(檔在且 sha 相同)→ ② 印來源與登記版號 · VIA_ROOT 指錯 → 黃且說明 · 找不到 → 列出查過的地方 | 下表「實跑」各列 |
| **② 邊測邊修:3 列表頭被當數據** | 把 U/I「驗證過的輸出」逐格看一遍 → 凱基 2637 P5 現金流量表「NT$百萬 Dec-23A … Dec-27F」5 筆 · JP 2330 P20「Balance Sheet & Cash Flow Statement FY24A … FY27E」4 筆 · GS 6415 P2「Jul-25 Oct-25」Jan-26 / Apr-26 2 筆 · **獨立驗證器 v0100 判這 11 筆對位**(表頭字本來就印在期間那一欄)→ 管理器 **v0238** 整列移剔除冊(理由「表頭列(…)· 不進年度數據」)· 驗證器 **v0101** 另查值的種類(HDRVAL) | `logs/verifier_v0101_on_v0237_output.log`(v0237 輸出 → HDRVAL 11 · 其餘不變)· `logs/verifier_mutation_suite.log`(cmp_hdr) |

## 輸出值驗證(獨立驗證器 v0101 · 不 import VRN-2 程式)

| 冊 | v0127 輸出(v0100 判) | v0127 輸出(v0101 判) | **v0128 輸出(v0101 判)** |
|---|---|---|---|
| 基本資料(14 份) | 194 過 | 194 過 | **194 過 · 0 錯**(與 v0127 逐位元相同) |
| 一標題四重點 | 63 過 | 63 過 | **63 過 · 0 錯**(與 v0127 逐位元相同) |
| 年度數據 | 4,916 · 全對位 | **HDRVAL 11**(3 列表頭)· 其餘 4,905 對位 | **4,905 筆 · ALIGNED 4,378 · SUBALIGNED 452 · TRANSALIGNED 75 · 不過 0 · PRESENT 0 · HDRVAL 0** |
| 剔除冊 | 733 | — | **744**(+ 表頭列 11 · 帶理由) |

- 每次跑出來的四本冊彼此逐位元相同(使用者機器情境 · 從 v0126 升級 · 新電腦 clone · 只跑啟動器):基本資料 `7548d40b79ef` · 一標題四重點 `1eba44824026` · 年度數據 `35a6fef4faf5` · 剔除冊 `4e2dce75d8cb`。
- U/I 冊指紋 `63a758ad569819a9` = 驗證報告指紋 → 判決套用 · 驗證器版本 v0101。

**驗證器反向測試總表**(`tools/verify_mutation_suite.py` · `logs/verifier_mutation_suite.log`):

| 放回的錯 | v3 漏抓 | v0100 漏抓 | **v0101 漏抓** |
|---|---|---|---|
| 年度數據換成下一列 / 上一列 / 同列鄰欄的值(3,000 / 3,000 / 2,970 筆 · v0128 輸出) | 2,915 / 136 / 20 | 0 / 0 / 0(v0127 輸出量的 · v0101 找值與 v0100 同一段程式) | **0 / 0 / 0** |
| 季度值標成年度期間 · 子欄換成別列的值 · 轉置表換成別年的值 | 4 · 29 / 31(v0127 量的)· 0 | 0 | **0** |
| 基本資料 / 一標題四重點(目標價 ↔ 股價 · 換成原文別的數 · EPS 對調 · 跨檔對調 · 太短) | 依構造會過 | 0 | **0** |
| **表頭列放回年度數據(v0237 輸出真的出現過的 11 筆)** | — | **11**(全判對位) | **0**(全標 HDRVAL) |
| 表頭列混進整本冊(4,905 + 11)→ 一般列被誤標 | — | — | **0** |
| 原本的 ①~⑩(子欄 4 種 · 分析師 · 日期 · 影像頁 · DUPKEY · 轉置 · 值列錯開) | — | 10/10 | **10/10** |

## 自測 / 實測

| 項目 | 結果 | 證據 |
|---|---|---|
| 啟動器 v0128 自測 | **23/23**(新增:依紀錄定位 A~E · 新 clone 的定位說明 · git 失敗訊息一行 · 內嵌 15 個元件 hash 全對) | `logs/launcher_selftest.log` |
| 管理器鏈自測 | v0231 33/33 · v0232 11/11 · v0233 6/6 · v0234 14/14 · v0235 7/7 · v0236 13/13 · v0237 12/12 · **v0238 7/7** | `logs/manager_selftest_v0238_chain.log` |
| 獨立驗證器 v0101 自測 | **17/17**(新增 HDRVAL) | `logs/verifier_selftest.log` |
| **使用者機器情境重現**(一行 · 環境變數 VIA_ROOT 指錯)| 上次成功 v0125(管理器鏈到 v0235)· Downloads 的啟動器已被上一次的一行換成 v0127 · VIA_ROOT=/nonexistent/VIA · 遠端放 v0128 發行分支 → 一行 → 程式碼 SHA-256 `32eadc1b5766` 相符 → 備份 v0127 → 換 v0128 → ③b 改正 VIA_ROOT(只在這個視窗 · 結束還原)→ ② 綠「來源 VIA_ROOT · 登記 VRN_SystemManager_v0235.py sha 相符」→ 落地 v0236 → v0237 → v0238 + 驗證器 v0101 → ⑧ 完成 · ⑨ 只送 VRN-2 船包 · ⑪ 綠 錯值 0 · U/I 判決寫回 | `logs/run_0_v0125_before.log` · `oneclick_cmd_oneliner_user_machine_v0125_wrong_VIA_ROOT.log` |
| 從 v0126 升級(一行 · VIA_ROOT 指錯)| 先跑 v0126 並上船 · 遠端被別台推了新提交 · 本機有別的系統的提交(未推)→ 一行 → 備份 v0126 → 換 v0128 → ② 「登記 VRN_SystemManager_v0236.py sha 相符」→ ⑧ 完成 · ⑨ **只送 VRN-2 船包**(疊在遠端最新上 · 本機另有 1 個提交不代推)· ⑪ 綠;第 2 次 本機已是 v0128 · ② 登記 v0238 sha 相符 · ⑨ 已是最新 | `logs/run_0_v0126_before.log` · `oneclick_cmd_oneliner_run1_from_v0126_wrong_VIA_ROOT.log` · `oneclick_cmd_oneliner_run2.log` |
| 一行的竄改測試 | 分支上的一鍵程式碼被改一個字(錯值 0 → 錯值 X)→ SHA-256 不對 → **不執行** | `logs/oneclick_cmd_oneliner_tamper.log` |
| 只跑啟動器(不經 PS)· VIA_ROOT 指到別的夾 | ② 黃「來源 git 倉裡找到 · 登記 VRN_SystemManager_v0238.py sha 相符 · VIA_ROOT … 那裡沒有 VRN-2 程式夾 → 不用」· ⑧ 完成 · ⑪ 綠 | `logs/run_launcher_only_wrong_VIA_ROOT.log` |
| 新電腦(從遠端 clone) | 第 1 次(沒設 git 使用者)② 綠「本機還沒有登記紀錄 · 船包清單的管理器 VRN_SystemManager_v0238.py 下一步依船包補回」· 船包補回 **17/17** · ⑧ 完成 · ⑪ 綠 · ⑨ 黃「這台電腦的 git 還沒設使用者名稱 / Email · 請跑一次 git config --global …」(以前只印「t your account's default identity.」);第 2 次(設了)② 登記 v0238 sha 相符 · ⑨ 上船 · 四本冊與原機逐位元相同 | `logs/run_new_machine_clone_1_no_git_user.log` · `run_new_machine_clone_2_git_user.log` |
| U/I 真瀏覽器(Chromium) | **35/35**(頁面每一格 = 年度數據冊那一筆 4,905 / 4,905 · 指紋相同才套用 · 指紋不同不套用) | `logs/ui_test.log` · `shots/` |

## 重跑方法

`vrn2_test_tools_v0128.zip`:`tools/scen128u.sh <樹>`(使用者機器情境)· `tools/scen128b.sh <樹>`(從 v0126 升級)→ `tools/run_boot_test_badroot.sh <樹>`(一行 · VIA_ROOT 指錯)· `tools/e2e128.sh z|u` 一次跑完 → `tools/verify_mutation_suite.py <output> <scope_in> 3000`(含 `cmp_hdr.py` · 用 `fixture/HDRROWS_v0237_output.json`)→ `node tools/ui_test.js <VRN2_UI_latest.html> <截圖夾> <output>`(`NODE_PATH` 指到 playwright)。
組裝:`tools/make_mgr_v0238.py <src 夾>` · `tools/make_verifier_v0101.py <v0100> <輸出>` · `tools/build_v0128.py <v0121 啟動器> <src 夾> <v0121 內嵌原件夾> <輸出>` · `tools/pack128.sh` + `tools/regen128.py`(一鍵程式碼 / 一行 / 雜湊一起換)。
`fixture/TESTSTUB_VRN_SystemManager_v0230.py` 只代表使用者機器上的前版鏈,**不可放進 functional modules/VRN**。

## 沒驗到的(不寫成綠)

Windows PowerShell 5.1 本身(容器是 pwsh 7.4 · 一鍵程式碼掃過沒有 7 才有的語法 · 使用者機器上次 5.1 跑一行已成功讀碼與核對雜湊)· `vrn2://` 註冊與自動開 U/I(Windows)· OCR 隔離環境 · ③ 補裝(容器 `--no-install` → ③ 紅 · 不擋 ⑧)· 使用者機器 52 份(新管理器 / 驗證器第一次在使用者機器跑 → 請貼回 ② / ③b / ⑨ / ⑪ 那幾行與驗證摘要)。
