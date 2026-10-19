# VRN-2 v0129 驗證紀錄(2026-10-19 · Claude Code 雲端容器)

發行檔:`ActivateVRN-2_v0129.zip`(內含 `ActivateVRN-2.py` · SHA-256 `600637bf6454…` · 全碼見 `VRN2_Release_v0129.json`)。交接報告:`../VRN2_Handover_v0129.md`。一鍵:`VRN2_OneClick_v0129.md`(**cmd / PowerShell 都能貼的一行** · 程式碼 SHA-256 `00cbbea2a4bf`)。日誌(`logs/*.log`)在 `logs_v0129.zip`(repo 的 .gitignore 不收 *.log)。前一版:`../vrn2_release_v0128/`。

## 本輪(繼續完成 · 輸出逐欄稽核)

| 項目 | 結果 | 證據 |
|---|---|---|
| 逐欄稽核年度數據(值以外的欄) | TICKER / BROKER / REPORT_DATE 與基本資料冊逐筆一致 · 期間字 50 種都合法 · 科目折行 1 列(完整存放)· **SECTION 有錯**(下一列) | `logs/section_audit_v0128_output.log` |
| **並排表段落標題互相拿錯**(凱基 2637 第 5 頁左「財務比率」∥ 右「投資回報率」) | 左表 流動比率 / 速動比率 / 淨負債 → 右表公式項「1 - 營業成本/營業收入」· 右表 1 / (營業運用資金 … = 稅後 ROIC → 左表「每股資料分析」/「資產運用狀況」· 右表 銷管費用 / 營業利益率 → 公式項 · 共 **13 列 65 筆 · 值都對**(驗證器 v0101 只查值 → 沒抓到) | `logs/verifier_v0102_on_v0238_output.log`(v0238 輸出 → SECFAIL 65 · 其餘不變) |
| 管理器 v0239 改回 | 第三讀法(pdfplumber)在這張表的上下範圍裡找科目那一列 → 上方同一欄找 SECTION 字 → 找不到 / 公式項 → 同一欄最近的段落標題(這 13 列都是空白:兩張表在本表範圍裡沒有自己的標題)· **值一個都不動** | `logs/ledger_diff_v0128_v0129.log`:有變的欄位只有 `SECTION` 65 筆 · 基本資料 / 一標題四重點 / 剔除冊逐位元相同 |
| 驗證器 v0102 另查(SECFAIL) | SECTION 字要在科目上方同一欄(pypdfium2 · x 差 ≤ 40)· 公式項不是標題 · 先定列再找值 | `logs/section_audit_v0129_output.log`:有 SECTION 的 561 筆全部同一欄 |

## 輸出值驗證(獨立驗證器 v0102 · 不 import VRN-2 程式)

| 冊 | v0128 輸出(v0102 判) | **v0129 輸出(v0102 判)** |
|---|---|---|
| 基本資料(14 份) | 194 過 | **194 過 · 0 錯**(與 v0128 逐位元相同) |
| 一標題四重點 | 63 過 | **63 過 · 0 錯**(與 v0128 逐位元相同) |
| 年度數據 | 4,905 · **SECFAIL 65** · 其餘對位 | **4,905 筆 · ALIGNED 4,378 · SUBALIGNED 452 · TRANSALIGNED 75 · 不過 0(HDRVAL 0 · SECFAIL 0)** |
| 剔除冊 | 744 | **744**(逐位元相同) |

- 每次跑出來的四本冊彼此逐位元相同(使用者機器情境 · 從 v0128 升級 · 新電腦 clone · 只跑啟動器):基本資料 `7548d40b79ef` · 一標題四重點 `1eba44824026` · 年度數據 `9746cbb5839c` · 剔除冊 `4e2dce75d8cb`。
- U/I 冊指紋 `63a758ad569819a9`(與 v0128 相同:指紋不含 SECTION)= 驗證報告指紋 → 判決套用 · 驗證器版本 v0102。

**驗證器反向測試總表**(`tools/verify_mutation_suite.py` · `logs/verifier_mutation_suite.log` · v0129 輸出):

| 放回的錯 | v3 漏抓 | v0100 / v0101 漏抓 | **v0102 漏抓** |
|---|---|---|---|
| 年度數據換成下一列 / 上一列 / 同列鄰欄的值(3,000 / 3,000 / 2,970 筆) | 2,915 / 136 / 20 | 0 / 0 / 0(找值同一段程式) | **0 / 0 / 0** |
| 季度值標成年度期間 · 子欄換成別列的值 · 轉置表換成別年的值 | 4 · 29 / 31(v0127 量的)· 0 | 0 | **0** |
| 基本資料 / 一標題四重點(目標價 ↔ 股價 · 換成原文別的數 · EPS 對調 · 跨檔對調 · 太短) | 依構造會過 | 0 | **0** |
| 表頭列放回年度數據(v0237 輸出的 11 筆) | — | v0100 **11** | **0** |
| **段落標題放回(v0238 輸出的 13 列 65 筆)** | — | v0101 **65**(不查 SECTION) | **0** |
| **右表科目換成左表才有的標題(摩根 2308 第 5 頁 100 筆)· 左表科目換成右表才有的標題(40 筆)** | — | — | **0 · 0** |
| 原本的 ①~⑩(子欄 4 種 · 分析師 · 日期 · 影像頁 · DUPKEY · 轉置 · 值列錯開) | — | 10/10 | **10/10** |

## 自測 / 實測

| 項目 | 結果 | 證據 |
|---|---|---|
| 啟動器 v0129 自測 | **23/23**(內嵌 16 個元件 hash 全對 · 管理器鏈 v0231 → v0239) | `logs/launcher_selftest.log` |
| 管理器鏈自測 | v0231 33/33 · v0232 11/11 · v0233 6/6 · v0234 14/14 · v0235 7/7 · v0236 13/13 · v0237 12/12 · v0238 7/7 · **v0239 10/10**(並排表版面同凱基 2637 第 5 頁 · 沒有表範圍不改 · 同一欄標題不動) | `logs/manager_selftest_v0239_chain.log` |
| 獨立驗證器 v0102 自測 | **18/18**(新增 SECFAIL) | `logs/verifier_selftest.log` |
| **使用者機器情境重現**(一行 · VIA_ROOT 指錯) | 上次成功 v0125 · Downloads 的啟動器已是 v0127 · VIA_ROOT=/nonexistent/VIA · 遠端放 v0129 發行分支 → 一行 → 程式碼 SHA-256 `00cbbea2a4bf` 相符 → 備份 v0127 → 換 v0129 → ③b 改正 → ② 綠「來源 VIA_ROOT · 登記 VRN_SystemManager_v0235.py sha 相符」→ 落地 v0236 → v0239 + 驗證器 v0102 → ⑧ 完成 · ⑨ 只送 VRN-2 船包 · ⑪ 綠 錯值 0 | `logs/run_0_v0125_before.log` · `oneclick_cmd_oneliner_user_machine_v0125_wrong_VIA_ROOT.log` |
| 從 v0128 升級(一行 · VIA_ROOT 指錯) | 先跑 v0128 並上船 · 遠端被別台推了新提交 · 本機有別的系統的提交 → 一行 → 備份 v0128 → 換 v0129 → ② 「登記 VRN_SystemManager_v0238.py sha 相符」→ **只落 v0239 + 驗證器 v0102**(其餘 11 個已在且 hash 同)→ ⑧ 完成 · ⑨ 只送 VRN-2 船包(本機另有 1 個提交不代推)· ⑪ 綠;第 2 次 本機已是 v0129 · ② 登記 v0239 sha 相符 · ⑨ 已是最新 | `logs/run_0_v0128_before.log` · `oneclick_cmd_oneliner_run1_from_v0128_wrong_VIA_ROOT.log` · `oneclick_cmd_oneliner_run2.log` |
| 一行的竄改測試 | 分支上的一鍵程式碼被改一個字 → SHA-256 不對 → **不執行** | `logs/oneclick_cmd_oneliner_tamper.log` |
| 只跑啟動器(不經 PS)· VIA_ROOT 指到別的夾 | ② 黃「來源 git 倉裡找到 · 登記 VRN_SystemManager_v0239.py sha 相符 · VIA_ROOT … 那裡沒有 VRN-2 程式夾 → 不用」· ⑧ 完成 · ⑪ 綠 | `logs/run_launcher_only_wrong_VIA_ROOT.log` |
| 新電腦(從遠端 clone) | 第 1 次(沒設 git 使用者)② 綠「船包清單的管理器 VRN_SystemManager_v0239.py 下一步依船包補回」· 船包補回 **18/18** · ⑧ 完成 · ⑪ 綠 · ⑨ 黃(一行寫明要跑的 git config);第 2 次(設了)② 登記 v0239 sha 相符 · ⑨ 上船 · 四本冊與原機逐位元相同 | `logs/run_new_machine_clone_1_no_git_user.log` · `run_new_machine_clone_2_git_user.log` |
| U/I 真瀏覽器(Chromium) | **35/35**(頁面每一格 = 年度數據冊那一筆 4,905 / 4,905 · 指紋相同才套用 · 指紋不同不套用) | `logs/ui_test.log` · `shots/` |

## 重跑方法

`vrn2_test_tools_v0129.zip`:`tools/e2e129.sh z|u`(z = 從 v0128 升級 · u = 使用者機器情境 · 一次跑完前置 + 一行)→ `tools/verify_mutation_suite.py <output> <scope_in> 3000`(含 `cmp_hdr.py` · `cmp_sec.py` · fixture `HDRROWS_v0237_output.json` · `SECROWS_v0238_output.json`)→ `tools/sec_audit.py <output> <scope_in>`(SECTION 稽核)→ `node tools/ui_test.js <VRN2_UI_latest.html> <截圖夾> <output>`(`NODE_PATH` 指到 playwright)。
組裝:`tools/make_mgr_v0239.py <src 夾>` · `tools/make_verifier_v0102.py <v0101> <輸出>` · `tools/build_v0129.py <v0121 啟動器> <src 夾> <v0121 內嵌原件夾> <輸出>` · `tools/pack129.sh` + `tools/regen129.py`(一鍵程式碼 / 一行 / 雜湊一起換 · 從 v0128 的 md 重新產生)。
`fixture/TESTSTUB_VRN_SystemManager_v0230.py` 只代表使用者機器上的前版鏈,**不可放進 functional modules/VRN**。

## 沒驗到的(不寫成綠)

Windows PowerShell 5.1 本身(容器是 pwsh 7.4 · 一鍵程式碼掃過沒有 7 才有的語法)· `vrn2://` 註冊與自動開 U/I(Windows)· OCR 隔離環境 · ③ 補裝(容器 `--no-install` → ③ 紅 · 不擋 ⑧)· 使用者機器 52 份(請貼回 ② / ③b / ⑨ / ⑪ 那幾行與驗證摘要;⑪ 若出現 SECFAIL / HDRVAL → 管理器沒改到的並排表 / 表頭列)。
