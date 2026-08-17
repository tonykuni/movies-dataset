@echo off
rem 文字統包引擎:10 本地車道+5 名錄(pymupdf blocks/docx 頁首尾/openpyxl 串流/pptx/markitdown/pandoc/tika/textract/tesseract/SDX)+zip炸彈/加密/亂碼三閘 — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VRN\vrn_text_omni_v0*.py"') do set "TX=%%f"
py "%~dp0..\functional modules\VRN\%TX%" %*
endlocal
