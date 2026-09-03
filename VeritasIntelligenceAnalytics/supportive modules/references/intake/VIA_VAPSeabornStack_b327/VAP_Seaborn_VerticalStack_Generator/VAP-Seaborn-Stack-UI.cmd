@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%"
set "VAP_ENV_READY="
if exist ".venv\Scripts\python.exe" if exist ".venv\Scripts\pythonw.exe" (
    ".venv\Scripts\python.exe" -c "import sys, tkinter, pandas, matplotlib, seaborn, plotly, pyarrow, duckdb, openpyxl, sqlalchemy; raise SystemExit(0 if sys.version_info[:2] == (3, 12) else 1)" >nul 2>nul
    if not errorlevel 1 set "VAP_ENV_READY=1"
)
if defined VAP_ENV_READY (
    ".venv\Scripts\pythonw.exe" "vap_seaborn_stack_ui.py"
) else (
    call "Setup-and-Run-VAP-Seaborn-Stack.cmd"
)
set "EXIT_CODE=%ERRORLEVEL%"
popd
endlocal & exit /b %EXIT_CODE%
