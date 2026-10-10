# 三系統對等獨立 · 全景檢視(2026-10-10 · VCGC-REQ176 · 政策 L120)

操作員原話:「不再視為一入口 三系統獨立 政策及全部寫入 VCGC VRN VDF SYSTEM MANAGER獨立互不影響但互相監控而獨立運作功能」「全景式檢視這是重大改變三系統」。

新規則(L120):VCGC · VDF · VRN 三個 SYSTEM MANAGER 對等,各是自己系統的入口;互不影響(不改他系統的正本 / 冊 / 號 / 檔);
互相只讀監控(看對方自報的燈與收據,只攤開不代修);各自獨立運作。不再有唯一入口。

| 系統 | 自己的入口 | 座位(SubsystemProbe) |
|---|---|---|
| VCGC | `supportive modules/registry/CGC_MDL149_VeritasCentralGovernanceConsole_v*.py` 尾版 | — |
| VDF | `functional modules/VDF/VDF_SystemManager_v*.py` 尾版 | `VDF_SystemManager_v0151.py` GREEN |
| VRN | `functional modules/VRN/VRN_SystemManager_v*.py` 尾版 | `VRN_SystemManager_v0151.py` GREEN |

## 一、已改(本批)

| 層 | 改了什麼 | 證據 |
|---|---|---|
| CI | 兩條 VCGC Windows 檢查(sole entry / numbering / handoff / SDD contracts · PowerShell 7 conflict guard / all-green gate)永久刪除 | PR #519 合併;run 38078270953:windows-uat · vdf-uat · vrn-uat 全綠 |
| 政策 | `VIA_Policy_Laws_SSOT_v0112.json` +L120;L111 加 `amended_by`(③ 母系統單向監控、⑥ 一對二 → 三方對等互相監控;①②④⑤ 照舊);L119 加 `extended_by` | VCGC 讀冊:律 117 · 不衝突通過 · 冗餘 0 |
| AI 功能卡 | `VIA_AI_FunctionCard_SSOT_v0102.json`:`enter` / `go` 改寫為 VCGC 自己的入口與編排;`entry.peers` 列三系統各自入口;`never` +L120 | `via-vcgc functions` 照印新卡 |
| 需求冊 | `VIA_Requirements_SSOT_v0188.json` +VCGC-REQ176(五則原話逐字,PARTIAL) | — |
| 接手說明 | `CLAUDE.md` · `AGENTS.md` 加三系統對等段;「同一 VCGC 入口」「測試必須經 VCGC」改掉;功能卡改指尾版 | — |

## 二、全景檢視結果(經 VCGC)

| 視角 | 指令 | 結果 |
|---|---|---|
| SSOT 六族 × 四層 | `ssot panorama` | YELLOW,與改前相同,零新紅(VCGC 註冊黃 = 掃橋器 v0111 待 registry-sync) |
| 同步 | `sync-check` | SDD 舊有 X-NUM 紅(尾版待編號),非本批造成 |
| 全樹 | `monitor scan` | ACCEL 557/557 · NET 123/123 · PS 模板 177/177;**ACCEL-USE 6/557**(橋在、幾乎沒有程式真的呼叫加速器) |
| 子系統座位 | `run CGC_MDL222_SubsystemProbe` | VDF / VRN 各自座位 GREEN |

## 三、還沒改(要操作員選)

1. **工作流冊**:`VIA_Workflow_VCGC_SSOT_v0126.json` 8 處(WKF001 實測「唯一入口 v0106 起」· WKF004 「唯一入口一輪」· WKF008 「VIA 唯一接觸口控制」· WKF009 「唯一接觸口閘」· WKF020 「L111 一對二」)
   與 `VIA_Workflow_Hub_SSOT_v0102.json`(組成 hub VCGC-WKF001 → loop_vdf → loop_vrn → exit;executor「唯一編排」)。
   改成三方對等 + 互相監控,要連帶出 SDD 驗證器新版(X-COMP 目前驗的就是 hub → loop 組成)。
2. **程式閘 `VIA_FROM_VCGC`**:約 33 個家族(VDF 約 16:SystemManager · ENG054 / 086 / 087 / 094 / 109–113 / 117 / 230 / 231 / 234 · MDL008;
   VRN 約 16:SystemManager · ENG109 / 110 / 113 / 114 / 392–400 · OCR / Lib 外掛;VAP_SystemManager)。兩條路:
   - 甲(零程式變更):政策定義 `VIA_FROM_VCGC` = 「經任一系統自己的 manager / 啟動器啟動」,只是舊名字;
   - 乙(逐家族新版號):各 manager 認自己的旗標(VIA_FROM_VDF / VIA_FROM_VRN),舊旗標照收相容。
3. **加速器真用到**:ACCEL-USE 6/557 —— 與操作台慢的根因同一件事(VDF `engine matrix` 52 秒,101/110 秒在 VCGC 盤點工具 CGC_MDL253 重複解析同一批引擎)。
