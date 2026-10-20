# 工作站分岔清單(workstation-20261020 → main)· 2026-10-20

來源:工作站 `main` 推到 `workstation-20261020`(本機獨有 133 提交、落後 origin/main 181 提交;分岔點 `bed850de4`)。
操作員裁定:VDF 接到 main 上(本 PR);VCGC / VRN / VRN-2 **只列清單不動**,交各系統自己整合(四系統互不干涉,L123)。

判讀:「兩邊同號不同內容」= 兩條線各自發了同一個版號,內容不同(撞號),不能直接合併,要由該系統決定保留哪一邊或改號接上;「main 沒有」= 只有工作站有。

## VDF 這次接回 / 延後(本 PR)

| 工作站檔 | 處理 | 原因 |
|---|---|---|
| `VDF_SystemManager` v0155(`all` 一鍵) | 改號 **v0159** 接上 main | 兩線同號不同內容 |
| `VDF_SystemManager` v0156(啟動就緒沿 Register 鏈) | 改號 **v0160** | 同上 |
| `VDF_SystemManager` v0157(汝窯天青頁首) | **延後** | 要共用字級冊 `VIA_UI_Template_SSOT` v0103(冊號 ≥ 103);該冊是三操作台共用的,加進 main 會改到他系統外觀 → 等操作員 / VCGC 決定 |
| `VDF_MDL012_FetchGroups` v0106(自測鏈隔離活資料樞) | **不搬** | 同號不同內容;main v0106 已在前版鏈自測期間封倉(`_SEAL_REPO_HUB`),同一目的。工作站版接到 main 上反而裝錯地方(main v0106 換掉了鏈上的 `find_db`,隔離只會裝在 v0106 模組上,v0100 呼叫的那個沒被換)|
| `VDF_MDL012_FetchGroups` v0107(清單先跑 · DuckDB 分道並行)· v0108(族群頁版面) | **原號加入** | main 只到 v0106,不撞號;自測裡寫死的「前版 = v0106」照樣對得上 |
| `VDF_ENG093_LaunchConsole` v0105(清單兩步鎖定先跑) | **延後** | 自測要 VCGC 的步驟冊 `CGC_MDL125` v0112(工作站獨有);main 上 4/7 紅 → 等 VCGC 把它的冊接回 |
| `VDF_ENG065_DbImport` v0102 · `VDF_ENG235_MojibakeRepair` v0100 · `SUP_MDL756_SmartDecode` v0100 | 原號加入 | main 沒有;亂碼修復一組 |
| `VDF_ENG077_ActiveETFUniverse` v0106 · `VDF_ActiveETF_Retired_SSOT` v0100 | 原號加入 | main 沒有;退役冊 |
| `VIA_UI_VDFFetchGroups_v0100.html` | 不搬 | 是 FetchGroups `ui` 產生的頁(輸出),跑一次就重產 |
| `activate_vdf.cmd` · `via-activate-vdf.cmd` · `via-vdf-refill.cmd` · `via-vdfeng.cmd` | 不動 | 是 VCGC Register 的短令梭,跟 Register v0276–v0278 一起由 VCGC 處理 |

## VCGC / 登記冊(75 檔:main 沒有 53 · 兩邊同號不同內容 18 · 只工作站改 4)

