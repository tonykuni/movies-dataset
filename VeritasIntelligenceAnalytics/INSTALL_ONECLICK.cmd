@echo off
chcp 65001 >nul
rem Veritas WorkOps 一鍵部署入口 — 新電腦只需內建 PowerShell 5.1,雙擊本檔即可
rem 全自動:pwsh7可攜+Python3.12+venv+graphviz+PATH+每日排程+全鏈自測;絕不代寄
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-VeritasWorkOps-OneClick.ps1" %*
pause
