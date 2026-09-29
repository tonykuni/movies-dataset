# 側線 2026-09-29 h:元件冊發號避開他冊已發的號(VCGC v0174)—— Codex #373 P1 · VIA-TOOL 一號兩主 16 號

主線批號由併線的手指定(L25)。本批接在 PR #373(c57ad385)之後。

## 一、起因(實錄)

PR #373 合併後,Codex 審查留了一條 P1:`via-in` 在元件冊拿到的 `VIA-TOOL-0194`,引擎版本冊(`VIA_EngineVersion_Register_v0100.json`)早就給了 token 引擎(CGC_MDL158 v0116);編號 SSOT 也把 `工具/VIA-TOOL-0194` 對到 `TOOL-C017`。

不只查這一號,全倉實測:

| 號 | 引擎版本冊(手寫、先發) | 元件冊(registry-sync 後發) |
|---|---|---|
| 0179–0181 | 09-27 17:37 起:加速器載入器 · 網路載入器 · 網路本體 | 09-28 18:21:via-cnnfg · via-fwdval · via-lists |
| 0182–0193 | 09-27 17:37 – 09-28 14:13:nlp · layout ×2 · 網路載入器 · 三支 VDF 引擎 · 加速器載入器 · 網路本體 / 候選 / 載入器 · 工具閘 | 09-29 01:43:via-aaii … via-vrntab(12 支短令) |
| 0194 | 09-29 00:44:token 引擎 | 09-29 10:39(PR #373):via-in |
| 0195 | 09-29 02:35:frame 引擎 | ——(元件冊沒發到這號) |

引擎版本冊從 09-27 起在 `VIA-TOOL` 命名空間**自己發號**(列上寫 `"where": "this register"`),沒記回元件冊的計數器;元件冊之後兩次 registry-sync 把同號發給 15 支短令,PR #373 再把 0194 發給 via-in。**共 16 號一號兩主**:15 號在本批之前就撞了,本批上一手多撞 1 號。

根因:v0142 的 `registry_sync` 發號只看元件冊自己的 `counters[前綴] + 1`,不知道別的冊已經發過哪些號。

## 二、誰讓號

- 引擎版本冊的號先發,而且下游都照它引用:編號 SSOT `TOOL-C002…C018`、編號書 `VIA_NumberBook_TOOL`(`工具/VIA-TOOL-01xx`)、編號台帳 `TL-0002…0016`、批文件(`VIA_Progress_20260928_Rollout.md`、`VIA_S20260929a_TokenFirstStep.md`)。
- 元件冊那 16 筆短令的號,全倉只有元件冊自己用;例外是上一批 via-in 的批文件 g 和台帳 1360(本批補更正)。
- 所以讓號的是**元件冊**;引擎版本冊、編號 SSOT 的 `TOOL` 區、編號書、編號台帳一字不動。

## 三、改了什麼

| 檔 | 內容 |
|---|---|
| `CGC_MDL149_VeritasCentralGovernanceConsole_v0174.py`(新,薄尾) | ① `minted_elsewhere()`:他冊自己發的號(`where = "this register"`)算已佔用;只抄元件冊號的列(`where = "inventory"`)不算。② `registry_sync()`:新號從「計數器 · 元件冊已用最大號 · 他冊已發最大號」三者取最大再 +1,已佔用的號一律跳過;撞號那筆在 `--apply` 時改發新號,留 `recoded_from`(舊號清單)· `recoded_at` · `recode_why`;乾跑零寫;只有寫**正本**元件冊才讀他冊,暫存冊的行為和前一版一模一樣。③ 鏈上每一支持有 `registry_sync` 的模組都換成本版(同 v0172 換 `live_components` 的做法),涵蓋 registry-sync 動詞、`--layout-only` / `--nlp-only` 限定範圍的同步、hub 委派的同步、v0168 同步檢查的乾跑。④ 同步檢查多報 `registry.recode`,有撞號就算「待同步」。⑤ registry-sync 動詞多印一段發號結果,`--apply` 之後還撞就 rc 2 |
| `VIA_Component_Inventory_SSOT_v0100.json`(原冊) | 16 筆改號(下表)· `TOOL` 計數器 194 → 211;另外照常登錄 v0174 / 格子 v0504(新函式 · 改由新版定義的函式) |
| `CGC_MDL064_SelftestGrid_v0504.py`(新) | 站名檢數:Veritas 中央控管台 七十二 → **八十二**(v0174 +①~⑩,實印 82 檢);其餘站一字不動 |
| `VIA_VCGC_SubsystemSeat_v0100.json` | CONSOLE → v0174 |
| 編號冊 · 編號 SSOT · 驗證 SSOT · 台帳 | 見「五、登錄」 |
| `docs/VIA_S20260929g_ViaIn.md` | 補一行更正:via-in 的元件碼改為 `VIA-TOOL-0211` |

改號對照(舊號都記在該筆的 `recoded_from`):

| 短令 | 舊號 | 新號 | 舊號原主(引擎版本冊) |
|---|---|---|---|
| via-cnnfg | 0179 | 0196 | accelerator · loader · SUP_MDL737 v0108 |
| via-fwdval | 0180 | 0197 | network · loader · SUP_MDL740 v0115 |
| via-lists | 0181 | 0198 | network · engine · VeritasAegisNexus v1652 |
| via-aaii | 0182 | 0199 | nlp · engine · SUP_MDL866 v0105 |
| via-akshare | 0183 | 0200 | layout · prior · SUP_MDL743 v0106 |
| via-deck | 0184 | 0201 | layout · engine · SUP_MDL743 v0109 |
| via-export | 0185 | 0202 | network · loader · SUP_MDL740 v0117 |
| via-fwdvintage | 0186 | 0203 | sentiment · engine · VDF_ENG229 v0100 |
| via-managers | 0187 | 0204 | valuation · engine · VDF_ENG230 v0101 |
| via-pmipair | 0188 | 0205 | listings · engine · VDF_ENG231 v0102 |
| via-sentiment | 0189 | 0206 | accelerator · loader · SUP_MDL737 v0109 |
| via-vcgctest | 0190 | 0207 | network · body · VeritasAegisNexus v1651 |
| via-vdfmatrix | 0191 | 0208 | network · candidate · VeritasAegisNexus v1652 |
| via-vrnreport | 0192 | 0209 | network · loader · SUP_MDL740 v0118 |
| via-vrntab | 0193 | 0210 | tools · gate · CGC_MDL233 v0100 |
| via-in | 0194 | 0211 | token · engine · CGC_MDL158 v0116 |

## 四、驗證

欄位照驗證 SSOT(`VIA_Validation_SSOT_v0100.json`):層 = 驗證邏輯 VAL / 結果驗證 RVL / 交叉核對 X;狀態用它的誠實狀態碼(GREEN · RED · YELLOW · ABSENT · GATED · SKIP)。一列一件事,不加列外的檢。

| 層 | 代碼 | 項 | 實測法(指令) | 狀態 | 結果 | 結果的驗證 |
|---|---|---|---|---|---|---|
| RVL | X-MINT | 元件冊 × 引擎版本冊零撞號 | `via-vcgc registry-sync`(乾跑)· 自測 ⑥ | GREEN | 修前 16 撞 → 修後 0 | 同一檢在真冊上正反都跑:修前 ⑥ 紅(撞 16)、修後綠 |
| VAL | X-MINT | 發號法:地板取三者之大 · 撞號讓號留舊號 · 只抬計數器 | 自測 ②③④(暫存 / 真冊副本) | GREEN | ④:0001 → 0213;前版新發 0214 / 0215 都在他冊號之上 | 突變 M03 · M05–M08 · M10 · M12 全被抓 |
| VAL | — | 暫存冊行為與前版一模一樣 | 自測 ⑤(同一副本:前版 vs 本版) | GREEN | 13785 鍵逐鍵同號 | 突變 M11(暫存冊誤讀他冊)被抓 |
| VAL | — | 乾跑零寫 | 自測 ④⑥ 位元比對 | GREEN | 冊位元不變 | 突變 M09 被抓(它寫壞的正本由工具還原並核 sha) |
| VAL | — | 鏈上每個呼叫點都走新版 | 自測 ⑦(含後載別名模組) | GREEN | 載入時換 1 · 後載換 1 | 突變 M13–M15 被抓 |
| VAL | — | 同步檢查報待改號 · 動詞印發號段 · 寫後仍撞 rc 2 | 自測 ⑧⑨(替身底層,不走寫檔的 SDD 路) | GREEN | 正控 recode 1 · 反控 0 · rc (0,0,2,2,0) | 突變 M16–M22 被抓 |
| RVL | — | 元件冊改動範圍 | 改前 / 改後逐筆比對 | GREEN | 只動 16 筆的代碼與改號三欄 · 計數器 · 新登錄函式 | 全冊代碼唯一;與引擎版本冊已發號交集為空 |
| RVL | — | 自測總數 | `v0174 --selftest` | GREEN | 82 / 82(前版鏈 72 + 本版 10) | 突變 22 / 22 全殺 |
| X | X-VAL | 驗證 SSOT 自己 | CGC_MDL246 核對 + 自測 | GREEN | 交叉代碼 23;X-MINT 的正主與記號 `def plan_codes` 對上 | 自測 12 / 12 |
| VAL | VCGC-VAL002 | 只收 VCGC 呼叫 · 閘 | `via-vcgc status` | GREEN | rc 0 · 註冊 13149 / 13149 缺 0 · 待改號 0 | 非綠兩燈(SSOT 連動 YELLOW · VRN 模板 ABSENT)與本批之前的閘輸出相同 |
| VAL | — | 殺手閘 | CGC_MDL187 v0103 `--base origin/main --run-selftest` | GREEN | 11 條全過 · 既有債 2 筆照記 | 第一次跑抓到 ④ 標號在同檔出現兩次 → 改成單一標號後通過 |
| VAL | — | 入口控制 | CGC_MDL157 v0106 `status` | GREEN | 29 / 29 | — |
| RVL | — | 總控頁(LL49) | `VIA_SYSTEM_MANAGER_v0150.py ui --no-open` 後逐列比對 | GREEN | 522 列只換 VCGC 一列 + 產生時間 | 合約測試 test_11 交 CI |
| RVL | — | 格子 v0504 站名 | 站名數字照 v0174 實印檢數 | SKIP | 七十二 → 八十二 | `--only` 本批沒在容器跑(操作員喊停),交 CI / 工作站 |
| VAL | X-REQ | 需求雙向(近三日操作員令入冊)| `via-vcgc sdd check` | GREEN | 需求 99 條 · 代碼連續唯一 · 每條歸屬都在(工作流 / 律 / 冊)| 入冊前同一檢是 RED(X-NUM:5 個新代碼未編號)→ 編號後綠 |
| VAL | X-NUM | WKF · STP · REQ 全編號 | 同上 | GREEN | 231 個全編號(號碼 = VIA- + 冊上代碼)| REQ 編號書只增 5 列,舊 94 列位元不動 |
| RVL | X-REQ-OPEN | 需求未全落地 | 同上 | YELLOW | 14 條 PARTIAL / MISSING(13 條既有 + 本批 VRN-REQ006)| 每條都有歸屬與下一步;照實記,不硬拗成綠 |
| VAL | X-LOCK | 已鎖工作流的尾版有沒有換 | 同上 | YELLOW | VCGC-WKF003 鎖在 VCGC v0172,尾版已到 v0174 | 既有:PR #372(v0173)合併時就亮;重鎖要先提交,再在同一個 HEAD 跑 `sdd selftests` · `sdd real` · `sdd lock --apply`,本批不擴大 |

## 五、登錄

- 元件冊:16 筆改號(0179–0194 → 0196–0211,舊號記在各筆 `recoded_from`)· `TOOL` 計數器 194 → 211 · 照常登錄 v0174 與格子 v0504 的函式。
- 編號冊只增合併:`VIA-VCGC-MDL1439`(v0174)· `VIA-VCGC-MDL1438`(格子 v0504)· FNC_VCGC +67;編號 SSOT 只更新兩冊的 n / sha,以及 `SSOT007`(元件冊)、`SSOT050`(驗證 SSOT)的 content_sha。
- 驗證 SSOT:只增 `X-MINT`(正主 CGC_MDL149 尾版 · 記號 `def plan_codes`),VCGC 的 cross_check 18 → 19。
- 座位冊 CONSOLE → v0174 · 總控頁 VCGC 那一列 · 台帳 1361。
- 需求冊 `VIA_Requirements_SSOT_v0102.json`(新版,v0101 留作版史;操作員令「先檢查更新近三日關於VCGC的功能要求更新 SSOT VCGC WORKFLOW 相關管理引擎功能檢查實測無誤收尾」):補進上一輪審查(止於 09-29 00:10Z)之後的操作員令 14 則 —— 新增 VCGC-REQ072 一句進環境(`enter` / `via-in`)· VCGC-REQ073 驗證輸出收斂(DataFrame · SSOT 欄位)· VCGC-REQ074 Actions 升 Node 24 · SUP-REQ006 Polars 與 temp · VRN-REQ006 擷取分層升級(PARTIAL,附下一步);REQ056 / 058 / 059 / 069 補引文(狀態不變);非需求 4 則。VCGC 工作流冊不必換版:新需求都歸屬到既有工作流代碼(WKF001 / WKF004 · VRN-WKF002 / 003)。
- 編號:REQ 編號書 +5(`VIA-VCGC-REQ072–074` · `VIA-SUP-REQ006` · `VIA-VRN-REQ006`)· 編號 SSOT 新列 `VIA-VCGC-SSOT051`(需求冊 v0102)。

## 六、之後怎麼防

- 任何範圍的 registry-sync(整冊、`--layout-only`、`--nlp-only`、hub 委派)都走 v0174:新號一定比所有冊已發的號都大。
- 引擎版本冊仍然是手寫。手寫的號如果撞上元件冊已發的號:v0174 自測 ⑥ 會紅,閘的同步檢查會印「待同步 · recode N」,跑 `via-vcgc registry-sync --apply` 由元件冊讓號。
- 手寫引擎版本冊時,新號取「元件冊 `counters.TOOL` 與引擎版本冊最大號」兩者較大再 +1,就不會撞。

## 七、同一次審查的另一條(P2,本批不動)

`VIA_PY_TIMEOUT_SEC` 設成負數時,`via-in` 不會放寬逾時;`Invoke-VIAPython` 又把負數當成不設上限,跟 via-in 自己的說明不一致。修法只改一個運算子(`-gt 0` 改成 `-ne 0`),但 v0263 已合併,要出 `Register-VIA-Commands-v0264.ps1`。依 L70 需要操作員逐次許可,已交給操作員,本批不動任何 `.ps1`。

## 八、還原

`git revert` 本批的合併提交:元件冊回到改號前(16 號一號兩主的狀態);刪掉 v0174 後 registry-sync 退回 v0142 的發號法,格子退回 v0503。
