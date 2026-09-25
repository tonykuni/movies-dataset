@echo off
rem 主動式台股 ETF 每日持股引擎(ENG051 批118):動態宇宙(冊鏈)→投信官方/MoneyDJ 後備→DuckDB+Parquet 冪等→持股增減偵測 — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\via_py_celeritas_launcher_v0*.py"') do set "LC=%%f"
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VDF\engine\VDF_ENG051_ActiveTWETF_Holdings*.py"') do set "EH=%%f"
py "%~dp0..\supportive modules\registry\%LC%" "%~dp0..\functional modules\VDF\engine\%EH%" %*
endlocal
