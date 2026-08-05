@echo off
rem VRN 內容級擷取 Stage-0 可行性探測(唯讀,不寫 SSOT):via-probe [PDF資料夾] [--limit N]
py "%~dp0..\functional modules\VRN\vrn_content_probe_v0100.py" %*
