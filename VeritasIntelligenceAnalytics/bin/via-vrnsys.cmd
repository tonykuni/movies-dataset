@echo off
rem =====================================================================
rem via-vrnsys.cmd - VIA 短指令 cmd 直通梭
rem =====================================================================
rrem 背後:VRN_SystemManager_v*.py(批681/682 VRN 子系統管理對接口;Z65 候准 → 側線 2026-09-21 b 准)。
rem   status(七域燈+連結表+七處自審)| catalog | links | read <域> [key] | sync [--apply] | page | --selftest(廿五檢)。
rem   零網路、預設只讀;尾版不在冊上函式印 ABSENT rc2。
em 梭因(批266 實錄):操作員殘常點 cmd,PS global 函式在 cmd 永不可見。
rem   每短指令配同名 .cmd:任何殼在本夾直打即通。**梭不得釘死版號**(CGC_MDL157)。
rem =====================================================================
setlocal
set "VIA=%~dp0..\"
set "PSEXE=powershell"
where pwsh >nul 2>nul
if %errorlevel%==0 set "PSEXE=pwsh"
%PSEXE% -NoProfile -ExecutionPolicy Bypass -Command "$r=Get-ChildItem -LiteralPath '%VIA%.' -Filter 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1; . $r.FullName; & '%~n0'" %*
exit /b %errorlevel%
