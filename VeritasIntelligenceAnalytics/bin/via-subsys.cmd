@echo off
rem 三子系統管理模組(TOOL-099):--sub VRN^|VDF^|VAP^|ALL 憲章對讀/盤點/AST 健康 RYG/VSM 迷你報 — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\via_subsys_manager_v0*.py"') do set "SM=%%f"
py "%~dp0..\supportive modules\registry\via_py_celeritas_launcher_v0100.py" "%~dp0..\supportive modules\registry\%SM%" %*
endlocal
