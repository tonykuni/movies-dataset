@echo off
rem VIA Note Pro 單機筆記(FNT-001)— 雙擊即用;全資料在瀏覽器 localStorage;零網路零安裝零伺服器
rem 動態解析鐵律:自動取最新版 VIA_Note_Pro_Standalone*.html(嚴禁寫死版號);正本在 VAP spec UIUX_Design_Source
set "VIA_NOTE="
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VAP\spec\UIUX_Design_Source\VIA_Note_Pro_Standalone*.html" 2^>nul') do set "VIA_NOTE=%%f"
if not defined VIA_NOTE (
  echo [FAIL] 找不到 VIA_Note_Pro_Standalone*.html — 請先 via-sync 取得正本
  exit /b 1
)
echo [via-note] 開啟 %VIA_NOTE%(資料在本機瀏覽器,不外傳)
start "" "%~dp0..\functional modules\VAP\spec\UIUX_Design_Source\%VIA_NOTE%"
