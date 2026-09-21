@echo off
rem =====================================================================
rem via-vrnrun.cmd - VIA 短指令 cmd 直通梭
rem =====================================================================
rem 背後:Invoke-VIA-VRN-v*.ps1(批677 一支跑完 VRN 一輪實測)。
rem   五步照順序:冊重建 → 六層鏈 → 庫價重算 → 驗真矩陣 → 標準 HTML U/I。
rem   開頭先印本窗對著哪一棵樹(批397 雙副本律);**不裝套件、不設同意閘**。
rem   -NoOpen 不跳頁;-Quick 快掃。
rem 梭因(批266 實錄):操作員殘常點 cmd,PS global 函式在 cmd 永不可見。
rem   每短指令配同名 .cmd:任何殼在本夾直打即通。**梭不得釘死版號**(CGC_MDL157)。
rem =====================================================================
setlocal
set "VIA=%~dp0..\"
set "PSEXE=powershell"
where pwsh >nul 2>nul
if %errorlevel%==0 set "PSEXE=pwsh"
%PSEXE% -NoProfile -ExecutionPolicy Bypass -Command "$r=Get-ChildItem -LiteralPath '%VIA%.' -Filter 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1; . $r.FullName; & '%~n0'" %*
exit /b %errorlevel%
