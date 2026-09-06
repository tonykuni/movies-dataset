@echo off
rem =====================================================================
rem VIA-TOWER-RESET.cmd - 指揮台殭屍塔清場器(批296;10 塔佔埠實錄)
rem =====================================================================
rem 實錄:netstat 見埠 8765 有 10 個 LISTENING=歷來非阻塞塔累積未關;
rem 總控台按鈕隨機打到其一=行為錯亂。本器=只清塔不動檔(唯讀於檔案):
rem   ①列出佔 8765 之 PID  ②逐一 taskkill(僅殺佔埠進程,不碰他物)
rem   ③重起「正主」單一乾淨塔(deck 尾版 serve;背景)  ④覆核只剩 1 座
rem 純 cmd=任何殼直跑;絕對路徑版=人在哪都通。
rem =====================================================================
setlocal enabledelayedexpansion
set "VIA=%~dp0"
echo ============ VIA 指揮台清場(批296)============
echo [1/4] 掃描佔埠 8765 之塔...
set "N=0"
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8765" ^| findstr "LISTENING"') do (
    set /a N+=1
    echo   殺塔 PID %%p
    taskkill /F /PID %%p >nul 2>nul
)
echo [1/4] 清除 !N! 座殭屍塔
echo [2/4] 等待埠釋放...
ping -n 3 127.0.0.1 >nul
echo [3/4] 重起正主單一乾淨塔(背景非阻塞)...
set "DECK="
for /f "delims=" %%f in ('dir /b /o:n "%VIA%supportive modules\registry\CGC_MDL095_DeckServer_v*.py" 2^>nul') do set "DECK=%VIA%supportive modules\registry\%%f"
if defined DECK (
    start "VIA-Tower" /min python "!DECK!" serve
    echo   起塔:!DECK!
) else (
    echo   [誠實] deck 尾版缺=先跑 VIA-ALL 同步
)
ping -n 3 127.0.0.1 >nul
echo [4/4] 覆核佔埠(應僅 1 座)...
netstat -ano | findstr ":8765" | findstr "LISTENING"
echo ================================================
echo [完成] 只剩 1 座=總控台按鈕即打到正主塔。
echo [提醒] banner 每次開視窗自動出現?=Windows Terminal 設定或
echo        「開機啟動」夾有分身啟動器;$PROFILE 已證無鉤子。
exit /b 0
