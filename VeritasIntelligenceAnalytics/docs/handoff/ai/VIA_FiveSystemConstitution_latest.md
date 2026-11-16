# 五系統編號憲法矩陣(L125 · 2026-11-15T15:15:36Z)

> 五系統各自 MAIN() SSOT 主導;編號預設空著;衝突解了 + VCGC 偵測無誤發號 → 號才有憲法性;唯一跨系統關聯 = 編號;引擎能實跑一個收一個、每次記進度、互不影響完成度;VRN-1 倉外只讀

總燈 **RED** · 實測綠 4/5 · 憲法性 0/5 · 空號 0 · 衝突冊 OPEN 7 · 進度帳 +5(累計 30)

| 系統 | 入口 MAIN() 尾版 | 號 | 憲法性 | 治理器(功 紅/黃/綠/留白 · 表 紅/黃/綠/留白) | 衝突 OPEN | 實測 | 進度(跑/綠/連綠) |
|---|---|---|---|---|---|---|---|
| VCGC | `supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v0192.py` v0192 | VIA-VCGC-MDL1625 | RED CONFLICT_OPEN | 0/5565/10631/11 · 0/53/15/0 | CONFLICT-00006 | GREEN rc 0 · 42.9s | 6/6/6 |
| VDF | `functional modules/VDF/VDF_SystemManager_v0183.py` v0183 | VIA-VDF-MDL279 | RED CONFLICT_OPEN | 0/457/861/10 · 0/69/6/0 | CONFLICT-00004, CONFLICT-00005, CONFLICT-00006 | GREEN rc 0 · 39.7s | 6/6/6 |
| VRN-2 | `functional modules/VRN/VRN_SystemManager_v0275.py` v0275 | VIA-VRN-MDL343 | RED CONFLICT_OPEN | 0/676/2397/10 · 0/107/19/0 | CONFLICT-00012 | GREEN rc 0 · 15.0s | 6/6/6 |
| VQG | `functional modules/VQG/VQG_AllInOne_v0110.py` v0110 | VIA-VQG-MDL007 | RED CONFLICT_OPEN | 未登記 L122 冊 | CONFLICT-00013 | RED rc 1 · 0.1s | 6/5/0 |
| VAP | `functional modules/VAP/VAP_SystemManager_v0100.py` v0100 | VIA-VAP-MDL014 | RED CONFLICT_OPEN | 未登記 L122 冊 | CONFLICT-00013 | GREEN rc 0 · 0.2s | 6/6/6 |
| VRN-1 | `—`  | **空號** | GRAY EXTERNAL_READONLY | 未登記 L122 冊 | CONFLICT-00013 | GRAY rc None · 0s | 0/0/0 |

## 每系統

