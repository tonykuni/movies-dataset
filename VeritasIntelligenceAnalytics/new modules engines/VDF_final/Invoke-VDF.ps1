# ============================================================================
# VeritasDataForge Cockpit Launcher (PowerShell 7)
# ============================================================================
# One script:
#   - boots the VDF HTTP API (src/vdf_api.py)
#   - opens the cockpit HTML UI in default browser
#   - all operations happen in the UI
#
# Usage:
#   .\Invoke-VDF.ps1                            # start cockpit (default)
#   .\Invoke-VDF.ps1 -Port 9000                 # custom port
#   .\Invoke-VDF.ps1 -NoBrowser                 # don't auto-open browser
#   .\Invoke-VDF.ps1 -CliMode -Mode test                  # legacy CLI: tests
#   .\Invoke-VDF.ps1 -CliMode -Mode full -ProdPaths       # legacy CLI: full run
#
# Author: VERITAS Intelligence System
# Build:  2026-05-25
# ============================================================================

[CmdletBinding()]
param(
    # Cockpit mode (default)
    [int]$Port = 8765,
    [string]$BindHost = "127.0.0.1",
    [switch]$NoBrowser,

    # Legacy CLI mode
    [switch]$CliMode,
    [ValidateSet("full","category","ticker","dry-run","test","list","gen-views")]
    [string]$Mode = "full",
    [string]$Category = "",
    [string]$Ticker = "",
    [string]$Start = "",
    [string]$End = "",
    [int]$Limit = 0,
    [ValidateSet("parquet","parquet+duckdb")]
    [string]$OutputFormat = "parquet",
    [switch]$ProdPaths,
    [switch]$FullRefresh,
    [switch]$SkipChips,
    [switch]$VerboseLog
)
# CELERITAS-TEMPLATE-JOIN v1 (no-wrap join, L103-3; batch R16-9; PS 5.1 runs unchanged, only PS7 loads the template)
# ===== [VIA:PS-TEMPLATE:v0101] Celeritas PS7 template: this process only, restore on exit, skip when absent, param() untouched =====
$VIACelTplOwn = $false
if ($PSVersionTable.PSVersion.Major -ge 7) {
    try {
        $VIACelTplFile = $null
        $VIACelTplProbe = $PSScriptRoot
        while ($VIACelTplProbe) {
            $VIACelTplTry = Join-Path $VIACelTplProbe 'supportive modules\ps7\VeritasCeleritas.PS7.ps1'
            if (Test-Path -LiteralPath $VIACelTplTry) { $VIACelTplFile = $VIACelTplTry; break }
            $VIACelTplUp = Split-Path $VIACelTplProbe -Parent
            if ((-not $VIACelTplUp) -or ($VIACelTplUp -eq $VIACelTplProbe)) { break }
            $VIACelTplProbe = $VIACelTplUp
        }
        if ($VIACelTplFile -and (-not (Get-Command Restore-CeleritasPS7 -ErrorAction Ignore))) {
            $VIACelTplKeep = @{}
            foreach ($VIACelTplName in 'RestoreOnly', 'Report', 'Body') {
                $VIACelTplVar = Get-Variable -Name $VIACelTplName -Scope 0 -ErrorAction Ignore
                if ($VIACelTplVar) { $VIACelTplKeep[$VIACelTplName] = $VIACelTplVar.Value }
            }
            try { $null = . $VIACelTplFile -RestoreOnly }
            finally {
                Set-StrictMode -Off
                foreach ($VIACelTplName in 'RestoreOnly', 'Report', 'Body') {
                    Remove-Variable -Name $VIACelTplName -Scope 0 -Force -ErrorAction Ignore
                    if ($VIACelTplKeep.ContainsKey($VIACelTplName)) { Set-Variable -Name $VIACelTplName -Value $VIACelTplKeep[$VIACelTplName] -Scope 0 }
                }
            }
            if (Get-Command Start-CeleritasPS7 -ErrorAction Ignore) {
                if (-not (Get-EventSubscriber -Force -ErrorAction Ignore | Where-Object { $_.SourceIdentifier -eq 'PowerShell.Exiting' })) {
                    $null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -SupportEvent -Action { try { Restore-CeleritasPS7 } catch { } }
                }
                [void](Start-CeleritasPS7)
                $VIACelTplOwn = $true
            }
        }
    } catch { }
}
# ===== [VIA:PS-TEMPLATE:END] =====


$ErrorActionPreference = "Stop"

# ============================================================================
# Paths
# ============================================================================
$ScriptRoot = [System.IO.Path]::GetDirectoryName($MyInvocation.MyCommand.Path)
$VdfRoot    = $ScriptRoot
$SrcDir     = Join-Path $VdfRoot "src"
$CockpitDir = Join-Path $VdfRoot "cockpit"
$Core       = Join-Path $SrcDir "vdf_core.py"
$ApiServer  = Join-Path $SrcDir "vdf_api.py"

$PyExe = "C:\Users\tonyk\envs\via_core_312\Scripts\python.exe"
if (-not (Test-Path $PyExe)) {
    $PyExe = "python"
    Write-Host "[VDF] venv python not found; falling back to system python" -ForegroundColor Yellow
}

