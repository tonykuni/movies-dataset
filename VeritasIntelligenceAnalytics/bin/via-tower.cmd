@echo off
rem VIA Control Tower (HTML console at 127.0.0.1:8765)
pwsh -NoProfile -File "%~dp0..\Start-VIA-OneClick.ps1" -Tower %*
