@echo off
rem VDF 輸出樞紐:統一輸入參數 SSOT+六格式輸出(parquet/csv/duckdb/sqlite/sql/gsheet相容)+讀回驗證+逐格式×逐表矩陣摘要 — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VDF\vdf_output_hub_v0*.py"') do set "VH=%%f"
py "%~dp0..\functional modules\VDF\%VH%" %*
endlocal
