@echo off
rem 全景式分析六獨立流程(唯讀零九頭龍)— 動態解析最新版(鐵律:嚴禁寫死版號)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\via_panorama_six_v0*.py"') do set "P6=%%f"
py "%~dp0..\supportive modules\registry\%P6%" %*
endlocal
