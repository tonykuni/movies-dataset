#requires -Version 7.0
[CmdletBinding()]
param(
    [string]$EnginePath = "$PSScriptRoot\VIA_TW_GroupingIndexRotationUnifiedEngine_v0201.py",
    [string]$MembershipPath = "$PSScriptRoot\VIA_ThreeList_CanonicalMembershipInput_v0100.csv",
    [string]$PricePath = "$env:USERPROFILE\OneDrive\桌面\tw_stock\StockData.parquet",
    [string]$FactorPath = "",
    [string]$OutputRoot = "$env:USERPROFILE\Downloads\VeritasIntelligenceAnalytics\outputs\VIA_TW_GroupingIndexRotation_v0201",
    [ValidateSet("Demo", "Real")]
    [string]$Mode = "Demo",
    [int]$DemoObservations = 160,
    [switch]$Strict,
    [switch]$RunPytest,
    [switch]$OpenHtml,
    [switch]$NonBlocking,
    [switch]$KeepPowerShellOpen
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
    throw "Python executable not found. Activate via_core_312 or provide Python on PATH."
}

function def_TestRequiredPath {
    param([string]$Path, [string]$Label)
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "$Label not found: $Path"
    }
}

function def_BuildArguments {
    $arguments = @(
        $EnginePath,
        "--membership", $MembershipPath,
        "--output-root", $OutputRoot
    )
    if ($Mode -eq "Demo") {
        $arguments += @("--demo", "--demo-observations", [string]$DemoObservations)
    }
    else {
        $arguments += @("--prices", $PricePath)
        if ($FactorPath) { $arguments += @("--factors", $FactorPath) }
    }
    if ($Strict) { $arguments += "--strict" }
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
}

function def_Main {
    def_WriteStep 3 "Preflight"
    def_TestRequiredPath -Path $EnginePath -Label "Engine"
    def_TestRequiredPath -Path $MembershipPath -Label "Membership"
    if ($Mode -eq "Real") { def_TestRequiredPath -Path $PricePath -Label "Price data" }

    $pythonExe = def_ResolvePython
    def_WriteStep 12 "Python: $pythonExe"

    def_WriteStep 22 "Python compile validation"
    & $pythonExe -m py_compile $EnginePath
    if ($LASTEXITCODE -ne 0) { throw "Python compile validation failed" }

    if ($RunPytest) {
        $testPath = Join-Path $PSScriptRoot "test_VIA_TW_GroupingIndexRotationUnifiedEngine_v0201.py"
        def_TestRequiredPath -Path $testPath -Label "Pytest"
        def_WriteStep 35 "Run pytest"
        & $pythonExe -m pytest -q $testPath
        if ($LASTEXITCODE -ne 0) { throw "Pytest failed" }
    }

    $arguments = def_BuildArguments
    def_WriteStep 50 "Start $Mode engine run"
    if ($NonBlocking) {
        def_RunBackground -PythonExe $pythonExe -Arguments $arguments
        def_WriteStep 100 "Background launch complete" "PASS"
        return
    }

    def_RunForeground -PythonExe $pythonExe -Arguments $arguments
    def_WriteStep 92 "Engine completed" "PASS"

    $htmlPath = Join-Path $OutputRoot "index.html"
    if ($OpenHtml -and (Test-Path -LiteralPath $htmlPath)) {
        Start-Process -FilePath $htmlPath
    }
    def_WriteStep 100 "Validation cycle complete" "PASS"
}

try {
    def_Main
}
catch {
    Write-Host "def [FAIL] $($_.Exception.Message)" -ForegroundColor Red
    throw
}
finally {
    if ($KeepPowerShellOpen) {
        Write-Host "def Press Enter to close..."
        [void](Read-Host)
    }
}
