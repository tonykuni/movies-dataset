@echo off
rem VAP+VDF 一支統包 — 六站順跑誠實矩陣(動態解析最新版統包器,嚴禁寫死版號)
rem 用法:via-vapvdf [-Quick] [-SkipVDF] [-SkipVAP]
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\Invoke-VIA-VAPVDF-ALL-v0*.ps1"') do set "ALL_PS=%%f"
if not defined ALL_PS (
  echo [FAIL] 統包器不在位 — via-sync 後重試
  exit /b 1
)
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\%ALL_PS%" %*
endlocal
