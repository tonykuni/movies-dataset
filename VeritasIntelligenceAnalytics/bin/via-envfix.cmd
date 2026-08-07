@echo off
rem EnvFix v0102:已就緒不動+check差分;-RepairBase 補 base 存量缺件(wheel限定;-IncludeHeavy 連 torch 家族);回退=改指 v0101
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\Invoke-VIA-EnvFix-v0102.ps1" %*
