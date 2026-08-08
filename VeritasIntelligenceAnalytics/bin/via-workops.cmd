@echo off
rem WorkOps 指揮板 v0100(產品裁決重造:專案指揮+追蹤哨,控管表自動吃入,人不開 Excel)
rem 用法:via-workops         → 一支到底:唯讀掃描+對帳+指揮板(動態最新版)
rem       via-workops ui     → 只開靜態儀表板(最新版,不掃描)
rem       via-workops Scan|Reconcile|Draft|FollowUp|Templates|All → v001 引擎非互動面
if "%~1"=="" (
  for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\WorkOps\Invoke-VIA-WorkOps-CommandBoard-v0*.ps1"') do set "WOPS_BOARD=%%f"
  call pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\WorkOps\%%WOPS_BOARD%%"
) else if /i "%~1"=="ui" (
  for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\WorkOps\Veritas_MailOps_Standalone*.html"') do set "WOPS_UI=%%f"
  call start "" "%~dp0..\functional modules\WorkOps\%%WOPS_UI%%"
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\WorkOps\Invoke-VeritasMailOps.ps1" -Action %1
)
