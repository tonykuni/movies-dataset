@echo off
rem OCR 擷取 x SSOT v2 內容級對帳(唯讀零落庫)— 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VRN\vrn_content_reconcile_v0*.py"') do set "RC=%%f"
py "%~dp0..\functional modules\VRN\%RC%" %*
endlocal
