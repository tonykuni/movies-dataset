# VRN-2 v0122 驗證紀錄(2026-10-18 · Claude Code 雲端容器)

發行檔:`ActivateVRN-2_v0122.zip`(內含 `ActivateVRN-2.py` · SHA-256 見 `VRN2_Release_v0122.json`)。交接報告:`../VRN2_Handover_v0122.md`。

## 輸出值驗證(同一個獨立驗證器 · pdfplumber + pypdfium2 · 不 import VRN-2 程式)

| 冊 | v0121 輸出 | v0122 輸出 |
|---|---|---|
| 基本資料(14 份 · 145 欄) | 135 過 · **10 錯**(TEL 7 · 分析師 2 · Email 1) | **145 過 · 0 錯** |
| 年度數據 | 4,185 筆:對欄 3,949 · 人工核對正確 24 · **不是單一值 210 · 錯欄 2** | 3,973 筆:對欄 3,949 · 人工核對正確 24 · **錯值 0** · 212 筆進剔除冊(帶理由) |
| 一標題四重點 | 容器無 PyMuPDF → BLOCKED | 同左 → BLOCKED(使用者機器驗) |

報告:`verify_report.json`(v0122)· `verify_report_v0121_baseline.json`(v0121)· `logs/verify.log` · `logs/verify_v0121_baseline.log`。

## 自測 / 實測

| 項目 | 結果 | 證據 |
|---|---|---|
| 啟動器 v0122 自測 | 12/12 | `logs/launcher_selftest.log` |
| 管理器 v0231 / v0232 自測 | 33/33 · 11/11 | `logs/run_cold.log` |
| ENG397 v0127 自測(無 PyMuPDF) | 34/34(v0126 為 33/34 → 被隔離) | `logs/run_cold.log` · `logs/run_v0121_original_no_fitz.log` |
| 完整實跑(冷 / 熱) | 43 秒 / 32 秒 · 平行段 6 步 3 路 · 新增九頭龍頭 0 · 四本冊連跑逐位元相同 | `logs/run_cold.log` · `logs/run_warm.log` |
| U/I 真瀏覽器(Chromium) | 20/20 | `logs/ui_test.log` · `shots/*.png` |
| ⑨ 上船 / ⑩ 封存(測試樹 + 假完成) | 11 檔含前版鏈 · 新 clone 尾版自測 rc 0 · 保留 GitHub 上的 ENG062 v0103 | `logs/ship_test.log` · `logs/clone_selftest.log` |

## 重跑方法

`vrn2_test_tools_v0122.zip`:`tools/mktree.sh`(建測試樹:repo 內 19 份 PDF + 管理器前版 stub)→ `tools/runl.sh`(跑啟動器 · `--no-install`)→ `tools/verify_outputs.py <output> <scope_in> <報告.json>` → `node tools/ui_test.js <VRN2_UI_latest.html> <截圖夾>`(`NODE_PATH` 指到 playwright)→ `tools/ship_test.py <啟動器> <樹>`。
`fixture/TESTSTUB_VRN_SystemManager_v0230.py` 只代表使用者機器上的前版鏈,**不可放進 functional modules/VRN**。

## 沒驗到的(不寫成綠)

⑤ 一標題四重點(需要 PyMuPDF)· `vrn2://` 註冊(Windows)· OCR 隔離環境 · ③ 補裝 · Parquet(無 pyarrow)· 使用者機器管理器鏈(v0228 為前版)。
