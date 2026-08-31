@echo off
rem SSD 資源守衛:TEMP 自清(僅本引擎標記)/SQLite 低DRAM盤點/分級指紋/嚴格副本隔離/CPU-DRAM-SSD Gate 後才放行高負載工具 — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\SUP_MDL738_InvokeVIASSDResourceGuard_v0*.py"') do set "SG=%%f"
py "%~dp0..\supportive modules\%SG%" %*
endlocal
