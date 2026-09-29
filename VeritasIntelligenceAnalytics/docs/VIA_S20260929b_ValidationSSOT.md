# 側線 2026-09-29 b:三系統驗證 SSOT(驗證邏輯 · 結果驗證 · 交叉核對)· Codex #366 三件修正

主線批號由併線的手指定(L25)。本批接在 PR #366(82ef70b9)之後。

## 一、操作員令(原文)

- 「三個系統的validation logic result validation logic cross checking機制寫入ssot」

## 二、先量再寫

| 量到的 | 位置 |
|---|---|
| SDD 五層裡每條工作流都有 `tests`(self · cross · real),**沒有系統層級**的「驗證邏輯 / 結果驗證 / 交叉核對」總表 | VIA_Workflow_{VCGC,VDF,VRN}_SSOT_v0100 |
| 工作流冊的 `tests.cross` 引用 **X-CONF**(4 處)與 **X-NET**(VDF 2 處),SDD 驗證器從沒實作這兩個代碼,也沒有任何冊說它們由誰實作 | CGC_MDL245 v0100 只實作 14 個 X- 代碼 |
| 別的分支正在改 SDD 驗證器(CGC_MDL245 v0101 在 `claude/vcgc-vrn-read-forward`)——再加一版會撞號或跳號(KILL-11) | LL334 全分支掃描 |

所以不改 MDL245、不另開一套工作流編號:另開**一本**驗證冊,由新核對器 CGC_MDL246 核對。工作流冊仍照 MDL245 的 `load_books` 讀,遵守 L05 一把尺。

## 三、冊:`VIA_Validation_SSOT_v0100.json`(VAL-SSOT)

| 層 | 代碼 | VCGC | VDF | VRN |
|---|---|---|---|---|
| 驗證邏輯(這一步准不准做、照不照律做) | `<系統>-VAL<三碼>` | 8 | 6 | 5 |
| 結果驗證(做完的東西對不對、齊不齊) | `<系統>-RVL<三碼>` | 6 | 4 | 7 |
| 交叉核對(兩個來源說的是不是同一件事) | `X-<名>`,三系統共用 22 個 | 18 | 11 | 12 |

- 每一條都指名**正主**(相對 VIA 根;`_v*.py` 取尾版)。交叉代碼另指**實作記號**,例如 X-CONF → VCGC 的 `def conformance`,X-NET → 全景治理類 `"NET"`,X-BROKER → 資料中介 `def bypass`。
- 誠實多態照冊上 `honest_states`:0 綠 · 1 紅 · 2 黃/缺料 · 3 缺件 · 4 待閘 · 5 略過。
- 代碼只增、舊號不改不刪,退役的記在 `retired`。

## 四、核對器:`CGC_MDL246_ValidationSSOT_v0100`(X-VAL)

| 規則 | 管什麼 |
|---|---|
| V-SHAPE | 三系統都在,每系統三層都不空,每條有 code / name / owner |
| V-CODE | VAL 只在驗證邏輯層、RVL 只在結果驗證層;系統前綴相符;不撞號;不用退役號 |
| V-OWNER | 每條的正主都在 |
| V-IMPL | 交叉代碼的實作記號在正主的**整條版本鏈**裡(薄尾的函式常在前一版本體) |
| V-XREF | 雙向:工作流冊引用的代碼都登記(X-* 是通配);各系統只列已登記的;登記了卻沒人用 = 黃 |
| V-SDD | SDD 驗證器實作的每個 X- 代碼都登記(驗證器多了新檢、本冊沒跟上 = 紅) |
| V-POLICY | L 條在法冊,其餘是政策小冊的 id |
| V-REF | refs 指的工作流 / 步代碼在工作流冊 |

用法:`via-vcgc val`(= `run --family core CGC_MDL246_ValidationSSOT check`)· `via-vcgc val show VDF`。

## 五、Codex 審查 PR #366 三件(新版檔修,舊版照 L04 不動)

| 發現 | 修法 |
|---|---|
| **P1** VCGC v0170:第一步紅時連 `tools activate token … --apply` 都擋,修第一步的鑰匙被鎖在門裡 | **VCGC v0171**:第一步紅時只放行 `tools`(狀態)與 `tools activate token\|nlp …`,並印「放行修第一步」;別家 activate、status、help 照停。help 也會被 v0161 的步驟門擋,所以不列入放行,不假裝走得通。新增 `val` 動詞 |
| **P2** 步驟矩陣 v0101:快取鍵只雜湊 NLP 薄尾 v0105,本體 v0104 被改或被刪仍沿用舊的綠 | **CGC_MDL226 v0102**:鍵 = 鎖上那支同 stem、版號 ≤ 它的整條版本鏈,加上矩陣自己的鏈 |
| **P2** 擊斃閘 v0102:類別方法、`if False:`、return 之後、結果丟掉的 `PRIOR.selftest()` 都被算成委派 | **CGC_MDL187 v0103**:只看模組層 selftest 函式的必經路徑(頂層述句與頂層 try 本體,遇到無條件 return 就停),而且結果要流進回傳值 |

## 六、驗證

| 項 | 結果 |
|---|---|
| CGC_MDL246 自測 | 12/12(真冊 GREEN · 八種負控 · 冊不在 = ABSENT rc3 · 零足跡);突變 11/11 全抓 |
| `via-vcgc val` 實跑 | GREEN rc0 · 22 個交叉代碼 · 八道規則全綠 |
| VCGC v0171 自測 | 6/6,並串接 v0170 → … → v0161 整條鏈全過;真事件夾零足跡 |
| CGC_MDL226 v0102 自測 | 前鏈 10/10 + ⑪ |
| CGC_MDL187 v0103 自測 | 27/27;新負控與正控突變 5/5 全抓(單拆「return 截斷」一道存活是雙重防護,兩道一起拆即被抓) |
| 前批(a)全格子 S5 | OK 323 · FAIL 24 · SKIP 16 · TIMEOUT 0。**24 站在本批之前的主線 0cebb651 上同樣全紅**(基準重跑 24/24 FAIL)。其中 6 站讀到本批改過的冊,逐檢比對 [FAIL] 行,新增 0、消失 0。本批沒有造成任何新紅 |

## 七、教訓(照實記)

- **冊上引用的代碼要有人實作**:X-CONF、X-NET 寫在三本工作流冊裡很久,卻從沒有檢查碼。SSOT 如果只寫「說法」、不指正主,就會出現沒人發現的空殼。本冊每一條都要點名正主與實作記號。
- **字面檢不能被自己的說明文字踩到**:擊斃閘 ⑫ 用 `def selftest(` 切出判決段,新說明寫了那幾個字,切點就被提前(LL384 同一個坑)。
- **量測前先掃別人的分支**:MDL245 v0101 在別的分支,硬加版號只會在撞號與跳號(KILL-11)之間二選一,所以改開新引擎。

## 八、還原

- 刪本批新檔,即回到尾版律的前一版:CGC_MDL246 v0100、VIA_Validation_SSOT v0100、VCGC v0171、CGC_MDL226 v0102、CGC_MDL187 v0103、格子 v0500。
- 座位冊 CONSOLE v0170 → v0171 照 FLOW-1「有變才上傳」一併入倉;還原時用 `git restore --source=82ef70b9`。
