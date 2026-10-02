# CPU 最大加速 · 三系統實測 · 工具使用盤點(2026-10-02 收尾記錄)

操作員令:「全部系統在 CPU 架構下最大加速化 · 完成 VCGC VRN VDF 實測輸出結果盤點驗證即編號一切記錄一切現況即收尾 · 有用到沒用到的工具功能紀錄全部有備份上傳收尾 CLOSE OUT」;中途「允許開閘」。
登錄:VCGC-REQ129(需求冊 v0151)· 交接工作項 `VCGC-REQ129:*`。完整明細:`docs/VIA_S20261002_ToolUsage_v0100.json`。
環境:雲端容器 4 核 · 15 GB;無 pwsh;不裝套件。

## 一、CPU 最大加速

**量測先行**:全功能串測 133 站一站接一站,牆鐘 609s,取樣 4 核忙碌率 19–26%(等於只用一核)。
C-* 交接案站 62 站共 420s,彼此不相依 → 加速的槓桿在「並行」,不在執行緒參數(數值函式庫沒設參數時本來就用滿核心)。

| 項目 | 前 | 後 |
|---|---|---|
| C-* 62 站(`test --full --only C-`) | `--jobs 1`(= 前版)339s | 平行度 4:**113s(3.0 倍)**· 62 站燈號全同 · 順序全同 |
| 全功能串測 `--full` 134 站 | 609s(前版,沿用模式,含 6 站沿用) | **431s**(全部重跑不沿用;C-* 63 站分 4 段並行) |
| 教訓帳並行寫入(6 行程 × 100 筆) | v0102 無鎖:**600 筆剩 24 筆** | v0103:600/600 · 重號 0 |
| VDF 鏈 | 14s · CPU 97%(已吃滿,不需再並行) | — |
| VRN 鏈 | 74s · CPU 92%(本來就層內並行 POOL=4) | — |

做法(新尾版,前版一字不動):
- `CGC_MDL224_TestAuto v0104`:平行度 = 加速器 `VeritasCeleritas.thread_budget("aggressive")`(實體核數 × 記憶體壓力係數;本機 4;`--jobs N` / `VIA_TEST_JOBS` 可改,1 = 前版)。只並行盤點冊上連續一段、真的要跑的 C-* 站;夾在中間的 V/S/E/I/L/P 站照序列;同引擎同線;進度暫存加鎖。
- `CGC_MDL058_Lessons v0103`:教訓帳跨行程鎖(fcntl / msvcrt)+ 原子寫入 + 讀到半截檔丟例外不當空帳(前版會蓋掉整本只增帳——不並行也會在背景監控與前景同時失敗時發生)。
- VCGC v0188 / v0189 快取:暫存檔換上 + 讀取防護,並行最壞只是沒命中重算(已核)。事件帳逐行追加(已核)。

## 二、三系統實測

| 系統 | 結果 |
|---|---|
| VCGC 全功能串測 | 134 站:綠 120 · 黃 12 · 紅 2(收尾前;紅 = 新尾版待 registry-sync / 編號,收尾 ④⑤ 處理後重驗)|
| VDF 鏈 | 未開閘:綠 7 · GATED 1 · NODATA 2;**開閘後(只在本次指令帶 VIA_NET_CONSENT)綠 8 · 紅 0 · NODATA 2**(3a/3b features_daily 表不在;容器連 Yahoo 429 · TWSE 連線被重置 → 落庫要在工作站)|
| VRN 鏈 | 未開閘:綠 44 · GATED 1 · NODATA 3 · ABSENT 3;**開閘後綠 45 · 紅 0 · NODATA 3 · ABSENT 3**(缺 paddleocr / pdfplumber / pydantic:容器不裝套件)|

本輪修掉的紅:
- C-onepage(教訓帳同簽名 5 次):過期判定拿捨入到 0.1 小時的年齡比時限 → `CGC_MDL254 v0101` 用未捨入值。
- V-systems VRN logic RED:VRN 邏輯冊 3 個指標落後尾版(ENG086 v0119 · SUP_MDL746 v0102 · SUP_MDL743 v0110)→ 照建冊器指示 `via_vrn_logic_book build` 重建,55/55 在尾版 → GREEN。
- V-systems:系統卡 rc 2(STALE/NODATA)照設計記黃(盤點冊 yellow_rc),rc 1 才紅。

照實留下(交接 PENDING):
- VDF 卡書 STALE:照指示 PEIS scan + book 重建後不同步反而 1 → 8(兩把尺:PEIS 建冊範圍 ≠ VDF_SystemManager 檢查範圍)→ 已還原,不硬改。
- `CGC_MDL092 ConsolidationAudit` 預設動作就地重寫 3 本冊,在無庫的容器把 Schema Registry 真表結構(440 行)蓋成「庫缺」→ 已還原,待出新尾版(庫缺不寫 · 寫冊要 --apply)。

## 三、工具 / 功能使用盤點(本容器事件帳)

