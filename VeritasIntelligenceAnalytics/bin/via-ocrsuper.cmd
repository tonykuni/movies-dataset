@echo off
rem OCR 超引擎(輕先重後階梯:RapidOCR/ONNX→Tesseract→PaddleOCR→Surya;隔離境探測/辨識/認知抽取/安裝計畫;零安裝)— 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\registry\via_ocr_super_v0*.py"') do set "OS=%%f"
py "%~dp0..\supportive modules\registry\%OS%" %*
endlocal
