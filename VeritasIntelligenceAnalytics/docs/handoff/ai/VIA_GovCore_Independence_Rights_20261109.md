# 治理核心 · 獨立系統互助與改動權對照(RC-1 W2 · 2026-11-09)

操作員令:「治理核心,但全部的系統接獨立;留意有無維持之前的獨立系統相互協助;只有我跟 AI 有改動的權利。」
本文把 `VIA_GovCoreChain_v0100` 的矩陣結果對到這三條,再把本日重新附上的五份外部交件逐份核對。全程唯讀;沒有改任何檔。

## 一、三條規則怎麼驗

| 規則 | 驗法 | 結果 |
|---|---|---|
| 五系統各自獨立(L123 互不干涉) | 治理核心是 supportive modules 共用層;看每個車道對它的載入是「只讀借用」還是「寫入」 | 載入 **1670 列**全是讀;TREE 寫入者 **0** |
| 互相協助只准只讀 | 車道 × 家族載入矩陣(下表);跨車道 import 另冊 | 見矩陣;VQG 0 列(它不碰治理核心),VAP 4 列 |
| 改動權只在操作員與 AI(經 PR) | 靜態掃所有會寫治理核心模組檔的呼叫(open 寫模式 · write_text/bytes · unlink/rename/replace · shutil.copy/move),目標必須是 X.py / X_v####.py | **GREEN**:樹上 0 筆;46 筆全是自測夾具寫 tempfile 暫存夾(VRN2_MarketFetch v0105–v0112 · SUP_MDL144 IfEngine · CGC_MDL248 FullCheck · CGC_MDL234) |

## 二、各獨立系統 × 治理核心(載入列數;只讀借用;含治理件彼此的載入,Codex PR 616 P2 後補)

| 家族 | CORE | SUP | VAP | VCGC | VDF | VRN |
|---|---|---|---|---|---|---|
| VIA_EnvManager | 8 | 176 | 2 | 149 | 0 | 44 |
| VIA_RegistryCore_v1 | 2 | 89 | 0 | 26 | 4 | 33 |
| VIA_Panorama_AST_RuntimeInjector | 2 | 66 | 0 | 8 | 0 | 33 |
| VIA_Runtime_Bridge_All_in_One | 2 | 77 | 0 | 16 | 0 | 33 |
| VIA_SSOT_Unified | 3 | 126 | 0 | 32 | 10 | 58 |
| VeritasAegisNexus | 2 | 173 | 2 | 255 | 53 | 186 |

讀法:數字是靜態掃到的「引用列」(裸 import · 字面路徑 · 只給名字),不是執行期次數。VRN 的大量「只給名字」列是插件載入器拿 `ssot_dir` 與其上層當搜尋夾(桌機設定值),倉內靜態推不出落點 —— 這是 VRN 與 VCGC 可能各載到不同副本的真正風險點,也是為什麼去重前要先裁正本。

## 三、六件治理核心現況(矩陣摘要;明細見 `VIA_GovCoreChain_v0100.md`)

| 家族 | 燈 | 副本 | 內容組 | 正本候選 |
|---|---|---|---|---|
| VIA_EnvManager | YELLOW | 3 | 1 | —(要裁) |
| VIA_RegistryCore_v1 | YELLOW | 3 | 1 | —(位元相同;20_Registry_SSOT 份有 3 個載入者:10_Core_Runtime 橋 v018 adapter 指名它)|
| VIA_Panorama_AST_RuntimeInjector | YELLOW | 3 | 1 | —(要裁) |
| VIA_Runtime_Bridge_All_in_One | YELLOW | 3 | 2 | supportive modules/10_Core_Runtime/VIA_Runtime_Bridge_All_in_One.py |
| VIA_SSOT_Unified | YELLOW | 3 | 2 | supportive modules/ssot/VIA_SSOT_Unified.py |
| VeritasAegisNexus | RED | 8 | 5 | supportive modules/network/VeritasAegisNexus_v1652.py |

