@echo off
rem =====================================================================
rem via-deploy.cmd - VIA 短指令 cmd 直通梭
rem =====================================================================
rem 背後:CGC_MDL175_AutoDeploy(批673 依現況佈署)。
rem   auto 可代跑;**裝套件與開同意閘永遠是操作員的手**,只印可貼的一行。
rem   現況全讀既有存證,不重新量;存證比樹舊就改排一步「先去量」。
rem   無參數=只印計畫(零動作);-Apply=跑 auto 那幾步,最後開 HTML U/I。
rem 梭因(批266 實錄):操作員殘常點 cmd,PS global 函式在 cmd 永不可見。
rem   每短指令配同名 .cmd:任何殼在本夾直打即通。**梭不得釘死版號**(CGC_MDL157)。
rem =====================================================================
setlocal
set "VIA=%~dp0"
set "VIA_NO_OPEN=1"
set "PSEXE=powershell"
where pwsh >nul 2>nul
if %errorlevel%==0 set "PSEXE=pwsh"
%PSEXE% -NoProfile -ExecutionPolicy Bypass -Command "$r=Get-ChildItem -LiteralPath '%VIA%.' -Filter 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1; . $r.FullName; & '%~n0'" %*
exit /b %errorlevel%
