@echo off
rem VIA full stack: VDF + VAP + VRN + Tower + audits
pwsh -NoProfile -File "%~dp0..\Start-VIA-OneClick.ps1" -VRN -Tower -Audit -Panorama -Polyglot %*
