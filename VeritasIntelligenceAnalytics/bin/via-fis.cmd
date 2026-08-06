@echo off
rem FIS 驗證 harness v3:E1/E2/E3 實驗+Matrix 報告(需 scipy/numpy:py -m pip install scipy;run-local 於 VIA_Reports\fis_run)
if not exist "%~dp0..\VIA_Reports\fis_run" mkdir "%~dp0..\VIA_Reports\fis_run"
cd /d "%~dp0..\VIA_Reports\fis_run"
py "%~dp0..\supportive modules\VIA_FlowSystem\VIA_FIS_Validation_v3.py" %*