| 狀態 | 檔 |
|---|---|
| main 沒有 | `Register-VIA-Commands-v0276.ps1` |
| main 沒有 | `Register-VIA-Commands-v0277.ps1` |
| main 沒有 | `Register-VIA-Commands-v0278.ps1` |
| main 沒有 | `supportive modules/registry/CGC_MDL125_FixAll_v0112.py` |
| main 沒有 | `supportive modules/registry/CGC_MDL134_ParallelLanes_v0102.py` |
| main 沒有 | `supportive modules/registry/CGC_MDL224_TestAuto_v0106.py` |
| main 沒有 | `supportive modules/registry/CGC_MDL237_NumberingSystem_v0118.py` |
| main 沒有 | `supportive modules/registry/CGC_MDL246_ValidationSSOT_v0101.py` |
| main 沒有 | `supportive modules/registry/CGC_MDL261_UIEngine_v0107.py` |
| main 沒有 | `supportive modules/registry/CGC_MDL274_HealthMatrix_v0115.py` |
| main 沒有 | `supportive modules/registry/VIA_Requirements_SSOT_v0197.json` |
| main 沒有 | `supportive modules/registry/VIA_Requirements_SSOT_v0198.json` |
| main 沒有 | `supportive modules/registry/VIA_Requirements_SSOT_v0199.json` |
| main 沒有 | `supportive modules/registry/VIA_Requirements_SSOT_v0200.json` |
| main 沒有 | `supportive modules/registry/VIA_Requirements_SSOT_v0201.json` |
| main 沒有 | `supportive modules/registry/VIA_Requirements_SSOT_v0202.json` |
| main 沒有 | `supportive modules/registry/VIA_Requirements_SSOT_v0203.json` |
| main 沒有 | `supportive modules/registry/VIA_Requirements_SSOT_v0204.json` |
| main 沒有 | `supportive modules/registry/VIA_Requirements_SSOT_v0205.json` |
| main 沒有 | `supportive modules/registry/VIA_Requirements_SSOT_v0206.json` |
| main 沒有 | `supportive modules/registry/VIA_Requirements_SSOT_v0207.json` |
| main 沒有 | `supportive modules/registry/VIA_Requirements_SSOT_v0208.json` |
| main 沒有 | `supportive modules/registry/VIA_UI_Template_SSOT_v0103.json` |
| main 沒有 | `supportive modules/registry/VIA_VCGC_FunctionInventory_SSOT_v0171.json` |
| main 沒有 | `supportive modules/registry/VIA_VCGC_FunctionInventory_SSOT_v0172.json` |
| main 沒有 | `supportive modules/registry/VIA_VCGC_FunctionInventory_SSOT_v0173.json` |
| main 沒有 | `supportive modules/registry/VIA_VCGC_FunctionInventory_SSOT_v0174.json` |
| main 沒有 | `supportive modules/registry/VIA_VCGC_FunctionInventory_SSOT_v0175.json` |
| main 沒有 | `supportive modules/registry/VIA_VCGC_FunctionInventory_SSOT_v0176.json` |
| main 沒有 | `supportive modules/registry/VIA_VCGC_FunctionInventory_SSOT_v0177.json` |
| main 沒有 | `supportive modules/registry/VIA_VCGC_FunctionInventory_SSOT_v0178.json` |
| main 沒有 | `supportive modules/registry/VIA_VCGC_FunctionInventory_SSOT_v0179.json` |
| main 沒有 | `supportive modules/registry/VIA_Validation_SSOT_v0101.json` |
| main 沒有 | `via-activate-vcgc.cmd` |
| main 沒有 | `via-camelot.cmd` |
| main 沒有 | `via-cmds.cmd` |
| main 沒有 | `via-duck.cmd` |
| main 沒有 | `via-engines.cmd` |
| main 沒有 | `via-groups-ui.cmd` |
| main 沒有 | `via-groups.cmd` |
| main 沒有 | `via-monitor.cmd` |
| main 沒有 | `via-op-pick.cmd` |
| main 沒有 | `via-op-run.cmd` |
| main 沒有 | `via-op.cmd` |
| main 沒有 | `via-precheck.cmd` |
| main 沒有 | `via-realtest.cmd` |
| main 沒有 | `via-review.cmd` |
| main 沒有 | `via-startdate.cmd` |
| main 沒有 | `via-tools.cmd` |
| main 沒有 | `via-ui-all.cmd` |
| main 沒有 | `via-uieng.cmd` |
| main 沒有 | `via-uihelp.cmd` |
| main 沒有 | `via-vrneng.cmd` |
| 兩邊同號不同內容 | `supportive modules/registry/VIA_Component_Inventory_SSOT_v0100.json` |
| 兩邊同號不同內容 | `supportive modules/registry/VIA_Handoff_Continuity_SSOT_v0100.json` |
| 兩邊同號不同內容 | `supportive modules/registry/VIA_NumberBooks/VIA_NumberBook_ENG_v0100.jsonl` |
| 兩邊同號不同內容 | `supportive modules/registry/VIA_NumberBooks/VIA_NumberBook_ENV_v0100.jsonl` |
| 兩邊同號不同內容 | `supportive modules/registry/VIA_NumberBooks/VIA_NumberBook_FNC_CORE_v0100.jsonl` |
| 兩邊同號不同內容 | `supportive modules/registry/VIA_NumberBooks/VIA_NumberBook_FNC_VCGC_v0100.jsonl` |
| 兩邊同號不同內容 | `supportive modules/registry/VIA_NumberBooks/VIA_NumberBook_FNC_VRN_v0100.jsonl` |
| 兩邊同號不同內容 | `supportive modules/registry/VIA_NumberBooks/VIA_NumberBook_MDL_v0100.jsonl` |
| 兩邊同號不同內容 | `supportive modules/registry/VIA_NumberBooks/VIA_NumberBook_REQ_v0100.jsonl` |
| 兩邊同號不同內容 | `supportive modules/registry/VIA_Numbering_SSOT_v0100.json` |
| 兩邊同號不同內容 | `supportive modules/registry/VIA_Requirements_SSOT_v0193.json` |
| 兩邊同號不同內容 | `supportive modules/registry/VIA_Requirements_SSOT_v0194.json` |
| 兩邊同號不同內容 | `supportive modules/registry/VIA_Requirements_SSOT_v0195.json` |
| 兩邊同號不同內容 | `supportive modules/registry/VIA_Requirements_SSOT_v0196.json` |
| 兩邊同號不同內容 | `supportive modules/registry/VIA_VCGC_FunctionInventory_SSOT_v0168.json` |
| 兩邊同號不同內容 | `supportive modules/registry/VIA_VCGC_FunctionInventory_SSOT_v0169.json` |
| 兩邊同號不同內容 | `supportive modules/registry/VIA_VCGC_FunctionInventory_SSOT_v0170.json` |
| 兩邊同號不同內容 | `supportive modules/registry/VIA_VCGC_FunctionLedger_v0100.jsonl` |
| 只工作站改 | `supportive modules/registry/VIA_NumberBooks/VIA_NumberBook_CLS_VCGC_v0100.jsonl` |
| 只工作站改 | `supportive modules/registry/VIA_NumberBooks/VIA_NumberBook_CLS_VRN_v0100.jsonl` |
| 只工作站改 | `supportive modules/registry/VIA_NumberBooks/VIA_NumberBook_FNC_SUP_v0100.jsonl` |
| 只工作站改 | `supportive modules/registry/VIA_ParallelLanes_v0100.json` |

