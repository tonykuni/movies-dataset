@echo off
rem =====================================================================
rem via-vrnfin.cmd - VIA 短指令 cmd 直通梭
rem =====================================================================
rem 背後:VRN_ENG090_FinStatementsTemplate_v*.py(側線 2026-09-25 第十六段;掉球 Z212 交易所財報 VRN 模板頁)。
rem   status(預設;只讀)/ run(重產頁,只落 VIA_Reports)/ check / --selftest(二十三檢)。
rem   零網路、唯讀庫;尾版不在冊上函式印 ABSENT rc2。
rem 梭因(批266 實錄):操作員殼常為 cmd,PS global 函式在 cmd 永不可見。
rem   每短指令配同名 .cmd:任何殼在本夾直打即通。**梭不得釘死版號**(CGC_MDL157)。
rem =====================================================================
setlocal
set "VIA=%~dp0..\"
set "PSEXE=powershell"
where pwsh >nul 2>nul
if %errorlevel%==0 set "PSEXE=pwsh"
%PSEXE% -NoProfile -ExecutionPolicy Bypass -Command "$r=Get-ChildItem -LiteralPath '%VIA%.' -Filter 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1; . $r.FullName; & '%~n0'" %*
exit /b %errorlevel%
