#requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [string[]]$InputPath,
    [string]$OutputDirectory = (Join-Path $PSScriptRoot 'VIA_NLP_Reconstruction_Output_v5'),
    [string]$LexiconPath = (Join-Path $PSScriptRoot 'VIA_NLP_SSOT_Lexicon_v5.json'),
    [double]$CommandThreshold = 0.45,
    [switch]$Regression
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Resolve-Python {
    foreach ($candidate in @('python', 'python3', 'py')) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($null -ne $command) { return $command.Source }
    }
    throw 'Python 3.9+ was not found.'
}

$python = Resolve-Python
$core = Join-Path $PSScriptRoot 'v5\via_nlp_reconstruction_v5.py'
if (-not (Test-Path -LiteralPath $core -PathType Leaf)) { throw "Missing v5 core: $core" }
if (-not (Test-Path -LiteralPath $LexiconPath -PathType Leaf)) { throw "Missing lexicon: $LexiconPath" }

$inputs = @($InputPath)
if ($Regression) {
    $inputs = @(
        (Join-Path $PSScriptRoot 'testmessage.txt'),
        (Join-Path $PSScriptRoot 'dialogue20260708.txt')
    )
}
if ($inputs.Count -eq 0) { throw 'Provide -InputPath or use -Regression.' }
foreach ($input in $inputs) {
    if (-not (Test-Path -LiteralPath $input -PathType Leaf)) { throw "Missing input: $input" }
}

$args = @($core) + $inputs + @('--output-dir', $OutputDirectory, '--lexicon', $LexiconPath, '--command-threshold', $CommandThreshold.ToString([Globalization.CultureInfo]::InvariantCulture))
& $python @args
if ($LASTEXITCODE -ne 0) { throw "v5 NLP reconstruction failed with exit code $LASTEXITCODE" }

if ($Regression) {
    $benchmark = Join-Path $PSScriptRoot 'v5\benchmark_v5_thresholds.py'
    $validator = Join-Path $PSScriptRoot 'validate_v5_integration.py'
    & $python $benchmark
    if ($LASTEXITCODE -ne 0) { throw "threshold benchmark failed with exit code $LASTEXITCODE" }
    & $python $validator
    if ($LASTEXITCODE -ne 0) { throw "v5 regression validation failed with exit code $LASTEXITCODE" }
}

Write-Host "PASS: v5 NLP output=$OutputDirectory threshold=$CommandThreshold" -ForegroundColor Green
Write-Host 'Source is read-only; command merge and semantic rewrite are projection-only; review_required remains enabled.' -ForegroundColor DarkGray
