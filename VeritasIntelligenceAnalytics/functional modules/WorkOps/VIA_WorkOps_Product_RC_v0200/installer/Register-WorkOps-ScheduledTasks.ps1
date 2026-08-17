#requires -Version 7.0
[CmdletBinding()]
param(
    [string]$InstallRoot = "$env:LOCALAPPDATA\VeritasWorkOps",
    [string]$FollowupTime = "16:30",
    [string]$BackupTime = "19:00"
)
$ErrorActionPreference="Stop"
$AppRoot=Join-Path $InstallRoot "app"
$Python=Join-Path $InstallRoot "venv\Scripts\python.exe"
if(-not (Test-Path $Python)){throw "WorkOps venv not found: $Python"}
if(-not (Test-Path $AppRoot)){throw "WorkOps app not found: $AppRoot"}

$FollowScript=Join-Path $InstallRoot "Run-DailyFollowup.ps1"
@"
#requires -Version 7.0
Set-Location '$($AppRoot.Replace("'","''"))'
& '$($Python.Replace("'","''"))' 'engines\workops_followup_pack_builder.py' build --language zh-TW
& '$($Python.Replace("'","''"))' 'engines\workops_watchlist_prioritizer.py' build
"@ | Set-Content $FollowScript -Encoding UTF8

$BackupScript=Join-Path $InstallRoot "Run-DailyBackup.ps1"
@"
#requires -Version 7.0
Set-Location '$($AppRoot.Replace("'","''"))'
& '$($Python.Replace("'","''"))' 'engines\workops_backup_restore.py' backup
"@ | Set-Content $BackupScript -Encoding UTF8

function To-DateTime([string]$hhmm){
    $parts=$hhmm.Split(":")
    return (Get-Date).Date.AddHours([int]$parts[0]).AddMinutes([int]$parts[1])
}
$Pwsh=(Get-Command pwsh -ErrorAction Stop).Source
$A1=New-ScheduledTaskAction -Execute $Pwsh -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$FollowScript`""
$T1=New-ScheduledTaskTrigger -Daily -At (To-DateTime $FollowupTime)
$A2=New-ScheduledTaskAction -Execute $Pwsh -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$BackupScript`""
$T2=New-ScheduledTaskTrigger -Daily -At (To-DateTime $BackupTime)

Register-ScheduledTask -TaskName "VeritasWorkOps-DailyFollowup" -Action $A1 -Trigger $T1 -Description "Prepare WorkOps follow-up pack; does not send mail." -Force | Out-Null
Register-ScheduledTask -TaskName "VeritasWorkOps-DailyBackup" -Action $A2 -Trigger $T2 -Description "Create local WorkOps backup." -Force | Out-Null

Write-Host "def Scheduled tasks registered for current user context." -ForegroundColor Green
Write-Host "def Follow-up : $FollowupTime (draft preparation only)"
Write-Host "def Backup    : $BackupTime"
