# VIA 天青智流 AzureFlow QA Plug-in
## v1.2.0 Portable ZIP 完整 Inventory

**ZIP：** `VIA_AzureFlow_QA_Plugin_Standalone.zip`
**內部根目錄：** `via-azureflow-qa-plugin/`
**檔案數：** 20
**ZIP entries：** 20 個檔案 entries，沒有額外 root-level duplicate
**ZIP size：** 478,787 bytes
**SHA-256：** `8fe8611105881dfae4dd0ff395fbd47cea8f853c82c2baba281515620e89c4e3`
**CRC／解壓：** PASS
**`__pycache__`：** 已排除

## 1. 檔案清單

| 相對路徑 | bytes | 類型與責任 |
|---|---:|---|
| `Invoke-VIA-AzureFlowQA.ps1` | 1,752 | 相容三 action Windows launcher |
| `Invoke-VIAAzureFlowQASystem.ps1` | 5,629 | manifest-driven complete-system Windows launcher；明確 `-ActivateSchedule` |
| `Run-VIAAzureFlowQAScheduled.cmd` | 992 | Task Scheduler 可直接指定的 CMD wrapper |
| `SKILL.md` | 10,524 | 可重用 Manus skill 工作流與安全規範 |
| `plugin_manifest.json` | 3,650 | v1.2.0 單一契約、actions、system mode、entrypoints、outputs、safety |
| `references/VIA_AzureFlow_Windows_Deployment_Architecture.mmd` | 2,955 | Mermaid 部署架構與 complete-system flow |
| `references/VIA_AzureFlow_Windows_Deployment_Architecture.png` | 450,164 | Mermaid rendered PNG |
| `references/integration_contract.md` | 7,020 | 三 action、system report、activation result、UI 與 acceptance contract |
| `references/windows_installation_deployment_manual.md` | 34,605 | Windows 安裝、launcher、system mode、Task Scheduler、故障排除 |
| `scripts/Invoke-VIA-AzureFlowQA-Scheduled.ps1` | 6,003 | timestamped scheduled runner、log、task result |
| `scripts/Register-VIAAzureFlowQATask.ps1` | 4,607 | 建立、更新、移除 Windows Task Scheduler task |
| `scripts/Test-VIAAzureFlowQATask.ps1` | 3,852 | direct runner／registered task smoke test harness |
| `scripts/inspect_azureflow.py` | 23,845 | AzureFlow v8 API、SSOT、jobs、runs、dashboard 唯讀檢查 |
| `scripts/validate_standardized_package.py` | 6,961 | standardized package directory validator |
| `scripts/validate_standardized_zip.py` | 3,774 | standardized ZIP safe extractor／validator wrapper |
| `scripts/validate_via_zip.py` | 13,542 | VIA all-in-one ZIP validator |
| `scripts/via_azureflow_qa.py` | 10,956 | 相容 `inspect`／`verify`／`all` orchestrator |
| `scripts/via_azureflow_qa_system.py` | 16,931 | manifest preflight、All、readiness、system reports |
| `templates/VIA_AzureFlow_QA_Standalone.html` | 12,456 | 淺色、無 CDN、file://、拖曳 ZIP、命令預覽 UI |
| `templates/VIA_AzureFlow_Windows_Deployment_Interactive.html` | 20,747 | 可點選節點的部署架構圖，含 Complete System 導覽 |

## 2. Manifest 核心欄位

| 欄位 | 值 |
|---|---|
| `plugin_id` | `via-azureflow-qa-plugin` |
| `version` | `1.2.0` |
| `actions` | `inspect`、`verify`、`all` |
| `system_mode.id` | `complete_system` |
| `system_mode.sequence` | `manifest_preflight` → `inspect` → `verify` → `combined_handoff` → `scheduler_readiness` → `human_review_gate` |
| `system_mode.default_activation` | `READY_FOR_WINDOWS_ACTIVATION` |
| `system_mode.activation_switch` | `-ActivateSchedule` |
| `automatic_registration` | `false` |
| `ssot_promotion` | `false` |
| `automatic_command_activation` | `false` |

## 3. 入口與輸出

Complete-system 的兩個 canonical 入口如下：

```text
scripts/via_azureflow_qa_system.py
Invoke-VIAAzureFlowQASystem.ps1
```

主要輸出如下：

```text
VIA_AzureFlow_QA_System_Report.json
VIA_AzureFlow_QA_System_Report.md
activation_result.json
qa/VIA_AzureFlow_QA_Run_Summary.json
qa/inspect/VIA_AzureFlow_Engine_Job_Inspection.md
qa/verify/verification.json
```

## 4. 封裝驗證

最終 package 在 sandbox 完成以下檢查：

| 檢查 | 結果 |
|---|---:|
| ZIP `testzip()` CRC | PASS |
| `quick_validate.py` source | PASS |
| `quick_validate.py` extracted package | PASS |
| Python syntax compile | PASS |
| package root duplicate scan | PASS |
| `__pycache__` exclusion | PASS |
| Complete-system positive fixture | PASS |
| Complete-system missing ZIP semantics | PASS；非零 exit、activation BLOCKED |

## 5. Windows runtime 邊界

目前 sandbox 為 Ubuntu，沒有 Windows PowerShell／Task Scheduler runtime。因此 inventory 與 package validation 沒有虛構 Windows registration 結果。到 Windows 主機後，請先用不含 `-ActivateSchedule` 的 system run 審核 `VIA_AzureFlow_QA_System_Report.md`；只有 QA PASS 且人工 review 完成，才使用明確的 `-ActivateSchedule`。

## References

[1]: file:///home/ubuntu/skills/via-azureflow-qa-plugin/plugin_manifest.json "VIA AzureFlow QA plug-in manifest"
[2]: file:///home/ubuntu/skills/via-azureflow-qa-plugin/references/integration_contract.md "VIA AzureFlow complete-system integration contract"
[3]: file:///home/ubuntu/skills/via-azureflow-qa-plugin/references/windows_installation_deployment_manual.md "VIA AzureFlow Windows installation and deployment manual"
[4]: file:///home/ubuntu/work/reconstruction/VIA_AzureFlow_QA_Plugin_Standalone.zip "VIA AzureFlow QA Plug-in portable ZIP"
