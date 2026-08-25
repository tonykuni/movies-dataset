#requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$BaseRoot = "",

    [Parameter(Mandatory = $false)]
    [string]$OutputRoot = "",

    [Parameter(Mandatory = $false)]
    [ValidateRange(1, 3)]
    [int]$Rounds = 3,

    [Parameter(Mandatory = $false)]
    [switch]$PreviewOnly,

    [Parameter(Mandatory = $false)]
    [switch]$ActivateSandbox,

    [Parameter(Mandatory = $false)]
    [switch]$OpenReport
)

# =============================================================================
# def PARAMETERS
# =============================================================================
$def_PARAM_ENGINE_PATH = Join-Path $PSScriptRoot "VIA_CentralGovernment_AdaptiveDownwardGovernor_v0100.py"
$def_PARAM_LATEST_FILE = "LATEST_RUN.json"
$def_PARAM_BASE_CANDIDATES = @(
    "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics",
    "C:\Users\tonyk\Downloads\movies-dataset\VeritasIntelligenceAnalytics",
    "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics"
)
$def_PARAM_PYTHON_CANDIDATES = @(
    "C:\Users\tonyk\envs\via_core_312\Scripts\python.exe",
    "C:\Users\tonyk\envs\via_core\Scripts\python.exe",
    "C:\Users\tonyk\envs\via_ml\Scripts\python.exe"
)
$def_PARAM_ERROR_ACTION = "Stop"
$def_PARAM_PROGRESS_WIDTH = 24

$ErrorActionPreference = $def_PARAM_ERROR_ACTION
$ProgressPreference = "SilentlyContinue"

# =============================================================================
# def DISPLAY
# =============================================================================
function def-WriteBanner {
    param([string]$Title)
    Write-Host ""
    Write-Host ("=" * 96) -ForegroundColor DarkCyan
    Write-Host ("def " + $Title) -ForegroundColor Cyan
    Write-Host ("=" * 96) -ForegroundColor DarkCyan
}

function def-WriteStep {
    param(
        [int]$Percent,
        [string]$Message,
        [ValidateSet("INFO", "PASS", "WARN", "FAIL")]
        [string]$Status = "INFO"
    )
    $safePercent = [Math]::Max(0, [Math]::Min(100, $Percent))
    $filled = [Math]::Floor(($safePercent / 100.0) * $def_PARAM_PROGRESS_WIDTH)
    $empty = $def_PARAM_PROGRESS_WIDTH - $filled
    $bar = ("█" * $filled) + ("░" * $empty)
    $color = switch ($Status) {
        "PASS" { "Green" }
        "WARN" { "Yellow" }
        "FAIL" { "Red" }
        default { "Cyan" }
    }
    Write-Host ("def [{0,3}%] [{1}] [{2}] {3}" -f $safePercent, $bar, $Status, $Message) -ForegroundColor $color
}

# =============================================================================
# def POWERSHELL AST SELF-GATE
# =============================================================================
function def-TestPowerShellAst {
    param([string]$ScriptPath)
    $tokens = $null
    $errors = $null
    [System.Management.Automation.Language.Parser]::ParseFile(
        $ScriptPath,
        [ref]$tokens,
        [ref]$errors
    ) | Out-Null
    if ($null -ne $errors -and $errors.Count -gt 0) {
        $detail = ($errors | ForEach-Object { $_.ToString() }) -join [Environment]::NewLine
        throw "PowerShell AST validation failed:$([Environment]::NewLine)$detail"
    }
    return $true
}

# =============================================================================
# def PATH RESOLUTION
# =============================================================================
function def-ResolveBaseRoot {
    param([string]$RequestedRoot)
    if (-not [string]::IsNullOrWhiteSpace($RequestedRoot)) {
        $resolved = [System.IO.Path]::GetFullPath($RequestedRoot)
        if (-not (Test-Path -LiteralPath $resolved -PathType Container)) {
            throw "BaseRoot not found: $resolved"
        }
        return $resolved
    }
    foreach ($candidate in $def_PARAM_BASE_CANDIDATES) {
        if (Test-Path -LiteralPath $candidate -PathType Container) {
            return $candidate
        }
    }
    throw "No VIA base root found. Supply -BaseRoot explicitly."
}

function def-ResolveOutputRoot {
    param(
        [string]$ResolvedBaseRoot,
        [string]$RequestedOutputRoot
    )
    if (-not [string]::IsNullOrWhiteSpace($RequestedOutputRoot)) {
        return [System.IO.Path]::GetFullPath($RequestedOutputRoot)
    }
    return (Join-Path $ResolvedBaseRoot "_via_adaptive_downward_runs")
}

function def-ResolvePython {
    foreach ($candidate in $def_PARAM_PYTHON_CANDIDATES) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return $candidate
        }
    }
    foreach ($commandName in @("python", "py")) {
        $command = Get-Command $commandName -ErrorAction SilentlyContinue
        if ($null -ne $command) {
            return $command.Source
        }
    }
    throw "Python not found. Expected via_core_312/via_core or python/py on PATH."
}

