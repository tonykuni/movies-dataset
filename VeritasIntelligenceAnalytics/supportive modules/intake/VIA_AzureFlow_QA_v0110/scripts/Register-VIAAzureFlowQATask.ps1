[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$TaskName = 'VIA-AzureFlow-QA-All',
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
    [ValidateSet('Once', 'Daily', 'Weekly')]
    [string]$Schedule = 'Daily',
    [datetime]$At = (Get-Date).Date.AddHours(2),
    [string]$UserId = '',
    [switch]$RunOnlyWhenUserIsLoggedOn,
    [switch]$RunWithHighest,
    [switch]$RunExtractedE2E,
    [switch]$NoArtifactProbe,
    [switch]$PurgeOldRuns,
    [ValidateRange(1, 3650)]
    [int]$RetentionDays = 30,
    [switch]$Unregister
)

$ErrorActionPreference = 'Stop'

function Add-Argument {
    param([System.Collections.Generic.List[string]]$List, [string]$Name, [string]$Value)
    if (-not [string]::IsNullOrWhiteSpace($Value)) {
        $List.Add($Name)
        $List.Add($Value)
    }
}

$pluginRoot = (Resolve-Path -LiteralPath ([Environment]::ExpandEnvironmentVariables($PluginRoot)) -ErrorAction Stop).Path
$runner = Join-Path $pluginRoot 'scripts\Invoke-VIA-AzureFlowQA-Scheduled.ps1'
if (-not (Test-Path -LiteralPath $runner -PathType Leaf)) {
    throw "Scheduled runner not found: $runner"
}

if ($Unregister) {
    if ($PSCmdlet.ShouldProcess($TaskName, 'Unregister scheduled task')) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
        Write-Host "Unregistered task: $TaskName"
    }
    exit 0
}

if ($Action -in @('Inspect', 'All') -and [string]::IsNullOrWhiteSpace($Root)) {
    throw "-Root is required for Action=$Action."
}
if ($Action -in @('Verify', 'All') -and [string]::IsNullOrWhiteSpace($Zip)) {
    throw "-Zip is required for Action=$Action."
}

$arguments = [System.Collections.Generic.List[string]]::new()
Add-Argument $arguments '-Action' $Action
Add-Argument $arguments '-PluginRoot' $pluginRoot
Add-Argument $arguments '-BaseUrl' $BaseUrl
Add-Argument $arguments '-PackageKind' $PackageKind
Add-Argument $arguments '-OutputRoot' $OutputRoot
Add-Argument $arguments '-Root' $Root
Add-Argument $arguments '-RunsDir' $RunsDir
Add-Argument $arguments '-Zip' $Zip
Add-Argument $arguments '-ChecksumFile' $ChecksumFile
Add-Argument $arguments '-RetentionDays' ([string]$RetentionDays)
if ($RunExtractedE2E) { $arguments.Add('-RunExtractedE2E') }
if ($NoArtifactProbe) { $arguments.Add('-NoArtifactProbe') }
if ($PurgeOldRuns) { $arguments.Add('-PurgeOldRuns') }

# Encode arguments as one PowerShell-safe command line for the scheduled task.
$escaped = $arguments | ForEach-Object { "'" + ($_ -replace "'", "''") + "'" }
$argumentString = "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$runner`" " + ($escaped -join ' ')
$actionObject = New-ScheduledTaskAction -Execute 'PowerShell.exe' -Argument $argumentString

switch ($Schedule) {
    'Once' { $trigger = New-ScheduledTaskTrigger -Once -At $At }
    'Weekly' { $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At $At }
    default { $trigger = New-ScheduledTaskTrigger -Daily -At $At }
}

$principalArgs = @{ UserId = if ($UserId) { $UserId } else { "$env:USERDOMAIN\$env:USERNAME" }; LogonType = 'Interactive'; RunLevel = if ($RunWithHighest) { 'Highest' } else { 'Limited' } }
$principal = New-ScheduledTaskPrincipal @principalArgs
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 4) -MultipleInstances IgnoreNew
$description = 'VIA AzureFlow QA Plug-in deterministic inspect/verify/all run. Source files remain read-only; review is required.'
$task = New-ScheduledTask -Action $actionObject -Trigger $trigger -Principal $principal -Settings $settings -Description $description

if ($RunOnlyWhenUserIsLoggedOn) {
    # Interactive is already the default. This switch documents the intended policy.
    Write-Host 'Policy: task runs only in the selected interactive user session.'
}

if ($PSCmdlet.ShouldProcess($TaskName, "Register or update scheduled task ($Schedule at $At)")) {
    Register-ScheduledTask -TaskName $TaskName -InputObject $task -Force | Out-Null
    Write-Host "Registered task: $TaskName"
    Write-Host "Schedule: $Schedule at $At"
    Write-Host "Action: $Action"
    Write-Host "OutputRoot: $OutputRoot"
    Write-Host "Runner: $runner"
}
