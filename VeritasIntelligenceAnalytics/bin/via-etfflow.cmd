@echo off
rem ETF 資金流三引擎:tw=台灣主動式ETF清單+申贖流 / global=全球跨資產流觀察 / groups=族群三分類+族群指數 — 動態解析最新版(鐵律)
setlocal
set "ENGDIR=%~dp0..\supportive modules\VIA_FlowSystem\FlowSystem_v2\engines"
if /i "%~1"=="tw"     ( shift & py "%ENGDIR%\flow_tw_active_etf.py" %2 %3 %4 %5 & goto :eof )
if /i "%~1"=="global" ( shift & py "%ENGDIR%\flow_global_etf_flowscope.py" %2 %3 %4 %5 & goto :eof )
if /i "%~1"=="groups" ( shift & py "%ENGDIR%\flow_group_taxonomy.py" %2 %3 %4 %5 & goto :eof )
echo 用法: via-etfflow tw^|global^|groups [--registry --refresh --ingest --flows / --universe --measure / --taxonomy --index --chartspec / --selftest]
endlocal
