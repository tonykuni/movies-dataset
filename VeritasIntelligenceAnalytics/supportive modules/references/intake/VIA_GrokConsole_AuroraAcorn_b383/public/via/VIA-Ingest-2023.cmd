@echo off
chcp 65001 >nul
setlocal EnableExtensions
REM VIA 先進入專案環境，再 COPY 2023→最新 · CMD 啟動器
REM 不要把 .ps1 貼進這個視窗

where pwsh >nul 2>&1
if errorlevel 1 (
  echo RED     NEED  PowerShell 7  ^(pwsh^)
  echo YELLOW  現在是 CMD。不能貼 PowerShell。
  pause
  goto :eof
)

set "ROOT="
for %%P in (
  "%USERPROFILE%\movies-dataset\VeritasIntelligenceAnalytics"
  "%USERPROFILE%\Github\movies-dataset\VeritasIntelligenceAnalytics"
  "%USERPROFILE%\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics"
  "%USERPROFILE%\OneDrive\Desktop\VeritasIntelligenceAnalytics"
  "%USERPROFILE%\Downloads\VeritasIntelligenceAnalytics"
) do (
  if not defined ROOT if exist "%%~P" set "ROOT=%%~P"
)

if not defined ROOT (
  echo RED     找不到母系統 · 先進入專案環境失敗
  pause
  goto :eof
)

echo GREEN   ENTER  %ROOT%

set "PS1="
for %%P in (
  "%~dp0VIA-Ingest-2023.ps1"
  "%ROOT%\scripts\VIA-Ingest-2023.ps1"
  "%USERPROFILE%\Github\VIA-Ingest-2023.ps1"
  "%USERPROFILE%\Github\movies-dataset\scripts\VIA-Ingest-2023.ps1"
  "%USERPROFILE%\movies-dataset\scripts\VIA-Ingest-2023.ps1"
) do (
  if not defined PS1 if exist "%%~P" set "PS1=%%~P"
)

if defined PS1 (
  echo GREEN   FILE   %PS1%
  echo GREEN   先入母目錄+via_vdf，再 COPY_ONLY 2023→最新 · 視窗不關
  pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -WorkingDirectory "%ROOT%" -File "%PS1%"
  goto :eof
)

echo YELLOW  找不到 VIA-Ingest-2023.ps1
echo GREEN   先開 pwsh 在母目錄。看到 PS^> 再貼 Ingest 整段。
pwsh -NoLogo -NoExit -WorkingDirectory "%ROOT%"
goto :eof
