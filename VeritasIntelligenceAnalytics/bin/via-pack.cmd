@echo off
rem 子系統獨立打包器 v0102:產品號+單機綁定+封面U/I;Launch 參數 PS 陣列(引號/空白路徑安全);回退=改指 via_pack_engine_v0101.py
py "%~dp0..\supportive modules\VIA_Governance_Runtime\via_pack_engine_v0102.py" %*
