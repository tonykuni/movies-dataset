@echo off
rem 全系統總啟動器 v0110:十四階段(+FORGE;WORKOPS 改開 MailOps 儀表板)或 -Only <鍵>
rem rollback: pwsh ... -File "%~dp0..\Invoke-VIA-One-v0109.ps1"
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\Invoke-VIA-One-v0110.ps1" %*
