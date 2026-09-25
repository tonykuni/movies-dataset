# VIA 天青智流 AzureFlow QA Plug-in
## 完整驗證測試、執行輸出與記錄報告

**驗證時間：** 2026-09-20（Asia/Taipei）
**Plug-in 版本：** 1.1.0
**驗證範圍：** `inspect`、`verify`、`all`、ZIP／checksum／HTML／Node syntax／standardized package／scheduled runner／Windows 文件與 PowerShell 契約
**最終 Plug-in ZIP：** `VIA_AzureFlow_QA_Plugin_Standalone.zip`
**ZIP SHA-256：** `b8f62b8215af2c0812cb07ebf30439b33f986d2d8fcbb07748fb4376e47a350a`

## 1. 結論

本次 Plug-in 完整驗證已完成。**所有正向功能路徑均通過**：AzureFlow v8 live inspection、standardized package 的自動分類與驗證、完整 `all` handoff、受控 packaged E2E opt-in，以及 scheduled runner simulation 均取得 PASS。負向測試也得到預期的 FAIL 或 REVIEW_REQUIRED，沒有把缺少輸入、未掛載路徑或錯誤 package 類型誤報為成功。

驗證過程中發現並修正一項路由問題：standardized package 本身依法包含 `ui/VIA-UI-Standalone-NoServer.html`，舊版 `auto` 分類會先看到 UI 檔而誤選 VIA validator。現在 `auto` 會先辨識 ZIP 根目錄的單一 `manifest.json`，再以 UI marker 作為 VIA fallback；source 與最終解壓 ZIP 都已重新測試通過。

## 2. 正向驗證矩陣

| 驗證項目 | 結果 | 實際證據 |
|---|---:|---|
| Python scripts syntax compile | PASS | Plug-in 解壓副本所有 Python scripts 通過 `py_compile` |
| `quick_validate.py` | PASS | source skill 與最終解壓 skill 均為 `Skill is valid!` |
| Standalone HTML UI smoke | PASS | 12,456 bytes；1 個 inline script；3 個 actions；Node syntax PASS |
| 互動架構圖 smoke | PASS | HTML、inline JS、Mermaid source、PNG 449,682 bytes 均通過 |
| Task Scheduler contract | PASS | runner、registration、test harness、CMD wrapper、manifest、manual 均 PASS |
| Auto detection regression | PASS | source 與解壓 ZIP 均將 standardized PASS fixture 判定為 `standardized`；VIA negative／Plug-in boundary 判定為 VIA fallback |
| Live `inspect` | PASS | `http://127.0.0.1:8766`；API、SSOT、jobs、dashboard、artifact report 均成功產生 |
| `verify` standardized PASS fixture（auto） | PASS | 14/14 checks；SHA-256、path safety、CRC、manifest、UI、Node、E2E report、JUnit、legacy boundary 均 PASS |
| `all` standardized PASS fixture（auto） | PASS | `inspect=PASS`、`verify=PASS`、combined summary=PASS；14/14 validator checks |
| `--run-extracted-e2e` opt-in | PASS | 15/15 checks；bundled E2E 與 packaged E2E 均 54/54 PASS |
| Scheduled runner simulation | PASS | `task_result.json` exit code 0；`task_scheduler.log` status=PASS；`inspect=PASS`、`verify=PASS` |
| Windows manual／PowerShell static contract | PASS | 手冊章節、命令參數、entrypoints、logs、task result 與安全旗標一致 |

### 2.1 `all` 正向 handoff

`all` 正向結果的 combined summary 為 `VIA_AZUREFLOW_QA_PLUGIN_RUN/1.0`，其中 `inspect` 與 `verify` 均為 PASS，並保留輸入路徑、validator 路徑、輸出路徑、exit code 與安全旗標。詳見 [standardized PASS 的 all summary](</home/ubuntu/work/reconstruction/VIA_AzureFlow_QA_Full_Validation_20260920/all_standardized_pass_auto/VIA_AzureFlow_QA_Run_Summary.json>)。

### 2.2 Packaged E2E opt-in

正常預設流程不執行解壓後的程式；本次另以本地建立、受控的 standardized fixture 明確指定 `--run-extracted-e2e`，用來驗證 opt-in 分支。結果為 15/15 validator checks，包含 `e2e_report: total=54, passed=54, failed=0` 與 `packaged_e2e: total=54, passed=54, failed=0`。該分支的直接 verify summary 明確標記 `run_extracted_e2e=true` 與 `code_execution=true`，不代表已執行使用者提供的來源檔案。詳見 [opt-in verification JSON](</home/ubuntu/work/reconstruction/VIA_AzureFlow_QA_Full_Validation_20260920/standardized_pass_e2e_opt_in/verify/verify/verification.json>)。

## 3. 負向與邊界驗證矩陣

| 測試 | 結果 | 預期語義與原因 |
|---|---:|---|
| Incomplete standardized fixture | FAIL（預期） | fixture 缺少完整 `profiles/industry-profile.json` 等契約內容，validator 回報 standardized contract failure，而非誤報 PASS |
| VIA negative fixture | FAIL（預期） | 找不到 `ui/VIA-UI-Standalone-NoServer.html`，在 package-root gate 停止 |
| Plug-in ZIP 送入 VIA all-in-one validator | FAIL（預期） | Plug-in 是 skill bundle，不是 VIA standalone application package；自我驗證應使用 `quick_validate`、ZIP integrity 與解壓 package check |
| Missing ZIP path | FAIL（預期） | `NOT_MOUNTED_IN_SANDBOX`；validator 未啟動，回傳明確錯誤 |
| Missing workspace/root path | REVIEW_REQUIRED（預期） | `NOT_MOUNTED_IN_SANDBOX`；仍產生 inspection report，但不宣稱已完成真實資料夾盤點 |

