@echo off
rem =====================================================================
rem via-projects.cmd - VIA 短指令 cmd 直通梭(批368;VIA-Verb-Shim v0100)
rem =====================================================================
rem 根因(批266 實錄):操作員殼常為 cmd,PS global 函式在 cmd 永不可見
rem ('not recognized as internal or external command' 即 cmd 簽名句)
rem =批261 雙殼陷阱續章。治本=每短指令配同名 .cmd:任何殼於本夾直打
rem 即通(cmd 找 .cmd;PowerShell 內函式優先=零衝突)。
rem 機制:pwsh 優先(缺退 powershell)->點源 Register 尾版->呼同名函式。
rem =====================================================================
setlocal
set "VIA=%~dp0"
set "PSEXE=powershell"
where pwsh >nul 2>nul
if %errorlevel%==0 set "PSEXE=pwsh"
%PSEXE% -NoProfile -ExecutionPolicy Bypass -Command "$r=Get-ChildItem -LiteralPath '%VIA%.' -Filter 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1; . $r.FullName; & '%~n0'" %*
exit /b %errorlevel%
