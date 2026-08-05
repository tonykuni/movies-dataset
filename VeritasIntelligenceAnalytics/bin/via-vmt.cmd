@echo off
rem v0101 = via_master_engine + Veritas 設計鎖刊頭(邏輯同 v1.0);回退=改指 via_master_engine.py
py "%~dp0..\supportive modules\VMT_SuperBOM\via_master_engine_v0101.py" %*
