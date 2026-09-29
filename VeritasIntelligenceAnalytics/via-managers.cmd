@echo off
rem =====================================================================
rem via-managers.cmd - VIA 短指令 cmd 直通梭(R33:命令冊沿 dot-source 鏈讀後,CGC_MDL157 v0106 量到此指令缺梭)
rem =====================================================================
rem 梭因(批266 實錄):操作員殼常為 cmd,PS global 函式在 cmd 永不可見。
rem   每短指令配同名 .cmd:任何殼在本夾直打即通。**梭不得釘死版號**(CGC_MDL157)。
rem 機制:pwsh 優先(缺退 powershell)-> 點源 Register 尾版 -> 呼同名函式 via-managers。
rem =====================================================================
setlocal
set "VIA=%~dp0"
set "VIA_NO_OPEN=1"
set "PSEXE=powershell"
where pwsh >nul 2>nul
if %errorlevel%==0 set "PSEXE=pwsh"
%PSEXE% -NoProfile -ExecutionPolicy Bypass -Command "$r=Get-ChildItem -LiteralPath '%VIA%.' -Filter 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1; . $r.FullName; & '%~n0'" %*
exit /b %errorlevel%
