#requires -Version 7.0
<#
================================================================================
def Invoke-VIA-MultiFactor-TestValidateSim-v0100.ps1
def Policy: append-only output / no delete / no source mutation / no network / optional HTML open
def Purpose: Launch VIA MultiFactor testing-validating-simulating engine.
================================================================================
#>
param(
    [string]$EnginePath = "$env:USERPROFILE\Downloads\VIA_ENG001_MultiFactorTestValidateSimEngine_v0100.py",
    [string]$SSOTPath = "$env:USERPROFILE\Downloads\SSOT_VPT_ingest.json",
    [string]$OutBase = "$env:USERPROFILE\Downloads\VIA_MF_ENGINE_RUNS",
    [string]$PythonExe = "python",
    [string]$Target = "TARGET_RISK_ASSET",
    [switch]$NoOpen,
    [switch]$KeepPowerShellOpen
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function def_WriteStep([int]$Pct, [string]$Msg) {
    Write-Progress -Activity "VIA MultiFactor Test Validate Sim" -Status $Msg -PercentComplete $Pct
    Write-Host ("def [{0,3}%] {1}" -f $Pct, $Msg) -ForegroundColor Cyan
}

try {
    def_WriteStep 5 "resolve paths"
    if (-not (Test-Path -LiteralPath $EnginePath)) { throw "ENGINE_NOT_FOUND: $EnginePath" }
    if (-not (Test-Path -LiteralPath $SSOTPath)) { throw "SSOT_NOT_FOUND: $SSOTPath" }
    New-Item -ItemType Directory -Force -Path $OutBase | Out-Null

    def_WriteStep 20 "run python engine append-only"
    $args = @(
        $EnginePath,
        "--ssot", $SSOTPath,
        "--out-base", $OutBase,
        "--target", $Target
    )
    $jsonText = & $PythonExe @args
    if ($LASTEXITCODE -ne 0) { throw "PYTHON_ENGINE_FAILED_EXIT_$LASTEXITCODE" }

    def_WriteStep 80 "parse engine result"
    $result = $jsonText | ConvertFrom-Json
    Write-Host "def EngineStatus : $($result.status)" -ForegroundColor Green
    Write-Host "def RunDir       : $($result.run_dir)" -ForegroundColor White
    Write-Host "def HtmlReport   : $($result.html_report)" -ForegroundColor White
    Write-Host "def HighConfExec : $($result.high_confidence_engine_execution)" -ForegroundColor White

    if (-not $NoOpen -and (Test-Path -LiteralPath $result.html_report)) {
        def_WriteStep 90 "open html report"
        Start-Process -FilePath $result.html_report | Out-Null
    }

    def_WriteStep 100 "complete"
}
catch {
    Write-Host "def FAIL" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    throw
}
finally {
    Write-Progress -Activity "VIA MultiFactor Test Validate Sim" -Completed
    if ($KeepPowerShellOpen) {
        Write-Host "def KeepPowerShellOpen enabled. Press Enter to close." -ForegroundColor Yellow
        [void][System.Console]::ReadLine()
    }
}
