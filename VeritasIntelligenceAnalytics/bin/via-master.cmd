@echo off
rem 母版管理中樞(central governance SSOT JSON + 入口 UI + 三子系統 UI;動詞表自動進化)— 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\CGC_MDL059_MasterHub_v0*.py"') do set "MH=%%f"
py "%~dp0..\supportive modules\registry\%MH%" %*
endlocal
