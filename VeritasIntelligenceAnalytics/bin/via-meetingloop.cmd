@echo off
chcp 65001 >nul
rem MeetingLoop 會議循環引擎轉發 — 動態解析最新版(嚴禁寫死版號);DraftOnly 絕不代寄
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\WorkOps\MeetingLoop\Start-VIA-MeetingLoop-v0*.ps1"') do set "VIA_ML=%%f"
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\WorkOps\MeetingLoop\%VIA_ML%" %*
