@echo off
rem =====================================================================
rem via-ppp.cmd - PDFPlumber-Plus 直通梭(批473;Windows 拖曳)
rem =====================================================================
rem 拖一個 PDF 或整個資料夾到本檔圖示上 -> Windows 以 %* 傳真實路徑進來。
rem 為什麼是 .cmd 不是 .ps1:檔案總管**不會**把拖曳路徑傳給 .ps1
rem (拖到 .ps1 上只會用記事本開它);.cmd/.bat 才收得到 %*。
rem 零參數(雙擊)= 跑冊上的收件夾;冊上沒 PDF 就誠實跳,不假裝跑了一批。
rem =====================================================================
setlocal
set "VIA=%~dp0"
set "PSEXE=powershell"
where pwsh >nul 2>nul
if %errorlevel%==0 set "PSEXE=pwsh"

set "PS1="
for /f "delims=" %%f in ('dir /b /o:n "%VIA%Invoke-VIA-PDFPlumberPlus-v*.ps1" 2^>nul') do set "PS1=%VIA%%%f"
if not defined PS1 (
    echo   [FAIL] Invoke-VIA-PDFPlumberPlus-v*.ps1 缺(母倉根^)
    exit /b 2
)

if "%~1"=="" (
    "%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%PS1%"
    set "RC=%errorlevel%"
    echo.
    pause
    exit /b %RC%
)

rem 拖曳進來的:是夾就 -In,是檔就 -Pdf
if exist "%~1\" (
    "%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%PS1%" -In "%~1"
) else (
    "%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%PS1%" -Pdf "%~1"
)
exit /b %errorlevel%
