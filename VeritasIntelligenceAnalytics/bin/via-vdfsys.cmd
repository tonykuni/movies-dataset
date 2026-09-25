@echo off
rem =====================================================================
rem via-vdfsys.cmd - VIA 短指令 cmd 直通梭
rem =====================================================================
rem 背後:VDF_SystemManager_v*.py(側線 2026-09-21 b VDF 子系統管理對接口;與 VRN 那扇門同一份契約)。
rem   status(九域燈+連結表+七處自審)| engines | bridges | tools | catalog | links | records
rem   | read <域> [key] [--full] | sync [--apply](只落 VIA_Reports\vdf_system)| page | --selftest(廿七檢)。
rem   零網路、零寫庫、預設只讀;rc0 綠 / rc2 過期或缺料 / rc1 壞;尾版不在冊上函式印 ABSENT rc2。
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
