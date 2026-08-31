@echo off
rem 個股報告摘要批跑器(TOOL-070):逐報告一標題五點摘要(Summarizer 統包)+填充語〔自動生成〕標註+矩陣 U/I — 動態解析最新版(鐵律)
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\functional modules\VRN\vrn_report_digest_v0*.py"') do set "RD=%%f"
py "%~dp0..\functional modules\VRN\%RD%" %*
endlocal
