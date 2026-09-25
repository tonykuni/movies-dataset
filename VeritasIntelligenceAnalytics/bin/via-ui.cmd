@echo off
rem UI Hub 活化版 v0108:WorkOps 磚=統合指揮板(WorkOps×VMT) + Workbench 視覺鎖(DesignLock v0102)+一點直入;py 失敗回退靜態 v0108
rem 鐵律清掃(L6 債冊):寫死版號改 dir /b /o:n 動態解析,最新版自動接任
rem rollback: py "%~dp0..\supportive modules\VIA_Governance_Runtime\SUP_MDL141_HubEngine_v0107.py"
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\VIA_Governance_Runtime\SUP_MDL141_HubEngine_v0*.py"') do set "EG=%%f"
py "%~dp0..\supportive modules\VIA_Governance_Runtime\%EG%" %*
endlocal
if errorlevel 1 start "" "%~dp0..\supportive modules\ui_support\VIA_UI_Hub_v0108.html"
