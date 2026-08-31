@echo off
rem W0 凍結+T0 身份稽核(AUDIT ONLY 100%% 唯讀:基線快照+核心資源雜湊集+Root 仲裁證據+裁決存證)— 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\CGC_MDL070_T0Audit_v0*.py"') do set "T0=%%f"
py "%~dp0..\supportive modules\registry\%T0%" %*
endlocal
