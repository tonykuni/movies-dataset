#requires -Version 7.0
param(
    [string]$TargetFile = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\input\MQ-1560 20260520.pdf"
)
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

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"

$Python = "C:\Users\tonyk\envs\via_core_312\Scripts\python.exe"
$BrokerHelper = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIS_VRN_BrokerAlias_Compatibility_v0222.py"
$FallbackHelper = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIS_VRN_PDFTextLayerFallbackPlan_v0222.py"

Write-Host "==================================================================================================" -ForegroundColor Cyan
Write-Host "def VRN MQ No-OCR Staging Runner v2.2.2" -ForegroundColor Cyan
Write-Host "==================================================================================================" -ForegroundColor Cyan
Write-Host "[MODE] NO OCR / STAGING ONLY / NO DB / NO SSOT" -ForegroundColor Yellow

if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "Python not found: $Python"
}

& $Python -m py_compile $BrokerHelper
& $Python -m py_compile $FallbackHelper

$pyCode = @"
import importlib.util, json, pathlib, sys
broker_path = pathlib.Path(sys.argv[1])
fallback_path = pathlib.Path(sys.argv[2])
target = pathlib.Path(sys.argv[3])

spec1 = importlib.util.spec_from_file_location('broker_helper', broker_path)
m1 = importlib.util.module_from_spec(spec1)
spec1.loader.exec_module(m1)

spec2 = importlib.util.spec_from_file_location('fallback_helper', fallback_path)
m2 = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(m2)

alias = m1.def_normalize_broker_name(target.name)
candidate = m2.def_build_noocr_candidate(str(target))
print('[ALIAS]', alias.canonical if alias else 'NONE')
print('[CANDIDATE]')
print(json.dumps(m2.def_to_dict(candidate), ensure_ascii=False, indent=2))
"@

$tmp = Join-Path $env:TEMP "vrn_mq_noocr_stage_v222.py"
[System.IO.File]::WriteAllText($tmp, $pyCode, [System.Text.UTF8Encoding]::new($false))
& $Python $tmp $BrokerHelper $FallbackHelper $TargetFile

Write-Host ""
Write-Host "PowerShell session remains open." -ForegroundColor Cyan
