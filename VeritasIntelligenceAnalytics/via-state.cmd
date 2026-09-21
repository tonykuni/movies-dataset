@echo off
rem =====================================================================
rem via-state.cmd - VIA 短指令 cmd 直通梭(批664 六域現況矩陣)
rem =====================================================================
rem 背後:VRN_ENG073_ReportStructuredDB repair-price
rem   **不重新擷取任何報告**,只拿庫裡現有列重算價與上漲空間(零網路·零擷取·不碰正本)。
rem   無參數=乾跑(會把前幾筆逐件印出來);--apply 才寫庫;--db <路徑> 指定另一本庫。
rem 批659 實錄:上漲空間整欄零綠,根因是 tw_daily_prices 只有上櫃 892 檔、上市所 0 檔。
rem   接上含上市的 tw_trading_daily 後乾跑說「新拿到 37 件」,逐件看才發現全是 2025-06-30
rem   的舊價(上市所停在該日)——**摘要會讓你以為修好了,明細才看得見**(LL300)。
rem 梭因(批266 實錄):操作員殘常點 cmd,PS global 函式在 cmd 永不可見。
rem   每短指令配同名 .cmd:任何殼在本夾直打即通。**梭不得釘死版號**(CGC_MDL157)。
rem =====================================================================
setlocal
set "VIA=%~dp0"
set "VIA_NO_OPEN=1"
set "PSEXE=powershell"
where pwsh >nul 2>nul
if %errorlevel%==0 set "PSEXE=pwsh"
%PSEXE% -NoProfile -ExecutionPolicy Bypass -Command "$r=Get-ChildItem -LiteralPath '%VIA%.' -Filter 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1; . $r.FullName; & '%~n0'" %*
exit /b %errorlevel%
