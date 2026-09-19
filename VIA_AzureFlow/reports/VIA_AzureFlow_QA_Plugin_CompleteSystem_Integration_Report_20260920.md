# VIA 天青智流 AzureFlow QA Plug-in
## Complete System 整合交付報告

**版本：** 1.2.0
**驗證時間：** 2026-09-20 02:37（Asia/Taipei）
**交付結論：** **PASS；已收斂為單一 manifest-driven system facade。**

## 1. 結論

本次整合將原有的 `via-azureflow-inspection` 與 `via-e2e-zip-verifier` 能力，連同 Windows launcher、拖曳式 standalone HTML、Task Scheduler runner、registration script 與測試 harness，收斂到同一個 `via-azureflow-qa-plugin`。原有三個 user-facing QA actions 沒有改名，也沒有建立平行 validator；新增的 complete-system layer 只負責編排既有能力並產生單一 handoff。

完整系統的標準順序是 **manifest preflight → inspect → verify → combined handoff → scheduler readiness → human-review activation gate**。Python system layer 的預設結果是 `READY_FOR_WINDOWS_ACTIVATION`，不會自動註冊 Windows Task Scheduler。只有在真實 Windows 主機上，人工檢閱 QA PASS 後，操作者明確加入 `-ActivateSchedule`，才會呼叫既有 registration script。

## 2. 整合後架構

| 層級 | canonical 入口 | 責任 | 主要輸出 |
|---|---|---|---|
| Manifest contract | `plugin_manifest.json` | 宣告三 actions、system mode、entrypoints、outputs、safety 與 handoff schema | manifest inventory、entrypoint hash |
| 相容 QA CLI | `scripts/via_azureflow_qa.py` | 保留 `inspect`、`verify`、`all`；路由 VIA 或 standardized ZIP validator | `VIA_AzureFlow_QA_Run_Summary.json` |
| AzureFlow inspection | `scripts/inspect_azureflow.py` | 唯讀檢查 v8 API、SSOT、jobs、runs、dashboard 與 artifact | engine/job Markdown report |
| ZIP verification | `scripts/validate_via_zip.py`、`scripts/validate_standardized_zip.py` | SHA-256、path safety、CRC、package contract 與 opt-in E2E | `verification.json`、validator summaries |
| Complete system | `scripts/via_azureflow_qa_system.py` | 依 manifest 編排 All QA、排程 readiness、activation gate | system JSON／Markdown、activation result |
| Windows system launcher | `Invoke-VIAAzureFlowQASystem.ps1` | Windows path I/O、Python discovery、All QA 與明確 Task activation | `activation_result.json`、registered task status |
| Windows scheduling | `scripts/Invoke-VIA-AzureFlowQA-Scheduled.ps1`、`Register-VIAAzureFlowQATask.ps1`、`Test-VIAAzureFlowQATask.ps1` | timestamped output、Task Scheduler 註冊、直接／已註冊 task 測試 | `task_scheduler.log`、`task_result.json` |
| Mouse-first UI | `templates/VIA_AzureFlow_QA_Standalone.html`、`templates/VIA_AzureFlow_Windows_Deployment_Interactive.html` | 本地 file:// UI、ZIP 拖曳、Windows path、命令預覽、架構節點導覽 | 不直接執行來源；只產生命令 |

視覺化部署圖已同步加入 complete system facade、system report、human-review gate 與 `-ActivateSchedule` opt-in 分支；Mermaid source 與 PNG 均已重新渲染。

## 3. 三個相容 actions 與新增 system mode

| 介面 | 狀態 | 說明 |
|---|---|---|
| `inspect` | 保留 | 只做 AzureFlow／local run 唯讀檢查；API unavailable 時記錄 error 與 fallback，不重啟服務 |
| `verify` | 保留 | 先做 checksum、path safety、CRC，再依 package kind 路由 validator |
| `all` | 保留 | 依序執行 inspect 與 verify，輸出 combined handoff |
| `complete_system` | 新增 | 不取代三 actions；以 manifest 驗證、All、排程 readiness 與 activation gate 組成一條完整流程 |

