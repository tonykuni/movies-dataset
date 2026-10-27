# VRN-2 v0124 驗證紀錄(2026-10-18 · Claude Code 雲端容器)

發行檔:`ActivateVRN-2_v0124.zip`(內含 `ActivateVRN-2.py` · SHA-256 見 `VRN2_Release_v0124.json`)。交接報告:`../VRN2_Handover_v0124.md`。日誌(`logs/*.log`)在 `logs_v0124.zip`(repo 的 .gitignore 不收 *.log)。

## 輸出值驗證(獨立驗證器 · 不 import VRN-2 程式)

| 冊 | v0123 輸出 | v0124 輸出 |
|---|---|---|
| 基本資料(14 份) | 189 欄過 · 0 錯 | **194 欄過 · 0 錯**(+ 電話 3 份 · 華南目標價 / 上漲空間) |
| 一標題四重點 | 62 過 · 0 錯 | **63 過 · 0 錯** |
| 年度數據 | 3,973 筆(對欄 3,949 · 人工核對 24)· 剔除 212 | **4,425 筆**(對欄 3,949 · 人工核對 24 · **子欄對位 452**)· **錯值 0** · 剔除 74 |

- 子欄(`SUBCOL`)用第三種讀法另查(pdfplumber 字詞框 · VRN-2 拆分用的是 pypdfium2):① 整列數值序列 = 原文那一列 ② 期間 = 數據列上方最近的期間表頭 ③ 同期間子欄標籤不重複 ④ 期間表頭落在該組值的範圍內 ⑤ 子欄標籤 = 離值最近的子表頭字。
- **驗證器反向測試**(`subcol_mutation_test.py`):把開發中真的出過的 4 種錯放回輸出 → 全部抓到(中點分組錯 16 筆 · 季度段標成年度 9 筆 · 標籤對調 12 筆 · 少拆一個值 8 筆);原樣 0 錯。

報告:`verify_report.json` · `logs/verify.log` · `logs/subcol_mutation_test.log`。

## 自測 / 實測

| 項目 | 結果 | 證據 |
|---|---|---|
| 啟動器 v0124 自測 | 15/15 | `logs/launcher_selftest.log` |
| 管理器 v0231 / v0232 / v0233 / v0234 自測 | 33/33 · 11/11 · 6/6 · 14/14 | `logs/run_complete_1.log` |
| 完整實跑(新樹) | ⑧ 完成 · 紅 0 · 黃 7 · ⑨ 船包 12 檔 · 約 75 秒 | `logs/run_complete_1.log` |
| 再跑一次 | ⑨ 船包無變更 · 四本冊逐位元相同 | `logs/run_complete_2_no_change.log` |
| 從 v0123 升級 | 只落 v0234 + ENG062 v0114 · ⑧ 完成 · ⑩ 封存 ENG062 v0113 · 四本冊與新樹逐位元相同 | `logs/run_upgrade_1_v0123.log` · `logs/run_upgrade_2_v0124.log` |
| 新電腦(從 GitHub clone) | ② 船包補回 12/12 · ⑧ 完成 · 四本冊與原機逐位元相同 | `logs/run_new_machine_clone.log` |
| ⑨ 提交內容 | 船包 + 清單 + 交接報告 · functional modules 0 檔 | `logs/ship_commit.log` |
| U/I 真瀏覽器(Chromium) | 21/21(新增子欄拆分分頁) | `logs/ui_test.log` · `shots/ui_subcol.png` |

## 重跑方法

`vrn2_test_tools_v0124.zip`:`tools/mktree.sh <樹> <啟動器>` → `PY=<python> tools/runl.sh <樹>` → `tools/verify_outputs.py <output> <scope_in> <報告.json>` → `tools/subcol_mutation_test.py <output> <scope_in>` → `node tools/ui_test.js <VRN2_UI_latest.html> <截圖夾>`(`NODE_PATH` 指到 playwright)→ `tools/upgrade_test.sh <樹> <v0123> <v0124>`。
組裝:`tools/build_v0124.py <v0121 啟動器> <src 夾> <v0121 內嵌原件夾> <輸出>`。
`fixture/TESTSTUB_VRN_SystemManager_v0230.py` 只代表使用者機器上的前版鏈,**不可放進 functional modules/VRN**。

## 沒驗到的(不寫成綠)

`vrn2://` 註冊(Windows)· OCR 隔離環境 · ③ 補裝(容器 `--no-install` → ③ 紅 · 不擋 ⑧)· 使用者機器管理器鏈(v0228 為前版)。
