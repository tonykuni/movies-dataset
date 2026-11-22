#requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string[]]$InputPath,
    [string]$OutputDirectory = ".\VIA_NLP_Unified_v7_Output",
    [ValidateSet("fast", "balanced", "deep")]
    [string]$Quality = "balanced",
    [string]$PythonCommand = "py",
    [switch]$OpenOutput
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Cli = Join-Path $Root "nlp_v7_upgrade\unified\via_nlp_unified_v7_cli.py"
if (-not (Test-Path -LiteralPath $Cli -PathType Leaf)) { throw "Missing v7 CLI: $Cli" }

$args = @($Cli, "--quality", $Quality, "--output-dir", $OutputDirectory, "--input") + $InputPath
Write-Host "[VIA] Unified NLP v7 / VIA-ENG-021" -ForegroundColor Cyan
Write-Host "[VIA] Source is immutable; extracted code is never executed." -ForegroundColor Yellow
& $PythonCommand @args
if ($LASTEXITCODE -ne 0) { throw "VIA Unified NLP v7 failed with exit code $LASTEXITCODE" }
if ($OpenOutput) {
    Start-Process -FilePath (Resolve-Path -LiteralPath $OutputDirectory)
}
