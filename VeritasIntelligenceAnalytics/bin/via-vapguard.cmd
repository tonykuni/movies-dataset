@echo off
rem VAP 圖規鎖守衛(TOOL-083):規格冊↔快照冊八鎖對勘(軸鎖4間隔5刻度/步階族/snsDeep配色鎖/熱圖鎖) — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VAP\vap_spec_guard_v0*.py"') do set "VG=%%f"
py "%~dp0..\functional modules\VAP\%VG%" %*
endlocal
