@echo off
rem =====================================================================
rem via-ssotregex.cmd - SSOT REGEX 字典(CGC_MDL115_SSOTRegexDict;別名 正則字典)
rem 批649:這支引擎樹上一直在,冊上卻從 批535 起失聯——via-ssot 被同名後定義吃掉,
rem 前者(MDL115)無聲消失,後者指 MDL155。操作員一再點名「優先 SSOT REGEX」的,正是這一支。
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
