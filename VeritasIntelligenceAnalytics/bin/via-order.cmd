@echo off
rem 擷取單接單引擎(ENG050 批114):--order NNN 雙車道(TWSE 官方籌碼線+yfinance 國際線)5 交易日回溯 — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\via_py_celeritas_launcher_v0*.py"') do set "LC=%%f"
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VDF\engine\VDF_ENG050_OrderFetch*.py"') do set "OF=%%f"
py "%~dp0..\supportive modules\registry\%LC%" "%~dp0..\functional modules\VDF\engine\%OF%" %*
endlocal
