@echo off
chcp 65001 >nul
setlocal EnableExtensions
REM VIA 先進入專案環境 · 可貼 CMD、可雙擊 · 不要在 CMD 貼 .ps1
REM 找到母目錄後開 pwsh，工作目錄=專案根，再跑 VIA-Enter-Root.ps1（釘 via_vdf）

where pwsh >nul 2>&1
if errorlevel 1 (
  echo RED     NEED  PowerShell 7  ^(pwsh^)
  echo YELLOW  現在是 CMD。先安裝 pwsh。
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
  echo RED     找不到母系統 VeritasIntelligenceAnalytics
  pause
  goto :eof
)

echo GREEN   ENTER  %ROOT%

set "PS1="
for %%P in (
  "%~dp0VIA-Enter-Root.ps1"
  "%ROOT%\scripts\VIA-Enter-Root.ps1"
  "%USERPROFILE%\Github\VIA-Enter-Root.ps1"
) do (
  if not defined PS1 if exist "%%~P" set "PS1=%%~P"
)

if defined PS1 (
  echo GREEN   FILE   %PS1%
  pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -WorkingDirectory "%ROOT%" -File "%PS1%"
  goto :eof
)

echo YELLOW  無 VIA-Enter-Root.ps1 · 仍開 pwsh 在母目錄
pwsh -NoLogo -NoExit -WorkingDirectory "%ROOT%"
goto :eof
