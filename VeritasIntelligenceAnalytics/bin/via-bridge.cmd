@echo off
rem Command Bridge v0100:一鍵前後端對接(後端 B1-B5 探測 + test/debug 三輪 + 多 TAB 狀態矩陣首頁 UI;run-local)
rem 鐵律清掃(L6 債冊):寫死版號改 dir /b /o:n 動態解析,最新版自動接任
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\Invoke-VIA-Bridge-v0*.ps1"') do set "EG=%%f"
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\%EG%" %*
endlocal
