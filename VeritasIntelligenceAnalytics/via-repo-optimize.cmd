@echo off
rem via-repo-optimize.cmd - repo 衛生一鍵梭(批325):跑 Invoke-VIA-RepoOptimizer 尾版(只宜工作站)
setlocal
set "VIA=%~dp0"
set "PSEXE=powershell"
where pwsh >nul 2>nul
if %errorlevel%==0 set "PSEXE=pwsh"
for /f "delims=" %%f in ('dir /b /o:n "%VIA%Invoke-VIA-RepoOptimizer-v*.ps1"') do set "PS1=%VIA%%%f"
if not defined PS1 ( echo [via-repo-optimize] FAIL: Invoke-VIA-RepoOptimizer-v*.ps1 缺 & exit /b 2 )
%PSEXE% -NoProfile -ExecutionPolicy Bypass -File "%PS1%" %*
exit /b %errorlevel%
