@echo off
rem 全系統總啟動器 v0109:十三階段(+WORKOPS 一點直入;BRIDGE 補實;HUB 活化引擎動態 pattern)或 -Only <鍵>
rem rollback: pwsh ... -File "%~dp0..\Invoke-VIA-One-v0108.ps1"
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\Invoke-VIA-One-v0109.ps1" %*
