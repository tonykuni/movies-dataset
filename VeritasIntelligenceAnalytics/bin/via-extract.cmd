@echo off
rem VRN 內容級擷取 CANDIDATE(DRY-RUN 專用,不寫 SSOT;--commit 被啟用記錄閘門擋下):via-extract [PDF資料夾] [--limit N]
py "%~dp0..\functional modules\VRN\vrn_content_extract_candidate_v0100.py" %*
