@echo off
REM ============================================================
REM  VIA_Forge 一鍵啟動（雙擊本檔）
REM  自動以 ExecutionPolicy Bypass 執行 Start-VIA.ps1
REM  找 Python -> 建 .venv -> 裝依賴 -> 樞自我測試 -> 起 server -> 開 HTML U/I
REM ============================================================
setlocal
cd /d "%~dp0"

where pwsh >nul 2>nul
if %errorlevel%==0 (
    pwsh -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-VIA.ps1" %*
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Start-VIA.ps1" %*
)

echo.
echo (visual kept; press any key to close)
pause >nul
