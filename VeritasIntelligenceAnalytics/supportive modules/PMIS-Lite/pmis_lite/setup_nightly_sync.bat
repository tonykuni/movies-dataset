@echo off
REM VIS Workbench 背景靜默同步 - 註冊每晚 23:30 自動增量讀信 + 跑 SSOT
REM 雙擊執行一次即完成註冊；之後每晚自動跑，早上打開就是最新。
cd /d "%~dp0"
set TASK=VISWorkbench_NightlySync
schtasks /Create /TN "%TASK%" /TR "python \"%~dp0fetch_mailbox.py\" --since-last --pipeline" /SC DAILY /ST 23:30 /F
if errorlevel 1 (
  echo [失敗] 註冊排程失敗，請以系統管理員身分執行本檔。
) else (
  echo [完成] 已註冊每晚 23:30 自動增量同步。可在「工作排程器」看到 %TASK%。
  echo 移除：schtasks /Delete /TN "%TASK%" /F
)
pause
