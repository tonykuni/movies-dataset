@echo off
REM VIS Workbench 郵箱自動擷取 - 雙擊即跑（用這台電腦記住的設定）
cd /d "%~dp0"
python fetch_mailbox.py
if errorlevel 1 pause
