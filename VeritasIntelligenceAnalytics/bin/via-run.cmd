@echo off
rem 指令留痕包裝器(操作員令:錯誤中斷前紀錄必留 LOGS):逐行先落檔再上螢幕;Ctrl+C/崩潰不失紀錄 — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\CGC_MDL044_Cmdlog_v0*.py"') do set "CL=%%f"
py "%~dp0..\supportive modules\registry\%CL%" %*
endlocal
