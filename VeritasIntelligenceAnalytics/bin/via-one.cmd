@echo off
rem 全系統總啟動器 v0103:十階段全跑 或 via-one -Only <mega^|vmt^|cge^|probe^|extract^|flow^|if^|fis> 選子系統看U/I;回退=改指 Invoke-VIA-One-v0102.ps1
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\Invoke-VIA-One-v0103.ps1" %*
