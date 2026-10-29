# 工作站分岔清單(workstation-20261020 → main)· 2026-10-20

來源:工作站 `main` 推到 `workstation-20261020`(本機獨有 133 提交、落後 origin/main 181 提交;分岔點 `bed850de4`)。
操作員裁定:VDF 接到 main 上(本 PR);VCGC / VRN / VRN-2 **只列清單不動**,交各系統自己整合(四系統互不干涉,L123)。

判讀:「兩邊同號不同內容」= 兩條線各自發了同一個版號,內容不同(撞號),不能直接合併,要由該系統決定保留哪一邊或改號接上;「main 沒有」= 只有工作站有。

## VDF 這次接回 / 延後(本 PR)

| 工作站檔 | 處理 | 原因 |
|---|---|---|
| `VDF_SystemManager` v0155(`all` 一鍵) | 改號 **v0159** 接上 main | 兩線同號不同內容 |
| `VDF_SystemManager` v0156(啟動就緒沿 Register 鏈) | 改號 **v0160**(第二批 PR) | 同上;擊斃閘 KILL-11:同一 PR 不能連加兩版 |
| `VDF_SystemManager` v0157(汝窯天青頁首) | **延後** | 要共用字級冊 `VIA_UI_Template_SSOT` v0103(冊號 ≥ 103);該冊是三操作台共用的,加進 main 會改到他系統外觀 → 等操作員 / VCGC 決定 |
| `VDF_MDL012_FetchGroups` v0106(自測鏈隔離活資料樞) | **不搬** | 同號不同內容;main v0106 已在前版鏈自測期間封倉(`_SEAL_REPO_HUB`),同一目的。工作站版接到 main 上反而裝錯地方(main v0106 換掉了鏈上的 `find_db`,隔離只會裝在 v0106 模組上,v0100 呼叫的那個沒被換)|
| `VDF_MDL012_FetchGroups` v0107(清單先跑 · DuckDB 分道並行)· v0108(族群頁版面) | **原號加入**(v0108 走第二批 PR) | main 只到 v0106,不撞號;自測裡寫死的「前版 = v0106」照樣對得上 |
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


## PR #546 審查修正(接回前在 PR 內修;四檔都是這次才進 main 的新檔)

| 審查 | 檔 | 問題 | 修法 | 自測 |
|---|---|---|---|---|
| P1 | `VDF_ENG065_DbImport_v0102.py` | 亂碼修復失敗(ENG235 回 `action=FAIL`)時照樣匯入,亂碼原樣進庫還回成功 | 有任一檔修復失敗 → 不匯入、rc 1、印失敗檔與原因;要硬匯入 = 操作員明示 `VIA_MOJIBAKE_FIX=0` | ⑦ · 7/7 |
| P2 | `VDF_ENG235_MojibakeRepair_v0100.py` | 備份只用檔名,遞迴掃到兩個同名檔(不同子夾)時第二個沒有備份卻照換 | 備份照「相對掃描根」路徑放 `_pre_mojibake/<子夾>/<檔名>`(`_bk_path`);parquet 與 DuckDB 都走它 | ⑨ · 9/9 |
| P2 | `VDF_ENG077_ActiveETFUniverse_v0106.py` | 退役冊在但讀不懂(截斷 / 結構不對)被當空冊,退役碼會被當現役重新入宇宙 | 丟 `RetiredBookError`;`run` 先驗冊,壞了 `[退役] FAIL`、rc 1、不跑(註冊表不動);沒有冊照舊 = 空 | ⑩ · 10/10 |
| P2 | `VDF_MDL014_WorkstationSync_v0100.py` | 分支名只到分鐘,同一分鐘重跑 `git switch -c` 撞名中斷 | 時間到秒;本機或遠端已有同名就加 `-2`、`-3`(`_free_name`),備份與收據分支都走它 | ⑮ · 15/15 |

