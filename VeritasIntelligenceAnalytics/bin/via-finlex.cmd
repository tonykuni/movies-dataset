@echo off
rem 財務三字庫收割引擎(TOOL-072):broker dict+財務數據中英同義+財務報表同義(--build/--ask/--selftest)— 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VRN\vrn_finlex_v0*.py"') do set "FL=%%f"
py "%~dp0..\functional modules\VRN\%FL%" %*
endlocal
