@echo off
rem VDF DataHub 心跳/就緒閘 — 動態解析最新版(鐵律:嚴禁寫死版號)
rem 用法:via-datahub [--data-root D] [--run-root D] [--core-root D] [--output F] [--supportive-timeout N] [--skip-supportive]
rem 無參數時使用 DEFAULT:data-root=VDF\db · 輸出 _via_datahub_output\heartbeat.json
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VDF\VDF_DataHub_Orchestrator*.py"') do set "DH=%%f"
set "ARGS=%*"
if "%ARGS%"=="" set ARGS=--data-root "%~dp0..\functional modules\VDF\db" --run-root "%USERPROFILE%\movies-dataset\_via_datahub_output" --core-root "%~dp0..\supportive modules" --output "%USERPROFILE%\movies-dataset\_via_datahub_output\heartbeat.json"
py "%~dp0..\functional modules\VDF\%DH%" %ARGS%
endlocal
