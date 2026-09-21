@echo off
rem VCGC — Veritas 中央治理台(VIA 往下的那一扇門;動態解析尾版,嚴禁寫死版號)
rem   status|check|audit|matrix|panorama|register-plan|registry-sync|--selftest
rem   批686:子系統對接口三家一把尺(VRN/VDF/VAP);缺席的家族回 ABSENT 誠實,不假裝有。
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\CGC_MDL149_VeritasCentralGovernanceConsole_v0*.py"') do set "V_ENG=%%f"
if not defined V_ENG (
  echo [FAIL] VCGC 不在位 — via-sync 後重試
  exit /b 1
)
py "%~dp0..\supportive modules\registry\%V_ENG%" %*
endlocal
