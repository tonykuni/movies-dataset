# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====
$ErrorActionPreference = "Stop"

$def_PROJECT = '
VIA
'
$def_CONTRACT_JSON = '
C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fourthstep_sandbox_adapter\RUN_20260622_181822_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110\_sandbox_adapter_candidates\VIA\VIA_VIA_BridgeContract_v0110.json
'
$def_CANDIDATE_DIR = '
C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fourthstep_sandbox_adapter\RUN_20260622_181822_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110\_sandbox_adapter_candidates\VIA
'

Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA Fixed Sandbox Smoke v0111 · $def_PROJECT" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan

$rows = @()

if (-not (Test-Path -LiteralPath $def_CANDIDATE_DIR)) { throw "Candidate directory missing: $def_CANDIDATE_DIR" }
if (-not (Test-Path -LiteralPath $def_CONTRACT_JSON)) { throw "Contract JSON missing: $def_CONTRACT_JSON" }

$obj = Get-Content -LiteralPath $def_CONTRACT_JSON -Raw -Encoding UTF8 | ConvertFrom-Json

$rows += [pscustomobject]@{ Check="CandidateDirExists"; Status="OK"; Detail=$def_CANDIDATE_DIR }
$rows += [pscustomobject]@{ Check="ContractJsonExists"; Status="OK"; Detail=$def_CONTRACT_JSON }
$rows += [pscustomobject]@{ Check="ContractJsonReadable"; Status="OK"; Detail=$obj.schema_version }
$rows += [pscustomobject]@{ Check="Project"; Status="OK"; Detail=$obj.project }

$sourceMutation = [string]$obj.source_mutation
$canonicalMerge = [string]$obj.canonical_merge
$dbWrite = [string]$obj.db_write

if ($sourceMutation -notin @("False","false","0","")) { throw "source_mutation is not false: $sourceMutation" }
if ($canonicalMerge -notin @("False","false","0","")) { throw "canonical_merge is not false: $canonicalMerge" }
if ($dbWrite -notin @("False","false","0","")) { throw "db_write is not false: $dbWrite" }

$rows += [pscustomobject]@{ Check="NoSourceMutation"; Status="OK"; Detail=$sourceMutation }
$rows += [pscustomobject]@{ Check="NoCanonicalMerge"; Status="OK"; Detail=$canonicalMerge }
$rows += [pscustomobject]@{ Check="NoDbWrite"; Status="OK"; Detail=$dbWrite }
$rows += [pscustomobject]@{ Check="Policy"; Status="OK"; Detail=$obj.policy }

$csv = Join-Path $def_CANDIDATE_DIR ("VIA_" + $def_PROJECT + "_FixedSmoke_Result_v0111.csv")
$json = Join-Path $def_CANDIDATE_DIR ("VIA_" + $def_PROJECT + "_FixedSmoke_Result_v0111.json")
$rows | Export-Csv -LiteralPath $csv -NoTypeInformation -Encoding UTF8
$rows | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $json -Encoding UTF8

Write-Host "[OK] Fixed smoke complete: $def_PROJECT" -ForegroundColor Green
Write-Host "[OK] CSV : $csv" -ForegroundColor Cyan
Write-Host "[OK] JSON: $json" -ForegroundColor Cyan

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
