@echo off
rem SuperDocExtractor — Word/Excel/CSV 擷取+編碼修復+驗證+對照(導入自會話 016d7f;selftest 15/15)
rem 用法:via-sdx selftest · via-sdx extract <檔> · via-sdx compare <舊> <新>
py "%~dp0..\functional modules\SuperDocExtractor\super_extract.py" %*
