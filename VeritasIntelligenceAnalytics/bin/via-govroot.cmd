@echo off
rem 中央治理母根一鍵器(跨會話導入:三層 VIA_MOTHER_ROOT 指標+SHA-256 斷點+硬閘門+HOLD 證據;永不關窗;禁 OneDrive)— 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\Invoke-VIA-Central-Governance-OneClick-v0*.ps1"') do set "GV=%%f"
pwsh -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\supportive modules\registry\%GV%" %*
endlocal
