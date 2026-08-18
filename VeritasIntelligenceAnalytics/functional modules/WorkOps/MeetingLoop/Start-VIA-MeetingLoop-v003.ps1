#requires -Version 7.0
param(
    [ValidateSet("Doctor","SelfTest","Process","OpenLatest","ImportReview","Consolidate")]
    [string]$Mode = "Doctor",

    [string]$Source,
    [string]$ReviewJson,
    [string]$MeetingId = "MTG-BUX-20260801-001",
    [switch]$OpenWorkbench
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# =============================================================================
# def 00_PARAMETERS
# =============================================================================

$BaseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Engine = Join-Path $BaseDir "VIA_ENG019_MeetingloopEngine.py"
$RunsDir = Join-Path $BaseDir "runs"
$PythonCandidates = @(
    "C:\Python313\python.exe",
    "C:\Python312\python.exe",
    (Join-Path $env:USERPROFILE "envs\via_core_312\Scripts\python.exe"),
    (Join-Path $env:USERPROFILE "envs\via_core\Scripts\python.exe"),
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

function def_LatestWorkbench {
    if (-not (Test-Path -LiteralPath $RunsDir)) { return $null }
    return Get-ChildItem -LiteralPath $RunsDir -Filter "12_mouse_first_workbench.html" -Recurse -File |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1
}

function def_RunEngine {
    param([string[]]$Arguments)
    $Python = def_ResolvePython
    & $Python $Engine @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Engine failed with exit code $LASTEXITCODE"
    }
}

function def_Main {
    Write-Host ""
    Write-Host ("=" * 96) -ForegroundColor DarkCyan
    Write-Host "def VIA MeetingLoop Intelligence Engine v003" -ForegroundColor Cyan
    Write-Host ("=" * 96) -ForegroundColor DarkCyan
    Write-Host "def Policy : append-only / mouse-first / no automatic email send"

    switch ($Mode) {
        "Doctor" {
            def_RunEngine -Arguments @("doctor")
        }
        "SelfTest" {
            def_RunEngine -Arguments @("self-test")
        }
        "Process" {
            if ([string]::IsNullOrWhiteSpace($Source)) {
                $Source = def_SelectFile -Title "Select meeting transcript" -Filter "Transcript (*.txt;*.md;*.vtt;*.json)|*.txt;*.md;*.vtt;*.json"
            }
            $Python = def_ResolvePython
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
            Write-Host "def Opened : $($Latest.FullName)"
        }
        "ImportReview" {
            if ([string]::IsNullOrWhiteSpace($ReviewJson)) {
                $ReviewJson = def_SelectFile -Title "Select VIA review result JSON" -Filter "JSON (*.json)|*.json"
            }
            def_RunEngine -Arguments @("import-review", "--review", $ReviewJson)
        }
        "Consolidate" {
            def_RunEngine -Arguments @("consolidate", "--meeting-id", $MeetingId)
        }
    }
}

try {
    def_Main
}
catch {
    Write-Host ""
    Write-Host "def FATAL: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "def PowerShell remains open. No canonical source was modified." -ForegroundColor Yellow
    exit 1
}
