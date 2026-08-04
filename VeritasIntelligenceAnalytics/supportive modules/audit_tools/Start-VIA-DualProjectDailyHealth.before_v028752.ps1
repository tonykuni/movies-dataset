#requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptPath = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_DualProjectDailyHealth\Invoke-VIA-DualProjectDailyHealth.ps1"

Write-Host ""
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "VIA DUAL PROJECT DAILY HEALTH · MANUAL LAUNCHER" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan

if(Test-Path -LiteralPath $ScriptPath -PathType Leaf){
    pwsh -NoProfile -ExecutionPolicy Bypass -File $ScriptPath -OpenHtmlReport
} else {
    Write-Host "[BLOCK] Daily health script missing: $ScriptPath" -ForegroundColor Red
}

Write-Host ""
Write-Host "PowerShell remains open. No exit. No Stop-Process." -ForegroundColor Green