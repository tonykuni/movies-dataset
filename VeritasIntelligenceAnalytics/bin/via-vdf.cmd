@echo off
rem v0160C 一般瀏覽器 HTML U/I(本機 HTTP 橋) · 回退: v0102=HTA 設計鎖刊頭 / v0101=v0160A 原版
rem 鐵律清掃(L6 債冊):寫死版號改 dir /b /o:n 動態解析,最新版自動接任
if /i "%~1"=="contract" (
  rem MDL501 取數契約增減:contract check=驗證盤點 | list [域] | diff 檔 | add 域 CODE 名 源 fetcher 頻 欄,欄 客,客 [狀態] | remove CODE | setstatus CODE 狀態
  for /f "tokens=1* delims= " %%a in ("%*") do py "%~dp0..\functional modules\VDF\VDF_MDL501_FetchContractManager.py" %%b
) else (
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VDF\Start-VIA-VDF-v0*.ps1"') do set "EG=%%f"
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\VDF\%EG%" %*
endlocal
)
