@echo off
rem VMT 資料層 bootstrap(不足的部分補上):以 repo 內 OneShot 對準 VMT 根目錄執行
rem 鐵律清掃(L6 債冊):寫死版號改 dir /b /o:n 動態解析,最新版自動接任
rem 建 superbom.duckdb(SQL 模板)+ ssot.json(14 案種子)+ 跑郵件器產生儀表板 + 交棒 Command Center UI
rem 冪等:已存在的 DB/SSOT 不覆寫(append-only)。root 可用環境變數 VMT_ROOT 覆寫。
if not defined VMT_ROOT set VMT_ROOT=C:\VIA\VeritasMailTracker
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\VIA_Governance_Runtime\installers\VIA-OneShot-v0*.ps1"') do set "EG=%%f"
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\supportive modules\VIA_Governance_Runtime\installers\%EG%" -Workbench "%VMT_ROOT%" %*
endlocal
