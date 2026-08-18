@echo off
rem 引擎總目錄:352 支逐引擎詳細功能(AST 實值零發明)→ JSON+MD+U/I 檢索板 — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\via_engine_catalog_v0*.py"') do set "EC=%%f"
py "%~dp0..\supportive modules\registry\%EC%" %*
endlocal
