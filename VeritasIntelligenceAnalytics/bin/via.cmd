@echo off
rem VIA one-click (default: sync + VDF + VAP + open UIs)
pwsh -NoProfile -File "%~dp0..\Start-VIA-OneClick.ps1" %*
