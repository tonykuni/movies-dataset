@echo off
rem VIA 母頁一鍵 — 重生母頁(矩陣資料最新)後開啟(動態解析最新版產生器,嚴禁寫死版號)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\build_via_mother_v0*.py"') do set "M_ENG=%%f"
if not defined M_ENG (
  echo [FAIL] 母頁產生器不在位 — via-sync 後重試
  exit /b 1
)
py "%~dp0..\supportive modules\registry\%M_ENG%"
start "" "%~dp0..\VIA_Mother.html"
endlocal
