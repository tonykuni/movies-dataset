@echo off
chcp 65001 >nul
title PMIS-Lite 一鍵執行
echo ============================================
echo   PMIS-Lite 工作進度自動彙整 (本機處理)
echo   僅讀取你有權限的資料,不外傳,不勞動 IT
echo ============================================
echo.

REM 找 Python（py 啟動器優先）
where py >nul 2>nul && (set PY=py) || (set PY=python)

REM 第一次自動裝套件（只裝在使用者範圍,不需系統管理員）
echo [1/2] 檢查並安裝必要套件...
%PY% -m pip install --user -q -r requirements.txt

echo [2/2] 開始自動偵測與彙整...
%PY% run_auto.py

echo.
echo 完成。結果頁已自動開啟;若未開,請見 ssot_store 資料夾。
pause
