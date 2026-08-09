@echo off
rem VTR everyday launcher (double-click this file for a full check).
rem Pass-through arguments work too, e.g. from a terminal:
rem   Run-VTR.cmd -Action Restore -Path .\input\
rem   Run-VTR.cmd -Action Inspect -DocId MTG-001 -ShowReview
chcp 65001 >nul
where pwsh >nul 2>nul
if %errorlevel%==0 (
  pwsh -NoProfile -ExecutionPolicy Bypass -File "%~dp0Invoke-VTR.ps1" %*
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Invoke-VTR.ps1" %*
)
echo.
pause
