@echo off
chcp 65001 >nul
cd /d "%~dp0"

rem ==== Veritas MailOps · One-Script Compliance Edition — 一鍵啟動 ====
rem 只讀掃描 / 對帳建議 / 追蹤信草稿(不自動寄、不自動寫回控管表)

set "PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
where pwsh >nul 2>&1 && set "PS=pwsh.exe"

set "SCRIPT=%~dp0Invoke-VeritasMailOps.ps1"
if not exist "%SCRIPT%" (
  echo 找不到 Invoke-VeritasMailOps.ps1(請與本 .cmd 放在同一資料夾)。
  pause
  goto :eof
)

"%PS%" -NoProfile -ExecutionPolicy Bypass -STA -File "%SCRIPT%" -Action Menu
pause
