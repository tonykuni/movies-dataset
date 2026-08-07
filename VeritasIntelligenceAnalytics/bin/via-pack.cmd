@echo off
rem 子系統獨立打包器 v0100:via-pack <cge^|mega^|bridge^|audit^|flow^|if^|vmt^|tools> — 產品號(AutoCoder PKG 序號+內容SHA8)+ 單機綁定(NODE_LOCKED_1_HOST)+ SHA256 manifest + zip(run-local)
py "%~dp0..\supportive modules\VIA_Governance_Runtime\via_pack_engine_v0100.py" %*
