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

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "VIA DUAL PROJECT USER-TEST CONSOLE" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "VDF + VRN · Read-only lanes · No DB write · No source repair · No Stop-Process"
Write-Host ""

$HtmlPath = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\dict\VDF\_active\VIA_DUAL_PROJECT_USERTEST_CONSOLE_v02873_20260611_205808\report\VIA_DualProjectUserTestConsole_Report_v02873.html"
$CommandDir = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\dict\VDF\_active\VIA_DUAL_PROJECT_USERTEST_CONSOLE_v02873_20260611_205808\commands"

if (Test-Path -LiteralPath $HtmlPath -PathType Leaf) {
    Write-Host "Opening HTML report:" -ForegroundColor Green
    Write-Host $HtmlPath
    Start-Process $HtmlPath
}
else {
    Write-Host "[WARN] HTML report not found:" -ForegroundColor Yellow
    Write-Host $HtmlPath
}

Write-Host ""
Write-Host "Available read-only user-test commands:" -ForegroundColor Yellow
Write-Host ""

Write-Host '[VDF] VDF-Lane1-FinalSealHealth' -ForegroundColor White
Write-Host 'pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\dict\VDF\_active\VIA_DUAL_PROJECT_USERTEST_CONSOLE_v02873_20260611_205808\commands\UserTest-Start-VDF-Lane1-FinalSealHealth.ps1"' -ForegroundColor Cyan
Write-Host ''
Write-Host '[VDF] VDF-Lane2-ReadOnlyInventory' -ForegroundColor White
Write-Host 'pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\dict\VDF\_active\VIA_DUAL_PROJECT_USERTEST_CONSOLE_v02873_20260611_205808\commands\UserTest-Start-VDF-Lane2-ReadOnlyInventory.ps1"' -ForegroundColor Cyan
Write-Host ''
Write-Host '[VDF] VDF-Lane3-EnvSupportiveHardGate' -ForegroundColor White
Write-Host 'pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\dict\VDF\_active\VIA_DUAL_PROJECT_USERTEST_CONSOLE_v02873_20260611_205808\commands\UserTest-Start-VDF-Lane3-EnvSupportiveHardGate.ps1"' -ForegroundColor Cyan
Write-Host ''
Write-Host '[VRN] VRN-Lane1-EntryHealth' -ForegroundColor White
Write-Host 'pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\dict\VDF\_active\VIA_DUAL_PROJECT_USERTEST_CONSOLE_v02873_20260611_205808\commands\UserTest-Start-VRN-Lane1-EntryHealth.ps1"' -ForegroundColor Cyan
Write-Host ''
Write-Host '[VRN] VRN-Lane2-IOInventory' -ForegroundColor White
Write-Host 'pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\dict\VDF\_active\VIA_DUAL_PROJECT_USERTEST_CONSOLE_v02873_20260611_205808\commands\UserTest-Start-VRN-Lane2-IOInventory.ps1"' -ForegroundColor Cyan
Write-Host ''
Write-Host '[VRN] VRN-Lane3-EngineCapability' -ForegroundColor White
Write-Host 'pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\dict\VDF\_active\VIA_DUAL_PROJECT_USERTEST_CONSOLE_v02873_20260611_205808\commands\UserTest-Start-VRN-Lane3-EngineCapability.ps1"' -ForegroundColor Cyan
Write-Host ''

Write-Host "Manual only. This console does not auto-run lanes." -ForegroundColor Yellow
Write-Host "PowerShell remains open. No exit. No Stop-Process. No destructive delete." -ForegroundColor Green

