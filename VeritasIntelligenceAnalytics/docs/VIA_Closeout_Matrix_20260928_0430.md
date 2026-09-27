# VIA Closeout Matrix 20260928_0430

側線 2026-09-28 · 分支 claude/vcgc-vrn-read-forward · HEAD 4f0d4cdb · 成果鎖 VIA_VCGC_CloseoutLock_v0100.json

| 區 | 件 | 燈 | 證據 |
|---|---|---|---|
| VCGC | 成果鎖/台帳/掉球 落冊 | GREEN | [紀錄] 成果鎖 · SuccessLedger · 台帳 0 · 收容PS +0 · 掉球 Z218-Z222 |
| VCGC | SuccessLedger check | RED | rc=2 "lock_success": false, |
| VCGC | PS 模板章 接上 0 支 · 解析錯還原 0 | GREEN | Parser::ParseFile 逐支驗 |
| VCGC | VCGC v0161 --selftest | GREEN | rc=0  |
| VCGC | StepMatrix v0100 --selftest | GREEN | rc=0  |
| VCGC | TALibLock (L50) | GREEN | rc=0 "talib": "GREEN", |
| VCGC | 產出契約閘 [PY] | INFO | [PY ] 掃描面 3068 · 帶橋 2962 (96.5%) · 凍結夾具名豁免 4 · 自家族排除 1(LL133)· 正典唯讀本 11 · 缺 91 |
| VCGC | 產出契約閘 [PS] | GREEN | [PS ] 掃描面 943 · 帶模板章 99 · 既有債 843(L70:操作員的手) · 自指豁免 1 · **基線外新缺 0** |
| VCGC | 閘自測(預期 OK 7 · FAIL 1) | GREEN | [計] 8 檢 OK 7 · FAIL 1 |
| VCGC | layout 登冊 乾跑 | INFO | "new": 0,  "changed": 0,  "stale": 0 |
| VCGC | layout 登冊 --apply | INFO | "state": "APPLIED",  "new": 0,  "changed": 0, |
| VCGC | layout 登冊 複驗(應 0/0/0) | GREEN | "new": 0,  "changed": 0,  "stale": 0 |
| VCGC | layout --selftest | GREEN | rc=0 |
| VCGC | layout --manifest | GREEN | "modules": {   "capabilities": [   "errors": [], |
| VRN | layout 批跑 C:\測試樣本報告 | RED |  |
| VDF | VDF_SystemManager v0118 --selftest | RED | rc=2  |
| VDF | 資料家目錄頁 | GREEN | 391 KB · 09-24 15:17 |
| VDF | 庫 vdf_tw_market.duckdb | GREEN | 656.3 MB · 09-25 20:40 |
| VDF | 庫 vdf_global_market.duckdb | GREEN | 88.8 MB · 09-27 21:50 |
| VDF | 庫 ActiveTWETF.duckdb | GREEN | 7.0 MB · 09-25 20:41 |
| VDF | 庫 aaii_sentiment.duckdb | GREEN | 0.8 MB · 09-27 00:14 |
| VRN | VRN_SystemManager v0108 --selftest | RED | rc=1  |
| VRN | ENG111 StockIdentity (BASIC INFO) | GREEN | rc=0 [OK] |
| VRN | ENG112 FinancialRead | GREEN | rc=0 [OK] |
| VRN | ENG110 TabReport v0116 | RED | rc=1  |
| VRN | MDL193 StockIdentityLock_v0100 | GREEN | rc=0 "lock_success": true, |
| VRN | MDL193 VrnTabLock_v0101 | GREEN | rc=0 "lock_success": true, |
| VRN | MDL193 TabFieldLock_v0100 | GREEN | rc=0 "lock_success": true, |
| VRN | MDL193 FinancialReadLock_v0100 | GREEN | rc=0 "lock_success": true, |
| VRN | MDL193 FinancialShownLock_v0100 | GREEN | rc=0 "lock_success": true, |
| VRN | MDL193 GateMapLock_v0100 | GREEN | rc=0 "lock_success": true, |
| VRN | MDL193 StatusLock_v0105 | GREEN | rc=0 "lock_success": true, |
| VCGC status | 邏輯庫 | INFO | 必讀:政策庫 · 邏輯庫 · 因子庫 · SSOT(正則·同義字委派正主)。下列各行就是這四本,本列不重讀 |
| VCGC status | 因子庫 | INFO | 必讀:政策庫 · 邏輯庫 · 因子庫 · SSOT(正則·同義字委派正主)。下列各行就是這四本,本列不重讀 |
| VCGC status | VRN 系統管理 | GREEN | VRN 系統管理 RED:燈 {'policy': 'GREEN', 'logic': 'RED', 'factor': 'GREEN', 'param': 'GREEN', 'engine': 'NODATA', 'h |
| VCGC status | VDF 系統管理 | GREEN | VDF 系統管理 GREEN:燈 {'policy': 'GREEN', 'logic': 'GREEN', 'factor': 'GREEN', 'param': 'GREEN', 'engine': 'GREEN', |
| VCGC status | L50 全景 | GREEN | [政策] L50 全景 · 尾版 516 · import 0 · 提及 34 · 已裝 False · GREEN |
| VCGC status | SSOT 連動 | BROKEN | SSOT 連動 BROKEN:BROKEN 4 · YELLOW 4 · ABSENT 2 · GREEN 2(正則·同義字逐格委派正主;側線 2026-09-23;via-vcgc ssot [plan/verify] |
