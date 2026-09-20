@echo off
rem =====================================================================
rem via-run25.cmd - VIA 短指令 cmd 直通梭(批649 全鏈編排器:批643-648 一次跑完)
rem =====================================================================
rem 梭因(批266 實錄):操作員殘常點 cmd,PS global 函式在 cmd 永不可見
rem ('not recognized as internal or external command' 即 cmd 簽名句)
rem =批261 雙段陷阱紀章。治本=每短指令配同名 .cmd:任何殼斯本夾直打
rem 即通(cmd 找 .cmd;PowerShell 內函式優先=零衝突)。
rem 機制:pwsh 優先(缺退 powershell)->黑源 Register 尾版->呼同名函式。
rem 批640(L97 要人手打路徑就一定會打錯):操作員兩次照我給的 via-py 全路徑啟動失敗
rem (一次把家族位當檔名、一次少了 VeritasIntelligenceAnalytics\)。治本=收成短令+梭,
rem 路徑由 Get-VIANewest 當場解析,人只打 via-run25。**梭不得釘死版號**(CGC_MDL157)。
rem 批649(編排器例外 LL199):編排器只配冊+梭,不開格子站
rem ——站屬於它呼叫的那些引擎,編排器自己沒有可獨立判的燈。
rem =====================================================================
setlocal
set "VIA=%~dp0"
set "VIA_NO_OPEN=1"
set "PSEXE=powershell"
where pwsh >nul 2>nul
if %errorlevel%==0 set "PSEXE=pwsh"
%PSEXE% -NoProfile -ExecutionPolicy Bypass -Command "$r=Get-ChildItem -LiteralPath '%VIA%.' -Filter 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1; . $r.FullName; & '%~n0'" %*
exit /b %errorlevel%
