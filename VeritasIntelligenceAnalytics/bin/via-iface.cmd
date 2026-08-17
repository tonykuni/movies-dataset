@echo off
rem 介面合約自適應註冊:引擎+支援模組全自動編號/說明萃取/合約推導/漂移偵測/跨子系統介面矩陣(AST 零執行)— 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\via_iface_contract_v0*.py"') do set "IC=%%f"
py "%~dp0..\supportive modules\registry\%IC%" %*
endlocal
