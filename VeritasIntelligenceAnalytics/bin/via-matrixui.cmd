@echo off
rem 三大 Matrix HTML U/I(TOOL-067):VRN 驗證矩陣/VDF 運作摘要/族群+量價指標 — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\CGC_MDL079_MatrixConsole_v0*.py"') do set "MX=%%f"
py "%~dp0..\supportive modules\registry\%MX%" %*
endlocal
