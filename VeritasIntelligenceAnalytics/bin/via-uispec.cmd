@echo off
rem UI 元件三語轉碼系統管理器(HTML→spec→py/js/ps1 驗同登冊+移植旁建)— 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\CGC_MDL107_UISpecManager_v0*.py"') do set "UM=%%f"
py "%~dp0..\supportive modules\registry\%UM%" %*
endlocal
