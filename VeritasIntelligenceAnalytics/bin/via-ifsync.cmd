@echo off
rem 介面自湊引擎(TOOL-089):模組對模組 mapping/connecting/syncing/test-debug/activate;--libs 庫冊;--failures 25 失效矩陣 — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\via_iface_autosync_v0*.py"') do set "IF=%%f"
py "%~dp0..\supportive modules\registry\%IF%" %*
endlocal
