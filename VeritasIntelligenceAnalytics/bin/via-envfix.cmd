@echo off
rem EnvManager 決策式無衝突安裝 v0100:五依賴(duckdb/rich/scipy/numpy/pandas)+ NumPy 黃金律 + pip check 後驗(run-local 留痕)
pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\Invoke-VIA-EnvFix-v0100.ps1" %*
