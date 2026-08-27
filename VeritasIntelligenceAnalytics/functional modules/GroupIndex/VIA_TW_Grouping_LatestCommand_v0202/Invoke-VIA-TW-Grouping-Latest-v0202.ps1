#requires -Version 7.0
[CmdletBinding()]
param(
    [string]$EnginePath = "$PSScriptRoot\VIA_TW_GroupingIndexRotationUnifiedEngine_v0201.py",
    [string]$MembershipPath = "$PSScriptRoot\VIA_ThreeList_CanonicalMembershipInput_v0100.csv",
    [string]$PricePath = "$env:USERPROFILE\OneDrive\桌面\tw_stock\StockData.parquet",
    [string]$FactorPath = "",
    [string]$OutputRoot = "$env:USERPROFILE\Downloads\VeritasIntelligenceAnalytics\outputs\VIA_TW_Grouping_REAL_20260102_LATEST",
    [string]$WarmupStartDate = "2025-01-02",
    [string]$EvaluationStartDate = "2026-01-02",
    [string]$EndDate = "",
    [ValidateSet("Real", "Demo")]
    [string]$Mode = "Real",
    [int]$DemoObservations = 260,
    [bool]$RunPytest = $true,
    [bool]$OpenHtml = $true,
    [bool]$NonBlocking = $true,
    [bool]$KeepPowerShellOpen = $true,
    [switch]$Strict,
    [switch]$VerboseEngine
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function def_WriteStep {
    param([int]$Percent, [string]$Message, [string]$Status = "INFO")
    $blocks = [Math]::Floor($Percent / 4)
    $bar = ("█" * $blocks).PadRight(25, "░")
    Write-Host ("def [{0,3}%] [{1}] [{2}] {3}" -f $Percent, $bar, $Status, $Message)
}

function def_ResolvePython {
    $candidates = @(
        "$env:USERPROFILE\Downloads\VeritasIntelligenceAnalytics\.venv\Scripts\python.exe",
        "$env:USERPROFILE\Downloads\VeritasIntelligenceAnalytics\via_core_312\Scripts\python.exe",
        "$env:USERPROFILE\Downloads\via_core_312\Scripts\python.exe"
    )
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    $command = Get-Command python -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }
    throw "Python executable not found. Activate via_core_312 or place Python on PATH."
}

function def_TestRequiredPath {
    param([string]$Path, [string]$Label)
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "$Label not found: $Path"
    }
}

function def_ValidateDates {
    $warmup = [datetime]::ParseExact($WarmupStartDate, "yyyy-MM-dd", $null)
    $evaluation = [datetime]::ParseExact($EvaluationStartDate, "yyyy-MM-dd", $null)
    if ($evaluation -lt $warmup) {
        throw "EvaluationStartDate must be on or after WarmupStartDate."
    }
    if ($EndDate) {
        $end = [datetime]::ParseExact($EndDate, "yyyy-MM-dd", $null)
        if ($end -lt $evaluation) {
            throw "EndDate must be on or after EvaluationStartDate."
        }
    }
}

function def_BuildArguments {
    $arguments = @(
        $EnginePath,
        "--membership", $MembershipPath,
        "--output-root", $OutputRoot,
        "--start-date", $WarmupStartDate,
        "--normalized-date", $EvaluationStartDate
    )

    if ($EndDate) {
        $arguments += @("--end-date", $EndDate)
    }

    if ($Mode -eq "Demo") {
        $arguments += @("--demo", "--demo-observations", [string]$DemoObservations)
    }
    else {
        $arguments += @("--prices", $PricePath)
        if ($FactorPath) {
            $arguments += @("--factors", $FactorPath)
        }
    }

    if ($Strict) { $arguments += "--strict" }
    if ($VerboseEngine) { $arguments += "--verbose" }
    return $arguments
}

function def_RunForeground {
    param([string]$PythonExe, [string[]]$Arguments)
    & $PythonExe @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Engine failed with exit code $LASTEXITCODE"
    }
}

