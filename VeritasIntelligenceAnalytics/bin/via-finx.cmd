@echo off
rem 財報頁年度分析擷取器(TOOL-082):四板塊年度表格(三大報表/比率/每股/評價)+finaudit 閉環 — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VRN\vrn_fin_extract_v0*.py"') do set "FX=%%f"
py "%~dp0..\functional modules\VRN\%FX%" %*
endlocal
