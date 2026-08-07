@echo off
rem WorkOps v001(session 0198nFZz 整合):無參數=開啟智慧工作台 U/I(不卡斷);帶參數=透傳 MailOps 引擎
rem 用法:via-workops                            → 開 VIA_WorkOps_Intelligence_Workbench_v0100.html
rem       via-workops Scan|Reconcile|Draft|FollowUp|Templates|All  → Invoke-VeritasMailOps.ps1 -Action <動作>(非互動)
if "%~1"=="" (
  start "" "%~dp0..\functional modules\WorkOps\VIA_WorkOps_Intelligence_Workbench_v0100.html"
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\WorkOps\Invoke-VeritasMailOps.ps1" -Action %1
)
