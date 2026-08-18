@echo off
rem VRN 輸入矩陣驗證 — 自動導入版:預設=VRN input\incoming(報告已移入即自動掃,免選擇)
rem 解析序:①參數指定 ②input\incoming 有件 ③input\ 有件 ④Windows 資料夾選擇器
rem 動態解析最新版引擎,嚴禁寫死版號
setlocal enabledelayedexpansion
set "VRNROOT=%~dp0..\functional modules\VRN"
set "SRC=%~1"
if not "%SRC%"=="" goto :run
set "CAND=%VRNROOT%\input\incoming"
call :probe && goto :run
set "CAND=%VRNROOT%\input"
call :probe && goto :run
for /f "usebackq delims=" %%p in (`pwsh -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms; $d=New-Object System.Windows.Forms.FolderBrowserDialog; $d.Description='選擇 VRN 輸入資料夾(pdf/csv/json)'; if($d.ShowDialog() -eq 'OK'){$d.SelectedPath}"`) do set "SRC=%%p"
if "%SRC%"=="" (
  echo [FAIL] 預設進件區無檔且未選擇資料夾
  exit /b 2
)
goto :run

:probe
for /f "delims=" %%f in ('dir /b /a-d "%CAND%" 2^>nul') do (
  set "SRC=%CAND%"
  echo [自動導入] %CAND%
  exit /b 0
)
exit /b 1

:run
for /f "delims=" %%f in ('dir /b /o:n "%VRNROOT%\VRN_ENG054_InputMatrixValidator_v0*.py"') do set "V_ENG=%%f"
if not defined V_ENG (
  echo [FAIL] 驗證引擎不在位 — via-sync 後重試
  exit /b 1
)
py "%VRNROOT%\%V_ENG%" "%SRC%"
for /f "delims=" %%h in ('dir /b /o:n "%SRC%\_vrn_intake_out\vrn_input_matrix_*.html" 2^>nul') do set "LAST=%%h"
if defined LAST start "" "%SRC%\_vrn_intake_out\!LAST!"
endlocal
