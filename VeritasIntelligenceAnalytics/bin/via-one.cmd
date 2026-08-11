@echo off
rem 全系統總啟動器 v0112:十四階段(WORKOPS=指揮板一支到底)或 -Only <鍵>
rem 鐵律清掃(L6 債冊):寫死版號改 dir /b /o:n 動態解析,最新版自動接任
rem rollback: pwsh ... -File "%~dp0..\Invoke-VIA-One-v0112.ps1"
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\Invoke-VIA-One-v0*.ps1"') do set "EG=%%f"
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\%EG%" %*
endlocal
