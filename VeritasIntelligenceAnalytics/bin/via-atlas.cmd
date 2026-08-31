@echo off
rem 向右樹枝狀圖譜(TOOL-066):--build 樹+ENV矩陣 / --env 環境工具矩陣 / --ladder 六級測試梯 — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\CGC_MDL078_TreeAtlas_v0*.py"') do set "TA=%%f"
py "%~dp0..\supportive modules\registry\%TA%" %*
endlocal
