#Requires -Version 7.0
# [VIA:ACCEL-BRIDGE] VCGC Test Closeout Windows entry
[CmdletBinding()]
param(
    [Alias('Profile')][string]$TestProfile = (Join-Path $PSScriptRoot 'Profile_VCGC_Native_v0100.json'),
    [string]$StateRoot = (Join-Path $env:LOCALAPPDATA 'VCGC\Test_Closeout_v0100'),
    [string]$RunId = ([Guid]::NewGuid().ToString()),
    [string]$Since,
    [string]$Python,
    [string]$NativeConsole,
    [string]$StationRegistry,
    [switch]$InventoryOnly,
    [switch]$RepairDemo,
    [switch]$Graphify,
    [string]$RouteModel,
    [ValidateRange(1,65535)][int]$RoutePort = 20128,
    [switch]$NoOpen
)

$ErrorActionPreference = 'Stop'
$Engine = Join-Path $PSScriptRoot 'VCGC_Test_Closeout_v0100.py'

function Get-CloseoutPython {
    param([string]$Selected)
    if ($Selected) {
        $app = Get-Command $Selected -CommandType Application -ErrorAction Stop | Select-Object -First 1
        return @{ Binary=$app.Source; Prefix=@() }
    }
    foreach ($name in @('python.exe','py.exe')) {
        $app = Get-Command $name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($app) {
            $prefix = @()
            if ($name -eq 'py.exe') { $prefix = @('-3') }
            & $app.Source @prefix -c 'import sys; raise SystemExit(sys.version_info < (3, 11))' 2>$null
            if ($LASTEXITCODE -eq 0) { return @{ Binary=$app.Source; Prefix=@($prefix) } }
        }
    }
    throw '找不到 Python 3.11+。可用 -Python 指向現有 VIA 環境的 python.exe。'
}

$runner = Get-CloseoutPython -Selected $Python
$binary = $runner.Binary
$baseArgs = @($runner.Prefix) + @('-X','utf8',$Engine,'--home',$StateRoot)
$discovery = @('verbs','--probe')
if ($NativeConsole) { $discovery += @('--native',$NativeConsole) }
if ($StationRegistry) { $discovery += @('--registry',$StationRegistry) }
Write-Host '[1/3] VCGC 動詞與功能站盤點' -ForegroundColor Cyan
& $binary @baseArgs @discovery
if ($LASTEXITCODE -ne 0 -or $InventoryOnly) { return }

if ($RepairDemo) { $TestProfile = Join-Path $PSScriptRoot 'Profile_Repair_Demo_v0100.json' }
$run = @('run',$TestProfile,'--id',$RunId)
if ($Since) { $run += @('--since',$Since) }
if (-not $NoOpen) { $run += '--open' }
if ($Graphify) {
    $graph = Get-Command graphify -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($graph) {
        $pin = (Get-FileHash -LiteralPath $graph.Source -Algorithm SHA256).Hash.ToLowerInvariant()
        $run += @('--graphify-sha',$pin)
    } else { Write-Warning 'Graphify 未安裝，本輪沿用測試契約的依賴關係。' }
}
Write-Host "[2/3] 測試、修正及驗收 · $RunId" -ForegroundColor Cyan
& $binary @baseArgs @run
$testExit = $LASTEXITCODE
Write-Host '[3/3] 精簡反饋與證據' -ForegroundColor Cyan
$feedback = @('feedback',$RunId)
if ($Since) { $feedback += @('--since',$Since) }
$brief = & $binary @baseArgs @feedback
if ($LASTEXITCODE -eq 0) {
    $brief | Out-Host
    if ($testExit -eq 2 -and $RouteModel -and ($brief | ConvertFrom-Json).state -eq 'BLOCKED') {
        & $binary @baseArgs omniroute $RunId --model $RouteModel --port $RoutePort
    }
}
Write-Host "測試退出碼 $testExit · Run ID $RunId" -ForegroundColor $(if ($testExit -eq 0) { 'Green' } else { 'Yellow' })
$global:LASTEXITCODE = $testExit
