@echo off
rem 語法敗三輪沙盒救援(TOOL-064):--scan 清單 / --repair 全數提案 / --repair-one 單檔;原件零觸碰,提案並排候裁 — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\CGC_MDL076_SyntaxRescue_v0*.py"') do set "SR=%%f"
py "%~dp0..\supportive modules\registry\%SR%" %*
endlocal
