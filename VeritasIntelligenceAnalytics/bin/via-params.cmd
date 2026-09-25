@echo off
rem 中央參數樞紐(TOOL-069):全參數 SSOT 冊指標索引+跨冊衝突燈+LOCKED 對齊+--get 跨冊查參 — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\via_params_central_v0*.py"') do set "PC=%%f"
py "%~dp0..\supportive modules\registry\%PC%" %*
endlocal
