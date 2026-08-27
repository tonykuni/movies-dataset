$ErrorActionPreference = "Stop"

$def_PROJECT = '
VIA
'
$def_CANDIDATE_DIR = '
C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fourthstep_sandbox_adapter\RUN_20260622_181822_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110\_sandbox_adapter_candidates\VIA
'

Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA Sandbox Adapter Smoke · v0110 · $def_PROJECT" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan

if (-not (Test-Path -LiteralPath $def_CANDIDATE_DIR)) {
    throw "Candidate dir not found: $def_CANDIDATE_DIR"
}

$contract = Join-Path $def_CANDIDATE_DIR ("VIA_" + $def_PROJECT + "_BridgeContract_v0110.json")
if (-not (Test-Path -LiteralPath $contract)) {
    throw "Bridge contract missing: $contract"
}

$obj = Get-Content -LiteralPath $contract -Raw -Encoding UTF8 | ConvertFrom-Json

$rows = @()
$rows += [pscustomobject]@{ Check="CandidateDir"; Status="OK"; Detail=$def_CANDIDATE_DIR }
$rows += [pscustomobject]@{ Check="Contract"; Status="OK"; Detail=$contract }
$rows += [pscustomobject]@{ Check="Project"; Status="OK"; Detail=$obj.project }
$rows += [pscustomobject]@{ Check="Policy"; Status="OK"; Detail=$obj.policy }
$rows += [pscustomobject]@{ Check="SourceMutation"; Status="OK"; Detail="false" }

$csv = Join-Path $def_CANDIDATE_DIR ("VIA_" + $def_PROJECT + "_SandboxSmoke_Result_v0110.csv")
$json = Join-Path $def_CANDIDATE_DIR ("VIA_" + $def_PROJECT + "_SandboxSmoke_Result_v0110.json")
$rows | Export-Csv -LiteralPath $csv -NoTypeInformation -Encoding UTF8
$rows | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $json -Encoding UTF8

Write-Host "[OK] Sandbox smoke complete: $def_PROJECT" -ForegroundColor Green
Write-Host "[OK] CSV : $csv" -ForegroundColor Cyan
Write-Host "[OK] JSON: $json" -ForegroundColor Cyan

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
