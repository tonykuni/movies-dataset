# VERITAS INTELLIGENCE ANALYTICS · Accelerated Integration v0139A

`VIA_Accelerated_Integration_v0139A` 是 v0138D 之後的新增式整合套件。它不覆寫既有 `VIA_FactSet_YFinance_Consensus_Matrix_Engine_v0111` owner，也不改寫 base registry。

## def 導入元件

| Component | Canonical Candidate | Dependency Order |
| --- | --- | ---: |
| VAP Integration Update | `engine/via_vap_update_engine_v0139a.py` | 5 |
| VIA Flow Simulation | `engine/via_flow_simulation_engine_v0139a.py` | 4 |
| TW Stock Group Classification | `engine/via_stock_group_classification_engine_v0139a.py` | 1 |
| TW Group Index | `engine/via_group_index_engine_v0139a.py` | 2 |
| TW Monthly Revenue Analysis | `engine/via_monthly_revenue_analysis_engine_v0139a.py` | 3 |

## def 方法契約

- 個股分類：Ticker 唯一語義 owner；同一 Ticker 有不同 Sector / Industry / Theme 時視為 Hydra，立即 fail-closed。
- 族群指數：以 `Adj Close` 計算；支援 Equal Weight 與 Lagged Market-Cap Weight；基期 100；市值權重使用前一期市值避免 look-ahead。
- 月營收：計算個股與族群 MoM、YoY、3M Average、YoY Acceleration 與 Momentum Score。
- Flow Simulation：合計 Foreign / Investment Trust / Dealer Net，除以 traded-value proxy，使用短長窗差建立 `BUY_PROXY / SELL_PROXY / NEUTRAL`，只用次日報酬做 out-of-sample proxy 評估。
- 缺值：`Adj Close` 依 Ticker 使用前一交易日；Volume 不前向填補，改為 0 並保留 `Volume Was Missing`，避免重複成交量。
- 輸出：CSV 使用 UTF-8-SIG，日期 `YYYY/MM/DD`；Parquet 保留型別；圖表日期 `YYYY-MM-DD`。
- VAP：小字、表格換行、responsive、MODULE / ENGINE / FUNCTION LIB / OTHERS、禁用 Rainbow / Jet。

## def Controlled Activation

PowerShell 預設為 `Audit`。只有精確 token 才能新增 canonical package、SHA-locked launcher 與 append-only activation records。正式 activation 階段不執行 canonical engine、不使用網路。

```powershell
$def_Downloads = Join-Path $env:USERPROFILE "Downloads"
$def_Package = Join-Path $def_Downloads "VIA_Accelerated_Integration_v0139A"
$def_MotherRoot = Join-Path $def_Downloads "VeritasIntelligenceAnalytics"

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

& (Join-Path $def_Package "Invoke-VIA-Accelerated-Integration-v0139A.ps1") `
    -MotherRoot $def_MotherRoot `
    -Mode ActivateLauncherOnly `
    -ApprovalToken "VIA_APPROVE_VAP_FLOW_CONTROLLED_LAUNCHER_ONLY_V0139A" `
    -MaximumParallelTasks 4 `
    -TimeoutSeconds 1800 `
    -PollIntervalSeconds 2 `
    -RequireParquet $true `
    -AutoOpenHtml $true

Write-Host "`ndef PowerShell remains open." -ForegroundColor Green
```

成功 Gate：

```text
VIA_ACCELERATED_INTEGRATION_PASS_LAUNCHER_ACTIVE_CANONICAL_RUNTIME_NOT_EXECUTED_V0139A
```

完全相同版本重跑 Gate：

```text
VIA_ACCELERATED_INTEGRATION_PASS_ALREADY_ACTIVE_IDENTICAL_V0139A
```

若缺少 `pyarrow` 或 `fastparquet`、發生分類 Hydra、canonical target digest 不同、launcher SHA 不同，流程會 HOLD，不會降級啟用。

## def 正式 Runtime

受控啟用完成後，正式入口位於：

```text
C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\bin\Invoke-VIA-VAP-Flow-Integration-v0139A.ps1
```

正式 runtime 需要四個資料檔：Price、Classification、Flows、Monthly Revenue。Launcher 沒有 `AllowNetwork` 參數，網路預設且固定為 DENY。

## def 驗證

```powershell
python -m compileall -q engine tests
python -m unittest discover -s tests -v
python engine\via_domain_engine_v0139a.py --mode fixture-uat --output-dir .\_uat --require-parquet
```

本套件只盤點 `MotherRoot` 最上層檔案；不遞迴掃描其他既有資料夾。只有已知的 append-only canonical、bin、registry 與 run 目錄會被建立或讀寫。
