@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
where pwsh.exe >nul 2>nul
if not errorlevel 1 (
    pwsh.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%Run-VAP-Seaborn-Stack.ps1" -Action demo -Config "examples/demo_stack.json" -OpenOutput
) else (
    powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%Run-VAP-Seaborn-Stack.ps1" -Action demo -Config "examples/demo_stack.json" -OpenOutput
)
set "EXIT_CODE=%ERRORLEVEL%"
endlocal & exit /b %EXIT_CODE%
