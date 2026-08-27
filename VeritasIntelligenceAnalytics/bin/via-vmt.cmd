@echo off
rem VMT SuperBOM 總指揮 v0103(Porcelain 刊頭;問卷->附件->收斂->CPM,缺件優雅略過;回退=改指 VIA_ENG021_MasterEngine_v0102.py)
rem 鐵律清掃(L6 債冊):寫死版號改 dir /b /o:n 動態解析,最新版自動接任
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\WorkOps\VMT\VIA_ENG021_MasterEngine_v0*.py"') do set "EG=%%f"
py "%~dp0..\functional modules\WorkOps\VMT\%EG%" %*
endlocal
