@echo off
rem TA-Lib 全指標工廠(ENG048 批110):Adj 優先/前值補洞/台灣 T+1/週期 5·10·20·60·120·240/rf 與基準可換 — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\via_py_celeritas_launcher_v0*.py"') do set "LC=%%f"
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VDF\engine\VDF_ENG048_TAFactory*.py"') do set "TA=%%f"
py "%~dp0..\supportive modules\registry\%LC%" "%~dp0..\functional modules\VDF\engine\%TA%" %*
endlocal
