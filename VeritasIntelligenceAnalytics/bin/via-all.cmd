@echo off
rem VIA full interactive stack: VDF + VAP + VRN preflight + Tower (no long-running disk audits)
pwsh -NoProfile -File "%~dp0..\Start-VIA-OneClick.ps1" -VRN -Tower %*
