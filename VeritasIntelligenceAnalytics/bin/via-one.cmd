@echo off
rem 全系統總啟動器 v0108:十二階段(HUB 引擎動態 pattern)或 -Only <鍵>;回退=改指 Invoke-VIA-One-v0107.ps1
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\Invoke-VIA-One-v0108.ps1" %*
