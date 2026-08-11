@echo off
rem Bootstrap-VIA-FreshPC-v0100.cmd — 全新電腦一鍵引導(裸機 Windows 即可跑,無需 PS7)
rem 鏈:cmd → 檢/裝 PowerShell 7(winget)→ 檢/裝 Python 3.12 → 交棒 Install-VIA-Product(最新版動態解析)
rem 規約:全自動 DEFAULT;誠實 OK/FAIL 不卡斷;不刪不覆蓋既有正本。用法:
rem   Bootstrap-VIA-FreshPC-v0100.cmd <PKG指針.json> [基座路徑(預設 C:\VeritasIntelligenceAnalytics)]
setlocal enabledelayedexpansion
set "PTR=%~1"
set "BASE=%~2"
if "%BASE%"=="" set "BASE=C:\VeritasIntelligenceAnalytics"
echo === VIA FreshPC Bootstrap v0100 ===
if "%PTR%"=="" (
  echo [FAIL] 用法:Bootstrap-VIA-FreshPC-v0100.cmd ^<PKG指針.json^> [基座]
  exit /b 2
)

rem ── ① PowerShell 7 ──
where pwsh >nul 2>nul
if %errorlevel%==0 (
  echo [OK  ] PowerShell 7 已在位
) else (
  echo [INST] PowerShell 7 缺席 — winget 自動安裝(全自動 DEFAULT)
  where winget >nul 2>nul
  if not %errorlevel%==0 (
    echo [FAIL] winget 亦缺席 — 請手動安裝一次:https://aka.ms/powershell-release?tag=stable 後重跑
    exit /b 2
  )
  winget install --id Microsoft.PowerShell --silent --accept-package-agreements --accept-source-agreements
  rem winget 裝完當前 cmd 的 PATH 未刷新 — 用已知預設路徑補找
  where pwsh >nul 2>nul
  if not %errorlevel%==0 (
    if exist "%ProgramFiles%\PowerShell\7\pwsh.exe" (
      set "PATH=%ProgramFiles%\PowerShell\7;%PATH%"
      echo [OK  ] PowerShell 7 裝妥(本次會話 PATH 已補)
    ) else (
      echo [FAIL] PowerShell 7 安裝未確認 — 重開視窗再跑一次本檔
      exit /b 2
    )
  ) else (
    echo [OK  ] PowerShell 7 裝妥
  )
)

rem ── ② Python 3 ──
where py >nul 2>nul
if %errorlevel%==0 (
  echo [OK  ] Python launcher 已在位
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    echo [OK  ] python 已在位
  ) else (
    echo [INST] Python 缺席 — winget 自動安裝 Python 3.12(全自動 DEFAULT)
    winget install --id Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
    echo [INFO] 裝完若找不到 python,重開視窗再跑本檔即可(PATH 刷新)
  )
)

rem ── ③ 交棒安裝器(動態解析最新版,嚴禁寫死版號)──
set "INST="
for /f "delims=" %%f in ('dir /b /o:n "%~dp0Install-VIA-Product-v0*.ps1" 2^>nul') do set "INST=%%f"
if not defined INST (
  echo [FAIL] 安裝器 Install-VIA-Product-v0*.ps1 不在本目錄
  exit /b 2
)
echo [HAND] pwsh -File "%~dp0!INST!" -Pointer "%PTR%" -Base "%BASE%"
pwsh -NoProfile -File "%~dp0!INST!" -Pointer "%PTR%" -Base "%BASE%"
set "RC=%errorlevel%"
echo === Bootstrap 結束(安裝器 rc=%RC%)===
endlocal & exit /b %RC%
