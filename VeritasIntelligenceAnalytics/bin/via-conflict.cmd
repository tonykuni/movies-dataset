@echo off
rem 衝突機制總哨兵+壞環境黑名單守衛(TOOL-107):C1 八道衝突巡檢+C2 五道環境守衛(誠實三態)— 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\via_py_celeritas_launcher_v0*.py"') do set "LC=%%f"
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\via_conflict_guard_v0*.py"') do set "CG=%%f"
py "%~dp0..\supportive modules\registry\%LC%" "%~dp0..\supportive modules\registry\%CG%" %*
endlocal
