@echo off
rem VRN 輸入矩陣驗證 — 資料夾式輸入(無參數=Windows 資料夾選擇器;動態解析最新版,嚴禁寫死版號)
setlocal
set "SRC=%~1"
if "%SRC%"=="" (
  for /f "usebackq delims=" %%p in (`pwsh -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $d=New-Object System.Windows.Forms.FolderBrowserDialog; $d.Description='選擇 VRN 輸入資料夾(csv/json)'; if($d.ShowDialog() -eq 'OK'){$d.SelectedPath}"`) do set "SRC=%%p"
)
if "%SRC%"=="" (
  echo [FAIL] 未選擇資料夾
  exit /b 2
)
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VRN\vrn_input_matrix_validator_v0*.py"') do set "V_ENG=%%f"
if not defined V_ENG (
  echo [FAIL] 驗證引擎不在位 — via-sync 後重試
  exit /b 1
)
py "%~dp0..\functional modules\VRN\%V_ENG%" "%SRC%"
for /f "delims=" %%h in ('dir /b /o:n "%SRC%\_vrn_intake_out\vrn_input_matrix_*.html" 2^>nul') do set "LAST=%%h"
if defined LAST start "" "%SRC%\_vrn_intake_out\%LAST%"
endlocal
