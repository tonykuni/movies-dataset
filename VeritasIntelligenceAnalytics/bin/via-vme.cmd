@echo off
rem VME 方法論引擎:InspectOnly 預設;RuntimeAppendOnly 需 -ApproveRuntimeAppend(Python 二次核准);--selftest 八檢
if "%~1"=="--selftest" ( py "%~dp0..\functional modules\VME\engines\vme_main.py" --selftest ) else ( pwsh -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\functional modules\VME\Invoke-VME.ps1" %* )