四個修正各做一個突變(拿掉修正)→ 對應自測都抓到(紅)。

## 第二批(KILL-11:同一家族一個 PR 只能尾版 +1,所以分兩批)

| 檔 | 來源 | 說明 | 自測 |
|---|---|---|---|
| `VDF_SystemManager_v0160.py` | 工作站 v0156 改號 + 本線加段 | 啟動就緒的短令檢查沿 Register 點源鏈讀(問參數頁假紅修正);**本線加段:U/I 實測修正**(下節) | 15/15 · 全鏈 0 FAIL |
| `VDF_MDL012_FetchGroups_v0108.py` | 工作站原號 | 族群頁版面最佳化(字級套件 · 左面板摺疊 · 短欄不換行 · 燈欄第一 · 空值 —)+ 接回修正:窄版一欄 | 8/8 · 前版鏈 PASS |

交接案:`vdf_ws_manager_ready` · `vdf_ws_fetch_groups_layout`(案名不帶版號,避開 KILL-11 把收據檔當版號檔)。
延後項 `VDF-REQ018:ws-fork-deferred` 只剩管理員工作站 v0157 與 ENG093 工作站 v0105(理由見上)。

### U/I 實測修正(操作員令「實測實際修正自動完成直到輸出結果驗證結果無誤於HTML U/I」)

驗法(只讀,不用 manager 的程式):無頭 Chromium 開五頁(資料庫檢查 · 獨立核對 · VDF U/I · 表頭彙整 · 全景)× 三種視窗(寬 · 深色 · 手機 390),
讀**渲染後**的 DOM(頁內 JS 跑完),三方比對:頁上的格子 ↔ `DB_CHECK_latest.json` ↔ DuckDB 唯讀重數。

| 項 | 修前 | 修後 |
|---|---|---|
| 資料庫檢查頁列數 / JSON 列數 | 65 / 65 | 65 / 65 |
| DuckDB 唯讀重數(34 表) | 0 差 | 0 差 |
| 燈號計數 頁 ↔ JSON | 紅 18 · 黃 29 · 綠 4 · 資訊 14 一致 | 一致 |
| 獨立核對頁 | PASS · 325 欄 · 差異 0 · 總列數 3,389,013 | 同 |
| 頁錯誤 / 手機橫向溢出 / 殘留 NaN | 0 / 0 / 0 | 0 / 0 / 0 |
| **整數欄印成小數**(列數 1163.0 · 最少 1.0 …) | **181 格(頁)· CSV 63 列** | **0** |
| **空的寫入者格** | **27 格空白** | **—** |
| **頁內燈號列 紅/黃/綠/灰**(同頁摘要 紅 18 · 黃 29 · 綠 4 · 資訊 14) | **18 / 29 / 18 / 0**(INFO 被算成綠) | **18 / 29 / 4 / 14** |
| **手機 390 單字被壓成多行**(表名 · 寫入者 · 候選檔) | **資料庫檢查頁 112 格 · 核對頁 2 格**(aaii_sentiment 拆成 9 行) | **0**(表變寬,在橫捲框裡捲) |
| **VDF 操作頁頁籤白頁**(健康 → VCGC 健康矩陣頁不在 · 本輪 PS U/I src 空) | **2 個白頁** | **0**(寫說明:哪個檔 · 誰的頁 · 產生指令 · 重跑 ui) |
| **VDF 操作頁手機左面板** | **被壓成 30px**(header 1/3 逼出隱形第二欄) | **全寬上下排** |
| **族群頁手機版面**(FetchGroups v0108) | **左 340px · 右 30px 一字一行**(v0105 無條件 340px 蓋掉 900px 一欄) | **一欄上下排** |

