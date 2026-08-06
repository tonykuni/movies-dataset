@echo off
rem 最終整合版總啟動器:sync -> Mega v0103 三輪全景 -> VMT -> CGE dry-run -> VRN probe/extract -> UI Hub(不卡斷)
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\Invoke-VIA-One-v0100.ps1" %*
