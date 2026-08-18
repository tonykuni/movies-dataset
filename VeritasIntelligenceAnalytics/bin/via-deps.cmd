@echo off
rem 依賴衝突統包引擎(十械三防線+三鏡像:全景掃描/逆溯/樹狀/鏡像測速切源/場景編成/多版本矩陣;唯讀零改動)— 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\CGC_MDL046_DepSuper_v0*.py"') do set "DS=%%f"
py "%~dp0..\supportive modules\registry\%DS%" %*
endlocal
