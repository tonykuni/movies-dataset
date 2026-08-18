@echo off
rem VIA OCR 統一路由器 v0100(ENG-026):全平台 OCR/擷取引擎的探測·裁決·薄執行(全本機免費)
rem 用法:via-ocr                → probe 誠實列出各段可用性(fitz/pdfplumber/pdfminer/camelot/paddle/tesseract/surya/檔名錨)
rem       via-ocr route 檔案     → 裁決該檔最佳引擎(正本在 VRN/Forge/PMIS)
rem       via-ocr extract 檔案   → 薄執行:文字層/影像輕 OCR;重 OCR 只路由;末梯檔名錨永不空手
py "%~dp0..\supportive modules\VIA_OCR_Router\SUP_MDL146_OcrRouter.py" %1 %2 %3
