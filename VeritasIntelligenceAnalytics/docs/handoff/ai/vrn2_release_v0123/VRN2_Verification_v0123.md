# VRN-2 v0123 驗證紀錄(2026-10-18 · Claude Code 雲端容器 · 獨立系統收尾)

發行檔:`ActivateVRN-2_v0123.zip`(內含 `ActivateVRN-2.py` · SHA-256 見 `VRN2_Release_v0123.json`)· 交接報告:`../VRN2_Handover_v0123.md`。

| 項目 | 結果 | 證據 |
|---|---|---|
| 啟動器自測 | 15/15 | `logs/launcher_selftest.log` |
| 管理器鏈自測 | v0231 33/33 · v0232 11/11 · v0233 6/6 | `logs/run_complete_1.log` |
| 完整實跑(有 PyMuPDF 的隔離測試環境) | ⑧ VRN-2 完成 · 紅 0 · 黃 7 → ⑨ 船包 11 檔 → ⑩ | `logs/run_complete_1.log` |
| 再跑一次 | ⑨ GitHub 已是最新 · 船包無變更 | `logs/run_complete_2.log` |
| 新電腦(從 GitHub clone) | ② 船包補回 11/11 → ⑧ 完成 → ⑨ | `logs/run_new_machine_clone.log` |
| ⑨ 提交內容 | 只有 vrn2_ship 船包 + 清單 + 交接報告 · functional modules 0 檔 | `logs/ship_commit.log` |
| 輸出值獨立驗證 | 基本資料 189/189 · 一標題四重點 62/62 · 年度數據 3,973 筆(3,949 對欄 + 24 人工)· 錯值 0 | `verify_report.json` · `logs/verify.log` |
| U/I 真瀏覽器 | 20/20 | `logs/ui_test.log` · `shots/` |

重跑方法:`vrn2_test_tools_v0123.zip`(`tools/mktree.sh` → `tools/runl.sh`(`PY=` 指定有 PyMuPDF 的 python)→ `tools/verify_outputs.py` → `tools/ui_test.js` → `tools/ship_test.py`)。
`fixture/TESTSTUB_VRN_SystemManager_v0230.py` 只代表使用者機器上的前版鏈:**不可放進 functional modules\VRN,測試樹產生的船包也不可提交**(真正的船包只由使用者機器的 ⑨ 產生)。

沒驗到(不寫成綠):`vrn2://` 註冊(Windows)· OCR 隔離環境 · ③ 補裝 · 使用者機器的管理器鏈(v0228 為前版)。