## 4. 測試與除錯矩陣

| 測試項目 | 結果 | 證據或說明 |
|---|---:|---|
| Python scripts `py_compile` | PASS | unified system、既有 CLI、inspection、VIA validator、standardized validators 均可編譯 |
| `plugin_manifest.json` JSON parse | PASS | schema `VIA_PLUGIN_MANIFEST/1.0`；version `1.2.0` |
| `quick_validate.py` source skill | PASS | source skill 結構與 frontmatter 合約通過 |
| `quick_validate.py` extracted package | PASS | 最終 ZIP 解壓副本再次通過 |
| Complete-system positive run | PASS | standardized PASS fixture；system status `PASS`；manifest checks `7/7`；QA exit code `0` |
| Complete-system negative run | PASS（預期失敗語義） | missing ZIP 回傳非零；system status `FAIL`；activation `BLOCKED` |
| Standardized validator | PASS | PASS fixture `14/14` checks |
| AzureFlow inspection | PASS | live localhost API／local runs 可產生 engine/job report |
| Auto package detection | PASS | standardized 與 VIA fixture 均正確分類 |
| Standalone UI smoke test | PASS | 1 inline script、3 QA actions、drag-and-drop、無外部依賴 |
| Architecture UI smoke test | PASS | HTML、inline JS、Mermaid source、PNG 與 system node 均可解析 |
| Task Scheduler contract test | PASS | runner、registration、test harness、CMD wrapper、manifest、manual 均一致 |
| Scheduled runner simulation | PASS | PASS fixture 可建立 timestamped output、summary、task log、task result |
| Windows Task Scheduler runtime | REVIEW_REQUIRED | sandbox 是 Ubuntu，沒有 `pwsh`／`schtasks`；未虛構 Windows runtime PASS |

### 4.1 實測輸出

Positive system run 的核心結果如下：

```json
{
  "status": "PASS",
  "version": "1.2.0",
  "manifest_checks": "7/7",
  "qa_status": "PASS",
  "qa_exit_code": 0,
  "scheduling_status": "READY",
  "windows_runtime": false,
  "activation_status": "READY_FOR_WINDOWS_ACTIVATION",
  "registered": false
}
```

這個結果表示 system orchestration、package verification 與輸出契約已通過；它**不表示** sandbox 已註冊 Windows Task Scheduler。真正的 Windows activation 必須在 Windows 主機上由操作者明確執行 `-ActivateSchedule`。

## 5. 安全邊界

整合後仍維持以下預設：`source_write=false`、`source_delete=false`、`network_default=false`、`automatic_command_activation=false` 與 `ssot_promotion=false`。`inspect` 僅對明確提供的 localhost/API URL 做 GET；系統不會因服務安靜或不可用而自動重啟。`--run-extracted-e2e` 仍是 opt-in，且只有在 checksum、path safety 與 CRC 通過後才會執行 packaged test runner。

Windows Task Scheduler registration 是唯一被刻意設計成明確 opt-in 的外部狀態變更。Python system mode 不會呼叫它；PowerShell system launcher 也只有在 QA PASS 且出現 `-ActivateSchedule` 時才會呼叫。任何 SSOT promotion、command approval、source execution、network provider activation 或部署仍需要人工 review。

## 6. Portable ZIP

| 項目 | 值 |
|---|---|
| ZIP | `VIA_AzureFlow_QA_Plugin_Standalone.zip` |
| ZIP entries | 20 files；無 root-level duplicate；無 `__pycache__` |
| ZIP size | 478,787 bytes |
| SHA-256 | `8fe8611105881dfae4dd0ff395fbd47cea8f853c82c2baba281515620e89c4e3` |
| Sidecar | `VIA_AzureFlow_QA_Plugin_Standalone.zip.sha256` |
| Extracted validation | CRC PASS；quick_validate PASS；Python syntax PASS |

