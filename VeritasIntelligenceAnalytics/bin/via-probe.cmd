@echo off
rem VRN 內容級擷取 Stage-0 可行性探測(唯讀,不寫 SSOT):via-probe [PDF資料夾] [--limit N]
rem 鐵律清掃(L6 債冊):寫死版號改 dir /b /o:n 動態解析,最新版自動接任
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VRN\vrn_content_probe_v0*.py"') do set "EG=%%f"
py "%~dp0..\functional modules\VRN\%EG%" %*
endlocal
