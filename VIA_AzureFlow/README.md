# VIA 天青智流 AzureFlow

這個區域收斂已完成整合測試的 **VIA AzureFlow QA Plug-in v1.2.0**、Windows 操作入口、可重跑的 system report review skill、可攜式 ZIP 與測試證據。它可獨立使用，也可作為 `tonykuni/movies-dataset` 母系統的外掛區域。

## Repository placement

- **Git branch：** `VIA_AzureFlow`
- **Repository：** `tonykuni/movies-dataset`
- **Area：** `VIA_AzureFlow/`
- **Canonical readable plug-in source：** [`plugin/`](plugin/)
- **Reusable report-review skill：** [`skills/via-azureflow-system-report-review/`](skills/via-azureflow-system-report-review/)
- **Portable packages：** [`packages/`](packages/)
- **Reports and test records：** [`reports/`](reports/)
- **Raw validation evidence：** [`evidence/`](evidence/)

## Quick start on Windows

1. 先依 `plugin/references/windows_installation_deployment_manual.md` 驗證 Portable ZIP 的 SHA-256。
2. 解壓 `packages/VIA_AzureFlow_QA_Plugin_Standalone.zip`。
3. 在 PowerShell 7 執行：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\Invoke-VIAAzureFlowQASystem.ps1 `
  -Root "C:\path\to\workspace" `
  -Zip "C:\path\to\package.zip"
```

4. 只有在人工審核並且確定要啟用 Windows Task Scheduler 時，才明確加入 `-ActivateSchedule`。預設不會註冊排程。
5. 可使用 [`plugin/templates/VIA_AzureFlow_QA_Standalone.html`](plugin/templates/VIA_AzureFlow_QA_Standalone.html) 進行滑鼠／拖曳式本地操作；UI 不依賴外部 CDN。

## Three QA actions

| Action | 目的 | 預設行為 |
|---|---|---|
| `inspect` | 唯讀檢查 AzureFlow API、SSOT、jobs、dashboard 與 artifacts | 只允許指定 localhost GET |
| `verify` | 驗證 VIA／standardized ZIP、checksum、path safety、UI 與契約 | 不執行來源附件 |
| `all` | 依序執行 inspect、verify 並產生 combined handoff summary | 保留 stdout、stderr、summary 與安全旗標 |

## Test status

Canonical complete-system report 的技術狀態為 **PASS**：manifest `7/7`、`inspect=PASS`、`verify=PASS`、standardized validator `14/14`。完整 15-case matrix 中有 9 個 exit code `0` 與 6 個預期的 negative／boundary case；這 6 個案例沒有被誤報為成功。

整體 review 判定為 **PASS_WITH_REVIEW**，原因是 sandbox 不是 Windows，Task Scheduler 尚未真機註冊，activation 仍是 `READY_FOR_WINDOWS_ACTIVATION`，且必須保留人工審核。這不表示整合 QA failure。

請先閱讀 [`reports/VIA_AzureFlow_QA_System_Report_Detailed_Review_20260920.md`](reports/VIA_AzureFlow_QA_System_Report_Detailed_Review_20260920.md)，再查看 [`reports/VIA_AzureFlow_QA_Full_Validation_20260920.md`](reports/VIA_AzureFlow_QA_Full_Validation_20260920.md)。

## Safety defaults

- `source_write=false`
- `source_delete=false`
- `code_execution=false`，只有受控 packaged E2E 且明確 opt-in 才例外
- `network=false`
- inspect 僅可使用指定 localhost GET
- 不自動啟用 command、不自動 promotion SSOT、不改寫來源文件

## Important provenance note

`reports/VIA_AzureFlow_QA_System_Report.*` 是 v1.2.0 complete-system run 的 system report。`reports/VIA_AzureFlow_QA_Full_Validation_20260920.md` 保留先前完整驗證矩陣，並在 detailed review 中標示其版本／ZIP hash drift；請以 v1.2.0 system report、`plugin/plugin_manifest.json` 及 [`EXPORT_MANIFEST.json`](EXPORT_MANIFEST.json) 作為本 branch 的 canonical export metadata。

## Contents

See [`EXPORT_MANIFEST.json`](EXPORT_MANIFEST.json) for the generated file inventory, SHA-256 values, source provenance, QA metrics and branch metadata.
