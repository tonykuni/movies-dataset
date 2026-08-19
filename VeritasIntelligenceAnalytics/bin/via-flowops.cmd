@echo off
rem 註冊台維運引擎(TOOL-075):--refresh-equity 個股清單 / --refresh-etf 委派 ENG023 / --holdings 持股攝入 / --coverage AUM流覆蓋稽核
py "%~dp0..\supportive modules\VIA_FlowSystem\FlowSystem_v2\engines\FLOW_ENG024_FlowRegistryOps.py" %*
