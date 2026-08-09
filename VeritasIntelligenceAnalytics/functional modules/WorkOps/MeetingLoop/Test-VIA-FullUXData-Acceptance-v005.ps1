#requires -Version 7.0
param(
    [switch]$OpenWorkbench,
    [switch]$OpenReport
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# =============================================================================
# def 00_PARAMETERS
# =============================================================================

$BaseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$EnvPython = Join-Path $env:USERPROFILE "envs\via_meeting_data_312\Scripts\python.exe"
$Engine = Join-Path $BaseDir "via_meetingloop_engine.py"
$Acceptance = Join-Path $BaseDir "via_duck_parquet_acceptance.py"
$DataReport = Join-Path $BaseDir "DATA_ENV_ACCEPTANCE_REPORT.json"
$UxPayload = Join-Path $BaseDir "UX_DUCKDB_PAYLOAD.json"
$FinalReport = Join-Path $BaseDir "FULL_UX_DATA_ACCEPTANCE_REPORT.json"

# =============================================================================
# def 01_FUNCTIONS
# =============================================================================

function def_AssertFile {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { throw "Required file missing: $Path" }
}

function def_Run {
    param([string]$Exe, [string[]]$Arguments)
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $Exe $($Arguments -join ' ')"
    }
}

function def_Main {
    Write-Host ""
    Write-Host ("=" * 100) -ForegroundColor DarkCyan
    Write-Host "def VIA MeetingLoop v005 Full UX / DuckDB / PyArrow Acceptance" -ForegroundColor Cyan
    Write-Host ("=" * 100) -ForegroundColor DarkCyan

    def_AssertFile -Path $EnvPython
    def_AssertFile -Path $Engine
    def_AssertFile -Path $Acceptance

    def_Run -Exe $EnvPython -Arguments @($Acceptance, "--strict")
    def_Run -Exe $EnvPython -Arguments @($Engine, "doctor")
    def_Run -Exe $EnvPython -Arguments @($Engine, "self-test")

    $Data = Get-Content -LiteralPath $DataReport -Raw | ConvertFrom-Json
    if ($Data.gate -ne "DATA_ENV_ACCEPTED") {
        throw "Data acceptance report did not reach DATA_ENV_ACCEPTED."
    }

    $Checks = [ordered]@{
        data_gate = $Data.gate
        all_data_tests_pass = (($Data.tests.PSObject.Properties.Value | Where-Object { $_ -ne $true }).Count -eq 0)
        ux_payload_exists = (Test-Path -LiteralPath $UxPayload)
        real_workbench_exists = (Test-Path -LiteralPath $Data.artifacts.real_workbench)
        duckdb_exists = (Test-Path -LiteralPath $Data.artifacts.duckdb)
        real_transcript_parquet_exists = (Test-Path -LiteralPath $Data.artifacts.real_transcript_parquet)
        real_action_parquet_exists = (Test-Path -LiteralPath $Data.artifacts.real_action_parquet)
    }

    $Passed = (($Checks.PSObject.Properties.Value | Where-Object { $_ -eq $false }).Count -eq 0)
    $Report = [ordered]@{
        gate = $(if ($Passed) { "FULL_UX_DATA_ACCEPTED" } else { "FULL_UX_DATA_REJECTED" })
        generated_at = (Get-Date).ToString("o")
        checks = $Checks
        data_report = $DataReport
        ux_payload = $UxPayload
    }
    $Report | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $FinalReport -Encoding utf8

    if (-not $Passed) { throw "Full UX/Data acceptance failed." }

    if ($OpenWorkbench) { Start-Process $Data.artifacts.real_workbench }
    if ($OpenReport) { Start-Process $FinalReport }

    Write-Host "def Gate : FULL_UX_DATA_ACCEPTED" -ForegroundColor Green
    Write-Host "def Report : $FinalReport"
}

try { def_Main }
catch {
    Write-Host ""
    Write-Host "def FATAL: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "def Gate : FULL_UX_DATA_REJECTED" -ForegroundColor Red
    exit 1
}
