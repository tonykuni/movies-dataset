@echo off
rem VRN 內容級擷取 v0101 ACTIVE(啟用交易 2026-08-05):dry-run 預設;--commit 落地 append-only store;回退=改指 candidate
rem 鐵律清掃(L6 債冊):寫死版號改 dir /b /o:n 動態解析,最新版自動接任
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VRN\VRN_ENG047_ContentExtract_v0*.py"') do set "EG=%%f"
py "%~dp0..\functional modules\VRN\%EG%" %*
endlocal
