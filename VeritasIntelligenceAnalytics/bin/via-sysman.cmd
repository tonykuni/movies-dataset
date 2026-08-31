@echo off
rem SYSTEM MANAGER 三輪全景協議(Mega-Prompt 最終整合版;20 加速器)— 動態解析最新版(鐵律)
rem 用法:via-sysman [--rounds N] [--no-open] [--json]   報告自動跳出、不關閉、不阻塞、不卡斷
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\CGC_MDL069_SystemManager_v0*.py"') do set "SM=%%f"
py "%~dp0..\supportive modules\registry\%SM%" %*
endlocal
