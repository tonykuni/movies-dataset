@echo off
rem 公定處理模式 v0105:三輪全景 x Porcelain Matrix + 參數置頂/附掛/parquet增量(DuckDB)/rich摘要;hydra 僅平台域(附掛部署副本=資訊項);回退=改指 via_mega_engine_v0104.py
py "%~dp0..\supportive modules\VIA_Governance_Runtime\via_mega_engine_v0105.py" %*
