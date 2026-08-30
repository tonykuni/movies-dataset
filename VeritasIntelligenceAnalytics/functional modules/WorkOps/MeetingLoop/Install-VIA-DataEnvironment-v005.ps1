#requires -Version 7.0
param(
    [switch]$AllowNetworkInstall,
    [switch]$RunAcceptanceTest = $true,
    [switch]$ForceRebuildEnvironment
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

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# =============================================================================
# def 00_PARAMETERS
# =============================================================================

$BaseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$EnvRoot = Join-Path $env:USERPROFILE "envs\via_meeting_data_312"
$Requirements = Join-Path $BaseDir "requirements-data-lock.txt"
$Acceptance = Join-Path $BaseDir "VIA_ENG018_DuckParquetAcceptance.py"
$StatePath = Join-Path $EnvRoot ".via_environment_state.json"
$PythonCandidates = @(
    "C:\Python312\python.exe",
    (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"),
    "C:\Python313\python.exe",
    "python"
)

# =============================================================================
# def 01_FUNCTIONS
# =============================================================================

function def_ResolvePython {
    foreach ($Candidate in $PythonCandidates) {
        if ($Candidate -eq "python") {
            $Command = Get-Command python -ErrorAction SilentlyContinue
            if ($Command) { return $Command.Source }
        }
        elseif (Test-Path -LiteralPath $Candidate) {
            return $Candidate
        }
    }
    throw "No usable Python interpreter found."
}

function def_AssertFile {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Required file not found: $Path"
    }
}

function def_FileSha256 {
    param([string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function def_ReadState {
    if (-not (Test-Path -LiteralPath $StatePath)) { return $null }
    try { return Get-Content -LiteralPath $StatePath -Raw | ConvertFrom-Json }
    catch { return $null }
}

function def_WriteState {
    param([string]$RequirementHash, [string]$PythonPath, [string]$Gate)
    $State = [ordered]@{
        schema_version = "v001"
        requirement_sha256 = $RequirementHash
        python = $PythonPath
        gate = $Gate
        updated_at = (Get-Date).ToString("o")
    }
    $State | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $StatePath -Encoding utf8
}

function def_Main {
    Write-Host ""
    Write-Host ("=" * 100) -ForegroundColor DarkCyan
    Write-Host "def VIA MeetingLoop v005 Actual DuckDB / PyArrow Environment" -ForegroundColor Cyan
    Write-Host ("=" * 100) -ForegroundColor DarkCyan
    Write-Host "def Policy : user-local venv / no admin / no canonical mutation / hash-state"

    def_AssertFile -Path $Requirements
    def_AssertFile -Path $Acceptance

    $BasePython = def_ResolvePython
    $RequirementHash = def_FileSha256 -Path $Requirements
    $ExistingState = def_ReadState

    if ($ForceRebuildEnvironment -and (Test-Path -LiteralPath $EnvRoot)) {
        $Backup = "$EnvRoot.backup.$((Get-Date).ToString('yyyyMMdd_HHmmss'))"
        Move-Item -LiteralPath $EnvRoot -Destination $Backup
        Write-Host "def Existing environment backed up : $Backup" -ForegroundColor Yellow
    }

    if (-not (Test-Path -LiteralPath $EnvRoot)) {
        & $BasePython -m venv $EnvRoot
        if ($LASTEXITCODE -ne 0) { throw "venv creation failed." }
    }

    $EnvPython = Join-Path $EnvRoot "Scripts\python.exe"
    if (-not (Test-Path -LiteralPath $EnvPython)) {
        throw "Environment Python not found: $EnvPython"
    }

    $StateMatches = $false
    if ($ExistingState -and $ExistingState.requirement_sha256 -eq $RequirementHash) {
        $StateMatches = $true
    }

    if ($StateMatches) {
        Write-Host "def Dependency state : proposed -> skip reinstall" -ForegroundColor Green
    }
    elseif ($AllowNetworkInstall) {
        Write-Host "def Dependency state : original/other -> install locked requirements"
        & $EnvPython -m pip install --disable-pip-version-check --requirement $Requirements
        if ($LASTEXITCODE -ne 0) { throw "dependency installation failed." }
        def_WriteState -RequirementHash $RequirementHash -PythonPath $EnvPython -Gate "INSTALLED_PENDING_ACCEPTANCE"
    }
    else {
        Write-Host "def Network installation disabled; testing existing environment." -ForegroundColor Yellow
    }

    if ($RunAcceptanceTest) {
        & $EnvPython $Acceptance --strict
        if ($LASTEXITCODE -ne 0) {
            def_WriteState -RequirementHash $RequirementHash -PythonPath $EnvPython -Gate "DATA_ENV_REJECTED"
            throw "DATA_ENV_ACCEPTED gate was not reached."
        }
        def_WriteState -RequirementHash $RequirementHash -PythonPath $EnvPython -Gate "DATA_ENV_ACCEPTED"
    }

    Write-Host "def Gate   : DATA_ENV_ACCEPTED" -ForegroundColor Green
    Write-Host "def Python : $EnvPython"
}

try { def_Main }
catch {
    Write-Host ""
    Write-Host "def FATAL: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "def No canonical production data was modified." -ForegroundColor Yellow
    exit 1
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
