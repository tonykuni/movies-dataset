@echo off
rem ETF 資金流三引擎:tw=台灣主動式ETF清單+申贖流 / global=全球跨資產流觀察 / groups=族群三分類+族群指數 — 動態解析最新版(鐵律)
setlocal
set "ENGDIR=%~dp0..\supportive modules\VIA_FlowSystem\FlowSystem_v2\engines"
if /i "%~1"=="tw"     ( shift & py "%ENGDIR%\FLOW_ENG023_FlowTwActiveEtf.py" %2 %3 %4 %5 & goto :eof )
if /i "%~1"=="global" ( shift & py "%ENGDIR%\FLOW_ENG021_FlowGlobalEtfFlowscope.py" %2 %3 %4 %5 & goto :eof )
if /i "%~1"=="groups" ( shift & py "%ENGDIR%\FLOW_ENG022_FlowGroupTaxonomy.py" %2 %3 %4 %5 & goto :eof )
echo 用法: via-etfflow tw^|global^|groups [--registry --refresh --ingest --flows / --universe --measure / --taxonomy --index --chartspec / --selftest]
endlocal
