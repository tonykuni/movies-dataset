@echo off
setlocal EnableExtensions
rem VIA AzureFlow QA Plug-in scheduled batch example.
rem Edit the four configuration values below before registering this file in Task Scheduler.

set "PLUGIN_ROOT=%~dp0"
set "ROOT=C:\VIA\work\reconstruction"
set "ZIP=C:\VIA\delivery\VIA-All-Latest.zip"
set "CHECKSUM=C:\VIA\delivery\VIA-All-Latest.zip.sha256"
set "OUTPUT_ROOT=%USERPROFILE%\Downloads\VIA_AzureFlow_QA_Scheduled"
set "BASE_URL=http://127.0.0.1:8766"

powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass ^
  -File "%PLUGIN_ROOT%scripts\Invoke-VIA-AzureFlowQA-Scheduled.ps1" ^
  -Action All ^
  -PluginRoot "%PLUGIN_ROOT%" ^
  -Root "%ROOT%" ^
  -Zip "%ZIP%" ^
  -ChecksumFile "%CHECKSUM%" ^
  -BaseUrl "%BASE_URL%" ^
  -PackageKind Auto ^
  -OutputRoot "%OUTPUT_ROOT%" ^
  -NoArtifactProbe

set "RC=%ERRORLEVEL%"
if not "%RC%"=="0" (
  echo VIA AzureFlow QA scheduled run failed. ExitCode=%RC%
) else (
  echo VIA AzureFlow QA scheduled run passed.
)
endlocal & exit /b %RC%
