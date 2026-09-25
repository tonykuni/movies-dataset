@echo off
rem 財務驗算稽核器(TOOL-078):估值 ADJ CLOSE 基/三表勾稽/比率含週轉/每股+加減除驗算歷歷對照 — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VRN\vrn_finaudit_v0*.py"') do set "FA=%%f"
py "%~dp0..\functional modules\VRN\%FA%" %*
endlocal
