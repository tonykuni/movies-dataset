[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Root,
    [Parameter(Mandatory = $true)]
    [string]$Zip,
    [string]$ChecksumFile = '',
    [string]$RunsDir = '',
    [string]$BaseUrl = 'http://127.0.0.1:8766',
    [ValidateSet('Auto', 'Via', 'Standardized')]
    [string]$PackageKind = 'Auto',
    [string]$Output = (Join-Path (Get-Location) 'VIA_AzureFlow_QA_System_Output'),
    [switch]$RunExtractedE2E,
    [switch]$NoArtifactProbe,
    [switch]$ActivateSchedule,
    [string]$TaskName = 'VIA-AzureFlow-QA-All',
    [ValidateSet('Once', 'Daily', 'Weekly')]
    [string]$Schedule = 'Daily',
    [datetime]$At = (Get-Date).Date.AddHours(2),
    [string]$UserId = '',
    [switch]$RunOnlyWhenUserIsLoggedOn,
    [switch]$RunWithHighest,
    [switch]$PurgeOldRuns,
    [ValidateRange(1, 3650)]
    [int]$RetentionDays = 30
)

$ErrorActionPreference = 'Stop'
$pluginRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$systemCli = Join-Path $pluginRoot 'scripts\via_azureflow_qa_system.py'
$register = Join-Path $pluginRoot 'scripts\Register-VIAAzureFlowQATask.ps1'
if (-not (Test-Path -LiteralPath $systemCli -PathType Leaf)) { throw "Unified system CLI not found: $systemCli" }
if ($ActivateSchedule -and -not (Test-Path -LiteralPath $register -PathType Leaf)) { throw "Task registration script not found: $register" }

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
if (-not $python) { throw 'Python 3 was not found. Install Python 3 and rerun this system launcher.' }

New-Item -ItemType Directory -Path $Output -Force | Out-Null
$arguments = @(
    $systemCli,
    '--root', $Root,
    '--zip', $Zip,
    '--base-url', $BaseUrl,
    '--package-kind', $PackageKind.ToLowerInvariant(),
    '--out-dir', $Output
)
if ($ChecksumFile) { $arguments += @('--checksum-file', $ChecksumFile) }
if ($RunsDir) { $arguments += @('--runs-dir', $RunsDir) }
if ($RunExtractedE2E) { $arguments += '--run-extracted-e2e' }
if ($NoArtifactProbe) { $arguments += '--no-artifact-probe' }

Write-Host 'VIA 天青智流 AzureFlow QA Plug-in｜Complete System' -ForegroundColor Cyan
Write-Host ("Root: {0}" -f $Root) -ForegroundColor DarkCyan
Write-Host ("ZIP: {0}" -f $Zip) -ForegroundColor DarkCyan
Write-Host ("Output: {0}" -f $Output) -ForegroundColor DarkCyan
& $python.Source @arguments
$qaExit = $LASTEXITCODE
$systemReport = Join-Path $Output 'VIA_AzureFlow_QA_System_Report.json'
if (-not (Test-Path -LiteralPath $systemReport -PathType Leaf)) {
    Write-Error "Unified system report was not produced: $systemReport"
    exit 2
}

$activationResult = [ordered]@{
    schema = 'VIA_AZUREFLOW_QA_SYSTEM_ACTIVATION/1.0'
    plugin = 'via-azureflow-qa-plugin'
    requested = [bool]$ActivateSchedule
    status = if ($ActivateSchedule) { 'PENDING' } else { 'READY_FOR_WINDOWS_ACTIVATION' }
    registered = $false
    task_name = $TaskName
    system_report = $systemReport
    qa_exit_code = $qaExit
    safety = [ordered]@{
        source_write = $false
        source_delete = $false
        automatic_command_activation = $false
        ssot_promotion = $false
        human_review_required = $true
    }
}

if ($qaExit -ne 0) {
    $activationResult.status = 'BLOCKED_QA_NOT_PASS'
    $activationResult | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $Output 'activation_result.json') -Encoding UTF8
    exit $qaExit
}

if ($ActivateSchedule) {
    $registrationArgs = @(
        '-TaskName', $TaskName,
        '-Action', 'All',
        '-PluginRoot', $pluginRoot,
        '-Root', $Root,
        '-Zip', $Zip,
        '-BaseUrl', $BaseUrl,
        '-PackageKind', $PackageKind,
        '-OutputRoot', (Join-Path $Output 'scheduled') ,
        '-Schedule', $Schedule,
        '-At', $At,
        '-RetentionDays', $RetentionDays
    )
    if ($UserId) { $registrationArgs += @('-UserId', $UserId) }
    if ($ChecksumFile) { $registrationArgs += @('-ChecksumFile', $ChecksumFile) }
    if ($RunsDir) { $registrationArgs += @('-RunsDir', $RunsDir) }
    if ($RunOnlyWhenUserIsLoggedOn) { $registrationArgs += '-RunOnlyWhenUserIsLoggedOn' }
    if ($RunWithHighest) { $registrationArgs += '-RunWithHighest' }
    if ($RunExtractedE2E) { $registrationArgs += '-RunExtractedE2E' }
    if ($NoArtifactProbe) { $registrationArgs += '-NoArtifactProbe' }
    if ($PurgeOldRuns) { $registrationArgs += '-PurgeOldRuns' }

    try {
        & $register @registrationArgs
        $registerExit = $LASTEXITCODE
        if ($registerExit -ne 0) { throw "Register-VIAAzureFlowQATask.ps1 exited with code $registerExit." }
        $activationResult.status = 'ACTIVATED'
        $activationResult.registered = $true
        $activationResult.registration_arguments = $registrationArgs
        $activationResult.register_exit_code = 0
    }
    catch {
        $activationResult.status = 'ACTIVATION_FAILED'
        $activationResult.error = $_.Exception.Message
        $activationResult.register_exit_code = 1
        $activationResult.registration_arguments = $registrationArgs
        $activationResult | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $Output 'activation_result.json') -Encoding UTF8
        exit 3
    }
}

$activationResult | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $Output 'activation_result.json') -Encoding UTF8
if ($ActivateSchedule) {
    Write-Host ("Task Scheduler activated: {0}" -f $TaskName) -ForegroundColor Green
}
else {
    Write-Host 'QA PASS. Schedule is ready; no Task Scheduler registration was requested.' -ForegroundColor Yellow
}
exit 0
