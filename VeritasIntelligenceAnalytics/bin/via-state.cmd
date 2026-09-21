@echo off
rem =====================================================================
rem via-state.cmd - VIA 短指令 cmd 直通梭
rem =====================================================================
rem 背後:CGC_MDL169_VIAStateMatrix(批664 六域現況矩陣)。
rem   ENV/LIBS/SSOT/TOOLS/VDF/VRN 六域逐格;無參數=印矩陣,html=落頁。
rem   批673 補:這一面梭原本只有根目錄有,bin 沒有——打包就緒閘照出來的。
rem 梭因(批266 實錄):操作員殘常點 cmd,PS global 函式在 cmd 永不可見。
rem   每短指令配同名 .cmd:任何殼在本夾直打即通。**梭不得釘死版號**(CGC_MDL157)。
rem =====================================================================
setlocal
set "VIA=%~dp0..\"
set "VIA_NO_OPEN=1"
set "PSEXE=powershell"
where pwsh >nul 2>nul
if %errorlevel%==0 set "PSEXE=pwsh"
%PSEXE% -NoProfile -ExecutionPolicy Bypass -Command "$r=Get-ChildItem -LiteralPath '%VIA%.' -Filter 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1; . $r.FullName; & '%~n0'" %*
exit /b %errorlevel%
