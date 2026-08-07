@echo off
rem VIA_Forge v001(staging K 整合;45/45 驗收容器重現):庫鍛/牡郵/觀察/樞管 + via_server 127.0.0.1
rem 用法:via-forge         → 開 Forge 工作台 UI(ui\index.html,一點直入)
rem       via-forge check  → 跑 via_checkmatrix.py 45 項驗收(報告自更新於 VIA_Forge\VIA_CheckMatrix.html)
rem       via-forge server → Start-VIA.ps1 啟動本機服務(127.0.0.1;-NoBrowser 等參數透傳)
if "%~1"=="" (
  start "" "%~dp0..\supportive modules\VIA_Forge\ui\index.html"
) else if /i "%~1"=="check" (
  py "%~dp0..\supportive modules\VIA_Forge\via_checkmatrix.py"
) else if /i "%~1"=="server" (
  shift
  pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\supportive modules\VIA_Forge\Start-VIA.ps1" %2 %3 %4
) else (
  echo 用法: via-forge ^| via-forge check ^| via-forge server [-NoBrowser -SkipDeps -SelfTestOnly]
)
