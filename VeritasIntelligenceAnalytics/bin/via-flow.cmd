@echo off
rem FlowSystem OneShot v1.0:五鏡頭 FIS+fusion+QA 閘+自產 UI(synthetic 預設;run-local 於 VIA_Reports\flow_run,不覆寫歸檔正本)
if not exist "%~dp0..\VIA_Reports\flow_run" mkdir "%~dp0..\VIA_Reports\flow_run"
cd /d "%~dp0..\VIA_Reports\flow_run"
py "%~dp0..\supportive modules\VIA_FlowSystem\VIA_FlowSystem_OneShot.py" %*
