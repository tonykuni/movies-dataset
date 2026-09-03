@echo off
rem via-ui.cmd - UI 橋接系統管理器(批345;CGC_MDL126 尾版;spec+template → 整合總台;VHUIRE 品質閘)
rem 用法: via-ui                 產 VIA_UI_Consolidated 並跳出
rem       via-ui --spec          印參數冊 JSON     via-ui --data   印資料層 JSON
rem       via-ui --import-tokens X.html   抽任何頁的 CSS variables 進新版參數冊(只增)
rem       via-ui --selftest
setlocal
set "VIA=%~dp0VeritasIntelligenceAnalytics"
if not exist "%VIA%\supportive modules\registry" set "VIA=%~dp0"
set "PY=C:\Python313\python.exe"
if not exist "%PY%" set "PY=python"
for /f "delims=" %%f in ('dir /b /o:n "%VIA%\supportive modules\registry\CGC_MDL126_UIBridge_v0*.py" 2^>nul') do set "ENG=%%f"
if not defined ENG ( echo [via-ui] CGC_MDL126 缺 & exit /b 2 )
if "%~1"=="" ( "%PY%" "%VIA%\supportive modules\registry\%ENG%" build --open ) else ( "%PY%" "%VIA%\supportive modules\registry\%ENG%" %* )
exit /b %errorlevel%
