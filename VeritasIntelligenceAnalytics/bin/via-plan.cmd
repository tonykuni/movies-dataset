@echo off
rem 環境暨安裝計畫引擎(先計畫先實測零風險:快照+分段計畫+pip --dry-run 可行性實測;GREEN 段才給執行令)— 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\CGC_MDL049_EnvPlan_v0*.py"') do set "EP=%%f"
py "%~dp0..\supportive modules\registry\%EP%" %*
endlocal
