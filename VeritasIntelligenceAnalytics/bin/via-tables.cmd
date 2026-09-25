@echo off
rem 本地免費表格函式庫統包引擎(9 本地車道+7 雲端列管;唯讀;缺件誠實 NOT_INSTALLED;裝件走 via-install 閘)— 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VRN\VRN_ENG058_TableOmni_v0*.py"') do set "TO=%%f"
py "%~dp0..\functional modules\VRN\%TO%" %*
endlocal
