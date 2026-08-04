@echo off
rem TickerRegex v0100 shimmed entry: via-shim -Target <file> [-DryRun] [-Args ...]
pwsh -NoProfile -File "%~dp0..\functional modules\VRN\Invoke-VRN-Shimmed-Entry-v0100.ps1" %*
