@echo off
rem 多環境隔離重建計畫引擎(via_*/BASE 盤點→衝突風險因子→旁建隔離重建計畫→三鏡像測選→dry-run 反覆實測→GREEN 段出執行檔;零安裝零刪改)— 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\via_env_rebuild_v0*.py"') do set "ER=%%f"
py "%~dp0..\supportive modules\registry\%ER%" %*
endlocal
