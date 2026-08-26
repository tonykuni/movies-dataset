@echo off
setlocal
where pwsh >nul 2>nul
if errorlevel 1 (
  echo PowerShell 7 ^(pwsh^) is required.
  echo Install PowerShell 7, then run this installer again.
  exit /b 1
)
pwsh -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-VeritasWorkOps.ps1"
endlocal
