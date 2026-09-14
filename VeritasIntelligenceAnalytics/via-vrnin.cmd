@echo off
rem =====================================================================
rem via-vrnin.cmd - VRN 輸入直通梭(批465;Windows I/O + 拖曳)
rem =====================================================================
rem 操作員令:「輸入介面不再有特定系統內指定位置,改為一律 WINDOWS I/O
rem 或拖曳式輸入,搜尋檔案夾中的 WORD PDF IMAGE 檔案」。
rem
rem 三種用法,都不必記路徑:
rem   ① 把檔或整個資料夾**拖到本檔圖示上** -> Windows 以 %* 傳真實路徑進來
rem   ② 直接雙擊本檔(零參數)             -> 開原生選檔對話框(可多選)
rem   ③ 殼裡打 via-vrnin -Pick Folder       -> 開原生選夾對話框
rem
rem 為什麼是 .cmd 而不是 .ps1:Windows 檔案總管**不會**把拖曳的路徑傳給
rem .ps1(拖到 .ps1 上只會用記事本開它);.cmd/.bat 才收得到 %*。
rem 機制:pwsh 優先(缺退 powershell)-> 跑 VIA_WinIO_InputPicker 尾版。
rem 參數直通:-Pick File|Folder / -ListOnly / -NoIncoming / -Open / -TimeoutSec
rem =====================================================================
setlocal
set "VIA=%~dp0"
set "PSEXE=powershell"
where pwsh >nul 2>nul
if %errorlevel%==0 set "PSEXE=pwsh"

set "PS1="
for /f "delims=" %%f in ('dir /b /o:n "%VIA%supportive modules\VIA_WinIO_InputPicker_v*.ps1" 2^>nul') do set "PS1=%VIA%supportive modules\%%f"
if not defined PS1 (
    echo   [FAIL] VIA_WinIO_InputPicker_v*.ps1 缺(supportive modules^)
    exit /b 2
)

rem 零參數=雙擊進來的:直接開原生選檔對話框,不要讓他對著空白畫面猜
if "%~1"=="" (
    "%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%PS1%" -Pick File
    set "RC=%errorlevel%"
    echo.
    pause
    exit /b %RC%
)

rem 有參數=拖曳進來的真實路徑,或殼裡打的旗標;一律原樣直通
"%PSEXE%" -NoProfile -ExecutionPolicy Bypass -File "%PS1%" %*
exit /b %errorlevel%
