@echo off
rem 全系統總啟動器 v0106:十二階段(全引擎動態最新版)或 -Only <鍵>;回退=改指 Invoke-VIA-One-v0105.ps1
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\Invoke-VIA-One-v0106.ps1" %*
