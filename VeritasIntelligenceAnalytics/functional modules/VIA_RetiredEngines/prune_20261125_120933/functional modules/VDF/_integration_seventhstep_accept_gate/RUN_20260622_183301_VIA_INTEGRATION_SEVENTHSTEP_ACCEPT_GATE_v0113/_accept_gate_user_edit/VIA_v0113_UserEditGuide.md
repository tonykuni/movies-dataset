# VIA v0113 Accept Gate User Edit Guide

目前狀態：
- Direct Contract Smoke 已可通過。
- P0/P1 仍等待人工接受。
- 不可直接 canonical merge。
- 不可改 source。

你要手動編輯兩個 CSV：

1. P0：
C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_seventhstep_accept_gate\RUN_20260622_183301_VIA_INTEGRATION_SEVENTHSTEP_ACCEPT_GATE_v0113\_accept_gate_user_edit\VIA_v0113_USER_EDIT_P0_AcceptGate.csv

需要填：
- def_user_accept = YES 或 NO
- def_selected_canonical_value = 選定值
- def_reject_reason = 若 NO，填原因

2. P1：
C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_seventhstep_accept_gate\RUN_20260622_183301_VIA_INTEGRATION_SEVENTHSTEP_ACCEPT_GATE_v0113\_accept_gate_user_edit\VIA_v0113_USER_EDIT_P1_PathAlias_AcceptGate.csv

需要填：
- def_user_accept = YES 或 NO
- def_selected_alias_value = 選定 alias/path
- def_reject_reason = 若 NO，填原因

只有 P0 與 P1 全部 YES，v0114 才允許生成 sandbox patch candidate。
