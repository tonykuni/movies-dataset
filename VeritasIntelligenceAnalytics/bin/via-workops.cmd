@echo off
rem WorkOps × Mail Tracker 統合指揮板 v0104(一系統四頁:專案/追蹤哨/範疇關係人/VMT;負載對照;絕不代寄)
rem 用法:via-workops                    → 一支到底:掃描+對帳+編號+指揮板+週報
rem       via-workops drafts            → 自動佇列(≥3 天未回)一次建草稿
rem       via-workops drafts THR-…,…    → 只為「圈選件」建草稿(板上複製之指令)
rem       via-workops report | ui | Scan|Reconcile|Draft|FollowUp|Templates|All
if "%~1"=="" (
  for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\WorkOps\Invoke-VIA-WorkOps-CommandBoard-v0*.ps1"') do set "WOPS_BOARD=%%f"
  call pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\WorkOps\%%WOPS_BOARD%%"
) else if /i "%~1"=="drafts" (
  if "%~2"=="" (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\WorkOps\Invoke-VeritasMailOps.ps1" -Action FollowUp -RecipientsCsv "%~dp0..\functional modules\WorkOps\out\recipients_auto.csv"
  ) else (
    for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\WorkOps\Invoke-VIA-WorkOps-CommandBoard-v0*.ps1"') do set "WOPS_BOARD=%%f"
    call pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\WorkOps\%%WOPS_BOARD%%" -DraftsFor "%~2"
  )
) else if /i "%~1"=="report" (
  start "" "%~dp0..\VIA_Reports\workops_run\VIA_WorkOps_WeeklyReport.html"
) else if /i "%~1"=="ui" (
  for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\WorkOps\Veritas_MailOps_Standalone*.html"') do set "WOPS_UI=%%f"
  call start "" "%~dp0..\functional modules\WorkOps\%%WOPS_UI%%"
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\WorkOps\Invoke-VeritasMailOps.ps1" -Action %1
)
