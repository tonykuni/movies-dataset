@echo off
rem VIA VAP 一鍵繪圖啟動器 — 動態解析最新 chartlib 引擎;嚴禁寫死版號
rem 用法:via-vap --demo --table demo_tw_stock_monthly --x date --series close,volume --transform rebase100
rem      via-vap --list ^| via-vap --table T --x date --left A --right B ^| --stackchart sarea ^| --bands "起:迄:標籤"
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VAP\engine\VAP_ENG001_AutoplotEngineChartlib_v0*.py"') do set "VAP_ENG=%%f"
if not defined VAP_ENG (
  echo [FAIL] chartlib 引擎不在位 — via-sync 後重試
  exit /b 1
)
py "%~dp0..\functional modules\VAP\engine\%VAP_ENG%" --base "%~dp0.." %*
endlocal
