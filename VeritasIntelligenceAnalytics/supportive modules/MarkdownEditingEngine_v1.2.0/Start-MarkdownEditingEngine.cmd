@echo off
where pwsh >nul 2>nul
if %errorlevel%==0 (
  pwsh -NoLogo -NoExit -ExecutionPolicy Bypass -File "%~dp0MarkdownEditingEngine.ps1" doctor -WaitForKey
) else (
  powershell -NoLogo -NoExit -ExecutionPolicy Bypass -File "%~dp0MarkdownEditingEngine.ps1" doctor -WaitForKey
)
