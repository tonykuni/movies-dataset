@echo off
rem EnvFix v0102:已就緒不動+check差分;-RepairBase 補 base 存量缺件(wheel限定;-IncludeHeavy 連 torch 家族);回退=改指 v0101
rem 鐵律清掃(L6 債冊):寫死版號改 dir /b /o:n 動態解析,最新版自動接任
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\Invoke-VIA-EnvFix-v0*.ps1"') do set "EG=%%f"
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\%EG%" %*
endlocal
