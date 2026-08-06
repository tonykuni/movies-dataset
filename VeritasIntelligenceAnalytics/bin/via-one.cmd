@echo off
rem 全系統總啟動器 v0101:sync -> Mega v0106 -> VMT -> CGE -> VRN probe/extract -> FlowSystem UI -> IF selftest -> FIS -> UI Hub v0104(不卡斷;回退=改指 Invoke-VIA-One-v0100.ps1)
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\Invoke-VIA-One-v0101.ps1" %*
