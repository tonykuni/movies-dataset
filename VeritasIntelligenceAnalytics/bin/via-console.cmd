@echo off
rem 中央治理台 Console — 功能正典 JSON 載入+引擎/動詞/資料在位驗證(動態解析最新版,嚴禁寫死版號)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\CGC_MDL053_GovernanceConsole_v0*.py"') do set "C_ENG=%%f"
if not defined C_ENG (
  echo [FAIL] Console 工具不在位 — via-sync 後重試
  exit /b 1
)
py "%~dp0..\supportive modules\registry\%C_ENG%" %*
endlocal
