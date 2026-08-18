@echo off
rem 實體更名引擎(TOOL-065;操作員解鎖令):--plan 分級計畫 / --commit SAFE級更名 / --undo 反轉;編號永不變+台帳可逆 — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\via_rename_engine_v0*.py"') do set "RN=%%f"
py "%~dp0..\supportive modules\registry\%RN%" %*
endlocal
