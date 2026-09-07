@echo off
REM 從「命令提示字元」轉進 PowerShell 7。不要在 cmd 貼 $ 變數。
where pwsh >nul 2>&1
if %ERRORLEVEL%==0 (
  pwsh -NoProfile -NoExit -File "%~dp0VIA-Activate.ps1"
  goto :eof
)
echo RED  找不到 pwsh。請開 PowerShell 7 視窗後貼 VIA-Activate.ps1 全文。
powershell -NoProfile -NoExit -File "%~dp0VIA-Activate.ps1"
