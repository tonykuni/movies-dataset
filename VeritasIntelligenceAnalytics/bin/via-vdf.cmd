@echo off
rem v0160B (Veritas design-lock masthead) · rollback: point at Start-VIA-VDF-v0101.ps1 (v0160A)
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\VDF\Start-VIA-VDF-v0102.ps1" %*