## VRN-2(3 檔:兩邊同號不同內容 1 · main 沒有 2)

| 狀態 | 檔 |
|---|---|
| main 沒有 | `docs/handoff/ai/VRN2_Handover_v0119.md` |
| main 沒有 | `functional modules/VRN/SSOT/VRN2_SSOT_v0100.json` |
| 兩邊同號不同內容 | `docs/handoff/ai/VRN2_Handover_latest.md` |

## VRN(未分辨 VRN-1/VRN-2)(24 檔:main 沒有 24)

| 狀態 | 檔 |
|---|---|
| main 沒有 | `functional modules/VRN/SSOT/VRN_Config_v1000.json` |
| main 沒有 | `functional modules/VRN/VRN_ENG062_SummarizerV1_v0105.py` |
| main 沒有 | `functional modules/VRN/VRN_ENG062_SummarizerV1_v0106.py` |
| main 沒有 | `functional modules/VRN/VRN_ENG062_SummarizerV1_v0107.py` |
| main 沒有 | `functional modules/VRN/VRN_ENG062_SummarizerV1_v0108.py` |
| main 沒有 | `functional modules/VRN/VRN_ENG062_SummarizerV1_v0109.py` |
| main 沒有 | `functional modules/VRN/VRN_ENG062_SummarizerV1_v0110.py` |
| main 沒有 | `functional modules/VRN/VRN_ENG062_SummarizerV1_v0111.py` |
| main 沒有 | `functional modules/VRN/VRN_ENG062_SummarizerV1_v0112.py` |
| main 沒有 | `functional modules/VRN/VRN_ENG397_P1Segment_v0113.py` |
| main 沒有 | `functional modules/VRN/VRN_ENG397_P1Segment_v0114.py` |
| main 沒有 | `functional modules/VRN/VRN_ENG397_P1Segment_v0115.py` |
| main 沒有 | `functional modules/VRN/VRN_ENG397_P1Segment_v0116.py` |
| main 沒有 | `functional modules/VRN/VRN_ENG397_P1Segment_v0117.py` |
| main 沒有 | `functional modules/VRN/VRN_ENG397_P1Segment_v0118.py` |
| main 沒有 | `functional modules/VRN/VRN_ENG397_P1Segment_v0119.py` |
| main 沒有 | `functional modules/VRN/VRN_ENG397_P1Segment_v0120.py` |
| main 沒有 | `functional modules/VRN/VRN_ENG397_P1Segment_v0121.py` |
| main 沒有 | `functional modules/VRN/VRN_ENG397_P1Segment_v0122.py` |
| main 沒有 | `functional modules/VRN/VRN_ENG397_P1Segment_v0123.py` |
| main 沒有 | `functional modules/VRN/VRN_ENG397_P1Segment_v0124.py` |
| main 沒有 | `functional modules/VRN/VRN_ENG397_P1Segment_v0125.py` |
| main 沒有 | `functional modules/VRN/VRN_SystemManager_v0229.py` |
| main 沒有 | `functional modules/VRN/rule_catalog_runtime.json` |

