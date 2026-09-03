@echo off
rem via-charter.cmd - 系統結構總冊(批343;CGC_MDL124 尾版;python 直呼;零 server)
rem 用法: via-charter            產頁+自動跳出 (file://)
rem       via-charter --probe    兩日試鏈計畫(不派工);加 --go 才派工
rem       via-charter --selftest
setlocal
set "VIA=%~dp0VeritasIntelligenceAnalytics"
if not exist "%VIA%\supportive modules\registry" set "VIA=%~dp0"
set "PY=C:\Python313\python.exe"
if not exist "%PY%" set "PY=python"
for /f "delims=" %%f in ('dir /b /o:n "%VIA%\supportive modules\registry\CGC_MDL124_SystemCharter_v0*.py" 2^>nul') do set "ENG=%%f"
if not defined ENG ( echo [via-charter] CGC_MDL124 缺 & exit /b 2 )
if "%~1"=="" ( "%PY%" "%VIA%\supportive modules\registry\%ENG%" --open ) else ( "%PY%" "%VIA%\supportive modules\registry\%ENG%" %* )
exit /b %errorlevel%
