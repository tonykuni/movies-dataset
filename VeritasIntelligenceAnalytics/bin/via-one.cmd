@echo off
rem 全系統總啟動器 v0107:十二階段(HUB=活化引擎開啟即探測)或 -Only <鍵>;回退=改指 Invoke-VIA-One-v0106.ps1
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\Invoke-VIA-One-v0107.ps1" %*
