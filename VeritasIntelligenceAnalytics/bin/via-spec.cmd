@echo off
rem VIA Spec — 母版最後一頁全系統規格總覽生成(canon SSOT 動態彙整;零手寫數字)
rem 用法:via-spec(動態解析最新版;產物 VIA_Reports\VIA_Spec_Master_LastPage.html)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\build_spec_master_v0*.py"') do set "SPEC=%%f"
if not defined SPEC (
  echo [FAIL] 規格生成器不在位 — via-sync 後重試
  exit /b 1
)
py "%~dp0..\supportive modules\registry\%SPEC%" %*
endlocal
