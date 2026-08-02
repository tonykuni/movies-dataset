@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo ============================================================
echo   VIS Workbench  一鍵讀取信箱
echo   桌機版 Outlook 免登入，直接以您本機身分讀取
echo ============================================================
echo.
echo 正在讀取並整理您的信箱，請稍候...
echo.

py -3.12 fetch_mailbox.py auto --pipeline 2>nul
if %errorlevel%==0 goto done
py -3.11 fetch_mailbox.py auto --pipeline 2>nul
if %errorlevel%==0 goto done
python fetch_mailbox.py auto --pipeline
if %errorlevel%==0 goto done

echo.
echo 似乎有問題。請確認：
echo   1. 已安裝 Python（python.org 下載，安裝時勾選 Add to PATH）
echo   2. 若要免登入直讀，請安裝並登入 Outlook 桌機版
echo   3. 首次用網頁版 Outlook / Gmail 需授權一次（見「門外漢說明」）
echo.
pause
goto end

:done
echo.
echo 完成！已產生摘要報告並開啟。
echo （報告位置：VIA_RUNS\mailbox\mail_summary.html）
echo.
timeout /t 3 >nul

:end
