@echo off
rem 自動編號註冊命名冊:SYS_MDL/ENG###_Camel 正典對映(先發先得 append-only;實體檔零改名紅線)+U/I 檢索板 — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\CGC_MDL071_Namereg_v0*.py"') do set "NR=%%f"
py "%~dp0..\supportive modules\registry\%NR%" %*
endlocal
