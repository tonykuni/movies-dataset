@echo off
rem 籌碼戰整合主控台(六引擎;全免費源;test→consolidate→usertest→activate 循環)— 動態解析最新版(鐵律)
setlocal
pushd "%~dp0..\functional modules\ChipWar\engines"
for /f "delims=" %%f in ('dir /b /o:n "VIA_ChipWar_Console_v0*.py" ^| findstr /v "_sha"') do set "CW=%%f"
py "%CW%" %*
popd
endlocal