事件 1753 筆(2026-09-30 16:26:31 → 2026-10-02 18:37:31)· 不同目標 107 個 · 動詞:run 1510, sync-check 87, registry-sync 36, matrix 22, status 20, token 18, tools 13, ssot 4, help 3, inventory 2。
工作站上的使用(PS 短令)不在本帳;容器沒有 pwsh,PS 入口只做文字檢查。

### 工具鎖冊七家

| 家族 | 鎖定檔 | 本容器直接執行次數 | 啟用時間 |
|---|---|---|---|
| accelerator | VeritasCeleritas_v1141.py | 0 | — |
| network | VeritasAegisNexus_v1652.py | 0 | — |
| layout | SUP_MDL743_GenericLayoutHub_v0110.py | 6 | 2026-10-02T17:49:20+00:00 |
| nlp | SUP_MDL866_VIAUnifiedNLPOrchestrator_v0106.py | 9 | 2026-10-02T17:49:27+00:00 |
| token | CGC_MDL158_VIAPanoramaAuditRepair_v0117.py | 13 | — |
| frame | SUP_MDL755_VIAPolarsFrame_v0100.py | 0 | — |
| praddle | VRN_ENG398_PraddleExtractor_v0100.py | 11 | 2026-10-02T17:46:53+00:00 |

加速器 · 網路 · frame 的「直接執行 0」不是沒用:它們經全樹 `[VIA:ACCEL-BRIDGE]` / 網路橋 / 鏈站 0a·0b 間接載入(VDF 鏈 0a 加速器掛載 GREEN、開閘後 0b 網路工具掛載 GREEN)。

### 用到最多的 25 個目標

| 目標 | 次數 |
|---|---|
| CGC_MDL140_HandoverConsole | 503 |
| CGC_MDL149_VeritasCentralGovernanceConsole | 268 |
| CGC_MDL237_NumberingSystem | 123 |
| CGC_MDL247_SSOTPanorama | 116 |
| CGC_MDL245_SDDValidator | 65 |
| VRN_SystemManager | 53 |
| CGC_MDL224_TestAuto | 52 |
| CGC_MDL254_ReviewOnePage | 37 |
| CGC_MDL253_ToolingInventory | 27 |
| VDF_SystemManager | 25 |
| CGC_MDL095_DeckServer | 25 |
| VIA_Panorama | 19 |
| CGC_MDL158_VIAPanoramaAuditRepair | 13 |
| CGC_MDL233_ToolActivate | 13 |
| CGC_MDL221_SystemBackup | 12 |
| CGC_MDL209_VdfStart | 12 |
| CGC_MDL240_EnvManager | 11 |
| CGC_MDL248_FullCheck | 11 |
| CGC_MDL182_ReportFieldRulers | 11 |
| CGC_MDL230_ToolCoverageProbe | 11 |
| CGC_MDL170_VDFChainRunner | 11 |
| CGC_MDL172_VRNChainRunner | 11 |
| VRN_ENG398_PraddleExtractor | 11 |
| SUP_MDL866_VIAUnifiedNLPOrchestrator | 9 |
| VDF_ENG087_MarketListGovernance | 9 |

### VCGC 功能(盤點冊 134 站)

全部 134 站本輪實跑(`--full`)。非綠:

| 站 | 燈 | rc |
|---|---|---|
| V-handoff-check | YELLOW | rc 1 |
| V-ssot | YELLOW | rc 2 |
| V-ssot-plan | YELLOW | rc 2 |
| V-ssot-panorama | YELLOW | rc 2 |
| V-sdd | RED | rc 1 |
| V-workflow | YELLOW | rc 1 |
| V-inventory | YELLOW | rc 2 |
| V-check | YELLOW | rc 2 |
| V-panorama | YELLOW | rc 2 |
| V-systems | YELLOW | rc 2 |
| V-dbm | YELLOW | rc 2 |
| E-number-audit | YELLOW | rc 2 |
| P-entry | YELLOW | rc 2 |
| V-closeout | RED | rc 1 |

### 沒用到(沒被任何活引擎引用)的引擎

`CGC_MDL092` census(唯讀算)本容器 **210 件**(已提交冊上 2026-09-19 為 101 件;冊沒有被覆寫),依群:

| 群 | 件數 |
|---|---|
| OTHER | 119 |
| GOV_TEST | 31 |
| FETCH_NET | 23 |
| PLOT_UI | 12 |
| OCR_DOC | 8 |
| FINANCE_CALC | 7 |
| NLP_TEXT | 4 |
| STORE_DB | 3 |
| FLOW_REGIME | 3 |

全部 210 個檔名在 JSON 明細 `unused_files`。全群 PENDING_OPERATOR:要不要整併、併去哪是操作員裁量,本輪不動任何引擎。

## 四、備份 · 上傳

倉即備份:程式 · 冊 · 本記錄經 closeout ⑦ 提交、⑧ 推上 GitHub(分支 `claude/ecstatic-brahmagupta-ec19u9`,PR tonykuni/movies-dataset#434)。
`VIA_Reports/` 不進 git(容器本機產物),所以本輪實測數字寫進本檔與 JSON 明細一起上傳。
