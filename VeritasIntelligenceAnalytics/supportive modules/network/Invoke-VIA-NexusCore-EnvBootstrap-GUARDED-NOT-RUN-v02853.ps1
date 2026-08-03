#requires -Version 7.0

param(
    [string]$ProjectRoot = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    [switch]$ExecuteInstall,
    [string]$ApprovalToken = ""
)

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