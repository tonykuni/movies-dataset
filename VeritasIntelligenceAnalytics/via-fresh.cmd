@echo off
rem =====================================================================
rem via-fresh.cmd - 冊新鮮度(別名 冊新鮮;批653)
rem 操作員實錄:pull 到 v0230(九站)之後在同一個 PS 視窗打 via-run25,印的是 8 站。
rem PowerShell 的 global 函式是**點源當下**烙進工作階段的,拉新檔不換掉已載入的函式。
rem 批629 記過同一件事;這次讓令自己會講,不要再由我連講四次。
rem =====================================================================
rem 梭(批261):操作員殘常點 cmd,PS global 函式在 cmd 永不可見。
rem 本梭天生免疫舊冊:每次都現場解析尾版冊再點源。**不得釘死版號**(CGC_MDL157)。
rem =====================================================================
setlocal
set "VIA=%~dp0"
set "VIA_NO_OPEN=1"
set "PSEXE=powershell"
where pwsh >nul 2>nul
if %errorlevel%==0 set "PSEXE=pwsh"
%PSEXE% -NoProfile -ExecutionPolicy Bypass -Command "$r=Get-ChildItem -LiteralPath '%VIA%.' -Filter 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1; . $r.FullName; & '%~n0'" %*
exit /b %errorlevel%
