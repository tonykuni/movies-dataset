@echo off
rem =====================================================================
rem via-six.cmd - VIA 短指令 cmd 直通梭(批342;VIA-Verb-Shim v0100)
rem 六流程零九頭龍派工: CGC_MDL123_SixStreams 尾版(python 直呼;零 server)
rem 用法: via-six            dry-run 九子行程並行 + 矩陣自動跳出
rem       via-six --go       僅放行 S1 修復(其餘流程本就唯讀)
rem       via-six --no-open  不跳出
rem =====================================================================
setlocal
set "VIA=%~dp0VeritasIntelligenceAnalytics"
if not exist "%VIA%\supportive modules\registry" set "VIA=%~dp0"
set "PY=C:\Python313\python.exe"
if not exist "%PY%" set "PY=python"
for /f "delims=" %%f in ('dir /b /o:n "%VIA%\supportive modules\registry\CGC_MDL123_SixStreams_v0*.py" 2^>nul') do set "ENG=%%f"
if not defined ENG ( echo [via-six] CGC_MDL123_SixStreams 缺 ^(先放入 registry^) & exit /b 2 )
"%PY%" "%VIA%\supportive modules\registry\%ENG%" run %*
exit /b %errorlevel%
