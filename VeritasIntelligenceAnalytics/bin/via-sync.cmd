@echo off
rem sync repo (fetch + merge claude branch + push main)
pwsh -NoProfile -File "%~dp0via-sync.ps1" %*
