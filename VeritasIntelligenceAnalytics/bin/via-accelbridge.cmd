@echo off
rem 全引擎加速器橋:AST 定位(docstring+__future__ 後)插 SuperAccel graceful 橋塊;逐檔 parse=0 閘;冪等 — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\CGC_MDL074_AccelBridge_v0*.py"') do set "AB=%%f"
py "%~dp0..\supportive modules\registry\%AB%" %*
endlocal
