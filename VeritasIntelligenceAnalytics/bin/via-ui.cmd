@echo off
rem UI Hub 活化版 v0106:WorkOps 磚動態解析 + Workbench v002 + Workbench 視覺鎖(DesignLock v0102)+一點直入;py 失敗回退靜態 v0108
rem rollback: py "%~dp0..\supportive modules\VIA_Governance_Runtime\via_hub_engine_v0105.py"
py "%~dp0..\supportive modules\VIA_Governance_Runtime\via_hub_engine_v0106.py" %*
if errorlevel 1 start "" "%~dp0..\supportive modules\ui_support\VIA_UI_Hub_v0108.html"