### VCGC · RED
- 憲法性:CONFLICT_OPEN —— 衝突冊 OPEN 1 項點到本系統 → 號不生效,先裁衝突
- 入口:`supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v0192.py`(200 行 · sha8 5d968efa)· 號冊列(本子系統)9996
- SSOT 冊:`supportive modules/registry/VIA_Policy_Laws_SSOT_v0117.json`; `supportive modules/registry/VIA_Requirements_SSOT_v0252.json`; `supportive modules/registry/VIA_Workflow_VCGC_SSOT_v0148.json`; `supportive modules/registry/VIA_VCGC_FunctionInventory_SSOT_v0224.json`; `supportive modules/registry/VIA_Numbering_SSOT_v0100.json`; `supportive modules/registry/VIA_Handoff_Continuity_SSOT_v0100.json`
- 衝突 OPEN:CONFLICT-00006(MEDIUM)15 組同一編號掛不同名:VCGC 8(CGC_MDL135 EnvGovernance/EnvPlan · CGC_M
- 實測:GREEN · rc 0 · 42.9s · `  """券商正典:CJK 別名子字串;拉丁別名詞界;≤3 字拉丁(gs/ms/mq/ubs)大寫獨立詞,或小寫但緊鄰檔名黏接字([_\-0-9]);`

### VDF · RED
- 憲法性:CONFLICT_OPEN —— 衝突冊 OPEN 3 項點到本系統 → 號不生效,先裁衝突
- 入口:`functional modules/VDF/VDF_SystemManager_v0183.py`(2445 行 · sha8 39bb3008)· 號冊列(本子系統)4678
- SSOT 冊:`functional modules/VDF/registry/VDF_SSOT_Register_v0112.json`; `functional modules/VDF/VDF_FetchSystem_SSOT_v0110.json`; `functional modules/VDF/VDF_InputUniverse_SSOT_v0104.json`; `functional modules/VDF/VDF_DataHome_SSOT_v0101.json`; `supportive modules/registry/VIA_Workflow_VDF_SSOT_v0112.json`
- 衝突 OPEN:CONFLICT-00004(HIGH)114 個 .py 檔名在多個活目錄重複;其中治理核心各 3 份:VIA_EnvManager.py · VIA_SSO; CONFLICT-00005(MEDIUM)277 個 `_sha<hex8>` 分身檔(例 VIA_Panorama_AST_RuntimeInjector_sh; CONFLICT-00006(MEDIUM)15 組同一編號掛不同名:VCGC 8(CGC_MDL135 EnvGovernance/EnvPlan · CGC_M
- 實測:GREEN · rc 0 · 39.7s · `[計] VDF_SystemManager v0183 全原生 39/39 PASS`

### VRN-2 · RED
- 憲法性:CONFLICT_OPEN —— 衝突冊 OPEN 1 項點到本系統 → 號不生效,先裁衝突
- 入口:`functional modules/VRN/VRN_SystemManager_v0275.py`(229 行 · sha8 83653d9b)· 號冊列(本子系統)1476
- SSOT 冊:`functional modules/VRN/SSOT/VRN2_SSOT_v0101.json`; `functional modules/VRN/registry/VRN_SSOT_Index_v0101.json`; `functional modules/VRN/SSOT/VRN_FinLexicon_SSOT_v0109.json`; `functional modules/VRN/VRN_FrameFlow_SSOT_v0102.json`
- 衝突 OPEN:CONFLICT-00012(MEDIUM)VRN-2 啟動器 ActivateVRN-2 本倉只有 docs 內的 release zip 到 v0132;本機 
- 實測:GREEN · rc 0 · 15.0s · `[計] VRN-2 SystemManager v0275(VRN_SystemManager_v0275.py)自測 8/8 · PASS`

### VQG · RED
- 憲法性:CONFLICT_OPEN —— 衝突冊 OPEN 1 項點到本系統 → 號不生效,先裁衝突
- 入口:`functional modules/VQG/VQG_AllInOne_v0110.py`(469 行 · sha8 56611ba9)· 號冊列(本子系統)11
- SSOT 冊:(倉內無常駐登記冊)
- 衝突 OPEN:CONFLICT-00013(HIGH)VAP_AllInOne v0302 尾版(v0300 / v0301 前版同)以 def_import_optiona
- 實測:RED · rc 1 · 0.1s · `目前 Python 缺少 polars。請改用已安裝 duckdb、polars 的 VIA 環境。`

### VAP · RED
- 憲法性:CONFLICT_OPEN —— 衝突冊 OPEN 1 項點到本系統 → 號不生效,先裁衝突
- 入口:`functional modules/VAP/VAP_SystemManager_v0100.py`(47 行 · sha8 0a09a97a)· 號冊列(本子系統)105
- SSOT 冊:`functional modules/VAP/VAP_Subsystem_Manifest.json`; `functional modules/VAP/VAP_Param_Registry_v0100.json`
- 衝突 OPEN:CONFLICT-00013(HIGH)VAP_AllInOne v0302 尾版(v0300 / v0301 前版同)以 def_import_optiona
- 實測:GREEN · rc 0 · 0.2s · `  [OK]`

### VRN-1 · GRAY
- 憲法性:EXTERNAL_READONLY —— 倉外只讀 · 不在本倉號冊 · 不發號(L123)
- 入口:`None`(0 行 · sha8 None)· 號冊列(本子系統)0
- SSOT 冊:(倉內無常駐登記冊)
- 衝突 OPEN:CONFLICT-00013(HIGH)VAP_AllInOne v0302 尾版(v0300 / v0301 前版同)以 def_import_optiona
- 實測:GRAY · rc None · 0s · `倉外只讀 · 不跑`
- 註:另一團隊的倉 tonykuni/VIA-VDF-VRN · 本倉只讀它自報的結果,不跑、不寫、不出版號(L123)

## 治理器(L122 · dry-run 不寫號)

- CGC_MDL270_RegistryGovernor_v0106.py · 總燈 YELLOW · SUBS VCGC, VDF, VRN

## 衝突冊 OPEN(全部)

- CONFLICT-00002 · MEDIUM · VeritasAegisNexus(網路橋本體)在活目錄有 8 份、4 種內容。
- CONFLICT-00004 · HIGH · 114 個 .py 檔名在多個活目錄重複;其中治理核心各 3 份:VIA_EnvManager.py · VIA_SSOT_Unified.py · VIA_RegistryCore_v1.py · VIA_Runtime_Bridge_All_in_One.py · VIA_Panorama_AST_RuntimeI
- CONFLICT-00005 · MEDIUM · 277 個 `_sha<hex8>` 分身檔(例 VIA_Panorama_AST_RuntimeInjector_sha63cefe28.py · StartVIAUnified_shaa1b427ff.ps1)。
- CONFLICT-00006 · MEDIUM · 15 組同一編號掛不同名:VCGC 8(CGC_MDL135 EnvGovernance/EnvPlan · CGC_MDL142 AccelImport/TWNameBook · CGC_MDL149 BoxesFlow/ChainAll/Closeout/EntryLock/FilenameCut/GreenMat
- CONFLICT-00007 · LOW · 275 個遠端分支(vcgc 138 · 根 54 · claude 30 · codex 11 …);抽樣 12 支非 claude 分支各有 1104–3342 筆未併入 main 的提交。
- CONFLICT-00012 · MEDIUM · VRN-2 啟動器 ActivateVRN-2 本倉只有 docs 內的 release zip 到 v0132;本機 vrn2_work 最高 v0178;操作員表列 v0149+。管理器本倉尾版 v0262、本機 v0260。
- CONFLICT-00013 · HIGH · VAP_AllInOne v0302 尾版(v0300 / v0301 前版同)以 def_import_optional("talib") 計算 SMA / EMA / RSI / MACD / BBANDS,並要求上游 taLibEvidence.engine == "TA-Lib";VAP v025 runtim

## 不在範圍

- 不發號、不寫任何系統的冊 / 正本 / 號冊(發號只經 VCGC run CGC_MDL237 --apply --scope · L122 治理器 --apply,都要操作員授權)
- 不裁衝突:衝突冊 OPEN 項只點名歸屬,解法由操作員 + AI 裁定書(L122 ④)
- VRN-1 倉外:不 clone、不跑、不評分(L123)
