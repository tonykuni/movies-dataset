@echo off
rem WorkOps 指揮板 v0102(自動編號 side-car:WOP/THR;Outlook 原件絕不動;+一鍵週報)
rem 用法:via-workops          → 一支到底:唯讀掃描+對帳+編號+三頁指揮板+週報(動態最新版)
rem       via-workops drafts  → 依預填 recipients_auto.csv 一次產生追蹤草稿(只建草稿,絕不代寄)
rem       via-workops report  → 開最近一次週報
rem       via-workops ui      → 靜態儀表板;其餘動作透傳 v001 引擎
if "%~1"=="" (
  for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\WorkOps\Invoke-VIA-WorkOps-CommandBoard-v0*.ps1"') do set "WOPS_BOARD=%%f"
  call pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\WorkOps\%%WOPS_BOARD%%"
) else if /i "%~1"=="drafts" (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\WorkOps\Invoke-VeritasMailOps.ps1" -Action FollowUp -RecipientsCsv "%~dp0..\functional modules\WorkOps\out\recipients_auto.csv"
) else if /i "%~1"=="report" (
  start "" "%~dp0..\VIA_Reports\workops_run\VIA_WorkOps_WeeklyReport.html"
) else if /i "%~1"=="ui" (
  for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\WorkOps\Veritas_MailOps_Standalone*.html"') do set "WOPS_UI=%%f"
  call start "" "%~dp0..\functional modules\WorkOps\%%WOPS_UI%%"
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\WorkOps\Invoke-VeritasMailOps.ps1" -Action %1
)
