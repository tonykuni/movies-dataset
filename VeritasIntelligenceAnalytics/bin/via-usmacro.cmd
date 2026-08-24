@echo off
rem 美國經濟細目擷取引擎(ENG047 批109):--list 冊盤點 / --fetch 實抓(法遵雙閘 VIA_NET_CONSENT+FRED_API_KEY)/ --selftest — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\via_py_celeritas_launcher_v0*.py"') do set "LC=%%f"
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VDF\engine\VDF_ENG047_USMacroDetailFetcher*.py"') do set "UM=%%f"
py "%~dp0..\supportive modules\registry\%LC%" "%~dp0..\functional modules\VDF\engine\%UM%" %*
endlocal
