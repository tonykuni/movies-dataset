# VIA Central Governance · Adaptive Downward Governor v0100

本套件補強 VIA Central Governance 的「自適應向下治理」：從根目錄遞迴到子系統、模組、函式與介面契約，執行三輪全景分析、沙盒安全修補、依賴序同步、SSOT 對齊、Hydra 偵測與 HTML RYG 矩陣報告。

## 安全邊界

- 原始 canonical 檔案只讀，不覆寫、不刪除、不改名。
- 修補只寫入每次執行的 `sandbox` 鏡像。
- Hydra／高風險節點只產生建議與 review queue。
- 所有證據使用 append-only JSONL，並於結束時驗證母檔 SHA-256 未變。
- 不自動安裝套件、不啟用正式 runtime、不執行網路擷取。

## Windows PowerShell 7

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
& "<套件路徑>\Invoke-VIA-CentralGovernance-AdaptiveDownward-v0100.ps1" `
  -BaseRoot "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics" `
  -Rounds 3 `
  -ActivateSandbox `
  -OpenReport
```

`-PreviewOnly` 只建立等內容沙盒與報告，不套用 allowlist 修補。未加 `-ActivateSandbox` 時，不執行核心模組 self-test。

## Python

```powershell
& "C:\Users\tonyk\envs\via_core_312\Scripts\python.exe" `
  ".\VIA_CentralGovernment_AdaptiveDownwardGovernor_v0100.py" `
  --base-root "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics" `
  --output-root "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\_via_adaptive_downward_runs" `
  --rounds 3 `
  --apply-safe-fixes `
  --activate-sandbox
```

## 主要輸出

- `VIA_Adaptive_Final_Matrix.html`
- `VIA_Adaptive_Final_Summary.json`
- `VIA_Adaptive_Final_Snapshot.json`
- `VIA_Canonical_Integrity.json`
- `VIA_Adaptive_Evidence_Ledger.jsonl`
- `reports/Round_1_Matrix.html` 至 `Round_3_Matrix.html`
- `sandbox/`：只在沙盒修正後的候選版本與治理相容層
