[CmdletBinding()]
param(
    [ValidateSet('Inspect', 'Verify', 'All')]
    [string]$Action = 'All',
    [string]$Root = '',
    [string]$RunsDir = '',
    [string]$Zip = '',
    [string]$ChecksumFile = '',
    [string]$Output = (Join-Path (Get-Location) 'VIA_AzureFlow_QA_Output'),
    [string]$BaseUrl = 'http://127.0.0.1:8766',
    [ValidateSet('Auto', 'Via', 'Standardized')]
    [string]$PackageKind = 'Auto',
    [switch]$RunExtractedE2E,
    [switch]$NoArtifactProbe
)

$ErrorActionPreference = 'Stop'
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$cli = Join-Path $scriptDir 'scripts\via_azureflow_qa.py'
if (-not (Test-Path -LiteralPath $cli -PathType Leaf)) {
    throw "VIA AzureFlow QA CLI not found: $cli"
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $python) {
    throw 'Python 3 was not found. Install Python 3 and rerun this launcher.'
}

$pythonCommand = $python.Source
$arguments = @($cli, $Action.ToLowerInvariant(), '--base-url', $BaseUrl, '--out-dir', $Output, '--package-kind', $PackageKind.ToLowerInvariant())
if ($Root) { $arguments += @('--root', $Root) }
if ($RunsDir) { $arguments += @('--runs-dir', $RunsDir) }
if ($Zip) { $arguments += @('--zip', $Zip) }
if ($ChecksumFile) { $arguments += @('--checksum-file', $ChecksumFile) }
if ($RunExtractedE2E) { $arguments += '--run-extracted-e2e' }
if ($NoArtifactProbe) { $arguments += '--no-artifact-probe' }

Write-Host 'VIA 天青智流 AzureFlow QA Plug-in' -ForegroundColor Cyan
Write-Host ("Action: {0}" -f $Action) -ForegroundColor DarkCyan
Write-Host ("Output: {0}" -f $Output) -ForegroundColor DarkCyan
& $pythonCommand @arguments
exit $LASTEXITCODE
