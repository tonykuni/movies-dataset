@echo off
rem VRN 內容級擷取 v0101 ACTIVE(啟用交易 2026-08-05):dry-run 預設;--commit 落地 append-only store;回退=改指 candidate
py "%~dp0..\functional modules\VRN\vrn_content_extract_v0101.py" %*
