@echo off
rem via-loop.cmd - 生命週期 digest(批344;CGC_MDL125 尾版;零派工;貼輸出即可)
rem 用法: via-loop          印 digest(≤25 行)並寫 VIA_Reports\loop\DIGEST_latest.txt
rem       via-loop page     同時產 RACI 頁;  via-loop --open  產頁並跳出
setlocal
set "VIA=%~dp0VeritasIntelligenceAnalytics"
if not exist "%VIA%\supportive modules\registry" set "VIA=%~dp0"
set "PY=C:\Python313\python.exe"
if not exist "%PY%" set "PY=python"
for /f "delims=" %%f in ('dir /b /o:n "%VIA%\supportive modules\registry\CGC_MDL125_LifecycleRACI_v0*.py" 2^>nul') do set "ENG=%%f"
if not defined ENG ( echo [via-loop] CGC_MDL125 缺 & exit /b 2 )
"%PY%" "%VIA%\supportive modules\registry\%ENG%" %*
exit /b %errorlevel%
