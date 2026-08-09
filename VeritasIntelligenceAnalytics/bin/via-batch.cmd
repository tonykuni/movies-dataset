@echo off
rem VRN batch: run every incoming PDF through the No-OCR line (resumable; -Fresh to redo all)
pwsh -NoProfile -File "%~dp0..\functional modules\VRN\Invoke-VRN-Batch-AllInOne-v0100.ps1" %*
