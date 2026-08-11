@echo off
rem 中央環境治理 EnvManager — 安裝衝突治理閘道(正本唯讀;conflicts/scan 走 NoStall 加速器 20 工作器+動態進度條)
rem 用法:via-envmgr [conflicts^|scan]([--workers 20] [--task-timeout 150])
rem      via-envmgr plan-install 套件 [版本] [環境] ^| execute-install ... ^| rebuild-candidates ^| export-plan ^| selftest
rem Gatekeeper:base 擋 MEDIUM/HIGH 風險;via_core 白名單;新工具先過 EnvManager
setlocal
set "CMD=%~1"
if "%CMD%"=="" set "CMD=conflicts"
if /i "%CMD%"=="conflicts" goto :nostall
if /i "%CMD%"=="scan" goto :nostall
py "%~dp0..\supportive modules\VIA_EnvManager.py" %*
goto :eof
:nostall
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\via_envmgr_nostall_v0*.py"') do set "NS_ENG=%%f"
if not defined NS_ENG (
  echo [WARN] NoStall 包覆器不在位 — 回退正本直呼(可能久跑無輸出)
  py "%~dp0..\supportive modules\VIA_EnvManager.py" %*
  goto :eof
)
py "%~dp0..\supportive modules\registry\%NS_ENG%" %*
