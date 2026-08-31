#requires -Version 7.0

[CmdletBinding()]
param(
    [string]$PythonExe = "python",
    [string]$EngineRoot = $PSScriptRoot,
    [ValidateSet("All", "Test", "Demo")]
    [string]$Mode = "All",
    [string]$OutputDirectory = "via_contract_engine_output",
    [bool]$OpenHtml = $true
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

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# def 01 PARAMETERS
$def_SourceDirectory = Join-Path $EngineRoot "src"
$def_TestDirectory = Join-Path $EngineRoot "tests"
$def_OutputPath = Join-Path $EngineRoot $OutputDirectory
$def_HtmlPath = Join-Path $def_OutputPath "via_contract_command_console.html"
$def_TwinHtmlPath = Join-Path $def_OutputPath "via_contract_twin_report.html"
$def_TotalSteps = 6

function def_WriteStep {
    param(
        [Parameter(Mandatory)]
        [int]$Step,
        [Parameter(Mandatory)]
        [string]$Message,
        [ValidateSet("INFO", "PASS", "WARN", "FAIL")]
        [string]$Status = "INFO"
    )

    $def_Percent = [math]::Min(100, [math]::Round(($Step / $def_TotalSteps) * 100))
    $def_Filled = [math]::Floor($def_Percent / 5)
    $def_Bar = ("█" * $def_Filled) + ("░" * (20 - $def_Filled))
    Write-Host ("def [{0,3}%] [{1}] [{2}] {3}" -f $def_Percent, $def_Bar, $Status, $Message)
}

function def_InvokePython {
    param(
        [Parameter(Mandatory)]
        [string[]]$Arguments
    )

    $def_PreviousPythonPath = $env:PYTHONPATH
    try {
        if ([string]::IsNullOrWhiteSpace($def_PreviousPythonPath)) {
            $env:PYTHONPATH = $def_SourceDirectory
        }
        else {
            $env:PYTHONPATH = "$def_SourceDirectory;$def_PreviousPythonPath"
        }

        & $PythonExe @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "Python command failed with exit code $LASTEXITCODE"
        }
    }
    finally {
        $env:PYTHONPATH = $def_PreviousPythonPath
    }
}

function def_TestPreflight {
    if (-not (Test-Path -LiteralPath $EngineRoot -PathType Container)) {
        throw "EngineRoot not found: $EngineRoot"
    }
    if (-not (Test-Path -LiteralPath $def_SourceDirectory -PathType Container)) {
        throw "Source directory not found: $def_SourceDirectory"
    }
    $null = Get-Command $PythonExe -ErrorAction Stop
    def_InvokePython -Arguments @("-c", "import pydantic; print('def Pydantic:', pydantic.__version__)")
}

function def_RunTests {
    def_InvokePython -Arguments @("-m", "unittest", "discover", "-s", $def_TestDirectory, "-v")
}

function def_RunDemo {
    def_InvokePython -Arguments @("-m", "via_interface_engine", "demo", "--output-dir", $def_OutputPath)
}

function def_OpenHtmlUi {
    if (-not $OpenHtml) {
        def_WriteStep -Step 5 -Message "HTML U/I open skipped" -Status "WARN"
        return
    }
    if (-not (Test-Path -LiteralPath $def_HtmlPath -PathType Leaf)) {
        throw "HTML U/I not found: $def_HtmlPath"
    }
    Start-Process -FilePath $def_HtmlPath
    if (Test-Path -LiteralPath $def_TwinHtmlPath -PathType Leaf) {
        Start-Process -FilePath $def_TwinHtmlPath
    }
}

function def_Main {
    try {
        def_WriteStep -Step 1 -Message "VIA Contract Interface Engine preflight" -Status "INFO"
        def_TestPreflight

        if ($Mode -in @("All", "Test")) {
            def_WriteStep -Step 2 -Message "Run unit and integration tests" -Status "INFO"
            def_RunTests
            def_WriteStep -Step 3 -Message "Unit and integration tests completed" -Status "PASS"
        }
        else {
            def_WriteStep -Step 3 -Message "Tests skipped by Mode" -Status "WARN"
        }

        if ($Mode -in @("All", "Demo")) {
            def_WriteStep -Step 4 -Message "Generate Schema, HTML U/I, and Digital Twin evidence" -Status "INFO"
            def_RunDemo
            def_OpenHtmlUi
        }
        else {
            def_WriteStep -Step 5 -Message "Demo and HTML U/I skipped by Mode" -Status "WARN"
        }

        def_WriteStep -Step 6 -Message "VIA Contract Interface Engine completed; PowerShell remains open" -Status "PASS"
    }
    catch {
        def_WriteStep -Step 6 -Message $_.Exception.Message -Status "FAIL"
        throw
    }
}

def_Main


