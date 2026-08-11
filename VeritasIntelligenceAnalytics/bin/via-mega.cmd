@echo off
rem 公定處理模式 v0108:三輪全景 14 域 + 巢狀 git repo 圍堵(自帶 .git 之子目錄=外來 clone,整棵跳過);回退=改指 via_mega_engine_v0108.py
rem 鐵律清掃(L6 債冊):寫死版號改 dir /b /o:n 動態解析,最新版自動接任
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\VIA_Governance_Runtime\via_mega_engine_v0*.py"') do set "EG=%%f"
py "%~dp0..\supportive modules\VIA_Governance_Runtime\%EG%" %*
endlocal
