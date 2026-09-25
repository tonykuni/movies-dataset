@echo off
rem VIA-Start.bat — 桌面雙擊啟動器(批204;真零打字入口)
rem 雙擊=非阻塞跑全鏈+自動開 UI(樞紐/治理矩陣/指揮台)
cd /d "%~dp0"
start "" powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0launch.ps1"
start "" "%~dp0supportive modules\ui_support\VIA_UI_CommandDeck_v0100.html"
exit /b 0
