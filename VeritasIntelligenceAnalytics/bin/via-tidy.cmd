@echo off
rem Downloads 整理歸納去重(dry-run 預設;--commit 才搬;零刪除全程可逆 --undo)— 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\CGC_MDL047_DownloadsOrganizer_v0*.py"') do set "TD=%%f"
py "%~dp0..\supportive modules\registry\%TD%" %*
endlocal
