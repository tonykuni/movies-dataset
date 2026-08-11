@echo off
rem 自動識別編號器(全域編碼註冊中心):via-code <類別> <元件名> [suffix] / via-code --list / via-code --register <類別> <前綴> [padding]
rem 鐵律清掃(L6 債冊):寫死版號改 dir /b /o:n 動態解析,最新版自動接任
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\via_autocoder_engine_v0*.py"') do set "EG=%%f"
py "%~dp0..\supportive modules\registry\%EG%" %*
endlocal
