@echo off
chcp 65001 >nul
rem GapFill Stage-2 一支到底轉發 — 找包→盤點→QA 復驗→晉升(不覆蓋)→推送(動態解析最新版)
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\Invoke-VIA-GapFill-Stage2-v0*.ps1"') do set "VIA_GF=%%f"
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\%VIA_GF%" %*
