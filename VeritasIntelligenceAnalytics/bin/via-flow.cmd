@echo off
rem FlowSystem OneShot v0101(Porcelain 表面;漲跌色功能語意保留;run-local VIA_Reports\flow_run;回退=改指 VIA_FlowSystem_OneShot.py)
rem 鐵律清掃(L6 債冊):寫死版號改 dir /b /o:n 動態解析,最新版自動接任
if not exist "%~dp0..\VIA_Reports\flow_run" mkdir "%~dp0..\VIA_Reports\flow_run"
cd /d "%~dp0..\VIA_Reports\flow_run"
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\VIA_FlowSystem\VIA_FlowSystem_OneShot_v0*.py"') do set "EG=%%f"
py "%~dp0..\supportive modules\VIA_FlowSystem\%EG%" %*
endlocal
