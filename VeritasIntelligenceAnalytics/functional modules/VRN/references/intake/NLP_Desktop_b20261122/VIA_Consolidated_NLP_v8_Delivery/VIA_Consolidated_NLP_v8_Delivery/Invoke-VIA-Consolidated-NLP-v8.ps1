#requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string[]]$InputPath,
    [string]$OutputDirectory = "$PSScriptRoot\VIA_v8_Output",
    [ValidateSet('fast','balanced','deep')]
    [string]$Quality = 'balanced',
    [switch]$ControlCenter,
    [int]$Port = 8766
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$cli = Join-Path $root 'v8\via_consolidated_nlp_v8_cli.py'

if ($ControlCenter) {
    $api = Join-Path $root 'via_nlp_control_api_v8.py'
    Write-Host "Starting VIA Consolidated NLP v8 Control Center on port $Port"
    & python $api --host 0.0.0.0 --port $Port
    exit $LASTEXITCODE
}

$resolved = foreach ($item in $InputPath) {
    $candidate = Resolve-Path -LiteralPath $item -ErrorAction Stop
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
        throw "Input is not a file: $item"
    }
    $candidate.Path
}

New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$args = @($cli) + $resolved + @('--out', $OutputDirectory, '--quality', $Quality)
Write-Host "VIA Consolidated NLP v8: $($resolved.Count) input file(s)"
Write-Host "Output: $OutputDirectory"
& python @args
exit $LASTEXITCODE
