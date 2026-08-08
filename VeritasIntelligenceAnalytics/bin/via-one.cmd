@echo off
rem 全系統總啟動器 v0111:十四階段(WORKOPS 動態最新版=Workbench v002)或 -Only <鍵>
rem rollback: pwsh ... -File "%~dp0..\Invoke-VIA-One-v0110.ps1"
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\Invoke-VIA-One-v0111.ps1" %*
