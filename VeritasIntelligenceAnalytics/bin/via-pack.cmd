@echo off
rem 子系統獨立打包器 v0103:entry_newest pattern 取最新引擎(升版自動跟進)+產品號+單機綁定+封面U/I;回退=改指 via_pack_engine_v0102.py
rem 鐵律清掃(L6 債冊):寫死版號改 dir /b /o:n 動態解析,最新版自動接任
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\VIA_Governance_Runtime\via_pack_engine_v0*.py"') do set "EG=%%f"
py "%~dp0..\supportive modules\VIA_Governance_Runtime\%EG%" %*
endlocal
