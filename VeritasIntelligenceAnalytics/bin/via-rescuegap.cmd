@echo off
rem 表格缺口多方案總攻:讀主表找「有字零表」→逐檔驅動 digital→img2table→ppstructure/SDX→office 橋,終局四態裁決 — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VRN\VRN_ENG059_GapMultirescue_v0*.py"') do set "GR=%%f"
py "%~dp0..\functional modules\VRN\%GR%" %*
endlocal
