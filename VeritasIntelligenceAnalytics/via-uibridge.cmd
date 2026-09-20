@echo off
rem =====================================================================
rem via-uibridge.cmd - U/I 橋接整合台(CGC_MDL130_UIBridge;別名 畫面橋)
rem 批649:批647 我把 via-ui 這個名字拿去指 MDL160 template,MDL130 當場從冊上失聯。
rem 活的那支不動(操作員已在用),被吃掉的這支改由本梭到達。
rem =====================================================================
rem 梭因(批261):操作員殘常點 cmd,PS global 函式在 cmd 永不可見。
rem 治本=每短指令配同名 .cmd。**梭不得釘死版號**(CGC_MDL157 檢②)。
rem =====================================================================
setlocal
set "VIA=%~dp0"
set "VIA_NO_OPEN=1"
set "PSEXE=powershell"
where pwsh >nul 2>nul
if %errorlevel%==0 set "PSEXE=pwsh"
%PSEXE% -NoProfile -ExecutionPolicy Bypass -Command "$r=Get-ChildItem -LiteralPath '%VIA%.' -Filter 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1; . $r.FullName; & '%~n0'" %*
exit /b %errorlevel%
