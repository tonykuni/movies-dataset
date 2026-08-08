@echo off
rem WorkOps v002(Workbench 視覺鎖前送):無參數=開最新版 MailOps 儀表板(動態解析);帶參數=透傳引擎非互動面
rem 用法:via-workops | via-workops Scan|Reconcile|Draft|FollowUp|Templates|All
if "%~1"=="" (
  for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\WorkOps\Veritas_MailOps_Standalone*.html"') do set "WOPS_UI=%%f"
  call start "" "%~dp0..\functional modules\WorkOps\%%WOPS_UI%%"
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\WorkOps\Invoke-VeritasMailOps.ps1" -Action %1
)
