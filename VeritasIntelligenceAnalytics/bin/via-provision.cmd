@echo off
rem 首啟布建精靈+機況體檢(初次啟動詢問存放位置;--check 體檢存安裝計畫;--fresh 新機鏈指路)— 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\via_provision_v0*.py"') do set "PV=%%f"
py "%~dp0..\supportive modules\registry\%PV%" %*
endlocal
