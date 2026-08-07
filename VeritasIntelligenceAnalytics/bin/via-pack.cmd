@echo off
rem 子系統獨立打包器 v0103:entry_newest pattern 取最新引擎(升版自動跟進)+產品號+單機綁定+封面U/I;回退=改指 via_pack_engine_v0102.py
py "%~dp0..\supportive modules\VIA_Governance_Runtime\via_pack_engine_v0103.py" %*
