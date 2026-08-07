@echo off
rem 全系統總啟動器 v0102:十階段 + UI Hub 動態最新版(回退=改指 Invoke-VIA-One-v0101.ps1)
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\Invoke-VIA-One-v0102.ps1" %*
