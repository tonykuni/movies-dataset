@echo off
chcp 65001 >nul
rem VTR 會議紀錄修復引擎轉發器 — 子系統正本在 functional modules\WorkOps\VTR
rem 用法:via-vtr            → All 全套驗證 Doctor+Lexicon+Test+Manifest
rem       via-vtr Doctor / Lexicon / Test / Manifest / Restore -Path 檔或夾 / Inspect / Replay -ToRev n
where pwsh >nul 2>nul
if %errorlevel%==0 (
  pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\WorkOps\VTR\Invoke-VTR.ps1" %*
) else (
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\WorkOps\VTR\Invoke-VTR.ps1" %*
)