根因:v0151 `_write_db` 用 pandas DataFrame,有 None 的整數欄被轉成 float64,頁與 CSV 都印小數;空字串格頁內 JS 不認。
修法(v0160 加段):db check 寫檔時接手 CSV 與頁上那張表 —— 整數照整數、空值頁上 —(CSV 留空)、燈色與頁殼照前版;JSON 本來就對,不動。
自測 ⑨⑩⑪;六個突變(整數 · 空值 — · CSV · 接手點 · NaN · 燈色)全被抓到。
燈號列:v0154 展現腳本的嚴重度表把 INFO 歸綠(`INFO:2`),表上 INFO 卻是灰字;v0160 把 v0154 模組的 `_TK_JS` 換成 `INFO:3`(歸灰),
字級套件每次產生都讀它 → 燈號列與摘要同數。自測 ⑫(拿掉修正 → ⑫ 紅)。比對工具也補上「燈號列 ↔ JSON 摘要」這一項(第一次漏量)。
手機:字級套件把超過 24 字的欄套 `overflow-wrap:anywhere`,表格因此把無空白的長字壓成一字一行,表也就永遠不比手機寬、橫捲框不出現。
v0160 把 CSS 與 JS 兩處改成 `break-word`(長字不拆;表變寬 → 套件自己的橫捲框接手)。自測 ⑬(拿掉修正 → ⑬ 紅);比對工具補「單字被壓成多行」與「寬表有橫捲框」兩項。
操作頁:頁籤目標檔不在或 src 空 → ui 跑完補 srcdoc 說明(自測 ⑭);窄版補 `header{grid-column:1/-1}`(自測 ⑮)。族群頁:v0108 頁尾版面 CSS 補 900px 一欄(v0108 自測 ⑧)。
比對工具再補「頁籤白頁」「手機左面板寬度」兩項;族群頁另用同一支工具量(三視窗 0 錯 · 0 擠壓 · 手機左面板 358/390)。

## 第三批:延後兩支改成 VDF 自足版接上(操作員令「把 VCGC 待辦的兩支接上 VDF」)

兩支原本延後,是因為工作站版要 VCGC 的檔(共用字級冊 `VIA_UI_Template_SSOT v0103`、步冊 `CGC_MDL125 v0112`、並行道 `CGC_MDL134 v0102`)。
四系統對等獨立(L123),本線**不搬、不改**這三份 VCGC 檔,改由 VDF 自己補上缺的那一塊;VCGC 哪天自己接回,兩支自動讓位給 VCGC 的版本。

| 檔 | 來源 | 說明 | 自測 |
|---|---|---|---|
| `VDF_UI_Design_SSOT_v0100.json` | 新冊(VDF 自己的) | 設計稿 1c 汝窯天青:47 個 token(共用冊 v0103 tokens ⊕ systems.VDF)· design.css · serif_selector;只管 VDF 頁,記來源 sha256 | (冊) |
| `VDF_SystemManager_v0161.py` | 工作站 v0157 改號 | 頁首 1c 汝窯天青視覺。共用冊有 systems.VDF + design.css → 用共用冊(工作站行為);沒有 → 用 VDF 自己的冊(共用 tokens 打底、燈四色仍鎖)· 壞冊照實寫 why · 前版鏈自測時先換回原樣再換上 | 11/11 · 全鏈 0 FAIL |
| `VDF_ENG093_LaunchConsole_v0105.py` | 工作站原號 | 問參數頁清單兩步 `tw_list` · `etf_list` 鎖定在最前(勾不掉、不送 -Steps)。VCGC 步冊有清單步 → 照工作站版交 VCGC 並行道;沒有 → 清單列改由 VDF 擷取冊 009 · 010 列出,按「啟動」後 ask 自己用 `VDF_MDL012_FetchGroups` 清單先行跑 009 → 010:全綠才放行;紅 → 決定檔 `lists_failed`(rc 5)· 雙閘沒開 → `lists_gated`(rc 4)· 只看計畫不跑。開啟器照決定不是 launch 就不啟動(.ps1 不動) | 16/16 · 前版鏈 PASS |

### 實測

