@echo off
rem 五系統產品門面產生器:CGC 綁機/VRN 多tab/VDF 77選/VAP 40卡/FLOW 六功能(理印鎖定+零 CDN)— 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\CGC_MDL072_ProductUi_v0*.py"') do set "PU=%%f"
py "%~dp0..\supportive modules\registry\%PU%" %*
endlocal