if (-not (Test-Path $Core)) {
    Write-Host "[VDF] FATAL: $Core not found" -ForegroundColor Red; if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }; exit 1
}

function Write-Banner {
    Write-Host ""
    Write-Host "  +-----------------------------------------------------------+" -ForegroundColor Cyan
    Write-Host "  |  VeritasDataForge  -  Matrix Cockpit  v2.0                 |" -ForegroundColor Cyan
    Write-Host "  |  VERITAS INTELLIGENCE ANALYTICS                            |" -ForegroundColor Cyan
    Write-Host "  +-----------------------------------------------------------+" -ForegroundColor Cyan
    Write-Host ""
}

# ============================================================================
# LEGACY CLI MODE
# ============================================================================
if ($CliMode) {
    Write-Banner
    Write-Host "[VDF] CLI mode  ->  $Core" -ForegroundColor Yellow
    $argv = @("--mode", $Mode)
    if ($Category)    { $argv += @("--category", $Category) }
    if ($Ticker)      { $argv += @("--ticker", $Ticker) }
    if ($Start)       { $argv += @("--start", $Start) }
    if ($End)         { $argv += @("--end", $End) }
    if ($Limit -gt 0) { $argv += @("--limit", $Limit) }
    if ($OutputFormat){ $argv += @("--output-format", $OutputFormat) }
    if ($ProdPaths)   { $argv += "--prod-paths" }
    if ($FullRefresh) { $argv += "--full-refresh" }
    if ($SkipChips)   { $argv += "--skip-chips" }
    if ($VerboseLog)  { $argv += "--verbose" }

    Write-Host " Args: $($argv -join ' ')" -ForegroundColor Gray
    & $PyExe $Core @argv
    $code = $LASTEXITCODE
    Write-Host ""
    if ($code -eq 0) { Write-Host "[OK] VDF CLI completed (exit=0)" -ForegroundColor Green }
    else             { Write-Host "[FAIL] VDF CLI exited with $code" -ForegroundColor Red }
    if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }; exit $code
}

# ============================================================================
# COCKPIT MODE (default)
# ============================================================================
if (-not (Test-Path $ApiServer))  { Write-Host "[VDF] FATAL: $ApiServer not found"  -ForegroundColor Red; if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }; exit 1 }
if (-not (Test-Path $CockpitDir)) { Write-Host "[VDF] FATAL: cockpit dir missing"   -ForegroundColor Red; if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }; exit 1 }

Write-Banner
Write-Host " Python   : $PyExe"
Write-Host " Server   : $ApiServer"
Write-Host " Endpoint : http://${BindHost}:${Port}/"
Write-Host " Cockpit  : $CockpitDir\index.html"
Write-Host ""

function Test-PortFree([int]$P) {
    try {
        $tcp = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback, $P)
        $tcp.Start(); $tcp.Stop()
        return $true
    } catch { return $false }
}

$tries = 0
while (-not (Test-PortFree -P $Port) -and $tries -lt 10) {
    Write-Host "[VDF] port $Port in use, trying $($Port+1)" -ForegroundColor Yellow
    $Port++
    $tries++
}

$ApiJob = Start-Job -Name "VDF_API" -ScriptBlock {
    param($py, $script, $h, $p)
    & $py $script "--host" $h "--port" $p
} -ArgumentList $PyExe, $ApiServer, $BindHost, $Port

Start-Sleep -Seconds 1
$pingUrl = "http://${BindHost}:${Port}/api/health"

$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $r = Invoke-RestMethod -Uri $pingUrl -TimeoutSec 1 -ErrorAction Stop
        if ($r.ok) { $ready = $true; break }
    } catch {
        Start-Sleep -Milliseconds 500
    }
}

if (-not $ready) {
    Write-Host "[VDF] API failed to come up within 15s" -ForegroundColor Red
    Receive-Job $ApiJob -Keep | Out-Host
    Stop-Job $ApiJob -Force
    Remove-Job $ApiJob -Force
    if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }; exit 1
}

Write-Host "[OK] API healthy at $pingUrl" -ForegroundColor Green

if (-not $NoBrowser) {
    Start-Process "http://${BindHost}:${Port}/"
    Write-Host "[OK] Opened cockpit in default browser" -ForegroundColor Green
}

Write-Host ""
Write-Host "Cockpit is running. Press Ctrl+C in this window to stop the API." -ForegroundColor Cyan
Write-Host "Streaming server log below:" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor DarkGray

try {
    while ($true) {
        Receive-Job $ApiJob | ForEach-Object { Write-Host $_ }
        if ((Get-Job $ApiJob).State -ne "Running") {
            Write-Host "[VDF] API job stopped (state=$((Get-Job $ApiJob).State))" -ForegroundColor Yellow
            break
        }
        Start-Sleep -Seconds 1
    }
} finally {
    Write-Host ""
    Write-Host "[VDF] shutting down API..." -ForegroundColor Yellow
    if (Get-Job -Id $ApiJob.Id -ErrorAction SilentlyContinue) {
        Stop-Job $ApiJob -Force -ErrorAction SilentlyContinue
        Receive-Job $ApiJob | Out-Null
        Remove-Job $ApiJob -Force -ErrorAction SilentlyContinue
    }
    Write-Host "[VDF] bye" -ForegroundColor Cyan
}
if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] restore on exit
