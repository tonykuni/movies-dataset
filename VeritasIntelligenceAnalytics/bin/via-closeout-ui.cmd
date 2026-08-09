@echo off
rem 五系統收官總覽 U/I(單檔離線)— 動態解析最新版,嚴禁寫死版號
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\ui_support\VIA_Grand_Closeout_UI_v0*.html"') do set "VIA_GCUI=%%f"
start "" "%~dp0..\supportive modules\ui_support\%VIA_GCUI%"
