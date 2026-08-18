@echo off
rem 文章攝入引擎:混合訊息流→切分/CJK 斷行修復/繁簡英判別/分類→JSONL+CSV(11 軸對齊);--fetch 鎖同意閘 — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\CGC_MDL041_ArticleIntake_v0*.py"') do set "AI=%%f"
py "%~dp0..\supportive modules\registry\%AI%" %*
endlocal