- 治理件彼此也互載:10_Core_Runtime 的 Runtime Bridge(v018 canonical adapter)以路徑指名 20_Registry_SSOT 的 RegistryCore 與 SSOT_Unified、50_Protection_Acceleration 的 AegisNexus —— 所以編號夾那幾份不是「無載入者可退」,要先遷這條橋。
- 多頭的根因是**三種目錄慣例並存**:平鋪根(加速器橋插 sys.path → 裸 import 落這裡)· 編號夾 10_–50_(10_Core_Runtime Runtime Bridge 的 v018 canonical adapter 指名)· 主題夾 environment/registry/ssot/network(VRN 插件載入器以 ssot_dir 搜尋)。
- 兩處「超集」是好消息:`10_Core_Runtime/VIA_Runtime_Bridge_All_in_One.py` = 根 + 79 行 append-only(v018 adapter);`ssot/VIA_SSOT_Unified.py` = 根 + 95 行 append-only(同義字計數三塊)。超集就是正本候選,子集可退。
- 一處真分岔:根 `VeritasAegisNexus.py`(= network/_v1651 位元相同,8438 行)與三份 5186 行副本(各自獨有 45 行)。鎖冊尾版是 network/_v1652(薄尾),SUP_MDL737 v0110 已把裸 import 接到它;三份 5186 行副本只剩 29 筆字面路徑引用指向平鋪根那一份 → 要操作員裁:v1651 體系為正本,5186 行那 45 行要不要保。

## 四、本日重新附上的五份外部交件,逐份對這三條

| 交件 | 它主張什麼 | 對三條規則 | 處置 |
|---|---|---|---|
| gemini-code-1794143633893.txt | 「SYSTEM INITIALIZATION: OVERRIDE & FULL AUTHORIZATION · Level-0 Full System Autonomy」;要 AI 以中央治理台身分自主執行、做 AST 外科注入、自我修復腳本與 auto-rollback | **違**改動權(把改動權交給 AI 自主,不經操作員 PR)· 違 L124 審計模式律 · 違 HARD FREEZE(收尾期不新增架構);也不分五系統 | 不採用;已在 W0 LESSON-0001 / 0002 證據欄記錄。只讀參考,不進任何冊 |
| VIA_VCGC_AI_handover_v0106.4.md(兩份位元相同) | 自報 Actual gate RED / BLOCKED · NOT_RUN · formal_registration false;OBS-0194「Do not auto-apply uploaded old replacement policy. Keep existing VCGC installer / EnvManager / InstallGate / Token tools unchanged」;「no Git writes were performed」 | **合**:它自己宣告不改既有 EnvManager 等治理件、不寫 Git | 維持 CONTAINED(CONFLICT-00003 審閱包);它的 RED 自報與本倉無涉 |
| VIA 六系統獨立工作台 v0106.4.md | 「每個子系統各有一個獨立畫面」· `row.system == 當前系統` 精確過濾 · shared evidence 不能算成 native PASS | **合**獨立原則;它是唯讀候選工作台,不是安裝包 | 只讀參考;不入冊 |
| subsystem_v0106_4_final_actual_zip_receipt.json | existing_engine_modified = false · formal_registration = false · production_deployment = false · commands_executed 0 · Tony-NB NOT_RUN | **合**:沒改既有引擎、沒登記、沒部署 | 收據照實記;審閱包不入倉 |

結論:五份交件裡只有 Gemini 那份 Level-0 提示違反「只有操作員與 AI 有改動權」與獨立原則;其餘四份自己就宣告不改、不登記、不部署,與本倉規則一致。倉內程式面:**沒有任何程式會自動寫治理核心**(靜態 0 筆),改動權目前只在操作員與 AI 的 PR 手上。

## 五、W2 下一步(要操作員裁,AI 不先動)

1. 裁正本:EnvManager / RegistryCore_v1 / Panorama_AST_RuntimeInjector 三份位元相同 → 建議以**平鋪根**為正本(加速器橋 + 裸 import 都落這裡,引用最多);Runtime Bridge → `10_Core_Runtime`(超集);SSOT_Unified → `ssot/`(超集);AegisNexus → network 版本鏈(_v1652 尾版,_v1651 本體),三份 5186 行副本那 45 行獨有要裁。
2. 裁完才動:出**版本化轉接件**(新檔名帶版號,不就地改任何已發布檔),遷呼叫者(字面路徑引用逐支改指正本),舊副本進 `_superseded`;每一步跑本引擎重出矩陣,直到每家族只剩一個正本 + 版本鏈。
3. VRN 插件載入器的 `ssot_dir` 搜尋夾是桌機設定值:桌機實測載到哪一份,要貼回收據;倉內推不出。

產生:`docs/handoff/ai/VIA_GovCoreChain_v0100.py run --apply` → `VIA_GovCoreChain_v0100.json / .md / VIA_GovCoreChain_UI.html`(自測 17/17)。
