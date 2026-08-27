@echo off
rem VIA 自動編號引擎 — 下一號預覽/核發(動態解析最新版,嚴禁寫死版號)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\CGC_MDL060_NumberEngine_v0*.py"') do set "N_ENG=%%f"
if not defined N_ENG (
  echo [FAIL] 編號引擎不在位 — via-sync 後重試
  exit /b 1
)
py "%~dp0..\supportive modules\registry\%N_ENG%" %*
endlocal
