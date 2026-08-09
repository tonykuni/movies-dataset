@echo off
rem 公定處理模式 v0108:三輪全景 14 域 + 巢狀 git repo 圍堵(自帶 .git 之子目錄=外來 clone,整棵跳過);回退=改指 via_mega_engine_v0108.py
py "%~dp0..\supportive modules\VIA_Governance_Runtime\via_mega_engine_v0109.py" %*