- 突變:ENG093 v0105 17 個突變(紅不停 · rc 對錯 · 不改決定 · 不看閘 · 一律 VDF · 不看歸屬 · 不清單先行 · dry 也跑 · 註記顛倒 · 預算不分 · 列不鎖 · 不看時間 · 窄版沒套 / 沒效)全被抓到;
  第一次 `註記顛倒` 活下來(頁上列文字本來就有註記),② 改驗鎖定框的 title 後抓到。
  管理員 v0161 7 個突變(不蓋 VDF 冊 · VDF 冊搶過共用冊 · 燈不鎖 · 壞冊不報 · 不取尾版 · 不換回 · 前版鏈前不換回)全被抓到;
  第一次 `VDF 冊搶過共用冊` 活下來(沒驗「共用冊有 systems.VDF 時 VDF 讓位」),⑦b 補這一案後抓到。
- 問參數頁真跑(無頭 Chromium · 本機頁 · 一次性權杖):兩列鎖定在最前(checked · disabled · VDF 註記)· 已勾 11/11(不含清單步)· 0 頁錯誤;
  按「用預設參數啟動」→ 本容器雙閘沒開 → `lists_gated` · rc 4 · 零子行程;勾「只看計畫」再按「用下面勾的啟動」→ `launch` · `SKIP_DRY` · rc 0;按「不啟動」→ 照舊 cancel。
- **找到並修好**:手機 390 寬問參數頁橫向溢出到 660(資料庫卡上的目錄路徑 `<code>` 一長串不斷行;v0104 就有)。v0105 在問參數頁與資料庫狀況頁頭加 `code{overflow-wrap:anywhere}`
  (自測 ⑤b)→ 兩頁手機 390/390、寬 1280/1280。
