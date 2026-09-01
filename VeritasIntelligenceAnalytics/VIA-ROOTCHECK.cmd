@echo off
rem =====================================================================
rem VIA-ROOTCHECK.cmd - 三胞胎資料夾查究器(批290;操作員令「查究檔案夾」)
rem =====================================================================
rem 批275 裁定:正主根=C:\Users\tonyk\movies-dataset(唯一 git 管控)。
rem 本器逐一體檢三候選夾:在否/是否 git 庫/HEAD/分支/遠端/髒行數/
rem 末次提交——貼回輸出即可裁定封存名單。純 cmd=任何殼直跑。
rem 紀律:只查不動(唯讀;零刪除零改動)。
rem =====================================================================
setlocal enabledelayedexpansion
echo ================= VIA 三胞胎資料夾查究(批290)=================
call :probe "C:\Users\tonyk\movies-dataset"            "正主根(批275 裁定)"
call :probe "C:\Users\tonyk\Downloads\movies-dataset"  "Downloads 分身"
call :probe "C:\Users\tonyk\OneDrive\Documents\movies-dataset" "OneDrive 分身"
echo.
echo --- 埠 8765 佔用(指揮台塔;雙塔同埠=按鈕可能打到錯的塔)---
netstat -ano 2>nul | findstr ":8765" | findstr "LISTENING"
if errorlevel 1 echo 埠 8765:無人佔用(塔未開)
echo.
echo --- $PROFILE 稽核(批295:揪自動起塔鉤子;唯讀傾印)---
powershell -NoProfile -Command "if(Test-Path $PROFILE){Write-Host ('路徑:'+$PROFILE); $i=0; Get-Content $PROFILE | ForEach-Object { $i++; Write-Host ('{0,3}: {1}' -f $i, $_) }}else{Write-Host '無 $PROFILE 檔'}"
echo [判讀] 正常應只有一行 VIA Register 點源;出現 Lane3/ControlTower/
echo        Start-VRN 等他行=分身鉤子(貼回裁定,先不要自行刪)。
echo =================================================================
echo [裁定律] 只有「正主根」可打指令/VIA-ALL;分身若為 git 庫且有
echo          獨有提交=先留痕再封存(把輸出貼回給 Claude 裁定)。
echo [OneDrive 警告] git 庫放 OneDrive 同步夾=檔案鎖/損毀風險,
echo          建議移出同步或封存。
exit /b 0

:probe
set "P=%~1"
echo.
echo --- %~2 ---
echo 路徑:%P%
if not exist "%P%" (
    echo 狀態:不存在
    exit /b 0
)
if not exist "%P%\.git" (
    echo 狀態:存在但「非 git 庫」(純資料夾)
    dir /b "%P%" 2>nul | find /c /v "" > "%TEMP%\viarc.tmp"
    set /p N=<"%TEMP%\viarc.tmp"
    echo 內容物:!N! 項(僅計頂層)
    exit /b 0
)
echo 狀態:git 庫
for /f "delims=" %%h in ('git -C "%P%" rev-parse --short HEAD 2^>nul') do echo HEAD:%%h
for /f "delims=" %%b in ('git -C "%P%" branch --show-current 2^>nul') do echo 分支:%%b
for /f "delims=" %%r in ('git -C "%P%" remote get-url origin 2^>nul') do echo 遠端:%%r
for /f "delims=" %%d in ('git -C "%P%" log -1 --format^=%%ci 2^>nul') do echo 末次提交:%%d
git -C "%P%" status --porcelain 2>nul | find /c /v "" > "%TEMP%\viarc.tmp"
set /p D=<"%TEMP%\viarc.tmp"
echo 髒行:!D!
exit /b 0
