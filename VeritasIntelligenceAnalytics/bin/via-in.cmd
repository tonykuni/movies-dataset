@echo off
rem =====================================================================
rem via-in.cmd - VIA 短指令 cmd 直通梭
rem =====================================================================
rem 背後:命令冊尾版的 via-in = via-entry + via-vcgc enter(側線 2026-09-29 g;VCGC v0173 入口流程一句完成)。
rem   --card(只出卡不啟動)/ --no-pull(不更新)/ 其餘參數照傳給 go。
rem   cmd 殼的目前資料夾不會跟著進倉(子行程改不了父殼);PowerShell 殼直接打 via-in 會真的進到 $VIA。
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
