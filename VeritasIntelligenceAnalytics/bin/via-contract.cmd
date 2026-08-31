@echo off
rem 契約介面引擎 v0200(跨會話導入:SSOT Registry/URN/DAG/Watchdog/Digital Twin;demo=全鏈示範)— 動態解析最新版目錄(鐵律)
setlocal
for /f "delims=" %%d in ('dir /b /ad /o:n "%~dp0..\supportive modules\VIA_ContractEngine_v0*"') do set "CE=%%d"
set "PYTHONPATH=%~dp0..\supportive modules\%CE%\src"
py -m via_interface_engine %*
endlocal
