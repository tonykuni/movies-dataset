@echo off
rem 全系統總啟動器 v0104:十階段(Mega/VMT/Hub 動態最新版)或 -Only <子系統> 看U/I;回退=改指 Invoke-VIA-One-v0103.ps1
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\Invoke-VIA-One-v0104.ps1" %*
