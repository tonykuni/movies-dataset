@echo off
rem =====================================================================
rem via-ssotadd.cmd - VIA 短指令 cmd 直通梭
rem =====================================================================
rem 背後:VRN_ENG088_SsotAdditiveBridge_v*.py(側線 2026-09-21 SSOT 增補審計橋)。
rem   status | tests(暫存副本跑收容包自帶測試+零觸碰證明)| drift | candidates | --selftest。
rem   零網路、零寫庫、只落 VIA_Reports/vrn/ssot_additive;候選一律 PENDING_OPERATOR。
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
