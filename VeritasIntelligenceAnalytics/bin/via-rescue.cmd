@echo off
rem 純影像掃描件 OCR 救援(fitz 渲染→paddleocr→併回主表)— 動態解析最新版(鐵律)
rem 用法:via-rescue "MQ-1560*"  [--dpi 300] [--dry-run]
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VRN\VRN_ENG057_ScanOcrRescue_v0*.py"') do set "RS=%%f"
py "%~dp0..\functional modules\VRN\%RS%" %*
endlocal
