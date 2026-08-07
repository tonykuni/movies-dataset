@echo off
rem FlowSystem OneShot v0101(Porcelain 表面;漲跌色功能語意保留;run-local VIA_Reports\flow_run;回退=改指 VIA_FlowSystem_OneShot.py)
if not exist "%~dp0..\VIA_Reports\flow_run" mkdir "%~dp0..\VIA_Reports\flow_run"
cd /d "%~dp0..\VIA_Reports\flow_run"
py "%~dp0..\supportive modules\VIA_FlowSystem\VIA_FlowSystem_OneShot_v0101.py" %*
