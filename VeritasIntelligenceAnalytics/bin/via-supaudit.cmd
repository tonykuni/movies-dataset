@echo off
rem 功能引擎 x 支援模組導入稽核(唯讀)— 動態解析最新版(鐵律:嚴禁寫死版號)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\via_support_import_audit_v0*.py"') do set "SA=%%f"
py "%~dp0..\supportive modules\registry\%SA%" %*
endlocal
