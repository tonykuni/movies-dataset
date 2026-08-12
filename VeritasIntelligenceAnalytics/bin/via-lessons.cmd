@echo off
rem 教訓帳本引擎(LESSON-LEARNED:收割存證→RESULT MATRIX+ROOT CAUSES & SOLUTIONS 落 log→GOLDEN 無衝突基線=改進起點;append-only)— 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\via_lessons_v0*.py"') do set "LS=%%f"
py "%~dp0..\supportive modules\registry\%LS%" %*
endlocal
