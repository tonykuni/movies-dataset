@echo off
rem v0160C 一般瀏覽器 HTML U/I(本機 HTTP 橋) · 回退: v0102=HTA 設計鎖刊頭 / v0101=v0160A 原版
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\VDF\Start-VIA-VDF-v0103.ps1" %*
