@echo off
rem 對話紀錄→編排文章+程式抽取(OneEngine Tier-1 掛載;誠實雙道)— 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\CGC_MDL108_ChatToDoc_v0*.py"') do set "CD=%%f"
py "%~dp0..\supportive modules\registry\%CD%" %*
endlocal
