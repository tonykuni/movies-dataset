@echo off
rem =====================================================================
rem via-vrnchain.cmd - VIA 短指令 cmd 直通梭
rem =====================================================================
rem 背後:CGC_MDL172_VRNChainRunner(批671 VRN 六層鏈實測)。
rem   鏈表不寫死:讀批665 已覆核的六層冊(44 節點),冊就是鏈——冊改了鏈跟著改。
rem   **層間依序、層內並行**;逾時記 NODATA 不記 RED;同意閘永不代設。
rem   無參數=plan;run=一句到底(逐層跑 + rich HTML MATRIX + 跳頁);--selftest 十九檢。
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
