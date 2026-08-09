@echo off
rem VIA long-running audits: TurboOptimizer SafeAudit + Panorama + Polyglot (expect many minutes)
pwsh -NoProfile -File "%~dp0..\Start-VIA-OneClick.ps1" -Audit -Panorama -Polyglot %*
