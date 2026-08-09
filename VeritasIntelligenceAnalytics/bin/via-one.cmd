@echo off
rem 全系統總啟動器 v0112:十四階段(WORKOPS=指揮板一支到底)或 -Only <鍵>
rem rollback: pwsh ... -File "%~dp0..\Invoke-VIA-One-v0112.ps1"
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\Invoke-VIA-One-v0113.ps1" %*
