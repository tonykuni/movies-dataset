@echo off
rem VIA 輸入前檢查動詞 — 重複輸入/缺欄/路徑存在(先擋後跑;動態解析最新版,嚴禁寫死版號)
rem 用法:via-precheck --file data.csv --key date,ticker --required close
rem      via-precheck --path "C:\x\y.json"   ^|   via-precheck selftest
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\via_input_precheck_v0*.py"') do set "PC_ENG=%%f"
if not defined PC_ENG (
  echo [FAIL] precheck 引擎不在位 — via-sync 後重試
  exit /b 1
)
py "%~dp0..\supportive modules\registry\%PC_ENG%" %*
endlocal
