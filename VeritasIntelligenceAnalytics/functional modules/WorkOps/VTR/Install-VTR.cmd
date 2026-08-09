@echo off
rem VTR one-click installer launcher (double-click this file).
rem Runs Install-VTR.ps1 with the execution policy bypassed for THIS run only,
rem so a beginner never hits the "scripts are disabled" wall.
rem Prefers PowerShell 7 (pwsh) if present, otherwise Windows PowerShell 5.1.
chcp 65001 >nul
where pwsh >nul 2>nul
if %errorlevel%==0 (
  pwsh -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-VTR.ps1" %*
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-VTR.ps1" %*
)
echo.
echo ----------------------------------------------------------------
echo  Done. You can close this window.
echo ----------------------------------------------------------------
pause
