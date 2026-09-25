@echo off
rem =====================================================================
rem via-packgate.cmd - VIA 短指令 cmd 直通梭
rem =====================================================================
rem 背後:CGC_MDL174_PackagingGate(批673 三個專案打包就緒閘)。
rem   **能不能打包不是一句感覺**:七列各自量得出來,每列掛一個下一步。
rem   **GREEN 才算就緒**;NODATA/GATED 不是壞掉,但講成「好了」就是假綠。
rem   本閘零動作:不裝套件、不設同意閘、不改任何檔。html=落矩陣頁。
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
