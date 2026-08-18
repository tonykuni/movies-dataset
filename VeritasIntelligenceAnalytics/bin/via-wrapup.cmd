@echo off
rem 加速收尾系統(TOOL-068):--supconfirm <舊根路徑> 導入確認(hash 對正典)/ --battery 六道并行收尾電池 — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\via_wrapup_v0*.py"') do set "WU=%%f"
py "%~dp0..\supportive modules\registry\%WU%" %*
endlocal