function def_RunBackground {
    param([string]$PythonExe, [string[]]$Arguments)

    New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null
    $stdout = Join-Path $OutputRoot "launcher_stdout.log"
    $stderr = Join-Path $OutputRoot "launcher_stderr.log"

    $process = Start-Process -FilePath $PythonExe -ArgumentList $Arguments `
        -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru

    Write-Host "def ProcessId : $($process.Id)"
    Write-Host "def Stdout    : $stdout"
    Write-Host "def Stderr    : $stderr"

    if ($OpenHtml) {
        $htmlPath = Join-Path $OutputRoot "index.html"
        Start-Job -ScriptBlock {
            param([int]$ProcessId, [string]$ReportPath)
            Wait-Process -Id $ProcessId -ErrorAction SilentlyContinue
            if (Test-Path -LiteralPath $ReportPath) {
                Start-Process -FilePath $ReportPath
            }
        } -ArgumentList $process.Id, $htmlPath | Out-Null
    }
}

function def_PrintRunContract {
    def_WriteStep 7 "Research contract"
    Write-Host "def Mode                 : $Mode"
    Write-Host "def Warm-up start        : $WarmupStartDate"
    Write-Host "def Evaluation baseline  : $EvaluationStartDate"
    Write-Host "def End date             : $(if ($EndDate) { $EndDate } else { 'LATEST_AVAILABLE_IN_LOCAL_DATA' })"
    Write-Host "def Market criteria      : DATA-DERIVED / ROLLING / NO FIXED MARKET CUTOFF"
    Write-Host "def Network execution    : 0"
    Write-Host "def Order execution      : 0"
}

function def_Main {
    def_WriteStep 2 "Preflight"
    def_TestRequiredPath -Path $EnginePath -Label "Engine"
    def_TestRequiredPath -Path $MembershipPath -Label "Membership"
    def_ValidateDates

    if ($Mode -eq "Real") {
        def_TestRequiredPath -Path $PricePath -Label "Price data"
        if (-not $FactorPath) {
            Write-Warning "FactorPath is blank. The engine may fall back to an estimated equal-weight market factor; final removal decisions should remain REVIEW/HOLD until an official factor file is supplied."
        }
        elseif (-not (Test-Path -LiteralPath $FactorPath)) {
            throw "Factor data not found: $FactorPath"
        }
    }

    def_PrintRunContract
    $pythonExe = def_ResolvePython
    def_WriteStep 15 "Python: $pythonExe"

    def_WriteStep 25 "Python compile validation"
    & $pythonExe -m py_compile $EnginePath
    if ($LASTEXITCODE -ne 0) { throw "Python compile validation failed" }

    if ($RunPytest) {
        $testPath = Join-Path $PSScriptRoot "test_VIA_TW_GroupingIndexRotationUnifiedEngine_v0201.py"
        def_TestRequiredPath -Path $testPath -Label "Pytest"
        def_WriteStep 38 "Run pytest"
        & $pythonExe -m pytest -q $testPath
        if ($LASTEXITCODE -ne 0) { throw "Pytest failed" }
    }

    $arguments = def_BuildArguments
    def_WriteStep 55 "Start $Mode engine run"

    if ($NonBlocking) {
        def_RunBackground -PythonExe $pythonExe -Arguments $arguments
        def_WriteStep 100 "Background launch complete" "PASS"
    }
    else {
        def_RunForeground -PythonExe $pythonExe -Arguments $arguments
        def_WriteStep 90 "Engine completed" "PASS"
        $htmlPath = Join-Path $OutputRoot "index.html"
        if ($OpenHtml -and (Test-Path -LiteralPath $htmlPath)) {
            Start-Process -FilePath $htmlPath
        }
        def_WriteStep 100 "Validation cycle complete" "PASS"
    }

    if ($KeepPowerShellOpen) {
        Write-Host "def PowerShell remains available. Do not close it while a background run is active."
    }
}

try {
    def_Main
}
catch {
    Write-Host "def [FAIL] $($_.Exception.Message)" -ForegroundColor Red
    throw
}
