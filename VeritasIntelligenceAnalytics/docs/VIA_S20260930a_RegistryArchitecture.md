# 側線 2026-09-30 a:編號 · 註冊 · SSOT 治理架構重整與風險治理(VCGC-REQ084)

主線批號由併線的手指定(L25)。本批接在 main e48318c38(PR #377 併入)之上。新版號用 LL334 掃過 242 個遠端分支,沒有撞號。

- 架構正本:`VIA_Registry_Architecture_SSOT_v0100.json`(VIA-VCGC-SSOT059)。
- 量到的風險寫成 R01–R15,能自動擋的都做成防線(新版號檔,舊版不動)。
- 需要操作員裁定的(正則 · 同義字 · 命名 · 紅列)只攤開,不自動改。

## 一、操作員原話(逐字)

| # | 原話 | 入冊 |
|---|---|---|
| 1 | SSOT / 自動編號 / 含版本及時間自動註冊 / WORKFLOW SSOT / REGEX / 同義字管理等將邏輯管理編號架構及可能的風險從新整理優化一遍 | VCGC-REQ084(需求冊 v0106,PARTIAL) |
| 2 | 繼續 | 非需求(續行) |
| — | 既有範圍內註冊 不要擴張範圍(2026-09-29,仍有效) | VCGC-REQ078;本批編號只登本批 13 檔 |

需求冊 v0106 `reviewed` 149 → 152 則;舊 109 條一字不動,`prior` 指回 v0105。

## 二、架構正本:VIA_Registry_Architecture_SSOT_v0100

### 2.1 原則(7 條)

1. 一個實體一個主號;其餘號碼只當別名,且別名要能由對照鍵推回主號。
2. 號碼是身分:發出去不改、不刪、不重用。
   - 不見了記 gone / RETIRED / retired_at。
   - 改號只准讓號,並留 recoded_from · recoded_at · recode_why。
3. 版號檔(snapshot)發布後不可就地改,要改就出新版號檔(`prior` 指回前版)。
   - 活冊(living)可就地寫,但只增不減,狀態轉移要帶時間。
4. 指標列(pointer)只由它的閘改。
   - 例:工具啟用閘 · 席位冊。
   - 歷史留在 previous / candidate 列,不靠覆寫。
5. 新寫入的時間一律 UTC ISO-8601 帶時區(`+00:00`)。舊格式照舊保留,不回頭改寫。
6. 寫入只登本批範圍;全量重建要操作員下令。
7. 先提交再編號:編號的 updated_at 取來源的 git 提交時間,未提交的檔不發號。

### 2.2 七層

| 層 | 名稱 | 正本 | 誰寫 |
|---|---|---|---|
| A0 | 檔案家族名 `<系統>_<MDL\|ENG><三碼>_<名>_v<四碼>` | `VIA_Naming_Registry_v0100.json` | 命名冊(先發先得 · 實體檔零改名) |
| A1 | 元件註冊 `VIA-<類>-<四碼>` | `VIA_Component_Inventory_SSOT_v0100.json` | VCGC `registry-sync`(v0179 起新時間寫 UTC) |
| A2 | 中央編號(26 類 × 子系統 × 分類;鍵 = 內容鍵@版本) | `VIA_Numbering_SSOT_v0100.json` + `VIA_NumberBooks/*.jsonl` | CGC_MDL237(v0109 起 `--apply --scope`) |
| A3 | 工具版本與啟用(六家) | `VIA_ToolVersion_Lock_v0100.json` + `VIA_EngineVersion_Register_v0100.json` | CGC_MDL233 `tools activate`(v0104 起席位唯一 · activated_at) |
| A4 | 治理代碼 REQ / WKF / STP | 需求冊 · 工作流冊 · 燈鎖冊(版號冊) | 每次改出新版;SDD 驗證 CGC_MDL245 |
| A5 | 政策與待辦:律 L · 教訓 LL · 掉球 Z · 交接工作項 | 律冊 · 掉球帳 · 交接冊 | 律冊(活冊)· 批文件 · 交接台 CGC_MDL140 |
| A6 | 帳本(每批一筆,只增) | `VIA_AutoCode_Registry_v0100.json` | 每批收尾 |

### 2.3 十一個號碼空間與主號

| 空間 | 例 | 層 | 地位 |
|---|---|---|---|
| NS-NM | `CGC_MDL237` | A0 | 主號(檔案家族) |
| NS-COMP | `VIA-FNC-12330` | A1 | 別名(元件註冊視圖) |
| NS-TOOL | `VIA-TOOL-0194` | A3 | 主號(工具;與 NS-COMP 共用 VIA-TOOL 空間) |
| NS-NUM | `VIA-VCGC-MDL1476-FNC001` | A2 | 中央主號(函式 / 類別 / SSOT 冊 / 正則 / 同義字 / 參數 / 政策…) |
| NS-FM | `VIA-VDF-FM-TW-EQT-0149` | A2 | 中央主號(金融商品) |
| NS-GOV | `VCGC-WKF001-STP007` | A4 | 主號(治理代碼;A2 鏡像 = `VIA-` + 代碼) |
| NS-LAW | `L50` · `LL443` | A5 | 主號(律 / 教訓) |
| NS-Z | `Z280` | A5 | 主號(掉球;LL334 全分支掃過再取) |
| NS-R22 | `TL-0017` | A2 | 別名(R22 工具 / 測試表) |
| NS-LEDGER | `1364` | A6 | 主號(帳本序) |
| NS-BATCH | `側線 2026-09-30 a` | A6 | 主號(批次;主線批號由併線的手指定) |

每個空間的正則寫在正本 `namespaces[].pattern`。實體主號(`entity_primary`)的規則:

- 檔案家族:主號 NS-NM,元件冊與中央編號是別名。
- 一個版本:主號 NS-NUM 的 MDL / ENG 列。
- 函式 / 類別:主號 NS-NUM FNC / CLS,元件冊 VIA-FNC/CLS 與命名冊 FNC### 是別名。
- 鎖版工具:主號 NS-TOOL(engine 列 = 席位)。
- 需求 / 工作流 / 步:主號 NS-GOV。
- SSOT 冊 · 正則 · 同義字 · 參數:主號 NS-NUM。

### 2.4 冊的可改性 · 時間 · 登錄次序

- **可改性**分四類:snapshot(版號冊)· living(活冊)· pointer(指標列)· generated(產出)。
  - 實測:多版家族 22 家 63 檔中,有 13 檔發布後又被就地改(其中 3 檔是尾版)→ R01。
- **時間**:新寫入 `YYYY-MM-DDTHH:MM:SS+00:00`。
  - 舊格式五種照舊保留,並記在正本裡,例如編號冊 `+0000`、元件冊無時區本地時間、帳本 `YYYY-MM-DD HH:MM`。
- **登錄次序**(8 步):
  1. token → functions → handoff check
  2. 出新版號檔
  3. 先提交
  4. registry-sync --apply
  5. 編號 `--apply --scope` → audit
  6. (只有鎖版工具)先登 candidate 列 → activate
  7. SDD → handoff test / checkpoint
  8. PR → CI → merge commit

## 三、風險冊(R01–R15)

| # | 風險 | 嚴重度 | 防線 | 狀態 |
|---|---|---|---|---|
| R01 | 已發布版號冊被就地改(需求冊 v0104 事件 · 啟用閘改寫名冊尾版) | 高 | CGC_MDL237 v0109 audit IMMUT(紅)· CGC_MDL233 v0104 名冊改寫出新版 | 本批加防線 |
| R02 | 交接收據沿用看不到新尾版 | 高 | CGC_MDL140 v0102 相依集合比對 | 本批修 |
| R03 | 全量重建把積壓混進本批 | 中高 | CGC_MDL237 v0109 `--apply --scope` | 本批修 |
| R04 | 未提交就發號(updated_at = uncommitted) | 中 | `--scope` 不收未提交 · audit UNCOMMITTED | 本批修 |
| R05 | SSOT 冊內容指紋過期 | 中 | audit FPSTALE | 本批加防線 |
| R06 | 同一版本兩個工具號 · 席位語意沒寫明 | 中高 | VIA-TOOL-0212 改 candidate · CGC_MDL233 v0104 席位唯一 · audit DUPREG | 本批修 |
| R07 | 同一實體多套號碼、沒有對照表 | 中 | 正本定主號與別名 · audit XCODE(共用空間撞號) | 規則已定;對照報表待辦 |
| R08 | 時間格式不一 · 元件冊時間沒時區 · 鎖冊沒啟用時間 | 中 | VCGC v0179 新時間 UTC · CGC_MDL233 v0104 activated_at · audit TIMEFMT | 本批修(舊值不改寫) |
| R09 | 交接待辦與掉球帳沒對帳 | 中 | 本批 Z280 結案(只增結案列);對帳列交接待辦 | 待辦 |
| R10 | 正則分歧(台股代號 4 本冊判法不同 E4)· 無版號正則檔 | 中 | SSOT 全景 booksync | 待操作員裁 |
| R11 | 同義字一詞兩主 15 組 · 同詞多義 10 · 拒絕閘漏口 8 | 中 | SUP_MDL749 additive / drift | 待操作員裁 |
| R12 | 命名異常:同號異名 12 組 · 版號異形 44 · 沒版號 .py 841 | 中 | SSOT 全景命名族 | 待操作員裁 |
| R13 | 已鎖工作流尾版換了未重驗(X-LOCK 6) | 中 | SDD X-LOCK | 待辦 VCGC-REQ030:relock |
| R14 | 冊上宣告碼 ≠ 發出號(紅列 21) | 低中 | audit 冊內一致 | 待操作員裁 |
| R15 | 薄尾讀尾版:新版一落地就被讀到 | 低中 | 登錄次序(先提交 → 註冊 → 編號 → 驗) | 流程規範 |

## 四、本批交付

| 檔 | 做什麼 | 號 |
|---|---|---|
| `CGC_MDL237_NumberingSystem_v0109.py` | `--apply --scope`:只登相對 base 的變更檔,合併時舊列不動,只刷新來源在範圍內的列。寫後自核,不過就整批還原。`scope` 乾跑列範圍。`audit` 多「註冊完整性」六檢:IMMUT / DUPREG / XCODE(紅)· FPSTALE / UNCOMMITTED / TIMEFMT(黃) | VIA-VCGC-MDL1484 |
| `CGC_MDL140_HandoverConsole_v0102.py` | 收據沿用前,重掃 case 宣告樣式 + VCGC 入口樣式,和收據的相依集合比對;新尾版落地 = 證據失效,重跑 | VIA-VCGC-MDL1481 |
| `CGC_MDL233_ToolActivate_v0104.py` | 檢查多「席位唯一」;鎖冊帶 activated_at(UTC)· activated_by;名冊換名出下一個版號檔,前版一字不動 | VIA-VCGC-MDL1483 |
| `CGC_MDL149_VeritasCentralGovernanceConsole_v0179.py` | `registry-sync --apply` 後,只把本輪新增 / 變更的時間欄補 UTC 時區,舊記錄不改寫 | VIA-VCGC-MDL1482 |
| `VIA_Registry_Architecture_SSOT_v0100.json`(新) | 架構正本(第二、三節) | VIA-VCGC-SSOT059 |
| `VIA_Requirements_SSOT_v0106.json` | +VCGC-REQ084 | VIA-VCGC-SSOT060 · VIA-VCGC-REQ084 |
| `VIA_Workflow_VCGC_SSOT_v0104.json` | WKF001 / WKF003 掛 REQ084;WKF003-STP006 動詞改 `--apply --scope · audit` | VIA-VCGC-SSOT061 |
| 引擎版本冊(活冊) | VIA-TOOL-0212 role engine → candidate,並帶 corrected_at 與更正說明(R06) | — |
| 交接冊(活冊,只增) | 新 case `activation`;handoff case 相依改樣式;工作項 +6(4 件 VERIFIED · 2 件帶理由待辦);`VCGC-REQ075:reuse-glob` → VERIFIED | VIA-VCGC-LGC164–170 |
| 功能卡 · 席位冊 · 元件冊 | 第 9 步改 `--apply --scope`,禁令加「版號冊不就地改」;席位指向 v0179;registry-sync 同步 | 指紋 SSOT007 / 052 / 055 更新 |
| 掉球帳(只增) | 文末追加 `~~Z280~~(結)` 結案列,原列不動 | — |

## 五、實測

- **自測**:
  - CGC_MDL237 v0109:本版 12/12,前版鏈 `[來源編號] checks=9; fail=0`。
  - CGC_MDL140 v0102:本版 5/5,前版 `[交接回歸] fail=0; tests=33`。
  - CGC_MDL233 v0104:前版鏈 8/8 + 4/4 × 3,本版 +5/5 PASS。
  - VCGC v0179:本版 5/5,v0178 8/8,`[交接入口] fail=0`。
- **編號(只登本批)**:
  - 範圍 13 檔 = 本批提交的檔,未提交 0。
  - 新增 +79 列:MDL +4 · FNC +63 · CLS +1 · LGC +7 · REQ +1 · SSOT +3。
  - 刷新:LGC 3 列 · SSOT 指紋 3 列 · OPT 234 列(掉球帳本批有改,updated_at 換成本批提交時間)。
  - audit 基準 main e48318c38:101,626 → 101,705 · 遺失 0 · 改身分 0 · 重號 0。
  - 註冊完整性六檢全 0(GREEN)。冊內不一致只剩既有紅列 21(R14)。
- **SDD**:
  - X-NUM 綠:新尾版全有號;WKF · STP · REQ 250 個全編號。
  - 黃只剩兩項既有的:X-REQ-OPEN 18、X-LOCK 6。X-LOCK 處數不變,只是尾版名換成 v0179 / v0109。
- **SSOT 全景**:
  - 編號前:自動編號@VCGC 缺號 4,SDD 紅(X-NUM)。
  - 編號後:272/272 有號,缺號 0。
  - 其餘黃都是既有待裁項(R10 / R11 / R12 / R13)。
- **交接**:
  - v0102 一上,含 VCGC 入口樣式的舊收據全判失效(新尾版 v0179 不在收據裡)。這正是 R02 要擋的盲點。
  - 9 案全部重跑:activation · handoff · numbering · entry · sdd · panorama · token · provenance · manager。結果見第六節。

### 本批自己踩到的一次(已改)

- 我原本就地把 Z280 原列劃線。編號冊用列文字認身分,原列文字變了,就判 Z280 那列 gone(AMBER)。
- 掉球帳 2026-09-28 起的慣例是「原列不動,文末追加 `~~Zxxx~~(結)` 結案列」,例如 Z218 · Z237 · Z243。
- 已改回只增寫法:編號冊退回、重登。OPT 只剩時間刷新,Z280 維持 GREEN,gone 0。

## 六、交接

- 9 案重跑,全部 rc 0、標記命中(每案 67–83 秒)。舊收據照 v0101 原格式存進 `evidence/history`(只增)。新收據的相依都含 v0179。
- `handoff checkpoint` → `handoff check`:**GREEN**(findings 0 · 待辦 27 · 可沿用 17)。
  - 驗收燈 **YELLOW**(X-LOCK 6 · 需求未全落地 18),不寫成成功。
- 總控頁:新尾版的說明變了,合約 test_11 紅。照 LL49 在只含已追蹤檔的乾淨工作樹重產,差異只有產生時間和模組表一列,合約 19/19。
- 帳本 +1364(只增)。教訓帳裡中途那次預期紅燈(收據被 v0102 判失效)的 VCGC_FAIL 記錄沒有收進來。

帶理由的待辦:

- AI:
  - `VCGC-REQ084:reconcile`(R09 兩本待辦帳對帳)
  - `VCGC-REQ084:crosswalk`(R07 三冊號碼對照報表)
  - `VCGC-REQ030:relock`(R13;`run CGC_MDL245_SDDValidator real` → `lock --apply`)
- 操作員:
  - R10 正則收斂
  - R11 同義字裁定
  - R12 命名(`VCGC-REQ080:naming`)
  - R14 紅列
  - `VCGC-REQ078:backlog`(全量積壓要不要登,要下令)

下一手照做:

1. 進場依序跑 `token` → `functions` → `handoff check`。
2. 改冊前後各跑一次 `ssot panorama`。
3. 出新版號檔 → 提交 → `registry-sync --apply` → `run CGC_MDL237_NumberingSystem --apply --scope` → `… audit`。
   - audit 必須遺失 0 · 改身分 0 · 重號 0,註冊完整性不能有紅。
4. 鎖版工具換版:新版先在引擎版本冊登 `role=candidate`,再 `tools activate <家> <檔> --apply`。
5. 已發布的版號冊(需求 · 工作流 · 燈鎖 · 工具名冊 · 本架構冊)不就地改,改就出新版號檔。
