@echo off
rem VRN batch 統一入口 — 動態解析最新版(鐵律:嚴禁寫死版號)
rem 用法:via-batch            → No-OCR 車道(v0100 行為)
rem       via-batch -OCR       → OCR 重擷取車道(MDL005 文字 + MDL004 表格 + DOCX 解析鏈)
rem       via-batch -OCR -Probe → 只印解析不執行
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VRN\Invoke-VRN-Batch-AllInOne-v0*.ps1"') do set "BT=%%f"
pwsh -NoProfile -File "%~dp0..\functional modules\VRN\%BT%" %*
endlocal
