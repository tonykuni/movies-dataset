#requires -Version 7.0
param(
    [string]$EnvRoot = "$env:USERPROFILE\envs",
    [string]$VenvName = "vpl_core",
    [string]$SupportiveRoot = "$env:USERPROFILE\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module",
    [switch]$Recreate
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

# VeritasPulse (VPL) one-click launcher
# Builds/uses an isolated Py3.11 venv, installs pinned deps, generates the deck,
# then opens the output folder. No VS Code, no input waits. (LL#12/#16 honoured.)
# Use full cmdlet names to avoid PS7 alias clashes (LL).

$ErrorActionPreference = "Stop"
$script:Root   = $PSScriptRoot
$script:Venv   = Join-Path $EnvRoot $VenvName
$script:PyExe  = Join-Path $script:Venv "Scripts\python.exe"
$script:OutDir = Join-Path $script:Root "output"

function Write-Step {
    param([string]$Msg, [string]$Color = "Cyan")
    Write-Host ("  -> {0}" -f $Msg) -ForegroundColor $Color
}

Write-Host ""
Write-Host "  VeritasPulse (VPL) - Project Deck Builder" -ForegroundColor Green
Write-Host "  ----------------------------------------" -ForegroundColor DarkGray

# 1. venv (LL#16: use Windows py launcher -3.11, never where.exe python3.11)
if ($Recreate -and (Test-Path $script:Venv)) {
    Write-Step "Recreate flag set - removing old venv"
    Remove-Item $script:Venv -Recurse -Force
}
if (-not (Test-Path $script:PyExe)) {
    Write-Step "Creating isolated venv (py -3.11) at ${script:Venv}"
    $null = New-Item -ItemType Directory -Path $EnvRoot -Force
    & py -3.11 -m venv $script:Venv
    if ($LASTEXITCODE -ne 0) { throw "py -3.11 venv creation failed - is Python 3.11 installed?" }
} else {
    Write-Step "Reusing venv at ${script:Venv}"
}

# 2. deps (pinned; numpy golden rule enforced by requirements.txt)
Write-Step "Upgrading pip"
& $script:PyExe -m pip install --upgrade pip --quiet
Write-Step "Installing pinned requirements"
& $script:PyExe -m pip install -r (Join-Path $script:Root "requirements.txt") --quiet
if ($LASTEXITCODE -ne 0) { throw "pip install failed" }

# 3. arrange environment WITH Veritas supportive tools (governance + health record)
#    EnvManager gates the plan; Celeritas/Aegis stay locked; result -> health registry.
Write-Step "Arranging environment with Veritas (EnvManager + HealthRegistry)"
& $script:PyExe -m vpl.core.env_arrange --root $SupportiveRoot --env $VenvName --out (Join-Path $script:Root "output")
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ! Veritas arrangement step reported an issue (continuing)" -ForegroundColor Yellow
}
$arrHtml = Join-Path $script:OutDir "vpl_env_arrangement.html"
if (Test-Path $arrHtml) { Start-Process $arrHtml }

# 4. build the interactive app + deck
Write-Step "Building VeritasPulse app + project deck"
$sw = [System.Diagnostics.Stopwatch]::StartNew()
& $script:PyExe (Join-Path $script:Root "build_all.py")
if ($LASTEXITCODE -ne 0) { throw "build failed" }
$sw.Stop()
Write-Step ("Done in {0:N2}s" -f $sw.Elapsed.TotalSeconds) "Green"

# 4b. activate: consolidated self-test gate
Write-Step "Running consolidated self-test"
& $script:PyExe (Join-Path $script:Root "selftest.py")
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ! self-test reported failures — see output\vpl_selftest.html" -ForegroundColor Yellow
} else {
    Write-Step "Self-test: all layers PASS — system activated" "Green"
}

# 5. open the outputs (LL#12: Start-Process to auto-open is permitted)
$app  = Join-Path $script:OutDir "VeritasPulse_App.html"
$deck = Join-Path $script:OutDir "VeritasPulse_ProjectDeck.pptx"
if (Test-Path $app) { Write-Step "Opening app"; Start-Process $app }
Start-Process explorer.exe -ArgumentList $script:OutDir
Write-Host ""

