[CmdletBinding()]
param(
    [string]$InputPath = 'C:\測試樣本報告',
    [switch]$RunPipeline
)

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$VIA = (Resolve-Path (Join-Path $here '..\..')).Path
Set-Location $VIA

$register = Get-ChildItem -LiteralPath $VIA -Filter 'Register-VIA-Commands-v*.ps1' -File |
    Sort-Object Name | Select-Object -Last 1
if (-not $register) { throw 'Register-VIA-Commands-v*.ps1 not found' }
. $register.FullName

Write-Host "=== VIA B532 Unified NLP Windows Probe ===" -ForegroundColor Cyan
Write-Host "VIA=$VIA"
Write-Host "Register=$($register.Name)"
Write-Host "--- SUP_MDL866 selftest ---" -ForegroundColor Yellow
NLP統一 -SelfTest
Write-Host "--- SUP_MDL866 status ---" -ForegroundColor Yellow
NLP統一 -Status

if ($RunPipeline) {
    if (-not (Test-Path -LiteralPath $InputPath)) {
        throw "InputPath not found: $InputPath"
    }
    Write-Host "--- SUP_MDL866 file pipeline (offline/network gate unchanged) ---" -ForegroundColor Yellow
    NLP統一 -Pipeline -In $InputPath -Points 5
}

Write-Host "Completed. A YELLOW/BLOCKED VDF coverage result is honest and must not be changed to GREEN." -ForegroundColor Green
