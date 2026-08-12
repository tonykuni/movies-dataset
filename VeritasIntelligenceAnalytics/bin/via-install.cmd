@echo off
rem 安裝治理閘(儲存規定):安裝一律過 EngineForge+EnvManager 閘→pip 前後衝突快照→VIA_Lib_Registry 註冊→輔助導入驗 — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\via_install_gate_v0*.py"') do set "IG=%%f"
py "%~dp0..\supportive modules\registry\%IG%" %*
endlocal
