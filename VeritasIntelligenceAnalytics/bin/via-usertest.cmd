@echo off
rem VIA UserTest — 使用者旅程逐段實測(唯讀;缺件誠實 SKIP)— 動態解析最新版;嚴禁寫死版號
rem 用法:via-usertest ^| via-usertest -SkipHeavy(略過重型引擎自測)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\Invoke-VIA-UserTest-v0*.ps1"') do set "UT=%%f"
if not defined UT (
  echo [FAIL] UserTest 腳本不在位 — via-sync 後重試
  exit /b 1
)
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\%UT%" %*
endlocal
