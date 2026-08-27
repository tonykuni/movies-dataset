@echo off
rem 舊根救援+封存一鍵:殘餘證據救援→具名提交雙推→封存改名(鎖定自癒+robocopy 後備)· 20 加速器+留痕+進度條 — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\Invoke-VIA-OldRoot-Salvage-Retire-v0*.ps1"') do set "RR=%%f"
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\supportive modules\registry\%RR%" %*
endlocal
