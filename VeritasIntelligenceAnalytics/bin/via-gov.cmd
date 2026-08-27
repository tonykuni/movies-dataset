@echo off
rem 中央治理引擎 CGE v0401:TAB 多頁儀表板+大表分段+設計鎖刊頭(治);dry-run 預設;--commit;--fetch-tw;回退=改指 v0400
rem 鐵律清掃(L6 債冊):寫死版號改 dir /b /o:n 動態解析,最新版自動接任
if not defined VMT_ROOT set VMT_ROOT=C:\VIA\VeritasMailTracker
setlocal
for /f "delims=" %%f in ('dir /b /o:n "%~dp0..\supportive modules\VIA_Central_Governance\CGC_MDL001_CentralGovernanceEngine_v0*.py"') do set "EG=%%f"
py "%~dp0..\supportive modules\VIA_Central_Governance\%EG%" --workdir "%VMT_ROOT%" %*
endlocal
