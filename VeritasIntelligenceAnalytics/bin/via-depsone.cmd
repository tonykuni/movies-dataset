@echo off
rem 依賴治理一鍵統包:via-deps 全景→三鏡像測速→via-rebuild 七段→GREEN 執行檔候裁/受令→回驗總結(預設零安裝;-Consent 開網;-Execute 受令跑)— 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\Invoke-VIA-DepsOne-v0*.ps1"') do set "DO=%%f"
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\supportive modules\registry\%DO%" %*
endlocal
