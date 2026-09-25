@echo off
rem =====================================================================
rem via-panoplan.cmd - VIA 短指令 cmd 直通梭
rem =====================================================================
rem 背後:CGC_MDL171_PanoramaBatchPlanner(批670 全景式分析 + 批次修復規劃器)。
rem   **只規劃不動手**:錯誤識別四類(真缺/尺的錯/缺料/等閘),只有「真缺」進修復波;
rem   同一波內目標檔案互不相交才算可並行;九頭龍風險件與禁動詞件一律不進波。
rem   無參數=計畫表;html=落 rich HTML(零 CDN);--selftest 廿一檢。
rem   判準向 CGC_MDL124 橋掃器整支取用,不自備第二份清單(批670 LL316)。
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