- 管理員 v0161 頁:五頁 × 三視窗重量 —— 頁錯誤 0 · 溢出 0 · 殘留 0 · 擠壓 0;資料庫檢查頁 65 列 = JSON 65 列 · 34 表 DuckDB 重數 0 差 · 燈號列 18/29/4/14 = 摘要;
  核對頁 PASS · 325 欄 · 差異 0;頁籤白頁 0;手機左面板 390。頁首換成 1c 汝窯天青(頁底色 #f5f4f0)。v0160 的 U/I 修正全部仍在。

Codex 審查(#548)兩條 P2 已修:① VCGC 步冊兩列在、但引擎檔不在或並行道 CGC_MDL134 < v0102 → 不讓位,VDF 自己跑(自測 ⑬b);
② 擷取冊 009 / 010 缺一 → ABSENT 不放行(原本只跑剩下那支就回 OK;自測 ⑩b)。各加突變(不看引擎 · 不看並行道版 · 缺一照跑)全被抓到。

交接案:`vdf_ws_manager_design` · `vdf_ws_eng093_lists`;延後項 `VDF-REQ018:ws-fork-deferred` 帶理由轉 VERIFIED。

## 第四批:工作站同步到 main —— `VDF_MDL014_WorkstationSync_v0101.py`(操作員令「用 MDL014 把工作站同步到 main」)

MDL014 的「同步」= **VDF 改從自己固定在 `origin/main` 的工作樹跑**;工作站原 checkout(含 VRN-2 / VCGC 的本機工作)一個位元組都不動(L123)。
v0100 在工作站實況下有兩個缺口,v0101(薄尾)補上:

| 缺口 | v0100 | v0101 |
|---|---|---|
| 工作站 checkout 是分岔、沒有 MDL014 這支檔 → 只能從工作樹裡跑 | 把工作樹當原 checkout:量不到分岔、不備份,還再建一個 `<工作樹>-vdf-main` | 原 checkout = `git worktree list` 第一個;本檔在工作樹裡 → 就用這個工作樹;`--repo` 可明指(自測 ①③) |
| VDF 資料不在 git(`output_hub` 的 DuckDB · `VIA_Reports/vdf_fetch`) | 工作樹裡的 VDF 是空的 | `--apply` 時以目錄接點(junction,免管理員)接到原 checkout 的實體夾;已有實體夾不動 · 原處沒有不接 · 已接照舊(自測 ④⑥⑦) |
| 接點被 git 當未追蹤(`output_hub/` 帶斜線只擋實體夾)| 第二次跑會誤判工作樹髒而停 | 量髒時濾掉本版的接點(自測 ⑤) |

自測 11/11(含前版 v0100 15/15);突變 12 個全抓到。
Codex 審查(#549)兩條已修:**P1** 從別的工作樹(他系統的功能分支等)跑也會被接手(切到 main · 接資料 · 開收據分支)→ 只沿用 VDF 的預設位置
(`%LOCALAPPDATA%\VIA\<倉名>-vdf-main`)或 `--worktree` 明指的,其他一律 rc 2 停在動手前(自測 ①b);
**P2** 預演印的 NEXT 掉了 `--repo` / `--worktree` / `--remote` / `--no-link-data` → 照全部參數重組(自測 ②b)。
容器內對真倉只做預演(`--apply` 會把收據分支推到 GitHub;本線只推指定分支)。

### 工作站步驟(PowerShell)

```powershell
cd <你的倉根>
git fetch origin
$wt = "$env:LOCALAPPDATA\VIA\" + (Split-Path -Leaf (git rev-parse --show-toplevel)) + "-vdf-main"
if (Test-Path $wt) { git -C $wt checkout --detach origin/main } else { git worktree add --detach $wt origin/main }
$m = "$wt\VeritasIntelligenceAnalytics\functional modules\VDF\VDF_MDL014_WorkstationSync_v0101.py"
python $m --case qg_onebridge --case vdf_ws_manager_design --case vdf_ws_eng093_lists            # 預演:只量不動
python $m --case qg_onebridge --case vdf_ws_manager_design --case vdf_ws_eng093_lists --apply    # 執行
```

之後 VDF 一律從 `$wt` 跑(管理員 · 啟動台 · 開啟器);兩邊共用同一份資料,同一時間只從一邊跑 VDF。

### 工作站步驟(cmd.exe —— 工作站的視窗是 cmd,不是 PowerShell)

2026-10-20 實錄:上面的 PowerShell 指令貼進 cmd,`$wt` 被當字面 → `git worktree add` 在倉內(OneDrive)建了一個叫 `$wt` 的整份工作樹(47,847 檔),
其餘指令都失敗、沒有副作用。先清掉它(視窗不要停在那個夾裡;OneDrive 若卡住檔案就先暫停同步):

```bat
cd /d C:\Users\tonyk\OneDrive\Documents\movies-dataset
git worktree remove --force "VeritasIntelligenceAnalytics/$wt"
git worktree prune
git worktree list
```

同步(cmd.exe;VDF 工作樹放 %LOCALAPPDATA%,不進 OneDrive):

```bat
cd /d C:\Users\tonyk\OneDrive\Documents\movies-dataset
git fetch origin
set "WT=%LOCALAPPDATA%\VIA\movies-dataset-vdf-main"
if exist "%WT%\.git" (git -C "%WT%" checkout --detach origin/main) else (git worktree add --detach "%WT%" origin/main)
set "M=%WT%\VeritasIntelligenceAnalytics\functional modules\VDF\VDF_MDL014_WorkstationSync_v0101.py"
python "%M%" --case qg_onebridge --case vdf_ws_manager_design --case vdf_ws_eng093_lists
python "%M%" --case qg_onebridge --case vdf_ws_manager_design --case vdf_ws_eng093_lists --apply
```

同步後在 VDF 工作樹裡看 U/I(cmd.exe):

```bat
cd /d "%WT%\VeritasIntelligenceAnalytics"
set VIA_FROM_VCGC=YES
for /f "delims=" %F in ('dir /b /o:n "supportive modules\registry\CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"') do set "V=%CD%\supportive modules\registry\%F"
python "%V%" run VDF_SystemManager --selftest
python "%V%" run VDF_ENG093_LaunchConsole --selftest
python "%V%" run VDF_SystemManager db check
python "%V%" run VDF_SystemManager ui
start "" "VIA_Reports\vdf\VDF_UI_latest.html"
python "%V%" run VDF_ENG093_LaunchConsole ask --open --out "%TEMP%\vdf_ask_check.json"
```

## 第五批(2026-10-21 16:03 工作站實錄 → MDL014 v0102)

操作員在 cmd 跑 `VDF_MDL014_WorkstationSync_v0101.py --apply`,停在 `ensure_worktree`:
`RuntimeError: VDF 工作樹有未提交的改動 … ['M  …/docs/handoff/evidence/qg_onebridge.json', ' M …/qg_onebridge.txt']`。
根因:那兩個檔是 MDL014 自己上一次 `--apply` 跑完交接案後寫的收據(stage 了、沒交完);v0100 的 `ensure_worktree` 把它們當別人的改動拒絕,
而 v0100 的 `publish` 交完收據停在收據分支上、沒回 main。

- **v0102(薄尾)**:① 髒檔全在 `docs/handoff/evidence/` → 還原 + 清未追蹤、印「清掉上次沒交完的收據 N 檔」再照常移到最新 main;有別的檔 → 一個都不動、拒絕(訊息帶 `git -C <工作樹> status`)。
  ② `publish` 推完收據分支後 `git checkout --detach origin/main`:工作樹回到 main、乾淨。③ `run` 裡的 RuntimeError → 一行 `[VDF MAIN] 停:…` 回 rc 2,不噴 traceback。
- 自測 7/7(假倉重演工作站實況:stage 一個 · 改一個 · 多一個未追蹤 → 清掉 → 同步 → 收據分支 → 回 main;別的髒檔 → 拒絕 rc 2;預演 NEXT 印本版檔名);前版鏈 v0101 11/11 · v0100 15/15。
- 工作站當下的解法(v0102 進 main 前):`git restore --staged --worktree -- "VeritasIntelligenceAnalytics/docs/handoff/evidence"` 再跑 `--apply`。

## 第六批(2026-10-27 工作站實錄 → 管理員 v0162)

操作員令「先啟動這兩個清單後單獨啟動每一個VDF的引擎」。工作站 PowerShell 逐支 `python $M fetch run <代號> --apply --mode live --home …\via_01_vdf`:
兩張清單 GREEN(全台股 1983 列 · 主動式 ETF 32 列)、001u GREEN、002 YELLOW rc 2(NODATA,yfinance 零列)、003 GREEN;其餘未跑完(操作員中斷)。

兩個實錄問題 → `VDF_SystemManager_v0162`(薄尾):
- 每個 fetch 動詞(run / verify / status / list)跑完,v0153 的 main 都再對 `VIA_Reports/vdf` 直下 `*_latest.html` 補一遍字級套件;fetch 不產頁,36 支 = 36 遍白工(操作員在 `fetch status` 收尾按了 Ctrl+C,traceback 停在 `typekit_block`)。v0162:`args[0] == "fetch"` 那一輪把 v0153 的 `typekit_dir` 換成零動作替身、跑完(含例外)還原;其他動詞照舊。
- 每次印 `VDF_SystemManager_v0155.py:6: SyntaxWarning: invalid escape sequence '\o'`(v0155 說明字串裡的 `VDF\output_hub`;正本不改)。v0162:載前版鏈那一刻 `warnings.catch_warnings` 只擋 SyntaxWarning / DeprecationWarning;本檔自己零無效跳脫(自測驗)。
- 自測 6/6(找得到補套主人 v0153 · fetch 經本版不補套 / 直走前版會補 / 非 fetch 照舊 · 炸掉也還原 · 兩個探針檔證明前版載入器會印、本版不印 · 橋 / 不起子行程 / 版面功能燈程式一行沒動);突變 9 個全抓到。
- 誠實說:本容器沒有 pandas,管理員全鏈自測(v0151 的 db 自測)在這裡跑不動;交接案 `vdf_ws_manager_fetch_quiet` 的綠收據要靠工作站或 Windows CI(有 pandas · duckdb)。

## 第七批(2026-10-28)· main 被 VRN-2 auto-merge `9e494a2a` 覆蓋的修復 + VCGC 閘被 VRN-2 斷鏈擋住

**事實(git 三方比對:base `bed850de` 10-12 · ours `ee55265d` = 合併當時 main 這一側 10-27 · theirs = 現在 main)**
- `9e494a2a`「VRN-2 auto-merge origin/main (conflicts → local, additions kept)」把 68 個 main 已改的檔用 VRN-2 本機舊版蓋掉(全部是兩邊都改過的真衝突,VRN-2 合併後再沒碰):
  VDF 程式 10 支(ENG093 v0105 · FetchGroups v0106–v0108 · SystemManager v0155–v0157 · ENG065 v0102 · ENG077 v0106 · ENG235 v0100)、交接收據 32 檔、
  共用冊 21 本(元件清冊 18515 → 18076 列 · 編號冊 FNC_VDF 10225 → 9647 列 · 編號 SSOT · 交接冊 209 案 → 189 案 · 370 項 → 349 項 · 需求冊 v0193–v0196 · VCGC 功能盤點冊 v0168–v0170 / 帳本)。
  VDF 這一側自 10-13 起的登錄全數消失(v0162 · MDL014 v0102 · ActivateVDF v0114 · 交接案 vdf_ws_manager_fetch_quiet / vdf_ws_sync_worktree …)。
- 修法(只增不減):VDF 程式 · 收據 · 已發布版本冊 → 還原 ours;只增冊 → 聯集(ours 全部 + theirs 新增:元件 +41 · 交接案 +20 · 工作項 +39 · 編號 SSOT +19 · 各編號冊 +0~178 列;同號異文 110+ 列留 ours,待閘開後跑 `run CGC_MDL237 audit`);VRN-2 自己的 5 份交接文件不動。
- 驗證:三本 JSON 冊格式照舊、所有編號冊 code 唯一、我方案子與標記都回來;還原的 ENG093 v0105 自測 16/16(其餘要 duckdb,容器沒有)。

**VCGC 閘(擋住 CI · closeout · sdd · registry-sync · 編號 · handoff test 全部 `run`)**
- `CGC_MDL223 FlowConsistency.gate()` → `missing ["VRN"]`:main 上 VRN-2 的管理器尾版 `VRN_SystemManager_v0254.py` 沒有 `VIA_FROM_VCGC`、沒有 `def main`;而且 VRN-2 自己的 `VRN2_ChainShip check` 判 RED:**缺 `VRN_SystemManager_v0242.py` · `v0248.py` · `v0253.py`**(v0244 / v0249 / v0254 的前版,倉內與任何分支都沒有)· 引用冊缺 8。
- 這三個檔只在 VRN-2 的桌機;要由 VRN-2 跑 `VRN2_ChainShip ship --commit` 補船,閘才會開。VDF 只攤開不代修(四系統對等)。
- 在閘開之前:VDF 的擷取 / 管理員直接跑(`python VDF_SystemManager_v0162.py …`)不受影響;只有經 `via-vcgc run` 的路徑被擋。

**閘開之後要補的 VDF 債(本批先登記)**:`VDF_ENG056_ChipBackfill_v0108.py` · `VDF_MDL011_AkshareFetcher_v0103.py` 編號 + registry-sync;closeout ② 點名的 VDF 案(qg_onebridge · vdf_akshare_v0101 · vdf_akshare)重跑;編號 audit 遺失 0 · 改身分 0 · 重號 0。
