@echo off
rem VIA 跨子系統繪圖動詞 — seaborn+plotly 引擎線(28 圖型全譜;動態解析最新版,嚴禁寫死版號)
rem 任何子系統資料皆可餵:--file 支援 .csv/.tsv/.json/.sqlite;SSOT 樣式自動向上尋 spec/ssot
rem 用法:via-plot probe                                    後端/SSOT 探測(零依賴可跑)
rem      via-plot list ^| via-plot spec                     28 圖型清單/樣式規格
rem      via-plot render --chart line --file "functional modules\VDF\db\demo_tw_stock_monthly.csv" --x date --y close --out vap_out
rem      via-plot demo --out vap_demo ^| via-plot selftest  全譜渲染/自我驗證
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VAP\engine\via_autoplot_seaborn_plotly_v0*.py"') do set "PLOT_ENG=%%f"
if not defined PLOT_ENG (
  echo [FAIL] seaborn/plotly 引擎不在位 — via-sync 後重試
  exit /b 1
)
py "%~dp0..\functional modules\VAP\engine\%PLOT_ENG%" %*
endlocal
