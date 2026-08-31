#requires -Version 7.0
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

param(
    [switch]$ExecuteInstall,
    [string]$ApprovalToken = ""
)

$RequiredToken = "APPROVE_VIA_TOOL_BUNDLE_INSTALL"
if (-not $ExecuteInstall -or $ApprovalToken -ne $RequiredToken) {
    Write-Host "[REVIEW ONLY] Tool install not executed." -ForegroundColor Yellow
    Write-Host "To execute later, run with: -ExecuteInstall -ApprovalToken $RequiredToken"
    Write-Host "PowerShell remains open. No exit." -ForegroundColor Green
    return
}

Write-Host "Install path intentionally disabled in v028.5.1 generated installer. Create a separate approved install gate first." -ForegroundColor Yellow
return

