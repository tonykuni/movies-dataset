@echo off
rem py 加速啟動器(TOOL-091):Celeritas 常駐後執行目標腳本(操作員令:py 一律過加速器)— 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\via_py_celeritas_launcher_v0*.py"') do set "VP=%%f"
py "%~dp0..\supportive modules\registry\%VP%" %*
endlocal
