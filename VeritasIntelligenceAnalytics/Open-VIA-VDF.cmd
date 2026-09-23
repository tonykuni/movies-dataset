@echo off
rem Open-VIA-VDF.cmd - double-click to open VDF in one step (side line 2026-09-23).
rem Opens a pwsh 7 window and dot-sources the newest Open-VIA-VDF-v*.ps1 next to this file
rem (dot-source, not the call operator: the command register must land in the window's global scope):
rem enter env -> HTML parameter page -> fetch -> database status page. The window stays open.
setlocal
set "HERE=%~dp0"
where pwsh >nul 2>nul
if errorlevel 1 (
  echo [FAIL] pwsh ^(PowerShell 7^) not found. Install PowerShell 7 and run this file again.
  pause
  exit /b 3
)
pwsh -NoExit -NoProfile -ExecutionPolicy Bypass -Command ". (Get-ChildItem -LiteralPath $env:HERE -Filter 'Open-VIA-VDF-v*.ps1' -File | Sort-Object Name | Select-Object -Last 1).FullName"
