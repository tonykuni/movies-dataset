@echo off
rem =====================================================================
rem via-matrixspec.cmd - VIA 短指令 cmd 直通梭
rem =====================================================================
rem 背後:CGC_MDL173_MatrixReportSpec(批672 矩陣式報告排版規格)。
rem   **它是排版,不是引擎**:不產生新資料、不判燈、不碰庫。
rem   一份規格四支共用(MDL169/170/171/172);要改字級只改這裡一個數字。
rem   無參數=印規格;demo=落示範頁;--selftest 二十檢。
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
