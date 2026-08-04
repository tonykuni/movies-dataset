@echo off
rem manifest-driven Downloads import (newest manifest by default; -Manifest IMPORT_x.json to pick)
pwsh -NoProfile -File "%~dp0..\Invoke-VIA-ImportStaging.ps1" %*
