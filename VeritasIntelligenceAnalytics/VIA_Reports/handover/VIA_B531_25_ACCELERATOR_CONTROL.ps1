[CmdletBinding()]
param(
    [switch]$RunQuantGuardStatus
)

$ErrorActionPreference = 'Stop'
$VIA = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
Set-Location -LiteralPath $VIA

$Register = Get-ChildItem -LiteralPath $VIA -Filter 'Register-VIA-Commands-v*.ps1' |
    Sort-Object Name | Select-Object -Last 1
if (-not $Register) { throw '找不到 Register-VIA-Commands-v*.ps1' }
. $Register.FullName

Write-Host '=== VIA B531 · 25 Accelerator Control Probe ===' -ForegroundColor Cyan
Write-Host "VIA=$VIA"
Write-Host "Register=$($Register.Name)"

$Roster = Get-VIAAccelRoster
$ids = @($Roster.Keys | ForEach-Object { [string]$_ })
$expectedIds = @(1..25 | ForEach-Object { '{0:00}' -f $_ })
$has25 = ($ids.Count -eq 25 -and ($expectedIds -join ',') -eq ($ids -join ','))
Write-Host "VIA_ACCEL20=$($VIA_ACCEL20.Count)"
Write-Host "VIA_ACCEL25=$($VIA_ACCEL25.Count)"
Write-Host "Get-VIAAccelRoster=$($Roster.Count)"
Write-Host "RosterIDs=$($ids -join ',')"
if (-not $has25) { throw 'PowerShell roster is not exactly 01..25' }
if ($VIA_ACCEL20.Count -ne 20) { throw 'VIA_ACCEL20 compatibility roster changed' }
if ($VIA_ACCEL25.Count -ne 25) { throw 'VIA_ACCEL25 is not exactly 25 entries' }

Write-Host '--- CGC156 selftest ---' -ForegroundColor Cyan
via-accel selftest
if ($LASTEXITCODE -ne 0) { throw "CGC156 selftest failed: $LASTEXITCODE" }

Write-Host '--- CGC156 routes ---' -ForegroundColor Cyan
via-accel routes
if ($LASTEXITCODE -ne 0) { throw "CGC156 routes failed: $LASTEXITCODE" }

if ($RunQuantGuardStatus) {
    Write-Host '--- QuantGuard status (offline; no TA-Lib; no data replenishment) ---' -ForegroundColor Cyan
    via-quantguard status
    if ($LASTEXITCODE -ne 0) { throw "QuantGuard status failed: $LASTEXITCODE" }
}

Write-Host '[PASS] VIA B531 25-item control probe completed.' -ForegroundColor Green
Write-Host '[POLICY] QuantGuard allowed; TA-Lib forbidden; network consent remains operator-owned and fail-closed.' -ForegroundColor Yellow
