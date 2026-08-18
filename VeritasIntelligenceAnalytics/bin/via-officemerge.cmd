@echo off
rem Office(xlsx/csv)併主表橋:SuperDocExtractor 擷取(合併格/參差列/編碼修復)→MDL004/005(dry-run 預設;--commit 寫;冪等+備份)— 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VRN\VRN_ENG055_OfficeMerge_v0*.py"') do set "OM=%%f"
py "%~dp0..\functional modules\VRN\%OM%" %*
endlocal
