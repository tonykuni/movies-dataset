@echo off
rem 舊根對帳掃描器(TOOL-086):舊 VIA 樹 vs 現役倉四態判決(SAME/MOVED 讓位;DIFF 候鏡像;MISSING 遺漏候收容)— 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\via_oldroot_scan_v0*.py"') do set "OS=%%f"
py "%~dp0..\supportive modules\registry\%OS%" %*
endlocal
