@echo off
rem PDF 法醫探針(唯讀;零輸出檔死因判定)— 動態解析最新版(鐵律)
rem 用法:via-pdfcheck "MQ-1560*"  或  via-pdfcheck --file "C:\path\x.pdf"
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VRN\VRN_ENG056_PdfForensics_v0*.py"') do set "PF=%%f"
py "%~dp0..\functional modules\VRN\%PF%" %*
endlocal
