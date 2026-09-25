@echo off
rem 統包唯一網路工具(TOOL-080):爬蟲雙引擎包+SuperAccel 統包一口;法遵雙閘 fail-closed(VIA_NET_CONSENT+VIA_SCRAPE_CONSENT)— 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\network\via_net_unified_v0*.py"') do set "VN=%%f"
py "%~dp0..\supportive modules\network\%VN%" %*
endlocal
