@echo off
rem =====================================================================
rem via-panorama-run.cmd - 全景修復啟動器(launchers\Invoke-VIA-Panorama-v*.ps1;別名 全景啟動)
rem 批649:via-panorama 在 批511 之後被同名後定義(MDL158)吃掉,啟動器從冊上失聯。
rem -Months 2 -StationTimeout 600 -FetchTimeout 7200 -BatchSize 20 [-Fetch] [-ReadOnly]
rem =====================================================================
rem 梭因(批261):操作員殘常點 cmd,PS global 函式在 cmd 永不可見。
rem 治本=每短指令配同名 .cmd。**梭不得釘死版號**(CGC_MDL157 檢②)。
rem =====================================================================
setlocal
set "VIA=%~dp0"
set "VIA_NO_OPEN=1"
set "PSEXE=powershell"
where pwsh >nul 2>nul
if %errorlevel%==0 set "PSEXE=pwsh"
%PSEXE% -NoProfile -ExecutionPolicy Bypass -Command "$r=Get-ChildItem -LiteralPath '%VIA%.' -Filter 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1; . $r.FullName; & '%~n0'" %*
exit /b %errorlevel%
