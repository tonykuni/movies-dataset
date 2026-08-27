@echo off
rem 全面自動化巡航(五站唯讀/dry-run 不影響正常運作;--register 註冊每日排程)— 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\CGC_MDL042_AutoPilot_v0*.py"') do set "AP=%%f"
py "%~dp0..\supportive modules\registry\%AP%" %*
endlocal
