@echo off
rem VDF 整合輸入介面清單矩陣(TOOL-093):--show/--add-item/--remove-item/--add-ticker/--remove-ticker/--restore/--set-tw/--set-vrn — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VDF\vdf_input_matrix_v0*.py"') do set "VI=%%f"
py "%~dp0..\supportive modules\registry\via_py_celeritas_launcher_v0100.py" "%~dp0..\functional modules\VDF\%VI%" %*
endlocal
