@echo off
rem TickerRegex v0100 shimmed entry: via-shim -Target <file> [-DryRun] [-Args ...]
rem 鐵律清掃(L6 債冊):寫死版號改 dir /b /o:n 動態解析,最新版自動接任
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VRN\Invoke-VRN-Shimmed-Entry-v0*.ps1"') do set "EG=%%f"
pwsh -NoProfile -File "%~dp0..\functional modules\VRN\%EG%" %*
endlocal
