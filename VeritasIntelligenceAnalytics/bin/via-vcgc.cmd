@echo off
rem =====================================================================
rem via-vcgc.cmd - VIA 短指令 cmd 直通梭
rem =====================================================================
rem 背後:CGC_MDL149_VeritasCentralGovernanceConsole(VCGC;VIA 往下的那一扇門)。
rem   status|check|audit|matrix|panorama|register-plan|registry-sync|--selftest
rem   批686:子系統對接口三家一把尺(VRN/VDF/VAP);缺席的家族回 ABSENT 誠實,不假裝有。
rem 梭因(批266 實錄):操作員常點 cmd,PS global 函式在 cmd 永不可見。
rem   每短指令配同名 .cmd:任何殼在本夾直打即通。**梭不得釘死版號**(CGC_MDL157)。
rem 批686 實錄:第一版寫成 `py <引擎>` 直跑——那是**獨立實作不是梭**,
rem   而 via-vcgc 在 Register 裡早已是同名函式,於是同一個名字指到兩個東西。
rem   CGC_MDL165 的撞名棘輪當場照紅(基線外 +1),判得對(L101)。
rem =====================================================================
setlocal
set "VIA=%~dp0..\"
set "PSEXE=powershell"
where pwsh >nul 2>nul
if %errorlevel%==0 set "PSEXE=pwsh"
%PSEXE% -NoProfile -ExecutionPolicy Bypass -Command "$r=Get-ChildItem -LiteralPath '%VIA%.' -Filter 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1; . $r.FullName; & '%~n0'" %*
exit /b %errorlevel%
