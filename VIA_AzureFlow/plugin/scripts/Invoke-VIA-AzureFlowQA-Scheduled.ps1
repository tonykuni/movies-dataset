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
    [string]$OutputRoot = (Join-Path $env:USERPROFILE 'Downloads\VIA_AzureFlow_QA_Scheduled'),
    [switch]$RunExtractedE2E,
    [switch]$NoArtifactProbe,
    [switch]$PurgeOldRuns,
    [ValidateRange(1, 3650)]
    [int]$RetentionDays = 30
)

$ErrorActionPreference = 'Stop'
$startedAt = Get-Date

function Write-TaskLog {
    param([string]$Message)
    $line = "[{0}] {1}" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz'), $Message
    Add-Content -LiteralPath $script:LogPath -Value $line -Encoding UTF8
    Write-Host $line
}

function Resolve-OptionalPath {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { return '' }
    return [Environment]::ExpandEnvironmentVariables($Value)
}

$runDir = $null
$exitCode = 1
try {
    $pluginRoot = (Resolve-Path -LiteralPath (Resolve-OptionalPath $PluginRoot) -ErrorAction Stop).Path
    $launcher = Join-Path $pluginRoot 'Invoke-VIA-AzureFlowQA.ps1'
    if (-not (Test-Path -LiteralPath $launcher -PathType Leaf)) {
        throw "VIA AzureFlow QA launcher not found: $launcher"
    }

    if ($Action -in @('Inspect', 'All') -and [string]::IsNullOrWhiteSpace($Root)) {
        throw "-Root is required for Action=$Action."
    }
    if ($Action -in @('Verify', 'All') -and [string]::IsNullOrWhiteSpace($Zip)) {
        throw "-Zip is required for Action=$Action."
    }

    $outputRoot = [Environment]::ExpandEnvironmentVariables($OutputRoot)
    New-Item -ItemType Directory -Path $outputRoot -Force | Out-Null
    $stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
    $runDir = Join-Path $outputRoot ("{0}-{1}" -f $Action, $stamp)
    New-Item -ItemType Directory -Path $runDir -Force | Out-Null
    $script:LogPath = Join-Path $runDir 'task_scheduler.log'
    Write-TaskLog "Scheduled run started. Action=$Action"
    Write-TaskLog "PluginRoot=$pluginRoot"
    Write-TaskLog "Output=$runDir"

    $arguments = @(
        '-Action', $Action,
        '-BaseUrl', $BaseUrl,
        '-Output', $runDir,
        '-PackageKind', $PackageKind
    )
    if (-not [string]::IsNullOrWhiteSpace($Root)) { $arguments += @('-Root', $Root) }
    if (-not [string]::IsNullOrWhiteSpace($RunsDir)) { $arguments += @('-RunsDir', $RunsDir) }
    if (-not [string]::IsNullOrWhiteSpace($Zip)) { $arguments += @('-Zip', $Zip) }
    if (-not [string]::IsNullOrWhiteSpace($ChecksumFile)) { $arguments += @('-ChecksumFile', $ChecksumFile) }
    if ($RunExtractedE2E) { $arguments += '-RunExtractedE2E' }
    if ($NoArtifactProbe) { $arguments += '-NoArtifactProbe' }

    Write-TaskLog ("Calling launcher with {0} arguments." -f $arguments.Count)
    & $launcher @arguments 2>&1 | Tee-Object -FilePath (Join-Path $runDir 'launcher_output.txt')
    $exitCode = $LASTEXITCODE
    $summaryPath = Join-Path $runDir 'VIA_AzureFlow_QA_Run_Summary.json'
    $status = if ($exitCode -eq 0 -and (Test-Path -LiteralPath $summaryPath -PathType Leaf)) { 'PASS' } else { 'FAIL' }
    if ($status -eq 'FAIL' -and $exitCode -eq 0) { $exitCode = 2 }

    $taskResult = [ordered]@{
        schema = 'VIA_AZUREFLOW_QA_TASK_RUN/1.0'
        plugin = 'via-azureflow-qa-plugin'
        action = $Action
        started_at = $startedAt.ToString('o')
        finished_at = (Get-Date).ToString('o')
        status = $status
        exit_code = $exitCode
        output_directory = $runDir
        summary = if (Test-Path -LiteralPath $summaryPath -PathType Leaf) { $summaryPath } else { $null }
        log = (Join-Path $runDir 'task_scheduler.log')
        launcher_output = (Join-Path $runDir 'launcher_output.txt')
        arguments = $arguments
        safety = [ordered]@{
            source_write = $false
            source_delete = $false
            network_default = $false
            extracted_e2e_opt_in = [bool]$RunExtractedE2E
            human_review_required = $true
        }
    }
    $taskResultPath = Join-Path $runDir 'task_result.json'
    $taskResult | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $taskResultPath -Encoding UTF8
    Write-TaskLog "Scheduled run finished. Status=$status ExitCode=$exitCode"

    if ($PurgeOldRuns -and $RetentionDays -gt 0) {
        $cutoff = (Get-Date).AddDays(-$RetentionDays)
        Get-ChildItem -LiteralPath $outputRoot -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.LastWriteTime -lt $cutoff } |
            Remove-Item -Recurse -Force
        Write-TaskLog "Purged scheduled output directories older than $RetentionDays days under $outputRoot."
    }
}
catch {
    if (-not $runDir) {
        $fallbackRoot = [Environment]::ExpandEnvironmentVariables($OutputRoot)
        New-Item -ItemType Directory -Path $fallbackRoot -Force | Out-Null
        $runDir = Join-Path $fallbackRoot ("FAILED-{0}" -f (Get-Date -Format 'yyyyMMdd_HHmmss'))
        New-Item -ItemType Directory -Path $runDir -Force | Out-Null
        $script:LogPath = Join-Path $runDir 'task_scheduler.log'
    }
    $message = $_.Exception.Message
    Write-TaskLog "Scheduled run failed before completion: $message"
    [ordered]@{
        schema = 'VIA_AZUREFLOW_QA_TASK_RUN/1.0'
        plugin = 'via-azureflow-qa-plugin'
        action = $Action
        status = 'FAIL'
        exit_code = 1
        output_directory = $runDir
        error = $message
        log = $script:LogPath
        safety = [ordered]@{
            source_write = $false
            source_delete = $false
            network_default = $false
            human_review_required = $true
        }
    } | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $runDir 'task_result.json') -Encoding UTF8
    $exitCode = 1
}

exit $exitCode
