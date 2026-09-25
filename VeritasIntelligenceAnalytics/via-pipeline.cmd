@echo off
rem =====================================================================
rem via-pipeline.cmd - 族群分類一鍵管線 cmd 直通梭(批316;VIA-Verb-Shim v0100)
rem =====================================================================
rem 任何殼於本夾直打 via-pipeline 即通:補齊資料→分類引擎 ENG070 自測+run
rem →回測引擎 ENG071 自測+run→開兩頁(參數直通:-SkipSync -SkipFill -NoOpen)。
rem 機制:pwsh 優先(缺退 powershell)->跑 Invoke-VIA-GroupPipeline 尾版。
rem =====================================================================
setlocal
set "VIA=%~dp0"
set "PSEXE=powershell"
where pwsh >nul 2>nul
if %errorlevel%==0 set "PSEXE=pwsh"
for /f "delims=" %%f in ('dir /b /o:n "%VIA%Invoke-VIA-GroupPipeline-v*.ps1"') do set "PS1=%VIA%%%f"
if not defined PS1 (
    echo [via-pipeline] FAIL: Invoke-VIA-GroupPipeline-v*.ps1 缺
    exit /b 2
)
%PSEXE% -NoProfile -ExecutionPolicy Bypass -File "%PS1%" %*
exit /b %errorlevel%
