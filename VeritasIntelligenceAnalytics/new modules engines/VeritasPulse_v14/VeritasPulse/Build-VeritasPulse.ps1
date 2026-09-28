#requires -Version 7.0
param(
    [string]$EnvRoot = "$env:USERPROFILE\envs",
    [string]$VenvName = "vpl_core",
    [string]$SupportiveRoot = "$env:USERPROFILE\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module",
    [switch]$Recreate
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
if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] restore on exit
