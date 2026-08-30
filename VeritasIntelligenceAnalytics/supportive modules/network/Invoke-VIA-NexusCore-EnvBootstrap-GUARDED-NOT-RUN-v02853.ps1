#requires -Version 7.0

param(
    [string]$ProjectRoot = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [switch]$ExecuteInstall,
    [string]$ApprovalToken = ""
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
$ErrorActionPreference = "Stop"

$RequiredToken = "APPROVE_VIA_NEXUSCORE_ENV_BOOTSTRAP"
$NexusCore = Join-Path $ProjectRoot "supportive modules\Invoke-VeritasNexusCore.ps1"

if ((-not $ExecuteInstall) -or ($ApprovalToken -ne $RequiredToken)) {
    Write-Host "[REVIEW ONLY] Environment bootstrap not executed." -ForegroundColor Yellow
    Write-Host "NexusCore:" $NexusCore
    Write-Host "Future approval token: APPROVE_VIA_NEXUSCORE_ENV_BOOTSTRAP"
    Write-Host "PowerShell remains open. No exit." -ForegroundColor Green
    return
}

throw "Execution path intentionally disabled in this guarded bootstrap. Use the main one-click installer or a separate approved gate."

