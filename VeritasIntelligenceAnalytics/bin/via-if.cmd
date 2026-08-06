@echo off
rem VIA-IF 產業預測 P1 整合引擎 v0100:唯讀掃描+append-only 輸出(--selftest 自檢;輸出進 VIA_Reports\if_out)
py "%~dp0..\supportive modules\VIA_IF_Engine\via_if_engine.py" --base "%~dp0.." --output-root "%~dp0..\VIA_Reports\if_out" %*
