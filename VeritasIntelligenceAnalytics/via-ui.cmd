@echo off
rem =====================================================================
rem via-ui.cmd - VIA 短指令 cmd 直通梭(批647 正典 TEMPLATE;批340 梭律;VIA-Verb-Shim v0100)
rem =====================================================================
rem 操作員令(批647):「本機自動跳出 HTML U/I NO SERVER」+「VIA_HTML_UI 進 VIA
rem 為可調整統一銜接系統的 TEMPLATE」。via-ui 一鍵開正典啟動器:
rem   VIA_HTML_UI/ui/VIA-Complete-System.html —— file:// 直開,零 server、零 CDN。
rem 本梭**不設 VIA_NO_OPEN**(其餘 86 支梭都設 1;這一支的工作就是跳出來)。
rem 要它別跳,自己在殼裡 set VIA_NO_OPEN=1,或打 via-ui --check(只驗不開)。
rem 機制:pwsh 優先(缺退 powershell)->點源 Register 尾版->呼同名函式。**梭不釘版號**。
rem =====================================================================
setlocal
set "VIA=%~dp0"
set "PSEXE=powershell"
where pwsh >nul 2>nul
if %errorlevel%==0 set "PSEXE=pwsh"
%PSEXE% -NoProfile -ExecutionPolicy Bypass -Command "$r=Get-ChildItem -LiteralPath '%VIA%.' -Filter 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1; . $r.FullName; & '%~n0'" %*
exit /b %errorlevel%
