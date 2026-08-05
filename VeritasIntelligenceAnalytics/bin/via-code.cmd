@echo off
rem 自動識別編號器(全域編碼註冊中心):via-code <類別> <元件名> [suffix] / via-code --list / via-code --register <類別> <前綴> [padding]
py "%~dp0..\supportive modules\registry\via_autocoder_engine_v0100.py" %*
