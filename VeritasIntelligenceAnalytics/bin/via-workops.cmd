@echo off
rem WorkOps v001(session 0198nFZz 整合;UI 更正:原誤植之 Workbench 實為 VIA_Forge UI,改用 MailOps 儀表板)
rem 用法:via-workops                            → 開 Veritas_MailOps_Standalone.html(不卡斷)
rem       via-workops Scan|Reconcile|Draft|FollowUp|Templates|All  → Invoke-VeritasMailOps.ps1 -Action <動作>(非互動)
if "%~1"=="" (
  start "" "%~dp0..\functional modules\WorkOps\Veritas_MailOps_Standalone.html"
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\WorkOps\Invoke-VeritasMailOps.ps1" -Action %1
)