## 7. Windows 啟用步驟

在 Windows 主機解壓並先執行不註冊任務的 system run：

```powershell
$plugin = 'C:\VIA\plugins\via-azureflow-qa-plugin'
& "$plugin\Invoke-VIAAzureFlowQASystem.ps1" `
  -Root 'C:\VIA\work\reconstruction' `
  -Zip 'C:\VIA\delivery\VIA-All-Latest.zip' `
  -ChecksumFile 'C:\VIA\delivery\VIA-All-Latest.zip.sha256' `
  -Output 'C:\VIA\QA\system-run' `
  -NoArtifactProbe
```

人工檢閱 `VIA_AzureFlow_QA_System_Report.md` 後，才使用：

```powershell
& "$plugin\Invoke-VIAAzureFlowQASystem.ps1" `
  -Root 'C:\VIA\work\reconstruction' `
  -Zip 'C:\VIA\delivery\VIA-All-Latest.zip' `
  -ChecksumFile 'C:\VIA\delivery\VIA-All-Latest.zip.sha256' `
  -Output 'C:\VIA\QA\system-run-activated' `
  -TaskName 'VIA-AzureFlow-QA-All' `
  -Schedule Daily `
  -At (Get-Date).Date.AddHours(2) `
  -RunOnlyWhenUserIsLoggedOn `
  -ActivateSchedule
```

完成後檢查 `activation_result.json` 的 `status=ACTIVATED`、`registered=true` 與 `qa_exit_code=0`，再用 `Test-VIAAzureFlowQATask.ps1 -UseRegisteredTask` 做真正的 task smoke test。若 Windows path 不可讀、checksum 不一致或 QA 非 PASS，system launcher 會阻擋 activation。

## 8. 已知限制

本次 sandbox 沒有 Windows Task Scheduler runtime，因此沒有宣稱已完成實際 Windows task registration。使用者提供的四個原始 Windows 文件仍須在可讀取那些路徑的 Windows 主機上執行既有 real-sample launcher；sandbox fixture 的 PASS 只驗證 plug-in 契約與流程，不可被解讀成四份原始文件已完成重建。

## 9. 交付檔案

- [完整系統整合報告](./VIA_AzureFlow_QA_Plugin_CompleteSystem_Integration_Report_20260920.md)
- [Portable Plug-in ZIP](./VIA_AzureFlow_QA_Plugin_Standalone.zip)
- [ZIP SHA-256 sidecar](./VIA_AzureFlow_QA_Plugin_Standalone.zip.sha256)
- [Complete-system regression evidence ZIP](./VIA_AzureFlow_QA_CompleteSystem_Evidence_20260920.zip)
- [解壓後完整 inventory](./VIA_AzureFlow_QA_Plugin_CompleteSystem_Inventory_20260920.md)
- [Windows 安裝與部署手冊](file:///home/ubuntu/skills/via-azureflow-qa-plugin/references/windows_installation_deployment_manual.md)
- [Complete-system regression test](./test_via_azureflow_complete_system.py)

## References

[1]: file:///home/ubuntu/skills/via-azureflow-qa-plugin/plugin_manifest.json "VIA AzureFlow QA plug-in manifest"
[2]: file:///home/ubuntu/skills/via-azureflow-qa-plugin/references/integration_contract.md "VIA AzureFlow QA plug-in integration contract"
[3]: file:///home/ubuntu/skills/via-azureflow-qa-plugin/Invoke-VIAAzureFlowQASystem.ps1 "VIA AzureFlow complete system Windows launcher"
[4]: file:///home/ubuntu/skills/via-azureflow-qa-plugin/scripts/via_azureflow_qa_system.py "VIA AzureFlow complete system Python orchestrator"
