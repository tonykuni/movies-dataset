# VIA 天青智流 AzureFlow 整合測試結果

## 結論

本次已完成本地與受控 fixture 的整合驗證。v1.2.0 complete-system report 的技術 QA 判定為 **PASS**；在目前非 Windows sandbox 的環境限制下，整體 operational review 判定為 **PASS_WITH_REVIEW**。

## 指標矩陣

| 測試面向 | 結果 | 證據 |
|---|---:|---|
| Manifest checks | PASS，7/7 | `reports/VIA_AzureFlow_QA_System_Report.json` |
| AzureFlow inspect | PASS，exit 0 | `reports/VIA_AzureFlow_QA_System_Report.json` 的 `qa.actions.inspect` |
| ZIP verify | PASS，exit 0 | `reports/VIA_AzureFlow_QA_System_Report.json` 的 `qa.actions.verify` |
| Standardized validator | PASS，14/14 | system report `validator_summary` |
| Full-validation cases | 15 cases | `reports/cases.tsv` |
| Full-validation exit 0 | 9 cases | `reports/cases.tsv` |
| Expected negative／boundary | 6 cases，exit 1 | `reports/VIA_AzureFlow_QA_Full_Validation_20260920.md` |
| Safety defaults | PASS | source write/delete、network、default code execution 均為 false |
| Windows Task Scheduler | READY，未在 sandbox 實際註冊 | system report `scheduling`／`activation` |
| Human review | REQUIRED | activation gate 尚未完成 |

## Expected boundary cases

下列 exit code `1` 是安全閘門或輸入邊界的預期結果，不是把錯誤當作成功：

- incomplete standardized fixture
- missing workspace/root
- missing ZIP path
- VIA negative fixture
- Plug-in ZIP 送入 VIA application validator
- incomplete／ambiguous standardized auto-detection fixture

## Security validation

本次整合不會修改使用者來源檔案，不會自動執行來源附件，不會自動註冊排程，不會自動啟用命令，也不會 promotion SSOT。`--run-extracted-e2e` 僅在受控本地 fixture 上明確 opt-in，並在 JSON summary 中揭露 execution flag。

## Windows handoff

在實際 Windows 主機上，請以 `plugin/references/windows_installation_deployment_manual.md` 為準，先驗證 ZIP checksum，再執行 `Invoke-VIAAzureFlowQASystem.ps1`。只有經人工審核後才可使用 `-ActivateSchedule`；本 repository branch 不宣稱已完成 Windows Task Scheduler 真機註冊。
