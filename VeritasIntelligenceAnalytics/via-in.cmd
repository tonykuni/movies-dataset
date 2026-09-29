@echo off
rem =====================================================================
rem via-in.cmd - VIA 短指令 cmd 直通梭(側線 2026-09-29 g;批340 律;VIA-Verb-Shim v0100)
rem =====================================================================
rem 背後:命令冊尾版的 via-in = via-entry + via-vcgc enter(VCGC v0173 入口流程一句完成)。
rem 根因(批266 實錄):操作員殼常為 cmd,PS global 函式在 cmd 永不可見
rem ('not recognized as internal or external command' 即 cmd 簽名句)。
rem 治本=每短指令配同名 .cmd:任何殼於本夾直打即通(cmd 找 .cmd;PowerShell 內函式優先=零衝突)。
rem 注意:cmd 殼跑這支,流程照跑,但 cmd 自己的目前資料夾不會跟著進倉(子行程改不了父殼);
rem   要在 cmd 下 git 指令,先 cd /d 到倉根。PowerShell 殼直接打 via-in 會真的進到 $VIA。
rem 機制:pwsh 優先(缺退 powershell)->點源 Register 尾版->呼同名函式。梭不得釘死版號(CGC_MDL157)。
rem =====================================================================
setlocal
set "VIA=%~dp0"
set "VIA_NO_OPEN=1"
set "PSEXE=powershell"
where pwsh >nul 2>nul
if %errorlevel%==0 set "PSEXE=pwsh"
%PSEXE% -NoProfile -ExecutionPolicy Bypass -Command "$r=Get-ChildItem -LiteralPath '%VIA%.' -Filter 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1; . $r.FullName; & '%~n0'" %*
exit /b %errorlevel%
