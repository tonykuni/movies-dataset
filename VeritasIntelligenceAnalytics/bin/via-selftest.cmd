@echo off
rem 全面自測矩陣(全站安全模式:唯讀/dry-run/selftest;誠實 OK/FAIL/SKIP 三態)— 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\CGC_MDL064_SelftestGrid_v0*.py"') do set "SG=%%f"
py "%~dp0..\supportive modules\registry\%SG%" %*
endlocal