這些負向結果是安全閘門的成功證據：缺少 Windows 路徑或錯誤 package 不會被自動轉為成功狀態。完整案例矩陣與每個 stdout／stderr 位置保存在 [full validation evidence directory 的 cases.tsv](</home/ubuntu/work/reconstruction/VIA_AzureFlow_QA_Full_Validation_20260920/cases.tsv>)。

## 4. Scheduled runner 與 Task Scheduler 輸出

Linux sandbox 沒有 `pwsh`、`powershell` 或 `schtasks`，因此本次沒有宣稱已在 Windows Task Scheduler 真實註冊或觸發工作。已完成三層替代驗證：PowerShell／CMD 靜態契約、跨平台 scheduled runner simulation，以及受控 standardized PASS fixture 的完整 `All` 執行。

最新 simulation 產出 `VIA_AZUREFLOW_QA_TASK_RUN/1.0`，`status=PASS`、`exit_code=0`，並產生下列記錄：

- `task_result.json`：含 action、開始／結束時間、輸出目錄、summary、log、launcher output 與安全旗標。
- `task_scheduler.log`：記錄 `simulated scheduled run status=PASS`。
- `launcher_output.txt`：記錄 `inspect=PASS`、`verify=PASS`。
- `VIA_AzureFlow_QA_Run_Summary.json`：combined `All` summary，兩個 action 均 PASS。

詳見 [scheduled task result](</home/ubuntu/work/reconstruction/VIA_AzureFlow_QA_Scheduled_Simulation/All-20260919_173505/task_result.json>)、[scheduled log](</home/ubuntu/work/reconstruction/VIA_AzureFlow_QA_Scheduled_Simulation/All-20260919_173505/task_scheduler.log>) 與 [launcher output](</home/ubuntu/work/reconstruction/VIA_AzureFlow_QA_Scheduled_Simulation/All-20260919_173505/launcher_output.txt>)。

## 5. 安全驗證

預設與 live inspection 路徑的安全旗標均為：`source_write=false`、`source_delete=false`、`code_execution=false`、`network=false`；inspection 僅使用 localhost GET，沒有重啟 AzureFlow server。`human_review_required=true` 仍保留，Plug-in 不會自動提升 SSOT、不會啟動命令、不會執行使用者附件程式碼，也不會進行外部網路動作。

`--run-extracted-e2e` 是明確 opt-in 的例外測試分支。本報告中的 opt-in E2E 只使用本地建置的測試 fixture runner，並在結果中揭露 execution flag；不應把該結果解讀為使用者來源檔案已被執行。

## 6. 最終交付檔案

| 交付物 | 說明 |
|---|---|
| [Plug-in standalone ZIP](</home/ubuntu/work/reconstruction/VIA_AzureFlow_QA_Plugin_Standalone.zip>) | 最終可攜式 Plug-in，22 ZIP entries、469,743 bytes、606,842 bytes uncompressed |
| [ZIP SHA-256 sidecar](</home/ubuntu/work/reconstruction/VIA_AzureFlow_QA_Plugin_Standalone.zip.sha256>) | `sha256sum -c` 已通過 |
| [完整 QA validation report](</home/ubuntu/work/reconstruction/VIA_AzureFlow_QA_Full_Validation_20260920.md>) | 本報告 |
| [Raw validation evidence](</home/ubuntu/work/reconstruction/VIA_AzureFlow_QA_Full_Validation_20260920/cases.tsv>) | 15 個主案例的 exit code 與 stdout 路徑 |
| [Raw evidence ZIP](</home/ubuntu/work/reconstruction/VIA_AzureFlow_QA_Full_Validation_20260920_Evidence.zip>) | 包含 full validation、negative／positive summaries、opt-in E2E 與 scheduled records |
| [Evidence ZIP SHA-256](</home/ubuntu/work/reconstruction/VIA_AzureFlow_QA_Full_Validation_20260920_Evidence.zip.sha256>) | Evidence archive 的 checksum sidecar |
| [Windows installation and deployment manual](</home/ubuntu/skills/via-azureflow-qa-plugin/references/windows_installation_deployment_manual.md>) | Windows 安裝、PowerShell launcher、HTML UI、Task Scheduler、故障排除 |
| [ZIP inventory and browser inspection](</home/ubuntu/work/reconstruction/VIA_AzureFlow_QA_Plugin_Standalone_Inventory_20260920.md>) | ZIP 目錄、大小、checksum、架構圖預覽檢查 |
| [Integration report](</home/ubuntu/work/reconstruction/VIA_AzureFlow_QA_Plugin_Integration_Report_20260920.md>) | Plug-in 架構、三 actions、Windows automation 與交付摘要 |

## 7. Windows 真機下一步

若要完成 Windows 真機驗收，請在具備 PowerShell 7 與 Task Scheduler 的 Windows 主機解壓 ZIP，先依手冊執行 checksum，接著執行 `Invoke-VIA-AzureFlowQA.ps1 -Action All` 或以 `Register-VIAAzureFlowQATask.ps1` 建立測試任務。對使用者的四個實際 Windows 文件，仍必須在原始路徑可讀取的 Windows 主機上執行；本次 sandbox 結果沒有把未掛載路徑誤稱為真實文件 PASS。

**最終判定：PASS（本地與受控 fixture 範圍）；Windows 真機 Task Scheduler 執行：尚未在本 sandbox 執行。**
