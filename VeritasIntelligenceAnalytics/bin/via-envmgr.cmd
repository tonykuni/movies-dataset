@echo off
rem 中央環境治理 EnvManager — 安裝衝突治理閘道(正本唯讀呼叫;預設=conflicts)
rem 用法:via-envmgr [conflicts^|scan^|rebuild-candidates^|plan-install 套件 [版本] [環境]^|execute-install ...^|export-plan^|selftest]
rem Gatekeeper:base 擋 MEDIUM/HIGH 風險;via_core 白名單;新工具先過 EnvManager
setlocal
set "ARGS=%*"
if "%ARGS%"=="" set "ARGS=conflicts"
py "%~dp0..\supportive modules\VIA_EnvManager.py" %ARGS%
endlocal
