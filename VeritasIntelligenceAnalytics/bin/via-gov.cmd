@echo off
rem 中央治理引擎 CGE v0400:同義字/regex SSOT 生命週期(dry-run 預設;--commit 落地;--fetch-tw 台股三代號;--import-curated/--import-matrix)
if not defined VMT_ROOT set VMT_ROOT=C:\VIA\VeritasMailTracker
py "%~dp0..\supportive modules\VIA_Central_Governance\VIA_CentralGovernanceEngine_v0400.py" --workdir "%VMT_ROOT%" %*
