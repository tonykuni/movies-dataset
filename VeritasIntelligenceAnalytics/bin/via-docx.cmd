@echo off
rem DOCX 深度解析引擎(文字+表格 擷取-修復-驗證對照)— 動態解析最新版(鐵律)
rem 用法:via-docx "*.docx"  或  via-docx --compare old.docx new.docx
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VRN\vrn_docx_engine_v0*.py"') do set "DX=%%f"
py "%~dp0..\functional modules\VRN\%DX%" %*
endlocal
