@echo off
rem 對帳綠燈內容落庫 via.duckdb(dry-run 預設;--commit 才寫;現表零觸碰)— 動態解析最新版(鐵律)
rem 用法:via-store [--db 路徑]        → 只出計畫
rem       via-store --commit [--db 路徑] → 備份後落庫三新表+稽核
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VRN\vrn_content_store_v0*.py"') do set "ST=%%f"
py "%~dp0..\functional modules\VRN\%ST%" %*
endlocal
