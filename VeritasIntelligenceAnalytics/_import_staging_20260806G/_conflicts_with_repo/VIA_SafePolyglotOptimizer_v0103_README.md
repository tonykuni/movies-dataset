# VIA Safe Polyglot Optimizer AIO v0103

整合目標：將 supportive modules 內的 Central Governance、NexusCore、Polyglot Check-Test-Repair、SafePolyglot、EngineForge、VAP orchestrator、ChartSpec registry、Unified Veritas data 與 governance report 納入同一個安全治理入口。

## 安全原則

- 預設 report-only。
- 不刪檔、不清回收筒、不 Stop-Process。
- 不修改全域 PATH / Profile / venv / node_modules / .git / .vscode。
- 所有檔案先複製到 sandbox，再做靜態檢查與 HTML Matrix。
- 額外 15 個各語言交叉加速器只註冊為矩陣與建議，不自動安裝、不自動套用。

## 一鍵安全啟動

```powershell
$BaseDir = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules"

pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass `
  -File "$BaseDir\Invoke-VIA-SafePolyglotOptimizer-AIO-v0103.ps1" `
  -SelfTest `
  -RegisterLauncher `
  -OpenReport
```

## 沙盒子腳本自測

只在 HTML 報告確認後使用：

```powershell
$BaseDir = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules"

pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass `
  -File "$BaseDir\Invoke-VIA-SafePolyglotOptimizer-AIO-v0103.ps1" `
  -SelfTest `
  -RegisterLauncher `
  -OpenReport `
  -RunSandboxSelfTest
```

## 主要輸出

- `_via_safe_polyglot_optimizer/RUN_*`
- `reports/VIA_SafePolyglotOptimizer_Matrix_Report.html`
- `04_ToolMatrix_Top15.csv/json`，含額外 Cross Accelerating Extra 15
- `_nexus_registry/VIA_SAFE_POLYGLOT_OPTIMIZER_REGISTRY.json`
- `_nexus_registry/VIA_SAFE_POLYGLOT_OPTIMIZER_ACTIVE_POINTER.json`
