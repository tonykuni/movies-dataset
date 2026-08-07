@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

set "PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
where pwsh >nul 2>&1 && set "PS=pwsh.exe"

echo ============================================================
echo  Veritas MailOps - Tracking Draft Templates
echo  Creates Outlook DRAFTS for your review. Never auto-sends.
echo ============================================================
echo.

"%PS%" -NoProfile -ExecutionPolicy Bypass -STA -File "%~dp0Invoke-VeritasMailOps-TrackingDrafts.ps1" %*

echo.
pause
endlocal
