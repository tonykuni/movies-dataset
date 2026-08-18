@echo off
rem VIA Central Governance Console(TOOL-063):三輪全景式分析+SSOT/Regex 治理中心+HTML Matrix(四分區/紅黃綠燈)— 動態解析最新版(鐵律)
setlocal
if /i "%~1"=="--ps" ( pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\supportive modules\registry\Invoke-VIA-CentralGov-v0100.ps1" & goto :eof )
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\via_central_gov_v0*.py"') do set "GV=%%f"
py "%~dp0..\supportive modules\registry\%GV%" %*
endlocal
