@echo off
REM ============================================================================
REM  governance.bat  --  VIA 治理式 Prompt 導入 (雙擊即跑，靜態驗證)
REM  雙擊後輸入要導入的 Prompt，經三個 PowerShell 入口做靜態治理驗證，
REM  產出 Registry / SSOT overlay / RYG 全景矩陣，最後開報告。
REM  絕不 import/執行未驗證目標、不安裝、不碰網路、不改 canonical。
REM ============================================================================
setlocal
cd /d "%~dp0"

set /p PROMPT=請輸入要導入的 Prompt (直接 Enter 用預設測試字串): 
if "%PROMPT%"=="" set PROMPT=VIA 支援核心治理測試 prompt

where pwsh >nul 2>nul
if %errorlevel%==0 (
    pwsh -NoProfile -ExecutionPolicy Bypass -File "%~dp0Invoke-VIA-SupportiveCore-PromptInjection.ps1" -PromptSource "%PROMPT%" -OpenReport
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Invoke-VIA-SupportiveCore-PromptInjection.ps1" -PromptSource "%PROMPT%" -OpenReport
)

echo.
echo (完成。報告已開啟。此視窗可關閉。)
pause
endlocal
