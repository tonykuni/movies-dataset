@echo off
rem 母系統向下接手引擎(TOOL-097):M1 PS 治理考古/M2 雙世代引擎舉證(核准閘)/M3 SSOT 真值+regex 提醒/M4 加速器稽核/M5 支援模組自動註冊/M6 外呼網路稽核 — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\via_mother_takeover_v0*.py"') do set "TK=%%f"
py "%~dp0..\supportive modules\registry\via_py_celeritas_launcher_v0100.py" "%~dp0..\supportive modules\registry\%TK%" %*
endlocal
