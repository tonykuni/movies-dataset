@echo off
rem DOCX 產物併主表(補齊令:docx_struct→MDL005/004;dry-run 預設;--commit 才寫;冪等+備份)— 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VRN\VRN_ENG053_DocxMerge_v0*.py"') do set "DM=%%f"
py "%~dp0..\functional modules\VRN\%DM%" %*
endlocal
