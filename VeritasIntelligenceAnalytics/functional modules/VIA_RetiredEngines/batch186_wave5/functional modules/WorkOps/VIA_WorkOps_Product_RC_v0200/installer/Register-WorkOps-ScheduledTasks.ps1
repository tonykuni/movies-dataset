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
& '$($Python.Replace("'","''"))' 'engines\VIA_ENG142_WorkopsWatchlistPrioritizer.py' build
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

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
