@echo off
rem SSOT 自動演化引擎 — 真實資料掃候選碼寫提案版(凍結正本零觸碰;動態解析最新版)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\via_ssot_evolve_v0*.py"') do set "S_ENG=%%f"
if not defined S_ENG (
  echo [FAIL] 演化引擎不在位 — via-sync 後重試
  exit /b 1
)
py "%~dp0..\supportive modules\registry\%S_ENG%" %*
endlocal
