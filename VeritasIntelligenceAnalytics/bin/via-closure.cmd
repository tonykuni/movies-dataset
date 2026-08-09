@echo off
chcp 65001 >nul
rem VDF·VRN·VAP 結案器轉發 — 盤點+封存基線(唯讀;快照 append-only;可重跑)
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\Invoke-VIA-TrinityClosure-v0*.ps1"') do set "VIA_TC=%%f"
where pwsh >nul 2>nul
if %errorlevel%==0 (
  pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\%VIA_TC%" %*
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\%VIA_TC%" %*
)
