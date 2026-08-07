@echo off
rem UI Hub 活化版 v0101:一點直入(12 卡直達連結;VAP/VDF/VRN=設計主頁視覺鎖);py 失敗回退靜態 v0108
py "%~dp0..\supportive modules\VIA_Governance_Runtime\via_hub_engine_v0101.py" %*
if errorlevel 1 start "" "%~dp0..\supportive modules\ui_support\VIA_UI_Hub_v0108.html"
