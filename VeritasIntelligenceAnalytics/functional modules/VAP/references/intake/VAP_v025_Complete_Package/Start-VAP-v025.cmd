@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Invoke-VAP-v025.ps1"
if errorlevel 1 (
  echo.
  echo VAP v025 failed. Review the message above.
  pause
)
endlocal
