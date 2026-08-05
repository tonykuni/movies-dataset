@echo off
rem 中央治理引擎 CGE v0401:TAB 多頁儀表板+大表分段+設計鎖刊頭(治);dry-run 預設;--commit;--fetch-tw;回退=改指 v0400
if not defined VMT_ROOT set VMT_ROOT=C:\VIA\VeritasMailTracker
py "%~dp0..\supportive modules\VIA_Central_Governance\VIA_CentralGovernanceEngine_v0401.py" --workdir "%VMT_ROOT%" %*
