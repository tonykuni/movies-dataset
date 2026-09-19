[CmdletBinding()]
param(
    [ValidateSet('Inspect', 'Verify', 'All')]
    [string]$Action = 'All',
    [string]$PluginRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$Root = '',
    [string]$RunsDir = '',
    [string]$Zip = '',
    [string]$ChecksumFile = '',
    [string]$BaseUrl = 'http://127.0.0.1:8766',
    [ValidateSet('Auto', 'Via', 'Standardized')]
    [string]$PackageKind = 'Auto',
    [string]$OutputRoot = (Join-Path $env:TEMP 'VIA_AzureFlow_QA_TaskTest'),
    [switch]$RunExtractedE2E,
    [switch]$NoArtifactProbe,
    [string]$TaskName = 'VIA-AzureFlow-QA-Test',
    [switch]$UseRegisteredTask,
    [ValidateRange(10, 3600)]
    [int]$TimeoutSeconds = 300
)

$ErrorActionPreference = 'Stop'
$pluginRoot = (Resolve-Path -LiteralPath ([Environment]::ExpandEnvironmentVariables($PluginRoot)) -ErrorAction Stop).Path
$runner = Join-Path $pluginRoot 'scripts\Invoke-VIA-AzureFlowQA-Scheduled.ps1'
if (-not (Test-Path -LiteralPath $runner -PathType Leaf)) {
    throw "Scheduled runner not found: $runner"
}
$testRoot = Join-Path ([Environment]::ExpandEnvironmentVariables($OutputRoot)) ("test-{0}" -f (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory -Path $testRoot -Force | Out-Null

function Assert-TaskResult {
    param([string]$RunDirectory)
    $resultPath = Join-Path $RunDirectory 'task_result.json'
    if (-not (Test-Path -LiteralPath $resultPath -PathType Leaf)) {
        throw "task_result.json was not produced: $RunDirectory"
    }
    $result = Get-Content -LiteralPath $resultPath -Raw | ConvertFrom-Json
    if ($result.status -ne 'PASS' -or [int]$result.exit_code -ne 0) {
        throw "Task result was not PASS. Status=$($result.status), ExitCode=$($result.exit_code), Path=$resultPath"
    }
    Write-Host "TASK_TEST_PASS: $resultPath"
    return $result
}

if ($UseRegisteredTask) {
    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction Stop
    Start-ScheduledTask -TaskName $TaskName
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    do {
        Start-Sleep -Seconds 2
        $info = Get-ScheduledTaskInfo -TaskName $TaskName
        $latest = Get-ChildItem -LiteralPath ([Environment]::ExpandEnvironmentVariables($OutputRoot)) -File -Recurse -Filter task_result.json -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($latest) {
            $candidate = Get-Content -LiteralPath $latest.FullName -Raw | ConvertFrom-Json
            if ($candidate.status -in @('PASS', 'FAIL')) { break }
        }
    } while ((Get-Date) -lt $deadline)
    if (-not $latest) { throw "Registered task did not produce task_result.json within $TimeoutSeconds seconds." }
    Assert-TaskResult -RunDirectory $latest.Directory.FullName | Out-Null
    exit 0
}

if ($Action -in @('Inspect', 'All') -and [string]::IsNullOrWhiteSpace($Root)) {
    throw "-Root is required for Action=$Action."
}
if ($Action -in @('Verify', 'All') -and [string]::IsNullOrWhiteSpace($Zip)) {
    throw "-Zip is required for Action=$Action."
}

$arguments = @(
    '-Action', $Action,
    '-PluginRoot', $pluginRoot,
    '-Root', $Root,
    '-RunsDir', $RunsDir,
    '-Zip', $Zip,
    '-ChecksumFile', $ChecksumFile,
    '-BaseUrl', $BaseUrl,
    '-PackageKind', $PackageKind,
    '-OutputRoot', $testRoot
)
if ($RunExtractedE2E) { $arguments += '-RunExtractedE2E' }
if ($NoArtifactProbe) { $arguments += '-NoArtifactProbe' }
$arguments = @($arguments | Where-Object { $_ -ne '' })

& $runner @arguments
if ($LASTEXITCODE -ne 0) {
    throw "Direct scheduled runner smoke test failed with exit code $LASTEXITCODE. OutputRoot=$testRoot"
}
$latestDir = Get-ChildItem -LiteralPath $testRoot -Directory -ErrorAction Stop | Sort-Object LastWriteTime -Descending | Select-Object -First 1
Assert-TaskResult -RunDirectory $latestDir.FullName | Out-Null