## 共用模組(SUP)(2 檔:main 沒有 2)

| 狀態 | 檔 |
|---|---|
| main 沒有 | `supportive modules/network/SUP_MDL740_NetUnified_v0119.py` |
| main 沒有 | `supportive modules/network/SUP_MDL756_SmartDecode_v0100.py` |

## 其他(4 檔:main 沒有 4)

| 狀態 | 檔 |
|---|---|
| main 沒有 | `docs/handoff/ai/VCGC_HealthCard_20261011.md` |
| main 沒有 | `docs/handoff/ai/VCGC_HealthCard_20261012.md` |
| main 沒有 | `docs/handoff/ai/VIA_ThreeSystems_FixRound_20261012.md` |
| main 沒有 | `supportive modules/ui_support/VIA_UI_Design_VeritasHeader_v0100.dc.html` |

## VDF(18 檔:main 沒有 11 · 兩邊同號不同內容 6 · 只工作站改 1)

VDF 部分由本 PR 處理(見批次文件「工作站分岔接回」段);此處列出供對照。

| 狀態 | 檔 |
|---|---|
| main 沒有 | `activate_vdf.cmd` |
| main 沒有 | `functional modules/VDF/VDF_ActiveETF_Retired_SSOT_v0100.json` |
| main 沒有 | `functional modules/VDF/VDF_ENG093_LaunchConsole_v0105.py` |
| main 沒有 | `functional modules/VDF/VDF_MDL012_FetchGroups_v0107.py` |
| main 沒有 | `functional modules/VDF/VDF_MDL012_FetchGroups_v0108.py` |
| main 沒有 | `functional modules/VDF/engine/VDF_ENG065_DbImport_v0102.py` |
| main 沒有 | `functional modules/VDF/engine/VDF_ENG077_ActiveETFUniverse_v0106.py` |
| main 沒有 | `functional modules/VDF/engine/VDF_ENG235_MojibakeRepair_v0100.py` |
| main 沒有 | `via-activate-vdf.cmd` |
| main 沒有 | `via-vdf-refill.cmd` |
| main 沒有 | `via-vdfeng.cmd` |
| 兩邊同號不同內容 | `functional modules/VDF/VDF_MDL012_FetchGroups_v0106.py` |
| 兩邊同號不同內容 | `functional modules/VDF/VDF_SystemManager_v0155.py` |
| 兩邊同號不同內容 | `functional modules/VDF/VDF_SystemManager_v0156.py` |
| 兩邊同號不同內容 | `functional modules/VDF/VDF_SystemManager_v0157.py` |
| 兩邊同號不同內容 | `supportive modules/registry/VIA_NumberBooks/VIA_NumberBook_CLS_VDF_v0100.jsonl` |
| 兩邊同號不同內容 | `supportive modules/registry/VIA_NumberBooks/VIA_NumberBook_FNC_VDF_v0100.jsonl` |
| 只工作站改 | `supportive modules/ui_support/VIA_UI_VDFFetchGroups_v0100.html` |

## 收據(268 檔:main 沒有 206 · 兩邊同號不同內容 28 · 只工作站改 34)

交接收據檔數多(歷史目錄),不逐一列;收據跟著各系統的程式一起處理。

