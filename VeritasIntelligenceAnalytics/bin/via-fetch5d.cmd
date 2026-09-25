@echo off
rem 五日相關數據擷取(ENG049 批112):TA 冊宇宙+台股焦點 149 檔;同意閘+預檢+批抓 — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\via_py_celeritas_launcher_v0*.py"') do set "LC=%%f"
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VDF\engine\VDF_ENG049_FiveDayFetch*.py"') do set "F5=%%f"
py "%~dp0..\supportive modules\registry\%LC%" "%~dp0..\functional modules\VDF\engine\%F5%" %*
endlocal
