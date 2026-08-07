@echo off
rem Command Bridge v0100:一鍵前後端對接(後端 B1-B5 探測 + test/debug 三輪 + 多 TAB 狀態矩陣首頁 UI;run-local)
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\Invoke-VIA-Bridge-v0100.ps1" %*
