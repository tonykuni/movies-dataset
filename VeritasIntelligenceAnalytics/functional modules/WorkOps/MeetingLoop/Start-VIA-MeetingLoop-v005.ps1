#requires -Version 7.0
param(
    [ValidateSet(
        "Doctor","SelfTest","Process","OpenLatest","ImportReview","Consolidate",
        "InstallDataEnvironment","DataAcceptance","FullUXDataAcceptance"
    )]
    [string]$Mode = "Doctor",

    [string]$Source,
    [string]$ReviewJson,
    [string]$MeetingId = "MTG-BUX-20260801-001",
    [switch]$OpenWorkbench,
    [switch]$AllowNetworkInstall,
    [switch]$ForceRebuildEnvironment
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# =============================================================================
# def 00_PARAMETERS
# =============================================================================

$BaseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Engine = Join-Path $BaseDir "VIA_ENG019_MeetingloopEngine.py"
$Installer = Join-Path $BaseDir "Install-VIA-DataEnvironment-v005.ps1"
$DataAcceptance = Join-Path $BaseDir "VIA_ENG018_DuckParquetAcceptance.py"
$FullAcceptance = Join-Path $BaseDir "Test-VIA-FullUXDataAcceptance-v005.ps1"
$RunsDir = Join-Path $BaseDir "runs"
$DataPython = Join-Path $env:USERPROFILE "envs\via_meeting_data_312\Scripts\python.exe"
$PythonCandidates = @(
    "C:\Python312\python.exe",
    "C:\Python313\python.exe",
    (Join-Path $env:USERPROFILE "envs\via_core_312\Scripts\python.exe"),
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
        elseif (Test-Path -LiteralPath $Candidate) { return $Candidate }
    }
    throw "No usable Python interpreter found."
}

function def_SelectFile {
    param([string]$Title, [string]$Filter)
    Add-Type -AssemblyName System.Windows.Forms
    $Dialog = New-Object System.Windows.Forms.OpenFileDialog
    $Dialog.Title = $Title
    $Dialog.Filter = $Filter
    if ($Dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
        throw "No file selected."
    }
    return $Dialog.FileName
}

function def_RunEngine {
    param([string[]]$Arguments, [string]$PythonPath)
    if ([string]::IsNullOrWhiteSpace($PythonPath)) { $PythonPath = def_ResolvePython }
    & $PythonPath $Engine @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Engine failed with exit code $LASTEXITCODE" }
}

function def_LatestWorkbench {
    if (-not (Test-Path -LiteralPath $RunsDir)) { return $null }
    return Get-ChildItem -LiteralPath $RunsDir -Filter "12_mouse_first_workbench.html" -Recurse -File |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
}

function def_Main {
    Write-Host ""
    Write-Host ("=" * 100) -ForegroundColor DarkCyan
    Write-Host "def VIA MeetingLoop Intelligence Engine v005" -ForegroundColor Cyan
    Write-Host ("=" * 100) -ForegroundColor DarkCyan
    Write-Host "def Policy : append-only / mouse-first / no automatic email send"

    switch ($Mode) {
        "Doctor" { def_RunEngine -Arguments @("doctor") }
        "SelfTest" { def_RunEngine -Arguments @("self-test") }
        "Process" {
            if ([string]::IsNullOrWhiteSpace($Source)) {
                $Source = def_SelectFile -Title "Select meeting transcript" -Filter "Transcript (*.txt;*.md;*.vtt;*.json)|*.txt;*.md;*.vtt;*.json"
            }
            $Python = if (Test-Path -LiteralPath $DataPython) { $DataPython } else { def_ResolvePython }
            $Output = & $Python $Engine process --source $Source 2>&1
            $Code = $LASTEXITCODE
            $Output | ForEach-Object { Write-Host $_ }
            if ($Code -ne 0) { throw "Process failed with exit code $Code" }
            if ($OpenWorkbench) {
                $Line = $Output | Where-Object { $_ -match "^def Workbench\s+:" } | Select-Object -Last 1
                if ($Line) {
                    $Path = (($Line -split ":", 2)[1]).Trim()
                    if (Test-Path -LiteralPath $Path) { Start-Process $Path }
                }
            }
        }
        "OpenLatest" {
            $Latest = def_LatestWorkbench
            if (-not $Latest) { throw "No generated workbench found." }
            Start-Process $Latest.FullName
        }
        "ImportReview" {
            if ([string]::IsNullOrWhiteSpace($ReviewJson)) {
                $ReviewJson = def_SelectFile -Title "Select VIA review JSON" -Filter "JSON (*.json)|*.json"
            }
            def_RunEngine -Arguments @("import-review","--review",$ReviewJson)
        }
        "Consolidate" { def_RunEngine -Arguments @("consolidate","--meeting-id",$MeetingId) }
        "InstallDataEnvironment" {
            & $Installer -AllowNetworkInstall:$AllowNetworkInstall -RunAcceptanceTest -ForceRebuildEnvironment:$ForceRebuildEnvironment
            if ($LASTEXITCODE -ne 0) { throw "Data environment installation/acceptance failed." }
        }
        "DataAcceptance" {
            if (-not (Test-Path -LiteralPath $DataPython)) {
                throw "Data Python not found. Run -Mode InstallDataEnvironment first."
            }
            & $DataPython $DataAcceptance --strict
            if ($LASTEXITCODE -ne 0) { throw "DATA_ENV_ACCEPTED was not reached." }
        }
        "FullUXDataAcceptance" {
            & $FullAcceptance -OpenWorkbench:$OpenWorkbench
            if ($LASTEXITCODE -ne 0) { throw "FULL_UX_DATA_ACCEPTED was not reached." }
        }
    }
}

try { def_Main }
catch {
    Write-Host ""
    Write-Host "def FATAL: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "def PowerShell remains open. No canonical source was modified." -ForegroundColor Yellow
    exit 1
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
