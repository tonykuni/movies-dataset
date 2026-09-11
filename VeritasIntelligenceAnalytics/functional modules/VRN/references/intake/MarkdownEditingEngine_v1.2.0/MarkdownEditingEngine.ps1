[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet("doctor", "check", "analyze-structure", "fix", "reorganize", "build-book", "all")]
    [string]$Action = "doctor",
    [Parameter(Position = 1)]
    [string]$InputPath,
    [ValidateSet("prettier", "mdformat", "rumdl", "pandoc", "none")]
    [string]$Formatter,
    [switch]$DryRun,
    [switch]$Strict,
    [switch]$Toc,
    [switch]$NoToc,
    [switch]$NoRecursive,
    [ValidateRange(1, 16)]
    [int]$Workers,
    [string]$ReportPath,
    [string]$BookOutputPath,
    [switch]$WaitForKey
)

$ErrorActionPreference = "Stop"
$EngineRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $EngineRoot ".venv\Scripts\python.exe"
$SystemPythonCommands = @("py", "python", "python3")
$EngineScript = Join-Path $EngineRoot "engine\markdown_engine.py"

function defGet-PythonCommand {
    if (Test-Path -LiteralPath $VenvPython) {
        return @($VenvPython)
    }
    foreach ($Candidate in $SystemPythonCommands) {
        if (Get-Command $Candidate -ErrorAction SilentlyContinue) {
            if ($Candidate -eq "py") { return @($Candidate, "-3") }
            return @($Candidate)
        }
    }
    throw "Python 3 not found. Run .\Install-MarkdownEditingEngine.ps1 first."
}

function defInvoke-MarkdownEditingEngine {
    $PythonCommand = @(defGet-PythonCommand)
    $Arguments = @($EngineScript, $Action)
    if ($InputPath) { $Arguments += @("--input", (Resolve-Path -LiteralPath $InputPath).Path) }
    if ($Formatter) { $Arguments += @("--formatter", $Formatter) }
    if ($DryRun) { $Arguments += "--dry-run" }
    if ($Strict) { $Arguments += "--strict" }
    if ($Toc) { $Arguments += "--toc" }
    if ($NoToc) { $Arguments += "--no-toc" }
    if ($NoRecursive) { $Arguments += "--no-recursive" }
    if ($Workers) { $Arguments += @("--workers", $Workers) }
    if ($ReportPath) { $Arguments += @("--report", $ReportPath) }
    if ($BookOutputPath) { $Arguments += @("--book-output", $BookOutputPath) }
    $PythonPrefixArguments = @()
    if ($PythonCommand.Count -gt 1) {
        $PythonPrefixArguments = $PythonCommand[1..($PythonCommand.Count - 1)]
    }
    & $PythonCommand[0] @PythonPrefixArguments @Arguments | Out-Host
    $EngineExitCode = $LASTEXITCODE
    return $EngineExitCode
}

$FinalExitCode = defInvoke-MarkdownEditingEngine
[Environment]::ExitCode = $FinalExitCode
if ($WaitForKey) {
    Read-Host "按 Enter 關閉"
}
