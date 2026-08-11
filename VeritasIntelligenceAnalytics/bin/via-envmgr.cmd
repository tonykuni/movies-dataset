@echo off
rem 中央環境治理 EnvManager 閘道 — 零分支:一律交 Python 路由器(動態解析最新版;層層印橫幅可稽核)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\via_envmgr_router_v0*.py"') do set "RT=%%f"
py "%~dp0..\supportive modules\registry\%RT%" %*
endlocal