# =============================================================================
# def EXECUTION
# =============================================================================
function def-BuildArguments {
    param(
        [string]$ResolvedBaseRoot,
        [string]$ResolvedOutputRoot
    )
    $arguments = @(
        $def_PARAM_ENGINE_PATH,
        "--base-root", $ResolvedBaseRoot,
        "--output-root", $ResolvedOutputRoot,
        "--rounds", [string]$Rounds
    )
    if (-not $PreviewOnly) {
        $arguments += "--apply-safe-fixes"
    }
    if ($ActivateSandbox) {
        $arguments += "--activate-sandbox"
    }
    return $arguments
}

function def-ReadLatestSummary {
    param([string]$ResolvedOutputRoot)
    $latestPath = Join-Path $ResolvedOutputRoot $def_PARAM_LATEST_FILE
    if (-not (Test-Path -LiteralPath $latestPath -PathType Leaf)) {
        return $null
    }
    return (Get-Content -LiteralPath $latestPath -Raw -Encoding UTF8 | ConvertFrom-Json -Depth 100)
}

function def-InvokeAdaptiveGovernor {
    param(
        [string]$PythonExecutable,
        [string[]]$Arguments,
        [string]$ResolvedOutputRoot
    )
    New-Item -ItemType Directory -Path $ResolvedOutputRoot -Force | Out-Null
    def-WriteStep -Percent 18 -Message "Python engine self-test" -Status "INFO"
    & $PythonExecutable $def_PARAM_ENGINE_PATH --selftest
    if ($LASTEXITCODE -ne 0) {
        throw "Governor self-test failed with exit code $LASTEXITCODE"
    }
    def-WriteStep -Percent 31 -Message "Three-round panoramic governance" -Status "INFO"
    & $PythonExecutable @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Governor execution failed with exit code $LASTEXITCODE"
    }
    def-WriteStep -Percent 88 -Message "Read append-only final summary" -Status "INFO"
    $summary = def-ReadLatestSummary -ResolvedOutputRoot $ResolvedOutputRoot
    if ($null -eq $summary) {
        throw "LATEST_RUN.json was not generated."
    }
    return $summary
}

function def-ShowSummary {
    param([object]$Summary)
    $status = if ([string]$Summary.gate -like "GREEN*") { "PASS" } elseif ([string]$Summary.gate -like "YELLOW*") { "WARN" } else { "FAIL" }
    def-WriteStep -Percent 100 -Message ("Gate: " + [string]$Summary.gate) -Status $status
    Write-Host "def RunDir             : $($Summary.run_dir)"
    Write-Host "def SandboxRoot        : $($Summary.sandbox_root)"
    Write-Host "def Rounds             : $($Summary.rounds_executed)"
    Write-Host "def CanonicalMutation  : $($Summary.canonical_mutation)"
    Write-Host "def CanonicalIntegrity : $($Summary.canonical_integrity.ok)"
    Write-Host "def FinalHTML          : $($Summary.final_html)"
    Write-Host "def FinalJSON          : $($Summary.final_json)"
}

function def-OpenFinalReport {
    param([object]$Summary)
    if (-not $OpenReport) {
        return
    }
    $reportPath = [string]$Summary.final_html
    if (Test-Path -LiteralPath $reportPath -PathType Leaf) {
        Start-Process -FilePath $reportPath | Out-Null
    }
}

# =============================================================================
# def MAIN
# =============================================================================
function def-Main {
    def-WriteBanner -Title "VIA CENTRAL GOVERNANCE · ADAPTIVE DOWNWARD v0100"
    def-WriteStep -Percent 5 -Message "Native PowerShell AST self-gate" -Status "INFO"
    [void](def-TestPowerShellAst -ScriptPath $PSCommandPath)
    def-WriteStep -Percent 9 -Message "Resolve canonical root without mutation" -Status "INFO"
    if (-not (Test-Path -LiteralPath $def_PARAM_ENGINE_PATH -PathType Leaf)) {
        throw "Engine not found: $def_PARAM_ENGINE_PATH"
    }
    $resolvedBaseRoot = def-ResolveBaseRoot -RequestedRoot $BaseRoot
    $resolvedOutputRoot = def-ResolveOutputRoot -ResolvedBaseRoot $resolvedBaseRoot -RequestedOutputRoot $OutputRoot
    $pythonExecutable = def-ResolvePython
    $arguments = def-BuildArguments -ResolvedBaseRoot $resolvedBaseRoot -ResolvedOutputRoot $resolvedOutputRoot

    Write-Host "def BaseRoot     : $resolvedBaseRoot"
    Write-Host "def OutputRoot   : $resolvedOutputRoot"
    Write-Host "def Python       : $pythonExecutable"
    Write-Host "def Rounds       : $Rounds"
    Write-Host "def PreviewOnly  : $([bool]$PreviewOnly)"
    Write-Host "def Activate     : $([bool]$ActivateSandbox)"
    Write-Host "def Policy       : sandbox-only / append-only / no canonical mutation"

    $summary = def-InvokeAdaptiveGovernor -PythonExecutable $pythonExecutable -Arguments $arguments -ResolvedOutputRoot $resolvedOutputRoot
    def-ShowSummary -Summary $summary
    def-OpenFinalReport -Summary $summary
}

try {
    def-Main
}
catch {
    def-WriteStep -Percent 100 -Message $_.Exception.Message -Status "FAIL"
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
    Write-Host ""
    Write-Host "PowerShell remains open. No canonical mutation was executed." -ForegroundColor Yellow
}
