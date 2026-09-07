@echo off
rem =====================================================================
rem via-autorun.cmd - VIA 一鍵全自動(批379;雙擊即可;VIA-Verb-Shim v0100)
rem =====================================================================
rem 操作員令「自動完成所有動作 不要打開 VS Code 我不知道要怎麼辦」:
rem 雙擊本檔=拉齊→六流程→十道並行補齊→四專案矩陣→產品閘;全程零跳出;
rem 結束停窗(看完按任意鍵關)。在 cmd 內打 via-autorun 同效(不停窗)。
rem 機制:pwsh 優先(缺退 powershell)->點源 Register 尾版->呼同名函式。
rem =====================================================================
setlocal
set "VIA=%~dp0"
set "VIA_NO_OPEN=1"
set "GIT_EDITOR=true"
set "GIT_MERGE_AUTOEDIT=no"
set "PSEXE=powershell"
where pwsh >nul 2>nul
if %errorlevel%==0 set "PSEXE=pwsh"
%PSEXE% -NoProfile -ExecutionPolicy Bypass -Command "$r=Get-ChildItem -LiteralPath '%VIA%.' -Filter 'Register-VIA-Commands-v*.ps1' | Sort-Object Name | Select-Object -Last 1; . $r.FullName; & '%~n0'" %*
set "RC=%errorlevel%"
echo.
echo [via-autorun] 畢(rc=%RC%);看頁請打 via-open 產品
echo %cmdcmdline% | find /i "/c" >nul && pause
exit /b %RC%
