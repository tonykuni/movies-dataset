@echo off
rem 一支 PowerShell 統包全流程:test-debug-optimize-consolidate-U/I-usertest-activate(唯讀/dry-run 建議制)— 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\Invoke-VIA-AllGreen-v0*.ps1"') do set "AG=%%f"
pwsh -NoProfile -File "%~dp0..\supportive modules\registry\%AG%" %*
endlocal
