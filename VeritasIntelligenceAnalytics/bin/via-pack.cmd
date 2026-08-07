@echo off
rem 子系統獨立打包器 v0101:產品號+單機綁定+每包自帶 Porcelain 封面 U/I(index.html,Launch 跑完自動開);回退=改指 via_pack_engine_v0100.py
py "%~dp0..\supportive modules\VIA_Governance_Runtime\via_pack_engine_v0101.py" %*
