@echo off
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\VDF\Start-VIA-VDF-v0101.ps1" %*
