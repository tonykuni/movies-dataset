@echo off
rem EnvManager 決策式安裝 v0101:已就緒不動+黃金律範圍修正(僅vmt_pm)+pip check 差分;回退=改指 Invoke-VIA-EnvFix-v0100.ps1
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\Invoke-VIA-EnvFix-v0101.ps1" %*
