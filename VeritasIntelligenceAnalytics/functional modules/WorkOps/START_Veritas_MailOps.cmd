@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

rem ==== choose PowerShell (prefer pwsh 7, else Windows PowerShell 5.1) ====
set "PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
where pwsh >nul 2>&1 && set "PS=pwsh.exe"

rem ==== locate components in this folder (defensive: match by pattern) ====
set "SCAN="
for %%F in ("*SubjectClusterSafeLocal*.ps1" "*SubjectCluster*SafeLocal*.ps1") do if exist "%%~F" set "SCAN=%%~F"
set "WIZARD="
for %%F in ("*OutlookWizard*.ps1") do if exist "%%~F" set "WIZARD=%%~F"
set "DRAFTS="
for %%F in ("*TrackingDrafts*.ps1") do if exist "%%~F" set "DRAFTS=%%~F"
set "DASH="
for %%F in ("*MailOps*Standalone*.html" "*Standalone*.html") do if exist "%%~F" set "DASH=%%~F"

set "RUNS=%USERPROFILE%\Desktop\Veritas_MailOps_Subject_Cluster\_runs"

:menu
cls
echo ============================================================
echo   Veritas MailOps - 一鍵工作台 (你自己權限 / 只讀 / 不自動寄)
echo ============================================================
echo   [1] 掃描信箱並匯出 JSON   (只讀 SafeLocal)
echo   [2] 開啟 Dashboard        (載入 JSON: 看板/應追蹤清單/簡報)
echo   [3] 建立追蹤信草稿        (Initial - 含選擇題,供你檢視後寄)
echo   [4] 補追殺草稿            (FollowUp - 再次追蹤語氣)
echo   [5] 一鍵依序: 掃描 -^> 開結果資料夾 -^> 開 Dashboard
echo   [0] 離開
echo ============================================================
if not defined SCAN  echo   ^(注意: 找不到 SafeLocal 掃描腳本,[1]/[5] 會略過^)
if not defined DASH  echo   ^(注意: 找不到 Dashboard HTML,[2]/[5] 會略過^)
if not defined DRAFTS echo   ^(注意: 找不到追蹤信腳本,[3]/[4] 會略過^)
echo.
set "c="
set /p "c=請輸入編號後按 Enter: "

if "%c%"=="1" goto scan
if "%c%"=="2" goto dash
if "%c%"=="3" goto drafts_initial
if "%c%"=="4" goto drafts_followup
if "%c%"=="5" goto runall
if "%c%"=="0" goto end
goto menu

:scan
if not defined SCAN ( echo 找不到 SafeLocal 掃描腳本。& pause & goto menu )
echo.
echo 執行只讀掃描: %SCAN%
"%PS%" -NoProfile -ExecutionPolicy Bypass -STA -File "%~dp0%SCAN%"
echo.
pause
goto menu

:dash
if not defined DASH ( echo 找不到 Dashboard HTML。& pause & goto menu )
start "" "%~dp0%DASH%"
goto menu

:drafts_initial
if not defined DRAFTS ( echo 找不到追蹤信腳本。& pause & goto menu )
"%PS%" -NoProfile -ExecutionPolicy Bypass -STA -File "%~dp0%DRAFTS%" -Mode Initial
echo.
pause
goto menu

:drafts_followup
if not defined DRAFTS ( echo 找不到追蹤信腳本。& pause & goto menu )
"%PS%" -NoProfile -ExecutionPolicy Bypass -STA -File "%~dp0%DRAFTS%" -Mode FollowUp
echo.
pause
goto menu

:runall
if defined SCAN (
    echo [1/3] 只讀掃描...
    "%PS%" -NoProfile -ExecutionPolicy Bypass -STA -File "%~dp0%SCAN%"
)
echo [2/3] 開啟結果資料夾...
if exist "%RUNS%" ( start "" explorer "%RUNS%" ) else ( echo   ^(尚無 _runs 資料夾,略^) )
echo [3/3] 開啟 Dashboard...
if defined DASH ( start "" "%~dp0%DASH%" )
echo.
echo 完成。請把結果資料夾裡最新 RUN_... 的 *.json 拖進 Dashboard 的「載入本機匯出」。
echo ^(瀏覽器安全限制:本機網頁無法自動讀取硬碟檔,故需這一次拖放。^)
pause
goto menu

:end
endlocal
