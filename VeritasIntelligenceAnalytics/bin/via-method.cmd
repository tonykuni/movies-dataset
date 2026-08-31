@echo off
rem VRN 方法核(TOOL-071):def01-20 方法冊可執行函式庫+五引擎符合度稽核+十二檢 — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VRN\vrn_method_kernel_v0*.py"') do set "MK=%%f"
py "%~dp0..\functional modules\VRN\%MK%" %*
endlocal
