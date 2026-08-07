@echo off
rem UI Hub 活化版:via_hub_engine 開啟即探測(十四介面+即時徽章);py 失敗自動回退靜態 v0108
py "%~dp0..\supportive modules\VIA_Governance_Runtime\via_hub_engine_v0100.py" %*
if errorlevel 1 start "" "%~dp0..\supportive modules\ui_support\VIA_UI_Hub_v0108.html"
