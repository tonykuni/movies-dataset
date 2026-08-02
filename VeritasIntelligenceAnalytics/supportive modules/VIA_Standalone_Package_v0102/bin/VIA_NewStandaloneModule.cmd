@echo off
set PACKAGE_DIR=%~dp0..
pwsh -NoLogo -ExecutionPolicy Bypass -File "%PACKAGE_DIR%\Launch-VIA_NewStandaloneModule.ps1" -ReviewOnly %*
